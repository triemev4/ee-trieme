# Delegação ao designer da LP

O coordenador é o assistente que executa `landing-page`. O especialista é `agents/designer-lp-stitch.md`. As referências de pesquisa e Stitch continuam sendo a fonte do método. Esta página define apenas a passagem de trabalho.

## Quando chamar

- `direcao`: LP no escopo, S3 encerrada, briefing e copy preparados, direção ainda por propor. O especialista escreve `DESIGN.md` antes da rodada consolidada de validação do consultor. Não depende do MCP.
- `prototipo`: briefing, copy e direção validados, geração ou correção visual necessária. Encaminhe a decisão já existente, sem repetir a pergunta. Se houver mudança comercial, o coordenador reconcilia ficha/briefing/copy antes da delegação.
- Fora do escopo, decisão ausente, S3 ainda aberta, entrega somente de briefing ou instalação do MCP: o coordenador segue o ramo correspondente do guia; não inicia geração pelo especialista.

## Tarefa enviada

Passe caminhos absolutos e este contexto curto; arquivos são lidos pelo especialista, não copiados por inteiro na conversa:

- Raiz do pacote; modo; cliente/slug; caminho de `briefing.md`, `copy.json`, `DESIGN.md` (existente ou a criar), links e capturas da régua do nicho e ativos autorizados. Referências podem estar no briefing; nenhum arquivo adicional é obrigatório só para preencher o protocolo.
- Objetivo, comprador, ação, pós-clique e limites da oferta; fonte/data das decisões validadas ou indicação explícita de cenário fictício autorizado. Não declare aprovação humana em um teste sintético.
- Pastas exatas de trabalho e entrega. `stitch.json` e `revisao.md`, quando existentes; projeto/tela atuais; defeito ou mudança que motivou a retomada.
- Liberdade visual dentro da direção; o que exige voltar ao coordenador. Limite de refinamento conforme o caso: no piloto, uma geração e até duas edições focadas; em retomada, não há nova geração por padrão.
- Ferramentas disponíveis para Stitch e navegador; restrições de rede/arquivos; comando de conferência mecânica já resolvido se for útil durante a execução.

Não envie transcrições ou ficha inteira ao Stitch. Para decisões omitidas do briefing, o coordenador fornece o recorte necessário com origem. Contas, provas e alegações de outras empresas não viram fatos do cliente.

## Acionamento por ambiente

**Claude Code:** use Agent com `subagent_type: "ee-trieme:designer-lp-stitch"`, sem passar `model`: o agente roda no modelo do próprio arquivo (opus), porque julga o visual. O plugin descobre o arquivo em `agents/`. Resolva a raiz e os caminhos na skill antes da chamada; o agente não depende de expansão de variável do plugin no próprio corpo. Pode retomar a mesma execução para ajustes, sempre relendo os arquivos atuais. Uma nova sessão retoma pelos arquivos.

O agente herda as ferramentas permitidas da sessão, incluindo MCP; `disallowedTools: Agent` evita delegações aninhadas. A lista de ferramentas não é fixada por nome de navegador, pois consultores usam configurações diferentes. Isso não amplia permissões nem cria uma barreira de escrita por pasta: os limites de arquivos são instruções do papel, que o coordenador também confere. O MCP é configurado pela skill própria, na sessão principal; credenciais não são passadas na tarefa.

**Sem subagente:** o principal faz o mesmo papel e registra esse modo em `revisao.md`.

## Retorno e retomada

O especialista devolve, de forma curta:

1. Modo e resultado: `direcao proposta`, `prototipo inspecionado`, `revisao pendente` ou `bloqueado`, sem alterar a fase oficial da ficha.
2. Caminhos escritos, IDs remotos e telas utilizadas, quando houver.
3. Escolhas visuais e motivos; quais problemas foram corrigidos.
4. Evidências: larguras, capturas, interações e comandos executados; limites do que não foi verificado.
5. Pendências/propostas para o coordenador, próxima ação e contagem de gerações/edições. Tempo automatizado não é hora humana do consultor.

`revisao.md` preserva os achados do especialista e recebe a conferência estratégica do coordenador. Falta de copy/direção validada retorna como pendência; não é resolvida inventando aprovação. Falta de MCP no modo protótipo volta à configuração; timeout consulta IDs antes de repetir; indisponibilidade de navegador deixa inspeção pendente. O especialista nunca marca a LP como entregue.

Depois do retorno, o coordenador confere os arquivos, inclusive textos acrescentados pelo Stitch, resolve as pendências e segue os passos 4 e 5 de `landing-page`. Ele gera o comprovante final e solicita aceite daquela revisão ao consultor. Não execute os dois sobre os mesmos arquivos ao mesmo tempo.
