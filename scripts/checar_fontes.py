"""Checagem de fontes de uma entrega da EE (base de todo encontro, B2).

Uso:
    python checar_fontes.py <entrega.html> [--sem-numeros] [--coleta <pasta da coleta>]
                           [--fontes online|congeladas] [--resultado-json <resultado.json>]

--fontes congeladas nunca consulta a rede: reabre somente os textos do índice salvo e declara
as limitações. Usa as mesmas buscas e regras numéricas do modo online (padrão compatível).

Abre cada link citado em .fonte-rodape e diz se abriu. Por padrão, procura na página (ou nas
páginas) da fonte de cada tela os números que a própria tela mostra; --sem-numeros desliga isso.

Conferência final da fonte conferida na coleta (R15): quando existe a coleta da semana (`_fonte/coleta/indice.json`
ao lado da entrega, ou --coleta), cada número ou termo que o coletor achou na página (`coletar_fontes.py --procurar`)
é procurado de novo na página reaberta. Só acusa mudança: o número sumiu da página (sai do deck ou troca a fonte);
se o número continua mas a frase em volta mudou, é aviso. Sem a coleta, ou sem beautifulsoup4, a checagem segue como antes.

Código de saída 1 quando algum link não abre ou algum número da tela não é achado na página
da fonte. A lista "conferir à mão" no fim diz o que fazer: número que não aparece na página
sai do deck ou a fonte é trocada. Número que a tela cita da fala do cliente ou da ficha não
está em página pública: confira na ficha e deixe o motivo registrado.
Sites que bloqueiam robôs (403) precisam de conferência manual ou de fonte oficial equivalente.
"""
import sys
sys.dont_write_bytecode = True
import argparse, io, json, re, ssl, urllib.request
from html import unescape
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

sys.path.insert(0, str(Path(__file__).resolve().parent))
CTX = ssl.create_default_context(); CTX.check_hostname = False; CTX.verify_mode = ssl.CERT_NONE
# números com milhar ou decimal (1.200, 12,5) e percentuais inteiros (40%)
NUMERO = r"\d{1,3}(?:\.\d{3})+(?:,\d+)?|\d+,\d+|\d+\s?%"


