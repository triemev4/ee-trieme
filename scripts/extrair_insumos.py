"""Extrai o texto dos insumos de um cliente (PDF, planilha, DOCX, TXT, MD) para leitura barata.

Uso:
    python extrair_insumos.py <pasta 0. Inputs e Transcrições> [--imagens] [--sem-ocr] [--refazer]

Grava em `<pasta>/_texto/`:
  - um `<arquivo>.txt` por insumo, com texto limpo. Cada trecho começa com a origem entre colchetes:
    PDF `[arquivo.pdf · página 3]` (`[arquivo.pdf · página 3 · OCR]` se a página era imagem e foi lida por OCR);
    planilha `[arquivo.xlsx · aba Nome · linhas 1 a 200]`; CSV `[arquivo.csv · linhas 1 a 200]`; DOCX, TXT e MD `[arquivo]` na primeira linha.
    Tabela em linhas, células com " | ". Planilha grande vem em trechos de 200 linhas;
  - `indice.md`: arquivo, tipo, páginas, caracteres, tamanho original e do texto, data do arquivo, quando foi extraído,
    as páginas lidas por OCR e as páginas sem texto;
  - `.estado.json`: o que já foi extraído (data e tamanho do arquivo). Insumo que não mudou não é refeito.

Planilha: XLSX/XLSM pelo openpyxl (valores, não fórmulas; fórmula sem valor salvo vai como aviso no índice); CSV/TSV pela biblioteca padrão (detecta ";", "," ou tab e a codificação).

OCR (PDF só de imagem): Tesseract em português, chamado por subprocess. Procura `tesseract` no PATH e em
`C:/Program Files/Tesseract-OCR/tesseract.exe` (a variável EE_TESSERACT, se existir, aponta o executável e vale só ela); os dados de idioma em TESSDATA_PREFIX,
depois em `%LOCALAPPDATA%/tessdata`, depois no padrão do Tesseract. A página é renderizada pelo PyMuPDF (fitz), se houver;
senão vale a imagem embutida na página, lida pelo pypdf. `--sem-ocr` desliga.
Sem OCR disponível, as páginas sem texto viram um JPEG de até 1000 px em `_texto/imagens/` (uma vez, listado no índice;
precisa do Pillow). Com OCR, imagem só com `--imagens`. `--refazer` ignora o cache.

Os guias leem os insumos por `_texto/`, nunca o PDF nem a planilha original.
Requer pypdf, python-docx e openpyxl (scripts/requirements.txt). Pillow e Tesseract são opcionais.
"""
import sys
sys.dont_write_bytecode = True
import argparse, csv, io, json, os, re, shutil, subprocess, tempfile, time
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, time as hora_t
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

PASTA_SAIDA = "_texto"
TIPOS = {".pdf": "PDF", ".docx": "DOCX", ".txt": "TXT", ".md": "MD",
         ".xlsx": "XLSX", ".xlsm": "XLSX", ".csv": "CSV", ".tsv": "CSV"}
MIN_LETRAS = 12          # página com menos letras/números que isso conta como sem texto
VERSAO_ESTADO = 3
LINHAS_POR_TRECHO = 200  # planilha e CSV: linhas não vazias por trecho
LINHAS_MAX_ABA = 50000   # acima disso a aba é cortada e o índice avisa
DPI_OCR = 200
LARGURA_MAX = 1000       # px, para --imagens


# ---------------------------------------------------------------- limpeza

def linha_layout(l):
    """Linha de PDF em modo layout: vão de colunas vira " | "; texto justificado (palavras soltas em minúscula) volta a espaço simples."""
    segs = re.split(r"\s{3,}", l.strip())
    segs = [re.sub(r" {2,}", " ", x) for x in segs]
    if len(segs) < 2:
        return segs[0]
    soltas = sum(1 for s in segs if " " not in s and s[:1].islower())
    if soltas >= 3:
        return re.sub(r"\s+", " ", l.strip())
    return " | ".join(segs)


def limpar(texto, layout=False):
    """layout=True (PDF): corta o recuo e troca o vão de colunas por " | ", para a tabela sair em linhas."""
    texto = texto.replace("\x00", "").replace("\u00ad", "").replace("\r\n", "\n").replace("\r", "\n")
    texto = texto.replace("\u00a0", " ").replace("\u200b", "").replace("\ufeff", "")
    out = []
    for l in texto.split("\n"):
        l = l.rstrip()
        if layout and l:
            l = linha_layout(l)
        out.append(l)
    texto = "\n".join(out)
    texto = re.sub(r"\n{3,}", "\n\n", texto)
    return texto.strip()


def so_letras(texto):
    return len(re.findall(r"\w", texto))


