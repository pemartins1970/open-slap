# Diário de Desenvolvimento — Open Slap!

Registro cronológico das decisões, descobertas e mudanças de direção durante o desenvolvimento. Escrito para quem quer entender o projeto por dentro — não apenas o que foi feito, mas por quê.

---

## Março de 2026

### v2.0 — Da base ao motor completo

**Ponto de partida**  
O projeto chegou ao estado v2.0 a partir de um protótipo que já tinha: autenticação JWT, suporte a múltiplos providers de LLM com fallback, memória básica em SQLite, RAG com FTS, WebSocket para streaming, e uma interface React funcional mas com muitos strings em PT-BR hardcoded e sem estrutura de skills real.

**Decisões arquiteturais tomadas em v2.0**

*Skills como sistema real, não decoração*  
As skills eram strings de texto sem estrutura. Foram reestruturadas em objetos com `id`, `name`, `description`, `content.prompt`, `content.focus` — o que permite que o backend injete o prompt da skill ativa no `user_context` do LLM. O frontend passou a enviar `skill_id` via WebSocket a cada mensagem.

*Idioma padrão: inglês*  
Decisão pragmática. O projeto tem ambição internacional. Inglês como default, com PT-BR e outros 3 idiomas disponíveis via seletor. A tabela de traduções já existia parcialmente — foi completada para 5 idiomas (PT, EN, ES, AR, ZH).

*Segurança: o .env estava no ZIP de distribuição*  
Descoberto durante auditoria: `src/.env` com um GitHub PAT real estava sendo incluído no arquivo ZIP de distribuição. Corrigido imediatamente. O token foi comprometido e precisou ser revogado. Lição: sempre listar explicitamente o que vai para o ZIP, nunca confiar em `.gitignore` para artefatos de build.

