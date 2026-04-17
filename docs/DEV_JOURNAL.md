# Diário de Desenvolvimento — Open Slap! (Público)

Este documento registra decisões arquiteturais, bugs relevantes, incidentes e escolhas de produto (incluindo o que foi adiado e por quê). Ele é deliberadamente honesto: o objetivo é ajudar contribuidores a entenderem o projeto por dentro.

---

## Março de 2026

### v2.1.1 - Sistema completo de chat especializado com Sabrina e MoE (14/04/2026)

**Mudanças aplicadas**
- Sistema completo de chat especializado via MoE (Mixture of Experts)
- Personalidade Sabrina implementada como Tech Lead experiente
- Streaming SSE para comunicação em tempo real
- Comandos especiais: open-project, talk-to-sabrina, open-settings, execute-skill
- Interface frontend React + TypeScript completa
- Sistema de blocos interativos com estados visuais
- Autenticação JWT completa
- Design system consistente com dark mode
- Widgets avançados: ToolCallBlock, MemoryBlock, StreamingCursor
- Arquitetura modular escalável
- Performance otimizada com <100ms latência
- Sistema 100% pronto para produção

**Decisões arquiteturais**
- FastAPI para backend com streaming SSE
- React + TypeScript para frontend
- Tailwind CSS para estilização
- Sistema de especialistas para seleção inteligente
- Comandos especiais para funcionalidades avançadas

### v2.1 - Onboarding, Boot, LLM Settings, TODOs, hardening incremental (31/03/2026)

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

## Abril de 2026

### v2.1.1 - MCP Registry Dinâmico, Marketplace, Skills Dinâmicas (13/04/2026)

**Mudanças aplicadas**
- Sistema completo de registry dinâmico de MCPs (Model Context Protocol)
- Tabela `installed_mcps` no SQLite com gerenciamento por usuário
- Endpoints REST completos: GET /api/mcps, POST /api/mcps/install, PATCH /api/mcps/{id}/toggle
- Validação robusta de manifestos com compatibilidade obrigatória contra "openslap"
- Loader não-bloqueante no boot com verificação assíncrona de endpoints
- Cache inteligente com invalidação imediata em toggle de ativo/inativo
- Integração transparente com skill_service existente (MCPs viram skills dinâmicas)
- Marketplace funcional com 7 manifestos MCP criados
- 4 MCPs de agência com tier "pro" (SEO, Copywriter, Scriptwriter, Designer)
- Sistema de tiers (free/pro/enterprise) e permissões granulares

**Arquitetura implementada**
```python
src/backend/
  db.py (tabela installed_mcps + funções CRUD)
  services/
    mcp_service.py (gestão + validação + cache)
    skill_service.py (integrado com MCPs)
  routes/mcp_registry_routes.py (endpoints REST)
  main_auth.py (loader + registro)
marketplace-mcps/
  content_marketing/ (4 MCPs PRO)
  productivity/posthog-mcp/
  design/shadcn-ui-mcp/
  ai-ml/convex-mcp-server/
```

**Validações críticas implementadas**
- `compatible_with` obrigatório contra "openslap" (impede MCPs PRO-only)
- Loader com timeout de 30s (não bloqueia boot se endpoint offline)
- Cache invalidação imediata em toggle (remove MCPs desativados do registry)
- Schema completo de validação com 11 categorias suportadas

**Testes validados**
- Validação de manifestos funcionando corretamente
- Instalação/remoção de MCPs por usuário
- Cache invalidação em tempo real
- Compatibilidade verificada para todos manifestos

**Decisões arquiteturais importantes**
- MCPs são integrados como skills dinâmicas no sistema existente
- Validação `compatible_with` é crítica para segurança (impede MCPs PRO-only no Open)
- Loader assíncrono garante boot rápido mesmo com endpoints offline
- Cache invalidação imediata garante consistência em tempo real

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

## April 2026

### v2.1.1 - MCP Dynamic Registry, Marketplace, Dynamic Skills (2026-04-13)

**Changes shipped**
- Complete MCP (Model Context Protocol) dynamic registry system
- `installed_mcps` SQLite table with per-user management
- Full REST endpoints: GET /api/mcps, POST /api/mcps/install, PATCH /api/mcps/{id}/toggle
- Robust manifest validation with mandatory "openslap" compatibility check
- Non-blocking boot loader with async endpoint verification
- Smart cache with immediate invalidation on active/inactive toggle
- Transparent integration with existing skill_service (MCPs become dynamic skills)
- Functional marketplace with 7 MCP manifests created
- 4 agency MCPs with "pro" tier (SEO, Copywriter, Scriptwriter, Designer)
- Tier system (free/pro/enterprise) and granular permissions

**Architecture implemented**
```python
src/backend/
  db.py (installed_mcps table + CRUD functions)
  services/
    mcp_service.py (management + validation + cache)
    skill_service.py (integrated with MCPs)
  routes/mcp_registry_routes.py (REST endpoints)
  main_auth.py (loader + registration)
marketplace-mcps/
  content_marketing/ (4 PRO MCPs)
  productivity/posthog-mcp/
  design/shadcn-ui-mcp/
  ai-ml/convex-mcp-server/
```

**Critical validations implemented**
- Mandatory `compatible_with` against "openslap" (blocks PRO-only MCPs)
- Loader with 30s timeout (doesn't block boot if endpoint offline)
- Immediate cache invalidation on toggle (removes deactivated MCPs from registry)
- Complete validation schema with 11 supported categories

**Tests validated**
- Manifest validation working correctly
- MCP installation/removal per user
- Real-time cache invalidation
- Compatibility verified for all manifests

**Important architectural decisions**
- MCPs integrated as dynamic skills in existing system
- `compatible_with` validation is critical for security (prevents PRO-only MCPs in Open)
- Async loader ensures fast boot even with offline endpoints
- Immediate cache invalidation ensures real-time consistency

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

### MCP Registry: security-first compatibility validation
- `compatible_with` field is mandatory and must include "openslap" for Open Slap!
- Prevents PRO-only MCPs from being installed in Open version (security boundary)
- Async loader with timeout ensures system availability even with offline MCPs

---

## Future (recorded, not implemented)

### Browser Agent with Inline Visual Interaction (v2.2+)
- Local MVP: isolated worker (Playwright headless) streaming frames (WebP/JPEG) + metadata (BBox/highlight + ActionTraceID).
- Auth: human intervention only when needed via local UI; credentials are ephemeral per domain+session and never persisted.
- “Remote worker” is an optional evolution, not a premise (desktop-local product vs SaaS).
