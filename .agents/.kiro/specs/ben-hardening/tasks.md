# Tasks

- [x] 1. GAP-01 Normalização de texto no evaluate()
  - Adicionar função `normalize_text()` em `backend/security_guardrail.py`
  - Normalizar unicode NFKD → ASCII, colapsar espaços extras, converter leet speak (0→o, 1→i, 3→e, 4→a, 5→s, 7→t, 8→b)
  - Aplicar normalização no início de `evaluate()` antes de verificar padrões
  - Atualizar dataset: remover xfail de CAT6-001, CAT6-002, CAT6-003
  - Executar `python -m pytest backend/tests/test_ben_unit.py -v --tb=short` e confirmar CAT6 passando
  - _Requirements: GAP-01_

- [x] 2. GAP-03 Adicionar BLOCKED_CODE_PATTERNS no evaluate()
  - Em `SecurityGuardrail.evaluate()`, após o loop de `BLOCKED_COMMAND_PATTERNS`, adicionar loop sobre `BLOCKED_CODE_PATTERNS`
  - Retornar `{"action": "block", "reason": "Padrão de código malicioso detectado no prompt.", "severity": "high", "confidence": 0.95}`
  - Atualizar dataset: remover xfail de CAT5-001, CAT5-002, CAT5-003
  - Executar testes e confirmar CAT5 passando em `evaluate()`
  - _Requirements: GAP-03_
  - _Dependencies: 1_

- [x] 3. GAP-04 MCPService sanitiza campos de texto via B.E.N.
  - Em `MCPService.validate_manifest()`, após validação estrutural existente, adicionar verificação dos campos `name`, `description`, `id` via `SecurityGuardrail.evaluate()`
  - Adicionar verificação dos itens da lista `tools` via `SecurityGuardrail.evaluate(str(tool))`
  - Se qualquer campo retornar `action == "block"`, adicionar ao `errors` e retornar `{"valid": False}`
  - Executar `python -m pytest backend/tests/test_ben_mcp_vector.py -v --tb=short` — os testes de GAP-MCP-01/02/04 devem agora falhar (comportamento mudou: manifesto é rejeitado)
  - Atualizar `test_ben_mcp_vector.py`: nos testes de injection (test_mcp_manifest_with_injection_in_name, test_mcp_manifest_with_injection_in_description, test_mcp_manifest_with_command_in_tools), mudar assert para `result["valid"] is False`
  - Executar testes novamente e confirmar todos passando
  - _Requirements: GAP-04_
  - _Dependencies: 1_

- [x] 4. GAP-02 Multilíngue ES/FR em PROMPT_INJECTION_PATTERNS
  - Adicionar 2 novos padrões em `PROMPT_INJECTION_PATTERNS` em `backend/security_guardrail.py`:
    - Espanhol: `re.compile(r"\b(olvidar|ignorar)\b.*\b(reglas|instrucciones)\b", re.IGNORECASE)`
    - Francês: `re.compile(r"\b(oublier|ignorer)\b.*\b(instructions|règles)\b", re.IGNORECASE)`
  - Atualizar dataset: remover xfail de CAT7-002, CAT7-003
  - Executar testes e confirmar CAT7-002 e CAT7-003 passando
  - _Requirements: GAP-02_
  - _Dependencies: 1_

- [x] 5. GAP-05 TraceLogger step counter por sessão
  - Em `WebSocketOrchestrator.__init__()`, adicionar `self.session_steps: Dict[str, int] = {}`
  - Em `_handle_chat_message()`, substituir `step=1` por: `step = self.session_steps.get(session_id, 0) + 1` seguido de `self.session_steps[session_id] = step`
  - Executar `python -m pytest backend/tests/test_ben_integration_ws.py -v --tb=short` e confirmar todos passando
  - _Requirements: GAP-05_
  - _Dependencies: 1_

- [x] 6. Executar suite completa e atualizar METRICAS_BASELINE.md
  - Executar `python -m pytest backend/tests/test_ben_unit.py backend/tests/test_ben_integration_ws.py backend/tests/test_ben_mcp_vector.py -v --tb=short`
  - Atualizar `METRICAS_BASELINE.md`: novos números, score atualizado (alvo 9/10), seção "Pós-Hardening"
  - _Requirements: todos_
  - _Dependencies: 2, 3, 4, 5_
