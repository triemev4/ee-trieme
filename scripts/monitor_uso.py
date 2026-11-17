"""Monitor de uso da EE: gasto de tokens e tempo por etapa. Só lê e mostra; não grava nada.

Lê o que a medição automática (medir_uso.py, gatilho de fim de tarefa) e o consultor gravam na seção Medição do
registro interno de cada cliente (<cliente>/_ensaios-internos/registro.md) e, no modo conversa, o histórico local da
conversa aberta. Só biblioteca padrão, sem rede, nada sai da máquina.

Uso:
    python monitor_uso.py tokens [<pasta EE>] [--cliente <nome>]
    python monitor_uso.py tempo [<pasta EE>] [--cliente <nome>]
    python monitor_uso.py conversa [<pasta EE>] [--sessao <id>] [--limite 150000]
A pasta EE é a que tem Clientes/. Sem ela, vale a pasta aberta ou a EE/ dentro dela.

tokens    Por etapa: sessões, tokens novos (entrada + cache criado), saída, cache lido, média por cliente e a sessão
          mais pesada. Lista as sessões que misturaram semanas ou clientes (a regra é uma conversa por semana).
tempo     Por etapa: horas do consultor registradas (Preparo, Reunião e Pós dos encontros; as atividades) contra a
          partida do modelo do registro, e o tempo ativo das sessões com o Claude. As duas medidas não se somam: o
          tempo com o Claude está dentro do preparo e do pós. O que não foi registrado é "não medido", nunca estimado.
conversa  A conversa aberta: quanto cada resposta relê (tamanho da última resposta), pico, gasto e tempo ativo.
          Avisa a partir de --limite tokens por resposta.
"""
import sys
sys.dont_write_bytecode = True
import argparse
import collections
import json
import os
import re
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import medir_uso as M  # noqa: E402
import relatorio_uso as R  # noqa: E402

LIMITE_CONVERSA = 150_000   # tokens relidos por resposta a partir dos quais a conversa é pesada

# Etapas na ordem da EE, com a partida em horas do consultor (comentário da Medição em modelos/registro-interno.md:
# total 48 h; Encerramento vira 1,5 h com Handoff, 49 h). Retrabalho não tem partida.
ETAPAS = [
    ("passagem", "Passagem da venda", 1.0),
    ("kickoff", "Kickoff (com pré e pós)", 6.0),
    ("pesquisa", "Pesquisa de Mercado", 8.5),
    ("marketing", "Diagnóstico de Marketing", 8.5),
    ("comercial", "Diagnóstico Comercial", 8.5),
    ("criacao", "Criação de entregáveis", 6.0),
    ("ensaio", "Ensaios", 1.0),
    ("mesa", "Mesa", 0.5),
    ("planejamento", "Planejamento Estratégico + Entregáveis", 7.5),
    ("encerramento", "Encerramento", 0.5),
    ("retrabalho", "Retrabalho", 0.0),
]
NOME = {k: n for k, n, _ in ETAPAS}
PARTIDA = {k: p for k, _, p in ETAPAS}
PARTIDA_HANDOFF = 1.5
PARTIDA_ENSAIO = 0.25       # por encontro das Semanas 2 a 5 (4 x 0,25 = 1 h)
SEM_ETAPA = "outros"
NOME[SEM_ETAPA] = "Sem etapa reconhecida"
ORDEM = [k for k, _, _ in ETAPAS] + [SEM_ETAPA]


def chave_da_etapa(texto):
    """Etapa canônica de um rótulo do registro ('Kick-Off', 'Pós-Kickoff', 'Ensaio S2 r1', 'Retrabalho: deck')."""
    t = M.sem_acento(texto)
    if t.startswith("retrabalho"):
        return "retrabalho"
    if t.startswith("ensaio"):
        return "ensaio"
    if t.startswith("mesa"):
        return "mesa"
    if t.startswith("criacao") or "entregaveis de criacao" in t:
        return "criacao"
    if t.startswith("passagem"):
        return "passagem"
    if t.startswith(("encerramento", "handoff", "conversao", "concluida")):
        return "encerramento"
    for pedaco, chave in (("kick", "kickoff"), ("pesquisa", "pesquisa"), ("marketing", "marketing"),
                          ("comercial", "comercial"), ("planejamento", "planejamento")):
        if pedaco in t:
            return chave
    return None


