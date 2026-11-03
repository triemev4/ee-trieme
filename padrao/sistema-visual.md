# Sistema visual

Padrão único das 5 semanas: documento de scroll único, de tela cheia por seção, apresentado ao vivo. Navega por scroll ou pelas bolinhas laterais. Referência de layout e CSS: `referencias/layout/`. As Semanas 3 a 5 saem de `moldes/` (R14); nas demais, copie bloco a bloco. Texto, números, provas e decisões vêm das fontes do projeto em andamento. Componentes ainda não cobertos pelo sistema são criados dentro deste padrão.

## Tokens (creme, dourado e tinta)

```css
--black:#F6F1E4  /* fundo de página */      --surface:#FFFFFF  /* fundo de card */
--surface-2:#EFE7D3  /* card aninhado */     --red:#A8791A  /* acento único, dourado */
--red-deep:#7A5710  /* bronze */              --red-glow:rgba(168,121,26,.35)
--white:#221D12  /* texto principal */       --gray:#726A57  --gray-dim:#A79C84  --line:#E3D9BE
--vinho:#6E1A2C; --vinho-deep:#4E1020; --vinho-glow:rgba(110,26,44,.28); --ouro-claro:#E2C27A;
```

- Os nomes das variáveis ficam como estão (`--black` é o fundo, `--white` é o texto, `--red` é o dourado): os componentes dependem deles. Aceita leve ajuste de matiz do dourado por cliente, com os demais tokens fixos.
- Cor fixa em SVG (gradiente, rosca, ícone) usa os hex dourado, bronze e `#8B3A1A` (alerta legível sobre fundo claro).
- A paleta vale para todo material interno. Entregável com a marca do cliente (landing page) usa a identidade dele, sem monograma.

**Hover vinho (todo card):** `.cell`, `.quad`, `.field-card`, `.segcard`, `.flowchain .fc`, `.gr`, `.ac`, `.fase-grid .fg`, `.frente`, `.diag-acao > div`, `.acao-card`, `.kpi-canvas`, `.auto-card`.
- Fundo e borda `var(--vinho)` com `!important` (vence `.cell.warn` e `.fc.now`), `box-shadow:0 12px 28px var(--vinho-glow)`, `translateY(-3px)`.
- Texto creme (`var(--black)`); rótulos (`.k`, `.lbl`, `.tag`, `.num`, `.letter`, `b`), marcadores `li::before` e `.badge` em `var(--ouro-claro)` (contraste de ~6,6:1; o dourado padrão sobre vinho tem ~3:1). `.chip` mantém texto escuro.

## Tipografia

Google Fonts por `<link>`: `--display` Space Grotesk (títulos), `--body` Inter (corpo), `--mono` JetBrains Mono (eyebrows, rótulos, dados, contador). Corpo em 14 a 16px.
- `.h-xl` capa e seção-âncora, `clamp(34-40px, 5.4-7vw, 68-96px)`, peso 700. `.h-l` título de seção, `clamp(28-30px, 4-4.4vw, 46-58px)`, `max-width` 900 a 1100px. `.h-m` subtítulo, peso 600, `--gray`.
- `.lede` parágrafo de abertura, `clamp(14-15px, 1.3-1.6vw, 17-19px)`, `--gray`, `line-height` 1.6 a 1.7, até 760px.
- `.eyebrow` mono, caixa alta, 16px, `letter-spacing:.14em`, `--red`, numerado por seção (`00 ·`, `01 ·`), como sumário narrado. `.accent` destaca trecho em `--red`.

## Layout, scroll e animação

