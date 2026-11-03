"""Gera o HTML do Kickoff (a pauta que o cliente recebe) a partir de um JSON de conteúdo.

Uso:
    python gerar_kickoff.py <conteudo.json> <pasta_de_saida> [--docx]
            --consultor "<nome>" --cargo "<cargo>" [--foto <arquivo>]

Saída: kickoff-<slug>.html. O DOCX do deck de perguntas só sai com --docx e não vai ao cliente
(o que o cliente recebe do Kickoff é o HTML da pauta e o Registro do Kickoff, de gerar_dossie.py).

O CSS, o logo e o script de navegação vêm do HTML de referência em referencias/layout/ (layout e
componentes), localizados por marcadores, não por número de linha. O consultor vem dos argumentos
--consultor, --cargo e --foto (userConfig do plugin); sem nome, o texto sai neutro, com aviso.
O script nunca grava dentro da pasta do pacote. Ver README.md e modelo-conteudo.json.
"""
import sys
sys.dont_write_bytecode = True
import argparse, json, os, re
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[3]  # skills/kick-off/gerador/ -> raiz do pacote
sys.path.insert(0, str(RAIZ / "scripts"))
from docx_common import *  # noqa: E402,F403

REF = RAIZ / "referencias" / "layout" / "kickoff.html"
REF_NOME = "Cliente"

EXTRA_CSS = """
/* rótulos de público em grupos (ex.: quem decide x quem usa) */
.pub-sub{font-family:var(--mono); font-size:11px; text-transform:uppercase; letter-spacing:.1em; color:var(--gray); margin:14px 0 4px;}
#bloco-design .quad:hover .pub-sub{color:var(--black);}
/* palavras-chave em negrito nas perguntas e nos cards (leitura no relance) */
.quad li b, .field-card .d b, .lede b{font-weight:700;}
/* "Para:" no topo do quadro: o que a resposta permite construir */
.quad .proposito{font-size:13px; color:var(--gray); line-height:1.5; margin:-2px 0 6px;}
.quad .proposito b{font-family:var(--mono); font-size:10px; text-transform:uppercase; letter-spacing:.08em; color:var(--red); font-weight:600; margin-right:4px;}
.quad:hover .proposito{color:var(--black);}
/* fechamento enxuto: spoiler do próximo encontro */
.spoiler{font-family:var(--display); font-size:clamp(21px,2.6vw,34px); font-weight:700; line-height:1.15; max-width:980px; margin:14px 0 4px;}
.spoiler .accent{color:var(--red);}
.flowchain .fc.done{opacity:.55;}
/* termos desta tela: glossário discreto de siglas e nomenclaturas do mercado do cliente */
.glossario{align-self:flex-start; margin-top:14px; padding-top:8px; border-top:1px dashed var(--line); font-size:12.5px; color:var(--gray); line-height:1.55; max-width:1100px;}
.glossario .lbl{font-family:var(--mono); font-size:10px; text-transform:uppercase; letter-spacing:.1em; color:var(--red); margin-right:8px;}
.glossario b{color:var(--white); font-weight:600;}
/* selo e faixa de pausa no tamanho do conteúdo (section é flex em coluna e esticava os dois) */
.live-fill,.pausa{align-self:flex-start;}
"""

SINO = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 8a6 6 0 0 0-12 0c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.7 21a2 2 0 0 1-3.4 0"/></svg>'


def extrair_referencia(nome_cliente):
    if not REF.is_file():
        sys.exit(f"ERRO: HTML de referência não encontrado: {REF}")
    src = REF.read_text(encoding="utf-8")
    head = limpar_referencia(src[: src.index("</head>") + len("</head>")])
    head = re.sub(r"<title>.*?</title>", f"<title>Kickoff · {nome_cliente}</title>", head)
    if ".live-fill,.pausa{align-self" not in head:
        head = head.replace("</style>", EXTRA_CSS + "</style>")
    else:
        head = head.replace("</style>", EXTRA_CSS.split("/* selo")[0] + "</style>")
    chrome = re.search(r'<div class="chrome">.*?</div></div>', src, re.S).group(0)
    chrome = chrome.replace(f"<b>{REF_NOME}</b>", f"<b>{nome_cliente}</b>")
    # decoração do hero (ex.: marca d'água .v4-mark): tudo entre a abertura da section e o .hero-top
    hero = re.search(r'<section class="hero">(.*?)<div class="hero-top', src, re.S).group(1).strip()
    script = src[src.index("<script>"):]
    return head, chrome, hero, script


