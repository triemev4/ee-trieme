"""Limpa uma transcrição, aplica o Glossário da ficha e a fatia em blocos por assunto, para leitura barata.

Uso:
    python fatiar_transcricao.py <transcrição> --ficha <ficha.md> [--semana N] [--assunto "Nome: palavra, palavra"]
                                 [--saida <pasta _texto>] [--minutos-min 2] [--minutos-max 8] [--chars-max 9000]
                                 [--pausa 20] [--limiar 0.5]

Entrada: texto com carimbo de tempo, em qualquer destes formatos (detectado sozinho):
  Whisper `[00:01:39] fala` ou `[00:01:39 --> 00:01:41] fala`; SRT e VTT (`00:00:01,000 --> 00:00:03,000`, com `<v Nome>`);
  Google Meet e Gemini (linha só com `00:01:39`, depois `Nome: fala`); tl;dv e Zoom (`Nome 00:01:39`, fala na linha de baixo,
  ou `00:01:39 Nome: fala`). Sem carimbo, vale a posição (linha e percentual do arquivo) e o índice diz isso.
DOCX e PDF: rode antes `extrair_insumos.py` e passe o `.txt` de `_texto/`.

Grava em `<pasta do arquivo>/_texto/<nome>.blocos/` (ou em `--saida`, que faz o papel de `_texto`):
  - `bloco-NN.md`: um por assunto, com o cabeçalho `[arquivo · bloco N de M · hh:mm:ss a hh:mm:ss]` e parágrafos
    com o carimbo de início (`[hh:mm:ss] Nome: fala`);
  - `indice.md`: bloco, minutos, assunto provável, palavras-chave, falantes (se houver) e como a leitura deve seguir.
Os guias leem o índice e abrem só os blocos pertinentes, nunca a transcrição inteira.

Limpeza: interjeição solta (aham, hum), ruído entre colchetes ([Música]) e fala repetida 3 vezes ou mais em sequência
saem; o índice conta o que saiu. Glossário: a seção `## Glossário` da ficha (grafia errada em uma ou mais variantes
separadas por vírgula, termo certo na segunda coluna; o que vem depois de "(" ou "," no termo certo é explicação e não
entra no texto). A troca vale para palavra inteira, sem diferenciar maiúscula.

Divisão por assunto, por regras simples e sem modelo: queda de coesão de vocabulário entre a janela antes e depois (estilo
TextTiling), mudança do tema dominante (temas gerais da EE e, com `--semana`, os da pauta do esqueleto da semana),
pergunta que abre assunto, pausa longa e marcador de transição ("vamos falar de", "outro ponto"). O tamanho do bloco fica
entre `--minutos-min` e `--minutos-max` (e `--chars-max`). O assunto de cada bloco é pista por palavra-chave, não verdade.

Só biblioteca padrão. Código de saída 0 se gravou; 2 se não deu para ler a transcrição.
"""
import sys
sys.dont_write_bytecode = True
import argparse, math, re, unicodedata
from collections import Counter
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

RAIZ = Path(__file__).resolve().parent.parent
CHARS_POR_SEG = 14          # velocidade de fala usada só para estimar o fim de uma fala sem carimbo de fim
PARAGRAFO_CHARS = 380       # parágrafo fecha ao passar disso, no fim de uma frase
JANELA_CHARS = 1500         # janela de coesão de cada lado do ponto de corte (cerca de 1 min e meio)
MIN_PALAVRAS_PERGUNTA = 4

TS = r"(?<![\d:])(\d{1,2}):(\d{2})(?::(\d{2}))?(?:[.,]\d{1,3})?(?![\d:])"
RE_TS = re.compile(TS)
SEP = "(?:-->|-|" + chr(0x2013) + "|a)"   # hífen ou traço entre dois carimbos
RE_CUE = re.compile(rf"^\s*{TS}\s*-->\s*{TS}")
RE_COLCHETE = re.compile(rf"^\s*[\[(]\s*{TS}(?:\s*{SEP}\s*{TS})?\s*[\])]\s*(.*)$")
RE_SO_TS = re.compile(rf"^\s*[\[(]?\s*{TS}\s*[\])]?\s*$")
RE_FALANTE_TS = re.compile(rf"^\s*([^\W\d_][^:\[\]()\d]{{1,40}}?)\s+[\[(]?\s*{TS}\s*[\])]?\s*$")
RE_PREFIXO = re.compile(rf"^\s*{TS}\s*[-:]?\s+(\S.*)$")
RE_FALA_NOME = re.compile(r"^([A-ZÀ-Ý][\w.'’ -]{0,38}?):\s+(\S.*)$")
RE_ORIGEM_PDF = re.compile(r"^\[[^\]]*(?:·|\.(?:txt|md|docx|pdf|vtt|srt))[^\]]*\]$", re.I)   # cabeçalho [arquivo] do extrair_insumos
RE_RUIDO = re.compile(r"^\[?\(?\s*(música|musica|music|aplausos|applause|risos|laughter|silêncio|silencio|inaudível|inaudivel|ruído|ruido)\s*\)?\]?\.?$", re.I)
INTERJEICOES = {"aham", "ahã", "aha", "uhum", "uhm", "uhn", "hum", "hmm", "hm", "ahn", "ãh", "ã", "éh", "eh", "ah", "uh", "oh"}


