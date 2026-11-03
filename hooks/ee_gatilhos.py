"""Gatilhos do pacote ee-trieme (versão única, seção 2.5). Só biblioteca padrão do Python.

Uso (chamado por hooks/gatilho, que o run-hook.cmd aciona): python ee_gatilhos.py <sessao|gravacao|parar>
A entrada é o JSON do Claude Code em stdin. A saída é JSON em stdout, sempre com código 0.

  sessao    SessionStart (startup, clear, compact). Painel curto dos clientes e os arquivos novos de
            "0. Inputs e Transcrições/" desde a última sessão.
  gravacao  PostToolUse (Write, Edit, MultiEdit, Bash). Roda só o verificador (sem --visual e sem a
            checagem de fontes) nos HTML de Clientes/ cujo conteúdo ou dependências mudaram. Reconhece
            o manifesto do preparador pelos hashes, incluindo conferência reprovada com erros preservados.
            A saída é curta e vai só ao assistente (additionalContext), não ao
            consultor. A conferência completa (visual e fontes) roda uma vez, no fim, pelo guia.
  parar     Stop. Lembra de atualizar a ficha quando ela ficou atrás da pasta do cliente (o que está em
            _ensaios-internos/ não conta). Só mostra o lembrete ao consultor: não força o assistente a continuar.
            Depois, mede o uso da sessão (tokens, duração, modelo, ferramentas) e grava uma linha por sessão na
            seção Medição de <cliente>/_ensaios-internos/registro.md (scripts/medir_uso.py, R15): local, sem
            rede, com prazo, nunca bloqueia.

Só age quando a pasta do projeto tem Clientes/. O estado fica em EE/.claude/ee-trieme-estado.json,
nunca na pasta do pacote.
"""
import sys
sys.dont_write_bytecode = True
import datetime as dt
import json
import os
import re
import subprocess
import tempfile
import time
from pathlib import Path

RAIZ_PACOTE = Path(__file__).resolve().parent.parent
SCRIPTS = RAIZ_PACOTE / "scripts"
sys.path.insert(0, str(SCRIPTS))
from manifesto_entrega import capturar, comprovante_basico, contexto_manifesto
ESTADO = Path(".claude") / "ee-trieme-estado.json"
MAX_AVISOS_LISTADOS = 5
TEMPO_VERIFICADOR = 20
ASSUNTO_STOP = "Ficha atrás da pasta do cliente"

PRIMEIRA_SESSAO_DIAS = 7
MAX_NOVOS = 10
MAX_PENDENCIAS_LISTADAS = 3
TEMPO_MEDICAO = 7  # segundos para ler o histórico da sessão (o Stop tem 15 s)


# ---------- entrada, saída, estado ----------

def ler_entrada():
    try:
        bruto = sys.stdin.buffer.read().decode("utf-8", "replace")
        return json.loads(bruto) if bruto.strip() else {}
    except Exception:
        return {}


def emitir(evento, mensagem=None, contexto=None):
    """Mensagem ao consultor (systemMessage) e, se houver, contexto ao assistente (additionalContext)."""
    saida = {}
    if mensagem:
        saida["systemMessage"] = mensagem
    if contexto and evento in ("SessionStart", "PostToolUse"):
        saida["hookSpecificOutput"] = {"hookEventName": evento, "additionalContext": contexto}
    if saida:
        sys.stdout.write(json.dumps(saida, ensure_ascii=True))
        sys.stdout.flush()


def raiz_ee(entrada):
    """Pasta do projeto, se ela tem Clientes/. Senão None (o gatilho não age)."""
    for cand in (os.environ.get("CLAUDE_PROJECT_DIR"), entrada.get("cwd"), os.getcwd()):
        if cand:
            p = Path(cand)
            if (p / "Clientes").is_dir():
                return p.resolve()
    return None


def ler_estado(raiz):
    try:
        return json.loads((raiz / ESTADO).read_text(encoding="utf-8"))
    except Exception:
        return {}


def gravar_estado(raiz, estado):
    try:
        alvo = raiz / ESTADO
        alvo.parent.mkdir(parents=True, exist_ok=True)
        tmp = alvo.with_suffix(".tmp")
        tmp.write_text(json.dumps(estado, ensure_ascii=False, indent=1), encoding="utf-8")
        os.replace(tmp, alvo)
    except Exception:
        pass


# ---------- clientes e fichas ----------

def nome_do_cliente(pasta):
    return re.sub(r"^\s*\d+\.\s*", "", pasta.name).strip()


