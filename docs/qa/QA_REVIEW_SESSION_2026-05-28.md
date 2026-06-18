# Q&A Review — Sessão 2026-05-28

> **Projeto**: Open Slap! v3
> **Data**: 2026-05-28
> **Objetivo**: Revisão do que foi planejado vs realizado, pendências, e próximos passos.

---

## 1. Resumo da Sessão

### Organização do open-slap-v3
- Criado `CURRENT_STATE.md` para documentar estado real vs visão v3
- Renomeado `README_V3.md` → `VISION_V3.md` (deixa claro que é documento de visão)
- Documentada dualidade de arquivos (original vs refatorado)
- Limpo `requirements.txt` (removidos SDKs não usados: `openai`, `google-generativeai`, `groq`)
- Corrigido `run_slap.bat` (apontava para `backend.main:app` inexistente)
- Resolvido conflito de porta 8000 → Open Slap agora usa 5150

### Integração Opcional com AI-Gateway
- Adicionado endpoint `/v1/chat/completions` (OpenAI format) ao AI-Gateway local (`C:\AI-Gateway`)
- Criado `AIGatewayClient` em `integrations/ai_gateway_client.py` para uso opcional
- Settings `AI_GATEWAY_ENABLED`, `AI_GATEWAY_URL`, `AI_GATEWAY_API_KEY` — tudo desligado por default
- **Nota**: AI-Gateway é setup local do ambiente do desenvolvedor, não requisito do Open Slap

---

## 2. O que Foi Implementado

### 2.1 Código Novo

| Arquivo | Descrição |
|---------|-----------|
| `backend/CURRENT_STATE.md` | Diagnóstico do estado real do projeto |
| `backend/integrations/ai_gateway_client.py` | Cliente para AI-Gateway (aiohttp) |
| `backend/agents/base.py` | BaseAgent, AgentResult, AgentRegistry |
| `backend/agents/__init__.py` | Package init com todos os agentes registrados |
| `backend/agents/po_agent.py` | PO Agent — user stories, backlog |
| `backend/agents/pmo_agent.py` | PMO Agent — charter, WBS, reports |
| `backend/agents/frontend_dev_agent.py` | Frontend Dev Agent — componentes UI |
| `backend/agents/backend_dev_agent.py` | Backend Dev Agent — APIs, schemas |
| `backend/agents/devops_agent.py` | DevOps Agent — CI/CD, infra |
| `backend/agents/documentation_agent.py` | Documentation Agent — docs, changelog |
| `backend/QA_REVIEW_SESSION_2026-05-28.md` | Este documento |

### 2.2 Código Modificado

| Arquivo | Mudança |
|---------|---------|
| `backend/main_auth_refactored.py` | + WebSocket handler, + rotas faltantes, + helpers, porta 5150 |
| `backend/config/settings.py` | + AI_GATEWAY_ENABLED, AI_GATEWAY_URL, AI_GATEWAY_API_KEY |
| `backend/services/mcp_service.py` | GAP-MCP-03: compatible_with sanitizado via SecurityGuardrail |
| `backend/tests/test_ben_mcp_vector.py` | Teste atualizado para validar GAP-MCP-03 fechado |
| `backend/requirements.txt` | SDKs não usados removidos, versões atualizadas |
| `backend/.env.example` | + AI_GATEWAY_* settings, BACKEND_PORT 5150 |
| `launch_app.py` | Porta 5150 |
| `run_slap.bat` | Corrigido entrypoint + porta 5150 |
| `CURRENT_STATE.md` | Documentação completa do estado |
| `C:\AI-Gateway\main.py` | + `/v1/chat/completions` (OpenAI format) |

---

## 3. Estado dos Testes

**95 testes, 100% passando** ✅

| Suite | Testes | Status |
|-------|--------|--------|
| B.E.N. Unit (SecurityGuardrail) | 29 | ✅ |
| B.E.N. Integration (WebSocket flow) | 16 | ✅ |
| B.E.N. MCP Vector (manifest validation) | 10 | ✅ (GAP-MCP-03 fechado) |
| Project Routes (CRUD) | 10 | ✅ |
| Security WS (injection blocking) | 4 | ✅ |
| Notes | 1 | ✅ |

