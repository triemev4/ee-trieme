---
name: mesa-cliente
description: 'Mesa com o cliente na cabeceira da Estruturação Estratégica (EE), entre a Semana 4 e a Semana 5: três cadeiras avaliam o plano e o cliente simulado fecha a ata. Use quando o consultor disser "roda a mesa antes da semana 5", "mesa da <cliente>", "testa o plano final com o cliente" ou quando o maestro chegar ao passo da mesa na Status da ficha.'
argument-hint: "[Nome do cliente]"
model: sonnet
---

# Mesa com o cliente na cabeceira

Sem o nome, pergunte. `<cliente>` = `EE/Clientes/<N>. <Nome>`; `<pasta>` = `<cliente>/5. Planejamento Estratégico + Entregáveis/`. Nos 3 primeiros clientes a mesa é obrigatória; depois, a calibração de `${CLAUDE_PLUGIN_ROOT}/padrao/rubrica-cliente.md` decide se fica.

## Antes

Confira e, faltando algo, diga o quê e pare:
- Semana 4 marcada na Status da ficha;
- rascunho `<pasta>/plano-final-<slug>.html` e os entregáveis de criação em `<pasta>/Entregaveis/`;
- seção "Persona do cliente" da ficha preenchida.

Rode e guarde a saída para o auditor:
```
python "${CLAUDE_PLUGIN_ROOT}/scripts/verificar_entrega.py" "<pasta>/plano-final-<slug>.html" --semana 5 --cliente "<Nome>" --ficha "<cliente>/<Nome>.md"
python "${CLAUDE_PLUGIN_ROOT}/scripts/checar_fontes.py" "<pasta>/plano-final-<slug>.html"
```

## Rodada

1. **Três cadeiras em paralelo**, numa só mensagem, cada uma sem ver as outras, cada chamada da ferramenta Agent com `model: "sonnet"` (o parâmetro vale mais que o modelo da conversa). Passe a cada uma os caminhos completos, não o conteúdo:
   - `ee-trieme:cadeira-auditor-fonte`: ficha, rascunho, `Entregaveis/`, rubrica e a saída dos dois scripts;
   - `ee-trieme:cadeira-gestor-metodo`: ficha, decks das Semanas 2 a 4, rascunho e seu `_fonte/textos.json`, `detalhe-<slug>.html` quando existir, `${CLAUDE_PLUGIN_ROOT}/skills/estruturacao-estrategica/base-de-todo-encontro.md`, `${CLAUDE_PLUGIN_ROOT}/skills/estruturacao-estrategica/esqueleto/semana-5-planejamento.md`, `${CLAUDE_PLUGIN_ROOT}/padrao/metodo-pse.md` e a rubrica; confira no manifesto os vínculos dessa preparação; em material legado sem manifesto/JSON, registre o limite e passe o disponível, sem presumir fundamento ausente;
   - `ee-trieme:cadeira-especialista-setor`: o formato e o setor do cabeçalho da ficha, ficha, rascunho e `Entregaveis/`.
2. **Cabeceira:** `ee-trieme:cabeceira-cliente`, sem o parâmetro `model` (o arquivo do agente põe opus), com ficha, rascunho, `Entregaveis/`, rubrica e as três avaliações como vieram, sem resumo nem comentário seu.
3. Sem réplica: nenhuma cadeira roda de novo.

## Depois

- Grave a ata da cabeceira, como veio, em "Ensaios e mesa" do registro interno (`_ensaios-internos/registro.md`), subseção "Mesa", com a data.
- Mostre ao consultor os ajustes e as divergências. Ele decide as divergências e quais ajustes entram; o guia `plano-final` aplica os aceitos junto com os do ensaio.
- Marque a mesa na Status com a data. Em "Medição" do registro interno, a linha da mesa (horas do consultor, modelo e esforço) e, depois da Semana 5, quantos ajustes foram aplicados.

## Verificação

Ata de até 30 linhas, com as 5 notas do cliente, as 3 técnicas, até 5 ajustes com tela ou arquivo e as divergências. Quatro execuções: três cadeiras e a cabeceira.

## Anti-exemplos

- Errado: resumir as cadeiras antes de passar à cabeceira. Certo: as três avaliações inteiras.
- Errado: a cabeceira escolher um lado quando o auditor e o especialista divergem num número decisivo. Certo: a divergência vai ao consultor.
- Errado: corrigir o deck durante a mesa. Certo: a ata aponta; quem produziu corrige.
