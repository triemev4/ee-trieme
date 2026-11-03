---
name: diagnostico-comercial
description: "Use quando o consultor pedir a Semana 4 da Estruturação Estratégica, o Diagnóstico Comercial de um cliente. Use quando pedir a estrutura de vendas, os Horizontes de Crescimento, o desenho do CRM ou o fluxo comercial. Use quando trouxer a transcrição ou o retorno do Diagnóstico Comercial para registrar."
model: sonnet
argument-hint: "[Nome do cliente]"
---

# Diagnóstico Comercial · Semana 4

Sem o nome, pergunte. `<cliente>` = `EE/Clientes/<N>. <Nome>`; `<slug>` = o nome em minúsculas, sem acento, com hífens; `<semana>` = `<cliente>/4. Diagnóstico Comercial`. O que vai em cada tela está no esqueleto da semana; aqui ficam os passos e os comandos.

**O que a semana entrega:** leitura do processo comercial real, capacidade atual, perdas e próximos testes; recomenda uma estrutura executável, com estado e limites proporcionais à evidência.

## 1. Ler
- `${CLAUDE_PLUGIN_ROOT}/skills/estruturacao-estrategica/base-de-todo-encontro.md`, `${CLAUDE_PLUGIN_ROOT}/skills/estruturacao-estrategica/esqueleto/semana-4-diagnostico-comercial.md` e `${CLAUDE_PLUGIN_ROOT}/skills/diagnostico-comercial/fluxo-comercial.md`.
- Da ficha, só o que a semana usa:
  ```
  python "${CLAUDE_PLUGIN_ROOT}/scripts/ler_ficha.py" "<cliente>/<Nome>.md" --cabecalho --secoes "Status, Contrato, Dados mínimos, Números-fonte, Meta, Direcionamento, Restrição, Pontos, Decisões por encontro, Contexto do consultor, Persona, Glossário" --obrigatorias "Status, Números-fonte"
  ```
- De `padrao/formatos-de-negocio.md`, só a seção 6, por Grep, pelo formato da triagem.
- Os insumos novos, por data, pelo `_texto/` (rode a extração se faltar ou se chegou insumo novo):
  ```
  python "${CLAUDE_PLUGIN_ROOT}/scripts/extrair_insumos.py" "<cliente>/0. Inputs e Transcrições"
  ```
- Das Semanas 2 e 3, só a capa, "Próximos passos" e "A trava e o plano"; da Semana 2, leia também ICP e Posicionamento (PUV em decks anteriores). Os números saem de Números-fonte:
  ```
  python "${CLAUDE_PLUGIN_ROOT}/scripts/extrair_telas.py" "<deck.html>" --tela "Próximos passos" --tela "A trava e o plano" --tela "A trava deste encontro" --tela "Plano de ação" --tela "Perfil de Cliente Ideal" --tela "Concorrentes" --tela "Posicionamento" --tela "PUV" --tela "Proposta Única de Valor" --tela 2
  ```
- **Cliente oculto:** inicie a coleta depois da Semana 2, com dois concorrentes e protocolo comparável. Registre um estado explícito: realizado válido, parcial, inválido ou ausente, com evidência e razão. Mantenha a tela 04 em todos os estados: ausência não esconde o resultado nem vira nota de atendimento. Teste contaminado não recebe score; preserve evidência independente que ainda seja válida. Se ausente, combine como coletar sem bloquear o restante do diagnóstico.
- Se o desenho do CRM depender de dados definidos na S3, leia também a tela Rastreamento e seu detalhe pertinente, pela extração; confirme o caminho pela regra **Operação dos dados do CRM** do esqueleto S4.

**Pronto quando:** você sabe como a venda acontece hoje, quem toca cada etapa, as ferramentas em uso, a trava da semana e o que as Semanas 2 e 3 deixaram no plano.

## 2. Perguntar uma vez
Numa rodada só, cada pergunta com a resposta recomendada: o que os arquivos não trazem (etapas reais do funil, quem toca em cada uma, ferramentas em uso).

**Pronto quando:** cada resposta está na ficha ou virou pendência com dono e data.

