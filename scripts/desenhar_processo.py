"""Desenha o processo observado em raias, sem transformar hipótese em fato.

Uso: desenhar_processo.py processo.json --svg processo.svg [--png processo.png]
Saídas ficam fora do pacote. PNG usa o Chromium/Playwright já usado pela EE.
O desenho cresce com o conteúdo: etapas, dores e fontes nunca são truncadas.
Figura alta deve ser lida em zoom ou no detalhe; a versão completa é preservada.
"""
import sys
sys.dont_write_bytecode = True
import argparse
import html
import json
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]


def validar(dados):
    def texto(v, cam):
        if not isinstance(v, str) or not v.strip():
            raise ValueError(f"{cam}: esperado texto não vazio")
        if any((ord(c) < 32 and c not in "\n\t\r") or 0xD800 <= ord(c) <= 0xDFFF
               or ord(c) in (0xFFFE, 0xFFFF) for c in v):
            raise ValueError(f"{cam}: caractere incompatível com SVG")
    if not isinstance(dados, dict):
        raise ValueError("processo: esperado objeto")
    for chave in ("lanes", "nodes", "flows"):
        if not isinstance(dados.get(chave), list) or (chave != "flows" and not dados[chave]):
            raise ValueError(f"{chave}: esperado lista" + (" não vazia" if chave != "flows" else ""))
    ids = {}
    for chave in ("lanes", "nodes"):
        ids[chave] = set()
        for i, item in enumerate(dados[chave]):
            cam = f"{chave}[{i}]"
            if not isinstance(item, dict): raise ValueError(f"{cam}: esperado objeto")
            texto(item.get("id"), f"{cam}.id")
            if item["id"] in ids[chave]: raise ValueError(f"{cam}.id: duplicado")
            ids[chave].add(item["id"])
            if chave == "lanes":
                texto(item.get("nome"), f"{cam}.nome")
                if not isinstance(item.get("externa", False), bool): raise ValueError(f"{cam}.externa: esperado booleano")
            else:
                if item.get("lane") not in ids["lanes"]: raise ValueError(f"{cam}.lane: raia inexistente")
                if item.get("tipo") not in ("inicio", "tarefa", "decisao", "fim"): raise ValueError(f"{cam}.tipo: inválido")
                texto(item.get("texto"), f"{cam}.texto")
                for campo in ("ferramenta", "dor", "fonte"):
                    if campo in item: texto(item[campo], f"{cam}.{campo}")
                if not isinstance(item.get("restricao", False), bool): raise ValueError(f"{cam}.restricao: esperado booleano")
    for i, fluxo in enumerate(dados["flows"]):
        if not isinstance(fluxo, dict): raise ValueError(f"flows[{i}]: esperado objeto")
        for campo in ("de", "para"):
            if fluxo.get(campo) not in ids["nodes"]: raise ValueError(f"flows[{i}].{campo}: nó inexistente")
        if "rotulo" in fluxo: texto(fluxo["rotulo"], f"flows[{i}].rotulo")
        if not isinstance(fluxo.get("mensagem", False), bool): raise ValueError(f"flows[{i}].mensagem: esperado booleano")


def linhas_texto(texto, limite=210, fonte=15):
    """Quebra por largura conservadora sem descartar palavras extensas."""
    def largura(c):
        if c.isspace(): return fonte * .35
        if c in "WM@#%" or ord(c) > 0xFFFF: return fonte
        if c in "ilI.,:;!'|": return fonte * .4
        return fonte * (.78 if c.isupper() else .65)
    saida = []
    for paragrafo in texto.splitlines() or [""]:
        atual, tamanho = "", 0
        for palavra in paragrafo.split():
            if atual and tamanho + largura(' ') + sum(map(largura, palavra)) > limite:
                saida.append(atual)
                atual, tamanho = "", 0
            for c in ((' ' if atual else '') + palavra):
                if atual and tamanho + largura(c) > limite:
                    saida.append(atual)
                    atual, tamanho = "", 0
                atual += c
                tamanho += largura(c)
        saida.append(atual)
    return saida


