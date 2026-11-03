"""Verificador de entrega da EE (portão antes de apresentar ou enviar).

Uso:
    python verificar_entrega.py <entrega.html> --semana N [--cliente "<Nome>"] [--ficha <ficha.md>]
                                [--outros-clientes "<A>,<B>"] [--visual] [--resultado-json <resultado.json>]

Erro bloqueia a entrega (código de saída 1). Aviso pede revisão humana.
Regras de origem: base-de-todo-encontro.md (B0 a B13) e esqueleto/semana-N-*.md.
A sequência de telas não está neste código: o verificador lê a coluna da tela da tabela "Sequência de
telas" do esqueleto da semana (<raiz do pacote>/skills/estruturacao-estrategica/esqueleto/semana-N-*.md).
Linha marcada "(opcional)" conta no total permitido: o deck pode ter todas as telas da tabela, no máximo.
Erro para `[falta prova` no texto visível. Aviso para termo da coluna "evitar" de padrao/glossario.md.
--visual chama scripts/conferir_visual.py (R15): abre cada tela em 1280x720 num navegador sem tela e acusa texto
estourando, fonte pequena e tela com texto demais. Sem playwright ou sem navegador, registra etapa
não realizada e bloqueia a conferência solicitada. --resultado-json preserva o texto humano e grava
estados explícitos das etapas; código zero sozinho não comprova que elas rodaram.
Na conferência final, uma vez antes de entregar, rode também --visual e scripts/checar_fontes.py (B2),
que abre cada link citado e procura na página os números da tela.

--ficha lê a tabela de números-fonte da ficha do cliente
(| id | dado | valor | unidade | período | dono do número | fonte e data | situação | decisivo | usado em |)
e confere o deck contra ela: valor "substituído" no deck é erro; valor "vigente" com decisivo
"sim" que não aparece no deck é aviso. A ficha vem primeiro, o deck depois.
"""
import sys
sys.dont_write_bytecode = True
import argparse, base64, io, json, os, re, subprocess, unicodedata
from decimal import Decimal, ROUND_HALF_UP
from html import unescape
from html.parser import HTMLParser
from pathlib import Path
from bs4 import BeautifulSoup

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

TRAVESSAO = chr(0x2014)

# Nome de caso de referência de layout que não pode vazar para a entrega de outro cliente.
CASOS_REFERENCIA = ["Empresa Exemplo"]

NOMES_OFICIAIS = ["Kickoff", "Pesquisa de Mercado", "Diagnóstico de Marketing", "Diagnóstico Comercial",
                  "Planejamento Estratégico + Entregáveis"]

PROIBIDOS = {
    r"\bJobs?[- ]to[- ]be[- ]Done\b|\bJTBD\b": "Jobs-to-be-Done não faz parte da EE",
    r"Diagnóstico de Vendas": "nome revogado (usar Diagnóstico Comercial)",
    r"Plano de Marketing e Vendas": "nome revogado (usar Planejamento Estratégico + Entregáveis)",
    r"\bQNP\b": "QNP é processo separado, nunca vira tela",
}
ABM = r"\bABM\b|Account[- ]Based"
CRM_FORNECEDORES = r"\b(Kommo|RD Station CRM|HubSpot|Pipedrive|Salesforce|Ploomes|Agendor|Moskit|Zoho CRM)\b"
MARCADORES = r"\[\[|\]\]|PREENCHER|\[\.\.\.\]|\bTODO\b|\bXXX\b|\{\{|\}\}|[Ll]orem ipsum"  # sensível a maiúsculas: "todo" e "preencher" são palavras comuns
FALTA_PROVA = r"\[falta prova"  # marcador de rascunho da régua de escrita: nunca vai ao cliente
CAMPO_PENDENTE = r"\ba (?:coletar|anexar)\b"
TITULO_PROIBIDO = [
    (r"Por onde começar", "Por onde começar"),
    (r"\bAnexo\b", "Anexo"),
    (r"\b(?:Ato|ATO)\s", "Ato"),
]


# ---------- leitura do HTML ----------

def visivel(html):
    return re.sub(r"(?s)<style.*?</style>|<script.*?</script>|<!--.*?-->", " ", html)


def texto(html):
    return unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", visivel(html))))


def secoes(html):
    return re.findall(r"(?s)<section.*?</section>", visivel(html))


def limpa_tags(s):
    return re.sub(r"\s+", " ", unescape(re.sub(r"<[^>]+>", " ", s))).strip()


def titulos_da_tela(sec):
    """Títulos (h1 a h4) e eyebrows/hero-tag de uma tela."""
    ts = [limpa_tags(m.group(1)) for m in re.finditer(r"(?s)<h[1-4][^>]*>(.*?)</h[1-4]>", sec)]
    ts += [limpa_tags(m.group(1)) for m in re.finditer(r'class="[^"]*\b(?:eyebrow|hero-tag)\b[^"]*"[^>]*>([^<]*)<', sec)]
    return [t for t in ts if t]


def nome_da_tela(sec):
    m = re.search(r'class="[^"]*\beyebrow\b[^"]*"[^>]*>([^<]*)<', sec)
    return limpa_tags(m.group(1)) if m else "capa"


def textos_da_classe(html, classe):
    """Texto de cada elemento que tem a classe dada (conta a profundidade do mesmo tipo de tag)."""
    class P(HTMLParser):
        def __init__(self):
            super().__init__()
            self.tag, self.depth, self.buf = None, 0, []

        def handle_starttag(self, tag, attrs):
            if self.depth:
                if tag == self.tag:
                    self.depth += 1
            elif classe in (dict(attrs).get("class") or "").split():
                self.tag, self.depth = tag, 1
                self.buf.append("")

        def handle_endtag(self, tag):
            if self.depth and tag == self.tag:
                self.depth -= 1

        def handle_data(self, data):
            if self.depth:
                self.buf[-1] += data + " "

    p = P()
    p.feed(visivel(html))
    return [re.sub(r"\s+", " ", b).strip() for b in p.buf]


def pos_classe(sec, classe, ini=0):
    m = re.compile(r'class="(?:[^"]*\s)?' + re.escape(classe) + r'(?:\s[^"]*)?"').search(sec, ini)
    return m.start() if m else None