## 3. Contas pelo Python
Funil, conversão entre etapas e motivos de perda saem do arquivo do CRM (CSV ou XLSX), que vai direto ao script, sem abrir. Outra conta (taxa por papel, capacidade, recompra) vai em `<semana>/_fonte/contas.json`, gravado com a ferramenta Write.
```
python "${CLAUDE_PLUGIN_ROOT}/scripts/calcular.py" --funil "<arquivo do CRM>" [--ordem "Lead,Qualificado,Proposta,Fechado"] --ficha "<cliente>/<Nome>.md" --unidade "oportunidades" --periodo "<período>" --saida "<semana>/_fonte/funil.resultado.json"
python "${CLAUDE_PLUGIN_ROOT}/scripts/calcular.py" --motivos "<arquivo do CRM>" --ficha "<cliente>/<Nome>.md" --unidade "negócios perdidos" --saida "<semana>/_fonte/motivos.resultado.json"
python "${CLAUDE_PLUGIN_ROOT}/scripts/calcular.py" --tabela "<cliente>/0. Inputs e Transcrições/_texto/<arquivo>.txt" --pagina N --ficha "<cliente>/<Nome>.md" --saida "<semana>/_fonte/tabela.resultado.json"
python "${CLAUDE_PLUGIN_ROOT}/scripts/calcular.py" "<semana>/_fonte/contas.json" --ficha "<cliente>/<Nome>.md"
```
```json
{"contas": [{"dado": "Conversão de proposta em venda", "formula": "fechados / propostas * 100", "unidade": "%",
  "decisivo": "sim", "entradas": {
    "fechados": {"valor": "12", "unidade": "negócios", "origem": "N21"},
    "propostas": {"valor": "48", "unidade": "propostas", "origem": "crm.txt · página 1"}}}]}
```
Origens aceitas: id de Números-fonte (`N21`), `dados-pesquisa.json#D07`, `arquivo.txt · página 3` (de `_texto`) e `premissa: consultor, dd/mm/aaaa`. Fórmula: `+ - * / ( )`, ponto decimal, nomes das entradas, `min`, `max`, `round`, `soma`. O texto copia o valor de `*.resultado.json`. Sem arquivo do cliente, a tela mostra o que foi observado, sem percentual.

**Pronto quando:** cada número da semana está em Números-fonte, com fórmula e origem, ou a tela diz "a medir".

## 4. Escrever o deck
- Copie `${CLAUDE_PLUGIN_ROOT}/moldes/semana-4.textos.json` para `<semana>/_fonte/textos.json` com `shutil.copyfile` e troque os textos de exemplo pelos do cliente. Edite campo a campo, com a ferramenta Edit. O exemplo orienta a forma; preserve verbo, objeto, responsável, condição e conclusão observável. Reduza palavras somente sem perder significado.
- Descreva etapas, filas, decisões, transferências e alçadas que acontecem hoje; separe o retrato atual da Estrutura Ideal. Proponha papéis pela função e pela carga real. Contratação imediata pode ser recomendada quando uma função indispensável falta; não crie uma fase sem contratar por padrão.
- Grave `_fonte/processo.json` pelo contrato de `fluxo-comercial.md` e gere a figura fora do pacote. Use o PNG em `tela-05.imagem` com `alt` descritivo; preserve etapas e fontes no texto. Sem navegador, omita `--png` e mantenha a alternativa textual; figura alta completa é consultada com zoom/no detalhe, com recorte legível no deck.
  ```
  python "${CLAUDE_PLUGIN_ROOT}/scripts/desenhar_processo.py" "<semana>/_fonte/processo.json" --svg "<semana>/_fonte/processo.svg" --png "<semana>/_fonte/processo.png"
  ```
- No fecho, aplique o teste do dobro como roteiro: sim, não ou inconclusivo. Se a evidência não fecha a causa, registre hipótese de trabalho, alternativa, evidência que pode mudar a escolha e teste decisivo. A `.corda` registra capacidade/limite atual ou o dado a medir, sem presumir um número. Reavalie por evidência ou mudança de gargalo, não só pelo calendário.
- Na composição de CRM e implantação, aplique **Operação dos dados do CRM**, usando stack, automações, apoio e dependências existentes.
- Gere o HTML (o HTML sai sempre do molde; `--listar` mostra os caminhos que ele espera):
  ```
  python "${CLAUDE_PLUGIN_ROOT}/scripts/preencher_molde.py" --validar "${CLAUDE_PLUGIN_ROOT}/moldes/semana-4.html" "<semana>/_fonte/textos.json"
  python "${CLAUDE_PLUGIN_ROOT}/scripts/preparar_entrega.py" "<semana>/_fonte/textos.json" "<semana>/diagnostico-comercial-<slug>.html" --semana 4 --cliente "<Nome>" --ficha "<cliente>/<Nome>.md" --modo rascunho --consultor "${user_config.consultor_nome}" --cargo "${user_config.consultor_cargo}"
  ```
