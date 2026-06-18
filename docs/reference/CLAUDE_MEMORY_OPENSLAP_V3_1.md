# Memória de Projeto — Open Slap! v3
**Mantido por**: Claude (Anthropic)  
**Última atualização**: 2026-05-30  
**Propósito**: Registro persistente de contexto, decisões arquiteturais e visão do produto para uso nas sessões de trabalho.

---

## 1. O que é o Open Slap!

Motor agêntico open source (Apache 2.0) para makers, desenvolvedores e escolas públicas. Roda em hardware de 2010 (i5, sem GPU). Aceita LLMs locais (Ollama) e remotas (Gemini, Groq, OpenAI, OpenRouter). O código é intencionalmente exposto e legível.

**Não é**: produto comercial, plataforma para usuário final, concorrente dos produtos Slap! PRO derivados dele.

**É**: motor base, ambiente de pesquisa, laboratório de arquitetura agêntica.

**Autor**: Pê Martins (@pemartins1970)

---

## 2. Arquitetura Atual (estado real em 2026-05-30)

### Stack
- **Backend**: Python + FastAPI, porta 5150
- **Frontend**: React + Vite, `App_auth.jsx` (~8040 linhas) é o entry point ativo
- **Banco**: SQLite
- **Comunicação chat**: WebSocket

### Entry points
- Backend: `backend/main_auth_refactored.py` (o original `main_auth.py` ainda existe mas não é o ativo)
- Frontend: `main_auth.jsx` → `App_auth.jsx`
- `App_auth_modular.jsx` existe mas está incompleto (~2500 linhas de seções ainda não extraídas)

### Componentes principais do backend
```
backend/
├── ws/orchestrator.py          # WebSocket handler: recebe msg → B.E.N. → MoE → LLM/agent
├── moe_router_simple.py        # MoE: 11 experts com keyword matching + LLM-first opcional
├── llm_manager_simple.py       # Multi-provider: Gemini, Groq, OpenAI, OpenRouter, Ollama
├── security_guardrail.py       # B.E.N. 2.0: regex + normalização de homoglifos
├── project_brain.py            # STUB — dict em memória, sem persistência real
├── agents/
│   ├── base.py                 # BaseAgent com stream_execute() via llm_manager
│   ├── cto_chat_agent.py       # CTOChatAgent(BaseAgent), name="cto"
│   ├── po_agent.py             # POAgent(BaseAgent), name="po"
│   ├── pmo_agent.py            # PMOAgent(BaseAgent), name="pmo"
│   ├── frontend_dev_agent.py   # FrontendDevAgent(BaseAgent), name="frontend"
│   ├── backend_dev_agent.py    # BackendDevAgent(BaseAgent), name="backend"
│   ├── devops_agent.py         # DevopsAgent(BaseAgent), name="devops"
│   ├── documentation_agent.py  # DocumentationAgent(BaseAgent), name="documentation"
│   ├── cto_agent.py            # CTOAgent LEGADO — validador de regras, NÃO é BaseAgent
│   ├── security_tester.py      # LEGADO — auditor HTTP, NÃO é BaseAgent
│   └── review_loop.py          # LEGADO — orquestrador interno, NÃO é BaseAgent
└── services/mcp_service.py     # Gestão de MCPs com validação via B.E.N.
```

### Fluxo de chat (estado atual)
```
WebSocket mensagem
    → B.E.N. 2.0 (security_guardrail)
    → MoE router (select expert por keyword ou LLM-first)
    → [se expert.id está no AgentRegistry] → BaseAgent.stream_execute() → llm_manager
    → [senão — fallback] → llm_manager.stream_generate() direto
    → chunks via WebSocket → frontend renderiza com react-markdown
```

---

## 3. Os 11 Experts do MoE Router