# ---------- esqueleto da semana: a sequência mora lá, não aqui ----------

RAIZ_PACOTE = Path(__file__).resolve().parent.parent
PALAVRAS_VAZIAS = {"como", "com", "para", "dos", "das", "que", "entre", "mais", "hoje", "este", "esta",
                   "neste", "semana", "encontro", "encontros", "tela", "uma", "por", "opcional"}


def ler_esqueleto(semana):
    """Tabela 'Sequência de telas' do esqueleto da semana: lista de (nome da tela, opcional), uma por linha,
    lida da coluna cujo cabeçalho começa com 'Tela'. Marca "(opcional)" no nome torna a linha opcional. None se não achar."""
    pasta = RAIZ_PACOTE / "skills" / "estruturacao-estrategica" / "esqueleto"
    achados = sorted(pasta.glob(f"semana-{semana}-*.md"))
    if not achados:
        return None
    telas, dentro, col = [], False, 1
    for ln in io.open(achados[0], encoding="utf-8").read().splitlines():
        ln = ln.strip()
        if ln.startswith("## "):
            dentro = sem_acento(ln).startswith("## sequencia de telas")
            col = 1
        elif dentro and ln.startswith("|"):
            c = [x.strip() for x in ln.strip("|").split("|")]
            if c and not c[0].isdigit():
                for i, h in enumerate(c):
                    if sem_acento(h).startswith("tela"):
                        col = i
                        break
            elif len(c) > col and c[0].isdigit():
                nome = re.sub(r"[`*]", "", c[col])
                opcional = re.search(r"\(\s*opcional\s*\)", nome, re.I) is not None
                telas.append((re.sub(r"\s*\(\s*opcional\s*\)", "", nome, flags=re.I).strip(), opcional))
    return telas or None


def palavras_significativas(s):
    return {w for w in re.findall(r"[a-z0-9]{3,}", sem_acento(s)) if w not in PALAVRAS_VAZIAS}


def palavra_em_comum(a, b):
    return any(x == y or (len(x) >= 5 and len(y) >= 5 and x[:5] == y[:5]) for x in a for y in b)


def e_continuacao(sec):
    return "continuacao" in sem_acento(nome_da_tela(sec))


def fora_de_ordem(secs, marcadores):
    """marcadores: [(nome, teste(sec))] na ordem do esqueleto. Cada tela tem de vir depois da anterior.
    Devolve os nomes das telas encontradas só antes do ponto onde deveriam estar (tela ausente não conta aqui)."""
    fora, pos = [], -1
    for nome, teste in marcadores:
        idx = [i for i, sec in enumerate(secs) if teste(sec)]
        depois = [i for i in idx if i > pos]
        if depois:
            pos = depois[0]
        elif idx:
            fora.append(nome)
    return fora


def comeca_com(sec, prefixo):
    return sem_acento(nome_da_tela(sec)).startswith(sem_acento(prefixo))


ULTIMA = {2: "Próximos passos", 3: "Próximos passos", 4: "Próximos passos", 5: "Fechamento"}


def conferir_ultima_tela(s, secs, vis):
    """Valida os próximos passos executáveis e a ordem da conversa, sem julgar a hipótese."""
    erros, avisos = [], []
    nome = ULTIMA[s]
    if pos_classe(vis, "fecho") is not None:
        avisos.append("fechamento com .fecho: o resumo P, S e E saiu de uso; corte o bloco")
    if not secs or not comeca_com(secs[-1], nome):
        erros.append(f"B9 · a última tela precisa ser '{nome}'; migre o fecho antigo para esse contrato")
        return erros, avisos
    u, p_fim = secs[-1], 0
    if s != 5:
        doc = BeautifulSoup(u, "html.parser")
        acoes = doc.select(".ac")
        if not 1 <= len(acoes) <= 5:
            erros.append(f"B8 · próximos passos precisam de 1 a 5 ações (achadas: {len(acoes)})")
        if doc.select_one(".lanes"):
            avisos.append("B8 · horizontes pertencem ao fundamento/PED; simplifique o fecho intermediário")
        n_prio = sum("prio" in ac.get("class", []) for ac in acoes)
        if n_prio != 1:
            erros.append(f"B8 · o plano precisa de exatamente um .ac.prio 'Comece aqui' (achados: {n_prio})")
        elif "prio" not in acoes[0].get("class", []):
            erros.append("B8 · Comece aqui precisa ser a primeira ação")
        for i, ac in enumerate(acoes, 1):
            own = ac.select_one(".own")
            if own is None or not own.get_text(strip=True):
                erros.append(f"B8 · ação {i} sem dono e prazo em .own")
                continue
            prazo = own.select_one(".prazo")
            # Texto legado aceita separação explícita; o contrato novo marca o prazo.
            partes = own.get_text(" ", strip=True).split("·", 1)
            tem_prazo = bool(prazo and prazo.get_text(strip=True)) or (len(partes) == 2 and all(p.strip() for p in partes))
            if not tem_prazo:
                erros.append(f"B8 · ação {i} sem prazo explícito: use .prazo dentro de .own")
        if acoes:
            p_fim = pos_classe(u, "ac") or 0
        if s == 4:
            dobro = doc.select_one(".dobro")
            if dobro is None or not dobro.select("tr td"):
                erros.append("B7 · S4 sem teste do dobro (.dobro) com hipótese e evidência; inconclusivo é uma resposta válida")
            corda = doc.select_one(".corda")
            if corda is None or not corda.get_text(strip=True):
                erros.append("B7 · S4 sem corda: capacidade ou limite a medir e teste")
    pausas = [m.start() for m in re.finditer(r'class="pausa[ "]', u) if m.start() > p_fim]
    if not pausas:
        erros.append(f"B9 · '{nome}' sem .pausa no fim (a ordem é .pausa, depois .gancho)")
    elif pos_classe(u, "gancho", pausas[-1]) is None:
        erros.append(f"B9 · '{nome}' sem .gancho depois do .pausa final")
    return erros, avisos


