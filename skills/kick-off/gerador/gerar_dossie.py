"""Gera o Registro do Kickoff (DOCX, vai ao cliente depois da reunião) a partir de registro.json.

Uso:
    python gerar_dossie.py <registro.json> <pasta_de_saida> --consultor "<nome>" --cargo "<cargo>"

Tipos de bloco aceitos em cada seção: p (parágrafo), nota (texto menor), b (bullets;
item pode ser ["Rótulo: ", "texto"]), h (subtítulo), tab (tabela com cab/linhas/larg),
call (destaque com lbl/t). Ver modelo-registro.json.

Em qualquer texto do JSON, {consultor}, {consultor_nome} e {consultor_cargo} são trocados
pelos argumentos --consultor e --cargo (userConfig do plugin).
Arquivo gerado: o campo "arquivo" do JSON, ou registro-kickoff-<slug>.docx.
O script nunca grava dentro da pasta do pacote.
"""
import sys
sys.dont_write_bytecode = True
import argparse, json
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[3]  # skills/kick-off/gerador/ -> raiz do pacote
sys.path.insert(0, str(RAIZ / "scripts"))
from docx_common import *  # noqa: E402,F403


def gerar(D, out):
    nome = D["cliente"]
    d = new_doc()
    para(d, "TRIEME & CO", 10, True, GOLD, after=0)
    para(d, "V4 Company · Estruturação Estratégica", 9, False, GRAY, after=14)
    para(d, D.get("titulo", "Registro do Kickoff"), 25, True, INK, DISPLAY, after=2)
    para(d, D.get("subtitulo", f"{nome} · Reunião de abertura"), 13, False, GOLD, DISPLAY, after=12)
    table(d, ["Item", "Detalhe"], D["meta"], [5.2, 11.4])
    h2(d, "Sobre este documento")
    for t in D["sobre"]: para(d, t)

    for n, sec in enumerate(D["secoes"], 1):
        h1(d, f"{n}. {sec['titulo']}")
        for blk in sec["blocos"]:
            k = blk["tipo"]
            if k == "p": para(d, blk["t"])
            elif k == "nota": para(d, blk["t"], 9.5, True, GRAY)
            elif k == "b": bullets(d, [tuple(x) if isinstance(x, list) else x for x in blk["itens"]])
            elif k == "h":
                p = para(d, blk["t"], 11, True, GOLD, before=6, after=3); p.paragraph_format.keep_with_next = True
            elif k == "tab": table(d, blk["cab"], blk["linhas"], blk.get("larg"))
            elif k == "call": callout(d, blk["lbl"], blk["t"])

    footer(d, D.get("rodape", f"Trieme & Co · V4 Company · Registro do Kickoff · {nome}"))
    txt = "\n".join(p.text for p in d.paragraphs) + "\n".join(c.text for t in d.tables for r in t.rows for c in r.cells)
    assert TRAVESSAO not in txt, "travessão encontrado"
    d.save(out)
    return out


def main():
    console_utf8()
    ap = argparse.ArgumentParser(description="Gera o Registro do Kickoff em DOCX.")
    ap.add_argument("registro", help="registro.json")
    ap.add_argument("saida", help="pasta de saída (a pasta 1. Kick-Off do cliente)")
    argumentos_do_consultor(ap)
    a = ap.parse_args()
    saida = exigir_fora_do_pacote(a.saida)
    cons = consultor_dos_args(a)
    D = aplicar_consultor(json.load(open(a.registro, encoding="utf-8")), cons)
    saida.mkdir(parents=True, exist_ok=True)
    print(gerar(D, str(saida / D.get("arquivo", f"registro-kickoff-{D['slug']}.docx"))))


if __name__ == "__main__":
    main()