| ID | Nome | Tem BaseAgent? | Observação |
|----|------|----------------|------------|
| `general` | **Sabrina** — Assistente Executiva | ❌ | Interface primária do usuário. Fallback padrão. Orquestradora. |
| `cto` | CTO — Arquiteto de Soluções | ✅ CTOChatAgent | Legado validador (cto_agent.py) permanece separado |
| `frontend` | Desenvolvedor Frontend | ✅ FrontendDevAgent | |
| `backend` | Desenvolvedor Backend | ✅ BackendDevAgent | |
| `devops` | Engenheiro DevOps | ✅ DevopsAgent | |
| `project` | Gestor de Projeto | ❌ | Sem BaseAgent ainda |
| `security` | Especialista em Segurança | ❌ | Sem BaseAgent ainda |
| `data` | Cientista de Dados | ❌ | Sem BaseAgent ainda |
| `cfo` | CFO — Finanças | ❌ | Sem BaseAgent ainda |
| `coo` | COO — Operações | ❌ | Sem BaseAgent ainda |
| `software_operator` | Operador CLI | ❌ | Expert reservado, nunca selecionado automaticamente |
| `ide_editor` | Editor de IDE | ❌ | Sem BaseAgent ainda |

**Nota**: AgentRegistry tem também PO, PMO, Documentation — sem correspondente no MoE.

---

## 4. A Sabrina — Contexto Crítico de Produto

**A Sabrina é o `general` expert no MoE** — não é um agente separado, é o expert de fallback com o system_prompt mais rico do sistema.

**Papel na visão do produto**: interface primária do usuário. Toda interação deveria começar com a Sabrina. Ela identifica a natureza do pedido e delega para o expert/orquestrador correto. O usuário nunca deveria precisar selecionar manualmente qual expert usar.

**Problema atual**: o MoE router faz o roteamento antes da Sabrina ter chance de orquestrar. A Sabrina só é ativada quando nenhum outro expert tem score suficiente. Isso é o inverso do que a visão descreve.

**O que está no system_prompt da Sabrina** (relevante para a visão):
- Orquestradora geral: convoca CTO, CFO, COO conforme necessário
- Usa tag `[[add_step: descrição]]` para registro de progresso lateral
- Pode acionar `software_operator` e `python-inline` via MCP
- Detecta quando criar plano no formato ```plan``` com tasks e skill_ids
- Inclui tarefa final de registro no Gestor de Projeto em todo plano

**Problema de renderização ativo**: `[[add_step: ...]]` aparece como texto puro no chat. O frontend não renderiza essa tag. O `MessageBlock.jsx` foi implementado mas não cobre esse token específico.

---

## 5. Visão de Produto — Sistema de Ideação e Projetos

**Contexto**: Pê tem dificuldades de memória. O Open Slap! tem função de compensação cognitiva, não apenas produtividade técnica.

### Três estados de uma ideia
```
Conversa → [Sabrina detecta potencial] → IDEAÇÃO (registro silencioso automático)
                                              ↓
                          [usuário confirma / recorrência detectada]
                                              ↓
                              PROJETO FORMAL (planejado ou imediato)
                                              ↓
                          [time do CTO executa e documenta]
```

### Decisão de design — Opção C (aprovada)
- Registro **agressivo e silencioso** — Sabrina não pergunta, registra
- Curadoria **periódica e leve** — apresenta resumo semanal do que capturou
- Usuário descarta o que não quer na revisão, não no momento da conversa
- Feature **ativável em Settings**, vem ativa por padrão

### Comportamento proativo da Sabrina
Quando nova ideia ressoa com ideação anterior:
> "Em [timestamp] discutimos sobre uma ideia semelhante: [escopo e insights]. Podemos resgatar esse conceito e adaptá-lo, ou prefere seguir por outro caminho?"

### Categorias de memória da Sabrina
- Perfil e preferências pessoais do usuário
- Ideias e conceitos soltos (baixa recorrência)
- Ideações (potencial de projeto identificado)
- Projetos formais (planejados para o futuro ou em execução)

### `project_brain.py` — estado atual
É um **stub em memória** (dict Python). Não persiste nada no banco. Não tem grafo, não tem busca. Foi concebido com a ideia de expandir para grafos tipo Obsidian. Precisa ser repensado como fundação do sistema de ideação — o stub atual é apenas um placeholder para não quebrar imports.

---

