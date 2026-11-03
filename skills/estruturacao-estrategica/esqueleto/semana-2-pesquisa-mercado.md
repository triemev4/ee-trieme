# Esqueleto · Semana 2 · Pesquisa de Mercado

Base: `../base-de-todo-encontro.md` vale antes deste esqueleto. Guia da etapa: `skills/pesquisa-mercado/SKILL.md` (passos e comandos).

**Pergunta do encontro:** o mercado comporta a meta? Contra quem a empresa disputa, para quem vende e o que a diferencia?
**Papel na EE:** lanterna. Mostra o tamanho da oportunidade, as lacunas de posicionamento e o foco de clientes. Mídia e CRM ficam nas Semanas 3 e 4.
**Referência de layout e CSS:** `referencias/layout/pesquisa-mercado.html`.

## Insumos

1. A ficha: Dados mínimos (foco de mercado e nível, meta, preço, carteira, conversão), Números-fonte, Meta, condições e efeitos indesejados, Persona do cliente, Direcionamento vigente, Restrição, PSE e Decisões por reunião. Leia o estado vigente e as substituições; histórico não volta a comandar execução.
2. O Registro e a transcrição do Kickoff: concorrentes citados, mercados declarados, sazonalidade.
3. As provas do cliente: número e fato dos documentos dele (propostas, apresentação, plano de negócios, casos), tirados antes da pesquisa web (`_fonte/provas-cliente.md`).
4. Pesquisa externa atual, nesta ordem: fonte oficial, consultoria ou imprensa especializada, estimativa V4, sempre com fonte e ano (`skills/pesquisa-mercado/fontes.md`).
5. Preço e posicionamento dos concorrentes efetivamente confirmados, escolhidos pela regra "Concorrentes certos"; falta de nome ou preço vira verificação, sem preencher vagas.

## Sequência de telas (10, ou 11 com a opcional)

| # | Tela (eyebrow) | PSE | Componente | Regra de conteúdo |
|---|---|---|---|---|
| 1 | Ponte entre encontros | · | `.bridge-track`, 2 colunas, `.pausa` | "O que já vimos": fatos do Kickoff. "O que vamos ver hoje": a pauta real, na ordem das telas, com a trava primeiro |
| 2 | Capa | · | hero, `.v4-mark` | Título = a ideia central, em até 10 palavras. 2 ou 3 métricas que a provam, com fonte |
| 3 | 01 · Análise de mercado | Contexto | `.cell`, `.barra`, `.rtable` | Preço comparável, cenário e macroeconomia: de 1 a 3 fatos com fonte, ano e efeito sobre a venda. Regulação quando pertinente, indicando limites na venda e comunicação |
| 4 | 02 · Tamanho do mercado (TAM, SAM e SOM) | Contexto | 3 elipses e legenda | Dinheiro e compradores; fórmula, premissas, fonte e período. Meta numérica exige leitura da participação no SAM e se o mercado limita; sem meta, pergunta de resultado e prazo. SOM segue capacidade e oportunidade, não a meta |
| 5 | 03 · Camadas e papéis | P | `.rtable` | Um ou mais grupos pertinentes, com nome, recorte, contagem ou lacuna, fonte e papel econômico/na compra. Duas camadas são válidas; não inventar terceira |
| 6 | 04 · Concorrentes | P → S | `.rtable`, `.segcard`, frase | Matriz com público, diferencial, atendimento, preço, canal e como anunciam; fonte/data. Colunas só para atores confirmados e substituto quando real. Posicionamento com prova e estado; fundamento da oferta antes da LP |
| 7 | 05 · Forças, Fraquezas, Oportunidades e Ameaças (SWOT) | P | 4 `.segcard` | Quadrantes permanecem. Oportunidade/ameaça sem fonte externa vira sinal a coletar, onde e quem verifica; nunca fato fabricado |
| 8 | 06 · Perfil de Cliente Ideal e personas (ICP) | P | `.cell`, `.segcard`, `.rtable` | Critérios e necessidades de compra; B2B/B2G traz quem decide, influencia e usa, com origem ou pendência explícita. A prioridade entre mercados fica em 08 |
| 9 | 07 · Como os concorrentes se posicionam (opcional) | P | mapa ou cards | Só quando fontes pertinentes sustentam a comparação e ela muda a decisão; decisão do consultor |
| 10 | 08 · Onde concentrar | S | `.rtable`, frase | Critérios comuns, papel de cada grupo/mercado (base, expansão, possibilidade, fora), evidência, condição de revisão e por agora não |
| 11 | Próximos passos | S → E | `.ac`, `.own`, `.ac.prio`, `.pausa`, `.gancho` | Trava, de 1 a 5 ações com um dono e prazo cada; exatamente uma primeira prioridade. Pausa de validação/viabilidade seguida de gancho real para S3. Sem trilhas por horizonte |

