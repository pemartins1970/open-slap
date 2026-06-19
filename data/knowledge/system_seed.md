# System Seed — Open Slap! Platform Self-Knowledge

This document describes what **Open Slap!** is, how it works, what it can and cannot do. It is injectable as context into any agent's system prompt so the model understands the platform it runs on.

---

## What is Open Slap!?

Open Slap! is a **multi-expert AI platform** with:
- A Python/FastAPI backend (WebSocket + REST)
- A React frontend
- Multiple LLM providers (Gemini, Groq, OpenAI, OpenRouter, Ollama, Claude)
- An agent registry with specialized agents
- A three-layer memory system (short-term, mid-term chronicle, long-term SOUL)
- A security guardrail system (B.E.N. 2.0)
- An MCP integration layer for tool execution

The primary user-facing agent is **Sabrina**, a generalist executive assistant registered as `general` in the MoE router. Other agents (CTO, CFO, COO, software_operator, security, data, ide_editor) handle specialized domains via explicit routing or MoE keyword matching.

---

## Architecture Layers

```
Frontend (React) ←→ WebSocket / REST ←→ FastAPI Backend
                                              │
                    ┌─────────────────────────┼─────────────────────────┐
                    │                         │                         │
               B.E.N. 2.0              MoE Router               AgentRegistry
            (security_guardrail)     (moe_router_simple)       (agents/base.py)
                    │                         │                         │
                    └─────────────────────────┼─────────────────────────┘
                                              │
                                    llm_manager_simple
                                    (LLM provider abstraction)
                                              │
                                    ┌─────────┴─────────┐
                                    │                   │
                              Chronicle           SOUL
                           (mid-term mem)     (long-term mem)
```

---

## Core Components

### Backend Stack
- **Framework**: FastAPI + uvicorn
- **Database**: SQLite via `backend/db.py` (custom manager with connection pooling)
- **WebSocket**: `ws/orchestrator.py` — `WebSocketOrchestrator` (single point of entry for all chat)
- **LLM Abstraction**: `llm_manager_simple.py` — wraps all providers behind a unified streaming interface
- **MoE Router**: `moe_router_simple.py` — keyword-based expert selection, with Sabrina as default (`general`)
- **Agent System**: `agents/base.py` — `BaseAgent` + `AgentRegistry` for structured agent execution

### Agents (registered in AgentRegistry)
| Agent | ID | Role |
|-------|----|------|
| Sabrina | `general` | Executive assistant, orchestrator |
| CTO | `cto` | Technical architecture, code generation |
| CFO | `cfo` | Financial analysis, budgeting |
| COO | `coo` | Operations, workflow |
| Software Operator | `software_operator` | Automation, CLI execution |
| Security | `security` | Security analysis, compliance |
| Data | `data` | Data analysis, visualization |
| IDE Editor | `ide_editor` | Code editing, refactoring |

### Security (B.E.N. 2.0)
Pre-LLM filter in `security_guardrail.py`. Blocks prompt injection, destructive OS commands, and malicious code patterns. Runs on every user message before reaching the model.

### Memory System
Three layers:
1. **Short-term**: Context window (`combined_context`) — rebuilt every turn
2. **Mid-term**: `chronicle.py` — SQLite + FTS5, write-only from pipeline, queried via `/search` and `/standup`
3. **Long-term**: `soul_extractor.py` + DB — persistent user profile (name, programming_language), injected into every LLM call

### File Writing
The LLM can persist files via `<FILES_JSON>` blocks in responses. The orchestrator intercepts these (`ws/orchestrator.py:276-301`) and writes them to disk if `allow_file_write` permission is enabled.

---

## Capabilities

- **Multi-provider LLM**: Switch between 6 providers with per-user API keys
- **Agent routing**: Explicit (`force_expert_id`) or implicit (MoE keyword matching)
- **Persistent user profile**: SOUL accumulates across sessions
- **Session memory**: Chronicle records every exchange with FTS5 search
- **File persistence**: LLM can write files to the workspace
- **Security filtering**: Pre-LLM prompt injection + command detection
- **Audit trail**: Every interaction logged to traces.jsonl

---

## Known Limitations (GAPs)

These are documented in detail in the companion architecture docs:
- **HARNESS.md**: 6 GAPs — uncalled `validate_code_execution()`, no trace query/rotation, no rate limiting, no circuit breaker, no input size limits, no security notifications
- **MEMORY_PIPELINE.md**: 6 GAPs — Project Brain is a stub, SOUL only extracts from assistant messages, only 2 SOUL fields, no SOUL editing UI, no memory decay/consolidation, LLM never reads Chronicle automatically

---

## How This Document Is Used

This `system_seed.md` is **not a persona prompt**. The persona prompt for Sabrina lives in `backend/agents/sabrina_agent.py` and `backend/moe_router_simple.py`.

This document is **platform self-knowledge** — it describes the system to the system. It should be:
- Injected as context when an agent needs to understand the platform
- Referenced when the LLM answers questions about Open Slap! internals
- Updated as the platform evolves (new components, changed architecture, new GAPs)
