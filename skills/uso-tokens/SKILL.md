---
name: uso-tokens
description: 'Use quando o consultor ou o gestor perguntar pelo gasto de tokens da EE: "quanto gastei de token", "quanto essa conversa já pesou", "qual etapa gasta mais", "tokens da <cliente>", "relatório de tokens", "estou perto do limite do plano?". Mostra a conversa aberta, um cliente ou todos, por etapa. Só lê.'
model: sonnet
argument-hint: "[conversa | <cliente> | todos]"
---

# Gasto de tokens por etapa

`/ee-trieme:uso-tokens [conversa | <cliente> | todos]`. Só lê e mostra: não grava na ficha nem no registro.

## De onde vem o número

- **Por etapa:** o gatilho de fim de tarefa grava sozinho uma linha por sessão na Medição do registro interno de cada cliente (`_ensaios-internos/registro.md`), com a etapa da pasta mais mexida. Este guia só soma essas linhas.
- **Conversa aberta:** lida na hora do histórico local da própria conversa.
- Nada sai da máquina. Sem linha no registro é "não medido", nunca estimado.

## Passos

1. Modo por `$ARGUMENTS`: vazio ou "conversa" → conversa aberta; nome de cliente → aquele cliente; "todos" → todos. Pergunta sobre etapa ou cliente sem argumento → todos.
2. Rode o comando do modo, a partir da pasta aberta.
3. Responda em até 8 linhas: o número que responde à pergunta, a etapa mais pesada e o aviso que o script der. Tabela inteira só se pedirem.
4. Aviso de conversa pesada: diga o tamanho e recomende fechar a semana e abrir conversa nova (`/clear`), como manda o guia-mãe ("uma conversa por semana"). Não dê `/clear` por conta própria.
5. Sessão que misturou semanas ou clientes: cite as sessões listadas, porque deixam o número da etapa torto.

## Comandos

Conversa aberta:

```
python "${CLAUDE_PLUGIN_ROOT}/scripts/monitor_uso.py" conversa --sessao "${CLAUDE_SESSION_ID}"
```

Um cliente, ou todos (sem `--cliente`):

```
python "${CLAUDE_PLUGIN_ROOT}/scripts/monitor_uso.py" tokens --cliente "<Nome>"
python "${CLAUDE_PLUGIN_ROOT}/scripts/monitor_uso.py" tokens
```

Se o script não achar a pasta EE, passe o caminho da pasta que tem `Clientes/` logo depois de `tokens`. O aviso da conversa sai a partir de 150 mil tokens por resposta; outro limite: `--limite 100000`.

## Como ler

- **Novos** = entrada + cache criado: o que entrou de novo na conversa. **Saída** = o que o Claude escreveu. **Cache lido** = a conversa relida a cada resposta. Cresce com o tamanho da conversa, por isso costuma ser o maior número.
- **Por resposta** (modo conversa) = quanto cada resposta relê agora. É o número que cresce e esgota o plano: conversa longa pesa em toda resposta seguinte.
- A sessão inteira conta para uma etapa só, a da pasta mais mexida. Sessão que misturou semanas infla aquela etapa e subconta a outra.
- Sessão que mexeu em dois clientes aparece nos dois; o total geral conta uma vez.

## Verificação

- Todo número da resposta saiu do script, não de conta sua.

## Anti-exemplos

- Errado: converter em reais ou dólares. Certo: tokens; o preço depende do plano e o script não o conhece.
- Errado: chamar o total de "tokens gastos" sem separar. Certo: novos, saída e cache lido.
- Errado: estimar a etapa sem linha. Certo: "não medido".
