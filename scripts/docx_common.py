"""Base comum dos scripts do pacote ee-trieme.

Mora só em scripts/. Os geradores e o html_para_docx.py importam daqui.

Traz três coisas:
- estilos DOCX na paleta EE (dourado, bronze, tinta; Georgia + Arial);
- a raiz do pacote, achada pela posição deste arquivo (nenhum caminho fixo);
- o consultor, vindo dos argumentos --consultor, --cargo e --foto (userConfig do plugin), e a
  trava que impede qualquer script de gravar dentro da pasta do pacote.
"""
import base64
import html as _html
import mimetypes
import re
import sys
from pathlib import Path

from docx import Document
from docx.shared import Pt, RGBColor, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

# ---------- pacote, consultor, saída ----------

RAIZ_PACOTE = Path(__file__).resolve().parent.parent
CASO_REFERENCIA = RAIZ_PACOTE / "referencias" / "layout"
TRAVESSAO = chr(0x2014)  # a régua de estilo proíbe; todo gerador confere a saída
CONSULTOR_NEUTRO = {"nome": "", "cargo": "", "foto": None, "neutro": True}


def console_utf8():
    """Evita erro de acentuação no console do Windows."""
    for f in (sys.stdout, sys.stderr):
        try:
            f.reconfigure(encoding="utf-8")
        except Exception:
            pass


def exigir_fora_do_pacote(caminho):
    """Para a execução se o caminho estiver dentro da pasta do pacote (ela muda a cada atualização)."""
    p = Path(caminho).resolve()
    if p == RAIZ_PACOTE or RAIZ_PACOTE in p.parents:
        sys.exit(f"ERRO: {p} fica dentro da pasta do pacote ({RAIZ_PACOTE}). Grave na pasta do cliente.")
    return p


def argumentos_do_consultor(ap):
    """Acrescenta ao argparse os três argumentos do consultor. Os guias passam os valores do userConfig
    do plugin: --consultor "${user_config.consultor_nome}" --cargo "${user_config.consultor_cargo}"
    [--foto "EE/foto-consultor.jpg"]."""
    ap.add_argument("--consultor", default="", help="nome do consultor (userConfig consultor_nome)")
    ap.add_argument("--cargo", default="", help="cargo do consultor (userConfig consultor_cargo)")
    ap.add_argument("--foto", default="", help="foto do consultor, opcional (opcional, EE/foto-consultor.jpg)")


def _valor(v):
    """Texto do argumento, ou "" quando vazio ou quando a variável do guia não foi substituída."""
    v = (v or "").strip()
    return "" if v.startswith("${") else v


def consultor_dos_args(a):
    """Devolve {"nome", "cargo", "foto", "neutro"} a partir de --consultor, --cargo e --foto.

    Sem nome, avisa no stderr e devolve o texto neutro. Cargo ausente avisa e sai sem cargo.
    Foto ausente ou inexistente avisa e sai sem foto. Nada é lido nem gravado na pasta do pacote."""
    nome, cargo, foto = _valor(a.consultor), _valor(a.cargo), _valor(a.foto)
    if not nome:
        print("AVISO: consultor não informado (--consultor \"<nome>\" --cargo \"<cargo>\", valores do userConfig "
              "do plugin). Usando texto neutro.", file=sys.stderr)
        return dict(CONSULTOR_NEUTRO)
    if not cargo:
        print("AVISO: cargo não informado (--cargo). A assinatura sai só com o nome.", file=sys.stderr)
    caminho = None
    if foto:
        caminho = Path(foto).expanduser()
        if not caminho.is_file():
            print(f"AVISO: foto {foto} não existe; o hero sai sem foto.", file=sys.stderr)
            caminho = None
    return {"nome": nome, "cargo": cargo, "foto": caminho, "neutro": False}


def assinatura(c, com_marca=True):
    """Linha de assinatura do consultor, com texto neutro quando o consultor não foi informado."""
    if c.get("neutro"):
        return "Trieme & Co · Estruturação Estratégica" if com_marca else "Trieme & Co"
    partes = [c["nome"]] + ([c["cargo"]] if c["cargo"] else []) + (["Trieme & Co"] if com_marca else [])
    return " · ".join(partes)


def tag_consultor_html(c, classe="consultor-tag r r4"):
    """Bloco .consultor-tag do hero do Kickoff, montado a partir dos argumentos do consultor."""
    esc = _html.escape
    img = ""
    foto = c.get("foto")
    if foto:
        foto = Path(foto)
        if foto.is_file():
            mime = mimetypes.guess_type(foto.name)[0] or "image/jpeg"
            b64 = base64.b64encode(foto.read_bytes()).decode("ascii")
            img = f'<img src="data:{mime};base64,{b64}" alt="{esc(c["nome"])}">'
        else:
            print(f"AVISO: foto {foto} não existe; o hero sai sem foto.", file=sys.stderr)
    if c.get("neutro"):
        info = '<div class="info"><b>Trieme &amp; Co</b>Estruturação Estratégica</div>'
    else:
        info = f'<div class="info"><b>{esc(c["nome"])}</b>{esc(c["cargo"])}</div>'
    return f'<div class="{classe}">{img}{info}</div>'


def aplicar_consultor(obj, c):
    """Troca {consultor}, {consultor_nome} e {consultor_cargo} ({consultor_titulo} segue valendo) nas strings de um JSON de conteúdo."""
    if isinstance(obj, str):
        if "{consultor" not in obj:
            return obj
        return (obj.replace("{consultor_nome}", c["nome"] or "Consultor Trieme & Co")
                   .replace("{consultor_cargo}", c["cargo"] or "Estruturação Estratégica")
                   .replace("{consultor_titulo}", c["cargo"] or "Estruturação Estratégica")
                   .replace("{consultor}", assinatura(c, com_marca=False)))
    if isinstance(obj, list):
        return [aplicar_consultor(x, c) for x in obj]
    if isinstance(obj, dict):
        return {k: aplicar_consultor(v, c) for k, v in obj.items()}
    return obj


