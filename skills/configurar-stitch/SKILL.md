---
name: configurar-stitch
description: "Configura ou diagnostica a conexão MCP do Stitch para a landing page da EE. Use na preparação da LP quando o Stitch estiver ausente, sem autenticação ou sem as ferramentas necessárias; também quando o consultor pedir a configuração."
---

# Configurar Stitch

Conecta o assistente ao serviço remoto do Google. Uma configuração por usuário e ferramenta; os projetos de cada cliente ficam separados no Stitch. Falha aqui limita a produção da LP, não interrompe as outras etapas da EE. A skill de LP do pacote contém o fluxo: skills globais do Stitch são opcionais.

## 1. Conferir antes de configurar

Descubra as ferramentas MCP disponíveis, inclusive as adiadas, pelo catálogo do ambiente. O prefixo pode variar. Se houver Stitch, faça uma chamada real de `list_projects`: lista vazia também é sucesso. Não crie projeto apenas para testar acesso. Confira a presença de leitura de projeto/tela, geração e edição; sistema visual exige as ferramentas correspondentes. Conexão saudável: termine aqui e volte à LP.

Sem conexão, identifique o cliente de execução e a versão. O guia abaixo atende execução local Windows, não configura automaticamente sessões em nuvem. Leia [configuracao.md](references/configuracao.md) para diagnósticos, escopos e fontes. Inspecione somente nomes, endpoint e existência dos campos de configuração; nunca imprima o arquivo inteiro ou valores de credenciais. Preserve outros servidores, modelos e permissões. Se `stitch` já existir, corrija somente sua configuração; nome ocupado por outro serviço permanece intacto, usando `stitch-ee` para o novo.

```powershell
# Execute apenas o par correspondente à ferramenta do consultor.
claude --version
claude mcp add --help
codex --version
codex mcp add --help
```

## 2. Credencial, pelo consultor

Oriente a conta Google que a unidade definiu para o consultor. Em [Settings do Stitch](https://stitch.withgoogle.com/settings), ele cria sua chave em **API Keys**. A chave é digitada somente no terminal local dele, nunca no chat, na ficha ou no pacote. Mostre o bloco abaixo para o próprio consultor executar; não abra um terminal interativo por ele.

O bloco guarda a chave na variável de ambiente do usuário Windows, fora do repositório, e a disponibiliza nesta sessão. Esse armazenamento é legível por processos da conta, não é um cofre criptografado. Se a política da unidade exigir cofre ou OAuth, use o fluxo aprovado por ela e a documentação oficial em vez deste armazenamento.

```powershell
$stitchSecret = Read-Host 'Chave de API do Stitch (entrada protegida)' -AsSecureString
$stitchPointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($stitchSecret)
try {
    $stitchValue = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($stitchPointer)
    if ([string]::IsNullOrWhiteSpace($stitchValue)) { throw 'Chave vazia.' }
    [Environment]::SetEnvironmentVariable('STITCH_API_KEY', $stitchValue, 'User')
    $env:STITCH_API_KEY = $stitchValue
} finally {
    [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($stitchPointer)
    Remove-Variable stitchValue, stitchPointer, stitchSecret -ErrorAction SilentlyContinue
}
```

Aplicativos já abertos mantêm o ambiente anterior. O consultor deve encerrar e abrir o assistente a partir desse terminal; para uso por atalhos, renovar a sessão Windows quando o aplicativo ainda não receber a variável. Não peça para exibir o valor. Existência de variável não comprova validade da chave.

## 3. Registrar somente a conexão escolhida

**Claude Code.** Para servidor ainda ausente, use o comando abaixo no PowerShell. As aspas simples preservam a referência à variável: o segredo não entra no argumento nem no histórico. O escopo `user` grava a definição em `%USERPROFILE%/.claude.json` (ou no diretório de configuração personalizado do Claude). Se já houver entrada, faça uma cópia de segurança local e altere só os campos do Stitch, preservando o restante; não remova o servidor para recriá-lo.

```powershell
claude mcp add --transport http --scope user --header 'X-Goog-Api-Key: ${STITCH_API_KEY}' stitch https://stitch.googleapis.com/mcp
```

**Codex.** Use a configuração de usuário em `%USERPROFILE%/.codex/config.toml`, ou no `CODEX_HOME` personalizado já definido. Faça cópia de segurança local e mescle o bloco abaixo. Se a tabela existir, atualize-a em vez de duplicá-la. Não grave a chave literal. O CLI não exige instalação de um servidor local nem pacote npm para este transporte.

```toml
[mcp_servers.stitch]
url = "https://stitch.googleapis.com/mcp"
env_http_headers = { "X-Goog-Api-Key" = "STITCH_API_KEY" }
```

Neste endpoint, chave de API usa `X-Goog-Api-Key`; `bearer_token_env_var` configura outro tipo de autenticação. Confirme a sintaxe no help e na referência oficial da versão instalada. Configuração da extensão/app e CLI pode apontar para outro ambiente: confira onde o processo que executa o MCP roda.

## 4. Comprovar acesso e devolver ao fluxo

Recarregue a conexão pelo cliente ou abra nova sessão. No Claude Code, `/mcp` mostra o diagnóstico; no Codex, o catálogo MCP da sessão deve carregar as ferramentas. A listagem de servidores configurados é apenas um diagnóstico, não o aceite.

1. Descubra novamente as ferramentas expostas pelo Stitch.
2. Chame `list_projects` pelo MCP e confira resposta sem erro de autenticação. Mostre só sucesso/erro e contagem, sem nomes de projetos de outros clientes.
3. Confira as capacidades exigidas pela próxima ação da LP. Ferramenta ausente vira pendência identificada; não invente nome ou esquema de chamada.
4. Registre no preparo da LP: ferramenta/versão, data, conexão conferida e capacidades disponíveis. Guarde apenas nomes e IDs necessários, nunca chave, token ou cabeçalhos de autenticação.

**Pronto quando:** leitura real autenticada funcionou e as ferramentas da próxima ação estão disponíveis. Isso comprova conexão; geração, edição e exportação só são comprovadas ao executar a LP. O primeiro protótipo autorizado é o teste dessas operações, sem projeto descartável criado pela instalação.

Falha: siga o diagnóstico da referência, registre a pendência da LP e permita que a EE continue. Em timeout de geração já iniciada, consulte projeto/telas antes de qualquer nova tentativa; não repita uma mutação só porque não recebeu a resposta.
