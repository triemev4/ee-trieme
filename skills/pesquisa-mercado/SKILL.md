---
name: pesquisa-mercado
description: "Use quando o consultor pedir a Semana 2 da Estruturação Estratégica, a Pesquisa de Mercado de um cliente. Use quando pedir análise de mercado, TAM, SAM e SOM, concorrentes, SWOT, ICP ou PUV. Use quando trouxer a transcrição ou o retorno da Pesquisa de Mercado para registrar."
model: sonnet
argument-hint: "[Nome do cliente]"
---

# Pesquisa de Mercado · Semana 2

Sem o nome, pergunte. `<cliente>` = `EE/Clientes/<N>. <Nome>`; `<slug>` = o nome em minúsculas, sem acento, com hífens; `<semana>` = `<cliente>/2. Pesquisa de Mercado`. O que vai em cada tela está no esqueleto da semana; aqui ficam os passos e os comandos.

**O que a semana entrega:** um deck que defende uma ideia central sobre o mercado do cliente, com números que abrem na fonte, escrito para um dono de negócio que não é de marketing.

## 1. Ler
- `${CLAUDE_PLUGIN_ROOT}/skills/estruturacao-estrategica/base-de-todo-encontro.md` e `${CLAUDE_PLUGIN_ROOT}/skills/estruturacao-estrategica/esqueleto/semana-2-pesquisa-mercado.md`.
- Da ficha, só o que a semana usa:
  ```
  python "${CLAUDE_PLUGIN_ROOT}/scripts/ler_ficha.py" "<cliente>/<Nome>.md" --cabecalho --secoes "Status, Dados mínimos, Números-fonte, Meta, Persona, Direcionamento, Restrição, Pontos, Decisões por encontro, Contexto do consultor" --obrigatorias "Status, Dados mínimos, Números-fonte"
  ```
- Os insumos, pelo índice. Rode a extração, leia `_texto/indice.md` e, do Kickoff, o `indice.md` dos blocos e só os blocos de dor, comprador, concorrência, preço e objeção:
  ```
  python "${CLAUDE_PLUGIN_ROOT}/scripts/extrair_insumos.py" "<cliente>/0. Inputs e Transcrições"
  ```
- `${CLAUDE_PLUGIN_ROOT}/base/<setor>/fontes.md`, se existir. Sob demanda, desta pasta: `fontes.md`, `adaptacao_modelos.md`, `indice-docx.md`.
- Os documentos do próprio cliente quem lê é o agente das provas (passo 2), e as páginas da web, o pesquisador (passo 4). Este guia já traz o que você precisa dos agentes e dos geradores.
- **Portões.** Sem ficha: chame `/ee-trieme:novo-cliente` e pare. Foco de mercado com nível em aberto bloqueia a semana (B13): diga e pare. Seção obrigatória ausente ou ambígua é erro de ficha. Meta legitimamente desconhecida não bloqueia: estime SOM apenas com base suficiente; sem ela, registre a verificação necessária e deixe a comparação pendente.

Leia primeiro o estado vigente e as decisões substituídas. O histórico explica o caminho, sem restaurar uma recomendação antiga. **Pronto quando:** você sabe o foco/nível, a meta ou sua ausência, o preço, os papéis na compra e as decisões ainda vigentes.

## 2. Provas do cliente, num agente
Chame a ferramenta Agent (`general-purpose`, `model: "sonnet"`) com a pasta `_texto`, a lista dos documentos do próprio cliente tirada do `indice.md` (propostas, apresentação, plano de negócios, casos, contrato), os blocos do Kickoff que você abriu, o caminho de `<semana>/_fonte/provas-cliente.md` e este pedido:

