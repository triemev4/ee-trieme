#!/usr/bin/env python3
"""Preenche o molde HTML de uma semana com os textos de um cliente (R14, seção 2.7 do Padrão EE).

Uso:
    python preencher_molde.py <molde.html> <textos.json> <saida.html>
    python preencher_molde.py --listar <molde.html>
    python preencher_molde.py --validar <molde.html> <textos.json>

O assistente nunca abre o HTML do molde: `--listar` mostra os caminhos que o molde espera e
`moldes/semana-N.textos.json` traz um exemplo completo. O contrato de marcação está em `moldes/README.md`.

Marcações lidas (todas saem do HTML final):
    data-t="tela-04.titulo"     troca o conteúdo pelo texto do JSON (texto puro; **assim** vira negrito e [fonte](https://...) vira link)
    data-lista="tela-05.frentes" repete o bloco uma vez por item da lista; dentro dele, caminhos relativos começam com ponto
    data-opcional/condensavel  usa opcionais.tela-NN; condensável aparece por padrão (B4)
    data-img="tela-08.print"    se o JSON traz o caminho de uma imagem, o conteúdo vira <img> embutida
    data-estilo="--pct:a.b.c"   põe a variável CSS no style do elemento, com o número do JSON
    data-num                    troca os dígitos do começo do texto do elemento pela ordem (01, 02, ...) entre os que ficaram;
                                "03 · Meta Ads" vira "02 · Meta Ads" se uma tela numerada antes dela saiu

Chaves do JSON que começam com "_" são notas e são ignoradas.
Código de saída: 0 ok, 1 erro (nada é gravado).
"""
import sys
sys.dont_write_bytecode = True
import argparse, base64, copy, io, json, math, re
from datetime import datetime
from pathlib import Path

try:
    from bs4 import BeautifulSoup, Comment, NavigableString, Tag
except ImportError:
    sys.stderr.write("ERRO: falta o pacote beautifulsoup4 (pip install -r scripts/requirements.txt)\n")
    sys.exit(1)

ATRIBUTOS = ("data-t", "data-lista", "data-opcional", "data-condensavel", "data-img", "data-estilo", "data-classe", "data-num")
MIME = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp",
        ".gif": "image/gif", ".svg": "image/svg+xml"}
NEGRITO = re.compile(r"\*\*(.+?)\*\*", re.S)
# **negrito** ou [texto](https://...): o link da fonte vira <a> de verdade, para o checar_fontes.py abrir (decisão 0044)
MARCA = re.compile(r"\*\*(.+?)\*\*|\[([^\]\n]+)\]\((https?://[^\s)]+)\)", re.S)
NUMERO_CSS = re.compile(r"^-?\d+(?:[.,]\d+)?%?$")
DIGITOS_INICIAIS = re.compile(r"^\d+")
ESTILO_IMG = "display:block;max-width:100%;height:auto"
PLACEHOLDER = re.compile(r"\b(?:PREENCHER|TODO|TBD)\b|\{\{[^{}]+\}\}|\$\{[^{}]+\}")
HORIZONTES = {"H1": (0, 30), "H2": (30, 180), "H3": (180, 365)}


class Falha(ValueError):
    pass