def desenhar(dados):
    validar(dados)
    esc = html.escape
    largura_raia, margem = 380, 34
    direita_raias = len(dados["lanes"]) * largura_raia + margem
    nomes = [linhas_texto(lane['nome'], largura_raia-36, 18) for lane in dados['lanes']]
    cabecalho = 44 + max(map(len, nomes))*22 + 32
    pos, blocos, y = {}, [], cabecalho+24
    indices = {no['id']: i for i, no in enumerate(dados['nodes'])}
    rotulos = [linhas_texto(f.get('rotulo', ''), 190, 14) if f.get('rotulo') else [] for f in dados['flows']]
    trilhas = {i: j for j, i in enumerate(i for i, f in enumerate(dados['flows'])
               if indices[f['para']] != indices[f['de']]+1)}
    largura = direita_raias + margem + len(trilhas)*230
    for no in dados["nodes"]:
        linhas = []
        for valor in (no["texto"], *(f"{rotulo}: {no[campo]}" for campo, rotulo in (("ferramenta", "Ferramenta"), ("dor", "Dor"), ("fonte", "Fonte")) if campo in no)):
            linhas.extend(linhas_texto(valor))
        if no.get("restricao"): linhas.append("Restrição em exame")
        decisao = no["tipo"] == "decisao"
        h = max(160, (len(linhas)*20+20)*3) if decisao else max(70, len(linhas)*20+30)
        meio_largura = 170 if decisao else 135
        lane = next(i for i, l in enumerate(dados["lanes"]) if l["id"] == no["lane"])
        x = margem + lane*largura_raia + largura_raia/2
        cy = y+h/2
        pos[no["id"]] = (x, cy, h, meio_largura)
        cor = "#b45309" if no.get("restricao") else "#334155"
        if decisao:
            forma = f'<polygon points="{x},{y} {x+meio_largura},{cy} {x},{y+h} {x-meio_largura},{cy}"'
        else:
            raio = 32 if no["tipo"] in ("inicio", "fim") else 5
            forma = f'<rect x="{x-135}" y="{y}" width="270" height="{h}" rx="{raio}"'
        partes = [f'<g data-node="{esc(no["id"], quote=True)}">', forma+f' fill="white" stroke="{cor}" stroke-width="2"/>']
        texto_y = cy-(len(linhas)-1)*10+5
        partes += [f'<text x="{x}" y="{texto_y+j*20}" text-anchor="middle" font-size="15">{esc(ln)}</text>' for j, ln in enumerate(linhas)]
        partes.append('</g>')
        blocos.append("".join(partes))
        maior_rotulo = max((len(rotulos[i]) for i, f in enumerate(dados['flows'])
                            if f['de'] == no['id']), default=0)
        y += h+max(80, maior_rotulo*18+36)
    altura = y+20
    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" class="processo-raias" role="img" aria-label="Processo atual em raias" width="{largura}" height="{altura}" viewBox="0 0 {largura} {altura}">',
           '<title>Processo atual, responsáveis, ferramentas e dores</title>',
           '<defs><marker id="seta" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z" fill="#64748b"/></marker></defs>',
           '<g font-family="Arial, sans-serif" fill="#172033">']
    for i, lane in enumerate(dados["lanes"]):
        x = margem+i*largura_raia
        tracejado = ' stroke-dasharray="7 4"' if lane.get("externa") else ""
        svg.append(f'<rect x="{x}" y="12" width="{largura_raia}" height="{altura-24}" fill="{("#f8fafc" if i%2==0 else "#f1f5f9")}" stroke="#94a3b8"{tracejado}/>')
        for j, linha in enumerate(nomes[i]):
            svg.append(f'<text x="{x+largura_raia/2}" y="{44+j*22}" text-anchor="middle" font-size="18" font-weight="bold">{esc(linha)}</text>')
        svg.append(f'<text x="{x+largura_raia/2}" y="{cabecalho-16}" text-anchor="middle" font-size="14">{("Participante externo" if lane.get("externa") else "Responsabilidade interna")}</text>')
    for i, fluxo in enumerate(dados["flows"]):
        x1, y1, h1, w1 = pos[fluxo["de"]]
        x2, y2, h2, w2 = pos[fluxo["para"]]
        if i not in trilhas:
            ini, fim = y1+h1/2, y2-h2/2
            meio = min(fim-16, ini+max(40, len(rotulos[i])*18+20))
            d = f"M {x1} {ini} V {meio} H {x2} V {fim}"
            tx, ty = (x1+x2)/2+8, ini+18
        else:
            lateral = direita_raias+24+trilhas[i]*230
            if fluxo['de'] == fluxo['para']:
                acima = y1-h1/2-28
                d = f"M {x1+w1} {y1} L {lateral} {y1} L {lateral} {acima} L {x1} {acima} L {x1} {y1-h1/2}"
            else:
                d = f"M {x1+w1} {y1} L {lateral} {y1} L {lateral} {y2} L {x2+w2} {y2}"
            tx, ty = lateral+10, max(cabecalho+20, (y1+y2)/2-(len(rotulos[i])-1)*9)
        tracejado = ' stroke-dasharray="6 4"' if fluxo.get("mensagem") else ""
        svg.append(f'<path data-de="{esc(fluxo["de"], quote=True)}" data-para="{esc(fluxo["para"], quote=True)}" d="{d}" fill="none" stroke="#64748b" stroke-width="2" marker-end="url(#seta)"{tracejado}/>')
        if fluxo.get("rotulo"):
            for j, linha in enumerate(rotulos[i]):
                svg.append(f'<text x="{tx}" y="{ty+18*j}" font-size="14">{esc(linha)}</text>')
    svg.extend(blocos)
    svg.append('</g></svg>')
    return "\n".join(svg)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("entrada", type=Path)
    ap.add_argument("--svg", type=Path, required=True)
    ap.add_argument("--png", type=Path)
    args = ap.parse_args()
    try:
        destinos = [p.resolve() for p in (args.svg, args.png) if p]
        if len(set(destinos)) != len(destinos): raise ValueError("SVG e PNG precisam de destinos diferentes")
        for p in destinos:
            if p == RAIZ or RAIZ in p.parents: raise ValueError("saída precisa ficar fora do pacote")
            if p == args.entrada.resolve(): raise ValueError("saída não pode substituir a entrada")
        svg = desenhar(json.loads(args.entrada.read_text(encoding="utf-8-sig")))
        # Renderiza em memória primeiro; falha de dependência não deixa PNG parcial.
        png = None
        if args.png:
            from playwright.sync_api import sync_playwright
            with sync_playwright() as pw:
                browser = pw.chromium.launch(headless=True)
                try:
                    page = browser.new_page(device_scale_factor=1)
                    page.route("**/*", lambda route: route.abort())
                    page.set_content('<html><body style="margin:0">'+svg+'</body></html>')
                    png = page.locator("svg").screenshot(type="png")
                finally: browser.close()
        args.svg.parent.mkdir(parents=True, exist_ok=True)
        args.svg.write_text(svg, encoding="utf-8")
        if args.png:
            args.png.parent.mkdir(parents=True, exist_ok=True)
            args.png.write_bytes(png)
        print(f"OK: {args.svg}" + (f" e {args.png}" if args.png else ""))
        return 0
    except Exception as ex:
        print(f"ERRO: {ex}", file=sys.stderr)
        return 1


if __name__ == "__main__": sys.exit(main())