> Leia os documentos e os blocos. Em `provas-cliente.md`, seção `## Provas do cliente`, grave uma linha por fato ou número que pode provar algo sobre o cliente:
> `| # | Fato ou número | Unidade e período | Tipo | Origem | O que pode provar | Decisiva | Destino |`
> - Tipo: observado, estimativa ou promessa. Número de proposta do cliente costuma ser estimativa ou promessa.
> - Origem: arquivo e página de `_texto`, ou a reunião e o minuto ("K 01:12:18"). Entram também as falas do Kickoff que provam algo: a objeção do comprador e a resposta do cliente; como o comprador faz hoje o trabalho que o cliente vende.
> - O que pode provar: delimite atributo, entidade, unidade, período e alcance cobertos. Fala registrada comprova a declaração; desempenho narrado sem verificação continua relato, identificado neste campo. Preserve os tipos existentes; "observado" para a fala não comprova o desempenho referido. Relatos úteis podem sustentar hipóteses e testes com origem e limites.
> - Antes de registrar divergência, leia B0 de `${CLAUDE_PLUGIN_ROOT}/skills/estruturacao-estrategica/base-de-todo-encontro.md`. Registre as duas origens e a base de comparação, ou o vínculo/contexto que falta conciliar.
> - Decisiva: "sim" quando pode sustentar a ideia central, o recorte, a PUV ou o enquadramento. Dado que a coleta ou as contas ainda vão trazer (preço de referência, tamanho do mercado) mantém o "sim".
> - Destino: em branco durante a coleta. Quem escreve o deck preenche antes de conferir. Preserve os IDs existentes.
> - Registre mudanças em `## Reclassificações`, colunas `ID | Estado anterior | Estado novo | Motivo`. Todo rebaixamento tem motivo e o histórico leva ao estado final da tabela. OCR sem conferência mantém esse motivo.
> - Sem prova disponível, mantenha a tabela com cabeçalho e declare `Sem provas: <motivo>`; isso exige revisão. Arquivo ausente ou inválido é erro; o novo presente não pode ser substituído silenciosamente pelo antigo.

Você lê a tabela e confronta as divergências alegadas com a ficha já lida, pela B0. **Pronto quando:** cada linha tem tipo e origem; contradições têm base comparável e contextos não conciliados têm verificação pendente.

## 3. Perguntar uma vez
Numa rodada só, cada pergunta com a resposta recomendada: o que a ficha e os insumos não trazem (concorrente não citado, praça de preço, mercado secundário). Plano de negócios ausente entra na rodada, porque a meta e o preço saem dele. Na mesma rodada, liste cada prova possivelmente decisiva lida por OCR, com o número, o arquivo e a página, para o consultor conferir. Conferida, ela pode ser decisiva e o tipo continua o mesmo; sem conferência, fica "não: OCR sem conferência", com pendência na ficha.

**Pronto quando:** cada resposta está na ficha ou virou pendência com dono e data.

## 4. Coletar os dados de mercado
Chame o agente `ee-trieme:pesquisador-mercado` (ferramenta Agent, `model: "sonnet"`) com a ficha, o setor, o foco de mercado com o nível, `${CLAUDE_PLUGIN_ROOT}/base/<setor>/fontes.md`, a pasta `<semana>/_fonte/` e as perguntas de dado do esqueleto (TAM, SAM, SOM, concorrentes, preço, ICP, benchmarks). Cada pergunta leva um id e a decisão que pode mudar ("se A, faço X; se B, faço Y"); pergunta que não muda decisão e que o contrato não pede fica fora. Na pergunta de concorrentes, passe cada nome que o cliente citou no Kickoff, como foi ouvido e com o horário. O pesquisador segue `concorrentes.md` desta pasta: até três buscas por candidato dentro do teto global de dez, encerrando assim que a identidade estiver demonstrada. Registre separadamente identidade, pertinência e página. Grafia ou página não confirmada vira pergunta, sem completar por semelhança de nome. Passe o comando já resolvido:
```
python "${CLAUDE_PLUGIN_ROOT}/scripts/coletar_fontes.py" "<semana>/_fonte/coleta/lista.txt" --saida "<semana>/_fonte/coleta" --procurar "<semana>/_fonte/coleta/procurar.json"
```
Ele devolve `_fonte/dados-pesquisa.json`; você lê esse arquivo, e a coleta de páginas e PDFs fica com o script. Dado com `valor: null` permanece pendente. Uma estimativa distinta exige premissas documentadas e cálculo; o valor ausente não vira número por receber um rótulo. Valor de fonte web vale com o trecho achado na página; sem o trecho, fica pendente até o consultor escrever `conferido` na linha.

**Pronto quando:** cada pergunta de dado tem valor com fonte e trecho, ou está pendente com o motivo.

