"""Gera a Pesquisa de Mercado (HTML + DOCX) a partir de um JSON de conteúdo.

Uso:
    python gerar_pesquisa.py <conteudo.json> <pasta_de_saida> --consultor "<nome>" --cargo "<cargo>"
    python gerar_pesquisa.py <conteudo.json> --validar

O CSS, o logo, o monograma e o script de navegação vêm do HTML de referência em
referencias/layout/ (layout e componentes), localizados por marcadores, não por número de linha.
O consultor vem dos argumentos --consultor e --cargo (userConfig do plugin); sem nome, o texto
sai neutro, com aviso. O script nunca grava dentro da pasta do pacote.

Regra de fonte: toda tela com dado leva as fontes atreladas ao próprio tópico (`fontes` no JSON,
viram .fonte-rodape com link no HTML e "Fontes" com link no DOCX). O gerador recusa tela sem
fonte, exceto as marcadas com "sem_fonte": true (o fecho). Telas com "so_docx": true
ficam fora do HTML; abertura_docx:true entra após a capa, demais telas sob "Detalhe para consulta".
O modelo padrão usa esquema_pesquisa:2. JSON sem versão preserva o legado; campos novos
presentes seguem o mesmo contrato validado pela conferência. Ver modelo-pesquisa.json.
"""
import sys
sys.dont_write_bytecode = True
import argparse, json, math, os, re
from pathlib import Path
from urllib.parse import urlsplit

RAIZ = Path(__file__).resolve().parents[3]  # skills/pesquisa-mercado/gerador/ -> raiz do pacote
sys.path.insert(0, str(RAIZ / "scripts"))
from docx_common import *  # noqa: E402,F403
from preencher_molde import validar_dados
from conferir_pesquisa import conferir_estrutura

REF = RAIZ / "referencias" / "layout" / "pesquisa-mercado.html"
REF_NOME = "Cliente"

EXTRA_CSS = """
/* ===== gerar_pesquisa.py ===== */
/* selo e faixa de pausa no tamanho do conteúdo */
.live-fill,.pausa{align-self:flex-start;}
/* fontes atreladas ao tópico: links discretos no rodapé da tela */
.fonte-rodape a{color:inherit; text-decoration:underline dotted; text-underline-offset:2px;}
.fonte-rodape a:hover{color:var(--red);}
.fonte-rodape .sep{color:var(--gray-dim); margin:0 6px;}
/* termos desta tela: glossário discreto dos nossos termos */
.glossario{align-self:flex-start; margin-top:12px; font-size:14px; color:var(--gray); line-height:1.55; max-width:1100px;}
.glossario .lbl{font-family:var(--mono); font-size:10px; text-transform:uppercase; letter-spacing:.1em; color:var(--red); margin-right:8px;}
.glossario b{color:var(--white); font-weight:600;}
/* listas dentro dos cards */
.segcard ul{list-style:none; font-size:14.5px; color:var(--gray); line-height:1.65;}
.segcard ul li{padding:3px 0 3px 20px; position:relative;}
.segcard ul li::before{content:"➔"; position:absolute; left:0; color:var(--red);}
.segcard .fonte-card{margin-top:10px; font-family:var(--mono); font-size:10px; text-transform:uppercase; letter-spacing:.06em; color:var(--gray-dim);}
.cell .d b,.segcard p b,.lede b{color:var(--white); font-weight:600;}
/* barras de preço */
.barras{display:flex; flex-direction:column; gap:12px; max-width:1040px; margin-top:22px;}
.barra{display:grid; grid-template-columns:minmax(200px,300px) 1fr 92px; gap:16px; align-items:center;}
.barra .rot{font-size:14px; color:var(--gray); line-height:1.35;}
.barra .rot b{color:var(--white); font-weight:600;}
.barra .trilho{height:26px; background:var(--surface); border:1px solid var(--line); border-radius:6px; overflow:hidden;}
.barra .enc{height:100%; background:var(--gray-dim); border-radius:5px;}
.barra.dest .enc{background:var(--red);}
.barra .val{font-family:var(--display); font-weight:700; font-size:17px;}
.barra.dest .val{color:var(--red);}
@media(max-width:800px){.barra{grid-template-columns:1fr auto;} .barra .trilho{grid-column:1 / -1; grid-row:2;}}
/* frase de destaque (PUV) */
.frase{font-family:var(--display); font-size:clamp(20px,2.4vw,30px); font-weight:700; line-height:1.25; max-width:1000px; color:var(--white);}
.frase .accent{color:var(--red);}
.checklist div::before{content:"○"; color:var(--red); font-size:14px; margin-top:3px;}
.rtable td b{font-weight:600;}
/* faixa de amarração: pilar do escopo · dor do cliente · o que significa para o cliente */
.amarra{display:flex; flex-wrap:wrap; gap:8px 18px; margin:10px 0 4px; padding:10px 14px; border-left:3px solid var(--red); background:var(--surface); border-radius:0 8px 8px 0; font-size:14px; color:var(--gray); line-height:1.45; max-width:1200px;}
.amarra span b{font-family:var(--mono); font-size:10px; text-transform:uppercase; letter-spacing:.08em; color:var(--red); margin-right:6px; font-weight:600;}
.amarra span{flex:1 1 260px;}
/* ações do plano por horizonte: texto que o cliente lê, mínimo de 14 px (a referência usa 12,5) */
.ac li{font-size:14px;}
/* TAM, SAM e SOM: elipses à esquerda e valores à direita, para a tela caber na altura */
.conc-wrap-h{display:grid; grid-template-columns:minmax(260px,400px) 1fr; gap:32px; align-items:center; margin-top:14px;}
.conc-svg-h{max-width:400px; margin:0;}
.conc-wrap-h .pyr-legend{flex-direction:column; gap:10px;}
.conc-wrap-h .pyr-item{min-width:0;}
.conc-wrap-h .pyr-item .k{font-size:14px;}
.conc-wrap-h .pyr-item .v{font-size:clamp(18px,1.8vw,23px); margin-top:2px;}
.conc-wrap-h .pyr-item .d{margin-top:2px; line-height:1.45;}
.mercado-sintese{display:grid;grid-template-columns:1.15fr 1fr;gap:20px;align-items:start;margin-top:14px;}
.mercado-sintese .rtable{margin:0!important;}
.mercado-sintese p{font-size:14px;line-height:1.5;margin:0 0 12px;}
.mercado-sintese h3{font-size:16px;line-height:1.4;margin:0 0 6px;}
@media(max-width:860px){.conc-wrap-h{grid-template-columns:1fr;} .conc-svg-h{margin:0 auto;}}
@media(max-width:860px){.mercado-sintese{grid-template-columns:1fr;}}
"""

