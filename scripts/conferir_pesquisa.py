"""Conferências da Semana 2 que o verificador de texto sozinho não faz (decisões 0041, 0042 e 0043).

Uso:
    python conferir_pesquisa.py <pasta da semana | deck.html>

Regra das conferências: erro só quando a evidência é estruturada (uma decisão declarada em `_fonte/ideia-central.md`,
um campo de `_fonte/dados-pesquisa.json`, a estrutura do `conteudo.json`). O que depende só de palavra é aviso.

1. Provas do cliente. Usa `provas-cliente.md` quando presente e a tabela antiga em `ideia-central.md` quando ausente.
   Novo ilegível/inválido, ausência de registro, origem vazia ou reclassificação sem motivo são erros.
   Toda prova marcada como decisiva na seção "Provas do cliente" tem destino:
   a tela onde entra ("tela 08"), "DOCX" ou "fora: <motivo>". Decisiva sem destino, ou fora sem motivo, é erro.
   Prova cujo número não aparece na tela indicada é aviso (o deck pode ter arredondado). Prova que é fala de reunião
   (Origem só com horário, "K 01:12:18", sem documento) vai à tela de destino com o horário à vista, no texto ou nas fontes; sem ele,
   é erro: usar a ideia sem dizer que veio do cliente não é usar a prova.
2. Um dono por ação no plano (tela "A trava e o plano"). Dono com "e", vírgula, barra ou "+" é erro: duas pessoas viram duas ações.
3. Rótulo. Frase que diz "pagam" (ou "pago") com um valor que `dados-pesquisa.json` marca como teto, sem dizer
   "teto" ou "máximo" junto do valor, é erro quando o tipo veio do campo `tipo_valor`; quando só a descrição sugere
   teto, ou a frase nega o pagamento, é aviso.
4. Mercado. A linha "Preço comparável: R$ x · por quê" (ou "nenhum") de `ideia-central.md` diz que preço de
   terceiro pode medir o mercado. TAM, SAM ou SOM com outro preço de `dados-pesquisa.json` é erro; sem a linha, aviso.
   O SOM diz o horizonte ("em 12 meses"); sem ele, erro.
5. Substituto. A tela 03 tem o cartão "Substituto · <nome>", com o nome da linha "Substituto: <nome> · <como>" de
   `ideia-central.md`. Cartão ausente ou com outro nome é erro. Confere coerência com a decisão, não o mérito dela.
6. Aviso: pilar da PUV com "Prova:" que é promessa ou estimativa (pela B6, promessa sem prova sai da tela). O fato duro sem
   decisão (D8) não tem conferência: casar palavras entre o SWOT e o TOWS não o detecta com confiabilidade.

Lê `_fonte/conteudo.json`, `_fonte/ideia-central.md`, `_fonte/provas-cliente.md` e `_fonte/dados-pesquisa.json`.
Sem conteúdo, ainda exige e confere o registro de provas; as demais conferências dependem do JSON. Sai 1 com erro.
O verificador (`verificar_entrega.py --semana 2`) chama `conferir()` sozinho.
"""
import sys
sys.dont_write_bytecode = True
import io, json, re, unicodedata
from pathlib import Path
from urllib.parse import unquote, urlsplit

VAZIAS = {
    "para", "como", "com", "das", "dos", "que", "mais", "sem", "entre", "ainda", "antes", "depois", "sobre", "pela",
    "pelo", "pelos", "pelas", "plano", "acao", "acoes", "horizonte", "semana", "tela", "telas", "evoluir", "onde",
    "fica", "desta", "deste", "esta", "este", "essa", "esse", "isso", "cada", "todo", "toda", "todos", "todas",
    "hoje", "lado", "valor", "numero", "vezes", "quando", "qual", "quais", "seus", "suas", "nosso", "nossa",
    "voces", "cliente", "empresa", "proximo", "proxima",
}
ANO = re.compile(r"^(19|20)\d\d$")
# número que identifica documento, e não é dado: "Lei 14.133/21", "ata nº 19/2024", "pregão 03/2025", "art. 73"
IDENTIFICADOR_ANTES = re.compile(r"(lei|n[º°o]\.?|art\.?|artigo|ata|preg[aã]o|edital|processo|portaria|decreto|resolu[cç][aã]o|"
                                 r"delibera[cç][aã]o|contrato|termo|cnpj|cep)\s*$", re.I)
NUM = r"\d{1,3}(?:\.\d{3})+(?:,\d+)?|\d+(?:,\d+)?"
RS = re.compile(r"R\$\s*(" + NUM + r")")
HORA = re.compile(r"\b(\d{1,2}):(\d{2})(?::\d{2})?\b")


def sem_acento(s):
    s = unicodedata.normalize("NFKD", str(s or ""))
    return "".join(c for c in s if not unicodedata.combining(c)).lower()


def sem_tags(s):
    return re.sub(r"<[^>]+>", " ", str(s or ""))


def texto_visivel(html):
    html = re.sub(r"<(style|script)\b.*?</\1>", " ", html, flags=re.S | re.I)
    return re.sub(r"\s+", " ", sem_tags(html))


