# Tasks

- [x] 1. Criar dataset de ataques security_payloads.json
  - Criar `backend/tests/security_payloads.json` com 30+ payloads em 9 categorias
  - Categorias: prompt_injection(5), jailbreak(4), system_prompt_leak(3), command_injection_os(4), code_injection(3), bypass_encoding(3), multilingual(3), mcp_abuse(2), false_positive(5)
  - Cada entrada: id, category, severity, text, expected_action, notes
  - _Requirements: R2_

- [x] 2. Suite de testes unitários B.E.N. (test_ben_unit.py)
  - Criar `backend/tests/test_ben_unit.py` com pytest parametrizado
  - Testar SecurityGuardrail.evaluate() contra todos os payloads do dataset
  - Testar SecurityGuardrail.validate_code_execution() contra CAT-5
  - Verificar campos de resposta: action, reason, severity, confidence
  - Testar falsos positivos (CAT-9) — devem retornar "allow"
  - _Requirements: R3_
  - _Dependencies: 1_

- [x] 3. Testes de integração WebSocket (test_ben_integration_ws.py)
  - Criar `backend/tests/test_ben_integration_ws.py`
  - Mockar autenticação e LLM (sem chamadas reais)
  - Testar bloqueio de CAT-1/2/3 via WebSocket — resposta deve ser type:error
  - Testar passagem de mensagens legítimas (CAT-9)
  - Verificar que TraceLogger cria arquivo em data/traces/ após mensagem legítima
  - _Requirements: R1, R4_
  - _Dependencies: 1_

- [ ] 4. Testes do vetor MCP (test_ben_mcp_vector.py)
  - Criar `backend/tests/test_ben_mcp_vector.py`
  - Testar MCPService.validate_manifest() com injection em campos name/description/id
  - Testar manifesto com compatible_with malicioso
  - Testar payloads em campos tools/agents
  - Documentar gaps: campos de texto não são sanitizados contra injection
  - _Requirements: R5_
  - _Dependencies: 1_

- [x] 5. Executar testes e gerar METRICAS_BASELINE.md
  - Executar pytest nas suites criadas (tasks 2, 3, 4)
  - Criar `METRICAS_BASELINE.md` na raiz do projeto com resultados reais
  - Incluir: total testado, taxa de bloqueio, falsos positivos, gaps identificados, recomendações de hardening
  - _Requirements: R6_
  - _Dependencies: 2, 3, 4_
