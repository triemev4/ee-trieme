"""Faz as contas do deck em Python e grava o resultado na ficha do cliente. Nenhum número do deck sai de cabeça.

Uso:
    python calcular.py <contas.json> [--ficha <ficha.md>] [--saida <resultado.json>]
    python calcular.py --funil <csv> | --midia <csv> [<csv>...] | --motivos <csv> | --tabela <_texto/arquivo.txt> --pagina N
                       [--ficha <ficha.md>] [--rotulo ...] [--periodo ...] [--dono ...] [--usado-em ...] [--decisivo sim]

O QUE O AGENTE OU O GUIA ESCREVE (contas.json):
  {"contas": [
    {"id": "N12", "dado": "TAM em R$", "formula": "populacao * preco", "unidade": "R$", "periodo": "2026",
     "dono": "Trieme", "decisivo": "sim", "usado_em": "S2 · TAM",
     "formato": "moeda", "casas": 0, "escala": "milhoes",
     "entradas": {
       "populacao": {"valor": "116.725", "unidade": "habitantes", "origem": "N03"},
       "preco":     {"valor": "R$ 54,50", "unidade": "R$", "origem": "dados-pesquisa.json#D07"}}}]}
  - `id` é opcional. Sem id, a conta é reconhecida pelo texto de `dado`; conta nova ganha o próximo Nxx.
  - `formula`: só + - * / ( ), números com PONTO decimal, os nomes das entradas e as funções min, max, round, soma.
    Qualquer outra coisa (potência, atributo, chamada, vírgula decimal) é recusada.
  - `valor` da entrada: número, ou texto no padrão brasileiro ("1.234,56", "R$ 54,50", "12,5%", "7,6 milhões").
    Percentual entra como número em pontos percentuais (12,5% vale 12.5): a fórmula divide por 100 quando precisar.
  - `origem` (obrigatória, uma destas):
      id da ficha (N03): o script confere o valor com a linha vigente da ficha;
      linha do pesquisador (dados-pesquisa.json#D07): confere valor e recusa dado pendente (valor null). Número de
        fonte web só entra com o trecho achado na página da coleta (status "conferido na coleta", gravado por
        coletar_fontes.py --procurar em <pasta do dados>/coleta/indice.json, ou --coleta); sem o trecho fica pendente;
      arquivo e página de _texto (arquivo.txt · página 3): confere que o valor está no trecho (com --texto <pasta _texto>);
      premissa (premissa: consultoria (proposta), 07/10/2026): autor, estado proposto/confirmado e data.
  - `formato`: moeda (R$ 1.234,56), percentual (12,5%), inteiro (1.234) ou numero (1.234,5). Sem formato, vale a unidade.
    `casas` muda as casas; `escala` ("mil", "milhoes", "bilhoes") divide o valor e põe a palavra depois.
  - prova fraca: trecho lido por OCR é prova fraca. Conta com prova fraca não pode ser decisiva até o consultor
    conferir (campo `conferido` na entrada). Dado web sem trecho achado na coleta (inclusive o que veio só pelo
    WebFetch) não é prova fraca, é pendente: só entra depois que o consultor escrever `conferido` na linha.

O QUE O SCRIPT FAZ: avalia com `ast` (sem eval), formata no padrão brasileiro e grava ou atualiza a linha na seção
"Números-fonte" da ficha (id, dado, valor, unidade, período, dono do número, fonte e data, situação, decisivo, usado em),
com a fórmula e a origem na coluna de fonte. Valor que muda vira linha nova (próximo id) e a anterior fica "substituído".
Escreve também o resultado em JSON (padrão: ao lado do contas.json, `<nome>.resultado.json`) para o deck.

RECEITAS (uma por chamada; leem CSV, TSV ou XLSX; sem --ficha só calculam):
  --funil <csv>    contagem por etapa e conversão entre etapas (tabela etapa+quantidade, ou um registro por oportunidade
                   com coluna de etapa; --ordem "A,B,C" fixa a ordem; --acumulado conta quem passou da etapa)
  --midia <csv>... gasto, resultados, custo por resultado e divisão por canal (colunas do Meta e do Google, em português
                   e em inglês; --canal "Meta" "Google" na mesma ordem dos arquivos; --por-campanha grava também por campanha)
  --motivos <csv>  contagem e % por motivo de perda
  --tabela <arquivo de _texto> --pagina N   soma e % de uma tabela já extraída (--coluna nome ou número)
Requer só a biblioteca padrão (openpyxl para XLSX).
"""
import sys
sys.dont_write_bytecode = True
import argparse, ast, csv, io, json, os, re, unicodedata
from datetime import datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP, localcontext
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

sys.path.insert(0, str(Path(__file__).resolve().parent))

HOJE = datetime.now().strftime("%d/%m/%Y")
COLUNAS_FICHA = ["id", "dado", "valor", "unidade", "periodo", "dono do numero", "fonte e data", "situacao", "decisivo", "usado em"]
FUNCOES = {"min", "max", "round", "soma"}
ESCALAS = {"mil": (Decimal(1000), "mil"), "milhoes": (Decimal(1000000), "milhões"), "bilhoes": (Decimal(10) ** 9, "bilhões")}


class ErroConta(Exception):
    pass


def sem_acento(s):
    return "".join(c for c in unicodedata.normalize("NFD", str(s)) if unicodedata.category(c) != "Mn").lower().strip()


# ---------------------------------------------------------------- números

MULT = {"mil": Decimal(1000), "milhao": Decimal(10) ** 6, "milhoes": Decimal(10) ** 6, "mi": Decimal(10) ** 6, "mm": Decimal(10) ** 6,
        "bilhao": Decimal(10) ** 9, "bilhoes": Decimal(10) ** 9, "bi": Decimal(10) ** 9}


def parse_valor(v, modo="br"):
    """Número ou texto ("R$ 1.234,56", "12,5%", "7,6 milhões") -> (Decimal, unidade detectada ou None).
    modo "br": vírgula decimal; "us": ponto decimal (coluna de CSV exportado em inglês)."""
    if isinstance(v, bool):
        raise ValueError(f"valor inválido: {v!r}")
    if isinstance(v, (int, float, Decimal)):
        return Decimal(str(v)), None
    s = str(v).strip()
    if not s:
        raise ValueError("valor vazio")
    unid = None
    neg = s.startswith("(") and s.endswith(")")
    s = s.strip("()").strip()
    if re.search(r"r\$", s, re.I):
        unid = "R$"
        s = re.sub(r"r\$", "", s, flags=re.I)
    if "%" in s:
        unid = "%"
        s = s.replace("%", "")
    s = s.replace(" ", " ").strip()
    mult = Decimal(1)
    m = re.fullmatch(r"(.*?)\s*([A-Za-zçãõé]+)", s)
    if m and sem_acento(m.group(2)) in MULT:
        mult, s = MULT[sem_acento(m.group(2))], m.group(1).strip()
    s = s.replace(" ", "")
    if s.startswith("-"):
        neg, s = True, s[1:]
    elif s.startswith("+"):
        s = s[1:]
    if not re.fullmatch(r"[\d.,]+", s) or not re.search(r"\d", s):
        raise ValueError(f"não é número: {v!r}")
    if "," in s and "." in s:
        dec = "," if s.rfind(",") > s.rfind(".") else "."
    elif "," in s:
        dec = ","
    elif "." in s:
        if modo == "us":
            dec = "."
        elif re.fullmatch(r"\d{1,3}(\.\d{3})+", s):
            dec = None                       # 1.234 e 1.234.567 são milhar no padrão brasileiro
        else:
            dec = "."                        # 0.5 ou 12.34
    else:
        dec = None
    if dec is None:
        limpo = s.replace(".", "").replace(",", "")
    else:
        mil = "." if dec == "," else ","
        limpo = s.replace(mil, "").replace(dec, ".")
    try:
        n = Decimal(limpo)
    except InvalidOperation:
        raise ValueError(f"não é número: {v!r}")
    n = n * mult
    return (-n if neg else n), unid