def palavras(s):
    return {w for w in re.findall(r"[a-z0-9]{4,}", sem_acento(sem_tags(s))) if w not in VAZIAS}


def palavra_em_comum(a, b):
    return any(x == y or (len(x) >= 5 and len(y) >= 5 and x[:5] == y[:5]) for x in a for y in b)


def numeros(s):
    """Números de 3 dígitos ou mais (ou com decimal), sem separador de milhar. Ficam fora os anos soltos e os
    números que identificam documento (lei, ata, edital, processo; ou seguidos de "/ano")."""
    s = str(s or "")
    achados = set()
    for m in re.finditer(r"\d{1,3}(?:\.\d{3})+(?:,\d+)?|\d+,\d+|\d{3,}", s):
        n = m.group(0).replace(".", "")
        if ANO.match(n):
            continue
        if IDENTIFICADOR_ANTES.search(s[max(0, m.start() - 14):m.start()]) or re.match(r"/\d{2,4}\b", s[m.end():]):
            continue
        achados.add(n)
    return achados


def horas(s):
    """Horários de reunião ('01:12:18', '1:12') como (hora, minuto)."""
    return {(int(h), int(m)) for h, m in HORA.findall(str(s or ""))}


def norm_rs(n):
    """'1.234,5' vira '1234,50'; '89' vira '89,00'."""
    n = n.replace(".", "")
    inteiro, _, dec = n.partition(",")
    return f"{int(inteiro)},{(dec + '00')[:2]}"


def valores_rs(s):
    """Valores em reais (precedidos de R$), normalizados: 'R$ 89' e 'R$ 89,00' são o mesmo valor."""
    return {norm_rs(m.group(1)) for m in RS.finditer(str(s or ""))}


def textos(conteudo):
    """(onde, texto) de tudo o que vai à tela: capa, título e blocos de cada tela (sem rodapé de fonte nem DOCX)."""
    def achatar(x):
        if isinstance(x, str):
            yield x
        elif isinstance(x, dict):
            for v in x.values():
                yield from achatar(v)
        elif isinstance(x, list):
            for v in x:
                yield from achatar(v)
    hero = conteudo.get("hero") or {}
    for s in achatar([hero.get("titulo"), hero.get("lede"), hero.get("meta")]):
        yield "capa", s
    for t in conteudo.get("telas", []) or []:
        if t.get("so_docx"):
            continue
        onde = (t.get("eyebrow") or "?")[:40]
        yield onde, t.get("h2", "") or ""
        for s in achatar(t.get("blocos", [])):
            yield onde, s
        for k in ("cenario", "regulacao", "camadas", "tam_compradores", "sam_compradores", "leitura_meta",
                  "mercado_limita", "posicionamento", "fundamento_oferta", "comite_compra", "onde_concentrar"):
            for s in achatar(t.get(k)):
                yield onde, s


def linha_da_ideia(fonte, rotulo):
    """Texto depois de '<rotulo>:' numa linha de ideia-central.md (sem acento, sem maiúscula). None se não houver."""
    arq = fonte / "ideia-central.md"
    if not arq.is_file():
        return None
    alvo = sem_acento(rotulo)
    for l in io.open(arq, encoding="utf-8").read().splitlines():
        m = re.match(r"^\s*(?:[-*]\s*)?\**([^:*]+?)\**\s*:\**\s*(.+)$", l)
        if m and sem_acento(m.group(1)).strip() == alvo:
            return m.group(2).strip()
    return None


# ---------------------------------------------------------------- 1. provas do cliente

def _secao(md, nome):
    secoes = list(re.finditer(r"^##[ \t]+([^\r\n]+)[ \t]*$", md, re.M))
    achadas = [(n, m) for n, m in enumerate(secoes) if sem_acento(m.group(1)).strip() == sem_acento(nome)]
    if len(achadas) > 1:
        raise ValueError(f"seção '{nome}' duplicada")
    if not achadas:
        return None
    n, m = achadas[0]
    return md[m.end():secoes[n + 1].start() if n + 1 < len(secoes) else len(md)]


def _tabela(secao):
    if secao is None:
        return None
    linhas = [l.strip() for l in secao.splitlines() if l.strip().startswith("|")]
    if len(linhas) < 2:
        raise ValueError("tabela inválida: faltam cabeçalho e separador")
    def cel(linha):
        return [c.strip().replace(r"\|", "|") for c in re.split(r"(?<!\\)\|", linha[1:-1] if linha.endswith("|") else linha[1:])]
    cab = [sem_acento(c).strip() for c in cel(linhas[0])]
    separador = cel(linhas[1])
    if len(separador) != len(cab) or not all(re.fullmatch(r":?-{3,}:?", c) for c in separador):
        raise ValueError("tabela inválida: separador não corresponde às colunas")
    corpo = [cel(l) for l in linhas[2:]]
    for n, linha in enumerate(corpo, 1):
        if len(linha) != len(cab):
            raise ValueError(f"linha {n}: quantidade de colunas inválida ({len(linha)}; esperado {len(cab)})")
    return cab, corpo


def ler_tabela_provas(md):
    """Tabela atual, preservando IDs e colunas. None se a seção não existir; inválida lança ValueError."""
    return _tabela(_secao(md, "Provas do cliente"))


