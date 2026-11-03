# Glossário da EE

Os termos do pacote e da Estruturação Estratégica, um nome por conceito. Vale para guias, decks, fichas e mensagens. O termo da coluna "evitar" sai do texto. O verificador confere nos decks só as seções sem "(interno)" no título, porque o resto é vocabulário de trabalho e o cliente pode usar essas palavras no negócio dele.

## O pacote e o trabalho (interno)

**Protótipo de landing page**:
Página navegável que apresenta uma oferta ao comprador, com texto final e comportamento demonstrável. Publicação e operação real de captura pertencem à execução quando contratadas.

**Comprador da oferta**:
Pessoa ou organização definida no ICP da Semana 2 para quem a página comunica. É distinta do contratante da EE, representado na Persona do cliente.

**Conferência da LP**:
Registro técnico ligado aos arquivos exatos que foram revisados. A aprovação do consultor é uma decisão separada, registrada na ficha para aquela revisão.

**Pacote**:
O conjunto de guias, modelos, scripts, casos de referência e índice de fontes instalado como plugin `ee-trieme`.
_Evitar_: kit, pasta de skills, `Skills/`

**Guia da etapa**:
O arquivo de regras e passos de uma etapa (`skills/<etapa>/SKILL.md`), chamado pelo maestro ou pelo comando.
_Evitar_: skill da semana, prompt

**Maestro**:
O guia `estruturacao-estrategica`, que lê o "Status" da ficha, identifica a etapa e chama o guia dela.
_Evitar_: skill-mãe, orquestrador

**Esqueleto**:
A sequência fixa de telas de uma semana, com a função e o componente de cada tela.
_Evitar_: template de telas

**Base**:
As regras B0 a B13 que valem para todo encontro (`base-de-todo-encontro.md`).
_Evitar_: constituição, regras gerais

**Assistente**:
O Claude Code quando gera material a partir dos guias.
_Evitar_: IA, agente, robô

**Molde**:
A página HTML de uma semana (3 a 5) com os textos em espaços marcados, em `moldes/`. O assistente escreve só o `textos.json`, e `scripts/preencher_molde.py` monta o deck.
_Evitar_: template, gerador (nome dos scripts das Semanas 1 e 2)

**Teste do pacote**:
O uso do pacote por um segundo consultor, com cliente fictício, antes do piloto, para o padrão ser testado por quem não o escreveu.
_Evitar_: ensaio (nome reservado ao teste do deck com o cliente simulado)

**Extrator de insumos**:
O script `extrair_insumos.py`, que transforma PDF, planilha (XLSX e CSV), DOCX, TXT e MD de `0. Inputs e Transcrições/` em texto limpo, em `_texto/`, com um `indice.md`. Página de PDF que é só imagem passa por OCR. Os guias leem os insumos por aí, nunca o PDF nem a planilha original.
_Evitar_: leitor de PDF, conversor de insumos

**`_texto`**:
A pasta `0. Inputs e Transcrições/_texto/`, com o texto de cada insumo. Cada trecho começa com o arquivo de origem e a página (ou a aba e as linhas); o que veio de OCR leva a marca `OCR` e não é prova decisiva até o consultor conferir a página. O gatilho de abertura não conta `_texto` como insumo novo.
_Evitar_: texto extraído, cache dos insumos

**Contas**:
Todo cálculo de número do deck (soma, percentual, TAM, SAM, SOM, forecast, funil, custo por resultado). É feito pelo script `calcular.py`, a partir de um `contas.json` com a fórmula e as entradas (valor, unidade e origem), e grava o resultado, a fórmula e a origem em "Números-fonte" da ficha. Nenhum número do deck é calculado de cabeça pelo modelo.
_Evitar_: conta de cabeça, cálculo do modelo

**Coletor de fontes**:
O script `coletar_fontes.py`, que baixa as URLs de uma lista, limpa o HTML e o PDF e grava um .txt por fonte e um `indice.json` (status, caracteres, motivo da falha).
_Evitar_: fetch, scraper, robô de coleta