# ---------- números ----------

def tok(v):
    """Tokens para leitura: 950, 123 mil, 12,3 mi."""
    v = int(round(v))
    if v < 1000:
        return str(v)
    if v < 1_000_000:
        return f"{v / 1000:.0f} mil"
    return f"{v / 1_000_000:.1f} mi".replace(".", ",")


def h(v):
    """Horas com até duas casas e vírgula: 8,5 · 0,25 · 6."""
    s = f"{v:.2f}".rstrip("0").rstrip(".")
    return s.replace(".", ",") if s else "0"


def dif(v):
    if abs(v) < 0.005:
        return "0"
    return ("+" if v > 0 else "−") + h(abs(v))


MEDIDO, PARCIAL, NAO_MEDIDO, ILEGIVEL = "medido", "parcial", "não medido", "ilegível"


def horas_da_celula(s):
    """(horas, estado). Aceita 1,5 · 1.5 · 2 h · 1h30 · 0:45 · 90 min. Vazio, 'não medido' e estimativa: não medido."""
    t = M.sem_acento(str(s)).strip()
    if not t or t in ("-", "—", "–") or "nao medido" in t or "estim" in t:
        return None, NAO_MEDIDO
    t = re.sub(r"\s*\(.*\)\s*$", "", t)                     # comentário entre parênteses no fim
    m = re.fullmatch(r"(\d+)\s*h\s*(\d{1,2})\s*(?:min)?", t)
    if m:
        return int(m.group(1)) + int(m.group(2)) / 60, MEDIDO
    m = re.fullmatch(r"(\d+):(\d{2})", t)
    if m:
        return int(m.group(1)) + int(m.group(2)) / 60, MEDIDO
    m = re.fullmatch(r"(\d+(?:[.,]\d+)?)\s*(?:min|minutos?)", t)
    if m:
        return float(m.group(1).replace(",", ".")) / 60, MEDIDO
    m = re.fullmatch(r"(\d+(?:[.,]\d+)?)\s*(?:h|horas?)?", t)
    if m:
        return float(m.group(1).replace(",", ".")), MEDIDO
    return None, ILEGIVEL


# ---------- leitura dos registros ----------

def tabelas(texto_secao):
    """Tabelas Markdown de um trecho: lista de tabelas, cada uma lista de linhas (cabeçalho primeiro)."""
    out, atual = [], []
    for ln in texto_secao.splitlines():
        s = ln.strip()
        if s.startswith("|"):
            if re.fullmatch(r"[\s:|-]+", s):
                continue
            atual.append([c.strip() for c in s.strip("|").split("|")])
        elif atual:
            out.append(atual)
            atual = []
    if atual:
        out.append(atual)
    return out


def _coluna(cab, prefixo):
    for i, c in enumerate(cab):
        if M.sem_acento(c).startswith(prefixo):
            return i
    return None


def horas_registradas(texto_registro):
    """{etapa: {"horas": float, "itens": [(rótulo, estado, horas)]}} e o flag de Handoff, lidos das tabelas de
    encontros (Preparo, Reunião, Pós) e de atividades (Real) da seção Medição."""
    etapas = collections.defaultdict(lambda: {"horas": 0.0, "itens": []})
    handoff = False
    for tab in tabelas(M.secao(texto_registro, "Medição")):
        cab = tab[0]
        primeira = M.sem_acento(cab[0]) if cab else ""
        if primeira.startswith("encontro") and _coluna(cab, "preparo") is not None:
            colunas = [(r, _coluna(cab, p)) for r, p in (("Preparo", "preparo"), ("Reunião", "reuniao"), ("Pós", "pos"))]
            for linha in tab[1:]:
                chave = chave_da_etapa(linha[0]) if linha else None
                if not chave:
                    continue
                for rotulo, i in colunas:
                    valor, estado = horas_da_celula(linha[i] if i is not None and i < len(linha) else "")
                    etapas[chave]["itens"].append((rotulo, estado, valor))
                    etapas[chave]["horas"] += valor or 0.0
        elif primeira.startswith("atividade") and _coluna(cab, "real") is not None:
            i = _coluna(cab, "real")
            for linha in tab[1:]:
                chave = chave_da_etapa(linha[0]) if linha else None
                if not chave:
                    continue
                celula = linha[i] if i < len(linha) else ""
                if chave == "retrabalho" and not celula.strip():
                    continue                                   # retrabalho vazio é "não houve"
                valor, estado = horas_da_celula(celula)
                if M.sem_acento(linha[0]).startswith("handoff") and estado == MEDIDO:
                    handoff = True                             # a linha do modelo "Encerramento (ou Handoff)" não conta
                modelo = "uma linha por" in M.sem_acento(linha[0])
                rotulo = re.sub(r"\s*\(uma linha por.*?\)", "", linha[0]).strip()[:50]
                etapas[chave]["itens"].append((rotulo, estado, valor, modelo))
                etapas[chave]["horas"] += valor or 0.0
    for d in etapas.values():
        # a linha do modelo "(uma linha por ...)" vazia sai quando o consultor já lançou linhas reais
        reais = [i for i in d["itens"] if len(i) < 4 or not i[3]]
        if reais and len(reais) < len(d["itens"]):
            d["itens"] = [i for i in d["itens"] if len(i) < 4 or not i[3] or i[1] != NAO_MEDIDO]
        d["itens"] = [i[:3] for i in d["itens"]]
    return etapas, handoff