def _selecionar_registro(fonte):
    """Um único ponto de seleção: novo presente é autoritativo, inclusive quando falha a leitura."""
    novo = fonte / "provas-cliente.md"
    antigo = fonte / "ideia-central.md"
    arq = novo if novo.exists() or novo.is_symlink() else antigo
    if not arq.exists():
        raise ValueError("sem registro: forneça _fonte/provas-cliente.md ou a tabela antiga em ideia-central.md")
    try:
        with io.open(arq, encoding="utf-8") as entrada:
            md = entrada.read()
    except (OSError, UnicodeError) as ex:
        raise ValueError(f"não foi possível ler {arq.name}: {ex}") from ex
    try:
        tabela = ler_tabela_provas(md)
        if tabela is None:
            raise ValueError("sem a tabela da seção 'Provas do cliente'")
    except ValueError as ex:
        raise ValueError(f"{arq.name}: {ex}") from ex
    return arq, md, tabela


def _colunas(cab, campos):
    indices = {}
    for campo, aliases in campos.items():
        encontrados = [i for i, c in enumerate(cab) if c in aliases]
        if len(encontrados) != 1:
            raise ValueError(f"colunas obrigatórias: '{campo}' precisa aparecer uma vez")
        indices[campo] = encontrados[0]
    return indices


def _estado(texto):
    estado = sem_acento(texto).strip()
    anotado = re.fullmatch(r"(sim|nao|decisiva|nao decisiva)[ \t]*:.*", estado)
    if anotado:
        estado = anotado.group(1)
    return {"decisiva": "sim", "nao decisiva": "nao"}.get(estado, estado)


def _conferir_historico(md, registros, colunas):
    secao = _secao(md, "Reclassificações")
    if secao is None:
        return []
    erros = []
    cab, linhas = _tabela(secao)
    cols = _colunas(cab, {"ID": {"id", "#"}, "Estado anterior": {"estado anterior"},
                          "Estado novo": {"estado novo", "novo estado"}, "Motivo": {"motivo"}})
    estados = {}
    for linha in linhas:
        ident = linha[cols["ID"]]
        anterior, novo = _estado(linha[cols["Estado anterior"]]), _estado(linha[cols["Estado novo"]])
        if ident not in registros:
            erros.append(f"reclassificações · referência {ident} não existe nas provas")
            continue
        if not linha[cols["Motivo"]].strip():
            erros.append(f"reclassificações · {ident} sem motivo da mudança")
        if not anterior or not novo or anterior == novo:
            erros.append(f"reclassificações · {ident} exige estados anterior e novo distintos e preenchidos")
            continue
        booleanos = {"sim", "nao"}
        if (anterior in booleanos) != (novo in booleanos):
            erros.append(f"reclassificações · {ident}: estados devem pertencer ao mesmo campo (Decisiva ou Tipo)")
            continue
        campo = "Decisiva" if anterior in booleanos else "Tipo"
        if campo not in colunas:
            erros.append(f"reclassificações · {ident} não possui coluna {campo} para conferir o estado final")
            continue
        chave = (ident, campo)
        if chave in estados and estados[chave] != anterior:
            erros.append(f"reclassificações · {ident} sem continuidade: {anterior} difere de {estados[chave]}")
        estados[chave] = novo
    for (ident, campo), estado in estados.items():
        if _estado(registros[ident][colunas[campo]]) != estado:
            erros.append(f"reclassificações · {ident}: estado final de {campo} não corresponde à prova atual")
    return erros


def _conferir_referencias(arq, md, registros, conteudo, texto_deck):
    erros = []
    textos_ref = [(arq.name, md), ("conteudo.json", json.dumps(conteudo, ensure_ascii=False)), ("deck", texto_deck)]
    resumo = arq.parent / "ideia-central.md"
    if resumo != arq and resumo.exists():
        try:
            with io.open(resumo, encoding="utf-8") as entrada:
                resumo_md = entrada.read()
            # A tabela antiga é substituída integralmente pelo novo registro, inclusive seus IDs.
            resumo_md = re.sub(r"^##[ \t]+Provas do cliente[ \t]*\r?$.*?(?=^##[ \t]|\Z)", "", resumo_md,
                               flags=re.M | re.S | re.I)
            textos_ref.append((resumo.name, resumo_md))
        except (OSError, UnicodeError) as ex:
            erros.append(f"não foi possível ler ideia-central.md: {ex}")
    for nome, texto in textos_ref:
        for ref in sorted(set(re.findall(r"\b(?:PC|C)\d{2,}\b", texto or "")) - registros.keys()):
            erros.append(f"referência {ref} em {nome} não existe nas provas")
    # Links explícitos são verificáveis; nomes e horários em prosa permanecem referências humanas.
    for alvo in re.findall(r"\[[^\]]*\]\(([^)]+)\)", md):
        alvo = alvo.strip().strip("<>")
        url = urlsplit(alvo)
        if url.scheme or alvo.startswith("#") or alvo.startswith("//"):
            continue
        caminho = arq.parent / unquote(url.path)
        if not caminho.is_file():
            erros.append(f"referência local ausente: {alvo}")
    return erros


