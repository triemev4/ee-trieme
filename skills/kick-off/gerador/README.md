# Gerador do Kickoff

Scripts que montam as entregas do Kickoff a partir de arquivos JSON de conteúdo. O modelo (estrutura, CSS, componentes) vive no pacote. O conteúdo de cada cliente vive na pasta dele, em `1. Kick-Off/_fonte/`.

O comando completo, com o caminho do pacote, está em `skills/kick-off/SKILL.md`. Este arquivo explica o que cada script faz.

## Arquivos

| Arquivo | Para quê |
|---|---|
| `gerar_kickoff.py` | Gera `kickoff-<slug>.html`, a pauta que o cliente recebe. Com `--docx`, gera também o DOCX do deck de perguntas (uso interno) |
| `gerar_dossie.py` | Gera o Registro do Kickoff (`registro-kickoff-<slug>.docx`) a partir de `registro.json`, depois da reunião |
| `modelo-conteudo.json` | Esqueleto do conteúdo do Kickoff |
| `modelo-registro.json` | Esqueleto do Registro do Kickoff |

Os estilos DOCX, a trava de saída e os argumentos do consultor moram em `scripts/docx_common.py`, usado por todos os scripts do pacote.

## Argumentos

```
gerar_kickoff.py <conteudo.json> <pasta de saída> --consultor "<nome>" --cargo "<cargo>" [--foto <arquivo>] [--docx]
gerar_dossie.py  <registro.json> <pasta de saída> --consultor "<nome>" --cargo "<cargo>"
```

A pasta de saída é a `1. Kick-Off/` do cliente. Os scripts recusam uma saída dentro da pasta do pacote.

## O consultor

Nome e cargo vêm das opções do plugin (`consultor_nome`, `consultor_cargo`), que o guia passa em `--consultor` e `--cargo`. A foto é o arquivo opcional `EE/foto-consultor.jpg`, passado em `--foto`. Sem nome, o script avisa e usa texto neutro. Sem foto, ou com foto que não existe, o hero sai sem a imagem.

Em qualquer texto do JSON, `{consultor}`, `{consultor_nome}` e `{consultor_cargo}` são trocados por esses dados. Use no `rodape` e nas linhas de consultor do `registro.json`.

## De onde vem o visual

`gerar_kickoff.py` copia o `<head>` (CSS), o chrome com o logo, a decoração do hero (tudo antes do `.hero-top`, como a marca d'água `.v4-mark`) e o script de navegação do HTML de referência `referencias/layout/kickoff.html`, localizando cada parte por marcador. A foto e o nome do consultor vêm dos argumentos, não da referência. Sempre acrescenta ao CSS os rótulos de público em grupos (`.pub-sub`) e a correção `.live-fill,.pausa{align-self:flex-start;}`.

Abra o HTML no navegador antes de entregar. Arquivo local pode ser bloqueado pela extensão do Chrome: sirva a pasta com `python -m http.server 8765 --bind 127.0.0.1`.

## Requisitos

Python 3 com as dependências de `scripts/requirements.txt`. Os scripts param com erro se encontrarem travessão no conteúdo.

## Chaves do conteudo.json

Opcionais em qualquer bloco de perguntas (`marketing`, `comerciais`, `metas`, `design`) e no cronograma (`cronograma_glossario`): `glossario` = `[[termo, definição], ...]`, que vira o rodapé discreto "Termos desta tela". Use só para os nossos termos de método e marketing, nunca para termos do mercado do cliente. Instituições sempre pelo nome completo. Em qualquer texto, `<b>palavra</b>` marca palavra-chave em negrito no HTML e no DOCX.

`fechamento.validacao`: pergunta de validação que vira `.pausa` entre o recap e o gancho.

Chaves: `cliente`, `slug`, `hero_lede`, `hero_meta`, `oque_lede`, `semanas_grid`, `roteiro`, `dores`, `mapeado`, `marketing`, `comerciais`, `metas`, `design` (com `publico` em grupos `[título, [rótulos]]`; título vazio para grupo único), `fechamento`, `cronograma` (os 5 nomes oficiais das semanas), `prosa` (parágrafos do DOCX por bloco), `rodape` (opcional).
