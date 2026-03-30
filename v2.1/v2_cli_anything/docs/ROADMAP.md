# Roadmap — Open Slap!

> Este roadmap reflete a direção do projeto, não um compromisso de entrega com datas.  
> Open Slap! é desenvolvido por uma pessoa, em hardware de 2010, no tempo disponível.

---

## ✅ v2.0 — Entregue (Março 2026)

### Core agêntico
- [x] Loop plan→build completo com orquestrador autônomo
- [x] 14 skills built-in com prompts estruturados
- [x] CTO emite planos no formato `plan block` → orquestrador executa automaticamente
- [x] Sub-conversas geradas por tarefa, acessíveis na sidebar

### Memória
- [x] Fase 1: escrita heurística em `user_soul_events`
- [x] Fase 2: momentum — reforço de memórias utilizadas no RAG
- [x] Fase 3: decay probabilístico e pruning por salience
- [x] Fase 4: snapshot consolidado por salience

### Conectores
- [x] GitHub (repos, issues)
- [x] Google Calendar (eventos próximos)
- [x] Gmail (e-mails não lidos com sujeito e remetente)
- [x] Google Drive (busca por arquivos relevantes)

### Feedback e aprendizado
- [x] 👍/👎 por mensagem persistido no banco
- [x] 👍 retroalimenta: CAC (cache), RAG (salience), expert rating
- [x] 👎 remove entrada do cache e registra rating negativo
- [x] MoE router blende keyword score com histórico de aprovações por expert

### Interface
- [x] 8 temas de cor (Deep Space, Midnight Blue, Forest, Crimson, Slate, Solarized, Light, Paper)
- [x] 5 idiomas (PT, EN, ES, AR, ZH) com suporte RTL para árabe
- [x] Layout responsivo desktop + mobile
- [x] Onboarding para novos usuários
- [x] Projetos compartilhados entre tarefas
- [x] Override manual de expert no input

### Qualidade
- [x] 50 testes automatizados (pytest)
- [x] ZIP de distribuição limpo sem credenciais nem arquivos de debug

---

## 🔄 v2.1 — Em planejamento

### Orquestrador
- [ ] Execução condicional: tarefa B só inicia quando A for aprovada pelo usuário
- [ ] Re-tentativa automática de tarefas com falha (retry com backoff)
- [ ] Exportação do resultado completo do plano como documento (MD ou DOCX)

### Memória
- [ ] Consolidação automática periódica (cronjob leve, semanal)
- [ ] Interface de revisão de memórias: pin/unpin, editar, apagar, "não memorize isso"
- [ ] Exibição de score de salience na UI de memórias

### Conectores
- [ ] Google Drive: leitura de conteúdo de documentos (não só listagem)
- [ ] GitHub: criação de issues diretamente pelo agente
- [ ] Notion (planejado)
- [ ] Slack (planejado)

### MoE e Skills
- [ ] Skills visíveis na lista de experts automáticos (não apenas em Personalizar)
- [ ] Criação guiada de skill via formulário (além do editor JSON)
- [ ] Importação/exportação de skills em formato JSON

---

## 🔮 v3.0 — Visão (sem data)

### Motor
- [ ] Multi-agente real: agentes com memória independente que se comunicam
- [ ] Tool execution loop com aprovação por etapa (modo cauteloso)
- [ ] Suporte a MCP (Model Context Protocol) para integração de ferramentas externas

### Memória
- [ ] Vector search (reservado para Slap! PRO — pode ser portado se houver demanda)
- [ ] Memória compartilhada entre usuários de um mesmo workspace (multi-tenant)

### Plataforma
- [ ] API pública documentada (OpenAPI)
- [ ] Modo headless (sem frontend) para uso em pipelines
- [ ] Container Docker oficial com compose para deploy em um comando

---

## Fora do escopo do Open Slap!

Estas funcionalidades existem ou existirão no **Slap! PRO** e outros produtos derivados, e não serão portadas para o core open source:

