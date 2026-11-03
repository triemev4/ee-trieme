"""Extrai o texto visível de um deck HTML, tela a tela (cada <section>).

Uso: python extrair_telas.py <deck.html> [--saida arquivo.md] [--tela <nome ou número>]...

Saída em Markdown: "## Tela N · eyebrow · título" e as linhas da tela, incluindo as notas de rodapé
de fonte. Sem HTML, CSS, script nem comentário. Fica de fora o texto marcado como interno do consultor
(classe interno, so-consultor, nota-consultor, ou atributo data-interno). A pausa (.pausa) é pergunta
ao cliente e fica. Serve de entrada ao ensaio com o cliente simulado. Só biblioteca padrão.

--tela devolve só as telas pedidas (repetível; com várias, sai a união, na ordem do deck). O texto dado precisa abrir
o nome da tela, sem diferenciar maiúscula nem acento. Nome da tela: o eyebrow (de "01 · Rastreamento" vale também
"Rastreamento", sem o número da frente) ou, na capa (a section hero), o texto do hero (a etiqueta ou o título). Um número
(--tela 2) escolhe a tela pela posição, contando de 1. Cada tela guarda o número da posição no deck ("## Tela 12").
Nenhuma tela achada: avisa no stderr e sai com código 0, sem saída. Sem --tela, a saída é a do deck inteiro.
"""
import sys
sys.dont_write_bytecode = True
import argparse
import re
import unicodedata
from html.parser import HTMLParser
from pathlib import Path

IGNORAR = {"script", "style", "noscript", "template", "head"}
VAZIOS = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}
QUEBRA = {"section", "div", "p", "li", "ul", "ol", "h1", "h2", "h3", "h4", "h5", "h6", "tr", "table",
          "blockquote", "figure", "figcaption", "header", "footer", "article", "dt", "dd", "details", "summary"}
CLASSES_INTERNAS = {"interno", "so-consultor", "nota-consultor"}
CLASSES_EYEBROW = {"eyebrow", "hero-tag"}


def limpar(txt):
    return re.sub(r"\s+", " ", txt).strip()


