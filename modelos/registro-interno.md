# Registro interno · {{NOME}}

<!--
Registro interno do cliente: medição e ensaios com o cliente simulado. Uso interno, nunca vai ao cliente, nunca vai para a base de conhecimento.
Fica em `_ensaios-internos/registro.md`, fora da ficha, para a ficha ser lida sem este peso. A medição de uso grava aqui sozinha (scripts/medir_uso.py).
-->

## Medição

<!--
O que não foi medido fica "não medido", nunca estimado como fato. Estimativas de partida; o real substitui.
Partida (h): passagem da venda 1 · pré-Kickoff 3 · Kickoff reunião 1,5 e pós 1,5 · Semanas 2 a 4: preparo 6, reunião 1,5, pós 1 · criação 6 · ensaio 0,25 por encontro das Semanas 2 a 5 · mesa 0,5 · Semana 5: 5, 1,5 e 1 · encerramento 0,5 (Handoff 1,5). Total 48 h (49 h com Handoff).
-->

| Encontro | Preparo (h) | Reunião (h) | Pós (h) | Duração anunciada | Duração real | Nota do cliente (0 a 10) e comentário | Modelo e esforço | Versão do pacote |
|---|---|---|---|---|---|---|---|---|
| Kickoff (preparo = pré-Kickoff) | não medido | não medido | não medido | | | | | |
| Pesquisa de Mercado | não medido | não medido | não medido | | | | | |
| Diagnóstico de Marketing | não medido | não medido | não medido | | | | | |
| Diagnóstico Comercial | não medido | não medido | não medido | | | | | |
| Planejamento Estratégico + Entregáveis | não medido | não medido | não medido | | | | | |

| Atividade | Real (h) | Quem | Observação |
|---|---|---|---|
| Passagem da venda | não medido | | |
| Criação (uma linha por entregável) | não medido | | |
| Ensaio (uma linha por semana e rodada: ler e decidir) | não medido | | |
| Mesa com o cliente na cabeceira (ler e decidir) | não medido | | |
| Encerramento (ou Handoff) | não medido | | |
| Retrabalho (uma linha por refação, com o motivo) | | | |

Calibração do cliente simulado (preenchida na rotina pós-encontro; decisão depois de 3 clientes: `padrao/rubrica-cliente.md`):

| Encontro | Nota simulada (média dos 5, última rodada) | Nota real | Diferença | Objeções reais | Delas, previstas no ensaio | Previstas que apareceram |
|---|---|---|---|---|---|---|
| Pesquisa de Mercado | | | | | | |
| Diagnóstico de Marketing | | | | | | |
| Diagnóstico Comercial | | | | | | |
| Planejamento Estratégico + Entregáveis | | | | | | |

- Ajustes da mesa aplicados: __ de __ (quais e por que os demais ficaram de fora)

Uso do plano, uma linha por sessão de trabalho (o `/cost` entra só como volume, marcado "estimativa"):

| Data | Cliente e etapa | Modelo e esforço | Bateu o limite (sim ou não, hora) | Espera até liberar | Claude fora da EE no intervalo |
|---|---|---|---|---|---|
| | | | | | |

<!-- uso-medido: linhas gravadas pelo gatilho de fim de tarefa (scripts/medir_uso.py); não edite -->
Uso medido por sessão (gravado sozinho no fim de cada tarefa; duração total inclui pausas, ativa descarta pausas de mais de 15 min; não edite as linhas):

| Sessão | Data | Etapa | Modelo | Entrada | Saída | Cache lido | Cache criado | Duração (min) | Ativa (min) | Ferramentas | Observação |
|---|---|---|---|---|---|---|---|---|---|---|---|

Conversão para o Executar (o gestor registra no dia 31 após a Semana 5; negociação em curso é "em aberto", nunca "não converteu"):

- EE concluída em: dd/mm · Dia 31: dd/mm · Contrato do Executar assinado até 30 dias depois: sim em dd/mm · não · em aberto · Registrado por: , em dd/mm

## Ensaios e mesa

<!-- Uso interno. Regras, critérios e quando o material está pronto: `padrao/rubrica-cliente.md`. -->

### Ensaios

<!-- Uma linha por rodada, gravada por quem chamou o ensaio. Uma rodada por encontro; a segunda só a pedido do consultor. As notas são medida, não portão. Na última coluna, o consultor decide cada ajuste e cada corte sugerido. -->

| Semana | Rodada | Data | Entendimento | Fala comigo | Confiança | Ação | Valor do tempo | Prova | Cortes sugeridos | Arquivo | Decisão do consultor |
|---|---|---|---|---|---|---|---|---|---|---|---|
| | | | | | | | | | | | |

Avaliador da Semana 2 (medida, sem portão): data · média · defeitos marcados · arquivo

### Mesa

<!-- Ata da cabeceira, até 30 linhas, como veio, gravada pelo guia da mesa. Abaixo, a decisão do consultor sobre cada ajuste e cada divergência. -->