def validar_dados(raiz, validar_placeholders=True):
    """Confere somente contratos explícitos nos dados, sem interpretar frases estratégicas.

    Notas com '_' e telas opcionais desligadas não são conteúdo ativo. Metadados opcionais:
    provas[].id, referencias[], reclassificacoes[], valor/origem/unidade/periodo,
    data[_inicio|_fim|_base], horizonte/prazo_dias e verbo/objeto/responsavel/conclusao.
    A existência da origem não comprova a veracidade do número; isso requer conferência posterior.
    """
    if not isinstance(raiz, dict):
        raise Falha("raiz: esperado objeto")
    avisos, ids = [], set()

    def texto(valor, caminho):
        if not isinstance(valor, str) or not valor.strip():
            raise Falha(f"{caminho}: esperado texto não vazio")

    def data(valor, caminho):
        texto(valor, caminho)
        for formato in ("%Y-%m-%d", "%d/%m/%Y"):
            try:
                d = datetime.strptime(valor, formato).date()
                if d.strftime(formato) == valor:
                    return d
            except ValueError:
                pass
        raise Falha(f"{caminho}: data inválida; use aaaa-mm-dd ou dd/mm/aaaa")

    provas = raiz.get("provas", [])
    if not isinstance(provas, list):
        raise Falha("provas: esperado lista")
    for i, prova in enumerate(provas):
        cam = f"provas[{i}]"
        if not isinstance(prova, dict):
            raise Falha(f"{cam}: esperado objeto com id")
        pid = prova.get("id")
        texto(pid, f"{cam}.id")
        if pid in ids:
            raise Falha(f"{cam}.id: identificador duplicado {pid!r}")
        ids.add(pid)

    def visitar(obj, caminho="", horizonte=None):
        if isinstance(obj, str):
            if any((ord(c) < 0x20 and c not in "\t\n\r") or 0xD800 <= ord(c) <= 0xDFFF
                   or ord(c) in (0xFFFE, 0xFFFF) for c in obj):
                raise Falha(f"{caminho}: caractere incompatível com XML/DOCX")
            if validar_placeholders and PLACEHOLDER.search(obj):
                raise Falha(f"{caminho}: placeholder não substituído")
        elif isinstance(obj, (int, float)) and not isinstance(obj, bool):
            if not math.isfinite(obj):
                raise Falha(f"{caminho}: número precisa ser finito")
        elif isinstance(obj, list):
            for i, valor in enumerate(obj):
                visitar(valor, f"{caminho}[{i}]", horizonte)
        elif isinstance(obj, dict):
            datas = {k: data(v, f"{caminho + '.' if caminho else ''}{k}") for k, v in obj.items()
                     if k in ("data", "data_inicio", "data_fim", "data_base")}
            if "data_inicio" in datas and "data_fim" in datas and datas["data_fim"] < datas["data_inicio"]:
                raise Falha(f"{caminho + '.' if caminho else ''}data_fim: anterior a data_inicio")
            if "valor" in obj and isinstance(obj["valor"], (int, float)) and not isinstance(obj["valor"], bool):
                if any(k in obj for k in ("origem", "fonte", "unidade", "periodo")):
                    for k in ("origem", "unidade", "periodo"):
                        valor = obj.get("origem", obj.get("fonte")) if k == "origem" else obj.get(k)
                        texto(valor, f"{caminho}.{k}")
                else:
                    avisos.append(f"{caminho}.valor: vínculo com origem, unidade e período não representado neste objeto; conferir a fonte do tópico")
            if "verbo" in obj or "objeto" in obj:
                for k in ("verbo", "objeto", "responsavel", "conclusao"):
                    texto(obj.get(k), f"{caminho}.{k}")
                if "condicao" in obj:
                    texto(obj["condicao"], f"{caminho}.condicao")
            if "horizonte" in obj:
                horizonte = obj["horizonte"]
                if not isinstance(horizonte, str) or horizonte not in HORIZONTES:
                    raise Falha(f"{caminho}.horizonte: esperado H1, H2 ou H3")
            prazo = obj.get("prazo_dias")
            if "prazo_dias" in obj:
                if isinstance(prazo, bool) or not isinstance(prazo, int) or prazo < 0:
                    raise Falha(f"{caminho}.prazo_dias: esperado inteiro não negativo")
            if horizonte and "data" in datas and "data_base" in raiz:
                intervalo = (datas["data"] - data(raiz["data_base"], "data_base")).days
                if prazo is not None and prazo != intervalo:
                    raise Falha(f"{caminho}.prazo_dias: diverge de data e data_base")
                prazo = intervalo
            if horizonte and prazo is not None:
                minimo, maximo = HORIZONTES[horizonte]
                if not minimo <= prazo <= maximo:
                    raise Falha(f"{caminho}.prazo_dias: {prazo} dias fora de {horizonte} ({minimo} a {maximo})")
            if obj.get("comece") is True and prazo is not None and not 0 <= prazo <= 7:
                raise Falha(f"{caminho}.prazo_dias: Comece aqui precisa caber em sete dias")
            refs = obj.get("referencias", [])
            if not isinstance(refs, list):
                raise Falha(f"{caminho + '.' if caminho else ''}referencias: esperado lista de IDs de provas")
            for i, pid in enumerate(refs):
                if not isinstance(pid, str) or pid not in ids:
                    raise Falha(f"{caminho + '.' if caminho else ''}referencias[{i}]: prova inexistente {pid!r}")
            reclassificacoes = obj.get("reclassificacoes", [])
            if not isinstance(reclassificacoes, list):
                raise Falha(f"{caminho + '.' if caminho else ''}reclassificacoes: esperado lista")
            for i, item in enumerate(reclassificacoes):
                cam = f"{caminho + '.' if caminho else ''}reclassificacoes[{i}]"
                if not isinstance(item, dict):
                    raise Falha(f"{cam}: esperado objeto")
                for k in ("id", "estado_anterior", "estado_novo", "motivo"):
                    texto(item.get(k), f"{cam}.{k}")
                if item["id"] not in ids:
                    raise Falha(f"{cam}.id: prova inexistente {item['id']!r}")
                if item["estado_anterior"] == item["estado_novo"]:
                    raise Falha(f"{cam}.estado_novo: não representa mudança de classificação")
            opcionais = raiz.get("opcionais", {})
            for k, valor in obj.items():
                if k.startswith("_") or (not caminho and isinstance(opcionais, dict) and opcionais.get(k) is False):
                    continue
                cam = f"{caminho}.{k}" if caminho else k
                visitar(valor, cam, k.upper() if k in ("h1", "h2", "h3") else horizonte)
    visitar(raiz)
    return avisos


