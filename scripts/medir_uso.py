"""Medição automática de uso (R15): lê o histórico local de uma sessão do Claude Code e grava uma linha por sessão
na seção Medição do registro interno do cliente que a sessão mexeu (<cliente>/_ensaios-internos/registro.md; criado
a partir de modelos/registro-interno.md se não existir). Só biblioteca padrão, sem rede, nada sai da máquina.

Uso (o gatilho de fim de tarefa chama a função `medir`; à mão, para conferir):
    python medir_uso.py <historico.jsonl> <pasta EE> [--sessao <id>] [--gravar]
Sem --gravar só mostra a linha que seria gravada em cada registro.

O que soma, por sessão (histórico principal e subagentes em <sessão>/subagents/): tokens de entrada, saída, cache lido
e cache criado (uma resposta que o histórico repete em vários blocos conta uma vez, pelo id da mensagem), duração
(primeira à última mensagem; "ativa" descarta pausas de mais de 15 min), modelos, esforço e ferramentas. Descobre o
cliente pelos caminhos em Write, Edit, MultiEdit, Read, Glob, Grep e Bash dentro de Clientes/<N. Nome>/.

A linha vai na tabela "Uso medido por sessão" da seção Medição (criada no registro que ainda não a tem). A chave é o id
curto da sessão (8 caracteres): as próximas paradas atualizam a mesma linha. O arquivo só é regravado se a linha mudou.
A ficha do cliente não é tocada: a regra "ficha atrás da pasta" do gatilho ignora _ensaios-internos/.
Prazo: lê em fluxo, linha a linha, e desiste sem gravar se passar do limite.
"""
import sys
sys.dont_write_bytecode = True
import argparse
import collections
import datetime as dt
import json
import os
import re
import time
import unicodedata
from pathlib import Path

PRAZO_PADRAO = 8.0          # segundos para ler o histórico (o Stop tem 15 s)
PAUSA_MAXIMA_S = 15 * 60    # intervalo maior que isso não conta como tempo ativo
TAMANHO_MAXIMO = 400 * 1024 * 1024
MARCA_TABELA = "<!-- uso-medido: linhas gravadas pelo gatilho de fim de tarefa (scripts/medir_uso.py); não edite -->"
TITULO_TABELA = "Uso medido por sessão (gravado sozinho no fim de cada tarefa; duração total inclui pausas, ativa descarta pausas de mais de 15 min; não edite as linhas):"
COLUNAS = ["Sessão", "Data", "Etapa", "Modelo", "Entrada", "Saída", "Cache lido", "Cache criado",
           "Duração (min)", "Ativa (min)", "Ferramentas", "Observação"]
CABECALHO = "| " + " | ".join(COLUNAS) + " |"
SEPARADOR = "|" + "---|" * len(COLUNAS)

ETAPAS_SEMANA = {1: "Kick-Off", 2: "Pesquisa de Mercado", 3: "Diagnóstico de Marketing", 4: "Diagnóstico Comercial",
                 5: "Planejamento Estratégico + Entregáveis"}
PASTA_REGISTRO = "_ensaios-internos"
MODELO_REGISTRO = Path(__file__).resolve().parent.parent / "modelos" / "registro-interno.md"
ROTULOS_STATUS = ["Pré-Kickoff", "Pós-Kickoff", "Kickoff", "Passagem da venda", "Entregáveis de criação", "Mesa",
                  "Encerramento", "Conversão"]


class Prazo(Exception):
    pass


def sem_acento(s):
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn").lower().strip()


def nfc(s):
    return unicodedata.normalize("NFC", s)


# ---------- leitura do histórico ----------

def arquivos_da_sessao(transcript):
    """Histórico principal e os de subagentes (agent-*.jsonl, em qualquer subpasta de <sessão>/subagents/)."""
    transcript = Path(transcript)
    achados = [transcript]
    sub = transcript.with_suffix("") / "subagents"
    if sub.is_dir():
        achados += sorted(sub.rglob("agent-*.jsonl"))
    return achados


