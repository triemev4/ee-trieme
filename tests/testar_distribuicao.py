"""Verifica o snapshot público usando somente os arquivos distribuídos.

Uso: python tests/testar_distribuicao.py [--saida PASTA_FORA_DO_PACOTE]
Dependências: pip install -r scripts/requirements.txt
Saídas sintéticas ficam fora do pacote. Não acessa a rede nem procura dados de clientes.
Estes testes verificam distribuição e montagem, não aprovam uma entrega real.
"""
import sys
sys.dont_write_bytecode = True
import argparse
import base64
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
import unittest
from urllib.parse import unquote, urlsplit
from zipfile import ZipFile

from bs4 import BeautifulSoup

RAIZ = Path(__file__).resolve().parents[1]
SAIDA = None
# Impressões digitais de identificadores privados: o teste não redistribui os nomes.
IDENTIFICADORES_PRIVADOS = {
    "92f404fff8fe3280ebc5dfa3f00517297a5bdad79633fd1794dd74576955bc89",
    "579aac4a9a9219ad18806172862e1aa2cdab65a60eac681b5407aedf8424a02a",
}
EXT_TEXTO = {".py", ".md", ".json", ".html", ".txt", ".cmd", ".toml", ".yml", ".yaml"}


def arquivos_publicos():
    return sorted(p for p in RAIZ.rglob("*") if p.is_file()
                  and not set(p.relative_to(RAIZ).parts) & {".git", ".venv", "__pycache__"})


def ler_json(caminho):
    return json.loads(caminho.read_text(encoding="utf-8-sig"))


def sintetizar(obj):
    """Completa os modelos vazios com conteúdo explicitamente inventado para o smoke."""
    if isinstance(obj, dict):
        return {k: sintetizar(v) for k, v in obj.items() if not k.startswith("_")}
    if isinstance(obj, list):
        return [sintetizar(v) for v in obj]
    if isinstance(obj, str) and "PREENCHER" in obj:
        return "Exemplo inteiramente fictício para teste de distribuição"
    return obj


def carregar(nome, caminho):
    spec = importlib.util.spec_from_file_location(nome, caminho)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


