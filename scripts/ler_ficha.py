"""Mostra só as seções pedidas da ficha do cliente, para leitura barata.

Uso:
    python ler_ficha.py <ficha.md> --secoes "Status, Dados mínimos, Números-fonte" [--obrigatorias "Status"] [--cabecalho] [--listar]

Uma seção vai do título `## Nome` até o próximo `## `, com as subseções `###` dentro dela.
O nome casa pelo começo do título, sem diferenciar maiúscula nem acento ("numeros" acha "Números-fonte";
"Meta" acha "Meta, condições e efeitos indesejados"). `--cabecalho` mostra também o bloco YAML do topo
(etapa, formato, setor, decisor). `--listar` mostra só os títulos das seções, com o número de linhas de cada uma.
Seção opcional que não existe vira aviso. Obrigatórias exigem uma seção única, preferindo nome exato normalizado
e depois prefixo único, e precisam fazer parte das solicitadas. Só biblioteca padrão. Sai 2 em falha de leitura ou contrato.
"""
import sys
sys.dont_write_bytecode = True
import argparse, re, unicodedata
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass


def chave(texto):
    sem_acento = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", sem_acento).strip().lower()


def secoes(linhas):
    """Lista de (título, início, fim) das seções `## `; fim é exclusivo."""
    inicios = [(i, l[3:].strip()) for i, l in enumerate(linhas) if l.startswith("## ")]
    saida = []
    for n, (i, titulo) in enumerate(inicios):
        fim = inicios[n + 1][0] if n + 1 < len(inicios) else len(linhas)
        saida.append((titulo, i, fim))
    return saida


def cabecalho(linhas):
    if not linhas or linhas[0].strip() != "---":
        return []
    for i in range(1, len(linhas)):
        if linhas[i].strip() == "---":
            return linhas[: i + 1]
    return []


def main():
    ap = argparse.ArgumentParser(description="Mostra só as seções pedidas da ficha.")
    ap.add_argument("ficha")
    ap.add_argument("--secoes", default="", help='nomes separados por vírgula, ex.: "Status, Números-fonte"')
    ap.add_argument("--obrigatorias", default="", help="seções solicitadas que devem existir de forma única")
    ap.add_argument("--cabecalho", action="store_true", help="mostra também o bloco YAML do topo")
    ap.add_argument("--listar", action="store_true", help="só os títulos das seções")
    a = ap.parse_args()

    try:
        linhas = Path(a.ficha).read_text(encoding="utf-8").splitlines()
    except Exception as e:
        print(f"Não li a ficha: {e}")
        return 2

    todas = secoes(linhas)
    pedidos = [p.strip() for p in a.secoes.split(",") if p.strip()]
    obrigatorias = [p.strip() for p in a.obrigatorias.split(",") if p.strip()]
    resolvidas = {}
    erros = []
    for pedido in obrigatorias:
        exatas = [s for s in todas if chave(s[0]) == chave(pedido)]
        candidatas = exatas or [s for s in todas if chave(s[0]).startswith(chave(pedido))]
        if not candidatas:
            erros.append(f"seção obrigatória não encontrada: {pedido}")
            continue
        if len(candidatas) != 1:
            erros.append(f"seção obrigatória ambígua: {pedido} ({', '.join(s[0] for s in candidatas)})")
            continue
        secao = candidatas[0]
        if not any(chave(secao[0]).startswith(chave(p)) for p in pedidos):
            erros.append(f"seção obrigatória fora das solicitadas em --secoes: {pedido}")
        resolvidas[chave(pedido)] = secao
    if erros:
        for erro in erros:
            print(f"[erro] {erro}")
        return 2
    if a.listar or not a.secoes.strip():
        for titulo, i, fim in todas:
            print(f"## {titulo} ({fim - i} linhas)")
        return 0

    partes = []
    if a.cabecalho:
        partes.append("\n".join(cabecalho(linhas)))
    faltam = []
    for pedido in pedidos:
        if chave(pedido) in resolvidas:
            achou = [resolvidas[chave(pedido)]]
        else:
            achou = [s for s in todas if chave(s[0]).startswith(chave(pedido))]
        if not achou:
            faltam.append(pedido)
            continue
        for titulo, i, fim in achou:
            partes.append("\n".join(linhas[i:fim]).rstrip())
    print("\n\n".join(p for p in partes if p))
    if faltam:
        nomes = ", ".join(t for t, _, _ in todas)
        print(f"\n[aviso] seção não encontrada: {', '.join(faltam)}. Seções da ficha: {nomes}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
