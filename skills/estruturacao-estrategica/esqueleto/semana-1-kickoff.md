# Esqueleto · Semana 1 · Kickoff

Base: `../base-de-todo-encontro.md`. Valem B0, B1, B2 (quando há dado), B4, B5, B6, B9, B10, B11, B12 e B13. O Kickoff é campo em branco: não há amarração de dor (B3), trava (B7) nem plano (B8).

**Pergunta do encontro:** o que dói, o que já sabemos e o que falta saber para as próximas 4 semanas?
**Papel na EE:** coletar. O Kickoff não diagnostica nem planeja. Sai com os insumos de cada semana, os dados mínimos e o critério de sucesso nas palavras do cliente.
**Guia da etapa:** `skills/kick-off/SKILL.md` (comandos e gerador). **Layout:** `referencias/layout/kickoff.html`.

## Insumos e nota de preparo

Insumos, na ordem de precedência da B0: contrato assinado; fala do cliente na call de venda e na Growth Class, quando houver (havendo vídeo, transcrever: a fala literal é o material mais valioso); handoff do comercial; formulário de diagnóstico e materiais enviados pelo cliente. Compare meta, prazo, formato e cobrança entre venda e Growth Class. Preserve as fontes e prepare uma pergunta só para lacuna, mudança ou divergência.

A nota de preparo (interna) tem três seções:
- **O que sabemos:** Passo 0, o modelo de mercado, com a fonte de cada resposta (quem compra, como compra, unidade de venda e receita, canal que pesa, regulação, estágio, maturidade), fechando em **um** nível de mercado (B11) · triagem de formato primário, secundário e maturidade, só como hipótese · de 3 a 5 necessidades reais, cada uma com a fala que a sustenta · cruzamento insumo × fonte (Inputs, Deck, Conversa, Auditamos), com os insumos de cada semana tirados da seção Insumos do esqueleto dela (Semanas 2 a 5): insumo sem fonte vira pergunta, pergunta sem insumo sai · duplicatas e divergências entre fontes.
- **Pessoas:** Mapa de Pessoas com nome (`padrao/mapa-de-pessoas.md`). Decisor ausente: combinar a conversa de alinhamento antes da Semana 2.
- **Condução:** o radar de insumos marcável (os da semana mais os do formato) e um tema por momento, na ordem do roteiro, marcado `deck` ou `conversa`: antes de entrar, rapport, capa e roteiro, dores, mapeado, marketing, comercial, metas, concorrentes, fechamento, depois. Traz o que não perguntar e as promessas da venda a confirmar com o closer.

## Sequência de telas (11)

| # | Tela | Função | Componente | Regra de conteúdo |
|---|---|---|---|---|
| 1 | Capa | Abrir | hero + `.consultor-tag` + `.v4-mark` | Cliente, data, responsável. Foto e título do consultor só aqui |
| 2 | O que é o Kickoff | Situar | grade das 5 semanas | Cada semana na língua do cliente. A pergunta de foco de mercado e nível entra aqui, nos 10 primeiros minutos |
| 3 | Roteiro da reunião | Dar o mapa | `.agenda-solo` | 7 blocos sem tag de papel, total 1h30 (15 · 5 · 10 · 20 · 15 · 10 · 15 min). Cada bloco abre com uma pergunta e fecha com o que foi ouvido |
| 4 | 01 · Problemas reais e dores | Escutar | 4 `.quad` | "Qual é a sua dor hoje?" Quadros: o que trava · o que já foi tentado · o que não aparece · **o que precisa mudar** (critério de sucesso). Sem resposta pré-escrita. Fecha devolvendo cada dor ao encontro certo |
| 5 | 02 · O que já mapeamos | Mostrar contexto | `.field-card` | Fatos ditos na venda e na Growth Class, quando houver, 1 a 2 linhas, com a fonte na nota. Ausência vira pergunta, nunca fato. Não repetir no Kickoff o que já foi respondido; convide o cliente a corrigir ou atualizar. Tom "você só complementa" |
| 6 | 03 · Perguntas de marketing | Coletar S3 | 4 `.quad` com "Para:" | Quadros pelas frentes da S3: anúncios e rastreamento · site, Google e Instagram · criativos e landing page · mensagem e autoridade. **Próximo passo e oferta de entrada obrigatórios**; se a resposta for "depende", insistir até sair uma ação e uma oferta. Setor regulado: perguntar o que pode ser divulgado |
| 7 | 04 · Perguntas comerciais | Coletar S4 | 4 a 5 `.quad` | Quadros do formato (trocam, não somam). Inside Sales: como a venda acontece · objeções e qualificação · contatos e acompanhamento · receita e entrega · pós-venda. Híbrido: formato primário mais 1 pergunta do secundário |
| 8 | 05 · Metas financeiras | Coletar S2, S3 e S5 | 4 `.quad` | Hoje · 12 meses (inclua: "Você prefere mais clientes ou menos clientes, maiores?") · Investimento (histórico, verba mínima/máxima ou "sem teto", quem toca, dependência do dono) · Prazo (retorno, evento crítico em 90 dias, sazonalidade) |
| 9 | 06 · Concorrentes, público e design | Coletar S2 | `.quad` + `.live-fill` | Concorrentes com o argumento deles e a resposta. Público **em branco**, sem persona. Marca e domínio. Formato de entrega preferido |
| 10 | Fechamento | Recapitular | `.lede` + `.pausa` + `.gancho` | Só fatos confirmados + trava como **hipótese** + pergunta de validação + spoiler da S2. Ressalva do cliente não se rebate: vira ponto a aprofundar. Sem `.fecho`, sem argumento de valor |
| 11 | Próximos passos | Mostrar o caminho | `.flowchain` | 5 semanas com os nomes oficiais, "estamos aqui" na S1. Rodapé com o contato do consultor e o convite para a Semana 2 |

