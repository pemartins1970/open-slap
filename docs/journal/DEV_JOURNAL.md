# Diário de Desenvolvimento — Open Slap!

Este documento registra decisões arquiteturais, bugs relevantes, incidentes e escolhas de produto (incluindo o que foi adiado e por quê).

---

## Histórico v2.x (Março-Abril 2026)

### v2.1.1 — Sistema completo de chat especializado com Sabrina e MoE (14/04/2026)

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

### v2.1 — Onboarding, Boot, LLM Settings, TODOs, hardening incremental (31/03/2026)

**Mudanças aplicadas**
- Onboarding multi-etapas, com "não mostrar novamente" por usuário.
- Tela Boot simplificada com saudação baseada no SOUL e input único.
- LLM Settings: chaves por provider com inferência de provider quando omitido.
- UI de PLAN: botão "Aprovar" com estado "Aprovado/Executando...".
- Software operator: robustez Windows (subprocess), fallback de workdir e placeholders no python-inline.
- Router MoE: modo LLM-first opcional com fallback seguro para keyword routing quando não configurado.
- Refactor frontend: App_auth.jsx reduzido e responsabilidades extraídas (settings, websocket, defaults).
- Refactor backend: fatiamento progressivo de rotas e deps para reduzir risco do monólito.

**Pendências ativas (hardening)**
- Orquestrador com aprovação por etapa (pause/resume) para tornar execuções mais confiáveis.
- Melhorias de UX do TODO (parser, evitar PLAN em captura pessoal, exibir priority/due_at, persistir estado de aprovação).

### v2.1.1 — MCP Registry Dinâmico, Marketplace, Skills Dinâmicas (13/04/2026)

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

---

## Decisões de design (ADR-lite) — v2.x

### Segurança: não versionar credenciais / não confiar em .gitignore para distribuição
- Incidente real: `.env` com token foi incluído em ZIP de distribuição e precisou ser revogado.
- Regra: sempre listar explicitamente o que entra no ZIP; excluir segredos e artefatos de runtime (node_modules, dist, caches, bancos locais).

### Skills como sistema real (não decoração)
- Skills foram estruturadas como objetos (`id`, `name`, `description`, `content.prompt`, etc.) para permitir injeção controlada no contexto do LLM.

### MoE router com fallback determinístico
- Keyword routing é o baseline.
- LLM-first routing (quando habilitado) deve falhar "rápido" e cair para keyword routing sem custo de timeout quando não configurado.

### MCP Registry: security-first compatibility validation
- `compatible_with` field is mandatory and must include "openslap" for Open Slap!
- Prevents PRO-only MCPs from being installed in Open version (security boundary)
- Async loader with timeout ensures system availability even with offline MCPs

---

## V3.0 (Maio 2026)

### [2026-05-19] — Transição para V3.0 e Implementação do MVP

**Contexto:** A versão 2.2 atingiu um platô em relação à integração orgânica das ideias do usuário com o sistema de Projetos e Tarefas. O Open Claw surgiu forte com sua simplicidade voltada para mensageria.

**Decisão Arquitetural:** Em vez de focar apenas no chat, vamos aprimorar o Open Slap! para ser a ferramenta definitiva de **Deep Work** e gestão complexa.

**Próximos Passos Iniciais:**
1. Criação do **Motor de Notas** (Knowledge Base) usando `notes_fts` no SQLite, que alimentará as respostas do Agente (Brain/Soul).
2. Reativação do **B.E.N. 2.0 (Security Guardrail)**, que atualmente está como um *stub*. Adicionaremos roteamento com LLM pequeno ou heurísticas fortes para impedir Prompt Injections indiretos.

**Ações Realizadas:**
- Todo o projeto foi migrado de `open-slap-2.2.10` para `open-slap-prototipo-3.0`.
- **B.E.N. 2.0 integrado** ao `main_auth.py` e `orchestrator.py` com detecções robustas de comandos de sistema, injeções e blocos maliciosos em Python.
- **Módulo de Teste de Chaves**: Nova rota `/api/settings/llm/keys/test` adicionada ao backend.
- **Aprimoramento de Interface (Onboarding)**: Redesenhada a modal de onboarding em `OnboardingModal.jsx`.
- **Correção no Salvamento do SOUL**: Divergências entre formato JSON e rota `/api/soul` corrigidas.
- **Split-View de Notas Integrada**: Painel principal de Notas com barra lateral, filtros e editor Markdown.
- **Suporte a Governança de Projetos Híbridos (PMBOK/Agile)**: Modo Especialista com TAP, Kanban, Métricas, Stakeholders, Riscos, Lições.
- **Instalação do Git**: Git instalado via `winget` (versão 2.54.0).