def norm(s):
    s = unicodedata.normalize("NFD", s.lower())
    return "".join(c for c in s if unicodedata.category(c) != "Mn")


def seg_ts(h_ou_m, m_ou_s, s):
    """Grupos do TS: `hh:mm:ss` (3 grupos) ou `mm:ss` (2 grupos)."""
    if s is None:
        return int(h_ou_m) * 60 + int(m_ou_s)
    return int(h_ou_m) * 3600 + int(m_ou_s) * 60 + int(s)


def fmt_ts(seg):
    seg = int(max(0, seg))
    return f"{seg // 3600:02d}:{seg % 3600 // 60:02d}:{seg % 60:02d}"


def fmt_min(seg):
    return f"{seg / 60:.1f}".replace(".", ",")


# ---------------------------------------------------------------- leitura

class Seg:
    __slots__ = ("t", "fim", "falante", "texto", "linha", "apos_vazia")

    def __init__(self, t, texto, linha, falante=None, fim=None, apos_vazia=False):
        self.t, self.texto, self.linha, self.falante, self.fim, self.apos_vazia = t, texto, linha, falante, fim, apos_vazia


def ler_texto(caminho):
    bruto = caminho.read_bytes()
    for cod in ("utf-8-sig", "cp1252"):
        try:
            return bruto.decode(cod)
        except UnicodeDecodeError:
            continue
    return bruto.decode("utf-8", errors="replace")


def detectar_formato(linhas):
    cont = Counter()
    nao_vazias = 0
    for l in linhas:
        if not l.strip():
            continue
        nao_vazias += 1
        if RE_CUE.match(l):
            cont["cue"] += 1
        elif RE_COLCHETE.match(l):
            cont["colchete"] += 1
        elif RE_SO_TS.match(l):
            cont["so_carimbo"] += 1
        elif RE_FALANTE_TS.match(l):
            cont["falante_carimbo"] += 1
        elif RE_PREFIXO.match(l):
            cont["prefixo"] += 1
    ordem = ["cue", "colchete", "so_carimbo", "falante_carimbo", "prefixo"]
    minimo = max(3, int(nao_vazias * 0.03))
    melhor = max(ordem, key=lambda f: (cont[f], -ordem.index(f)))
    return melhor if cont[melhor] >= minimo else "sem_carimbo"


def limpa_tags(t):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", t)).strip()


def segmentos(texto):
    """Lista de Seg e o nome do formato. Linha antes do primeiro carimbo (cabeçalho do arquivo) é ignorada."""
    linhas = texto.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    formato = detectar_formato(linhas)
    out = []
    ignoradas = 0

    def junta(texto_novo, n):
        if out and texto_novo:
            out[-1].texto = (out[-1].texto + " " + texto_novo).strip()
        return None

    if formato == "cue":
        i = 0
        while i < len(linhas):
            m = RE_CUE.match(linhas[i])
            if not m:
                i += 1
                continue
            g = m.groups()
            ini, fim = seg_ts(*g[0:3]), seg_ts(*g[3:6])
            j, partes = i + 1, []
            while j < len(linhas) and linhas[j].strip():
                partes.append(linhas[j].strip())
                j += 1
            fala = limpa_tags(" ".join(partes))
            nome = None
            mv = re.search(r"<v\s+([^>]+)>", " ".join(partes))
            if mv:
                nome = mv.group(1).strip()
            if fala:
                out.append(Seg(ini, fala, i + 1, nome, fim))
            i = j
        return out, formato, ignoradas

    if formato in ("colchete", "prefixo"):
        rx = RE_COLCHETE if formato == "colchete" else RE_PREFIXO
        for n, l in enumerate(linhas, 1):
            if not l.strip():
                continue
            m = rx.match(l)
            if m:
                g = m.groups()
                if formato == "colchete":
                    ini = seg_ts(*g[0:3])
                    fim = seg_ts(*g[3:6]) if g[3] else None
                    fala = g[6]
                else:
                    ini, fim, fala = seg_ts(*g[0:3]), None, g[3]
                out.append(Seg(ini, fala.strip(), n, None, fim))
            elif out:
                junta(l.strip(), n)
            else:
                ignoradas += 1
        return out, formato, ignoradas

    if formato in ("so_carimbo", "falante_carimbo"):
        atual = None
        for n, l in enumerate(linhas, 1):
            if not l.strip():
                continue
            m_ts = RE_SO_TS.match(l)
            m_fa = RE_FALANTE_TS.match(l) if formato == "falante_carimbo" else None
            if m_ts or m_fa:
                if m_ts:
                    g, nome = m_ts.groups(), None
                else:
                    g, nome = m_fa.groups()[1:4], m_fa.group(1).strip()
                atual = Seg(seg_ts(*g[0:3]), "", n, nome)
                out.append(atual)
            elif atual is not None:
                atual.texto = (atual.texto + " " + l.strip()).strip()
            else:
                ignoradas += 1
        return [s for s in out if s.texto], formato, ignoradas

    anterior_vazia = False
    for n, l in enumerate(linhas, 1):
        if not l.strip():
            anterior_vazia = True
            continue
        out.append(Seg(None, l.strip(), n, None, None, anterior_vazia))
        anterior_vazia = False
    return out, "sem_carimbo", ignoradas