def situacao(itens):
    estados = {e for _, e, _ in itens}
    if not itens or estados <= {NAO_MEDIDO}:
        return NAO_MEDIDO
    if estados == {MEDIDO}:
        return MEDIDO
    return PARCIAL


def sessoes_do_registro(texto_registro, cliente):
    """Linhas automáticas (medir_uso) do registro, com a etapa canônica e as marcas de mistura."""
    out = []
    for d in M.ler_linhas_uso(texto_registro):
        r = {"Cliente": cliente, "Sessão": d["Sessão"], "Data": d["Data"], "Etapa": d["Etapa"],
             "chave": chave_da_etapa(d["Etapa"]) or SEM_ETAPA,
             "Entrada": R.inteiro(d["Entrada"]), "Saída": R.inteiro(d["Saída"]),
             "Cache lido": R.inteiro(d["Cache lido"]), "Cache criado": R.inteiro(d["Cache criado"]),
             "Ativa (min)": R.minutos(d["Ativa (min)"]), "Duração (min)": R.minutos(d["Duração (min)"])}
        r["Novos"] = r["Entrada"] + r["Cache criado"]
        r["Total"] = r["Novos"] + r["Saída"] + r["Cache lido"]
        partes = [p.strip() for p in d["Observação"].split(";")]
        r["semanas_extra"] = next((p[len("também mexeu em "):] for p in partes if p.startswith("também mexeu em ")), "")
        r["outros_clientes"] = next((p[len("sessão também mexeu em "):] for p in partes
                                     if p.startswith("sessão também mexeu em ")), "")
        out.append(r)
    return out


def carregar(raiz, filtro=None):
    """[{nome, sessoes, horas, handoff, tem_registro}] dos clientes de <raiz>/Clientes, filtrados por nome."""
    clientes = []
    for pasta in M.pastas_de_clientes(raiz):
        registro = M.caminho_registro(pasta)
        if not registro.is_file() and M.achar_ficha(pasta) is None:
            continue
        nome = M.nome_do_cliente(pasta)
        texto = registro.read_text(encoding="utf-8-sig") if registro.is_file() else ""
        horas, handoff = horas_registradas(texto)
        handoff = handoff or (pasta / "Handoff").is_dir()   # o guia de encerramento renomeia a pasta com Executar
        clientes.append({"nome": nome, "pasta": pasta.name, "sessoes": sessoes_do_registro(texto, nome),
                         "horas": horas, "handoff": handoff, "tem_registro": registro.is_file()})
    if filtro:
        f = M.sem_acento(filtro)
        exatos = [c for c in clientes if M.sem_acento(c["nome"]) == f or M.sem_acento(c["pasta"]) == f]
        clientes = exatos or [c for c in clientes if f in M.sem_acento(c["pasta"])]
    return clientes


def achar_raiz(dada=None):
    candidatas = [Path(dada)] if dada else [Path.cwd(), Path.cwd() / "EE"]
    for c in candidatas:
        if (c / "Clientes").is_dir():
            return c
    return None