*Loop plan→build: de intenção a implementação*  
O prompt do CTO dizia "emita um plano e orquestre a execução" mas não havia mecanismo nenhum. Implementação em três partes:
1. Protocolo: CTO emite blocos ` ```plan ` com título e `skill_id` por linha
2. Detecção: backend parseia o response com regex e extrai os tasks
3. Orquestrador: `_run_orchestration()` como coroutine de background — itera sobre os tasks, cria sub-conversas, chama o LLM com o prompt da skill, salva respostas, atualiza status

*DatabaseManager: bug de escopo de classe*  
Ao adicionar novos métodos ao `DatabaseManager`, todos foram inseridos fora da classe (após o singleton `db_manager = DatabaseManager()`). Os métodos estavam no arquivo mas não eram acessíveis via instância. Detectado pelos testes: `AttributeError: 'DatabaseManager' object has no attribute 'create_project'`. Corrigido movendo os métodos para dentro da classe.

*Decorator @app.websocket perdido*  
Durante uma das rodadas de edição, o decorator `@app.websocket("/ws/{session_id}")` foi removido acidentalmente. O servidor subia sem erros, mas nenhuma mensagem chegava ao handler do WebSocket — o endpoint não estava roteado. Identificado via auditoria de código antes do deploy.

*Feedback retroalimenta tudo*  
👍 em uma mensagem agora: (1) salva o par Q&A no answer_cache, (2) escreve entrada de memória com salience 0.95, (3) incrementa rating positivo do expert. 👎: (1) remove do cache, (2) registra rating negativo. O MoE router blende keyword score (70%) com taxa de aprovação histórica por expert (30%).

**Sobre testes**  
O projeto tinha 5 testes cobrindo apenas backup, migration e update_checker. Adicionados 45 testes novos cobrindo: schema de novas tabelas, feedback, plan_tasks (incluindo constraint CHECK com `failed`), projects, expert_ratings, memória (decay, reinforce, prune), MoE router (force override, selection_reason, keywords), orchestration_runs. Total: 50 testes, todos passando.

**Mobile**  
O layout original era 100% desktop — sidebar fixa de 220px, sem `@media` queries. Adicionado suporte mobile via CSS classes (`slap-layout`, `slap-sidebar`) com breakpoint em 640px: sidebar colapsa para barra horizontal, hamburger button, header title comprime, status de conexão some.

---

### v2.0 — MCP autônomo: inventário, execução e rastreio (26/03/2026)

**Motivação**  
Transformar o MCP em um “operador autônomo”: escolher ferramentas locais quando existirem, instalar quando faltarem (com segurança), criar ferramentas temporárias quando não houver CLI adequada, e manter rastreabilidade real na área de tarefas.

**Decisões e ajustes**

*Terminal inline com streaming real (linha a linha)*  
Para tarefas de software_operator, a UI recebe eventos via WebSocket e renderiza stdout/stderr incrementalmente, reduzindo a sensação de travamento e permitindo acompanhar o progresso.

*Inventário de software + cache persistente*  
O backend coleta a lista de softwares via winget, persiste um snapshot no banco para evitar custo de CPU a cada pergunta e reconcilia diffs (incluindo itens removidos desde o último scan).

*Winget liberado com segurança operacional*  
Winget entrou na whitelist e a bridge injeta automaticamente `--accept-source-agreements` e `--accept-package-agreements` (e `--silent` em installs) para evitar prompts interativos que quebrariam a automação.

*Auto-build de ferramentas temporárias (python-inline)*  
Quando não existir uma ferramenta local adequada para a lógica solicitada, o fluxo permite criar um script temporário em Python e executá-lo imediatamente. O terminal sinaliza esse momento com: `[AUTO-BUILD] Criando ferramenta customizada para esta tarefa...`.

*Diretório padrão de trabalho (Workspace)*  
Foi definido um diretório padrão (`~/OpenSlap/Workspace`, override por `OPENSLAP_WORKDIR`) para manter consistência de paths entre captura e edição. Isso não impede entregas em outro diretório quando o usuário pedir (via `--cwd`).

*Rastreio obrigatório no TODO (atividades concluídas)*  
O backend registra automaticamente atividades relevantes como itens concluídos no Inbox de tarefas: aprovações de plano, início/fim de orquestração, execuções de software_operator e criação de arquivos. Planos também recebem uma tarefa final `project`, cujo output em bullets é extraído e persistido no TODO.

### v2.0 — Software Operator: contexto de ferramentas + whitelist dinâmica + ordem de eventos (26/03/2026)

**Problema raiz (feedback externo)**  
O backend emitia eventos de execução do `software_operator` após a narrativa já ter “terminado” (fim do streaming), quebrando a conexão visual entre “o que foi dito” e “o que está sendo executado”.

**Mudanças aplicadas**

*Contexto de ferramentas instaladas, legível para o LLM*  
Foi adicionada `_build_software_tool_context()` e a injeção do inventário passou a ser condicional: para `software_operator`, entra um bloco categorizado (“Softwares instalados disponíveis como ferramentas”); para outros experts, mantém-se o resumo top20 (comportamento anterior).

*Whitelist dinâmica sem mexer na âncora fixa*  
Foi adicionada `build_dynamic_whitelist()` na `cli_bridge`, que mescla a whitelist fixa com executáveis detectados no PATH (via `shutil.which`) a partir do inventário instalado. A âncora fixa não é sobrescrita.

*Prompt do software_operator orientado por algoritmo*  
O prompt do `software_operator` foi reescrito para priorizar: (1) usar ferramentas instaladas listadas no contexto; (2) fallback para `python-inline`; (3) instalar via winget/apt/brew quando necessário.

*Melhora na ordem “streaming vs execução”*  
Quando o expert selecionado é `software_operator`, o backend não streama o comando parcial como “resposta visível” e envia um status (“Executando automação…”) imediatamente antes de iniciar a execução, permitindo que os eventos de terminal apareçam como o foco principal durante a ação.

### v2.0 — Tarefas em abas, origem de conversa (source) e varredura do vínculo de projeto (28/03/2026)

**Objetivo**  
Evitar poluição da lista principal de chats por sub-conversas automáticas do orquestrador, e reorganizar a área de Tarefas de forma navegável (mesmo padrão de Configurações), preservando os ajustes existentes.

**Mudanças aplicadas**

*Origem como atributo ortogonal (`source`) — sem criar novos kinds*  
`source` foi adotado como metadado independente de `kind`: conversas do usuário continuam como `kind=conversation` com `source=user`, enquanto sub-conversas criadas por automação podem ser `source=orchestrator`. Isso habilita filtragem cirúrgica na UI sem quebrar o modelo existente.

*Lista principal de conversas filtrada*  
O frontend passou a listar conversas com `kind=conversation&source=user`, reduzindo ruído sem esconder tarefas (`kind=task`) nem impedir auditoria futura.

*Página de Tarefas reorganizada em abas (Projeto → Tarefas → TODO)*  
A tela de tarefas foi reorganizada como Configurações: tabs no topo e conteúdo segmentado. A aba Projeto concentra o kickoff/contexto em Markdown por projeto; Tarefas mantém a lista e busca; TODO mantém o inbox global com links de origem, reforçando o papel do TODO como índice e não como fonte da verdade.

*Varredura do vínculo de projeto (`project_id`) antes de remover UI de projeto*  
Confirmado que `project_id` não é apenas UI: ele injeta contexto compartilhado no chat e é propagado para sub-conversas do orquestrador, além de aparecer em logs de execução. A remoção do botão/fluxo de projeto só é segura após existir inferência automática confiável (ex.: TODO→Task→Chat) que também faça o `set_conversation_project` de forma consistente.

## Decisões de design que ficaram para depois

**Orquestrador totalmente automático com aprovação por etapa**  
O orquestrador atual executa todos os tasks em sequência sem intervenção do usuário. A ideia de "tarefa B só começa quando A é aprovada" foi mapeada no roadmap v2.1 mas não implementada — requer um mecanismo de pause/resume que interage com o WebSocket, mais complexo do que o background task atual.

**Google Drive: leitura de conteúdo**  
O conector de Drive busca e lista arquivos por nome. Ler o conteúdo de um documento (especialmente Google Docs/Sheets) requer parsing adicional e pode gerar payloads muito grandes para o contexto do LLM. Deixado para v2.1 com injeção controlada de chunks.

**Vector search**  
Explicitamente reservado para o Slap! PRO. O FTS do SQLite cobre 80% dos casos de uso com zero dependências extras. Vector search aumenta dramaticamente o tamanho do ZIP de distribuição (requer numpy/faiss ou similar) e a complexidade operacional. A decisão foi manter o core leve.

---

## Filosofia de desenvolvimento adotada

- **Incrementalismo**: cada rodada de desenvolvimento termina com um ZIP testável e funcional
- **Verificação antes de entrega**: cada patch tem um bloco de verificação (`python3 - <<'PYEOF'`) que confirma o que foi feito antes de seguir
- **Backups antes de patches grandes**: `cp arquivo arquivo.bak` antes de qualquer mudança significativa
- **Testes como documentação**: os nomes dos testes descrevem o comportamento esperado, não o código

---
---

# Development Journal — Open Slap!

Chronological record of decisions, discoveries, and direction changes during development. Written for those who want to understand the project from the inside — not just what was done, but why.

---

## March 2026

### v2.0 — From foundation to complete engine

**Starting point**  
The project reached v2.0 state from a prototype that already had: JWT authentication, multi-provider LLM support with fallback, basic SQLite memory, RAG with FTS, WebSocket for streaming, and a functional React interface but with many hardcoded PT-BR strings and no real skills structure.

**Architectural decisions made in v2.0**

*Skills as a real system, not decoration*  
Skills were plain text strings with no structure. They were restructured into objects with `id`, `name`, `description`, `content.prompt`, `content.focus` — allowing the backend to inject the active skill's prompt into the LLM `user_context`. The frontend now sends `skill_id` via WebSocket with every message.

*Default language: English*  
A pragmatic decision. The project has international ambitions. English as the default, with PT-BR and 3 other languages available via selector. The translations table already existed partially — completed for 5 languages (PT, EN, ES, AR, ZH).

*Security: .env was in the distribution ZIP*  
Discovered during audit: `src/.env` with a real GitHub PAT was being included in the distribution ZIP. Fixed immediately. The token was compromised and had to be revoked. Lesson: always explicitly list what goes into the ZIP, never rely on `.gitignore` for build artefacts.

*Plan→build loop: from intent to implementation*  
The CTO prompt said "emit a plan and orchestrate execution" but there was no mechanism. Implementation in three parts:
1. Protocol: CTO emits ` ```plan ` blocks with title and `skill_id` per line
2. Detection: backend parses the response with regex and extracts tasks
3. Orchestrator: `_run_orchestration()` as a background coroutine — iterates over tasks, creates sub-conversations, calls the LLM with the skill prompt, saves responses, updates status

