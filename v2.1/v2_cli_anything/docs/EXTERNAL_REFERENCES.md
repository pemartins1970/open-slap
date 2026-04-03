# Referências Externas (Backlog) — Open Slap!

Este documento registra ideias, riscos e procedimentos inspirados por projetos externos. Implementação: somente após estabilização de Projetos/Tarefas.

## Microsoft: Agent Lightning

Link: https://github.com/microsoft/agent-lightning

### Ideia principal

- Instrumentar qualquer agente com spans (prompt, tool calls, outputs, rewards) e permitir otimização (RL, prompt optimization, SFT) sem reescrever o agente.

### O que aproveitar no Open Slap!

- Telemetria local estruturada: transformar execução em “traces” versionados.
- Store central: separar runtime (coleta) de otimizador offline (aprendizado).
- Recursos atualizáveis com rollback: prompts de skills, heurísticas do MoE, templates de plano.
- Treino seletivo: otimizar um expert/skill por vez, mantendo isolamento.

### Procedimentos (etapa posterior)

- Definir um schema de trace local (mínimo): trace_id, conversation_id, message_id, tool_call, tool_result, timings, status, feedback.
- Persistir traces sem mexer no RAW (SQL de mensagens continua integral).
- Criar um “otimizador offline” inicial sem RL: replay + prompt refinement + avaliação baseada em testes/lint/feedback.
- Adicionar UI opt-in: “Treino local”, seleção por skill/expert, histórico de mudanças e rollback.

### Riscos/alertas

- Reward design: precisa ser barato, determinístico e auditável.
- Privacidade: traces devem respeitar redaction e não incluir secrets.

## paoloanzn: free-code (CLI)

Link: https://github.com/paoloanzn/free-code

### Ideia principal

- Uma CLI de agente de código (terminal UI), com ferramentas (bash/read/edit/search) e mecanismos de planejamento/memória, focada em execução no terminal.

### O que pode ser útil no Open Slap!

- UX de CLI para automação: modo “one-shot” + modo REPL.
- Bridge/integração com IDE e protocolos (ex.: LSP/MCP) como inspiração de arquitetura.
- Feature gating por flags, com builds diferenciados.

### Procedimentos (etapa posterior)

- Definir objetivo: CLI do Open Slap como alternativa ao frontend web, ou como ferramenta de operadores.
- Mapear comandos mínimos:
  - login/config
  - selecionar projeto
  - executar “plan → approve → run”
  - listar/atualizar TODOs
  - consultar memória RAW e snapshot
- Reusar o backend atual como servidor (API/WebSocket) e criar um cliente CLI fino (preferencialmente sem duplicar lógica).

### Riscos/alertas

- Este repositório declara ser um fork buildável de uma base exposta publicamente; avaliar implicações legais/éticas antes de depender dele.
- Não incorporar código/artefatos de terceiros sem revisão de licenças e sem evitar “contaminação” de implementação.

## Andrej Karpathy: llm-council (multi-model consensus)

Link: https://github.com/karpathy/llm-council

### Ideia principal

- “Council” de modelos: coletar respostas independentes, fazer revisão cruzada entre modelos (anônimo) e sintetizar por um “Chairman”.

### O que aproveitar no Open Slap!

- Consenso multi-modelo para tarefas sensíveis (ex.: análise, verificação, segurança), sem depender de um único provider.
- Etapas explícitas anti-alucinação:
  - respostas independentes
  - revisão cruzada com ranking por acurácia/insight
  - síntese final
- “Primary source veto”: quando houver fonte primária contraditória, capar confiança e forçar resultado para “mixed/needs verification”.

### Procedimentos (etapa posterior)

- Definir um “council mode” no orquestrador (opt-in) para operações de alto risco.
- Registrar no trace/event log:
  - modelos usados
  - notas de revisão
  - decisão do chairman + justificativa curta
  - links de fontes primárias que influenciaram veto
- Aplicar budget guard: limitar tokens/custo para evitar explosão de gasto.

### Riscos/alertas

- Custo/latência: multi-model aumenta custo e tempo; deve ser restrito a casos específicos.
- Viés de revisão: anonimizar identidades reduz “favoritismo” entre providers.