---

## 4. Pendências (para próxima sprint)

### Prioridade Alta

| # | Item | Detalhes |
|---|------|----------|
| P1 | **Integrar agentes ao fluxo do app** | AgentRegistry existe mas nenhum orquestrador chama `agent.execute()`. Revisar `review_loop.py` e `ws/orchestrator.py` para delegar para os agentes do time. |
| P2 | **QA Agent** | 9º agente da VISION. Especificação completa em `AGENT_SPECIFICATIONS.md` linha 1017. Seguir padrão dos outros 6 agentes criados. |
| P3 | **AIGatewayClient no LLM manager** | Cliente existe mas `llm_manager_simple.py` e `moe_router_simple.py` ainda não usam gateway como provider opcional. |

### Prioridade Média

| # | Item | Detalhes |
|---|------|----------|
| P4 | **Extrair helpers do ws/orchestrator** | `ws/orchestrator.py` importa 5 funções de `backend.main_auth`. Mover para `backend/utils/llm_helpers.py` e atualizar imports para desacoplar. |
| P5 | **SPA fallback + MCP init no refatorado** | `main_auth_refactored.py` precisa da rota catch-all SPA e `initialize_mcp_system()` para substituir o original completamente. |
| P6 | **Agentes legados (CTO, Security, ReviewLoop)** | Migrar para BaseAgent (herdar de `agents/base.py` e registrar no AgentRegistry). |
| P7 | **Testes E2E com LLM real** | Nenhum teste usa LLM real. Criar teste que conecta AIGatewayClient a um provider. |

### Prioridade Baixa

| # | Item | Detalhes |
|---|------|----------|
| P8 | **Orquestrador v3 (Build → Test → Deploy)** | VISION prevê pipeline completo. Atual: só Plan → Build via ReviewLoop. |

---

## 5. Arquitetura Atual dos Agentes

```
AgentRegistry (singleton)
├── CTO Agent           ✅ (legado, não migrado para BaseAgent)
├── Security Tester     ✅ (legado)
├── ReviewLoop          ✅ (legado, orquestrador parcial)
├── PO Agent            ✅ (novo, BaseAgent)
├── PMO Agent           ✅ (novo, BaseAgent)
├── Frontend Dev Agent  ✅ (novo, BaseAgent)
├── Backend Dev Agent   ✅ (novo, BaseAgent)
├── DevOps Agent        ✅ (novo, BaseAgent)
├── Documentation Agent ✅ (novo, BaseAgent)
└── QA Agent            ❌ Não implementado
```

**Nota**: Nenhum agente (novo ou legado) está integrado ao fluxo real do `ws/orchestrator` ou `main_auth.py`. Eles existem como módulos registrados mas não são chamados pelo runtime.

---

## 6. Dependências Externas

| Componente | Porta | Status |
|-----------|-------|--------|
| Open Slap backend (main_auth:app) | 5150 | ✅ Funcional |
| AI-Gateway (opcional, local) | 8000 | ✅ Disponível |

> AI-Gateway é setup local do desenvolvedor. Open Slap funciona sem ele (`AI_GATEWAY_ENABLED=false` por default).

---

## 7. Decisões de Arquitetura

1. **Porta 5150 para Open Slap** — Libera 8000 para AI-Gateway, consistente com `start_server.bat` existente
2. **BaseAgent sem ABC** — Optou-se por classe simples com `@dataclass AgentResult` em vez de ABC para manter flexibilidade e evitar rigidez na migração dos agentes legados
3. **aiohttp no AIGatewayClient** — Consistente com o resto do codebase (que usa aiohttp em vez de httpx)
4. **AI-Gateway com dois formatos** — Mantém `/v1beta/...` (Google format) para Antigravity + `/v1/chat/completions` (OpenAI format) para Open Slap
5. **GAP-MCP-03 via SecurityGuardrail** — Reutiliza o B.E.N. 2.0 existente em vez de criar sanitização separada