SINO = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 8a6 6 0 0 0-12 0c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.7 21a2 2 0 0 1-3.4 0"/></svg>'
CHECK = '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="var(--green)" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:-2px; margin-right:5px;"><polyline points="20 6 9 17 4 12"/></svg>'


def validar_conteudo(C):
    """Valida os dados de ambos os formatos em memória; não grava nem acessa a rede.

    ValueError sempre indica o caminho e o motivo objetivo. Textos livres não demonstram
    fonte, viabilidade ou qualidade estratégica por passarem aqui; seguem para as conferências.
    """
    def falha(cam, motivo):
        raise ValueError(f"{cam}: {motivo}")

    def objeto(v, cam):
        if not isinstance(v, dict):
            falha(cam, "esperado objeto")
        return v

    def texto(v, cam, vazio=False):
        if not isinstance(v, str) or (not vazio and not v.strip()):
            falha(cam, "esperado texto" + ("" if vazio else " não vazio"))
        if isinstance(v, str) and TRAVESSAO in v:
            falha(cam, "travessão não permitido no conteúdo")

    def lista(v, cam, minimo=0):
        if not isinstance(v, list) or len(v) < minimo:
            falha(cam, f"esperado lista com pelo menos {minimo} item(ns)")
        return v

    def textos(v, cam, minimo=0):
        for i, x in enumerate(lista(v, cam, minimo)):
            texto(x, f"{cam}[{i}]")

    def linhas(v, cam, tamanho, tipos=None, minimo=0):
        for i, linha in enumerate(lista(v, cam, minimo)):
            p = f"{cam}[{i}]"
            if not isinstance(linha, list) or len(linha) != tamanho:
                falha(p, f"esperado lista de {tamanho} campos")
            for j, x in enumerate(linha):
                if tipos is None or tipos[j] == "texto":
                    texto(x, f"{p}[{j}]", vazio=True)

    def flag(obj, chave, cam):
        if chave in obj and not isinstance(obj[chave], bool):
            falha(f"{cam}.{chave}", "esperado true ou false")

    def numero(v, cam, minimo=0):
        if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) or v < minimo:
            falha(cam, f"esperado número finito maior ou igual a {minimo}")

    objeto(C, "raiz")
    avisos = validar_dados(C)
    texto(C.get("cliente"), "cliente")
    texto(C.get("slug"), "slug")
    if not re.fullmatch(r"[a-z0-9-]+", C["slug"]):
        falha("slug", "use letras minúsculas sem acento, números e hífen")
    telas = lista(C.get("telas"), "telas", 1)
    ids = set()
    for i, s in enumerate(telas):
        objeto(s, f"telas[{i}]")
        if "id" in s:
            texto(s["id"], f"telas[{i}].id")
            if re.search(r"[\s#]", s["id"]) or s["id"] in ids:
                falha(f"telas[{i}].id", "identificador inválido ou duplicado")
            ids.add(s["id"])

    def fontes(fs, cam):
        linhas(fs, cam, 3, ("texto", "texto", "url"), 1)
        for i, (_, txt, url) in enumerate(fs):
            texto(txt, f"{cam}[{i}][1]")
            if url is not None:
                texto(url, f"{cam}[{i}][2]")
                if url.startswith("#"):
                    if url[1:] not in ids:
                        falha(f"{cam}[{i}][2]", f"referência local inexistente {url!r}")
                else:
                    try:
                        u = urlsplit(url)
                        valido = u.scheme in ("http", "https") and bool(u.hostname) and not re.search(r"[\s<>\"']", url)
                    except ValueError:
                        valido = False
                    if not valido:
                        falha(f"{cam}[{i}][2]", "URL inválida; use http(s) ou #id de tela existente")

    ponte = objeto(C.get("ponte"), "ponte")
    linhas(ponte.get("trilha"), "ponte.trilha", 2, minimo=1)
    for i, linha in enumerate(lista(ponte.get("colunas"), "ponte.colunas", 1)):
        cam = f"ponte.colunas[{i}]"
        if not isinstance(linha, list) or len(linha) != 2:
            falha(cam, "esperado [rótulo, lista de textos]")
        texto(linha[0], cam + "[0]")
        textos(linha[1], cam + "[1]")
    if "pausa" in ponte:
        texto(ponte["pausa"], "ponte.pausa", vazio=True)
    hero = objeto(C.get("hero"), "hero")
    for k in ("titulo", "lede"):
        texto(hero.get(k), "hero." + k)
    linhas(hero.get("meta"), "hero.meta", 2, minimo=1)
    fontes(hero.get("fontes"), "hero.fontes")
    for k in ("assinatura", "rodape"):
        if k in C:
            texto(C[k], k, vazio=True)

    def bloco(b, cam):
        objeto(b, cam)
        t = b.get("t")
        if not isinstance(t, str) or t not in {"lede", "abertura", "live", "cells", "cards", "tabela", "elipses", "barras", "layers", "explicador", "frase", "checklist", "gancho", "pausa", "plano", "proximos_passos"}:
            falha(cam + ".t", f"bloco desconhecido {t!r}")
        if "cols" in b and (isinstance(b["cols"], bool) or not isinstance(b["cols"], int) or b["cols"] not in (1, 2, 3, 4)):
            falha(cam + ".cols", "esperado inteiro de 1 a 4")
        if t in ("lede", "abertura", "gancho", "pausa", "frase") or (t == "live" and "texto" in b):
            texto(b.get("texto"), cam + ".texto")
        if t == "gancho":
            texto(b.get("lbl"), cam + ".lbl")
        if t == "frase":
            texto(b.get("rotulo"), cam + ".rotulo")
            if "tag" in b:
                texto(b["tag"], cam + ".tag", vazio=True)
        if t in ("layers", "elipses"):
            chave, tam = ("itens", 3) if t == "layers" else ("camadas", 4)
            linhas(b.get(chave), cam + "." + chave, tam, minimo=1)
            if t == "elipses" and len(b[chave]) != 3:
                falha(cam + ".camadas", "esperado exatamente três camadas (TAM, SAM e SOM)")
        if t == "cells":
            for i, linha in enumerate(lista(b.get("itens"), cam + ".itens", 1)):
                if not isinstance(linha, list) or len(linha) not in (3, 4):
                    falha(f"{cam}.itens[{i}]", "esperado [rótulo, valor, leitura, classe opcional]")
                for j, x in enumerate(linha):
                    texto(x, f"{cam}.itens[{i}][{j}]", vazio=True)
        if t == "cards":
            for i, c in enumerate(lista(b.get("itens"), cam + ".itens", 1)):
                p = f"{cam}.itens[{i}]"
                objeto(c, p)
                texto(c.get("tag"), p + ".tag")
                for k in ("h", "p", "fonte"):
                    if k in c:
                        texto(c[k], p + "." + k, vazio=True)
                if "ul" in c:
                    textos(c["ul"], p + ".ul")
                flag(c, "pos", p)
        if t == "tabela":
            textos(b.get("cab"), cam + ".cab", 1)
            linhas(b.get("linhas"), cam + ".linhas", len(b["cab"]))
        if t == "barras":
            linhas(b.get("itens"), cam + ".itens", 4, ("texto", "numero", "texto", "bool"), 1)
            for i, (_, v, _, destaque) in enumerate(b["itens"]):
                numero(v, f"{cam}.itens[{i}][1]")
                if not isinstance(destaque, bool):
                    falha(f"{cam}.itens[{i}][3]", "esperado true ou false")
            mx = max(linha[1] for linha in b["itens"])
            if "max" in b:
                numero(b["max"], cam + ".max")
                if b["max"] <= 0 or b["max"] < mx:
                    falha(cam + ".max", "precisa ser positivo e comportar todos os valores")
            elif mx <= 0:
                falha(cam + ".itens", "ao menos uma barra precisa ter valor positivo")
        if t == "checklist":
            textos(b.get("itens"), cam + ".itens", 1)
        if t == "explicador":
            texto(b.get("tag"), cam + ".tag")
            textos(b.get("ps"), cam + ".ps", 1)
        if t == "plano":
            avisos.append(cam + ": plano legado por horizonte; migre para proximos_passos")
            comece = []
            for h in ("h1", "h2", "h3"):
                for i, acao in enumerate(lista(b.get(h), cam + "." + h)):
                    p = f"{cam}.{h}[{i}]"
                    objeto(acao, p)
                    texto(acao.get("dor"), p + ".dor")
                    texto(acao.get("dono"), p + ".dono")
                    textos(acao.get("itens"), p + ".itens", 1)
                    flag(acao, "comece", p)
                    if acao.get("comece"):
                        if h != "h1":
                            falha(p + ".comece", "Comece aqui deve pertencer ao H1")
                        if acao.get("prazo_dias", 0) > 7:
                            falha(p + ".prazo_dias", "Comece aqui deve caber em sete dias")
                        comece.append(p)
            if len(comece) > 1:
                falha(comece[-1] + ".comece", "mantenha uma única primeira ação")

    for i, s in enumerate(telas):
        cam = f"telas[{i}]"
        texto(s.get("eyebrow"), cam + ".eyebrow")
        for k in ("h2", "pausa", "foot"):
            if k in s:
                texto(s[k], cam + "." + k, vazio=True)
        for k in ("so_docx", "sem_fonte", "abertura_docx"):
            flag(s, k, cam)
        if s.get("abertura_docx") and not s.get("so_docx"):
            falha(cam + ".abertura_docx", "abertura precisa de so_docx:true")
        if not s.get("sem_fonte") or s.get("fontes"):
            fontes(s.get("fontes"), cam + ".fontes")
        if "glossario" in s:
            linhas(s["glossario"], cam + ".glossario", 2)
        if "amarra" in s:
            am = objeto(s["amarra"], cam + ".amarra")
            for k in ("pilar", "dor", "cliente_texto"):
                texto(am.get(k), cam + ".amarra." + k)
            if "cliente" in am:
                texto(am["cliente"], cam + ".amarra.cliente")
        for j, b in enumerate(lista(s.get("blocos"), cam + ".blocos")):
            bloco(b, f"{cam}.blocos[{j}]")
    erros_novos = conferir_estrutura(C)
    if erros_novos:
        raise ValueError(erros_novos[0])
    return avisos