# ---------------------------------------------------------------- OCR

_OCR_CACHE = {}


def _langs_do_diretorio(d):
    try:
        return {f.name[:-len(".traineddata")] for f in Path(d).iterdir() if f.name.endswith(".traineddata")}
    except OSError:
        return set()


def configurar_ocr():
    """Acha o Tesseract e a pasta de dados com o português. Devolve (config, motivo): config é um dict
    (exe, lang, tessdata, versao, aviso) ou None, e então o motivo diz por quê."""
    if "r" in _OCR_CACHE:
        return _OCR_CACHE["r"]
    exe = None
    forcado = os.environ.get("EE_TESSERACT")      # caminho do executável; vale só ele (usado nos testes)
    cands = [forcado] if forcado else [shutil.which("tesseract"),
             "C:/Program Files/Tesseract-OCR/tesseract.exe", "C:/Program Files (x86)/Tesseract-OCR/tesseract.exe"]
    for c in cands:
        if c and Path(c).is_file():
            exe = str(c)
            break
    if not exe:
        _OCR_CACHE["r"] = (None, "Tesseract não encontrado (PATH e C:/Program Files/Tesseract-OCR)")
        return _OCR_CACHE["r"]
    try:
        v = subprocess.run([exe, "--version"], capture_output=True, timeout=30)
        saida_v = (v.stdout or v.stderr).decode("utf-8", "replace").strip().splitlines()
        versao = saida_v[0] if saida_v else "tesseract"
    except Exception as e:
        _OCR_CACHE["r"] = (None, f"Tesseract não roda ({type(e).__name__})")
        return _OCR_CACHE["r"]
    pastas = []
    pref = os.environ.get("TESSDATA_PREFIX")
    if pref:
        pastas += [Path(pref) / "tessdata", Path(pref)]
    local = os.environ.get("LOCALAPPDATA")
    if local:
        pastas.append(Path(local) / "tessdata")
    achou_eng = None
    for d in pastas:
        langs = _langs_do_diretorio(d)
        if "por" in langs:
            _OCR_CACHE["r"] = ({"exe": exe, "lang": "por", "tessdata": str(d), "versao": versao, "aviso": ""}, "")
            return _OCR_CACHE["r"]
        if "eng" in langs and not achou_eng:
            achou_eng = d
    try:                                    # padrão do Tesseract
        p = subprocess.run([exe, "--list-langs"], capture_output=True, timeout=30)
        langs = set((p.stdout or b"").decode("utf-8", "replace").split()[1:])
        if "por" in langs:
            _OCR_CACHE["r"] = ({"exe": exe, "lang": "por", "tessdata": None, "versao": versao, "aviso": ""}, "")
            return _OCR_CACHE["r"]
    except Exception:
        pass
    if achou_eng:
        _OCR_CACHE["r"] = ({"exe": exe, "lang": "eng", "tessdata": str(achou_eng), "versao": versao,
                            "aviso": "sem dados de português (por.traineddata): OCR em inglês, acentos podem sair errados"}, "")
        return _OCR_CACHE["r"]
    _OCR_CACHE["r"] = (None, "Tesseract sem dados de idioma (por.traineddata)")
    return _OCR_CACHE["r"]


def ocr_arquivo(ocr, caminho):
    cmd = [ocr["exe"], str(caminho), "stdout", "-l", ocr["lang"], "--dpi", str(DPI_OCR)]
    if ocr["tessdata"]:
        cmd += ["--tessdata-dir", ocr["tessdata"]]
    env = dict(os.environ, OMP_THREAD_LIMIT="1")
    p = subprocess.run(cmd, capture_output=True, timeout=180, env=env)
    if p.returncode != 0:
        raise RuntimeError((p.stderr or b"").decode("utf-8", "replace").strip()[:100] or f"código {p.returncode}")
    return p.stdout.decode("utf-8", "replace")


def limpar_ocr(texto):
    """Tira linhas sem letra nem número (ruído de logo e moldura) e aplica a limpeza comum."""
    linhas = [l for l in limpar(texto).split("\n") if not l.strip() or re.search(r"\w", l)]
    return limpar("\n".join(linhas))


def _abrir_fitz(caminho):
    try:
        import fitz
    except ImportError:
        return None
    try:
        if hasattr(caminho, "read"):
            caminho.seek(0)
            return fitz.open(stream=caminho.read(), filetype="pdf")
        return fitz.open(str(caminho))
    except Exception:
        return None


