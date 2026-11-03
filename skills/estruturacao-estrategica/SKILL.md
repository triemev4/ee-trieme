---
name: estruturacao-estrategica
description: 'Maestro da Estruturação Estratégica (EE) da Trieme & Co. Use quando o consultor pedir o andamento ou o passo seguinte de um cliente: "próximo passo da <cliente>", "vamos preparar a semana N", "como está a <cliente>", "o que falta", "rodar a EE". Também para consultar o fluxo, a hierarquia ou o racional da EE. Pedido de cliente novo ou pasta nova: oriente o comando /ee-trieme:novo-cliente <Nome>, sem criar sozinho.'
argument-hint: "[cliente]"
model: sonnet
---

# Estruturação Estratégica · maestro

Descobre a etapa pela ficha, confere o que bloqueia e chama o guia da etapa. Arquivos deste guia: `${CLAUDE_PLUGIN_ROOT}/skills/estruturacao-estrategica/` (`base-de-todo-encontro.md`, `rotina-pos-encontro.md` e `esqueleto/`). Padrões e glossário: `${CLAUDE_PLUGIN_ROOT}/padrao/`. Por que cada regra existe: `${CLAUDE_PLUGIN_ROOT}/docs/decisoes/`.

## Racional
A EE é um diagnóstico de dores e travas que termina em plano: 5 encontros ao vivo de cerca de 1h30, em 5 semanas, com um consultor só. O Kickoff coleta os efeitos indesejados; cada semana técnica diagnostica uma camada e devolve um plano por horizonte; a Semana 5 liga os efeitos a uma causa comum, a restrição principal (Teoria das Restrições), e consolida o Mapa de Ações. O material é para o dono do negócio, que não é de marketing: pouco e bom.

| # | Encontro | Pergunta que responde | Sai com |
|---|---|---|---|
| 1 | Kickoff | O que dói, o que já sabemos e o que falta saber? | Dados mínimos com classe (B13), critério de sucesso nas palavras do cliente, seção Meta, condições e efeitos indesejados, Registro do Kickoff |
| 2 | Pesquisa de Mercado | O mercado comporta a meta? Contra quem e para quem? | Tamanho do mercado, concorrência, ICP, PUV com prova, plano por horizonte |
| 3 | Diagnóstico de Marketing | Os canais atraem e medem? Onde investir primeiro? | Auditoria por frente, forecast em 3 cenários, maturidade fechada, plano por horizonte |
| 4 | Diagnóstico Comercial | O comercial converte a demanda? Onde perde? | Cliente oculto, funil, CRM desenhado, Horizontes confirmados, plano por horizonte |
| 5 | Planejamento Estratégico + Entregáveis | Qual é a restrição principal e como atacá-la? | Restrição provada, Mapa de Ações, entregáveis da matriz, decisão sobre o Executar |

## O que o maestro faz
1. Descobre o cliente: o nome da frase, ou `EE/Clientes/Clientes.md` (vários ativos: pergunta qual). Sem `EE/CLAUDE.md`, pede `/ee-trieme:instalar`. Cliente sem pasta, pede `/ee-trieme:novo-cliente <Nome>`. Os dois comandos só o consultor dispara.
2. Lê Status e o resumo opcional da LP: `python "${CLAUDE_PLUGIN_ROOT}/scripts/ler_ficha.py" "EE/Clientes/<N>. <Nome>/<Nome>.md" --cabecalho --secoes "Status, Landing page"`. O primeiro passo aberto é a etapa semanal. Ausência da seção LP significa decisão não registrada, não uma recusa.
3. Confere os dados "Bloqueia" de Dados mínimos que alimentam a etapa (B13). Pendência vencida só bloqueia quando sua ausência impede esta atividade; diga qual é, quem responde e até quando. Dependência de foto ou MCP da LP não impede preparar ou realizar a S4.
4. Sem bloqueio da semana, chama o guia da etapa com o nome do cliente. O maestro mantém a leitura curta de Status e LP; cada guia da etapa consulta as seções pertinentes da ficha, incluindo Direcionamento, Restrição, Pontos, soluções e estrutura, Decisões por encontro e Contexto do consultor quando alimentarem o trabalho. Entre S3 concluída e S4, decisão LP ausente vai ao passo 1 de `/ee-trieme:landing-page <Nome>` para conferir contrato e perguntar ao consultor. LP confirmada e ainda em insumos/preparo segue ao mesmo guia para a primeira versão. Depois retorna à S4. Pendência da LP não bloqueia o encontro; se a dependência continua sem mudança, informa a pendência e segue, sem repetir a tentativa.
5. Para "como está" e "o que falta", responde em até 5 linhas com Status, resumo da LP quando aplicável e Pendências, sem chamar produção. Pedido explícito de LP segue ao seu guia, que confere o contrato.

