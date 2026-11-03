# Esqueleto · Semana 4 · Diagnóstico Comercial

Base: `../base-de-todo-encontro.md`. Telas, fonte, amarração, trava, plano e fechamento seguem a base; este arquivo diz só o que é desta semana.

**Pergunta do encontro:** o comercial converte a demanda que existe? Onde perde, por quê, e como deve funcionar?
**Papel na EE:** fechar o ciclo de diagnóstico. A hipótese de restrição é sustentada, revista ou mantida inconclusiva segundo evidência e teste decisivo.
**Guia da etapa:** `skills/diagnostico-comercial/SKILL.md` (comandos). Fluxos e kanban: `skills/diagnostico-comercial/fluxo-comercial.md`. Layout: `moldes/semana-4.html`, preenchido por `scripts/preencher_molde.py`.

## Insumos

1. Fio do projeto vigente e histórico, Direcionamento e Decisões da ficha; Semanas 2 e 3: ICP, posicionamento, forecast e Próximos passos. Preserve a origem e revise recomendações quando a evidência mudar; registre a substituição no Fio.
2. Transcrições, das mais recentes às mais antigas: como a venda acontece, quem decide, ferramentas, objeções, prazo e dependências de implantação.
3. **Cliente oculto**, padrão com dois concorrentes nomeados e protocolo registrado. Declare realizado válido, parcial, inválido ou ausente; teste contaminado não produz score. Preserve evidência independente do formulário e planeje repetição quando necessário.
4. Números do cliente: seção Números-fonte da ficha, com "decisivo = sim" nos que entram na trava e nos Horizontes. Taxa por etapa, motivos de perda, recompra, Pareto e tempo do primeiro contato saem das análises de `padrao/formatos-de-negocio.md` (seção 8), registradas na ficha. Sem arquivo do cliente não há número: a tela mostra o que foi observado e a pendência vai para o plano.

## Sequência de telas (14)

| # | Tela (eyebrow) | PSE | Componente | Regra de conteúdo |
|---|---|---|---|---|
| 1 | Ponte entre encontros | · | `.bridge-track` + 2 colunas + `.pausa` | Recap vigente da S3 e pauta real |
| 2 | Capa | · | hero + `.v4-mark` | Fatos conhecidos e seu estado |
| 3 | Distância até a meta | Situar | `.grid` + `.cell` + estado | Objetivo, período e base comparáveis; sem meta ou base, pergunta e teste, sem lacuna numérica inventada |
| 4 | Cliente oculto | P → S → E | prints + `.rtable.dossie` + fluxo ideal | Protocolo, validade e limite da evidência; comparação padrão com dois concorrentes; sem score em teste contaminado |
| 5 | Processo atual | P → S | `.processo-raias` + `.processo-textual` + `.rtable` + `ol.tasks` | Trabalho real: entrada, saída, papel, espera, passagem e dores com evidência; imagem local com alternativa textual |
| 6 | Escada do time | E | `ol.escada` | Necessidade, papel, decisão atual e condição para avançar; redistribuição ou contratação conforme capacidade e competência |
| 7 | Horizontes | E | régua e barras de intensidade | Prazos da base, ligação entre horizontes, pilares pertinentes e métrica testável ou condição de medição |
| 8 | Indicadores e rotinas | E | `.rtable` | O que medir, como, rotina e responsável; metas propostas identificadas |
| 9 | Funil | E | pirâmide + fluxo | Etapas do formato e critério de passagem; dado do cliente ou a medir |
| 10 | Playbook de qualificação | S | `.rtable` + ações | Critérios por etapa e passagem entre papéis. A/B/C proposto com fundamento; pontuação calibrada somente após teste real |
| 11 | CRM e ferramentas | E | kanban + automações + stack | Caminho e manutenção dos dados demonstrados ou condicionados, com alternativa viável; CRM como capacidade |
| 12 | Perdas e base | P → S | motivos + base + reativação | Percentuais só com arquivo; motivos observados permanecem qualitativos |
| 13 | Pós-venda e implantação | P → S → E | fluxo + `.rtable` | Dono, prazo, dependência, teste e contingência; reunião de Processos separada só por aditivo |
| 14 | Próximos passos | Fechar | `.dobro` + `.corda` + `.ac` + `.own` + `.pausa` + `.gancho` | Estado da hipótese, teste do dobro e limite de capacidade; uma a cinco ações, uma prioridade primeira, sem trilhas no fecho |

## Regras da semana

