"""Coleta mecânica da auditoria da Semana 3 (R15): prints do site e do Google Meu Negócio, velocidade pelo
PageSpeed Insights e os dados de SEO de cada página. A IA só interpreta o que sai daqui.

Uso:
    python coletar_auditoria.py --site <url> [--gmn <url ou "Nome, Cidade">] --saida <pasta da semana>/_fonte/auditoria
        [--paginas 4] [--pagina-inteira] [--sem-prints] [--sem-velocidade] [--timeout 30] [--navegador msedge,chrome]

O que faz:
  (a) Prints do site em computador (1440 px) e celular (390 px, user-agent de celular): a página inicial e até
      --paginas páginas internas principais (links do menu e do cabeçalho primeiro, uma por seção do site).
      Navegador sem tela pelo playwright, usando o Edge ou o Chrome já instalado (nada é baixado). O playwright é
      opcional: sem ele os prints são pulados com aviso e o resto segue.
  (b) Print do Google Meu Negócio, quando --gmn vem (URL do perfil, ou nome e cidade para buscar no Google Maps).
  (c) Velocidade pela API pública do PageSpeed Insights (mobile e desktop, sem chave). Se o limite estourar, a chave
      gratuita entra pela variável de ambiente PAGESPEED_API_KEY. Guarda o dado de laboratório (Lighthouse), marcado
      como laboratório, e o dado de campo (CrUX, usuários reais) quando existir, com a data da coleta como fonte.
  (d) Por página: título, meta descrição, H1 (quantos e quais), canonical, dados estruturados (tipos do JSON-LD) e
      imagens sem alt.
  (e) `auditoria.json` (tudo, para script e molde) e `auditoria.md` (curto, para a IA ler).

Grava em --saida: auditoria.json, auditoria.md, prints/*.jpg (home-desktop.jpg, home-celular.jpg, <pagina>-desktop.jpg...)
e gmn.jpg. O print é a primeira dobra da página; --pagina-inteira grava também a página toda (até 8000 px).
Os caminhos que entram no JSON da Semana 3 (data-img do molde) saem em `molde_s3` do auditoria.json, já relativos
à pasta pai de --saida, onde fica o `textos.json` (em `_fonte/`), com o nome da pasta de saída na frente
(`auditoria/prints/home-desktop.jpg`). Pode copiar o valor direto para o JSON da semana. Os demais caminhos de
prints (em `paginas`) continuam relativos à própria pasta de --saida.

Requer beautifulsoup4 (scripts/requirements.txt). Opcional: playwright (python -m pip install --user playwright).
"""
import sys
sys.dont_write_bytecode = True
import argparse, json, os, re, socket, ssl, time
import urllib.error, urllib.parse, urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

UA_DESKTOP = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
              "Chrome/126.0 Safari/537.36")
UA_CELULAR = ("Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) "
              "Chrome/126.0 Mobile Safari/537.36")
PSI_URL = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"
DESKTOP = (1440, 900)
CELULAR = (390, 844)
ALTURA_MAX_INTEIRA = 8000
# esperas entre as tentativas do PageSpeed (o limite sem chave estoura fácil); o teste zera pela variável de ambiente
ESPERAS_PSI = tuple(float(x) for x in os.environ.get("EE_PSI_ESPERAS", "0,6,18").split(","))
QUALIDADE_JPEG = 82

# links que não são página principal
EXT_FORA = re.compile(r"\.(pdf|jpe?g|png|gif|webp|svg|zip|rar|docx?|xlsx?|pptx?|mp[34]|xml|json|txt)$", re.I)
CAMINHO_FORA = re.compile(r"/(wp-admin|wp-login|wp-json|login|entrar|cadastr[\w-]*|minha-conta|conta|carrinho|cart|"
                          r"checkout|finalizar[\w-]*|politica[\w-]*|privacidade[\w-]*|privacy[\w-]*|termos[\w-]*|"
                          r"terms[\w-]*|cookies?|lgpd|feed|tag|author|autor|busca|search|cdn-cgi)(/|$)", re.I)
ESQUEMAS_FORA = ("mailto:", "tel:", "javascript:", "whatsapp:", "sms:", "data:")
HOSTS_FORA = ("wa.me", "api.whatsapp.com", "web.whatsapp.com")

