---
name: passagem-venda
description: Use quando o consultor disser "passagem da venda", "conferir o formulário do closer", "o que foi vendido para a X" ou antes de agendar o Kickoff.
model: sonnet
argument-hint: "[Nome do cliente]"
---

# Passagem da venda

`/ee-trieme:passagem-venda <Nome>`. O Kickoff só é agendado com esta conferência feita.

## O que gera

A seção Contrato da ficha preenchida, a Persona do cliente semeada, o Contexto do consultor atualizado com as fontes de venda disponíveis, a lista de divergências e, no cabeçalho da ficha, `decisor` (função), `formato` (hipótese), `setor` e `nda`.

## Ler antes

1. `${CLAUDE_PLUGIN_ROOT}/skills/estruturacao-estrategica/base-de-todo-encontro.md` (B0 e B10).
2. A ficha `EE/Clientes/<N>. <Nome>/<Nome>.md`.
3. Em `0. Inputs e Transcrições/`: o formulário do closer, o contrato e a transcrição da call de venda. Se houver transcrição ou gravação de Growth Class, leia junto com a call; compare meta, prazo, formato e cobrança e preserve a fonte de cada resposta. PDF e planilha por `_texto/`, nunca o original: `python "${CLAUDE_PLUGIN_ROOT}/scripts/extrair_insumos.py" "EE/Clientes/<N>. <Nome>/0. Inputs e Transcrições"` se faltar ou se houver insumo novo.

## Passos

1. **Formulário.** Há formulário do closer: use-o. Não há e passou menos de 2 dias úteis da assinatura: escreva ao closer (um parágrafo, com os campos de `${CLAUDE_PLUGIN_ROOT}/modelos/formulario-venda.md`) e pare. Passaram 2 dias úteis: copie o modelo para `0. Inputs e Transcrições/Formulário da venda - <Nome>.md`, preencha pela transcrição da call e escreva "preenchido pelo consultor" no topo. Só há gravação sem transcrição: peça a transcrição e pare.
2. **Conferir.** Compare os campos do formulário (produto, semanas e entregáveis, prazo, promessas, garantias, desconto, decisor e participantes, evento crítico, NDA) com o contrato e com a call. Havendo Growth Class, compare também a meta, o prazo, o formato e a cobrança entre as duas conversas. Diferenças ficam explícitas com fonte e tempo; não escolha silenciosamente uma versão.
3. **Divergências.** Liste em tabela: campo · formulário · contrato · call de venda · Growth Class (se houver) · tratamento. Cada divergência vira pergunta ao cliente e linha em Pendências da ficha (dono e data). Até a resposta, vale a ordem da B0. Campo que nenhuma fonte traz fica "não informado", com pendência, nunca preenchido por dedução.
4. **Preencher a seção Contrato.** Matriz só com os itens do contrato; correspondência (EE 3.0); promessas da venda com o tempo na gravação e a pendência "confirmar com o closer"; data final contratual; calendário dos encontros; decisão de 4 ou 5 encontros (padrão 5); formulário de 48 h; origem (formulário do closer ou "preenchido pelo consultor").
   **Conferência do pacote:** use como referência a EE padrão (3 criativos de performance, 1 LP, Manual de Identidade Visual e Manual de Copy) e a EE pocket (conferência de uma LP existente). O contrato assinado é a fonte dos entregáveis: pocket não autoriza produção de LP; qualquer diferença entre pacote e contrato vira pergunta ao closer e pendência. Não prometa item de referência que não esteja contratado.
5. **Prazo (B10).** Data final contratual antes da Semana 5 do calendário: registre a diferença e a pendência de formalizar por escrito com o cliente, antes da Semana 2, a lista dos entregáveis e o critério de aceite de cada um.
6. **Portão.** Marque "Passagem da venda conferida" na Status com a data e atualize `etapa` no cabeçalho. Antes de falar em agendar o Kickoff, procure nos insumos (`0. Inputs e Transcrições/_texto/indice.md` e os nomes dos arquivos) uma transcrição ou gravação do Kickoff:
   - **Achou:** o Kickoff já aconteceu e não espera o visto. Pergunte ao consultor a data e a hora, se o arquivo não trouxer. Marque "Kickoff realizado" com essa data, registre o visto do gestor como pendência com dono e data que não bloqueia, e o próximo passo é o pós-Kickoff (`/ee-trieme:kick-off`, passo 6).
   - **Não achou:** divergência aberta, o Kickoff só é agendado depois do visto do gestor sobre cada uma; registre o visto na ficha.
7. **Contexto e Persona.** Registre em Contexto do consultor quais fontes existem (call de venda e Growth Class, quando houver), os fatos relevantes de cada uma e as divergências ainda abertas, sempre com fonte/data. Semeie a seção "Persona do cliente" pela transcrição da call de venda: só o que o cliente disse, com a fonte (call e minuto) em cada linha, até 40 linhas, regras na B9. O que a call não traz fica em branco.
8. Grave as horas em "Passagem da venda", na Medição do registro interno (`_ensaios-internos/registro.md`).

## Onde salvar

Ficha e `0. Inputs e Transcrições/`. Nada dentro de `${CLAUDE_PLUGIN_ROOT}`.

## Verificação

- Cada linha da matriz tem item do contrato, semana da EE e data-limite, ou pendência com dono e data.
- Cada promessa da venda tem o tempo na gravação.
- Decisor e participantes por função.

## Mensagem

Ao closer (interna, curta): as divergências e o que falta, com o prazo de 1 dia útil. Nada vai ao cliente nesta etapa.

## Anti-exemplos

- Errado: "Garantia: não há", com o formulário em branco. Certo: "não informado" e pendência com dono e data.
- Errado: escolher o formulário quando ele contradiz o contrato. Certo: valer o contrato até a resposta do cliente e listar a divergência.
- Errado: perguntar ao cliente, no Kickoff, sobre uma promessa que o closer não confirmou. Certo: confirmar antes com o closer.