class Ctx:
    """Estado de uma montagem. Em modo silencioso (parte que vai ser descartada) erros não contam."""

    def __init__(self, soup, raiz, base, usados, faltas, erros, avisos, secoes_vistas, silencioso=False):
        self.soup, self.raiz, self.base = soup, raiz, base
        self.usados, self.faltas, self.erros, self.avisos = usados, faltas, erros, avisos
        self.secoes_vistas = secoes_vistas
        self.silencioso = silencioso

    def quieto(self):
        return Ctx(self.soup, self.raiz, self.base, self.usados, [], [], [], self.secoes_vistas, True)

    def falta(self, caminho, tipo="texto"):
        if not self.silencioso and caminho not in self.faltas:
            self.faltas.append(caminho)

    def erro(self, msg):
        if not self.silencioso:
            self.erros.append(msg)

    def aviso(self, msg):
        if not self.silencioso:
            self.avisos.append(msg)


# ---------- caminhos ----------

def resolver(ctx, scope, caminho):
    """Devolve (achou, valor, caminho_completo). Caminho com ponto na frente é relativo ao item da lista."""
    obj, pref = scope
    caminho = caminho.strip()
    if caminho.startswith("."):
        partes = [p for p in caminho[1:].split(".") if p]
        cur, completo = obj, pref
    else:
        partes = [p for p in caminho.split(".") if p]
        cur, completo = ctx.raiz, ""
    for p in partes:
        completo = f"{completo}.{p}" if completo else p
    achou = True
    for p in partes:
        if isinstance(cur, dict) and p in cur:
            cur = cur[p]
        else:
            achou = False
            break
    return achou, (cur if achou else None), completo


# ---------- texto ----------