def pausa(t): return f'<div class="pausa r">{SINO}<b>Anotando</b><span>{t}</span></div>'
def gancho(t, lbl="Ao fechar o bloco", cls="gancho r"): return f'<div class="{cls}"><b>{lbl}</b><span>{t}</span></div>'
def quad(h, qs, extra="", para=""):
    p = f'<div class="proposito"><b>Para:</b> {para}</div>' if para else ""
    return f'<div class="quad"><h4>{h}</h4>{p}<ul>' + "".join(f"<li>{q}</li>" for q in qs) + f"</ul>{extra}</div>"
def field(b, k, v, d): return f'<div class="field-card"><div class="badge">{b}</div><div class="body"><div class="k">{k}</div><div class="v">{v}</div><div class="d">{d}</div></div></div>'
def glossario(itens):
    if not itens: return ""
    return '<div class="glossario r"><span class="lbl">Termos desta tela</span>' + " · ".join(f"<b>{t}</b>: {d}" for t, d in itens) + "</div>"
def chips(xs): return '<div class="chips-rot">' + "".join(f'<span class="chip">{x}</span>' for x in xs) + "</div>"

BLOCOS = [("marketing", "03 · Perguntas de marketing", "bloco-tecnicas"),
          ("comerciais", "04 · Perguntas comerciais", "bloco-comerciais"),
          ("metas", "05 · Metas financeiras", "bloco-metas")]


