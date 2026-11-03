"""Gera o DOCX de uma entrega a partir do HTML final da semana.

Uso:
    python html_para_docx.py <entrega.html> [<saida.docx>] [--detalhe <detalhe.html>]
            --consultor "<nome>" --cargo "<cargo>"

O HTML é a fonte da verdade e o DOCX é derivado dele, na paleta EE (dourado, bronze, tinta;
Georgia + Arial) de docx_common.py.

--detalhe: as seções desse arquivo entram no DOCX depois das telas, sob o título
"Detalhe para consulta". É assim que as Semanas 3 a 5 mandam o detalhe só para o DOCX.
A exceção é section.abertura: entra logo após a capa, antes das telas, uma única vez
quando igual no deck e no detalhe. O HTML apresentado não muda.

Regras de conversão:
- A seção .hero vira a capa (vai primeiro, mesmo que a Ponte venha antes no HTML).
- .eyebrow de cada seção vira título; h2 vira subtítulo.
- Cards (.cell, .segcard, .acao-card, .ac, .gr, .fc, .kcol, .quad, .layer, .hm,
  .field-card, .auto-card, .dep-card, .bridge-col, .diag-acao > div) viram itens
  com rótulo em negrito.
- .pausa vira destaque "Anotando"; .gancho vira destaque com o próprio rótulo;
  .explicador vira destaque.
- Mockups, SVG e decoração não entram. PNG local/base64 entra como imagem;
  formato indisponível usa o texto alternativo, sem consultar a rede.
- O consultor vem dos argumentos --consultor e --cargo (userConfig do plugin); sem nome, o texto
  é neutro, com aviso.
- Para se encontrar travessão no texto final. Nunca grava dentro da pasta do pacote.
"""
import sys
sys.dont_write_bytecode = True
import argparse, base64, io, os, re
from pathlib import Path
from bs4 import BeautifulSoup, NavigableString, Tag

sys.path.insert(0, str(Path(__file__).resolve().parent))
from docx_common import *  # noqa: E402,F403

PULAR = {"noise", "navdots", "chrome", "scrollcue", "browser-mock", "ig-mock", "phone", "bridge-track",
         "ar", "ck", "v4-mark", "consultor-tag", "hero-top", "ic", "arrow", "stars"}
CARDS = {"cell", "segcard", "acao-card", "ac", "gr", "fc", "kcol", "quad", "layer", "hm", "field-card",
         "auto-card", "dep-card", "bridge-col", "frente", "step", "m"}
ROTULOS = {"k", "tag", "num", "lbl", "kh", "name", "badge", "n", "letter", "t", "layer-head", "top", "head"}


def juntar(itens):
    """Junta itens de lista sem gerar pontuação dupla (".;")."""
    itens = [i for i in itens if i]
    return " ".join(i if i[-1] in ".!?:" else i + ";" for i in itens[:-1]) + (" " + itens[-1] if len(itens) > 1 else (itens[0] if itens else ""))


def txt(el):
    if el is None:
        return ""
    t = el.get_text(" ", strip=True) if isinstance(el, Tag) else str(el)
    t = re.sub(r"\s+", " ", t).strip()
    return re.sub(r"\s+([,.;:!?])", r"\1", t)


def classes(el):
    return set(el.get("class", [])) if isinstance(el, Tag) else set()