NOME_PROPRIO = re.compile(r"^(?:[A-ZÀ-Ý][\w.'’-]*|d[aeo]s?|e|van|von)(?: (?:[A-ZÀ-Ý][\w.'’-]*|d[aeo]s?|e|van|von)){0,3}$")


def extrai_falantes(segs):
    """`Nome: fala`. Só vira falante o que parece nome (até 4 palavras, iniciais maiúsculas), se repete (3 vezes ou mais),
    há ao menos 2 nomes e eles cobrem metade das falas: "Resumindo: ..." e "O funil tem 4 etapas: ..." não são pessoas."""
    cand = Counter()
    for s in segs:
        if s.falante is None:
            m = RE_FALA_NOME.match(s.texto)
            if m and NOME_PROPRIO.match(m.group(1).strip()):
                cand[m.group(1).strip()] += 1
    validos = {n for n, c in cand.items() if c >= 3}
    if len(validos) > 12:
        validos = {n for n, _ in cand.most_common(12)}
    if len(validos) < 2 or sum(cand[n] for n in validos) < 0.5 * len(segs):
        return sorted({s.falante for s in segs if s.falante})
    for s in segs:
        if s.falante is None:
            m = RE_FALA_NOME.match(s.texto)
            if m and m.group(1).strip() in validos:
                s.falante, s.texto = m.group(1).strip(), m.group(2).strip()
    return sorted(validos)


def limpar(segs):
    """Tira ruído, interjeição solta e repetição em laço (3 ou mais iguais em sequência). Devolve a lista e as contagens."""
    cont = Counter()
    saida = []
    for s in segs:
        s.texto = re.sub(r"\s+", " ", s.texto.replace(" ", " ").replace("​", "").replace("﻿", "")).strip()
        if not s.texto:
            continue
        if RE_RUIDO.match(s.texto):
            cont["ruido"] += 1
            continue
        palavra = re.sub(r"[^\wãõé]", "", s.texto.lower())
        if palavra in INTERJEICOES and len(s.texto) <= 8:
            cont["interjeicao"] += 1
            continue
        saida.append(s)
    final, i = [], 0
    while i < len(saida):
        j = i
        while j + 1 < len(saida) and norm(saida[j + 1].texto) == norm(saida[i].texto) and saida[j + 1].falante == saida[i].falante:
            j += 1
        if j - i + 1 >= 3:
            cont["laco"] += j - i
            final.append(saida[i])
        else:
            final.extend(saida[i:j + 1])
        i = j + 1
    return final, cont


# ---------------------------------------------------------------- glossário

def le_glossario(ficha):
    """[(variantes, termo)] da seção Glossário da ficha. Linha de exemplo vazia é ignorada."""
    if not ficha:
        return []
    linhas = ler_texto(ficha).splitlines()
    dentro, pares = False, []
    for l in linhas:
        if re.match(r"^#{1,6}\s", l):
            dentro = norm(l).lstrip("# ").startswith("glossario")
            continue
        if not dentro or not l.strip().startswith("|"):
            continue
        celulas = [c.strip() for c in l.strip().strip("|").split("|")]
        if len(celulas) < 2 or re.fullmatch(r"[-: ]+", celulas[0] or "-") or norm(celulas[0]).startswith("grafia"):
            continue
        errado, certo = celulas[0], celulas[1]
        if not errado or not certo:
            continue
        certo = re.split(r"\s\(|,", certo, maxsplit=1)[0].strip().strip("*`\"'")
        variantes = [v.strip().strip("*`\"'") for v in re.split(r"[,;]", errado)]
        variantes = [v for v in variantes if v and norm(v) != norm(certo)]
        if certo and variantes:
            pares.append((variantes, certo))
    return pares


def compila_glossario(pares):
    mapa = {}
    for variantes, certo in pares:
        for v in variantes:
            mapa[norm(v)] = (v, certo)
    if not mapa:
        return None, mapa
    alts = sorted((v for v, _ in mapa.values()), key=len, reverse=True)
    corpo = "|".join(r"\s+".join(re.escape(p) for p in a.split()) for a in alts)
    return re.compile(rf"(?<!\w)(?:{corpo})(?!\w)", re.I), mapa


def aplica_glossario(rx, mapa, texto, contagem):
    if rx is None:
        return texto

    def troca(m):
        chave = norm(re.sub(r"\s+", " ", m.group(0)))
        achado = mapa.get(chave)
        if not achado:
            return m.group(0)
        contagem[achado[1]] += 1
        return achado[1]
    return rx.sub(troca, texto)


# ---------------------------------------------------------------- vocabulário