```css
.scroller{height:100vh;overflow-y:auto;scroll-snap-type:y proximity}
section{min-height:100vh;scroll-snap-align:start;padding:min(9vh,80px) min(8vw,90px);border-bottom:1px solid var(--line)}
.live-fill,.pausa{align-self:flex-start}  /* section é flex column; sem isso eles esticam */
```
- Cada `<section>` é uma tela. `.noise` (SVG `feTurbulence`, opacidade .035, `mix-blend-mode:overlay`) vai em todas as seções.
- Revelação: `.r{opacity:0;transform:translateY(28px);transition:opacity .9s cubic-bezier(.16,1,.3,1),transform .9s cubic-bezier(.16,1,.3,1)}`, `.r.in` visível, `.r2` a `.r5` com `transition-delay` de .12s em .12s. Aplicar `.r` em todo bloco de conteúdo.
- Contagem animada: `.count-num` com `data-count` sobe de 0 ao valor quando a seção entra e repete a cada reentrada (`animateCounters` no enter, `resetCounters` no exit, no mesmo `IntersectionObserver`).

## Barra fixa e navegação

```html
<div class="chrome"><div><b>Cliente</b> · Nome do Documento</div>
<div><img class="chrome-logo" src="data:image/png;base64,..." alt="V4 Trieme &amp; Co"> <span id="pagecount">01/12</span></div></div>
<div class="navdots" id="navdots"></div>
```
- `.chrome-logo{height:16px;width:auto;vertical-align:middle}`. A logo é `assets/v4-trieme-logo.png` embutida em base64 (usar o PNG tratado, sem refazer a partir de outra origem), igual em todas as semanas.
- JS (copiar): um `<button>` por `<section>` em `#navdots`, com `scrollIntoView({behavior:'smooth'})`; `IntersectionObserver` (threshold 0.5) marca o dot `.active`, atualiza `#pagecount` (`NN/total`) e põe `.in` nos `.r` da seção.
- Rede de segurança obrigatória, depois de observar as seções: `setTimeout(function(){document.querySelectorAll('.r:not(.in)').forEach(function(el){el.classList.add('in')})},2500)`. Seção densa pode nunca atingir 50% de visibilidade e deixar o conteúdo preso em `opacity:0`.
- `.navdots button` é círculo de 8px (borda `--gray-dim`), 10px e `--red` com glow quando `.active`. Abaixo de 800px, `.navdots{display:none}`. Navegação por teclado não existe; só scroll e clique.

## Hero

`<section class="hero">` é a primeira tela no Kickoff e a segunda nas Semanas 2 a 5 (depois da ponte). Estrutura: `.hero-top` (marca e data, mono 15px), `.hero-mid` (`.hero-tag` mono dourado 16px, `.h-xl`/`.hero-title`), `.hero-sub` (lede), `.hero-bottom` (`.hero-meta` com 2 ou 3 métricas-gancho, `.m .k` mono 13px `--red`, `.m .v` display 22px peso 700; e `.scrollcue` "role para começar"). `.treadline`/`.pulseline` é faixa decorativa de baixa opacidade na base.
- `.consultor-tag`: nome e cargo do consultor (da configuração do pacote) e foto opcional (`EE/foto-consultor.jpg`; sem arquivo, sem foto), no hero do Kickoff.
- `.v4-mark`: monograma `assets/v4-monograma.png` (558x558, transparente), em base64 como `mask` sobre `background:var(--vinho)`, `opacity:.08`, à direita. HTML `<div class="v4-mark" aria-hidden="true"></div>` logo depois de `.noise`; CSS `.hero > :not(.noise):not(.v4-mark){position:relative;z-index:1}`. Só no hero, nunca na ponte nem em outra seção. Usar o PNG oficial.

## Componentes de conteúdo