# ---------- tokens ----------

def relatorio_tokens(clientes, titulo):
    linhas = [r for c in clientes for r in c["sessoes"]]
    sem_uso = [c["nome"] for c in clientes if not c["sessoes"]]
    out = [f"# Gasto de tokens por etapa · {titulo}", ""]
    if not linhas:
        out.append("Nenhuma sessão medida ainda (não medido).")
        if sem_uso:
            out.append("Clientes sem medição: " + ", ".join(sem_uso) + ".")
        return "\n".join(out)
    unicas = {}
    for r in linhas:
        unicas.setdefault(r["Sessão"], r)
    u = list(unicas.values())
    nclientes = len({r["Cliente"] for r in linhas})
    out.append(f"{len(u)} sessão(ões) em {nclientes} cliente(s). Novos {tok(R.soma(u, 'Novos'))} · saída "
               f"{tok(R.soma(u, 'Saída'))} · cache lido {tok(R.soma(u, 'Cache lido'))} · total "
               f"{tok(R.soma(u, 'Total'))}. Sessão de dois clientes conta uma vez neste total.")
    por = collections.defaultdict(dict)                       # etapa -> {sessão: linha} (sem contar duas vezes)
    clientes_da_etapa = collections.defaultdict(set)
    for r in linhas:
        por[r["chave"]].setdefault(r["Sessão"], r)
        clientes_da_etapa[r["chave"]].add(r["Cliente"])
    rows = []
    for k in [k for k in ORDEM if k in por]:
        ls = list(por[k].values())
        pesada = max(ls, key=lambda r: r["Total"])
        ncl = len(clientes_da_etapa[k])
        rows.append([NOME[k], len(ls), ncl, tok(R.soma(ls, "Novos")), tok(R.soma(ls, "Saída")),
                     tok(R.soma(ls, "Cache lido")), tok(R.soma(ls, "Total")), tok(R.soma(ls, "Total") / ncl),
                     f"{pesada['Sessão']} ({pesada['Cliente']}, {pesada['Data']}): {tok(pesada['Total'])}"])
    out += ["", R.tabela(["Etapa", "Sessões", "Clientes", "Novos", "Saída", "Cache lido", "Total",
                          "Média por cliente", "Sessão mais pesada"], rows)]
    topo = sorted(u, key=lambda r: -r["Total"])[:5]
    out += ["", "## Sessões mais pesadas", "",
            R.tabela(["Sessão", "Data", "Cliente", "Etapa", "Total", "Cache lido", "Ativa (min)"],
                     [[r["Sessão"], r["Data"], r["Cliente"], NOME[r["chave"]], tok(r["Total"]), tok(r["Cache lido"]),
                       M.minutos_txt(r["Ativa (min)"] * 60)] for r in topo])]
    misturadas = [r for r in u if r["semanas_extra"] or r["outros_clientes"]]
    if misturadas:
        out += ["", "## Sessões que misturaram semanas ou clientes", "",
                "A sessão inteira conta para a etapa mais mexida: a etapa listada está inflada e a outra, subcontada. "
                "A regra é uma conversa por semana.", ""]
        for r in misturadas:
            extra = []
            if r["semanas_extra"]:
                extra.append("também " + r["semanas_extra"])
            if r["outros_clientes"]:
                extra.append("também o cliente " + r["outros_clientes"])
            out.append(f"- {r['Sessão']} ({r['Data']}, {r['Cliente']}): contou em {NOME[r['chave']]}; "
                       + "; ".join(extra) + f". Total {tok(r['Total'])}.")
    notas = ["Novos = entrada + cache criado. Cache lido = a conversa relida a cada resposta; cresce com o tamanho "
             "da conversa e por isso costuma ser o maior número."]
    if sem_uso:
        notas.append("Clientes sem sessão medida (não medido): " + ", ".join(sem_uso) + ".")
    return "\n".join(out + ["", "## Notas", ""] + [f"- {x}" for x in notas])


# ---------- tempo ----------

