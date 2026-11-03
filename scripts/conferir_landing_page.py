"""Conferência local de copy, links e recursos da LP e integridade da revisão. Não aprova conteúdo."""
import sys
sys.dont_write_bytecode = True
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile
from urllib.parse import unquote, urlsplit

from bs4 import BeautifulSoup, NavigableString

PACOTE = Path(__file__).resolve().parents[1]
ATRIBUTOS_LOCAIS = {"a": ("href",), "link": ("href",), "script": ("src",), "img": ("src", "srcset"),
                    "source": ("src", "srcset"), "video": ("src", "poster"), "audio": ("src",), "track": ("src",),
                    "iframe": ("src",), "embed": ("src",), "object": ("data",), "input": ("src",),
                    "image": ("href", "xlink:href"), "use": ("href", "xlink:href")}
CSS_URL = re.compile(r"""url\(\s*(?:"([^"]*)"|'([^']*)'|([^)\s]*))\s*\)|@import\s+(?:"([^"]*)"|'([^']*)')""", re.I)
BLOCOS = set("address article aside blockquote button caption dd details dialog div dl dt fieldset figcaption figure "
             "footer form h1 h2 h3 h4 h5 h6 header hgroup label legend li main nav ol option p pre section select "
             "summary table tbody td tfoot th thead tr ul".split())
RASCUNHO = re.compile(r"\bpreencher\s*:|\blorem ipsum\b|\[falta prova")
LIMITE_TRECHOS = 10


def limpar(texto):
    texto = re.sub(r"\s+", " ", texto).strip()
    return re.sub(r"\s+([.,;:!?])", r"\1", texto)


def normalizar(texto):
    return limpar(texto).casefold()


def ler_copy(caminho):
    dado = json.loads(Path(caminho).read_text(encoding="utf-8-sig"))
    if not isinstance(dado, dict) or dado.get("versao") != 1:
        raise ValueError("copy: objeto com versao 1 obrigatório")
    cta, textos = dado.get("cta"), dado.get("textos")
    if not isinstance(cta, dict) or any(not isinstance(cta.get(k), str) or not cta[k].strip()
                                       for k in ("texto", "destino")):
        raise ValueError("copy: CTA exige texto e destino")
    destino = cta["destino"]
    if not ((destino.startswith("#") and len(destino) > 1) or
            (urlsplit(destino).scheme == "https" and urlsplit(destino).netloc)):
        raise ValueError("copy: destino deve ser âncora identificada ou URL HTTPS")
    if not isinstance(textos, list) or not textos:
        raise ValueError("copy: textos deve ser lista não vazia")
    ids = set()
    for item in textos:
        if (not isinstance(item, dict) or
            any(not isinstance(item.get(k), str) or not item[k].strip() for k in ("id", "texto")) or
            item.get("estado", "inicial") not in ("inicial", "interacao")):
            raise ValueError("copy: item exige id/texto e estado inicial ou interacao")
        if item["id"] in ids:
            raise ValueError("copy: id repetido: " + item["id"])
        ids.add(item["id"])
    return dado


def urls_css(texto):
    texto = re.sub(r"/\*.*?\*/", "", texto, flags=re.S)
    return [next((g for g in m.groups() if g), "") for m in CSS_URL.finditer(texto)]


def urls_srcset(valor):
    return re.findall(r"[\s,]*(\S*[^\s,])(?:,+|\s[^,]*)?", valor)


def referencias_html(soup):
    refs = []
    for tag in soup.find_all(list(ATRIBUTOS_LOCAIS)):
        for atributo in ATRIBUTOS_LOCAIS[tag.name]:
            valor = tag.get(atributo)
            if isinstance(valor, str):
                refs += urls_srcset(valor) if atributo == "srcset" else [valor]
    for tag in soup.find_all(style=True):
        refs += urls_css(tag["style"])
    for tag in soup.find_all("style"):
        refs += urls_css(tag.get_text())
    return refs


def caminho_local(ref):
    """Caminho do arquivo citado, sem ?query nem #fragmento; None para externo ou só âncora."""
    ref = ref.strip().replace("\\", "/")
    try:
        partes = urlsplit(ref)
    except ValueError:
        return None
    if not ref or ref.startswith(("#", "//")) or (len(partes.scheme) > 1 and partes.scheme != "file"):
        return None
    return ref if partes.scheme else unquote(partes.path)


