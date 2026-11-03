# Método PSE

Lógica de argumento das Semanas 2 a 5: Pontos de Melhoria (P), depois Soluções (S), depois Estrutura Ideal (E). O objetivo é amarrar a teoria a um plano prático que o cliente consiga tocar, sem deixá-lo só com a explicação do conceito. O Kickoff não usa PSE (ele é recap, hipótese e pergunta, base B9).

## O que é P, S e E

- **P, Ponto de Melhoria:** dado do cliente com implicação. O que foi observado e o que isso custa ou arrisca se nada mudar. Até cinco pertinentes por bloco, cada um com fonte (print, dado, estimativa com método), sem criar achados para ocupar vagas.
- **S, Solução:** recomendação ligada ao Ponto, em 5W1H curto (o quê, quem, quando, como, por quê). Dono e prazo ficam na própria ação. Alternativa e teste são explícitos quando a evidência ainda não permite decidir.
- **E, Estrutura Ideal:** como o tópico deve funcionar (campanhas, funil, fluxo, SLA, papéis), nunca em parágrafo corrido. Vira figura nas telas em que o esqueleto pede o visual pelo nome (`sistema-visual.md`, Gráficos); nas demais, é o componente que o esqueleto indica, sem obrigação de desenho.

## PSE por tópico

- Cada tópico de diagnóstico (rastreamento, funil, posicionamento etc.) carrega os três estágios, na ordem P, S, E, com a E do mesmo tópico.
- PSE permanece completo no material. Na apresentação, preserve o achado e a decisão; condense tópicos que repetem lacuna pelo B4, mantendo fonte e cobertura no detalhe. A E conserva o rótulo do tópico.
- Todo framework ou teoria (TAM/SAM/SOM, TOWS, Horizontes, LIFT) é seguido, no mesmo bloco ou no próximo, da ação concreta para aquele cliente.
- Pendência de dado fica abaixo do achado em peso visual (base B6).
- O material gerado por passos automáticos ganha o julgamento do consultor antes de ir para a tela: PSE sem leitura crítica sai superficial e o cliente rejeita.

## Perfil do decisor

A ênfase muda conforme o perfil, e o conteúdo da semana fica o mesmo. O perfil e a evidência vêm do Mapa de Pessoas (`mapa-de-pessoas.md`), e o perfil do decisor fica na ficha. Sem perfil com evidência, usar a combinação equilibrada.

## Validação antes do gancho

A pergunta de validação é decidida pelo perfil (Analítico, premissas; Comunicador, o que mais chamou atenção; Executor, se os passos estão claros; Planejador, se algum risco ficou de fora). Posição na tela: base B9.
- A resposta do cliente não é rebatida na hora. Concordância vai para o registro da semana; discordância ou ressalva vira pendência da semana seguinte, com fonte e tempo na gravação.
- A validação e o gancho seguem por escrito na mensagem pós-encontro (`mensagens-pos-encontro.md`).
- A ponte de abertura (Semanas 2 a 5) pergunta o que ficou do encontro anterior; se o cliente não lembra do gancho, o consultor retoma em uma frase.

## A tela "Próximos passos" (Semanas 2 a 4)

Última tela do deck. Título livre, curto e proporcional ao achado. Contrato único: `proximos_passos = {trava, acoes: [{acao,dono,prazo,comece_aqui}], pausa, gancho}`. Há de uma a cinco ações, exatamente uma `comece_aqui: true`, na primeira posição. HTML usa `.ac`, `.own`, `.ac.prio`, `.pausa` e `.gancho`.

1. **Trava:** leitura vigente, com fonte e estado. A restrição pode amadurecer; hipótese provisória mantém alternativa, limite e próximo teste.
2. **Ações:** verbo e objeto, dono proposto/confirmado, prazo e condição de liberação quando depender de algo. Pedido de dado ao cliente também é ação. Na S2, inicie o cliente oculto com protocolo, cliente e dois concorrentes.
3. **S4:** teste do dobro em `.dobro`, com resposta sim, não ou inconclusivo e evidência. `.corda` registra capacidade ou limite a medir e teste. Falta de dado não vira confirmação.
4. **Fim:** `.pausa` para validar leitura e viabilidade, depois `.gancho` real da semana seguinte. Trilhas H1/H2/H3 não se repetem no fecho intermediário: horizonte, derivações e PSE completo permanecem no fundamento/DOCX; o PED integra a execução.

- A ponte de abertura cita a mesma trava, e "O que vamos ver hoje" (B6) abre com ela. Prometa só o que o deck entrega.
- A data real de cada ação decide a trilha. Cada ação sai das Soluções que a semana publicou; ação sem diagnóstico que a sustente fica fora.
- Na Semana 2, o plano trata de meta, posicionamento e foco de clientes; mídia e CRM ficam para as semanas seguintes.
- O Mapa da S5 seleciona execução pelo B8: até três frentes H1, primeira data proposta, responsável proposto/confirmado e liberação. `.orig` aponta a semana ou insumo novo; desdobramentos ficam no detalhe.

## Memória e consulta

Registre P/S/E na seção Pontos, soluções e estrutura da ficha com IDs estáveis e ligações a evidência, restrição e decisão. Situação e substituição determinam o que comanda a execução; histórico preservado não mantém recomendação revogada ativa. Códigos são internos. O detalhe S2–S4 termina com Pontos, Soluções e Estrutura em linguagem autônoma, fontes e limites, sem copiar os IDs. O fundamento pode classificar a ação na TOC sem exigir uma etiqueta formal em cada card visível.

No detalhe S3–S5, a `section.abertura` abre com **Achados que mudam a decisão** (até cinco pertinentes, com referência à tela) e **Como ler** (dado, estimativa e premissa, com o que valida ou substitui cada premissa decisiva). Contexto, meta, decisões vigentes e limites dão autonomia à consulta. O conversor promove essa abertura para depois da capa; não a repita no restante do detalhe.