def extrair_referencia(nome_cliente):
    if not REF.is_file():
        sys.exit(f"ERRO: HTML de referência não encontrado: {REF}")
    src = REF.read_text(encoding="utf-8")
    head = limpar_referencia(src[: src.index("</head>") + len("</head>")])
    head = re.sub(r"<title>.*?</title>", f"<title>Pesquisa de Mercado · {nome_cliente}</title>", head)
    head = head.replace("</style>", EXTRA_CSS + "</style>", 1) if "fonte-rodape a{color:inherit" not in head else head
    chrome = re.search(r'<div class="chrome">.*?</div></div>', src, re.S).group(0)
    chrome = chrome.replace(f"<b>{REF_NOME}</b>", f"<b>{nome_cliente}</b>")
    hero = re.search(r'<section class="hero">(.*?)<div class="hero-top', src, re.S).group(1).strip()
    script = src[src.index("<script>"):]
    return head, chrome, hero, script


# ---------- HTML ----------

def fontes_html(fs, cls="fonte-rodape r r4"):
    if not fs:
        return ""
    partes = []
    for rot, txt, url in fs:
        t = f'<a href="{url}" target="_blank" rel="noopener">{txt}</a>' if url else txt
        partes.append((f"<b>{rot}:</b> " if rot else "") + t)
    lbl = "Fonte" if len(fs) == 1 else "Fontes"
    return f'<div class="{cls}"><b>{lbl}</b> · ' + '<span class="sep">|</span>'.join(partes) + "</div>"