def marcadores_da_semana(s):
    """Telas de nome fixo, na ordem do esqueleto, pelos marcadores que o verificador já usa."""
    ponte = ("Ponte entre encontros", lambda x: comeca_com(x, "Ponte entre encontros") or pos_classe(x, "bridge-track") is not None)
    if s == 1:
        return [("Fechamento", lambda x: comeca_com(x, "Fechamento")),
                ("Próximos passos (.flowchain)", lambda x: pos_classe(x, "flowchain") is not None)]
    if s in (2, 3, 4):
        return [ponte, (ULTIMA[s], lambda x: comeca_com(x, ULTIMA[s]))]
    return [ponte,
            ("Caminho da receita", lambda x: pos_classe(x, "caminho") is not None),
            ("Restrição principal", lambda x: comeca_com(x, "Restrição principal")),
            ("Horizontes", lambda x: pos_classe(x, "gr-matriz") is not None),
            ("Mapa de Ações", lambda x: re.search(r'class="ac[ "]', x) is not None),
            ("A conta da receita", lambda x: comeca_com(x, "A conta da receita")),
            ("Entregáveis", lambda x: pos_classe(x, "entreg-grid") is not None),
            ("Fechamento", lambda x: comeca_com(x, "Fechamento"))]


def conferir_sequencia(s, secs):
    """B4 · sequência do esqueleto da semana. Devolve (erros, avisos)."""
    erros, avisos = [], []
    if s in (3, 4):
        base = "Ponto de partida" if s == 3 else "Distância até a meta"
        capas = [i for i, sec in enumerate(secs) if pos_classe(sec, "hero") is not None]
        def nome_sem_numero(sec):
            return re.sub(r"^\d{2}\s*·\s*", "", nome_da_tela(sec))
        if not capas or capas[0]+1 >= len(secs) or not sem_acento(nome_sem_numero(secs[capas[0]+1])).startswith(sem_acento(base)):
            erros.append(f"B4 · '{base}' precisa vir logo após a capa, com leitura qualitativa quando não há meta numérica")
    # eyebrows numerados: ordem crescente, sem repetir número (a tela que continua não conta)
    nums = []
    for sec in secs:
        m = None if e_continuacao(sec) else re.match(r"(\d{2}) · ", nome_da_tela(sec))
        if m:
            nums.append(int(m.group(1)))
    repetidos = sorted({n for n in nums if nums.count(n) > 1})
    if repetidos:
        erros.append("B4 · eyebrows numerados repetem o número: " + ", ".join(f"{n:02d}" for n in repetidos))
    if any(b < a for a, b in zip(nums, nums[1:])):
        erros.append("B4 · eyebrows numerados fora da ordem crescente: " + " ".join(f"{n:02d}" for n in nums))
    # telas de nome fixo na ordem do esqueleto
    if s >= 2 and secs:
        ponte = marcadores_da_semana(s)[0][1]
        achou = [i for i, x in enumerate(secs) if ponte(x)]
        if achou and achou[0] != 0:
            erros.append("B4 · a ponte entre encontros precisa ser a primeira tela")
    ms = marcadores_da_semana(s)
    fora = fora_de_ordem(secs, ms)
    if fora:
        erros.append("B4 · telas de nome fixo fora da ordem do esqueleto: " + "; ".join(fora)
                     + " (ordem: " + " > ".join(n for n, _ in ms) + ")")
    # contra a tabela do esqueleto
    telas = ler_esqueleto(s)
    if telas is None:
        avisos.append(f"B4 · esqueleto da Semana {s} não encontrado em {RAIZ_PACOTE / 'skills' / 'estruturacao-estrategica' / 'esqueleto'}: sequência não conferida")
        return erros, avisos
    logicas = [x for x in secs if not e_continuacao(x)]
    n_opc = sum(1 for _, o in telas if o)
    if len(logicas) > len(telas):
        erros.append(f"B4 · {len(logicas)} telas lógicas (sem contar continuação) e o esqueleto da Semana {s} permite até {len(telas)}"
                     + (f", contando {n_opc} opcional(is)" if n_opc else "") + ": há tela a mais ou fundida fora do esqueleto")
    das_telas = [palavras_significativas(t) for t, _ in telas]
    fora_da_lista = []
    for sec in secs:
        nome = nome_da_tela(sec)
        m = re.match(r"\d{2} · (.*)", nome)
        if m and not e_continuacao(sec):
            pal = palavras_significativas(m.group(1))
            if pal and not any(palavra_em_comum(pal, p) for p in das_telas):
                fora_da_lista.append(nome)
    if fora_da_lista:
        avisos.append("B4 · eyebrow numerado sem palavra em comum com as telas do esqueleto (possivelmente fora da sequência): " + "; ".join(fora_da_lista))
    return erros, avisos


def _termos_evitados(celula, limpa, vazio):
    """Termos de uma célula 'evitar'. Termo com condição (parênteses, ou segmento seguinte iniciado por 'quando' ou
    'salvo') vale só em certo contexto, como 'trava (na Semana 5)' ou 'Handoff, quando não há Executar', e não entra
    na checagem automática."""
    celula = re.sub(r"\s*\([^)]*\)", "§", celula)
    segs = [x.strip() for x in re.split(r"[,;/]", celula)]
    saida = []
    for e in segs:
        if re.match(r"(?i)(quando|salvo|se)\b", e):
            if saida:
                saida.pop()
            continue
        if "§" in e or sem_acento(limpa(e)) in vazio:
            saida.append(None)
            continue
        saida.append(limpa(e))
    return [x for x in saida if x]