def _arquivos_da_pagina(pg, doc_fitz, idx, tmp):
    """Arquivos de imagem a ler por OCR: a página renderizada (fitz) ou as imagens embutidas (pypdf)."""
    # Anotações/widgets também podem ter texto visível sem instruções em /Contents.
    # Só a página sem conteúdo e sem anotações dispensa a renderização e o OCR.
    conteudo = pg.get_contents()
    if (conteudo is None or not conteudo.get_data().strip()) and not pg.get("/Annots"):
        return []
    if doc_fitz is not None:
        alvo = tmp / f"p{idx}.png"
        doc_fitz[idx - 1].get_pixmap(dpi=DPI_OCR).save(str(alvo))
        return [alvo]
    try:
        embutidas = list(pg.images)
    except Exception:
        return []
    prontas = []
    for k, im in enumerate(embutidas):
        alvo = None
        try:
            from PIL import Image
            img = im.image
            if img.size[0] * img.size[1] < 40_000:        # selo, logo, filete
                continue
            if img.mode not in ("RGB", "L"):
                img = img.convert("RGB")
            alvo = tmp / f"p{idx}-{k}.png"
            img.save(alvo, dpi=(DPI_OCR, DPI_OCR))
        except ImportError:
            ext = Path(im.name).suffix.lower()
            if ext in (".jpg", ".jpeg", ".png"):
                alvo = tmp / f"p{idx}-{k}{ext}"
                alvo.write_bytes(im.data)
        except Exception:
            alvo = None
        if alvo:
            prontas.append(alvo)
    return prontas


def ler_paginas_por_ocr(leitor, caminho, paginas, ocr, avisos):
    """OCR das páginas dadas. Devolve {n: texto} só das que deram texto."""
    resultados, tarefas = {}, []
    doc = _abrir_fitz(caminho)
    with tempfile.TemporaryDirectory(prefix="ee-ocr-") as tmp:
        tmp = Path(tmp)
        for i in paginas:
            try:
                arqs = _arquivos_da_pagina(leitor.pages[i - 1], doc, i, tmp)
            except Exception:
                arqs = []
            if not arqs:
                avisos.append([i, "sem imagem embutida (página vetorial sem texto)"])
                continue
            tarefas.append((i, arqs))

        def uma(t):
            i, arqs = t
            try:
                return i, "\n".join(ocr_arquivo(ocr, a) for a in arqs), None
            except Exception as e:
                return i, "", f"OCR falhou ({type(e).__name__}: {str(e)[:80]})"

        with ThreadPoolExecutor(max_workers=max(1, min(4, os.cpu_count() or 1))) as ex:
            for i, txt, erro in ex.map(uma, tarefas):
                if erro:
                    avisos.append([i, erro])
                txt = limpar_ocr(txt)
                if so_letras(txt) >= MIN_LETRAS:
                    resultados[i] = txt
    if doc is not None:
        doc.close()
    return resultados


# ---------------------------------------------------------------- leitores

def ler_pdf(caminho, imagens_dir=None, nome_base="", nome_arquivo=None, ocr=None, info=None):
    """`caminho`: arquivo ou BytesIO. Devolve (texto, paginas, sem_texto [lista de n], imagens [lista de nomes], avisos).
    `nome_arquivo` entra no cabeçalho de cada página. `ocr` (de configurar_ocr) lê por OCR as páginas sem texto;
    `info`, se vier, recebe "ocr_paginas". `sem_texto` são as páginas que continuam sem texto depois do OCR."""
    from pypdf import PdfReader
    leitor = PdfReader(caminho if hasattr(caminho, "read") else str(caminho))
    if leitor.is_encrypted:
        try:
            leitor.decrypt("")
        except Exception:
            raise ValueError("PDF protegido por senha")
    textos, sem_texto, imagens, avisos = {}, [], [], []
    total = len(leitor.pages)
    for i, pg in enumerate(leitor.pages, 1):
        try:
            t = pg.extract_text(extraction_mode="layout") or ""
        except Exception:
            try:
                t = pg.extract_text() or ""
            except Exception:
                t = ""
        t = limpar(t, layout=True)
        if so_letras(t) < MIN_LETRAS:
            sem_texto.append(i)
        else:
            textos[i] = t
    por_ocr = {}
    if ocr and sem_texto:
        print(f"OCR de {len(sem_texto)} página(s){' em ' + nome_arquivo if nome_arquivo else ''}...", flush=True)
        por_ocr = ler_paginas_por_ocr(leitor, caminho, sem_texto, ocr, avisos)
        sem_texto = [i for i in sem_texto if i not in por_ocr]
    if imagens_dir is not None:
        for i in sem_texto:
            nome, aviso = salvar_imagem_pagina(leitor.pages[i - 1], imagens_dir, f"{nome_base}-p{i}")
            if nome:
                imagens.append(nome)
            elif aviso:
                avisos.append([i, aviso])
    visto, unicos = set(), []
    for n, msg in avisos:
        if (n, msg) not in visto:
            visto.add((n, msg))
            unicos.append([n, msg])
    pre = f"{nome_arquivo} · " if nome_arquivo else ""
    partes = []
    for i in range(1, total + 1):
        if i in textos:
            partes.append(f"[{pre}página {i}]\n{textos[i]}")
        elif i in por_ocr:
            partes.append(f"[{pre}página {i} · OCR]\n{por_ocr[i]}")
    if info is not None:
        info["ocr_paginas"] = sorted(por_ocr)
    return "\n\n".join(partes), total, sem_texto, imagens, sorted(unicos)


