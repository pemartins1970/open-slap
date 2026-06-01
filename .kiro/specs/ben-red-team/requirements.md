# B.E.N. 2.0 Red Team — Requisitos

## Contexto

O B.E.N. 2.0 (Behavioral Ethics Network) é o guardrail de segurança do Open Slap!.
Ele opera em `backend/security_guardrail.py` e é chamado no fluxo WebSocket em
`backend/ws/orchestrator.py` antes de qualquer mensagem chegar ao LLM.

O TraceLogger (`backend/trace_logger.py`) registra cada interação em `data/traces/`.

Este spec cobre:
1. Validação de que o TraceLogger está funcionando
2. Red team completo do B.E.N. — ataques via chat, via API REST e via MCP
3. Baseline documentado com métricas reais

## Requisitos

### R1 — TraceLogger Validado
- O TraceLogger deve criar arquivos JSON em `data/traces/` a cada mensagem processada
- Cada arquivo deve conter: session_id, step, harness, input, output, reward, timestamp
- O diretório deve ser criado automaticamente se não existir

### R2 — Dataset de Ataques Completo
- Mínimo 30 payloads cobrindo: prompt injection, jailbreak, command injection, MCP abuse, bypass via encoding, ataques multilíngues
- Cada payload deve ter: categoria, severidade esperada, resultado esperado (block/allow)
- Dataset em `backend/tests/security_payloads.json`

### R3 — Suite de Testes Unitários B.E.N.
- Testar `SecurityGuardrail.evaluate()` contra todos os payloads do dataset
- Testar `SecurityGuardrail.validate_code_execution()` contra scripts maliciosos
- Testar falsos positivos: mensagens legítimas não devem ser bloqueadas
- Cobertura mínima: 100% dos padrões definidos em `security_guardrail.py`

### R4 — Testes de Integração WebSocket
- Simular conexão WebSocket real e enviar payloads maliciosos
- Verificar que a resposta é `{"type": "error", "content": "Segurança: ..."}` para ataques
- Verificar que o TraceLogger registra o evento mesmo quando bloqueado

### R5 — Testes via MCP (vetor de ataque indireto)
- Simular um MCP malicioso tentando injetar comandos via manifesto
- Testar payloads de injeção embutidos em campos de manifesto MCP
- Verificar que o MCPService valida e rejeita manifestos com payloads maliciosos

### R6 — Baseline Documentado
- Arquivo `METRICAS_BASELINE.md` com: total de testes, taxa de bloqueio, falsos positivos, falsos negativos
- Relatório de cobertura: quais vetores de ataque são cobertos e quais não são
- Recomendações de hardening para padrões não cobertos
