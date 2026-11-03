---
name: encerramento
description: Use quando o consultor disser "encerrar a X", "fechar a EE" ou "handoff para o Executar".
model: sonnet
argument-hint: "[Nome do cliente]"
---

# Encerramento

`/ee-trieme:encerramento <Nome>`. O que fecha e quando está em `esqueleto/encerramento.md`; este guia traz a operação.

## O que gera

`Encerramento/` com a mensagem final e a lista de pendências, a ficha fechada com "EE concluída em dd/mm" e, havendo Executar, a pasta `Handoff/` com as duas peças.

## Ler antes

1. `${CLAUDE_PLUGIN_ROOT}/skills/estruturacao-estrategica/base-de-todo-encontro.md`.
2. `${CLAUDE_PLUGIN_ROOT}/skills/estruturacao-estrategica/esqueleto/encerramento.md`.
3. Havendo Executar: `${CLAUDE_PLUGIN_ROOT}/skills/estruturacao-estrategica/esqueleto/handoff-executar.md`.
4. A ficha do cliente.

## Passos

1. **Conferir a matriz** na seção Contrato: todo item com "enviado em dd/mm" e evidência. Item sem evidência: não feche; liste o que falta ao consultor. Exceção: linha "pendente", só se a pendência é do cliente, com 2 pedidos por escrito e datados e o entregável em versão limitada, dita ao cliente (condições em `esqueleto/encerramento.md`). Pendência do consultor nunca é "pendente". O forecast não bloqueia o fechamento.
2. **Fechar a ficha.** Nota do cliente da Semana 5 e linha de Medição no registro interno (`_ensaios-internos/registro.md`), com "não medido" onde faltar. Pendências que ficaram, cada uma com dono do lado do cliente e data. Marque "Encerramento" na Status com a data e escreva "EE concluída em dd/mm" em `etapa`.
3. **Pasta `Encerramento/`.** `Mensagem final - <Nome>.md` (modelo da Semana 5 em `${CLAUDE_PLUGIN_ROOT}/padrao/mensagens-pos-encontro.md`, com a linha de status dos entregáveis) e `Pendências - <Nome>.md`.
4. **Executar.** Contratado no PED ou até 30 dias depois: renomeie `Encerramento/` para `Handoff/` (o conteúdo fica) e monte as duas peças pelo esqueleto do Handoff, com o aceite do CSAM. Sem Executar, a pasta continua `Encerramento/`.
5. **Retrospectiva.** Na ficha, em "Encerramento" (seção Pendências), escreva a pergunta "o que muda no padrão?" para o curador e confira que a Calibração, na Medição do registro interno, está preenchida (nota simulada × real, objeções previstas × ocorridas, ajustes da mesa aplicados).
6. **Conversão.** O gestor registra no dia 31 após a Semana 5, na Medição do registro interno. Antes, deixe a data calculada na ficha.

## Comando

Peça 1 do Handoff, HTML para DOCX:

```
python "${CLAUDE_PLUGIN_ROOT}/scripts/html_para_docx.py" "<entrega.html>" --consultor "${user_config.consultor_nome}" --cargo "${user_config.consultor_cargo}" --foto "EE/foto-consultor.jpg"
```

## Onde salvar

`Encerramento/` ou `Handoff/` na pasta do cliente, a ficha e o registro interno. Nada dentro de `${CLAUDE_PLUGIN_ROOT}`.

## Verificação

- Matriz toda em "enviado" ou "aprovado", com data; "pendente" só nas condições do esqueleto.
- Toda pendência tem dono e data.
- Handoff: aceite do CSAM registrado.

## Mensagem

A mensagem final ao cliente fica em `Encerramento/`. Quem envia é o consultor.

## Anti-exemplos

- Errado: marcar "enviado" sem arquivo na pasta. Certo: "em produção" até o arquivo existir e o link abrir.
- Errado: criar `Handoff/` sem Executar contratado. Certo: `Encerramento/` até a contratação.
- Errado: contar proposta em negociação como "não converteu". Certo: "em aberto".