def pastas_de_clientes(raiz):
    base = raiz / "Clientes"
    def chave(p):
        n = re.match(r"\d+", p.name)
        return (0, int(n.group(0)), p.name) if n else (1, 0, p.name)
    return sorted((p for p in base.iterdir() if p.is_dir() and not p.name.startswith((".", "_"))), key=chave)


def yaml_da_ficha(texto):
    m = re.match(r"﻿?---\s*\n(.*?)\n---\s*(?:\n|$)", texto, re.S)
    dados = {}
    if m:
        for ln in m.group(1).splitlines():
            k = re.match(r"^([A-Za-z_][\w-]*)\s*:\s*(.*)$", ln)
            if k:
                dados[k.group(1).lower()] = k.group(2).strip().strip("\"'").strip()
    return dados


def achar_ficha(pasta):
    """Ficha do cliente: <Nome>.md na pasta; senão o primeiro .md com cabeçalho YAML que tem 'cliente'."""
    esperada = pasta / f"{nome_do_cliente(pasta)}.md"
    candidatas = [esperada] + sorted(pasta.glob("*.md"))
    for c in candidatas:
        if c.is_file():
            try:
                if "cliente" in yaml_da_ficha(c.read_text(encoding="utf-8")):
                    return c
            except Exception:
                continue
    return None


def secao(texto, titulo):
    """Corpo da seção '## <titulo>' (sem os comentários HTML) até o próximo '## '."""
    texto = re.sub(r"(?s)<!--.*?-->", "", texto)
    alvo = sem_acento(titulo)
    dentro, linhas = False, []
    for ln in texto.splitlines():
        if re.match(r"^#{2,}\s+", ln):
            dentro = bool(re.match(r"^##\s+(?!#)", ln)) and sem_acento(re.sub(r"^##\s+", "", ln)).startswith(alvo)
            continue
        if dentro:
            linhas.append(ln)
    return "\n".join(linhas)


def sem_acento(s):
    import unicodedata
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn").lower().strip()


def data_no_texto(texto, hoje):
    """Última data do texto (dd/mm/aaaa, dd/mm ou aaaa-mm-dd) ou None."""
    achados = []
    for m in re.finditer(r"(?<!\d)(\d{4})-(\d{2})-(\d{2})(?!\d)|(?<![\d/])(\d{1,2})/(\d{1,2})(?:/(\d{4}|\d{2}))?(?![\d/])", texto):
        try:
            if m.group(1):
                d = dt.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
            else:
                ano = int(m.group(6)) if m.group(6) else hoje.year
                ano = ano + 2000 if ano < 100 else ano
                d = dt.date(ano, int(m.group(5)), int(m.group(4)))
            achados.append(d)
        except ValueError:
            continue
    return achados[-1] if achados else None


FEITO = re.compile(r"\[[xX]\]|~~|\b(feito|feita|resolvid[oa]|fechad[oa]|conclu[ií]d[oa])\b", re.I)


def pendencias(texto, hoje):
    """Itens da seção Pendências: [(texto, data|None, vencida)]. Item concluído não conta."""
    itens = []
    for ln in secao(texto, "Pendências").splitlines():
        s = ln.strip()
        if not s or re.fullmatch(r"\|?[\s:|-]+\|?", s):
            continue
        if not re.match(r"^([-*+]|\d+[.)]|\|)", s):
            continue
        corpo = re.sub(r"^([-*+]|\d+[.)])\s*(\[[ xX]\])?\s*", "", s).strip(" |")
        corpo = re.sub(r"\s*\|\s*", " · ", corpo).strip(" ·")
        if not corpo or FEITO.search(s):
            continue
        d = data_no_texto(corpo, hoje)
        if d is None and re.search(r"\b(pend[eê]ncia|dono|data)\b", corpo, re.I) and corpo.count("·") >= 2 \
                and not re.search(r"\d", corpo):
            continue  # linha de cabeçalho de tabela
        itens.append((corpo, d, d is not None and d < hoje))
    return itens


def resumo_cliente(pasta, hoje):
    ficha = achar_ficha(pasta)
    nome = nome_do_cliente(pasta)
    if ficha is None:
        return {"nome": nome, "ficha": None, "linha": f"{nome} · sem ficha"}
    texto = ficha.read_text(encoding="utf-8")
    y = yaml_da_ficha(texto)
    pend = pendencias(texto, hoje)
    vencidas = [p for p in pend if p[2]]
    sem_data = [p for p in pend if p[1] is None]
    proxima = y.get("proxima_data", "") or "a confirmar"
    d = data_no_texto(proxima, hoje)
    marca = " (passou)" if d is not None and d < hoje else ""
    linha = f"{y.get('cliente') or nome} · etapa: {y.get('etapa') or 'a confirmar'} · próxima data: {proxima}{marca}"
    linha += f" · pendências vencidas: {len(vencidas)}"
    if sem_data:
        linha += f" · sem data: {len(sem_data)}"
    return {"nome": nome, "ficha": ficha, "linha": linha, "vencidas": vencidas}