BANNER_JS = """() => {
  const re = /^(aceitar( todos)?( os cookies)?|aceito|concordo|entendi|permitir( todos)?|ok|accept( all)?( cookies)?|allow all|got it|i agree)$/i;
  const ctx = /cookie|consent|lgpd|gdpr|privacy|privacidade/i;
  const els = [...document.querySelectorAll('button,[role=button],a,input[type=button],input[type=submit]')];
  for (const el of els) {
    const t = (el.innerText || el.value || '').trim();
    if (!t || t.length > 30 || !re.test(t)) continue;
    const r = el.getBoundingClientRect();
    if (r.width <= 0 || r.height <= 0) continue;
    let a = el, ok = false;
    for (let i = 0; i < 7 && a; i++, a = a.parentElement) {
      const p = getComputedStyle(a).position;
      if (p === 'fixed' || p === 'sticky' || ctx.test((a.id || '') + ' ' + (a.className || ''))) { ok = true; break; }
    }
    if (ok) { el.click(); return t; }
  }
  return null;
}"""


def aviso(avisos, texto):
    avisos.append(texto)
    print("AVISO: " + texto)


# ---------------------------------------------------------------- endereços

def normaliza_site(url):
    url = url.strip()
    if not re.match(r"^[a-z][a-z0-9+.-]*://", url, re.I):
        url = "https://" + url
    p = urllib.parse.urlsplit(url)
    if not p.netloc:
        raise ValueError(f"URL inválida: {url}")
    return urllib.parse.urlunsplit((p.scheme, p.netloc, p.path or "/", p.query, ""))


def sem_www(host):
    host = (host or "").lower()
    return host[4:] if host.startswith("www.") else host


def mesmo_site(a, b):
    ha, hb = sem_www(urllib.parse.urlsplit(a).hostname), sem_www(urllib.parse.urlsplit(b).hostname)
    # mesmo host (com ou sem www): subdomínio (loja., blog., docs.) é outro site, não página interna
    return bool(ha) and ha == hb


def chave_url(url):
    """Mesma página, em qualquer grafia: sem www, sem barra final, sem busca e sem âncora."""
    p = urllib.parse.urlsplit(url)
    return sem_www(p.hostname) + (p.path.rstrip("/") or "")


def slug_pagina(url, usados):
    caminho = urllib.parse.urlsplit(url).path.strip("/")
    s = re.sub(r"[^a-z0-9]+", "-", caminho.lower()).strip("-")[:40] or "pagina"
    base, n = s, 2
    while s in usados:
        s, n = f"{base}-{n}", n + 1
    usados.add(s)
    return s


def escolhe_internas(html, base_url, quantas):
    """Até `quantas` páginas internas principais, como (url, texto do link): menu e cabeçalho primeiro, uma por
    seção, caminho curto."""
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, "html.parser")
    topo = set()
    for no in soup.find_all(["nav", "header"]):
        for a in no.find_all("a", href=True):
            topo.add(id(a))
    candidatos, vistos = [], {chave_url(base_url)}
    for ordem, a in enumerate(soup.find_all("a", href=True)):
        href = a["href"].strip()
        if not href or href.startswith("#") or href.lower().startswith(ESQUEMAS_FORA):
            continue
        url = urllib.parse.urljoin(base_url, href)
        p = urllib.parse.urlsplit(url)
        if p.scheme not in ("http", "https") or not mesmo_site(base_url, url) or (p.hostname or "") in HOSTS_FORA:
            continue
        if EXT_FORA.search(p.path) or CAMINHO_FORA.search(p.path + "/"):
            continue
        k = chave_url(url)
        if k in vistos:
            continue
        vistos.add(k)
        segmentos = [s for s in p.path.split("/") if s]
        texto = re.sub(r"\s+", " ", a.get_text(" ")).strip()[:40]
        candidatos.append((id(a) not in topo, len(segmentos), ordem, urllib.parse.urlunsplit((p.scheme, p.netloc, p.path, "", "")),
                           segmentos[:1], texto))
    candidatos.sort(key=lambda c: c[:3])
    escolhidas, secoes = [], set()
    for _, _, _, url, secao, texto in candidatos:
        s = tuple(secao)
        if s in secoes:
            continue
        secoes.add(s)
        escolhidas.append((url, texto))
        if len(escolhidas) >= quantas:
            break
    return escolhidas


# ---------------------------------------------------------------- SEO por página

