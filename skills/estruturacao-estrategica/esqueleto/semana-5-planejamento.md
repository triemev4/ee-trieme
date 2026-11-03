# Esqueleto · Semana 5 · Planejamento Estratégico + Entregáveis

Base: `../base-de-todo-encontro.md`. Valem B0 a B6 e B9 a B13. Aqui a B7 é a restrição principal e a B8 vira o Mapa de Ações.

**Pergunta do encontro:** qual restrição a evidência sustenta, o que executar primeiro e em que condição revisar a decisão?
**Duração:** 1h30.
**Papel na EE:** consolidar e decidir. Liga efeitos à restrição sustentada, seleciona execução e entrega a matriz do contrato. Incorpora insumo novo com origem e conta rastreada; cenário e proposta seguem a regra de estilo.
**Guia da etapa:** `skills/plano-final/SKILL.md` (comandos). Modelos e critérios dos entregáveis: `skills/plano-final/entregaveis.md`. Layout e CSS: `moldes/semana-5.html`, preenchido por `scripts/preencher_molde.py`.

## Insumos

- A ficha: matriz do Contrato (o que se entrega, peça ou briefing), Números-fonte decisivos, Meta, condições e efeitos indesejados.
- Fio do projeto vigente e histórico, Direcionamento e Decisões da ficha; Próximos passos e planos pertinentes das Semanas 2 a 4, teste do dobro da S4 e forecast da S3.
- Transcrições e mensagens pós-encontro, das mais recentes às mais antigas (B0): validações, ressalvas e as restrições que o cliente já declarou.
- Os arquivos em `Entregaveis/` e a ata da mesa com o cliente na cabeceira, no registro interno (`_ensaios-internos/registro.md`, seção Ensaios e mesa).

## Sequência de telas (11; o Mapa pode ocupar 2 telas)

| # | Tela | Função | Componente | Regra de conteúdo |
|---|---|---|---|---|
| 1 | Ponte entre encontros | Retomar | `.bridge-track` + 2 colunas + `.pausa` | Recap vigente das S2 a S4 e pauta real |
| 2 | Capa | Abrir | hero + `.v4-mark` | Referências conhecidas com estado, sem transformar SOM em promessa |
| 3 | Caminho da receita | Consolidar | `.caminho` | Etapas pertinentes do formato, achado, estado e origem; quantidade conforme o trabalho real |
| 4 | Restrição | Decidir hipótese | `.grid.g4` + cadeia + explicador | Evidência e limite sustentam a hipótese; S5 não confirma por calendário |
| 5 | Playbook tático (opcional) | Selecionar | `.segcard` | Soluções anteriores e insumo novo fundamentado, com origem |
| 6 | Horizontes e matriz | Ordenar | `.roadmap-rail` + `table.gr-matriz` | Oito linhas: sete dimensões originais mais calendário; evolução H1/H2/H3 sem projetos inventados |
| 7 | Mapa de Ações | Executar | `.blockbar` + `.lanes` + `.ac` | Até duas seções com a mesma chave; até três frentes H1, dono, tipo, origem, liberação e capacidade |
| 8 | A conta da receita | Conferir economia | `.rtable.receita` + `.selo` | Incremento, recorrência, unidade/período, contribuição, tempo e sobreposição; uma alavanca pertinente ou lacuna explícita |
| 9 | Riscos e premissas | Condicionar | `table.riscos` + `table.premissas` | Somente itens pertinentes, sem mínimo para preencher vagas; dono, teste e decisão |
| 10 | Entregáveis | Entregar | `.entreg-grid` | Matriz do contrato, status real e arquivo quando pronto |
| 11 | Fechamento | Começar e revisar | tese + `ol.dias` + `.proxima-restricao` + `.pausa` + `.gancho` | Tese específica e proporcional; primeira semana pertinente, prioridade e condição de revisão |

Tópico sem achado próprio segue B4: lacuna uma vez na apresentação, pilar no detalhe. Sigla vem depois da tradução. Árvore, dilema, cinco passos e classificação TOC ficam no fundamento quando ajudam o raciocínio; não são telas obrigatórias nem prova formal exigida.