def modo_da_coluna(valores):
    """"us" se a coluna do CSV usa ponto decimal (1234.56), "br" no resto (padrão)."""
    us = br = 0
    for v in valores:
        s = str(v).strip().replace("R$", "").strip()
        if re.fullmatch(r"-?\d{1,3}(,\d{3})+\.\d+", s) or re.fullmatch(r"-?\d+\.\d{1,2}", s) or re.fullmatch(r"-?\d+\.\d{4,}", s):
            us += 1
        elif re.fullmatch(r"-?\d{1,3}(\.\d{3})+,\d+", s) or re.fullmatch(r"-?\d+,\d+", s):
            br += 1
    return "us" if us > br else "br"


def casas_de(d):
    return max(0, -d.as_tuple().exponent)


def quantiza(d, casas):
    return d.quantize(Decimal(1).scaleb(-casas), rounding=ROUND_HALF_UP)


def milhar_br(d, casas):
    q = quantiza(d, casas)
    texto = f"{abs(q):,.{casas}f}".replace(",", "\0").replace(".", ",").replace("\0", ".")
    return ("-" if q < 0 else "") + texto


def formatar(d, formato=None, casas=None, unidade="", escala=None):
    """Valor no padrão brasileiro: R$ 1.234,56 · 12,5% · 1.234 · 1.234,5."""
    if not formato:
        u = (unidade or "").strip()
        formato = "moeda" if u == "R$" else "percentual" if u == "%" else None
    sufixo = ""
    if escala:
        div, palavra = ESCALAS[escala]
        d, sufixo = d / div, " " + palavra
    if formato == "moeda":
        c = 2 if casas is None else casas
        txt = milhar_br(d, c)
        return ("-R$ " + txt[1:] if txt.startswith("-") else "R$ " + txt) + sufixo
    if formato == "percentual":
        return milhar_br(d, 1 if casas is None else casas) + "%"
    if formato == "inteiro":
        return milhar_br(d, 0 if casas is None else casas) + sufixo
    c = casas if casas is not None else (0 if quantiza(d, 2) == quantiza(d, 0) else 2)
    return milhar_br(d, c) + sufixo


def formato_da_unidade(unidade):
    u = (unidade or "").strip()
    return "moeda" if u == "R$" else "percentual" if u == "%" else None


# ---------------------------------------------------------------- avaliador seguro

def avaliar(formula, valores, unidades=None):
    """Avalia só + - * / ( ), números, nomes de `valores` e min, max, round, soma. Decimal do começo ao fim."""
    return avaliar_u(formula, valores, unidades)[0]


def _un(u):
    return sem_acento(u) if u else None


def avaliar_u(formula, valores, unidades=None):
    """Como `avaliar`, mas devolve (valor, unidade). `unidades` {nome: unidade} liga a conferência: soma, subtração,
    min, max e soma() recusam unidades diferentes. Multiplicar por número puro mantém a unidade; conta entre duas
    grandezas com unidade vira unidade desconhecida (None)."""
    if not isinstance(formula, str) or not formula.strip():
        raise ErroConta("fórmula vazia")
    if len(formula) > 500:
        raise ErroConta("fórmula longa demais (500 caracteres)")
    try:
        arvore = ast.parse(formula.strip(), mode="eval")
    except SyntaxError:
        dica = " (use ponto decimal na fórmula: 0.05, não 0,05)" if re.search(r"\d,\d", formula) else ""
        raise ErroConta(f"fórmula inválida{dica}: {formula}")
    unidades = unidades or {}
    nomes_un = {k: (str(v).strip() or None) for k, v in unidades.items()}

    def junta(us, op):
        vistas = {}
        for u in us:
            if u:
                vistas.setdefault(_un(u), u)
        if len(vistas) > 1:
            raise ErroConta(f"{op} de unidades diferentes ({' e '.join(vistas.values())}): converta antes ou use outra fórmula")
        return next(iter(vistas.values()), None)

    def no(n):
        if isinstance(n, ast.Expression):
            return no(n.body)
        if isinstance(n, ast.Constant):
            if isinstance(n.value, bool) or not isinstance(n.value, (int, float)):
                raise ErroConta(f"só número na fórmula, achei {n.value!r}")
            return Decimal(repr(n.value)), None
        if isinstance(n, ast.Name):
            if n.id in valores:
                return valores[n.id], nomes_un.get(n.id)
            if n.id in FUNCOES:
                raise ErroConta(f"'{n.id}' é função: use {n.id}(...)")
            raise ErroConta(f"nome sem entrada: {n.id}")
        if isinstance(n, ast.Tuple):
            raise ErroConta("vírgula na fórmula: use ponto como decimal (0.5, não 0,5); vírgula só separa argumentos de função")
        if isinstance(n, ast.UnaryOp) and isinstance(n.op, (ast.USub, ast.UAdd)):
            v, u = no(n.operand)
            return (-v if isinstance(n.op, ast.USub) else v), u
        if isinstance(n, ast.BinOp) and isinstance(n.op, (ast.Add, ast.Sub, ast.Mult, ast.Div)):
            (a, ua), (b, ub) = no(n.left), no(n.right)
            try:
                if isinstance(n.op, (ast.Add, ast.Sub)):
                    u = junta([ua, ub], "soma" if isinstance(n.op, ast.Add) else "subtração")
                    return (a + b if isinstance(n.op, ast.Add) else a - b), u
                if isinstance(n.op, ast.Mult):
                    return a * b, (ua if ub is None else ub if ua is None else None)
                return a / b, (ua if ub is None else None)
            except (ZeroDivisionError, InvalidOperation):
                raise ErroConta("divisão por zero")
        if isinstance(n, ast.Call):
            if not isinstance(n.func, ast.Name) or n.func.id not in FUNCOES or n.keywords:
                raise ErroConta("função não permitida (só min, max, round, soma)")
            if any(isinstance(x, ast.Starred) for x in n.args):
                raise ErroConta("argumento com * não é permitido")
            pares = [no(x) for x in n.args]
            args = [p[0] for p in pares]
            f = n.func.id
            if f == "round":
                if len(args) not in (1, 2):
                    raise ErroConta("round(valor) ou round(valor, casas)")
                casas = 0
                if len(args) == 2:
                    if args[1] != args[1].to_integral_value() or not (0 <= args[1] <= 12):
                        raise ErroConta("round: casas deve ser inteiro de 0 a 12")
                    casas = int(args[1])
                return quantiza(args[0], casas), pares[0][1]
            if not args:
                raise ErroConta(f"{f}() sem argumentos")
            u = junta([p[1] for p in pares], "soma" if f == "soma" else f)
            return (sum(args, Decimal(0)) if f == "soma" else (min(args) if f == "min" else max(args))), u
        raise ErroConta(f"construção não permitida na fórmula ({type(n).__name__}); só + - * / ( ), números, nomes e min, max, round, soma")

    with localcontext() as ctx:
        ctx.prec = 40
        return no(arvore)


# ---------------------------------------------------------------- ficha