def analisa_html(html, url):
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, "html.parser")

    def limpo(t):
        return re.sub(r"\s+", " ", t or "").strip()

    t = soup.find("title")
    titulo = limpo(t.get_text()) if t else None
    meta = soup.find("meta", attrs={"name": re.compile(r"^description$", re.I)})
    descricao = limpo(meta.get("content")) if meta and meta.get("content") is not None else None
    h1s = [limpo(h.get_text(" ")) for h in soup.find_all("h1")]
    canon = None
    for l in soup.find_all("link", href=True):
        rel = l.get("rel") or []
        if isinstance(rel, str):
            rel = rel.split()
        if "canonical" in [r.lower() for r in rel]:
            canon = urllib.parse.urljoin(url, l["href"].strip())
            break
    robots = soup.find("meta", attrs={"name": re.compile(r"^robots$", re.I)})
    viewport = soup.find("meta", attrs={"name": re.compile(r"^viewport$", re.I)})

    tipos, invalidos = [], 0

    def coleta_tipos(no):
        if isinstance(no, list):
            for x in no:
                coleta_tipos(x)
        elif isinstance(no, dict):
            tp = no.get("@type")
            for x in ([tp] if isinstance(tp, str) else tp if isinstance(tp, list) else []):
                if isinstance(x, str) and x not in tipos:
                    tipos.append(x)
            for k, v in no.items():
                if k in ("@graph", "mainEntity", "itemListElement", "item") or isinstance(v, (dict, list)):
                    coleta_tipos(v)

    for s in soup.find_all("script", attrs={"type": re.compile(r"ld\+json", re.I)}):
        try:
            coleta_tipos(json.loads(s.string or s.get_text() or ""))
        except (ValueError, TypeError):
            invalidos += 1

    imgs = soup.find_all("img")
    sem_alt = [i for i in imgs if i.get("alt") is None]
    alt_vazio = [i for i in imgs if i.get("alt") is not None and i.get("alt").strip() == ""]

    def origem(i):
        return (i.get("src") or i.get("data-src") or i.get("data-lazy-src") or "")[:120]

    return {
        "url": url,
        "titulo": titulo,
        "titulo_caracteres": len(titulo) if titulo is not None else 0,
        "meta_descricao": descricao,
        "meta_descricao_caracteres": len(descricao) if descricao is not None else 0,
        "h1": {"quantos": len(h1s), "textos": h1s[:5]},
        "canonical": canon,
        "canonical_igual_a_url": (chave_url(canon) == chave_url(url)) if canon else None,
        "robots": robots.get("content") if robots else None,
        "viewport_meta": bool(viewport),
        "lang": (soup.html.get("lang") if soup.html else None),
        "dados_estruturados": {"tipos": tipos, "blocos_invalidos": invalidos},
        "imagens": {"total": len(imgs), "sem_alt": len(sem_alt), "alt_vazio": len(alt_vazio),
                    "exemplos_sem_alt": [origem(i) for i in sem_alt[:5]]},
    }


def baixa_html(url, timeout):
    """HTML bruto pelo urllib (quando não há navegador). Devolve (html, http, url_final)."""
    import coletar_fontes as CF
    bruto, ctype, final, http, _ = CF.baixar_com_tentativas(url, timeout)
    return CF.decodificar(bruto, ctype), http, final


# ---------------------------------------------------------------- navegador

class Navegador:
    """Envolve o playwright. `ok` é falso se faltar o pacote ou o navegador; o motivo vai para os avisos."""

    def __init__(self, canais, timeout, avisos, sem_prints):
        self.ok, self.pw, self.nav, self.timeout, self.avisos = False, None, None, timeout * 1000, avisos
        if sem_prints:
            return
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            aviso(avisos, "playwright não instalado: prints pulados, o resto da coleta segue. Para ter os prints: "
                          "python -m pip install --user playwright (usa o Edge ou o Chrome já instalado, não baixa navegador).")
            return
        self.pw = sync_playwright().start()
        erros = []
        for canal in [c.strip() for c in canais.split(",") if c.strip()]:
            try:
                self.nav = self.pw.chromium.launch(channel=canal, headless=True)
                self.ok = True
                break
            except Exception as e:
                erros.append(f"{canal}: {str(e).splitlines()[0][:80]}")
        if not self.ok:
            aviso(avisos, "nenhum navegador abriu (" + "; ".join(erros) + "): prints pulados.")
            self.pw.stop()
            self.pw = None

    def contexto(self, celular):
        if celular:
            return self.nav.new_context(viewport={"width": CELULAR[0], "height": CELULAR[1]}, device_scale_factor=2,
                                        is_mobile=True, has_touch=True, user_agent=UA_CELULAR, locale="pt-BR")
        return self.nav.new_context(viewport={"width": DESKTOP[0], "height": DESKTOP[1]}, user_agent=UA_DESKTOP,
                                    locale="pt-BR")

    def fecha(self):
        try:
            if self.nav:
                self.nav.close()
        finally:
            if self.pw:
                self.pw.stop()

    def abre(self, ctx, url):
        """Abre a URL; devolve (pagina, status, banner). Levanta exceção se não carregar."""
        pg = ctx.new_page()
        pg.set_default_timeout(self.timeout)
        resp = pg.goto(url, wait_until="domcontentloaded", timeout=self.timeout)
        try:
            pg.wait_for_load_state("networkidle", timeout=min(8000, self.timeout))
        except Exception:
            pass
        banner = None
        try:
            banner = pg.evaluate(BANNER_JS)
            if banner:
                pg.wait_for_timeout(800)
        except Exception:
            pass
        pg.wait_for_timeout(700)
        return pg, (resp.status if resp else None), banner