STOP = set("""
a o as os um uma uns umas de do da dos das em no na nos nas por para pra pro com sem sobre entre até ate ao aos à às
e ou mas se que quem qual quais como quando onde porque porquê pois então entao assim aí ai aqui ali lá la ainda já ja
também tambem só so mais menos muito muita muitos muitas pouco pouca bem mal tudo nada algo alguém ninguém cada todo toda
todos todas outro outra outros outras mesmo mesma esse essa esses essas este esta estes estas isso isto aquilo aquele aquela
eu tu ele ela nós nos vocês voces você voce eles elas meu minha meus minhas seu sua seus suas dele dela deles delas nosso nossa
sou é era eram foi são sao ser está esta estão estao estava estavam estou estamos tem têm tinha tinham tenho temos ter teve
vai vão vao vou vamos ir indo fui foram fazer faz fazem fazendo feito fiz fez fica ficar ficou fico pode podem posso podemos
poder podia dá da dar deu dou sei sabe sabem saber acho achar acha né ne tipo gente coisa coisas ótimo otimo ok tá ta certo
sim não nao agora hoje ontem sempre nunca depois antes ainda tão tao quanto quantos quantas tanto aí então
falar fala falei falou falando disse dizer diz conta contar olha olhar vê ver vi viu vimos queria quero quer querem
uhum aham tava tavam bora acerca eh show top tranquilo bacana fantástico fantastico exatamente realmente claro perfeito entendi entendo
vez vezes lado parte forma jeito maneira ponto gente pessoal beleza bom boa bons boas dia tarde noite obrigado obrigada
""".split())

# temas gerais da EE; palavra curta (3 letras ou menos) vale como palavra inteira, as outras como começo de palavra
TEMAS = {
    "Abertura e apresentações": ["boa tarde", "bom dia", "boa noite", "prazer", "tudo bem", "tudo bom", "tudo joia", "apresent", "bem-vind", "obrigad"],
    "Histórico e contexto da empresa": ["histori", "trajetori", "começou", "comecou", "fundad", "fundou", "nasceu", "anos de", "surgiu", "origem", "sociedade", "sócio", "socio"],
    "Dores e desafios": ["dor ", "dores", "problema", "dificuldade", "desafio", "gargalo", "trava", "não consegu", "nao consegu", "reclam", "perde", "perdemos"],
    "Meta e resultado esperado": ["meta", "objetivo", "faturamento", "receita", "crescer", "crescimento", "expectativ", "resultado", "projeç", "projec", "sucesso", "ambição", "ambicao"],
    "Produto, preço e oferta": ["preço", "preco", "valor", "ticket", "plano", "pacote", "produto", "serviço", "servico", "margem", "desconto", "tabela", "mensalidade", "contrato de", "oferta", "per capita"],
    "Público e cliente ideal": ["público", "publico", "perfil", "persona", "segmento", "nicho", "idade", "região", "regiao", "cliente ideal", "paciente", "empresa que", "decisor"],
    "Concorrência e mercado": ["concorr", "mercado", "diferencial", "posicionament", "referência", "referencia", "licitaç", "licitac", "benchmark", "tamanho do"],
    "Marketing e canais": ["anúncio", "anuncio", "mídia", "midia", "tráfego", "trafego", "instagram", "google", "facebook", "meta ads", "site", "seo", "campanha", "lead", "investimento em", "canal", "conteúdo", "conteudo", "rede social", "redes sociais", "influenci", "whatsapp", "landing", "pixel", "analytics", "tag manager"],
    "Comercial e vendas": ["venda", "vendedor", "closer", "sdr", "crm", "funil", "proposta", "fechamento", "follow", "pipeline", "comercial", "conversão", "conversao", "negociaç", "negociac", "reunião de venda", "prospecç", "prospecc", "cold", "outbound", "inbound", "agendad"],
    "Equipe e estrutura": ["equipe", "time ", "funcionári", "funcionari", "contrat", "gestão", "gestao", "processo", "operaç", "operac", "capacidade", "atendiment", "colaborador", "cargo", "organograma", "treinament"],
    "Contrato, escopo e próximos passos": ["escopo", "entregável", "entregavel", "prazo", "cronograma", "encontro", "semana", "kickoff", "kick-off", "acesso", "insumo", "documento", "próximo passo", "proximo passo", "agenda", "gravaç", "gravac"],
}

MARCADORES = ["vamos falar", "vamos para", "vamos passar", "vamos ver", "passando para", "passando pra", "proximo assunto", "proximo ponto",
              "proximo bloco", "agora vamos", "mudando de assunto", "outro ponto", "outro assunto", "falando em", "queria falar", "queria entender",
              "vou te perguntar", "pergunta para", "primeiro bloco", "segundo bloco", "terceiro bloco", "ultimo bloco", "sobre o tema", "partindo para"]
PERGUNTA_INI = ("como ", "qual ", "quais ", "quanto ", "quantos ", "quantas ", "onde ", "quando ", "por que", "o que ", "que tipo",
                "me conta", "me fala", "me explica", "conta pra", "e sobre", "e quanto", "e como", "e qual")

