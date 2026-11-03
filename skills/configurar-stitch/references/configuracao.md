# Conexão Stitch: escopos, diagnóstico e fontes

Consulte quando a conexão falhar, houver configuração prévia ou a ferramenta do consultor diferir do guia. Os comandos ficam no `SKILL.md` desta pasta.

## Responsabilidades

| Informação | Onde vive |
|---|---|
| Credencial do consultor | Ambiente/cofre local autorizado, fora do pacote e das pastas de clientes |
| Endpoint e referência à credencial | Configuração de usuário da ferramenta que executa o MCP |
| IDs de projeto e telas de uma LP | Registro técnico dessa LP |
| Escopo contratado e aceite do material | Ficha e matriz do cliente |

O endpoint oficial é remoto. A máquina do consultor precisa de acesso ao serviço e de um cliente MCP compatível; o caminho por chave de API não exige instalar Google Cloud SDK. OAuth é uma alternativa com configuração própria, não um remédio automático para chave inválida.

No Claude Code, servidores de escopo local/projeto podem prevalecer sobre a definição do usuário. Se a alteração parecer ignorada, investigue a origem ativa sem apagar as demais. No Codex, a configuração de usuário usa `config.toml`; ambientes remotos e configurações de projeto podem mudar a configuração efetiva. Uma variável presente no terminal não prova que chegou ao processo do assistente.

## Diagnóstico orientado pelo erro

| Resultado observado | Próximo passo |
|---|---|
| Ferramentas ausentes | Conferir se o servidor carregou, configuração efetiva, escopo, conexão desabilitada e reinício do processo |
| Variável ausente | Consultor fornece a credencial pelo terminal protegido e inicia o assistente nesse ambiente |
| 401/403 | Conferir conta, chave revogada, referência do cabeçalho e acesso ao projeto; registrar somente a classe do erro |
| Conecta, mas não carrega ferramentas | Conferir compatibilidade de versão e erro de schema; consultar as notas oficiais antes de propor atualização |
| Lista vazia de projetos | A leitura funcionou; ainda não há projetos visíveis nessa conta |
| 429 ou cota esgotada | Registrar limite informado e janela de retomada; preservar trabalho e seguir as etapas independentes da EE |
| Timeout de geração/edição | Verificar se a operação concluiu no projeto antes de reenviar; preservar IDs e resposta parcial |
| Acesso ao projeto de uma LP negado | Confirmar titularidade/compartilhamento com o responsável; não criar cópia como correção automática |

Rotação de chave é feita pelo consultor nas configurações do Stitch e no armazenamento local. O segredo permanece fora de capturas, relatórios, logs e argumentos literais. Não use a chave de outro consultor para contornar acesso ou limite.

## Fontes e validade

Conferido em **30/10/2026**. Help local consultado: **Claude Code 2.1.304** e **Codex CLI 0.146.1**. Essas versões são evidência de pesquisa, não versões mínimas certificadas. Não foi realizada instalação em máquina limpa nem autenticação nova ao escrever o guia. O teste autenticado do `SKILL.md` continua obrigatório em cada ambiente.

- [Google Stitch: configuração e autenticação MCP](https://stitch.withgoogle.com/docs/mcp/setup). Explica serviço remoto, chave criada no Stitch, cabeçalho e alternativa OAuth. [Conteúdo oficial carregado pela documentação](https://app-companion-430619.appspot.com/docs/mcp/setup/index.html).
- [Claude Code: configuração MCP](https://code.claude.com/docs/en/mcp). Fonte dos escopos, transporte HTTP, expansão de variável em cabeçalhos e diagnóstico de conexão.
- [OpenAI: MCP e cabeçalhos de ambiente](https://learn.chatgpt.com/docs/extend/mcp#streamable-http-servers). Fonte de `env_http_headers`; a consulta foi feita pela ferramenta oficial OpenAI Docs.
- [Google Labs: skills do Stitch](https://github.com/google-labs-code/stitch-skills#prerequisites). Skills e conexão MCP são camadas distintas. O fluxo de LP da EE usa o MCP diretamente; não depende da instalação global desse catálogo.

Quando uma ferramenta mudar, atualize apenas a seção correspondente depois de verificar help e fonte oficial. Preserve o contrato do módulo: acesso autenticado e capacidades descobertas, sem copiar credenciais para o produto.
