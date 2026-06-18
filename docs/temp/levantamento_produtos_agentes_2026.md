# Levantamento de Produto: Agentes de Desktop e Orquestração Agêntica
## Atualizado: 17 de junho de 2026

---

## 1. Claude Desktop (Anthropic)

### 1.1 Identificação
- **Nome:** Claude Desktop
- **Versão atual:** Redesign completo (abril/2026) + Computer Use Beta (lançado junho/2026)
- **Licença:** Proprietária
- **Autor:** Anthropic
- **Stack:** Electron (estimado), serviços em nuvem Anthropic

### 1.2 Proposta
Consolidar Chat, Cowork e Claude Code em uma única janela nativa, transformando o Claude de "janela de chat" em "agente que opera seu computador". Foco em produtividade de conhecimento e automação de tarefas no desktop.

### 1.3 Arquitetura Geral
```
┌─────────────────────────────────────────────┐
│           CLAUDE DESKTOP APP                │
│  macOS (Computer Use) · Windows · Web       │
├─────────────────────────────────────────────┤
│  Chat · Cowork · Claude Code (3 modos)      │
│  Mission Control (sidebar redesign)          │
│  Terminal built-in · File editor · Diff     │
│  HTML/PDF preview                            │
├─────────────────────────────────────────────┤
│  Computer Use (Beta) — macOS only            │
│  Screenshot → mouse/keyboard control         │
│  Per-action approval · App permissions       │
├─────────────────────────────────────────────┤
│  Cloud: Anthropic API · Routines (async)     │
│  Memory (todos os planos, desde mar/2026)    │
│  MCP integrations                            │
└─────────────────────────────────────────────┘
```

### 1.4 Sistema de Agentes
- **Modelo:** Single-agente (Claude) com múltiplos modos de operação
- **Modos:** Chat (conversação), Cowork (trabalho de conhecimento agêntico), Code (desenvolvimento)
- **Orquestração:** Nenhuma — Claude atua como agente único
- **Sub-agentes:** Não há; Routines rodam em nuvem de forma assíncrona

### 1.5 Sistema de Memória
- **Memória persistente:** Disponível para todos os planos (incluindo gratuito) desde março/2026
- **Tipo:** Memória de conversa + preferências do usuário
- **Persistência:** Nuvem Anthropic
- **SOUL/Perfil:** Não documentado explicitamente

### 1.6 Segurança
- **Computer Use:** Aprovação por ação, permissões por app, screenshots limitados
- **Guardrails:** Padrão Anthropic (Constitutional AI)
- **Cobertura:** Prompt injection, jailbreak, conteúdo nocivo
- **Score/Tests:** Não publicado

### 1.7 Conectores
- Excel Add-in, PowerPoint Add-in
- MCP (Model Context Protocol)
- Routines (automações em nuvem)
- Sem gateway multi-plataforma de mensagens

### 1.8 Providers LLM
- **Único provider:** Anthropic (Claude 3.7 Sonnet, Opus, etc.)
- **Sem fallback chain**
- **Sem escolha de modelo pelo usuário**

### 1.9 Interface do Usuário
- Chat streaming
- Global Quick Access (atalho global, toque duplo Option)
- Gráficos interativos inline
- Multi-sessão lado a lado (redesign abril/2026)
- 5 idiomas (estimado)
- Temas: claro/escuro

### 1.10 Estado Atual vs Limitações
| Recurso | Situação |
|---------|----------|
| Chat + memória | ✅ Funcional |
| Computer Use | ✅ Beta (macOS only) |
| Multi-sessão | ✅ Redesign abril/2026 |
| Routines (async) | ✅ Research preview |
| Claude Code integrado | ✅ Redesign abril/2026 |
| Windows Computer Use | ❌ Não no lançamento |
| Linux app nativo | ❌ Web apenas |
| Multi-agente/orquestração | ❌ Não existe |
| Escolha de LLM | ❌ Anthropic only |
| Execução local/offline | ❌ Cloud-dependent |
| Gateway multi-mensagens | ❌ Não existe |

### 1.11 Diferenciais Competitivos
1. **Computer Use nativo** — único dos grandes a oferecer controle de tela no app consumer
2. **Integração office** — Excel/PowerPoint add-ins com contexto compartilhado
3. **Routines em nuvem** — automações que rodam com laptop fechado
4. **Memória gratuita** — disponível em todos os planos
5. **Redesign maduro** — interface polida, multi-sessão, Mission Control

