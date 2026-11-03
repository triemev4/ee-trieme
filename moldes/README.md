# Moldes por semana (R14)

Um molde por semana: `semana-N.html` (a página com espaços marcados), `semana-N.textos.json` (textos de exemplo explicitamente fictícios) e `scripts/preencher_molde.py` (que junta os dois). Este arquivo é para quem faz e mantém moldes. O consultor e o assistente não abrem o HTML do molde.

## Como usar

```
python scripts/preencher_molde.py moldes/semana-N.html _fonte/textos.json saida.html
python scripts/preencher_molde.py --listar moldes/semana-N.html
```

`--listar` imprime o que o molde espera: um caminho por linha, com a lista e o item aninhados. A saída é o HTML pronto, sem nenhuma marcação `data-`. Faltou um caminho no JSON: o script lista tudo o que falta, não grava nada e sai com código 1. Chave do JSON sem espaço no molde: aviso, e a saída sai igual. Também saem como aviso (a saída é gravada): texto vazio num `data-t` (o elemento sai vazio) e número onde o molde espera texto (`"titulo": 45` sai como "45"; se era texto, ponha entre aspas). Texto vazio de propósito, como o cartão em branco do quadro de funil da Semana 4, também avisa; confira se era isso mesmo.

## Marcações

| Marca no HTML | O que faz |
|---|---|
| `data-t="tela-04.titulo"` | O conteúdo do elemento vira o texto desse caminho do JSON. O JSON é aninhado: `{"tela-04": {"titulo": "..."}}`. |
| `data-lista="tela-05.frentes"` | Bloco repetível. O valor é uma lista; o bloco sai uma vez por item, na ordem. Lista vazia remove o bloco. |
| `data-opcional="tela-07"` | Numa `<section>`. O JSON liga ou desliga em `{"opcionais": {"tela-07": false}}`. Desligada, a tela sai. Sem valor no JSON: erro. |
| `data-img="tela-08.print"` | Espaço de print real. Com caminho de imagem no JSON, o conteúdo vira `<img>` embutida (base64). Vazio ou `null`: fica o mockup. |
| `data-estilo="--pct:tela-04.rosca.pct"` | Põe a variável CSS no `style` do elemento com o número do JSON. Várias marcas se separam com `;`. |
| `data-classe="prio:.comece_aqui"` | Adiciona a classe quando o caminho é `true` e remove quando é `false`. Exige booleano; aceita contexto do item e pares separados por `;`. Mantém a ordem da lista. |
| `data-num` | Troca só os dígitos do começo do texto do elemento pela ordem em que os marcados ficaram (01, 02, 03...). `<div class="eyebrow r" data-num>03 · Meta Ads</div>` vira `02 · Meta Ads` se uma tela numerada antes dele saiu; o resto do texto fica. O eyebrow continua sendo texto direto do elemento, que é o que o verificador lê. Texto que não começa com dígitos: erro. Serve para tela opcional desligada não deixar buraco na numeração. |

## Regras de cada marca

- **Texto.** Só texto puro e negrito escrito como `**assim**` (vira `<b>`). Todo o resto é escapado, então `<` e `&` no texto não quebram o layout. O elemento marcado perde tudo o que tinha dentro; para manter um ícone ou um número fixo, ponha o texto num `<span>` interno e marque o `<span>`.
- **Lista.** Dentro do bloco, o caminho relativo começa com ponto: `data-t=".titulo"`. Lista dentro de lista vale: `data-lista=".acoes"`. Para lista de textos simples, o item é o próprio texto e o caminho é `data-t="."`. O elemento com `data-lista` é o que se repete (o cartão, a linha da tabela, o item de lista). Ele pode levar também `data-estilo` ou `data-t` relativos ao item.
- **Opcional/condensável.** `data-opcional` exige flag; `data-condensavel` aparece por padrão. Ambos usam `opcionais.tela-NN: false` para retirar a tela. Na condensação, preserve o pilar e suas fontes no detalhe do DOCX (B4).
- **Imagem.** O valor no JSON é um caminho relativo ao JSON ou absoluto (png, jpg, webp, gif ou svg), ou um objeto `{"caminho": "...", "alt": "..."}`. Os textos do mockup só são exigidos quando não há imagem. O `<img>` sai com largura máxima de 100%.
- **Estilo.** O JSON traz um número (`45`) ou um texto com percentual (`"45%"`). O script escreve exatamente isso; o CSS do molde decide a forma (`calc(var(--pct) * 1%)` pede `45`, `var(--pct)` pede `"45%"`). O exemplo do JSON mostra a forma certa.
- **Notas.** Chave do JSON que começa com `_` é nota para o assistente (limite de caracteres, exemplo) e é ignorada.

## O que o script não mexe

O resto do HTML sai igual: CSS, scripts, comentários. O parser (`html.parser` do BeautifulSoup) faz só normalizações inevitáveis: `<br>` vira `<br/>`, atributo sem valor ganha `=""`, entidade como `&nbsp;` vira o caractere. A aparência não muda.

## Regras para fazer e manter um molde

1. Use `referencias/layout/` para consultar os exemplos neutros de Kickoff e pesquisa de mercado; para as Semanas 3 a 5, mantenha o próprio molde como referência visual. Preserve CSS e componentes pertinentes à sequência vigente. Prova causal da S5 pertence ao detalhe, sem restaurar a árvore como tela.
2. A sequência é a do esqueleto (o teto), com a faixa `.amarra` e, nas Semanas 3 e 4, a tela "Próximos passos": uma a cinco ações, a primeira e única `comece_aqui`, dono/prazo, pausa e gancho. Horizontes ficam no fundamento e no PED.
3. Eyebrow numerado ("03 · Meta Ads", Semanas 3 e 4) leva `data-num`; o nome depois do número é fixo e o número acompanha a sequência do esqueleto. Todo texto visível que muda de um cliente para outro leva `data-t`. Texto fixo do método (rótulos de componente, legendas) fica sem marca.
4. Nome do caminho: `tela-NN.assunto` para a tela, nomes curtos e iguais ao que o guia da semana usa. O número da tela é o da posição no esqueleto, não o que o eyebrow mostra depois da numeração.
5. Todo bloco que muda de quantidade (cartão, concorrente, ação, linha de tabela) leva `data-lista`. Confira o JSON de exemplo com 1 item e com 6 itens.
6. Toda tela que o esqueleto marca como opcional leva `data-opcional`.
7. Todo print real (Google Meu Negócio, anúncio, site) leva `data-img`, com o mockup dentro como substituto.
8. Barra, rosca e pirâmide desenhadas por CSS recebem o valor por `data-estilo`. Não escreva a conta no JSON; guarde só o número.
9. O molde preenchido precisa passar no verificador público e preservar o sistema visual nas telas pertinentes. Inspecione manualmente mudanças de conteúdo, ordem e componentes sem exigir igualdade de telas retiradas.
10. Sem travessão em nenhum arquivo do molde nem do JSON de exemplo. Os textos seguem `padrao/estilo-de-escrita.md`.

## Verificação pública

Execute `python tests/testar_distribuicao.py` para a verificação de distribuição incluída neste pacote. Os testes e as referências privadas da equipe não fazem parte deste repositório.