class Conversor:
    def __init__(self, d, origem=None):
        self.d = d
        self.ultimo = None
        self.origem = Path(origem).resolve().parent if origem else Path.cwd()

    def imagem(self, el):
        """Incorpora PNG local/base64; demais formatos mantêm a alternativa, sem rede."""
        src, alt = el.get("src", ""), el.get("alt", "").strip()
        try:
            if src.startswith("data:image/png;base64,"):
                dados = base64.b64decode(src.split(",", 1)[1], validate=True)
            elif re.match(r"^[a-z][a-z0-9+.-]*://", src, re.I) or src.startswith(("//", "data:")):
                raise ValueError("imagem remota ou formato não suportado")
            else:
                caminho = Path(src)
                if not caminho.is_absolute():
                    caminho = self.origem / caminho
                if caminho.suffix.lower() != ".png":
                    raise ValueError("formato não suportado; use PNG")
                dados = caminho.read_bytes()
            if not dados.startswith(b"\x89PNG\r\n\x1a\n"):
                raise ValueError("conteúdo não é PNG")
            self.d.add_picture(io.BytesIO(dados), width=Cm(16))
            self.ultimo = None
        except Exception as e:
            print(f"AVISO: imagem não incorporada ({src[:100]}): {e}; usando alternativa textual.", file=sys.stderr)
            self.p(alt or "Imagem indisponível; consulte o HTML original.")

    def p(self, t, **kw):
        if t and t != self.ultimo:
            para(self.d, t, **kw)
            self.ultimo = t

    def card(self, el):
        cl = classes(el)
        rot, corpo = [], []
        for c in el.children:
            if isinstance(c, NavigableString):
                if c.strip():
                    corpo.append(c.strip())
                continue
            if not isinstance(c, Tag) or c.name in ("svg", "script") or classes(c) & PULAR:
                continue
            if "ac" in cl and "prio" not in cl and "badge" in classes(c):
                continue
            if classes(c) & ROTULOS or c.name in ("h3", "h4", "h5") or "v" in classes(c):
                t = txt(c)
                if t:
                    rot.append(t)
            elif c.name in ("ul", "ol"):
                corpo.append(juntar([txt(li) for li in c.find_all("li")]))
            elif classes(c) & {"own", "src"}:
                t = txt(c)
                if t:
                    corpo.append(("Responsável: " if "own" in classes(c) else "Origem: ") + t + ".")
            elif c.name == "table":
                self.tabela(c)
            else:
                t = txt(c)
                if t:
                    corpo.append(t)
        rot = [r.replace("→", "").strip() for r in rot]
        titulo = " · ".join(dict.fromkeys(r for r in rot if r))
        texto = " ".join(corpo)
        if "kcol" in cl and not titulo:
            titulo = txt(el.find(class_="kh"))
        if titulo and texto:
            bullets(self.d, [(titulo + ": ", texto)])
        elif titulo or texto:
            bullets(self.d, [titulo or texto])
        self.ultimo = None

    def tabela(self, t):
        linhas = []
        for tr in t.find_all("tr"):
            cel = [txt(c) for c in tr.find_all(["th", "td"])]
            if cel:
                linhas.append(cel)
        if not linhas:
            return
        n = max(len(l) for l in linhas)
        linhas = [l + [""] * (n - len(l)) for l in linhas]
        if t.find("th"):
            table(self.d, linhas[0], linhas[1:])
        else:
            table(self.d, [""] * n, linhas)

    def destaque(self, el, padrao):
        b = el.find("b")
        lbl = txt(el.find(class_="tag")) or (txt(b) if b else "") or padrao
        resto = []
        for c in el.children:
            if isinstance(c, Tag) and (c is b or classes(c) & {"tag"} or c.name in ("svg", "table")):
                continue
            t = txt(c)
            if t:
                resto.append(t)
        callout(self.d, lbl, " ".join(resto))
        for t in el.find_all("table"):
            self.tabela(t)
        self.ultimo = None

    def emitir(self, el):
        if isinstance(el, NavigableString):
            t = el.strip()
            if t:
                self.p(re.sub(r"\s+", " ", t))
            return
        if not isinstance(el, Tag) or el.name in ("svg", "script", "style", "button", "input", "select", "form"):
            return
        cl = classes(el)
        if cl & PULAR:
            return
        if el.name == "img":
            return self.imagem(el)
        if "pausa" in cl:
            return self.destaque(el, "Anotando")
        if "gancho" in cl or "porque" in cl:
            return self.destaque(el, "A seguir")
        if el.find(class_="chip") and not el.find(["ul", "table", "div"]):
            chips = [txt(c) for c in el.find_all(class_="chip")]
            for c in el.find_all(class_="chip"):
                c.extract()
            return self.p((txt(el) + " " + ", ".join(chips) + ".").strip())
        if "explicador" in cl:
            lbl = txt(el.find(class_="tag")) or "O que é"
            callout(self.d, lbl, " ".join(txt(p) for p in el.find_all("p")))
            self.ultimo = None
            return
        if "fonte-rodape" in cl or "nota-evid" in cl:
            return self.p(txt(el), size=9, color=GRAY, italic=True)
        if "eyebrow" in cl:
            t = txt(el)
            if t:
                label(self.d, t); self.ultimo = t
            return
        if el.name == "table":
            return self.tabela(el)
        if cl & CARDS:
            return self.card(el)
        if el.name in ("h1", "h2"):
            t = txt(el)
            if t:
                h2(self.d, t); self.ultimo = t
            return
        if el.name in ("h3", "h4"):
            t = txt(el)
            if t:
                label(self.d, t); self.ultimo = t
            return
        if el.name in ("ul", "ol"):
            itens = [txt(li) for li in el.find_all("li", recursive=False)]
            bullets(self.d, [i for i in itens if i]); self.ultimo = None
            return
        if el.name == "p" or cl & {"lede", "abertura-capitulo", "def", "total", "foot", "spoiler"}:
            return self.p(txt(el), italic="foot" in cl)
        blocos = [c for c in el.children if isinstance(c, Tag) and c.name not in ("b", "i", "em", "strong", "span", "br", "a", "sup", "sub")]
        if not blocos:
            return self.p(txt(el))
        for c in el.children:
            self.emitir(c)


def corpo_de_secoes(soup):
    """Seções de um HTML; sem <section>, o <body> inteiro conta como uma."""
    secs = soup.find_all("section")
    if secs:
        return secs
    return [soup.body] if soup.body else []