## Restrição e dimensões dos horizontes

- Sustente a restrição com os efeitos, evidências e estado do Fio. Escreva a limitação específica, proporcional à evidência. Se houver lacuna, apresente hipótese de trabalho e teste decisivo com dono, prazo e resultado observável.
- Compare com meta e base na mesma unidade e período quando existirem. Meta ausente continua lacuna; nenhuma projeção é criada para ocupar o campo. Decisão anterior pode ser substituída por evidência nova, com registro no Fio.
- Mostre condição de revisão: marco do teste ou antes se a fila, a capacidade ou o gargalo mudar. A S5 não converte a hipótese da S4 em certeza por passagem de semana.
- A matriz tem oito dimensões: desenho do CRM, estrutura de campanhas, rastreamento, critérios de qualificação, fluxo das campanhas, TAM/SAM/SOM básicos, estrutura do time e calendário do cliente (evento crítico, sazonalidade, ciclo de compra e prazo). Cada linha mostra H1/H2/H3 e origem. Não obriga contratar, criar meta ou executar uma ação em toda célula; condição ou ausência justificada preserva o trabalho real.
- Fato ausente permanece ausente. Insumo novo entra na ficha e no `calcular.py` quando houver conta, preservando unidade, período e estado. Posicionamento sustentado antecede a Landing Page, mesmo sem Manual de Copy contratado.

## Mapa de Ações

- É o único Mapa (B8): escolhe a execução, sem acumular todos os planos. H1 tem no máximo três frentes ativas no total, entre Vendas e Marketing. Cada card traz o primeiro passo da frente; desdobramentos e backlog ficam no detalhe.
- O primeiro passo de cada frente tem data proposta, responsável **proposto** ou **confirmado**, condição explícita de liberação e conclusão observável. Sem data-base confirmada, use D+N após validação. `.orig` aponta semana ou insumo novo; critério A/B/C é proposta justificada para decisão, não formulário vazio.
- Toda ação identifica um responsável, pela regra **Viabilidade do Mapa** abaixo, e a etiqueta `.tipo`, com `.tipo-leg` abaixo do `.blockbar` do primeiro bloco.
  - **Quick win:** resultado visível em até 30 dias, depende só de decisão ou configuração interna.
  - **Estrutural:** constrói a base (processo, sistema, time) ou depende de outra ação.
- Exatamente um "Comece aqui", ligado à restrição, no topo da trilha. Se o Kickoff registrou um evento crítico (data ou compromisso nos próximos 90 dias), as ações que o protegem vêm logo depois.

### Viabilidade do Mapa

Antes de confirmar o Mapa, percorra as ações de cada horizonte por responsável e recurso compartilhado:

1. Use cargo informado ou função proposta; nome só se informado. **Confirmado** exige fonte do aceite; **proposto** depende de aceite e disponibilidade, sem pressupor pessoa ou contratação.
2. Confira simultaneidade e capacidade conhecida de cada responsável. Libere a primeira execução apenas após suas condições (B8); três frentes não garantem disponibilidade. Reduza ou sequencie quando houver conflito.
3. Relacione recursos à conta e ao detalhe de investimento: tempo interno, desembolso, recorrente e pontual. Cotação ausente é "a cotar", não zero; horas não viram reais sem base. Preserve o estado de cada premissa.

Mantenha condição e pendência junto da ação dependente no HTML e no DOCX, pela B8; o detalhe pode guardar esforço, premissas e derivações. Responsável, disponibilidade ou custo decisivo desconhecido não autoriza afirmar execução viável. A análise pode ser entregue com pendências explícitas, sem declarar essas ações liberadas.

## A conta da receita e os riscos