def glossario_html(itens):
    if not itens:
        return ""
    return '<div class="glossario r"><span class="lbl">Termos desta tela</span>' + " · ".join(f"<b>{t}</b>: {d}" for t, d in itens) + "</div>"


def chk(s):
    return s.replace("✓ ", CHECK).replace("✓", CHECK)


def bloco_html(b):
    t = b["t"]
    if t == "lede":
        return f'<p class="lede r r2" style="margin-top:12px; max-width:1000px;">{b["texto"]}</p>'
    if t == "abertura":
        return f'<div class="abertura-capitulo r r2">{b["texto"]}</div>'
    if t == "live":
        return f'<div class="live-fill r">{b.get("texto", "Estamos ao vivo")}</div>'
    if t == "cells":
        cs = "".join(f'<div class="cell{(" " + c[3]) if len(c) > 3 and c[3] else ""}"><div class="k">{c[0]}</div><div class="v">{c[1]}</div><div class="d">{c[2]}</div></div>' for c in b["itens"])
        return f'<div class="grid g{b.get("cols", 3)} r r3" style="margin-top:20px;">{cs}</div>'
    if t == "cards":
        out = []
        for c in b["itens"]:
            corpo = f'<p>{c["p"]}</p>' if c.get("p") else ""
            if c.get("ul"):
                corpo += "<ul>" + "".join(f"<li>{x}</li>" for x in c["ul"]) + "</ul>"
            h = f'<h4>{c["h"]}</h4>' if c.get("h") else ""
            fc = f'<div class="fonte-card">{c["fonte"]}</div>' if c.get("fonte") else ""
            out.append(f'<div class="segcard{" pos" if c.get("pos") else ""}"><span class="tag">{c["tag"]}</span>{h}{corpo}{fc}</div>')
        return f'<div class="grid g{b.get("cols", 2)} r r3" style="margin-top:18px;">{"".join(out)}</div>'
    if t == "tabela":
        cab = "".join(f"<th>{h}</th>" for h in b["cab"])
        linhas = "".join("<tr>" + "".join(f"<td>{chk(v)}</td>" for v in l) + "</tr>" for l in b["linhas"])
        return f'<table class="rtable r r3" style="margin-top:18px;"><tr>{cab}</tr>{linhas}</table>'
    if t == "elipses":
        cam = b["camadas"]  # [[sigla, conceito, valor, descricao], x3]
        # no desenho só a sigla de cada camada; valor e conceito ficam na legenda ao lado (valor longo se sobrepunha)
        xs, ys = (110, 300, 450), (88, 126, 160)
        svg_txt = "".join(f'''<line x1="{x}" y1="40" x2="{x}" y2="{y}" stroke="var(--gray-dim)" stroke-width="1"/><circle cx="{x}" cy="{y}" r="3" fill="{'var(--gray)' if i == 0 else '#fff'}"/>
      <text x="{x}" y="28" text-anchor="middle" fill="var(--red)" font-family="JetBrains Mono, monospace" font-size="22" letter-spacing="1.5">{c[0]}</text>''' for i, (c, x, y) in enumerate(zip(cam, xs, ys)))
        leg = "".join(f'<div class="pyr-item"><span class="dot {k}"></span><div><div class="k">{c[0]} ({c[1]})</div><div class="v">{c[2]}</div><div class="d">{c[3]}</div></div></div>' for k, c in zip(("tam", "sam", "som"), cam))
        return f'''<div class="conc-wrap conc-wrap-h r r3">
    <svg class="conc-svg conc-svg-h" viewBox="-20 0 640 340" role="img" aria-label="{cam[0][0]}, {cam[1][0]} e {cam[2][0]} em elipses sobrepostas">
      <defs>
        <radialGradient id="gTam" cx="32%" cy="26%" r="85%"><stop offset="0%" stop-color="#8a8272"/><stop offset="55%" stop-color="#6b6455"/><stop offset="100%" stop-color="#EFE7D3"/></radialGradient>
        <radialGradient id="gSam" cx="32%" cy="26%" r="85%"><stop offset="0%" stop-color="#C99A3A"/><stop offset="55%" stop-color="var(--red-deep)"/><stop offset="100%" stop-color="#4A2F08"/></radialGradient>
        <radialGradient id="gSom" cx="32%" cy="26%" r="85%"><stop offset="0%" stop-color="#E8C878"/><stop offset="55%" stop-color="var(--red)"/><stop offset="100%" stop-color="#5C3D0A"/></radialGradient>
        <filter id="shTam" x="-40%" y="-40%" width="180%" height="200%"><feDropShadow dx="0" dy="16" stdDeviation="16" flood-color="#000" flood-opacity="0.55"/></filter>
        <filter id="shSam" x="-40%" y="-40%" width="180%" height="200%"><feDropShadow dx="0" dy="11" stdDeviation="11" flood-color="#000" flood-opacity="0.5"/></filter>
        <filter id="shSom" x="-40%" y="-40%" width="180%" height="200%"><feDropShadow dx="0" dy="8" stdDeviation="8" flood-color="#000" flood-opacity="0.45"/></filter>
      </defs>
      <ellipse cx="260" cy="200" rx="270" ry="120" fill="url(#gTam)" filter="url(#shTam)"/>
      <ellipse cx="350" cy="200" rx="150" ry="80" fill="url(#gSam)" filter="url(#shSam)"/>
      <ellipse cx="450" cy="200" rx="80" ry="45" fill="url(#gSom)" filter="url(#shSom)"/>
      {svg_txt}
    </svg>
    <div class="pyr-legend">{leg}</div>
  </div>'''
    if t == "barras":
        mx = b.get("max") or max(v for _, v, _, _ in b["itens"])
        bs = "".join(f'<div class="barra{" dest" if d else ""}"><div class="rot">{rot}</div><div class="trilho"><div class="enc" style="width:{v / mx * 100:.1f}%"></div></div><div class="val">{val}</div></div>' for rot, v, val, d in b["itens"])
        return f'<div class="barras r r3">{bs}</div>'
    if t == "layers":
        ls = "".join(f'<div class="layer l1"><div class="layer-head"><div class="name">{n}</div><div class="tag">{tg}</div></div><p>{p}</p></div>' for n, tg, p in b["itens"])
        return f'<div class="r r3" style="margin-top:14px; max-width:1100px;">{ls}</div>'
    if t == "explicador":
        ps = "".join(f"<p>{p}</p>" for p in b["ps"])
        return f'<div class="explicador r r2"><span class="tag">{b["tag"]}</span>{ps}</div>'
    if t == "frase":
        return f'<div class="layer l1 r r3"><div class="layer-head"><div class="name">{b["rotulo"]}</div><div class="tag">{b.get("tag", "")}</div></div><p class="frase">{b["texto"]}</p></div>'
    if t == "checklist":
        return '<div class="checklist r r3" style="margin-top:20px;">' + "".join(f"<div>{x}</div>" for x in b["itens"]) + "</div>"
    if t == "gancho":
        return f'<div class="gancho r r4"><b>{b["lbl"]}</b><span>{b["texto"]}</span></div>'
    if t == "pausa":
        # pausa no corpo da tela, antes do .gancho
        return f'<div class="pausa r r4">{SINO}<b>Anotando</b><span>{b["texto"]}</span></div>'
    if t == "proximos_passos":
        acoes = "".join(f'<div class="ac{" prio" if a["comece_aqui"] else ""}"><div class="top"><h4>{a["acao"]}</h4>'
                        + ('<span class="badge">Comece aqui</span>' if a["comece_aqui"] else '')
                        + f'</div><div class="own"><span class="chip">{a["dono"]}</span><span class="prazo">{a["prazo"]}</span></div></div>' for a in b["acoes"])
        return (f'<div class="trava r r2">{b["trava"]}</div><div class="grid g2 r r3">{acoes}</div>'
                + bloco_html({"t": "pausa", "texto": b["pausa"]})
                + bloco_html({"t": "gancho", "lbl": "A seguir", "texto": b["gancho"]}))
    if t == "plano":
        # Plano de ação por horizonte: mesmos componentes do Mapa de Ações da Semana 5.
        # b = {"t": "plano", "h1": [{"dor", "itens", "dono", "comece"}], "h2": [...], "h3": [...]}
        rot = {"h1": "H1 · 0 a 30 dias", "h2": "H2 · 30 a 180 dias", "h3": "H3 · 6 a 12 meses"}
        def ac(x):
            badge = '<span class="badge">Comece aqui</span>' if x.get("comece") else ""
            ul = "".join(f"<li>{i}</li>" for i in x["itens"])
            return f'<div class="ac{" prio" if x.get("comece") else ""}"><div class="top"><h4>{x["dor"]}</h4>{badge}</div><ul>{ul}</ul><div class="own"><span class="chip">{x["dono"]}</span></div></div>'
        lanes = "".join(f'<div class="lane"><h3>{rot[h]}</h3>{"".join(ac(x) for x in b[h])}</div>' for h in ("h1", "h2", "h3"))
        return f'<div class="lanes h3c r r3">{lanes}</div>'
    raise ValueError(f"bloco desconhecido: {t}")