O TOWS (quatro cruzamentos) e o detalhe dos concorrentes vão para o DOCX. Abertura `so_docx:true, abertura_docx:true` entra após a capa, antes da ponte. O PSE fundamenta os achados e fecha o detalhe, sem códigos internos. B4 permite condensar lacunas repetidas no DOCX preservando cobertura; não elimina perguntas decisivas.

## Regras desta semana

- **Ideia central.** O deck defende uma ideia que muda uma decisão do cliente, com evidências e limites identificados. A capa e os títulos de 01 a 08 permitem acompanhar o argumento. Título curto orienta clareza; pode nomear o tema quando isso for mais fiel ao conteúdo, sem impor frase conclusiva. Como escolher: guia da etapa, passo 6.
  Exemplo fictício de título específico: "A equipe perde tempo procurando documentos. Um índice comum pode facilitar a consulta."
- **Escolha e prioridade.** Compare a proposta e a alternativa pelos mesmos critérios que mudam a decisão, escolhidos pela trava, com evidências e incertezas à vista. Uma lacuna compartilhada não basta para favorecer uma opção: explicite a evidência que as distingue ou mantenha a escolha provisória, com teste que possa mudá-la. A comparação pode ser qualitativa; notas e pesos exigem fundamento. Confira o registro de decisão, a capa, o ICP e o plano juntos: a prioridade de execução precisa ser coerente. Quando tiverem papéis diferentes (sustentar a base, explorar uma expansão, chegar ao comprador por um intermediário), explique essa relação nas telas pertinentes; o fundamento detalhado pode ir ao DOCX. Uma conversa exploratória com público secundário pode vir primeiro quando seu papel e esforço estiverem justificados; isso não o torna automaticamente prioritário para execução.
- **Enquadramento honesto.** Fato duro (preço acima, conversão baixa, concorrente forte) entra inteiro, com duas frases curtas na mesma tela: "Consequência para o cliente: ..." e "Decisão: ..." (seguir por outro caminho, adiar, abandonar um segmento ou buscar prova antes de prometer). O título diz o que fazer com o medo que o cliente declarou.
  Ruim: "Seu preço é o dobro da média". Bom: "O mercado paga a aula avulsa. Vocês vendem o plano anual, com outra régua."
- **Mercado medido pelo que o cliente vende.** TAM e SAM combinam dinheiro e compradores (empresas, lojas, escolas). Aceitam preço do cliente, referência declarada comparável ou proxy defensável com cadeia de premissas e conta rastreada. Sem base para contar, indicar ordem de grandeza sustentada ou lacuna com verificação. Preço de outro produto não vira automaticamente preço do cliente. As três medidas do framework usam unidades comparáveis, SOM dentro do SAM, período dos dados e horizonte da projeção ("em 12 meses"). Os grupos da tela 03 são outra segmentação, sem cardinalidade fixa.
  Exemplo fictício: um serviço hipotético de organização de documentos estima o mercado pelo número de equipes que poderiam contratá-lo multiplicado pelo preço comparável do serviço, não pelo faturamento dessas equipes.
- **Concorrentes certos.** Nesta ordem: (1) quem vende para o mesmo comprador a mesma coisa ou algo vizinho; (2) o substituto: quem ou o quê faz hoje, dentro do comprador, o trabalho que o cliente vende; (3) um modelo a copiar de outro mercado, se ensina algo. Cada um traz "o que copiar" ou "o que evitar".
  - Teste do substituto: se o cliente não existisse, quem faria esse trabalho amanhã? Pode ser um setor, um sistema, uma planilha ou ninguém, e a origem pode ser a fala do Kickoff, com o horário. O substituto faz o mesmo trabalho que o cliente; o produto que o comprador já compra na camada de baixo é outra coisa. Exemplo fictício: para o serviço hipotético de organização de documentos, o substituto pode ser uma planilha mantida manualmente; o sistema de armazenamento já usado pela equipe é uma camada diferente.
  - Concorrente entra pelo nome e pertinência confirmados. Nome só ouvido vira pendência, com dono. Um só confirmado é suficiente; sem nenhum, registrar sinais e coleta, sem inventar empresa. O substituto entra apenas se real e documentado, concordando com a decisão registrada; ausência gera aviso de revisão, não erro nem obrigação de criar um cartão.
  - O comprador fica na tela 01: comprador que já usa algo parecido é prova de demanda. Quem vende para outro comprador fica fora, mesmo que seja grande.
