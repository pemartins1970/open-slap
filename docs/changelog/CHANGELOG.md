# Changelog — Open Slap!

Todas as mudanças notáveis. Para decisões, contexto e incidentes, ver `docs/journal/DEV_JOURNAL.md`.

---

## [3.0.5] - 2026-06-12

### Added
- **RightSidebar colapsável**: Status column agora com toggle ◀/▶ (36px colapsado / 320px expandido). Componente fully controlled (Option A), estado no App_auth.jsx.
- **Settings "Configured Providers" colapsável**: Seção com header clicável + seta ▾ rotacionável.
- **Traduções ES**: `show_status`, `hide_status`, `chat_input_placeholder` adicionados ao locale es.

### Fixed
- **Textarea auto-expand**: Substituído `onInput` por `useRef` + `useEffect` com reset `height='auto'` — corrige bug em que textarea nunca encolhia ao apagar linhas em componente controlado React.
- **WS override não propagava ao header**: `_last_provider`/`_last_model` agora inicializados do `user_llm_override` logo após aplicação do override (`orchestrator.py:197-200`), não mais do DB. O `done` event carrega o provider/model selecionado pelo usuário.
- **RightSidebar anti-pattern**: Removido dual state (internalCollapsed + prop conflitante). Agora é totalmente controlado via props.

### Changed
- **Send button**: `fontWeight: 700` no ↑ arrow.
- **Input area**: `overflow: hidden` no textarea; `inputContainer` unified com border + `--bg2`.

## [3.0.4] - 2026-06-08

### Added
- **SPEC P-01 — Auto-aprovação de `plan_auto`**: `parseMessageBlocks` em `App_auth.jsx` agora detecta ````plan_auto` e emite `type: 'plan_auto'`. Blocos informacionais (pesquisa, análise, docs) executam automaticamente sem aprovação manual.

### Removed
- **`planAutoApproveInformational` toggle**: removido de `SystemSettingsPanel.jsx` e `App_auth.jsx`. Era dívida técnica visível — o toggle existia mas o `useEffect` de auto-aprovação nunca o consultava, tornando-o inoperante.
- **`buildStartProjectPrompt`**: função removida de `App_auth.jsx`, prop removida de `OnboardingModal.jsx`. Órfã desde a remoção dos CTAs da sidebar.

### Fixed
- **P-01**: Bloco ````plan_auto` era parseado como tipo `plan` (laranja, exigia aprovação) porque o slice sempre usava `'```plan'.length` (7 chars), engolindo o sufixo `_auto`. Agora detecta header completo e emite o tipo correto.

## [3.0.3] - 2026-06-02

### Added
- **Opção B — Feedback & Plan Routes**: `_build_orchestration_context()` em `feedback_plan_routes.py` constrói o mesmo `combined_context` que o WebSocketOrchestrator (soul + runtime + llm settings).
- **WebSocket em tempo real na orquestração**: `_run_orchestration` agora recebe `websocket` opcional e transmite chunks/status/done. Frontend envia `session_id` no payload.
- **`session_id` no `OrchestrationStartInput`**: novo campo em `deps.py` para conectar frontend ao WebSocket ativo.

### Fixed
- **B-01 (crítico)**: `context={}` é falsy em Python — `base.py:21` mudou de `if context` para `isinstance(context, dict)`. Agora agentes registrados produzem output no chat.
- **B-01 — combined_context vazio**: `_run_orchestration` passava `context={}` e `user_context=""`. Agora constrói contexto real com soul do usuário, runtime context block e llm_override.
- **B-01 — MoE sem llm_override**: `stream_generate()` no fallback agora recebe `user_llm_override`, respeitando provider/modelo preferido do usuário.

### Changed
- `backend/routes/feedback_plan_routes.py` — arquivo substituído: nova `_build_orchestration_context()`, `_ws_send()`, `_run_orchestration` com parâmetros websocket/current_user, imports adicionais (main_auth, deps, db).
- `backend/agents/base.py:21` — guard `if context` → `if isinstance(context, dict)`.
- `backend/deps.py:149` — `session_id: Optional[str] = None` adicionado.
- `frontend/src/App_auth.jsx:3196` — payload agora inclui `session_id: sessionId.current`.

## [3.0.2] - 2026-05-30