*DatabaseManager: class scope bug*  
When adding new methods to `DatabaseManager`, all were inserted outside the class (after the singleton `db_manager = DatabaseManager()`). The methods were in the file but not accessible via the instance. Detected by tests: `AttributeError: 'DatabaseManager' object has no attribute 'create_project'`. Fixed by moving the methods inside the class.

*@app.websocket decorator lost*  
During one of the editing rounds, the `@app.websocket("/ws/{session_id}")` decorator was accidentally removed. The server started without errors, but no messages reached the WebSocket handler — the endpoint was not routed. Identified via code audit before deploy.

*Feedback retrofeeds everything*  
👍 on a message now: (1) saves the Q&A pair to answer_cache, (2) writes a memory entry with salience 0.95, (3) increments positive rating for the expert. 👎: (1) removes from cache, (2) records negative rating. The MoE router blends keyword score (70%) with historical approval rate per expert (30%).

### v2.0 — Software Operator: tool context + dynamic whitelist + event ordering (26/03/2026)

**Root cause (external feedback)**  
Execution events for `software_operator` were appearing only after the narrative streaming had finished, weakening the user's mental model of “what was said” vs “what is happening”.

**Changes applied**

*Tool context injected in a model-friendly format*  
Added `_build_software_tool_context()` and made inventory injection conditional: `software_operator` receives a categorized “installed tools” block; other experts keep the previous top20 summary behavior.