class Ficha:
    """Tabela "Números-fonte" da ficha, lida e regravada linha a linha, sem tocar no resto do arquivo."""

    def __init__(self, caminho):
        self.caminho = Path(caminho)
        bruto = self.caminho.read_bytes().decode("utf-8")
        self.nl = "\r\n" if "\r\n" in bruto else "\n"
        self.linhas = bruto.split(self.nl)
        self.achar_tabela()

    @staticmethod
    def celulas(linha):
        return [c.strip() for c in linha.strip().strip("|").split("|")]

    def achar_tabela(self):
        ini = None
        for i, ln in enumerate(self.linhas):
            if re.match(r"^##\s+", ln) and sem_acento(ln).replace("#", "").strip().startswith("numeros-fonte"):
                ini = i
                break
        if ini is None:
            raise ErroConta('a ficha não tem a seção "Números-fonte"')
        fim = len(self.linhas)
        for j in range(ini + 1, len(self.linhas)):
            if re.match(r"^##\s+", self.linhas[j]):
                fim = j
                break
        k = ini + 1
        while k < fim:
            if self.linhas[k].strip().startswith("|"):
                cab = [sem_acento(c) for c in self.celulas(self.linhas[k])]
                if {"valor", "situacao", "decisivo"} <= set(cab):
                    self.cab = cab
                    self.i_cab = k
                    f = k + 1
                    while f < len(self.linhas) and self.linhas[f].strip().startswith("|"):
                        f += 1
                    self.i_fim = f           # primeira linha depois da tabela
                    for obrig in ("id", "dado", "valor", "situacao", "decisivo"):
                        if obrig not in self.cab:
                            raise ErroConta(f'a tabela de Números-fonte não tem a coluna "{obrig}"')
                    return
                while k < fim and self.linhas[k].strip().startswith("|"):
                    k += 1
                continue
            k += 1
        raise ErroConta('a seção "Números-fonte" não tem a tabela (| id | dado | valor | ... | situação | decisivo | ...|)')

    def linhas_dados(self):
        """[(índice no arquivo, dict)] das linhas de dados."""
        out = []
        for i in range(self.i_cab + 1, self.i_fim):
            c = self.celulas(self.linhas[i])
            if all(re.fullmatch(r":?-{2,}:?", x) for x in c if x):
                continue
            c += [""] * (len(self.cab) - len(c))
            out.append((i, dict(zip(self.cab, c))))
        return out

    def vazia(self, d):
        return not d.get("dado") and not d.get("valor")

    def escreve(self, i, d):
        self.linhas[i] = "| " + " | ".join(d.get(c, "").replace("|", "¦") for c in self.cab) + " |"

    def novo_id(self):
        usados = [d["id"] for _, d in self.linhas_dados()]
        n = max([int(m.group(1)) for x in usados for m in [re.fullmatch(r"[Nn](\d+)", x)] if m] + [0])
        return f"N{n + 1:02d}"

    def vigente_por_id(self, ident):
        for _, d in self.linhas_dados():
            if d["id"].lower() == str(ident).lower() and sem_acento(d["situacao"]) == "vigente":
                return d
        return None

    def gravar(self, c, valor_txt, fonte_txt):
        """Grava a conta `c`. Devolve (id final, ação)."""
        linhas = self.linhas_dados()
        alvo = None
        if c.get("id"):
            for i, d in linhas:
                if d["id"].lower() == c["id"].lower() and sem_acento(d["situacao"]) == "vigente":
                    alvo = (i, d)
                    break
        if alvo is None and not c.get("id"):
            chave = sem_acento(c["dado"])
            for i, d in linhas:
                if sem_acento(d["dado"]) == chave and sem_acento(d["situacao"]) == "vigente":
                    alvo = (i, d)
                    break
        nova = {k: "" for k in self.cab}
        nova.update({"dado": c["dado"], "valor": valor_txt, "unidade": c.get("unidade", ""), "periodo": c.get("periodo", ""),
                     "dono do numero": c.get("dono", "Trieme"), "fonte e data": fonte_txt, "situacao": "vigente",
                     "decisivo": c.get("decisivo", "não"), "usado em": c.get("usado_em", "")})
        if alvo:
            i, velha = alvo
            if self.vazia(velha):                                   # linha-modelo (N01 em branco): preenche
                nova["id"] = velha["id"]
                self.escreve(i, nova)
                return nova["id"], "nova"
            if self.mesmo_valor(velha["valor"], valor_txt):
                nova["id"] = velha["id"]
                igual = all(velha.get(k, "") == nova.get(k, "") for k in self.cab)
                self.escreve(i, nova)
                return nova["id"], "sem mudança" if igual else "atualizada"
            novo_id = self.novo_id()
            nova["id"] = novo_id
            nova["fonte e data"] = f"{fonte_txt} · substitui {velha['id']}"
            velha = dict(velha, situacao="substituído")
            velha["fonte e data"] = (velha.get("fonte e data", "") + f" · substituído por {novo_id} em {HOJE}").strip(" ·")
            self.escreve(i, velha)
            self.inserir(nova)
            return novo_id, f"substituiu {velha['id']}"
        usados = {d["id"].lower() for _, d in linhas}
        for i, d in linhas:                                         # linha-modelo em branco: preenche, não acrescenta
            if self.vazia(d) and sem_acento(d["situacao"]) in ("vigente", ""):
                outros = usados - {d["id"].lower()}
                nova["id"] = c["id"] if c.get("id") and c["id"].lower() not in outros else d["id"]
                self.escreve(i, nova)
                return nova["id"], "nova"
        nova["id"] = c["id"] if c.get("id") and c["id"].lower() not in usados else self.novo_id()
        self.inserir(nova)
        return nova["id"], "nova"

    def inserir(self, d):
        ln = "| " + " | ".join(d.get(c, "").replace("|", "¦") for c in self.cab) + " |"
        self.linhas.insert(self.i_fim, ln)
        self.i_fim += 1

    @staticmethod
    def mesmo_valor(a, b):
        if a.strip() == b.strip():
            return True
        try:
            return parse_valor(a) == parse_valor(b)
        except ValueError:
            return False

    def salvar(self):
        tmp = self.caminho.with_name(self.caminho.name + ".tmp")
        tmp.write_bytes(self.nl.join(self.linhas).encode("utf-8"))
        os.replace(tmp, self.caminho)


# ---------------------------------------------------------------- origens

ORIGEM_FICHA = re.compile(r"^[Nn]\d+$")
ORIGEM_DADOS = re.compile(r"^(?P<arq>[^#\s]+\.json)#(?P<id>[\w.-]+)$")
ORIGEM_TEXTO = re.compile(r"^(?P<arq>.+?\.txt)\s*(?:[·,;]|\s)\s*(?:p\.?|pág\.?|página)\s*(?P<pg>\d+)\s*$", re.I)
ORIGEM_PREMISSA = re.compile(r"^premissa\s*:\s*(?P<quem>[^,]+),\s*(?P<data>\d{2}/\d{2}/\d{4})\s*$", re.I)


def pagina_do_texto(caminho, pagina):
    """Trecho `[... · página N ...]` de um arquivo de _texto: (texto, tem OCR) ou (None, False)."""
    linhas = Path(caminho).read_text(encoding="utf-8").splitlines()
    ini = None
    for i, ln in enumerate(linhas):
        if re.fullmatch(rf"\[[^\]]*página {pagina}(\s*·[^\]]*)?\]", ln.strip()):
            ini = i
            break
    if ini is None:
        return None, False
    fim = len(linhas)
    for j in range(ini + 1, len(linhas)):
        if re.fullmatch(r"\[[^\]]*·[^\]]*\]", linhas[j].strip()):
            fim = j
            break
    return "\n".join(linhas[ini + 1:fim]), bool(re.search(r"·\s*OCR\s*\]", linhas[ini]))


def resolucao(texto):
    """Menor passo do número como está escrito ("7,6 milhões" -> 100000; "R$ 54,57" -> 0,01; "116.725" -> 1)."""
    m = re.search(r"\d[\d.,]*", str(texto))
    if not m:
        return Decimal(0)
    tok = m.group(0)
    if "," in tok:
        casas = len(tok.rsplit(",", 1)[1])
    elif re.fullmatch(r"\d+\.\d{1,2}", tok) or re.fullmatch(r"\d+\.\d{4,}", tok):
        casas = len(tok.rsplit(".", 1)[1])
    else:
        casas = 0
    mult = Decimal(1)
    resto = sem_acento(str(texto)[m.end():]).strip()
    for palavra, f in MULT.items():
        if re.match(rf"{palavra}\b", resto):
            mult = f
            break
    return Decimal(1).scaleb(-casas) * mult