- `.grid` com `.g2`/`.g3`/`.g4` e `.cell`: cards de dado, borda `1.5px solid var(--red)`. `.k` rótulo mono 14px cinza; `.v` valor em display (`.v.red` no número-âncora); `.d` descrição. `.cell.warn` marca achado real crítico (só nele o `.k` vira dourado) e nunca "não sabemos ainda".
- `.layer`, `.layer-head` (`.name`, `.tag`), `.l1` `.l2` `.l3`: blocos aninhados com recuo de 0, 4% e 8% (TAM, SAM, SOM).
- `.segcard`: card de segmento, persona, pilar ou coluna, com `.tag`, `h4` e parágrafo. `.split`: duas colunas (.85fr 1.15fr), resumo de um lado e texto do outro. `.quad`: quadro de borda dourada com conceito e pergunta aberta.
- `.funnel`: etapas verticais numeradas com tag de status. `.pillar`: pilar temático. `.timeline` e `.phase`: execução por fases. `.rtable`: tabela de dados, números em mono. `.risk`: linha de risco com nível e mitigação. `.checklist`: grade de 2 colunas para recomendações. `.comp-card`: comparação entre concorrentes. `.prio`: recomendação priorizada.
- `.chip` e `.pill`: etiquetas mono de status, dono e categoria. `.foot`: rodapé de assinatura.
- `.fonte-rodape`: fonte curta, de 1 a 2 linhas, na tela que tem o dado (arquivo, período, quantidade de registros, método da estimativa). Toda tela com número pesado leva um. Não há tela de referências nem `.srclist`.
- `.amarra`: faixa abaixo do `h2` em toda tela de conteúdo das Semanas 2 a 5 (regra B3; o verificador recusa a tela sem ela). Três `<span>` com `<b>`: Pilar do escopo, Dor que trata (fala do cliente e reunião), Para a [Cliente]. CSS: `.amarra{display:flex;flex-wrap:wrap;gap:8px 18px;margin:10px 0 4px;padding:10px 14px;border-left:3px solid var(--red);background:var(--surface);border-radius:0 8px 8px 0;font-size:13px;color:var(--gray);line-height:1.45;max-width:1200px}`, `.amarra span{flex:1 1 260px}`, `.amarra span b{font-family:var(--mono);font-size:10px;text-transform:uppercase;letter-spacing:.08em;color:var(--red);margin-right:6px;font-weight:600}`. O gerador da Pesquisa injeta o CSS; nas outras semanas, copiar.

## Componentes de condução

- `.bridge`: ponte de abertura (Semanas 2 a 5) com 2 ou 3 achados (Pontos de Melhoria) da semana anterior, nunca Solução, tirados literalmente das telas publicadas, e 2 ou 3 do que esta cobre. `.bridge-cols` alinha as linhas das duas colunas (`min-height` fixo e `box-sizing:border-box`). `.bridge-track` com `.tk.done` e `.tk.now` mostra as 5 semanas, com setas entre elas.
- `.abertura-capitulo`: frase "Hoje vamos [verbo]... [objetivo]." abaixo do eyebrow, uma frase só, apenas na tela que abre cada tópico de diagnóstico, nunca em toda tela. `.agenda-solo`: agenda cronometrada (`.item .time`, `.total`), sem papéis, no início do Kickoff.
- `.ponto-partida`: rótulo "Ponto de partida" que abre um bloco de diagnóstico. `.diag-acao`: duas colunas, Pontos de Melhoria (P) e Para onde isso vai (S). `.acao-card`: "AÇÃO N, título" e uma frase. `.kpi-canvas`: quatro linhas (o que medir, como medir, fórmula, meta).
- `.field-card`: selo de 2 letras, rótulo, valor e descrição de campo confirmado pelo cliente; `.field-card.pending` (selo preenchido) para pendência real.
- `.live-fill`: selo "Estamos ao vivo" (borda tracejada) em seção deixada em branco para preencher com o cliente, sem conteúdo pronto nem hipótese. Uso no Kickoff: esqueleto da Semana 1, telas 5 e 9.
- `.explicador`: caixa de borda esquerda dourada, tag "O QUE É [TERMO]" e 1 ou 2 parágrafos simples. Termo já explicado antes leva uma nota de 1 linha com a remissão.
- `.pausa`: sino dourado e uma pergunta curta para interagir. `.gancho`: spoiler da próxima etapa. Composição do fechamento: base B9.
- `.flowchain`: cronograma sequencial com setas, itens `.fc` (`.fc.now` no atual). `.donut-wrap`: rosca SVG (`stroke-dasharray`, r=15.9155) com legenda, só com dado real.
- `.lanes` (2 trilhas) e `.lanes.h3c` (3 trilhas H1, H2, H3): trilhas de plano, empilhadas em coluna única no celular. `.ac`: card de ação (título, ação, dono em `.chip`); `.ac.prio` é o "Comece aqui", um por plano. `.own`: linha do dono. `.orig`: "vem da Semana N". `.tipo.qw` (Quick win, preenchida) e `.tipo.es` (Estrutural, contorno) dentro de `.own`, com legenda `.tipo-leg`.
- Semana 5: `.caminho` com etapas pertinentes, estado e origem; `table.gr-matriz` com oito dimensões (sete mais calendário do cliente); `.rtable.receita` com incremento, tempo, contribuição, sobreposição e `.selo` dado/estimativa/premissa; `table.riscos` e `table.premissas` com itens pertinentes; `.entreg-grid` preserva status. Mapa em `.lanes` com um `.ac.prio`. Fecho com tese proporcional, `ol.dias` de ações pertinentes e `.proxima-restricao`. Árvore, dilema e classificação TOC ficam no fundamento/detalhe quando ajudam, sem telas próprias obrigatórias.
- Semanas 2 a 4: Próximos passos com `.ac`, dono/prazo em `.own`, uma única `.ac.prio` na primeira posição, `.pausa` e `.gancho`; sem trilhas no fecho. S4 acrescenta `.dobro` e `.corda`, aceitando hipótese e limite a medir. Processo atual em `.processo-raias`, imagem local com alternativa textual completa; PNG serve também ao DOCX.
- Semana 3: `.frente` (card de frente de marketing). Régua de CRM e automações: `.auto-card` (referência: `moldes/`).