- **Apresentação:** visual indicado quando houver achado. Sem achado próprio, condense pelo B4: lacuna uma vez, pilar coberto no detalhe. Critérios e responsáveis propostos seguem B8, sem campo em branco.
- **Horizontes (tela 7):**
  - confirmam os prazos padrão da tabela da base e só mudam com dado do cliente registrado na ficha;
  - H2 e H3 abrem com uma frase de ligação ao horizonte anterior;
  - os mesmos domínios (ex.: comercial e CRM, marketing e autoridade, tecnologia) aparecem desde o H1 e evoluem nos três: implementar, escalar, consolidar;
  - as ações dos planos das Semanas 2 e 3 entram nos pilares, com "vem da Semana N"; a que sai leva o motivo;
  - barras ascendentes por intensidade (não por R$ nem por dias), ícone temático por horizonte, cor que aprofunda de H1 a H3; recap de uma linha por horizonte com a métrica de sucesso, cada uma testável.
- **SLA:** toda solução que prescreve tempo de resposta traz número ideal e número máximo, marcados como meta proposta a validar com o histórico do cliente. Referência: Lead Response Management Study (Oldroyd, MIT e InsideSales.com): responder em até 5 minutos torna o contato cerca de 100 vezes mais provável do que esperar 30. Citar com o ano da fonte aberta.
- **Papéis:** a escada parte da necessidade e da capacidade verificadas. Pode propor redistribuição ou contratação imediata quando necessária, com recurso, dono e alternativa explícitos. CHA completo vai para o DOCX.
- **Termo técnico** (raias, níveis de gestão, Horizontes de Crescimento, SDR, closer, MQL, SAL, SQL) ganha `.explicador` de uma frase na primeira vez, sem autor.
- **Ferramentas necessárias:** só ferramenta real que o cliente usa, com o CRM sempre como capacidade (B10). Ferramenta sem valor confirmado vira uma linha de observação.
- **Operação dos dados do CRM:** para os dados que sustentam qualificação, retomada, carteira ou indicadores, explicite origem, forma de entrada/atualização, cargo responsável, frequência e uso. Diferencie o que já funciona, o que é proposta e o que precisa de teste. API, acesso e trabalho de manutenção não são presumidos: confronte-os com os sistemas e a disponibilidade de quem opera. Quando a integração não estiver demonstrada, proponha teste de atualização com resultado observável e alternativa compatível com os acessos e a carga conhecidos. Sem alternativa viável, mantenha o uso dependente condicionado, sem prometer atualização automática ou ausência de digitação. O caminho mínimo aparece no CRM (tela 11); dependências, teste e contingência na implantação (tela 13), com detalhe no DOCX quando necessário. Planejar a verificação não significa executar a integração durante a EE.

## Modulação

- **Formato:** o que muda por formato (cliente oculto, processo, dores, funil, papéis, réguas, stack) está em `padrao/formatos-de-negocio.md`, seção 6. As telas são as mesmas.
- **Maturidade baixa:** H1 de organização mínima (CRM, roteiro, retomada). **Alta:** governança, pontuação calibrada, margem.
- **Perfil do decisor** (`padrao/mapa-de-pessoas.md`): Planejador pede rotina, riscos e controle. Executor pede o "quem faz o quê" cedo.

## Processo e próximos passos

O processo descreve etapas, entradas, saídas, cargos, esperas e passagens observados. A quantidade de dores orienta o recorte visual; fatos não são descartados para cumprir uma quantidade. O desenho usa `desenhar_processo.py` com `lanes`, `nodes` e `flows` válidos. A S4 incorpora arquivo local por `data-img="tela-05.imagem"`, com texto alternativo; sem imagem, `ol.processo-textual` mantém os passos. A explicação `.processo-alternativa` continua disponível. Imagem ou alternativa devem explicar o processo, além de existir no HTML.

No slot `tela-14`, use `{titulo, trava, acoes: [{acao, dono, prazo, comece_aqui}], pausa, gancho, estado, dobro: [{pergunta, resposta, evidencia}], corda}`. De uma a cinco ações; uma única prioritária, primeira. `.own` mantém dono e prazo; o fecho não usa trilhas de horizonte.

O teste do dobro admite **sim, não ou inconclusivo**. Atendimento, entrega, gestão e caixa são roteiro inicial, não obrigação de preencher respostas sem evidência. Registre pergunta, resposta sustentada ou ausência, evidência e teste decisivo. A `.corda` informa capacidade conhecida ou limite a medir; ausência de número não autoriza presumir folga. S4 pode fechar com hipótese de trabalho. A decisão de revisão entra no marco proposto ou antes, se o gargalo ou a evidência mudar.

## Pronto quando

Checklist B12, mais:
- Cliente oculto tem estado e protocolo; quando ausente, parcial ou inválido, seus limites e próximo teste estão explícitos.
- Processo e escada refletem trabalho e capacidade, sem contratação ou automação presumida.
- Horizontes incorporam decisões vigentes das semanas anteriores; CRM, funil, pós-venda e implantação mantêm condições, dono e prazo.
- Próximos passos preserva hipótese/evidência, teste do dobro, corda e uma prioridade executável com validação e gancho.