def texto_da_tela(conteudo, nn):
    return " ".join(s for onde, s in textos(conteudo or {}) if onde.startswith(nn))


def tela_inteira(conteudo, nn):
    """Tudo o que a tela NN traz, com o rodapé de fontes, onde a origem de uma fala costuma ficar."""
    for t in (conteudo or {}).get("telas", []) or []:
        if not t.get("so_docx") and (t.get("eyebrow") or "").startswith(nn):
            return json.dumps(t, ensure_ascii=False)
    return ""


def conferir_provas(fonte, texto_deck, conteudo=None):
    erros, avisos = [], []
    try:
        arq, md, (cab, corpo) = _selecionar_registro(Path(fonte))
        colunas = _colunas(cab, {"ID": {"#", "id"}, "Fato": {"fato ou numero", "fato/numero", "fato", "numero"},
                               "Origem": {"origem"}, "Decisiva": {"decisiva"}, "Destino": {"destino"}})
        if "tipo" in cab:
            colunas["Tipo"] = cab.index("tipo")
    except ValueError as ex:
        return [f"provas do cliente · {ex}"], []
    i_id, i_dec, i_dest, i_fato, i_orig = (colunas[k] for k in ("ID", "Decisiva", "Destino", "Fato", "Origem"))
    registros = {}
    for linha in corpo:
        ident = linha[i_id]
        if not ident or not linha[i_fato] or not linha[i_orig]:
            erros.append(f"provas do cliente · {ident or '?'}: ID, fato e origem devem estar preenchidos")
        if _estado(linha[i_dec]) not in {"sim", "nao"}:
            erros.append(f"provas do cliente · {ident}: Decisiva deve ser 'sim' ou 'não'")
        if ident in registros:
            if registros[ident] != linha:
                erros.append(f"provas do cliente · ID {ident} com duplicação conflitante")
            else:
                avisos.append(f"provas do cliente · ID {ident} repetido de forma idêntica; revisar duplicação")
        registros[ident] = linha
    if not corpo:
        motivo = re.search(r"^[ \t]*Sem provas:[ \t]*(\S[^\r\n]*)", _secao(md, "Provas do cliente"), re.M | re.I)
        if not motivo:
            erros.append("provas do cliente · tabela vazia exige 'Sem provas: <motivo>'")
        else:
            avisos.append(f"provas do cliente · sem provas declarado: {motivo.group(1)}; exige revisão semântica")
    try:
        erros.extend(_conferir_historico(md, registros, colunas))
        erros.extend(_conferir_referencias(arq, md, registros, conteudo, texto_deck))
    except ValueError as ex:
        erros.append(f"provas do cliente · {arq.name}: {ex}")
    nums_deck = numeros(texto_deck)
    pals_deck = palavras(texto_deck)
    for linha in corpo:
        if len(linha) <= max(i_dec, i_dest):
            continue
        ident = linha[i_id] or "?"
        if _estado(linha[i_dec]) != "sim":
            continue
        dest = sem_acento(linha[i_dest]).strip(" -—")
        fato = linha[i_fato] if i_fato is not None and i_fato < len(linha) else ""
        if not dest:
            erros.append(f"provas do cliente · {ident} é decisiva e não tem destino: diga a tela, 'DOCX' ou 'fora: motivo'")
        elif dest.startswith("fora"):
            motivo = dest.split(":", 1)[1].strip() if ":" in dest else ""
            if not motivo:
                erros.append(f"provas do cliente · {ident} ficou fora do deck sem motivo: escreva 'fora: <motivo>'")
        elif "tela" in dest:
            m = re.match(r"tela\s*(\d{1,2})(?!\d)\b", dest)
            if not m or (conteudo is not None and not tela_inteira(conteudo, f"{int(m.group(1)):02d}")):
                erros.append(f"provas do cliente · destino de {ident}: {dest} não corresponde a uma tela existente")
                continue
            if not texto_deck and conteudo is None:
                continue
            na_tela = texto_da_tela(conteudo, f"{int(m.group(1)):02d}") if (m and conteudo) else ""
            origem = linha[i_orig] if i_orig is not None and i_orig < len(linha) else ""
            # fala: origem só com horário de reunião; quando um documento também é origem, o número ou a palavra bastam
            documento = re.search(r"\bp(?:agina|ag|\.)\s*\d|\.(?:txt|pdf|docx?|xlsx?|pptx?)\b", sem_acento(origem))
            hs = set() if documento else horas(origem)
            if hs and conteudo:
                alvo = (tela_inteira(conteudo, f"{int(m.group(1)):02d}") if m else "") or json.dumps(conteudo, ensure_ascii=False)
                if not hs & horas(alvo):
                    h, mi = min(hs)
                    erros.append(f"provas do cliente · {ident} é fala de reunião ({origem[:30]}) e a {dest[:12]} não traz "
                                 f"o horário: a fala entra com a origem à vista, '(Kickoff, {h:02d}:{mi:02d})'")
                    continue
            nums = numeros(fato)
            if nums:
                if (na_tela and nums & numeros(na_tela)) or (not na_tela and nums & nums_deck):
                    continue
                lugar = f"na {dest[:12]}" if na_tela else "no deck"
                extra = " (está no deck, em outra tela)" if (na_tela and nums & nums_deck) else ""
                avisos.append(f"provas do cliente · {ident} vai para a {dest[:12]}, mas nenhum número dela "
                              f"({', '.join(sorted(nums)[:3])}) aparece {lugar}{extra}")
            elif fato and not palavra_em_comum(palavras(fato), palavras(na_tela) if na_tela else pals_deck):
                avisos.append(f"provas do cliente · {ident} vai para a {dest[:12]}, mas a tela não traz nada dela")
        elif dest != "docx":
            erros.append(f"provas do cliente · destino de {ident} não reconhecido ('{linha[i_dest][:30]}'): use 'tela NN', 'DOCX' ou 'fora: motivo'")
    return erros, avisos


