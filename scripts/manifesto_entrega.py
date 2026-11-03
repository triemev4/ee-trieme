"""Comprovantes locais de entrega. Não grava estado de gatilho nem faz consultas externas."""
import sys
sys.dont_write_bytecode = True
import hashlib
import json
import os
import tempfile
from pathlib import Path
from urllib.parse import unquote, urlsplit
from urllib.request import url2pathname

RAIZ_PACOTE = Path(__file__).resolve().parent.parent
NOME = "manifesto-entrega.json"
ESTADOS = {"aprovada", "reprovada", "nao_realizada"}


def fora_do_pacote(caminho):
    p = Path(caminho).resolve()
    if p == RAIZ_PACOTE or RAIZ_PACOTE in p.parents:
        raise ValueError(f"saída dentro do pacote: {p}")
    return p


def gravar_atomico(caminho, objeto):
    p = fora_do_pacote(caminho)
    p.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=p.name + ".", suffix=".tmp", dir=p.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(objeto, f, ensure_ascii=False, indent=2)
            f.write("\n")
        os.replace(tmp, p)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def sha256(p):
    p = Path(p)
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else None


def _arquivos(pasta):
    if not pasta.is_dir():
        return []
    return sorted(p for p in pasta.rglob("*") if p.is_file()
                  and not set(p.relative_to(pasta).parts) & {".git", "__pycache__"}
                  and p.name != NOME and not p.name.endswith((".tmp", ".pyc")))


def _referencias(arquivo):
    """Recursos locais de JSON/HTML/CSS, inclusive caminho ainda ausente."""
    import re
    saida = set()
    if not arquivo.is_file() or arquivo.suffix.lower() not in {".json", ".html", ".css"}:
        return saida
    texto = arquivo.read_text(encoding="utf-8", errors="replace")
    valores = []
    if arquivo.suffix.lower() == ".json":
        try:
            def andar(v):
                if isinstance(v, str):
                    valores.append(v)
                elif isinstance(v, dict):
                    for x in v.values():
                        andar(x)
                elif isinstance(v, list):
                    for x in v:
                        andar(x)
            andar(json.loads(texto))
        except ValueError:
            pass
    else:
        valores += re.findall(r'''(?:src|href|poster|data)\s*=\s*["']([^"']+)|url\(\s*["']?([^\s)'";]+)|@import\s+["']([^"']+)''', texto, re.I)
        valores = [next((s for s in x if s), "") if isinstance(x, tuple) else x for x in valores]
        for srcset in re.findall(r'''srcset\s*=\s*["']([^"']+)''', texto, re.I):
            if not srcset.startswith("data:"):
                valores += [v.strip().split()[0] for v in srcset.split(",") if v.strip()]
    for valor in valores:
        if not valor or valor.startswith(("#", "data:", "http:", "https:", "mailto:", "javascript:")):
            continue
        uri = urlsplit(valor)
        if uri.scheme.lower() == "file":
            if uri.netloc not in ("", "localhost"):
                raise ValueError("recurso file em host remoto não é acervo local")
            valor = url2pathname(uri.path)
        elif not Path(valor).is_absolute():
            valor = unquote(uri.path)
        if not valor or Path(valor).suffix.lower() not in {".png", ".jpg", ".jpeg", ".svg", ".webp", ".gif", ".avif", ".bmp", ".ico", ".tif", ".tiff", ".cur", ".html", ".css", ".js", ".json", ".md", ".pdf", ".docx", ".woff", ".woff2", ".ttf", ".otf", ".eot", ".mp4", ".webm", ".mp3", ".wav", ".ogg", ".m4a", ".vtt"}:
            continue
        p = Path(valor)
        saida.add((arquivo.parent / p).resolve() if not p.is_absolute() else p.resolve())
    return saida


