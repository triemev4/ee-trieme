"""Relatório de uso da EE (R15), para a banca: junta as linhas "Uso medido por sessão" da seção Medição dos registros
internos (<cliente>/_ensaios-internos/registro.md) de todos os clientes por etapa e por cliente (total, média por etapa, modelo). Só biblioteca padrão, lê os registros e não grava nada
na pasta EE.

Uso:
    python relatorio_uso.py <pasta EE> [--md relatorio-uso.md] [--csv relatorio-uso.csv]
Sem --md o Markdown sai na tela. O CSV (ponto e vírgula, UTF-8 com BOM, abre direto no Excel em português) traz uma
linha por sessão e cliente. Clientes sem linhas de uso entram só no aviso final.

Regras de leitura:
  - "Total" de tokens = entrada + saída + cache lido + cache criado.
  - Sessão que mexeu em dois clientes aparece nos dois (cada registro guarda a sessão inteira); o total geral conta a
    sessão uma vez, pelo id curto.
  - "Média por etapa" = total da etapa dividido pelo número de clientes que passaram por ela.
"""
import sys
sys.dont_write_bytecode = True
import argparse
import collections
import csv
import re
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import medir_uso as M  # noqa: E402

CAMPOS_TOKEN = ["Entrada", "Saída", "Cache lido", "Cache criado"]
ORDEM_ETAPAS = ["Pré-Kickoff", "Kick-Off", "Kickoff", "Pós-Kickoff", "Passagem da venda", "Pesquisa de Mercado",
                "Diagnóstico de Marketing", "Diagnóstico Comercial", "Entregáveis de criação", "Mesa",
                "Planejamento Estratégico + Entregáveis", "Encerramento"]


def inteiro(s):
    d = re.sub(r"[^\d]", "", str(s))
    return int(d) if d else 0


def minutos(s):
    """Minutos de uma célula: "0,3", "12" ou "12.5". Linha antiga (inteiro) continua valendo."""
    m = re.search(r"\d+(?:[.,]\d+)?", str(s))
    return float(m.group(0).replace(",", ".")) if m else 0.0


def carregar(raiz):
    """(linhas, clientes_sem_uso). Cada linha é um dict com cliente, sessão, etapa, modelo, números e observação."""
    linhas, sem_uso = [], []
    for pasta in M.pastas_de_clientes(raiz):
        registro = M.caminho_registro(pasta)
        if not registro.is_file() and M.achar_ficha(pasta) is None:
            continue
        nome = M.nome_do_cliente(pasta)
        achadas = M.ler_linhas_uso(registro.read_text(encoding="utf-8-sig")) if registro.is_file() else []
        if not achadas:
            sem_uso.append(nome)
        for d in achadas:
            r = {"Cliente": nome, "Sessão": d["Sessão"], "Data": d["Data"], "Etapa": d["Etapa"], "Modelo": d["Modelo"],
                 "Duração (min)": minutos(d["Duração (min)"]), "Ativa (min)": minutos(d["Ativa (min)"]),
                 "Ferramentas": d["Ferramentas"], "Observação": d["Observação"]}
            for c in CAMPOS_TOKEN:
                r[c] = inteiro(d[c])
            r["Total"] = sum(r[c] for c in CAMPOS_TOKEN)
            linhas.append(r)
    return linhas, sem_uso


def modelos_de(texto):
    """Nomes de modelo de uma célula 'opus-5-5 (high) + sonnet-5-5'."""
    return [re.sub(r"\s*\(.*?\)\s*$", "", p).strip() for p in texto.split(" + ") if p.strip()]


def modelo_principal(linhas):
    """Modelo mais usado (por saída) entre as sessões; o primeiro da célula é o de mais saída."""
    c = collections.Counter()
    for r in linhas:
        ms = modelos_de(r["Modelo"])
        if ms:
            c[ms[0]] += max(r["Saída"], 1)
    return ", ".join(m for m, _ in c.most_common(3)) or "não registrado"


def n(v):
    return f"{int(round(v)):,}".replace(",", ".")


def horas(min_):
    return f"{min_ / 60:.2f}".replace(".", ",")


def soma(linhas, chave):
    return sum(r[chave] for r in linhas)


def ordem_etapa(e):
    return (ORDEM_ETAPAS.index(e), e) if e in ORDEM_ETAPAS else (len(ORDEM_ETAPAS), e)


def tabela(cabecalho, linhas):
    out = ["| " + " | ".join(cabecalho) + " |", "|" + "---|" * len(cabecalho)]
    out += ["| " + " | ".join(str(c) for c in l) + " |" for l in linhas]
    return "\n".join(out)