# ---------------------------------------------------------------- 2. plano e dono

def blocos(conteudo):
    for tela in conteudo.get("telas", []) or []:
        for b in tela.get("blocos", []) or []:
            yield tela, b


def plano(conteudo):
    for _, b in blocos(conteudo):
        if b.get("t") == "plano":
            return b
    return None


def conferir_plano(conteudo):
    erros, avisos = [], []
    novos = [b for _, b in blocos(conteudo) if b.get("t") == "proximos_passos"]
    if novos:
        return erros, avisos
    pl = plano(conteudo)
    if pl is None:
        avisos.append("plano · conteudo.json sem o bloco do plano: os donos não foram conferidos")
        return erros, avisos
    avisos.append("plano · formato legado por horizonte; migre para proximos_passos com ação, dono e prazo")
    for h in ("h1", "h2", "h3"):
        for card in pl.get(h, []) or []:
            dono = sem_tags(card.get("dono", "")).strip()
            if re.search(r"\s+e\s+|,|/|\+", dono):
                erros.append(f"plano · ação com mais de um dono ({h.upper()} · {card.get('dor', '?')}: '{dono}'): "
                             "uma ação, um dono; duas pessoas viram duas ações")
    return erros, avisos


def conferir_estrutura(conteudo):
    """Contrato novo compartilhado com o gerador. Legados validam só campos novos presentes.

    esquema_pesquisa:2 exige a espinha inteira; a ausência do campo mantém o formato
    anterior legível, sem fingir que uma fixture antiga oferece as análises novas.
    """
    erros = []
    def texto(v, caminho):
        if not isinstance(v, str) or not sem_tags(v).strip():
            erros.append(caminho + ": esperado texto não vazio")
    def objeto(v, caminho):
        if not isinstance(v, dict):
            erros.append(caminho + ": esperado objeto")
            return {}
        return v
    def lista(v, caminho, minimo=1, maximo=None):
        if not isinstance(v, list) or len(v) < minimo or (maximo and len(v) > maximo):
            erros.append(caminho + f": esperado lista de {minimo}" + (f" a {maximo}" if maximo else " ou mais") + " itens")
            return []
        return v
    def campos(v, nomes, caminho):
        obj = objeto(v, caminho)
        for nome in nomes:
            texto(obj.get(nome), caminho + "." + nome)
        return obj

    versao = conteudo.get("esquema_pesquisa")
    novo = versao == 2 and not isinstance(versao, bool)
    if versao is not None and not novo:
        erros.append("esquema_pesquisa: versão não suportada; use 2 ou preserve o legado sem esse campo")
    if novo:
        if not isinstance(conteudo.get("meta_declarada"), bool):
            erros.append("meta_declarada: esperado true ou false")
        if conteudo.get("tipo_comprador") not in ("B2B", "B2G", "B2C"):
            erros.append("tipo_comprador: use B2B, B2G ou B2C")
        numeros = [re.match(r"^(\d{2})\b", t.get("eyebrow", "")) for t in conteudo.get("telas", []) if not t.get("so_docx")]
        numeros = [m.group(1) for m in numeros if m]
        esperados = ["01", "02", "03", "04", "05", "06"] + (["07"] if "07" in numeros else []) + ["08"]
        if numeros != esperados:
            erros.append("telas: sequência nova exige 01–06, 07 opcional e 08, nessa ordem")
        if not any(t.get("abertura_docx") is True for t in conteudo.get("telas", [])):
            erros.append("abertura_docx: esquema 2 exige abertura explícita so_docx")
        fechos = [(t, b) for t, b in blocos(conteudo) if b.get("t") == "proximos_passos"]
        visiveis = [t for t in conteudo.get("telas", []) if not t.get("so_docx")]
        if len(fechos) != 1 or not visiveis or fechos[0][0] is not visiveis[-1]:
            erros.append("proximos_passos: exatamente um fecho na última tela apresentada")

    for i, t in enumerate(conteudo.get("telas", [])):
        cam = f"telas[{i}]"
        numero = t.get("eyebrow", "")[:2]
        exigidos = {"01": ("cenario",), "02": ("tam_compradores", "sam_compradores", "mercado_limita"),
                    "03": ("camadas",), "04": ("posicionamento", "fundamento_oferta"),
                    "06": (("comite_compra",) if conteudo.get("tipo_comprador") in ("B2B", "B2G") else ()),
                    "08": ("onde_concentrar",)}.get(numero, ()) if novo and not t.get("so_docx") else ()
        for k in exigidos:
            if k not in t:
                erros.append(cam + "." + k + ": campo obrigatório nesta tela")
        if novo and numero == "02" and not t.get("so_docx"):
            if not any(b.get("t") == "elipses" for b in t.get("blocos", [])):
                erros.append(cam + ".blocos.elipses: TAM, SAM e SOM permanecem obrigatórios")
        if "abertura_docx" in t:
            if not isinstance(t["abertura_docx"], bool) or (t["abertura_docx"] and t.get("so_docx") is not True):
                erros.append(cam + ".abertura_docx: exige booleano e so_docx:true quando ligada")
        for k, nomes, teto in (("cenario", ("fato", "fonte", "ano", "impacto"), 3), ("regulacao", ("regra", "fonte", "efeito"), None),
                               ("camadas", ("nome", "recorte", "contagem", "fonte", "papel"), None)):
            if k in t:
                for j, item in enumerate(lista(t[k], cam + "." + k, maximo=teto)):
                    campos(item, nomes, f"{cam}.{k}[{j}]")
        for k, nomes in (("tam_compradores", ("valor", "fonte")), ("sam_compradores", ("valor", "fonte")),
                          ("comite_compra", ("decide", "influencia", "usa")), ("posicionamento", ("frase", "prova", "estado")),
                          ("fundamento_oferta", ("comprador", "situacao_compra", "promessa", "diferencial", "provas", "objecoes", "proximo_passo"))):
            if k in t:
                campos(t[k], nomes, cam + "." + k)
        if "posicionamento" in t and isinstance(t["posicionamento"], dict):
            if t["posicionamento"].get("estado") not in ("dado", "hipótese sustentada", "estimativa", "premissa", "a verificar"):
                erros.append(cam + ".posicionamento.estado: use dado, hipótese sustentada, estimativa, premissa ou a verificar")
        if "leitura_meta" in t or (novo and numero == "02" and conteudo.get("meta_declarada") is True):
            texto(t.get("leitura_meta"), cam + ".leitura_meta")
        if "mercado_limita" in t:
            texto(t["mercado_limita"], cam + ".mercado_limita")
        if "onde_concentrar" in t:
            p = objeto(t["onde_concentrar"], cam + ".onde_concentrar")
            for j, criterio in enumerate(lista(p.get("criterios"), cam + ".onde_concentrar.criterios")):
                texto(criterio, f"{cam}.onde_concentrar.criterios[{j}]")
            for j, grupo in enumerate(lista(p.get("grupos"), cam + ".onde_concentrar.grupos")):
                g = campos(grupo, ("nome", "papel", "motivo"), f"{cam}.onde_concentrar.grupos[{j}]")
                if g.get("papel") not in ("base", "expansão", "possibilidade", "fora"):
                    erros.append(f"{cam}.onde_concentrar.grupos[{j}].papel: papel inválido")
            texto(p.get("por_agora_nao"), cam + ".onde_concentrar.por_agora_nao")
        for j, b in enumerate(t.get("blocos", [])):
            if b.get("t") != "proximos_passos":
                continue
            bc = f"{cam}.blocos[{j}]"
            campos(b, ("trava", "pausa", "gancho"), bc)
            acoes = lista(b.get("acoes"), bc + ".acoes", maximo=5)
            prioridades = []
            for n, acao in enumerate(acoes):
                a = campos(acao, ("acao", "dono", "prazo"), f"{bc}.acoes[{n}]")
                if not isinstance(a.get("comece_aqui"), bool):
                    erros.append(f"{bc}.acoes[{n}].comece_aqui: esperado booleano")
                if a.get("comece_aqui") is True:
                    prioridades.append(n)
                if re.search(r"\s+e\s+|,|/|\+", str(a.get("dono", ""))):
                    erros.append(f"{bc}.acoes[{n}].dono: uma ação exige um único dono")
            if prioridades != [0]:
                erros.append(bc + ".acoes.comece_aqui: exatamente uma prioridade, na primeira ação")
    return erros


