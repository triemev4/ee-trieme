# Base de todo encontro

Vale para as 5 semanas. Leia antes do esqueleto da semana. Quem lê o material é o dono do negócio, que não é de marketing: escreva para ele entender sem perguntar. Onde aparece "(o verificador confere)", o script acusa sozinho; o resto é com você, no B12. Comandos: no guia da etapa. Termos: `padrao/glossario.md`.

Esta base organiza os encontros e seus decks. Entregáveis de criação preservam contrato, evidência e revisão humana, mas seguem o formato do próprio guia. A LP usa `skills/landing-page/`, a marca do cliente e a linguagem do comprador, sem transportar moldes, teto de telas ou PSE visível para a página.

## B0 · Insumos primeiro, pela data
- Antes de escrever, liste `0. Inputs e Transcrições/` por data e leia o que chegou desde a última entrega.
- PDF, planilha e DOCX se leem pelo `_texto/` (o guia traz o comando de extração); cada trecho diz o arquivo e a página. Número lido por OCR (trecho marcado `OCR`) entra na ficha como não decisivo até o consultor conferir a página.
- **Comparabilidade antes da contradição.** Confira entidade/objeto e contexto das duas fontes; quando aplicáveis, métrica, unidade e período. Lista parcial não define o universo inteiro; papéis citados separadamente não provam pessoas adicionais. Se o vínculo não está demonstrado, preserve valores e origens como contextos não conciliados e registre o que verificar. Diferença literal pode ser registrada; contradição exige incompatibilidade em base comparável.
- Fontes que divergem viram pergunta ao cliente e linha em Pendências, com dono e data. Até a resposta vale, nesta ordem: contrato e documentos oficiais, a fala do cliente nas reuniões, o handoff da venda.
- Valuation, rodada e participação societária ficam fora da tela.

## B1 · Nada de presumir
Fatos do cliente vêm dos insumos e reuniões; ausência permanece ausência. Cenários e propostas seguem **Fato, cenário e proposta** de `padrao/estilo-de-escrita.md`: premissa da consultoria marcada, justificada e testável, sem inventar fato ou aceite.

## B2 · Número com dono, unidade e fonte
- **Ficha primeiro.** Todo número nasce em Números-fonte (id, valor, unidade, período, dono, fonte, data), e o deck copia de lá. Valor que muda vira linha nova; a antiga fica "substituído". (o verificador compara deck e ficha)
- **Conta pelo `calcular.py`.** Soma, percentual, TAM, SAM, SOM, forecast, funil, conversão e projeção: o script calcula e grava valor, fórmula e origem. O texto copia o valor no formato que ele devolve. O pesquisador traz as parcelas com fonte; a conta é do script.
- **Fonte web com trecho.** Número de página da web vale só com o trecho achado nela (`coletar_fontes.py --procurar`); sem o trecho, o `calcular.py` recusa.
- **Fonte na tela.** Toda tela com dado tem `.fonte-rodape`: rótulo do dado, fonte, ano e link. Nos moldes, o link se escreve `[texto](https://...)`. No fim, o `checar_fontes.py` abre cada link: link que não abre vira fonte oficial equivalente, e número que a fonte não traz sai.
- O que é do cliente cita a reunião ou o documento. Estimativa V4 mostra a conta. Print de evidência é um recorte legível, com o link de origem.
- Números decisivos (trava, SOM, forecast, Mapa de Ações) ficam "decisivo = sim" na ficha e são conferidos um a um.
- Cada semana cita a anterior: número do cliente sai de Números-fonte; número de mercado, da Semana 2.
- Fontes por setor: `base/<setor>/fontes.md`. Fonte pública nova é proposta ao curador no fim da Semana 2.

## B3 · Amarrado ao cliente (Semanas 2 a 5)
- Toda tela de conteúdo tem a faixa `.amarra` logo abaixo do título: **Pilar do escopo** (o nome do escopo da semana) · **Dor que trata** (a fala do cliente entre aspas, com a reunião) · **Para [cliente]** (o que a tela significa para ele, com nomes próprios).
- Concorrente sempre pelo nome. Célula sem fonte: "não informado"; critério que não cabe: "não se aplica".