### [2026-05-29] — Exploração da Codebase e Mapeamento de Memória

**Contexto:** Estabelecer fundação de memória persistente para o agente opencode, permitindo continuidade entre sessões e rastreabilidade do trabalho realizado.

**Trabalho Realizado:**
- Exploração completa da codebase: estrutura de diretórios, arquivos-fonte, entrypoints.
- Criação do diretório `C:\Agent\_opencode_memory\` com os 4 arquivos JSON de memória.
- Mapeamento detalhado em `medium.json`: frontend (React + Vite + 13 packages), backend (FastAPI + SQLite + 40+ dependencies), dual codebase (5 pares original/refactored), arquitetura MoE, agentes, conectores externos.
- SQLite criado com CLI de consulta.
- Testes executados (95/95) para baseline antes de alterações.

### [2026-05-30] — SPEC P6 + Infra de Memória + Bugfixes

**Contexto:** Sprint focado em (a) completar a implementação do CTOChatAgent e documentar o fallback do orchestrator, (b) criar infraestrutura de memória persistente para o agente conversacional, (c) corrigir bugs de ambiente que impediam o Gemini de funcionar.

**Trabalho Realizado:**

**Especificação P6 — CTOChatAgent e Fallback do Orchestrator:**
- Criado `backend/agents/cto_chat_agent.py` — `CTOChatAgent(BaseAgent)` com `name="cto"`, system_prompt de 1400+ caracteres com 4 skills conversacionais.
- Atualizado `backend/agents/__init__.py` — `register_agents()` agora registra CTOChatAgent no AgentRegistry.
- 3 testes adicionados em `test_agent_llm.py`.
- Orchestrator fallback documentado em `CURRENT_STATE.md`: tabela completa com 13 IDs do MoE x AgentRegistry (4 cobertos, 9 em fallback via `else`).

**Infraestrutura de Memória do Agente:**
- Sistema de memória persistente em `C:\Agent\_opencode_memory\` com 4 camadas JSON + SQLite + CLI.
- Mapeamento completo do projeto no `medium.json`.

**Bugfixes:**
- **Gemini não carregava**: `.env` não continha `GEMINI_API_KEYS`. Criada entrada e backend reiniciado.
- **.env.example com armadilha**: `OPENROUTER_API_KEY=` descomentado com valor vazio. Corrigido para comentado.
- **init_db() ausente**: Adicionada em `db.py`.

### [2026-06-02] — Implementação Opção B: Fix B-01 + WebSocket + session_id

**Contexto:** Após QA review (2026-06-01) confirmar causa raiz do B-01, implementamos a Opção B da especificação.

**O que foi feito:**

**1. `backend/deps.py`** — `OrchestrationStartInput.session_id: Optional[str] = None` adicionado.

**2. `backend/agents/base.py:21`** — Fix B-01: `if context` → `if isinstance(context, dict)`. Impede `AttributeError` quando `context={}` (dict vazio é falsy em Python).

**3. `backend/routes/feedback_plan_routes.py`** — Substituído completamente:
- `_build_orchestration_context()`: constrói o mesmo combined_context que o WebSocketOrchestrator (soul via `get_user_soul`+`list_soul_events`+`_build_soul_markdown`, runtime via `_build_runtime_context_block`, llm override via `get_user_llm_settings`+`_safe_llm_settings`+`_get_user_api_key`).
- `_ws_send()`: envia mensagens JSON ao WebSocket, silencia erros de conexão fechada.
- `_run_orchestration()`: agora recebe `websocket` e `current_user`, constrói contexto real, passa `combined_context` e `llm_override` nos dois caminhos (agente registrado e fallback MoE).
- `start_orchestration()`: recupera WebSocket ativo via `payload.session_id` de `ws_orchestrator.active_connections`.

**4. `frontend/src/App_auth.jsx:3196`** — Payload do POST `/api/plan/orchestrate/{convId}` agora inclui `session_id: sessionId.current`.

**Decisão arquitetural:** A `_run_orchestration` de `main_auth.py` (linhas 5132+) é mais rica (priorização software_operator, injeção de projeto, url_fetch, FILES_JSON). Não unificamos agora para evitar risco de refactor. Opção B resolve os bugs documentados sem tocar em `main_auth.py`.

### [2026-06-08] — SPEC P-01: Auto-aprovação de Steps + Cleanup de Dívida Técnica

**Contexto:** Steps do tipo `plan` exigiam aprovação manual mesmo para tarefas informacionais (pesquisa, análise, documentação). O frontend já tinha toda a infraestrutura para `plan_auto` (renderer verde, useEffect de auto-execução), mas o parser `parseMessageBlocks` nunca emitia o tipo correto.

**Causa raiz:** `remaining.startsWith('```plan')` casava com ambos `plan` e `plan_auto`. O `slice` usava `'```plan'.length` (7 chars), então ````plan_auto\n...` virava `{ type: 'plan', content: '_auto\n...' }`.

