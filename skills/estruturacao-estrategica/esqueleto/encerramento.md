# Esqueleto · Encerramento

Base: `../base-de-todo-encontro.md` vale antes deste esqueleto. Operação: `/ee-trieme:encerramento`.

**Pergunta:** o que o cliente contratou foi entregue, com prova, e o que sobrou tem dono?
**Quando:** sempre, no fim da Semana 5. A EE termina com a entrega ao cliente.
**Onde:** `<cliente>/Encerramento/`. A pasta vira `Handoff/` quando o cliente contrata o Executar (`handoff-executar.md`).

## As duas saídas

| Saída | Quando | O que fecha a ficha |
|---|---|---|
| Encerramento | Sempre | Matriz do Contrato toda em "enviado", com data e evidência (ou "pendente", nas condições abaixo); nota do cliente e Medição da Semana 5 no registro interno; pendências com dono do lado do cliente; "EE concluída em dd/mm" |
| Handoff para o Executar | No PED ou até 30 dias depois, se o cliente contratar o Executar | O esqueleto do Handoff, com o aceite do CSAM, mais tudo o que o Encerramento fecha |

## O que a pasta tem

1. `Mensagem final - <Nome>.md`: modelo da Semana 5 (`padrao/mensagens-pos-encontro.md`), com a linha de status dos entregáveis.
2. `Pendências - <Nome>.md`: cada pendência com dono do lado do cliente, data e o que não será concluído sem ela.

## Regras

- "Enviado" e "pronto" valem com arquivo na pasta e link que abre (base B12).
- **Linha "pendente" na matriz** vale só com as três condições juntas: a pendência é do cliente; há 2 pedidos por escrito, cada um com data; o entregável foi enviado em versão limitada, e a limitação foi dita ao cliente, com a data registrada na ficha. A linha traz o dono do lado do cliente, as datas dos 2 pedidos e o que a versão limitada não cobre. Pendência do consultor nunca vale: o item fica "em produção" e a EE não fecha.
- **O forecast não bloqueia o encerramento.** Sem verba do cliente, ele já saiu na Semana 3 em hipótese marcada, e a verba fica em Pendências.
- A conversão para o Executar é lida da ficha no dia 31 após a Semana 5 e não condiciona o fechamento. Proposta em negociação é "em aberto".
- A retrospectiva é uma pergunta na ficha ("o que muda no padrão?"), enviada ao curador junto com a tabela de Calibração da Medição (`padrao/rubrica-cliente.md`).
- Dado de cliente fica fora do pacote; o que serve ao padrão vai ao curador como regra, sem nome.

## Pronto quando

- Toda linha da matriz está "enviado" ou "aprovado", com data e evidência, ou "pendente" dentro das três condições.
- A nota do cliente, a Medição e a Calibração estão no registro interno (`_ensaios-internos/registro.md`), com "não medido" onde faltou.
- Toda pendência tem dono do lado do cliente e data.
- A mensagem final saiu com a linha de status dos entregáveis.
- A ficha diz "EE concluída em dd/mm" e a pergunta da retrospectiva está registrada.
- Havendo Executar, a pasta se chama `Handoff/` e o aceite do CSAM está registrado.