def salvar_imagem_pagina(pg, pasta, base):
    """Maior imagem embutida da página, reduzida a LARGURA_MAX px. Devolve (nome|None, aviso|None)."""
    try:
        from PIL import Image
    except ImportError:
        return None, "para --imagens instale o Pillow (pip install pillow)"
    try:
        embutidas = list(pg.images)
    except Exception as e:
        return None, f"imagem não lida ({type(e).__name__})"
    if not embutidas:
        return None, "sem imagem embutida (página vetorial sem texto)"
    melhor, melhor_area = None, 0
    for im in embutidas:
        try:
            img = im.image
            area = img.size[0] * img.size[1]
        except Exception:
            continue
        if area > melhor_area:
            melhor, melhor_area = img, area
    if melhor is None:
        return None, "imagem embutida em formato que o Pillow não abre"
    img = melhor
    if img.width > LARGURA_MAX:
        img = img.resize((LARGURA_MAX, max(1, round(img.height * LARGURA_MAX / img.width))), Image.LANCZOS)
    pasta.mkdir(parents=True, exist_ok=True)
    if img.mode in ("RGBA", "LA", "P", "CMYK", "I;16"):
        img = img.convert("RGB")
    nome = f"{base}.jpg"
    img.save(pasta / nome, "JPEG", quality=70, optimize=True)
    return nome, None


def ler_docx(caminho):
    from docx import Document
    from docx.table import Table
    from docx.text.paragraph import Paragraph
    doc = Document(str(caminho))
    linhas = []
    for filho in doc.element.body.iterchildren():
        if filho.tag.endswith("}p"):
            linhas.append(Paragraph(filho, doc).text)
        elif filho.tag.endswith("}tbl"):
            for lin in Table(filho, doc).rows:
                celulas, vistas = [], set()
                for c in lin.cells:
                    if id(c._tc) in vistas:      # célula mesclada repete
                        continue
                    vistas.add(id(c._tc))
                    celulas.append(re.sub(r"\s*\n\s*", " / ", c.text.strip()))
                if any(celulas):
                    linhas.append(" | ".join(celulas))
            linhas.append("")
    return "\n".join(linhas)


def ler_texto(caminho):
    bruto = caminho.read_bytes()
    for enc in ("utf-8-sig", "cp1252"):
        try:
            return bruto.decode(enc)
        except UnicodeDecodeError:
            continue
    return bruto.decode("latin-1")


# ---------------------------------------------------------------- planilhas

def num_br(v):
    """Número sem separador de milhar e com vírgula decimal (1234,5), sem ruído de ponto flutuante."""
    if isinstance(v, float) and v == int(v) and abs(v) < 1e15:
        return str(int(v))
    return format(round(v, 10), ".10g").replace(".", ",")


def celula_texto(v, fmt=""):
    if v is None:
        return ""
    if isinstance(v, bool):
        return "VERDADEIRO" if v else "FALSO"
    if isinstance(v, datetime):
        return v.strftime("%d/%m/%Y") if (v.hour, v.minute, v.second) == (0, 0, 0) else v.strftime("%d/%m/%Y %H:%M")
    if isinstance(v, date):
        return v.strftime("%d/%m/%Y")
    if isinstance(v, hora_t):
        return v.strftime("%H:%M")
    if isinstance(v, (int, float)):
        fmt = fmt or ""
        if "%" in fmt:
            casas = len(re.search(r"\.(0+)", fmt).group(1)) if re.search(r"\.(0+)", fmt) else 0
            return f"{v * 100:.{casas}f}".replace(".", ",") + "%"
        if "R$" in fmt:
            return "R$ " + f"{v:.2f}".replace(".", ",")
        return num_br(float(v)) if isinstance(v, float) else str(v)
    s = re.sub(r"\s*\n\s*", " / ", str(v).replace("\r", "").strip())
    return s.replace("|", "¦")


