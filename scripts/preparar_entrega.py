"""Gera e confere uma revisão S2–S5. Nunca executa avaliação por modelo.

Uso: preparar_entrega.py conteudo.json entrega.html --semana 2 --cliente Nome
     --ficha ficha.md --modo rascunho [--consultor Nome --cargo Cargo]
     --modo final exige --fontes online|congeladas [--coleta pasta].
"""
import sys
sys.dont_write_bytecode = True
import argparse
import datetime as dt
import importlib.util
import json
import os
import re
import subprocess
import uuid
from pathlib import Path

from manifesto_entrega import RAIZ_PACOTE, capturar, capturar_insumos, fora_do_pacote, gravar_atomico

SCRIPTS = RAIZ_PACOTE / "scripts"
TEMPO_VERIFICADOR = 90
ETAPAS = ("validacao", "html", "docx", "extracao", "basica", "visual", "fontes", "integridade")


def carregar_gerador():
    arquivo = RAIZ_PACOTE / "skills" / "pesquisa-mercado" / "gerador" / "gerar_pesquisa.py"
    spec = importlib.util.spec_from_file_location("ee_gerar_pesquisa", arquivo)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def rodar_verificador(html, semana, cliente, ficha, resultado, visual=False, sem_rede=False, conteudo=None):
    """O JSON atesta as etapas; retorno zero sozinho não é comprovante."""
    resultado.unlink(missing_ok=True)
    cmd = [sys.executable, "-B", str(SCRIPTS / "verificar_entrega.py"), str(html),
           "--semana", str(semana), "--cliente", cliente, "--ficha", str(ficha),
           "--resultado-json", str(resultado)]
    if visual:
        cmd.append("--visual")
    if sem_rede:
        cmd.append("--sem-rede")
    if semana == 2 and conteudo is not None:
        cmd += ["--conteudo", str(conteudo)]
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTHONIOENCODING="utf-8")
    proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", env=env,
                          timeout=TEMPO_VERIFICADOR)
    if proc.stdout:
        print(proc.stdout.rstrip())
    if proc.stderr:
        print(proc.stderr.rstrip(), file=sys.stderr)
    r = json.loads(resultado.read_text(encoding="utf-8"))
    if r.get("versao") != 1 or r.get("concluido") is not True:
        raise ValueError("verificador não concluiu as etapas obrigatórias")
    if not isinstance(r.get("erros"), list) or not isinstance(r.get("avisos"), list):
        raise ValueError("verificador não forneceu erros/avisos estruturados")
    for nome in ("basica", "visual") if visual else ("basica",):
        etapa = r.get("etapas", {}).get(nome, {})
        if etapa.get("status") not in {"aprovada", "reprovada", "nao_realizada"}:
            raise ValueError(f"verificador não comprovou etapa {nome}")
        if not isinstance(etapa.get("erros"), list) or not isinstance(etapa.get("avisos"), list):
            raise ValueError(f"resultado inválido da etapa {nome}")
        if etapa["status"] == "aprovada" and etapa["erros"]:
            raise ValueError(f"etapa {nome} contradiz os próprios erros")
        if etapa["status"] != "aprovada" and not etapa["erros"]:
            raise ValueError(f"etapa {nome} não explica por que não foi aprovada")
    if proc.returncode not in (0, 1) or (proc.returncode == 1 and not r.get("erros")):
        raise ValueError("verificador terminou sem resultado consistente")
    if proc.returncode == 0 and (r.get("erros") or any(r["etapas"][n]["status"] != "aprovada"
                                                     for n in (("basica", "visual") if visual else ("basica",)))):
        raise ValueError("verificador declarou sucesso sem executar ou aprovar etapa obrigatória")
    return r