---

## 2. Hermes Desktop (Nous Research)

### 2.1 Identificação
- **Nome:** Hermes Desktop
- **Versão atual:** Lançado fevereiro/2026, evolução contínua
- **Licença:** MIT (open source)
- **Repositório:** https://github.com/NousResearch/hermes-desktop
- **Autor:** Nous Research
- **Stack:** Electron (estimado), Python backend, SQLite

### 2.2 Proposta
Agente de código aberto com "loop de aprendizado fechado" — cria skills a partir da própria experiência, melhora-as durante o uso e constrói um modelo do usuário ao longo das sessões. Foco em autonomia e evolução contínua.

### 2.3 Arquitetura Geral
```
┌─────────────────────────────────────────────┐
│           HERMES DESKTOP                     │
│  macOS 12+ · Windows 10/11 · Linux           │
├─────────────────────────────────────────────┤
│  Gateway Multi-Mensagens (16+ plataformas)   │
│  Memória persistente (SQLite FTS5)           │
│  Skills auto-evolutivas (Markdown)            │
│  Sub-agentes paralelos                        │
├─────────────────────────────────────────────┤
│  Browser automation · Execução de código     │
│  Cron scheduler (linguagem natural)           │
├─────────────────────────────────────────────┤
│  Multi-modelo (200+ via OpenRouter, etc.)    │
│  Execução remota (VPS, cluster, serverless)   │
└─────────────────────────────────────────────┘
```

### 2.4 Sistema de Agentes
- **Modelo:** Single-agente com sub-agentes paralelos
- **Registry:** Não documentado como registry formal
- **Sub-agentes:** Spawna sub-agentes isolados para workstreams paralelos com terminais próprios
- **Orquestração:** Não há orquestração visual; sub-agentes rodam em paralelo
- **Skills:** Auto-criadas após cada tarefa — extraem padrões reutilizáveis e armazenam como Markdown. Agents com 20+ skills completam tarefas similares 40% mais rápido.

### 2.5 Sistema de Memória
- **SQLite FTS5** — busca de sessões e sumarização por LLM
- **Memória persistente** — lembra preferências, projetos e ambiente entre sessões
- **Auto-evolutiva** — melhora com o uso
- **SOUL/Perfil:** Implícito no modelo do usuário construído ao longo do tempo
- **Persistência:** Local (SQLite) + remota (VPS/cloud)

### 2.6 Segurança
- **Sandbox:** VM isolada para execução de código
- **Guardrails:** Não documentado formalmente
- **Cobertura:** Não publicado
- **Score/Tests:** Não publicado

### 2.7 Conectores
- **Gateway multi-mensagens:** Telegram, Discord, Slack, WhatsApp, Signal, Matrix, Email, SMS, iMessage, DingTalk, WeChat, etc.
- Todos compartilham uma sessão e memória única
- Browser automation (navegação, cliques, digitação, screenshots, extração)
- MCP: não documentado explicitamente

### 2.8 Providers LLM
- **200+ modelos** via OpenRouter, Nous Portal, Anthropic, OpenAI, Google, xAI, Qwen, MiniMax, Hugging Face, Ollama
- **Fallback chain:** Sim
- **Escolha via CLI:** `hermes model`
- **Nous Portal:** Tier gratuito e Plus a $20/mês

### 2.9 Interface do Usuário
- Chat streaming
- Terminal/CLI nativo
- Sem orquestração visual documentada
- Multi-plataforma de mensagens (16+ gateways)
- Idiomas: não documentado explicitamente
- Temas: não documentado explicitamente

### 2.10 Estado Atual vs Limitações
| Recurso | Situação |
|---------|----------|
| Memória persistente | ✅ Funcional |
| Skills auto-evolutivas | ✅ Funcional |
| Multi-plataforma mensagens | ✅ 16+ gateways |
| Sub-agentes paralelos | ✅ Funcional |
| Agendamento cron | ✅ Linguagem natural |
| Multi-modelo | ✅ 200+ |
| Execução remota | ✅ VPS/cloud |
| Browser automation | ✅ Funcional |
| Computer Use (controle de tela) | ❌ Browser only |
| Orquestração visual | ❌ Não existe |
| UI desktop rica | ❌ Minimalista/CLI-focused |
| Acessível a não-devs | ❌ Requer familiaridade técnica |