_GEN_TELA = {"roteiro", "reuniao", "perguntas", "passos", "mapeamos", "kickoff", "semana", "reais", "capa", "ponte", "fechamento", "trava", "plano", "proximos", "estrutura", "entre", "encontros", "deste", "encontro", "acao", "sobre", "como"}


def tema_regex(kws):
    partes = []
    for k in kws:
        k = norm(k)
        e = re.escape(k).replace(r"\ ", " ")
        partes.append(rf"\b{e}\b" if len(k.strip()) <= 3 else rf"\b{e}")
    return re.compile("|".join(partes))


def temas_do_esqueleto(semana):
    """Temas extras: títulos das telas da tabela do esqueleto da semana (cada título vira um tema)."""
    pasta = RAIZ / "skills" / "estruturacao-estrategica" / "esqueleto"
    achados = sorted(pasta.glob(f"semana-{semana}-*.md"))
    if not achados:
        return {}, f"esqueleto da semana {semana} não encontrado em {pasta.name}; seguindo só com os temas gerais"
    extra = {}
    for l in ler_texto(achados[0]).splitlines():
        m = re.match(r"^\|\s*\d+\s*\|\s*([^|]+?)\s*\|", l)
        if not m:
            continue
        titulo = re.sub(r"`[^`]*`", "", m.group(1)).strip()
        limpo = re.sub(r"^\d+\s*·\s*", "", titulo)
        siglas = [s for s in re.findall(r"\(([A-Za-zÀ-ú]{2,6})\)", limpo)]
        palavras = [w for w in re.findall(r"[A-Za-zÀ-ú]{5,}", re.sub(r"\([^)]*\)", "", limpo)) if norm(w) not in _GEN_TELA and norm(w) not in STOP]
        if not palavras and not siglas:
            continue
        rotulo = re.sub(r"\s*\([^)]*\)", "", limpo).strip() or limpo
        extra[f"Pauta S{semana}: {rotulo}"] = [*palavras, *siglas]
    return extra, ""


# ---------------------------------------------------------------- parágrafos

def eh_pergunta_ini(texto):
    n = norm(texto)
    primeira = re.split(r"(?<=[.!?])\s+", n)[0]
    if len(n.split()) < MIN_PALAVRAS_PERGUNTA:
        return False
    return primeira.rstrip().endswith("?") or n.startswith(PERGUNTA_INI)


class Par:
    __slots__ = ("t", "fim", "falante", "texto", "linha", "chars", "pergunta", "marcador", "pausa", "troca", "stems", "temas")


def montar_paragrafos(segs, com_tempo, pausa_s):
    pars, atual = [], None
    prev = None
    for s in segs:
        gap = 0.0
        if com_tempo and prev is not None:
            fim_prev = prev.fim if prev.fim is not None else prev.t + max(1.5, len(prev.texto) / CHARS_POR_SEG)
            gap = max(0.0, s.t - fim_prev)
        elif prev is not None and s.apos_vazia:
            gap = pausa_s * 0.6
        troca = prev is not None and s.falante != prev.falante
        prev_fechou = prev is None or re.search(r"[.!?…]\s*$", prev.texto) is not None
        perg_ini = eh_pergunta_ini(s.texto) and not (prev and eh_pergunta_ini(prev.texto)) and prev_fechou
        fecha_frase = atual is not None and re.search(r"[.!?…]$", atual.texto.strip())
        quebra = (atual is None or troca or gap >= pausa_s / 2 or perg_ini or (len(atual.texto) >= PARAGRAFO_CHARS and fecha_frase)
                  or (len(atual.texto) >= PARAGRAFO_CHARS * 2))
        if quebra:
            atual = Par()
            atual.t, atual.fim, atual.falante, atual.texto, atual.linha = s.t, None, s.falante, s.texto, s.linha
            atual.pausa = gap
            atual.troca = troca
            pars.append(atual)
        else:
            atual.texto += " " + s.texto
        atual.fim = s.fim if s.fim is not None else (s.t + max(1.5, len(s.texto) / CHARS_POR_SEG) if s.t is not None else None)
        prev = s
    return pars


# ---------------------------------------------------------------- pontuação dos cortes

def radical(w):
    return w[:6]


def palavras_conteudo(texto):
    return [radical(w) for w in re.findall(r"[a-z0-9]{4,}", norm(texto)) if w not in STOP and not w.isdigit()]


def cosseno(a, b):
    if not a or not b:
        return None
    if len(a) > len(b):
        a, b = b, a
    dot = sum(v * b.get(k, 0) for k, v in a.items())
    na = math.sqrt(sum(v * v for v in a.values()))
    nb = math.sqrt(sum(v * v for v in b.values()))
    return dot / (na * nb) if na and nb else None


def percentil(vals, p):
    if not vals:
        return 0.0
    v = sorted(vals)
    return v[min(len(v) - 1, int(p * (len(v) - 1) + 0.5))]