**Coletor da auditoria**:
O script `coletar_auditoria.py`, que na Semana 3 tira os prints do site e do Google Meu Negócio, mede a velocidade pelo PageSpeed Insights e lê o SEO de cada página, e grava `auditoria.json` e `auditoria.md`.
_Evitar_: auditor automático, robô de auditoria

**Pesquisador de mercado**:
O agente `pesquisador-mercado`, chamado pelo guia da Semana 2: lê o texto limpo do coletor, busca o que falta na web e devolve `dados-pesquisa.json`, um dado por linha, com o trecho literal que prova e o pendente com o motivo.
_Evitar_: analista de mercado, robô de pesquisa

**Curador**:
Quem aprova a mudança de um guia e a entrada de fonte nova no índice.
_Evitar_: dono do padrão

## O cliente (interno)

**Ficha**:
O arquivo `<Nome>.md` na pasta do cliente, fonte única de status, contrato, dados mínimos, números, meta, memória estratégica, persona, glossário e pendências.
_Evitar_: nota de acompanhamento, dossiê, estudo do cliente, análise de dados

**Fio vigente**:
O resumo atual do Direcionamento na ficha. O histórico preserva formulações anteriores, sua situação e o registro que as substituiu.
_Evitar_: memória paralela, Fio em arquivo separado

**Situação**:
Estado de um registro estratégico na ficha: proposta, validada, em execução, substituída ou descartada. Um registro substituído permanece no histórico e aponta para o registro que assume; o resumo vigente indica qual registro orienta o trabalho. `Reconstituído` descreve proveniência, não situação: identifique a fonte e a data do conteúdo recuperado.

**ID P/S/E**:
Identificador interno estável de um Ponto, Solução ou elemento de Estrutura no registro PSE da ficha, no formato tipo + etapa + contador, como `P-M1`, `S-MK2` e `E-C3`. Não renumere; ligue Ponto, Solução, Estrutura e restrição relacionada pelos IDs.

**Proveniência reconstituída**:
Origem recuperada de material preexistente, com fonte e data da reconstrução. O item conserva sua situação estratégica (proposta, validada, em execução, substituída ou descartada).

**Modo do marketing**:
Resumo da estratégia de aquisição: volume, conta, combinado ou a verificar. As frentes registram separadamente público, função, abordagem, evento de conversão, destino e limite; modo combinado mantém frentes de volume e de contas quando ambas têm função.

**Frente de marketing**:
Um caminho de aquisição com público, função, abordagem, evento de conversão, destino e limite operacional definidos.

**Hipótese de trabalho**:
Explicação provisória que sustenta uma ação enquanto a evidência não permite concluir. Deve indicar alternativa, teste decisivo e condição de revisão; não é uma confirmação da restrição principal.

**Nota de preparo**:
O arquivo interno de condução do cliente: o que sabemos, pessoas e condução de cada encontro.
_Evitar_: dossiê, estudo do cliente, resumo de temas sensíveis

**Insumos**:
O material de origem do cliente: contrato, call e handoff da venda, transcrições e arquivos enviados.
_Evitar_: inputs (salvo no nome da pasta `0. Inputs e Transcrições/`), briefing do cliente

**Dado mínimo**:
Um dado que o Kickoff precisa obter, com classe Bloqueia, Limita ou Não se aplica (base B13).
_Evitar_: pergunta obrigatória

**Número decisivo**:
Número que entra na trava, no SOM, no forecast ou no Mapa de Ações, marcado "decisivo = sim" em "Números-fonte".
_Evitar_: número-chave, KPI principal

**Pendência**:
O que falta do lado do cliente ou da equipe, com dono, data e o que não será concluído sem ela, em "Pendências" da ficha.
_Evitar_: tarefa de casa, "a coletar"

**Estimativa V4**:
Número calculado pela equipe com as duas premissas com fonte e o método à vista.
_Evitar_: projeção sem método, chute, ordem de grandeza sem fonte

## O contrato (interno)

**Item do contrato**:
Uma linha do escopo assinado, registrada em "Contrato" da ficha.
_Evitar_: entregável, quando se fala do que foi vendido

**Entregável**:
O arquivo final que cumpre um item do contrato, com critério de aceite e evidência de envio.

