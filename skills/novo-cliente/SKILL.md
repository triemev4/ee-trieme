---
name: novo-cliente
description: 'Use quando o consultor pedir "novo cliente", "novo cliente <Nome>", "cria um cliente novo", "abrir o cliente X" ou "criar a pasta do cliente". Guia só de comando: roda por /ee-trieme:novo-cliente.'
disable-model-invocation: true
model: sonnet
argument-hint: "[Nome do cliente]"
---

# Novo cliente

`/ee-trieme:novo-cliente <Nome>`. Se o nome não vier em `$ARGUMENTS`, pergunte antes de qualquer ação. Cliente fictício de teste vale como cliente comum.

## O que gera

```
EE/Clientes/<N>. <Nome>/
  <Nome>.md                          a ficha
  Nota de preparo - <Nome>.md
  _ensaios-internos/registro.md      medição e ensaios (interno)
  0. Inputs e Transcrições/
  1. Kick-Off/_fonte/                conteudo.json e registro.json
  2. Pesquisa de Mercado/_fonte/
  3. Diagnóstico de Marketing/
  4. Diagnóstico Comercial/
  5. Planejamento Estratégico + Entregáveis/Entregaveis/
  Encerramento/
```

## Ler antes

Só os modelos: `${CLAUDE_PLUGIN_ROOT}/modelos/ficha-cliente.md`, `${CLAUDE_PLUGIN_ROOT}/modelos/nota-preparo.md`, `${CLAUDE_PLUGIN_ROOT}/modelos/registro-interno.md`, `${CLAUDE_PLUGIN_ROOT}/skills/kick-off/gerador/modelo-conteudo.json` e `modelo-registro.json`.

## Passos

1. Procure `EE/CLAUDE.md` na pasta atual ou acima. Não achou: peça `/ee-trieme:instalar` e pare.
2. Normalize o nome: acentos e espaços preservados, em Title Case.
3. Número: o próximo livre em `EE/Clientes/` (existe `1. Alfa`, o próximo é `2. <Nome>`).
4. Pasta já existe: avise e pare. Nada é sobrescrito.
5. Crie a pasta e as subpastas da árvore acima, e só elas (inclui `_ensaios-internos/`).
6. Copie a ficha como `<Nome>.md`, trocando `{{NOME}}` pelo nome, `{{DATA}}` pela data de hoje (dd/mm/aaaa) e `{{VERSAO_PACOTE}}` pela `version` de `${CLAUDE_PLUGIN_ROOT}/.claude-plugin/plugin.json`.
7. Copie a nota de preparo como `Nota de preparo - <Nome>.md`, trocando `{{NOME}}` e `{{DATA}}`.
8. Copie `registro-interno.md` como `_ensaios-internos/registro.md` (crie a pasta), trocando `{{NOME}}`.
9. Copie `modelo-conteudo.json` para `1. Kick-Off/_fonte/conteudo.json` e `modelo-registro.json` para `1. Kick-Off/_fonte/registro.json`. Preencha só `cliente` (e `slug`, minúsculas sem acento e com hífens, se o modelo tiver o campo).
10. Acrescente a linha em `EE/Clientes/Clientes.md`: número, nome, formato "a confirmar", etapa "Pasta criada", próxima data vazia, link da ficha.

Crie as pastas e copie os modelos com Python (`pathlib` e `shutil`), que funciona igual em qualquer sistema. Script temporário só em `EE/.claude/tmp/`, apagado no fim.

## Onde salvar

Só em `EE/Clientes/<N>. <Nome>/` e na linha do índice. Nada dentro de `${CLAUDE_PLUGIN_ROOT}`.

## Verificação

- Nenhuma chave `{{...}}` na ficha, na nota de preparo nem no registro interno.
- A ficha tem `versao_pacote` preenchida e o primeiro passo da seção Status marcado com a data.
- Os dois JSON abrem como JSON válido.

## Mensagem ao consultor

Uma linha: `Pasta <N>. <Nome> criada com ficha, nota de preparo, registro interno e JSON do Kickoff.` Próximo passo: reunir contrato, call e formulário em `0. Inputs e Transcrições/` e dizer "próximo passo da <Nome>" (ou `/ee-trieme:passagem-venda <Nome>`).

## Anti-exemplos

- Errado: criar README ou `.gitkeep` nas pastas. Certo: só as subpastas fixas.
- Errado: copiar entregas de outro cliente ou do caso de referência. Certo: só os modelos limpos.
- Errado: nomear a pasta final `Handoff/`. Certo: `Encerramento/`; a renomeação acontece só com Executar (`/ee-trieme:encerramento`).