# ---------- arquivos ----------

def arquivos_da_pasta(pasta):
    for dentro, dirs, nomes in os.walk(pasta):
        # "_texto" é o texto extraído dos insumos (extrair_insumos.py): derivado, não chegada nova.
        # "_ensaios-internos" guarda a medição e os ensaios: gravar lá não é mexer na pasta do cliente
        dirs[:] = [d for d in dirs if not d.startswith((".", "__")) and d not in ("_texto", "_ensaios-internos")]
        for n in nomes:
            if n.startswith((".", "~$")) or n.endswith((".tmp", ".pyc")):
                continue
            yield Path(dentro) / n


def novos_inputs(pasta_cliente, desde):
    achados = []
    for sub in sorted(pasta_cliente.iterdir()):
        if sub.is_dir() and sub.name.startswith("0."):
            for f in arquivos_da_pasta(sub):
                try:
                    m = f.stat().st_mtime
                except OSError:
                    continue
                if m > desde:
                    achados.append((m, f))
    return sorted(achados)


def hora(ts):
    return dt.datetime.fromtimestamp(ts).strftime("%d/%m %H:%M")


# ---------- gatilho 1: abertura da sessão ----------

def sessao(entrada, raiz):
    agora = time.time()
    hoje = dt.date.today()
    estado = ler_estado(raiz)
    desde = estado.get("ultima_sessao") or (agora - PRIMEIRA_SESSAO_DIAS * 86400)
    linhas, novos = [], []
    for pasta in pastas_de_clientes(raiz):
        r = resumo_cliente(pasta, hoje)
        linhas.append("- " + r["linha"])
        for texto, d, _ in (r.get("vencidas") or [])[:MAX_PENDENCIAS_LISTADAS]:
            linhas.append("    vencida: " + (texto[:90] + "..." if len(texto) > 90 else texto))
        for m, f in novos_inputs(pasta, desde):
            novos.append((r["nome"], m, f.relative_to(pasta)))
    nome_consultor = os.environ.get("CLAUDE_PLUGIN_OPTION_CONSULTOR_NOME", "").strip()
    cab = f"EE · painel de clientes · {hoje.strftime('%d/%m/%Y')}" + (f" · {nome_consultor}" if nome_consultor else "")
    if not linhas:
        linhas = ["- nenhum cliente em Clientes/ ainda (novo cliente: /ee-trieme:novo-cliente <Nome>)"]
    texto = [cab] + linhas
    if novos:
        texto.append("Arquivos novos em 0. Inputs e Transcrições desde a última sessão:")
        for nome, m, rel in novos[:MAX_NOVOS]:
            texto.append(f"- {nome} · {rel.as_posix()} · {hora(m)}")
        if len(novos) > MAX_NOVOS:
            texto.append(f"- e mais {len(novos) - MAX_NOVOS}")
        texto.append("Processar?")
    estado["ultima_sessao"] = agora
    gravar_estado(raiz, estado)
    painel = "\n".join(texto)
    contexto = painel + ("\n\nOs arquivos novos acima chegaram desde a última sessão. Pergunte ao consultor, uma vez, "
                         "se quer processá-los agora (atualizar a ficha do cliente com o que trazem)." if novos else "")
    emitir("SessionStart", painel, contexto)


# ---------- gatilho 2: depois de gravar um HTML de cliente ----------

def e_entrega(raiz, caminho):
    """(cliente, semana) se o caminho é um deck de semana: Clientes/<N. Nome>/<S. Semana>/<arquivo>.html."""
    try:
        rel = Path(caminho).resolve().relative_to(raiz / "Clientes")
    except Exception:
        return None
    p = rel.parts
    if len(p) != 3 or not p[2].lower().endswith(".html"):
        return None
    m = re.match(r"^([1-5])\.", p[1])
    if not m or p[2].startswith("_") or "detalhe" in p[2].lower():
        return None
    return raiz / "Clientes" / p[0], int(m.group(1))


def rodar(cmd, tempo):
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTHONIOENCODING="utf-8")
    return subprocess.run([sys.executable, "-B", *cmd], capture_output=True, timeout=tempo, env=env)


def saida_de(proc):
    return (proc.stdout or b"").decode("utf-8", "replace")


