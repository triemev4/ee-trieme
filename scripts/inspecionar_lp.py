"""Inspeção da landing page no navegador: larguras, contraste, foco, CTA e formulário. Mede e registra; não aprova.

Uso:
    python inspecionar_lp.py <landing-page.html> --copy <copy.json> [--saida <pasta>] [--larguras 390,800,1440]
                             [--navegador msedge,chrome] [--timeout 30]

Abre o HTML local em cada largura (padrão 390, 800 e 1440 px) num navegador sem tela e registra:
  rolagem horizontal; contraste efetivo do texto e das bordas dos campos (a cor do fundo entra na conta, com
  transparência; texto sobre imagem ou degradê fica "sem medida"); campos sem rótulo; âncoras sem destino; textos da
  copy ausentes; o CTA (visível, na primeira dobra, destino, cabeçalho fixo cobrindo o alvo); foco pelo teclado;
  formulário (envio vazio, e-mail inválido, confirmação); recursos que não carregaram e erros de JavaScript.
Nos cliques e no envio do formulário a rede externa fica bloqueada: nada é enviado nem aberto fora da página.
O formulário recebe dados fictícios. Destino externo do CTA não é aberto.

Grava em --saida (padrão: a pasta <nome da LP>-inspecao, ao lado da LP; nunca dentro do pacote):
  <largura>-dobra.png, <largura>-completa.png, <largura>-confirmacao.png e inspecao.json.

Requer beautifulsoup4 (scripts/requirements.txt): a copy é lida e validada pelo conferir_landing_page.py.
Opcional: playwright (python -m pip install --user playwright), que usa o Edge ou o Chrome já instalado (nada é
baixado). Sem ele, ou sem navegador, o script imprime "inspeção pendente" com o que o consultor faz à mão e sai
com código 0.
Código de saída: 0 quando a inspeção rodou (com ou sem achados) ou ficou pendente; 2 para arquivo, copy ou pasta de
saída inválidos. Os achados não mudam o código: o aceite é decisão do consultor.
"""
import sys
sys.dont_write_bytecode = True
import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import json
from pathlib import Path
import re

sys.path.insert(0, str(Path(__file__).resolve().parent))
from conferir_landing_page import ler_copy, normalizar  # noqa: E402

PACOTE = Path(__file__).resolve().parents[1]
ALTURA = 900
MAXIMO_TABS = 15
REDE = re.compile(r"^(?:https?|wss?|ftp)://", re.I)
IGNORADOS = {"hidden", "submit", "button", "reset", "image", "file", "range", "color"}
ESTATICOS = {"image", "stylesheet", "font", "script", "media"}
MARCAS_DO_TESTE = ("teste%40example", "teste@example", "teste%20fict", "teste+fict")  # dados fictícios que o inspetor digita
VALORES = {"email": "teste@example.invalid", "tel": "11999990000", "url": "https://example.invalid", "number": "1",
           "date": "2030-01-01", "time": "10:00", "month": "2030-01", "week": "2030-W01", "datetime-local": "2030-01-01T10:00"}
LIMITES = [
    "não testa leitor de tela, dispositivo físico nem conformidade WCAG completa",
    "contraste: texto sobre imagem ou degradê não é medido; a transparência entra na conta",
    "formulário: só o primeiro; dados fictícios; a rede externa fica bloqueada nos cliques e no envio",
    "navegador sem tela com a janela na largura pedida; não é um celular de verdade",
]