def _texto_de_ferramenta(bloco):
    """Textos de caminho de um tool_use: file_path, path, command."""
    entrada = bloco.get("input") or {}
    if not isinstance(entrada, dict):
        return []
    return [str(entrada[k]) for k in ("file_path", "path", "notebook_path", "command", "pattern") if entrada.get(k)]


def _hora(ts):
    try:
        return dt.datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
    except Exception:
        return None


def ler_sessao(transcript, prazo_s=PRAZO_PADRAO):
    """Soma o uso da sessão. Devolve dict ou levanta Prazo. Lê em fluxo."""
    limite = time.monotonic() + prazo_s
    arquivos = arquivos_da_sessao(transcript)
    total = sum(f.stat().st_size for f in arquivos if f.exists())
    if total > TAMANHO_MAXIMO:
        raise Prazo(f"histórico de {total // (1024 * 1024)} MB, grande demais para ler no prazo")
    usos = {}                       # id da mensagem -> dict de tokens (o maior valor de cada campo)
    modelo_msg = {}                 # id da mensagem -> (modelo, esforço)
    ferramentas = collections.Counter()
    textos = []                     # (texto, nome da ferramenta)
    horas = []
    n = 0
    for f in arquivos:
        try:
            fh = open(f, encoding="utf-8", errors="replace")
        except OSError:
            continue
        with fh:
            for ln in fh:
                n += 1
                if n % 200 == 0 and time.monotonic() > limite:
                    raise Prazo("passou do prazo de leitura")
                if not ln.startswith("{") or ("assistant" not in ln and '"user"' not in ln):
                    continue
                try:
                    o = json.loads(ln)
                except ValueError:
                    continue
                tipo = o.get("type")
                if tipo not in ("assistant", "user"):
                    continue
                h = _hora(o.get("timestamp"))
                if h is not None:
                    horas.append(h)
                if tipo != "assistant":
                    continue
                msg = o.get("message") or {}
                mid = msg.get("id") or o.get("uuid")
                uso = msg.get("usage") or {}
                modelo = msg.get("model")
                if mid and isinstance(uso, dict):
                    atual = usos.setdefault(mid, {"in": 0, "out": 0, "cl": 0, "cc": 0})
                    for campo, chave in (("in", "input_tokens"), ("out", "output_tokens"),
                                         ("cl", "cache_read_input_tokens"), ("cc", "cache_creation_input_tokens")):
                        v = uso.get(chave)
                        if isinstance(v, int) and v > atual[campo]:
                            atual[campo] = v
                    if modelo and modelo != "<synthetic>":
                        modelo_msg[mid] = (modelo, o.get("effort") or o.get("perTurnEffort") or "")
                conteudo = msg.get("content")
                if isinstance(conteudo, list):
                    for b in conteudo:
                        if isinstance(b, dict) and b.get("type") == "tool_use":
                            nome = b.get("name") or "?"
                            ferramentas[nome] += 1
                            for t in _texto_de_ferramenta(b):
                                textos.append((t, nome))
    tokens = {k: sum(u[k] for u in usos.values()) for k in ("in", "out", "cl", "cc")}
    horas.sort()
    duracao = (horas[-1] - horas[0]).total_seconds() if len(horas) >= 2 else 0.0
    ativa = sum((b - a).total_seconds() for a, b in zip(horas, horas[1:])
                if (b - a).total_seconds() <= PAUSA_MAXIMA_S)
    por_modelo = collections.defaultdict(lambda: {"out": 0, "esforco": collections.Counter()})
    for mid, (modelo, esforco) in modelo_msg.items():
        por_modelo[modelo]["out"] += usos[mid]["out"]
        if esforco:
            por_modelo[modelo]["esforco"][esforco] += 1
    return {"tokens": tokens, "mensagens": len(usos), "inicio": horas[0] if horas else None,
            "fim": horas[-1] if horas else None, "duracao_s": duracao, "ativa_s": ativa,
            "modelos": por_modelo, "ferramentas": ferramentas, "textos": textos,
            "subagentes": len(arquivos) - 1}


