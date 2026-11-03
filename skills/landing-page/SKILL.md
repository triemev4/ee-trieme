---
name: landing-page
description: "Produz, retoma ou revisa o protótipo de landing page de um cliente da EE pelo Stitch. Acionado entre as Semanas 3 e 4 quando há LP no escopo; valida alterações comerciais na Semana 4 e confere a entrega na Semana 5."
---

# Landing page

Uma entrada para toda a produção da LP. `<cliente>` é a pasta em `EE/Clientes/`; `<entrega>` é `<cliente>/5. Planejamento Estratégico + Entregáveis`; `<trabalho>` é `<entrega>/_fonte/landing-page`. O arquivo entregue do protótipo é `<entrega>/Entregaveis/landing-page-<slug>.html`, com recursos locais ao lado. Criar a LP antes da S5 não muda esses caminhos.

## 1. Decisão e próximo trabalho

Leia a ficha por seção:
```
python "${CLAUDE_PLUGIN_ROOT}/scripts/ler_ficha.py" "<cliente>/<Nome>.md" --secoes "Contrato, Landing page, Status, Pendências, Direcionamento, Restrição, Pontos, Decisões por encontro, Contexto do consultor"
```

Na S1, pergunte ao consultor: **"Esta EE inclui entrega de protótipo de landing page?"** Recomende conforme o contrato; registre resposta, data e referência à linha da matriz na seção Landing page (`modelos/ficha-cliente.md`). Sem resposta, não presuma não. Resposta divergente da matriz exige resolver o escopo; não cancela obrigação. Confirmação do consultor não cria aditivo por si só.

- Fora do escopo: registre a decisão e retorne à semana. Não configure Stitch nem faça pesquisa específica.
- Matriz com aceite escrito de briefing: produza pesquisa, copy e direção no nível combinado e retorne à semana; geração de protótipo só entra se o escopo for alterado. Identifique a entrega como briefing e grave o arquivo final em `<entrega>/Entregaveis/briefing-landing-page-<slug>.md`.
- Dentro do escopo, antes do fim da S3: peça somente os materiais faltantes, com dono e prazo; registre público/oferta ainda provisórios. Retorne à semana.
- S3 encerrada: prepare e gere a primeira versão.
- Retomada: leia a seção LP e os arquivos existentes; continue do primeiro resultado incompleto. Reutilize projeto e telas registrados.
- Depois da S4: confira as decisões comerciais contra briefing/copy. Alteração de oferta, prova, prazo, ação ou qualificação muda a fase para `revisão necessária`; atualize a fonte na ficha, depois os derivados e a página.
- S5: valide a revisão atual e o aceite; encaminhe o link para o plano final.

Fases internas: `decisão pendente`, `insumos`, `preparo`, `protótipo`, `revisão necessária`, `conferida`. Não substituem os status contratuais da matriz. Ausência do MCP limita a geração; os outros trabalhos e encontros continuam. Pendência interna não vira "pendência do cliente" no encerramento.

## 2. Briefing e copy

Leia [pesquisa-e-copy.md](references/pesquisa-e-copy.md). Use insumos limpos, ICP, Posicionamento (PUV em decks anteriores) e provas da S2, auditoria/canais da S3 e decisões vigentes da S4. O fundamento do posicionamento precisa existir antes da LP mesmo quando o Manual de Copy não faz parte do contrato; o manual formaliza um fundamento sustentado, não o inaugura. Contratante da EE e comprador da oferta são pessoas distintas. Reaproveite a pesquisa existente; busque apenas o que falta para escolher linguagem, composição e prova. Você coleta os links e as capturas de 1440 e 390 px da régua do nicho (concorrentes da S2 com site, completados até 3 com sites do nicho); o designer só lê.

Grave `<trabalho>/briefing.md` e `<trabalho>/copy.json`. Para protótipo com S3 encerrada e direção ainda por propor, leia [delegacao-design.md](references/delegacao-design.md) e chame `ee-trieme:designer-lp-stitch` no modo `direcao`, passando a raiz resolvida `${CLAUDE_PLUGIN_ROOT}` e os caminhos absolutos. O especialista escreve `<trabalho>/DESIGN.md`, com a régua e a Assinatura; copy que trava a ideia é ajustada antes da validação. Direção já validada é reaproveitada; entrega somente de briefing permanece com o coordenador, no nível contratado.