### 2.11 Diferenciais Competitivos
1. **Skills auto-evolutivas** — único com aprendizado autônomo de padrões
2. **Gateway multi-mensagens** — 16+ plataformas, sessão única
3. **Multi-modelo** — 200+ modelos, troca fácil
4. **Execução remota** — VPS $5, serverless hibernável
5. **Código aberto** — MIT, comunidade ativa (180k+ stars)

---

## 3. OpenClaw

### 3.1 Identificação
- **Nome:** OpenClaw
- **Versão atual:** Não especificado (ativo em 2026)
- **Licença:** Open source
- **Repositório:** Não especificado
- **Autor:** Comunidade
- **Stack:** Não especificado

### 3.2 Proposta
Gateway multi-agente de propósito geral com ecossistema maduro de ferramentas e plugins. Atua como roteador que gerencia múltiplos agentes simultaneamente.

### 3.3 Arquitetura Geral
```
┌─────────────────────────────────────────────┐
│           OPENCLAW                           │
│  Gateway Multi-Agente                        │
├─────────────────────────────────────────────┤
│  ClawHub — 5.700+ skills comunitárias       │
│  Ecossistema de plugins e ferramentas        │
├─────────────────────────────────────────────┤
│  Memória persistente                         │
│  Personas customizáveis                       │
│  Roteamento multi-agente                      │
└─────────────────────────────────────────────┘
```

### 3.4 Sistema de Agentes
- **Modelo:** Gateway multi-agente (roteador nativo)
- **Registry:** Não documentado
- **Sub-agentes:** Gerenciados pelo gateway
- **Orquestração:** Roteamento entre múltiplos agentes especializados
- **Skills:** 5.700+ skills comunitárias (ClawHub) — maior ecossistema

### 3.5 Sistema de Memória
- **Memória persistente:** Sim
- **Tipo:** Não especificado
- **Persistência:** Não especificado
- **SOUL/Perfil:** Personas customizáveis

### 3.6 Segurança
- **Sandbox:** Não documentado
- **Guardrails:** Não documentado
- **Cobertura:** Não publicado

### 3.7 Conectores
- ClawHub (5.700+ skills)
- Ecossistema de plugins maduro
- MCP: não documentado explicitamente
- Gateway multi-mensagens: não documentado explicitamente

### 3.8 Providers LLM
- **Múltiplos providers:** Sim
- **Fallback chain:** Não documentado
- **Escolha de modelo:** Sim

### 3.9 Interface do Usuário
- Não documentado detalhadamente
- Sem orquestração visual documentada
- Maior complexidade devido ao modelo gateway

### 3.10 Estado Atual vs Limitações
| Recurso | Situação |
|---------|----------|
| Gateway multi-agente | ✅ Arquitetura nativa |
| ClawHub (5.700+ skills) | ✅ Maior ecossistema |
| Memória persistente | ✅ Funcional |
| Personas customizáveis | ✅ Funcional |
| Migração para Hermes | ✅ Tool built-in |
| Computer Use | ❌ Não existe |
| Orquestração visual | ❌ Não existe |
| Skills auto-evolutivas | ❌ Predefinidas apenas |
| Execução local-first | ❌ Gateway = complexidade |
| UI desktop rica | ❌ Não documentado |

### 3.11 Diferenciais Competitivos
1. **ClawHub** — 5.700+ skills, maior ecossistema comunitário
2. **Gateway multi-agente** — arquitetura nativa de roteamento
3. **Ecossistema maduro** — plugins e ferramentas consolidados
4. **Migração Hermes** — tool built-in para transição

---

## 4. Open Slap! v3 (Pe Martins)

### 4.1 Identificação
- **Nome:** Open Slap!
- **Versão atual:** v2.2.6 (com features incrementais da v3)
- **Licença:** Apache 2.0
- **Repositório:** https://github.com/pemartins1970/open-slap
- **Autor:** Pe Martins (@pemartins1970)
- **Stack:** Python 3.11+ / FastAPI (backend) · React + Vite (frontend) · Electron (v27) (desktop) · SQLite (DB)