| Passo aberto na Status | Guia | Pronto quando |
|---|---|---|
| Passagem da venda | `/ee-trieme:passagem-venda` | Formulário conferido contra contrato e call; seção Contrato preenchida |
| Pré-Kickoff | `/ee-trieme:kick-off` | Matriz com visto do gestor; diferença de prazo formalizada; formulário de 48 h enviado; nota de preparo e deck prontos; verificador sem erro |
| Kickoff realizado e Pós-Kickoff | `/ee-trieme:kick-off` (passo 6 para o pós) | Portão B13 cumprido; % confirmado e % com pendência na ficha; Registro, dados mínimos e mensagem prontos |
| Semana 2 | `/ee-trieme:pesquisa-mercado` | HTML e DOCX com o checklist B12; ensaio e avaliador feitos e cada ajuste e corte decidido; mensagem pronta; ficha atualizada |
| Semana 3 | `/ee-trieme:diagnostico-marketing` | Idem, com maturidade fechada e forecast na ficha |
| Semana 4 | `/ee-trieme:diagnostico-comercial` | Idem, com Horizontes confirmados |
| Entregáveis de criação produzidos e revisados | `/ee-trieme:plano-final` | Cada item de criação com arquivo em `Entregaveis/` e status real; LP retomada do módulo próprio |
| Mesa com o cliente na cabeceira (entre as Semanas 4 e 5) | `/ee-trieme:mesa-cliente <Nome>` | Ata de até 30 linhas no registro interno; consultor decidiu cada ajuste e cada divergência |
| Semana 5 | `/ee-trieme:plano-final` | HTML e DOCX com o checklist B12; ajustes aceitos da mesa aplicados; ensaio feito e cortes decididos; restrição provada; entregáveis com link; mensagem pronta |
| Encerramento | `/ee-trieme:encerramento <Nome>` | Matriz toda "enviado" com data e evidência; "EE concluída em dd/mm". Handoff só com Executar contratado. Conversão no dia 31: só lembrete, o gestor registra |

## O ciclo de cada semana
Ler (base, esqueleto, as seções da ficha que o guia pede e os insumos novos) · perguntar uma vez, com a resposta recomendada · produzir pelo molde e pelos scripts · revisar numa rodada (ensaio e, na Semana 2, avaliador) · conferir uma vez no fim · o consultor decide e envia · depois da reunião, a rotina pós-encontro. Os passos com comandos estão no guia de cada etapa.

**Uma conversa por semana.** A conversa longa custa a cada resposta (no primeiro teste real, uma conversa só chegou a 390 mil tokens por resposta). Ao fechar cada semana, termine a resposta com este aviso: "Semana N fechada. Abra uma conversa nova (`/clear`) antes da próxima: a ficha guarda tudo o que a próxima semana precisa."

**Modelo dos agentes.** Todo guia que chama um agente passa `model: "sonnet"` na chamada, porque o parâmetro da chamada vale mais que o do arquivo do agente. As exceções são a cabeceira da mesa e o `designer-lp-stitch`: o guia chama os dois sem passar `model`, e eles rodam no modelo do próprio arquivo (opus), porque os dois julgam qualidade (o plano e o visual).

Ficam com o consultor: enviar qualquer material, toda ação com o cliente, decidir a trava e a restrição principal, aprovar mudança de guia (curador). Os gatilhos do pacote (painel ao abrir a sessão, verificação ao gravar um HTML, lembrete da ficha e medição de uso ao fim da tarefa) rodam sozinhos; aviso de gatilho se trata antes de seguir. Relatório de uso para a banca: `python "${CLAUDE_PLUGIN_ROOT}/scripts/relatorio_uso.py" "<pasta EE>"`.

## Hierarquia
Base > esqueleto da semana > guia da etapa > padrões > referências visuais neutras, que orientam apenas o layout; nas Semanas 3 a 5 o layout vem do molde (`moldes/`). Divergência entre arquivos: vale o de cima, e o consultor avisa o curador, que corrige no pacote. Ninguém grava dentro da pasta do pacote.

Essa hierarquia governa os encontros e decks. A LP segue o contrato, a régua de evidência/escrita e `skills/landing-page/`; estrutura de deck, PSE visível e paleta Trieme não são seu molde. Responsabilidades e fontes: `docs/arquitetura.md`.

## Cliente em curso quando o padrão muda
A entrega em preparo segue na versão em que começou; a nova vale a partir da seguinte. A ficha pode ser atualizada a qualquer momento. Regras de conteúdo entram na próxima semana ainda não produzida. Pastas, nomes e instalação mudam só entre clientes.