def preencher_texto(ctx, el, texto):
    el.clear()
    pos = 0
    for m in MARCA.finditer(texto):
        if m.start() > pos:
            el.append(NavigableString(texto[pos:m.start()]))
        if m.group(1) is not None:
            tag = ctx.soup.new_tag("b")
            tag.append(NavigableString(m.group(1)))
        else:
            tag = ctx.soup.new_tag("a", href=m.group(3), target="_blank", rel="noopener")
            tag.append(NavigableString(m.group(2)))
        el.append(tag)
        pos = m.end()
    if pos < len(texto) or not texto:
        el.append(NavigableString(texto[pos:]))


def aplicar_texto(ctx, el, scope):
    caminho = el["data-t"]
    del el["data-t"]
    ok, val, cam = resolver(ctx, scope, caminho)
    if not ok or val is None:
        ctx.falta(cam)
        return
    if isinstance(val, (dict, list)) or isinstance(val, bool):
        ctx.erro(f"{cam}: o molde espera um texto, o JSON traz {'lista' if isinstance(val, list) else 'objeto' if isinstance(val, dict) else 'verdadeiro/falso'}")
        return
    ctx.usados.add(cam)
    if isinstance(val, (int, float)):
        ctx.aviso(f"{cam}: o molde espera texto e o JSON traz o número {val}; saiu como \"{val}\" (se era para ser texto, ponha entre aspas)")
    elif not str(val).strip():
        ctx.aviso(f"{cam}: texto vazio, o elemento sai vazio")
    if PLACEHOLDER.search(str(val)):
        ctx.erro(f"{cam}: placeholder não substituído")
        return
    preencher_texto(ctx, el, str(val))


# ---------- imagem ----------

def aplicar_img(ctx, el, scope):
    caminho = el["data-img"]
    del el["data-img"]
    ok, val, cam = resolver(ctx, scope, caminho)
    if not ok or val in (None, ""):
        if ok:
            ctx.usados.add(cam)
        ctx.aviso(f"{cam}: sem imagem, fica o mockup")
        processar_filhos(ctx, el, scope)
        return
    alt = ""
    arquivo = val
    ctx.usados.add(cam)
    if isinstance(val, dict):
        arquivo = val.get("caminho") or val.get("arquivo")
        alt = str(val.get("alt") or "")
        for k in val:
            ctx.usados.add(f"{cam}.{k}")
    if not isinstance(arquivo, str) or not arquivo.strip():
        ctx.erro(f"{cam}: caminho de imagem inválido")
        return
    p = Path(arquivo)
    if not p.is_absolute():
        p = ctx.base / p
    if not p.is_file():
        ctx.erro(f"{cam}: imagem não encontrada: {p}")
        return
    mime = MIME.get(p.suffix.lower())
    if not mime:
        ctx.erro(f"{cam}: formato de imagem não aceito ({p.suffix}); use png, jpg, webp, gif ou svg")
        return
    # o mockup que sai também tem textos; marca como usados sem exigir
    cont = ctx.soup.new_tag("div")
    cont.append(copy.copy(el))
    processar_filhos(ctx.quieto(), cont.contents[0], scope)
    dados = base64.b64encode(p.read_bytes()).decode("ascii")
    el.clear()
    el.append(ctx.soup.new_tag("img", attrs={"src": f"data:{mime};base64,{dados}", "alt": alt, "style": ESTILO_IMG}))


# ---------- estilo ----------