# Roda dentro da página, depois de rolar tudo. Devolve as medidas de uma largura.
JS_MEDIDAS = r"""
() => {
  const cv = document.createElement('canvas');
  cv.width = cv.height = 1;
  const cx = cv.getContext('2d', { willReadFrequently: true });
  const cor = (s) => {
    const m = /^rgba?\(\s*([\d.]+)[\s,]+([\d.]+)[\s,]+([\d.]+)(?:\s*[,/]\s*([\d.]+)(%?))?\s*\)$/.exec(s);
    if (m) return [+m[1], +m[2], +m[3], m[4] === undefined ? 1 : (m[5] ? +m[4] / 100 : +m[4])];
    cx.clearRect(0, 0, 1, 1);
    cx.fillStyle = '#010203';
    cx.fillStyle = s;
    if (cx.fillStyle === '#010203') return null;
    cx.fillRect(0, 0, 1, 1);
    const d = cx.getImageData(0, 0, 1, 1).data;
    return [d[0], d[1], d[2], d[3] / 255];
  };
  const lum = ([r, g, b]) => {
    const f = (v) => { v /= 255; return v <= 0.04045 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); };
    return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b);
  };
  const razao = (a, b) => { const x = lum(a), y = lum(b); return (Math.max(x, y) + 0.05) / (Math.min(x, y) + 0.05); };
  const sobre = (f, b) => [0, 1, 2].map(i => f[i] * f[3] + b[i] * (1 - f[3]));
  const hex = (c) => '#' + c.map(v => Math.round(v).toString(16).padStart(2, '0')).join('');
  const r2 = (v) => Math.round(v * 100) / 100;
  const curto = (t, n) => t.replace(/\s+/g, ' ').trim().slice(0, n);
  const sel = (e) => e.tagName.toLowerCase() + (e.id ? '#' + e.id :
    (typeof e.className === 'string' && e.className.trim() ? '.' + e.className.trim().split(/\s+/)[0] : ''));
  const opacidade = (e) => {
    if (getComputedStyle(e).visibility !== 'visible') return 0;
    let op = 1;
    for (let p = e; p && p.nodeType === 1; p = p.parentElement) op *= parseFloat(getComputedStyle(p).opacity);
    return op > 0.05 ? op : 0;
  };
  const visivel = (e) => e.getClientRects().length > 0 && opacidade(e) > 0;
  // Fundo efetivo: camadas de cor do elemento para cima, até a primeira opaca. Imagem ou degradê: sem medida.
  const fundoDe = (e) => {
    const camadas = [];
    for (let p = e; p && p.nodeType === 1; p = p.parentElement) {
      const c = getComputedStyle(p);
      if (c.backgroundImage !== 'none') return null;
      const k = cor(c.backgroundColor);
      if (!k) return null;
      if (k[3] > 0) { camadas.push(k); if (k[3] >= 0.999) break; }
    }
    return camadas.reduceRight((base, k) => sobre(k, base), [255, 255, 255]);
  };
  // Imagens e fundos com imagem que podem ficar atrás do texto sem serem ancestrais dele.
  const retas = [];
  document.body.querySelectorAll('*').forEach((e) => {
    const t = e.tagName.toLowerCase();
    if (e.closest('svg') && t !== 'svg') return;
    const rc = e.getBoundingClientRect();
    if (rc.width < 2 || rc.height < 2) return;
    const imagem = ['img', 'video', 'canvas', 'picture', 'iframe', 'object', 'embed'].includes(t) ||
      (t === 'svg' && rc.width * rc.height > 40000);
    if ((imagem || getComputedStyle(e).backgroundImage !== 'none') && opacidade(e) > 0) retas.push({ e, rc });
  });
  const sobreImagem = (e, rc) => retas.some(({ e: x, rc: ri }) => !x.contains(e) && !e.contains(x) &&
    Math.min(rc.right, ri.right) - Math.max(rc.left, ri.left) > 2 && Math.min(rc.bottom, ri.bottom) - Math.max(rc.top, ri.top) > 2);

  // Texto: todo elemento com texto próprio, mais campos e placeholders.
  const itens = [];
  document.body.querySelectorAll('*').forEach((e) => {
    if (e.closest('svg,script,style,noscript,template')) return;
    const tag = e.tagName.toLowerCase();
    const controle = ['input', 'textarea', 'select'].includes(tag) &&
      !['hidden', 'checkbox', 'radio', 'image', 'file', 'range', 'color'].includes((e.type || '').toLowerCase());
    const proprio = [...e.childNodes].filter(n => n.nodeType === 3).map(n => n.nodeValue).join(' ');
    if (!controle && !proprio.trim()) return;
    if (!visivel(e) || e.disabled || e.closest('[disabled]')) return;
    const rc = e.getBoundingClientRect(), op = opacidade(e);
    itens.push({ e, cs: getComputedStyle(e), rc, op, texto: curto(controle ? (e.value || e.placeholder || tag) : proprio, 60) });
    if (controle && e.placeholder) itens.push({ e, cs: getComputedStyle(e, '::placeholder'), rc, op, texto: curto(e.placeholder, 60) });
  });
  const texto = { medidos: 0, sem_medida: 0, exemplos_sem_medida: [], abaixo_total: 0, abaixo: [], menor: null };
  itens.forEach(({ e, cs, rc, op, texto: t }) => {
    const px = parseFloat(cs.fontSize), peso = parseInt(cs.fontWeight, 10) || 400;
    const minimo = (px >= 24 || (px >= 18.66 && peso >= 700)) ? 3 : 4.5;
    const fg = cor(cs.webkitTextFillColor || cs.color), bg = fundoDe(e);
    if (!fg || !bg || fg[3] === 0 || sobreImagem(e, rc)) {
      texto.sem_medida++;
      if (texto.exemplos_sem_medida.length < 3) texto.exemplos_sem_medida.push(sel(e) + ' "' + t.slice(0, 30) + '"');
      return;
    }
    const ef = sobre([fg[0], fg[1], fg[2], fg[3] * op], bg);
    const r = razao(ef, bg);
    const item = { sel: sel(e), texto: t, cor: hex(ef), fundo: hex(bg), px: r2(px), peso, razao: r2(r), minimo };
    texto.medidos++;
    if (!texto.menor || item.razao < texto.menor.razao) texto.menor = item;
    if (r + 0.005 < minimo) { texto.abaixo_total++; texto.abaixo.push(item); }
  });
  texto.abaixo.sort((a, b) => a.razao - b.razao);
  texto.abaixo = texto.abaixo.slice(0, 40);

  // Campos: rótulo e contraste da borda e do fundo contra o entorno (3:1).
  const rotuloDe = (e) => {
    if (e.labels && e.labels.length && e.labels[0].innerText.trim()) return e.labels[0].innerText.trim();
    const a = (e.getAttribute('aria-label') || '').trim();
    if (a) return a;
    const ids = (e.getAttribute('aria-labelledby') || '').split(/\s+/).filter(Boolean);
    const t = ids.map(i => document.getElementById(i)).filter(Boolean).map(x => x.innerText.trim()).join(' ');
    return t || (e.getAttribute('title') || '').trim();
  };
  const campos = [...document.querySelectorAll('input:not([type=hidden]):not([type=submit]):not([type=button]):not([type=reset]):not([type=image]),textarea,select')]
    .filter(e => visivel(e)).map((e) => {
      const cs = getComputedStyle(e), tipo = (e.type || e.tagName).toLowerCase();
      const nativo = tipo === 'checkbox' || tipo === 'radio';
      const fora = e.parentElement ? fundoDe(e.parentElement) : null;
      let borda = null, fundo = null;
      if (fora && !nativo) {
        const lados = ['Top', 'Right', 'Bottom', 'Left'].map(l => ({ w: parseFloat(cs['border' + l + 'Width']),
          s: cs['border' + l + 'Style'], c: cor(cs['border' + l + 'Color']) })).filter(l => l.w > 0 && l.s !== 'none' && l.c && l.c[3] > 0);
        if (lados.length) borda = r2(Math.max(...lados.map(l => razao(sobre(l.c, fora), fora))));
        const f = cor(cs.backgroundColor);
        fundo = f ? r2(razao(sobre(f, fora), fora)) : null;
      }
      return { id: e.id, nome: e.name, tipo, obrigatorio: e.required, rotulo: rotuloDe(e), placeholder: e.placeholder || '',
               contraste_borda: borda, contraste_fundo: fundo, medido: !!fora && !nativo };
    });

  const ancoras = [...document.querySelectorAll('a[href^="#"]')].map((a) => {
    const h = a.getAttribute('href');
    let id = h.slice(1);
    try { id = decodeURIComponent(id); } catch (_) {}
    return { texto: curto(a.innerText, 40), href: h, valida: !!id && !!document.getElementById(id) };
  });

  const larg = innerWidth, rolagem = document.documentElement.scrollWidth;
  let culpados = [];
  if (rolagem > larg + 1) {
    document.body.querySelectorAll('*').forEach((e) => {
      const rc = e.getBoundingClientRect();
      if (rc.width < 1 || rc.right <= larg + 1 || !visivel(e)) return;
      for (let p = e.parentElement; p && p !== document.body && p !== document.documentElement; p = p.parentElement) {
        if (/(hidden|auto|scroll|clip)/.test(getComputedStyle(p).overflowX)) return;
      }
      culpados.push({ sel: sel(e), direita: Math.round(rc.right) });
    });
    culpados = culpados.sort((a, b) => b.direita - a.direita).slice(0, 3);
  }
  const cabecalhos = [...document.querySelectorAll('header')].map(e => ({ texto: curto(e.innerText, 60), position: getComputedStyle(e).position }));
  return { largura: larg, rolagem, excesso: Math.max(0, rolagem - larg), culpados, texto, campos, ancoras, cabecalhos };
}
"""