def recursos_locais(html, soup):
    """Arquivos locais citados pelo HTML e pelos CSS locais. Ausente ou fora da pasta da LP vira erro."""
    pasta = Path(html).resolve().parent
    arquivos, erros, pendentes = [], [], [("HTML", pasta, ref) for ref in referencias_html(soup)]
    while pendentes:
        origem, base, ref = pendentes.pop(0)
        caminho = caminho_local(ref)
        if not caminho:
            continue
        alvo = None if caminho.startswith("/") or ":" in caminho else (base / caminho).resolve()
        if alvo is None:
            problema = "referência com caminho absoluto"
        elif not alvo.is_relative_to(pasta):
            problema = "referência fora da pasta da LP"
        elif not alvo.is_file():
            problema = "arquivo local ausente"
        else:
            if alvo not in arquivos:
                arquivos.append(alvo)
                if alvo.suffix.lower() == ".css":
                    css = alvo.read_text(encoding="utf-8", errors="replace")
                    pendentes += [(alvo.relative_to(pasta).as_posix(), alvo.parent, r) for r in urls_css(css)]
            continue
        mensagem = f"{origem}: {problema}: {ref.strip()}"
        if mensagem not in erros:
            erros.append(mensagem)
    return arquivos, erros


def blocos_de_texto(tag, saida=None):
    """Texto de cada bloco (parágrafo, item, botão...), com a formatação interna junta."""
    saida = [[]] if saida is None else saida
    for filho in tag.children:
        if isinstance(filho, NavigableString):
            if type(filho) is NavigableString and filho.strip():
                saida[-1].append(filho.strip())
        elif any(c.startswith(("material-symbols", "material-icons")) for c in filho.get("class", [])):
            continue
        elif filho.name in BLOCOS:
            saida.append([])
            blocos_de_texto(filho, saida)
            saida.append([])
        else:
            blocos_de_texto(filho, saida)
    return [" ".join(bloco) for bloco in saida if bloco]


def fora_da_copy(blocos, conhecidos):
    """Trechos do HTML que não vêm da copy (textos de qualquer estado e CTA)."""
    normais = [normalizar(t) for t in conhecidos]
    padroes = [re.compile(r"(?<!\w)" + re.escape(limpar(t)) + r"(?!\w)", re.I)
               for t in sorted(conhecidos, key=len, reverse=True)]
    achados = []
    for bloco in map(limpar, blocos):
        parte_da_copy = re.compile(r"(?<!\w)" + re.escape(bloco.casefold()) + r"(?!\w)")
        if any(parte_da_copy.search(c) for c in normais):
            continue
        for padrao in padroes:
            bloco = padrao.sub("\n", bloco)
        for trecho in bloco.split("\n"):
            trecho = trecho.lstrip(" .,;:!?·•|-").rstrip(" ,;:·•|-")
            if re.search(r"[^\W\d_]", trecho) and not RASCUNHO.search(trecho.casefold()) and trecho not in achados:
                achados.append(trecho)
    return achados


def conferir(html, copy):
    """Devolve o resultado e os arquivos locais citados pela página."""
    dado = ler_copy(copy)
    soup = BeautifulSoup(Path(html).read_text(encoding="utf-8-sig"), "html.parser")
    recursos, erros_recursos = recursos_locais(html, soup)
    erros, avisos = [], []
    if not soup.html or not str(soup.html.get("lang", "")).lower().startswith("pt"):
        erros.append("HTML: idioma português não declarado")
    if not soup.find("meta", attrs={"name": "viewport"}):
        erros.append("HTML: viewport ausente")
    body = soup.body
    if body is None:
        return {"erros": erros + ["HTML: body ausente"] + erros_recursos, "avisos": avisos}, recursos
    for tag in body.find_all(["script", "style", "template", "noscript"]):
        tag.decompose()
    estados = normalizar(body.get_text(" ", strip=True))
    blocos = blocos_de_texto(body)
    for tag in list(body.find_all(True)):
        if tag.attrs is None:
            continue
        estilo = re.sub(r"\s+", "", tag.get("style", "")).lower()
        if tag.has_attr("hidden") or tag.get("aria-hidden") == "true" or "display:none" in estilo or "visibility:hidden" in estilo:
            tag.decompose()
    visivel = normalizar(body.get_text(" ", strip=True))
    for item in dado["textos"]:
        texto = normalizar(item["texto"])
        if item.get("estado") == "interacao":
            if texto not in estados:
                avisos.append("Texto de interação fora do HTML estático, exige prova no navegador: " + item["id"])
        elif texto not in visivel:
            erros.append("copy ausente ou alterada: " + item["id"])
    if RASCUNHO.search(estados):
        erros.append("HTML: marcador de rascunho presente")
    destinos = [soup.html, body, *body.find_all(id=True)]
    ids = Counter(tag["id"] for tag in destinos if tag is not None and tag.has_attr("id"))
    for id_, n in ids.items():
        if n > 1:
            erros.append("HTML: id duplicado: " + id_)
    for link in body.find_all("a", href=True):
        href = link["href"]
        if href.startswith("#") and unquote(href[1:]) not in ids:
            erros.append("HTML: âncora sem destino: " + href)
    erros += erros_recursos
    cta = dado["cta"]
    links = [tag for tag in body.find_all("a") if normalizar(tag.get_text(" ", strip=True)) == normalizar(cta["texto"])]
    if not links:
        erros.append("CTA: link com o texto aprovado ausente")
    elif any(tag.get("href") != cta["destino"] for tag in links):
        erros.append("CTA: destino diferente do aprovado")
    trechos = fora_da_copy(blocos, [item["texto"] for item in dado["textos"]] + [cta["texto"]])
    avisos += ["Texto fora da copy: " + (t if len(t) <= 100 else t[:97] + "...") for t in trechos[:LIMITE_TRECHOS]]
    if len(trechos) > LIMITE_TRECHOS:
        avisos.append(f"Texto fora da copy: mais {len(trechos) - LIMITE_TRECHOS} trechos")
    if len(body.find_all("h1")) != 1:
        avisos.append("Conferir hierarquia: quantidade de H1 diferente de um")
    avisos.append("Revisão editorial, visual, estados de interação e responsividade exigem inspeção no navegador")
    return {"erros": erros, "avisos": avisos}, recursos