def blocos_da_tela(s, mercado=True):
    """Projeta os campos analíticos nos componentes existentes de HTML e DOCX."""
    resultado = list(s.get("blocos", []))
    for k, titulo, campos in (("cenario", "Cenário", ("fato", "impacto", "fonte", "ano")),
                               ("regulacao", "Regulação", ("regra", "efeito", "fonte")),
                               ("camadas", "Grupos e papéis", ("nome", "recorte", "contagem", "papel", "fonte"))):
        if s.get(k):
            resultado.append({"t": "tabela", "cab": [x.replace("_", " ").capitalize() for x in campos],
                              "linhas": [[item[x] for x in campos] for item in s[k]]})
    compradores = [[nome[:3].upper() + " · compradores", s[nome]["valor"], s[nome]["fonte"]]
                   for nome in ("tam_compradores", "sam_compradores") if nome in s]
    if compradores and mercado:
        resultado.append({"t": "tabela", "cab": ["Recorte", "Compradores", "Fonte ou lacuna"], "linhas": compradores})
        resultado.append({"t": "lede", "texto": s.get("leitura_meta") or "Meta não declarada. Qual resultado e prazo devemos avaliar contra o mercado?"})
    if s.get("mercado_limita") and mercado:
        resultado.append({"t": "frase", "rotulo": "O mercado limita a meta?", "texto": s["mercado_limita"]})
    if s.get("posicionamento"):
        p = s["posicionamento"]
        resultado.extend([{"t": "frase", "rotulo": "Posicionamento", "tag": p["estado"], "texto": p["frase"]},
                          {"t": "lede", "texto": "Fundamento: " + p["prova"]}])
    for k, titulo in (("comite_compra", "Comitê de compra"), ("fundamento_oferta", "Fundamento da oferta")):
        if s.get(k):
            resultado.append({"t": "tabela", "cab": [titulo, "Leitura sustentada ou hipótese"],
                              "linhas": [[campo.replace("_", " ").capitalize(), valor] for campo, valor in s[k].items()]})
    if s.get("onde_concentrar"):
        p = s["onde_concentrar"]
        resultado.extend([{"t": "lede", "texto": "Critérios: " + "; ".join(p["criterios"])},
                          {"t": "tabela", "cab": ["Grupo", "Papel", "Motivo"], "linhas": [[g["nome"], g["papel"], g["motivo"]] for g in p["grupos"]]},
                          {"t": "frase", "rotulo": "Por agora não", "texto": p["por_agora_nao"]}])
    return resultado