## 5. Contas pelo Python
Toda conta (TAM, SAM, SOM, soma, percentual) vai em `<semana>/_fonte/contas.json`. Número decisivo que não é conta (preço de referência) também entra, com a fórmula igual à própria entrada. Grave o arquivo com a ferramenta Write e rode o script:
```json
Exemplo fictício de estrutura: os campos entre sinais de menor e maior são marcadores; substitua-os por valores documentados antes de executar o cálculo.
{"contas": [{"dado": "TAM em moeda", "formula": "compradores * preco", "unidade": "moeda",
  "periodo": "<período>", "decisivo": "sim", "usado_em": "S2 · TAM", "entradas": {
    "compradores": {"valor": "<quantidade verificada>", "unidade": "<unidade compradora>", "origem": "dados-pesquisa.json#<ID>"},
    "preco": {"valor": "<preço comparável>", "unidade": "moeda", "origem": "N<ID>"}}}]}
```
```
python "${CLAUDE_PLUGIN_ROOT}/scripts/calcular.py" "<semana>/_fonte/contas.json" --ficha "<cliente>/<Nome>.md" --dados "<semana>/_fonte/dados-pesquisa.json"
```
Origens aceitas: id de Números-fonte (`N03`), `dados-pesquisa.json#D07`, `arquivo.txt · página 3` (de `_texto`) e `premissa: consultor, dd/mm/aaaa`. Fórmula: `+ - * / ( )`, ponto decimal, nomes das entradas, `min`, `max`, `round`, `soma`. Erro do script se corrige na entrada. O deck copia o valor de `contas.resultado.json`.

**Pronto quando:** cada número estimável está em Números-fonte, com fórmula e origem; a parcela sem base tem lacuna, responsável e verificação, sem número inventado.

## 6. Ideia central e títulos
Grave `<semana>/_fonte/ideia-central.md` com **400 a 700 palavras no total**: ideia central, três linhas contratuais, decisão, títulos e índice curto. O registro de decisão tem aproximadamente 300 palavras dentro desse total. As provas completas ficam em `provas-cliente.md`.

1. Releia as provas depois da coleta e das contas. Quando o estado mudar, registre ID, estado anterior, novo e motivo em `Reclassificações`. Rebaixar uma decisiva exige justificativa; OCR sem conferência não vira decisiva.
2. A ideia central é uma conclusão que muda uma decisão sobre a trava, sustentada por duas evidências com fonte, e orienta a próxima conversa com o comprador. Escolha uma proposta e examine uma alternativa real nos quatro campos abaixo. A obrigação histórica de três candidatas da decisão 0040 foi substituída pela decisão 0047. Se os dados não permitem escolher, proponha a verificação que permite decidir.
3. Escreva uma vez cada linha abaixo, com o rótulo no começo da linha. Preserve a leitura literal de `Substituto:` e `Preço comparável:`. Sem substituto real documentado, escreva `Substituto: não identificado · <limite da pesquisa e verificação>` e mantenha-o fora da comparação; isso gera revisão, não ator fictício:
   ```
   O que vendemos: <entrega do cliente, na camada correta>
   Substituto: <nome curto> · <quem resolve hoje o mesmo trabalho no comprador>
   Preço comparável: R$ x · <por quê; ou nenhum · motivo>
   ```
4. Registro de decisão, pela regra de inferência de `padrao/estilo-de-escrita.md`:
   - **Decisão proposta:** escolha, público, prioridade e condições de viabilidade (equipe, orçamento, dependências).
   - **Alternativa considerada:** alternativa plausível e razão de não a escolher, vinculada à trava e às fontes. Aplique **Escolha e prioridade** do esqueleto à comparação e à relação entre registro, capa, ICP e plano.
   - **Evidências e premissa crítica:** provas a favor, evidência contrária mais relevante com referência e o que não está demonstrado. Sem evidência contrária encontrada, declare a ausência e os limites da busca.
   - **Teste e mudança de decisão:** primeira ação ou verificação, responsável, prazo, resultado observável e condição de rever a escolha. Incorpora os antigos campos “Primeira ação” e “O que faria mudar”.
5. Leve a proposta sustentada para a capa; cerca de dez palavras orienta clareza, sem exceder o recorte da evidência. Em `Títulos`, liste 01 a 08, omitindo 07 se a opcional não ajudar. Tema curto é válido quando comunica melhor. Feche com referências às provas, contradições e exclusões no detalhe.

**Pronto quando:** o resumo cabe no total, preserva as três linhas únicas, a alternativa e a contrária foram examinadas, e os títulos contam o argumento. Ausência de base é pendência de decisão, com teste; não exige tese inventada.