def conferir(raiz, html, pasta_cliente, semana, conteudo=None):
    """Roda só o verificador, sem --visual (a conferência completa roda uma vez, no fim, pelo guia).
    Devolve uma etapa estruturada. Retorno zero sem comprovante não dispensa nova tentativa."""
    nome = nome_do_cliente(pasta_cliente)
    ficha = achar_ficha(pasta_cliente)
    cmd = [str(SCRIPTS / "verificar_entrega.py"), str(html), "--semana", str(semana), "--cliente", nome]
    if ficha:
        cmd += ["--ficha", str(ficha)]
    if semana == 2 and conteudo is not None:
        cmd += ["--conteudo", str(conteudo)]
    try:
        with tempfile.TemporaryDirectory(prefix="ee-gatilho-") as temp:
            resultado = Path(temp) / "resultado.json"
            proc = rodar(cmd + ["--resultado-json", str(resultado)], TEMPO_VERIFICADOR)
            r = json.loads(resultado.read_text(encoding="utf-8"))
            etapa = r["etapas"]["basica"]
            if r.get("concluido") is not True or etapa.get("status") not in {"aprovada", "reprovada"}:
                raise ValueError("conferência básica não concluída")
            if not isinstance(etapa.get("erros"), list) or not isinstance(etapa.get("avisos"), list):
                raise ValueError("resultado sem erros/avisos estruturados")
            if proc.returncode not in (0, 1) or (proc.returncode == 0 and (etapa["status"] != "aprovada" or etapa["erros"])):
                raise ValueError("verificador terminou sem resultado consistente")
            if proc.returncode == 1 and (etapa["status"] != "reprovada" or not etapa["erros"]):
                raise ValueError("reprovação não comprovada")
            return etapa
    except subprocess.TimeoutExpired:
        msg = f"o verificador passou de {TEMPO_VERIFICADOR} s e foi interrompido; rode à mão"
    except Exception as e:
        msg = f"o verificador não concluiu ({type(e).__name__}); rode à mão"
    return {"status": "nao_realizada", "erros": [msg], "avisos": []}


def htmls_novos(raiz, desde, conferidos):
    """Descobre entregas; o hash decide se há mudança, inclusive com mtime preservado."""
    achados = []
    base = raiz / "Clientes"
    for cli in base.iterdir():
        if not cli.is_dir() or cli.name.startswith((".", "_")):
            continue
        for sem in cli.iterdir():
            if not sem.is_dir() or not re.match(r"^[1-5]\.", sem.name):
                continue
            for f in sem.glob("*.html"):
                if e_entrega(raiz, f):
                    achados.append(f)
    return sorted(achados)


def gravacao(entrada, raiz):
    agora = time.time()
    estado = ler_estado(raiz)
    conferidos = estado.setdefault("conferencias", {})
    desde = estado.get("ultima_conferencia") or (agora - 600)
    alvos = []
    entrada_ferr = entrada.get("tool_input") or {}
    fp = entrada_ferr.get("file_path")
    if entrada.get("tool_name") in ("Bash", "Write", "Edit", "MultiEdit") or fp:
        # Uma dependência alterada também invalida a conferência de HTML inalterado.
        alvos = [f.resolve() for f in htmls_novos(raiz, desde, conferidos)]
        estado["ultima_conferencia"] = agora
    if not alvos:
        gravar_estado(raiz, estado)
        return
    msgs, ha_erro = [], False
    for html in alvos:
        pasta_cliente, semana = e_entrega(raiz, html)
        anterior = conferidos.get(str(html), {})
        contexto = contexto_manifesto(html) or (anterior.get("contexto", {}) if isinstance(anterior, dict) else {})
        ficha = achar_ficha(pasta_cliente)
        if ficha:
            contexto["ficha"] = str(ficha.resolve())
        configuracao = {"semana": semana, "cliente": nome_do_cliente(pasta_cliente),
                        "ficha": str(ficha.resolve()) if ficha else None}
        conteudo = contexto.get("entrada") if semana == 2 else None
        if semana == 2:
            configuracao["entrada"] = str(Path(conteudo).resolve()) if conteudo else str(html.parent / "_fonte" / "conteudo.json")
        fotografia = capturar(html, contexto)
        etapa = comprovante_basico(html, configuracao)
        reutilizada = etapa is not None
        if etapa is None and isinstance(anterior, dict) and anterior.get("snapshot") == fotografia \
                and anterior.get("configuracao") == configuracao:
            teste = anterior.get("resultado", {})
            if teste.get("status") in {"aprovada", "reprovada"}:
                etapa, reutilizada = teste, True
        if etapa is None:
            etapa = conferir(raiz, html, pasta_cliente, semana, conteudo=conteudo)
        conferidos[str(html)] = {"snapshot": fotografia, "contexto": contexto, "configuracao": configuracao, "resultado": etapa}
        erros, avisos = etapa["erros"], etapa["avisos"]
        # Aviso de conferência reaproveitada já apareceu quando os hashes mudaram; repetir a cada comando só gasta contexto.
        # Erro continua aparecendo sempre, até ser corrigido.
        if erros or (avisos and not reutilizada):
            ha_erro = ha_erro or bool(erros)
            linhas = [f"Verificador de {html.name} (Semana {semana}): {etapa['status']} · {len(erros)} erro(s), {len(avisos)} aviso(s)"
                      + (" · já conferido para estes hashes" if reutilizada else "")]
            linhas += ["  ERRO  " + e for e in erros]
            linhas += ["  AVISO " + a for a in avisos[:MAX_AVISOS_LISTADOS]]
            if len(avisos) > MAX_AVISOS_LISTADOS:
                linhas.append(f"  e mais {len(avisos) - MAX_AVISOS_LISTADOS} aviso(s); rode o verificador à mão para ver todos")
            msgs.append("\n".join(linhas))
        elif not reutilizada:
            msgs.append(f"Verificador de {html.name} (Semana {semana}): sem pendência")
    gravar_estado(raiz, estado)
    texto = "\n\n".join(msgs)
    if ha_erro:
        texto += "\n\nCorrija os erros antes de apresentar ou enviar."
    # só ao assistente: o consultor não precisa ver a mesma saída duas vezes
    if texto:
        emitir("PostToolUse", None, texto)


