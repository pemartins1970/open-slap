# Changelog — Open Slap! (Público)

Este arquivo lista mudanças por versão (o “o que mudou”). Para decisões, contexto e incidentes, ver `docs/DEV_JOURNAL.md`.

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