def sintese_mercado_html(s):
    """Agrupa compradores e decisão, preservando o detalhe integral do DOCX."""
    compradores = [[nome[:3].upper(), s[nome]["valor"], s[nome]["fonte"]]
                   for nome in ("tam_compradores", "sam_compradores") if nome in s]
    if not compradores:
        return ""
    tabela = bloco_html({"t": "tabela", "cab": ["Recorte", "Compradores", "Fonte ou lacuna"], "linhas": compradores})
    leitura = s.get("leitura_meta") or "Meta não declarada. Qual resultado e prazo devemos avaliar contra o mercado?"
    limite = f'<h3>O mercado limita a meta?</h3><p>{s["mercado_limita"]}</p>' if s.get("mercado_limita") else ""
    return f'<div class="mercado-sintese r r3">{tabela}<div><p>{leitura}</p>{limite}</div></div>'


def tela_html(s):
    if not s.get("sem_fonte") and not s.get("fontes"):
        raise ValueError(f"tela sem fonte: {s.get('eyebrow')}")
    h2 = f'<h2 class="h-l r r2">{s["h2"]}</h2>' if s.get("h2") else ""
    am = s.get("amarra")
    if am:
        h2 += ('<div class="amarra r r2">' + f'<span><b>Pilar do escopo</b>{am["pilar"]}</span>'
               + f'<span><b>Dor que trata</b>{am["dor"]}</span>' + f'<span><b>Para {am.get("cliente", "o cliente")}</b>{am["cliente_texto"]}</span></div>')
    tem_compradores = "tam_compradores" in s or "sam_compradores" in s
    corpo = "\n  ".join(bloco_html(b) for b in blocos_da_tela(s, mercado=not tem_compradores))
    if tem_compradores:
        corpo += sintese_mercado_html(s)
    pausa = f'<div class="pausa r">{SINO}<b>Anotando</b><span>{s["pausa"]}</span></div>' if s.get("pausa") else ""
    foot = f'<div class="foot">{s["foot"]}</div>' if s.get("foot") else ""
    sid = f' id="{s["id"]}"' if s.get("id") else ""
    return f'''<section{sid}><div class="noise"></div>
  <div class="eyebrow r">{s["eyebrow"]}</div>
  {h2}
  {corpo}
  {fontes_html(s.get("fontes"))}
  {pausa}
  {glossario_html(s.get("glossario"))}
  {foot}
</section>
'''