### 4.2 Proposta
Motor de agentes open-source, local-first, com orquestração visual multi-agente, memória híbrida que aprende o perfil do usuário (SOUL) e roteamento por Mistura de Especialistas (MoE). Projetado para makers, devs e escolas com hardware modesto (i5, sem GPU). Não é produto comercial — sem SLA, sem suporte pago.

### 4.3 Arquitetura Geral
```
┌─────────────────────────────────────────────┐
│              ELECTRON (v27)                  │
│  Windows/macOS/Linux — auto-setup Python     │
├─────────────────────────────────────────────┤
│           FRONTEND (React + Vite)             │
│  Porta 5173 → proxy reverso → backend:5150   │
│  WebSocket streaming · 5 idiomas · 8 temas   │
├─────────────────────────────────────────────┤
│           BACKEND (FastAPI, porta 5150)      │
│  Rotas REST (35+) · WebSocket · MoE · LLM    │
│  B.E.N. 2.0 (guarda de segurança)            │
│  AgentRegistry (18 agentes registrados)      │
│  5 providers LLM com fallchain                │
├─────────────────────────────────────────────┤
│         BANCO DE DADOS (SQLite)               │
│  slap.db · auth.db · referrals.db · 30+ tabs │
│  FTS5 · Chronicle (memória episódica)         │
└─────────────────────────────────────────────┘
```

**Componentes Críticos (backend):**

| Arquivo | Função |
|---------|--------|
| ws/orchestrator.py (368 linhas) | Handler WebSocket: msg → B.E.N. → MoE → LLM/agente → resposta stream |
| moe_router_simple.py (857 linhas) | 13 experts (CTO, CFO, COO, Sabrina, Back/Front/DevOps/Sec/Data/PMO/QA/SoftwareOp/IDEEditor) com roteamento keyword + LLM |
| llm_manager_simple.py (~1700 linhas) | 5 providers: Gemini, Groq, OpenAI, OpenRouter, Ollama — fallback chain + streaming |
| security_guardrail.py (212 linhas) | B.E.N. 2.0 — normalização Unicode/homoglifo/leet, 78 testes, score 9/10 |
| agents/base.py (82 linhas) | BaseAgent + AgentRegistry (singleton), stream_execute/execute |
| project_brain.py (67 linhas) | Stub de memória de projetos (dict em RAM, sem persistência) |
| chronicle.py | Memória episódica SQLite + FTS5 |
| soul_extractor.py | Extrai perfil do usuário (preferências, estilo) da conversa |

**Estrutura do Frontend:**

| Arquivo/Local | Função |
|---------------|--------|
| main_auth.jsx | Entry point ativo (aponta pra App_auth.jsx) |
| App_auth.jsx (~7772 linhas) | Monolito legado — todo o app num arquivo |
| App_auth_modular.jsx (~660 linhas) | Versão refatorada com componentes separados |
| components/layout/ | AppLayout, LeftSidebar, RightSidebar, Header |
| components/panels/ | SkillsPanel, DoctorPanel |
| hooks/ | 13 hooks: useChatSocket, useAuth, useSettings, useLLMConfig, etc |
| i18n/ | 5 idiomas: PT, EN, ES, AR, ZH |
| styles/ | 8 temas via JSS + variáveis CSS |
| vite_auth.config.js | Proxy para backend em 127.0.0.1:5150 |

### 4.4 Sistema de Agentes

**18 agentes registrados no AgentRegistry:**

| Agente | ID | Especialidade |
|--------|-----|---------------|
| Sabrina | general | Assistente executiva — orquestradora principal, fallback padrão |
| CTO | cto | Arquiteto de soluções — PLAN → DELEGATE → BUILD |
| CFO | cfo | Finanças, orçamento, runway, precificação |
| COO | coo | Operações, processos, SLAs, OKRs |
| PO | po | Product Owner — requisitos, backlog |
| PMO | pmo | Gestão de projeto, escopo, roadmap |
| Backend Dev | backend_dev | APIs, banco, servidores Python/FastAPI |
| Frontend Dev | frontend_dev | React, CSS, UI/UX |
| DevOps | devops | Docker, CI/CD, cloud, infra |
| Security | security | Auth, criptografia, vulnerabilidades |
| Data | data | Análise, ML, estatística |
| QA | qa | Testes, qualidade, revisão de código |
| Software Operator | software_operator | Geração de comandos CLI para automação local |
| IDE Editor | ide_editor | Refatoração, LSP, navegação em IDE |
| CTO Chat | cto_chat | (provavelmente duplicata/legado) |
| Documentation | documentation | Geração de docs |
| Security Tester | security_tester | Testes de segurança |
| Review Loop | review_loop | Revisão de código |