def ler_evitar_do_glossario():
    """Termos da coluna 'evitar' de padrao/glossario.md: lista de (termo evitado, termo escolhido). Vazia se o arquivo não existe.
    Aceita tabela com coluna 'Evitar' ou linhas '_Evitar_: a, b' / '_Avoid_: a, b' sob o termo em negrito.
    Seção '## ... (interno)' é vocabulário de trabalho e fica fora da checagem do deck."""
    arq = RAIZ_PACOTE / "padrao" / "glossario.md"
    if not arq.is_file():
        return []
    vazio = {"", "-", "n/a", "nenhum", "nenhuma", ".", TRAVESSAO, "·"}
    limpa = lambda x: re.sub(r"[*_`\"'“”]", "", x).strip()
    saida, col_ev, termo, interno = [], None, "", False
    for ln in io.open(arq, encoding="utf-8").read().splitlines():
        t = ln.strip()
        if t.startswith("|"):
            c = [x.strip() for x in t.strip("|").split("|")]
            if col_ev is None or all(re.fullmatch(r":?-{2,}:?", x) for x in c if x):
                if col_ev is None:
                    for i, h in enumerate(c):
                        if sem_acento(limpa(h)).startswith(("evitar", "avoid")):
                            col_ev = i
                continue
            if len(c) > col_ev:
                saida += [(e, limpa(c[0])) for e in _termos_evitados(c[col_ev], limpa, vazio)]
            continue
        col_ev = None
        if t.startswith("## "):
            interno = "(interno)" in t
            continue
        if interno:
            continue
        m = re.match(r"^\*\*(.+?)\*\*", t)
        if m:
            termo = limpa(m.group(1)).rstrip(":")
        m = re.search(r"(?i)(?:^|[\s_*])(?:evitar|avoid)[_*]*\s*:\s*(.+)$", t)
        if m:
            saida += [(e, termo) for e in _termos_evitados(m.group(1), limpa, vazio)]
    return saida


def termos_evitados_no_texto(txt):
    """Termos da lista 'evitar' do glossário que aparecem no texto visível. Termo de até 3 letras (IA) só casa com a
    mesma grafia, para não pegar palavra comum."""
    achados = []
    for ev, escolhido in ler_evitar_do_glossario():
        flags = 0 if len(ev) <= 3 else re.I
        if len(ev) >= 2 and re.search(r"(?<!\w)" + re.escape(ev) + r"(?!\w)", txt, flags):
            achados.append(f'"{ev}"' + (f' (usar "{escolhido}")' if escolhido else ""))
    return list(dict.fromkeys(achados))


def nomes_na_ordem(t):
    """Nomes oficiais que faltam ou estão fora de ordem no texto."""
    t, pos, ruins = t.lower(), 0, []
    for n in NOMES_OFICIAIS:
        i = t.find(n.lower(), pos)
        if i < 0:
            ruins.append(n)
        else:
            pos = i + len(n)
    return ruins


# ---------- ficha: tabela de números-fonte ----------

def sem_acento(s):
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn").lower().strip()


def ler_numeros_fonte(caminho):
    """Linhas da tabela de números-fonte da ficha: lista de dicts (chaves sem acento) ou None se não achar a tabela."""
    linhas = io.open(caminho, encoding="utf-8").read().splitlines()
    achou, saida, i = False, [], 0
    while i < len(linhas):
        ln = linhas[i].strip()
        if ln.startswith("|"):
            bloco = []
            while i < len(linhas) and linhas[i].strip().startswith("|"):
                bloco.append(linhas[i].strip()); i += 1
            cel = lambda l: [c.strip() for c in l.strip().strip("|").split("|")]
            cab = [sem_acento(c) for c in cel(bloco[0])]
            if {"valor", "situacao", "decisivo"} <= set(cab):
                achou = True
                for l in bloco[1:]:
                    c = cel(l)
                    if all(re.fullmatch(r":?-{2,}:?", x) for x in c if x):
                        continue
                    c += [""] * (len(cab) - len(c))
                    saida.append(dict(zip(cab, c)))
            continue
        i += 1
    return saida if achou else None


def norm_num(s):
    s = unescape(s).replace(" ", " ").replace("*", "").replace("`", "").lower()
    s = re.sub(r"r\$\s*", "r$", s)
    s = re.sub(r"\s+%", "%", s)
    return re.sub(r"\s+", " ", s).strip()


def variantes_numero(v, arredondado=False):
    """Formas em que o mesmo número pode estar escrito. Em R$: com e sem centavos zero (R$ 130,00 e R$ 130);
    com `arredondado`, também o valor arredondado para inteiro (R$ 123,45 aparecendo como R$ 123)."""
    if v.startswith("r$") and re.fullmatch(r"[\d.,]+", v[2:]):
        corpo = v[2:]
        base = set(variantes_numero(corpo))
        m = re.fullmatch(r"(\d{1,3}(?:\.\d{3})+|\d+),(\d+)", corpo)
        if m:
            inteiro = int(m.group(1).replace(".", ""))
            if not m.group(2).strip("0"):
                base |= variantes_numero(str(inteiro))
            elif arredondado:
                r = int(Decimal(corpo.replace(".", "").replace(",", ".")).quantize(Decimal(1), rounding=ROUND_HALF_UP))
                base |= variantes_numero(str(r))
        elif re.fullmatch(r"\d{1,3}(?:\.\d{3})*|\d+", corpo):
            base |= variantes_numero(corpo + ",00")
        return {"r$" + x for x in base} | {v}
    out = {v}
    if re.fullmatch(r"[\d.,]+", v):
        if re.fullmatch(r"\d{1,3}(?:\.\d{3})+(?:,\d+)?", v):
            out.add(v.replace(".", ""))
        if re.fullmatch(r"\d{4,}(?:,\d+)?", v):
            inteiro, _, dec = v.partition(",")
            out.add(f"{int(inteiro):,}".replace(",", ".") + ("," + dec if dec else ""))
        if "," in v and "." not in v:
            out.add(v.replace(",", "."))
    return out


def aparece(valor, unidade, texto_deck, arredondado=False):
    """True, False ou None (valor curto demais para conferir sozinho e sem unidade para ajudar)."""
    v, u, t = norm_num(valor), norm_num(unidade), norm_num(texto_deck)
    ini, fim = r"(?<![\d.,])", r"(?!\d|[.,]\d)"
    if re.fullmatch(r"\d{1,3}", v):
        if not u or u in ("-", "n/a", "nao se aplica"):
            return None
        eu = re.escape(u)
        return bool(re.search(ini + re.escape(v) + r"\s?" + eu + r"(?!\w)", t) or re.search(r"(?<!\w)" + eu + r"\s?" + re.escape(v) + fim, t))
    return any(re.search(ini + re.escape(x) + fim, t) for x in variantes_numero(v, arredondado))