def salva_print(pg, destino, inteira=False, largura=None):
    """Primeira dobra em JPEG; com `inteira`, a página toda (até ALTURA_MAX_INTEIRA)."""
    destino.parent.mkdir(parents=True, exist_ok=True)
    if not inteira:
        pg.evaluate("window.scrollTo(0, 0)")
        pg.screenshot(path=str(destino), type="jpeg", quality=QUALIDADE_JPEG)
        return
    try:
        alt = pg.evaluate("Math.max(document.documentElement.scrollHeight, document.body ? document.body.scrollHeight : 0)")
    except Exception:
        alt = DESKTOP[1]
    vp = pg.viewport_size
    pg.set_viewport_size({"width": vp["width"], "height": max(vp["height"], min(int(alt), ALTURA_MAX_INTEIRA))})
    pg.wait_for_timeout(600)
    pg.evaluate("window.scrollTo(0, 0)")
    pg.screenshot(path=str(destino), type="jpeg", quality=QUALIDADE_JPEG)


def tira_prints(nav, paginas, saida, inteira, avisos):
    """Para cada página, um print de computador e um de celular. Preenche p['prints'] e guarda o HTML renderizado
    (visto no computador) em p['_html']."""
    for celular in (False, True):
        ctx = nav.contexto(celular)
        try:
            for p in paginas:
                nome = f"{p['slug']}-{'celular' if celular else 'desktop'}"
                try:
                    pg, status, banner = nav.abre(ctx, p["url"])
                except Exception as e:
                    aviso(avisos, f"print {'celular' if celular else 'computador'} de {p['url']} falhou: {str(e).splitlines()[0][:100]}")
                    continue
                try:
                    if status and status >= 400:
                        aviso(avisos, f"{p['url']} respondeu HTTP {status} no navegador; o print mostra a página de erro.")
                    salva_print(pg, saida / "prints" / f"{nome}.jpg")
                    p["prints"]["celular" if celular else "desktop"] = f"prints/{nome}.jpg"
                    if inteira:
                        salva_print(pg, saida / "prints" / f"{nome}-inteira.jpg", inteira=True)
                        p["prints"]["celular_inteira" if celular else "desktop_inteira"] = f"prints/{nome}-inteira.jpg"
                    if banner:
                        p.setdefault("banner_fechado", banner)
                    if not celular:
                        p["_html"] = pg.content()
                        p["status_http"] = status
                finally:
                    pg.close()
        finally:
            ctx.close()


def print_gmn(nav, alvo, saida, avisos):
    """Print do Google Meu Negócio. `alvo` é URL ou 'Nome, Cidade'."""
    if re.match(r"^https?://", alvo.strip(), re.I):
        url, busca = alvo.strip(), False
    else:
        url, busca = "https://www.google.com/maps/search/?api=1&query=" + urllib.parse.quote(alvo.strip()), True
    r = {"alvo": alvo, "url": url, "busca_por_nome": busca, "print": None, "texto_visivel": None}
    ctx = nav.contexto(False)
    try:
        pg, status, _ = nav.abre(ctx, url)
        try:
            if "consent." in pg.url:
                for rotulo in ("Aceitar tudo", "Accept all", "Concordo"):
                    try:
                        pg.get_by_role("button", name=rotulo).first.click(timeout=2500)
                        pg.wait_for_load_state("domcontentloaded")
                        break
                    except Exception:
                        continue
            pg.wait_for_timeout(3500)
            salva_print(pg, saida / "gmn.jpg")
            r["print"] = "gmn.jpg"
            r["url_final"] = pg.url
            try:
                r["texto_visivel"] = re.sub(r"\n{3,}", "\n\n", pg.inner_text("body", timeout=3000)).strip()[:3000]
            except Exception:
                pass
            if "consent." in pg.url:
                aviso(avisos, "o Google pediu consentimento e o print pode mostrar essa tela: confira gmn.jpg.")
            if busca:
                aviso(avisos, "o perfil foi buscado por nome e cidade: confira em gmn.jpg se abriu o perfil certo "
                              "(com a URL do perfil o resultado é mais firme).")
        finally:
            pg.close()
    except Exception as e:
        aviso(avisos, f"print do Google Meu Negócio falhou: {str(e).splitlines()[0][:100]}")
    finally:
        ctx.close()
    return r