### Added
- **SPEC P6 — CTOChatAgent**: `backend/agents/cto_chat_agent.py` criado. `CTOChatAgent(BaseAgent)` com `name="cto"`, system_prompt conversacional e 4 skills (architecture_review, code_review, security_assessment, tech_planning). Registrado via `agent_registry.register()`.
- **Orchestrator Fallback Documentado**: Mapeamento completo de quais IDs do MoE têm correspondente no AgentRegistry (4/13 cobertos, 9 em fallback). `ws/orchestrator.py` else mantido intencionalmente.
- **Testes P6**: 3 novos testes em `test_agent_llm.py` — registro, execução mockada, legado inalterado.
- **Infra de Memória do Agente**: Sistema externo de memória persistente com 4 camadas JSON (short/medium/long/permanent) + SQLite integral com CLI (`db/cli.js`). Localizado em `C:\Agent\_opencode_memory\`.

### Fixed
- **Gemini Provider não carregava**: `.env` não existia. `_load_providers()` no `llm_manager_simple.py` só lê de env vars, nunca do banco. Criado `.env` com `GEMINI_API_KEYS` + reinício do backend via venv Python.
- **.env.example com armadilha**: `OPENROUTER_API_KEY=` estava descomentado com valor vazio — provider registrado sem chave. Corrigido para comentado.

## [3.0.1] - 2026-05-20

### Added
- **B.E.N. 2.0 Red Team — Suite de Testes Completa**: 78 testes automatizados cobrindo 9 categorias de ataque (prompt injection, jailbreak, system prompt leak, command injection OS, code injection, bypass encoding, multilíngue, MCP abuse, falsos positivos). Dataset de 32 payloads em `backend/tests/security_payloads.json`.
- **Normalização de Texto Anti-Evasão** (`normalize_text()`): B.E.N. agora detecta ataques via leet speak (`ign0re`), espaçamento entre letras (`i g n o r e`) e homoglifos Unicode Cyrillic (і → i) antes de aplicar os padrões regex.
- **Cobertura Multilíngue ES/FR**: Novos padrões em `PROMPT_INJECTION_PATTERNS` para Espanhol (`olvidar/ignorar + reglas/instrucciones`) e Francês (`oublier/oubliez + instructions/regles`).
- **Code Injection em `evaluate()`**: `SecurityGuardrail.evaluate()` agora verifica `BLOCKED_CODE_PATTERNS` além de `BLOCKED_COMMAND_PATTERNS`, bloqueando scripts maliciosos enviados como mensagens de chat.
- **MCPService Sanitizado via B.E.N.**: `MCPService.validate_manifest()` agora passa campos `name`, `description`, `id` e itens de `tools` pelo guardrail antes de aceitar o manifesto.
- **TraceLogger Step Counter por Sessão**: `WebSocketOrchestrator` mantém contador incremental de steps por `session_id`, evitando sobrescrita de traces da mesma sessão.
- **Testes de Rotas de Projetos**: `backend/tests/test_project_routes.py` com 12 testes unitários cobrindo GET/POST/PUT/DELETE `/api/projects` (happy path, 401, 404, 400).
- **`METRICAS_BASELINE.md`**: Relatório de segurança documentando baseline (7.5/10) e resultado pós-hardening (9/10).

### Changed
- **Score de Segurança B.E.N. 2.0**: 7.5/10 → **9/10** após fechamento de 5 gaps críticos.
- **Taxa de bloqueio `evaluate()`**: 70.4% → **100%** (todos os 27 vetores de ataque bloqueados).
- **XFails eliminados**: 8 gaps documentados como xfail → 0 xfails (todos resolvidos).

### Fixed
- **GAP-01**: Bypass via encoding não detectado — resolvido com `normalize_text()`.
- **GAP-02**: Multilíngue ES/FR ausente — resolvido com novos padrões regex.
- **GAP-03**: Code injection passava por `evaluate()` — resolvido adicionando loop `BLOCKED_CODE_PATTERNS`.
- **GAP-04**: MCPService aceitava injection em campos de texto — resolvido com sanitização B.E.N.
- **GAP-05**: TraceLogger sobrescrevia traces da mesma sessão — resolvido com `session_steps` dict.

## [3.0.0] - 2026-05-19
### Added
- **Gestão de Projetos Híbrida (Modo Especialista)**: Nova interface dashboard de gerenciamento de projetos com 6 abas dinâmicas (TAP, Kanban, Métricas de Sucesso, Stakeholders, Riscos/Roadmap, Retrospectiva/Lições).
- **Termo de Abertura de Projetos (TAP)**: Modal de cadastro manual do TAP ao criar novos projetos ou editar projetos existentes.
- **Persistência no Backend**: Atualização das rotas e banco de dados SQLite para persistir informações estruturadas de governança de projetos (campos `tap_json`, `expert_mode` e novos endpoints/métodos para persistir dados complexos).
- **Instalação do Git**: Git configurado e instalado via winget para suporte a controle de versão no ambiente do usuário.
- **B.E.N. 2.0 Security Guardrail**: Implementado filtro heurístico robusto para Prompt Injection, comandos perigosos do SO (ex: `rm -rf`, `format C:`) e execuções em Python no WebSocket.
- **Validação ao Vivo de Chaves**: Adicionado endpoint `/api/settings/llm/keys/test` para verificar chaves de API (Gemini, OpenAI, Groq, Anthropic, OpenRouter) antes do salvamento.
- **Sistema de Notas (Obsidian Split-View)**: Nova interface e integração com banco de dados para criação, edição, exclusão de notas estruturadas com busca por FTS5 e associação a Projetos.

### Changed
- **Onboarding Redesenhado**: Layout expandido para tela cheia e retangular padrão, evitando overflow nas telas de configuração.
- **Configurações de Provedores**: Integração direta da validação ao vivo ("Testar") na tela de onboarding.

### Fixed
- **Salvamento do SOUL**: Corrigido mapeamento de dicionários e argumentos posicionais no banco de dados que causava falha ao salvar as informações do SOUL no onboarding.
- **Dependências e Imports Circulares**: Resolvido conflito de importação circular no orquestrador WebSocket.

---

## v2.1.2 (03/04/2026)

- Segurança: hardening do backend (CORS sem wildcard, proteção contra path traversal em /media, register sem vazamento de exceções).
- Segurança: reset de senha com token de alta entropia (substitui código numérico curto).
- Segurança: update_task_todo com whitelist de colunas (remove SQL dinâmico via f-string).
- Auth: expiração do JWT reduzida e configurável via `OPENSLAP_JWT_EXPIRE_MINUTES` (default 120).
- Auth: TTL do JWT configurável por usuário (Settings → Security → Sessão), com alerta de risco no UI.
- Chaves: armazenamento seguro de API keys não fica restrito ao Windows (fallback com criptografia local fora do DPAPI).

---

## v2.1.1 (02/04/2026)

- Projetos/Kickoff em retrabalho (fluxo e UI continuam evoluindo).
- Projetos: CRUD básico (renomear/excluir) e melhorias de UX na lista.
- Kickoff: import de Markdown com abertura de task vinculada ao projeto e geração de plano inicial.
- Memória: botão "Dream" e busca no RAW (SQL) em Settings → Memory.
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