def tempo_do_cliente(c):
    """{etapa: {partida, registrado, situacao, faltando, ilegiveis, claude_h}}."""
    claude = collections.defaultdict(float)
    for r in c["sessoes"]:
        claude[r["chave"]] += r["Ativa (min)"] / 60
    res = {}
    for k in ORDEM:
        reg = c["horas"].get(k, {"horas": 0.0, "itens": []})
        partida = PARTIDA_HANDOFF if k == "encerramento" and c["handoff"] else PARTIDA.get(k, 0.0)
        lancados = [i for i in reg["itens"] if i[1] == MEDIDO]
        if k == "ensaio" and lancados:
            partida = PARTIDA_ENSAIO * len(lancados)         # uma linha por semana e rodada; partida com uma rodada
        if not reg["itens"] and k not in claude and (k in ("retrabalho", SEM_ETAPA)):
            continue
        faltando = [rot for rot, e, _ in reg["itens"] if e == NAO_MEDIDO]
        if not reg["itens"] and k not in ("retrabalho", SEM_ETAPA):
            faltando = ["sem linha no registro"]
        res[k] = {"partida": partida, "registrado": reg["horas"], "situacao": situacao(reg["itens"]),
                  "faltando": faltando,
                  "ilegiveis": [rot for rot, e, _ in reg["itens"] if e == ILEGIVEL],
                  "claude_h": claude.get(k)}
    return res


def _texto_registrado(d):
    if d["situacao"] == NAO_MEDIDO:
        return "não medido"
    return h(d["registrado"]) + (" (parcial)" if d["situacao"] == PARCIAL else "")


def relatorio_tempo_cliente(c):
    t = tempo_do_cliente(c)
    out = [f"# Tempo por etapa · {c['nome']}", ""]
    if not c["tem_registro"]:
        out.append("Sem registro interno (_ensaios-internos/registro.md): nada medido.")
        return "\n".join(out)
    completas = [d for d in t.values() if d["situacao"] == MEDIDO]
    claude_total = sum(d["claude_h"] or 0 for d in t.values())
    out.append(f"Horas do consultor: {h(sum(d['registrado'] for d in completas))} h em {len(completas)} etapa(s) "
               f"medidas por inteiro, contra {h(sum(d['partida'] for d in completas))} h de partida nessas etapas. "
               f"Sessões com o Claude: {h(claude_total)} h ativas (medido sozinho; não somar às horas do consultor).")
    rows = []
    for k, d in t.items():
        diferenca = dif(d["registrado"] - d["partida"]) if d["situacao"] == MEDIDO else "—"
        rows.append([NOME[k], h(d["partida"]) if k not in ("retrabalho", SEM_ETAPA) else "—", _texto_registrado(d),
                     diferenca, h(d["claude_h"]) if d["claude_h"] is not None else "não medido", d["situacao"]])
    total_partida = sum(PARTIDA.values()) + (PARTIDA_HANDOFF - PARTIDA["encerramento"] if c["handoff"] else 0)
    rows.append(["**Total**", h(total_partida), h(sum(d["registrado"] for d in t.values())), "—", h(claude_total), ""])
    out += ["", R.tabela(["Etapa", "Partida (h)", "Registrado (h)", "Diferença", "Com o Claude (h ativas)",
                          "Situação"], rows)]
    faltas = [f"{NOME[k]}: " + ", ".join(d["faltando"]) for k, d in t.items() if d["faltando"]]
    ileg = [f"{NOME[k]}: " + ", ".join(d["ilegiveis"]) for k, d in t.items() if d["ilegiveis"]]
    if faltas:
        out += ["", "## Falta registrar", ""] + [f"- {x}" for x in faltas]
    if ileg:
        out += ["", "## Célula ilegível (corrigir no registro)", ""] + [f"- {x}" for x in ileg]
    return "\n".join(out)