- **Rótulo preciso.** O rótulo do cartão diz só o que o número conta, com o recorte da conta e o tipo: observado, estimativa, promessa ou teto. A causa e a conclusão vão para o título. Teto ou valor máximo é "teto", estimativa do cliente é "estimativa", promessa é "promessa". As notas do `modelo-pesquisa.json` trazem a regra campo a campo.
- **Provas do cliente primeiro.** Número do material do próprio cliente vale mais que média de mercado para os atributos que ele efetivamente cobre, e passa pelo `calcular.py` como qualquer número decisivo. Seu alcance segue a regra PUV e alcance da prova. Toda prova decisiva de `provas-cliente.md` tem destino (a tela, o DOCX, ou "fora: motivo"). Reclassificação guarda ID, estado anterior, novo e motivo no mesmo registro; rebaixamento sem motivo é erro. Prova que é fala de reunião aparece na tela de destino com a origem: "(Kickoff, 01:12:18)". (o verificador confere)
- **Dado velho.** Dado de concorrente com mais de 2 anos aparece com o ano à vista e ao lado de outro dado mais novo.
- **Preço** aparece na análise de mercado (o que o mercado paga contra a tabela do cliente) e na linha "Preço" da comparação. Benchmark externo é referência de preço; a meta é do cliente.
- **SOM.** Na unidade do comprador, dentro do SAM e com horizonte de 12 meses. Separe tração observada (o que já ocorreu, com período), cenário condicional (capacidade e oportunidades sob premissas com origem) e previsão (estimativa de resultado futuro com método e limites). Cada cenário usa o menor entre capacidade e oportunidades que fecham no período, considerando ciclo de compra; reunião não é contrato.
  - Cenário pode usar premissa proposta pela consultoria, marcada, justificada e com teste de confirmação/refutação, pela regra de estilo. Período desconhecido permanece desconhecido: explicite a condição de comparação. Sem fundamento para delimitar a estimativa, mantenha-a ausente e indique a verificação.
  - Meta compara o cenário, sem definir o SOM. Separe tração, cenário condicional e previsão; conta rastreada no `calcular.py`.

- **TOWS no detalhe**, alimentando as decisões de posicionamento e prioridade. Cada fraqueza e ameaça tem destino: decisão nos cruzamentos, ação sustentada ou semana que a trata. Sem fonte externa, o quadrante de oportunidade/ameaça registra sinal, onde coletar e responsável.
- **Posicionamento, oferta e alcance da prova (compatibilidade: PUV).** A frase na tela 04 traz evidência, relato ou teste e seu estado. Registre comprador, situação de compra, promessa, diferencial sustentado, provas, objeções e próximo passo antes da LP. O Manual de Copy, quando contratado, formaliza esse fundamento na S5; sua contratação não condiciona o raciocínio nem a produção da LP. Tópico que só repete lacuna segue B4.
  **Vínculo com a compra:** antes de escolher a frase e os pilares, relacione o atributo disponível a uma necessidade ou critério do comprador descrito na tela de ICP e personas e explique o efeito esperado para ele. Identifique a origem dessa necessidade, inclusive quando for visão relatada pelo vendedor. Benefício ou relevância apenas inferidos seguem como hipótese pela regra de inferência; atributo comprovado não comprova sozinho o efeito na compra. Sem base para essa ligação, registre o que testar nos espaços existentes, mantendo o estado da evidência pelos casos abaixo.
  - **Evidência suficiente:** formule posicionamento e atributos dentro do que as fontes sustentam. "Prova:" identifica evidência observada com origem e atributo, entidade, unidade, período e alcance cobertos. Dado, caso, depoimento autorizado ou certificação só sustenta o que efetivamente demonstra. Um cadastro histórico de estabelecimento não comprova prazo de entrega nem situação atual; sem vínculo confirmado, também não comprova atributo de outra entidade. Exclusividade ou combinação rara de atributos exige base comparativa pertinente.
  - **Somente relato ou base parcial:** mantenha título e frase como hipótese, com origem e limites. A fala registrada comprova o que foi declarado; o desempenho narrado continua relato enquanto não verificado. Relatos úteis permitem raciocinar, priorizar e propor testes, conservando premissas e condições da ação. Use os cards para a base relatada, o que falta e como verificar, com rótulos correspondentes ao conteúdo.
  - **Sem base suficiente para formular:** mantenha a formulação pendente, com lacuna e teste; as demais decisões sustentadas avançam. Não completar promessa para preencher campo: o campo registra o estado e a verificação.