def preparar(a):
    html = fora_do_pacote(a.saida)
    if html.suffix.lower() != ".html":
        raise ValueError("saida: use arquivo .html")
    semana_da_pasta = re.match(r"^([1-5])\.", html.parent.name)
    if html.parent.parent.parent.name == "Clientes" and semana_da_pasta and int(semana_da_pasta.group(1)) != a.semana:
        raise ValueError(f"semana: --semana {a.semana} não corresponde à pasta {html.parent.name}")
    entrada, ficha = Path(a.entrada).resolve(), Path(a.ficha).resolve()
    detalhe = Path(a.detalhe).resolve() if a.detalhe else None
    fonte = html.parent / "_fonte"
    manifesto = fonte / "manifesto-entrega.json"
    docx, telas = html.with_suffix(".docx"), fonte / "telas.md"
    verificacao = fonte / "verificacao-entrega.json"
    resultado_fontes = fonte / "fontes-entrega.json"
    alvos = [html, docx, telas, manifesto, verificacao, resultado_fontes]
    for p in alvos:
        fora_do_pacote(p)
    if {p.resolve() for p in alvos} & {p for p in (entrada, ficha, detalhe) if p}:
        raise ValueError("a saída não pode sobrescrever insumos")
    if a.modo == "final" and not a.fontes:
        raise ValueError("modo final exige --fontes online|congeladas")
    contexto = {"entrada": str(entrada), "ficha": str(ficha), "detalhe": str(detalhe) if detalhe else None,
                "coleta": str(Path(a.coleta).resolve()) if a.coleta else str(fonte / "coleta"),
                "foto": str(Path(a.foto).resolve()) if a.foto else None}
    m = {"versao": 1, "revisao": str(uuid.uuid4()), "modo": a.modo, "entrega": str(html),
         "criada_em": dt.datetime.now(dt.timezone.utc).isoformat(), "concluido": False,
         "pacote": {"raiz": str(RAIZ_PACOTE)}, "contexto": contexto,
         "configuracao": {"semana": a.semana, "cliente": a.cliente, "fontes": a.fontes,
                          "consultor": a.consultor, "cargo": a.cargo},
         "etapas": {nome: {"status": "nao_realizada", "erros": [], "avisos": []} for nome in ETAPAS},
         "erros": [], "avisos": [], "conclusao_tecnica": "nao_realizada", "aprovacao_humana": "pendente"}
    # Invalida a conclusão anterior ANTES de validar, gerar ou substituir derivados.
    gravar_atomico(manifesto, m)
    etapa_atual = "validacao"
    insumos_antes = None
    try:
        insumos_antes = capturar_insumos(html, contexto)
        if not ficha.is_file():
            raise ValueError(f"ficha: arquivo não encontrado: {ficha}")
        if detalhe and not detalhe.is_file():
            raise ValueError(f"detalhe: arquivo não encontrado: {detalhe}")
        from docx_common import aplicar_consultor, consultor_dos_args
        cons = consultor_dos_args(a)
        dados = json.loads(entrada.read_text(encoding="utf-8"))
        if not isinstance(dados, dict):
            raise ValueError("entrada: JSON precisa ser objeto")
        if a.semana == 2:
            gerador = carregar_gerador()
            dados = aplicar_consultor(dados, cons)
            avisos = gerador.validar_conteudo(dados)
            codigo_html = gerador.gerar_html(dados)
        else:
            from preencher_molde import montar
            molde = RAIZ_PACOTE / "moldes" / f"semana-{a.semana}.html"
            codigo_html, avisos = montar(molde, entrada)
            codigo_html = aplicar_consultor(codigo_html, cons)
        m["etapas"]["validacao"] = {"status": "aprovada", "erros": [], "avisos": avisos}
        etapa_atual = "html"
        html.parent.mkdir(parents=True, exist_ok=True)
        verificacao.unlink(missing_ok=True)
        resultado_fontes.unlink(missing_ok=True)
        html.write_text(codigo_html, encoding="utf-8")
        m["etapas"]["html"]["status"] = "aprovada"
        etapa_atual = "extracao"
        from extrair_telas import extrair, formatar
        extraidas = extrair(html.read_text(encoding="utf-8"))
        if not extraidas:
            raise ValueError("HTML não contém telas para revisão")
        telas.write_text(formatar(extraidas), encoding="utf-8")
        m["etapas"]["extracao"]["status"] = "aprovada"
        etapa_atual = "docx"
        if a.semana == 2:
            gerador.gerar_docx(dados, str(docx), cons)
            m["etapas"]["docx"]["status"] = "aprovada"
        elif a.modo == "final":
            from html_para_docx import converter
            converter(html, docx, cons, detalhe)
            m["etapas"]["docx"]["status"] = "aprovada"
        else:
            docx.unlink(missing_ok=True)
            m["etapas"]["docx"]["motivo"] = "S3–S5: DOCX somente no modo final"
        etapa_atual = "basica"
        r = rodar_verificador(html, a.semana, a.cliente, ficha, verificacao, a.modo == "final",
                              sem_rede=a.modo == "final" and a.fontes == "congeladas",
                              conteudo=entrada if a.semana == 2 else None)
        m["etapas"]["basica"] = r["etapas"]["basica"]
        if a.modo == "final":
            m["etapas"]["visual"] = r["etapas"]["visual"]
            etapa_atual = "fontes"
            from checar_fontes import conferir
            rf = conferir(html, a.fontes, contexto["coleta"])
            gravar_atomico(resultado_fontes, rf)
            m["etapas"]["fontes"] = rf
        else:
            for nome in ("visual", "fontes"):
                m["etapas"][nome]["motivo"] = "rascunho: sem navegador e sem rede"
        m["concluido"] = True
    except (Exception, KeyboardInterrupt) as e:
        msg = f"{etapa_atual}: {type(e).__name__}: {e}"
        m["etapas"][etapa_atual] = {"status": "nao_realizada", "erros": [msg], "avisos": []}
        print("ERRO " + msg, file=sys.stderr)
    finally:
        # A fotografia do comprovante vem antes da última comparação de insumos.
        # Uma edição posterior a essa comparação diverge da fotografia ao ser lida pelo gatilho.
        erro_fotografia = None
        try:
            fotografia_final = capturar(html, contexto)
        except Exception as e:
            erro_fotografia = f"não foi possível registrar os hashes finais: {type(e).__name__}: {e}"
            fotografia_final = {"arquivos": {}, "arvores": {}}
            m["concluido"] = False
            m["etapas"]["integridade"] = {"status": "nao_realizada", "erros": [erro_fotografia], "avisos": []}
        if insumos_antes is not None and erro_fotografia is None:
            try:
                if insumos_antes != capturar_insumos(html, contexto):
                    raise ValueError("insumos ou regras mudaram durante a preparação; gere e confira novamente")
                m["etapas"]["integridade"]["status"] = "aprovada"
            except Exception as e:
                m["concluido"] = False
                m["etapas"]["integridade"] = {"status": "nao_realizada", "erros": [str(e)], "avisos": []}
        m["erros"] = [e for etapa in m["etapas"].values() for e in etapa["erros"]]
        m["avisos"] = [e for etapa in m["etapas"].values() for e in etapa["avisos"]]
        obrigatorias = ["validacao", "html", "extracao", "basica", "integridade"]
        if a.semana == 2 or a.modo == "final":
            obrigatorias.append("docx")
        if a.modo == "final":
            obrigatorias += ["visual", "fontes"]
        estados = [m["etapas"][n]["status"] for n in obrigatorias]
        m["conclusao_tecnica"] = ("nao_realizada" if "nao_realizada" in estados else
                                  "reprovada" if "reprovada" in estados or m["erros"] else "aprovada")
        m["snapshot"] = fotografia_final
        arquivos = m["snapshot"]["arquivos"]
        m["entradas"] = {str(p): arquivos.get(str(p)) for p in (entrada, ficha, detalhe) if p}
        m["saidas"] = {str(p): arquivos.get(str(p)) for p in alvos if p != manifesto and p.is_file()}
        m["dependencias"] = {p: h for p, h in arquivos.items() if p not in m["entradas"] and p not in m["saidas"]}
        pacote = {p: h for p, h in arquivos.items() if str(RAIZ_PACOTE) + os.sep in p}
        import hashlib
        m["pacote"]["sha256"] = hashlib.sha256(json.dumps(pacote, sort_keys=True).encode()).hexdigest()
        gravar_atomico(manifesto, m)
    print(f"Preparação {m['revisao']} · {a.modo} · {m['conclusao_tecnica']} · aprovação humana pendente")
    print(f"Manifesto: {manifesto}")
    return m


def main():
    from docx_common import argumentos_do_consultor, console_utf8
    console_utf8()
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("entrada")
    ap.add_argument("saida")
    ap.add_argument("--semana", required=True, type=int, choices=(2, 3, 4, 5))
    ap.add_argument("--cliente", required=True)
    ap.add_argument("--ficha", required=True)
    ap.add_argument("--modo", required=True, choices=("rascunho", "final"))
    ap.add_argument("--fontes", choices=("online", "congeladas"))
    ap.add_argument("--coleta")
    ap.add_argument("--detalhe")
    argumentos_do_consultor(ap)
    a = ap.parse_args()
    if a.modo == "final" and not a.fontes:
        ap.error("modo final exige --fontes online|congeladas")
    try:
        m = preparar(a)
        return 0 if m["conclusao_tecnica"] == "aprovada" else 1
    except (Exception, KeyboardInterrupt) as e:
        print(f"ERRO: {type(e).__name__}: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