## 6. B.E.N. 2.0 — Avaliação Crítica

**O que é**: filtro de segurança de entrada. Regex + normalização de texto (homoglifos Cyrillic, leet speak, espaçamento) + validação de manifestos MCP.

**O que não é**: proteção completa contra ataques modernos.

**Gaps identificados**:
1. Cobre apenas injeção direta (usuário digitando no chat). Não cobre injeção indireta (conteúdo de e-mails, Drive, páginas web que o agente vai ler).
2. Sem output filtering — não valida o que o LLM produz antes de enviar ao cliente.
3. Sem action screening — sem camada entre "LLM decide executar tool call" e "tool call executa".
4. O score "9/10" é circular: testa os ataques que os próprios padrões foram feitos para detectar.

**O que tem valor real**: `normalize_text()` com cobertura de homoglifos — contribuição técnica reutilizável.

**Alternativas pesquisadas e viáveis no hardware alvo**:
- PIGuard (184MB, F1 superior a PromptGuard) — viável
- PromptGuard 2 86M (Meta) — viável  
- Mirror SVM (Rust, <1ms) — ideal para filtro de retornos de conectores

**Recomendação**: substituir regex manuais por PIGuard ou PromptGuard 2 86M para input direto; Mirror SVM para sanitizar retornos de Gmail/Drive antes de entrar no contexto do LLM.

---

## 7. Pendências Ativas (QA Review 2026-05-28 + sessão de hoje)

| # | Item | Status | Observação |
|---|------|--------|------------|
| P2 | QA Agent (9º agente) | ⏳ | Especificação em AGENT_SPECIFICATIONS.md linha 1017 |
| P3 | AIGatewayClient no LLM manager | ⏳ | Cliente existe mas não usado pelos managers |
| P4 | Extrair helpers do orchestrator | ⏳ | 5 funções importadas de main_auth, mover para utils |
| P5 | SPA fallback + MCP init no refatorado | ⏳ | Para main_auth_refactored substituir original |
| P7 | Testes E2E com LLM real | ⏳ | Testes atuais usam mock, não validam chamadas reais |
| P8 | Orquestrador v3 completo | ⏳ | Plan → Build → Test → Deploy |
| — | Limpar 2 falhas de mock path nos testes | ⏳ | Pré-existentes, não regressão |
| — | `[[add_step: ...]]` não renderiza no frontend | ⏳ | Token da Sabrina sem handler no MessageBlock |
| — | Sistema de ideação / project_brain real | ⏳ | Visão definida, sem spec ainda |
| — | Sabrina como interface primária (não fallback) | ⏳ | Mudança arquitetural no fluxo de roteamento |

---

## 8. Decisões Arquiteturais Registradas

| Decisão | Motivo |
|---------|--------|
| BaseAgent sem ABC | Flexibilidade para migração dos legados sem rigidez |
| Import local do llm_manager no BaseAgent | Evitar circular import |
| CTOAgent legado não migra para BaseAgent | É validador de regras, não agente conversacional |
| SecurityTesterAgent não migra para BaseAgent | É auditor HTTP ativo, não agente conversacional |
| Opção A para integração de agentes (LLM call por agente) | Arquitetura correta, cada agente gerencia seu contexto |
| LLM remota como padrão (hardware do público-alvo) | i5 2010, sem GPU — Ollama é fallback, não primário |
| Opção C para sistema de ideação (registro agressivo + curadoria periódica) | Elimina o problema do limiar errado |
| `else` (fallback) no orchestrator mantido | 9 experts do MoE ainda sem BaseAgent |

---

## 9. Ecossistema e Contexto Comercial

- **Open Slap!**: motor base open source (este projeto)
- **Slap! PRO**: produto comercial derivado, não concorrente
- **AI-Gateway** (`C:\AI-Gateway`): setup local do desenvolvedor, não requisito do Open Slap!. Adiciona endpoint `/v1/chat/completions` (formato OpenAI) + `/v1beta/...` (formato Google) com rotação de chaves e fallback.
- **_opencode_memory** (`C:\Agent\_opencode_memory`): sistema de memória do Opencode (SQLite + JSONs por camada)