def aplicar_estilo(ctx, el, scope):
    spec = el["data-estilo"]
    del el["data-estilo"]
    novos = []
    for par in spec.split(";"):
        par = par.strip()
        if not par:
            continue
        var, _, caminho = par.partition(":")
        var, caminho = var.strip(), caminho.strip()
        if not var.startswith("--") or not caminho:
            ctx.erro(f"molde com data-estilo mal escrito: \"{par}\" (esperado --variavel:caminho)")
            continue
        ok, val, cam = resolver(ctx, scope, caminho)
        if not ok or val is None:
            ctx.falta(cam)
            continue
        if isinstance(val, bool) or not isinstance(val, (int, float, str)) or not NUMERO_CSS.match(str(val).strip()):
            ctx.erro(f"{cam}: esperado um número (45 ou \"45%\"), o JSON traz {json.dumps(val, ensure_ascii=False)}")
            continue
        ctx.usados.add(cam)
        novos.append(f"{var}:{str(val).strip().replace(',', '.')}")
    if novos:
        atual = (el.get("style") or "").strip().rstrip(";").strip()
        el["style"] = (atual + ";" if atual else "") + ";".join(novos)


def aplicar_classe(ctx, el, scope):
    """Alterna classes por booleanos explícitos, inclusive no contexto de cada item."""
    spec = el["data-classe"]
    del el["data-classe"]
    classes = list(el.get("class", []))
    for par in spec.split(";"):
        classe, _, caminho = par.strip().partition(":")
        classe, caminho = classe.strip(), caminho.strip()
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_-]*", classe) or not caminho:
            ctx.erro(f"data-classe inválido: {par!r}; esperado classe:caminho")
            continue
        ok, val, cam = resolver(ctx, scope, caminho)
        if not ok:
            ctx.falta(cam)
            continue
        ctx.usados.add(cam)
        if not isinstance(val, bool):
            ctx.erro(f"{cam}: data-classe espera booleano true ou false")
            continue
        classes = [c for c in classes if c != classe]
        if val:
            classes.append(classe)
    el["class"] = classes


# ---------- lista ----------

def expandir_lista(ctx, el, scope):
    caminho = el["data-lista"]
    del el["data-lista"]
    ok, val, cam = resolver(ctx, scope, caminho)
    if not ok or val is None:
        ctx.falta(cam)
        el.decompose()
        return
    if not isinstance(val, list):
        ctx.erro(f"{cam}: o molde espera uma lista, o JSON traz {'objeto' if isinstance(val, dict) else 'valor simples'}")
        el.decompose()
        return
    ctx.usados.add(cam)
    anterior = el.previous_sibling
    sep = str(anterior) if isinstance(anterior, NavigableString) and not isinstance(anterior, Comment) and not anterior.strip() else "\n"
    for i, item in enumerate(val):
        clone = copy.copy(el)
        if i > 0:
            el.insert_before(NavigableString(sep))
        el.insert_before(clone)
        item_cam = f"{cam}[{i}]"
        tratar_corpo(ctx, clone, (item, item_cam))
    el.decompose()


# ---------- percurso ----------

def processar_filhos(ctx, el, scope):
    for filho in list(el.children):
        if isinstance(filho, Tag):
            tratar(ctx, filho, scope)


def tratar(ctx, el, scope):
    if el.has_attr("data-opcional") or el.has_attr("data-condensavel"):
        atributo = "data-opcional" if el.has_attr("data-opcional") else "data-condensavel"
        nome = el[atributo].strip()
        del el[atributo]
        ctx.secoes_vistas.add(nome)
        ops = ctx.raiz.get("opcionais")
        ligada = True
        if not isinstance(ops, dict) or nome not in ops:
            if atributo == "data-opcional":
                ctx.falta(f"opcionais.{nome}", "opcional")
        elif not isinstance(ops[nome], bool):
            ctx.erro(f"opcionais.{nome}: esperado true ou false")
        else:
            ctx.usados.add(f"opcionais.{nome}")
            ligada = ops[nome]
        if not ligada:
            cont = ctx.soup.new_tag("div")
            cont.append(copy.copy(el))
            processar_filhos(ctx.quieto(), cont, scope)  # só marca as chaves usadas; a cópia é descartada
            el.decompose()
            return
    tratar_corpo(ctx, el, scope)


