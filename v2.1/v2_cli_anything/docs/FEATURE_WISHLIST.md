# Wishlist de Recursos (Backlog) — Open Slap!

Este documento registra recursos desejados e o status no Open Slap. Implementação: somente após estabilização de Projetos/Tarefas.

## Status atual (resumo)

- Já existe cache de respostas (CAC) com hash SHA-256 da pergunta e TTL.
- Já existe roteamento simples (MoE por expert/skill) e fallback de provider por ordem.
- Não existe (ainda) cost tracking/budget, circuit breaker/backoff, lifecycle hooks genéricos, túnel integrado, REPL CLI ou job-state-machine com auto-repair.

## Matriz (itens do questionamento)

| Recurso | Status | Observações / Procedimento proposto |
|---|---|---|
| Circuit breaker + retry + backoff exponencial (providers LLM) | Parcial | Hoje há fallback por provider, mas sem backoff/circuit. Proposta: camada de “provider health” (erros 429/5xx/timeouts), janela móvel, open/half-open/closed e jittered backoff. Base: [llm_manager_simple.py](file:///c:/workaround/projetos/Slap/Open_Slap/v2.1/v2_cli_anything/src/backend/llm_manager_simple.py). |
| Detecção de leak de credenciais no output | Parcial | Há redaction ao persistir em DB (ex.: JWT/Bearer/email) via [_redact_text](file:///c:/workaround/projetos/Slap/Open_Slap/v2.1/v2_cli_anything/src/backend/db.py). Falta “guard” no outbound: varrer resposta antes de enviar ao usuário e bloquear/mascarar. |
| Cache de respostas LLM com SHA-256 da prompt | Já existe | CAC usa `sha256` da pergunta e salva em `answer_cache` (TTL por horas): [main_auth.py](file:///c:/workaround/projetos/Slap/Open_Slap/v2.1/v2_cli_anything/src/backend/main_auth.py) + [db.py](file:///c:/workaround/projetos/Slap/Open_Slap/v2.1/v2_cli_anything/src/backend/db.py). |
| Cost tracking + budget guards (80% aviso, 100% bloqueio) | Não existe | Precisa de: captura de tokens/custo por provider/modelo, tabela de agregação, e guardrail no runtime. Depende de termos tokens/usage confiáveis por provider. |
| Extended thinking (Claude 3.7+ e o1) | Não existe | Hoje não há integração Anthropic, e “reasoning effort” ainda não está modelado como setting por request. Pode entrar via providers compatíveis (OpenAI “o1” e similares) quando a camada de provider suportar parâmetros. |
| MCP client para tool servers externos | Parcial | Existe integração pontual (ex.: Telegram) e harness de ferramentas, mas não um client MCP genérico. Proposta: definir protocolo de tool server, auth, allowlist e UI de gerenciamento. |
| Lifecycle hooks (inbound, tool calls, outbound) | Não existe | Proposta: pipeline de eventos (pre-inbound, post-inbound, pre-tool, post-tool, pre-outbound, post-outbound) com logs estruturados e políticas (redaction, rate limit, audit). |
| Smart model routing (queries simples → modelos baratos) | Parcial | Existe roteamento por expert (MoE) e seleção de provider por ordem, mas não um “complexity router” por custo/latência. Proposta: classificador barato + thresholds + fallback. |
| Suporte a túneis (cloudflared/ngrok/tailscale) | Não existe | Pode ser “procedimento documentado”, não feature core. Proposta: doc com comandos recomendados e alertas de segurança. |
| REPL interativo (CLI) | Não existe | Ideia futura alinhada com docs/EXTERNAL_REFERENCES.md (free-code). Proposta: cliente CLI fino consumindo a API/WebSocket do backend, sem duplicar lógica. |
| Wizard de criação de projeto (sem título/mote, Sabrina conduz e gera kickoff) | Parcial | Hoje existe um wizard “Start Project” no chat, e existe criação manual de projeto (nome obrigatório) no módulo de Projetos. Proposta: unificar o fluxo: “Criar projeto” dispara o wizard e só cria/renomeia o projeto ao final, com kickoff gerado e vinculado. |
| Routines com event triggers além de cron | Parcial | Há mecanismos de eventos (ex.: friction/auditoria), mas não um scheduler de rotinas por gatilho (arquivo, webhook, mudança de estado). Proposta: “rules engine” simples + triggers + permissões. |
| Job state machine com auto-repair | Parcial | Há orquestração e status, mas não “auto-repair” genérico. Proposta: state machine por task/step (pending/running/failed/retrying/done), com retries limitados e diagnósticos. |

## Recomendação de prioridade (para depois de Projetos/Tarefas)

- Prioridade alta (resiliência/segurança): circuit breaker+backoff, outbound leak guard, hooks mínimos (pre-outbound).
- Prioridade média (produto): smart routing por custo, budget/cost tracking, rotinas por gatilho.
- Prioridade baixa (forma/futuro): túnel integrado (fica como doc), REPL CLI (se houver demanda), extended thinking por provider.