## B4 · O esqueleto é o teto
- A sequência do esqueleto dá a ordem e o máximo de telas, cada uma com o nome fixo. Tela "(opcional)" entra quando o caso pede. Tela nova entra só no lugar de outra, dizendo qual sai. (o verificador confere)
- Todo pilar permanece coberto. Cada lacuna aparece uma vez na apresentação; tópico sem achado próprio fica no DOCX, com fonte, limite e verificação. Na S2 use `so_docx: true`; nos moldes S3–S5, `opcionais.tela-NN: false` e conteúdo no detalhe. Preserve ponte, capa e fechamento/plano.
- Condense na escrita ou na revisão única, registrando destino no JSON/índice do detalhe. O ensaio pode sugerir condensação; aprovação e envio continuam com o consultor.

## B5 · Uma ideia por tela, para quem não é de marketing
- Uma ideia por tela: no máximo um número grande e uma leitura; uma pergunta "Anotando" por tópico.
- **Teste do leigo:** o dono do negócio entende a tela sem perguntar? Use a palavra dele e a do mercado ("diferencial", "como os concorrentes se posicionam") no lugar do jargão interno.
- Escreva já curto: frase de até 20 palavras, até 3 itens por bloco. Por tela, até 350 palavras na Semana 2 e até 400 nas Semanas 3 a 5. (o verificador avisa acima disso) O resto vai para o DOCX.
- Termo técnico ou sigla (funil, Pixel, GA4, PUV, H1) ganha, na primeira vez, uma frase em palavras do cliente (`.explicador`, sem autor; o autor vai para o DOCX). Tela que ensina ferramenta fica fora.
- Na tela, só o nome que o cliente reconhece: IDs internos (por exemplo, `P-M1`, `S-MK2`, `E-C3`, `N18`, `D07`) e apelidos de trabalho ficam na ficha. Um rótulo legível de estado (`a validar`, `indicativo`, `hipótese de trabalho`) pode aparecer quando ajuda o cliente a entender o limite da conclusão. (o verificador confere IDs)
- A apresentação é uma sequência contínua de telas; o detalhe vai para o DOCX (como gerar: guia da etapa).

## B6 · Títulos que se explicam
- O título nomeia o assunto e apresenta o achado ou a pergunta quando a evidência permite. Clareza é o objetivo; não exija uma frase conclusiva em todo título.
- Quando a incerteza muda a decisão, sinalize o estado com "a validar", "ordem de grandeza", "fora do plano" ou "indicativo" no título, no eyebrow ou junto ao dado, e explique a razão no texto. Use só o rótulo que descreve o limite real.
- A tela mostra o que o cliente tem. O que falta medir vai para o plano ou para a pendência da mensagem.
- Quando uma resposta pendente pode mudar a recomendação, registre a pergunta e sua fonte, o que muda com cada resposta pertinente e a verificação seguinte. A quantidade acompanha as decisões reais; não crie perguntas para preencher um formato. Use `.pausa` para validar a leitura com o cliente.
- "O que vamos ver hoje", na ponte, é a pauta real, na ordem das telas.
- Antes de escrever, leia as objeções e ressalvas da Persona do cliente na ficha. Cada objeção que a semana toca ganha resposta numa tela. Pedido que esbarra numa ressalva diz como a respeita (ex.: com NDA pendente, a verba pede só um teto mensal).

## B7 · A trava e a restrição principal
- Semanas 2 a 4: uma trava do encontro, a partir da Meta e da Restrição vigentes na ficha. A ponte abre com ela e "Próximos passos" fecha com a hipótese e a ação pertinente. Diferencie sintoma, trava local e restrição sistêmica; não imponha o mesmo nome quando evidência nova mudar a leitura. Como montar: `padrao/metodo-pse.md`.
- S4 aplica o teste do dobro e explicita a corda (capacidade ou limite a medir). Sim, não e inconclusivo são respostas legítimas. Compare a hipótese com a melhor alternativa, incluindo evidência contrária e teste que muda a decisão.
- S5 consolida a restrição sustentada ou uma hipótese de trabalho proporcional à evidência, com decisão provisória e teste decisivo. A passagem de semana não confirma causa. O fundamento causal fica no detalhe; a decisão e seus limites aparecem na apresentação. Registre mudanças no Fio e reveja no marco ou antes, se capacidade, fila ou evidência mudar.
- O assistente propõe a trava e a restrição com a evidência; o consultor decide.