# ---------------------------------------------------------------- velocidade (PageSpeed Insights)

def num(v, casas=1):
    return round(float(v), casas) if isinstance(v, (int, float)) else None


def parse_psi(js):
    lh = js.get("lighthouseResult") or {}
    cats, aud = lh.get("categories") or {}, lh.get("audits") or {}

    def nota(k):
        s = (cats.get(k) or {}).get("score")
        return int(round(s * 100)) if isinstance(s, (int, float)) else None

    def ms(k):
        return (aud.get(k) or {}).get("numericValue")

    lab = {
        "tipo": "laboratório (Lighthouse, teste simulado)",
        "nota": nota("performance"),
        "notas": {"desempenho": nota("performance"), "seo": nota("seo"), "acessibilidade": nota("accessibility"),
                  "boas_praticas": nota("best-practices")},
        "metricas": {
            "lcp_s": num(ms("largest-contentful-paint") / 1000, 2) if ms("largest-contentful-paint") is not None else None,
            "fcp_s": num(ms("first-contentful-paint") / 1000, 2) if ms("first-contentful-paint") is not None else None,
            "speed_index_s": num(ms("speed-index") / 1000, 2) if ms("speed-index") is not None else None,
            "tti_s": num(ms("interactive") / 1000, 2) if ms("interactive") is not None else None,
            "tbt_ms": num(ms("total-blocking-time"), 0),
            "cls": num((aud.get("cumulative-layout-shift") or {}).get("numericValue"), 3),
        },
        "maiores_ganhos": [],
    }
    ganhos = []
    for a in aud.values():
        d = a.get("details") or {}
        if d.get("type") == "opportunity" and (d.get("overallSavingsMs") or 0) > 0:
            ganhos.append((d["overallSavingsMs"], a.get("title"), a.get("displayValue")))
    for _, titulo, valor in sorted(ganhos, key=lambda g: -g[0])[:5]:
        lab["maiores_ganhos"].append({"item": titulo, "economia": valor})

    def campo_de(exp, nivel):
        mets = (exp or {}).get("metrics") or {}
        if not mets:
            return None
        nomes = {"LARGEST_CONTENTFUL_PAINT_MS": "lcp_ms", "FIRST_CONTENTFUL_PAINT_MS": "fcp_ms",
                 "INTERACTION_TO_NEXT_PAINT": "inp_ms", "CUMULATIVE_LAYOUT_SHIFT_SCORE": "cls",
                 "EXPERIMENTAL_TIME_TO_FIRST_BYTE": "ttfb_ms"}
        saida = {}
        for k, nome in nomes.items():
            m = mets.get(k)
            if m and m.get("percentile") is not None:
                v = m["percentile"] / 100 if nome == "cls" else m["percentile"]
                saida[nome] = {"percentil_75": v, "categoria": m.get("category")}
        return {"tipo": "campo (CrUX, usuários reais do Chrome, últimos 28 dias)", "nivel": nivel,
                "resultado_geral": exp.get("overall_category"), "metricas": saida} if saida else None

    pagina = js.get("loadingExperience") or {}
    origem = js.get("originLoadingExperience") or {}
    campo = None
    if pagina.get("metrics") and not pagina.get("origin_fallback"):
        campo = campo_de(pagina, "página")
    if campo is None:
        campo = campo_de(origem, "origem (site inteiro)") or campo_de(pagina, "origem (site inteiro)")
    return {"laboratorio": lab, "campo": campo}


def consulta_psi(url, estrategia, chave, timeout, endpoint):
    params = [("url", url), ("strategy", estrategia), ("locale", "pt_BR")]
    params += [("category", c) for c in ("performance", "seo", "accessibility", "best-practices")]
    if chave:
        params.append(("key", chave))
    req = urllib.request.Request(endpoint + "?" + urllib.parse.urlencode(params), headers={"User-Agent": UA_DESKTOP})
    ultimo = "erro desconhecido"
    for espera in ESPERAS_PSI:
        if espera:
            time.sleep(espera)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return parse_psi(json.loads(r.read().decode("utf-8"))), None
        except urllib.error.HTTPError as e:
            corpo = ""
            try:
                corpo = e.read().decode("utf-8", "replace")
                corpo = (json.loads(corpo).get("error") or {}).get("message", corpo)
            except Exception:
                pass
            ultimo = f"HTTP {e.code}: {str(corpo)[:160]}"
            if e.code == 429 and "per day" in str(corpo).lower():
                return None, ultimo      # cota do dia esgotada: esperar não adianta
            if e.code == 429 or e.code >= 500:
                continue
            return None, ultimo
        except (urllib.error.URLError, socket.timeout, TimeoutError, ssl.SSLError, ConnectionError, OSError) as e:
            ultimo = f"sem resposta ({getattr(e, 'reason', e)})"
            continue
        except ValueError as e:
            return None, f"resposta inválida ({e})"
    return None, ultimo