def tabela_em_trechos(rotulo, linhas):
    """`linhas`: lista de (número da linha na planilha, [células em texto]). Trechos de LINHAS_POR_TRECHO linhas não vazias."""
    cheias = []
    for n, cels in linhas:
        while cels and not cels[-1]:
            cels = cels[:-1]
        if cels:
            cheias.append((n, cels))
    partes = []
    for k in range(0, len(cheias), LINHAS_POR_TRECHO):
        bloco = cheias[k:k + LINHAS_POR_TRECHO]
        partes.append(f"[{rotulo} · linhas {bloco[0][0]} a {bloco[-1][0]}]\n" + "\n".join(" | ".join(c) for _, c in bloco))
    return partes, len(cheias)


def _formulas_sem_valor(ws_formulas, ws_valores):
    """Endereços das células com fórmula cujo valor não foi salvo (o data_only devolve vazio)."""
    achadas = []
    try:
        for n, (lf, lv) in enumerate(zip(ws_formulas.iter_rows(), ws_valores.iter_rows()), 1):
            if n > LINHAS_MAX_ABA:
                break
            for cf, cv in zip(lf, lv):
                f = getattr(cf, "value", None)
                if isinstance(f, str) and f.startswith("=") and getattr(cv, "value", None) is None:
                    achadas.append(f"{cf.coordinate}")
    except Exception:
        pass
    return achadas


def ler_xlsx(caminho, nome_arquivo):
    """Devolve (texto, resumo das abas, avisos). Valores, não fórmulas."""
    try:
        from openpyxl import load_workbook
    except ImportError:
        raise RuntimeError("openpyxl não instalado (pip install -r scripts/requirements.txt)")
    wb = load_workbook(str(caminho), read_only=True, data_only=True)
    try:
        wf = load_workbook(str(caminho), read_only=True, data_only=False)    # só para achar fórmula sem valor salvo
    except Exception:
        wf = None
    partes, resumo, avisos = [], [], []
    try:
        for ws in wb.worksheets:
            try:
                ws.reset_dimensions()
            except Exception:
                pass
            linhas = []
            for n, row in enumerate(ws.iter_rows(), 1):
                if n > LINHAS_MAX_ABA:
                    avisos.append([0, f"aba {ws.title}: cortada em {LINHAS_MAX_ABA} linhas"])
                    break
                linhas.append((n, [celula_texto(c.value, getattr(c, "number_format", "")) for c in row]))
            sem_valor = _formulas_sem_valor(wf[ws.title], ws) if wf is not None else []
            if sem_valor:
                avisos.append([0, f"aba {ws.title}: {len(sem_valor)} célula(s) com fórmula sem valor salvo (planilha nunca aberta no Excel), "
                                  f"ficam fora do texto: {', '.join(sem_valor[:8])}{' e mais' if len(sem_valor) > 8 else ''}. Abrir e salvar no Excel e rodar de novo com --refazer"])
            oculta = " (oculta)" if getattr(ws, "sheet_state", "visible") != "visible" else ""
            ps, nl = tabela_em_trechos(f"{nome_arquivo} · aba {ws.title}{oculta}", linhas)
            partes += ps
            resumo.append(f"{ws.title}: {nl} linhas")
    finally:
        wb.close()
        if wf is not None:
            wf.close()
    return "\n\n".join(partes), resumo, avisos


def decodificar_csv(bruto):
    if bruto[:2] in (b"\xff\xfe", b"\xfe\xff"):
        return bruto.decode("utf-16", "replace")
    if bruto[:3] == b"\xef\xbb\xbf":
        return bruto[3:].decode("utf-8", "replace")
    try:
        return bruto.decode("utf-8")
    except UnicodeDecodeError:
        return bruto.decode("cp1252", "replace")


def detectar_separador(texto):
    """";", ",", tab ou "|": o que dá o mesmo número de colunas (maior que 1) no maior número de linhas iniciais."""
    amostra = texto[:30000].splitlines()[:40]
    melhor, nota = ",", 0
    for d in (";", ",", "\t", "|"):
        cols = [len(r) for r in csv.reader(amostra, delimiter=d) if r]
        if not cols:
            continue
        moda = max(set(cols), key=cols.count)
        pontos = (moda > 1) * cols.count(moda) * moda
        if pontos > nota:
            melhor, nota = d, pontos
    return melhor


def ler_csv(caminho, nome_arquivo):
    """Devolve (texto, resumo, avisos)."""
    csv.field_size_limit(10_000_000)
    texto = decodificar_csv(Path(caminho).read_bytes())
    sep = detectar_separador(texto)
    linhas = []
    for n, row in enumerate(csv.reader(io.StringIO(texto, newline=""), delimiter=sep), 1):
        linhas.append((n, [celula_texto(c) for c in row]))
    partes, nl = tabela_em_trechos(nome_arquivo, linhas)
    nome_sep = {";": "ponto e vírgula", ",": "vírgula", "\t": "tab", "|": "barra"}[sep]
    return "\n\n".join(partes), [f"{nl} linhas, separador {nome_sep}"], []


