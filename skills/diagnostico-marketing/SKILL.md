---
name: diagnostico-marketing
description: "Use quando o consultor pedir a Semana 3 da Estruturação Estratégica, o Diagnóstico de Marketing de um cliente. Use quando pedir a auditoria de canais, o forecast de mídia, o CRO ou a análise dos anúncios dos concorrentes. Use quando trouxer a transcrição ou o retorno do Diagnóstico de Marketing para registrar."
model: sonnet
argument-hint: "[Nome do cliente]"
---

# Diagnóstico de Marketing · Semana 3

Sem o nome, pergunte. `<cliente>` = `EE/Clientes/<N>. <Nome>`; `<slug>` = o nome em minúsculas, sem acento, com hífens; `<semana>` = `<cliente>/3. Diagnóstico de Marketing`. O que vai em cada tela está no esqueleto da semana; aqui ficam os passos e os comandos.

**O que a semana entrega:** leitura por evidência das frentes de marketing, prioridade e ação por frente, e um forecast que usa a base disponível. O formato e a quantidade de cenários dependem da qualidade das referências e da pergunta econômica.

## 1. Ler
- `${CLAUDE_PLUGIN_ROOT}/skills/estruturacao-estrategica/base-de-todo-encontro.md` e `${CLAUDE_PLUGIN_ROOT}/skills/estruturacao-estrategica/esqueleto/semana-3-diagnostico-marketing.md`.
- Da ficha, só o que a semana usa:
  ```
  python "${CLAUDE_PLUGIN_ROOT}/scripts/ler_ficha.py" "<cliente>/<Nome>.md" --cabecalho --secoes "Status, Contrato, Dados mínimos, Números-fonte, Meta, Direcionamento, Restrição, Pontos, Decisões por encontro, Contexto do consultor, Persona, Glossário" --obrigatorias "Status, Números-fonte"
  ```
- A nota de preparo e as transcrições, das mais recentes às mais antigas, pelo `indice.md` dos blocos. Insumo novo: rode a extração e leia pelo `_texto/`:
  ```
  python "${CLAUDE_PLUGIN_ROOT}/scripts/extrair_insumos.py" "<cliente>/0. Inputs e Transcrições"
  ```
- Da Semana 2, só a capa, Posicionamento (ou PUV, nome anterior), "Próximos passos" e "A trava e o plano"; os números saem de Números-fonte:
  ```
  python "${CLAUDE_PLUGIN_ROOT}/scripts/extrair_telas.py" "<cliente>/2. Pesquisa de Mercado/pesquisa-mercado-<slug>.html" --tela "Próximos passos" --tela "Concorrentes" --tela "Posicionamento" --tela "PUV" --tela "Proposta Única de Valor" --tela "A trava e o plano" --tela "A trava deste encontro" --tela "Plano de ação" --tela 2
  ```
- Dos padrões, só a seção da semana, por Grep: `metodo-pse.md`, `formatos-de-negocio.md` (Semana 3 e maturidade), `mapa-de-pessoas.md`. O visual vem pronto no molde.
- **Confira na ficha:** o acesso às contas de anúncio (classe Bloqueia), a verba mínima e máxima (classe Limita) e o endereço do site. Sem o endereço na ficha, procure nos insumos (`grep -i -E "www\.|\.com"` em `_texto/`) e grave o achado em Dados mínimos; só sem achado o site vira pendência.

**Pronto quando:** cada frente relevante tem público, função, abordagem, conversão, destino e limite; conhece a trava, a verba disponível (ou a ausência textual) e os acessos; os rótulos refletem as evidências.

## 2. Perguntar uma vez
Numa rodada só, cada pergunta com a resposta recomendada: o que a ficha e as transcrições não trazem (quem cuida das contas, histórico de anúncios, canal que o cliente já decidiu não usar). Teste os acessos às contas antes de perguntar.

**Pronto quando:** cada resposta está na ficha ou virou pendência com dono e data.

## 3. Coletar, em paralelo
A auditoria e os anúncios dos concorrentes são independentes: rode os dois ao mesmo tempo, cada um no modelo mais barato que dá conta.
- **Auditoria por script:** prints do site no computador e no celular, Google Meu Negócio, velocidade e SEO por página. Você lê só `auditoria.md`; os caminhos dos prints para o `textos.json` estão em `molde_s3` do `auditoria.json` (com o prefixo `auditoria/`). O Instagram pede login: print à mão em `tela-10.print_atual`.
  ```
  python "${CLAUDE_PLUGIN_ROOT}/scripts/coletar_auditoria.py" --site "<url do site>" --gmn "<url do perfil ou Nome, Cidade>" --saida "<semana>/_fonte/auditoria"
  ```