## Mockups (comparação atual e ideal)

Dentro de `.wf-compare`, `.wf-col` e `.cap` (rótulo "Atual" ou "Ideal", centralizado, porque o mockup fica centralizado na coluna).
- `.browser-mock`: moldura de navegador com `.bm-page` clara, `.bm-nav` (menu real do cliente), `.bm-hero.weak` ou `.bm-hero.strong`, `.bm-trust`, `.bm-problems`, `.bm-grid` de `.bm-card` (`.hi` nos destaques do ideal) e `.bm-caption` de 1 frase.
- `.ig-mock`: moldura de celular com perfil real (avatar, posts, seguidores e seguindo iguais nos dois lados), bio, destaques com ícone e `.ig-feed` de `.ig-tile` (`.promo`, `.brand`, `.tech`), cada miniatura com gradiente, ícone e legenda.
- `.ad-mock`: anúncio com cabeçalho "Patrocinado", `.ad-media` (`.half.bad` e `.half.good`, `.reel`, `.product`, `.quote`) e `.ad-foot .btn`.
- `.phone` com `.bub.in` e `.bub.out`: conversa de WhatsApp, rotulada "exemplo de abordagem" quando não é transcrição.
- Número em mockup (preço, seguidores, nome de cliente) é real e confirmado; só o elemento genérico (ícone, texto de anúncio de exemplo) é ilustrativo. Exemplo realista (print reconstituído de perfil, anúncio que parece real) vale mais que conceito abstrato.

## Gráficos

- TAM/SAM/SOM em 3 elipses SVG sobrepostas na horizontal, da maior (TAM, cinza) à menor (SOM, dourado pleno), com gradiente radial e rótulo de conceito (Mercado Total, Atendível, Alcançável), com o escopo do cliente na `.fonte-rodape`. O `viewBox` começa em x negativo o suficiente para não cortar a primeira elipse.
- Visual por nome segue o esqueleto vigente: TAM/SAM/SOM (S2, tela 4), rosca da verba no Forecast (S3, tela 12), campanhas (S3, telas 6 e 7), atual × ideal site/Instagram (S3, telas 9 e 10), processo em raias (S4, tela 5), pirâmide do funil (S4, tela 9). Sem base para número, a visualização preserva estado/lacuna em vez de inventar percentual. Fora desses casos, use o componente pertinente.
- Mapa mental híbrido (o draw flow): SVG só para as linhas, `div` posicionadas para os nós, conexão na borda das caixas e `min-height` nas folhas.
- Os 5 nomes oficiais das semanas aparecem em `.flowchain` e `.bridge-track` exatamente como na base.
