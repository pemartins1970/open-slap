# MCP Telegram — Open Slap!

Este documento especifica um conector Telegram via MCP (Model Context Protocol) para o Open Slap!, com foco em segurança e privacidade.

O objetivo é permitir que o usuário converse com a Sabrina remotamente pelo Telegram (ex.: “de casa”), recebendo respostas e delegando tarefas (projetos, documentos, demandas), sem expor o backend a riscos desnecessários.

---

## Escopo

- Permitir conversas 1:1 via Telegram (chat privado) com a Sabrina.
- Vincular um chat do Telegram a um usuário do Open Slap! com um fluxo explícito e seguro.
- Encaminhar mensagens do Telegram para o Open Slap! e devolver respostas ao Telegram.
- Suportar comandos mínimos de operação e segurança (`/start`, `/link`, `/unlink`, `/status`, `/help`).

Fora de escopo (primeira versão):
- Suporte a grupos/canais.
- Acesso “admin” a dados de outros usuários.
- Upload/download de arquivos sensíveis sem política de DLP.
- Execução de comandos do SO a partir do Telegram.

---

## Requisitos de Segurança e Privacidade (prioridade)

### Princípios

- Menor privilégio: o conector só faz o mínimo necessário (receber/enviar mensagens).
- Opt-in explícito: só funciona após o usuário vincular o chat.
- Minimização de dados: não persistir conteúdo de mensagens por padrão.
- Segredos não saem do host: token do bot e chaves ficam locais.
- “Fail closed”: em caso de dúvida, negar a ação.

### Controles obrigatórios

- Vinculação por código de uso único e expiração curta (ex.: 5–10 min).
- Lista de chats permitidos (allowlist) derivada da vinculação; todo o resto é ignorado.
- Rate limiting por chat/usuário.
- Redação de segredos/PII antes de persistir qualquer coisa (quando habilitado).
- Logs sem conteúdo (somente metadados mínimos).
- Criptografia em repouso para segredos do conector (reutilizar o padrão do projeto).
- Modo “privacidade máxima”: não salvar histórico vindo do Telegram no SQLite.

### Limitações de privacidade do Telegram (bots)

- Bots **não** suportam “Secret Chats” (E2EE). Mensagens de bot trafegam e podem ser armazenadas na infraestrutura do Telegram.
- Isso significa que Telegram é um canal conveniente, mas **não é o canal mais privado** possível.

Implicação prática: tratar Telegram como “borda” e evitar enviar/retornar segredos ou dados altamente sensíveis. Para informações sensíveis, preferir “resumo” + link/ação no Open Slap! local, ou exigir confirmação adicional.

---

## Arquitetura (visão geral)

### Componentes

1. **Open Slap! Backend (FastAPI)**
   - Mantém autenticação, usuários, projetos e a lógica da Sabrina.
   - Exponibiliza endpoints internos para vincular Telegram e para “entregar” mensagens ao orquestrador.

2. **Telegram MCP Server (processo separado)**
   - Implementa MCP e expõe ferramentas do Telegram como “tools”.
   - Faz polling (long polling) ou webhook (opcional) para receber mensagens.
   - Envia mensagens via Telegram Bot API.

3. **Open Slap! MCP Client (no backend)**
   - Cliente MCP que chama as ferramentas do Telegram MCP Server.
   - Responsável por aplicar políticas: allowlist, rate limit, privacidade, redaction.

Na prática, o caminho mais seguro para V1 é manter **Telegram MCP Server e Backend no mesmo host** e não expor o backend publicamente. O Telegram conecta no bot via internet, mas o bot fala com o backend localmente.

### Fluxo de mensagens (entrada)

1. Usuário envia mensagem para o bot no Telegram.
2. Telegram MCP Server recebe a atualização (polling/webhook).
3. Telegram MCP Server entrega o evento ao backend (via endpoint local) ou o backend puxa via MCP (dependendo do modo).
4. Backend valida vinculação + políticas (chat_id permitido, rate limit, modo privacidade).
5. Backend envia texto para o orquestrador (Sabrina) e recebe resposta.
6. Backend chama MCP `telegram.sendMessage` para responder ao chat.

### Fluxo de mensagens (saída)

- Sabrina/Backend decide enviar uma notificação (ex.: “build finalizado”, “lembrete de tarefa”).
- Backend chama MCP `telegram.sendMessage` apenas para chats vinculados.

