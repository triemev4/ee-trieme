---
name: instalar
description: Use quando o consultor disser "instalar a EE", "configurar o ambiente" ou "primeira vez", uma vez por máquina, logo depois de instalar o plugin ee-trieme.
disable-model-invocation: true
model: sonnet
---

# Instalar

Uma vez por máquina. Nada é apagado: o que sai do lugar vai para `EE/_arquivo/`. Antes de mover ou substituir qualquer arquivo, mostre o plano e espere o "ok" do consultor. Não leia o conteúdo dos arquivos dos clientes; bastam nomes e datas.

## O que gera

```
EE/
  CLAUDE.md               de modelos/CLAUDE-raiz.md, com nome e cargo do consultor
  .claude/settings.json   de modelos/settings.json (mescla)
  Clientes/Clientes.md    índice: N · Cliente · Formato · Etapa · Próxima data · Ficha
  _arquivo/
```

## Dados do consultor

Nome: `${user_config.consultor_nome}`. Cargo: `${user_config.consultor_cargo}`. Nome ou cargo em branco, ou escrito como texto de variável, quer dizer userConfig sem preencher: pare e peça ao consultor para configurar o plugin (`/plugin`, opções do ee-trieme). Foto opcional: ponha `EE/foto-consultor.jpg` na pasta de trabalho; sem ela, a capa sai sem foto.

## Ler antes

`${CLAUDE_PLUGIN_ROOT}/modelos/CLAUDE-raiz.md` e `${CLAUDE_PLUGIN_ROOT}/modelos/settings.json`.

## Passos

1. Onde fica `EE/`: se a pasta atual já se chama `EE` ou está vazia, instale nela mesma; senão, crie `EE/` dentro dela. Liste até 3 níveis, só nomes e datas, e diga o que existe: pasta nova, pasta já organizada pelo kit ou pasta com skills antigas.
2. **Pasta nova.** Crie `EE/Clientes/`, `EE/_arquivo/` e `EE/.claude/`. Crie `Clientes.md` com a tabela do índice.
3. **Pasta já organizada pelo kit.** Mostre a tabela "origem → destino" e, com o "ok", faça:
   - Skills em `EE/.claude/skills/` (as do kit): mova cada pasta inteira para `EE/_arquivo/skills-kit/`. O pacote as substitui.
   - `EE/Base/<setor>/fontes.md`: deixe onde está e escreva `EE/_arquivo/propostas-ao-curador.md` com uma linha por arquivo (setor, caminho, quantas fontes). O índice curado é o `base/` do pacote; a lista segue ao curador, e `EE/Base/` só sai da pasta depois da resposta dele.
   - Cada ficha de cliente: acrescente o que falta, sem tocar no que existe. Chaves do cabeçalho (`cliente`, `etapa`, `proxima_data`, `formato`, `maturidade`, `decisor`, `nda`, `versao_pacote`) e seções do modelo `${CLAUDE_PLUGIN_ROOT}/modelos/ficha-cliente.md`, na ordem e com os nomes dele. Sem a pasta `Encerramento/`, crie. Sem `_ensaios-internos/registro.md`, crie do modelo `${CLAUDE_PLUGIN_ROOT}/modelos/registro-interno.md`; se a ficha ainda tem as seções Medição e Ensaios e mesa, mova as duas, iguais, para o registro.
4. **`EE/CLAUDE.md`.** Copie o modelo trocando `{{CONSULTOR}}` e `{{CARGO}}` pelos valores acima. Já existe um: guarde-o em `EE/_arquivo/CLAUDE-anterior.md` (com o "ok") e grave o novo. Nenhuma chave `{{...}}` pode sobrar.
5. **`EE/.claude/settings.json`.** Não existe: copie o modelo. Existe: mescle. Acrescente `"model": "sonnet"` se não houver modelo definido (havendo outro, pergunte), e junte as listas `permissions.allow` e `permissions.deny` do modelo às que já existem, sem repetir e sem remover nada. A lista `allow` deixa o assistente ler o pacote, gravar em `Clientes/` e rodar os scripts sem parar a cada passo; a `deny` protege `_arquivo/` e o pacote.
6. Dependências, sem ambiente virtual (a primeira linha confere que o Python roda), em qualquer terminal:

```
python --version
python -m pip install --user -r "${CLAUDE_PLUGIN_ROOT}/scripts/requirements.txt"
```

Opcional: o playwright serve à inspeção da LP (e também aos prints da auditoria da Semana 3 e à conferência visual do deck), usa o Edge ou o Chrome já instalado e não baixa navegador. Se quiser: `python -m pip install --user playwright`. Sem ele, a inspeção da LP fica pendente e o consultor confere a olho.

7. Oriente `/model sonnet` e a conferência com `/model`.
8. Semana 3, com o "ok" do consultor:
   - A skill `espionar-concorrente-pro`, quando instalada, precisa das dependências dela: `python -m pip install --user -r "<home>/.claude/skills/espionar-concorrente-pro/scripts/requirements.txt"`. Sem elas, a coleta de anúncios falha e vira pendência.
   - A velocidade do site usa o PageSpeed Insights do Google. Sem chave, o limite estoura fácil. A chave é gratuita: o consultor cria no Google Cloud (API "PageSpeed Insights") e grava na variável de ambiente `PAGESPEED_API_KEY`.
9. Opcional (PDF escaneado): o OCR usa o Tesseract com o idioma português (`por.traineddata`); sem ele, a página só de imagem vira JPEG pequeno e nada deixa de funcionar. Informe o consultor; não instale sem o "ok" dele.

## Onde salvar

**Stitch, quando houver LP.** O módulo `/ee-trieme:configurar-stitch` confere a conexão existente e orienta a configuração por usuário e ferramenta. Chame-o quando o consultor optar pela LP ou pedir a integração; não é dependência para todas as EEs. Credenciais pertencem à configuração local do usuário, nunca à pasta de cliente ou ao pacote.

Arquivos de trabalho desta instalação ficam dentro de `EE/`; a configuração de conexão por usuário segue o guia próprio acima. Nada dentro de `${CLAUDE_PLUGIN_ROOT}`: a pasta muda a cada atualização do pacote.

## Verificação

- `EE/CLAUDE.md` existe, traz nome e cargo e não contém `{{`.
- `EE/.claude/settings.json` abre como JSON válido e tem `model` e as listas `allow` e `deny` do modelo.
- `python -c "import bs4, docx"` roda sem erro.
- Nenhum arquivo foi apagado: tudo o que saiu do lugar está em `EE/_arquivo/`.

## Mensagem ao consultor

Abra com esta linha, igual: "Feche e abra o Claude Code dentro de EE/: sem isso o painel e os gatilhos não aparecem." Na segunda linha: "Na primeira vez, aceite a pergunta de confiança da pasta EE: sem isso a lista de permissões do settings.json é ignorada e o assistente para a cada passo." Depois, uma linha por item: o que foi criado, o que já existia e foi mantido, o que foi para `_arquivo/`. Próximo passo: `/ee-trieme:novo-cliente <Nome>`.

## Anti-exemplos

- Errado: sobrescrever `EE/CLAUDE.md` ou `settings.json` existente. Certo: guardar o antigo em `_arquivo/` ou mesclar.
- Errado: ler as pastas dos clientes para organizar. Certo: só nomes e datas.
- Errado: apagar a skill antiga do kit. Certo: mover para `_arquivo/skills-kit/`.