def confere_com(valor, texto):
    """O valor da entrada bate com o número escrito em `texto` (ficha ou pesquisador), dentro do arredondamento mostrado."""
    v, _ = parse_valor(texto)
    return abs(valor - v) <= resolucao(texto) / 2


def fonte_web_da(linha):
    """A linha do pesquisador vem da web? (tem link http, ou a via é coletor, webfetch ou websearch)."""
    return bool(re.match(r"https?://", str(linha.get("link", "")).strip(), re.I)) or         str(linha.get("via", "")).strip().lower() in ("coletor", "webfetch", "websearch")


class Origens:
    def __init__(self, ficha, dados_json, texto_dir, base, coleta=None):
        self.ficha, self.texto_dir, self.base = ficha, texto_dir, base
        self.dados_json = dados_json
        self.coleta = coleta
        self._dados = {}
        self._pasta_dados = None

    def dados(self, arq):
        cand = []
        if self.dados_json:
            cand.append(Path(self.dados_json))
        cand += [self.base / arq, self.base / "_fonte" / arq, Path(arq)]
        for c in cand:
            if c.is_file():
                if c not in self._dados:
                    self._dados[c] = {d.get("id"): d for d in json.loads(c.read_text(encoding="utf-8")).get("dados", [])}
                self._pasta_dados = c.resolve().parent
                return self._dados[c]
        raise ErroConta(f"arquivo {arq} não encontrado (use --dados)")

    fonte_web = staticmethod(fonte_web_da)

    def pasta_coleta(self):
        if self.coleta:                              # --coleta manda: não procura em outro lugar
            return Path(self.coleta)
        cand = []
        for pai in (self._pasta_dados, self.base):
            if pai:
                cand += [Path(pai) / "coleta", Path(pai) / "_fonte" / "coleta"]
        return next((c for c in cand if (c / "indice.json").is_file()), cand[0] if cand else None)

    def trecho_na_coleta(self, nome, ident, linha):
        """Número de fonte web: só entra com o trecho achado na página, na coleta. Devolve onde; senão, pendente."""
        link = str(linha.get("link", "")).strip()
        if not link:
            raise ErroConta(f"entrada '{nome}': {ident} é de fonte web e a linha não tem link; sem o trecho achado na página da coleta o dado fica pendente")
        pasta = self.pasta_coleta()
        if pasta is None:
            raise ErroConta(f"entrada '{nome}': {ident} é de fonte web e não há pasta de coleta; sem o trecho achado na página o dado fica pendente (coletar_fontes.py --procurar)")
        from coletar_fontes import conferir_na_coleta
        ok, info = conferir_na_coleta(link, linha.get("valor"), ident, pasta)
        if not ok:
            raise ErroConta(f"entrada '{nome}': {ident} é de fonte web e o trecho não foi achado na página: {info}. "
                            "Fica pendente: rode coletar_fontes.py com --procurar, ou o consultor confere a página e escreve `conferido` na linha")
        return info

    def conferir(self, nome, ent, valor):
        """Confere a entrada com a origem. Devolve (descrição curta, fraca [lista de motivos])."""
        origem = str(ent.get("origem", "")).strip()
        if not origem:
            raise ErroConta(f"entrada '{nome}' sem origem")
        if ent.get("_interna"):                  # número que a própria receita leu da tabela
            return origem, []
        conferido = bool(ent.get("conferido"))
        m = ORIGEM_DADOS.match(origem)
        if ORIGEM_FICHA.match(origem):
            if self.ficha is None:
                return origem, []
            lin = self.ficha.vigente_por_id(origem)
            if lin is None:
                raise ErroConta(f"entrada '{nome}': {origem} não está vigente na ficha")
            try:
                v, _ = parse_valor(lin["valor"])
            except ValueError:
                raise ErroConta(f"entrada '{nome}': o valor de {origem} na ficha ({lin['valor']!r}) não é número")
            if not confere_com(valor, lin["valor"]):
                raise ErroConta(f"entrada '{nome}': valor {valor} diferente do de {origem} na ficha ({lin['valor']})")
            return origem, ([] if conferido or "prova fraca" not in lin.get("fonte e data", "").lower() else [f"{origem} (prova fraca)"])
        if m:
            linha = self.dados(m["arq"]).get(m["id"])
            if linha is None:
                raise ErroConta(f"entrada '{nome}': {m['id']} não existe em {m['arq']}")
            if linha.get("pendente") or linha.get("valor") in (None, ""):
                raise ErroConta(f"entrada '{nome}': {m['id']} está pendente (sem valor); não dá para calcular com ele")
            try:
                v, _ = parse_valor(linha["valor"])
            except ValueError:
                raise ErroConta(f"entrada '{nome}': o valor de {m['id']} ({linha['valor']!r}) não é número")
            if not confere_com(valor, str(linha["valor"])):
                raise ErroConta(f"entrada '{nome}': valor {valor} diferente do de {m['id']} em {m['arq']} ({linha['valor']})")
            fraca = linha.get("prova") == "fraca" and not (linha.get("conferido") or conferido)
            if linha.get("conferido"):
                origem += f", conferido: {linha['conferido']}"
            elif not conferido and self.fonte_web(linha):
                origem += f", conferido na coleta: {self.trecho_na_coleta(nome, m['id'], linha)}"
                fraca = False
            return origem, ([f"{m['id']} (prova fraca)"] if fraca else [])
        m = ORIGEM_TEXTO.match(origem)
        if m:
            if not self.texto_dir:
                return origem, []              # sem a pasta, não dá para conferir
            arq = Path(self.texto_dir) / Path(m["arq"]).name
            if not arq.is_file():
                raise ErroConta(f"entrada '{nome}': {arq.name} não está em {self.texto_dir}")
            trecho, ocr = pagina_do_texto(arq, int(m["pg"]))
            if trecho is None:
                raise ErroConta(f"entrada '{nome}': {arq.name} não tem a página {m['pg']}")
            bruto = str(ent["valor"]).strip()
            if bruto not in trecho and not any(x in trecho for x in variantes_texto(valor)):
                raise ErroConta(f"entrada '{nome}': o valor {bruto!r} não aparece em {arq.name}, página {m['pg']}")
            return origem, ([f"{arq.name} p.{m['pg']} (OCR)"] if ocr and not conferido else [])
        if ORIGEM_PREMISSA.match(origem):
            return origem, []
        raise ErroConta(f"entrada '{nome}': origem não reconhecida ({origem!r}). Use o id da ficha (N03), "
                        "dados-pesquisa.json#D07, arquivo.txt · página 3 ou premissa: consultor, dd/mm/aaaa")


def variantes_texto(d):
    """Formas em que o mesmo número pode estar escrito num trecho de _texto."""
    out = set()
    for c in (0, 1, 2):
        out.add(milhar_br(d, c))
        out.add(milhar_br(d, c).replace(".", ""))
    if d == d.to_integral_value():
        out.add(str(int(d)))
    return out


# ---------------------------------------------------------------- contas

def fmt_entrada(v, unidade):
    f = formato_da_unidade(unidade)
    casas = min(casas_de(v.normalize()), 4)
    if f:
        return formatar(v, f, 2 if f == "moeda" and casas <= 2 else casas, unidade)
    return f"{milhar_br(v, casas)} {unidade}".strip()


