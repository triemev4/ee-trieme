"""Baixa fontes públicas e grava o texto limpo, uma por arquivo, para o agente ler sem abrir a página crua.

Uso:
    python coletar_fontes.py <lista.txt ou URL> [<URL> ...] --saida <pasta> [--refazer] [--timeout 25] [--parte 25000]
                             [--procurar <procurar.json>]

A lista é um .txt ou .md com uma URL por linha (ou links no meio do texto, como em `base/<setor>/fontes.md`).
Cada URL é baixada com urllib, user-agent de navegador e tempo limite; redirecionamento para outro domínio não é seguido.
HTML: sai o texto sem script, style, nav, footer, aside, formulário e cabeçalho do site; as tabelas saem em linhas
(células separadas por " | "). PDF: texto por página, com o marcador `[página N]`.

Grava em --saida:
  - `<fonte>.txt` por URL, com cabeçalho (URL, título, data da coleta, status). Texto acima de --parte caracteres
    é cortado em `<fonte>.p01.txt`, `.p02.txt`... e nada se perde;
  - `indice.json`: url, status ("ok" ou "falha"), http, arquivo, partes, caracteres, titulo, coletado_em, motivo,
    webfetch (true quando o agente deve abrir a URL pelo WebFetch: 403, JavaScript, tempo, redirecionamento).
URL já coletada com sucesso em rodada anterior não é baixada de novo (--refazer força). O índice acumula as rodadas.

--procurar <procurar.json> (fonte conferida na coleta): o agente diz o que espera achar em cada URL,
  {"https://...": ["7,6 milhões", {"id": "D03", "termo": "12,5%", "contexto": ["inadimplência"]}]}
e o script procura no texto limpo, sem modelo. Número vale em qualquer formato (1.234,5, 1,234.5, 1234,5, 1 234,5;
"7,6 milhões" = 7.600.000 = "7.6 million"; % exige o sinal ou "por cento"); fora disso o termo é texto literal, sem
diferenciar maiúscula. `contexto` (opcional) exige essas palavras perto do achado. Em cada URL do `indice.json` fica
`procurar`: uma linha por termo com achou, status ("conferido na coleta" ou "pendente"), achado, forma (igual ou
equivalente), trecho (frase literal de uma linha, que o grep -F encontra no arquivo), posicao (caractere do texto),
arquivo e linha. URL que só aparece no --procurar também é coletada. Pode rodar de novo com a lista de termos
nova: a fonte já coletada não é baixada, só a busca é refeita.

Requer beautifulsoup4 e pypdf (scripts/requirements.txt).
"""
import sys
sys.dont_write_bytecode = True
import argparse, gzip, hashlib, io, json, re, ssl, time, zlib
import urllib.error, urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"
MAX_BYTES = 30 * 1024 * 1024
MAX_PAGINAS_PDF = 300
MIN_TEXTO_HTML = 300      # abaixo disso a página provavelmente é montada por JavaScript
# página curta com estes sinais é muro (login, robô, JavaScript), não conteúdo
BARREIRA = re.compile(r"conteúdo restrito|necessário autenticar|faça login|just a moment|access denied|"
                      r"verify you are human|enable javascript|habilite o javascript|captcha|acesso negado|"
                      r"attention required|are you a robot", re.I)
REMOVER = ("script", "style", "noscript", "nav", "footer", "aside", "form", "iframe", "svg", "template",
           "button", "select", "dialog")
BLOCOS = {"p", "div", "section", "article", "main", "ul", "ol", "li", "blockquote", "pre", "dl", "dt", "dd",
          "figure", "figcaption", "hr", "address", "details", "summary", "center", "body", "html", "tr", "header"}


class ForaDoDominio(Exception):
    pass


# ---------------------------------------------------------------- rede

def sem_www(host):
    host = (host or "").lower()
    return host[4:] if host.startswith("www.") else host


def mesmo_site(a, b):
    ha = sem_www(urlparse(a).hostname)
    hb = sem_www(urlparse(b).hostname)
    return ha == hb or ha.endswith("." + hb) or hb.endswith("." + ha)