def gerar_html(C, out=None):
    validar_conteudo(C)
    nome = C["cliente"]
    head, chrome, hero_deco, script = extrair_referencia(nome)
    br = C["ponte"]
    trilha = "".join(f'<div class="tk{(" " + c) if c else ""}">{n}</div>' for n, c in br["trilha"])
    cols = "".join(f'<div class="bridge-col r{" r2" if i else ""}"><div class="lbl">{lbl}</div><ul>' + "".join(f"<li>{x}</li>" for x in xs) + "</ul></div>" for i, (lbl, xs) in enumerate(br["colunas"]))
    # pausa de ponte (metodo-pse.md → "Validação antes do gancho", item 3)
    ponte_pausa = f'<div class="pausa r">{SINO}<b>Anotando</b><span>{br["pausa"]}</span></div>' if br.get("pausa") else ""
    H = C["hero"]
    meta = "".join(f'<div class="m r r{i + 2}"><div class="k">{k}</div><div class="v">{v}</div></div>' for i, (k, v) in enumerate(H["meta"]))
    partes = [f'''<body>
{chrome}
<div class="navdots" id="navdots"></div>
<div class="scroller">

<section><div class="noise"></div>
  <div class="eyebrow r">Ponte entre encontros</div>
  <div class="bridge-track">{trilha}</div>
  <div class="bridge-cols">{cols}</div>
  {ponte_pausa}
</section>

<section class="hero">{hero_deco}
  <div class="hero-top r"><div>{nome} · Estruturação Estratégica</div><div>Trieme &amp; Co</div></div>
  <div>
    <div class="hero-tag r">Pesquisa de Mercado · Semana 2</div>
    <h1 class="h-xl r r2">{H["titulo"]}</h1>
    <p class="lede r r3" style="margin-top:18px;">{H["lede"]}</p>
    <div class="hero-meta">{meta}</div>
    {fontes_html(H["fontes"], "fonte-rodape r r5")}
  </div>
  <div class="scrollcue r r6">role para começar ↓</div>
</section>
''']
    # "so_docx": true: tela de detalhe que fica só no DOCX, para a apresentação ao vivo caber em ~12 telas
    partes += [tela_html(s) for s in C["telas"] if not s.get("so_docx")]
    partes.append("</div>")
    corpo = "\n".join(partes)
    assert TRAVESSAO not in corpo, "travessão encontrado no conteúdo"
    html = head + "\n" + corpo + "\n" + script
    if out is None:
        return html
    exigir_fora_do_pacote(out).write_text(html, encoding="utf-8")
    return out


# ---------- DOCX ----------

def limpa(s):
    s = s.replace("<br>", " ")
    return re.sub(r"<(?!/?b>)[^>]+>", "", s)


def hyperlink(p, texto, url, size=9):
    """Run clicável no DOCX (python-docx não tem API própria para link)."""
    r_id = p.part.relate_to(url, "http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink", is_external=True)
    h = OxmlElement("w:hyperlink"); h.set(qn("r:id"), r_id)
    r = OxmlElement("w:r"); rPr = OxmlElement("w:rPr")
    for tag, attrs in (("w:rFonts", {"w:ascii": BODY, "w:hAnsi": BODY}), ("w:color", {"w:val": "7A5710"}), ("w:u", {"w:val": "single"}), ("w:sz", {"w:val": str(int(size * 2))})):
        e = OxmlElement(tag)
        for k, v in attrs.items():
            e.set(qn(k), v)
        rPr.append(e)
    r.append(rPr)
    t = OxmlElement("w:t"); t.text = texto; t.set(qn("xml:space"), "preserve")
    r.append(t); h.append(r); p._p.append(h)


def fontes_docx(d, fs):
    if not fs:
        return
    p = para(d, before=2, after=8)
    run(p, ("FONTE" if len(fs) == 1 else "FONTES") + ": ", 8.5, True, BRONZE)
    for i, (rot, txt, url) in enumerate(fs):
        if i:
            run(p, "  |  ", 9, False, GRAY)
        if rot:
            run(p, limpa(rot) + ": ", 9, True, GRAY)
        if url:
            hyperlink(p, re.sub(r"<[^>]+>", "", txt), url)
        else:
            run(p, limpa(txt), 9, False, GRAY)


def bloco_docx(d, b):
    t = b["t"]
    if t in ("lede", "abertura"):
        para(d, limpa(b["texto"]))
    elif t == "live":
        para(d, b.get("texto", "Estamos ao vivo") + ": preencher na reunião.", 9.5, True, BRONZE)
    elif t == "cells":
        table(d, ["Indicador", "Valor", "Leitura"], [[limpa(c[0]), limpa(c[1]), limpa(c[2])] for c in b["itens"]], [4, 3.6, 9])
    elif t == "cards":
        for c in b["itens"]:
            label(d, limpa(c["tag"]) + (f" · {limpa(c['h'])}" if c.get("h") else ""))
            if c.get("p"):
                para(d, limpa(c["p"]))
            if c.get("ul"):
                bullets(d, [limpa(x) for x in c["ul"]])
            if c.get("fonte"):
                para(d, "Fonte: " + limpa(c["fonte"]), 8.5, False, GRAY, italic=True, after=4)
    elif t == "tabela":
        table(d, [limpa(h) for h in b["cab"]], [[limpa(v) for v in l] for l in b["linhas"]])
    elif t == "elipses":
        table(d, ["Camada", "Valor", "Como chegamos"], [[f"{c[0]} ({c[1]})", limpa(c[2]), limpa(c[3])] for c in b["camadas"]], [4, 3.6, 9])
    elif t == "barras":
        table(d, ["Referência", "Preço por pessoa/mês"], [[limpa(r), limpa(v)] for r, _, v, _ in b["itens"]], [11, 5.6])
    elif t == "layers":
        for n, tg, p in b["itens"]:
            label(d, limpa(n) + (f" · {limpa(tg)}" if tg else "")); para(d, limpa(p))
    elif t == "explicador":
        callout(d, b["tag"], " ".join(limpa(p) for p in b["ps"]))
    elif t == "frase":
        label(d, limpa(b["rotulo"]) + (f" · {limpa(b['tag'])}" if b.get("tag") else ""))
        para(d, limpa(b["texto"]), 13, True, INK, DISPLAY)
    elif t == "checklist":
        bullets(d, ["☐ " + limpa(x) for x in b["itens"]])
    elif t == "gancho":
        callout(d, b["lbl"], limpa(b["texto"]))
    elif t == "pausa":
        callout(d, "Anotando", limpa(b["texto"]))
    elif t == "proximos_passos":
        callout(d, "A trava", limpa(b["trava"]))
        table(d, ["O que fazer", "Dono", "Prazo"],
              [[limpa(a["acao"]) + (" (comece aqui)" if a["comece_aqui"] else ""), limpa(a["dono"]), limpa(a["prazo"])] for a in b["acoes"]])
        callout(d, "Anotando", limpa(b["pausa"]))
        callout(d, "A seguir", limpa(b["gancho"]))
    elif t == "plano":
        rot = {"h1": "H1 · 0 a 30 dias", "h2": "H2 · 30 a 180 dias", "h3": "H3 · 6 a 12 meses"}
        linhas = [[rot[h], limpa(x["dor"]) + (" (comece aqui)" if x.get("comece") else ""), " ".join(limpa(i) for i in x["itens"]), limpa(x["dono"])]
                  for h in ("h1", "h2", "h3") for x in b[h]]
        table(d, ["Horizonte", "Dor", "O que fazer", "Dono"], linhas, [3.2, 4, 6.6, 2.8])