# ---------------------------------------------------------------- índice

def kb(n):
    return f"{n / 1024:.0f}" if n >= 10 * 1024 or n == 0 else f"{n / 1024:.1f}"


def listar_insumos(pasta):
    achados, ignorados = [], []
    for p in sorted(pasta.rglob("*")):
        if not p.is_file() or PASTA_SAIDA in p.relative_to(pasta).parts[:1]:
            continue
        if p.name.startswith((".", "~$")):
            continue
        (achados if p.suffix.lower() in TIPOS else ignorados).append(p)
    return achados, ignorados


def nomes_de_saida(pasta, arquivos):
    """Um .txt por arquivo. O nome é o do arquivo sem extensão; se repetir, leva a extensão e a subpasta."""
    base = {}
    for p in arquivos:
        rel = p.relative_to(pasta)
        base.setdefault(p.stem if len(rel.parts) == 1 else " - ".join(rel.with_suffix("").parts), []).append(p)
    saida = {}
    for nome, lst in base.items():
        for p in lst:
            n = nome if len(lst) == 1 else f"{nome}.{p.suffix.lower().lstrip('.')}"
            saida[p] = re.sub(r'[<>:"/\\|?*]', "_", n) + ".txt"
    return saida


def faixas(paginas, total=0):
    """[3,4,5,9] -> ["páginas 3 a 5", "página 9"]; todas as páginas -> ["todas as 16 páginas"]."""
    if total and len(paginas) == total and total > 1:
        return [f"todas as {total} páginas"]
    out, i = [], 0
    while i < len(paginas):
        j = i
        while j + 1 < len(paginas) and paginas[j + 1] == paginas[j] + 1:
            j += 1
        out.append(f"página {paginas[i]}" if i == j else f"páginas {paginas[i]} a {paginas[j]}")
        i = j + 1
    return out


def montar_indice(pasta, estado, ignorados, ocr_txt=""):
    linhas = ["# Índice dos insumos extraídos", "",
              f"Pasta: `{pasta.name}`. Texto em `{PASTA_SAIDA}/`, um arquivo por insumo; cada trecho traz o arquivo de origem e a página (ou a aba e as linhas). Leia por aqui, não pelo PDF nem pela planilha original.", "",
              f"OCR: {ocr_txt}", "",
              "| Arquivo | Tipo | Páginas | Caracteres | Original (KB) | Texto (KB) | Data do arquivo | Extraído em | Texto em | Situação |",
              "|---|---|---|---|---|---|---|---|---|---|"]
    tot_orig = tot_txt = 0
    sem_texto, por_ocr = [], []
    for rel, e in sorted(estado.items()):
        if e.get("erro"):
            linhas.append(f"| {rel} | {e['tipo']} | | | {kb(e['tamanho'])} | | {e['data_arquivo']} | {e['extraido_em']} | | erro: {e['erro']} |")
            continue
        situ = "ok"
        if e.get("ocr_paginas"):
            situ = f"{len(e['ocr_paginas'])} página(s) por OCR"
        if e["sem_texto"]:
            situ = (situ + "; " if situ != "ok" else "") + f"{len(e['sem_texto'])} página(s) sem texto"
        pags = e["paginas"] if e["paginas"] else e.get("unidades", "")
        linhas.append(f"| {rel} | {e['tipo']} | {pags} | {e['caracteres']} | {kb(e['tamanho'])} | {kb(e['bytes_texto'])} | {e['data_arquivo']} | {e['extraido_em']} | `{e['saida']}` | {situ} |")
        tot_orig += e["tamanho"]
        tot_txt += e["bytes_texto"]
        for n in e["sem_texto"]:
            sem_texto.append((rel, n, e.get("imagens", {}).get(str(n))))
        if e.get("ocr_paginas"):
            por_ocr.append((rel, e["ocr_paginas"]))
    linhas += ["", f"Total: {kb(tot_orig)} KB de originais, {kb(tot_txt)} KB de texto.", ""]
    if por_ocr:
        linhas += ["## Páginas lidas por OCR", "",
                   "Eram imagem; o texto vem do Tesseract e pode errar número, acento e tabela. Trecho marcado `OCR` no cabeçalho. Número vindo de OCR entra na ficha como não decisivo até o consultor conferir a página.", ""]
        for rel, pgs in por_ocr:
            linhas.append(f"- {rel}: {', '.join(faixas(pgs, total=estado[rel]['paginas']))}")
        linhas.append("")
    if sem_texto:
        linhas += ["## Páginas sem texto", "",
                   "Escaneadas ou só imagem, sem texto lido. Viram imagem (JPEG de até 1000 px, em `imagens/`) quando não há OCR ou com `--imagens`.", ""]
        por_arquivo = {}
        for rel, n, img in sem_texto:
            por_arquivo.setdefault(rel, []).append((n, img))
        for rel, itens in por_arquivo.items():
            for faixa in faixas([n for n, _ in itens], total=estado[rel]["paginas"]):
                linhas.append(f"- {rel}: sem texto, {faixa}")
            for n, img in itens:
                if img:
                    linhas.append(f"  - página {n}: imagem em `{PASTA_SAIDA}/imagens/{img}`")
        linhas.append("")
    avisos = []
    for rel, e in sorted(estado.items()):
        por_msg = {}
        for n, msg in e.get("avisos", []):
            por_msg.setdefault(msg, []).append(n)
        avisos += [f"- {rel}, {', '.join(faixas(ns))}: {msg}" if ns[0] else f"- {rel}: {msg}" for msg, ns in por_msg.items()]
    if avisos:
        linhas += ["## Avisos", ""] + avisos + [""]
    if ignorados:
        linhas += ["## Fora do formato", "", "Tipos que o extrator não lê (abra só se o guia mandar; planilha antiga .xls: salvar como .xlsx):", ""]
        linhas += [f"- {p.relative_to(pasta)}" for p in ignorados] + [""]
    return "\n".join(linhas)


