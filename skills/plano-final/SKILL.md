---
name: plano-final
description: "Use quando o consultor pedir a Semana 5 da Estruturação Estratégica, o Planejamento Estratégico + Entregáveis de um cliente. Use quando pedir o plano final, o Mapa de Ações, a restrição principal, o Relatório Estratégico do Negócio, criativos ou manuais. Pedido específico de landing page segue ao guia landing-page."
model: sonnet
argument-hint: "[Nome do cliente]"
---

# Planejamento Estratégico + Entregáveis · Semana 5

Sem o nome, pergunte. `<cliente>` = `EE/Clientes/<N>. <Nome>`; `<slug>` = o nome em minúsculas, sem acento, com hífens; `<pasta>` = `<cliente>/5. Planejamento Estratégico + Entregáveis`. O que vai em cada tela está no esqueleto da semana; aqui ficam os passos e os comandos.

**Entrega:** leitura da restrição sustentada ou hipótese de trabalho com teste decisivo, Mapa executável, conta econômica e itens contratados. Incorpore insumo novo: ficha primeiro, conta pelo `calcular.py`. Fato ausente permanece ausente; cenário e proposta seguem a regra de estilo.

## 1. Ler
- `${CLAUDE_PLUGIN_ROOT}/skills/estruturacao-estrategica/base-de-todo-encontro.md`, `${CLAUDE_PLUGIN_ROOT}/skills/estruturacao-estrategica/esqueleto/semana-5-planejamento.md` e `${CLAUDE_PLUGIN_ROOT}/skills/plano-final/entregaveis.md`.
- Da ficha, só o que a semana usa:
  ```
  python "${CLAUDE_PLUGIN_ROOT}/scripts/ler_ficha.py" "<cliente>/<Nome>.md" --cabecalho --secoes "Status, Contrato, Números-fonte, Meta, Direcionamento, Restrição, Pontos, Decisões por encontro, Contexto do consultor, Persona, Pendências, Landing page" --obrigatorias "Status, Números-fonte"
  ```
- Os insumos novos pelo `_texto/` (rode a extração se faltar ou se chegou insumo novo):
  ```
  python "${CLAUDE_PLUGIN_ROOT}/scripts/extrair_insumos.py" "<cliente>/0. Inputs e Transcrições"
  ```
- Das Semanas 2 a 4, só a capa, "Próximos passos" e "A trava e o plano" de cada deck (`pesquisa-mercado-`, `diagnostico-marketing-` e `diagnostico-comercial-<slug>.html`). Da S2 leia também Posicionamento (PUV em decks anteriores); os números saem de Números-fonte:
  ```
  python "${CLAUDE_PLUGIN_ROOT}/scripts/extrair_telas.py" "<deck.html>" --tela "Próximos passos" --tela "A trava e o plano" --tela "A trava deste encontro" --tela "Plano de ação" --tela "Concorrentes" --tela "Posicionamento" --tela "PUV" --tela "Proposta Única de Valor" --tela 2
  ```
- Liste os entregáveis da matriz do Contrato, com peça ou briefing e status. A matriz é o limite do que se entrega.

**Pronto quando:** você tem meta e efeitos, a memória vigente e suas decisões, os próximos passos e planos das Semanas 2 a 4, os números decisivos, limites e entregáveis de contrato.

## 2. Perguntar uma vez
Numa rodada só, cada pergunta com a resposta recomendada: o que falta para fechar a matriz (aprovação de briefing, dado que nenhuma semana levantou).

**Pronto quando:** cada resposta está na ficha ou virou pendência com dono e data.

## 3. Entregáveis
Cada entregável pelo modelo de `entregaveis.md`, com o status atualizado na matriz. Criativos e manuais podem ser preparados em paralelo quando independentes. LP contratada: retome `/ee-trieme:landing-page <Nome>` e confira a revisão atual, incluindo decisões da S4. Não crie outra versão por um método separado. Texto compartilhado com criativos vem da copy reconciliada.

**Pronto quando:** cada item da matriz tem arquivo em `<pasta>/Entregaveis/` ou status real com o motivo.

### Opções e preços, quando houver aquisição necessária