*Dynamic whitelist without changing the fixed anchor*  
Added `build_dynamic_whitelist()` in `cli_bridge` to merge the fixed whitelist with PATH-resolvable executables (`shutil.which`) derived from the installed inventory. The fixed anchor is never overwritten.

*Algorithmic software_operator prompt*  
Rewrote the `software_operator` prompt to prioritize: (1) use installed tools listed in context; (2) fallback to `python-inline`; (3) install via winget/apt/brew when needed.

*Improved “streaming vs execution” ordering*  
When the selected expert is `software_operator`, the backend stops streaming the partial command as user-facing text and emits a status (“Executing automation…”) right before running, allowing terminal events to become the primary visible feedback during action.

### v2.0 — Task tabs, conversation source filtering, and project linkage audit (28/03/2026)

**Goal**  
Keep the main chat list clean from orchestrator-generated sub-conversations, and reorganise the Tasks area with a navigable structure (same pattern as Settings), without losing the adjustments already made in that section.

**Changes applied**

*Source as an orthogonal attribute (no new kinds)*  
`source` is treated as metadata independent from `kind`: user chats remain `kind=conversation` with `source=user`, while automation sub-conversations can be marked as `source=orchestrator`. This enables precise UI filtering without breaking the existing data model.

*Main conversation list filtered*  
The frontend now lists conversations using `kind=conversation&source=user`, reducing noise while keeping tasks (`kind=task`) intact and still allowing future audit views.

*Tasks page reorganised into tabs (Project → Tasks → TODO)*  
The Tasks screen was reorganised like Settings: top tabs and segmented content. The Project tab concentrates the per-project kickoff/shared Markdown context; Tasks keeps list and search; TODO keeps the global inbox with origin links, reinforcing TODO as an index rather than the source of truth.

*Project linkage (`project_id`) audited before removing project UI*  
Confirmed `project_id` is not only UI: it injects shared project context into chat runs and is propagated to orchestrator sub-conversations, and also appears in execution logs. Removing the project button/flow is only safe after a reliable automatic inference exists (e.g., TODO→Task→Chat) that also sets `project_id` consistently via `set_conversation_project`.

**On testing**  
The project had 5 tests covering only backup, migration, and update_checker. Added 45 new tests covering: new table schemas, feedback, plan_tasks (including CHECK constraint with `failed`), projects, expert_ratings, memory (decay, reinforce, prune), MoE router (force override, selection_reason, keywords), orchestration_runs. Total: 50 tests, all passing.

**Mobile**  
The original layout was 100% desktop — fixed 220px sidebar, no `@media` queries. Mobile support added via CSS classes (`slap-layout`, `slap-sidebar`) with breakpoint at 640px: sidebar collapses to a horizontal bar, hamburger button, header title shrinks, connection status hides.

---

## Design decisions deferred

**Fully automatic orchestrator with per-step approval**  
The current orchestrator executes all tasks in sequence without user intervention. The idea of "task B only starts when A is approved" was mapped in the v2.1 roadmap but not implemented — it requires a pause/resume mechanism that interacts with the WebSocket, more complex than the current background task.

**Google Drive: content reading**  
The Drive connector finds and lists files by name. Reading the content of a document (especially Google Docs/Sheets) requires additional parsing and can generate payloads too large for the LLM context. Left for v2.1 with controlled chunk injection.

