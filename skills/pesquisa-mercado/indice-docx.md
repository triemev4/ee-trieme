# Índice do DOCX · Detalhe para consulta

O HTML mostra as telas do esqueleto (10, ou 11 com a opcional). O fundamento que não cabe nelas vai para telas `"so_docx": true` do `conteudo.json`. A abertura também usa `"abertura_docx": true`: o gerador a coloca após a capa, antes da ponte, sem repeti-la no detalhe. As demais seções exclusivas vêm depois da apresentação, sob "Detalhe para consulta"; não contam nas telas HTML.

## Regras do detalhe

- Toda tela de detalhe leva `fontes` (o gerador recusa tela sem fonte), com link quando houver URL. Cada seção fecha com "Fontes".
- O DOCX traz o que o deck não mostra. Tela do deck não se repete aqui.
- Um número do detalhe que reaparece no deck vem da seção Números-fonte da ficha, com o mesmo valor.
- Eyebrow no formato "Detalhe · Setor". Apagar do JSON a tela que não se aplica ao cliente.
- Um nível de mercado por vez (B11).

## O que entra

| Detalhe | Conteúdo | Quando |
|---|---|---|
| Achados que mudam a decisão / Como ler | Abertura explícita com achados pertinentes e tela de referência. Distinguir dado, estimativa e premissa: uma faixa depende da cadeia de premissas, não é prova, e é substituída por medição identificada. Método, hierarquia das fontes e limitações, com frameworks de fonte primária quando usados | Sempre; após a capa |
| Setor | Global, nacional, dinâmica de preços e consumo final; subsegmento do cliente (caracterização técnica, tamanho com a marca "estimativa" quando não oficial, geografia da produção ou do consumo) | Sempre |
| Regras e dinheiro | Como o mercado compra e quem paga; regulação e o que pode ser divulgado; origem do recurso | Setor regulado ou compra pública |
| Capacidade e meta | Origem da receita; capacidade demonstrada (reuniões × conversão, contratos, carteira); cenários de 12 meses do SOM com premissa por cenário; meta ano a ano | Sempre |
| Mercados secundários | Cobrir cada mercado declarado com peso proporcional à decisão: quem paga, referência de preço, dimensão e concorrência sustentadas. Comparar pelos mesmos critérios; prioridade e papéis em 08 · Onde concentrar | Mais de um mercado declarado |
| Público e jornada de compra | Personas em detalhe e comportamento no ponto de venda ou no funil digital; jornada de compra em etapas (reconhecimento, critérios, pesquisa, validação, negociação, aprovação, recorrência) com a intervenção de comunicação de cada uma; calendário e sazonalidade do setor | Sempre que houver dado |
| Tendências | Cada tendência com título, parágrafo com fonte e a implicação para o cliente. Escolher as do nicho: premiumização, conveniência, sustentabilidade, canal digital, ativo subutilizado, digitalização do comprador B2B | Sempre que houver fonte |
| Preço e margem | Tabela de preços por praça, rede ou player (mínimo de 5 linhas), leitura da banda de preço, margem do cliente e princípio de política de preço | Sempre que houver preço e margem |
| Oferta | Formatos e pacotes do mercado contra os do cliente, hipóteses para validar em campo e testes A/B propostos | Bem físico, plano ou pacote de serviço |
| Concorrentes | Identidade, pertinência, oferta, fonte/data e limites de cada concorrente confirmado; substituto somente quando real. Sem evidência, sinais, onde coletar e responsável | Conforme investigação |
| Cruzamentos do SWOT (TOWS) | Atacar, defender, corrigir e evitar, ligando os quadrantes a decisões e próximos passos; sinal pendente continua pendente | Sempre; fora do deck |
| Pontos de melhoria, soluções e estrutura ideal | Achado com fonte e efeito, solução proporcional à evidência, estrutura necessária e condição de revisão. Traduzir os códigos da ficha em linguagem de negócio | Última seção do detalhe |

## Fora do detalhe

Forecast e calendário de conteúdo são da Semana 3. CRM, playbook comercial e cadência são da Semana 4. A apresentação institucional e a produção de conteúdo são entregáveis da Semana 5, só quando o contrato os prevê.