def tratar_corpo(ctx, el, scope):
    if el.has_attr("data-lista"):
        expandir_lista(ctx, el, scope)
        return
    if el.has_attr("data-estilo"):
        aplicar_estilo(ctx, el, scope)
    if el.has_attr("data-classe"):
        aplicar_classe(ctx, el, scope)
    if el.has_attr("data-t"):
        aplicar_texto(ctx, el, scope)
        return
    if el.has_attr("data-img"):
        aplicar_img(ctx, el, scope)
        return
    processar_filhos(ctx, el, scope)


# ---------- listar ----------

def listar(el, nivel, mockup, linhas):
    ind = "  " * nivel
    for filho in el.children:
        if not isinstance(filho, Tag):
            continue
        sufixo = "  (só sem imagem)" if mockup else ""
        if filho.has_attr("data-opcional"):
            linhas.append(f"{ind}opcional  {filho['data-opcional']}  (true ou false em opcionais)")
        elif filho.has_attr("data-condensavel"):
            linhas.append(f"{ind}condensavel  {filho['data-condensavel']}  (padrão true; false em opcionais, conteúdo no detalhe)")
        prox = nivel
        if filho.has_attr("data-lista"):
            linhas.append(f"{ind}lista     {filho['data-lista']}")
            prox = nivel + 1
        ind2 = "  " * prox
        if filho.has_attr("data-classe"):
            for par in filho["data-classe"].split(";"):
                if par.strip():
                    classe, _, cam = par.partition(":")
                    linhas.append(f"{ind2}booleano  {cam.strip()}  (alterna classe {classe.strip()}){sufixo}")
        if filho.has_attr("data-estilo"):
            for par in filho["data-estilo"].split(";"):
                if par.strip():
                    var, _, cam = par.partition(":")
                    linhas.append(f"{ind2}numero    {cam.strip()}  (vira {var.strip()}){sufixo}")
        if filho.has_attr("data-t"):
            linhas.append(f"{ind2}texto     {filho['data-t']}{sufixo}")
            continue
        if filho.has_attr("data-img"):
            linhas.append(f"{ind2}imagem    {filho['data-img']}  (caminho de imagem ou vazio para manter o mockup){sufixo}")
            listar(filho, prox + 1, True, linhas)
            continue
        listar(filho, prox, mockup, linhas)


# ---------- chaves sobrando ----------

def folhas(obj, pref):
    if isinstance(obj, dict):
        for k, v in obj.items():
            if str(k).startswith("_"):
                continue
            yield from folhas(v, f"{pref}.{k}" if pref else str(k))
    elif isinstance(obj, list):
        if not obj:
            yield pref
        for i, v in enumerate(obj):
            yield from folhas(v, f"{pref}[{i}]")
    else:
        yield pref


# ---------- principal ----------

def ler_texto(caminho):
    with io.open(caminho, encoding="utf-8-sig", newline="") as f:
        return f.read()