---

## 10. Sistema de Projetos, Wiki e Ideação — Decisões (2026-05-30)

### Arquitetura de três sistemas interligados
```
SISTEMA DE PROJETOS          WIKI/BASE DE CONHECIMENTO       SISTEMA DE IDEAÇÃO
(formalização)               (contexto vivo)                 (captura silenciosa)
      └──────────────────────────────┴───────────────────────────────┘
                                     │
                              SABRINA (orquestradora)
                                     │
                              TIME DE AGENTES
```

### Quatro caminhos de entrada de um projeto (todos terminam no mesmo estado no banco)
1. Wizard manual — usuário preenche telas
2. Import de documento externo (PDF/MD/DOCX/TXT) — script extrai, agente faz fallback se incompleto
3. Chat com Sabrina — usuário pede para iniciar, Sabrina chama `create_project()` direto
4. Detecção proativa da Sabrina — identifica potencial de projeto na conversa

### Status do projeto
`draft` → `ativo` → `suspenso` (requer justificativa) → `encerrado` / `cancelado`

### Wiki — decisões chave
- Sistema **interno**, sem interface humana direta
- Interface do usuário com a wiki é via **notas + tarefas + chat com Sabrina**
- Cada projeto criado inicializa wiki automaticamente (zero tokens)
- Seções: `codebase`, `todos`, `notes`, `issues`, `agent_communication`, `change_management`, `general`
- Watcher de filesystem detecta mudanças externas (Cursor, Windsurf, etc.) e registra na seção `agent_communication`
- Grafos tipo Obsidian: **mantido na visão, implementação futura** — requer API de navegação por nós
- Obsidian endpoint (para usuários que já usam Obsidian) também mapeado para evolução futura

### Sistema de Ideação — decisão adotada: Opção C
- Registro **agressivo e silencioso** — Sabrina não pergunta, registra via `create_note()` com `category=ideacao`
- Curadoria **periódica e leve** — resumo semanal apresentado pela Sabrina
- Feature ativável em Settings (`IDEATION_CAPTURE_ENABLED=True` por padrão)
- Categorias de notas: `nota`, `ideia_solta`, `ideacao`, `projeto_futuro`
- Campo `source`: `user` | `agent`
- Resgate de ideação anterior: keyword matching via FTS5 (busca semântica é evolução futura)

### Relatórios
- **Status** (sob demanda): script determinístico, zero tokens, exportável em MD e PDF
- **Encerramento**: parte 1 script (dados banco) + parte 2 narrativa do agente
- SPI/CPI: exibido como `N/A` quando Planned Value não informado
- Rastreamento de tokens: retrospectivo apenas (consumido por sprint) — orçamento prospectivo é evolução futura

### Rastreamento de tokens
- Nova tabela `project_token_usage` com `sprint_label`, `agent_id`, `provider`, `model`, `tokens_in`, `tokens_out`
- Exibido na ficha do projeto por sprint
- Campo `budget` no TAP: opcional, default "Orçamento zero / Não informado"

### Filosofia de implementação
- Scripts onde possível: determinístico, zero tokens, autônomo
- Agentes apenas onde há interpretação semântica necessária
- Agentes não "abrem telas" — chamam funções que gravam no banco; a UI é o espelho

### Novas tabelas criadas
- `project_wiki` — base de conhecimento por projeto
- `project_token_usage` — rastreamento de tokens por sprint
- `agent_communication_log` — log de ações de agentes e mudanças externas

### Colunas adicionadas a tabelas existentes
- `projects`: `status`, `suspension_reason`, `repository_json`
- `notes`: `category`, `source`

### Novos serviços criados
- `backend/services/report_service.py` — geração determinística de relatórios
- `backend/services/fs_watcher.py` — watcher de filesystem (watchdog)
- `backend/services/tap_import_service.py` — extração de TAP de documentos externos
- `backend/services/ideation_service.py` — captura silenciosa de ideações

### Spec gerada
`SPEC_PROJECT_SYSTEM_V1.md` — 9 fases sequenciais, executar fase por fase com testes

