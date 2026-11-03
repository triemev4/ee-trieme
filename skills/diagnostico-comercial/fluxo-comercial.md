# Fluxo comercial · como desenhar fluxo, kanban e funil na Semana 4

Quatro peças dentro do deck da Semana 4 (sequência e teto: esqueleto S4, base B4):
- **processo atual em raias**, na tela 5, com responsáveis, ferramentas e dores observadas;
- **fluxo de aquisição proposto**, na tela 9 (Funil), ao lado da pirâmide;
- **kanban do CRM**, na tela 11 (Desenho do CRM);
- **fluxo de pós-venda**, na tela 13 (Pós-venda e implantação).
Fluxo que não cabe legível na tela vai inteiro para o detalhe do DOCX. Layout e CSS: `moldes/semana-4.html`, preenchido por `scripts/preencher_molde.py` (o guia da etapa traz o comando).

## O que ler antes de desenhar

- Transcrições, das mais recentes às mais antigas: a reunião mais nova vence (base B0).
- Origem dos leads que o cliente opera de fato, não a desejável.
- Etapas reais entre o lead e o cliente ativo, quem toca em cada uma, onde há decisão, onde há loop.
- Motivos de perda por etapa e o pipeline atual, com o nome que o time do cliente dá a cada estágio.
- Pós-venda: quem cuida da conta ativa, quando começa a expansão, se existe indicação.
- Falta algo? Vira pendência no plano, nunca invenção. Fluxo errado estraga a reunião.

## Regras de desenho

- **Nó** em verbo mais objeto direto: "Lead registrado no CRM", "Reunião agendada", "Contrato assinado". Número dentro do nó só quando ele é a informação, e vem da ficha.
- **Cargo, nunca nome de pessoa:** "SDR qualifica: porte, volume, nicho". Cargo ainda não definido: "SDR" genérico e pendência.
- **Gateway** é uma pergunta que decide o caminho: "Dentro do ICP?", "Fechou na reunião?". Toda saída tem rótulo (SIM, NÃO, RETORNA). Use só decisões reais; se muitas prejudicarem a leitura, divida a apresentação e preserve o fluxo completo no detalhe.
- **Card de saída** para todo nó que sai do fluxo (desqualificado, perdido, follow-up): kick curto ("Saída", "Loop"), título curto e uma frase do que acontece nesse caminho.
- **Direção:** fluxo vertical, do início ao fim; ramificação sempre para a direita. Legenda de uma linha (início ou fim, tarefa, decisão, saída positiva, saída negativa).

## Os dois fluxos

- **Aquisição**, a adaptar ao que o cliente opera: origem → ativo de conversão → captação no CRM → qualificação → "Dentro do ICP?" → reunião → "Fechou?" (NÃO volta para a reunião como follow-up) → proposta → "Contrato assinado?" → implantação → ganho, que aponta para o pós-venda. Nó que o cliente não tem sai.
- **Pós-venda:** retenção → monitoramento da conta → "Dor mapeada?" (NÃO volta ao monitoramento) → oferta nova → "Expandiu?" (NÃO volta à retenção) → indicação, em loop tracejado de volta ao topo da aquisição. O loop é o que diferencia o desenho de "gerenciar conta".

## Gerar o processo atual em raias

Grave `<semana>/_fonte/processo.json` a partir de observação e fontes. Separe o processo atual da proposta. `lanes` contém `{id,nome,externa}`; `nodes`, `{id,lane,tipo,texto,ferramenta?,dor?,fonte?,restricao?}`; `flows`, `{de,para,rotulo?,mensagem?}`. Tipos: `inicio`, `tarefa`, `decisao`, `fim`. `externa`, `restricao` e `mensagem` são booleanos; IDs são únicos em cada lista e referências devem existir. A ordem de `nodes` é a ordem de leitura; conexões podem voltar ou formar loops. O comprador ocupa uma raia externa. Dor e ferramenta são textos observados, não rótulos deduzidos do cargo. O comando está no guia da etapa.

O SVG fica para inspeção/zoom; use o PNG no `tela-05.imagem`, com `alt` descritivo, para incorporar também no DOCX. Sem navegador, gere apenas SVG e mantenha etapas, responsáveis, entradas/saídas, ferramentas e dores no substituto textual do molde e no detalhe. A imagem complementa o diagnóstico; não substitui o fato, a fonte, o impacto e a ação. Fluxo alto vai para o detalhe com recorte legível na apresentação. Preserve todas as dores registradas; dez é orientação de composição, nunca limite de dados.

## Kanban e funil

- **Estágios com os nomes do cliente**, sem número fixo de colunas. Cada um: nome curto e uma frase do que acontece dentro. Último estágio ("ganho") em verde.
- "Perdido" e "desqualificado" são caixa lateral tracejada, nunca estágio.
- Funil e kanban usam os mesmos nomes de estágio.
- **Funil numérico:** cada etapa com o número do cliente (Números-fonte da ficha) ou "a medir". Nenhum percentual típico de mercado.
- **CRM:** só a capacidade necessária (B10).

## Anti-exemplos

- Nó ruim: "Análise multifatorial do fit comercial do lead". Bom: "SDR qualifica: porte, volume, nicho".
- Gateway ruim: "Avaliação de viabilidade do lead". Bom: "Dentro do ICP?".
- Estágio ruim: "Fase de nurturing avançado com scoring automático". Bom: "Reunião agendada: reunião marcada com o decisor".