def pontuar(pars, temas_rx, pausa_s):
    """score[i] = força de um corte antes do parágrafo i (i de 1 a n-1)."""
    n = len(pars)
    nomes = list(temas_rx)
    acum = [0]
    for p in pars:
        p.stems = Counter(palavras_conteudo(p.texto))
        nt = norm(p.texto)
        p.temas = Counter({t: len(rx.findall(nt)) * (2 if t.startswith("Pauta S") else 1) for t, rx in temas_rx.items() if rx.search(nt)})
        p.chars = len(p.texto) + 14 + (len(p.falante) + 2 if p.falante else 0)      # com o carimbo e o nome, como vai para o arquivo
        p.pergunta = eh_pergunta_ini(p.texto)
        p.marcador = any(m in nt[:120] for m in MARCADORES)
        acum.append(acum[-1] + p.chars)

    def janela(i, lado):
        if lado < 0:
            j = i
            while j > 0 and acum[i] - acum[j - 1] <= JANELA_CHARS:
                j -= 1
            return range(max(j, 0), i)
        j = i
        while j < n and acum[j + 1] - acum[i] <= JANELA_CHARS:
            j += 1
        return range(i, min(max(j, i + 1), n))

    coes, tema_cos = [None] * n, [None] * n
    for i in range(1, n):
        esq, dir_ = Counter(), Counter()
        te, td = Counter(), Counter()
        for k in janela(i, -1):
            esq.update(pars[k].stems)
            te.update(pars[k].temas)
        for k in janela(i, +1):
            dir_.update(pars[k].stems)
            td.update(pars[k].temas)
        coes[i] = cosseno(esq, dir_)
        tema_cos[i] = cosseno(te, td)

    # profundidade do vale de coesão (TextTiling)
    base = [c if c is not None else 0.5 for c in coes]
    prof = [0.0] * n
    for i in range(1, n):
        e = i
        while e > 1 and base[e - 1] >= base[e]:
            e -= 1
        d = i
        while d < n - 1 and base[d + 1] >= base[d]:
            d += 1
        prof[i] = (base[e] - base[i]) + (base[d] - base[i])
    ref = percentil([x for x in prof[1:] if x > 0], 0.9) or 1.0

    score = [0.0] * n
    for i in range(1, n):
        lex = min(1.0, prof[i] / ref)
        tema = 0.0 if tema_cos[i] is None else (1 - tema_cos[i])
        pausa = 0.0 if pars[i].pausa < pausa_s / 2 else min(1.0, pars[i].pausa / pausa_s)
        s = 0.40 * lex + 0.20 * tema + 0.20 * (1.0 if pars[i].pergunta else 0.0) + 0.20 * pausa + 0.25 * (1.0 if pars[i].marcador else 0.0)
        s += 0.05 if pars[i].troca else 0.0
        if not re.search(r"[.!?…]\s*$", pars[i - 1].texto):      # cortar no meio de uma frase é pior
            s -= 0.25
        score[i] = s
    return score


def escolher_cortes(pars, score, com_tempo, min_s, max_s, chars_min, chars_max, limiar):
    n = len(pars)

    def tam_s(a, b):                        # segundos do parágrafo a até o início do b
        t0 = pars[a].t
        t1 = pars[b].t if b < n else (pars[n - 1].fim or pars[n - 1].t)
        return t1 - t0

    def tam_c(a, b):
        return sum(p.chars for p in pars[a:b])

    def cabe_min(a, b):
        return tam_c(a, b) >= chars_min and (not com_tempo or tam_s(a, b) >= min_s)

    def passou_max(a, b):
        return tam_c(a, b) > chars_max or (com_tempo and tam_s(a, b) > max_s)

    K = 12
    picos = [i for i in range(1, n) if score[i] >= limiar and score[i] >= max(score[max(1, i - K):i + K + 1])]
    cortes, ini = [], 0
    while ini < n:
        j = ini + 1
        while j < n and not cabe_min(ini, j):
            j += 1
        if j >= n:
            break
        k = j
        while k + 1 < n and not passou_max(ini, k + 1):
            k += 1
        cand = [p for p in picos if j <= p <= k]
        if cand:                            # primeiro pico forte depois do mínimo
            corte = cand[0]
        elif passou_max(ini, n):            # sem pico e já estourou o máximo: corta no ponto mais fraco de coesão
            corte = max(range(j, k + 1), key=lambda x: score[x])
        else:
            break
        cortes.append(corte)
        ini = corte
    if cortes and not cabe_min(cortes[-1], n):   # sobra final pequena demais volta para o bloco anterior
        cortes.pop()
    return cortes


# ---------------------------------------------------------------- saída

def rotular(temas_bloco, minimo=3):
    if not temas_bloco:
        return "sem tema claro (veja as palavras-chave)"
    ordem = temas_bloco.most_common(2)
    if ordem[0][1] < minimo:
        return "sem tema claro (veja as palavras-chave)"
    rot = [ordem[0][0]]
    if len(ordem) > 1 and ordem[1][1] >= max(minimo, ordem[0][1] * 0.6):
        rot.append(ordem[1][0])
    return "; ".join(rot)