Cada bloco de perguntas fecha com um `.gancho` que diz qual semana usa as respostas. O texto visível soa natural ("Estamos ao vivo", "Anotando"), sem instrução de bastidor.

## Regras das perguntas

- De 20 a 28 nos quadros (a pergunta de foco conta), 1 ou 2 por quadro, abertas e de conversa; cada uma cobre vários insumos. Acima de 25, cada pergunta tem insumo e semana declarados no cruzamento.
- Cada pergunta contrasta com um card de "O que já mapeamos" ou cobre uma lacuna. A que se responde lendo o slide anterior sai. Card relevante cujo uso, atualização ou responsável ainda não se sabe vira pergunta, dentro do teto.
- Pergunte só o que o cliente sabe: site, SEO, Google Meu Negócio, redes e anúncios de concorrentes a equipe audita.
- Em investimento, pergunte se já investiu em mídia, quanto investiu e qual verba mínima/máxima cabe agora. "Nunca investiu" e "sem teto" são respostas textuais válidas; registre-as em Dados mínimos e Números-fonte sem converter em zero ou inventar um valor. Não force teto se ainda não existe.
- Registre a preferência por volume ou qualidade nas palavras do cliente; ela orienta o modo inicial de marketing, que segue hipótese até haver evidência.
- Termo só do que está nos insumos (B1). Instituições pelo nome completo; sigla de método com tradução entre parênteses na primeira ocorrência da tela. Termos nossos entram no `glossario` do bloco ("Termos desta tela"); termo do mercado do cliente vai para o Glossário da ficha.
- Pergunte pelo que existe e pela visão do cliente, dentro do que a EE faz. Episódio específico do cliente vira rapport. Promessa da venda só vira pergunta depois de confirmada com o closer.

## Portão de saída: dados mínimos

Classes na B13. Cada dado sai da sala com resposta ou com pendência com dono e data, registrado na seção Dados mínimos da ficha. % confirmado = confirmados ÷ aplicáveis; % com pendência = pendentes com dono e data ÷ aplicáveis; os dois somam 100%. Registre no fim do Kickoff e atualize quando a pendência fecha.

| Dado mínimo (comuns aos 3 formatos) | Classe | O que trava ou limita |
|---|---|---|
| Foco de mercado e um nível | Bloqueia | Semana 2 |
| Meta de 12 meses em número (R$ ou contratos) ou carteira com estágio | Bloqueia | SOM; basta um dos dois |
| Preço e unidade de venda | Bloqueia | SOM em R$ |
| Verba mínima e máxima de mídia | Limita | Forecast em hipótese marcada, se faltar |
| Acessos às contas, por convite, testados antes da Semana 2 | Bloqueia | Frente de mídia da Semana 3 |
| Receita dos últimos 12 meses, ou "sem histórico" | Limita | SOM só por capacidade |
| Conversão observada (reunião para fechamento) e carteira ou funil com estágio, ou "não medida" | Limita | Funil sem taxa |
| Ciclo e orçamento de quem compra | Limita | Sazonalidade e prioridade de mercado |
| Quem decide e influencia; equipe e papéis | Limita | Dono de cada ação |
| Dependência do dono; evento crítico em 90 dias ("sem evento crítico declarado" vale) | Limita | Ordem do H1 |
| Exportação de 90 dias das contas de anúncio | Limita | Sem custo por resultado |