def nome_do_modelo(m):
    m = re.sub(r"^claude-", "", m)
    return re.sub(r"-\d{8}$", "", m)


def texto_modelos(por_modelo):
    ordem = sorted(por_modelo.items(), key=lambda kv: -kv[1]["out"])
    partes = []
    for modelo, d in ordem:
        s = nome_do_modelo(modelo)
        if d["esforco"]:
            s += f" ({d['esforco'].most_common(1)[0][0]})"
        partes.append(s)
    return " + ".join(partes) if partes else "não registrado"


def texto_ferramentas(c, maximo=6):
    itens = c.most_common()
    s = ", ".join(f"{k} {v}" for k, v in itens[:maximo])
    if len(itens) > maximo:
        s += f", +{len(itens) - maximo}"
    return s or "nenhuma"


# ---------- clientes mexidos ----------

def pastas_de_clientes(raiz):
    base = Path(raiz) / "Clientes"
    if not base.is_dir():
        return []
    return sorted(p for p in base.iterdir() if p.is_dir() and not p.name.startswith((".", "_")))


def _norm_caminho(t):
    return re.sub(r"[\\/]+", "/", nfc(t)).lower()


def formas_da_raiz(raiz):
    """Grafias da raiz EE que um caminho pode ter: como foi dada, resolvida e no estilo do Git Bash (/c/...)."""
    formas = set()
    for r in {Path(raiz), Path(raiz).resolve()}:
        f = _norm_caminho(str(r)).rstrip("/")
        formas.add(f)
        m = re.match(r"^([a-z]):(/.*)$", f)
        if m:
            formas.add("/" + m.group(1) + m.group(2))
    return formas


def _dentro_da_raiz(t, inicio, formas, nome_raiz):
    """O 'Clientes/' que começa em `inicio` é o da raiz EE informada? Caminho absoluto precisa começar na raiz;
    caminho relativo (nada de barra antes) vale. Cópia em outra pasta (scratchpad/.../EE/Clientes) não vale."""
    antes = _norm_caminho(t[max(0, inicio - 400):inicio])
    if not antes or antes[-1] != "/":
        return True                                        # relativo: Clientes/1. Nome/...
    if antes.endswith("./") and not antes.endswith("../") and (len(antes) == 2 or antes[-3] in " \"'=(:"):
        return True                                        # ./Clientes/...
    if any(antes.endswith(f + "/") for f in formas):
        return True
    n = "/" + nome_raiz.lower() + "/"
    if antes.endswith(n):
        ante = antes[:-len(n)]
        return not ante or ante[-1] in " \"'=(:,;"       # EE/Clientes/... relativo ao pai da raiz
    return False


def clientes_mexidos(textos, pastas):
    """{pasta do cliente: Counter de subpastas mexidas}, pelos caminhos dentro de <raiz EE>/Clientes/<N. Nome>/."""
    achados = {}
    if not pastas:
        return achados
    raiz = pastas[0].parent.parent
    formas, nome_raiz = formas_da_raiz(raiz), raiz.name
    padroes = []
    for p in pastas:
        nome = re.escape(nfc(p.name)).replace(r"\ ", r"\\?\s")
        padroes.append((p, re.compile(r"Clientes[\\/]+" + nome + r"(?:[\\/]+([^\\/\"'\n\r]+))?", re.I)))
    for texto, _ferr in textos:
        t = nfc(texto)
        if "lientes" not in t:
            continue
        for p, rx in padroes:
            for m in rx.finditer(t):
                if not _dentro_da_raiz(t, m.start(), formas, nome_raiz):
                    continue
                c = achados.setdefault(p, collections.Counter())
                sub = (m.group(1) or "").strip()
                if sub and not sub.endswith(".md") and not sub.startswith("."):
                    c[sub] += 1
                else:
                    c[""] += 1
    return achados