def limpar_referencia(head):
    """Tira do <head> copiado da referência de layout todo comentário CSS."""
    return re.sub(r"/\*.*?\*/", "", head, flags=re.S)


# ---------- DOCX ----------

GOLD = RGBColor(0xA8, 0x79, 0x1A)
BRONZE = RGBColor(0x7A, 0x57, 0x10)
INK = RGBColor(0x22, 0x1D, 0x12)
GRAY = RGBColor(0x72, 0x6A, 0x57)
BODY = "Arial"
DISPLAY = "Georgia"


def new_doc():
    d = Document()
    s = d.sections[0]
    s.page_width, s.page_height = Cm(21), Cm(29.7)
    for m in ("left_margin", "right_margin"):
        setattr(s, m, Cm(2.2))
    s.top_margin = s.bottom_margin = Cm(2)
    st = d.styles["Normal"]
    st.font.name = BODY
    st.element.rPr.rFonts.set(qn("w:eastAsia"), BODY)
    st.font.size = Pt(10.5)
    st.font.color.rgb = INK
    st.paragraph_format.space_after = Pt(6)
    st.paragraph_format.line_spacing = 1.25
    return d


def run(p, text, size=10.5, bold=False, color=INK, font=BODY, italic=False):
    """Adiciona texto ao parágrafo. Trechos entre <b>...</b> (palavras-chave do conteúdo) saem em negrito."""
    partes = re.split(r"(<b>.*?</b>)", text) if "<b>" in text else [text]
    r = None
    for parte in partes:
        if not parte:
            continue
        negrito = bold or parte.startswith("<b>")
        r = p.add_run(re.sub(r"</?b>", "", parte))
        r.font.size = Pt(size); r.bold = negrito; r.italic = italic
        r.font.color.rgb = color; r.font.name = font
        r._element.rPr.rFonts.set(qn("w:eastAsia"), font)
    return r


def para(d, text="", size=10.5, bold=False, color=INK, font=BODY, before=0, after=6, italic=False):
    p = d.add_paragraph()
    p.paragraph_format.space_before = Pt(before)
    p.paragraph_format.space_after = Pt(after)
    if text:
        run(p, text, size, bold, color, font, italic)
    return p


def h1(d, text):
    p = para(d, text, 15, True, GOLD, DISPLAY, before=16, after=6)
    p.paragraph_format.keep_with_next = True
    return p


def h2(d, text):
    p = para(d, text, 11.5, True, INK, BODY, before=10, after=4)
    p.paragraph_format.keep_with_next = True
    return p


def label(d, text):
    p = para(d, text.upper(), 9.5, True, BRONZE, BODY, before=8, after=2)
    p.paragraph_format.keep_with_next = True
    return p


def bullets(d, items, color=GOLD):
    for it in items:
        p = d.add_paragraph()
        p.paragraph_format.left_indent = Cm(0.6)
        p.paragraph_format.first_line_indent = Cm(-0.4)
        p.paragraph_format.space_after = Pt(3)
        run(p, "•  ", 10.5, True, color)
        if isinstance(it, tuple):
            run(p, it[0], 10.5, True); run(p, it[1])
        else:
            run(p, it)


def callout(d, lbl, text):
    p = para(d, after=6)
    p.paragraph_format.left_indent = Cm(0.4)
    _border_left(p)
    run(p, lbl.upper() + ": ", 9.5, True, GOLD)
    run(p, text, 10, False, INK)
    return p


def _border_left(p):
    pPr = p._p.get_or_add_pPr()
    b = OxmlElement("w:pBdr")
    l = OxmlElement("w:left")
    for k, v in (("w:val", "single"), ("w:sz", "18"), ("w:space", "8"), ("w:color", "A8791A")):
        l.set(qn(k), v)
    b.append(l); pPr.append(b)


def _shade(cell, fill):
    tcPr = cell._tc.get_or_add_tcPr()
    sh = OxmlElement("w:shd")
    sh.set(qn("w:val"), "clear"); sh.set(qn("w:color"), "auto"); sh.set(qn("w:fill"), fill)
    tcPr.append(sh)


def table(d, header, rows, widths=None):
    t = d.add_table(rows=1, cols=len(header))
    t.style = "Table Grid"
    for i, h in enumerate(header):
        c = t.rows[0].cells[i]; c.text = ""
        run(c.paragraphs[0], h.upper(), 9, True, RGBColor(0xFF, 0xFF, 0xFF))
        _shade(c, "A8791A")
    for ri, r in enumerate(rows):
        cells = t.add_row().cells
        for i, v in enumerate(r):
            cells[i].text = ""
            run(cells[i].paragraphs[0], str(v), 9.5, i == 0 and len(header) > 1)
            if ri % 2 == 1:
                _shade(cells[i], "F6F1E4")
    if widths:
        for row in t.rows:
            for i, w in enumerate(widths):
                row.cells[i].width = Cm(w)
    para(d, after=4)
    return t


def rule(d):
    p = para(d, after=8)
    pPr = p._p.get_or_add_pPr()
    b = OxmlElement("w:pBdr"); bt = OxmlElement("w:bottom")
    for k, v in (("w:val", "single"), ("w:sz", "8"), ("w:space", "1"), ("w:color", "A8791A")):
        bt.set(qn(k), v)
    b.append(bt); pPr.append(b)


def footer(d, text):
    f = d.sections[0].footer.paragraphs[0]
    f.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run(f, text, 8, False, GRAY)