**Roteamento MoE — dois modos:**
1. **Keyword-based (fallback):** match de regex nas keywords de cada expert, score normalizado (cap 15). Score < 0.1 → Sabrina.
2. **LLM-first (ativo):** LLM externo (configurável via PROVIDER_ORDER) decide expert_id + need_tool. Se tool_needed=true, redireciona pra Sabrina.

**Problema arquitetural conhecido:** O roteamento ocorre antes de consultar Sabrina. Ela só atua quando nenhum outro expert atinge >= 0.1. O ideal seria inverter: Sabrina sempre primeiro, ela delega.

### 4.5 Sistema de Memória

**Híbrido — 4 camadas simultâneas:**

| Camada | Mecanismo | Finalidade |
|--------|-----------|------------|
| SQLite | slap.db, auth.db, referrals.db | Persistência de conversas, usuários, notas, sessões |
| FTS5 | Full-text search (Chronicle) | Busca textual em notas, conversas, memórias |
| Embeddings | sentence-transformers (planejado para Slap PRO) | Similaridade semântica |
| Heurísticas | Salience scoring, decay, consolidação | Relevância temporal |

**SOUL** — Perfil de usuário extraído automaticamente da conversa via soul_extractor.py: preferências, estilo de comunicação, linguagem de programação.

**Chronicle** — Memória episódica: cada interação é registrada com timestamp, permitindo checkpoint/recover.

### 4.6 Segurança (B.E.N. 2.0)
- **78 testes, 100% passando**
- **Score: 9/10** (pós-hardening)
- **Cobre:** prompt injection, jailbreak, system prompt leak, command injection, code injection, bypass encoding (leet speak, homoglifos Cyrillic), multilingual (PT/EN/ES/FR), MCP abuse
- **Diferencial:** zero falsos positivos, normalização Unicode de homoglifos
- **Gap único:** GAP-MCP-03 (sanitização de compatible_with list)

### 4.7 Conectores

| Conector | Status |
|----------|--------|
| GitHub | Funcional |
| Google Drive/Calendar/Gmail | Funcional |
| Telegram | Funcional |
| MCP (Model Context Protocol) | 15+ integrações (Stripe, Notion, Twilio, Shopify, Slack) |
| AI Gateway (NVidia, etc) | Cliente existe, providers não usam ainda |

### 4.8 Providers LLM

| Provider | Tipo | Chave |
|----------|------|-------|
| Gemini | API key | GEMINI_API_KEYS (múltiplas, rotação por 429) |
| Groq | API key | GROQ_API_KEYS |
| OpenAI | API key | OPENAI_API_KEY |
| OpenRouter | API key | OPENROUTER_API_KEY |
| Ollama | Local | OLLAMA_URL (localhost) |

**Ordem de fallback configurável via** `PROVIDER_ORDER=gemini,groq,ollama,openai,openrouter`.

### 4.9 Interface do Usuário
- Chat streaming via WebSocket com chunk buffering (requestAnimationFrame)
- Onboarding multi-etapas + boot screen animado
- Plano → Aprovação visual (blocos laranja/verde) com auto-approval
- 8 temas (JSS + CSS variables)
- 5 idiomas (PT, EN, ES, AR, ZH)
- Sidebar com Conversas (busca), Nova conversa, Nova nota
- Painéis: Skills (17 built-in), Doctor (diagnóstico), Settings (LLM, security, sistema)
- Modo colapsado no sidebar esquerdo
- Login com JWT + bcrypt

### 4.10 Estado Atual vs Visão v3

| Recurso | Situação |
|---------|----------|
| Chat + MoE + memória | ✅ Funcional |
| Orquestração Plan→Build | ✅ Funcional |
| SOUL (perfil usuário) | ✅ Implementado |
| B.E.N. 2.0 | ✅ 78 testes, score 9 |
| 18 agentes registrados | ⚠️ Só Sabrina e CTOChat ativos; 8 MoE IDs usam fallback |
| Refactored files em produção | ❌ 5 pares original/refatorado — nenhum conectado |
| Contexto entre mensagens (B-06) | ❌ Não funciona — cada msg é tratada como primeira |
| Auto-rename conversas (B-07) | ❌ Não implementado |
| Modo full-width (B-08) | ❌ Usa bubbles |
| Orquestração Plan→Build→Test→Deploy | ❌ Só Plan→Build |
| QA Agent (9º agente da Visão) | ❌ Existe spec, não implementado |