def etapa_pela_pasta(contagem):
    """Semana (1 a 5) ou Encerramento mais mexida; None se só houve Inputs, ficha ou nada."""
    melhor, melhor_n = None, 0
    for sub, n in contagem.items():
        m = re.match(r"^([1-5])\.\s*", sub)
        if m:
            chave = int(m.group(1))
        elif sem_acento(sub).startswith("encerramento"):
            chave = 6
        else:
            continue
        if n > melhor_n or (n == melhor_n and melhor is not None and chave > melhor):
            melhor, melhor_n = chave, n
    if melhor is None:
        return None
    return "Encerramento" if melhor == 6 else ETAPAS_SEMANA[melhor]


def etapa_pelo_status(texto_ficha):
    """Rótulo curto do primeiro passo aberto da seção Status. 'Concluída' se todos estão marcados."""
    sec = secao(texto_ficha, "Status")
    abertos = [ln for ln in sec.splitlines() if re.match(r"^\s*[-*]\s*\[ \]", ln)]
    if not abertos:
        return "Concluída" if re.search(r"\[[xX]\]", sec) else "a confirmar"
    t = re.sub(r"^\s*[-*]\s*\[ \]\s*", "", abertos[0]).strip()
    m = re.search(r"Semana\s*([1-5])", t)
    if m and not t.lower().startswith(("pré", "pos", "pós")):
        return ETAPAS_SEMANA[int(m.group(1))]
    for r in ROTULOS_STATUS:
        if sem_acento(t).startswith(sem_acento(r)):
            return r
    t = re.split(r":| realizad[oa]| e mensagem| · data| \(", t)[0].strip(" ·")
    return t[:40] or "a confirmar"


def secao(texto, titulo):
    texto = re.sub(r"(?s)<!--.*?-->", "", texto)
    alvo = sem_acento(titulo)
    dentro, linhas = False, []
    for ln in texto.splitlines():
        if re.match(r"^#{2,}\s+", ln):
            dentro = bool(re.match(r"^##\s+(?!#)", ln)) and sem_acento(re.sub(r"^##\s+", "", ln)).startswith(alvo)
            continue
        if dentro:
            linhas.append(ln)
    return "\n".join(linhas)


# ---------- ficha e registro ----------

def yaml_da_ficha(texto):
    m = re.match(r"﻿?---\s*\n(.*?)\n---\s*(?:\n|$)", texto, re.S)
    dados = {}
    if m:
        for ln in m.group(1).splitlines():
            k = re.match(r"^([A-Za-z_][\w-]*)\s*:\s*(.*)$", ln)
            if k:
                dados[k.group(1).lower()] = k.group(2).strip().strip("\"'").strip()
    return dados


def nome_do_cliente(pasta):
    return re.sub(r"^\s*\d+\.\s*", "", Path(pasta).name).strip()


def achar_ficha(pasta):
    pasta = Path(pasta)
    candidatas = [pasta / f"{nome_do_cliente(pasta)}.md"] + sorted(pasta.glob("*.md"))
    for c in candidatas:
        if c.is_file():
            try:
                if "cliente" in yaml_da_ficha(c.read_text(encoding="utf-8-sig")):
                    return c
            except Exception:
                continue
    return None


def caminho_registro(pasta_cliente):
    return Path(pasta_cliente) / PASTA_REGISTRO / "registro.md"


def texto_do_modelo(pasta_cliente):
    """Texto de modelos/registro-interno.md com o nome do cliente, ou None se o modelo não existe."""
    try:
        return MODELO_REGISTRO.read_text(encoding="utf-8-sig").replace("{{NOME}}", nome_do_cliente(pasta_cliente))
    except OSError:
        return None


def _celula(s):
    return re.sub(r"\s+", " ", str(s)).replace("|", "/").strip()


def minutos_txt(segundos):
    """Minutos com uma casa e vírgula ("0,3"): sessão curta não vira 0 e a soma do relatório não perde segundos."""
    return f"{segundos / 60:.1f}".replace(".", ",")


def montar_linha(sessao_id, dados, etapa, observacao):
    t = dados["tokens"]
    ini = dados["inicio"].astimezone() if dados["inicio"] else None
    campos = [sessao_id[:8], ini.strftime("%d/%m/%Y") if ini else "não medido", etapa,
              texto_modelos(dados["modelos"]), t["in"], t["out"], t["cl"], t["cc"],
              minutos_txt(dados["duracao_s"]), minutos_txt(dados["ativa_s"]),
              texto_ferramentas(dados["ferramentas"]), observacao]
    return "| " + " | ".join(_celula(c) for c in campos) + " |"