def baixar(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/126 Safari/537.36", "Accept-Language": "pt-BR"})
    return urllib.request.urlopen(req, timeout=30, context=CTX).read()


def texto_cru(raw):
    if raw[:4] == b"%PDF":
        from pypdf import PdfReader
        return " ".join((p.extract_text() or "") for p in PdfReader(io.BytesIO(raw)).pages)
    t = raw.decode("utf-8", "ignore")
    t = re.sub(r"(?s)<script.*?</script>|<style.*?</style>", " ", t)
    return unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", t)))


def pagina(url):
    return texto_cru(baixar(url))


def texto_limpo(raw):
    """O mesmo texto limpo que o coletor gravou (sem menu, rodapé e script); None se faltar beautifulsoup4 ou pypdf."""
    try:
        import coletar_fontes as CF
        if raw[:4] == b"%PDF":
            from extrair_insumos import ler_pdf
            return ler_pdf(io.BytesIO(raw))[0]
        return CF.limpar_html(CF.decodificar(raw, ""))[2]
    except Exception:
        return None


def coleta_da_entrega(arquivo, pasta=None):
    """{url: [buscas achadas]} do índice da coleta, ou {}."""
    cand = [Path(pasta)] if pasta else [Path(arquivo).resolve().parent / "_fonte" / "coleta"]
    for c in cand:
        try:
            indice = json.loads((c / "indice.json").read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        return {r["url"]: [b for b in r.get("procurar") or [] if b.get("achou")] for r in indice
                if isinstance(r, dict) and r.get("status") == "ok" and r.get("url")}
    return {}


def reconfirmar(url, buscas, cru, limpo):
    """Refaz a busca de cada achado da coleta na página reaberta. Devolve (mudou, avisos)."""
    import coletar_fontes as CF
    mudou, avisos = [], []
    texto = limpo if limpo is not None else cru
    norm = re.sub(r"\s+", " ", texto)
    for b in buscas:
        r = CF.procurar_termo(texto, b)
        if not r["achou"]:
            mudou.append(b["termo"])
        elif b.get("trecho") and re.sub(r"\s+", " ", b["trecho"]) not in norm:
            avisos.append(b["termo"])
    return mudou, avisos


def variantes(n):
    """Formas em que o mesmo número costuma aparecer na página."""
    n = re.sub(r"\s+", "", n)
    v = {n}
    if n.endswith("%"):
        v.add(n[:-1] + " %"); v.add(n[:-1] + " por cento")
    base = n.rstrip("%")
    if re.fullmatch(r"\d{1,3}(?:\.\d{3})+(?:,\d+)?", base):
        v.add(base.replace(".", "")); v.add(base.replace(".", " ")); v.add(base.replace(".", ","))
    if re.fullmatch(r"\d+,\d+", base):
        v.add(base.replace(",", "."))
    return v


def acha(n, t):
    if any(re.search(r"(?<![\d.,])" + re.escape(x) + r"(?!\d|[.,]\d)", t) for x in variantes(n)):
        return True
    try:                                       # outros formatos do mesmo número (1,234.5; 7,6 milhões = 7.600.000)
        import coletar_fontes as CF
        alvo = CF.alvo_numerico(n)
        return bool(alvo and CF._ocorrencias_numero(t, alvo[0], alvo[1], ignora_escala=True))
    except Exception:
        return False


def telas_com_fontes(html):
    """Para cada tela com .fonte-rodape: nome, links e números do corpo da tela."""
    out = []
    for s in re.findall(r"(?s)<section.*?</section>", html):
        eb = re.search(r'class="eyebrow[^"]*">([^<]*)<', s)
        tela = unescape(eb.group(1)).strip() if eb else "capa"
        corpo = re.sub(r"<[^>]+>", " ", re.sub(r'(?s)<div class="fonte-rodape.*', "", s))
        nums = sorted(set(re.sub(r"\s+", "", n) for n in re.findall(NUMERO, unescape(corpo))))
        links = []
        for bloco in re.findall(r'class="fonte-rodape.*?(?=</div>)', s, re.S):
            links += re.findall(r'href="([^"]+)"', bloco)
        if links:
            out.append({"tela": tela, "links": list(dict.fromkeys(unescape(u) for u in links)), "nums": nums})
    return out


def conferir(arquivo, fontes="online", coleta=None, sem_numeros=False):
    """Mesma interpretação nos dois modos; congeladas nunca abre a URL atual."""
    if fontes not in ("online", "congeladas"):
        raise ValueError("fontes: use online ou congeladas")
    import coletar_fontes as CF
    html = Path(arquivo).read_text(encoding="utf-8")
    telas = telas_com_fontes(html)
    limitacoes = (["Acervo congelado: confere somente o texto salvo; não confirma a página atual, imagens, OCR não conferido ou disponibilidade histórica."]
                  if fontes == "congeladas" else [])
    for aviso in limitacoes:
        print("AVISO " + aviso)
    if not telas:
        print("Nenhum link em .fonte-rodape neste arquivo.")
        return {"status": "aprovada", "erros": [], "avisos": limitacoes, "modo": fontes, "links": 0}

    pasta = Path(coleta) if coleta else Path(arquivo).resolve().parent / "_fonte" / "coleta"
    buscas_coleta = coleta_da_entrega(arquivo, pasta)
    indice = []
    if fontes == "congeladas":
        try:
            indice = json.loads((pasta / "indice.json").read_text(encoding="utf-8"))
            if not isinstance(indice, list):
                raise ValueError("índice precisa ser uma lista")
        except (OSError, ValueError) as e:
            motivo = f"acervo congelado ausente ou ilegível: {e}"
            print("ERRO " + motivo)
            return {"status": "nao_realizada", "erros": [motivo], "avisos": limitacoes, "modo": fontes}
    paginas, brutos, falhas = {}, {}, {}
    for u in dict.fromkeys(u for t in telas for u in t["links"]):
        try:
            if fontes == "congeladas":
                reg = next((r for r in indice if isinstance(r, dict) and r.get("url")
                            and CF.mesma_url(r["url"], u) and r.get("status") == "ok"), None)
                if reg is None:
                    raise ValueError("URL sem coleta salva válida")
                arquivos = reg.get("partes") or ([reg["arquivo"]] if reg.get("arquivo") else [])
                if not arquivos:
                    raise ValueError("coleta sem arquivos de texto")
                for item in arquivos:
                    p = (pasta / item).resolve()
                    if pasta.resolve() not in p.parents or not p.is_file():
                        raise ValueError("arquivo de coleta ausente ou fora do acervo")
                paginas[u], _ = CF.ler_corpo(pasta, reg)
                if not paginas[u].strip():
                    raise ValueError("texto salvo vazio")
                print(f"SALVO  {u[:110]}")
            else:
                brutos[u] = baixar(u)
                paginas[u] = texto_cru(brutos[u])
                print(f"ABRE  {u[:110]}")
        except Exception as e:
            paginas.pop(u, None)
            falhas[u] = f"{type(e).__name__} {str(e)[:50]}"
            print(f"NÃO ABRE ({falhas[u]})  {u[:110]}")

    a_mao = []
    for u, motivo in falhas.items():
        quem = "; ".join(t["tela"][:30] for t in telas if u in t["links"])
        a_mao.append(f"link não abre ({motivo}): {u}\n      telas: {quem}\n      trocar por fonte oficial equivalente ou conferir no navegador")

    avisos_trecho = []
    if buscas_coleta:
        sem_bs4 = False
        for u in paginas:
            buscas = next((b for k, b in buscas_coleta.items() if CF.mesma_url(k, u) and b), [])
            if not buscas:
                continue
            limpo = paginas[u] if fontes == "congeladas" else texto_limpo(brutos[u])
            sem_bs4 = sem_bs4 or limpo is None
            mudou, avisos = reconfirmar(u, buscas, paginas[u], limpo)
            if mudou:
                situacao = "o texto salvo não confirma os termos do índice" if fontes == "congeladas" else "a página mudou desde a coleta, não tem mais"
                a_mao.append(f"{situacao}: {', '.join(mudou)}\n      fonte: {u[:100]}\n"
                             "      tirar o número do deck, trocar a fonte, ou coletar de novo e refazer a conta")
            else:
                local = "presentes no texto salvo" if fontes == "congeladas" else "ainda na página"
                print(f"CONFERE  {len(buscas)} trecho(s) da coleta {local}  {u[:90]}")
            avisos_trecho += [f"{t} (frase em volta mudou; o número continua)" for t in avisos]
        if sem_bs4:
            print("AVISO sem beautifulsoup4: a reconferência usou o texto bruto da página, que traz menu e rodapé")
        for t in avisos_trecho:
            print(f"AVISO trecho da coleta mudou: {t}")

    if not sem_numeros:
        print()
        for t in telas:
            if not t["nums"]:
                continue
            abertas = [u for u in t["links"] if u in paginas]
            if not abertas:
                a_mao.append(f"tela '{t['tela'][:40]}': nenhuma fonte abriu, números sem conferência: {', '.join(t['nums'][:8])}")
                continue
            texto = " ".join(paginas[u] for u in abertas)
            achados = [n for n in t["nums"] if acha(n, texto)]
            faltam = [n for n in t["nums"] if n not in achados]
            print(f"tela '{t['tela'][:40]}': {len(achados)} de {len(t['nums'])} números achados na página da fonte")
            if faltam:
                a_mao.append(f"tela '{t['tela'][:40]}': número não achado na página da fonte: {', '.join(faltam)}\n      fontes: {'; '.join(u[:80] for u in t['links'])}\n      tirar o número do deck, trocar a fonte, ou registrar de onde ele vem (ficha)")

    n_links = len(dict.fromkeys(u for t in telas for u in t["links"]))
    print(f"\n{n_links} links · {len(paginas)} abrem · {len(falhas)} não abrem")
    if a_mao:
        print("\nConferir à mão:")
        for x in a_mao:
            print("  -", x)
    else:
        print("Tudo conferido no texto salvo." if fontes == "congeladas" else "Tudo conferido.")
    return {"status": "reprovada" if a_mao else "aprovada", "erros": a_mao,
            "avisos": limitacoes + avisos_trecho, "modo": fontes, "links": n_links}


def main():
    ap = argparse.ArgumentParser(description="Confere fontes online ou somente o acervo salvo.")
    ap.add_argument("arquivo")
    ap.add_argument("--sem-numeros", action="store_true")
    ap.add_argument("--numeros", action="store_true", help=argparse.SUPPRESS)
    ap.add_argument("--coleta", help="pasta com indice.json e textos da coleta")
    ap.add_argument("--fontes", choices=("online", "congeladas"), default="online")
    ap.add_argument("--resultado-json", help="resultado estruturado fora do pacote")
    a = ap.parse_args()
    try:
        r = conferir(a.arquivo, a.fontes, a.coleta, a.sem_numeros)
    except Exception as e:
        r = {"status": "nao_realizada", "erros": [f"fontes não conferidas: {type(e).__name__}: {e}"], "avisos": []}
        print("ERRO " + r["erros"][0])
    if a.resultado_json:
        from manifesto_entrega import gravar_atomico
        gravar_atomico(a.resultado_json, r)
    return 0 if r["status"] == "aprovada" else 1


if __name__ == "__main__":
    sys.exit(main())
