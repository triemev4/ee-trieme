# Verificação da distribuição 1.4.0

Verificação em 17/11/2026, com Python 3.12 no Windows. A 1.4.0 acrescenta `/ee-trieme:uso-tokens`, `/ee-trieme:tempo-etapas` e `scripts/monitor_uso.py` (só leitura); o resto do pacote é o da 1.3.0.

- `python tests/testar_distribuicao.py --saida <pasta externa>`: oito testes aprovados. Os sete da 1.3.0 (estrutura/JSON/Python, credenciais e identificadores privados, referências visuais, geração de Kickoff/Registro/Pesquisa, moldes S3–S5 e caminhos operacionais documentados) e o novo `test_08_monitor_de_uso`, que grava uma sessão sintética pela medição real (`scripts/medir_uso.py`) e confere as leituras de tokens, tempo e conversa.
- Cabeçalho das 16 skills lido como YAML, sem erro.
- O monitor foi exercitado numa pasta EE fictícia com dois clientes (sessões que misturaram semanas e clientes, horas em vários formatos, célula ilegível, Handoff) e numa conversa real do Claude Code, só leitura.
- **Não repetido nesta versão:** `claude plugin validate --strict` e a instalação real do marketplace em configuração isolada. A máquina que preparou a 1.4.0 não tinha o CLI do Claude Code. Na 1.3.0 (03/11/2026, Claude Code CLI 2.1.304) os manifests passaram sem erros nem avisos e a instalação reconheceu 14 skills, sete agentes e três eventos de gatilho; os manifests mudaram só no número da versão.

Essas verificações demonstram instalação e montagem do pacote; não medem qualidade consultiva, resultado comercial ou tempo economizado. Não foi executada uma EE real para esta publicação. A primeira utilização pela equipe dentro do Orca continua sendo a verificação do ambiente de cada consultor.

Para repetir o teste, instale as dependências de `scripts/requirements.txt` e rode o comando acima. A pasta indicada em `--saida` precisa ficar fora da pasta do plugin.