def calcular_conta(c, origens):
    """Faz a conta. Devolve dict com valor, texto da fonte e avisos."""
    for obrig in ("dado", "formula", "unidade", "entradas"):
        if not c.get(obrig):
            raise ErroConta(f"conta sem '{obrig}'" + (" (nenhum número entra de cabeça: cada um vem de uma entrada com origem)" if obrig == "entradas" else ""))
    if not isinstance(c["entradas"], dict):
        raise ErroConta("entradas deve ser um objeto {nome: {valor, unidade, origem}}")
    dec = str(c.get("decisivo", "não")).strip().lower()
    if dec not in ("sim", "não", "nao"):
        raise ErroConta("decisivo é 'sim' ou 'não'")
    c["decisivo"] = "sim" if dec == "sim" else "não"
    if c.get("escala") and c["escala"] not in ESCALAS:
        raise ErroConta(f"escala deve ser uma de {', '.join(ESCALAS)}")
    if c.get("formato") and c["formato"] not in ("moeda", "percentual", "inteiro", "numero"):
        raise ErroConta("formato: moeda, percentual, inteiro ou numero")
    if c.get("casas") is not None and not (isinstance(c["casas"], int) and 0 <= c["casas"] <= 8):
        raise ErroConta("casas é inteiro de 0 a 8")
    valores, partes, fracas = {}, [], []
    for nome, ent in c["entradas"].items():
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", nome) or nome in FUNCOES:
            raise ErroConta(f"nome de entrada inválido: {nome!r}")
        if not isinstance(ent, dict) or "valor" not in ent or not str(ent.get("unidade", "")).strip():
            raise ErroConta(f"entrada '{nome}' precisa de valor, unidade e origem")
        try:
            v, detectada = parse_valor(ent["valor"])
        except ValueError as e:
            raise ErroConta(f"entrada '{nome}': {e}")
        if detectada and _un(detectada) != _un(ent["unidade"]):
            raise ErroConta(f"entrada '{nome}': o valor {ent['valor']!r} está em {detectada}, mas a unidade declarada é {str(ent['unidade']).strip()!r}; corrija um dos dois")
        valores[nome] = v
        desc, fraca = origens.conferir(nome, ent, v)
        fracas += fraca
        if ent.get("conferido"):
            desc += f"; conferido: {ent['conferido']}" if isinstance(ent["conferido"], str) else "; conferido pelo consultor"
        partes.append(f"{nome} = {fmt_entrada(v, ent['unidade'])} ({desc})")
    unidades = {n: e["unidade"] for n, e in c["entradas"].items()}
    resultado, un_res = avaliar_u(c["formula"], valores, unidades)
    if _un(c["unidade"]) == "%" and un_res != "%" and not any(
            isinstance(x, ast.Constant) and x.value == 100 for x in ast.walk(ast.parse(c["formula"].strip(), mode="eval"))):
        raise ErroConta("unidade % e a fórmula não tem 100: o resultado sairia 100 vezes menor (25/200 daria 0,1%). Multiplique por 100, por exemplo a/b*100")
    usados = {n.id for n in ast.walk(ast.parse(c["formula"].strip(), mode="eval")) if isinstance(n, ast.Name)}
    avisos = [f"entrada '{n}' não é usada na fórmula" for n in valores if n not in usados]
    if c["decisivo"] == "sim" and fracas:
        raise ErroConta("não pode ser decisivo: depende de prova fraca que o consultor ainda não conferiu: " + "; ".join(fracas))
    formato = c.get("formato") or formato_da_unidade(c["unidade"])
    valor_txt = formatar(resultado, formato, c.get("casas"), c["unidade"], c.get("escala"))
    fonte = f"Cálculo: {c['formula'].strip()}; " + "; ".join(partes) + f" · {HOJE}"
    if fracas:
        fonte += " [prova fraca: " + "; ".join(fracas) + "]"
    return {"valor_txt": valor_txt, "valor_num": resultado, "fonte": fonte, "avisos": avisos, "fracas": fracas}


def executar_contas(contas, ficha, origens):
    """Calcula e grava cada conta. Devolve (resultados, erros)."""
    resultados, erros = [], []
    for k, c in enumerate(contas, 1):
        rotulo = (c.get("id") or c.get("dado")) if isinstance(c, dict) else None
        rotulo = rotulo or f"conta {k}"
        try:
            if not isinstance(c, dict):
                raise ErroConta("conta deve ser um objeto")
            r = calcular_conta(c, origens)
            ident, acao = (c.get("id") or "", "calculada (sem ficha)")
            if ficha is not None:
                ident, acao = ficha.gravar(c, r["valor_txt"], r["fonte"])
            resultados.append({"id": ident, "dado": c["dado"], "valor": r["valor_txt"], "valor_num": str(r["valor_num"]),
                               "unidade": c["unidade"], "periodo": c.get("periodo", ""), "formula": c["formula"].strip(),
                               "entradas": {n: {"valor": str(e["valor"]), "unidade": e["unidade"], "origem": e["origem"]} for n, e in c["entradas"].items()},
                               "fonte": r["fonte"], "decisivo": c["decisivo"], "usado_em": c.get("usado_em", ""),
                               "acao": acao, "avisos": r["avisos"], "prova_fraca": r["fracas"]})
        except ErroConta as e:
            erros.append(f"{rotulo}: {e}")
    return resultados, erros


# ---------------------------------------------------------------- tabelas (receitas)

def ler_tabela(caminho, aba=None):
    """CSV, TSV ou XLSX -> lista de linhas (listas de texto). CSV: separador e codificação detectados."""
    from extrair_insumos import decodificar_csv, detectar_separador
    p = Path(caminho)
    if not p.is_file():
        raise ErroConta(f"arquivo não encontrado: {p}")
    if p.suffix.lower() in (".xlsx", ".xlsm"):
        try:
            from openpyxl import load_workbook
        except ImportError:
            raise ErroConta("openpyxl não instalado (pip install -r scripts/requirements.txt)")
        wb = load_workbook(str(p), read_only=True, data_only=True)
        try:
            ws = wb[aba] if aba else next((w for w in wb.worksheets if w.max_row and w.max_row > 1), wb.worksheets[0])
            return [["" if c is None else str(c) for c in row] for row in ws.iter_rows(values_only=True)]
        finally:
            wb.close()
    csv.field_size_limit(10_000_000)
    texto = decodificar_csv(p.read_bytes())
    sep = detectar_separador(texto)
    return [row for row in csv.reader(io.StringIO(texto, newline=""), delimiter=sep)]


def achar_cabecalho(linhas, termos):
    """Primeira linha (nas 20 primeiras) com alguma célula que case com os termos. Devolve o índice."""
    for i, row in enumerate(linhas[:20]):
        if any(sem_acento(c) in termos for c in row):
            return i
    raise ErroConta("cabeçalho não reconhecido (esperava colunas como " + ", ".join(sorted(termos)[:6]) + "...)")


def coluna(cab, nomes):
    norm = [sem_acento(c) for c in cab]
    for n in nomes:
        if n in norm:
            return norm.index(n)
    for n in nomes:                                        # "valor usado (brl)" casa com "valor usado"
        for i, c in enumerate(norm):
            if c.startswith(n) and " por " not in c and "/" not in c:
                return i
    return None


def linhas_de_dados(linhas, i_cab):
    cab = linhas[i_cab]
    corpo = [r for r in linhas[i_cab + 1:] if any(c.strip() for c in r)]
    return cab, corpo


def num_coluna(corpo, idx):
    """Valores numéricos de uma coluna (None onde não for número)."""
    bruto = [r[idx] if idx < len(r) else "" for r in corpo]
    modo = modo_da_coluna(b for b in bruto if b.strip())
    out = []
    for b in bruto:
        try:
            out.append(parse_valor(b, modo)[0] if b.strip() not in ("", "-", "--") else None)
        except ValueError:
            out.append(None)
    return out


def conta_pronta(dado, formula, entradas, unidade, **kw):
    c = {"dado": dado, "formula": formula, "unidade": unidade, "entradas": entradas}
    c.update({k: v for k, v in kw.items() if v is not None})
    return c


def ent(valor, unidade, origem):
    return {"valor": valor, "unidade": unidade, "origem": origem, "_interna": True}


def linha_conta(dado, valor, unidade, origem, **kw):
    """Conta de um valor lido direto da tabela (fórmula = a própria entrada)."""
    return conta_pronta(dado, "v", {"v": ent(valor, unidade, origem)}, unidade, **kw)