- O que o esqueleto manda para o DOCX vai em `<semana>/detalhe-<slug>.html`, em até 1.500 palavras. Comece por `<section class="abertura">` antes do corpo, com contexto, meta, decisões vigentes, limites e plano. Escreva sem IDs/códigos internos.
- O preparador atualiza `_fonte/telas.md` e o manifesto. O gatilho reconhece a conferência básica pelos hashes; corrija erros e prepare novamente.

**Pronto quando:** o deck gera sem erro.

## 5. Revisão numa rodada
1. Com o deck completo e sem erro, confira como autor **Operação dos dados do CRM** no `textos.json`, na extração e no detalhe pertinente. Depois, o ensaio: `/ee-trieme:ensaio-cliente <Nome> 4`. O ensaio mantém o papel de leitura pelo cliente.
2. Junte numa lista os ajustes e os cortes. Em conflito, vale o que tem prova e respeita o esqueleto; condensação segue B4, com cobertura no detalhe; aprovação segue com o consultor. Aplique tudo de uma vez (a ficha primeiro, se mexer em número; depois o `textos.json`), reconcilie a revisão corrigida pela mesma regra e prepare a revisão final no próximo passo.
3. Conferência final, uma vez só, com a passada por `padrao/estilo-de-escrita.md`:
   ```
   python "${CLAUDE_PLUGIN_ROOT}/scripts/preparar_entrega.py" "<semana>/_fonte/textos.json" "<semana>/diagnostico-comercial-<slug>.html" --semana 4 --cliente "<Nome>" --ficha "<cliente>/<Nome>.md" --modo final --fontes online --detalhe "<semana>/detalhe-<slug>.html" --consultor "${user_config.consultor_nome}" --cargo "${user_config.consultor_cargo}"
   ```
   Sem detalhe, omita `--detalhe`. Em acervo congelado, use `--fontes congeladas --coleta "<semana>/_fonte/coleta"`; não pesquise fora dele. Depois da última correção, prepare novamente a revisão final, inclusive sua extração; avaliação experimental usa os hashes finais. Erro ou etapa obrigatória não realizada impede conclusão técnica. A aprovação do consultor continua separada. Erro se corrige; aviso se lê e se corrige quando é real. Número calculado que o `checar_fontes.py` não acha na página é esperado: a fonte dele é a conta.
4. No registro interno (`<cliente>/_ensaios-internos/registro.md`), em "Ensaios e mesa", a linha do ensaio, com a decisão do consultor sobre cada corte. Segunda rodada, só a pedido do consultor.

**Pronto quando:** a conferência final passa sem erro, o DOCX existe e a linha está no registro.

## 6. Decisão do consultor
Ele lê o rascunho, põe o peso da mão e decide a trava comercial. Pode manter uma hipótese de trabalho e um teste decisivo quando os dados ainda não sustentam conclusão; registra estado e condição de revisão na ficha.

## 7. Depois da reunião
Siga `${CLAUDE_PLUGIN_ROOT}/skills/estruturacao-estrategica/rotina-pos-encontro.md` com `--semana 4`. Desta semana: a Status passa à mesa com o cliente (`/ee-trieme:mesa-cliente <Nome>`) quando os entregáveis e o rascunho da Semana 5 existirem, e a mensagem sai pelo bloco da Semana 4, com a linha de status dos entregáveis. Condução: `padrao/mapa-de-pessoas.md`. O consultor decide o envio do HTML, do DOCX e da mensagem.

LP no escopo: confronte oferta, ação, campos de qualificação, responsável e prazo de retorno da página com as decisões comerciais. Registre a validação na seção Landing page da ficha e retome `/ee-trieme:landing-page <Nome>` se houver produção ou ajuste pendente. Mudança material exige nova revisão antes da entrega; não mantém aprovação da versão anterior.
