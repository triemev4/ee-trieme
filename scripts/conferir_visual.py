"""Conferência visual do deck (R15): abre cada tela (<section>) em 1280x720 num navegador sem tela e acusa o que o
verificador de texto não vê.

Uso:
    python conferir_visual.py <deck.html> [--saida <pasta dos PNG>] [--navegador msedge,chrome] [--medidas]

Acusa, tela por tela:
  ERRO   texto estourando a tela ou o próprio cartão (o conteúdo passa da largura ou da altura do elemento, ou
         sai do cartão que o contém), texto cortado por overflow hidden.
  ERRO   fonte calculada pequena demais em texto visível. Texto corrido: ERRO abaixo de 11,5 px e AVISO de 11,5 a
         14 px (o menor texto corrido dos moldes é 11,5 px; o deck bom usa 12,5 e 13 px em notas). Limite próprio
         de ERRO para o que é pequeno de propósito: etiquetas mono (fonte monoespaçada: eyebrow, chips, selos) e
         legenda de mockup (.bm-caption) 9 px; rodapé de fonte (.fonte-rodape) 10 px. Mockup (classe com "mock",
         imitação de site, perfil ou anúncio) fica fora da regra, porque imita uma tela de terceiros.
  AVISO  tela com texto demais: mais de 350 palavras visíveis (mockup não conta).
  AVISO  tela alta: altura acima de 1,6 vezes os 720 px (1152 px) em tela que não é de continuação (eyebrow sem a
         palavra "continuação"). Tela alta pede continuação ou corte.

Os limites ficam em LIMITES, no topo do código, calibrados no deck bom (uma Pesquisa de Mercado aprovada) e nos moldes da Trieme
preenchidos com os textos de exemplo.

Saída: linhas ERRO e AVISO no estilo do verificador (verificar_entrega.py --visual chama este script) e um PNG por
tela com problema na pasta de --saida (padrão: pasta temporária, com o nome do deck). A tela é capturada inteira,
mesmo a que passa de 720 px.

Opcional: playwright (python -m pip install --user playwright), que usa o Edge ou o Chrome já instalado (nada é
baixado). Sem ele, ou sem navegador, o script pula com um AVISO e sai com código 0.
Código de saída: 1 se houver ERRO; 0 caso contrário.
"""
import sys
sys.dont_write_bytecode = True
import argparse, json, re, tempfile, unicodedata
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

LARGURA, ALTURA = 1280, 720

LIMITES = {
    "fonte_texto_aviso_px": 14,   # texto corrido abaixo disso: AVISO
    "fonte_texto_erro_px": 11.5,  # texto corrido abaixo disso: ERRO
    "fonte_mono_erro_px": 9,      # etiquetas em fonte monoespaçada
    "fonte_legenda_erro_px": 9,   # legenda de mockup (.bm-caption)
    "fonte_rodape_erro_px": 10,   # .fonte-rodape (fonte do dado)
    "palavras_aviso": 350,        # palavras visíveis por tela (sem mockup)
    "altura_aviso_vezes": 1.6,  # altura da tela / 720, fora as telas de continuação
    "tolerancia_px": 2,         # folga das medidas (arredondamento de linha e de borda)
}
# Semanas 3 a 5 (moldes do deck de referência, telas que rolam): as telas rolam, então a altura tem folga maior.
# O texto ficou em 400 palavras por tela, com os exemplos dos moldes encurtados para caber (decisões 0044 e 0046).
LIMITES_MOLDE = {"palavras_aviso": 400, "altura_aviso_vezes": 2.25}