def vazio_ou_modelo(v):
    v = v.strip()
    return (not v) or v.startswith("[") or v in ("-", "n/a") or v == TRAVESSAO


# ---------- contaminação por outro cliente ----------

def outros_clientes_da_pasta(html_path, cliente):
    """Nomes das pastas de EE/Clientes/<N>. <Nome>/ acima do HTML, menos o cliente desta entrega."""
    d = Path(html_path).resolve()
    for pasta in d.parents:
        if pasta.name == "Clientes" and pasta.is_dir():
            nomes = []
            for sub in pasta.iterdir():
                if sub.is_dir():
                    nomes.append(re.sub(r"^\s*\d+\.\s*", "", sub.name).strip())
            return [n for n in nomes if len(n) >= 3 and sem_acento(n) != sem_acento(cliente)]
    return []


TEMPO_VISUAL = 25  # segundos para a conferência visual (o gatilho de gravação dá 30 s ao verificador)


def conferir_visual(arquivo, erros, avisos, semana=None, sem_rede=False):
    """Só conclui com a confirmação de telas medidas, inclusive quando há erros."""
    script = Path(__file__).resolve().parent / "conferir_visual.py"
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTHONIOENCODING="utf-8")
    extra = ["--semana", str(semana)] if semana else []
    if sem_rede:
        extra.append("--sem-rede")
    try:
        p = subprocess.run([sys.executable, "-B", str(script), str(arquivo), *extra], capture_output=True, env=env,
                           timeout=TEMPO_VISUAL)
    except subprocess.TimeoutExpired:
        erros.append(f"visual · a conferência visual passou de {TEMPO_VISUAL} s e foi interrompida; rode conferir_visual.py à mão")
        return "nao_realizada"
    except Exception as e:
        erros.append(f"visual · a conferência visual não rodou ({type(e).__name__}); rode conferir_visual.py à mão")
        return "nao_realizada"
    n_erros = len(erros)
    out = p.stdout.decode("utf-8", "replace")
    for ln in out.splitlines():
        t = ln.strip()
        m = re.match(r"^(ERRO|AVISO)\s+(.*)$", t)
        if not m:
            continue
        msg = m.group(2) if m.group(2).startswith("conferência visual") else "visual · " + m.group(2)
        (erros if m.group(1) == "ERRO" else avisos).append(msg)
    if p.returncode not in (0, 1) or not re.search(r"telas:\s*[1-9]\d*\s*·\s*abertas em", out):
        erros.append("visual · conferência obrigatória não concluída; rode conferir_visual.py à mão")
        return "nao_realizada"
    if p.returncode == 1 and len(erros) == n_erros:
        erros.append("visual · conferidor reprovou sem detalhar o erro")
    return "reprovada" if len(erros) > n_erros else "aprovada"