class DistribuicaoPublica(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.saida = SAIDA.resolve()
        if cls.saida == RAIZ or RAIZ in cls.saida.parents:
            raise ValueError("A saída precisa estar fora do pacote")
        cls.saida.mkdir(parents=True, exist_ok=True)

    def comando(self, *args):
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTHONUTF8="1")
        r = subprocess.run([sys.executable, "-B", *map(str, args)], cwd=self.saida,
                           env=env, capture_output=True, text=True, encoding="utf-8", timeout=90)
        self.assertEqual(r.returncode, 0, f"Falha executando {Path(args[0]).name}:\n{r.stdout}\n{r.stderr}")
        return r

    def conferir_html(self, caminho):
        soup = BeautifulSoup(caminho.read_text(encoding="utf-8"), "html.parser")
        self.assertTrue(soup.title and soup.title.get_text(strip=True), caminho.name)
        self.assertIsNotNone(soup.select_one("section.hero"), caminho.name)
        self.assertIsNotNone(soup.select_one(".chrome"), caminho.name)
        self.assertTrue(soup.find("style"), caminho.name)
        self.assertTrue(soup.find("script"), caminho.name)
        self.assertTrue(soup.select_one(".chrome img, .chrome svg"), caminho.name)
        self.assertTrue(soup.select_one("#navdots"), caminho.name)
        for el in soup.find_all(True):
            for attr in ("data-t", "data-lista", "data-opcional", "data-condensavel", "data-img", "data-estilo", "data-classe", "data-num"):
                self.assertNotIn(attr, el.attrs, f"Marcação residual em {caminho.name}: {attr}")
        for el in soup.find_all(src=True):
            src = el["src"]
            if src.startswith("data:"):
                if ";base64," in src:
                    self.assertTrue(base64.b64decode(src.split(",", 1)[1], validate=True))
            elif not urlsplit(src).scheme and not src.startswith("//"):
                self.assertTrue((caminho.parent / unquote(urlsplit(src).path)).is_file(), f"Recurso ausente em {caminho.name}")
        ids = {el.get("id") for el in soup.find_all(id=True)}
        for el in soup.select('a[href^="#"]'):
            self.assertIn(unquote(el["href"][1:]), ids, f"Âncora ausente em {caminho.name}")
        return soup

    def conferir_docx(self, caminho):
        self.assertTrue(caminho.is_file(), caminho.name)
        with ZipFile(caminho) as z:
            xml = z.read("word/document.xml").decode("utf-8")
            self.assertIn("Exemplo", xml, caminho.name)
            self.assertIn("[Content_Types].xml", z.namelist())

    def test_01_metadados_e_estrutura(self):
        plugin = ler_json(RAIZ / ".claude-plugin/plugin.json")
        self.assertEqual(plugin["name"], "ee-trieme")
        self.assertEqual(plugin["version"], "1.3.0")
        self.assertTrue(plugin["description"])
        self.assertTrue(plugin["author"]["name"])
        mercado = ler_json(RAIZ / ".claude-plugin/marketplace.json")
        entradas = [p for p in mercado["plugins"] if p["name"] == plugin["name"]]
        self.assertEqual(len(entradas), 1)
        self.assertEqual(entradas[0].get("version", plugin["version"]), plugin["version"])
        self.assertEqual(entradas[0]["source"], "./")
        for pasta in ("agents", "skills", "hooks", "modelos", "moldes", "padrao", "scripts", "referencias/layout"):
            self.assertTrue((RAIZ / pasta).is_dir(), pasta)
        for nome in ("README.md", "scripts/requirements.txt", "hooks/ee_gatilhos.py", "hooks/run-hook.cmd"):
            self.assertTrue((RAIZ / nome).is_file(), nome)
        for p in arquivos_publicos():
            self.assertFalse(p.is_symlink(), str(p.relative_to(RAIZ)))
            self.assertNotIn(p.suffix.lower(), {".docx", ".pdf", ".xlsx", ".zip", ".log", ".jsonl", ".pem", ".key", ".p12", ".sqlite"}, str(p.relative_to(RAIZ)))
            self.assertFalse(p.name == ".env" or p.name.startswith(".env."), str(p.relative_to(RAIZ)))
            self.assertFalse(set(p.relative_to(RAIZ).parts) & {"casos", "estudos", "Clientes", ".claude"}, str(p.relative_to(RAIZ)))
            if p.suffix == ".json":
                ler_json(p)
            if p.suffix == ".py":
                compile(p.read_text(encoding="utf-8-sig"), str(p), "exec")

    def test_02_identificadores_privados_e_credenciais(self):
        padroes = {
            "chave privada": r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----",
            "token de provedor": r"\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,}|AIza[0-9A-Za-z_-]{35}|sk-(?:proj-)?[A-Za-z0-9_-]{40,}|AKIA[0-9A-Z]{16})\b",
            "JWT": r"\beyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}\b",
            "segredo literal": r'''\b(?:api[_-]?key|client[_-]?secret|password|senha|access[_-]?token)\s*[:=]\s*["'][A-Za-z0-9_+/=-]{24,}["']''',
            "URL com autenticação": r"https?://[^\s/:<>]+:[^\s/@<>]+@",
            "caminho local pessoal": r"(?:[A-Z]:[\\/](?:Users|Documentos)[\\/]|\x2fUsers\x2f|\x2fhome\x2f)[^\s<>\"']+",
        }
        problemas = []
        for p in arquivos_publicos():
            if p.suffix not in EXT_TEXTO and p.name not in {"gatilho", ".gitignore"}:
                continue
            texto = p.read_text(encoding="utf-8-sig")
            rel = str(p.relative_to(RAIZ))
            # Tokeniza nomes também quando aparecem em domínios, slugs ou handles.
            tokens = re.findall(r"[^\W_]+", texto.lower(), re.UNICODE)
            if any(hashlib.sha256(t.encode()).hexdigest() in IDENTIFICADORES_PRIVADOS for t in tokens):
                problemas.append(rel + ": identificador privado")
            for tipo, padrao in padroes.items():
                if re.search(padrao, texto, re.I):
                    problemas.append(rel + ": " + tipo)
        self.assertEqual(problemas, [], "\n".join(problemas))

    def test_03_referencias_layout_extraiveis(self):
        for nome, pasta, arquivo in (("kickoff", "kick-off", "gerar_kickoff.py"), ("pesquisa", "pesquisa-mercado", "gerar_pesquisa.py")):
            with self.subTest(gerador=nome):
                modulo = carregar("publico_" + nome, RAIZ / "skills" / pasta / "gerador" / arquivo)
                self.assertTrue(modulo.REF.is_file())
                self.assertIn(RAIZ / "referencias/layout", modulo.REF.parents)
                head, chrome, hero, script = modulo.extrair_referencia("Exemplo Fictício")
                self.assertIn("<head", head)
                self.assertIn("<style", head)
                self.assertIn("Exemplo Fictício", head)
                self.assertIn("Exemplo Fictício", chrome)
                self.assertTrue(re.search(r"<(img|svg)\b", chrome))
                self.assertTrue(hero.strip())
                self.assertIn("<script", script)
                self.assertIn("navdots", script)

    def test_04_kickoff_e_registro(self):
        base = RAIZ / "skills/kick-off/gerador"
        for modelo, gerador, opcoes in (("modelo-conteudo.json", "gerar_kickoff.py", ["--docx"]), ("modelo-registro.json", "gerar_dossie.py", [])):
            with self.subTest(gerador=gerador):
                dados = sintetizar(ler_json(base / modelo))
                dados.update(cliente="Exemplo Fictício", slug="exemplo-ficticio")
                entrada = self.saida / modelo
                entrada.write_text(json.dumps(dados, ensure_ascii=False), encoding="utf-8")
                self.comando(base / gerador, entrada, self.saida, "--consultor", "Exemplo Consultor", "--cargo", "Consultor", *opcoes)
        self.conferir_html(self.saida / "kickoff-exemplo-ficticio.html")
        self.conferir_docx(self.saida / "kickoff-exemplo-ficticio.docx")
        self.conferir_docx(self.saida / "registro-kickoff-exemplo-ficticio.docx")

    def test_05_pesquisa_modelo_completo(self):
        base = RAIZ / "skills/pesquisa-mercado/gerador"
        dados = sintetizar(ler_json(base / "modelo-pesquisa.json"))
        dados.update(cliente="Exemplo Fictício", slug="exemplo-ficticio")
        entrada = self.saida / "pesquisa-conteudo.json"
        entrada.write_text(json.dumps(dados, ensure_ascii=False), encoding="utf-8")
        self.comando(base / "gerar_pesquisa.py", entrada, "--validar")
        self.comando(base / "gerar_pesquisa.py", entrada, self.saida, "--consultor", "Exemplo Consultor", "--cargo", "Consultor")
        self.conferir_html(self.saida / "pesquisa-mercado-exemplo-ficticio.html")
        self.conferir_docx(self.saida / "pesquisa-mercado-exemplo-ficticio.docx")

    def test_06_moldes_semanas_3_a_5(self):
        for n in (3, 4, 5):
            with self.subTest(semana=n):
                html = self.saida / f"semana-{n}.html"
                self.comando(RAIZ / "scripts/preencher_molde.py", RAIZ / f"moldes/semana-{n}.html", RAIZ / f"moldes/semana-{n}.textos.json", html)
                soup = self.conferir_html(html)
                self.assertGreater(len(soup.find_all("section")), 3)
                self.comando(RAIZ / "scripts/html_para_docx.py", html, html.with_suffix(".docx"), "--consultor", "Exemplo Consultor", "--cargo", "Consultor")
                self.conferir_docx(html.with_suffix(".docx"))

    def test_07_caminhos_operacionais_documentados(self):
        problemas = []
        for p in RAIZ.rglob("*.md"):
            texto = p.read_text(encoding="utf-8-sig")
            for target in re.findall(r'\$\{CLAUDE_PLUGIN_ROOT\}/([^`"\s]+)', texto):
                if any(c in target for c in "<>*|") or target.endswith("/"):
                    continue
                target = target.rstrip(".,;)")
                if not (RAIZ / target).exists():
                    problemas.append(f"{p.relative_to(RAIZ)}: {target}")
            for target in re.findall(r"\btests/[A-Za-z0-9_/-]+\.py\b", texto):
                if not (RAIZ / target).is_file():
                    problemas.append(f"{p.relative_to(RAIZ)}: {target}")
        self.assertEqual(problemas, [], "\n".join(problemas))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--saida", type=Path)
    args, restante = parser.parse_known_args()
    if args.saida:
        SAIDA = args.saida
        unittest.main(argv=[sys.argv[0], *restante], verbosity=2)
    else:
        with tempfile.TemporaryDirectory(prefix="ee-trieme-publico-") as temporario:
            SAIDA = Path(temporario)
            unittest.main(argv=[sys.argv[0], *restante], verbosity=2)