# ---------------------------------------------------------------- 3. rótulo

TETO_DESC = re.compile(r"m[aá]xim|\bteto", re.I)
PAGAR = re.compile(r"\bpag(a|am|ou|aram|amos|o|os|as)\b|\bpagamento", re.I)
NEGA = re.compile(r"\b(n[aã]o|sem|nenhum|nenhuma|nunca)\b", re.I)
QUALIFICA = re.compile(r"(teto|m[aá]xim\w*)\W+(?:\w+\W+){0,2}$", re.I)


def precos_dos_dados(fonte):
    """{valor: (id, tipo, explicito)} dos dados em R$ de dados-pesquisa.json. tipo 'teto' quando o campo tipo_valor
    diz teto ou máximo (explicito=True) ou, sem o campo, quando a descrição sugere (explicito=False)."""
    arq = fonte / "dados-pesquisa.json"
    if not arq.is_file():
        return {}
    try:
        dados = json.load(io.open(arq, encoding="utf-8")).get("dados", [])
    except Exception:
        return {}
    out = {}
    for d in dados:
        val = str(d.get("valor") or "")
        vs = valores_rs(val)
        if not vs and "r$" in sem_acento(d.get("unidade", "")):
            vs = {norm_rs(m.group(0)) for m in re.finditer(NUM, val)}
        if not vs:
            continue
        tv = sem_acento(d.get("tipo_valor") or "").strip()
        if tv:
            tipo, explicito = ("teto" if ("teto" in tv or "maxim" in tv) else tv), True
        else:
            tipo, explicito = ("teto" if TETO_DESC.search(f"{d.get('dado', '')} {d.get('obs', '')}") else "?"), False
        for v in vs:
            out.setdefault(v, (d.get("id", "?"), tipo, explicito))
    return out