ETAPA = {"etapa", "estagio", "fase", "stage", "status", "etapa do funil", "estagio do funil", "funil", "situacao"}
QTD = {"quantidade", "qtd", "qtde", "total", "count", "contagem", "leads", "negocios", "oportunidades", "deals", "volume", "numero de leads"}
MOTIVO = {"motivo", "motivo de perda", "motivo da perda", "motivo perda", "motivo de perda do negocio", "razao", "razao da perda",
          "loss reason", "lost reason", "reason", "motivo de descarte", "motivo do descarte"}


def contar(linhas, termos_rotulo, ordem=None, acumulado=False):
    """Tabela de contagem (rótulo + quantidade) ou registros (um por linha, com coluna de rótulo). -> [(rótulo, n)]."""
    i = achar_cabecalho(linhas, termos_rotulo)
    cab, corpo = linhas_de_dados(linhas, i)
    ir = coluna(cab, sorted(termos_rotulo, key=len, reverse=True))
    iq = coluna(cab, sorted(QTD, key=len, reverse=True))
    pares = []
    if iq is not None and iq != ir:
        qs = num_coluna(corpo, iq)
        for r, q in zip(corpo, qs):
            rot = (r[ir] if ir < len(r) else "").strip()
            if rot and q is not None and sem_acento(rot) not in ("total", "soma", "total geral"):
                pares.append((rot, q))
        agregado = {}
        for rot, q in pares:
            agregado[rot] = agregado.get(rot, Decimal(0)) + q
        pares = list(agregado.items())
    else:
        cont = {}
        for r in corpo:
            rot = (r[ir] if ir < len(r) else "").strip()
            if rot:
                cont[rot] = cont.get(rot, 0) + 1
        pares = [(k, Decimal(v)) for k, v in cont.items()]
    if ordem:
        chaves = {sem_acento(k): k for k, _ in pares}
        faltam = [o for o in ordem if sem_acento(o) not in chaves]
        if faltam:
            raise ErroConta("etapa(s) da --ordem que não existem no arquivo: " + ", ".join(faltam))
        pares = [(chaves[sem_acento(o)], dict(pares)[chaves[sem_acento(o)]]) for o in ordem]
        if acumulado:
            pares = [(r, sum((q for _, q in pares[k:]), Decimal(0))) for k, (r, _) in enumerate(pares)]
    if not pares:
        raise ErroConta("nenhuma linha de dados")
    return pares


def receita_funil(caminho, a):
    linhas = ler_tabela(caminho, a.aba)
    ordem = [x.strip() for x in a.ordem.split(",")] if a.ordem else None
    pares = contar(linhas, ETAPA, ordem, a.acumulado)
    nome = Path(caminho).name
    org = f"{nome}, contagem por etapa"
    contas, tabela = [], []
    for k, (etapa, q) in enumerate(pares):
        contas.append(linha_conta(f"{a.rotulo or 'Funil'} · {etapa}", q, a.unidade, org))
        tabela.append({"etapa": etapa, "quantidade": q})
    for k in range(1, len(pares)):
        (e0, q0), (e1, q1) = pares[k - 1], pares[k]
        if q0 == 0:
            continue
        contas.append(conta_pronta(f"{a.rotulo or 'Funil'} · conversão {e0} → {e1}", "q1 / q0 * 100",
                                   {"q0": ent(q0, a.unidade, org), "q1": ent(q1, a.unidade, org)}, "%", casas=1))
        tabela[k]["conversao_da_anterior"] = q1 / q0 * 100
    if len(pares) > 2 and pares[0][1] != 0:
        contas.append(conta_pronta(f"{a.rotulo or 'Funil'} · conversão total {pares[0][0]} → {pares[-1][0]}", "qf / q0 * 100",
                                   {"q0": ent(pares[0][1], a.unidade, org), "qf": ent(pares[-1][1], a.unidade, org)}, "%", casas=1))
    for t in tabela:
        for k in ("conversao_da_anterior",):
            if k in t:
                t[k + "_fmt"] = milhar_br(t[k], 1) + "%"
        t["quantidade_fmt"] = milhar_br(t["quantidade"], 0)
    return contas, {"receita": "funil", "arquivo": nome, "linhas": tabela}


def receita_motivos(caminho, a):
    linhas = ler_tabela(caminho, a.aba)
    pares = sorted(contar(linhas, MOTIVO), key=lambda x: (-x[1], x[0]))
    total = sum((q for _, q in pares), Decimal(0))
    nome = Path(caminho).name
    org = f"{nome}, contagem por motivo"
    rot = a.rotulo or "Motivo de perda"
    contas = [linha_conta(f"{rot} · total", total, a.unidade, org)]
    tabela = []
    for motivo, q in pares:
        contas.append(linha_conta(f"{rot} · {motivo} (quantidade)", q, a.unidade, org))
        contas.append(conta_pronta(f"{rot} · {motivo} (%)", "q / total * 100",
                                   {"q": ent(q, a.unidade, org), "total": ent(total, a.unidade, org)}, "%", casas=1))
        tabela.append({"motivo": motivo, "quantidade": q, "quantidade_fmt": milhar_br(q, 0),
                       "percentual_fmt": milhar_br(q / total * 100, 1) + "%" if total else ""})
    return contas, {"receita": "motivos", "arquivo": nome, "total": milhar_br(total, 0), "linhas": tabela}


CAMPANHA = ["nome da campanha", "campaign name", "campanha", "campaign", "nome do conjunto de anuncios", "ad set name"]
GASTO = ["valor usado (brl)", "valor usado", "amount spent (brl)", "amount spent", "valor gasto", "custo (brl)", "custo", "cost", "spend",
         "gasto", "investimento", "cost (brl)", "valor investido"]
RESULTADOS = ["resultados", "results", "conversoes", "conversions", "todas as conversoes", "all conversions", "leads", "compras",
              "purchases", "conversoes (todas)", "resultado"]
CANAL = ["canal", "channel", "plataforma", "platform", "rede", "network", "fonte", "source"]
IMPRESSOES = ["impressoes", "impressions", "impr."]
CLIQUES = ["cliques", "clicks", "cliques no link (todos)", "link clicks", "cliques no link"]