def coleta_velocidade(url, chave, timeout, endpoint, avisos, data):
    resultado = {"fonte": "PageSpeed Insights API v5 (Google)", "coletado_em": data, "url": url,
                 "nota": "Laboratório é um teste simulado do Lighthouse; campo (CrUX) é a experiência de usuários "
                         "reais e só existe para site com tráfego. Cite o campo com a data; a nota de laboratório "
                         "alimenta o anel do molde.", "com_chave": bool(chave)}
    with ThreadPoolExecutor(max_workers=2) as ex:
        fut = {e: ex.submit(consulta_psi, url, e, chave, timeout, endpoint) for e in ("mobile", "desktop")}
        for e, f in fut.items():
            dados, erro = f.result()
            if dados is None:
                resultado[e] = None
                dica = (" Defina a chave gratuita do Google na variável de ambiente PAGESPEED_API_KEY e rode de novo."
                        if "429" in (erro or "") and not chave else "")
                aviso(avisos, f"velocidade {e} indisponível ({erro}).{dica}")
            else:
                resultado[e] = dados
                if dados["campo"] is None:
                    resultado.setdefault("sem_campo", []).append(e)
    return resultado


# ---------------------------------------------------------------- saída

def f1(v, casas=1):
    return "?" if v is None else f"{v:.{casas}f}".replace(".", ",")


def linha_psi(rotulo, d):
    if not d:
        return [f"- {rotulo}: indisponível."]
    lab, campo = d["laboratorio"], d["campo"]
    m = lab["metricas"]
    out = [f"- {rotulo}, laboratório (nota do anel do molde): **{lab['nota']}**. LCP {f1(m['lcp_s'])} s, FCP {f1(m['fcp_s'])} s, "
           f"TBT {f1(m['tbt_ms'], 0)} ms, CLS {f1(m['cls'], 2)}, Speed Index {f1(m['speed_index_s'])} s. "
           f"SEO {lab['notas']['seo']}, acessibilidade {lab['notas']['acessibilidade']}, boas práticas {lab['notas']['boas_praticas']}."]
    if campo:
        pedacos = []
        for k, v in campo["metricas"].items():
            val = v["percentil_75"]
            if k in ("lcp_ms", "fcp_ms", "ttfb_ms"):
                txt = f"{f1(val / 1000)} s"
            elif k == "inp_ms":
                txt = f"{val} ms"
            else:
                txt = f1(val, 2)
            pedacos.append(f"{k.split('_')[0].upper()} {txt} ({str(v['categoria']).lower()})")
        out.append(f"- {rotulo}, campo ({campo['nivel']}, CrUX, 75% dos acessos): " + ", ".join(pedacos) + ".")
    else:
        out.append(f"- {rotulo}, campo: sem dado (tráfego baixo demais para o CrUX). Não cite campo.")
    if lab["maiores_ganhos"]:
        out.append("  Maiores ganhos: " + "; ".join(f"{g['item']}" + (f" ({g['economia']})" if g.get("economia") else "")
                                                   for g in lab["maiores_ganhos"]) + ".")
    return out