def assinatura(caminho):
    return hashlib.sha256(Path(caminho).read_bytes()).hexdigest()


def registrar(caminho, arquivos, resultado):
    """Grava os hashes com caminhos relativos à pasta do comprovante: mover a pasta inteira não invalida."""
    destino = Path(caminho).resolve()
    arquivos = {Path(p).resolve() for p in arquivos}
    if destino.is_relative_to(PACOTE):
        raise ValueError("comprovante deve ficar fora do pacote")
    if destino in arquivos:
        raise ValueError("comprovante não pode sobrescrever entrada")
    try:
        relativos = {Path(os.path.relpath(p, destino.parent)).as_posix(): p for p in arquivos}
    except ValueError:
        raise ValueError("comprovante deve ficar no mesmo disco dos arquivos conferidos") from None
    dados = {"versao": 2, "tipo": "conferencia-lp", "conferido_em": datetime.now(timezone.utc).isoformat(),
             "arquivos": [{"caminho": r, "sha256": assinatura(relativos[r])} for r in sorted(relativos)],
             **resultado}
    destino.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=destino.parent,
                                     prefix=".conferencia-lp-", suffix=".tmp", delete=False) as handle:
        temporario = Path(handle.name)
        handle.write(json.dumps(dados, ensure_ascii=False, indent=2) + "\n")
    try:
        temporario.replace(destino)
    finally:
        temporario.unlink(missing_ok=True)
    return assinatura(destino)


def validar_revisao(caminho, sha256_esperado=None):
    if sha256_esperado is not None:
        if not re.fullmatch(r"[a-f0-9]{64}", sha256_esperado):
            raise ValueError("SHA-256 esperado inválido")
        if assinatura(caminho) != sha256_esperado:
            return {"erros": ["comprovante diferente da revisão registrada"], "avisos": []}
    dado = json.loads(Path(caminho).read_text(encoding="utf-8-sig"))
    if isinstance(dado, dict) and dado.get("tipo") == "conferencia-lp" and dado.get("versao") == 1:
        return {"erros": ["comprovante antigo, com caminho absoluto: rode verificar de novo e aprove o novo hash"],
                "avisos": []}
    if (not isinstance(dado, dict) or dado.get("versao") != 2 or dado.get("tipo") != "conferencia-lp" or
        dado.get("erros") != [] or not isinstance(dado.get("arquivos"), list) or len(dado["arquivos"]) < 2):
        raise ValueError("comprovante inválido ou sem arquivos conferidos")
    base = Path(caminho).resolve().parent
    erros = []
    for item in dado["arquivos"]:
        if (not isinstance(item, dict) or not isinstance(item.get("caminho"), str) or
            not isinstance(item.get("sha256"), str) or not re.fullmatch(r"[a-f0-9]{64}", item["sha256"])):
            raise ValueError("entrada inválida no comprovante")
        p = base / item["caminho"]
        if not p.is_file() or assinatura(p) != item["sha256"]:
            erros.append("revisão desatualizada: " + item["caminho"])
    return {"erros": erros, "avisos": ["Integridade não substitui aprovação humana nem reconciliação com novas decisões da ficha"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="acao", required=True)
    verificar = sub.add_parser("verificar")
    verificar.add_argument("html")
    verificar.add_argument("--copy", required=True)
    verificar.add_argument("--dependencia", action="append", default=[])
    verificar.add_argument("--comprovante")
    validar = sub.add_parser("validar-revisao")
    validar.add_argument("comprovante")
    validar.add_argument("--sha256-esperado")
    args = parser.parse_args()
    try:
        if args.acao == "validar-revisao":
            resultado = validar_revisao(args.comprovante, args.sha256_esperado)
        else:
            resultado, recursos = conferir(args.html, args.copy)
            if args.comprovante and not resultado["erros"]:
                entradas = [args.html, args.copy, *args.dependencia, *recursos]
                resultado["comprovante_sha256"] = registrar(args.comprovante, entradas, resultado)
        print(json.dumps(resultado, ensure_ascii=False, indent=2))
        return 1 if resultado["erros"] else 0
    except (OSError, ValueError, TypeError) as exc:
        print(json.dumps({"erros": [str(exc)], "avisos": []}, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass
    sys.exit(main())