- Use `tela-08 = {titulo, base, alavancas, lacuna}`. Cada alavanca traz nome, incremento sobre a base, recorrência, unidade/período, margem ou contribuição, tempo, sobreposição, fonte e `.selo` **dado**, **estimativa** ou **premissa**. Uma alavanca pertinente basta; sem base, a lista pode estar vazia com lacuna explícita e teste para decidir.
- Receita atual, receita incremental, venda pontual e recorrência são grandezas distintas. Considere maturação e dupla contagem: retomada, conversão e recompra sobre a mesma venda não são somadas como efeitos independentes. Cálculo não transforma premissa em dado.
- Preserve fonte e estado do forecast vigente, referência de custo, histórico, verba e recursos do Mapa. Sem retorno defensável, mostre teste e condição de avanço. Custo desconhecido é a cotar; esforço interno não é zero; horas não viram reais sem base.
- `tela-09 = {titulo, riscos, premissas}` usa tabelas com itens pertinentes, limitados pela leitura. Listas vazias são legítimas quando não há item conhecido; ausência não significa garantia de inexistência. Cada premissa que decide a execução informa como validar, dono e quando decidir. Não há mínimo fixo de riscos ou premissas.

## Primeira semana e revisão

No slot `tela-11`, a tese é específica e proporcional à evidência; não segue fórmula fixa de exclusão. `comece_aqui` lembra a prioridade do Mapa, sem duplicá-lo. `primeira_semana` tem somente ações pertinentes, de uma a cinco, em `ol.dias`, com ação, dono e prazo. Uma ação é suficiente para começar. `.proxima-restricao` informa quando e por qual condição a hipótese será revista; se a restrição ainda não estiver resolvida, o teste continua sobre ela.

## Entregáveis

- Um card por item da matriz do Contrato (B10), nenhum fora dela. "Pronto, clique para abrir" só com o arquivo em `Entregaveis/` e o link abrindo; senão "Em produção" ou "Pendente", com o motivo. "Pendente" vale só para pendência do cliente, nas condições de `esqueleto/encerramento.md`; atraso do consultor é "Em produção".
- Critério de aceite de cada item: `skills/plano-final/entregaveis.md`.
- Régua de CRM e especificação de atendimento com IA entram só por contrato ou aditivo. Sem contrato, viram recomendação no encerramento, ou no Handoff quando houver Executar.
- Tudo no nível "pronto para configurar". Implantar é execução, depois da EE.

## Modulação

- **Formato:** etapas do caminho da receita. Inside Sales: Aquisição, Primeiro contato, Cotação e fechamento, Recompra. E-commerce: Visita, Carrinho, Pedido, Recompra. PDV: Chega à loja, Atendimento, Compra, Volta. Dimensões da matriz: `padrao/formatos-de-negocio.md`, 7.1, mais calendário do cliente (evento crítico, sazonalidade, ciclo de compra e prazo).
- **Maturidade:** baixa, o H1 é fundação e a mídia nova só entra com dado. Alta, a restrição continua proporcional à evidência e a otimização considera margem, capacidade e resultado por canal.
- **Perfil do decisor** (`padrao/mapa-de-pessoas.md`): o Analítico pede fundamento, premissas e conta, o Executor pede o Mapa cedo, o Planejador pede riscos e rotina.
- **Playbook, quando ligado:** os temas reais do cliente (aquisição, comercial, conteúdo), com retenção se a recorrência é forte e autoridade se a marca é o gargalo.

## Depois do encontro

Encerramento: `esqueleto/encerramento.md`. O Handoff (`esqueleto/handoff-executar.md`) só existe quando o cliente contrata o Executar.

## Fora da semana

A tela não promete escopo, preço ou prazo do Executar, nem traz comitês, ciclos ou matriz de expansão do produto de origem.

## Pronto quando

Checklist B12, mais:
- A restrição tem evidência e estado, ou teste decisivo para resolver a lacuna; a matriz tem oito dimensões e origem.
- O Mapa passou por **Viabilidade do Mapa**, tem responsável ou pendência condicionante explícita, etiqueta e origem em toda ação, e um só "Comece aqui".
- A conta distingue base e incremento, recorrência, unidade/período, contribuição, tempo, sobreposição e estado; riscos e premissas não foram fabricados para preencher vagas. A primeira semana tem prioridade e condição de revisão.
- Todo entregável da matriz tem status real e link que abre; a ata da mesa está no registro interno, com a decisão do consultor sobre cada ajuste.
