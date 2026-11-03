# EE Trieme

Plugin público `ee-trieme` para apoiar consultores na execução da Estruturação Estratégica (EE) com Claude Code. Reúne guias por etapa, padrões, modelos, moldes HTML e scripts locais. Os exemplos distribuídos são fictícios; dados e conclusões do projeto devem vir das fontes de cada cliente.

Versão **1.3.0**. [Baixar a versão](https://github.com/triemev4/ee-trieme/releases/tag/v1.3.0) · [Verificações da distribuição](docs/validacao.md).

## Requisitos

- Git, para instalação pelo marketplace ou por clone.
- Python 3 para os scripts do pacote.
- Claude Code instalado e uma conta Claude com acesso ao produto. O GitHub não exige login para baixar o repositório público.

Instale Git e Python pelas páginas oficiais dos respectivos projetos. Confira no terminal:

```powershell
git --version
python --version
```

## Instalar pelo marketplace público

No Windows, recomendamos a instalação pelo ZIP, descrita abaixo. Na validação com Claude Code 2.1.304, o clone direto pelo CLI encontrou erros `EBUSY`/`EPERM` ao renomear a pasta temporária; o ZIP foi baixado e instalado com sucesso. Se encontrar esse erro, use a opção pelo ZIP.

No terminal do sistema ou no terminal integrado do Orca, antes de iniciar uma sessão do Claude Code, adicione e instale o marketplace do GitHub:

```text
claude plugin marketplace add https://github.com/triemev4/ee-trieme.git --scope user
claude plugin install ee-trieme@ee-trieme --scope user
```

O repositório público pode ser baixado sem autenticação GitHub. O uso do Claude Code ainda requer uma conta Claude.

## Instalar pelo ZIP

Baixe o ZIP da versão `v1.3.0` em:

[Baixar ee-trieme-1.3.0.zip](https://github.com/triemev4/ee-trieme/releases/download/v1.3.0/ee-trieme-1.3.0.zip)

Extraia o arquivo e adicione a pasta extraída como marketplace local:

```text
claude plugin marketplace add "C:\caminho\para\ee-trieme-1.3.0" --scope user
claude plugin install ee-trieme@ee-trieme --scope user
```

Guarde a pasta extraída fora da pasta de trabalho dos clientes.

## Instalar por caminho local

Se o pacote já estiver em uma pasta local, use o mesmo comando de marketplace apontando para ela:

```text
claude plugin marketplace add "C:\caminho\para\ee-trieme" --scope user
claude plugin install ee-trieme@ee-trieme --scope user
```

## Configurar e preparar a pasta de trabalho

1. No Claude Code, abra `/plugin` e configure `consultor_nome` e `consultor_cargo` nas opções do `ee-trieme`.
2. Crie uma pasta de trabalho `EE/` separada do checkout do plugin. No Orca, abra essa pasta como espaço de trabalho. Se o Orca exigir um repositório, inicialize um repositório Git local nessa pasta, sem adicionar remoto; mantenha dados de clientes fora do checkout público do plugin.
3. Inicie o Claude Code nessa pasta de trabalho, execute `/ee-trieme:instalar` e acompanhe a prévia de alterações apresentada pelo assistente.
4. Depois da instalação, feche e reabra a sessão do Claude Code dentro da pasta `EE/` para carregar as instruções e permissões locais.
5. Para abrir o primeiro projeto, execute `/ee-trieme:novo-cliente <Nome>`.

O instalador orienta a dependência Python do pacote e verifica a instalação. Recursos opcionais, como Stitch, Playwright e OCR, são configurados apenas quando o fluxo correspondente for usado.

## O que contém

- `agents/`: papéis de apoio para tarefas específicas.
- `skills/`: comandos e procedimentos por etapa da EE.
- `padrao/` e `modelos/`: regras de método e arquivos iniciais de trabalho.
- `moldes/`: estruturas HTML reutilizáveis e instruções para preenchê-las.
- `scripts/`: utilitários locais chamados pelos guias.
- `docs/`: arquitetura e decisões técnicas resumidas.

O pacote não inclui dados de clientes nem casos privados. A equipe pode usar exemplos inventados para aprender o formato, marcando-os como fictícios e sem reutilizar fatos ou valores de projetos reais.

## Atualizar

No terminal do sistema ou integrado do Orca:

```text
claude plugin update ee-trieme@ee-trieme
```

Reinicie a sessão para carregar a atualização. Se instalou por ZIP, baixe e extraia a versão nova antes de atualizar o marketplace local. Termine entregas em andamento na versão em que começaram e adote a nova na próxima entrega.

## Licença e reutilização

A disponibilidade pública do repositório não concede automaticamente uma licença aberta. Consulte o responsável pelo pacote antes de redistribuir, adaptar ou incorporar os materiais em outro produto.