class SoMesmoDominio(urllib.request.HTTPRedirectHandler):
    def __init__(self, origem):
        self.origem = origem

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if not mesmo_site(self.origem, newurl):
            raise ForaDoDominio(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def baixar(url, timeout, verificar=True):
    """Devolve (bytes, content-type, url final, http, aviso)."""
    ctx = ssl.create_default_context()
    if not verificar:
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
    abre = urllib.request.build_opener(SoMesmoDominio(url), urllib.request.HTTPSHandler(context=ctx))
    req = urllib.request.Request(url, headers={
        "User-Agent": UA, "Accept": "text/html,application/xhtml+xml,application/pdf;q=0.9,*/*;q=0.5",
        "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.5", "Accept-Encoding": "gzip, deflate"})
    with abre.open(req, timeout=timeout) as r:
        bruto = r.read(MAX_BYTES + 1)
        if len(bruto) > MAX_BYTES:
            raise ValueError(f"arquivo maior que {MAX_BYTES // 1048576} MB")
        cod = (r.headers.get("Content-Encoding") or "").lower()
        if cod == "gzip" or bruto[:2] == b"\x1f\x8b":
            bruto = gzip.decompress(bruto)
        elif cod == "deflate":
            try:
                bruto = zlib.decompress(bruto)
            except zlib.error:
                bruto = zlib.decompress(bruto, -zlib.MAX_WBITS)
        return bruto, (r.headers.get("Content-Type") or ""), r.geturl(), r.status, ("" if verificar else "certificado não verificado")


def baixar_com_tentativas(url, timeout):
    """Uma nova tentativa em tempo esgotado ou erro 5xx/429; certificado inválido cai para o modo sem verificação."""
    verificar, ultimo = True, None
    for tentativa in range(2):
        try:
            return baixar(url, timeout, verificar)
        except urllib.error.HTTPError as e:
            ultimo = e
            if e.code in (429, 500, 502, 503, 504) and tentativa == 0:
                time.sleep(2)
                continue
            raise
        except (ssl.SSLError, urllib.error.URLError) as e:
            ultimo = e
            razao = getattr(e, "reason", e)
            if verificar and isinstance(razao, ssl.SSLCertVerificationError):
                verificar = False
                continue
            if tentativa == 0 and not isinstance(razao, ssl.SSLError):
                time.sleep(2)
                continue
            raise
        except (TimeoutError, ConnectionError, OSError) as e:
            ultimo = e
            if tentativa == 0:
                time.sleep(2)
                continue
            raise
    raise ultimo


# ---------------------------------------------------------------- HTML

def decodificar(bruto, content_type):
    m = re.search(r"charset=([\w-]+)", content_type, re.I) or re.search(rb"<meta[^>]+charset=[\"']?([\w-]+)", bruto[:4096], re.I)
    if m:
        cs = m.group(1)
        cs = cs.decode() if isinstance(cs, bytes) else cs
        try:
            return bruto.decode(cs, "replace")
        except LookupError:
            pass
    try:
        return bruto.decode("utf-8")
    except UnicodeDecodeError:
        return bruto.decode("cp1252", "replace")


def texto_de(tag):
    return re.sub(r"\s+", " ", tag.get_text(" ")).strip()


def tabela_em_linhas(tbl):
    linhas = []
    cap = tbl.find("caption")
    if cap and texto_de(cap):
        linhas.append(texto_de(cap))
    for tr in tbl.find_all("tr"):
        celulas = [texto_de(c) for c in tr.find_all(["th", "td"], recursive=False)]
        if any(celulas):
            linhas.append(" | ".join(celulas))
    return "\n".join(linhas)


def caminhar(no, buf):
    from bs4 import NavigableString, Comment, Tag
    for filho in no.children:
        if isinstance(filho, Comment):
            continue
        if isinstance(filho, NavigableString):
            buf.append(re.sub(r"\s+", " ", str(filho)))
            continue
        if not isinstance(filho, Tag):
            continue
        n = filho.name
        if n == "table":
            buf.append("\n[tabela]\n" + tabela_em_linhas(filho) + "\n")
        elif n == "br":
            buf.append("\n")
        elif n and re.fullmatch(r"h[1-6]", n):
            buf.append("\n\n" + "#" * int(n[1]) + " ")
            caminhar(filho, buf)
            buf.append("\n")
        elif n == "li":
            buf.append("\n- ")
            caminhar(filho, buf)
            buf.append("\n")
        elif n in BLOCOS:
            buf.append("\n")
            caminhar(filho, buf)
            buf.append("\n")
        else:
            caminhar(filho, buf)


def juntar(buf):
    texto = "".join(buf).replace("\u00a0", " ").replace("\u200b", "").replace("\u00ad", "")
    linhas = [re.sub(r"[ \t]+", " ", l).strip() for l in texto.split("\n")]
    texto = "\n".join(linhas)
    return re.sub(r"\n{3,}", "\n\n", texto).strip()


def limpar_html(html):
    """Devolve (titulo, publicado, texto)."""
    from bs4 import BeautifulSoup
    sopa = BeautifulSoup(html, "html.parser")
    titulo = ""
    if sopa.title and sopa.title.string:
        titulo = re.sub(r"\s+", " ", sopa.title.string).strip()
    if not titulo:
        og = sopa.find("meta", attrs={"property": "og:title"})
        h1 = sopa.find("h1")
        titulo = (og.get("content", "").strip() if og else "") or (texto_de(h1) if h1 else "")
    publicado = ""
    for attrs in ({"property": "article:published_time"}, {"itemprop": "datePublished"}, {"name": "date"},
                  {"name": "pubdate"}, {"name": "DC.date.issued"}):
        meta = sopa.find("meta", attrs=attrs)
        if meta and meta.get("content"):
            publicado = meta["content"].strip()[:25]
            break
    if not publicado:
        t = sopa.find("time", attrs={"datetime": True})
        if t:
            publicado = t["datetime"].strip()[:25]
    for t in sopa.find_all(REMOVER):
        t.decompose()
    for t in sopa.find_all("header"):         # cabeçalho do site sai; o do artigo (título e data) fica
        if not t.find_parent(["article", "main"]):
            t.decompose()
    for t in sopa.find_all(attrs={"role": re.compile(r"^(navigation|banner|contentinfo|search|complementary)$")}):
        t.decompose()
    for t in sopa.find_all(attrs={"id": re.compile(r"cookie|consent|lgpd|gdpr", re.I)}) + \
            sopa.find_all(attrs={"class": re.compile(r"cookie|consent|lgpd|gdpr", re.I)}):
        if t.parent is not None and len(texto_de(t)) < 1500:
            t.decompose()
    corpo = sopa.body or sopa
    completo = []
    caminhar(corpo, completo)
    completo = juntar(completo)
    principais = sopa.find_all(["main", "article"]) + sopa.find_all(attrs={"role": "main"})
    melhor = None
    for c in principais:
        buf = []
        caminhar(c, buf)
        txt = juntar(buf)
        if melhor is None or len(txt) > len(melhor):
            melhor = txt
    if melhor and len(melhor) >= 0.5 * len(completo):
        completo = melhor
    return titulo, publicado, completo


# ---------------------------------------------------------------- saída

def nome_de(url):
    p = urlparse(url)
    base = re.sub(r"[^a-z0-9]+", "-", (sem_www(p.hostname) + p.path).lower()).strip("-")[:60].strip("-")
    return f"{base}-{hashlib.sha1(url.encode()).hexdigest()[:6]}"


def partir(texto, tamanho):
    """Corta em partes de até `tamanho` caracteres, na quebra de parágrafo ou de linha mais próxima."""
    if len(texto) <= tamanho:
        return [texto]
    partes, ini = [], 0
    while ini < len(texto):
        fim = min(ini + tamanho, len(texto))
        if fim < len(texto):
            corte = texto.rfind("\n\n", ini + tamanho // 2, fim)
            if corte == -1:
                corte = texto.rfind("\n", ini + tamanho // 2, fim)
            if corte != -1:
                fim = corte
        partes.append(texto[ini:fim].strip())
        ini = fim
    return [p for p in partes if p]


def gravar(pasta, nome, url, titulo, publicado, quando, aviso, texto, tamanho_parte):
    partes = partir(texto, tamanho_parte)
    arquivos = []
    for i, parte in enumerate(partes, 1):
        arq = f"{nome}.txt" if len(partes) == 1 else f"{nome}.p{i:02d}.txt"
        cab = [f"URL: {url}", f"Título: {titulo or '(sem título)'}", f"Coletado em: {quando}"]
        if publicado:
            cab.append(f"Publicado: {publicado}")
        cab.append("Status: ok" + (f" ({aviso})" if aviso else ""))
        if len(partes) > 1:
            cab.append(f"Parte: {i} de {len(partes)}")
        (pasta / arq).write_text("\n".join(cab) + "\n---\n" + parte + "\n", encoding="utf-8")
        arquivos.append(arq)
    return arquivos


def obter_texto(url, timeout):
    """Baixa a URL e devolve o texto limpo. Dict: http, titulo, publicado, texto, aviso e, quando a página
    não serve (PDF escaneado, bloqueio, JavaScript, tipo estranho), falha=True com motivo e webfetch.
    Erro de rede e HTTP sobem como exceção."""
    from extrair_insumos import ler_pdf
    bruto, ctype, final, http, aviso = baixar_com_tentativas(url, timeout)
    r = {"http": http, "titulo": "", "publicado": "", "texto": "", "aviso": aviso, "final": final}
    if bruto[:5] == b"%PDF-" or "pdf" in ctype.lower():
        texto, total, sem_texto, _, _ = ler_pdf(io.BytesIO(bruto))
        r["titulo"] = Path(urlparse(final).path).name
        if total > MAX_PAGINAS_PDF:
            r["aviso"] = (r["aviso"] + "; " if r["aviso"] else "") + f"PDF com {total} páginas"
        if len(texto) < 50:
            r.update(falha=True, webfetch=True, motivo="PDF sem texto (escaneado): abrir pelo WebFetch ou ler a imagem da página decisiva")
            return r
        if sem_texto:
            r["aviso"] = (r["aviso"] + "; " if r["aviso"] else "") + f"{len(sem_texto)} página(s) sem texto"
        r["texto"] = texto
    elif any(t in ctype.lower() for t in ("html", "xml", "text/plain")) or bruto[:200].lstrip().lower().startswith((b"<!doctype", b"<html")):
        html = decodificar(bruto, ctype)
        titulo, publicado, texto = limpar_html(html)
        r.update(titulo=titulo, publicado=publicado, texto=texto)
        barreira = BARREIRA.search(texto) if len(texto) < 2500 else None
        if len(texto) < MIN_TEXTO_HTML or barreira:
            r.update(falha=True, webfetch=True, motivo=(f"página de bloqueio ou login ('{barreira.group(0)}')" if barreira
                     else f"texto quase vazio ({len(texto)} caracteres): provável página montada por JavaScript"))
    else:
        r.update(falha=True, webfetch=False, motivo=f"tipo não suportado ({ctype.split(';')[0] or 'desconhecido'})")
    return r


def coletar_uma(url, pasta, timeout, tamanho_parte):
    quando = datetime.now().strftime("%Y-%m-%d %H:%M")
    reg = {"url": url, "status": "falha", "http": None, "arquivo": None, "partes": [], "caracteres": 0,
           "titulo": "", "coletado_em": quando, "motivo": "", "webfetch": True}
    try:
        info = obter_texto(url, timeout)
        reg["http"] = info["http"]
        if info.get("falha"):
            reg["titulo"], reg["caracteres"] = info["titulo"], len(info["texto"])
            reg["motivo"], reg["webfetch"] = info["motivo"], info["webfetch"]
            return reg
        titulo, publicado, texto, aviso = info["titulo"], info["publicado"], info["texto"], info["aviso"]
        nome = nome_de(url)
        arquivos = gravar(pasta, nome, url, titulo, publicado, quando, aviso, texto, tamanho_parte)
        reg.update(status="ok", arquivo=arquivos[0], partes=arquivos, caracteres=len(texto), titulo=titulo,
                   motivo=aviso, webfetch=False)
        if publicado:
            reg["publicado"] = publicado
    except ForaDoDominio as e:
        reg["motivo"] = f"redirecionou para outro domínio: {e}"
    except urllib.error.HTTPError as e:
        reg["http"] = e.code
        reg["motivo"] = f"HTTP {e.code} {e.reason}" + (" (bloqueia robô)" if e.code in (401, 403, 429) else "")
        reg["webfetch"] = e.code not in (404, 410)
        if e.code in (404, 410):
            reg["motivo"] += ": link não existe; procurar o mesmo dado em outra fonte"
    except Exception as e:
        razao = getattr(e, "reason", e)
        if isinstance(e, TimeoutError) or "timed out" in str(razao):
            reg["motivo"] = f"tempo esgotado ({timeout} s)"
        else:
            reg["motivo"] = f"{type(e).__name__}: {razao}"[:200]
    return reg


# ---------------------------------------------------------------- busca de número e termo (--procurar)

LETRA = r"A-Za-zÀ-ÿ"
_ESC = (r"milh(?:ão|ões|ao|oes)|bilh(?:ão|ões|ao|oes)|trilh(?:ão|ões|ao|oes)|mil|thousand|millions?|billions?|"
        r"trillions?|mi|bi|mn|bn|k")
ESCALA_TXT = {"mil": 10 ** 3, "k": 10 ** 3, "thousand": 10 ** 3, "milhao": 10 ** 6, "milhoes": 10 ** 6, "mi": 10 ** 6,
              "mn": 10 ** 6, "million": 10 ** 6, "millions": 10 ** 6, "bilhao": 10 ** 9, "bilhoes": 10 ** 9, "bi": 10 ** 9,
              "bn": 10 ** 9, "billion": 10 ** 9, "billions": 10 ** 9, "trilhao": 10 ** 12, "trilhoes": 10 ** 12,
              "trillion": 10 ** 12, "trillions": 10 ** 12}
_PCT = r"%|por[  ]cento|percent"
# número com milhar (1.234,5 / 1,234.5 / 1 234) ou simples (1234,5 / 12.5), sem colar em outro número
TOKEN = re.compile(r"(?<![\d.,])(\d{1,3}(?:[.,\u0020\u00a0\u2009\u202f]\d{3})+(?:[.,]\d+)?|\d+(?:[.,]\d+)?)(?!\d|[.,]\d)")
# TOKEN_ESPACO foi fundido no TOKEN: um grupo de milhar solto ("261" de "361 261") nunca vira número sozinho
SUFIXO = re.compile(r"[  ]{0,2}(?:(?P<esc>" + _ESC + r")(?![" + LETRA + r"]))?[  ]{0,2}(?P<pct>(?:" + _PCT + r")(?![" + LETRA + r"]))?", re.I)
TERMO_NUMERO = re.compile(r"^\s*(?:R\$|US\$|€|\$)?\s*[-+]?(?P<n>\d[\d.,\u0020\u00a0\u2009\u202f]*)\s*(?:(?P<esc>" + _ESC + r")(?![" + LETRA + r"]))?\s*(?P<pct>(?:" + _PCT + r"))?\s*$", re.I)


def sem_acento(s):
    import unicodedata
    return "".join(c for c in unicodedata.normalize("NFD", str(s)) if unicodedata.category(c) != "Mn").lower().strip()


def leituras(tok):
    """Valores possíveis de um número escrito. Brasileiro primeiro (1.234 é mil duzentos e trinta e quatro;
    1,234 é um vírgula duzentos e trinta e quatro); o internacional entra quando o texto é ambíguo."""
    from decimal import Decimal
    s = re.sub(r"[\u0020\u00a0\u2009\u202f]", "", tok)
    pontos, virgulas = s.count("."), s.count(",")
    try:
        if pontos and virgulas:
            dec = "," if s.rfind(",") > s.rfind(".") else "."
            mil = "." if dec == "," else ","
            inteiro, frac = s.rsplit(dec, 1)
            if not re.fullmatch(r"\d{1,3}(?:%s\d{3})+" % re.escape(mil), inteiro):
                return []
            return [Decimal(inteiro.replace(mil, "") + "." + frac)]
        if virgulas or pontos:
            sep = "," if virgulas else "."
            partes = s.split(sep)
            if len(partes) > 2:                                   # 1.234.567 (br) ou 1,234,567 (internacional)
                ok = all(len(x) == 3 for x in partes[1:]) and 1 <= len(partes[0]) <= 3
                return [Decimal("".join(partes))] if ok else []
            ambiguo = len(partes[1]) == 3 and 1 <= len(partes[0]) <= 3 and not partes[0].startswith("0")
            como_decimal, como_milhar = Decimal(partes[0] + "." + partes[1]), Decimal(partes[0] + partes[1])
            if not ambiguo:
                return [como_decimal]
            return [como_milhar, como_decimal] if sep == "." else [como_decimal, como_milhar]
        return [Decimal(s)]
    except Exception:
        return []


def alvo_numerico(termo):
    """Termo numérico ("7,6 milhões", "12,5%", "R$ 54,50", "1,234.5") -> (valor, percentual) ou None."""
    m = TERMO_NUMERO.match(str(termo))
    if not m:
        return None
    lei = leituras(m.group("n"))
    if not lei:
        return None
    mult = ESCALA_TXT[sem_acento(m.group("esc"))] if m.group("esc") else 1
    return lei[0] * mult, bool(m.group("pct"))


def _ocorrencias_numero(texto, alvo, pct, ignora_escala=False):
    """Posições (início, fim) dos números do texto que valem `alvo`, em qualquer formato."""
    achados = []
    for m in TOKEN.finditer(texto):
        lei = leituras(m.group(1))
        if not lei:
            continue
        suf = SUFIXO.match(texto, m.end(), min(len(texto), m.end() + 30))
        esc, pc = suf.group("esc"), suf.group("pct")
        fim = m.end()
        if esc:
            fim = max(fim, suf.end("esc"))
        if pc:
            fim = max(fim, suf.end("pct"))
        mult = ESCALA_TXT[sem_acento(esc)] if esc else 1
        if any(v * mult == alvo or (ignora_escala and v == alvo) for v in lei) and (pc or not pct):
            achados.append((m.start(), fim))
    return sorted(set(achados))


def _ocorrencias_texto(texto, termo):
    partes = [re.escape(p) for p in termo.split()]
    if not partes:
        return []
    padrao = r"\s+".join(partes)
    if re.match(r"\w", termo):
        padrao = r"(?<!\w)" + padrao
    if re.search(r"\w$", termo):
        padrao += r"(?!\w)"
    return [(m.start(), m.end()) for m in re.finditer(padrao, texto, re.I)]


def _trecho(texto, ini, fim, raio=150):
    """Frase literal em volta, de uma linha só, sem cortar palavra."""
    ls = texto.rfind("\n", 0, ini) + 1
    le = texto.find("\n", fim)
    le = len(texto) if le == -1 else le
    lo, hi = max(ls, ini - raio), min(le, fim + raio)
    if lo > ls:
        while lo < ini and not texto[lo - 1].isspace():
            lo += 1
    if hi < le:
        while hi > fim and not texto[hi].isspace():
            hi -= 1
    return texto[lo:hi].strip()


def procurar_termo(corpo, entrada):
    """Procura um número ou termo no texto coletado. `entrada`: {termo, id?, contexto?}. Devolve o registro
    que vai para o índice: achou, status, trecho literal, posição (caractere do texto; arquivo e linha vêm depois)."""
    termo = str(entrada.get("termo", "")).strip()
    contexto = [str(c).strip() for c in (entrada.get("contexto") or []) if str(c).strip()]
    reg = {"termo": termo, "tipo": "texto", "achou": False, "status": "pendente",
           "procurado_em": datetime.now().strftime("%Y-%m-%d %H:%M")}
    if entrada.get("id"):
        reg["id"] = str(entrada["id"])
    if contexto:
        reg["contexto"] = contexto
    alvo = alvo_numerico(termo)
    if alvo:
        reg["tipo"] = "numero"
        posicoes = _ocorrencias_numero(corpo, alvo[0], alvo[1])
    else:
        posicoes = _ocorrencias_texto(corpo, termo)
    if contexto:
        cs = [sem_acento(c) for c in contexto]
        posicoes = [(a, b) for a, b in posicoes if all(c in sem_acento(corpo[max(0, a - 250):b + 250]) for c in cs)]
    if not posicoes:
        reg["motivo"] = ("número não aparece no texto limpo da página" if alvo else "termo não aparece no texto limpo da página") + \
            (" com o contexto pedido" if contexto else "") + " (pode estar em imagem, gráfico ou montado por JavaScript)"
        return reg
    def norm(x):
        return re.sub(r"\s+", " ", x).strip().lower()
    a, b = next(((x, y) for x, y in posicoes if norm(corpo[x:y]) == norm(termo)), posicoes[0])   # prefere a escrita igual
    achado = corpo[a:b]
    igual = norm(achado) == norm(termo)
    reg.update(achou=True, status="conferido na coleta", achado=achado, forma="igual" if igual else "equivalente",
               trecho=_trecho(corpo, a, b), posicao=a, ocorrencias=len(posicoes))
    return reg


def ler_corpo(pasta, reg):
    """Texto de uma fonte coletada (todas as partes) e o mapa [(início no texto, arquivo, linha em que o texto começa)]."""
    pedacos, mapa, pos = [], [], 0
    arquivos = reg.get("partes") or ([reg["arquivo"]] if reg.get("arquivo") else [])
    for arq in arquivos:
        txt = (Path(pasta) / arq).read_text(encoding="utf-8")
        i = txt.find("\n---\n")
        corpo, linha0 = (txt, 1) if i == -1 else (txt[i + 5:], txt[:i + 5].count("\n") + 1)
        corpo = corpo[:-1] if corpo.endswith("\n") else corpo
        mapa.append((pos, arq, linha0))
        pedacos.append(corpo)
        pos += len(corpo) + 1
    return "\n".join(pedacos), mapa


def onde(corpo, mapa, posicao):
    """Arquivo e linha (como o grep -n do arquivo mostra) de uma posição do texto."""
    ini, arq, linha0 = [m for m in mapa if m[0] <= posicao][-1]
    return arq, linha0 + corpo.count("\n", ini, posicao)


def aplicar_procurar(pasta, reg, entradas):
    """Roda a busca de cada entrada sobre a fonte coletada e devolve a lista para o índice."""
    if reg.get("status") != "ok":
        saida = []
        for e in entradas:
            r = {"termo": str(e.get("termo", "")).strip(), "achou": False, "status": "pendente",
                 "motivo": f"fonte não coletada: {reg.get('motivo') or 'falha'}",
                 "procurado_em": datetime.now().strftime("%Y-%m-%d %H:%M")}
            if e.get("id"):
                r["id"] = str(e["id"])
            saida.append(r)
        return saida
    corpo, mapa = ler_corpo(pasta, reg)
    saida = []
    for e in entradas:
        r = procurar_termo(corpo, e)
        if r["achou"]:
            r["arquivo"], r["linha"] = onde(corpo, mapa, r["posicao"])
        saida.append(r)
    return saida


def chave_busca(r):
    return (r.get("id", ""), r.get("termo", ""), tuple(r.get("contexto") or ()))


def juntar_buscas(antigas, novas):
    por = {chave_busca(r): r for r in antigas or []}
    for r in novas:
        por[chave_busca(r)] = r
    return list(por.values())


def entradas_procurar(caminho):
    """Lê o arquivo --procurar: {url: [termo ou {termo, id?, contexto?}]} ou [{url, termos: [...]}]."""
    dados = json.loads(Path(caminho).read_text(encoding="utf-8"))
    if isinstance(dados, list):
        dados = {d["url"]: d.get("termos", []) for d in dados if isinstance(d, dict) and d.get("url")}
    if not isinstance(dados, dict):
        raise ValueError("esperava {url: [termos]}")
    saida = {}
    for url, termos in dados.items():
        lista = []
        for t in termos if isinstance(termos, list) else [termos]:
            e = {"termo": t} if isinstance(t, (str, int, float)) else dict(t)
            e["termo"] = str(e.get("termo", e.get("valor", ""))).strip()
            e["contexto"] = [str(c).strip() for c in (e.get("contexto") or []) if str(c).strip()]
            if e.get("id"):
                e["id"] = str(e["id"])
            else:
                e.pop("id", None)
            if e["termo"]:
                lista.append(e)
        saida[url] = lista
    return saida


def mesma_url(a, b):
    return str(a).strip().split("#")[0].rstrip("/") == str(b).strip().split("#")[0].rstrip("/")


def conferir_na_coleta(link, valor, ident, pasta):
    """Para o calcular.py: o valor desta linha do pesquisador foi achado na página da coleta? Reabre o texto salvo
    e refaz a busca (não confia no que está gravado no índice). Devolve (ok, descrição ou motivo)."""
    pasta = Path(pasta)
    try:
        indice = json.loads((pasta / "indice.json").read_text(encoding="utf-8"))
        reg = next((r for r in indice if mesma_url(r.get("url", ""), link)), None)
    except (OSError, ValueError, TypeError):
        return False, f"não há coleta em {pasta} (falta o indice.json)"
    if reg is None:
        return False, f"a URL {link} não foi coletada"
    if reg.get("status") != "ok":
        return False, f"a coleta de {link} falhou ({reg.get('motivo') or 'sem motivo'})"
    alvo = alvo_numerico(valor)
    candidatas = []
    for b in reg.get("procurar") or []:
        if not b.get("achou"):
            continue
        ba = alvo_numerico(b.get("termo", ""))
        if alvo is not None:
            mesmo = ba is not None and ba[0] == alvo[0] and (ba[1] == alvo[1] or not (ba[1] or alvo[1]))
        else:
            mesmo = str(b.get("termo", "")).strip() == str(valor).strip()
        if mesmo:
            candidatas.append(b)
    if not candidatas:
        return False, f"o valor {valor!r} não foi procurado na página (rode o coletor com --procurar) ou não foi achado"
    try:
        corpo, mapa = ler_corpo(pasta, reg)
    except OSError as e:
        return False, f"texto coletado ilegível: {e}"
    for b in sorted(candidatas, key=lambda b: b.get("id") != ident):
        r = procurar_termo(corpo, b)
        if r["achou"]:
            arq, linha = onde(corpo, mapa, r["posicao"])
            return True, f"{arq} linha {linha}"
    return False, f"o texto coletado de {link} não tem mais o valor {valor!r}"


# ---------------------------------------------------------------- entrada

def urls_de(entradas):
    achadas = []
    for e in entradas:
        if re.match(r"https?://", e):
            achadas.append(e)
            continue
        p = Path(e)
        if not p.is_file():
            print(f"Aviso: nem URL nem arquivo: {e}")
            continue
        for u in re.findall(r"https?://[^\s<>\"')\]|]+", p.read_text(encoding="utf-8", errors="replace")):
            achadas.append(u.rstrip(".,;:"))
    vistas, saida = set(), []
    for u in achadas:
        if u not in vistas:
            vistas.add(u)
            saida.append(u)
    return saida


def principal():
    ap = argparse.ArgumentParser(description="Baixa URLs e grava o texto limpo, uma fonte por arquivo.")
    ap.add_argument("entradas", nargs="+", help="lista .txt/.md com URLs, ou as URLs")
    ap.add_argument("--saida", required=True, help="pasta de saída (criada se não existir)")
    ap.add_argument("--timeout", type=int, default=25, help="segundos por tentativa (padrão 25)")
    ap.add_argument("--parte", type=int, default=25000, help="caracteres por parte do texto (padrão 25000)")
    ap.add_argument("--refazer", action="store_true", help="baixa de novo mesmo o que já foi coletado")
    ap.add_argument("--paralelo", type=int, default=4, help="downloads ao mesmo tempo (padrão 4)")
    ap.add_argument("--procurar", help="JSON {url: [termos]}: procura cada número ou termo no texto coletado e grava o trecho")
    a = ap.parse_args()

    procurar = {}
    if a.procurar:
        try:
            procurar = entradas_procurar(a.procurar)
        except (OSError, ValueError, KeyError, TypeError) as e:
            print(f"ERRO --procurar: {e}")
            return 1
    urls = urls_de(a.entradas)
    for u in procurar:
        if u not in urls:
            urls.append(u)
    if not urls:
        print("Nenhuma URL encontrada.")
        return 1
    pasta = Path(a.saida)
    pasta.mkdir(parents=True, exist_ok=True)
    arq_indice = pasta / "indice.json"
    anterior = {}
    if arq_indice.exists():
        try:
            anterior = {r["url"]: r for r in json.loads(arq_indice.read_text(encoding="utf-8"))}
        except (ValueError, KeyError, TypeError):
            anterior = {}

    def trabalho(u):
        ant = anterior.get(u)
        if ant and ant.get("status") == "ok" and not a.refazer and all((pasta / f).is_file() for f in ant.get("partes", [])):
            reg, cache = dict(ant), True
        else:
            reg, cache = coletar_uma(u, pasta, a.timeout, a.parte), False
        if u in procurar and procurar[u]:
            reg["procurar"] = juntar_buscas(reg.get("procurar"), aplicar_procurar(pasta, reg, procurar[u]))
        return reg, cache

    with ThreadPoolExecutor(max_workers=max(1, a.paralelo)) as ex:
        resultados = list(ex.map(trabalho, urls))

    novo = dict(anterior)
    for reg, _ in resultados:
        novo[reg["url"]] = reg
    arq_indice.write_text(json.dumps(list(novo.values()), ensure_ascii=False, indent=1), encoding="utf-8")

    ok = [r for r, _ in resultados if r["status"] == "ok"]
    cache = sum(1 for _, c in resultados if c)
    print(f"{len(urls)} URL(s): {len(ok)} ok ({cache} já coletadas), {len(urls) - len(ok)} com falha. Índice: {arq_indice}")
    for r, _ in resultados:
        if r["status"] == "ok":
            extra = f", {len(r['partes'])} partes" if len(r["partes"]) > 1 else ""
            print(f"  ok     {r['caracteres']:>7} car  {r['arquivo']}{extra}  <- {r['url']}")
    for r, _ in resultados:
        if r["status"] != "ok":
            print(f"  FALHA  {r['motivo']}  <- {r['url']}" + ("  [abrir pelo WebFetch]" if r["webfetch"] else ""))
    if procurar:
        pedidos = {(u, chave_busca(e)) for u, es in procurar.items() for e in es}
        achei = nao = 0
        for r, _ in resultados:
            for b in r.get("procurar") or []:
                if (r["url"], chave_busca(b)) not in pedidos:
                    continue
                if b["achou"]:
                    achei += 1
                    print(f"  ACHOU  {b['termo']!r} em {b['arquivo']} linha {b['linha']} ({b['forma']}): {b['trecho'][:110]}")
                else:
                    nao += 1
                    print(f"  NAO ACHOU  {b['termo']!r}  <- {r['url']}  ({b.get('motivo', '')})")
        print(f"Busca: {achei} achado(s), {nao} pendente(s). O que não foi achado fica pendente: sem o trecho, o número não entra.")
    return 0


if __name__ == "__main__":
    sys.exit(principal())