def converter(html_path, out_path, cons, detalhe_path=None):
    exigir_fora_do_pacote(out_path)
    soup = BeautifulSoup(Path(html_path).read_text(encoding="utf-8"), "html.parser")
    det = BeautifulSoup(Path(detalhe_path).read_text(encoding="utf-8"), "html.parser") if detalhe_path else None
    secoes = soup.find_all("section")
    hero = next((s for s in secoes if "hero" in classes(s)), None)
    titulo_doc = soup.title.get_text(strip=True) if soup.title else os.path.basename(html_path)
    d = new_doc()
    c = Conversor(d, html_path)

    if hero:
        tag = hero.find(class_=["hero-tag", "eyebrow"])
        para(d, (txt(tag) or titulo_doc).upper() + " · ESTRUTURAÇÃO ESTRATÉGICA", 10, True, GOLD, after=2)
        h = hero.find(["h1", "h2"])
        para(d, txt(h) if h else titulo_doc, 24, True, INK, DISPLAY, after=4)
        for lede in hero.find_all(class_="lede"):
            para(d, txt(lede), 12, False, GRAY, after=6)
        para(d, assinatura(cons), 9.5, True, BRONZE, after=6)
        metas = hero.find_all(class_="m")
        if metas:
            table(d, [txt(m.find(class_="k")) for m in metas], [[txt(m.find(class_="v")) for m in metas]])
        rule(d)

    # Só a marcação explícita promove uma seção; títulos iguais não provam duplicação.
    aberturas = [(s, origem) for documento, origem in ((soup, html_path), (det, detalhe_path))
                 if documento is not None for s in documento.select("section.abertura")]
    vistas = set()
    for abertura, origem in aberturas:
        identidade = str(abertura)
        if identidade not in vistas:
            if vistas:
                print("AVISO: aberturas diferentes no deck/detalhe; ambas preservadas para revisão.", file=sys.stderr)
            c.origem = Path(origem).resolve().parent
            for filho in abertura.children:
                c.emitir(filho)
            vistas.add(identidade)
        abertura.extract()
    identificacao = txt(hero.find(class_="hero-tag")) if hero else ""
    if not aberturas and re.search(r"\bsemana\s*[345]\b", identificacao or titulo_doc, re.I):
        print("AVISO: Semana 3–5 sem section.abertura; acrescente os achados e como ler. DOCX preservado.", file=sys.stderr)

    c.origem = Path(html_path).resolve().parent
    for s in secoes:
        if s is hero or "abertura" in classes(s):
            continue
        eyebrow = s.find(class_="eyebrow")
        titulo = txt(eyebrow) if eyebrow else "Seção"
        h1(d, titulo); c.ultimo = titulo
        for filho in s.children:
            if filho is eyebrow:
                continue
            c.emitir(filho)

    if detalhe_path:
        c.origem = Path(detalhe_path).resolve().parent
        rule(d)
        h1(d, "Detalhe para consulta"); c.ultimo = None
        para(d, "O que sustenta a apresentação, com as fontes de cada número.", 10, False, GRAY, italic=True)
        for s in corpo_de_secoes(det):
            eyebrow = s.find(class_="eyebrow")
            titulo = txt(eyebrow) if eyebrow else (txt(s.find(["h1", "h2"])) or "Seção")
            h2(d, titulo); c.ultimo = titulo
            for filho in s.children:
                if filho is eyebrow:
                    continue
                c.emitir(filho)

    footer(d, f"Trieme & Co · V4 Company · {titulo_doc}")
    paragrafos = [p.text for p in d.paragraphs] + [cel.text for t in d.tables for r in t.rows for cel in r.cells]
    texto = " ".join(paragrafos)
    codigos = sorted(set(re.findall(r"\b(?:[PSEDR]-[A-Z]{1,3}\d{1,3}|PC\d{2}|[PN]\d{1,2}|[CDSE]\d{2})\b", texto)))
    if codigos:
        print("AVISO: possível código interno no DOCX: " + ", ".join(codigos) + "; escreva o significado para o cliente.", file=sys.stderr)
    assert TRAVESSAO not in texto, "travessão encontrado no DOCX"
    d.save(out_path)
    return out_path


def main():
    console_utf8()
    ap = argparse.ArgumentParser(description="Converte o HTML de uma entrega em DOCX.")
    ap.add_argument("html", help="entrega.html")
    ap.add_argument("saida", nargs="?", help="saida.docx (padrão: ao lado do HTML, mesmo nome)")
    ap.add_argument("--detalhe", help="detalhe.html: abertura após a capa; demais seções em 'Detalhe para consulta'")
    argumentos_do_consultor(ap)
    a = ap.parse_args()
    out = Path(a.saida) if a.saida else Path(a.html).with_suffix(".docx")
    exigir_fora_do_pacote(out)
    cons = consultor_dos_args(a)
    out.parent.mkdir(parents=True, exist_ok=True)
    print(converter(a.html, str(out), cons, a.detalhe))


if __name__ == "__main__":
    main()