def _main():
    ap = argparse.ArgumentParser(description="Verificador de entrega da EE.")
    ap.add_argument("arquivo")
    ap.add_argument("--semana", type=int, required=True, choices=[1, 2, 3, 4, 5])
    ap.add_argument("--cliente", default="")
    ap.add_argument("--ficha", help="ficha do cliente (<Nome>.md) com a tabela de números-fonte")
    ap.add_argument("--outros-clientes", default="", help="nomes de outros clientes, separados por vírgula")
    ap.add_argument("--visual", action="store_true", help="também roda a conferência visual (conferir_visual.py)")
    ap.add_argument("--sem-rede", action="store_true", help="conferência visual somente com recursos locais/data")
    ap.add_argument("--conteudo", help="JSON efetivamente usado para gerar S2; ausente preserva _fonte/conteudo.json")
    ap.add_argument("--resultado-json", help="grava resultado estruturado fora do pacote, preservando a saída humana")
    a = ap.parse_args()

    etapas = {"basica": {"status": "nao_realizada", "erros": [], "avisos": []},
              "pesquisa": {"status": "nao_realizada", "motivo": "não aplicável" if a.semana != 2 else "a executar"},
              "visual": {"status": "nao_realizada", "motivo": "não solicitada"}}
    if a.resultado_json:
        from manifesto_entrega import gravar_atomico
        gravar_atomico(a.resultado_json, {"versao": 1, "concluido": False, "etapas": etapas,
                                        "erros": ["verificação ainda não concluída"], "avisos": []})

    html = io.open(a.arquivo, encoding="utf-8").read()
    vis, txt, secs = visivel(html), texto(html), secoes(html)
    erros, avisos = [], []
    tem = lambda pat, alvo=vis: re.search(pat, alvo, re.S | re.I) is not None

    ficha_txt = ""
    numeros = None
    if a.ficha:
        if not Path(a.ficha).is_file():
            erros.append(f"ficha não encontrada: {a.ficha}")
        else:
            ficha_txt = io.open(a.ficha, encoding="utf-8").read()
            numeros = ler_numeros_fonte(a.ficha)
            if numeros is None:
                avisos.append("a ficha não tem a tabela de números-fonte (| id | dado | valor | ... | situação | decisivo | ...|): números não conferidos")

    # Escrita
    if TRAVESSAO in txt:
        erros.append(f"travessão no texto visível ({txt.count(TRAVESSAO)} ocorrências)")
    if re.search(MARCADORES, txt):
        erros.append("marcador de preenchimento esquecido: " + ", ".join(sorted(set(m.group(0) for m in re.finditer(MARCADORES, txt)))))
    if re.search(FALTA_PROVA, txt, re.I):
        erros.append(f"marcador [falta prova: ...] no texto visível ({len(re.findall(FALTA_PROVA, txt, re.I))}): o marcador nunca vai ao cliente; "
                     "trazer a prova ou cortar a frase")
    if re.search(CAMPO_PENDENTE, txt, re.I):
        achados = sorted(set(m.group(0).lower() for m in re.finditer(CAMPO_PENDENTE, txt, re.I)))
        erros.append("campo pendente em tela (" + ", ".join(f'"{x}"' for x in achados) + "): resolver antes de apresentar; o que não temos não evidenciamos")
    for pat, msg in PROIBIDOS.items():
        if re.search(pat, txt, re.I):
            erros.append(msg)
    if re.search(ABM, txt, re.I):
        direcao = re.search(r"^##\s+Direcionamento\s*\r?\n(.*?)(?=^##\s|\Z)", ficha_txt, re.M | re.S | re.I)
        modo = re.search(r"^\s*Modo do marketing\s*:\s*(conta|combinado)\b", direcao.group(1).replace("*", ""), re.I | re.M) if direcao else None
        if modo:
            avisos.append("ABM em Direcionamento conta/combinado: conferir público B2B, contas nomeadas, qualidade e viabilidade econômica (B10)")
        else:
            erros.append("ABM exige Modo do marketing: conta ou combinado em ## Direcionamento da ficha, com fundamento por frente (B10)")
    if re.search(CRM_FORNECEDORES, txt):
        avisos.append("possível fornecedor de CRM nomeado: " + ", ".join(sorted(set(re.findall(CRM_FORNECEDORES, txt)))))
    # B5: código interno não vai à tela (pendência P15, número N18, dado D07, prova C05 ou PC07)
    codigos = sorted(set(re.findall(r"\b(?:[PSEDR]-(?:MK|PL|K|M|C)\d+|PC\d{2}|[PN]\d{1,2}|[CD]\d{2})\b", txt)))
    if codigos:
        da_ficha = [c for c in codigos if ficha_txt and re.search(re.escape(c) + r"\s*[|·]", ficha_txt)]
        if da_ficha:
            erros.append("B5 · código interno da ficha na tela: " + ", ".join(da_ficha) + "; escreva o que ele quer dizer")
        resto = [c for c in codigos if c not in da_ficha]
        if resto:
            avisos.append("B5 · possível código interno na tela: " + ", ".join(resto) + "; o cliente não sabe o que é")

    evitados = termos_evitados_no_texto(txt)
    if evitados:
        avisos.append("glossário · termo da lista 'evitar' no texto: " + "; ".join(evitados[:12]) + (" e mais" if len(evitados) > 12 else ""))

    # Títulos de tela proibidos (B4, B5)
    for sec in secs:
        for h2 in re.findall(r"(?s)<h2\b[^>]*>(.*?)</h2>", sec):
            titulo = limpa_tags(h2)
            n = len(titulo.split())
            if n > 12:
                avisos.append(f'título com {n} palavras: "{titulo}"; avaliar concisão sem perder o achado')
        for t in titulos_da_tela(sec):
            for pat, nome in TITULO_PROIBIDO:
                if re.search(pat, t, re.I if nome != "Ato" else 0):
                    erros.append(f'tela com "{nome}" no título ou eyebrow: "{t[:60]}" (B4 e B5: sem tela inventada, sem atos, sem anexo)')

    # Contaminação por outro cliente ou pelo caso de referência
    cli = a.cliente.strip().lower()
    if not cli:
        avisos.append("sem --cliente: a checagem de contaminação por outro cliente não foi feita")
    else:
        outros = list(CASOS_REFERENCIA)
        outros += [x.strip() for x in a.outros_clientes.split(",") if x.strip()]
        outros += outros_clientes_da_pasta(a.arquivo, a.cliente)
        vistos = set()
        for nome in outros:
            if sem_acento(nome) == sem_acento(a.cliente) or sem_acento(nome) in vistos:
                continue
            vistos.add(sem_acento(nome))
            if re.search(r"\b" + re.escape(nome) + r"\b", txt, re.I):
                erros.append(f"contaminação: '{nome}' aparece na entrega de {a.cliente}")

    # Estrutura comum
    n_pausa = len(re.findall(r'class="pausa', vis))
    if not tem(r"Trieme|v4-trieme|chrome-logo"):
        avisos.append("logo da Trieme & Co não encontrada no chrome")
    if not tem(r'class="v4-mark'):
        avisos.append("monograma V4 (.v4-mark) não encontrado no hero")

    s = a.semana
    if s == 1:
        if not tem(r"O que precisa mudar"):
            erros.append("Kickoff sem o quadro 'O que precisa mudar' (critério de sucesso)")
        if not tem(r"live-fill"):
            avisos.append("Kickoff sem campos em branco (.live-fill) em público")
        if not tem(r'class="flowchain'):
            erros.append("Kickoff sem cronograma em .flowchain")
        else:
            cadeia = " ".join(textos_da_classe(html, "flowchain")).lower()
            faltam = [n for n in NOMES_OFICIAIS if n.lower() not in cadeia]
            if faltam:
                erros.append("Kickoff com .flowchain sem os 5 nomes oficiais (faltam: " + "; ".join(faltam) + ")")
        if tem(r'class="fecho'):
            erros.append("Kickoff com .fecho de 3 colunas (fechamento é recap + hipótese + validação + gancho)")
        if tem(r"lanes h3c|Plano de ação ·"):
            erros.append("Kickoff com plano de ação (não há diagnóstico no Kickoff)")
        titulos = " | ".join(re.sub(r"<[^>]+>", " ", t) for t in re.findall(r'(?s)<(?:h[1-4])[^>]*>.*?</h[1-4]>|class="eyebrow[^"]*">[^<]*<', vis))
        if re.search(r"\bSWOT\b|Pitch", titulos):
            erros.append("Kickoff com bloco de SWOT ou Pitch (B10: sem SWOT e sem Pitch no Kickoff)")
        if not tem(r'class="gancho'):
            erros.append("Kickoff sem .gancho para a Semana 2")
        fech1 = [x for x in secs if nome_da_tela(x).lower().startswith("fechamento")]
        if fech1:
            p_pausa, p_gancho = pos_classe(fech1[-1], "pausa"), pos_classe(fech1[-1], "gancho")
            if p_pausa is None:
                erros.append("Kickoff: fechamento sem .pausa de validação do recap (a ordem é recap, .pausa, .gancho)")
            elif p_gancho is not None and p_pausa > p_gancho:
                erros.append("Kickoff: fechamento com .pausa depois do .gancho")
    else:
        if not tem(r"Ponte entre encontros|bridge-track"):
            erros.append("sem ponte entre encontros na abertura")
        e_ult, a_ult = conferir_ultima_tela(s, secs, vis)
        erros += e_ult
        avisos += a_ult
        if n_pausa < 5:
            avisos.append(f"só {n_pausa} pausas de interação (esperado: uma por tópico importante)")

    if s in (2, 3, 4):
        if tem(r"Antes do próximo encontro"):
            erros.append("tarefa de casa para o cliente ('Antes do próximo encontro')")
        if s == 2 and len(re.findall(r'class="fonte-rodape', vis)) < 3:
            avisos.append("Pesquisa com poucas fontes no rodapé das telas")
        if s == 3:
            # decisão 0044: na tela, só as dimensões com achado; as 6 ficam no deck ou no detalhe (detalhe-<slug>.html)
            lift = ("Proposta de Valor", "Relevância", "Clareza", "Ansiedade", "Distração", "Urgência")
            detalhe = " ".join(texto(io.open(f, encoding="utf-8").read())
                               for f in Path(a.arquivo).resolve().parent.glob("detalhe-*.html"))
            if not all(tem(d, txt) or tem(d, detalhe) for d in lift):
                erros.append("CRO sem as 6 dimensões do LIFT Model (na tela ou no detalhe, detalhe-<slug>.html)")
        if s == 4 and not tem(r"H1.*H2.*H3", txt):
            erros.append("Diagnóstico Comercial sem Horizontes H1/H2/H3")
        if s == 4:
            doc = BeautifulSoup(vis, "html.parser")
            processo = doc.select_one(".processo-raias")
            legivel = False
            if processo:
                passos = processo.select(".processo-textual li")
                legivel = any(p.get_text(strip=True) for p in passos)
                for img in processo.select("img[src][alt]"):
                    if not img.get("alt", "").strip():
                        continue
                    src = img["src"]
                    if src.startswith("data:image/"):
                        try:
                            dados = base64.b64decode(src.split(",", 1)[1], validate=True)
                            legivel |= bool(dados)
                        except (ValueError, IndexError):
                            pass
                    elif not re.match(r"[a-z]+:|//", src, re.I):
                        arquivo = Path(a.arquivo).resolve().parent / src
                        legivel |= arquivo.is_file() and arquivo.stat().st_size > 0
            if not legivel:
                erros.append("S4 · processo atual sem imagem local descrita ou etapas textuais preenchidas em .processo-raias")

    if s == 5:
        for pat, msg in [(r'class="caminho', "caminho da receita (diagnóstico consolidado)"),
                         (r"Restrição principal", "restrição principal"),
                         (r'class="entreg-grid', "entregáveis com status")]:
            if not tem(pat):
                erros.append("Semana 5 sem " + msg)
        doc = BeautifulSoup(vis, "html.parser")
        if doc.select_one(".crt") or any(comeca_com(sec, "Árvore da restrição") for sec in secs):
            erros.append("Semana 5: árvore da restrição saiu do deck; preserve a prova pertinente no detalhe do DOCX")
        matriz = doc.select_one("table.gr-matriz")
        n_gr = len(matriz.select("tbody tr")) if matriz else 0
        if n_gr != 8:
            erros.append(f"matriz de horizontes: {n_gr} de 8 dimensões (sete mais calendário)")
        for classe in ("riscos", "premissas"):
            if not doc.select_one(f"table.{classe}"):
                erros.append(f"Semana 5 sem tabela de {classe}; ausência legítima deve ser explícita")
        receita = doc.select_one("table.receita")
        if receita is None:
            erros.append("Semana 5 sem A conta da receita (.receita), com alavancas ou lacuna explícita")
        else:
            alavancas = [tr for tr in receita.select("tr") if tr.select_one("td")]
            for i, tr in enumerate(alavancas, 1):
                selo = tr.select_one(".selo")
                if selo is None or sem_acento(selo.get_text(strip=True)) not in ("dado", "estimativa", "premissa"):
                    erros.append(f"conta da receita · alavanca {i} sem selo válido: dado, estimativa ou premissa")
            lacuna = doc.select_one(".lacuna-receita")
            if not alavancas and not (lacuna and lacuna.get_text(strip=True)):
                erros.append("conta da receita sem alavanca nem lacuna explícita com verificação")
        if not doc.select_one(".proxima-restricao"):
            erros.append("Semana 5 sem condição de revisão e próxima restrição (.proxima-restricao)")
        acs = re.findall(r'(?s)<div class="ac[ "].*?<div class="own">.*?</div></div>', vis)
        if not acs:
            erros.append("Semana 5 sem Mapa de Ações (.ac)")
        else:
            sem_tipo = sum(1 for x in acs if 'class="tipo' not in x)
            sem_orig = sum(1 for x in acs if 'class="orig' not in x)
            if sem_tipo:
                erros.append(f"{sem_tipo} ações do Mapa sem etiqueta quick win × estrutural")
            if sem_orig:
                avisos.append(f"{sem_orig} ações do Mapa sem a origem 'vem da Semana N'")
            if len(re.findall(r'class="ac prio[ "]', vis)) != 1:
                erros.append("Mapa de Ações precisa de exatamente um .ac.prio 'Comece aqui'")
    # B9 · fechamento das Semanas 2 a 5 sem quote nem resumo geral
    if s in (2, 3, 4, 5) and tem(r"Considerações finais|conc-quote"):
        erros.append("B9 · quote ou 'Considerações finais' no fechamento")

    # B4 e B5 · sequência do esqueleto, que é o teto: total de telas, ordem das numeradas e das de nome fixo
    e_seq, a_seq = conferir_sequencia(s, secs)
    erros += e_seq
    avisos += a_seq
    # B10 · os 5 nomes oficiais, na ordem, na ponte (Semanas 2 a 5)
    if s >= 2:
        ponte_txt = " ".join(textos_da_classe(html, "bridge-track"))
        if ponte_txt:
            ruins = nomes_na_ordem(ponte_txt)
            if ruins:
                erros.append("B10 · .bridge-track sem os 5 nomes oficiais na ordem (faltam ou fora de ordem: " + "; ".join(ruins) + ")")
    # B3 · faixa de amarração em toda tela numerada de conteúdo (Semanas 2 a 5)
    if s >= 2:
        numeradas = [x for x in secs if re.search(r'class="eyebrow[^"]*">\d{2} · ', x)]
        sem_amarra = [nome_da_tela(x) for x in numeradas if 'class="amarra' not in x]
        if sem_amarra:
            erros.append("B3 · telas sem a faixa de amarração (pilar · dor · para o cliente): " + "; ".join(sem_amarra))
    # B2 · rodapé de fonte nas telas numeradas
    if s >= 2:
        sem_fonte = [nome_da_tela(x) for x in secs
                     if re.search(r'class="eyebrow[^"]*">\d{2} · ', x) and 'class="fonte-rodape' not in x]
        if sem_fonte:
            avisos.append("B2 · telas numeradas sem rodapé de fonte (conferir se há dado): " + "; ".join(sem_fonte))
    # 0041 · Semana 2: prova do cliente com destino, trava ligada ao plano, um dono por ação (conferir_pesquisa.py)
    if s == 2:
        try:
            sys.path.insert(0, str(Path(__file__).resolve().parent))
            import conferir_pesquisa
            if a.conteudo:
                conteudo = json.loads(Path(a.conteudo).read_text(encoding="utf-8"))
                e_cp, a_cp = conferir_pesquisa.conferir_conteudo(Path(a.arquivo).resolve().parent, conteudo, txt)
            else:
                e_cp, a_cp = conferir_pesquisa.conferir(Path(a.arquivo).resolve().parent, txt)
            erros += e_cp
            avisos += a_cp
            etapas["pesquisa"] = {"status": "reprovada" if e_cp else "aprovada", "erros": e_cp, "avisos": a_cp}
        except Exception as ex:
            msg = f"conferência da pesquisa (conferir_pesquisa.py) não rodou: {ex}"
            erros.append(msg)
            etapas["pesquisa"] = {"status": "nao_realizada", "erros": [msg], "avisos": []}

    # B2 e B13 · números-fonte da ficha contra o deck (ficha primeiro, deck depois)
    if numeros is not None:
        vig_decisivos = [x for x in numeros if sem_acento(x.get("situacao", "")) == "vigente"]
        vigentes_valores = {norm_num(x.get("valor", "")) for x in vig_decisivos}
        sub_no_deck, curtos, faltam = [], [], []
        for x in numeros:
            valor, unid = x.get("valor", ""), x.get("unidade", "")
            ident = f'{x.get("id", "?")} ({x.get("dado", "")[:40]}: {valor})'
            if vazio_ou_modelo(valor):
                continue
            sit, dec = sem_acento(x.get("situacao", "")), sem_acento(x.get("decisivo", ""))
            if sit == "substituido":
                r = aparece(valor, unid, txt, arredondado=True)
                if r is None:
                    curtos.append(ident)
                elif r and norm_num(valor) in vigentes_valores:
                    avisos.append(f"valor substituído igual a um valor vigente da ficha: {ident}; conferir qual número a tela mostra")
                elif r:
                    sub_no_deck.append(ident)
            elif sit == "vigente" and dec == "sim":
                # Número que a coluna "usado em" atribui só a outras semanas não é cobrado deste deck
                semanas_uso = {int(n) for n in re.findall(r"\b(?:s|semana)\s*([1-5])\b", sem_acento(x.get("usado em", "")))}
                if semanas_uso and s not in semanas_uso:
                    continue
                r = aparece(valor, unid, txt)
                if r is None:
                    curtos.append(ident)
                elif not r:
                    faltam.append(ident)
        if sub_no_deck:
            erros.append("número substituído na ficha ainda aparece no deck: " + "; ".join(sub_no_deck))
        # Semanas 3 a 5 citam só os números que usam; a falta dos números de outras semanas no deck não é sinal (decisão 0044)
        if faltam and s not in (3, 4, 5):
            avisos.append("número decisivo vigente da ficha não aparece no deck: " + "; ".join(faltam))
        if curtos:
            avisos.append("valor curto demais para conferir sozinho (conferir à mão): " + "; ".join(curtos))
    elif s >= 2 and not a.ficha:
        avisos.append("sem --ficha: os números do deck não foram conferidos contra a tabela de números-fonte")

    etapas["basica"] = {"status": ("nao_realizada" if s == 2 and etapas["pesquisa"]["status"] == "nao_realizada"
                                  else "reprovada" if erros else "aprovada"), "erros": list(erros), "avisos": list(avisos)}
    if a.visual:
        ne, na = len(erros), len(avisos)
        status_visual = conferir_visual(a.arquivo, erros, avisos, s, a.sem_rede)
        etapas["visual"] = {"status": status_visual, "erros": erros[ne:], "avisos": avisos[na:], "sem_rede": a.sem_rede}

    if a.resultado_json:
        gravar_atomico(a.resultado_json, {"versao": 1, "concluido": True, "etapas": etapas,
                                        "erros": erros, "avisos": avisos,
                                        "conclusao_tecnica": "reprovada" if erros else "aprovada"})

    print(f"Verificação · Semana {s} · {a.arquivo}")
    print(f"  telas: {len(secs)} · pausas: {n_pausa}")
    for e in erros:
        print("  ERRO  ", e)
    for v in avisos:
        print("  AVISO ", v)
    if not erros and not avisos:
        print("  OK, nenhum problema encontrado.")
    elif not erros:
        print("  Sem erros. Revisar os avisos.")
    sys.exit(1 if erros else 0)


def main():
    try:
        _main()
    except (Exception, KeyboardInterrupt) as e:
        msg = f"verificação não concluída: {type(e).__name__}: {e}"
        print("  ERRO  " + msg)
        if "--resultado-json" in sys.argv:
            try:
                from manifesto_entrega import gravar_atomico
                alvo = sys.argv[sys.argv.index("--resultado-json") + 1]
                gravar_atomico(alvo, {"versao": 1, "concluido": False,
                                     "etapas": {"basica": {"status": "nao_realizada", "erros": [msg], "avisos": []}},
                                     "erros": [msg], "avisos": []})
            except Exception:
                pass
        sys.exit(1)


if __name__ == "__main__":
    main()