def relatorio_tempo_todos(clientes):
    out = [f"# Tempo por etapa · {len(clientes)} cliente(s)", ""]
    if not clientes:
        out.append("Nenhum cliente em Clientes/.")
        return "\n".join(out)
    por_cliente = {c["nome"]: tempo_do_cliente(c) for c in clientes}
    out.append("Média registrada e diferença usam só os clientes com a etapa medida por inteiro. Tempo com o Claude "
               "é a média de quem teve sessão na etapa; não somar às horas do consultor.")
    rows = []
    for k in ORDEM:
        ds = [t[k] for t in por_cliente.values() if k in t]
        if not ds:
            continue
        completas = [d for d in ds if d["situacao"] == MEDIDO]
        com_claude = [d["claude_h"] for d in ds if d["claude_h"] is not None]
        media = sum(d["registrado"] for d in completas) / len(completas) if completas else None
        partida_media = sum(d["partida"] for d in completas) / len(completas) if completas else PARTIDA.get(k, 0.0)
        rows.append([NOME[k], h(PARTIDA[k]) if k in PARTIDA and k != "retrabalho" else "—",
                     f"{len(completas)} de {len(ds)}", h(media) if media is not None else "não medido",
                     dif(media - partida_media) if media is not None and k in PARTIDA and k != "retrabalho" else "—",
                     h(sum(com_claude) / len(com_claude)) if com_claude else "não medido"])
    out += ["", R.tabela(["Etapa", "Partida (h)", "Clientes medidos", "Média registrada (h)", "Diferença média",
                          "Média com o Claude (h ativas)"], rows)]
    rows = []
    for c in clientes:
        t = por_cliente[c["nome"]]
        completas = [d for d in t.values() if d["situacao"] == MEDIDO]
        rows.append([c["nome"], len(completas), h(sum(d["registrado"] for d in t.values())),
                     h(sum(d["partida"] for d in completas)), h(sum(d["claude_h"] or 0 for d in t.values()))])
    out += ["", "## Por cliente", "", R.tabela(["Cliente", "Etapas medidas", "Registrado (h)",
                                                 "Partida das etapas medidas (h)", "Com o Claude (h ativas)"], rows)]
    faltas = []
    for c in clientes:
        t = por_cliente[c["nome"]]
        itens = [NOME[k] for k, d in t.items() if d["faltando"] or d["ilegiveis"]]
        if not c["tem_registro"]:
            faltas.append(f"- {c['nome']}: sem registro interno")
        elif itens:
            faltas.append(f"- {c['nome']}: " + ", ".join(itens))
    if faltas:
        out += ["", "## Falta registrar (detalhe: tempo --cliente <nome>)", ""] + faltas
    return "\n".join(out)


# ---------- conversa aberta ----------

def pasta_de_config():
    return Path(os.environ.get("CLAUDE_CONFIG_DIR") or (Path.home() / ".claude"))


