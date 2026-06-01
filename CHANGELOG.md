# CHANGELOG - Open Slap! v3.0

Todas as mudanças notáveis para este projeto a partir da versão protótipo 3.0 serão documentadas neste arquivo.

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