## 7. Escrever o deck
- Copie `${CLAUDE_PLUGIN_ROOT}/skills/pesquisa-mercado/gerador/modelo-pesquisa.json` para `<semana>/_fonte/conteudo.json`, se ainda não existir, e troque cada "PREENCHER:" pelo texto do cliente, seguindo a nota do próprio campo. Edite campo a campo, com a ferramenta Edit.
- O modelo padrão usa `esquema_pesquisa:2`, `meta_declarada` booleano e `tipo_comprador` B2B/B2G/B2C. Essa versão exige a nova espinha. JSON antigo sem versão permanece legível; quando um campo novo é introduzido, seu contrato é validado. Migre o fecho antigo `plano` para `proximos_passos`, sem apagar decisões históricas.
- Preencha cenário com fonte/ano/impacto; regulação quando pertinente. TAM/SAM/SOM permanecem três medidas, com dinheiro e compradores comparáveis; contagem ausente exige proxy fundamentado ou lacuna. Com meta, `leitura_meta` e `mercado_limita`; sem meta, pergunta de resultado/prazo, sem número fabricado.
- Em 03, `camadas` tem um ou mais grupos, com recorte, contagem ou lacuna, fonte e papel. B2B/B2G exige `comite_compra` em 06 (decide/influencia/usa), inclusive papéis ainda a confirmar. Em 08, `onde_concentrar` compara por critérios comuns e registra papéis e o que fica fora.
- SWOT, posicionamento e TOWS são concluídos após a coleta: SWOT permanece em 05; oportunidade/ameaça sem fonte vira sinal a coletar (onde/quem), e os quatro cruzamentos TOWS ficam no DOCX. Concorrentes confirmados e matriz de oferta ficam juntos em 04; substituto só quando documentado.
- Aplique **Posicionamento, oferta e alcance da prova** do esqueleto à frase de 04 e a `fundamento_oferta`: comprador, situação de compra, promessa, diferencial, provas, objeções e próximo passo. Hipótese traz fundamento e teste. Esse registro já sustenta a LP entre S3 e S4, mesmo sem Manual de Copy contratado; o manual da S5 formaliza o que foi construído.
- O DOCX abre com tela `so_docx:true, abertura_docx:true`, com achados que mudam a decisão e como ler dado/estimativa/premissa, indicando o dado que substituirá cada estimativa. O gerador a promove após a capa, sem repeti-la no detalhe. Feche o detalhe com PSE traduzido, sem códigos da ficha.
- Preencha o Destino de cada prova em `provas-cliente.md`: a tela ("tela 08"), "DOCX" ou "fora: motivo".
- **Antes de gerar, confira as 6 falhas que mais derrubam a nota** (regra completa no esqueleto):
  1. Cada título diz no máximo o que os rótulos da tela dizem, no mesmo recorte e no mesmo tipo. Ruim: "o preço do setor" para o preço de 2 concorrentes. Bom: "o preço de 2 concorrentes da região".
  2. Diferencie tração observada, cenário condicional e previsão. Premissa proposta segue a regra de estilo: origem, fundamento e teste; fato ausente continua ausente. Sem fundamento, mantenha a estimativa pendente uma vez na tela.
  3. Todo fato duro, inclusive no SWOT, tem "Consequência para o cliente" e "Decisão" na mesma tela, e o título traz a saída, não o medo.
  4. Diferença entre relatos segue B0: só chame contradição após conferir a comparabilidade. Preserve as duas origens e o que falta conciliar, sem criar entidades ou universos adicionais.
  5. Cada fraqueza e ameaça do SWOT tem destino: decisão no TOWS do detalhe, próximo passo ou semana que trata.
  6. O "Comece aqui" ataca a trava, cabe em 7 dias e põe o cliente diante do comprador prioritário.
- Antes de gravar, valide os dados sem criar saída; depois prepare o rascunho (HTML, DOCX S2, extração e conferência básica). Havendo versão enviada, preserve-a em `EE/_arquivo/`.
```
python "${CLAUDE_PLUGIN_ROOT}/skills/pesquisa-mercado/gerador/gerar_pesquisa.py" "<semana>/_fonte/conteudo.json" --validar
python "${CLAUDE_PLUGIN_ROOT}/scripts/preparar_entrega.py" "<semana>/_fonte/conteudo.json" "<semana>/pesquisa-mercado-<slug>.html" --semana 2 --cliente "<Nome>" --ficha "<cliente>/<Nome>.md" --modo rascunho --consultor "${user_config.consultor_nome}" --cargo "${user_config.consultor_cargo}"
```
- O gatilho reconhece a conferência dessa revisão pelos hashes. Sem comprovante válido executa a básica; não abre navegador nem rede. Corrija erros na ficha e no JSON e prepare novamente.

**Pronto quando:** o deck gera sem erro e toda prova decisiva tem destino.