def achar_historico(sessao=None):
    """Histórico (.jsonl) da conversa: pelo id, se veio e é um id; senão o mais recente da pasta aberta."""
    base = pasta_de_config() / "projects"
    if sessao and re.fullmatch(r"[0-9A-Za-z-]{8,}", sessao):
        achados = sorted(base.glob(f"*/{sessao}.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True)
        if achados:
            return achados[0]
    pasta = base / re.sub(r"[^A-Za-z0-9]", "-", str(Path.cwd()))
    candidatos = sorted(pasta.glob("*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True) if pasta.is_dir() else []
    return candidatos[0] if candidatos else None


def contexto_por_resposta(historico):
    """Tokens relidos em cada resposta da conversa principal (entrada + cache lido + cache criado), em ordem."""
    vistos, ordem = {}, []
    with open(historico, encoding="utf-8", errors="replace") as fh:
        for ln in fh:
            if '"assistant"' not in ln:
                continue
            try:
                o = json.loads(ln)
            except ValueError:
                continue
            if o.get("type") != "assistant" or o.get("isSidechain"):
                continue
            msg = o.get("message") or {}
            uso = msg.get("usage") or {}
            if msg.get("model") == "<synthetic>" or not isinstance(uso, dict):
                continue
            ctx = sum(v for v in (uso.get("input_tokens"), uso.get("cache_read_input_tokens"),
                                  uso.get("cache_creation_input_tokens")) if isinstance(v, int))
            mid = msg.get("id") or o.get("uuid")
            if mid not in vistos:
                ordem.append(mid)
            vistos[mid] = max(vistos.get(mid, 0), ctx)
    return [vistos[m] for m in ordem]


def relatorio_conversa(historico, limite=LIMITE_CONVERSA, raiz=None):
    dados = M.ler_sessao(historico, prazo_s=120)
    ctx = contexto_por_resposta(historico)
    t = dados["tokens"]
    out = ["# Esta conversa", ""]
    if not ctx:
        out.append("Ainda sem resposta medida nesta conversa.")
        return "\n".join(out), False
    ultima, pico = ctx[-1], max(ctx)
    out.append(f"- Cada resposta relê agora {tok(ultima)} tokens (pico {tok(pico)}), em {len(ctx)} resposta(s).")
    out.append(f"- Gasto até aqui: novos {tok(t['in'] + t['cc'])} · saída {tok(t['out'])} · cache lido {tok(t['cl'])}"
               + (f" · inclui {dados['subagentes']} subagente(s)" if dados["subagentes"] else "") + ".")
    out.append(f"- Tempo: {M.minutos_txt(dados['ativa_s'])} min ativos ({M.minutos_txt(dados['duracao_s'])} min no "
               f"relógio). Modelo: {M.texto_modelos(dados['modelos'])}.")
    if raiz is not None:
        mexidos = M.clientes_mexidos(dados["textos"], M.pastas_de_clientes(raiz))
        if mexidos:
            partes = [f"{M.nome_do_cliente(p)} ({M.etapa_pela_pasta(c) or 'etapa pela ficha'})" for p, c in mexidos.items()]
            out.append("- Conta para: " + "; ".join(partes) + ". A linha entra no registro interno no fim da tarefa.")
        else:
            out.append("- Ainda não mexeu em arquivo de cliente: não entra em nenhum registro.")
    pesada = ultima >= limite
    if pesada:
        out += ["", f"AVISO conversa pesada: cada resposta relê {tok(ultima)} tokens (limite {tok(limite)}). Feche o "
                "que está fazendo, confira a ficha e abra uma conversa nova (/clear): a ficha guarda o que a próxima "
                "precisa."]
    return "\n".join(out), pesada


# ---------- entrada ----------

def main(argv=None):
    ap = argparse.ArgumentParser(description="Monitor de uso da EE: tokens e tempo por etapa (só lê).")
    sub = ap.add_subparsers(dest="modo", required=True)
    for modo in ("tokens", "tempo"):
        p = sub.add_parser(modo)
        p.add_argument("raiz", nargs="?", help="pasta EE (a que tem Clientes/); padrão: a aberta ou EE/")
        p.add_argument("--cliente", help="nome do cliente (ou parte do nome da pasta)")
    p = sub.add_parser("conversa")
    p.add_argument("raiz", nargs="?", help="pasta EE, para dizer a que cliente a conversa conta")
    p.add_argument("--sessao", help="id da conversa (padrão: a mais recente da pasta aberta)")
    p.add_argument("--historico", help="caminho do .jsonl, no lugar de --sessao")
    p.add_argument("--limite", type=int, default=LIMITE_CONVERSA, help="tokens por resposta para o aviso")
    a = ap.parse_args(argv)
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    raiz = achar_raiz(a.raiz)
    if a.modo == "conversa":
        historico = Path(a.historico) if a.historico else achar_historico(a.sessao)
        if not historico or not historico.is_file():
            print("ERRO não achei o histórico desta conversa em " + str(pasta_de_config() / "projects"))
            return 1
        try:
            texto, _ = relatorio_conversa(historico, a.limite, raiz)
        except M.Prazo as e:
            print(f"ERRO {e}")
            return 1
        print(texto)
        return 0
    if raiz is None:
        print("ERRO não achei a pasta EE (a que tem Clientes/). Passe o caminho: monitor_uso.py " + a.modo + " <pasta EE>")
        return 1
    clientes = carregar(raiz, a.cliente)
    if a.cliente and not clientes:
        todos = ", ".join(c["nome"] for c in carregar(raiz)) or "nenhum"
        print(f"ERRO nenhum cliente com '{a.cliente}'. Clientes: {todos}")
        return 1
    if a.cliente and len(clientes) > 1:
        print(f"ERRO '{a.cliente}' serve para mais de um cliente: " + ", ".join(c["nome"] for c in clientes))
        return 1
    if a.modo == "tokens":
        print(relatorio_tokens(clientes, clientes[0]["nome"] if a.cliente else f"{len(clientes)} cliente(s)"))
    elif a.cliente:
        print(relatorio_tempo_cliente(clientes[0]))
    else:
        print(relatorio_tempo_todos(clientes))
    return 0


if __name__ == "__main__":
    sys.exit(main())
