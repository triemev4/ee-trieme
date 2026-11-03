---
name: kick-off
description: "Use quando o consultor pedir a Semana 1 da Estruturação Estratégica, o Kickoff de um cliente: o deck da reunião de abertura e a nota de preparo. Use quando ele trouxer a gravação ou as anotações do Kickoff para registrar o que foi dito. Use quando pedir o Registro do Kickoff ou a mensagem pós-Kickoff."
model: sonnet
argument-hint: "[Nome do cliente]"
---

# Kickoff · Semana 1

Sem o nome, pergunte. `<pasta>` = `EE/Clientes/<N>. <Nome>`; `<slug>` = o nome em minúsculas, sem acento, com hífens. O que vai em cada tela está no esqueleto da semana; aqui ficam os passos e os comandos.

**O que a semana entrega:** antes da reunião, o deck e a nota de preparo; depois, a ficha com dados mínimos, meta, direcionamento inicial e restrição como hipótese, o Registro do Kickoff e a mensagem. A matriz Contrato da ficha define o que será entregue; o deck não promete itens fora dela.

**Kickoff já realizado** (há transcrição, anotações ou gravação do Kickoff em `0. Inputs e Transcrições/`, ou "Kickoff realizado" marcado na Status): vá direto ao passo 6. A nota de preparo serviria para conduzir uma reunião que já passou; o que ela guardaria vai para a ficha (pessoas e papéis em Persona do cliente, por função; triagem de formato e maturidade no cabeçalho; insumos que faltam em Pendências).

## 1. Ler
- `${CLAUDE_PLUGIN_ROOT}/skills/estruturacao-estrategica/base-de-todo-encontro.md` e `${CLAUDE_PLUGIN_ROOT}/skills/estruturacao-estrategica/esqueleto/semana-1-kickoff.md`.
- Da ficha:
  ```
  python "${CLAUDE_PLUGIN_ROOT}/scripts/ler_ficha.py" "<pasta>/<Nome>.md" --cabecalho --secoes "Status, Contrato, Dados mínimos, Landing page"
  ```
- Tudo de `0. Inputs e Transcrições/`, por data, pelo `_texto/` (rode a extração se faltar ou se chegou insumo novo):
  ```
  python "${CLAUDE_PLUGIN_ROOT}/scripts/extrair_insumos.py" "<pasta>/0. Inputs e Transcrições"
  ```
- Se houver Growth Class, leia sua transcrição junto com a call de venda. Leve fatos de ambas para a tela "O que já mapeamos" e para a nota de preparo, preservando fonte e tempo. No Kickoff, confirme se um dado conhecido mudou; não refaça a pergunta já respondida.
- `padrao/formatos-de-negocio.md` e `padrao/mapa-de-pessoas.md`. Sem ficha, chame `/ee-trieme:novo-cliente` e pare.

**Pronto quando:** você sabe o que foi vendido, o que o cliente já disse na venda e o que falta saber.

## 2. Perguntar uma vez
Numa rodada só, cada pergunta com a resposta recomendada: divergência entre fontes (B0), promessa da venda a confirmar com o closer, decisor ausente. Fato, você busca. A call e a Growth Class, quando existe, já respondem parte da pauta: pergunte apenas o que falta ou o que precisa de confirmação por estar divergente ou desatualizado.

Inclua a decisão sobre protótipo de LP pelo passo 1 de `/ee-trieme:landing-page <Nome>`: pergunta ao consultor, resposta na ficha e conferência com o contrato. Com LP, colete apenas materiais faltantes e prepare a conexão antes da S3; produção visual vem entre S3 e S4. Ficha antiga ganha só a seção necessária, sem migração em lote.

## 3. Produzir
A nota de preparo (`${CLAUDE_PLUGIN_ROOT}/modelos/nota-preparo.md`) vem primeiro, porque as perguntas saem dela. Depois, `<pasta>/1. Kick-Off/_fonte/conteudo.json` (copiado de `${CLAUDE_PLUGIN_ROOT}/skills/kick-off/gerador/modelo-conteudo.json`, se ainda não existir): troque cada "PREENCHER: ..." e apague o campo que a venda não alimenta. Gere:
```
python "${CLAUDE_PLUGIN_ROOT}/skills/kick-off/gerador/gerar_kickoff.py" "<pasta>/1. Kick-Off/_fonte/conteudo.json" "<pasta>/1. Kick-Off" --consultor "${user_config.consultor_nome}" --cargo "${user_config.consultor_cargo}" --foto "EE/foto-consultor.jpg"
```
O DOCX do deck é só para uso interno e sai com `--docx`.

**Pronto quando:** o roteiro soma 1h30 e as perguntas ficam entre 20 e 28.

