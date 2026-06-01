# Changelog — Open Slap! (Público)

Este arquivo lista mudanças por versão (o “o que mudou”). Para decisões, contexto e incidentes, ver `docs/DEV_JOURNAL.md`.

---

## v2.1.2 (03/04/2026)

- Segurança: hardening do backend (CORS sem wildcard, proteção contra path traversal em /media, register sem vazamento de exceções).
- Segurança: reset de senha com token de alta entropia (substitui código numérico curto).
- Segurança: update_task_todo com whitelist de colunas (remove SQL dinâmico via f-string).
- Auth: expiração do JWT reduzida e configurável via `OPENSLAP_JWT_EXPIRE_MINUTES` (default 120).
- Auth: TTL do JWT configurável por usuário (Settings → Security → Sessão), com alerta de risco no UI.
- Chaves: armazenamento seguro de API keys não fica restrito ao Windows (fallback com criptografia local fora do DPAPI).
- Testes: suíte de regressão adicionada cobrindo os pontos acima (PRs do Eduardo Pontes).

---

## v2.1.1 (02/04/2026)

- Projetos/Kickoff em retrabalho (fluxo e UI continuam evoluindo).
- Projetos: CRUD básico (renomear/excluir) e melhorias de UX na lista.
- Kickoff: import de Markdown com abertura de task vinculada ao projeto e geração de plano inicial.
- Memória: botão “Dream” e busca no RAW (SQL) em Settings → Memory.
- Backend: correções de estabilidade (inclui crash fix em `MemoryImportPayload`) e menos fricção no dev (reload opcional).
- Frontend: dedupe/ack de mensagens do usuário no WS (reduz duplicação em reconexões).
- Packaging: checklist e scripts de verificação pré-release; build Vite sem sourcemaps.

---

## v2.1 (31/03/2026)

- Onboarding multi-etapas com persistência por usuário.
- Tela Boot simplificada com saudação baseada no SOUL.
- Configurações de LLM: chaves por provider, inferência de provider e melhorias de estado/feedback na UI.
- TODOs: evolução incremental de campos e filtros.
- Software operator: robustez no Windows e melhorias de contexto/fallback.
- Refactors: redução do App_auth.jsx e extração de settings/websocket/defaults; fatiamento incremental do backend (rotas e deps).
- Router MoE: modo LLM-first opcional com fallback seguro.

---

## v2.0 (Março/2026)

- Core: autenticação JWT, WebSocket streaming, memória SQLite, RAG/FTS, multi-providers com fallback.
- Loop plan→build: detecção de `plan` e orquestração em background.
- Mobile: ajustes de layout e responsividade.
- Execução local: whitelist dinâmica, inventário de software e melhorias de eventos.

---

# Changelog — Open Slap! (Public)

This file lists changes by version (“what changed”). For decisions, context, and incidents, see `docs/DEV_JOURNAL.md`.

---

## v2.1.2 (2026-04-03)

- Security: backend hardening (no wildcard CORS, path traversal protection on /media, register endpoint does not leak exceptions).
- Security: password reset uses a high-entropy token (replaces short numeric codes).
- Security: update_task_todo uses a column whitelist (removes dynamic SQL via f-string).
- Auth: JWT expiry reduced and configurable via `OPENSLAP_JWT_EXPIRE_MINUTES` (default 120).
- Auth: per-user JWT TTL setting (Settings → Security → Session), with risk confirmation modal.
- Keys: secure API key storage is not Windows-only (local encryption fallback outside DPAPI).
- Tests: regression tests added for the above (Eduardo Pontes PRs).

---

## v2.1.1 (2026-04-02)

- Projects/Kickoff module is being reworked (flow and UI are still evolving).
- Projects: basic CRUD (rename/delete) and UX improvements in the project list.
- Kickoff: Markdown import opens a project-linked task and emits an initial plan.
- Memory: “Dream” button + RAW (SQL) search in Settings → Memory.
- Backend: stability fixes (including `MemoryImportPayload` crash fix) and smoother dev mode (reload is optional).
- Frontend: WS user message ack/dedup to reduce duplicates after reconnects.
- Packaging: checklist + pre-release verification scripts; Vite build without sourcemaps.

---

## v2.1 (2026-03-31)

- Multi-step onboarding with per-user persistence.
- Simplified boot screen with SOUL-based greeting.
- LLM settings: per-provider keys, provider inference, improved UI state/feedback.
- TODOs: incremental schema + UI filter evolution.
- Software operator: Windows robustness and improved context/fallback behavior.
- Refactors: App_auth.jsx reduction and extraction of settings/websocket/defaults; backend incremental split (routes and deps).
- MoE router: optional LLM-first mode with safe fallback.

---

## v2.0 (March/2026)

- Core: JWT auth, WebSocket streaming, SQLite memory, RAG/FTS, multi-provider fallback.
- plan→build loop: `plan` parsing and background orchestration.
- Mobile: layout and responsiveness.
- Local execution: dynamic whitelist, software inventory, improved event ordering.