Quando o plano pedir capacidade que o cliente precisa comprar, produza `<pasta>/Opções e preços - <Nome>.md`, de uma página. Compare opções pertinentes (duas ou três quando existirem) por capacidade atendida, valor pontual, recorrência, implantação, limite e condição, com URL/fonte e data. Sem cotação, escreva a cotar e a pergunta restante; não invente alternativa para completar tabela. Identifique oferta própria da V4 como tal, separada da recomendação técnica. Documento orienta a decisão e não autoriza compra, implantação ou escopo extra. Na mensagem S5 indique o arquivo junto do plano; a matriz continua mandando nos entregáveis contratados.

## 4. Contas e restrição
- Reutilize forecast e SOM por seus ids; insumo novo pode recalibrá-los, preservando valor anterior e estado da premissa. Conta em `<pasta>/_fonte/contas.json`:
  ```json
  {"contas": [{"dado": "Investimento incremental no período", "formula": "mensal * meses", "unidade": "R$",
    "decisivo": "sim", "entradas": {
      "mensal": {"valor": "R$ 3.000", "unidade": "R$", "origem": "N14"},
      "meses": {"valor": "3", "unidade": "meses", "origem": "premissa: consultor, 07/10/2026"}}}]}
  ```
  ```
  python "${CLAUDE_PLUGIN_ROOT}/scripts/calcular.py" "<pasta>/_fonte/contas.json" --ficha "<cliente>/<Nome>.md"
  ```
  Origens aceitas: id de Números-fonte, `dados-pesquisa.json#D07`, `arquivo.txt · página 3` e `premissa: consultor, dd/mm/aaaa`. O deck copia o valor de `contas.resultado.json`. Item sem cotação fica "a cotar".
- A conta de receita separa incremento de receita preservada, recorrência e unidade/período; usa margem de contribuição, incorpora o tempo até venda e recebimento e verifica sobreposição entre alavancas. Receita bruta não substitui contribuição. A conta não transforma premissa em dado.
- A restrição principal segue a inferência de `padrao/estilo-de-escrita.md`: evidência, mecanismo, premissa crítica, alternativa, teste e condição de revisão. Conecte efeitos e causas pertinentes com a semana e fonte de origem, sem exigir número fixo de efeitos ou árvore formal. Se a evidência sustenta uma hipótese útil mas não a causa comum, registre hipótese de trabalho e teste decisivo; S5 não a confirma só pelo calendário. A decisão é do consultor.
- Sem base para retorno numérico, mostre o teste proposto, verba disponível e limite de gasto, e a condição que permite avançar. Não invente taxa nem prazo de retorno.

**Pronto quando:** números, unidades, períodos, fontes e premissas estão em Números-fonte; a tese proporcional à evidência tem estado, alternativa, ação inicial e revisão/teste, ou explicita o que falta para decidir.

## 5. Escrever o deck
- Copie `${CLAUDE_PLUGIN_ROOT}/moldes/semana-5.textos.json` para `<pasta>/_fonte/textos.json` com `shutil.copyfile` e troque os textos de exemplo pelos do cliente. Edite campo a campo, com a ferramenta Edit. O exemplo orienta a forma; preserve verbo, objeto, responsável, condição e conclusão observável. Reduza palavras somente sem perder significado.
- Aplique **Viabilidade do Mapa** nos campos existentes: até três frentes H1, sem mínimo de ações, primeira ação prioritária, data ou condição, responsável proposto/confirmado, capacidade e liberação. Inclua a decisão e condição de revisão; restante no detalhe, com condensação pelo B4.
- A Teoria das Restrições fundamenta a análise. O detalhe pode explicar a causalidade e as fontes quando necessário; a tela traduz a lógica para a operação, sem exigir prova formal, etiqueta ou fórmula visual. O detalhe vai para `<pasta>/detalhe-<slug>.html`, em até 1.500 palavras. Abra com `<section class="abertura">` antes do corpo: contexto, meta, decisões vigentes, limites e plano, em linguagem natural e sem IDs/códigos internos. Escreva-o antes da preparação do rascunho e inclua `--detalhe "<pasta>/detalhe-<slug>.html"` nesse comando, para vinculá-lo à revisão recebida pela mesa. Sem detalhe, omita a opção.
- Gere o HTML (o HTML sai sempre do molde; `--listar` mostra os caminhos que ele espera):
  ```
  python "${CLAUDE_PLUGIN_ROOT}/scripts/preencher_molde.py" --validar "${CLAUDE_PLUGIN_ROOT}/moldes/semana-5.html" "<pasta>/_fonte/textos.json"
  python "${CLAUDE_PLUGIN_ROOT}/scripts/preparar_entrega.py" "<pasta>/_fonte/textos.json" "<pasta>/plano-final-<slug>.html" --semana 5 --cliente "<Nome>" --ficha "<cliente>/<Nome>.md" --modo rascunho --consultor "${user_config.consultor_nome}" --cargo "${user_config.consultor_cargo}"
  ```