O fecho usa um bloco `proximos_passos` com `trava`, `acoes`, `pausa` e `gancho`. Há de uma a cinco ações pertinentes, cada uma com `acao`, um `dono`, `prazo` e `comece_aqui` booleano. Exatamente a primeira é prioritária, cabe em sete dias e respeita dependências e responsável proposto/confirmado. O plano por horizontes será consolidado na S5; a S2 termina com compromisso concreto e pergunta real para a S3.

Inclua iniciar o cliente oculto após a Pesquisa, com dono/data: cliente e dois concorrentes identificados, persona coerente com praça/DDD/e-mail e roteiro comum. Em contas que se conhecem, apenas canais públicos. Registre execução válida, parcial, inválida ou ausente; teste contaminado não gera score e não elimina evidência independente. Se algum insumo faltar, a ação explicita a condição e sua resolução, sem inventar realização.

## 8. Revisão numa rodada
1. Use `_fonte/telas.md` atualizado pelo preparador e confira no manifesto os hashes da extração, do HTML e do `_fonte/conteudo.json` da mesma preparação. As telas `so_docx` desse JSON são a fonte do conteúdo exclusivo do DOCX; a extração HTML não as contém.
2. Na mesma mensagem, chame os dois revisores: o agente `ee-trieme:avaliador-pesquisa` (ferramenta Agent, `model: "sonnet"`), com os caminhos de `telas.md`, de `_fonte/conteudo.json`, de `_fonte/ideia-central.md`, de `_fonte/provas-cliente.md`, da ficha e da saída `<cliente>/_ensaios-internos/qualidade-semana-2.md`; e o ensaio, `/ee-trieme:ensaio-cliente <Nome> 2`.
3. Junte numa lista os ajustes dos dois e os cortes do ensaio. Em conflito, vale o que tem prova e respeita o esqueleto; condensação segue B4, com destino no DOCX; aprovação continua com o consultor. Aplique tudo de uma vez (a ficha primeiro, se mexer em número; depois o `conteudo.json`). Confira a revisão corrigida por **Escolha e prioridade** e **Vínculo com a compra** do esqueleto. Reconcilie o plano corrigido inteiro pela checagem **Condições e ordem de execução** de B8, inclusive quando um ajuste acrescentar condição a uma etapa. Essa conferência do autor integra a mesma passagem de correção, sem outra chamada de avaliador ou ensaio. Prepare a revisão final no próximo passo.
4. Depois da última correção, passe por `padrao/estilo-de-escrita.md` e prepare a revisão final uma vez:
   ```
   python "${CLAUDE_PLUGIN_ROOT}/scripts/preparar_entrega.py" "<semana>/_fonte/conteudo.json" "<semana>/pesquisa-mercado-<slug>.html" --semana 2 --cliente "<Nome>" --ficha "<cliente>/<Nome>.md" --modo final --fontes online --consultor "${user_config.consultor_nome}" --cargo "${user_config.consultor_cargo}"
   ```
   Em execução com acervo congelado, troque por `--fontes congeladas --coleta "<semana>/_fonte/coleta"`; não faça pesquisa adicional. O relatório declara as limitações das evidências salvas. Erro ou etapa obrigatória não realizada impede conclusão. A extração e o DOCX são da revisão final; qualquer edição posterior exige nova preparação. A revisão editorial continua única, com segunda rodada só a pedido do consultor. A avaliação experimental, separada, usa os hashes finais e a rubrica externa.

5. No registro interno (`<cliente>/_ensaios-internos/registro.md`), em "Ensaios e mesa": a linha do ensaio, com a decisão do consultor sobre cada corte, e abaixo da tabela a do avaliador (data, média, defeitos marcados e arquivo). Segunda rodada, só a pedido do consultor.

**Pronto quando:** a conferência final passa sem erro e as duas linhas estão no registro.

## 9. Decisão do consultor
Ele lê a nota do avaliador e o rascunho, confere o SOM contra a meta, decide a trava do encontro e se a tela opcional "Como os concorrentes se posicionam" entra.

## 10. Depois da reunião
Siga `${CLAUDE_PLUGIN_ROOT}/skills/estruturacao-estrategica/rotina-pos-encontro.md` com `--semana 2`. Desta semana: a trava e a pergunta da Semana 3 vão para a ficha, e as fontes públicas novas são propostas ao curador para `base/<setor>/fontes.md` (fonte, link, o que traz, data de abertura; dado de cliente fica fora). O consultor decide o envio do HTML, do DOCX e da mensagem.