def conferir_rotulo(precos, conteudo):
    erros, avisos = [], []
    for onde, s in textos(conteudo):
        for frase in re.split(r"(?<=[.;!?])\s+", sem_tags(s)):
            verbo = PAGAR.search(frase)
            if not verbo:
                continue
            negada = NEGA.search(frase[:verbo.start()][-40:]) is not None
            for m in RS.finditer(frase):
                v = norm_rs(m.group(1))
                info = precos.get(v)
                if not info or info[1] != "teto":
                    continue
                if QUALIFICA.search(frase[max(0, m.start() - 40):m.start()]):
                    continue
                msg = (f"rótulo · {onde}: \"{frase.strip()[:90]}\" chama de pago R$ {v}, que é teto ou valor máximo "
                       f"({info[0]}): diga \"teto\" junto do valor ou use o preço pago")
                (erros if info[2] and not negada else avisos).append(msg)
    return erros, avisos


# ---------------------------------------------------------------- 4. mercado

HORIZONTE = re.compile(r"\b(em|at[eé]|nos pr[oó]ximos|no prazo de|dentro de)\s+\d+\s+(m[eê]s|meses|anos?)\b", re.I)


def conferir_mercado(fonte, precos, conteudo):
    erros, avisos = [], []
    linha = linha_da_ideia(fonte, "preço comparável")
    permitidos = None if linha is None else (set() if "nenhum" in sem_acento(linha) else valores_rs(linha))
    for t in conteudo.get("telas", []) or []:
        if not sem_acento(t.get("eyebrow", "")).startswith("02"):
            continue
        for b in t.get("blocos", []) or []:
            if b.get("t") != "elipses":
                continue
            for camada in b.get("camadas", []) or []:
                txt = " ".join(sem_tags(x) for x in camada[2:] if isinstance(x, str))
                usados = sorted(v for v in valores_rs(txt) if v in precos and (permitidos is None or v not in permitidos))
                if usados:
                    ids = ", ".join(precos[v][0] for v in usados)
                    if permitidos is None:
                        avisos.append(f"mercado · {camada[0]} usa R$ {', '.join(usados)}, preço de terceiro ({ids}); "
                                      "declare em ideia-central.md a linha 'Preço comparável: R$ x · por quê' (ou 'nenhum')")
                    else:
                        erros.append(f"mercado · {camada[0]} usa R$ {', '.join(usados)} ({ids}), que a linha 'Preço comparável' "
                                     "de ideia-central.md não declara: o mercado sai do preço do cliente, da contagem de compradores "
                                     "ou do preço declarado comparável")
                if sem_acento(str(camada[0])).strip() == "som":
                    tudo = " ".join(sem_tags(x) for x in camada[1:] if isinstance(x, str))
                    if not HORIZONTE.search(tudo):
                        erros.append("mercado · o SOM não diz o horizonte: escreva em quanto tempo (por exemplo, \"em 12 meses\")")
    return erros, avisos


# ---------------------------------------------------------------- 5. substituto

def conferir_substituto(fonte, conteudo):
    """Substituto é condicional; quando incluído, continua fiel à decisão registrada."""
    erros, avisos = [], []
    nova = conteudo.get("esquema_pesquisa") == 2 or any("posicionamento" in t for t in conteudo.get("telas", []))
    nn = "04" if nova else "03"
    tela = next((t for t in conteudo.get("telas", []) or [] if not t.get("so_docx") and sem_acento(t.get("eyebrow", "")).startswith(nn)), None)
    if tela is None:
        return erros, avisos
    cards = [it for b in tela.get("blocos", []) or [] if b.get("t") == "cards" for it in b.get("itens", []) or []]
    card = next((c for c in cards if sem_acento(sem_tags(c.get("tag", ""))).strip().startswith("substituto")), None)
    if card is None:
        avisos.append(f"concorrentes · a tela {nn} não tem o cartão 'Substituto': inclua apenas quando houver alternativa real documentada")
        return erros, avisos
    linha = linha_da_ideia(fonte, "substituto")
    if linha is None:
        avisos.append(f"concorrentes · ideia-central.md sem a linha 'Substituto:': o cartão da tela {nn} não foi conferido contra a decisão")
        return erros, avisos
    nome = re.split(r"\s[·—–-]\s|\(", linha, maxsplit=1)[0].strip(" *.:")
    if not nome:
        erros.append("concorrentes · a linha 'Substituto:' de ideia-central.md não tem o nome: escreva 'Substituto: <nome> · <como>'")
    elif not re.search(r"(?<![a-z0-9])" + re.escape(sem_acento(nome)) + r"(?![a-z0-9])", sem_acento(sem_tags(card.get("tag", "")))):
        erros.append(f"concorrentes · o cartão 'Substituto' da tela {nn} não traz o substituto decidido em ideia-central.md "
                     f"(\"{nome[:60]}\"); o tag do cartão é \"{sem_tags(card.get('tag', ''))[:60]}\"")
    # a comparação (tela 07) tem a coluna do substituto, e comprador não ocupa vaga de concorrente
    vagas = [sem_tags(c.get("tag", "")) for c in cards if c is not card]
    comparacao = tela if nova else next((t for t in conteudo.get("telas", []) or [] if sem_acento(t.get("eyebrow", "")).startswith("07")), None)
    cab = []
    for b in (comparacao or {}).get("blocos", []) or []:
        if b.get("t") == "tabela":
            cab = [sem_tags(c) for c in (b.get("cab") or [])[2:]]
            if nome and not any(re.search(r"(?<![a-z0-9])" + re.escape(sem_acento(nome)) + r"(?![a-z0-9])", sem_acento(c)) for c in cab):
                erros.append(f"concorrentes · a comparação da tela {nn if nova else '07'} não tem a coluna do substituto (\"{nome[:60]}\"): "
                             f"escreva \"Substituto · {nome[:40]}\" no cabeçalho")
            break
    for v in vagas + cab:
        if re.search(r"\bcomprador", sem_acento(v)) and not sem_acento(v).startswith("substituto"):
            avisos.append(f"concorrentes · \"{v[:60]}\" ocupa vaga de concorrente, mas é comprador: vai para a tela 01, como prova de demanda")
    return erros, avisos