### 4.11 Problema Estrutural Central
Dois produtos no mesmo src/:
- App_auth.jsx ~7772 linhas monolítico (legado)
- App_auth_modular.jsx ~660 linhas modular (refatorado)
- Vite aponta pro monolito via main_auth.jsx → App_auth.jsx
- +5 pares de arquivos backend (original vs refatorado) que não se conectam
- Git com 1 único commit (baseline), 61+ arquivos sujos — sem rastreabilidade

Isso gera rollouts indesejados, race conditions de import, e consumo de recursos corrigindo bugs que já foram resolvidos num dos dois lados.

### 4.12 Métricas de Teste

| Suite | Testes | Status |
|-------|--------|--------|
| B.E.N. Unit | 34 | 100% |
| B.E.N. Integration (WS) | 25 | 100% |
| B.E.N. MCP Vector | 10 | 100% |
| Project Routes | 10 | 100% |
| Security WS | 4 | 100% |
| Agent LLM | ~5 | Passing |
| **Total** | **125** | **100%** |

### 4.13 Diferenciais Competitivos
1. **MoE + multi-agente + UI visual** — nenhum concorrente combina os três
2. **Memória híbrida (SQLite + FTS5 + Embeddings + Heurísticas + SOUL)** — concorrentes usam no máximo 1-2 camadas
3. **Orquestrador visual com blocos (plano/aprovação/stream/artefatos)** — sem equivalente
4. **Desktop (Electron) + Web** — única solução com experiência desktop rica
5. **Acessível a não-devs** — UI visual, linguagem natural, sem terminal/YAML
6. **Local-first** — sem dependência de nuvem, funciona offline com Ollama

---

## 5. Outros Produtos Agênticos Relevantes

### 5.1 Claude Code (Anthropic)
- Ferramenta de coding agêntico via terminal, agora integrada ao Claude Desktop
- Redesign de abril/2026 trouxe sidebar "Mission Control", terminal built-in, editor de arquivos, diff viewer e previews HTML/PDF
- Disponível para Pro, Max, Team e Enterprise
- Não é produto standalone

### 5.2 ChatGPT Desktop (OpenAI)
- App nativo macOS e Windows com Voice mode e atalho global Cmd+Shift+G
- **Computer Use disponível apenas via API** (research preview), não no app consumer
- Sem capacidade agêntica de controle de tela no app desktop
- Sem orquestração multi-agente

### 5.3 Gemini (Google)
- Sem app desktop nativo — acesso apenas via web (Chrome/Google AI Studio)
- Sem controle agêntico de tela no consumidor em junho/2026
- Sem orquestração multi-agente documentada

---

## 6. Quadro Comparativo Consolidado