# ---------- gatilho 3: fim da tarefa ----------

def mais_novo(pasta, ignorar):
    melhor = 0.0
    for f in arquivos_da_pasta(pasta):
        if f == ignorar:
            continue
        try:
            melhor = max(melhor, f.stat().st_mtime)
        except OSError:
            continue
    return melhor


def medir_uso(entrada, raiz):
    """Grava a linha de uso da sessão no registro interno do cliente mexido. Nunca levanta, nunca emite mensagem."""
    try:
        caminho = entrada.get("transcript_path")
        if not caminho:
            return
        sys.path.insert(0, str(SCRIPTS))
        import medir_uso as M
        estado = ler_estado(raiz)
        vistos = estado.setdefault("medicao", {})
        M.medir(caminho, entrada.get("session_id") or "", raiz, estado=vistos, prazo_s=TEMPO_MEDICAO)
        if len(vistos) > 200:
            for k in list(vistos)[:-100]:
                vistos.pop(k, None)
        gravar_estado(raiz, estado)
    except Exception as e:
        sys.stderr.write(f"ee-trieme medicao: {type(e).__name__}: {e}\n")


def parar(entrada, raiz):
    try:
        lembrar_ficha(entrada, raiz)
    finally:
        medir_uso(entrada, raiz)  # roda também quando o Stop veio de um lembrete (stop_hook_active)


def lembrar_ficha(entrada, raiz):
    if entrada.get("stop_hook_active"):
        return  # já seguiu um lembrete: sem laço
    estado = ler_estado(raiz)
    sessao_desde = estado.get("ultima_sessao") or 0
    lembrados = estado.setdefault("lembrados", {})
    atrasados = []
    for pasta in pastas_de_clientes(raiz):
        ficha = achar_ficha(pasta)
        if ficha is None:
            continue
        recente = mais_novo(pasta, ficha)
        if recente > ficha.stat().st_mtime + 1 and recente > sessao_desde and recente > lembrados.get(pasta.name, 0):
            atrasados.append(pasta)
            lembrados[pasta.name] = recente
    if not atrasados:
        return
    gravar_estado(raiz, estado)
    nomes = ", ".join(nome_do_cliente(p) for p in atrasados)
    emitir("Stop", f"{ASSUNTO_STOP}: {nomes}. Atualizar a ficha (seção Status e Pendências) e preparar a mensagem "
                   f"pós-encontro (padrao/mensagens-pos-encontro.md) quando a reunião tiver acontecido.")


# ---------- main ----------

def main():
    evento = sys.argv[1] if len(sys.argv) > 1 else ""
    entrada = ler_entrada()
    try:
        raiz = raiz_ee(entrada)
        if raiz is None:
            return
        {"sessao": sessao, "gravacao": gravacao, "parar": parar}.get(evento, lambda *_: None)(entrada, raiz)
    except Exception as e:  # um gatilho nunca derruba a sessão
        sys.stderr.write(f"ee-trieme gatilho {evento}: {type(e).__name__}: {e}\n")


if __name__ == "__main__":
    main()