# ---------------------------------------------------------------- 6. promessa com rótulo de prova (aviso)

PROMESSA = re.compile(r"promessa|estimativ|a provar|falta mostrar|descri[cç][aã]o d[oa]|sem caso", re.I)


def tela_por_inicio(conteudo, *inicios):
    return next((t for t in conteudo.get("telas", []) or []
                 if sem_acento(t.get("eyebrow", "")).startswith(tuple(sem_acento(i) for i in inicios))), None)


def conferir_prova_da_puv(conteudo):
    """Aviso: pilar da PUV com 'Prova:' que é promessa ou estimativa (pela B6, promessa sem prova sai da tela)."""
    avisos = []
    puv = tela_por_inicio(conteudo, "08 · proposta", "09 · proposta")
    if puv:
        for b in puv.get("blocos", []) or []:
            for card in (b.get("itens", []) or []) if b.get("t") == "cards" else []:
                for item in card.get("ul", []) or []:
                    txt = sem_tags(item).strip()
                    if sem_acento(txt).startswith("prova") and PROMESSA.search(txt):
                        avisos.append(f"rótulo · PUV, pilar \"{sem_tags(card.get('tag', ''))[:40]}\": \"{txt[:70]}\" é promessa ou "
                                      "estimativa com o rótulo 'Prova:'; promessa sem prova sai da tela e vira pendência (B6)")
    return [], avisos


# ---------------------------------------------------------------- entrada

def conferir(pasta_semana, texto_deck=""):
    """Erros e avisos da Semana 2; registro de provas obrigatório também para deck sem conteúdo estruturado."""
    fonte = Path(pasta_semana) / "_fonte"
    arq = fonte / "conteudo.json"
    if not arq.is_file():
        return conferir_provas(fonte, texto_deck)
    try:
        conteudo = json.load(io.open(arq, encoding="utf-8"))
    except Exception as ex:
        return [f"conteudo.json não abre como JSON: {ex}"], []
    return conferir_conteudo(pasta_semana, conteudo, texto_deck)


def conferir_conteudo(pasta_semana, conteudo, texto_deck=""):
    """Confere o conteúdo efetivamente gerado, sem substituir o JSON canônico do cliente."""
    fonte = Path(pasta_semana) / "_fonte"
    if not isinstance(conteudo, dict):
        return ["conteúdo da pesquisa precisa ser objeto JSON"], []
    precos = precos_dos_dados(fonte)
    erros, avisos = conferir_estrutura(conteudo), []
    for e, a in (conferir_provas(fonte, texto_deck, conteudo), conferir_plano(conteudo),
                 conferir_rotulo(precos, conteudo), conferir_mercado(fonte, precos, conteudo),
                 conferir_substituto(fonte, conteudo), conferir_prova_da_puv(conteudo)):
        erros += e
        avisos += a
    return erros, avisos


def main(argv):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    if len(argv) != 1:
        print(__doc__)
        return 2
    alvo = Path(argv[0])
    if alvo.is_file():
        pasta, deck = alvo.parent, alvo
    else:
        pasta = alvo
        deck = next(iter(sorted(alvo.glob("pesquisa-mercado-*.html"))), None)
    txt = texto_visivel(io.open(deck, encoding="utf-8").read()) if deck else ""
    erros, avisos = conferir(pasta, txt)
    print(f"Conferência da pesquisa · {pasta}")
    for e in erros:
        print("  ERRO  ", e)
    for a in avisos:
        print("  AVISO ", a)
    if not erros and not avisos:
        print("  OK, nenhum problema encontrado.")
    return 1 if erros else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