**Solução:** Detectar `isAuto` via `remaining.startsWith('```plan_auto')`, usar `headerLen` dinâmico, emitir `type: plan_auto` quando aplicável.

**Dívida técnica removida:**
1. `planAutoApproveInformational` — toggle visível no `SystemSettingsPanel` que não controlava nada. O `useEffect` de auto-aprovação ignorava esta flag. Removido o toggle, o `useState`, o handler e o `localStorage` persist.
2. `buildStartProjectPrompt` — função órfã desde que os CTAs `ask_sabrina` e `start_project` foram removidos da sidebar. Seu único consumidor (`OnboardingModal.handleStartFirstTask`) foi atualizado para iniciar conversa sem `internalPrompt`.

**Decisão arquitetural:** Preferimos remover o toggle `planAutoApproveInformational` a consertá-lo porque (a) o comportamento desejado já é coberto por `planAutoApproveAll` e (b) manter um toggle que não faz nada é pior que não ter o toggle. Se no futuro houver necessidade de granularidade fina (auto-aprovar só informacionais mas não destrutivos), o `plan_auto` do lado do backend (LLM decide o tipo do bloco) é o mecanismo correto, não uma flag no frontend.

### [2026-06-12] — Phase 1 & 2 QA: RightSidebar, Textarea, WS Override, Traduções

**Contexto:** Sessão de QA após implementação Phase 1 (UI redesign) e Phase 2 (model selector session-only). Revisão externa apontou 5 pontos de falha.

**Trabalho Realizado:**
- **RightSidebar**: Simplificado de dual state (internalCollapsed + prop conflitante) para fully controlled (Option A). Estado agora em `App_auth.jsx` e `AppLayout.jsx` (dead code — rota modular inativa). Componente placeholder alinhado ao escopo Phase 1.
- **Textarea auto-expand**: Verificado que `height='auto'` reset já existia no código. Nenhum bug encontrado — a QA confirmou que o padrão `useRef`+`useEffect` é tecnicamente correto.
- **WS override propagation**: Código já tinha guard `user_llm_override.get(...) or _active.get(...)` — protege contra None/override parcial. Nenhum bug encontrado.
- **Traduções ES**: `show_status`/`hide_status` adicionados ao locale es que estava incompleto.
- **`/api/providers` bug**: Diagnosticado como timing de startup (endpoint chamado antes do llm_manager inicializar providers). Sentinela adicionada. Fechado.
- **Entry point confirmado**: `main_auth.jsx` → `App_auth.jsx` (monolito). `AppLayout.jsx` e `App_auth_modular.jsx` são dead code — não estão no caminho ativo.

**Decisão arquitetural:** RightSidebar como fully controlled (Option A) em vez de dual state — mesmo que o toggle pareça "funcionar" com dual state, qualquer componente que aceita `collapsed` como prop mas mantém estado interno divergente é uma bomba relógio. Num placeholder Phase 1 que será reescrito em Phase 3, a simplicidade vence.

**Decisão arquitetural:** WS override fix feito no backend (propagar override ao `done` event) em vez de no frontend (ignorar `fetchRuntimeLlmLabel` após done) porque o backend é a fonte autoritativa do provider/model para cada resposta.

### [2026-06-01] — QA Backlog: B-01 e B-02 — Análise de Causa Raiz

**Contexto:** Sessão inaugural no VS Code nativo (pós-migração do Trae). Revisão crítica do backlog de UX/Estabilidade/Bugs.

**Trabalho Realizado:**
- B-01 investigado: causa real identificada — `context={}` é falsy em Python (`base.py:21`), não o fallback do orchestrator.
- B-02 investigado: três problemas distintos (sem retry intra-provider, estrutura inconsistente de chaves, DB ignorado pelo runtime).
- Documento consolidado gerado: `docs/qa/qa-review-b01-b02-2026-06-01.md`.
- Backlog arquivado como spec viva com correções factuais.
- Organização dos .md da raiz para `docs/` com estrutura temática.

---

## Futuros (registrados, não implementados)

### Agente de Navegação com Interação Visual (v2.2+)
- MVP local: worker isolado (Playwright headless) com streaming de frames (WebP/JPEG) + metadados (BBox/highlight + ActionTraceID).
- Autenticação: intervenção humana apenas quando necessário, via UI local; credenciais efêmeras por domínio+sessão e nunca persistidas.
- "Worker remoto" é evolução opcional, não premissa (diferença de produto local vs SaaS).