| Aspecto | Claude Desktop | Hermes Desktop | OpenClaw | Open Slap! v3 |
|---------|:------------:|:------------:|:--------:|:-------------:|
| **Modelo de negócio** | Proprietário | Open source (MIT) | Open source | Open source (Apache 2.0) |
| **Computer Use / Controle de tela** | ✅ (macOS, per-action) | ❌ (browser only) | ❌ | ❌ |
| **Memória persistente** | ✅ | ✅ (auto-evolutiva) | ✅ | ✅ (híbrida 4 camadas) |
| **Multi-sessão paralela** | ✅ | ✅ (sub-agentes) | ✅ (gateway) | ⚠️ (estrutura existe, não ativa) |
| **Skills auto-criadas** | ❌ | ✅ | ❌ (predefinidas) | ❌ (17 built-in, não auto) |
| **Multi-plataforma mensagens** | ❌ | ✅ (16+ gateways) | N/D | ❌ (Telegram only) |
| **Agendamento** | ✅ (Routines) | ✅ (cron natural) | ✅ | ❌ |
| **Execução remota/cloud** | ❌ | ✅ | ✅ | ❌ (local-first) |
| **Escolha de modelo LLM** | ❌ (Anthropic only) | ✅ (200+) | ✅ | ✅ (5 providers) |
| **Custo** | Planos pagos | Gratuito (API only) | Gratuito | Gratuito |
| **Orquestração multi-agente** | ❌ | ❌ | ✅ (gateway) | ✅ (MoE visual) |
| **Orquestração visual** | ❌ | ❌ | ❌ | ✅ (blocos plano/aprovação) |
| **UI desktop rica** | ✅ | ❌ (minimalista) | ❌ | ✅ (Electron + React) |
| **Local-first / offline** | ❌ | ⚠️ (parcial) | ❌ | ✅ (Ollama) |
| **Segurança documentada** | ⚠️ (padrão) | ❌ | ❌ | ✅ (B.E.N. 2.0, 78 testes) |
| **SOUL / perfil usuário** | ❌ | ⚠️ (implícito) | ⚠️ (personas) | ✅ (soul_extractor.py) |
| **Acessível a não-devs** | ✅ | ❌ | ⚠️ | ✅ |
| **i18n / multi-idioma** | ⚠️ (~5) | N/D | N/D | ✅ (5 idiomas) |
| **Temas customizáveis** | ⚠️ (claro/escuro) | N/D | N/D | ✅ (8 temas) |
| **MCP support** | ✅ | N/D | N/D | ✅ (15+ integrações) |
| **Testes automatizados** | ❌ | ❌ | ❌ | ✅ (125 testes, 100%) |
| **Gateway de mensagens** | ❌ | ✅ | N/D | ⚠️ (Telegram) |
| **Fallback chain LLM** | ❌ | ✅ | N/D | ✅ (5 providers) |
| **Sub-agentes paralelos** | ❌ | ✅ | ✅ | ❌ |
| **Routines/async cloud** | ✅ | ❌ | ❌ | ❌ |

---

## 7. Análise SWOT — Open Slap! vs Concorrentes

### 7.1 Forças (Strengths) — Open Slap!
1. **Único com orquestração visual multi-agente** — nenhum concorrente oferece blocos visuais de plano/aprovação/stream
2. **Memória híbrida mais profunda** — 4 camadas (SQLite + FTS5 + Embeddings + Heurísticas + SOUL) vs. 1-2 dos concorrentes
3. **Segurança documentada e testada** — B.E.N. 2.0 com 78 testes e score 9/10; nenhum concorrente publica métricas
4. **Local-first genuíno** — funciona 100% offline com Ollama; concorrentes dependem de nuvem
5. **Acessibilidade** — UI visual para não-devs; Hermes e OpenClaw são CLI/developer-focused
6. **Multi-provider com fallchain** — 5 providers com rotação automática; Claude é lock-in Anthropic
7. **i18n e temas** — 5 idiomas e 8 temas; concorrentes têm cobertura superficial
8. **Testes automatizados** — 125 testes, 100% passando; nenhum concorrente documenta suite de testes

### 7.2 Fraquezas (Weaknesses) — Open Slap!
1. **Problema estrutural crítico** — dois produtos no mesmo src/ (monolito vs. modular), nenhum conectado
2. **Contexto entre mensagens quebrado** — B-06 não funciona; cada msg é tratada como primeira
3. **Agentes registrados mas inativos** — 18 no registry, só 2 realmente funcionam; 8 MoE IDs usam fallback
4. **Orquestração incompleta** — Plan→Build funciona, mas Test→Deploy não implementado
5. **Sem gateway multi-mensagens** — só Telegram; Hermes tem 16+
6. **Sem execução remota/cloud** — Hermes roda em VPS $5; Slap é puramente local
7. **Sem agendamento** — Hermes tem cron natural; Claude tem Routines
8. **Git sujo** — 1 commit, 61+ arquivos não rastreáveis
9. **Skills não auto-evolutivas** — 17 built-in estáticas; Hermes cria skills automaticamente
10. **Sem Computer Use** — Claude tem controle de tela nativo