def monta_md(r):
    vel = r.get("velocidade") or {}
    if any(vel.get(e) for e in ("mobile", "desktop")):
        fonte_vel = f"PageSpeed Insights API, coletado em {r['coletado_em'][:10]}"
    else:
        motivos = [a for a in r["avisos"] if a.startswith("velocidade ")]
        motivo = ("; ".join(motivos) if motivos else "não coletada nesta rodada")
        fonte_vel = f"indisponível ({motivo})"
    L = [f"# Auditoria: {r['site']}", "",
         f"Coleta de {r['coletado_em']}. Fonte da velocidade: {fonte_vel}. "
         f"HTML analisado: {r['fonte_html']}.", ""]
    if r["avisos"]:
        L += ["## Avisos"] + [f"- {a}" for a in r["avisos"]] + [""]
    L += ["## Velocidade (página inicial)"]
    if r.get("velocidade"):
        L += linha_psi("Celular", r["velocidade"].get("mobile")) + linha_psi("Computador", r["velocidade"].get("desktop"))
    else:
        L += ["- Não coletada."]
    L += ["", "## SEO por página"]
    for p in r["paginas"]:
        a = p.get("seo")
        L += ["", f"### {p['rotulo']} · {p['url']}"]
        if not a:
            L += [f"- Não analisada: {p.get('erro', 'sem HTML')}."]
        else:
            ti, md = a["titulo"], a["meta_descricao"]
            L += [f"- Título ({a['titulo_caracteres']} car.): " + (f"\"{ti}\"" if ti else "ausente"),
                  f"- Meta descrição ({a['meta_descricao_caracteres']} car.): " + (f"\"{md}\"" if md else "ausente ou vazia"),
                  f"- H1: {a['h1']['quantos']}" + (": " + " | ".join(f"\"{t}\"" for t in a["h1"]["textos"]) if a["h1"]["textos"] else ""),
                  "- Canonical: " + (f"{a['canonical']}" + ("" if a["canonical_igual_a_url"] else " (aponta para outra URL)") if a["canonical"] else "ausente"),
                  "- Dados estruturados: " + (", ".join(a["dados_estruturados"]["tipos"]) or "nenhum")
                  + (f" ({a['dados_estruturados']['blocos_invalidos']} bloco(s) com JSON inválido)" if a["dados_estruturados"]["blocos_invalidos"] else ""),
                  f"- Imagens: {a['imagens']['total']}; sem alt: {a['imagens']['sem_alt']}; alt vazio (decorativa): {a['imagens']['alt_vazio']}"]
            if a["robots"] and "noindex" in a["robots"].lower():
                L += [f"- Robots: {a['robots']} (a página pede para não ser indexada)"]
            if not a["viewport_meta"]:
                L += ["- Sem meta viewport (pode não se adaptar ao celular)"]
        if p["prints"]:
            L += ["- Prints: " + ", ".join(p["prints"].values())]
    if r.get("gmn"):
        g = r["gmn"]
        L += ["", "## Google Meu Negócio", f"- Print: {g['print'] or 'não saiu'} (alvo: {g['alvo']})"]
        if g.get("texto_visivel"):
            L += ["- Texto visível na página (pode vir incompleto):", "", "```", g["texto_visivel"][:1500], "```"]
    L += ["", "## Caminhos no JSON da semana (data-img)"]
    if r["molde_s3"]:
        L += [f"- `{k}`: `{v}`" for k, v in r["molde_s3"].items()]
    else:
        L += ["- Nenhum print saiu."]
    L += ["- Print de celular não tem espaço no molde: vai para o detalhe (DOCX)."]
    return "\n".join(L) + "\n"


