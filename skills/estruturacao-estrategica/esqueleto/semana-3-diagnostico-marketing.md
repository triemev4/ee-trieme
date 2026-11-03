# Esqueleto · Semana 3 · Diagnóstico de Marketing

Base: `../base-de-todo-encontro.md` (B0 a B13) vale antes deste esqueleto.

**Pergunta do encontro:** os canais atraem, convertem e medem? Onde investir primeiro, quanto e em que ordem?
**Papel na EE:** partir do objetivo e da base vigente, escolher a aquisição por público, auditar os ativos e definir um teste e investimento fundamentados. Cada frente fecha o próprio ciclo PSE.
**Guia da etapa:** `skills/diagnostico-marketing/SKILL.md` (passos e comandos). **Layout e CSS:** `moldes/semana-3.html`, preenchido por `scripts/preencher_molde.py`.

## Insumos

1. A Semana 2: TAM/SAM/SOM, ICP, PUV, citados como estão.
2. A ficha (Fio do projeto vigente e histórico, Direcionamento e frentes, Decisões, meta, verba, Números-fonte e Glossário), o Registro do Kickoff e as transcrições, das mais recentes às mais antigas: próximo passo do cliente, oferta de entrada, histórico de anúncios, quem cuida das contas.
3. A auditoria feita antes da reunião: site (velocidade, SEO, LIFT), Google Meu Negócio (8 dimensões), Instagram e, só para concorrente nomeado pelo cliente e achado com página oficial na Semana 2, a Biblioteca de Anúncios da Meta.
4. Os acessos testados e a exportação de 90 dias das contas de anúncio, quando houver. Acesso pendente bloqueia a auditoria da conta existente, sem cancelar a estratégia e o teste fundamentados. Nunca anunciou/sem conta é estado próprio; referência de custo pertinente pode sustentar cenário rotulado. Sem exportação, custo observado fica ausente; referência não vira histórico. Sem verba confirmada, trate limite e teste conforme B13, sem inventar retorno.

## Sequência de telas (14)

| # | Tela | Função | Componente | Regra de conteúdo |
|---|---|---|---|---|
| 1 | Ponte entre encontros | Retomar | `.bridge-track` + 2 colunas + `.pausa` | Recap vigente da S2, trava e pauta real, na ordem das frentes apresentadas |
| 2 | Capa | Abrir | hero + `.v4-mark` | Fatos e estado conhecidos |
| 3 | Ponto de partida | Situar | `.grid` + `.cell` + estado | Meta, unidade, período e base comparáveis; sem dado, declarar a lacuna e a condição para medir |
| 4 | Rastreamento | P → S → E | PSE + diagrama site → GTM → destinos | Primeira frente operacional: eventos e origem rastreáveis até o resultado pertinente |
| 5 | Estratégia de aquisição | Escolher | `.rtable.estrategia-aquisicao` | Modo do marketing e frentes por público, função, abordagem, evento, destino e limite |
| 6 | Meta Ads | P → S → E | PSE + draw flow de campanhas | Público, objetivo, verba e destino coerentes com a estratégia; apresentar quando pertinente |
| 7 | Google Ads | P → S → E | PSE + draw flow | Busca por intenção com as palavras do negócio e resultado verificável |
| 8 | O que o comprador vê | P → S → E | `.rtable.ativos-comprador` + perfil local e evidência | Auditar ativos pertinentes com estado, evidência e implicação; Google Meu Negócio mantém suas oito dimensões quando pertinente |
| 9 | Site e CRO | P → S → E | `.browser-mock` atual × ideal + LIFT | Velocidade, SEO, mensagem, prova e próximo passo; até três dimensões com achado na tela |
| 10 | Instagram e calendário | P → S → E | `.ig-mock` atual × ideal + calendário | Bio, destaques e cadência que a equipe consegue executar |
| 11 | Criativos | P → S | `.ad-mock` | Concorrentes identificados; sem evidência, ângulos propostos e rotulados como proposta |
| 12 | Forecast | Decidir teste e recurso | rosca + legenda + fases + cenários pertinentes | Depois da estratégia; distinguir referência de custo, histórico, verba, cenário e resultado |
| 13 | Primeiras ações | Preparar execução | `.rtable` | Ações ligadas aos achados, com dono proposto, recurso e condição; esforço interno não implica custo zero |
| 14 | Próximos passos | Fechar | `.ac` + `.own` + `.pausa` + `.gancho` | Uma a cinco ações, um único Comece aqui na primeira posição, dono e prazo explícitos; sem trilhas de horizonte no fecho |

## Regras da sequência