**Peça**:
O entregável pronto para uso, produzido pelo consultor.
_Evitar_: arte, criativo final

**Briefing**:
A especificação que outra pessoa usa para produzir a peça; vale no lugar da peça só quando a matriz e o cliente confirmam por escrito.
_Evitar_: brief, rascunho da peça

**Encerramento**:
O fechamento da EE ao fim da Semana 5, sempre feito, com a matriz toda em "enviado".
_Evitar_: Handoff, quando não há Executar

**Handoff para o Executar**:
A passagem ao serviço de execução, feita só quando o cliente contrata o Executar.
_Evitar_: entrega final, passagem de bastão

## Os encontros

**Semanas**:
Kickoff · Pesquisa de Mercado · Diagnóstico de Marketing · Diagnóstico Comercial · Planejamento Estratégico + Entregáveis.
_Evitar_: Diagnóstico de Vendas, Plano de Marketing e Vendas, Plano Final, Entrega Comercial, Briefing Visual, sexta semana

**Trava do encontro**:
A dor que um encontro das Semanas 2 a 4 trata, nas palavras do cliente, tirada de "Meta, condições e efeitos indesejados".
_Evitar_: trava global, gargalo (como nome da trava), restrição (nas Semanas 2 a 4)

**Restrição principal**:
A causa comum dos efeitos indesejados, provada na Semana 5.
_Evitar_: trava (na Semana 5), problema central, dor principal

**Frentes do plano**:
As três áreas em que o plano de uma semana se divide, um card por frente (base B8).
_Evitar_: travas globais, pilares do plano, dores do plano

**Pilar do escopo**:
Um tema do escopo da semana como está escrito no contrato e no esqueleto; aparece na faixa `.amarra`.

**Plano por horizonte**:
O plano da tela "A trava e o plano" (Semanas 2 a 4), com as ações por frente em H1, H2 e H3.
_Evitar_: Mapa de Ações (nas Semanas 2 a 4)

**Mapa de Ações**:
A consolidação dos planos das Semanas 2 a 4, só na Semana 5, com dono e origem de cada ação.
_Evitar_: roadmap, plano 0-30/30-60

**Horizontes de Crescimento**:
Os três prazos do plano: H1 Fundação (0 a 30 dias), H2 Tração Controlada (30 a 180 dias), H3 Escala com Previsibilidade (6 a 12 meses).
_Evitar_: Horizontes McKinsey, blocos 0-30 e 30-60, fases (fase é do forecast)

**PSE**:
A lógica de argumento Pontos de Melhoria, Soluções e Estrutura Ideal (`metodo-pse.md`).
_Evitar_: Fechamento Universal, aulão

**Ponte**:
A primeira tela das Semanas 2 a 5, que liga o encontro anterior a este e abre com a trava.
_Evitar_: recap

**Gancho**:
O spoiler real da próxima semana, no fim do deck e na mensagem.
_Evitar_: teaser

**Mensagem pós-encontro**:
O texto curto enviado depois de cada encontro, com achado, validação, status dos entregáveis, insumos e gancho.
_Evitar_: follow-up (como nome da mensagem), resumo da reunião

## O cliente simulado (interno)

**Persona do cliente**:
A seção da ficha com o que o cliente disse ou fez, com a fonte; é tudo o que o cliente simulado sabe.
_Evitar_: perfil do cliente, avatar

**Ensaio**:
O teste do deck de um encontro das Semanas 2 a 5 com o cliente simulado, antes da reunião (`ensaio-cliente`). Só isso se chama ensaio.
_Evitar_: revisão e simulação (como nome do ensaio), ensaio (para o teste do pacote)

**Mesa com o cliente na cabeceira**:
A avaliação do plano entre a Semana 4 e a Semana 5: três cadeiras em paralelo e o cliente simulado fechando a ata (`mesa-cliente`).
_Evitar_: revisão única, mesa redonda, mesa ampliada

**Registro interno**:
O arquivo `_ensaios-internos/registro.md` do cliente, com as seções Medição e Ensaios e mesa.
_Evitar_: portão 9, nota de corte