Dados por formato: ficha, Dados mínimos; todos Limita. Dado que não existe no formato é "Não se aplica", com o motivo.

## Condução que protege o portão

- Tempo anunciado igual ao real: o roteiro soma 1h30 e é o que se diz ao cliente.
- Pergunta de foco de mercado e nível nos 10 primeiros minutos.
- Relógio aos 60 minutos: decidir o bloco a cortar. Corte primeiro concorrentes, público e design; um dado "Bloqueia" fica sempre.
- Os 15 minutos finais são do fechamento: recap em 3 linhas, critério de sucesso lido de volta, pendências com dono e data, nota do cliente (0 a 10 e um comentário).
- Pedido de insumos da Semana 2 feito na sala, com data de corte: arquivos do formato, 90 dias de mídia e acessos por convite (`padrao/formatos-de-negocio.md`). Histórico de anúncios, rastreamento e base de contatos que já existem: seção 3.3 do mesmo arquivo.
- Radar conferido antes de pular qualquer bloco, porque a conversa não segue a ordem dos slides. Semana 2 agendada antes de encerrar.
- Mudança estratégica proposta pelo cliente vira hipótese da Semana 2. Promessa da venda não confirmada: "vou confirmar e te retorno".

## Artefatos

- **Antes:** deck HTML (gerador) e nota de preparo.
- **Depois:** Registro do Kickoff em DOCX; ficha atualizada; mensagem pós-Kickoff pedindo o "de acordo" do critério de sucesso. Na ficha: Contrato (promessas da venda confirmadas) · Dados mínimos (valor, fonte e tempo da gravação, ou "pendente · dono · data", com % confirmado e % com pendência) · Números-fonte novos, com id e decisivo · Meta, condições e efeitos indesejados · primeira linha de Meta ao longo · Direcionamento e modo inicial como hipótese · Restrição como hipótese · Decisões por encontro com autoria separada · Glossário com as grafias da transcrição · Status e Pendências. Mapa de Pessoas e triagem confirmados na nota. A matriz Contrato continua sendo a fonte única do que será entregue: mostre apenas os itens contratados e não prometa peça extra pela descrição do cronograma.
- **Meta, condições e efeitos indesejados:** meta principal nas palavras do cliente (sem número: "não declarada" e a pergunta da Semana 2, nunca estimar) · de 6 a 8 condições necessárias · de 8 a 10 efeitos indesejados, no presente. Cada item com fonte e a semana que o trata; leitura da Trieme marcada como tal. Alimenta a restrição principal da Semana 5.
- **O cliente recebe** o HTML e o Registro. O DOCX do deck é só para uso interno, e a nota de preparo nunca é enviada nem prometida: na sala, prometa "o material da apresentação e um registro do que conversamos".

## Modulação

- **Formato:** troca os quadros da tela 7, a lista de acessos e os arquivos a pedir (`padrao/formatos-de-negocio.md`).
- **Maturidade:** hipótese só na nota, nunca no deck.
- **Perfil do decisor:** muda a abertura e o que dizer cedo.
- **Modelo de mercado:** muda o vocabulário, os rótulos de público e as descrições das semanas.

## Fora do Kickoff

Análise de concorrente, SWOT, Pitch, persona nomeada, plano, tarefa de casa, Mapa de Ações e quote final (B10). O deck e o Registro mostram a função da pessoa, nunca o nome. Tela fora da sequência, fundida ou com campo vazio não existe.

## Pronto quando

Checklist B12, mais:
- As perguntas cobrem o cruzamento e ficam entre 20 e 28; os 4 quadros de dores existem; o fechamento tem validação e gancho; o cronograma usa os 5 nomes oficiais.
- Nenhum "PREENCHER" sobra nos JSON. Portão: nenhum dado "Bloqueia" sem resposta ou sem pendência com data anterior à Semana 2.
- Ficha atualizada, Registro e mensagem enviados, Semana 2 agendada.