# Roda dentro da página. Devolve uma entrada por <section>.
JS = r"""
(lim) => {
  const estilo = document.createElement('style');
  estilo.textContent = '*,*::before,*::after{animation:none!important;transition:none!important}' +
    '.r,.reveal,[class*="reveal"]{opacity:1!important;transform:none!important}';
  document.head.appendChild(estilo);
  // quem rola é o documento: tira a altura fixa e o scroll interno dos pais das telas
  document.documentElement.style.setProperty('height', 'auto', 'important');
  document.body.style.setProperty('height', 'auto', 'important');
  const secs = [...document.querySelectorAll('section')];
  const pais = new Set();
  secs.forEach(s => { for (let p = s.parentElement; p && p !== document.documentElement; p = p.parentElement) pais.add(p); });
  pais.forEach(p => {
    const c = getComputedStyle(p);
    if (/(auto|scroll|hidden)/.test(c.overflowY) && p !== document.body) {
      p.style.setProperty('height', 'auto', 'important');
      p.style.setProperty('overflow', 'visible', 'important');
    }
  });
  const tol = lim.tolerancia_px;
  const mono = (cs) => /mono|courier|consolas/i.test((cs.fontFamily.split(',')[0] || ''));
  const noMock = (el) => !!el.closest('[class*="mock"]');
  const opacidade = (el) => { let o = 1; for (let p = el; p && p.nodeType === 1; p = p.parentElement) o *= parseFloat(getComputedStyle(p).opacity); return o; };
  const visivel = (el) => {
    if (!el.getClientRects().length) return false;
    for (let p = el; p && p.nodeType === 1; p = p.parentElement) {
      const c = getComputedStyle(p);
      if (c.display === 'none' || c.visibility === 'hidden') return false;
    }
    return opacidade(el) > 0.05;
  };
  const rot = (el) => el.tagName.toLowerCase() + (el.className && typeof el.className === 'string' ? '.' + el.className.trim().split(/\s+/)[0] : '');
  const corta = (t) => t.replace(/\s+/g, ' ').trim().slice(0, 48);
  const cartao = (el, secao) => {
    for (let p = el; p && p !== secao; p = p.parentElement) {
      const c = getComputedStyle(p);
      const borda = ['Top', 'Right', 'Bottom', 'Left'].some(l => parseFloat(c['border' + l + 'Width']) > 0 && c['border' + l + 'Style'] !== 'none');
      const fundo = c.backgroundColor && !/rgba\(0, 0, 0, 0\)|transparent/.test(c.backgroundColor);
      const corte = /(hidden|clip)/.test(c.overflowX + c.overflowY);
      if ((borda || fundo || corte) && p.getBoundingClientRect().width > 0) return p;
    }
    return null;
  };
  const saida = [];
  secs.forEach((sec, i) => {
    const rs = sec.getBoundingClientRect();
    const e = { i: i + 1, topo: rs.top + window.scrollY, altura: Math.round(rs.height), palavras: 0,
                nome: '', pequenas: [], estouros: [] };
    const eb = sec.querySelector('.eyebrow, .hero-tag');
    e.nome = eb ? corta(eb.textContent) : '';
    const vistos = new Set();
    const pequenas = new Map();
    const donos = new Set();
    const w = document.createTreeWalker(sec, NodeFilter.SHOW_TEXT);
    for (let n = w.nextNode(); n; n = w.nextNode()) {
      const t = n.nodeValue.replace(/\s+/g, ' ').trim();
      if (!t) continue;
      const el = n.parentElement;
      if (!el || el.closest('script,style,noscript,svg,template') || noMock(el) || !visivel(el)) continue;
      const rg = document.createRange(); rg.selectNodeContents(n);
      const rc = rg.getBoundingClientRect();
      if (rc.width < 1 || rc.height < 1) continue;
      if ((t.match(/[\p{L}\p{N}]+/gu) || []).length) e.palavras += (t.match(/[\p{L}\p{N}][\p{L}\p{N}.,%$'’\-\/]*/gu) || []).length;
      const cs = getComputedStyle(el);
      const px = parseFloat(cs.fontSize);
      const tipo = el.closest('.fonte-rodape') ? 'rodape' : (el.closest('.bm-caption') ? 'legenda' : (mono(cs) ? 'mono' : 'texto'));
      const erro = { rodape: lim.fonte_rodape_erro_px, legenda: lim.fonte_legenda_erro_px, mono: lim.fonte_mono_erro_px, texto: lim.fonte_texto_erro_px }[tipo];
      const minimo = tipo === 'texto' ? lim.fonte_texto_aviso_px : erro;
      if (px + 0.01 < minimo) {
        const k = tipo + '|' + px;
        const p = pequenas.get(k) || { tipo, px, erro, n: 0, ex: corta(t), onde: rot(el) };
        p.n += 1; pequenas.set(k, p);
      }
      // texto fora da tela
      if (rc.right > window.innerWidth + tol || rc.left < -tol) {
        const k = 'tela|' + rot(el) + '|' + corta(t);
        if (!vistos.has(k)) { vistos.add(k); e.estouros.push({ tipo: 'tela', onde: rot(el), texto: corta(t), dx: Math.round(Math.max(rc.right - window.innerWidth, -rc.left)) }); }
      }
      // texto fora do cartão que o contém
      const card = cartao(el, sec);
      if (card) {
        const rk = card.getBoundingClientRect();
        const sai = Math.max(rc.right - rk.right, rk.left - rc.left, rc.bottom - rk.bottom, rk.top - rc.top);
        if (sai > tol) {
          const k = 'cartao|' + rot(card) + '|' + corta(t);
          if (!vistos.has(k)) { vistos.add(k); e.estouros.push({ tipo: 'cartao', onde: rot(card), texto: corta(t), dx: Math.round(sai) }); }
        }
      }
      donos.add(el);
    }
    // conteúdo que passa da largura ou da altura do próprio elemento (overflow oculto ou fixo)
    donos.forEach(el => {
      const cs = getComputedStyle(el);
      if (cs.display === 'inline' || el.clientWidth < 1) return;
      const ox = el.scrollWidth - el.clientWidth, oy = el.scrollHeight - el.clientHeight;
      const corte = /(hidden|clip)/.test(cs.overflowX + ' ' + cs.overflowY);
      const rolagem = /(auto|scroll)/.test(cs.overflowX + ' ' + cs.overflowY);
      if (rolagem) return;
      if (ox > tol) {
        const k = 'larg|' + rot(el) + '|' + corta(el.textContent);
        if (!vistos.has(k)) { vistos.add(k); e.estouros.push({ tipo: corte ? 'cortado' : 'largura', onde: rot(el), texto: corta(el.textContent), dx: ox }); }
      } else if (oy > tol && corte) {
        const k = 'alt|' + rot(el) + '|' + corta(el.textContent);
        if (!vistos.has(k)) { vistos.add(k); e.estouros.push({ tipo: corte ? 'cortado' : 'altura', onde: rot(el), texto: corta(el.textContent), dx: oy }); }
      }
    });
    // a tela inteira passando da largura (rolagem horizontal)
    if (sec.scrollWidth - sec.clientWidth > tol) e.estouros.push({ tipo: 'tela', onde: 'section', texto: e.nome || 'tela', dx: sec.scrollWidth - sec.clientWidth });
    e.pequenas = [...pequenas.values()];
    saida.push(e);
  });
  return { secoes: saida, larguraDoc: document.documentElement.scrollWidth, alturaDoc: document.documentElement.scrollHeight };
}
"""


