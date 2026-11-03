# Estruturação Estratégica (EE) · Trieme & Co

Consultor: {{CONSULTOR}}, {{CARGO}}.

## O que é
Produto consultivo de 5 encontros ao vivo de cerca de 1h30, conduzido por um consultor só:
Kickoff · Pesquisa de Mercado · Diagnóstico de Marketing · Diagnóstico Comercial ·
Planejamento Estratégico + Entregáveis. Cada encontro gera um HTML apresentado ao vivo
e um DOCX de consulta. Depois, o encerramento (ou o Handoff, se o cliente contratar o Executar).

## Onde está cada coisa
- Guias, modelos, scripts e índice de fontes por setor: no pacote `ee-trieme`, instalado como
  plugin. Os guias são chamados com `/ee-trieme:<guia>`. Nada do pacote é copiado nem editado aqui.
- Clientes/Clientes.md: lista dos clientes, etapa e próxima data.
- Clientes/<N>. <Nome>/<Nome>.md: a ficha do cliente. É a fonte de contrato, dados,
  números, meta, Direcionamento, Restrição, Pontos/soluções/estrutura, Decisões por encontro e pendências. Esse é o Fio: estado vigente com histórico e fonte. Leia Status para navegar; as seções novas entram quando o guia da etapa pedir.
- Clientes/<N>. <Nome>/_ensaios-internos/registro.md: medição de uso e ensaios com o cliente
  simulado. Interno; só o guia que o pedir lê.
- Clientes/<N>. <Nome>/Nota de preparo - <Nome>.md: interna, nunca vai ao cliente.
- _arquivo/: morto. Não ler.

## Por onde começar
- Dizer "próximo passo da <Nome>": o guia-mãe lê a seção Status da ficha e decide.
- Cliente novo: `/ee-trieme:novo-cliente <Nome>`, depois `/ee-trieme:passagem-venda <Nome>`.
- Qualquer semana: ler a base, o esqueleto da semana e as seções da ficha que o guia pedir. Só então produzir.
- Landing page contratada: `/ee-trieme:landing-page <Nome>` retoma a criação ou revisão; a decisão é registrada na S1 e a primeira versão nasce entre S3 e S4. Conexão ausente: `/ee-trieme:configurar-stitch`.

## Regras que valem sempre (a regra completa mora no ponteiro)
1. Fontes que divergem viram pergunta ao cliente e linha na ficha: nunca escolher um lado em
   silêncio. Até a resposta, vale: contrato e documentos oficiais, depois o que o cliente
   disse na reunião, depois o handoff da venda. Casa: base B0.
2. Nada de presumir: sobre o cliente, só o que está nos insumos ou foi dito. O resto vira
   pergunta ou pendência. Casa: `padrao/estilo-de-escrita.md` e base B1.
3. Todo número tem dono, unidade e fonte. Os números saem da ficha: se um número mudar,
   corrigir primeiro na ficha e depois no deck. Casa: base B2.
4. Uma ideia por tela, e o esqueleto da semana é o teto de telas. O detalhe vai para o DOCX. Casa: base B4 e B5.
5. Simples e sofisticado: se a frase serviria no site do concorrente, reescrever com o fato
   do cliente. Casa: `padrao/estilo-de-escrita.md`.
6. Sem travessão, sem nome de pessoa da equipe do cliente (usar o cargo; dono de ação no Mapa de Ações: cargo com o nome entre parênteses), sem nome de
   fornecedor como recomendação sem fundamento. Ferramenta atual pode ser citada como fato; opções e preços vão em comparação separada e datada. Casa: `padrao/estilo-de-escrita.md` e base B10.
7. Só dizer "pronto" ou "enviado" com o arquivo na pasta e a data. Casa: base B12.
8. Nada vai para o cliente sem a revisão do consultor. Casa: base B10.
9. O cliente simulado (ensaio e mesa) é interno: nunca aparece no material nem substitui a
   validação ao vivo. Casa: `padrao/rubrica-cliente.md`.
10. Script temporário só em `EE/.claude/tmp/`, apagado no fim. Nunca na pasta do usuário nem no pacote.
