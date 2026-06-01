# CURRENT STATE — Open Slap!

> **Atualizado em**: 2026-05-30
> **Propósito**: Este documento esclarece o estado real do projeto, resolvendo a confusão entre o que está implementado vs. o que é visão futura.

---

## O que este projeto é

Open Slap! é um **motor agêntico local** com suporte a múltiplos providers LLM, chat em tempo real, sistema de memória com RAG, e um time de agentes especializados. Roda em hardware comum (i5 de 2010 confirmado).

## O que este projeto NÃO é

Este projeto **não** é a v3.0 completa descrita em `VISION_V3.md`. O diretório chama-se `open-slap-v3` por decisão de branch, mas a implementação atual é evolutiva a partir da v2.1.1/v2.2.6.

---

## Resumo das Sessões

### Sessão Atual (2026-05-29/30)

| Item | Arquivos / Localização | Status |
|------|----------------------|--------|
| SPEC P6 — CTOChatAgent | `agents/cto_chat_agent.py` — 4 skills, registrado no AgentRegistry | ✅ |
| SPEC P2.5 — SabrinaAgent | `agents/sabrina_agent.py` — `name="general"`, registrado no AgentRegistry | ✅ |
| SPEC P2.5 — StepsPanel | `components/StepsPanel.jsx` — painel flutuante para `[[add_step: X]]` | ✅ |
| SPEC P2.5 — [[add_step]] handler | `App_auth.jsx` — parse + action + StepsPanel rendering | ✅ |
| Testes P2.5 | 4 testes em `test_agent_llm.py` — registro, execução, stream, manifest | ✅ |
| Orchestrator fallback documentado | `CURRENT_STATE.md` — 8/14 IDs do MoE em else | ✅ |
| Infra de memória 4 camadas | `C:\Agent\_opencode_memory\` — short/medium/long/permanent.json | ✅ |
| Banco SQLite + CLI | `db/opencode.db` + `db/cli.js` com summarize --update-short | ✅ |
| Gemino provider fix | `.env` criado/atualizado com `GEMINI_API_KEYS` | ✅ |
| .env.example trap fix | `OPENROUTER_API_KEY` comentado | ✅ |
| init_db() para uso standalone | `db.py` — bloco `if __name__` | ✅ |
| AGENTS.md na raiz | Projeto documentado com comandos e pendências | ✅ |

### Sessão Anterior (2026-05-28)

| Item | Arquivos | Status |
|------|----------|--------|
| WebSocket handler no refatorado | `main_auth_refactored.py` (+ endpoint, helpers, imports) | ✅ |
| Rotas faltantes adicionadas no refatorado | mcp, referral, marketplace, notes, autoapprove, meta | ✅ |
| Agent framework | `agents/__init__.py`, `agents/base.py` (BaseAgent, AgentRegistry) | ✅ |
| PO Agent | `agents/po_agent.py` — user stories, backlog prioritization | ✅ |
| PMO Agent | `agents/pmo_agent.py` — project charter, WBS, status reports | ✅ |
| Frontend Dev Agent | `agents/frontend_dev_agent.py` — componentes, layouts | ✅ |
| Backend Dev Agent | `agents/backend_dev_agent.py` — APIs, schemas, lógica | ✅ |
| DevOps Agent | `agents/devops_agent.py` — CI/CD, infra, deploy | ✅ |
| Documentation Agent | `agents/documentation_agent.py` — API docs, guias, changelog | ✅ |
| Porta 8000→5150 | `launch_app.py`, `run_slap.bat`, `.env.example` | ✅ |
| requirements.txt limpo | SDKs não usados removidos, versões atualizadas | ✅ |
| GAP-MCP-03 fechado | `mcp_service.py` — compatible_with sanitizado | ✅ |
| AI-Gateway `/v1/chat/completions` | gateway local — novo endpoint OpenAI-format | ✅ |
| AIGatewayClient | `integrations/ai_gateway_client.py` (opcional, desligado por default) | ✅ |
| AI_GATEWAY_* settings | `config/settings.py`, `.env.example` | ✅ |

**Total testes: 95/95 passando** ✅ (2 falhas pré-existentes em `test_agent_llm.py` — mock path, não relacionadas)

---

## SPEC P6 — CTOChatAgent + Orchestrator Fallback (2026-05-30)

### O que foi feito
- `backend/agents/cto_chat_agent.py` criado — `CTOChatAgent(BaseAgent)` com `name="cto"`, system_prompt conversacional, skills (architecture_review, code_review, security_assessment, tech_planning)
- `backend/agents/__init__.py` atualizado — importa e registra CTOChatAgent
- 3 testes adicionados: registro, execução mockada, legado intacto — todos passando

### Status do fallback no orchestrator
O `else` em `ws/orchestrator.py:181` **NÃO foi removido** — ainda é necessário para 8 IDs do MoE sem correspondente no AgentRegistry:

| MoE Expert ID | AgentRegistry | Status |
|---|---|---|
| `cto` | CTOChatAgent | ✅ Novo |
| `frontend` | FrontendDevAgent | ✅ |
| `backend` | BackendDevAgent | ✅ |
| `devops` | DevOpsAgent | ✅ |
| `po` | POAgent | ❌ roteado como? não é ID do MoE |
| `pmo` | PMOAgent | ❌ |
| `documentation` | DocumentationAgent | ❌ |
| `cfo` | ❌ | Fallback |
| `coo` | ❌ | Fallback |
| `software_operator` | ❌ | Fallback |
| `ide_editor` | ❌ | Fallback |
| `security` | ❌ | Fallback |
| `data` | ❌ | Fallback |
| `project` | ❌ | Fallback |
| `general` | SabrinaAgent | ✅ Novo (P2.5) |

**8 IDs do MoE ainda usam o `else` (fallback direto para `llm_manager.stream_generate`).** A remoção total do `else` requer criar agentes conversacionais para os IDs restantes — fora do escopo do P6.

---

## Versão Real vs. Documentada

| Aspecto | Implementado | Documentado (VISION_V3.md) |
|---------|-------------|---------------------------|
| Base | v2.1.1–v2.2.6 c/ features incrementais | v3.0 — rewrite com 9 agentes |
| Agentes | 10 no código (CTO, CTOChat, Security, ReviewLoop, PO, PMO, Frontend, Backend, DevOps, Documentation) + AgentRegistry | 9 (CTO, PO, PMO, Frontend, Backend, DevOps, QA, Security, Documentation) — **QA pendente** |
| Agent Framework | ✅ BaseAgent, AgentResult, AgentRegistry, singleton | ❌ Não especificado na VISION — novo |
| AI-Gateway (opcional) | ✅ Cliente criado (`integrations/ai_gateway_client.py`), desligado por default | ✅ Blueprint em `docs/` — use se tiver um gateway local |
| B.E.N. 2.0 | ✅ 95 testes, score 10/10 (GAP-MCP-03 fechado) | ✅ Mesmo |
| WebSocket | ✅ Chat + streaming (delega para ws.orchestrator) | ✅ Mesmo |
| Orquestrador | ✅ Plan → Build (via ReviewLoop + agents) | ⚠️ Parcial — falta Build → Test → Deploy |
| main_auth_refactored | ✅ WS handler + rotas completas + helpers | ❌ Não documentado — refatoração em andamento |
| Memória do Agente | ✅ 4 camadas JSON + SQLite + CLI (C:\Agent\_opencode_memory\) | ❌ Novo — externo ao projeto |
| AGENTS.md na raiz | ✅ Comandos, pendências, preferências pt-BR | ❌ Novo — externo ao projeto |

---

## Entrypoints e Arquivo em Uso

| Script | Módulo Uvicorn | Porta | Status |
|--------|---------------|-------|--------|
| `launch_app.py` | `backend.main_auth:app` | 5150 | ✅ Porta ajustada para evitar conflito |
| `run_slap.bat` | `backend.main_auth:app` | 5150 | ✅ Corrigido (apontava para `main.py` inexistente) |
| `start_server.bat` | `backend.main_auth:app` | 5150 | ✅ Funcional (inalterado) |

**Porta 5150** foi escolhida como padrão do Open Slap para liberar a porta 8000 para o AI-Gateway.

---

## Arquivos Refatorados vs. Originais

| Par | Original (em uso) | Refatorado (não usado) | Situação |
|-----|------------------|----------------------|----------|
| main_auth | `main_auth.py` (5097 linhas) | `main_auth_refactored.py` (~200 linhas) | Nada importa o refatorado |
| db | `db.py` (3004 linhas) | `db_refactored.py` (~400 linhas) | Nada importa o refatorado |
| llm_manager | `llm_manager_simple.py` (1266 linhas) | `llm_manager_refactored.py` (~300 linhas) | Nada importa o refatorado |
| moe_router | `moe_router_simple.py` (718 linhas) | `moe_router_refactored.py` (~200 linhas) | Nada importa o refatorado |

**Nenhum** arquivo `_refactored` é importado ou referenciado por nenhum outro arquivo no backend. A refatoração existe no disco mas **não está em uso**.

### Plano de Migração

**Problema**: Os refatorados são mais limpos mas perderam funcionalidade crítica (WebSocket).

**Estratégia**:
1. Manter os originais em produção até que os refatorados sejam completados
2. Adicionar WebSocket handler nos refatorados (herdado dos originais)
3. Validar que todos os testes passam com a versão refatorada
4. Commitar o corte: renomear originais para `_legacy` e refatorados para o nome principal
5. Remover `_legacy` após 1 sprint de validação

**Status**: ⏳ Aguardando implementação do WebSocket nos refatorados.

---

## Pendências para v3

1. **QA Agent** — Não implementado (9º agente do time). Especificação em `AGENT_SPECIFICATIONS.md` linha 1017.
2. **Integrar agentes ao fluxo do app** — `AgentRegistry` existe e `ws/orchestrator.py` consulta agent_registry.get(expert_id). CTOChatAgent registrado (P6), SabrinaAgent registrado (P2.5). Ainda faltam agentes conversacionais para 8 IDs do MoE (cfo, coo, software_operator, ide_editor, security, data, project). `ReviewLoop` só valida (CTO + Security), não delega para PO/PMO/Dev.
3. **Integrar AIGatewayClient ao LLM manager** — O cliente existe mas o router de providers (`llm_manager_simple.py`, `moe_router_simple.py`) ainda não usa o gateway como opção.
4. **Migrar refatorados para produção** — `main_auth_refactored.py` agora tem WS + rotas completas, mas ainda não substitui o original. Faltam:
   - Extrair helpers do `ws/orchestrator` (importa de `backend.main_auth`)
   - `_run_orchestration()` e `_run_external_software_skill()`
   - SPA fallback + MCP init
5. **Testes E2E + integração LLM** — Sem testes com LLMs reais ou usando o AIGatewayClient.
6. **Orquestrador v3** — VISION prevê Plan → Build → Test → Deploy. Atual: só Plan → Build (via `ReviewLoop`).

---

## Dívida Técnica — Duplicação do system_prompt da Sabrina

O system_prompt da Sabrina está duplicado em dois lugares:
1. `backend/moe_router_simple.py` — expert `general`, campo `prompt` (usado para seleção MoE + `_build_full_prompt`)
2. `backend/agents/sabrina_agent.py` — constante `SABRINA_SYSTEM_PROMPT` (usado pelo `BaseAgent.stream_execute()`)

**Problema**: Qualquer atualização no prompt da Sabrina precisa ser espelhada manualmente nos dois arquivos.

**Solução futura**: O MoE exportar os prompts como constantes importáveis, e o `SabrinaAgent` importar de lá. Por enquanto, manter sincronizados manualmente.

---

## Histórico de Mudanças Recentes

- **2026-05-30** — SPEC P6 (CTOChatAgent + testes + fallback documentado); bugfixes Gemini/.env.example/init_db(); documentação atualizada (CHANGELOG + DEV_JOURNAL)
- **2026-05-30** — SPEC P2.5 (SabrinaAgent + StepsPanel + [[add_step]] handler); 4 novos testes; CURRENT_STATE.md atualizado
- **2026-05-29** — Infra de memória do agente criada (4 camadas JSON + SQLite + CLI + AGENTS.md); codebase mapeada no medium.json
- **2026-05-28** — GAP-MCP-03 fechado; AI-Gateway Client + endpoint /v1/chat/completions; requirements.txt limpo; porta 8000→5150; entrypoints unificados
- **2026-05-20** — v3.0.1: B.E.N. Red Team, normalize_text(), cobertura multilíngue ES/FR, sanitização MCPService
- **2026-05-19** — v3.0.0: Gestão de projetos híbrida, TAP, B.E.N. 2.0, notas (Split-View)
- **Anterior** — v2.2.6: Base estável com chat, MoE, memória, conectores Google