def observacao_da_sessao(dados, outros_clientes, semanas_extra):
    partes = []
    if outros_clientes:
        partes.append("sessão também mexeu em " + ", ".join(outros_clientes) +
                      "; tokens e duração são da sessão inteira, contados uma vez no total geral")
    if semanas_extra:
        partes.append("também mexeu em " + ", ".join(semanas_extra))
    if dados["subagentes"]:
        partes.append(f"inclui {dados['subagentes']} subagente(s)")
    return "; ".join(partes)


def ler_linhas_uso(texto_registro):
    """Linhas da tabela de uso medido do registro: lista de dicts com as COLUNAS."""
    sec = secao(texto_registro, "Medição")
    linhas = []
    cab_visto = False
    for ln in sec.splitlines():
        s = ln.strip()
        if not s.startswith("|"):
            if cab_visto and s:
                break
            continue
        cel = [c.strip() for c in s.strip("|").split("|")]
        if not cab_visto:
            if len(cel) >= len(COLUNAS) and cel[0] == "Sessão" and cel[1] == "Data":
                cab_visto = True
            continue
        if re.fullmatch(r"[\s:|-]+", s):
            continue
        if len(cel) >= len(COLUNAS) and cel[0]:
            linhas.append(dict(zip(COLUNAS, cel)))
    return linhas


def aplicar_linha(texto, sessao_id, linha):
    """Devolve o texto do registro com a linha da sessão gravada (nova ou atualizada). Não muda nada além disso."""
    nl = "\r\n" if "\r\n" in texto else "\n"
    linhas = texto.split(nl)
    # limites da seção Medição (título '## Medição' até o próximo '## ')
    ini = fim = None
    for i, ln in enumerate(linhas):
        if re.match(r"^##\s+(?!#)", ln):
            if ini is None and sem_acento(re.sub(r"^##\s+", "", ln)).startswith("medicao"):
                ini = i
            elif ini is not None:
                fim = i
                break
    if ini is None:
        return None  # registro sem a seção Medição: não inventa seção
    if fim is None:
        fim = len(linhas)
    chave = sessao_id[:8]
    # procura a tabela de uso medido dentro da seção
    cab = None
    for i in range(ini, fim):
        c = [x.strip() for x in linhas[i].strip().strip("|").split("|")]
        if linhas[i].lstrip().startswith("|") and len(c) >= len(COLUNAS) and c[0] == "Sessão" and c[1] == "Data":
            cab = i
            break
    if cab is None:
        fim_conteudo = fim
        while fim_conteudo > ini + 1 and not linhas[fim_conteudo - 1].strip():
            fim_conteudo -= 1
        bloco = ["", MARCA_TABELA, TITULO_TABELA, "", CABECALHO, SEPARADOR, linha]
        linhas[fim_conteudo:fim_conteudo] = bloco
        return nl.join(linhas)
    i = cab + 2
    ultima = cab + 1
    while i < fim and linhas[i].lstrip().startswith("|"):
        c = [x.strip() for x in linhas[i].strip().strip("|").split("|")]
        if c and c[0] == chave:
            if linhas[i] == linha:
                return texto
            linhas[i] = linha
            return nl.join(linhas)
        ultima = i
        i += 1
    linhas.insert(ultima + 1, linha)
    return nl.join(linhas)


def gravar_registro(registro, novo_texto, bom):
    registro.parent.mkdir(parents=True, exist_ok=True)
    tmp = registro.with_name(registro.name + ".uso.tmp")
    dados = novo_texto.encode("utf-8")
    if bom:
        dados = b"\xef\xbb\xbf" + dados
    tmp.write_bytes(dados)
    os.replace(tmp, registro)


# ---------- orquestração ----------