def palavras_chave(blocos_stems, blocos_formas, i, n=6):
    df = Counter()
    for st in blocos_stems:
        df.update(set(st))
    total = len(blocos_stems)
    pontos = {}
    for r, c in blocos_stems[i].items():
        if c < 2:
            continue
        pontos[r] = c * math.log((1 + total) / (1 + df[r])) + (0.001 * c)
    top = sorted(pontos, key=lambda r: -pontos[r])[:n]
    return [blocos_formas[i][r].most_common(1)[0][0] for r in top]


def escreve(pars, cortes, nome_arq, saida, com_tempo, formato, falantes, rx_t, extra_info):
    inicios = [0, *cortes]
    fins = [*cortes, len(pars)]
    nb = len(inicios)
    blocos = [pars[a:b] for a, b in zip(inicios, fins)]
    stems = [Counter(r for p in b for r in p.stems.elements()) for b in blocos]
    formas = []
    for b in blocos:
        f = {}
        for p in b:
            for w in re.findall(r"[A-Za-zÀ-ÿ0-9]{4,}", p.texto):
                nw = norm(w)
                if nw in STOP:
                    continue
                f.setdefault(radical(nw), Counter())[w] += 1
        formas.append(f)

    pasta = saida / f"{Path(nome_arq).stem}.blocos"
    pasta.mkdir(parents=True, exist_ok=True)
    for velho in list(pasta.glob("bloco-*.md")) + list(pasta.glob("indice.md")):
        velho.unlink()

    total_linhas = max(p.linha for p in pars) or 1
    linhas_ind = []
    tamanhos = []
    for i, b in enumerate(blocos):
        ini_t = b[0].t
        fim_t = pars[fins[i]].t if fins[i] < len(pars) else (b[-1].fim or b[-1].t)
        if com_tempo:
            rot = f"{fmt_ts(ini_t)} a {fmt_ts(fim_t)}"
            minutos = f"{fmt_ts(ini_t)} a {fmt_ts(fim_t)} ({fmt_min(fim_t - ini_t)} min)"
        else:
            a, z = b[0].linha, max(p.linha for p in b)
            rot = f"linhas {a} a {z}"
            minutos = f"linhas {a} a {z} ({round(100 * a / total_linhas)}% a {round(100 * z / total_linhas)}%)"
        temas_b = Counter()
        for p in b:
            temas_b.update(p.temas)
        assunto = rotular(temas_b)
        chaves = palavras_chave(stems, formas, i)
        charsb = sum(len(p.texto) for p in b)
        tamanhos.append((charsb, (fim_t - ini_t) if com_tempo else None))
        fal = Counter()
        for p in b:
            if p.falante:
                fal[p.falante] += len(p.texto)
        abertura = re.sub(r"\s+", " ", b[0].texto)[:90].rstrip()
        linhas_ind.append((i + 1, minutos, assunto, ", ".join(chaves), ", ".join(n for n, _ in fal.most_common(4)), charsb, abertura))

        corpo = [f"[{nome_arq} · bloco {i + 1} de {nb} · {rot}]", ""]
        for p in b:
            marca = f"[{fmt_ts(p.t)}]" if com_tempo else f"[linha {p.linha}]"
            quem = f"{p.falante}: " if p.falante else ""
            corpo.append(f"{marca} {quem}{p.texto}")
            corpo.append("")
        (pasta / f"bloco-{i + 1:02d}.md").write_text("\n".join(corpo).rstrip() + "\n", encoding="utf-8")

    ind = [f"# Índice da transcrição {nome_arq}", "",
           f"Blocos: {nb}. Leia esta tabela e abra só o `bloco-NN.md` que tratar do assunto; não leia a transcrição inteira. "
           "O assunto é pista por palavra-chave (regra simples, sem modelo): confirme no bloco. Cite o carimbo do parágrafo."
           if com_tempo else
           f"Blocos: {nb}. Leia esta tabela e abra só o `bloco-NN.md` que tratar do assunto; não leia a transcrição inteira. "
           "O assunto é pista por palavra-chave (regra simples, sem modelo): confirme no bloco.", ""]
    ind += extra_info
    if not com_tempo:
        ind.append("**Sem carimbo de tempo:** as posições abaixo são linhas do arquivo e percentual do texto, não minutos.")
    if not falantes:
        ind.append("Sem separação de falantes na transcrição (a coluna de falantes não aparece).")
    ind.append("")
    cab = "| Bloco | " + ("Minutos" if com_tempo else "Posição") + " | Assunto provável | Palavras-chave | " + ("Falantes | " if falantes else "") + "Caracteres | Abre com |"
    ind += [cab, "|" + "---|" * (cab.count("|") - 1)]
    for num, mins, assunto, chaves, fal, charsb, abertura in linhas_ind:
        arq = f"[bloco-{num:02d}](bloco-{num:02d}.md)"
        cel_fal = f" {fal} |" if falantes else ""
        ind.append(f"| {arq} | {mins} | {assunto} | {chaves} |{cel_fal} {charsb} | {abertura.replace('|', '/')} |")
    (pasta / "indice.md").write_text("\n".join(ind) + "\n", encoding="utf-8")
    return pasta, nb, tamanhos