---

## Modelo de Ameaças (ameaças e mitigação)

| Ameaça | Vetor | Impacto | Mitigação |
|---|---|---:|---|
| Sequestro de conta Telegram | SIM swap/roubo de sessão | Alto | Vinculação revogável, alertas, permitir “PIN de sessão” opcional, mínimo de dados |
| Vazamento do token do bot | .env/logs/print | Crítico | Segredo só em env/secret store local, nunca logar, rotação, permissões de arquivo |
| Acesso não autorizado (chat não vinculado) | Mensagens de estranhos | Alto | Allowlist por (chat_id, telegram_user_id), ignorar grupos por padrão |
| Prompt injection via Telegram | Conteúdo malicioso | Alto | Redaction, guardrails, bloqueio de ferramentas perigosas, separar “comando” de “texto” |
| Exfiltração de dados | Perguntas induzidas | Alto | Políticas: “nunca mostrar segredos”, filtros, confirmação para ações sensíveis |
| Replay de código de vinculação | Código interceptado | Médio | Código curto + expiração + uso único + bind por usuário autenticado |
| DoS por spam | Flood de mensagens | Médio | Rate limit + backoff + bloqueio temporário por chat |
| Persistência indevida de PII | Logs/DB | Alto | Modo privacidade máxima, logs sem conteúdo, retenção curta configurável |

---

## Fluxo de vinculação (linking) — recomendado

### Objetivo

Garantir que somente um usuário autenticado no Open Slap! consiga vincular seu Telegram, sem depender de “conhecer um token”.

### Passo a passo

1. No Open Slap! (web), o usuário autenticado acessa “Conectores → Telegram” e clica em “Gerar código”.
2. Backend gera `link_code` aleatório, curto, uso único, com expiração (ex.: 10 minutos), associado ao `user_id`.
3. No Telegram, o usuário envia `/link <codigo>` em chat privado com o bot.
4. Telegram MCP Server entrega o evento ao backend.
5. Backend valida o código, registra a vinculação `(user_id, telegram_user_id, chat_id)` e invalida o código.
6. Backend responde “Conectado com sucesso”.

### Validação de identidade (recomendado)

- Para cada update recebido do Telegram, validar ambos:
  - `telegram_user_id` (ex.: `message.from.id`)
  - `chat_id` (ex.: `message.chat.id`)
- Exigir que a dupla `(telegram_user_id, chat_id)` exista vinculada ao `user_id` no Open Slap!.
- Em chat privado, `chat_id` normalmente coincide com o usuário, mas a validação dupla reduz risco de confusão de contexto e deixa o modelo explícito.

### Bloqueio de usuários não vinculados

- O Telegram não oferece um “ban” em chat privado com bot; portanto o bloqueio é lógico.
- Política recomendada: `default deny`.
  - Se não estiver vinculado: ignorar mensagens ou responder apenas uma vez com “Não autorizado” e depois silenciar por rate limit.
  - Nunca revelar se um `telegram_user_id` “existe” no sistema e nunca retornar detalhes do backend.

### Revogação

- `/unlink` remove a vinculação do chat (e opcionalmente revoga “sessões” pendentes).
- A UI do Open Slap! permite remover vinculações e gerar novos códigos.

---

## Política de dados (privacidade)

### O que o conector precisa saber

- `chat_id` e `telegram_user_id` para enviar respostas e aplicar allowlist.
- `user_id` interno do Open Slap! para roteamento de contexto.

### O que NÃO deve ser armazenado por padrão

- Texto integral das mensagens do Telegram.
- Metadados ricos (ex.: localização, contatos, mídia).

### Modos operacionais

- **Privacidade máxima (padrão recomendado)**
  - Não persistir mensagens vindas do Telegram no SQLite.
  - Persistir somente eventos técnicos mínimos (ex.: vinculação, falhas de rate limit).

- **Histórico mínimo (opcional)**
  - Persistir apenas as mensagens do usuário e respostas, com redaction ativa.
  - Retenção curta (ex.: 7–30 dias) com rotina de expurgo.

---

## Especificação MCP (proposta)

### Server name

- `openslap-telegram`

### Tools

#### `telegram.sendMessage`

