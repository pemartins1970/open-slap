# Diário de Desenvolvimento — Open Slap! (Público)

Este documento registra decisões arquiteturais, bugs relevantes, incidentes e escolhas de produto (incluindo o que foi adiado e por quê). Ele é deliberadamente honesto: o objetivo é ajudar contribuidores a entenderem o projeto por dentro.

---

## Março de 2026

### v2.1 — Onboarding, Boot, LLM Settings, TODOs, hardening incremental (31/03/2026)

**Mudanças aplicadas**
- Onboarding multi-etapas, com “não mostrar novamente” por usuário.
- Tela Boot simplificada com saudação baseada no SOUL e input único.
- LLM Settings: chaves por provider com inferência de provider quando omitido.
- UI de PLAN: botão “Aprovar” com estado “Aprovado/Executando…”.
- Software operator: robustez Windows (subprocess), fallback de workdir e placeholders no python-inline.
- Router MoE: modo LLM-first opcional com fallback seguro para keyword routing quando não configurado.
- Refactor frontend: App_auth.jsx reduzido e responsabilidades extraídas (settings, websocket, defaults).
- Refactor backend: fatiamento progressivo de rotas e deps para reduzir risco do monólito.

**Pendências ativas (hardening)**
- Orquestrador com aprovação por etapa (pause/resume) para tornar execuções mais confiáveis.
- Melhorias de UX do TODO (parser, evitar PLAN em captura pessoal, exibir priority/due_at, persistir estado de aprovação).

---

## Decisões de design (ADR-lite)

### Segurança: não versionar credenciais / não confiar em .gitignore para distribuição
- Incidente real: `.env` com token foi incluído em ZIP de distribuição e precisou ser revogado.
- Regra: sempre listar explicitamente o que entra no ZIP; excluir segredos e artefatos de runtime (node_modules, dist, caches, bancos locais).

### Skills como sistema real (não decoração)
- Skills foram estruturadas como objetos (`id`, `name`, `description`, `content.prompt`, etc.) para permitir injeção controlada no contexto do LLM.

### MoE router com fallback determinístico
- Keyword routing é o baseline.
- LLM-first routing (quando habilitado) deve falhar “rápido” e cair para keyword routing sem custo de timeout quando não configurado.

---

## Futuros (registrados, não implementados)

### Agente de Navegação com Interação Visual (v2.2+)
- MVP local: worker isolado (Playwright headless) com streaming de frames (WebP/JPEG) + metadados (BBox/highlight + ActionTraceID).
- Autenticação: intervenção humana apenas quando necessário, via UI local; credenciais efêmeras por domínio+sessão e nunca persistidas.
- “Worker remoto” é evolução opcional, não premissa (diferença de produto local vs SaaS).

---

# Development Journal — Open Slap! (Public)

This document records architectural decisions, relevant bugs, incidents, and product choices (including what was deferred and why). It is intentionally honest: the goal is to help contributors understand the project from the inside.

---

## March 2026

### v2.1 — Onboarding, Boot, LLM Settings, TODOs, incremental hardening (2026-03-31)

**Changes shipped**
- Multi-step onboarding, with per-user “don’t show again”.
- Simplified boot screen with SOUL-based greeting and single input.
- LLM Settings: per-provider keys with provider inference when omitted.
- PLAN UI: “Approve” button with “Approved/Running…” state.
- Software operator: Windows robustness (subprocess), workdir fallback, python-inline placeholders handling.
- MoE router: optional LLM-first mode with safe fallback to keyword routing when not configured.
- Frontend refactor: App_auth.jsx reduced, responsibilities extracted (settings, websocket, defaults).
- Backend refactor: incremental route/deps extraction to reduce monolith risk.

**Open items (hardening)**
- Step-by-step plan approval (pause/resume) to make executions reliable.
- TODO UX improvements (parser, avoid PLAN for personal capture, show priority/due_at, persist approval state).

---

## Design Decisions (ADR-lite)

### Security: never ship credentials / don’t rely on .gitignore for distribution
- Real incident: `.env` containing a token was included in a distribution ZIP and had to be revoked.
- Rule: explicitly list ZIP contents; exclude secrets and runtime artifacts (node_modules, dist, caches, local DBs).

### Skills as a real system (not decoration)
- Skills are structured objects to enable controlled injection into LLM context.

### MoE router with deterministic fallback
- Keyword routing is the baseline.
- LLM-first routing (when enabled) must fail fast and fall back to keyword routing with no per-message timeout when not configured.

---

## Future (recorded, not implemented)

### Browser Agent with Inline Visual Interaction (v2.2+)
- Local MVP: isolated worker (Playwright headless) streaming frames (WebP/JPEG) + metadata (BBox/highlight + ActionTraceID).
- Auth: human intervention only when needed via local UI; credentials are ephemeral per domain+session and never persisted.
- “Remote worker” is an optional evolution, not a premise (desktop-local product vs SaaS).