JS_ROLAR = r"""
async () => {
  const pausa = (ms) => new Promise(r => setTimeout(r, ms));
  const passo = Math.max(innerHeight * 0.8, 200);
  const total = Math.min(document.documentElement.scrollHeight, 40 * passo);
  for (let y = 0; y < total; y += passo) { window.scrollTo({ top: y, behavior: 'instant' }); await pausa(50); }
  window.scrollTo({ top: 0, behavior: 'instant' });
  await pausa(150);
  document.getAnimations().forEach((a) => { try { a.finish(); } catch (_) { a.cancel(); } });
}
"""

JS_CTA = r"""
(alvo) => {
  const norm = (t) => t.replace(/\s+/g, ' ').trim().toLowerCase().replace(/\s+([.,;:!?])/g, '$1');
  const itens = [...document.querySelectorAll('a,button,[role=button],input[type=submit],input[type=button]')]
    .filter(e => e.getClientRects().length && getComputedStyle(e).visibility === 'visible' && norm(e.innerText || e.value || '') === alvo);
  itens.forEach((e, i) => e.setAttribute('data-ee-cta', i));
  return itens.map((e) => { const r = e.getBoundingClientRect();
    return { tag: e.tagName.toLowerCase(), href: e.getAttribute('href'), topo: Math.round(r.top + scrollY), base: Math.round(r.bottom + scrollY) }; });
}
"""

JS_DESTINO = r"""
(destino) => {
  const dec = (s) => { try { return decodeURIComponent(s); } catch (_) { return s; } };
  const alvo = destino.length > 1 ? document.getElementById(dec(destino.slice(1))) : null;
  let cabecalho = 0;
  if (alvo) {
    document.body.querySelectorAll('*').forEach((e) => {
      const p = getComputedStyle(e).position;
      if (p !== 'fixed' && p !== 'sticky') return;
      const r = e.getBoundingClientRect();
      if (r.width >= innerWidth * 0.5 && r.top <= 1 && r.bottom > 0) cabecalho = Math.max(cabecalho, r.bottom);
    });
  }
  return { hash: dec(location.hash), confere: dec(location.hash) === dec(destino),
           alvo_topo: alvo ? Math.round(alvo.getBoundingClientRect().top) : null, cabecalho_base: Math.round(cabecalho) };
}
"""

JS_FOCAVEIS = r"""
() => [...document.querySelectorAll('a[href],button,input:not([type=hidden]),select,textarea,summary,[tabindex]:not([tabindex="-1"])')]
  .filter(e => !e.disabled && e.getClientRects().length && getComputedStyle(e).visibility === 'visible').length
"""

JS_FOCO = r"""
() => {
  const e = document.activeElement;
  if (!e || e === document.body || e === document.documentElement) return null;
  const c = getComputedStyle(e);
  const t = (e.innerText || e.value || e.getAttribute('aria-label') || '').replace(/\s+/g, ' ').trim().slice(0, 40);
  return { tag: e.tagName.toLowerCase(), id: e.id, texto: t, contorno: c.outlineStyle + ' ' + c.outlineWidth, sombra: c.boxShadow };
}
"""

JS_FORM = r"""
() => {
  const f = [...document.querySelectorAll('form')].find(x => x.getClientRects().length);
  let armazenamento = null;
  try { armazenamento = localStorage.length + sessionStorage.length; } catch (_) {}
  return { invalido: f ? !f.checkValidity() : null, sem_validacao_nativa: f ? f.noValidate : false,
           email_invalido: [...document.querySelectorAll('input[type=email]')].some(e => !e.checkValidity()),
           aria_invalid: document.querySelectorAll('[aria-invalid="true"]').length, armazenamento };
}
"""


def ler_larguras(texto):
    try:
        valores = [int(v) for v in texto.split(",") if v.strip()]
    except ValueError:
        raise ValueError("larguras: use números inteiros separados por vírgula, por exemplo 390,800,1440")
    if not valores or any(v < 200 or v > 4000 for v in valores):
        raise ValueError("larguras: de 200 a 4000 px")
    return sorted(set(valores))


def erro_curto(exc):
    return f"{type(exc).__name__}: {str(exc).splitlines()[0][:120] if str(exc) else ''}"


def virgula(numero):
    return str(numero).replace(".", ",")


def host(url):
    achado = re.match(r"^\w+://([^/:?#]+)", url)
    return achado.group(1) if achado else url


def imprimir_pendencia(motivo):
    print(f"  inspeção pendente: {motivo}")
    print("  O que fazer: abrir o HTML da LP no navegador e conferir a olho em 390, 800 e 1440 px. Sem rolagem horizontal, "
          "texto cortado ou colunas comprimidas; botão, âncoras e formulário funcionando; foco visível ao navegar com Tab.")
    print('  Registrar em revisao.md: "contraste não medido" e as larguras conferidas.')
    print("  Para ter a inspeção automática: python -m pip install --user playwright (usa o Edge ou o Chrome já instalado, "
          "não baixa navegador).")
    print("  Inspeção pendente não aprova nem reprova a página: o aceite é decisão do consultor.")


