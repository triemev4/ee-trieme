---
name: tempo-etapas
description: 'Use quando o consultor ou o gestor perguntar pelo tempo gasto na EE: "quanto tempo levou cada etapa", "horas da <cliente>", "estamos acima da partida?", "tempo por semana", "relatório de horas", "o que falta registrar de horas". Compara as horas registradas com a partida de 48 h e mostra o tempo das sessões com o Claude. Um cliente ou todos.'
model: sonnet
argument-hint: "[<cliente> | todos]"
---

# Tempo por etapa

`/ee-trieme:tempo-etapas [<cliente> | todos]`. Lê e mostra; só grava no registro o que o consultor disser no passo 4.

## De onde vem o número

Duas medidas, lado a lado, **nunca somadas** (o tempo com o Claude está dentro do preparo e do pós do consultor):

- **Horas do consultor:** o que ele registra na Medição do registro interno (`_ensaios-internos/registro.md`): Preparo, Reunião e Pós de cada encontro; Passagem da venda, Criação, Ensaio, Mesa, Encerramento e Retrabalho. A partida é a do modelo do registro: 48 h, ou 49 h com Handoff.
- **Com o Claude:** tempo ativo das sessões, gravado sozinho pelo gatilho de fim de tarefa (pausa de mais de 15 min não conta).

## Passos

1. Modo por `$ARGUMENTS`: nome de cliente → aquele cliente; vazio ou "todos" → todos.
2. Rode o comando.
3. Responda em até 8 linhas: registrado contra partida nas etapas medidas, a etapa mais acima da partida, o retrabalho, se houver, e o que falta registrar.
4. Se houver "Falta registrar", ofereça preencher com o consultor: pergunte as horas de cada item, um por vez. Grave no registro só o que ele disser, na célula da tabela e no formato dela ("1,5"). O que ele não souber continua "não medido".

## Comando

```
python "${CLAUDE_PLUGIN_ROOT}/scripts/monitor_uso.py" tempo --cliente "<Nome>"
python "${CLAUDE_PLUGIN_ROOT}/scripts/monitor_uso.py" tempo
```

Se o script não achar a pasta EE, passe o caminho da pasta que tem `Clientes/` logo depois de `tempo`.

## Como ler

- **Situação:** medido (todos os itens da etapa têm hora), parcial (falta algum), não medido.
- **Diferença** só sai em etapa medida por inteiro. Na média de todos, entram só os clientes com a etapa medida por inteiro.
- **Ensaios:** a partida é 0,25 h por linha lançada (uma rodada por semana). **Criação:** compara com as 6 h do total; no meio da EE, o registrado ainda vai crescer.
- **Handoff:** a partida do Encerramento vira 1,5 h quando existe a pasta `Handoff/` do cliente ou uma linha "Handoff" com horas.
- Célula aceita: 1,5 · 1.5 · 2 h · 1h30 · 0:45 · 90 min. Com "estimado", conta como não medido. O que o script não lê aparece em "Célula ilegível": corrija com o consultor.

## Verificação

- Todo número da resposta saiu do script.
- Nenhuma hora gravada sem o consultor ter dito.

## Anti-exemplos

- Errado: somar o tempo com o Claude às horas do consultor. Certo: duas colunas.
- Errado: preencher "não medido" com a partida. Certo: perguntar ou deixar.
- Errado: dizer que a etapa estourou com ela ainda parcial. Certo: "parcial, falta o Pós".