def relatorio_md(linhas, sem_uso):
    if not linhas:
        txt = "# Uso da EE\n\nNenhuma linha de uso medido nos registros ainda."
        if sem_uso:
            txt += "\n\nClientes sem medição: " + ", ".join(sem_uso) + "."
        return txt
    # sessões únicas para o total geral
    unicas = {}
    for r in linhas:
        unicas.setdefault(r["Sessão"], r)
    clientes = sorted({r["Cliente"] for r in linhas})
    out = ["# Uso da EE (medição automática)", ""]
    out.append(f"{len(unicas)} sessão(ões) em {len(clientes)} cliente(s). Tokens totais (entrada, saída, cache lido e cache "
               f"criado): {n(soma(list(unicas.values()), 'Total'))}; saída: {n(soma(list(unicas.values()), 'Saída'))}. "
               f"Duração: {horas(soma(list(unicas.values()), 'Duração (min)'))} h no relógio, "
               f"{horas(soma(list(unicas.values()), 'Ativa (min)'))} h ativas. Sessão que mexeu em dois clientes conta uma vez aqui.")
    # por etapa
    por_etapa = collections.defaultdict(list)
    for r in linhas:
        por_etapa[r["Etapa"]].append(r)
    out += ["", "## Por etapa", ""]
    rows = []
    for e in sorted(por_etapa, key=ordem_etapa):
        ls = por_etapa[e]
        cl = len({r["Cliente"] for r in ls})
        rows.append([e, cl, len(ls), n(soma(ls, "Total")), n(soma(ls, "Saída")), horas(soma(ls, "Duração (min)")),
                     horas(soma(ls, "Ativa (min)")), n(soma(ls, "Total") / cl), horas(soma(ls, "Ativa (min)") / cl),
                     modelo_principal(ls)])
    out.append(tabela(["Etapa", "Clientes", "Sessões", "Tokens totais", "Saída", "Duração (h)", "Ativa (h)",
                       "Média por cliente (tokens)", "Média por cliente (h ativas)", "Modelo"], rows))
    # por cliente
    por_cliente = collections.defaultdict(list)
    for r in linhas:
        por_cliente[r["Cliente"]].append(r)
    out += ["", "## Por cliente", ""]
    rows = []
    for c in clientes:
        ls = por_cliente[c]
        et = len({r["Etapa"] for r in ls})
        rows.append([c, len(ls), et, n(soma(ls, "Total")), n(soma(ls, "Saída")), horas(soma(ls, "Duração (min)")),
                     horas(soma(ls, "Ativa (min)")), n(soma(ls, "Total") / et), modelo_principal(ls)])
    out.append(tabela(["Cliente", "Sessões", "Etapas", "Tokens totais", "Saída", "Duração (h)", "Ativa (h)",
                       "Média por etapa (tokens)", "Modelo"], rows))
    # cliente x etapa
    out += ["", "## Cliente por etapa", ""]
    rows = []
    for c in clientes:
        por = collections.defaultdict(list)
        for r in por_cliente[c]:
            por[r["Etapa"]].append(r)
        for e in sorted(por, key=ordem_etapa):
            ls = por[e]
            rows.append([c, e, len(ls), n(soma(ls, "Total")), n(soma(ls, "Saída")), horas(soma(ls, "Ativa (min)")),
                         modelo_principal(ls)])
    out.append(tabela(["Cliente", "Etapa", "Sessões", "Tokens totais", "Saída", "Ativa (h)", "Modelo"], rows))
    # por modelo (sessões, pelo modelo de mais saída)
    por_modelo = collections.defaultdict(list)
    for r in unicas.values():
        ms = modelos_de(r["Modelo"])
        por_modelo[ms[0] if ms else "não registrado"].append(r)
    out += ["", "## Por modelo (modelo de mais saída em cada sessão)", ""]
    rows = [[m, len(ls), n(soma(ls, "Total")), n(soma(ls, "Saída")), horas(soma(ls, "Ativa (min)"))]
            for m, ls in sorted(por_modelo.items(), key=lambda kv: -soma(kv[1], "Total"))]
    out.append(tabela(["Modelo", "Sessões", "Tokens totais", "Saída", "Ativa (h)"], rows))
    compartilhadas = [r for r in linhas if "sessão também mexeu em" in r["Observação"]]
    notas = []
    if compartilhadas:
        notas.append(f"{len({r['Sessão'] for r in compartilhadas})} sessão(ões) mexeram em mais de um cliente: "
                     "cada registro guarda a sessão inteira, então a soma por cliente passa do total geral.")
    if sem_uso:
        notas.append("Clientes sem linha de uso: " + ", ".join(sem_uso) + ".")
    if notas:
        out += ["", "## Notas", ""] + [f"- {x}" for x in notas]
    return "\n".join(out)


def gravar_csv(linhas, destino):
    cols = ["Cliente", "Sessão", "Data", "Etapa", "Modelo"] + CAMPOS_TOKEN + ["Total", "Duração (min)", "Ativa (min)",
                                                                                "Ferramentas", "Observação"]
    with open(destino, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(cols)
        for r in linhas:
            w.writerow([f"{r[c]:.1f}".replace(".", ",") if c in ("Duração (min)", "Ativa (min)") else r[c] for c in cols])


def main():
    ap = argparse.ArgumentParser(description="Relatório de uso da EE por etapa e por cliente.")
    ap.add_argument("raiz", help="pasta EE (a que tem Clientes/)")
    ap.add_argument("--md", help="grava o Markdown neste arquivo (padrão: tela)")
    ap.add_argument("--csv", help="grava o CSV (uma linha por sessão e cliente) neste arquivo")
    a = ap.parse_args()
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    raiz = Path(a.raiz)
    if not (raiz / "Clientes").is_dir():
        print(f"ERRO {raiz} não tem a pasta Clientes/")
        return 1
    linhas, sem_uso = carregar(raiz)
    md = relatorio_md(linhas, sem_uso)
    if a.md:
        Path(a.md).write_text(md + "\n", encoding="utf-8")
        print(f"Markdown em {a.md}")
    else:
        print(md)
    if a.csv:
        gravar_csv(linhas, a.csv)
        print(f"CSV em {a.csv}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