def gerar_html(C, out, cons):
    nome = C["cliente"]
    head, chrome, hero_deco, script = extrair_referencia(nome)
    consultor = tag_consultor_html(cons)
    body = [f'''<body>
{chrome}
<div class="navdots" id="navdots"></div>
<div class="scroller">

<section class="hero">{hero_deco}
  <div class="hero-top r"><div>{nome} · Estruturação Estratégica</div><div>Trieme &amp; Co</div></div>
  <div>
    <div class="hero-tag r">Kickoff · Semana 1</div>
    <h1 class="h-xl r r2">{nome.upper()}</h1>
    <p class="lede r r3" style="margin-top:18px;">{C["hero_lede"]}</p>
    <div class="hero-meta">''' + "".join(f'<div class="m r r{i+2}"><div class="k">{k}</div><div class="v">{v}</div></div>' for i, (k, v) in enumerate(C["hero_meta"])) + f'''</div>
  </div>
  {consultor}
  <div class="scrollcue r r5">role para começar ↓</div>
</section>

<section><div class="noise"></div>
  <div class="eyebrow r">Como vai funcionar</div>
  <h2 class="h-l r r2">O que é o Kickoff</h2>
  <p class="lede r r3" style="margin-top:14px;">{C["oque_lede"]}</p>
  <div class="grid g3 r r3" style="margin-top:22px;">''' + "".join(f'<div class="cell"><div class="k">{k}</div><div class="d">{d}</div></div>' for k, d in C["semanas_grid"]) + '''</div>
</section>

<section><div class="noise"></div>
  <div class="eyebrow r">Como vai funcionar</div>
  <h2 class="h-l r r2">Roteiro da reunião</h2>
  <p class="lede r r2" style="margin-top:12px;">Cada bloco abre com uma pergunta e fecha com o que ouvimos e para onde isso vai no projeto.</p>
  <div class="agenda-solo r r3" style="margin-top:22px;">''' + "".join(f'<div class="item"><div class="name">{n}</div><div class="time">{t}</div></div>' for n, t in C["roteiro"]) + '''</div>
  <div class="total">Estimativa da reunião: 1h30</div>
</section>
''']

    d = C["dores"]
    body.append(f'''<section id="bloco-dores"><div class="noise"></div>
  <div class="eyebrow r">01 · Problemas reais e dores</div>
  <div class="live-fill r">Estamos ao vivo</div>
  <h2 class="pergunta-central r r2" style="margin:8px 0 10px;">Qual é a sua dor hoje?</h2>
  <p class="lede r r2" style="margin:0 0 24px;">Aquela que você leva para o travesseiro e não conta para ninguém, às vezes nem para o vendedor da V4. Abre aqui que eu vou te ajudar a resolver.</p>
  <div class="grid g2 r r3">{"".join(quad(h, q) for h, q in d["quads"])}</div>
  {gancho(d["gancho"])}
  {pausa(d["pausa"])}
</section>
''')

    m = C["mapeado"]
    body.append(f'''<section id="bloco-dados"><div class="noise"></div>
  <div class="eyebrow r">02 · O que já mapeamos</div>
  <div class="abertura-capitulo r">{m["abertura"]}</div>
  <div class="grid g3 r r2" style="margin-top:14px;">{"".join(field(*f) for f in m["fields"])}</div>
  {pausa(m["pausa"])}
</section>
''')

    for key, eyebrow, gid in BLOCOS:
        b = C[key]
        ab = f'<div class="abertura-capitulo r">{b["abertura"]}</div>' if b.get("abertura") else ""
        body.append(f'''<section id="{gid}"><div class="noise"></div>
  <div class="eyebrow r">{eyebrow}</div>
  <div class="live-fill r">Estamos ao vivo</div>
  {ab}
  <div class="grid g2 r r2" style="margin-top:8px;">{"".join(quad(x[0], x[1], para=(x[2] if len(x) > 2 else "")) for x in b["quads"])}</div>
  {gancho(b["gancho"])}
  {pausa(b["pausa"])}
  {glossario(b.get("glossario"))}
</section>
''')

    g = C["design"]
    publico = '<div class="quad"><h4>Público</h4>' + "".join((f'<div class="pub-sub">{t}</div>' if t else "") + chips(xs) for t, xs in g["publico"]) + "</div>"
    conf = f'<div class="def" style="margin-top:10px;">{g["design_conf"]}</div>' if g.get("design_conf") else ""
    body.append(f'''<section id="bloco-design"><div class="noise"></div>
  <div class="eyebrow r">06 · Concorrentes, público e design</div>
  <div class="live-fill r">Estamos ao vivo</div>
  <div class="grid g2 r r2" style="margin-top:8px;">
    {quad("Concorrentes", g["concorrentes"])}
    {publico}
    {quad("Design", g["design"], conf)}
    {quad("Como receber as informações", g["receber"])}
  </div>
  {gancho(g["gancho"])}
  {pausa(g["pausa"])}
  {glossario(g.get("glossario"))}
</section>
''')

    f = C["fechamento"]
    if f.get("modo") == "spoiler":
        # fechamento enxuto: um slide só, com spoiler do próximo encontro e as 5 etapas (próximo encontro em destaque)
        def fc(i, k, h, p):
            if i == 0:
                return f'<div class="fc done"><div class="k">Concluído hoje</div><h4>{h}</h4><p>{p}</p></div>'
            if i == 1:
                return f'<div class="fc now"><div class="k">Próximo encontro · {k}</div><h4>{h}</h4><p>{p}</p></div>'
            return f'<div class="fc"><div class="k">{k}</div><h4>{h}</h4><p>{p}</p></div>'
        body.append(f'''<section id="bloco-fechamento"><div class="noise"></div>
  <div class="eyebrow r">Fechamento</div>
  <h2 class="h-l r r2">O que vem a seguir</h2>
  <p class="spoiler r r2">{f["spoiler"]}</p>
  <p class="lede r r3" style="margin:6px 0 22px;">{f["spoiler_lede"]}</p>
  <div class="flowchain r r3">''' + '<div class="ar">→</div>'.join(fc(i, k, h, p) for i, (k, h, p) in enumerate(C["cronograma"])) + f'''</div>
  {glossario(C.get("cronograma_glossario"))}
  <div class="foot">{f.get("compromisso", "")}</div>
</section>

</div>''')
    else:
        body.append(f'''<section><div class="noise"></div>
  <div class="eyebrow r">Fechamento</div>
  <h2 class="h-l r r2">O que já sabemos e o que vem a seguir</h2>
  <p class="lede r r3" style="margin-top:10px;">{f["lede"]}</p>
  {pausa(f["validacao"]) if f.get("validacao") else ""}
  {gancho(f["gancho"], "A seguir", "gancho r r4")}
</section>

<section><div class="noise"></div>
  <div class="eyebrow r">Próximos passos</div>
  <h2 class="h-l r r2">Cronograma da Estruturação Estratégica</h2>
  <div class="flowchain r r3" style="margin-top:22px;">''' + '<div class="ar">→</div>'.join(f'<div class="fc{" now" if i == 0 else ""}"><div class="k">{k}</div><h4>{h}</h4><p>{p}</p></div>' for i, (k, h, p) in enumerate(C["cronograma"])) + f'''</div>
  {glossario(C.get("cronograma_glossario"))}
  <div class="foot">{C.get("rodape", assinatura(cons, com_marca=False) + " · Próximo encontro: Pesquisa de Mercado (Semana 2)")}</div>
</section>

</div>''')

    corpo = "\n".join(body)
    assert TRAVESSAO not in corpo, "travessão encontrado no conteúdo"
    open(out, "w", encoding="utf-8").write(head + "\n" + corpo + "\n" + script)
    return out