### 7.3 Oportunidades (Opportunities)
1. **Resolver o problema estrutural** — conectar os arquivos refatorados e eliminar o monolito
2. **Implementar contexto entre mensagens** — B-06 é blocker para experiência fluida
3. **Ativar os 18 agentes** — o registry existe, falta wiring
4. **Completar orquestração** — Plan→Build→Test→Deploy
5. **Adicionar gateway multi-mensagens** — replicar modelo Hermes (16+ plataformas)
6. **Skills auto-evolutivas** — aprender com padrões de uso, como Hermes
7. **Execução remota opcional** — manter local-first, mas permitir VPS/cloud
8. **Computer Use via browser automation** — já tem navegação; expandir para controle de tela
9. **Agent Skills (agentskills.io)** — adotar padrão aberto para interoperabilidade
10. **Slap PRO** — tier comercial com embeddings, suporte, SLA

### 7.4 Ameaças (Threats)
1. **Claude Desktop Computer Use** — se Anthropic expandir para Windows e aprovação em lote, elimina vantagem de "agente que opera computador"
2. **Hermes crescimento explosivo** — 180k+ stars, comunidade ativa, skills auto-evolutivas são diferencial forte
3. **ChatGPT Desktop + API Computer Use** — OpenAI pode integrar no app consumer a qualquer momento
4. **Fragmentação do projeto** — problema estrutural pode levar a abandonar v3 e recomeçar
5. **Recursos de desenvolvimento** — projeto solo vs. equipes da Anthropic, Nous Research, OpenAI
6. **Lock-in de usuários** — Claude e ChatGPT já têm bases massivas; migração é difícil
7. **Complexidade técnica** — MoE + memória híbrida + orquestração visual = alta barreira de manutenção

---

## 8. Tendências-Chave do Mercado em 2026

1. **De "copiloto" para "orquestrador"** — A filosofia de design mudou de assistente single-threaded para gestão de múltiplos fluxos de trabalho simultâneos. Open Slap! está alinhado com essa tendência via MoE.

2. **Controle de computador como diferencial** — Claude é o único dos grandes a oferecer Computer Use nativamente no app desktop consumer em 2026. Open Slap! não compete nesse eixo.

3. **Aprendizado autônomo** — Hermes aposta que um agente que aprende com o tempo supera um com mais features — com dados preliminares mostrando ganho de 40% em eficiência. Open Slap! precisa evoluir nessa direção.

4. **Execução local + remota** — A tendência é rodar agentes tanto no laptop quanto em VPS/cloud serverless, com sincronização entre interfaces. Open Slap! é local-only.

5. **Padrão aberto de skills** — O padrão Agent Skills (agentskills.io) permite interoperabilidade de skills entre plataformas. Open Slap! pode adotar para expandir ecossistema.

6. **Memória como camada estratégica** — Todos os produtos estão investindo em memória, mas nenhum atinge a profundidade híbrida do Open Slap! (4 camadas + SOUL).

7. **Segurança como diferenciador** — Com Computer Use e agentes autônomos, segurança torna-se crítica. B.E.N. 2.0 do Open Slap! é vantagem competitiva documentada.

8. **UI visual para não-devs** — O mercado se expande além de desenvolvedores. Open Slap! está posicionado corretamente com orquestração visual acessível.

---

## 9. Recomendações Estratégicas para Open Slap! v3

### Prioridade 1 — Crítico (bloqueia qualquer release)
1. **Resolver problema estrutural** — Escolher monolito OU modular, eliminar o outro, conectar 5 pares de arquivos backend
2. **Implementar contexto entre mensagens (B-06)** — Sem isso, a experiência é quebrada
3. **Ativar wiring dos 18 agentes** — Registry existe, falta conexão real

### Prioridade 2 — Alto (diferencial competitivo)
4. **Completar orquestração Plan→Build→Test→Deploy**
5. **Implementar skills auto-evolutivas** — aprender padrões de uso do usuário
6. **Adicionar gateway multi-mensagens** — replicar modelo Hermes
7. **Implementar execução remota opcional** — manter local-first, mas permitir cloud

### Prioridade 3 — Médio (melhoria de UX)
8. **Auto-rename conversas (B-07)**
9. **Modo full-width (B-08)**
10. **Implementar QA Agent (9º agente da Visão)**
11. **Adotar padrão Agent Skills (agentskills.io)**

### Prioridade 4 — Baixo (nice-to-have)
12. **Computer Use via browser automation expandido**
13. **Agendamento (cron natural)**
14. **Slap PRO tier comercial**

---

*Documento gerado em 17 de junho de 2026. Dados baseados em pesquisa de mercado e documentação do projeto Open Slap! v3.*