# ---------------------------------------------------------------- principal

def principal():
    ap = argparse.ArgumentParser(description="Extrai texto de PDF, planilha (XLSX, CSV), DOCX, TXT e MD de uma pasta de insumos.")
    ap.add_argument("pasta", help="pasta 0. Inputs e Transcrições do cliente")
    ap.add_argument("--imagens", action="store_true", help="gera JPEG pequeno (até 1000 px) das páginas de PDF que seguem sem texto (sem OCR, isso já é o padrão)")
    ap.add_argument("--sem-ocr", action="store_true", help="não usa o Tesseract")
    ap.add_argument("--refazer", action="store_true", help="ignora o cache")
    a = ap.parse_args()

    pasta = Path(a.pasta).resolve()
    if not pasta.is_dir():
        print(f"Pasta não encontrada: {pasta}")
        return 1
    saida = pasta / PASTA_SAIDA
    saida.mkdir(exist_ok=True)
    arq_estado = saida / ".estado.json"
    try:
        lido = json.loads(arq_estado.read_text(encoding="utf-8")) if arq_estado.exists() and not a.refazer else {}
        estado = lido.get("arquivos", {}) if lido.get("versao") == VERSAO_ESTADO else {}
    except (ValueError, OSError, AttributeError):
        estado = {}

    arquivos, ignorados = listar_insumos(pasta)
    nomes = nomes_de_saida(pasta, arquivos)
    atuais = {p.relative_to(pasta).as_posix() for p in arquivos}
    for rel in list(estado):                      # insumo apagado sai do índice e do disco
        if rel not in atuais:
            old = saida / estado[rel].get("saida", "")
            if estado[rel].get("saida") and old.is_file():
                old.unlink()
            del estado[rel]

    tem_pdf = any(p.suffix.lower() == ".pdf" for p in arquivos)
    if a.sem_ocr:
        ocr, motivo_ocr = None, "desligado (--sem-ocr)"
    elif tem_pdf:
        ocr, motivo_ocr = configurar_ocr()
    else:
        ocr, motivo_ocr = None, "nenhum PDF na pasta"
    quer_imagem = a.imagens or not ocr
    if ocr:
        ocr_txt = f"{ocr['versao']}, idioma {ocr['lang']}" + (f". Aviso: {ocr['aviso']}" if ocr["aviso"] else "")
    else:
        ocr_txt = f"indisponível, {motivo_ocr}."
        if tem_pdf and not a.sem_ocr:
            print(f"OCR indisponível: {motivo_ocr}. PDF só de imagem vira JPEG pequeno em _texto/imagens/.")

    novos = reaproveitados = 0
    for p in arquivos:
        rel = p.relative_to(pasta).as_posix()
        st = p.stat()
        ant = estado.get(rel)
        igual = (ant and ant.get("tamanho") == st.st_size and ant.get("mtime") == int(st.st_mtime)
                 and not ant.get("erro") and (saida / ant["saida"]).is_file())
        precisa_imagem = (quer_imagem and igual and ant["tipo"] == "PDF" and ant["sem_texto"]
                          and len(ant.get("imagens", {})) < len(ant["sem_texto"]) and not ant.get("imagens_tentadas"))
        precisa_ocr = bool(ocr and igual and ant["tipo"] == "PDF" and ant["sem_texto"] and not ant.get("ocr"))
        if igual and not precisa_imagem and not precisa_ocr:
            reaproveitados += 1
            continue
        tipo = TIPOS[p.suffix.lower()]
        reg = {"tipo": tipo, "tamanho": st.st_size, "mtime": int(st.st_mtime),
               "data_arquivo": datetime.fromtimestamp(st.st_mtime).strftime("%d/%m/%Y"),
               "extraido_em": datetime.now().strftime("%d/%m/%Y %H:%M"),
               "saida": nomes[p], "paginas": 0, "caracteres": 0, "bytes_texto": 0, "sem_texto": []}
        try:
            if tipo == "PDF":
                img_dir = (saida / "imagens") if quer_imagem else None
                base = re.sub(r"[^\w.-]+", "_", nomes[p][:-4])
                if (saida / "imagens").is_dir():                      # refazendo: imagem velha não fica solta
                    for velha in (saida / "imagens").glob(f"{base}-p*.jpg"):
                        velha.unlink()
                info = {}
                texto, total, sem, imgs, avisos = ler_pdf(p, img_dir, base, nome_arquivo=p.name, ocr=ocr, info=info)
                reg.update(paginas=total, sem_texto=sem, avisos=avisos, ocr=bool(ocr), ocr_paginas=info.get("ocr_paginas", []))
                if quer_imagem:
                    reg["imagens_tentadas"] = not any("Pillow" in x[1] for x in avisos)
                    reg["imagens"] = {str(n): nome for n, nome in zip(sem, _alinhar(sem, imgs, base))
                                      if nome}
            elif tipo in ("XLSX", "CSV"):
                texto, resumo, avisos = (ler_xlsx if tipo == "XLSX" else ler_csv)(p, p.name)
                reg.update(avisos=avisos, unidades=(f"{len(resumo)} aba(s): " + "; ".join(resumo)) if tipo == "XLSX" else resumo[0])
            elif tipo == "DOCX":
                texto = f"[{p.name}]\n" + limpar(ler_docx(p))
            else:
                texto = f"[{p.name}]\n" + limpar(ler_texto(p))
            (saida / nomes[p]).write_text(texto + "\n", encoding="utf-8")
            reg["caracteres"] = len(texto)
            reg["bytes_texto"] = (saida / nomes[p]).stat().st_size
            novos += 1
        except Exception as e:
            reg["erro"] = f"{type(e).__name__}: {e}"[:160]
            print(f"ERRO em {rel}: {reg['erro']}")
        estado[rel] = reg

    arq_estado.write_text(json.dumps({"versao": VERSAO_ESTADO, "arquivos": estado}, ensure_ascii=False, indent=1), encoding="utf-8")
    (saida / "indice.md").write_text(montar_indice(pasta, estado, ignorados, ocr_txt), encoding="utf-8")

    tot_orig = sum(e["tamanho"] for e in estado.values() if not e.get("erro"))
    tot_txt = sum(e["bytes_texto"] for e in estado.values() if not e.get("erro"))
    n_sem = sum(len(e["sem_texto"]) for e in estado.values())
    n_ocr = sum(len(e.get("ocr_paginas", [])) for e in estado.values())
    n_pag = sum(e["paginas"] for e in estado.values() if e["tipo"] == "PDF" and not e.get("erro"))
    print(f"{len(arquivos)} insumo(s): {novos} extraído(s), {reaproveitados} sem mudança (cache).")
    print(f"Texto: {kb(tot_txt)} KB, contra {kb(tot_orig)} KB de originais. Páginas de PDF: {n_pag}; com texto {n_pag - n_sem} ({n_ocr} por OCR); sem texto {n_sem}.")
    for rel, e in sorted(estado.items()):
        if e["tipo"] == "PDF" and not e.get("erro") and e["paginas"] and len(e["sem_texto"]) == e["paginas"]:
            print(f"Sem texto nenhum (só imagem): {rel}")
    print(f"Índice: {saida / 'indice.md'}")
    return 0


def _alinhar(sem, imgs, base):
    """Casa cada página sem texto com o JPEG gerado (o nome carrega o número da página)."""
    por_pagina = {}
    for nome in imgs:
        m = re.search(r"-p(\d+)\.jpg$", nome)
        if m:
            por_pagina[int(m.group(1))] = nome
    return [por_pagina.get(n) for n in sem]


if __name__ == "__main__":
    sys.exit(principal())