def abre_navegador(canais):
    """Devolve (playwright, navegador, canal) ou levanta RuntimeError com o motivo."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        raise RuntimeError("playwright não instalado")
    except Exception as exc:
        raise RuntimeError(f"playwright não importou ({type(exc).__name__})")
    try:
        pw = sync_playwright().start()
    except Exception as exc:
        raise RuntimeError("playwright não iniciou (" + erro_curto(exc) + ")")
    erros = []
    for canal in [c.strip() for c in canais.split(",") if c.strip()]:
        try:
            return pw, pw.chromium.launch(channel=canal, headless=True), canal
        except Exception as exc:
            erros.append(f"{canal}: {str(exc).splitlines()[0][:80]}")
    pw.stop()
    raise RuntimeError("nenhum navegador abriu (" + "; ".join(erros) + ")")


def observar(ctx):
    """Anota pedidos, falhas e respostas com erro. `fase` separa a carga das ações (clique e envio)."""
    reg = {"fase": "carga", "pedidos": [], "falhas": [], "erros": []}

    def pedido(r):
        reg["pedidos"].append({"url": r.url, "fase": reg["fase"]})

    def falha(r):
        reg["falhas"].append({"url": r.url, "falha": r.failure or "falhou", "fase": reg["fase"]})

    def resposta(r):
        if r.status >= 400:
            reg["falhas"].append({"url": r.url, "falha": f"HTTP {r.status}", "fase": reg["fase"]})

    ctx.on("request", pedido)
    ctx.on("requestfailed", falha)
    ctx.on("response", resposta)
    return reg


@contextmanager
def sem_rede_externa(ctx, reg):
    """Nos cliques e no envio, aborta e anota todo pedido à rede externa. Entrega a lista dos bloqueados."""
    bloqueados = []

    def rota(route):
        bloqueados.append({"url": route.request.url, "metodo": route.request.method, "tipo": route.request.resource_type})
        route.abort()

    ctx.route(REDE, rota)
    reg["fase"] = "acao"
    try:
        yield bloqueados
    finally:
        reg["fase"] = "carga"
        try:
            ctx.unroute(REDE, rota)
        except Exception:
            pass


def abrir(ctx, url, reg, timeout_s):
    pg = ctx.new_page()
    pg.set_default_timeout(8000)
    pg.on("pageerror", lambda exc: reg["erros"].append(str(exc)[:200]))
    pg.goto(url, wait_until="load", timeout=timeout_s * 1000)
    try:
        pg.wait_for_load_state("networkidle", timeout=5000)
    except Exception:
        pass
    try:
        pg.evaluate("document.fonts && document.fonts.ready.then(() => true)")
        pg.evaluate(JS_ROLAR)
    except Exception:
        pass
    return pg


def captura(pg, caminho, completa=False):
    try:
        pg.screenshot(path=str(caminho), full_page=completa, animations="disabled")
        return caminho.name
    except Exception as exc:
        return "falhou: " + str(exc).splitlines()[0][:80]


def testar_foco(pg):
    """Aperta Tab até 15 vezes e anota, em cada parada, se há contorno ou sombra de foco."""
    focaveis = pg.evaluate(JS_FOCAVEIS)
    passos = []
    for _ in range(min(max(focaveis, 1), MAXIMO_TABS)):
        pg.keyboard.press("Tab")
        pg.wait_for_timeout(120)
        info = pg.evaluate(JS_FOCO)
        if info is not None:
            estilo, _, largura = info["contorno"].partition(" ")
            info["indicador"] = (estilo != "none" and largura not in ("0px", "0")) or info["sombra"] != "none"
        passos.append(info)
    return {"focaveis": focaveis, "passos": passos}


def testar_cta(ctx, pg, cta, reg):
    """Acha o CTA, mede a posição e, se o destino for uma âncora, clica e confere onde a página parou."""
    alvos = pg.evaluate(JS_CTA, normalizar(cta["texto"]))
    dados = {"texto": cta["texto"], "destino": cta["destino"], "encontrados": len(alvos), "alvos": alvos}
    if not alvos:
        return dados
    dados["na_primeira_dobra"] = any(a["base"] <= ALTURA for a in alvos)
    dados["href_confere"] = None if alvos[0]["href"] is None else alvos[0]["href"] == cta["destino"]
    if not cta["destino"].startswith("#"):
        dados["clique"] = {"nao_aberto": True}
        return dados
    pg.evaluate("window.scrollTo(0, 0); document.activeElement && document.activeElement.blur()")
    try:
        with sem_rede_externa(ctx, reg) as bloqueados:
            pg.locator("[data-ee-cta='0']").click(timeout=4000)
            pg.wait_for_timeout(700)
            dados["clique"] = pg.evaluate(JS_DESTINO, cta["destino"])
            dados["clique"]["bloqueados"] = bloqueados
            if alvos[0]["href"] is None:  # botão sem href: vale o alvo ter ficado à vista, e não a âncora na barra
                topo = dados["clique"]["alvo_topo"]
                dados["clique"]["confere"] = topo is not None and 0 <= topo < ALTURA
                dados["clique"]["por"] = "alvo visível"
    except Exception as exc:
        dados["clique"] = {"erro": erro_curto(exc)}
    return dados


def fase_pagina(ctx, url, copy, largura, saida, reg, timeout_s):
    """Medidas da página, capturas, foco pelo teclado e CTA."""
    pg = abrir(ctx, url, reg, timeout_s)
    try:
        dados = pg.evaluate(JS_MEDIDAS)
        corpo = normalizar(pg.inner_text("body"))
        dados["copy_ausente"] = [t["id"] for t in copy["textos"]
                                 if t.get("estado", "inicial") == "inicial" and normalizar(t["texto"]) not in corpo]
        dados["capturas"] = {"dobra": captura(pg, saida / f"{largura}-dobra.png"),
                             "completa": captura(pg, saida / f"{largura}-completa.png", completa=True)}
        pg.evaluate("window.scrollTo(0, 0)")
        try:
            dados["foco"] = testar_foco(pg)
        except Exception as exc:
            dados["foco"] = {"focaveis": 0, "passos": [], "erro": erro_curto(exc)}
        try:
            dados["cta"] = testar_cta(ctx, pg, copy["cta"], reg)
        except Exception as exc:
            dados["cta"] = {"texto": copy["cta"]["texto"], "destino": copy["cta"]["destino"], "encontrados": 0, "erro": erro_curto(exc)}
        return dados
    finally:
        pg.close()


def preencher(form, email="teste@example.invalid"):
    """Preenche os campos visíveis com dados fictícios. Devolve (campos preenchidos, há campo de e-mail)."""
    preenchidos, tem_email = 0, False
    for campo in form.locator("input, textarea, select").all():
        info = campo.evaluate("""e => ({tag: e.tagName.toLowerCase(), tipo: (e.type || '').toLowerCase(), min: e.getAttribute('min'),
            minlen: e.minLength > 0 ? e.minLength : 0, off: !!(e.disabled || e.readOnly), vis: e.getClientRects().length > 0})""")
        if info["off"] or not info["vis"] or info["tipo"] in IGNORADOS:
            continue
        try:
            if info["tipo"] in ("checkbox", "radio"):
                campo.check(timeout=2000, force=True)
            elif info["tag"] == "select":
                campo.evaluate("""e => { const i = [...e.options].findIndex(o => o.value && !o.disabled);
                    if (i >= 0) e.selectedIndex = i;
                    e.dispatchEvent(new Event('input', {bubbles: true})); e.dispatchEvent(new Event('change', {bubbles: true})); }""")
            else:
                if info["tipo"] == "email":
                    tem_email, valor = True, email
                elif info["tipo"] == "number" and info["min"]:
                    valor = info["min"]
                else:
                    valor = VALORES.get(info["tipo"], "Teste fictício")
                    valor = valor.ljust(info["minlen"], "x") if info["minlen"] else valor
                campo.fill(valor, timeout=2000)
            preenchidos += 1
        except Exception:
            pass
    return preenchidos, tem_email


def botao_enviar(form):
    for seletor in ("button[type=submit]:visible", "input[type=submit]:visible", "button:not([type]):visible", "button:visible"):
        alvo = form.locator(seletor)
        if alvo.count():
            return alvo.first
    return None


def interacao_visivel(pg, copy):
    try:
        corpo = normalizar(pg.inner_text("body"))
    except Exception:
        return []
    return [t["id"] for t in copy["textos"] if t.get("estado") == "interacao" and normalizar(t["texto"]) in corpo]


def estado_form(pg):
    try:
        pg.wait_for_load_state("load", timeout=2000)
        return pg.evaluate(JS_FORM)
    except Exception:
        return {"invalido": None, "sem_validacao_nativa": False, "email_invalido": False, "aria_invalid": 0, "armazenamento": None}


def fase_formulario(ctx, url, copy, largura, saida, reg, timeout_s):
    """Envio vazio, e-mail inválido e envio válido, cada um numa página nova. Sem formulário: presente falso."""
    pg = abrir(ctx, url, reg, timeout_s)
    try:
        formularios = pg.locator("form:visible").count()
        if not formularios:
            return {"presente": False}
        resultado = {"presente": True, "formularios": formularios}
        form = pg.locator("form:visible").first
        botao = botao_enviar(form)
        resultado["botao_enviar"] = botao is not None
        if botao is None:
            return resultado
        with sem_rede_externa(ctx, reg) as bloqueados:
            botao.click(timeout=4000)
            pg.wait_for_timeout(200)
            estado = estado_form(pg)
            resultado["vazio"] = {"invalido": estado["invalido"], "sem_validacao_nativa": estado["sem_validacao_nativa"],
                                  "aria_invalid": estado["aria_invalid"], "interacao_visivel": interacao_visivel(pg, copy),
                                  "bloqueados": list(bloqueados)}
    finally:
        pg.close()

    pg = abrir(ctx, url, reg, timeout_s)
    try:
        form = pg.locator("form:visible").first
        _, tem_email = preencher(form, email="email-invalido")
        if tem_email:
            with sem_rede_externa(ctx, reg):
                botao_enviar(form).click(timeout=4000)
                pg.wait_for_timeout(200)
                estado = estado_form(pg)
                resultado["email_invalido_barrado"] = None if estado["sem_validacao_nativa"] else estado["email_invalido"]
    except Exception as exc:
        resultado["email_invalido_erro"] = erro_curto(exc)
    finally:
        pg.close()

    pg = abrir(ctx, url, reg, timeout_s)
    try:
        form = pg.locator("form:visible").first
        preenchidos, _ = preencher(form)
        estado = estado_form(pg)
        antes = estado["armazenamento"]
        url_antes = pg.url.split("#")[0]
        if estado["invalido"] and not estado["sem_validacao_nativa"]:
            resultado["valido"] = {"preenchidos": preenchidos, "nao_preenchido": True}
            return resultado
        with sem_rede_externa(ctx, reg) as bloqueados:
            botao_enviar(form).click(timeout=4000)
            pg.wait_for_timeout(300)
            depois = estado_form(pg)["armazenamento"]
            visiveis = interacao_visivel(pg, copy)
            esperados = [t["id"] for t in copy["textos"] if t.get("estado") == "interacao"]
            resultado["valido"] = {"preenchidos": preenchidos, "interacao_esperada": esperados, "interacao_visivel": visiveis,
                                   "interacao_ausente": [i for i in esperados if i not in visiveis],
                                   "trocou_de_pagina": pg.url.split("#")[0] != url_antes, "bloqueados": list(bloqueados),
                                   "armazenamento_novo": (depois - antes) if isinstance(antes, int) and isinstance(depois, int) else None}
            resultado["capturas"] = {"confirmacao": captura(pg, saida / f"{largura}-confirmacao.png")}
    except Exception as exc:
        resultado["valido_erro"] = erro_curto(exc)
    finally:
        pg.close()
    return resultado


def inspecionar_largura(nav, url, copy, largura, saida, timeout_s):
    ctx = nav.new_context(viewport={"width": largura, "height": ALTURA}, reduced_motion="reduce", locale="pt-BR")
    reg = observar(ctx)
    try:
        d = {"largura": largura}
        for nome, fase in (("pagina", fase_pagina), ("formulario", fase_formulario)):
            try:
                d[nome] = fase(ctx, url, copy, largura, saida, reg, timeout_s)
            except Exception as exc:
                d[nome] = {"erro": erro_curto(exc)}
        carga = [p for p in reg["pedidos"] if p["fase"] == "carga"]
        d["dependencias_externas"] = sorted({host(p["url"]) for p in carga if REDE.match(p["url"])})
        pasta = url.rsplit("/", 1)[0] + "/"
        vistos, falhas = set(), []
        for f in reg["falhas"]:
            if f["fase"] == "carga" and f["url"] not in vistos and not f["url"].endswith("/favicon.ico"):
                vistos.add(f["url"])
                falhas.append({"url": f["url"][len(pasta):] if f["url"].startswith(pasta) else f["url"], "falha": f["falha"]})
        d["recursos_com_falha"] = falhas
        d["erros_de_pagina"] = sorted(set(reg["erros"]))
        return d
    finally:
        ctx.close()


def inspecionar(html, copy, copy_caminho, canais, larguras, saida, timeout_s):
    """Roda a inspeção. Levanta RuntimeError se faltar o playwright ou o navegador."""
    pw, nav, canal = abre_navegador(canais)
    try:
        saida.mkdir(parents=True, exist_ok=True)
        resultado = {"arquivo": str(html), "copy": str(copy_caminho), "navegador": f"{canal} {nav.version}",
                     "inspecionado_em": datetime.now(timezone.utc).isoformat(), "larguras": [], "limites": LIMITES}
        for largura in larguras:
            resultado["larguras"].append(inspecionar_largura(nav, html.as_uri(), copy, largura, saida, timeout_s))
        return resultado
    finally:
        nav.close()
        pw.stop()


def achados_rede(quem, bloqueados):
    """Pedidos externos barrados num clique ou envio. Chamada que leva dado é achado; recurso estático sem dado é aviso."""
    envio = [b for b in bloqueados if b["metodo"] != "GET" or b["tipo"] not in ESTATICOS
             or any(m in b["url"].lower() for m in MARCAS_DO_TESTE)]
    resto = [b for b in bloqueados if b not in envio]
    out = []
    if envio:
        out.append(("ACHADO", f"{quem} tentou chamar a rede externa (bloqueada): " + ", ".join(sorted({host(b["url"]) for b in envio}))))
    if resto:
        out.append(("AVISO", f"{quem} puxou {len(resto)} recurso(s) externo(s) estático(s) sem dados, provável carga tardia: "
                             + ", ".join(sorted({host(b["url"]) for b in resto}))))
    return out


def achados_pagina(pag):
    out = []
    if pag["excesso"] > 0:
        onde = ""
        if pag["culpados"]:
            onde = "; mais à direita: " + ", ".join(f"{c['sel']} ({c['direita']} px)" for c in pag["culpados"])
        out.append(("ACHADO", f"rolagem horizontal: o conteúdo passa {pag['excesso']} px da largura{onde}"))
    texto = pag["texto"]
    grupos = {}
    for t in texto["abaixo"]:
        grupos.setdefault((t["cor"], t["fundo"], t["px"], t["razao"], t["minimo"]), []).append(t)
    for (cor, fundo, px, razao, minimo), itens in list(grupos.items())[:5]:
        out.append(("ACHADO", f"contraste {virgula(razao)}:1 (mínimo {virgula(minimo)}:1) em {len(itens)} trecho(s) de {virgula(px)} px, {cor} sobre {fundo}; "
                              f"ex.: {itens[0]['sel']} \"{itens[0]['texto'][:40]}\""))
    if texto["abaixo_total"] > sum(len(g) for g in list(grupos.values())[:5]):
        out.append(("ACHADO", f"{texto['abaixo_total']} trechos de texto abaixo do contraste mínimo no total; o arquivo inspecao.json lista os piores"))
    if texto["sem_medida"]:
        out.append(("AVISO", f"contraste não medido em {texto['sem_medida']} trecho(s) (fundo com imagem ou degradê, ou texto sobre "
                             f"imagem); conferir a olho, ex.: {'; '.join(texto['exemplos_sem_medida'])}"))
    for c in pag["campos"]:
        nome = c["id"] or c["nome"] or c["tipo"]
        if not c["rotulo"]:
            out.append(("ACHADO", f"campo \"{nome}\" sem rótulo (label, aria-label ou aria-labelledby); placeholder não conta"))
        if c["medido"] and (c["contraste_borda"] or 1) < 3 and (c["contraste_fundo"] or 1) < 3:
            out.append(("ACHADO", f"campo \"{nome}\": borda {virgula(c['contraste_borda']) if c['contraste_borda'] else 'sem'}:1 e fundo "
                                  f"{virgula(c['contraste_fundo']) if c['contraste_fundo'] else 'sem'}:1 contra o entorno (mínimo 3:1 em um dos dois)"))
    sem_destino = [a for a in pag["ancoras"] if not a["valida"]]
    if sem_destino:
        lista = ", ".join(f"\"{a['href']}\" ({a['texto'] or 'sem texto'})" for a in sem_destino[:5])
        out.append(("ACHADO", f"{len(sem_destino)} âncora(s) sem destino: {lista}" + (" e mais" if len(sem_destino) > 5 else "")))
    if pag["copy_ausente"]:
        out.append(("ACHADO", "texto da copy ausente na tela: " + ", ".join(pag["copy_ausente"])))
    return out


def achados_cta(cta):
    out = []
    if "erro" in cta:
        return [("AVISO", "CTA não testado: " + cta["erro"])]
    if not cta["encontrados"]:
        return [("ACHADO", f"CTA \"{cta['texto']}\" não encontrado visível")]
    if cta["href_confere"] is False:
        out.append(("ACHADO", f"CTA aponta para \"{cta['alvos'][0]['href']}\" e a copy manda \"{cta['destino']}\""))
    elif cta["href_confere"] is None:
        out.append(("AVISO", "o CTA não é um link (sem href): o destino só vale pelo clique"))
    if not cta["na_primeira_dobra"]:
        out.append(("AVISO", f"CTA fora da primeira dobra ({cta['alvos'][0]['topo']} px do topo; dobra de {ALTURA} px)"))
    clique = cta.get("clique", {})
    if "erro" in clique:
        out.append(("ACHADO", "CTA não respondeu ao clique: " + clique["erro"]))
    elif "nao_aberto" in clique:
        out.append(("AVISO", f"CTA com destino externo ({cta['destino']}) não aberto; testar só com o escopo e a autorização da ação"))
    elif clique:
        if not clique["confere"] and clique.get("por") == "alvo visível":
            out.append(("ACHADO", f"CTA (botão) não deixou o destino \"{cta['destino']}\" à vista depois do clique"))
        elif not clique["confere"]:
            out.append(("ACHADO", f"CTA não levou ao destino: a página ficou em \"{clique['hash'] or 'sem âncora'}\" e a copy manda \"{cta['destino']}\""))
        if clique["alvo_topo"] is not None and clique["cabecalho_base"] - clique["alvo_topo"] > 2:
            out.append(("ACHADO", f"o cabeçalho fixo cobre {clique['cabecalho_base'] - clique['alvo_topo']} px do começo do destino do CTA"))
        out += achados_rede("o clique no CTA", clique["bloqueados"])
    return out


def achados_foco(foco):
    if "erro" in foco:
        return [("AVISO", "foco pelo teclado não testado: " + foco["erro"])]
    paradas = [p for p in foco["passos"] if p is not None]
    if not paradas:
        return [("ACHADO", "nada recebeu foco pelo teclado (Tab)")]
    sem = [p for p in paradas if not p["indicador"]]
    if not sem:
        return []
    nomes = sorted({p["tag"] + ("#" + p["id"] if p["id"] else "") + " \"" + p["texto"][:20] + "\"" for p in sem})[:4]
    return [("AVISO", f"{len(sem)} de {len(paradas)} elementos focados sem contorno nem sombra de foco (conferir a olho): " + ", ".join(nomes))]


def achados_formulario(form):
    if "erro" in form:
        return [("AVISO", "o formulário não foi inspecionado: " + form["erro"])]
    if not form["presente"]:
        return []
    if not form["botao_enviar"]:
        return [("AVISO", "formulário sem botão de envio visível; não foi testado")]
    out = []
    vazio = form["vazio"]
    barrado = (vazio["invalido"] and not vazio["sem_validacao_nativa"]) or vazio["aria_invalid"] or vazio["interacao_visivel"]
    if not barrado:
        out.append(("ACHADO", "envio vazio sem validação visível (nativa, aria-invalid ou mensagem de erro da copy)"))
    if form.get("email_invalido_barrado") is False:
        out.append(("ACHADO", "o formulário aceitou um e-mail inválido"))
    if "email_invalido_erro" in form:
        out.append(("AVISO", "e-mail inválido não testado: " + form["email_invalido_erro"]))
    if "valido_erro" in form:
        out.append(("AVISO", "envio válido não testado: " + form["valido_erro"]))
    valido = form.get("valido")
    if valido and valido.get("nao_preenchido"):
        out.append(("AVISO", "o inspetor não conseguiu preencher o formulário de forma válida (algum campo tem regra própria); "
                             "envio válido e confirmação não conferidos"))
    elif valido:
        if valido["trocou_de_pagina"]:
            out.append(("ACHADO", "o envio troca de página ou recarrega; o formulário demonstrativo confirma na própria página"))
        out += achados_rede("o envio do formulário", valido["bloqueados"])
        if not valido["interacao_esperada"]:
            out.append(("AVISO", "a copy não traz texto de interação (estado interacao); a confirmação não foi conferida"))
        elif not valido["interacao_visivel"]:
            out.append(("ACHADO", "a confirmação não apareceu depois do envio válido (esperado: " + ", ".join(valido["interacao_esperada"]) + ")"))
        elif valido["interacao_ausente"]:
            out.append(("AVISO", "textos de interação que não apareceram no envio válido (podem ser mensagens de erro): " + ", ".join(valido["interacao_ausente"])))
        if valido["armazenamento_novo"]:
            out.append(("AVISO", f"o envio gravou {valido['armazenamento_novo']} item(ns) no armazenamento do navegador"))
    return out


def achados_da_largura(d):
    """Devolve [(gravidade, mensagem)] de uma largura. ACHADO é o que se olha; AVISO é o que ficou sem medida."""
    out = []
    pag = d["pagina"]
    if "erro" in pag:
        out.append(("AVISO", "a página não foi inspecionada: " + pag["erro"]))
    else:
        out += achados_pagina(pag) + achados_cta(pag["cta"]) + achados_foco(pag["foco"])
    out += achados_formulario(d["formulario"])
    falhas = d["recursos_com_falha"]
    out += [("ACHADO", f"recurso não carregou: {f['url']} ({f['falha']})") for f in falhas[:5]]
    if len(falhas) > 5:
        out.append(("ACHADO", f"mais {len(falhas) - 5} recursos não carregaram; o inspecao.json lista todos"))
    out += [("ACHADO", "erro de JavaScript na página: " + e) for e in d["erros_de_pagina"]]
    if d["dependencias_externas"]:
        out.append(("AVISO", "a página pede recursos externos e exige internet: " + ", ".join(d["dependencias_externas"])))
    return out


def agrupar(larguras):
    """Junta a mesma mensagem de larguras diferentes. Devolve [{gravidade, larguras, mensagem}]."""
    grupos = {}
    for d in larguras:
        for gravidade, mensagem in achados_da_largura(d):
            grupos.setdefault((gravidade, mensagem), []).append(d["largura"])
    ordem = {"ACHADO": 0, "AVISO": 1}
    return [{"gravidade": g, "larguras": ls, "mensagem": m}
            for (g, m), ls in sorted(grupos.items(), key=lambda kv: (ordem[kv[0][0]], kv[1][0]))]


def linha_da_largura(d):
    pag, form = d["pagina"], d["formulario"]
    partes = [f"{d['largura']} px"]
    if "erro" in pag:
        partes.append("página não inspecionada")
    else:
        t, cta = pag["texto"], pag["cta"]
        partes.append("rolagem horizontal: " + (f"{pag['excesso']} px" if pag["excesso"] > 0 else "não"))
        partes.append(f"texto: {t['medidos']} medidos, {t['abaixo_total']} abaixo do mínimo" + (f", {t['sem_medida']} sem medida" if t["sem_medida"] else ""))
        partes.append(f"campos: {len(pag['campos'])}")
        if "erro" in cta:
            partes.append("CTA: não testado")
        elif not cta["encontrados"]:
            partes.append("CTA: não encontrado")
        else:
            clique = cta.get("clique", {})
            if clique.get("nao_aberto"):
                levou = "destino externo não aberto"
            elif "confere" in clique:
                levou = "levou ao destino" if clique["confere"] else "não levou ao destino"
            else:
                levou = "clique sem resultado"
            partes.append("CTA: " + ("na primeira dobra" if cta["na_primeira_dobra"] else "abaixo da dobra") + ", " + levou)
        paradas = [p for p in pag["foco"]["passos"] if p is not None]
        partes.append("foco: não testado" if "erro" in pag["foco"] else f"foco: {sum(1 for p in paradas if p['indicador'])} de {len(paradas)} com indicador")
    if "erro" in form:
        partes.append("formulário não inspecionado")
    elif not form["presente"]:
        partes.append("formulário: não há")
    elif form.get("valido", {}).get("nao_preenchido"):
        partes.append("formulário: envio válido não testado (campo com regra própria)")
    elif form.get("valido"):
        v, vazio = form["valido"], form["vazio"]
        barrado = (vazio["invalido"] and not vazio["sem_validacao_nativa"]) or vazio["aria_invalid"] or vazio["interacao_visivel"]
        partes.append("formulário: envio vazio " + ("barrado" if barrado else "sem validação") + ", confirmação "
                      + ("visível" if v["interacao_visivel"] else "ausente") + f", pedidos externos ao enviar: {len(v['bloqueados'])}")
    else:
        partes.append("formulário: não testado até o envio")
    return " · ".join(partes)


def main():
    parser = argparse.ArgumentParser(description="Inspeção da landing page no navegador: larguras, contraste, foco, CTA e formulário.")
    parser.add_argument("html", help="landing page (arquivo .html)")
    parser.add_argument("--copy", required=True, help="copy.json da LP (CTA e textos esperados)")
    parser.add_argument("--saida", help="pasta das capturas e do inspecao.json (padrão: <nome da LP>-inspecao, ao lado da LP)")
    parser.add_argument("--larguras", default="390,800,1440", help="larguras em px, separadas por vírgula (padrão: 390,800,1440)")
    parser.add_argument("--navegador", default="msedge,chrome", help="canais do playwright, em ordem de preferência")
    parser.add_argument("--timeout", type=int, default=30, help="segundos para carregar a página (padrão: 30)")
    args = parser.parse_args()
    try:
        html = Path(args.html).resolve()
        if not html.is_file():
            raise ValueError("arquivo não encontrado: " + args.html)
        copy_caminho = Path(args.copy).resolve()
        try:
            copy = ler_copy(copy_caminho)
        except FileNotFoundError:
            raise ValueError("copy: arquivo não encontrado: " + args.copy)
        except UnicodeDecodeError:
            raise ValueError("copy: o arquivo deve estar em UTF-8")
        except json.JSONDecodeError as exc:
            raise ValueError(f"copy: JSON inválido (linha {exc.lineno}, coluna {exc.colno})")
        larguras = ler_larguras(args.larguras)
        saida = Path(args.saida).resolve() if args.saida else html.with_name(html.stem + "-inspecao")
        if saida.is_relative_to(PACOTE):
            raise ValueError("a pasta de saída deve ficar fora do pacote: " + str(saida))
        if saida.is_file():
            raise ValueError("a saída deve ser uma pasta, e não um arquivo: " + str(saida))
        if saida / "inspecao.json" in (html, copy_caminho):
            raise ValueError("inspecao.json não pode sobrescrever uma entrada")
    except (OSError, ValueError, TypeError) as exc:
        print("ERRO: " + str(exc))
        return 2
    print(f"Inspeção da landing page · {html}")
    try:
        resultado = inspecionar(html, copy, copy_caminho, args.navegador, larguras, saida, args.timeout)
    except RuntimeError as exc:
        imprimir_pendencia(str(exc))
        return 0
    except Exception as exc:
        imprimir_pendencia("o navegador falhou durante a inspeção (" + erro_curto(exc) + ")")
        return 0
    resultado["achados"] = agrupar(resultado["larguras"])
    (saida / "inspecao.json").write_text(json.dumps(resultado, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"  navegador: {resultado['navegador']} · larguras: {', '.join(str(x) for x in larguras)} px")
    for d in resultado["larguras"]:
        print("  " + linha_da_largura(d))
    for a in resultado["achados"]:
        quando = "todas as larguras" if a["larguras"] == larguras else ", ".join(str(x) for x in a["larguras"]) + " px"
        print(f"  {a['gravidade']:<6} [{quando}] {a['mensagem']}")
    if not resultado["achados"]:
        print("  Nenhum achado nas medidas feitas.")
    print(f"  Capturas e medidas em: {saida}")
    print("  A inspeção mede e não aprova. Contraste sobre imagem, leitor de tela e celular de verdade ficam para a conferência a olho; "
          "o aceite é decisão do consultor.")
    return 0


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass
    sys.exit(main())