### O que a spec NÃO cobre (evolução futura)
- Sabrina como orquestradora primária (P2.5)
- Busca semântica de ideações
- Consolidado narrativo do agente no relatório de encerramento (requer Sabrina integrada)
- Teto de gasto de tokens por sprint
- SPI/CPI prospectivo
- Validação completa de GitHub e Google Drive
- Grafos de conhecimento / Obsidian endpoint

---

## 11. Hardware e Perfil do Público-Alvo

- Desenvolvedor primário: i5 2010, sem GPU
- Público-alvo primário: makers, desenvolvedores, escolas públicas
- Constraint principal de hardware: modelos locais limitados a ~2B parâmetros
- Implicação: LLM remota é padrão; features de IA local (classificadores pequenos como PIGuard) são viáveis se <500MB

---

## 11. Sabrina — Implementação Real (descoberta na leitura profunda)

A Sabrina está mais implementada do que parecia. Está **espalhada** em múltiplos lugares:

### Onde existe
- `moe_router_simple.py` — expert `id="general"`, `name="Sabrina — Assistente Executiva"`, system_prompt de ~80 linhas (o mais rico do sistema)
- `App_auth.jsx` — botão "Chame a Sabrina" na sidebar, `buildSabrinaBellPrompt()`, kernel prompt inicia com "Você é a Sabrina."
- `data/skillI18n.js` — skill `chat-assistant` com nome Sabrina em pt/en/es
- `backend/main_auth.py` linha 644 — regex de saudação para ativação: `^(?:sabrina|sabina|oi|olá)...`
- Wizard service — delega kickoff à Sabrina via LLM

### Tokens que a Sabrina produz (e o que o frontend faz com eles)
O `chatSocketReducers.js` → `reduceDoneEvent` chama `parseAssistantDirectivesFromText` no conteúdo final. Este parser (definido em `App_auth.jsx`) processa:
- `[[open_settings:llm_api_key]]` → abre painel de settings
- `[[add_step: descrição]]` → **NÃO tem handler visual implementado** — aparece como texto puro
- ` ```plan ... ``` ` → `MessageBlock` renderiza com CTA de aprovação ✅
- `<THINKING>...</THINKING>` → `MessageBlock` renderiza com collapse ✅
- `<COMMAND_REQUEST_JSON>...</COMMAND_REQUEST_JSON>` → `parseCommandRequestsFromContent` extrai e exibe modal de aprovação ✅

### O problema arquitetural real da Sabrina
O MoE router faz keyword matching **antes** da Sabrina ser consultada. A Sabrina só é ativada quando nenhum expert tem score ≥ 0.1. Na prática:
- "crie um componente React" → `frontend` (score 0.1) → FrontendDevAgent direto, Sabrina nunca vê
- "o que eu devo fazer hoje?" → `general` (score 0.5) → Sabrina responde

**Para a visão funcionar** (Sabrina como orquestradora primária), o fluxo precisa ser invertido:
```
WebSocket → B.E.N. → [sempre Sabrina primeiro]
                           ↓
            Sabrina decide: responde direto OU delega para expert
                           ↓
            [se delega] → expert específico via AgentRegistry
```
Isso requer que `SabrinaAgent(BaseAgent)` seja criado como orquestrador, e o MoE passe a ser um **catálogo de capacidades** que a Sabrina consulta — não o seletor primário.

---

## 12. Sistema de Tokens da Sabrina — Mapa Completo

| Token | Parseado? | Renderizado? | Onde |
|-------|-----------|-------------|------|
| ` ```plan...``` ` | ✅ `parseMessageBlocks` | ✅ `MessageBlock` CTA | parsers.js + MessageBlock.jsx |
| `<THINKING>...</THINKING>` | ✅ `parseMessageBlocks` | ✅ `MessageBlock` collapse | parsers.js + MessageBlock.jsx |
| `[[open_settings:X]]` | ✅ `parseAssistantDirectivesFromText` | ✅ abre settings | App_auth.jsx |
| `[[add_step: X]]` | ✅ parseado | ❌ sem handler visual | App_auth.jsx — só extrai, não renderiza |
| `<COMMAND_REQUEST_JSON>` | ✅ `parseCommandRequestsFromContent` | ✅ modal de aprovação | parsers.js + App_auth.jsx |