def receita_midia(caminhos, a):
    todas, nomes_arq = [], []
    canais_arg = list(a.canal or [])
    for k, cam in enumerate(caminhos):
        linhas = ler_tabela(cam, a.aba)
        i = achar_cabecalho(linhas, set(CAMPANHA) | set(GASTO))
        cab, corpo = linhas_de_dados(linhas, i)
        ic, ig = coluna(cab, CAMPANHA), coluna(cab, GASTO)
        ir, ik = coluna(cab, RESULTADOS), coluna(cab, CANAL)
        if ig is None:
            raise ErroConta(f"{Path(cam).name}: não achei a coluna de gasto (Valor usado, Amount spent, Custo, Cost...)")
        gastos = num_coluna(corpo, ig)
        resultados = num_coluna(corpo, ir) if ir is not None else [None] * len(corpo)
        if canais_arg:
            padrao = canais_arg[k] if k < len(canais_arg) else canais_arg[-1]
        else:
            nc = [sem_acento(c) for c in cab]
            padrao = ("Meta" if any(x in nc for x in ("nome da campanha", "campaign name")) and any("valor usado" in x or "amount spent" in x for x in nc)
                      else "Google" if any(x in nc for x in ("custo", "cost")) else Path(cam).stem)
        for r, g, res in zip(corpo, gastos, resultados):
            nome_c = (r[ic] if ic is not None and ic < len(r) else "").strip()
            if g is None or (ic is not None and not nome_c) or sem_acento(nome_c).startswith(("total", "resultado total")):
                continue
            canal = (r[ik].strip() if not canais_arg and ik is not None and ik < len(r) and r[ik].strip() else padrao)
            todas.append({"canal": canal, "campanha": nome_c, "gasto": g, "resultados": res})
        nomes_arq.append(Path(cam).name)
    if not todas:
        raise ErroConta("nenhuma linha de campanha com gasto")
    tem_res = any(t["resultados"] is not None for t in todas)
    arq = ", ".join(nomes_arq)
    rot = a.rotulo or "Mídia"
    canais = {}
    for t in todas:
        c = canais.setdefault(t["canal"], {"gasto": Decimal(0), "resultados": Decimal(0), "campanhas": 0})
        c["gasto"] += t["gasto"]
        c["resultados"] += t["resultados"] or Decimal(0)
        c["campanhas"] += 1
    gasto_total = sum((c["gasto"] for c in canais.values()), Decimal(0))
    res_total = sum((c["resultados"] for c in canais.values()), Decimal(0))
    org = f"{arq}, colunas de gasto{' e resultados' if tem_res else ''}"
    contas = [linha_conta(f"{rot} · gasto total", gasto_total, "R$", org, casas=2)]
    if tem_res:
        contas.append(linha_conta(f"{rot} · resultados totais", res_total, a.unidade_resultado, org))
        if res_total:
            contas.append(conta_pronta(f"{rot} · custo por resultado total", "g / r",
                                       {"g": ent(gasto_total, "R$", org), "r": ent(res_total, a.unidade_resultado, org)}, "R$"))
    tabela_canais = []
    for nome_c, c in sorted(canais.items(), key=lambda x: -x[1]["gasto"]):
        contas.append(linha_conta(f"{rot} · {nome_c} · gasto", c["gasto"], "R$", org, casas=2))
        if gasto_total:
            contas.append(conta_pronta(f"{rot} · {nome_c} · % do investimento", "g / t * 100",
                                       {"g": ent(c["gasto"], "R$", org), "t": ent(gasto_total, "R$", org)}, "%", casas=1))
        linha_t = {"canal": nome_c, "campanhas": c["campanhas"], "gasto_fmt": formatar(c["gasto"], "moeda"),
                   "percentual_fmt": milhar_br(c["gasto"] / gasto_total * 100, 1) + "%" if gasto_total else ""}
        if tem_res:
            contas.append(linha_conta(f"{rot} · {nome_c} · resultados", c["resultados"], a.unidade_resultado, org))
            linha_t["resultados_fmt"] = milhar_br(c["resultados"], 0)
            if c["resultados"]:
                contas.append(conta_pronta(f"{rot} · {nome_c} · custo por resultado", "g / r",
                                           {"g": ent(c["gasto"], "R$", org), "r": ent(c["resultados"], a.unidade_resultado, org)}, "R$"))
                linha_t["custo_por_resultado_fmt"] = formatar(c["gasto"] / c["resultados"], "moeda")
            else:
                linha_t["custo_por_resultado_fmt"] = "sem resultado"
        tabela_canais.append(linha_t)
    tabela_camp = []
    for t in sorted(todas, key=lambda x: (x["canal"], -x["gasto"])):
        linha_t = {"canal": t["canal"], "campanha": t["campanha"], "gasto_fmt": formatar(t["gasto"], "moeda")}
        if tem_res and t["resultados"] is not None:
            linha_t["resultados_fmt"] = milhar_br(t["resultados"], 0)
            linha_t["custo_por_resultado_fmt"] = formatar(t["gasto"] / t["resultados"], "moeda") if t["resultados"] else "sem resultado"
        tabela_camp.append(linha_t)
        if a.por_campanha:
            contas.append(linha_conta(f"{rot} · {t['canal']} · {t['campanha']} · gasto", t["gasto"], "R$", org, casas=2))
            if tem_res and t["resultados"]:
                contas.append(conta_pronta(f"{rot} · {t['canal']} · {t['campanha']} · custo por resultado", "g / r",
                                           {"g": ent(t["gasto"], "R$", org), "r": ent(t["resultados"], a.unidade_resultado, org)}, "R$"))
    avisos = [] if tem_res else ["sem coluna de resultados: só gasto e divisão por canal"]
    return contas, {"receita": "midia", "arquivos": nomes_arq, "por_canal": tabela_canais, "por_campanha": tabela_camp,
                    "gasto_total": formatar(gasto_total, "moeda"), "avisos": avisos}


def receita_tabela(caminho, a):
    arq = Path(caminho)
    if not arq.is_file():
        raise ErroConta(f"arquivo não encontrado: {arq}")
    if not a.pagina:
        raise ErroConta("--tabela precisa de --pagina N")
    trecho, ocr = pagina_do_texto(arq, a.pagina)
    if trecho is None:
        raise ErroConta(f"{arq.name} não tem a página {a.pagina}")
    blocos, atual = [], []
    for ln in trecho.splitlines():
        if " | " in ln:
            atual.append([c.strip() for c in ln.split(" | ")])
        else:
            if atual:
                blocos.append(atual)
            atual = []
    if atual:
        blocos.append(atual)
    if not blocos:
        raise ErroConta(f"não achei tabela (linhas com ' | ') na página {a.pagina} de {arq.name}")
    bloco = max(blocos, key=len)
    n_col = max(set(len(r) for r in bloco), key=[len(r) for r in bloco].count)
    bloco = [r for r in bloco if len(r) == n_col]
    cab = None
    primeira_numerica = sum(1 for c in bloco[0] if _eh_numero(c))
    if primeira_numerica == 0 and len(bloco) > 1:
        cab, bloco = bloco[0], bloco[1:]
    numericas = [j for j in range(n_col) if sum(1 for r in bloco if _eh_numero(r[j])) >= max(1, 0.6 * len(bloco))]
    if not numericas:
        raise ErroConta("a tabela não tem coluna numérica")
    if a.coluna:
        if a.coluna.isdigit():
            j = int(a.coluna) - 1
        else:
            j = next((i for i, c in enumerate(cab or []) if sem_acento(c) == sem_acento(a.coluna)), None)
        if j is None or j not in numericas:
            raise ErroConta(f"coluna {a.coluna!r} não é uma coluna numérica da tabela (numéricas: {[(cab[i] if cab else i + 1) for i in numericas]})")
    else:
        j = numericas[0]
    rotulo_j = cab[j] if cab else f"coluna {j + 1}"
    j_rot = next((i for i in range(n_col) if i not in numericas), 0)
    modo = modo_da_coluna(r[j] for r in bloco)
    itens = []
    for r in bloco:
        rot = r[j_rot]
        if sem_acento(rot) in ("total", "soma", "total geral"):
            continue
        itens.append((rot, parse_valor(r[j], modo)[0], r[j]))
    soma = sum((v for _, v, _ in itens), Decimal(0))
    pag = f"{arq.name} · página {a.pagina}"
    rot = a.rotulo or "Tabela"
    unid = a.unidade if a.unidade != "itens" else (parse_valor(itens[0][2])[1] or "itens")
    fmt = formato_da_unidade(unid)
    contas = [linha_conta(f"{rot} · soma de {rotulo_j}", soma, unid, pag, casas=0 if unid not in ("R$",) else 2)]
    tabela = []
    for nome_i, v, bruto in itens:
        contas.append(linha_conta(f"{rot} · {nome_i} ({rotulo_j})", v, unid, pag, casas=casas_de(v) if fmt != "moeda" else 2))
        contas.append(conta_pronta(f"{rot} · {nome_i} (% de {rotulo_j})", "v / s * 100",
                                   {"v": ent(v, unid, pag), "s": ent(soma, unid, pag)}, "%", casas=1))
        tabela.append({"item": nome_i, "valor": bruto, "percentual_fmt": milhar_br(v / soma * 100, 1) + "%" if soma else ""})
    total_lido = next((parse_valor(r[j], modo)[0] for r in bloco if sem_acento(r[j_rot]) in ("total", "soma", "total geral")), None)
    avisos = []
    if total_lido is not None and total_lido != soma:
        avisos.append(f"a linha Total da tabela ({milhar_br(total_lido, 2)}) difere da soma calculada ({milhar_br(soma, 2)})")
    if ocr:
        avisos.append("página lida por OCR: prova fraca, o consultor confere antes de usar como decisivo")
    return contas, {"receita": "tabela", "arquivo": pag, "coluna": rotulo_j, "soma": formatar(soma, fmt, None, unid), "linhas": tabela,
                    "avisos": avisos, "ocr": ocr}