- **Cada frente mantém PSE:** dado e implicação, solução, estrutura ideal. Sem achado próprio, condense pelo B4 e cubra o pilar no detalhe; cada lacuna aparece uma vez. Ação e liberação seguem B8.
- **Frentes que ficam:** as que o cliente usa ou ainda considera. Canal que ele decidiu não usar sai, e a ponte lista só as que ficam. Sem presença digital: `modulacao.md`.
- **Visual por nome**, nas frentes apresentadas: rosca do investimento (12), draw flow das campanhas (6 e 7), atual × ideal do site (9) e do Instagram (10). Nas outras, o componente da tabela basta.
- **Prints reais ou mockup realista.** Print real substitui o mockup. No mockup, menu, categorias, contagem de posts e seguidores são os do cliente, iguais nos dois lados, e todo número vem do cliente. O perfil otimizado do Google e o `.ad-mock` mostram copy do nicho, rotulados como proposta.
- **LIFT.** No detalhe, as 6 dimensões (proposta de valor, relevância, clareza, ansiedade, distração, urgência), com autor e método. Na tela, o `.explicador` cita os 6 nomes numa frase, sem autor, e a análise fica nas dimensões que têm achado, até 3, com até 3 ações. Dimensão forte vira card positivo. A proposta de valor confere se a PUV da Semana 2 aparece no topo do site e no Instagram; o diferencial que existe e não aparece vira Ponto de Melhoria. Benchmark de CRO de concorrente entra quando foi levantado.
- **Siglas da semana** (CRO, LIFT, GA4, GTM, CRM): tradução no eyebrow, a sigla depois.
- **A Semana 2 é citada como está**, sem recalcular nem repetir.

## Forecast (regra única, só aqui)

1. **Base da decisão:** leia Direcionamento, frentes e Decisões vigentes da ficha. Em cada frente, separe referência de custo com fonte/setor/ano, histórico próprio, verba disponível, cenário e resultado. Histórico ausente não apaga uma referência pertinente.
2. **Cenários pertinentes:** use somente os que têm base. Cada cenário distingue faixa de investimento, divisão por canal, resultado defensável e condição de avanço. A lista não exige três cenários nem taxas inventadas para preencher cards.
3. **Sem base para retorno numérico:** mostre teste, verba disponível ou a confirmar, resultado que será medido, janela e condição de avanço. A rosca representa a composição de verba conhecida ou hipótese identificada; não converte hipótese em retorno.
4. **Fases:** comece pela validação de eventos, destino e resultado final. O marco de leitura é proposto conforme ciclo e maturação do negócio. Repartir ou aumentar verba exige resultado comparável e capacidade; calendário sozinho não libera escala. A S5 preserva a origem, estado e unidade desses números na conta da receita e nos recursos do Mapa.
5. **Sem verba declarada:** registre a pergunta e limite a proposta à base disponível. Hipótese sustentada recebe rótulo e fundamento. Se faltar base até para a hipótese, mantenha a lacuna com responsável e teste; a ausência não bloqueia a entrega analítica.
6. **Resultado e destino dos canais:** relacione público, função, destino e resultado verificável antes de distribuir verba. Compare resultado e qualificação equivalentes, período e maturação compatíveis, com origem e desfecho rastreáveis. Clique, contato, oportunidade e compra são etapas distintas. Demanda encaminhada a parceiro não equivale a venda direta. Sem base comparável, proponha teste delimitado e respeite verba e capacidade conhecidas; contato mais barato sozinho não libera transferência.

**Estratégia por frente:** volume, conta, combinado ou a verificar vêm do Direcionamento. A abordagem por contas exige fundamento B2B, contas pertinentes, qualidade e economia. Busca e ABM podem coexistir quando cada frente tem função e conversão claras. Posicionamento sustentado precede a Landing Page; o Manual de Copy, quando contratado, formaliza esse fundamento.

## Modulação

- **Formato:** peso e foco de cada frente em `padrao/formatos-de-negocio.md` (Semana 3).
- **Maturidade:** baixa pede estrutura mínima e mídia nova só depois do rastreamento e da fundação. Alta pede governança, leitura de fadiga, otimização fina e margem por canal.
- **Perfil do decisor:** o Executor pede prazo e dono cedo; o Analítico, as premissas do forecast.

## Próximos passos

No slot `tela-14`, use `{titulo, trava, acoes: [{acao, dono, prazo, comece_aqui}], pausa, gancho}`. A lista tem de uma a cinco ações; uma única `comece_aqui: true`, na primeira posição. Dono proposto continua proposto até aceite; prazo explicita data ou condição. `.ac` recebe `data-classe="prio:.comece_aqui"`; `.own` reúne dono e prazo. O fecho não repete o Mapa por horizonte. Desdobramentos e condições detalhadas ficam no DOCX.

## Pronto quando

Checklist B12, mais:
- Cada frente tem seu ciclo de diagnóstico e proposta; o LIFT mantém as seis dimensões no detalhe.
- O modo e as frentes sustentam os canais escolhidos; o forecast vem depois, com cenários somente onde há base.
- Ausência de meta, histórico, verba ou referência aparece com seu estado e próximo teste, sem projeção fabricada.
- As primeiras ações têm recurso e condição; Próximos passos fecha com uma prioridade, dono, prazo, validação e gancho, dentro de 1h30.

## Concorrentes e teste de leitura

Siga `skills/pesquisa-mercado/concorrentes.md` para identidade, pertinência, página e limites. Na Biblioteca, somente concorrente nomeado pelo cliente e identificado; a exceção continua desativada. Registre pergunta, origem, decisão, data e filtros.

No piloto, experimentar 120 a 200 palavras na explicação principal de Site/CRO e Instagram, preservando pontos de melhoria, soluções, estrutura ideal, mockup e ação. Verificar compreensão, altura e legibilidade no HTML; a faixa não é teto universal das demais telas.