- **Anúncios reais dos concorrentes, só de quem o cliente nomeou e a Semana 2 achou.** A Biblioteca de Anúncios da Meta entra apenas para o concorrente que o cliente citou pelo nome e que a Semana 2 confirmou com a página oficial (link na ficha ou na tela 03). A busca vai por essa página, nunca pelo nome solto. Sem concorrente assim, a Biblioteca fica fora desta semana: a tela de Criativos traz os formatos e ângulos propostos para o cliente, rotulados como proposta, e o nome sem página vira pergunta ao cliente ("qual é a página da X?").
  Aplique `skills/pesquisa-mercado/concorrentes.md`: até quatro concorrentes nomeados e identificados por etapa, com pergunta concreta, data e filtros no registro. Empresa descoberta na pesquisa permanece fora da Biblioteca enquanto a exceção não tiver aceite explícito do curador. Ausência de anúncio nos filtros não prova ausência geral de publicidade.
  Com a página confirmada: a skill `espionar-concorrente-pro` do consultor, uma chamada por concorrente (URL da Biblioteca), sem análise por IA. Sem a skill, ou se ela falhar, print à mão de 3 a 6 anúncios ativos desse concorrente, com a data de início visível. O print é `concorrentes/<nome>/<data>/ad-NNN/image-1.jpg` (vídeo: print à mão) e vai para `tela-11.<formato>[i].print` do `textos.json`; o `meta.json` traz texto, chamada e "ativo desde". A Biblioteca mostra o anúncio e a data; gasto ela não mostra, então o deck fala de formato, ângulo e tempo no ar.
  ```
  python -X utf8 "<home do consultor>/.claude/skills/espionar-concorrente-pro/scripts/main.py" --name "<concorrente>" --no-headless --max-ads 6 --skip-analyze --output-base "<semana>/_fonte/anuncios" "<URL da Biblioteca>"
  ```
- **Exportação de 90 dias** do Meta e do Google (CSV ou XLSX), quando houver: passe ao script sem abrir. Ele soma gasto, resultados, custo por resultado e divisão por canal e grava em Números-fonte.
  ```
  python "${CLAUDE_PLUGIN_ROOT}/scripts/calcular.py" --midia "<exportação do Meta>" "<exportação do Google>" --canal "Meta" "Google" --ficha "<cliente>/<Nome>.md" --periodo "últimos 90 dias" --por-campanha --saida "<semana>/_fonte/midia.resultado.json"
  ```

**Pronto quando:** `auditoria.md` existe, evidências dos anúncios identificados estão em `_fonte/anuncios` (ou em prints feitos à mão), e a exportação, quando disponível, está em Números-fonte. Ausência de histórico próprio fica registrada sem ser confundida com ausência de referência de mercado.

## 4. Forecast pela base disponível
Defina primeiro a função e prioridade das frentes; depois faça o forecast. Separe verba disponível, histórico do cliente, referência de custo, hipótese de conversão, cenário condicional e resultado observado. Ausência de histórico não elimina uma referência defensável; dado com `valor: null` ou de prova fraca fica fora de número decisivo. Escolha apenas os cenários que os dados e a decisão sustentam; não preencha três cenários por padrão. Sem base para retorno numérico, apresente teste, verba/limite disponível e condição de avanço. O forecast e qualquer outra conta vão em `<semana>/_fonte/contas.json`; grave com Write e rode o script:
```json
{"contas": [{"dado": "Leads por mês, cenário conservador", "formula": "verba / custo", "unidade": "leads",
  "periodo": "mês", "decisivo": "sim", "usado_em": "S3 · forecast", "entradas": {
    "verba": {"valor": "R$ 3.000", "unidade": "R$", "origem": "N05"},
    "custo": {"valor": "R$ 25,00", "unidade": "R$", "origem": "relatorio-meta.txt · página 2"}}}]}
```
```
python "${CLAUDE_PLUGIN_ROOT}/scripts/calcular.py" "<semana>/_fonte/contas.json" --ficha "<cliente>/<Nome>.md"
```
Origens aceitas: id de Números-fonte (`N05`), `dados-pesquisa.json#D07`, `arquivo.txt · página 3` (de `_texto`) e `premissa: consultor, dd/mm/aaaa`. Fórmula: `+ - * / ( )`, ponto decimal, nomes das entradas, `min`, `max`, `round`, `soma`. O texto copia o valor de `*.resultado.json`, no formato dele.

**Pronto quando:** cada número do forecast está em Números-fonte, com fórmula e origem.