- **Input**
  - `chat_id` (string ou number)
  - `text` (string)
  - `parse_mode` (opcional: `"MarkdownV2" | "HTML"`)
  - `disable_preview` (opcional: boolean)
- **Output**
  - `message_id` (string/number)

Regras:
- Nunca aceitar `chat_id` que não esteja allowlisted.
- Se disponível no payload, validar também `telegram_user_id` contra o vínculo do chat.
- Aplicar rate limit e tamanho máximo.

#### `telegram.getUpdates` (somente modo polling)

- **Input**
  - `offset` (opcional)
  - `timeout_sec` (opcional)
- **Output**
  - Lista de updates normalizados.

Regras:
- O MCP server não deve repassar updates sem validação de “tipo de chat” (private only, por padrão).

#### `telegram.setWebhook` / `telegram.deleteWebhook` (opcional)

- Somente habilitar se houver TLS e validação de origem.

### Resources (opcional)

- `telegram://linked-chats` (somente para debug interno; nunca retornar PII sem permissão)

---

## Configuração (env vars propostas)

No host do Telegram MCP Server:

- `TELEGRAM_BOT_TOKEN` (obrigatório)
- `OPENSLAP_BACKEND_URL` (ex.: `http://127.0.0.1:5150`)
- `OPENSLAP_TELEGRAM_MODE` (`polling` | `webhook`)
- `OPENSLAP_TELEGRAM_PRIVACY_MODE` (`max` | `minimal_history`)
- `OPENSLAP_TELEGRAM_RATE_LIMIT_PER_MIN` (ex.: `20`)

No Open Slap! Backend:

- `OPENSLAP_MCP_TELEGRAM_URL` (endpoint do MCP server, se usar HTTP transport)
- `SLAP_DB_PATH` (já existente no projeto)

---

## Endpoints internos (backend) — proposta

- `POST /connectors/telegram/link-code`
  - Requer JWT do Open Slap!
  - Retorna `link_code` + expiração

- `POST /connectors/telegram/link`
  - Consumido pelo MCP server ao receber `/link <code>`
  - Valida e grava vinculação

- `POST /connectors/telegram/inbound`
  - Consumido pelo MCP server para entregar uma mensagem normalizada
  - Backend responde com “ação” (ex.: `sendMessage`) ou texto pronto

---

## Guardrails de conteúdo (prompt injection e vazamento)

- Tratar Telegram como **input não confiável**.
- Separar comandos (`/link`, `/unlink`) de mensagens naturais.
- Ações sensíveis exigem confirmação:
  - “apagar dados”, “exportar arquivo”, “revelar segredo”, “enviar documento”.
- Redaction ativa para padrões comuns (tokens, chaves, senhas).
- Política “no secrets by default”: nunca retornar valores de env vars, tokens de conectores, chaves.

---

## Observabilidade (com privacidade)

- Logar apenas:
  - `event_type`, `chat_id` (hash), `user_id`, `status`, latência
- Não logar:
  - `text` integral, payload do Telegram, tokens

---

## Plano de implementação (marcos)

1. **Banco e vinculação**
   - Tabela `telegram_links` com `(user_id, telegram_user_id, chat_id, created_at, revoked_at)`
   - Tabela `telegram_link_codes` com expiração e uso único

2. **MCP server do Telegram (polling)**
   - Implementar `sendMessage` e `getUpdates`
   - Normalização de eventos e filtros (private only)

3. **Backend: políticas e roteamento**
   - Allowlist, rate limit, modo privacidade máxima
   - Encaminhar mensagem ao orquestrador e responder

4. **Hardening**
   - Rotação de token, teste de replay, testes de spam
   - Checklist de produção (firewall, TLS se webhook)

---

## Checklist de hardening (produção)

```
[ ] Backend não exposto publicamente (preferir reverse proxy + allowlist)
[ ] TELEGRAM_BOT_TOKEN fora do repo e fora de logs
[ ] Vinculação com expiração curta e uso único
[ ] Allowlist ativa (default deny)
[ ] Rate limit por chat
[ ] Modo privacidade máxima ativo por padrão
[ ] Redaction habilitada
[ ] Rotina de revogação e auditoria de vinculações
```

---

## Referências internas

- [SECURITY.md](file:///c:/workaround/projetos/Slap/Open_Slap/v2/docs/SECURITY.md)
