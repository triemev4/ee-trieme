# Verificação da distribuição 1.3.0

Verificação em 03/11/2026, com Claude Code CLI 2.1.304 e Python 3 no Windows.

- Manifests do plugin e marketplace aprovados por `claude plugin validate --strict`, sem erros nem avisos.
- `python tests/testar_distribuicao.py --saida <pasta externa>`: sete testes aprovados. Inclui estrutura/JSON/Python, credenciais e identificadores privados, referências visuais, geração de Kickoff/Registro/Pesquisa, moldes S3–S5 e caminhos operacionais documentados.
- Os geradores foram exercitados com dados sintéticos, em saídas externas ao pacote, produzindo HTML e DOCX. A regressão de Pesquisa também foi conferida com 67 testes na preparação da distribuição.
- Instalação real do marketplace em configuração temporária do Claude, sem credenciais GitHub: versão 1.3.0 habilitada, 14 skills, sete agentes e três eventos de gatilho reconhecidos. A configuração pessoal usada no dia a dia foi preservada.
- Revisão independente de referências, links, exemplos e dados distribuídos. Os layouts contêm somente estrutura visual reutilizável; os exemplos são fictícios. Estudos, casos privados e histórico de desenvolvimento interno não compõem o repositório público.

Essas verificações demonstram instalação e montagem do pacote; não medem qualidade consultiva, resultado comercial ou tempo economizado. Não foi executada uma EE real para esta publicação. A primeira utilização pela equipe dentro do Orca continua sendo a verificação do ambiente de cada consultor.

Para repetir o teste, instale as dependências de `scripts/requirements.txt` e rode o comando acima. A pasta indicada em `--saida` precisa ficar fora da pasta do plugin.