**`[[add_step: X]]`** é o único token sem renderização. Deveria atualizar um painel lateral de progresso — esse painel existe no `showExecutionPanel` state mas não está conectado ao handler do token.

---

## 13. Frontend — Estrutura Real do App_auth.jsx

O monolito tem ~270 `useState` declarations. Principais grupos de estado:

- **Chat core**: `messages`, `input`, `streaming`, `connected`, `wsRef`
- **LLM config**: `llmMode`, `llmProvider`, `llmApiKey`, `llmHasStoredApiKey`, etc. (12 states)
- **Experts/MoE**: `forceExpertId`, `lastExpertReason`, `showRoutingDebug`
- **Plan→Build**: `planTasks`, `activePlanConvId`, `activePlanMessageId`, `pendingPlanTasksRef`
- **Projects/TAP**: `projects`, `activeProjectId`, `tapFormData`, `tapEditingProjectId`
- **Notes/Brain**: `notes`, `selectedNote`, `noteSearchQuery` — **esta é a fundação do sistema de ideação**
- **Orchestration**: `orchRunId`, `orchStatus`, `orchLog` — orquestrador Plan→Build→Deploy
- **SOUL**: `soulData`, `soulMarkdown` — perfil do usuário
- **Connectors**: GitHub, Google Drive, Calendar, Gmail, Tera

O sistema de **Notes** (`/notes` routes) já existe no backend e frontend. É o candidato natural para a **camada de Ideação** — não é necessário criar uma nova entidade, apenas adicionar categorização (ideia solta / ideação / projeto) ao modelo existente.

---

## 14. TAP (Technical Analysis & Planning)

Já existe um modal TAP no App_auth.jsx com campos:
- `name`, `purpose`, `objectives`, `scope`, `risks`, `stakeholders`, `budget`
- Plus: stakeholders list, risks list, releases list

Este é o embrião da **documentação formal de projetos** da visão. Está implementado mas provavelmente sem integração com o time de agentes para preenchimento automático.

---

## Notas para próximas sessões

1. **Antes de qualquer spec nova**: ler `short.json` e `medium.json` do Opencode em `C:\Agent\_opencode_memory\`

2. **Antes de executar SPEC_PROJECT_SYSTEM_V1.md**: confirmar com Opencode:
   - Nome exato da tabela/funções de cifragem de credenciais (`user_connector_secrets`?)
   - Assinatura real de `create_project()` — retorna `id` ou outro tipo?
   - Executar fase por fase com testes, não tudo de uma vez

3. **Sabrina como interface primária (P2.5)** — próxima grande mudança arquitetural:
   - Criar `SabrinaAgent(BaseAgent)` como orquestrador
   - MoE vira catálogo de capacidades consultado pela Sabrina, não seletor primário
   - `[[add_step: X]]` precisa ser conectado ao `showExecutionPanel` no frontend
   - Outros tokens da Sabrina sem handler visual podem existir — auditar antes de implementar

4. **project_brain.py** — stub sem valor reaproveitável. Não referenciar em novas specs.

5. **Teste de aceitação do sistema de projetos** — quando a estrutura estiver pronta, o teste maior é solicitar ao agente criar e documentar o projeto da v3 do Open Slap! dentro dele mesmo.

6. **TAP modal** — já existe no frontend. Após o sistema de projetos estar no banco, integrar agentes (PO, PMO) para preenchimento automático via LLM.

7. **Próxima ordem de trabalho após SPEC_PROJECT_SYSTEM_V1**:
   - P2.5: SabrinaAgent como orquestradora primária + fix `[[add_step: X]]`
   - P2: QA Agent (9º agente do time)
   - P3: AIGatewayClient no LLM manager
   - P4/P5: limpeza de dívida técnica (helpers do orchestrator, SPA fallback)
   - P7: testes E2E com LLM real