def _eh_numero(c):
    try:
        parse_valor(c)
        return True
    except ValueError:
        return False


# ---------------------------------------------------------------- principal

def principal():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("contas", nargs="?", help="contas.json (o que calcular: id, dado, fórmula e entradas com valor, unidade e origem)")
    ap.add_argument("--ficha", help="ficha do cliente (<Nome>.md): grava ou atualiza as linhas de Números-fonte")
    ap.add_argument("--saida", help="resultado em JSON para o deck (padrão: ao lado do contas.json ou do CSV)")
    ap.add_argument("--dados", help="dados-pesquisa.json, para conferir origens 'dados-pesquisa.json#D07'")
    ap.add_argument("--texto", help="pasta _texto do cliente, para conferir origens 'arquivo.txt · página N'")
    ap.add_argument("--coleta", help="pasta da coleta de fontes (indice.json do coletar_fontes.py); padrão: coleta/ ao lado do dados-pesquisa.json")
    ap.add_argument("--funil", metavar="CSV")
    ap.add_argument("--midia", nargs="+", metavar="CSV")
    ap.add_argument("--motivos", metavar="CSV")
    ap.add_argument("--tabela", metavar="TEXTO")
    ap.add_argument("--pagina", type=int)
    ap.add_argument("--coluna", help="--tabela: nome ou número da coluna numérica")
    ap.add_argument("--aba", help="planilha XLSX: aba a ler")
    ap.add_argument("--ordem", help="--funil: etapas na ordem, separadas por vírgula")
    ap.add_argument("--acumulado", action="store_true", help="--funil com --ordem: quem passou da etapa conta nas anteriores")
    ap.add_argument("--canal", nargs="*", help="--midia: nome do canal de cada arquivo, na ordem")
    ap.add_argument("--por-campanha", action="store_true", help="--midia: grava também gasto e custo por resultado de cada campanha")
    ap.add_argument("--rotulo", help="prefixo do nome do dado nas receitas")
    ap.add_argument("--unidade", default="itens", help="receitas: unidade das contagens (padrão: itens)")
    ap.add_argument("--unidade-resultado", default="resultados", help="--midia: unidade dos resultados")
    ap.add_argument("--periodo", default="")
    ap.add_argument("--dono", default="Trieme")
    ap.add_argument("--usado-em", default="")
    ap.add_argument("--decisivo", default="não")
    ap.add_argument("--data", help="data do cálculo dd/mm/aaaa (padrão: hoje)")
    a = ap.parse_args()
    global HOJE
    if a.data:
        HOJE = a.data

    receitas = [x for x in (a.funil, a.midia, a.motivos, a.tabela) if x]
    if len(receitas) > 1 or (receitas and a.contas):
        print("Use um só: contas.json ou uma receita (--funil, --midia, --motivos, --tabela).")
        return 1
    if not receitas and not a.contas:
        ap.print_help()
        return 1
    try:
        ficha = Ficha(a.ficha) if a.ficha else None
    except (ErroConta, OSError, UnicodeDecodeError) as e:
        print(f"ERRO ficha: {e}")
        return 1

    extra, avisos_receita = {}, []
    if a.contas:
        base_dir = Path(a.contas).resolve().parent
        try:
            cj = json.loads(Path(a.contas).read_text(encoding="utf-8"))
        except (OSError, ValueError) as e:
            print(f"ERRO contas.json: {e}")
            return 1
        contas = cj.get("contas") if isinstance(cj, dict) else cj
        if not isinstance(contas, list) or not contas:
            print('ERRO contas.json: esperava {"contas": [ ... ]} com ao menos uma conta')
            return 1
        for c in contas:                                        # só as receitas marcam entrada como lida da tabela
            if isinstance(c, dict) and isinstance(c.get("entradas"), dict):
                for e in c["entradas"].values():
                    if isinstance(e, dict):
                        e.pop("_interna", None)
        saida_padrao = Path(a.contas).with_suffix("").with_name(Path(a.contas).stem + ".resultado.json")
    else:
        try:
            if a.funil:
                base_dir = Path(a.funil).resolve().parent
                contas, extra = receita_funil(a.funil, a)
            elif a.midia:
                base_dir = Path(a.midia[0]).resolve().parent
                contas, extra = receita_midia(a.midia, a)
            elif a.motivos:
                base_dir = Path(a.motivos).resolve().parent
                contas, extra = receita_motivos(a.motivos, a)
            else:
                base_dir = Path(a.tabela).resolve().parent
                contas, extra = receita_tabela(a.tabela, a)
        except ErroConta as e:
            print(f"ERRO: {e}")
            return 1
        avisos_receita = extra.get("avisos", [])
        for c in contas:
            c.setdefault("periodo", a.periodo)
            c["dono"], c["usado_em"], c["decisivo"] = a.dono, a.usado_em, a.decisivo
            if extra.get("ocr") and c["decisivo"] == "sim":
                c["decisivo"] = "não"
        fonte_ref = receitas[0] if isinstance(receitas[0], str) else receitas[0][0]
        pasta_fonte = Path(fonte_ref).resolve().parent
        if not a.saida and any(sem_acento(x).startswith("0.") or "inputs" in sem_acento(x) or x == "_texto" for x in [pasta_fonte.name]):
            print("ERRO: o arquivo está em 0. Inputs e Transcrições; passe --saida com um caminho em _fonte/ da semana (a pasta de insumos não recebe arquivo novo).")
            return 1
        saida_padrao = Path(fonte_ref).with_name(Path(fonte_ref).stem + ".resultado.json")

    texto_dir = a.texto
    if not texto_dir:                                           # _texto ao lado, se existir
        for pai in [base_dir, *list(base_dir.parents)[:3]]:
            if (pai / "_texto").is_dir():
                texto_dir = str(pai / "_texto")
                break
            if (pai / "0. Inputs e Transcrições" / "_texto").is_dir():
                texto_dir = str(pai / "0. Inputs e Transcrições" / "_texto")
                break
    origens = Origens(ficha, a.dados, texto_dir, base_dir, a.coleta)
    resultados, erros = executar_contas(contas, ficha, origens)

    if ficha is not None and resultados:
        ficha.salvar()
    saida = Path(a.saida) if a.saida else saida_padrao
    corpo = {"gerado_em": HOJE, "ficha": str(a.ficha) if a.ficha else None, "resultados": resultados, "erros": erros}
    corpo.update({k: v for k, v in extra.items() if k not in ("avisos", "ocr")})
    corpo["avisos"] = avisos_receita + [f"{r['id'] or r['dado']}: {x}" for r in resultados for x in r["avisos"]]
    try:
        saida.write_text(json.dumps(corpo, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    except OSError as e:
        print(f"ERRO ao gravar {saida}: {e}")
        return 1

    for r in resultados:
        print(f"{r['id'] or '-'} · {r['dado']} = {r['valor']} ({r['acao']})")
    for x in corpo["avisos"]:
        print(f"AVISO {x}")
    for e in erros:
        print(f"ERRO {e}")
    print(f"{len(resultados)} conta(s) feita(s), {len(erros)} com erro. " + (f"Ficha: {a.ficha}. " if a.ficha else "Sem --ficha: nada gravado na ficha. ") + f"Resultado: {saida}")
    return 1 if erros else 0


if __name__ == "__main__":
    sys.exit(principal())