def planejar(transcript, session_id, raiz, prazo_s=PRAZO_PADRAO):
    """[(registro, linha, cliente)] que seriam gravadas. Lista vazia se a sessão não mexeu em cliente."""
    transcript = Path(transcript)
    if not transcript.is_file():
        return []
    sid = session_id or transcript.stem
    dados = ler_sessao(transcript, prazo_s)
    if not dados["mensagens"]:
        return []
    mexidos = clientes_mexidos(dados["textos"], pastas_de_clientes(raiz))
    resultado = []
    nomes = {p: nome_do_cliente(p) for p in mexidos}
    for pasta, contagem in mexidos.items():
        ficha = achar_ficha(pasta)
        if ficha is None:
            continue
        texto = ficha.read_text(encoding="utf-8-sig")
        etapa = etapa_pela_pasta(contagem) or etapa_pelo_status(texto)
        outros = [n for p, n in nomes.items() if p != pasta]
        semanas = [ETAPAS_SEMANA[int(re.match(r"(\d)", s).group(1))] for s in contagem
                   if re.match(r"^[1-5]\.", s)]
        extras = sorted({s for s in semanas if s != etapa})
        linha = montar_linha(sid, dados, etapa, observacao_da_sessao(dados, outros, extras))
        resultado.append((caminho_registro(pasta), linha, nomes[pasta]))
    return resultado


def medir(transcript, session_id, raiz, estado=None, prazo_s=PRAZO_PADRAO, gravar=True):
    """Chamada do gatilho. Devolve a lista de registros atualizados. Nunca levanta. `estado` é um dict que o gatilho
    guarda: evita reler um histórico que não mudou desde a última parada."""
    try:
        transcript = Path(transcript)
        if not transcript.is_file():
            return []
        st = transcript.stat()
        sid = session_id or transcript.stem
        marca = [st.st_size, st.st_mtime_ns]
        if estado is not None:
            if estado.get(sid[:8]) == marca:
                return []
        planos = planejar(transcript, sid, raiz, prazo_s)
        atualizadas = []
        for registro, linha, _cliente in planos:
            if not gravar:
                atualizadas.append(registro)
                continue
            if registro.is_file():
                bruto = registro.read_bytes()
                bom = bruto.startswith(b"\xef\xbb\xbf")
                texto = bruto.decode("utf-8-sig", "replace")
            else:
                texto, bom = texto_do_modelo(registro.parent.parent), False
                if texto is None:
                    continue
            novo = aplicar_linha(texto, sid, linha)
            if novo is None or (novo == texto and registro.is_file()):
                continue
            gravar_registro(registro, novo, bom)
            atualizadas.append(registro)
        if estado is not None:
            estado[sid[:8]] = marca
        return atualizadas
    except Prazo as e:
        sys.stderr.write(f"ee-trieme medicao: {e}; sem gravar nesta parada\n")
    except Exception as e:
        sys.stderr.write(f"ee-trieme medicao: {type(e).__name__}: {e}\n")
    return []


def main():
    ap = argparse.ArgumentParser(description="Mede o uso de uma sessão do Claude Code e grava no registro interno do cliente.")
    ap.add_argument("historico", help="arquivo .jsonl da sessão")
    ap.add_argument("raiz", help="pasta EE (a que tem Clientes/)")
    ap.add_argument("--sessao", help="id da sessão (padrão: nome do arquivo)")
    ap.add_argument("--gravar", action="store_true", help="grava no registro; sem isso só mostra")
    a = ap.parse_args()
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    sid = a.sessao or Path(a.historico).stem
    try:
        planos = planejar(a.historico, sid, a.raiz, prazo_s=120)
    except Prazo as e:
        print(f"ERRO {e}")
        return 1
    if not planos:
        print("A sessão não mexeu em nenhum cliente de Clientes/.")
        return 0
    for registro, linha, cliente in planos:
        print(f"Cliente: {cliente}\nRegistro: {registro}\n{CABECALHO}\n{SEPARADOR}\n{linha}\n")
    if a.gravar:
        medir(a.historico, sid, a.raiz, prazo_s=120)
        print("Gravado.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
