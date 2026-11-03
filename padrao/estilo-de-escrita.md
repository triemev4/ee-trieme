# Estilo de escrita

Régua de redação de todo material da EE: decks, DOCX, fichas, mensagens e os próprios guias. Todo guia de etapa termina com uma passada por este arquivo antes de gerar o HTML (seção "Revisão final"). Os guias apontam para cá e listam só o que é específico deles.

## Princípio: simplicidade sofisticada

Simples quer dizer o essencial, sem lacuna. Cada material passa por estes testes:
- **Uma ideia por tela,** que cabe numa frase e muda uma decisão do cliente.
- **Teste do corte:** tirar o item piora o resultado? Se não piora, sai.
- **Teste da troca:** a frase serviria no site do concorrente? Se serviria, é genérica e se reescreve com o fato do cliente (número, nome, fala), nunca trocando sinônimo.
- **Tela com contenção:** um número grande, uma leitura, espaço; cor, borda e ícone só quando carregam significado (`sistema-visual.md`).

## Regra-mãe de fonte

Todo conteúdo sobre o cliente sai dos insumos (`0. Inputs e Transcrições/`: handoff, transcrição da venda, contrato, materiais enviados) e do que o cliente disser nas reuniões do projeto. O que não estiver aí vira pergunta (Kickoff) ou pendência explícita (demais semanas). Vale para os fatos sobre número, nome, estrutura societária, foco, canal, processo e ferramenta. Interpretações e escolhas estratégicas seguem a regra de inferência abaixo.

1. **Fontes que divergem:** base B0. Até a resposta do cliente, usar o termo neutro e confirmado ("a empresa", "o fundador"). Exemplo: o contrato diz "Alfa Serviços" e só o site diz "Grupo Alfa"; escrever "a Alfa Serviços" e perguntar sobre a estrutura societária.
2. **Afirmar só o que a fonte diz.**
   - Repetir a fonte: se ela diz "iniciativa da prefeitura", a tela diz "iniciativa da prefeitura".
   - Escrever o alcance real da leitura: "nos contratos que lemos (A, B e C)".
   - **Fato, cenário e proposta:** dado factual ausente continua ausente. Cenário pode usar premissa proposta pela consultoria: marque autor, unidade, data, justificativa e teste que a confirma ou refuta. Separe relato, cenário e proposta de execução; nenhum equivale a fato comprovado ou aceite. Inferência decisiva mostra evidência, premissa e condição de revisão. Conta passa pelo `calcular.py`; premissa proposta usa `origem: "premissa: consultoria (proposta), dd/mm/aaaa"`. O número conserva esse estado na ficha e na tela.
3. **Número só com origem.** Número fora dos insumos e de fonte confiável recebe o rótulo "estimativa V4", com o método na tela, ou vira pendência. Conta nenhuma sai de cabeça: o resultado vem de `scripts/calcular.py`, já gravado em Números-fonte com a fórmula e a origem de cada parcela, e o texto copia esse valor, no formato que o script devolveu.
4. **Mercado:** universo e preço têm origem; contagem explicita recorte, capacidade e período. Premissa proposta exige fundamento e teste pela regra acima. Sem fundamento para delimitar a conta, mantenha a lacuna uma vez na tela; detalhe e verificação no DOCX. Rótulo sozinho não sustenta estimativa.
5. **Todo número diz de quem é e a unidade.** Ruim: "R$ 40 contra R$ 25 a 35". Bom: "a [Cliente] cobra R$ 40 por consulta; as clínicas do bairro cobram de R$ 25 a 35 por consulta particular". O mesmo vale para "a diferença", "o escopo" e "o preço".
6. **Dado de mercado** (tamanho de setor, concorrência, tendência) vem de pesquisa externa com fonte e ano. A regra vale para fatos do cliente; o mercado se pesquisa.
7. **Validar o modelo do cliente nos insumos antes de escrever:** quem compra, como compra, unidade de venda, canal, regulação, estágio. As referências visuais neutras orientam o layout; o negócio vem dos insumos.
8. **Nível de mercado:** um por vez (base B11).
9. **Sem prova, marcar.** Quando falta o dado que sustentaria a frase, o rascunho leva `[falta prova: o que falta]` no lugar da afirmação. O marcador nunca chega ao cliente: antes de entregar, vira pergunta, pendência ou sai.
10. **Frentes de aquisição:** separe público, função, abordagem, evento de conversão, destino e limite operacional. Busca e abordagem por contas podem coexistir. ABM depende de contas identificáveis e acessíveis, economia e capacidade, além do perfil B2B ou da preferência por compradores de maior valor. Procura por poucos clientes grandes, sozinha, não prova que ABM serve.
11. **Ferramenta atual e recomendação:** preserve o nome e o uso das ferramentas que o cliente já tem quando forem relevantes, com a fonte. Apresente como proposta a capacidade que falta; opções de fornecedores e preços ficam em comparação separada, com fonte, data e condições.