def main():
    ap = argparse.ArgumentParser(description="Limpa a transcrição, aplica o Glossário da ficha e fatia em blocos por assunto.")
    ap.add_argument("transcricao")
    ap.add_argument("--ficha", help="ficha do cliente (seção Glossário)")
    ap.add_argument("--semana", type=int, choices=range(1, 6), help="semana do encontro: usa a pauta do esqueleto como temas")
    ap.add_argument("--assunto", action="append", default=[], help='tema extra, "Nome: palavra, palavra" (repetível)')
    ap.add_argument("--saida", help="pasta que faz o papel de _texto (padrão: _texto ao lado da transcrição)")
    ap.add_argument("--minutos-min", type=float, default=2.0)
    ap.add_argument("--minutos-max", type=float, default=8.0)
    ap.add_argument("--chars-max", type=int, default=9000)
    ap.add_argument("--chars-min", type=int, default=900)
    ap.add_argument("--pausa", type=float, default=20.0, help="segundos de silêncio que contam como pausa longa")
    ap.add_argument("--limiar", type=float, default=0.5, help="força mínima de um corte (0 a 1,5)")
    a = ap.parse_args()

    arq = Path(a.transcricao)
    if not arq.is_file():
        print(f"Não achei a transcrição: {arq}", file=sys.stderr)
        return 2
    if arq.suffix.lower() in (".docx", ".pdf"):
        print("DOCX e PDF não são lidos aqui: rode extrair_insumos.py e passe o .txt de _texto/.", file=sys.stderr)
        return 2
    saida = Path(a.saida) if a.saida else (arq.parent if arq.parent.name == "_texto" else arq.parent / "_texto")

    texto = "\n".join(l for l in ler_texto(arq).splitlines() if not RE_ORIGEM_PDF.match(l.strip()))
    segs, formato, ign = segmentos(texto)
    if not segs:
        print("A transcrição está vazia ou não tem fala reconhecível.", file=sys.stderr)
        return 2
    com_tempo = formato != "sem_carimbo"
    falantes = extrai_falantes(segs)
    segs, cont = limpar(segs)

    pares = le_glossario(Path(a.ficha)) if a.ficha else []
    avisos = []
    if not a.ficha:
        avisos.append("sem --ficha: glossário não aplicado")
    elif not pares:
        avisos.append("Glossário da ficha vazio ou não encontrado: nada foi trocado")
    rx_g, mapa_g = compila_glossario(pares)

    pars = montar_paragrafos(segs, com_tempo, a.pausa)
    trocas = Counter()
    for p in pars:
        p.texto = aplica_glossario(rx_g, mapa_g, p.texto, trocas)

    temas = dict(TEMAS)
    if a.semana:
        extra, aviso = temas_do_esqueleto(a.semana)
        temas.update(extra)
        if aviso:
            avisos.append(aviso)
    for t in a.assunto:
        nome, _, kws = t.partition(":")
        if nome.strip() and kws.strip():
            temas[nome.strip()] = [k.strip() for k in kws.split(",") if k.strip()]
    temas_rx = {nome: tema_regex(kws) for nome, kws in temas.items()}

    score = pontuar(pars, temas_rx, a.pausa)
    cortes = escolher_cortes(pars, score, com_tempo, a.minutos_min * 60, a.minutos_max * 60, a.chars_min, a.chars_max, a.limiar)

    info = [f"- Formato lido: {formato.replace('_', ' ')}" + (f"; {ign} linha(s) de cabeçalho ignorada(s)" if ign else "") + f"; {len(segs)} falas em {len(pars)} parágrafos.",
            f"- Limpeza: {cont['interjeicao']} interjeição(ões) solta(s), {cont['ruido']} ruído(s) e {cont['laco']} fala(s) repetida(s) em laço retirados."]
    if pares:
        resumo = ", ".join(f"{t} ×{n}" for t, n in trocas.most_common(8)) or "nenhuma ocorrência"
        info.append(f"- Glossário da ficha aplicado ({sum(trocas.values())} troca(s)): {resumo}.")
    for av in avisos:
        info.append(f"- Aviso: {av}.")
    info.append(f"- Divisão por regras (coesão de vocabulário, tema, pergunta, pausa, marcador); bloco entre {a.minutos_min:g} e {a.minutos_max:g} min e até {a.chars_max} caracteres.")
    info.append("")

    pasta, nb, tamanhos = escreve(pars, cortes, arq.name, saida, com_tempo, formato, bool(falantes), temas_rx, info)
    media_c = sum(c for c, _ in tamanhos) / nb
    msg = f"{nb} blocos em {pasta} (média de {media_c:.0f} caracteres"
    if com_tempo:
        msg += f", {fmt_min(sum(s for _, s in tamanhos) / nb)} min"
    print(msg + ")")
    print(f"Glossário: {sum(trocas.values())} troca(s). Formato: {formato}." + ("" if not avisos else " Avisos: " + "; ".join(avisos) + "."))
    return 0


if __name__ == "__main__":
    sys.exit(main())