- O preparador atualiza `_fonte/telas.md` e o manifesto. O gatilho reconhece a conferência básica pelos hashes; corrija erros e prepare novamente.

**Pronto quando:** o deck gera sem erro.

## 6. Mesa, ensaio e conferência
1. Com o deck completo e sem erro, confira como autor **Viabilidade do Mapa** no `textos.json`, na extração e no detalhe pertinente. A mesa (`/ee-trieme:mesa-cliente <Nome>`), se a Status ainda não a marca, recebe esse mesmo rascunho e seu fundamento; depois, o ensaio (`/ee-trieme:ensaio-cliente <Nome> 5`). O consultor decide os ajustes da mesa. O ensaio mantém o papel de leitura pelo cliente.
2. Junte numa lista os ajustes e os cortes. Em conflito, vale o que tem prova e respeita o esqueleto; condensação segue B4, com cobertura no detalhe; aprovação segue com o consultor. Aplique tudo de uma vez (a ficha primeiro, se mexer em número; depois o `textos.json`), reconcilie a revisão corrigida por **Viabilidade do Mapa** e prepare a revisão final no próximo passo.
3. Conferência final, uma vez só, com a passada por `padrao/estilo-de-escrita.md`. Abra os links da tela de Entregáveis um a um.
   ```
   python "${CLAUDE_PLUGIN_ROOT}/scripts/preparar_entrega.py" "<pasta>/_fonte/textos.json" "<pasta>/plano-final-<slug>.html" --semana 5 --cliente "<Nome>" --ficha "<cliente>/<Nome>.md" --modo final --fontes online --detalhe "<pasta>/detalhe-<slug>.html" --consultor "${user_config.consultor_nome}" --cargo "${user_config.consultor_cargo}"
   ```
   Sem detalhe, omita `--detalhe`. Em acervo congelado, use `--fontes congeladas --coleta "<pasta>/_fonte/coleta"`; não pesquise fora dele. Depois da última correção, prepare novamente a revisão final, inclusive sua extração; avaliação experimental usa os hashes finais. Erro ou etapa obrigatória não realizada impede conclusão técnica. A aprovação do consultor continua separada. Erro se corrige; aviso se lê e se corrige quando é real. Número calculado que o `checar_fontes.py` não acha na página é esperado: a fonte dele é a conta.
4. No registro interno (`<cliente>/_ensaios-internos/registro.md`), em "Ensaios e mesa", a linha do ensaio, com a decisão do consultor sobre cada corte. Segunda rodada, só a pedido do consultor.

**Pronto quando:** a conferência final passa sem erro, o DOCX existe, a ata da mesa e a linha do ensaio estão no registro.

## 7. Decisão do consultor
Ele lê o rascunho, decide entre conclusão sustentada e hipótese com teste decisivo, registra estado e revisão, e aprova cada entregável antes da apresentação.

## 8. Depois da reunião
Siga `${CLAUDE_PLUGIN_ROOT}/skills/estruturacao-estrategica/rotina-pos-encontro.md` com `--semana 5`. Desta semana: a nota do cliente, a matriz com a data de envio de cada item e a mensagem com a linha de status dos entregáveis, só com o que existe e com link ("Pendente" só para pendência do cliente, nas condições de `esqueleto/encerramento.md`). Depois, `/ee-trieme:encerramento <Nome>`. O consultor decide o envio do HTML, do DOCX, dos entregáveis e da mensagem.