## B8 · Próximos passos e Mapa de Ações
- Semanas 2 a 4: "Próximos passos" traz a trava, de uma a cinco ações com dono e prazo, uma única prioridade na primeira posição, pausa e gancho. Dados pedidos ao cliente também têm dono e prazo. Na S2, programe o cliente oculto com protocolo, cliente e dois concorrentes para chegar à S4 com validade conhecida. Horizontes e desdobramentos ficam no fundamento; o plano integrado é o PED.
- Cada ação preserva verbo, objeto, conclusão e condição de liberação. No Mapa S5, no máximo três frentes H1 ativas no total, sem mínimo para preencher espaço. Identifique primeira ação e condição/data de revisão; demais desdobramentos vão ao detalhe.
- **Condições e ordem de execução.** Antes de fechar ou corrigir o plano, percorra todos os horizontes e o detalhe do DOCX:
  1. Localize a **primeira execução** dependente, inclusive teste ou entrega inicial; verificar só antes da expansão é tarde.
  2. Ponha verificação e critério de liberação antes dela, por data ou precedência escrita, mesmo dentro do mesmo horizonte.
  3. Repita a condição junto da ação dependente no HTML e no DOCX; cumprir uma não libera as demais. Condição desconhecida mantém execução bloqueada.
  4. Conversa exploratória sem compromisso pode anteceder condições exclusivas da entrega; compromisso de entrega exige essas condições.
- Um responsável por ação: cargo informado ou função proposta pela consultoria, sempre marcado **confirmado** (com fonte do aceite) ou **proposto**. Função proposta não prova pessoa disponível; indique quem deve aceitá-la na liberação. Critério A/B/C sai como proposta justificada para decidir, nunca campo em branco.
- A data decide o horizonte. Um único "Comece aqui"; o cliente valida a proposta sem receber tarefa de preenchimento.
- O Mapa da Semana 5 seleciona execução dos planos anteriores e do insumo novo rastreado; conserva os desdobramentos no detalhe (`padrao/metodo-pse.md`).

## B9 · Fechamento e rotina pós-encontro
- Semanas 2 a 4: "Próximos passos" termina num `.pausa` (uma pergunta que junta validação e viabilidade) e num `.gancho` com o spoiler real da semana seguinte. S4 também traz teste do dobro e corda. S5: "Fechamento" com tese específica, próxima restrição/condição de revisão, primeira semana pertinente e "Comece aqui", `.pausa` e `.gancho`. Kickoff: recap, hipótese, validação e gancho.
- O fechamento tem só isso e retoma só o que as telas mostraram.
- Depois do encontro, a rotina de registro é a de `rotina-pos-encontro.md`, nesta pasta. Leia-a só nessa hora.

## B10 · Premissas do projeto
- Um consultor só. Entregáveis: só os itens de Contrato na ficha; o que não está lá entra por contrato ou aditivo, escrito na matriz.
- Os 5 nomes, nesta ordem: Kickoff · Pesquisa de Mercado · Diagnóstico de Marketing · Diagnóstico Comercial · Planejamento Estratégico + Entregáveis. O cronograma mostrado ao cliente usa os 5, com "estamos aqui" na semana atual.
- Ferramentas que o cliente já usa podem ser nomeadas como fatos, com fonte. A recomendação define a capacidade necessária; opções de fornecedores e preços ficam separadas do diagnóstico e levam fonte, data e condição. Não apague ferramenta existente para manter uma recomendação genérica.
- Fora do padrão: Jobs-to-be-Done; SWOT e Pitch no Kickoff. Marketing baseado em contas (ABM) é uma frente possível, não uma exceção: registre-a como modo `conta` ou `combinado` e justifique por mercado B2B, qualidade/valor dos compradores, contas identificáveis e acessíveis, economia da abordagem e capacidade de atendimento. Demanda por busca e ABM podem coexistir quando têm papéis distintos.
- `referencias/layout/` é só referência de layout; conteúdo e sequência vêm do cliente e do esqueleto.
- Calendário: o combinado com o cliente. Data final do contrato antes do último encontro: a diferença é formalizada por escrito antes da Semana 2, com os entregáveis e o critério de aceite de cada um. Os 5 encontros continuam 5.
- Pós-venda e implantação são uma tela da Semana 4; reunião de processos só por aditivo.
- Vai ao cliente: HTML da pauta e Registro do Kickoff; HTML e DOCX das Semanas 2 a 5; os entregáveis da matriz; o Planejamento do Executar, quando houver. Fica interno: ficha, nota de preparo, ensaios, análise bruta, DOCX do deck do Kickoff, Documento de Handoff.
- O porquê de cada premissa: `docs/decisoes/`.

