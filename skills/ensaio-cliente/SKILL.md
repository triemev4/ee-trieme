---
name: ensaio-cliente
description: 'Ensaio do deck com o cliente simulado antes de um encontro das Semanas 2 a 5 da Estruturação Estratégica (EE). Use quando o consultor disser "faz o ensaio do deck da semana N", "ensaia a semana N da <cliente>", "testa o deck com o cliente" ou "o cliente entenderia isso?". Use também no passo 4 das Semanas 2 a 5, com o deck completo e sem erro. Passe o nome do cliente e o número da semana; se o cliente não for citado e só houver um em Clientes/, usa esse e diz qual.'
argument-hint: "<Nome do cliente> <semana de 2 a 5>"
context: fork
agent: general-purpose
model: sonnet
background: false
---

# Ensaio com o cliente simulado

Entrada: $ARGUMENTS (nome do cliente e semana). Cliente não citado e só uma pasta em `Clientes/`: use essa e diga qual numa linha. Sem semana, ou com semana fora de 2 a 5, ou com mais de um cliente possível, devolva "ensaio não rodado: falta cliente ou semana" e pare.

`<cliente>` = `EE/Clientes/<N>. <Nome>`. Pasta da semana: `2. Pesquisa de Mercado`, `3. Diagnóstico de Marketing`, `4. Diagnóstico Comercial` ou `5. Planejamento Estratégico + Entregáveis`. Deck: o HTML da pasta que não começa com `detalhe-` nem com `_`; havendo mais de um, pergunte qual.

## Ler só isto

1. Da ficha `<cliente>/<Nome>.md`, só a seção "Persona do cliente" (do título até o próximo `## `). Persona vazia: devolva "ensaio não rodado: persona vazia" e pare.
2. A linha "Pergunta do encontro" de `${CLAUDE_PLUGIN_ROOT}/skills/estruturacao-estrategica/esqueleto/semana-N-*.md`.
3. O texto do deck, tela a tela:
   ```
   python "${CLAUDE_PLUGIN_ROOT}/scripts/extrair_telas.py" "<deck.html>"
   ```
4. `${CLAUDE_PLUGIN_ROOT}/padrao/rubrica-cliente.md`.

Nada além disso.

## Rodada

O ensaio é interno e mora em `<cliente>/_ensaios-internos/` (crie a pasta se faltar). Confira só se os arquivos existem. Sem `_ensaios-internos/ensaio-semana-N.md`: rodada 1, grave nele. Com ele: rodada 2, só se o pedido diz que o consultor a quer; grave `_ensaios-internos/ensaio-semana-N-rodada-2.md`. Sem esse pedido, ou com os dois arquivos, devolva "segunda rodada só a pedido do consultor" e pare.

## Papel

"Você é o decisor descrito na persona. Você só sabe o que está na persona e no deck. Leia como leria na reunião e reaja com as objeções e o vocabulário dele."

A nota segue a régua da rubrica. Fala que a persona não sustenta não entra.

## Saída

O arquivo da rodada, com:
1. Nota de 0 a 10 nos 5 critérios, como medida. Toda nota abaixo de 9 traz a tela e a fala que a justificam.
2. Tabela "critério de sucesso → tela que responde", uma linha por item da persona: a tela, "no DOCX", "nenhuma" ou "fica para a Semana N" com o motivo.
3. Tabela "objeção da persona → tela que responde", no mesmo formato.
4. "O que eu cortaria": até 3 telas ou blocos, cada um com o motivo (repetição, aula, não é para mim).
5. Até 3 ajustes, em ordem de impacto, cada um com a tela. Ajuste que acrescenta tela ou bloco diz o que sai no lugar.
6. A pergunta que o decisor faria e que o deck não responde.

Devolva a quem chamou os ajustes (item 5), os cortes (item 4) e a linha da tabela de ensaios do registro interno, nesta ordem de colunas: Semana, Rodada, Data, Entendimento, Fala comigo, Confiança, Ação, Valor do tempo, Prova (sim ou não), Cortes sugeridos, Arquivo e Decisão do consultor vazia. Quem chamou grava a linha e edita o deck.