def capturar(html, contexto=None, ignorar=()):
    """Fotografia de arquivos e presença/ausência. Mtime nunca participa da prova."""
    html = Path(html).resolve()
    contexto = contexto or {}
    ignorar = {Path(p).resolve() for p in ignorar}
    arvores = {html.parent, RAIZ_PACOTE}
    caminhos = {html, html.with_suffix(".docx"), html.parent / "_fonte" / "telas.md"}
    for chave in ("entrada", "ficha", "detalhe", "foto", "coleta"):
        if contexto.get(chave):
            p = Path(contexto[chave]).resolve()
            if chave == "coleta":
                arvores.add(p)
            else:
                caminhos.add(p)
    # Descoberta de ficha também cobre a chegada de uma ficha antes ausente.
    fichas = sorted(html.parent.parent.glob("*.md"))
    caminhos.update(fichas)
    inventario = {}
    for pasta in sorted(arvores):
        arquivos = [p for p in _arquivos(pasta) if p.resolve() not in ignorar]
        inventario[str(pasta)] = [str(p.relative_to(pasta)) for p in arquivos] if pasta.is_dir() else None
        caminhos.update(arquivos)
    caminhos.difference_update(ignorar)
    fila = list(caminhos)
    while fila:
        for p in _referencias(fila.pop()):
            if p not in caminhos and p not in ignorar:
                caminhos.add(p)
                fila.append(p)
    # A lista das fichas é parte da fotografia, mesmo quando vazia.
    inventario["fichas:" + str(html.parent.parent)] = [str(p) for p in fichas]
    return {"arquivos": {str(p): sha256(p) for p in sorted(caminhos)}, "arvores": inventario}


def capturar_insumos(html, contexto=None):
    """Versão sem os derivados que a preparação está autorizada a substituir."""
    html = Path(html).resolve()
    fonte = html.parent / "_fonte"
    derivados = [html, html.with_suffix(".docx"), fonte / "telas.md",
                 fonte / "verificacao-entrega.json", fonte / "fontes-entrega.json"]
    return capturar(html, contexto, ignorar=derivados)


def contexto_manifesto(html):
    try:
        m = json.loads((Path(html).parent / "_fonte" / NOME).read_text(encoding="utf-8"))
        return m.get("contexto", {}) if isinstance(m, dict) else {}
    except (OSError, ValueError):
        return {}


def comprovante_basico(html, configuracao_esperada=None):
    """Resultado concluído e atual, incluindo reprovação; None não dispensa conferência."""
    try:
        m = json.loads((Path(html).parent / "_fonte" / NOME).read_text(encoding="utf-8"))
        basico = m["etapas"]["basica"]
        if m["versao"] != 1 or m["pacote"]["raiz"] != str(RAIZ_PACOTE):
            return None
        if configuracao_esperada is not None:
            esperado = configuracao_esperada
            config = m.get("configuracao", {})
            if config.get("semana") != esperado.get("semana") or config.get("cliente") != esperado.get("cliente"):
                return None
            ficha_m = m.get("contexto", {}).get("ficha")
            ficha_e = esperado.get("ficha")
            if (str(Path(ficha_m).resolve()) if ficha_m else None) != (str(Path(ficha_e).resolve()) if ficha_e else None):
                return None
            if "entrada" in esperado:
                entrada_m = m.get("contexto", {}).get("entrada")
                if not entrada_m or str(Path(entrada_m).resolve()) != str(Path(esperado["entrada"]).resolve()):
                    return None
        alvo = str(Path(html).resolve())
        if m.get("concluido") is not True or m.get("entrega") != alvo or alvo not in m.get("saidas", {}):
            return None
        if basico["status"] not in {"aprovada", "reprovada"}:
            return None
        if m["snapshot"] != capturar(html, m.get("contexto")):
            return None
        if not isinstance(basico.get("erros"), list) or not isinstance(basico.get("avisos"), list):
            return None
        if (basico["status"] == "reprovada") != bool(basico["erros"]):
            return None
        return basico
    except (OSError, ValueError, KeyError, TypeError):
        return None