## 5. Escrever o deck
- Copie `${CLAUDE_PLUGIN_ROOT}/moldes/semana-3.textos.json` para `<semana>/_fonte/textos.json` com `shutil.copyfile` e troque os textos de exemplo pelos do cliente, a partir da ficha, dos insumos e do esqueleto. Edite campo a campo, com a ferramenta Edit. O exemplo orienta a forma; preserve verbo, objeto, responsável, condição e conclusão observável. Reduza palavras somente sem perder significado.
- Frente que o cliente decidiu não usar fica `false` em `opcionais`.
- Para compor Rastreamento e os canais, aplique **Resultado e destino dos canais** do esqueleto; escreva a estratégia por frente antes do forecast. Preserve funções diferentes de busca e contas quando ambas se aplicam. Uma frente não é desativada apenas por faltar histórico próprio se há referência pertinente e teste viável.
- Gere o HTML (o HTML sai sempre do molde; `--listar` mostra os caminhos que ele espera):
  ```
  python "${CLAUDE_PLUGIN_ROOT}/scripts/preencher_molde.py" --validar "${CLAUDE_PLUGIN_ROOT}/moldes/semana-3.html" "<semana>/_fonte/textos.json"
  python "${CLAUDE_PLUGIN_ROOT}/scripts/preparar_entrega.py" "<semana>/_fonte/textos.json" "<semana>/diagnostico-marketing-<slug>.html" --semana 3 --cliente "<Nome>" --ficha "<cliente>/<Nome>.md" --modo rascunho --consultor "${user_config.consultor_nome}" --cargo "${user_config.consultor_cargo}"
  ```
- O que a tela não comporta (autor e método do LIFT, derivação do forecast, fontes, notas da auditoria) vai para `<semana>/detalhe-<slug>.html`, em até 1.500 palavras. Abra o detalhe com `<section class="abertura">` antes do corpo: contexto, meta, decisões vigentes, limites e plano. Use linguagem natural e omita IDs e códigos internos.
- O preparador atualiza `_fonte/telas.md` e o manifesto. O gatilho reconhece a conferência básica pelos hashes; corrija erros e prepare novamente.

**Pronto quando:** o deck gera sem erro.

## 6. Revisão numa rodada
1. Com o deck completo e sem erro, confira como autor **Resultado e destino dos canais** no `textos.json`, na extração e no detalhe que fundamenta o forecast. Depois, o ensaio: `/ee-trieme:ensaio-cliente <Nome> 3`. O ensaio mantém o papel de leitura pelo cliente, sem assumir essa conferência técnica.
2. Junte numa lista os ajustes e os cortes. Em conflito, vale o que tem prova e respeita o esqueleto; condensação segue B4, com cobertura no detalhe; aprovação segue com o consultor. Aplique tudo de uma vez (a ficha primeiro, se mexer em número; depois o `textos.json`), reconcilie a revisão corrigida pela mesma regra e prepare a revisão final no próximo passo.
3. Conferência final, uma vez só, com a passada por `padrao/estilo-de-escrita.md`. Sem detalhe, gere o DOCX sem `--detalhe`.
   ```
   python "${CLAUDE_PLUGIN_ROOT}/scripts/preparar_entrega.py" "<semana>/_fonte/textos.json" "<semana>/diagnostico-marketing-<slug>.html" --semana 3 --cliente "<Nome>" --ficha "<cliente>/<Nome>.md" --modo final --fontes online --detalhe "<semana>/detalhe-<slug>.html" --consultor "${user_config.consultor_nome}" --cargo "${user_config.consultor_cargo}"
   ```
   Sem detalhe, omita `--detalhe`. Em acervo congelado, use `--fontes congeladas --coleta "<semana>/_fonte/coleta"`; não pesquise fora dele. Depois da última correção, prepare novamente a revisão final, inclusive sua extração; avaliação experimental usa os hashes finais. Erro ou etapa obrigatória não realizada impede conclusão técnica. A aprovação do consultor continua separada. Erro se corrige; aviso se lê e se corrige quando é real. Número calculado que o `checar_fontes.py` não acha na página é esperado: a fonte dele é a conta.
4. No registro interno (`<cliente>/_ensaios-internos/registro.md`), em "Ensaios e mesa", a linha do ensaio, com a decisão do consultor sobre cada corte. Segunda rodada, só a pedido do consultor.

**Pronto quando:** a conferência final passa sem erro, o DOCX existe e a linha está no registro.

## 7. Decisão do consultor
Ele lê o rascunho, põe o peso da mão e decide a trava de marketing e a nota de maturidade.

## 8. Depois da reunião
Siga `${CLAUDE_PLUGIN_ROOT}/skills/estruturacao-estrategica/rotina-pos-encontro.md` com `--semana 3`. Desta semana: a trava, o forecast em Números-fonte, e a mensagem com o achado de uma frente, a validação, o gancho com data e as pendências específicas. O consultor decide o envio do HTML, do DOCX e da mensagem.

Após registrar as decisões, leia Landing page na ficha. Se confirmada no escopo, encaminhe `/ee-trieme:landing-page <Nome>` para produzir a primeira versão entre S3 e S4. Decisão ausente: o guia resolve com o consultor. Sem LP, siga à S4; falta de MCP ou ativo visual não impede o encontro.
