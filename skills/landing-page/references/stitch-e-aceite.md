# Stitch e aceite

## Geração

Use a lista de ferramentas da sessão como contrato técnico. A sequência conceitual é localizar/criar projeto, estabelecer sistema visual, gerar tela, ler HTML/imagem e editar. Há variação de nomes de parâmetros entre clientes/versões; não copie chamada de exemplo sem conferir o esquema disponível.

1. Projeto: um por cliente/LP, salvo outra organização já definida. Registre o ID imediatamente em `stitch.json`; na retomada, consulte esse ID. Conta pertence ao consultor ou organização definida no ambiente; não misture credenciais entre consultores.
2. Sistema visual: crie/aplique a direção aprovada usando as ferramentas disponíveis de sistema de design. Se importar `DESIGN.md`, conclua a criação/aplicação depois do upload. Em projeto com sistema aplicado, concentre o prompt na página, sem repetir tokens de tema conflitantes.
3. Prompt inicial: objetivo de negócio, comprador, dispositivo, percurso, seções com texto exato da copy, função de imagens, ação e estados necessários. Use linguagem direta e estrutura curta. Descreva a ideia da Assinatura por seção e o que a régua guarda.
4. Inspeção: recupere imagem e HTML. Compare texto e dados com a copy; observe primeira dobra, hierarquia, leitura no celular e representação da marca. Repetir "mais premium" não especifica uma correção.
   Quando houver `download_file`, use o nome do recurso retornado pela tela e extraia o campo `html` da resposta. URLs de download podem exigir autenticação ou retornar um envelope JSON; não as trate automaticamente como HTML público.
5. Refinamento: cite localização, problema e efeito desejado. Preserve o restante da página. Use variantes quando houver uma escolha real entre composições; edições focadas para corrigir uma direção já escolhida.

Exemplo de refinamento:

> Na primeira dobra do celular, o botão fica depois de uma imagem muito alta. Reduza a altura da imagem e ajuste o espaçamento para tornar a oferta e a ação visíveis. Preserve o texto e o sistema visual.

`stitch.json` guarda somente IDs, URLs, datas, revisão da copy usada e histórico curto das gerações/edições. Nunca chave de API. Em timeout de geração/edição, consulte projeto/telas: a operação pode ter terminado. Não dispare outra criação às cegas. Em indisponibilidade persistente, registre a pendência interna e retome depois; pesquisa/copy e o próximo encontro continuam.

## Aceite

O protótipo deve cumprir o escopo registrado. Para a entrega padrão:

| Dimensão | Evidência necessária |
|---|---|
| Estratégia | Comprador, oferta e ação coerentes com S2–S4; cada promessa dentro da prova |
| Copy | Textos finais, naturais e específicos; nenhuma afirmação nova sem origem; nomes/CTA coerentes com criativos |
| Visual | Marca e contexto do nicho reconhecíveis; hierarquia legível e imagens adequadas; direção aprovada; contraste medido de textos e controles |
| Assinatura | Régua do nicho e frase da ideia no `DESIGN.md`, com a fonte (ficha, ICP, PUV ou fala do comprador); ideia visível na primeira dobra e em mais uma seção; com a logo de cada concorrente da régua, a página não serviria a ele; sinal de molde ou de IA só com motivo escrito |
| Responsividade | HTML inspecionado no navegador em 390 px, 1440 px e ao menos uma largura intermediária próxima da mudança de layout (por exemplo, 800 px); sem rolagem horizontal, texto cortado ou colunas comprimidas |
| Interação | A ação escolhida para a página é testada: botões levam ao destino previsto; se houver formulário, ele demonstra validação e confirmação; teste de teclado/foco e rótulos acessíveis |
| Entrega | HTML e recursos recuperáveis, link na S5, versão revisada identificada e limites de implantação registrados |

Capturas distintas do Stitch não provam responsividade. Abra o HTML entregue. Formulário demonstrativo não envia dados nem simula um atendimento real: a confirmação deve tornar claro que é uma demonstração. Destinos externos reais só são ativados quando o escopo e a autorização cobrirem a ação; até lá, o protótipo mostra o percurso sem abrir conversa ou enviar solicitação.

Meça as cores efetivas no navegador: texto comum exige 4,5:1; texto grande (24 px, ou 18,67 px em negrito) exige 3:1; informação visual necessária para reconhecer controles e estados, incluindo fronteiras de campos quando necessárias e foco customizado, exige 3:1 contra as cores adjacentes. Divisor decorativo não é borda de controle. Se a direção fixa falhar, proponha o ajuste ao coordenador em vez de declarar a página aprovada por fidelidade ao `DESIGN.md`. Registre par de cores, razão e elemento; estes testes não certificam conformidade WCAG completa. Fontes: [contraste de texto](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html) e [contraste de controles](https://www.w3.org/WAI/WCAG22/Understanding/non-text-contrast.html).

`scripts/inspecionar_lp.py` mede as cores e confere larguras, teclado, CTA e formulário em 390, 800 e 1440 px, e grava as capturas e o `inspecao.json`: `python "<raiz>/scripts/inspecionar_lp.py" "<html>" --copy "<copy.json>" --saida "<pasta das capturas>"`. Ele usa o playwright, que é opcional. Sem o playwright, ou sem Edge e Chrome, o script diz "inspeção pendente": o consultor confere a olho em 390, 800 e 1440 px e registra "contraste não medido". O script mede e não aprova: o aceite continua decisão do consultor.

Teste de leitura pelo comprador: ele consegue explicar o que se vende, para quem serve, por que confiar e qual o próximo passo? Use ICP/personas da S2. O ensaio dos decks representa o contratante da EE e não substitui essa revisão. Registre simulação como revisão, nunca como teste de conversão.

`revisao.md` lista arquivos e larguras inspecionados, observações de linguagem/visual/interação, problemas corrigidos, avisos aceitos com motivo e itens ainda dependentes. Se houver problema material, a página segue em revisão. A aprovação humana na ficha referencia o comprovante daquela versão; alterações em copy, HTML, estilo ou recursos locais exigem nova conferência.

O HTML pode usar dependências remotas justificadas, mas o consultor precisa saber que exigem internet. Prefira recursos locais para os ativos essenciais: o verificador acha os que o HTML e os CSS citam e inclui todos no comprovante sozinho. Publicar, configurar domínio, capturar leads, instalar pixels e integrar CRM são tarefas de execução; a entrega registra o que será necessário, sem declarar essas tarefas realizadas.

## Medição do piloto

Registrar no sistema existente: horas humanas de pesquisa/copy/visual/revisão, chamadas e refinamentos, motivo do retrabalho e aceite. Depois de publicado, medir conversão e qualidade dos leads com origem/período. Comparar desempenho exige tráfego e condições comparáveis; nota editorial não estima ganho de conversão.