- **Mercados múltiplos:** cada mercado declarado no Kickoff tem análise no DOCX (`skills/pesquisa-mercado/indice-docx.md`); 08 traz prioridade, papéis e o que fica fora.
- **Detalhe no DOCX**, nas telas `"so_docx": true` do `indice-docx.md`.
- **Siglas:** a tradução vem no eyebrow, e a sigla depois. **Uma `.pausa` por tópico**, com uma pergunta ao cliente. **Visual por nome:** o TAM/SAM/SOM em 3 elipses na tela 4; nas outras, o componente da tabela basta.

## Próximos passos

Foco de mercado, posicionamento/prova e preço orientam as ações pertinentes, sem três frentes obrigatórias.
- De 1 a 5 ações, com dono proposto/confirmado e prazo; desdobramentos ficam no detalhe. Contrato do gerador: bloco `proximos_passos` com `trava`, `acoes`, `pausa`, `gancho`; cada ação tem `acao`, `dono`, `prazo`, `comece_aqui` booleano.
- Exatamente uma `comece_aqui:true`, na primeira posição, ataca a trava e cabe em 7 dias. A conversa com o comprador ou teste que realiza a ideia central respeita as condições de viabilidade; ação exploratória não se apresenta como execução aprovada.
- Ação é verbo e objeto concreto. Exemplo fictício: "Contatar as empresas de uma lista hipotética e agendar uma demonstração". "Decidir", "avaliar" e "definir" vêm com o objeto e o critério da decisão.
- As ações saem das soluções publicadas nesta semana. Conta, reunião ou contrato específico vai para a pendência da mensagem. Mídia e CRM: só apontar que vêm depois.
- Plano consolidado por horizontes na S5. `plano` legado continua aceito com aviso de migração, preservando conteúdo antigo; não é o formato de novas pesquisas.

## Modulação

- **Formato e modelo de negócio:** `padrao/formatos-de-negocio.md` (Semana 2) e `skills/pesquisa-mercado/adaptacao_modelos.md`.
- **Nível de mercado:** a unidade do SOM (contratos, clientes, pedidos) e o nível geográfico vêm do foco de mercado da ficha. Um nível por vez (B11).
- **Setor regulado:** a PUV e as provas respeitam o que pode ser divulgado.
- **Perfil do decisor:** o Analítico pede premissas explícitas; o Comunicador, o comparativo visual (`padrao/mapa-de-pessoas.md`).

## Fora da semana

Auditoria de mídia/CRM e execução detalhada de aquisição ficam nas S3/S4. Uma classificação de contas pode explicar papéis e prioridade sem antecipar o plano comercial. Preserve meta e condições declaradas; qualquer correção sustentada mantém a original ao lado e requer decisão registrada.

## Pronto quando

Checklist B12, mais:
- Cada número estimável de TAM, SAM, SOM e preço de referência está em Números-fonte, com fórmula e premissas; a meta aparece ao lado quando informada. Premissa proposta segue a regra de estilo. Sem fundamento, lacuna uma vez na tela, com verificação; detalhe no DOCX.
- O substituto, quando incluído, passa no teste "quem faria esse trabalho amanhã?"; os grupos têm papéis pertinentes e cada rótulo diz só o que o número conta.
- O cenário tem fonte/ano e efeito, B2B/B2G tem comitê, a regulação pertinente é tratada. SWOT e sinais preservam fontes; TOWS fica no detalhe.
- Posicionamento e fundamento da oferta sustentam a LP antes da S5, com estado da evidência explícito; prioridade entre mercados fica em 08.
- A última tela tem trava, de 1 a 5 ações com dono/prazo, primeira prioridade única, pausa e gancho. DOCX abre com achados e como ler, sem duplicação, e termina com PSE sem códigos.
- A capa traz a ideia central, toda prova decisiva tem destino, e a revisão rodou numa leva, com avaliador e ensaio.