def gerar_docx(C, out, cons):
    validar_conteudo(C)
    destino = exigir_fora_do_pacote(out)
    nome = C["cliente"]
    d = new_doc()
    para(d, "PESQUISA DE MERCADO · SEMANA 2 · ESTRUTURAÇÃO ESTRATÉGICA", 10, True, GOLD, after=2)
    para(d, limpa(C["hero"]["titulo"]).upper(), 26, True, INK, DISPLAY, after=4)
    para(d, limpa(C["hero"]["lede"]), 12, False, GRAY, after=6)
    para(d, C.get("assinatura", assinatura(cons)), 9.5, True, BRONZE, after=6)
    table(d, [limpa(k) for k, _ in C["hero"]["meta"]], [[limpa(v) for _, v in C["hero"]["meta"]]])
    fontes_docx(d, C["hero"]["fontes"])
    rule(d)
    aberturas = [s for s in C["telas"] if s.get("abertura_docx")]
    for s in aberturas:
        h1(d, limpa(s["eyebrow"]) + (f": {limpa(s['h2'])}" if s.get("h2") else ""))
        for b in blocos_da_tela(s):
            bloco_docx(d, b)
        fontes_docx(d, s.get("fontes"))
    h1(d, "Ponte entre encontros")
    for lbl, xs in C["ponte"]["colunas"]:
        label(d, lbl); bullets(d, [limpa(x) for x in xs])
    if C["ponte"].get("pausa"):
        callout(d, "Anotando", limpa(C["ponte"]["pausa"]))
    detalhe_aberto = False
    for s in C["telas"]:
        if s.get("abertura_docx"):
            continue
        if s.get("so_docx") and not detalhe_aberto:
            rule(d); para(d, "DETALHE PARA CONSULTA", 10, True, GOLD, before=6, after=2)
            para(d, "O que sustenta a apresentação, com as fontes de cada número.", 10, False, GRAY, italic=True)
            detalhe_aberto = True
        h1(d, limpa(s["eyebrow"]) + (f": {limpa(s['h2'])}" if s.get("h2") else ""))
        if s.get("amarra"):
            am = s["amarra"]
            for rot, txt in (("Pilar do escopo", am["pilar"]), ("Dor que trata", am["dor"]), (f"Para {am.get('cliente', 'o cliente')}", am["cliente_texto"])):
                p = para(d, after=1); run(p, rot.upper() + ": ", 8.5, True, BRONZE); run(p, limpa(txt), 9.5, False, GRAY, italic=True)
        for b in blocos_da_tela(s):
            bloco_docx(d, b)
        fontes_docx(d, s.get("fontes"))
        if s.get("pausa"):
            callout(d, "Anotando", limpa(s["pausa"]))
        for t, df in s.get("glossario", []) or []:
            p = para(d, after=2); run(p, t + ": ", 9.5, True, BRONZE); run(p, limpa(df), 9.5, False, GRAY)
    para(d, C.get("rodape", ""), 9.5, True, BRONZE, before=8)
    footer(d, f"Trieme & Co · V4 Company · Pesquisa de Mercado {nome}")
    assert TRAVESSAO not in "\n".join(p.text for p in d.paragraphs), "travessão encontrado"
    d.save(destino)
    return out


def main():
    console_utf8()
    ap = argparse.ArgumentParser(description="Gera a Pesquisa de Mercado em HTML e DOCX.")
    ap.add_argument("conteudo", help="conteudo.json da Pesquisa")
    ap.add_argument("saida", nargs="?", help="pasta de saída (a pasta 2. Pesquisa de Mercado do cliente)")
    ap.add_argument("--validar", action="store_true", help="valida HTML e DOCX em memória; não grava nem cria diretórios")
    argumentos_do_consultor(ap)
    a = ap.parse_args()
    try:
        with open(a.conteudo, encoding="utf-8-sig") as f:
            C = json.load(f)
        avisos = validar_conteudo(C)
        for av in avisos:
            print(f"AVISO: {av}", file=sys.stderr)
        if a.validar:
            print("OK: conteúdo HTML e DOCX validado em memória; nenhum arquivo gravado")
            return 0
        if a.saida is None:
            raise ValueError("saida: informe pasta de saída ou use --validar")
        saida = exigir_fora_do_pacote(a.saida)
        cons = consultor_dos_args(a)
        C = aplicar_consultor(C, cons)
        html = gerar_html(C)
        saida.mkdir(parents=True, exist_ok=True)
        slug = C["slug"]
        caminho_html = saida / f"pesquisa-mercado-{slug}.html"
        caminho_html.write_text(html, encoding="utf-8")
        print(caminho_html)
        print(gerar_docx(C, str(saida / f"pesquisa-mercado-{slug}.docx"), cons))
        return 0
    except (ValueError, OSError) as e:
        print(f"ERRO: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