def montar(molde, textos):
    html = ler_texto(molde)
    soup = BeautifulSoup(html, "html.parser")
    try:
        raiz = json.loads(ler_texto(textos))
    except json.JSONDecodeError as e:
        raise Falha(f"JSON inválido em {textos}: linha {e.lineno}, coluna {e.colno}: {e.msg}")
    if not isinstance(raiz, dict):
        raise Falha("o JSON precisa ser um objeto na raiz")
    usados, faltas, erros, avisos, secoes = set(), [], [], [], set()
    ctx = Ctx(soup, raiz, Path(textos).resolve().parent, usados, faltas, erros, avisos, secoes)
    for filho in list(soup.children):
        if isinstance(filho, Tag):
            tratar(ctx, filho, (raiz, ""))
    if faltas or erros:
        msg = []
        if faltas:
            msg.append(f"o JSON não tem {len(faltas)} caminho(s) que o molde pede:")
            msg += [f"  - {c}" for c in faltas]
        msg += [f"  {e}" for e in erros]
        raise Falha("\n".join(msg))
    avisos += validar_dados(raiz, validar_placeholders=False)
    n = 0
    erros_num = []
    for el in soup.find_all(attrs={"data-num": True}):
        n += 1
        del el["data-num"]
        primeiro = next((c for c in el.children if isinstance(c, NavigableString) and not isinstance(c, Comment)), None)
        if primeiro is None or not DIGITOS_INICIAIS.match(str(primeiro)):
            erros_num.append(f"data-num no molde: o texto do elemento não começa com dígitos ({el.get_text()[:40]!r})")
            continue
        primeiro.replace_with(NavigableString(DIGITOS_INICIAIS.sub(f"{n:02d}", str(primeiro), count=1)))
    if erros_num:
        raise Falha("\n".join(erros_num))
    sobras = [a for a in ATRIBUTOS if soup.find_all(attrs={a: True})]
    if sobras:
        raise Falha("marcação não tratada no molde (fora do alcance do script): " + ", ".join(sobras))
    ops = raiz.get("opcionais")
    if isinstance(ops, dict):
        for nome in ops:
            if not str(nome).startswith("_") and nome not in secoes:
                avisos.append(f"opcionais.{nome}: o molde não tem essa tela opcional")
    for f in folhas({k: v for k, v in raiz.items() if k != "opcionais"}, ""):
        if f and f not in usados:
            avisos.append(f"{f}: chave sem espaço no molde (sobrando)")
    return str(soup), avisos


def main():
    class Parser(argparse.ArgumentParser):
        def error(self, message):
            sys.stderr.write(f"ERRO: {message}\n")
            sys.exit(1)

    ap = Parser(description="Preenche o molde HTML de uma semana com os textos do cliente.")
    ap.add_argument("arquivos", nargs="*", help="<molde.html> <textos.json> <saida.html>")
    modos = ap.add_mutually_exclusive_group()
    modos.add_argument("--listar", action="store_true", help="imprime os caminhos que o molde espera (um só argumento: o molde)")
    modos.add_argument("--validar", action="store_true", help="valida em memória <molde.html> <textos.json>, sem gravar arquivos")
    a = ap.parse_args()
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8")
        except Exception:
            pass

    try:
        if a.listar:
            if len(a.arquivos) != 1:
                raise Falha("uso: preencher_molde.py --listar <molde.html>")
            molde = Path(a.arquivos[0])
            if not molde.is_file():
                raise Falha(f"molde não encontrado: {molde}")
            linhas = []
            listar(BeautifulSoup(ler_texto(molde), "html.parser"), 0, False, linhas)
            print("\n".join(linhas))
            return 0
        if len(a.arquivos) != (2 if a.validar else 3):
            raise Falha("uso: preencher_molde.py --validar <molde.html> <textos.json>" if a.validar else "uso: preencher_molde.py <molde.html> <textos.json> <saida.html>")
        molde, textos = map(Path, a.arquivos[:2])
        for p in (molde, textos):
            if not p.is_file():
                raise Falha(f"arquivo não encontrado: {p}")
        html, avisos = montar(molde, textos)
        for av in avisos:
            sys.stderr.write(f"AVISO: {av}\n")
        if a.validar:
            print("OK: validação em memória concluída; nenhum arquivo gravado")
            return 0
        saida = Path(a.arquivos[2])
        if saida.resolve() in (molde.resolve(), textos.resolve()):
            raise Falha("a saída não pode ser o molde nem o JSON")
        pacote = Path(__file__).resolve().parent.parent
        if saida.resolve() == pacote or pacote in saida.resolve().parents:
            raise Falha("a saída precisa ficar fora da pasta do pacote")
        saida.parent.mkdir(parents=True, exist_ok=True)
        with io.open(saida, "w", encoding="utf-8", newline="") as f:
            f.write(html)
        print(f"OK: {saida} ({len(html.encode('utf-8')) / 1024:.1f} KB)")
        return 0
    except (Falha, OSError) as e:
        sys.stderr.write(f"ERRO: {e}\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