## Regras de estilo

- Pausa com vírgula, dois-pontos ou ponto. O travessão fica fora de todo material.
- Pessoa do cliente aparece pelo cargo ("o Diretor Comercial"), inclusive nos nós de fluxo. Única exceção: o dono de ação do Mapa de Ações, que é o cargo com o nome entre parênteses ("Vendas (Lia)"). Fora isso, nome só na nota de preparo e em executivos de terceiros quando o dado é público e relevante.
- O sujeito da mudança é a empresa ("a [Cliente] precisa..."). A pessoa é sujeito só quando a frase trata do que ela decide, aprova ou diz.
- Termo técnico ou sigla leva tradução simples na tela (`.explicador`), e a sigla é aberta na primeira ocorrência de cada tela. Termo que o mercado usa em inglês fica em inglês ("fulfillment"). No texto voltado à operação, a palavra do time do cliente ocupa o lugar do nome do método (SPIN, BANT).
- Título e tela "a validar": base B6. Use rótulos de estado para deixar visível uma incerteza que afeta a conclusão; o título orienta a leitura e não precisa fechar uma tese em forma fixa.
- Dado repetido em formatos diferentes (título, diagrama, recap) reforça. A mesma frase em blocos vizinhos sai ou ganha informação nova. Diagrama que já comunica dispensa o parágrafo que repete o conceito.
- A tela ao vivo fica enxuta; o detalhe vai para o DOCX e para os entregáveis.

## Textos que evitar

- **Dicotomia avulsa:** "não é só X, é Y", "mais que uma ferramenta, uma parceria". Vale só como comparação real e útil.
- **Lista de negação:** "sem X, sem Y, sem Z", "nada de A, nada de B". Dizer o que é.
- **Frase arrastada:** a frase termina e segue com vírgula e mais cláusulas ("..., o que mostra..., garantindo..."). Ponto final e frase nova.
- **Palavras esvaziadas:** solução, inovador, transformação digital, tecnologia de ponta, jornada, ecossistema, sinergia, empoderar, revolucionar, elevar, potencializar, otimizar, alavancar, robusto, escalável sem métrica ao lado.
- **Frases-cobertor:** "no mundo cada vez mais digital", "em um mercado competitivo", "hoje em dia", "vale ressaltar", "é importante notar".
- **Abertura enrolada** ("Antes de mais nada", "É fundamental entender que") e **fechamento vazio** ("em resumo", "portanto" sem conteúdo novo). Começar e terminar pelo conteúdo.
- **Revelação com dois-pontos** ("O resultado: ...", "O motivo? ...") e **frase curta de efeito** ("E isso muda tudo."). Escrever a frase inteira, com sujeito e verbo, no lugar do achado.
- **Adjetivos empilhados**, **listas de três rimadas**, **pergunta retórica decorativa**, emoji decorativo e exclamação em cascata.
- **Elogio à marca sem prova** ("somos referência") e **fonte vaga** ("especialistas apontam"). Dizer quem, qual estudo e o ano, ou cortar a frase.

## Tom

Direto e seco, de quem entende do negócio do cliente, como conversa entre duas pessoas do setor. Português formal por padrão; seguir o glossário e o registro que o cliente usa nas transcrições.

## Números e formatação

- Vírgula decimal e ponto de milhar: `R$ 1.500,00`. Percentual sem espaço antes do `%`.
- Faixa com "a" (`R$ 30 a 50 mil`, `6 a 12 meses`); aproximação com uma forma só ("cerca de" ou "~").
- Estatística de mercado traz fonte e ano entre parênteses.
- Nos documentos, cabeçalhos numerados em hierarquia (2, 2.1, 2.1.1) e tabelas comparativas em markdown.

## Revisão final

A última passada de todo guia, antes de gerar o HTML:
1. Os quatro testes do Princípio, tela por tela.
2. Lista "Textos que evitar" e marcadores `[falta prova: ...]` resolvidos.
3. Ortografia, acento, hífen e crase; nome de produto, marca e termo técnico como o cliente escreve.
4. Concordância e registro coerentes do começo ao fim; CTA e nomes de produto, serviço e formulário idênticos em todas as seções.
5. Promessa do início sustentada até o fim, com os mesmos números e prazos.
6. Termos do `glossario.md`, sem os da coluna "evitar".