def main():
    ap = argparse.ArgumentParser(description="Coleta da auditoria da Semana 3: prints, velocidade e SEO.")
    ap.add_argument("--site", required=True, help="URL do site do cliente")
    ap.add_argument("--gmn", help="URL do perfil no Google Meu Negócio, ou 'Nome, Cidade' para buscar no Google Maps")
    ap.add_argument("--saida", required=True, help="pasta de saída (<pasta da semana>/_fonte/auditoria)")
    ap.add_argument("--paginas", type=int, default=4, help="páginas internas além da inicial (padrão 4)")
    ap.add_argument("--pagina-inteira", action="store_true", help="grava também o print da página toda")
    ap.add_argument("--sem-prints", action="store_true", help="não abre navegador")
    ap.add_argument("--sem-velocidade", action="store_true", help="não consulta o PageSpeed Insights")
    ap.add_argument("--timeout", type=int, default=30, help="tempo limite por página, em segundos")
    ap.add_argument("--navegador", default="msedge,chrome", help="canais do playwright, em ordem de preferência")
    ap.add_argument("--psi-url", default=PSI_URL, help=argparse.SUPPRESS)
    a = ap.parse_args()

    try:
        site = normaliza_site(a.site)
    except ValueError as e:
        print(f"ERRO: {e}")
        return 2
    saida = Path(a.saida).resolve()
    saida.mkdir(parents=True, exist_ok=True)
    agora = datetime.now().astimezone()
    avisos = []
    r = {"site": site, "coletado_em": agora.strftime("%Y-%m-%d %H:%M"), "fonte_html": "bruto (sem navegador)",
         "avisos": avisos, "paginas": [], "gmn": None, "velocidade": None, "molde_s3": {}}

    # velocidade em segundo plano, enquanto o navegador trabalha
    ex = ThreadPoolExecutor(max_workers=1)
    fut_psi = None
    if not a.sem_velocidade:
        fut_psi = ex.submit(coleta_velocidade, site, os.environ.get("PAGESPEED_API_KEY", "").strip() or None,
                            100, a.psi_url, avisos, agora.strftime("%Y-%m-%d"))

    nav = Navegador(a.navegador, a.timeout, avisos, a.sem_prints)
    usados = {"home"}
    paginas = [{"rotulo": "Página inicial", "slug": "home", "url": site, "prints": {}}]
    try:
        # página inicial: navegador (HTML renderizado) ou urllib
        html_home = None
        if nav.ok:
            tira_prints(nav, paginas, saida, a.pagina_inteira, avisos)
            html_home = paginas[0].pop("_html", None)
            if html_home:
                r["fonte_html"] = "renderizado no navegador"
        if html_home is None:
            try:
                html_home, http, final = baixa_html(site, a.timeout)
                paginas[0]["status_http"] = http
                if final and chave_url(final) != chave_url(site):
                    paginas[0]["url_final"] = final
            except Exception as e:
                paginas[0]["erro"] = f"não abriu ({str(e)[:100]})"
                aviso(avisos, f"a página inicial não abriu pelo urllib: {str(e)[:100]}")
        if html_home:
            paginas[0]["seo"] = analisa_html(html_home, site)
            for u, texto in escolhe_internas(html_home, site, max(0, a.paginas)):
                paginas.append({"rotulo": f"Interna {len(paginas)}" + (f" ({texto})" if texto else ""),
                                "slug": slug_pagina(u, usados), "url": u, "prints": {}})
            if len(paginas) == 1 and a.paginas > 0:
                aviso(avisos, "nenhuma página interna encontrada nos links da página inicial.")
        # internas
        internas = paginas[1:]
        if nav.ok and internas:
            tira_prints(nav, internas, saida, a.pagina_inteira, avisos)
        for p in internas:
            html = p.pop("_html", None)
            if html is None:
                try:
                    html, http, _ = baixa_html(p["url"], a.timeout)
                    p["status_http"] = http
                except Exception as e:
                    p["erro"] = f"não abriu ({str(e)[:100]})"
                    aviso(avisos, f"{p['url']} não abriu: {str(e)[:100]}")
                    continue
            p["seo"] = analisa_html(html, p["url"])
        if a.gmn:
            if nav.ok:
                r["gmn"] = print_gmn(nav, a.gmn, saida, avisos)
            else:
                r["gmn"] = {"alvo": a.gmn, "print": None}
                aviso(avisos, "print do Google Meu Negócio pulado (sem navegador): tire à mão e ponha em tela-08.print.")
    finally:
        nav.fecha()

    for p in paginas:
        p.pop("_html", None)
    r["paginas"] = paginas
    if fut_psi is not None:
        r["velocidade"] = fut_psi.result()
    ex.shutdown()

    home = paginas[0]["prints"]
    if home.get("desktop"):
        r["molde_s3"]["tela-09.print_atual"] = home["desktop"]
    if r["gmn"] and r["gmn"].get("print"):
        r["molde_s3"]["tela-08.print"] = r["gmn"]["print"]
    # caminhos como o preencher_molde resolve: relativos ao textos.json, que fica na pasta pai de --saida
    r["molde_s3"] = {k: f"{saida.name}/{v}" if isinstance(v, str) and k.endswith(("print_atual", ".print")) else v
                     for k, v in r["molde_s3"].items()}
    if r["velocidade"]:
        for chave, e in (("tela-09.desktop.nota", "desktop"), ("tela-09.celular.nota", "mobile")):
            d = r["velocidade"].get(e)
            if d:
                r["molde_s3"][chave] = d["laboratorio"]["nota"]

    (saida / "auditoria.json").write_text(json.dumps(r, ensure_ascii=False, indent=2), encoding="utf-8")
    (saida / "auditoria.md").write_text(monta_md(r), encoding="utf-8")
    ok_html = sum(1 for p in paginas if p.get("seo"))
    prints = sum(len(p["prints"]) for p in paginas) + (1 if r["gmn"] and r["gmn"].get("print") else 0)
    print(f"OK: {ok_html} página(s) analisada(s), {prints} print(s), velocidade "
          f"{'coletada' if r['velocidade'] and any(r['velocidade'].get(e) for e in ('mobile', 'desktop')) else 'não coletada'}.")
    print(f"Saída: {saida / 'auditoria.json'} e {saida / 'auditoria.md'}")
    return 0 if ok_html else 1


if __name__ == "__main__":
    sys.exit(main())
