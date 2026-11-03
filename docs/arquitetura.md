# Arquitetura do pacote

`ee-trieme` é um plugin do Claude Code para guiar a execução da Estruturação Estratégica (EE). Os arquivos do plugin descrevem o método; os arquivos de cada projeto ficam na pasta de trabalho do consultor.

## Camadas

| Camada | Responsabilidade |
|---|---|
| `.claude-plugin/` | Identidade do marketplace e configuração do plugin. |
| `skills/` | Fluxos acionados por comando, incluindo instalação, encontros, pesquisa, diagnóstico e entregáveis. |
| `agents/` | Papéis especializados chamados pelos fluxos quando aplicável. |
| `padrao/` | Regras estáveis de método, escrita, análise e apresentação. |
| `modelos/` | Arquivos limpos que o instalador usa para iniciar uma pasta de trabalho. |
| `moldes/` | Estrutura de HTML para decks e scripts de preenchimento. |
| `scripts/` | Operações determinísticas de leitura, validação, geração e conversão. |
| `docs/` | Contexto arquitetural e razões técnicas resumidas. |

## Fluxo de trabalho

O consultor instala o plugin no escopo de usuário e abre uma pasta de trabalho no Claude Code. `/ee-trieme:instalar` prepara nela a estrutura `EE/`, com instruções locais, índice de clientes e configurações. Os comandos seguintes leem as fontes e decisões pertinentes ao projeto, produzem arquivos na pasta de trabalho e usam os scripts para validar formatos ou artefatos.

O plugin é tratado como material de referência. Arquivos específicos de clientes, credenciais e configurações locais ficam fora do plugin. Cada recomendação deve distinguir fatos fornecidos, fontes externas, estimativas, hipóteses e lacunas; um exemplo de documentação nunca é evidência para um projeto.

## Autoridade e precedência

Para encontros e decks, a base comum define as regras transversais; o esqueleto define sequência e escopo da semana; o guia da etapa conduz a execução; os padrões definem critérios reutilizáveis. Moldes e referências visuais orientam a forma, sem fornecer conteúdo de cliente. Se documentos divergirem, aplica-se a hierarquia declarada em `skills/estruturacao-estrategica/SKILL.md`, e a divergência deve ser registrada para correção do pacote.

A landing page segue a matriz contratual e seus próprios guias de evidência, copy, direção e aceite. Ela não herda automaticamente a estrutura de deck, a paleta ou os componentes visuais dos encontros.

## Limites

O plugin orienta o trabalho e valida artefatos locais; não substitui decisão do consultor, aprovação do cliente, fonte primária, contrato ou configuração de acesso a serviços externos. Integrações opcionais dependem da ferramenta e da conta configuradas no ambiente de trabalho.