**Vector search**  
Explicitly reserved for Slap! PRO. SQLite FTS covers 80% of use cases with zero extra dependencies. Vector search dramatically increases the distribution ZIP size (requires numpy/faiss or similar) and operational complexity. The decision was to keep the core lean.

---

## Development philosophy adopted

- **Incrementalism**: each development round ends with a testable, functional ZIP
- **Verification before delivery**: each patch has a verification block (`python3 - <<'PYEOF'`) confirming what was done before moving on
- **Backups before large patches**: `cp file file.bak` before any significant change
- **Tests as documentation**: test names describe the expected behaviour, not the code

---

### v2.1 — Referências (memória/tokens) + risco de “zombie prompts” (30/03/2026)

**Referências para estudar (insumos)**

- TurboQuant (Google Research) — compressão extrema/eficiência, com foco em reduzir gargalos de memória em mecanismos de quantização e no contexto de KV-cache.
  - https://research.google/blog/turboquant-redefining-ai-efficiency-with-extreme-compression/
- Supermemory — “Memory API” e iniciativas de memória universal (inclui integrações e MCP).
  - https://github.com/supermemoryai/
- Pixel Agents — UI lúdica (VS Code) para visualizar agentes/terminais como personagens e estados (typing/reading/waiting), com potencial de “dashboard de agentes”.
  - https://github.com/pablodelucca/pixel-agents
- AgentScope — framework de agentes com foco em produção; abstrações, orquestração, memória e integrações (inclui MCP/A2A).
  - https://github.com/agentscope-ai/agentscope
- Everything Claude Code — “agent harness performance system”: otimização de tokens, hooks, memória, loops de verificação e scans de segurança.
  - https://github.com/affaan-m/everything-claude-code
- CodeVisualizer — extensão VS Code para grafos/fluxogramas e visualização do codebase (local-first).
  - https://github.com/DucPhamNgoc08/CodeVisualizer
- Blackbox CLI — gerenciamento de sessões, limites de tokens por conversa e compressão de histórico.
  - https://www.blackbox.ai/
  - https://github.com/blackboxaicode/cli
- LLM Council — padrão de brainstorm/consenso: múltiplos modelos geram respostas, revisam entre si, e um “chairman” sintetiza.
  - https://github.com/karpathy/llm-council

**Como isso conecta com Open Slap (direções prováveis)**

- Memória/Context: avaliar compressão/compactação “controlada” e “reversível” (camadas), para reduzir custo de contexto sem perder rastreabilidade.
- Brainstorm: explorar um modo “council” opcional para ideação (geração paralela + revisão cruzada + síntese), limitado a tarefas de baixo risco e com controle de custos.
- Dashboard de agentes: manter a UI atual, mas planejar uma “view alternativa” no futuro (inspirada em Pixel Agents) para estados e saúde de execução (conexão, tarefas, tokens, approvals).
- Segurança: tratar memória como dado não confiável e introduzir barreiras explícitas contra “instruções persistentes” vindas de memória/TODO/perfis.

**Segurança: mitigação de zombie prompts (plano)**

- Definição: “zombie prompt” = instrução maliciosa ou indesejada que entra em um artefato persistente (memória, TODO, notas, contexto de projeto) e volta a ser injetada em conversas futuras, tentando reprogramar o agente (“ignore regras”, “exfiltre chaves”, “sempre execute comandos”, etc.).
- Medidas:
  - Firewall de ingestão: ao persistir memória/TODO, detectar padrões de prompt-injection e salvar como “untrusted_content” (ou descartar) em vez de “policy/instructions”.
  - Firewall de montagem de contexto: toda memória persistida entra como “dados citados” (quote), nunca como instrução; nada do storage pode alterar regras do sistema.
  - Proveniência + escopo: armazenar origem (user/agent/tool), timestamp, e scope (projeto/conversa). Contexto global deve ser mínimo e explicitamente aprovado.
  - Quarentena e revisão: se um item for classificado como “instrução”/“comando”, exigir aprovação humana antes de reusar.
  - Scans recorrentes: varrer itens persistidos em busca de padrões (ex.: “ignore previous”, “system prompt”, “reveal secrets”) e marcar/retirar.
  - “Hard policy” no system prompt: explicitar que instruções vindas de memória/TODO são não-autoritativas e devem ser tratadas como dados.