class Extrator(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.telas = []
        self.pilha = []          # (tag, papel) dos elementos abertos dentro de uma tela
        self.tela = None
        self.fundo_secao = 0
        self.ignorar = 0         # profundidade de elementos ignorados
        self.linha = []
        self.papel_ativo = None  # "eyebrow" ou "titulo" enquanto dentro de um
        self.buf_papel = []
        self.negrito_fechou = False

    def _fecha_linha(self):
        txt = limpar("".join(self.linha))
        self.linha = []
        if txt and self.tela is not None:
            self.tela["linhas"].append(txt)

    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        classes = set((d.get("class") or "").split())
        if self.ignorar:
            if tag not in VAZIOS:
                self.ignorar += 1
            return
        interno = bool(classes & CLASSES_INTERNAS) or "data-interno" in d
        if tag in IGNORAR or interno:
            if tag not in VAZIOS:
                self.ignorar = 1
            return
        if tag == "section":
            self.fundo_secao += 1
            if self.fundo_secao == 1:
                self.tela = {"eyebrow": "", "titulo": "", "linhas": [], "hero": "hero" in classes}
                self.telas.append(self.tela)
                self.linha = []
                return
        if self.tela is None:
            return
        if tag in QUEBRA:
            self._fecha_linha()
        if tag == "br":
            self.linha.append(" ")
            if self.papel_ativo:
                self.buf_papel.append(" ")
        if tag in VAZIOS:
            return
        papel = None
        if self.papel_ativo is None:
            if classes & CLASSES_EYEBROW and not self.tela["eyebrow"]:
                papel = "eyebrow"
            elif tag in ("h1", "h2", "h3") and not self.tela["titulo"]:
                papel = "titulo"
            if papel:
                self.papel_ativo = papel
                self.buf_papel = []
        self.pilha.append((tag, papel))

    def handle_endtag(self, tag):
        if self.ignorar:
            if tag not in VAZIOS:
                self.ignorar -= 1
            return
        if self.tela is None:
            return
        if tag == "section":
            self.fundo_secao -= 1
            self._fecha_linha()
            if self.fundo_secao == 0:
                self.tela = None
                self.pilha = []
            return
        if tag in VAZIOS:
            return
        # fecha o elemento aberto mais próximo com a mesma tag
        for i in range(len(self.pilha) - 1, -1, -1):
            if self.pilha[i][0] == tag:
                papel = self.pilha[i][1]
                del self.pilha[i:]
                if papel and papel == self.papel_ativo:
                    self.tela[papel] = limpar("".join(self.buf_papel))
                    self.papel_ativo = None
                break
        self.negrito_fechou = tag in ("b", "strong")
        if tag in QUEBRA:
            self._fecha_linha()

    def handle_data(self, data):
        if self.ignorar or self.tela is None:
            return
        if self.negrito_fechou and data[:1].isalnum():
            data = " " + data
        self.negrito_fechou = False
        self.linha.append(data)
        if self.papel_ativo:
            self.buf_papel.append(data)

    def handle_comment(self, data):
        pass


def extrair(html):
    p = Extrator()
    p.feed(html)
    p.close()
    return p.telas


def _norm(s):
    s = unicodedata.normalize("NFD", s)
    return re.sub(r"\s+", " ", "".join(c for c in s if unicodedata.category(c) != "Mn")).casefold().strip()


def nomes_da_tela(t):
    """Nomes pelos quais --tela acha a tela, já normalizados."""
    if t.get("hero"):
        brutos = [t["titulo"], t["eyebrow"]]
    else:
        brutos = [t["eyebrow"] or t["titulo"]]
        sem_numero = re.sub(r"^\d+\s*[·.:-]\s*", "", brutos[0])
        if sem_numero != brutos[0]:
            brutos.append(sem_numero)
    return [_norm(b) for b in brutos if b]


def escolher(telas, pedidos):
    """(posições escolhidas, na ordem do deck; pedidos sem tela). Posições contam de 1."""
    achadas, sem = set(), []
    for ped in pedidos:
        ped = ped.strip()
        if ped.isdigit():
            n = int(ped)
            ok = [n] if 1 <= n <= len(telas) else []
        else:
            alvo = _norm(ped)
            ok = [i for i, t in enumerate(telas, 1) if alvo and any(n.startswith(alvo) for n in nomes_da_tela(t))]
        if ok:
            achadas.update(ok)
        else:
            sem.append(ped)
    return sorted(achadas), sem


def formatar(telas, posicoes=None):
    saida = []
    for i, t in enumerate(telas, 1):
        if posicoes is not None and i not in posicoes:
            continue
        cab = " · ".join(x for x in (t["eyebrow"], t["titulo"]) if x)
        saida.append(f"## Tela {i}" + (f" · {cab}" if cab else ""))
        vistos = {t["eyebrow"], t["titulo"]}
        corpo = [ln for ln in t["linhas"] if ln not in vistos]
        saida.extend(corpo)
        saida.append("")
    return "\n".join(saida).rstrip() + "\n"


def main():
    ap = argparse.ArgumentParser(description="Extrai o texto de um deck HTML, tela a tela.")
    ap.add_argument("deck", help="HTML do deck")
    ap.add_argument("--saida", help="arquivo .md de saída (padrão: stdout)")
    ap.add_argument("--tela", action="append", default=[], metavar="NOME_OU_NUMERO",
                    help="só esta tela (repetível): o começo do nome da tela, ou a posição contando de 1")
    a = ap.parse_args()
    for f in (sys.stdout, sys.stderr):
        try:
            f.reconfigure(encoding="utf-8")
        except Exception:
            pass
    caminho = Path(a.deck)
    if not caminho.is_file():
        sys.exit(f"ERRO: o arquivo não existe: {caminho}")
    telas = extrair(caminho.read_text(encoding="utf-8", errors="replace"))
    if not telas:
        sys.exit(f"ERRO: nenhuma <section> em {caminho}")
    posicoes = None
    if a.tela:
        posicoes, sem = escolher(telas, a.tela)
        for ped in sem:
            print(f"AVISO: nenhuma tela começa com '{ped}' em {caminho.name} ({len(telas)} telas)", file=sys.stderr)
        if not posicoes:
            return
    texto = formatar(telas, posicoes)
    if a.saida:
        Path(a.saida).write_text(texto, encoding="utf-8")
        print(f"{len(telas) if posicoes is None else len(posicoes)} telas, {len(texto.splitlines())} linhas em {a.saida}", file=sys.stderr)
    else:
        sys.stdout.write(texto)


if __name__ == "__main__":
    main()