O consultor valida objetivo, copy e direção na mesma rodada de perguntas da etapa; decisões já registradas não são perguntadas novamente. Sem prova para uma promessa, reescreva dentro do sustentado. Item indispensável ausente vira pendência, não uma afirmação inventada.

**Pronto quando:** cada seção tem função, texto e fundamento; a ação principal e o pós-clique estão definidos; marca, referências, lacunas e Assinatura estão registradas.

## 3. Gerar e refinar no Stitch

Confirme uma chamada autenticada de leitura ao MCP. Sem conexão, use `/ee-trieme:configurar-stitch`; retorne ao ponto interrompido. O núcleo deste guia é autossuficiente: skills globais do Stitch podem ajudar, mas não são requisito.

Acione ou retome `ee-trieme:designer-lp-stitch` no modo `prototipo`, conforme [delegacao-design.md](references/delegacao-design.md). Envie arquivos atuais, decisões validadas, pastas autorizadas e limite de refinamento. O especialista usa [stitch-e-aceite.md](references/stitch-e-aceite.md) para gerar, editar, baixar e inspecionar; devolve o HTML local, recursos, IDs, revisão e evidências. Confira os arquivos devolvidos e as pendências antes do aceite. Sem suporte a subagentes, execute o mesmo papel pelo caminho alternativo documentado, sem criar outro método.

**Pronto quando:** há uma página navegável que preserva a copy e pode ser inspecionada localmente. Falha, timeout ou cota são registrados; consulte o projeto antes de repetir geração e evite laço de tentativas.

## 4. Conferir a revisão

Leia Aceite em [stitch-e-aceite.md](references/stitch-e-aceite.md). Confira as evidências do especialista e examine o HTML entregue; complete testes ausentes e repita os afetados por correções. Acrescente a revisão de texto, estratégia e percurso em `<trabalho>/revisao.md`, preservando achados e larguras do especialista. Faça o teste do comprador com o ICP da S2; simulação não prova conversão. A revisão do consultor é obrigatória; a autoinspeção do designer não é revisão independente nem aceite humano.

Execute a conferência mecânica e registre as dependências da revisão:
```
python "${CLAUDE_PLUGIN_ROOT}/scripts/conferir_landing_page.py" verificar "<entrega>/Entregaveis/landing-page-<slug>.html" --copy "<trabalho>/copy.json" --dependencia "<trabalho>/briefing.md" --dependencia "<trabalho>/DESIGN.md" --dependencia "<trabalho>/revisao.md" --dependencia "<trabalho>/stitch.json" --comprovante "<trabalho>/conferencia.json"
```
O verificador acha sozinho os CSS, JavaScript, imagens e fontes locais que o HTML e os CSS citam, e põe todos no comprovante; arquivo ausente ou fora da pasta da LP é erro. Use `--dependencia` só para os arquivos da revisão, como no comando, e para arquivo que a página usa e o HTML não cita. Avisos exigem decisão no registro editorial; erro impede conferência. O script não aprova estratégia, estética, veracidade nem funcionamento do formulário.

Antes de entregar ou reaproveitar uma revisão:
```
python "${CLAUDE_PLUGIN_ROOT}/scripts/conferir_landing_page.py" validar-revisao "<trabalho>/conferencia.json" --sha256-esperado "<SHA-256 da revisão aprovada na ficha>"
```

Antes da primeira aprovação, omita `--sha256-esperado` apenas para conferir integridade técnica. Para entrega/reuso aprovado, exija a decisão humana e seu hash na ficha. Mudança de arquivo invalida a conferência; regenerar o comprovante não herda aprovação anterior. Nova decisão relevante da ficha exige reconciliar o briefing mesmo que o arquivo ainda não tenha mudado. Faça nova revisão depois da correção; não atualize apenas o hash para encobrir mudança.

## 5. Registrar e devolver à EE

Na ficha, atualize fase interna, caminho e hash SHA-256 do comprovante, validação comercial e decisão do consultor sobre aquela revisão. Nova conferência deixa a aprovação anterior pendente até o consultor confirmar o novo hash. Na matriz, mantenha o status real do entregável. Horas, chamadas, refinamentos e retrabalho vão ao registro interno já existente. Envio é decisão do consultor e usa o arquivo conferido.

Retorne ao guia da semana com: arquivo, revisão, o que depende de implantação e pendências com responsável/data. Se o escopo for somente briefing, siga o aceite escrito registrado na matriz; não o apresente como protótipo concluído.