## 4. Conferir
A passada final por `padrao/estilo-de-escrita.md` e os scripts. O `--visual` abre cada tela em 1280x720: texto estourando e fonte pequena são erro; texto demais e tela alta, aviso.
```
python "${CLAUDE_PLUGIN_ROOT}/scripts/verificar_entrega.py" "<pasta>/1. Kick-Off/kickoff-<slug>.html" --semana 1 --cliente "<Nome>" --ficha "<pasta>/<Nome>.md" --visual
python "${CLAUDE_PLUGIN_ROOT}/scripts/checar_fontes.py" "<pasta>/1. Kick-Off/kickoff-<slug>.html" --sem-numeros
```

## 5. Decisão do consultor
Ele lê o deck e a nota, confirma a triagem de formato (hipótese) e ajusta a condução.

## 6. Depois da reunião
Se o Kickoff já ocorreu e a decisão da LP ainda não está registrada, resolva-a com o consultor pelo passo 1 de `landing-page`, sem recriar a pauta da reunião.

1. **Transcrição.** Só gravação: `ffmpeg` extrai o áudio em 16 kHz mono e `faster-whisper` (modelo `small`, CPU `int8`, `language="pt"`, `vad_filter=True`) transcreve. Com o texto em mãos, siga o passo 1 de `${CLAUDE_PLUGIN_ROOT}/skills/estruturacao-estrategica/rotina-pos-encontro.md` com `--semana 1`.
2. **Ficha, seção a seção:**
   - Contrato: promessas da venda que o cliente confirmou.
   - Dados mínimos: classe, valor, fonte e minuto, ou "pendente · dono · data"; % confirmado e % com pendência (esqueleto, "Portão de saída").
   - Números-fonte: os números novos, com id e "decisivo".
   - Meta, condições e efeitos indesejados: como o esqueleto pede, em "Artefatos". Abra a linha de Meta ao longo com a data do Kickoff, distinguindo fala, fonte/ID e leitura do consultor.
   - Direcionamento: registre em uma linha o modelo do negócio, o objetivo do marketing, a fala sobre volume ou qualidade, o modo inicial como hipótese com sua evidência e o que o cliente disse que fica fora desta fase. Separe fala do cliente de leitura do consultor.
   - Restrição: abra o registro com situação `hipótese`, sem apresentar diagnóstico como comprovado.
   - Decisões por encontro: registre `Kickoff · dd/mm/aaaa` e as decisões do cliente separadas das recomendações do consultor.
   - Dados mínimos e Números-fonte: `nunca investiu` e `sem teto` são respostas textuais válidas. Preserve essas expressões como texto; não as converta em zero, verba disponível ou estimativa.
   - Glossário (as grafias da transcrição), Persona do cliente (complete a da passagem da venda, com a fonte em cada linha), Status e Pendências.
3. **Nota de preparo**, quando existir: marque o radar de insumos e atualize Pessoas e triagem. Arquivo que faltar é cobrado; ao chegar, rode a análise de `formatos-de-negocio.md` e grave em Números-fonte.
4. **Registro do Kickoff.** Copie `modelo-registro.json` (pasta do gerador) para `<pasta>/1. Kick-Off/_fonte/registro.json`, preencha só com o que foi dito, confira que nenhum `PREENCHER` sobrou e gere:
   ```
   python "${CLAUDE_PLUGIN_ROOT}/skills/kick-off/gerador/gerar_dossie.py" "<pasta>/1. Kick-Off/_fonte/registro.json" "<pasta>/1. Kick-Off" --consultor "${user_config.consultor_nome}" --cargo "${user_config.consultor_cargo}"
   ```
5. **Mensagem** pelo bloco da Semana 1 de `padrao/mensagens-pos-encontro.md`: a dor nas palavras do cliente, o critério de sucesso para o "de acordo", pendências com dono e data, gancho com a data da Semana 2.
6. Feche os passos 4 a 6 da rotina pós-encontro (mensagem salva, Medição, Status).

**Pronto quando:** nenhum dado "Bloqueia" fica sem resposta ou sem pendência datada antes da Semana 2, o Registro gerou sem `PREENCHER` e a mensagem está salva.

## 7. Decisão do consultor de enviar
HTML, Registro e mensagem; a nota de preparo fica interna. Kickoff feito antes deste fluxo não tem HTML da pauta: vão só o Registro e a mensagem.

## Perguntas boas e ruins
- **Dado solto:** "Quem cuida do site? Tem Pixel?" rende sim ou não. Pergunte: "Quando você apresenta o produto, que parte prende a atenção e que parte você sente que não convence?"
- **Repete o card:** "Quais canais a empresa tem hoje?" depois do card de ativos digitais. Vá um nível abaixo: "Depois de te ouvir, onde o cliente busca mais sobre vocês, e o que encontra lá?"
- **Pressupõe:** "Você topa ser o rosto da marca?" Pergunte pelo que existe: "Como você vê a presença da marca e a sua nas redes, e até onde gostaria de chegar?"