## B11 · Mercado
- Um nível de mercado por vez, o que os insumos sustentam. O outro nível aparece só como fato da situação do cliente, nunca alternado na mesma frase.
- Cada mercado que o cliente declara tem bloco próprio na S2; grupos e camadas seguem os compradores reais, sem cardinalidade fixa. A prioridade entre eles é decidida em "Onde concentrar", com fundamento no ICP, compra, economia e capacidade. TAM/SAM/SOM continuam três dimensões distintas, sem confundir com a quantidade de segmentos.
- O SOM distingue tração observada, cenário condicional e previsão, com premissas, período e limites. A meta é referência de comparação, não parcela da conta. Sem base para estimar, declare a lacuna e a verificação necessária; o rótulo de hipótese não autoriza um número sem premissas.
- A decisão por contas considera acesso às contas, ciclo de compra, concorrência e capacidade, além do tamanho da meta. Querer poucos clientes grandes, sozinho, não justifica ABM.

## B12 · Antes de entregar
Depois da última correção, execute `preparar_entrega.py --modo final` pelo guia da etapa: validação, geração, extração atual, conferências e manifesto da mesma revisão. Durante o preparo use `--modo rascunho`; o gatilho reconhece a conferência básica pelos hashes e só a executa quando necessário. Erro ou conferência obrigatória não realizada impede conclusão técnica. Aviso exige leitura. Aprovação do consultor é uma decisão separada. O DOCX e `telas.md` correspondem ao HTML final.

O que os scripts não julgam, você confere:
- [ ] B0: insumos lidos por data; comparabilidade conferida antes de alegar contradição; contextos não conciliados e divergências viraram pergunta e pendência
- [ ] B1: inferências decisivas com evidências, premissa e condição de revisão; estimativas com premissas pertinentes
- [ ] B5: teste do leigo em cada tela; detalhe no DOCX
- [ ] B6: títulos que se explicam; pauta igual à sequência; objeções da Persona respondidas
- [ ] B7 e B8: trava e plano (Semanas 2 a 4); restrição e Mapa de Ações (Semana 5); checagem de Condições e ordem de execução aplicada ao plano final nos dois formatos
- [ ] B9: fechamento com validação e gancho; mensagem pronta
- [ ] B13: nenhuma análise emitida com dado "Bloqueia" em aberto
- [ ] Passada final por `padrao/estilo-de-escrita.md`

**Pronto e enviado.** "Pronto" só com o arquivo na pasta, o link que abre e a data. "Enviado" só com a data do envio registrada em Contrato, na ficha. Sem os três, diga o que falta.

## B13 · Dados faltantes
Cada dado mínimo do Kickoff tem uma classe em Dados mínimos da ficha (exemplos de cada classe: esqueleto do Kickoff).
- **Bloqueia:** a análise que depende dele espera. A semana segue com as demais análises e a pergunta pertinente. Sem acesso a conta existente, não emita auditoria observada dessa conta; ainda pode propor estratégia e teste identificados como proposta, sustentados por fontes pertinentes. Nunca anunciou/sem conta não é acesso negado e não anula referência de custo válida.
- **Limita:** declare na tela qual conclusão os dados não permitem emitir. Se isso afetar a leitura, marque "indicativo", "sem histórico" ou "a validar" no título, eyebrow ou dado; a ficha guarda a ressalva. Evidência suficiente ainda pode sustentar uma recomendação provisória, com condição de revisão. Sem verba, o forecast segue as condições do esqueleto S3 e nunca bloqueia; sem base numérica, apresente o teste, o limite disponível e a verificação, sem inventar retorno.
- **Não se aplica:** o dado não existe nesse formato e sai do denominador, com o motivo.

## Horizontes de Crescimento
| Horizonte | Prazo | Nome |
|---|---|---|
| H1 | 0 a 30 dias | Fundação |
| H2 | 30 a 180 dias | Tração Controlada |
| H3 | 6 a 12 meses | Escala com Previsibilidade |

A Semana 4 confirma estes prazos; eles mudam só com dado do cliente registrado na ficha. As fases do forecast ficam no esqueleto da Semana 3.

## Onde cada semana aplica a base
Kickoff: B0, B1, B2 (quando há dado), B4, B5, B6, B9 (fechamento do Kickoff) e B10 a B13; B3, B7 e B8 começam na Semana 2. Semanas 2 a 4: todas. Semana 5: todas, com a restrição principal no B7 e o Mapa de Ações no B8.