def gerar_docx(C, out, cons):
    P, nome = C["prosa"], C["cliente"]
    d = new_doc()
    para(d, "KICKOFF · SEMANA 1 · ESTRUTURAÇÃO ESTRATÉGICA", 10, True, GOLD, after=2)
    para(d, nome.upper(), 26, True, INK, DISPLAY, after=4)
    para(d, "Reunião de abertura da Estruturação Estratégica. Confirmação do que já sabemos, levantamento das dores reais, perguntas de marketing, comerciais e metas, e alinhamento do cronograma das 5 semanas.", 12, False, GRAY, after=6)
    para(d, assinatura(cons), 9.5, True, BRONZE, after=6)
    table(d, [k for k, _ in C["hero_meta"]], [[v for _, v in C["hero_meta"]]])
    rule(d)

    h1(d, "Como vai funcionar: o que é o Kickoff")
    for t in P["oque"]: para(d, t)
    table(d, ["Semana", "Conteúdo"], [[k.replace("Semana ", ""), v] for k, v in C["semanas_grid"]], [6, 10.6])
    h2(d, "Roteiro da reunião"); para(d, P["roteiro"])
    table(d, ["Bloco", "Tempo"], C["roteiro"], [12, 4.6])

    def bloco(title, intro, b):
        h1(d, title)
        for t in intro: para(d, t)
        for x in b["quads"]:
            label(d, x[0])
            if len(x) > 2 and x[2]: para(d, "Para: " + x[2], 9.5, False, GRAY, italic=True, after=2)
            bullets(d, x[1])
        callout(d, "Ao fechar o bloco", b["gancho"]); callout(d, "Anotando", b["pausa"])
        for t, df in b.get("glossario", []):
            p = para(d, after=2); run(p, t + ": ", 9.5, True, BRONZE); run(p, df, 9.5, False, GRAY)

    h1(d, "01 · Problemas reais e dores")
    para(d, "Qual é a sua dor hoje?", 12.5, True)
    para(d, "Aquela que você leva para o travesseiro e não conta para ninguém, às vezes nem para o vendedor da V4. Abre aqui que eu vou te ajudar a resolver.", italic=True)
    for t in P["dores"]: para(d, t)
    for h, qs in C["dores"]["quads"]:
        label(d, h); bullets(d, qs)
    callout(d, "Ao fechar o bloco", C["dores"]["gancho"]); callout(d, "Anotando", C["dores"]["pausa"])

    m = C["mapeado"]
    h1(d, "02 · O que já mapeamos"); para(d, m["abertura"])
    table(d, ["Campo", "Valor", "Detalhe"], [[k, v, de] for _, k, v, de in m["fields"]], [3.4, 3.8, 9.4])
    for t in P["mapeado"]: para(d, t)
    callout(d, "Anotando", m["pausa"])

    for key, eyebrow, _ in BLOCOS:
        bloco(eyebrow, P[key], C[key])

    g = C["design"]
    h1(d, "06 · Concorrentes, público e design")
    for t in P["design"]: para(d, t)
    label(d, "Concorrentes"); bullets(d, g["concorrentes"])
    label(d, "Público")
    for t, xs in g["publico"]:
        p = para(d, after=3)
        if t: run(p, t + ": ", 10.5, True)
        run(p, ", ".join(xs).lower().capitalize() + ". Campos a preencher ao vivo com o cliente.")
    label(d, "Design"); bullets(d, g["design"])
    if g.get("design_conf"): para(d, g["design_conf"], 10, False, GRAY, italic=True)
    label(d, "Como receber as informações"); bullets(d, g["receber"])
    callout(d, "Ao fechar o bloco", g["gancho"]); callout(d, "Anotando", g["pausa"])

    F = C["fechamento"]
    if F.get("modo") == "spoiler":
        h1(d, "Fechamento: o que vem a seguir")
        para(d, re.sub(r"<[^>]+>", "", F["spoiler"]), 12.5, True)
        para(d, F["spoiler_lede"])
        if F.get("compromisso"): callout(d, "Combinado", F["compromisso"])
        h2(d, "Cronograma da Estruturação Estratégica")
    else:
        h1(d, "Fechamento: o que já sabemos e o que vem a seguir")
        para(d, P["fechamento"]); para(d, F["lede"])
        if F.get("validacao"): callout(d, "Validação", F["validacao"])
        callout(d, "A seguir", F["gancho"])
        h1(d, "Próximos passos: cronograma da Estruturação Estratégica")
    table(d, ["Semana", "Etapa", "O que entrega"], [[k.replace("Estamos aqui · ", "") + (" (hoje)" if i == 0 else ""), h, p] for i, (k, h, p) in enumerate(C["cronograma"])], [3.2, 4.4, 9])
    for t, df in C.get("cronograma_glossario", []):
        p = para(d, after=2); run(p, t + ": ", 9.5, True, BRONZE); run(p, df, 9.5, False, GRAY)
    para(d, C.get("rodape", assinatura(cons, com_marca=False) + " · Próximo encontro: Pesquisa de Mercado (Semana 2)"), 9.5, True, BRONZE, before=8)
    footer(d, f"Trieme & Co · V4 Company · Kickoff {nome}")

    assert TRAVESSAO not in "\n".join(p.text for p in d.paragraphs), "travessão encontrado"
    d.save(out)
    return out


def main():
    console_utf8()
    ap = argparse.ArgumentParser(description="Gera o HTML do Kickoff (e o DOCX do deck com --docx).")
    ap.add_argument("conteudo", help="conteudo.json do Kickoff")
    ap.add_argument("saida", help="pasta de saída (a pasta 1. Kick-Off do cliente)")
    ap.add_argument("--docx", action="store_true", help="gera também o DOCX do deck (uso interno; não vai ao cliente)")
    argumentos_do_consultor(ap)
    a = ap.parse_args()
    saida = exigir_fora_do_pacote(a.saida)
    cons = consultor_dos_args(a)
    C = aplicar_consultor(json.load(open(a.conteudo, encoding="utf-8")), cons)
    saida.mkdir(parents=True, exist_ok=True)
    slug = C["slug"]
    print(gerar_html(C, str(saida / f"kickoff-{slug}.html"), cons))
    if a.docx:
        print(gerar_docx(C, str(saida / f"kickoff-{slug}.docx"), cons))
        print("AVISO: o DOCX do deck é de uso interno e não vai ao cliente.", file=sys.stderr)


if __name__ == "__main__":
    main()
