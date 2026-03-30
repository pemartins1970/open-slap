# Segurança — Open Slap!

Open Slap! é uma aplicação local-first. Trate conectores, skills e execução de ferramentas como capacidades privilegiadas e evite expor o aplicativo a redes não confiáveis.

---

## Versões suportadas

Correções de segurança se aplicam a:

- A release mais recente publicada
- O branch `main`

Versões anteriores não recebem patches retroativos.

---

## Modelo de ameaças

| Ameaça | Nível | Status |
|--------|-------|--------|
| Prompt injection via input não confiável | Alto | ⚠️ Mitigado parcialmente via redação |
| Exposição de segredos no repositório | Crítico | ✅ `.env` excluído do ZIP e do `.gitignore` |
| CORS aberto em produção | Alto | ✅ Restrito ao `APP_URL` quando `NODE_ENV=production` |
| JWT com secret padrão em produção | Alto | ✅ Aviso no console se `JWT_SECRET` não estiver definido |
| Upload de arquivos sem limite de tamanho | Médio | ✅ Limite de 10 MB via Multer |
| Execução de comandos do sistema | Alto | ✅ Controlado por `OPENSLAP_OS_COMMANDS` (padrão: off em produção) |
| PII persistida na memória | Médio | ✅ `SLAP_MEMORY_REDACTION_ENABLED=1` (padrão) |
| Credenciais de conector no banco | Alto | ✅ Armazenadas criptografadas (DPAPI / cipher) |

---

## O que está implementado

### Redação de memória
Quando `SLAP_MEMORY_REDACTION_ENABLED=1` (padrão), padrões de segredos comuns (tokens, chaves, senhas) são redacionados antes da persistência no SQLite.

Implementado em:
- `backend/db.py` → `_redact_text()` aplicado em mensagens e eventos de memória
- Redação também presente no servidor MCP

### Autenticação
- Tokens JWT assinados com `JWT_SECRET`
- Senhas armazenadas com bcrypt (10 rounds)
- Senhas de grupos privados nunca armazenadas em texto puro

### Conectores
- Tokens de conectores (GitHub, Google, etc.) armazenados criptografados no banco
- Nunca incluídos em logs, respostas de API ou exports

### CORS
- Em produção (`NODE_ENV=production`): aceita apenas origens de `APP_URL`
- Em desenvolvimento: aceita qualquer origem (padrão seguro para uso local)

---

## Checklist de hardening para produção

```
[ ] JWT_SECRET definido com 32+ caracteres aleatórios
[ ] NODE_ENV=production no .env
[ ] APP_URL definido com a URL real do servidor
[ ] OPENSLAP_OS_COMMANDS=0 se execução de shell não for necessária
[ ] Servidor não exposto em 0.0.0.0 sem firewall ou reverse proxy
[ ] .env não versionado (verificar .gitignore)
[ ] SLAP_MEMORY_REDACTION_ENABLED=1 (padrão — verificar se não foi desabilitado)
[ ] Uploads limitados a 10 MB (padrão — verificar se não foi alterado)
```

---

## Reportar vulnerabilidades

Se você descobrir uma vulnerabilidade:

1. **Não abra uma issue pública** com detalhes de exploit.
2. Use o sistema de **Security Advisories** do GitHub (reporte privado de vulnerabilidade).
3. Se não estiver disponível, abra uma issue mínima solicitando um canal de divulgação privado.

Responderemos o mais rápido possível dentro da capacidade de um projeto de desenvolvedor solo.

---
---

# Security — Open Slap!

Open Slap! is a local-first application. Treat connectors, skills, and tool execution as privileged capabilities, and avoid exposing the application to untrusted networks.

---

## Supported versions

Security fixes apply to:

- The latest published release
- The `main` branch

Previous versions do not receive retroactive patches.

---

## Threat model

| Threat | Level | Status |
|--------|-------|--------|
| Prompt injection via untrusted input | High | ⚠️ Partially mitigated via redaction |
| Secret exposure in repository | Critical | ✅ `.env` excluded from ZIP and `.gitignore` |
| Open CORS in production | High | ✅ Restricted to `APP_URL` when `NODE_ENV=production` |
| Default JWT secret in production | High | ✅ Console warning if `JWT_SECRET` not set |
| File uploads without size limit | Medium | ✅ 10 MB limit via Multer |
| System command execution | High | ✅ Controlled by `OPENSLAP_OS_COMMANDS` (default: off in production) |
| PII persisted to memory | Medium | ✅ `SLAP_MEMORY_REDACTION_ENABLED=1` (default) |
| Connector credentials in database | High | ✅ Stored encrypted (DPAPI / cipher) |

---

## What is implemented

### Memory redaction
When `SLAP_MEMORY_REDACTION_ENABLED=1` (default), common secret patterns (tokens, keys, passwords) are redacted before persistence in SQLite.

Implemented in:
- `backend/db.py` → `_redact_text()` applied to messages and memory events
- Redaction also present in the MCP server

### Authentication
- JWT tokens signed with `JWT_SECRET`
- Passwords stored with bcrypt (10 rounds)
- Private group passwords never stored in plain text

### Connectors
- Connector tokens (GitHub, Google, etc.) stored encrypted in the database
- Never included in logs, API responses, or exports

### CORS
- In production (`NODE_ENV=production`): accepts only origins matching `APP_URL`
- In development: accepts any origin (safe default for local use)

---

## Hardening checklist for production

```
[ ] JWT_SECRET set with 32+ random characters
[ ] NODE_ENV=production in .env
[ ] APP_URL set to the real server URL
[ ] OPENSLAP_OS_COMMANDS=0 if shell execution is not needed
[ ] Server not exposed on 0.0.0.0 without firewall or reverse proxy
[ ] .env not versioned (check .gitignore)
[ ] SLAP_MEMORY_REDACTION_ENABLED=1 (default — verify it has not been disabled)
[ ] Uploads limited to 10 MB (default — verify it has not been changed)
```

---

## Reporting vulnerabilities

If you discover a vulnerability:

1. **Do not open a public issue** with exploit details.
2. Use GitHub's **Security Advisories** system (private vulnerability reporting).
3. If not available, open a minimal issue requesting a private disclosure channel.

We will respond as quickly as possible within the capacity of a solo-developer project.