- SLA e suporte técnico
- Autenticação OAuth com providers de identidade externos
- Conectores proprietários (Salesforce, SAP, Oracle, etc.)
- Supervisão avançada de agentes em produção
- Multi-tenant com isolamento de dados entre organizações
- Interface polida para usuário final não-técnico

---
---

# Roadmap — Open Slap!

> This roadmap reflects the project's direction, not a delivery commitment with dates.  
> Open Slap! is developed by one person, on 2010 hardware, in available time.

---

## ✅ v2.0 — Shipped (March 2026)

### Agentic core
- [x] Full plan→build loop with autonomous orchestrator
- [x] 14 built-in skills with structured prompts
- [x] CTO emits plans in `plan block` format → orchestrator executes automatically
- [x] Sub-conversations generated per task, accessible in sidebar

### Memory
- [x] Phase 1: heuristic write to `user_soul_events`
- [x] Phase 2: momentum — reinforce memories used in RAG
- [x] Phase 3: probabilistic decay and salience-based pruning
- [x] Phase 4: salience-based consolidated snapshot

### Connectors
- [x] GitHub (repos, issues)
- [x] Google Calendar (upcoming events)
- [x] Gmail (unread emails with subject and sender)
- [x] Google Drive (relevant file search)

### Feedback and learning
- [x] 👍/👎 per message persisted to database
- [x] 👍 retrofeeds: CAC (cache), RAG (salience), expert rating
- [x] 👎 removes cache entry and records negative rating
- [x] MoE router blends keyword score with per-expert approval history

### Interface
- [x] 8 colour themes (Deep Space, Midnight Blue, Forest, Crimson, Slate, Solarized, Light, Paper)
- [x] 5 languages (PT, EN, ES, AR, ZH) with RTL support for Arabic
- [x] Responsive desktop + mobile layout
- [x] Onboarding for new users
- [x] Projects shared across tasks
- [x] Manual expert override in the input area

### Quality
- [x] 50 automated tests (pytest)
- [x] Clean distribution ZIP without credentials or debug files

---

## 🔄 v2.1 — In planning

### Orchestrator
- [ ] Conditional execution: task B only starts when A is approved by user
- [ ] Automatic retry of failed tasks (retry with backoff)
- [ ] Export complete plan results as a document (MD or DOCX)

### Memory
- [ ] Automatic periodic consolidation (lightweight weekly cronjob)
- [ ] Memory review interface: pin/unpin, edit, delete, "don't memorise this"
- [ ] Salience score display in memory UI

### Connectors
- [ ] Google Drive: read document content (not just listing)
- [ ] GitHub: create issues directly from the agent
- [ ] Notion (planned)
- [ ] Slack (planned)

### MoE and Skills
- [ ] Skills visible in auto-expert list (not only in Customise)
- [ ] Guided skill creation via form (in addition to JSON editor)
- [ ] Skill import/export in JSON format

---

## 🔮 v3.0 — Vision (no date)

### Engine
- [ ] True multi-agent: agents with independent memory communicating with each other
- [ ] Tool execution loop with per-step approval (cautious mode)
- [ ] MCP (Model Context Protocol) support for external tool integration

### Memory
- [ ] Vector search (reserved for Slap! PRO — may be ported if community demand exists)
- [ ] Memory shared across users in a workspace (multi-tenant)

### Platform
- [ ] Documented public API (OpenAPI)
- [ ] Headless mode (no frontend) for use in pipelines
- [ ] Official Docker container with compose for one-command deploy

---

## Out of scope for Open Slap!

These features exist or will exist in **Slap! PRO** and derived products, and will not be ported to the open-source core:

- SLA and technical support
- OAuth authentication with external identity providers
- Proprietary connectors (Salesforce, SAP, Oracle, etc.)
- Advanced agent supervision in production environments
- Multi-tenant with data isolation between organisations
- Polished interface for non-technical end users