def sem_acento(s):
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn").lower()


def aviso_pulo(motivo):
    print(f"  AVISO  conferência visual pulada: {motivo}")


def abre_navegador(canais):
    """Devolve (playwright, navegador) ou levanta RuntimeError com o motivo."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        raise RuntimeError("playwright não instalado (python -m pip install --user playwright; usa o Edge ou o Chrome "
                           "já instalado, não baixa navegador)")
    pw = sync_playwright().start()
    erros = []
    for canal in [c.strip() for c in canais.split(",") if c.strip()]:
        try:
            return pw, pw.chromium.launch(channel=canal, headless=True)
        except Exception as e:
            erros.append(f"{canal}: {str(e).splitlines()[0][:80]}")
    pw.stop()
    raise RuntimeError("nenhum navegador abriu (" + "; ".join(erros) + ")")


def medir(caminho, canais, timeout_s=30, sem_rede=False):
    """Abre o deck e devolve (dados, pagina, navegador, pw). Levanta RuntimeError se não houver navegador."""
    pw, nav = abre_navegador(canais)
    try:
        pg = nav.new_page(viewport={"width": LARGURA, "height": ALTURA}, locale="pt-BR",
                          offline=sem_rede, service_workers="block" if sem_rede else "allow")
        if sem_rede:
            # Contexto offline mais rotas explícitas: conteúdo local/data continua disponível.
            pg.context.route(re.compile(r"^(?:https?|wss?|ftp)://", re.I), lambda rota: rota.abort())
            # Interceptar sem connect_to_server mantém o socket somente local.
            # close() dentro do callback síncrono trava algumas combinações de navegador/Playwright.
            pg.context.route_web_socket(re.compile(r"^wss?://", re.I),
                                       lambda socket: socket.on_message(lambda mensagem: None))
        pg.set_default_timeout(timeout_s * 1000)
        pg.goto(Path(caminho).resolve().as_uri(), wait_until="domcontentloaded")
        try:
            pg.wait_for_load_state("networkidle", timeout=6000)
        except Exception:
            pass
        try:
            pg.evaluate("document.fonts && document.fonts.ready.then(() => true)")
        except Exception:
            pass
        pg.wait_for_timeout(400)
        dados = pg.evaluate(JS, LIMITES)
        return dados, pg, nav, pw
    except Exception:
        nav.close()
        pw.stop()
        raise


def descreve(e, i_nome):
    return f"tela {e['i']} ({i_nome})"


def nome_da_tela(e):
    return e["nome"] or ("capa" if e["i"] == 1 else "sem eyebrow")


def achados(dados):
    """Devolve [(gravidade, indice da tela, mensagem)] a partir das medidas."""
    out = []
    fontes_avisadas = {}
    for e in dados["secoes"]:
        nome = nome_da_tela(e)
        rotulo = f"tela {e['i']} ({nome})"
        for x in e["estouros"]:
            if x["tipo"] == "tela":
                msg = f'texto passa da largura da tela em {x["dx"]} px: {x["onde"]} "{x["texto"]}"'
            elif x["tipo"] == "cartao":
                msg = f'texto sai do cartão {x["onde"]} em {x["dx"]} px: "{x["texto"]}"'
            elif x["tipo"] == "cortado":
                msg = f'texto cortado por overflow hidden em {x["onde"]} ({x["dx"]} px a mais que o espaço): "{x["texto"]}"'
            elif x["tipo"] == "largura":
                msg = f'texto passa da largura do próprio elemento {x["onde"]} em {x["dx"]} px: "{x["texto"]}"'
            else:
                msg = f'texto passa da altura do próprio elemento {x["onde"]} em {x["dx"]} px: "{x["texto"]}"'
            out.append(("ERRO", e["i"], f"{rotulo}: {msg}"))
        for p in sorted(e["pequenas"], key=lambda p: p["px"]):
            qual = {"texto": "texto corrido", "mono": "etiqueta mono", "rodape": "rodapé de fonte",
                    "legenda": "legenda de mockup"}[p["tipo"]]
            if p["px"] + 0.01 < p["erro"]:
                out.append(("ERRO", e["i"], f'{rotulo}: fonte de {"%g" % p["px"]} px em {qual} (mínimo {"%g" % p["erro"]} px), '
                                            f'{p["n"]} trecho(s), ex.: "{p["ex"]}"'))
            else:
                fontes_avisadas.setdefault(e["i"], []).append(p)
        if e["palavras"] > LIMITES["palavras_aviso"]:
            out.append(("AVISO", e["i"], f'{rotulo}: texto demais, {e["palavras"]} palavras (limite {LIMITES["palavras_aviso"]}); '
                                         "dividir a tela ou cortar"))
        if e["altura"] > ALTURA * LIMITES["altura_aviso_vezes"] and "continuacao" not in sem_acento(e["nome"]):
            out.append(("AVISO", e["i"], f'{rotulo}: tela alta, {e["altura"]} px (a tela cabe em {ALTURA} px) e não é de '
                                         "continuação; dividir em duas telas ou cortar"))
    if fontes_avisadas:
        tamanhos = sorted({p["px"] for ps in fontes_avisadas.values() for p in ps})
        menor = min((p for ps in fontes_avisadas.values() for p in ps), key=lambda p: p["px"])
        telas = ", ".join(str(i) for i in sorted(fontes_avisadas))
        out.append(("AVISO", None, f'texto corrido abaixo de {"%g" % LIMITES["fonte_texto_aviso_px"]} px em {len(fontes_avisadas)} '
                                   f'tela(s) ({telas}): {", ".join("%g" % t for t in tamanhos)} px; o menor, "{menor["ex"]}"; '
                                   "texto que o cliente lê vai a 14 px ou mais"))
    return out


def salva_pngs(pg, dados, telas, pasta):
    """Um PNG por tela com problema (tela inteira, mesmo a mais alta que 720 px). Devolve {indice: caminho}."""
    pasta.mkdir(parents=True, exist_ok=True)
    caminhos = {}
    por_indice = {e["i"]: e for e in dados["secoes"]}
    for i in sorted(telas):
        e = por_indice[i]
        alt = max(e["altura"], 1)
        destino = pasta / f"tela-{i:02d}.png"
        try:
            pg.screenshot(path=str(destino), full_page=True,
                          clip={"x": 0, "y": max(e["topo"], 0), "width": LARGURA, "height": min(alt, 8000)})
            caminhos[i] = destino
        except Exception as ex:
            print(f"  AVISO  não consegui gravar o print da tela {i}: {str(ex).splitlines()[0][:80]}")
    return caminhos


def main():
    ap = argparse.ArgumentParser(description="Conferência visual do deck: estouro, fonte pequena e texto demais.")
    ap.add_argument("arquivo")
    ap.add_argument("--saida", help="pasta dos PNG das telas com problema (padrão: pasta temporária)")
    ap.add_argument("--navegador", default="msedge,chrome", help="canais do playwright, em ordem de preferência")
    ap.add_argument("--medidas", action="store_true", help="imprime as medidas de cada tela (para calibrar os limites)")
    ap.add_argument("--semana", type=int, help="3 a 5: limites de texto e altura do deck de referência (telas que rolam)")
    ap.add_argument("--sem-rede", action="store_true", help="bloqueia rede, WebSocket e service workers; permite arquivos locais/data")
    a = ap.parse_args()
    if a.semana and a.semana >= 3:
        LIMITES.update(LIMITES_MOLDE)

    if not Path(a.arquivo).is_file():
        print(f"ERRO: arquivo não encontrado: {a.arquivo}")
        return 2
    print(f"Conferência visual · {a.arquivo}")
    try:
        dados, pg, nav, pw = medir(a.arquivo, a.navegador, sem_rede=a.sem_rede)
    except RuntimeError as e:
        aviso_pulo(str(e))
        return 0
    except Exception as e:
        aviso_pulo(f"o navegador não abriu o deck ({type(e).__name__}: {str(e).splitlines()[0][:80]})")
        return 0
    try:
        lista = achados(dados)
        if a.medidas:
            for e in dados["secoes"]:
                print(f"  tela {e['i']:>2} {nome_da_tela(e)[:34]:<34} altura {e['altura']:>5} palavras {e['palavras']:>4} "
                      f"pequenas {[(p['tipo'], p['px'], p['n'], p['onde']) for p in e['pequenas']]} estouros {len(e['estouros'])}")
        com_problema = {i for _, i, _ in lista if i is not None}
        pasta = Path(a.saida) if a.saida else Path(tempfile.gettempdir()) / "ee-conferencia-visual" / Path(a.arquivo).stem
        pngs = salva_pngs(pg, dados, com_problema, pasta) if com_problema else {}
    finally:
        nav.close()
        pw.stop()

    print(f"  telas: {len(dados['secoes'])} · abertas em {LARGURA}x{ALTURA}")
    if a.sem_rede:
        print("  AVISO  visual sem rede: fontes e recursos remotos ficam bloqueados; a medição usa os recursos locais disponíveis")
    erros = 0
    for grav, i, msg in lista:
        erros += grav == "ERRO"
        png = f" [png: {pngs[i]}]" if i is not None and i in pngs else ""
        print(f"  {grav:<5}  {msg}{png}")
    if not lista:
        print("  OK, nenhum problema visual encontrado.")
    elif not erros:
        print("  Sem erros visuais. Revisar os avisos.")
    return 1 if erros else 0


if __name__ == "__main__":
    sys.exit(main())
