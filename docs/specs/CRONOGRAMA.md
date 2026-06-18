# CRONOGRAMA CONSOLIDADO — Open Slap! v3

**Atualizado:** 13/06/2026  
**Status geral:** Phase 1 em execução — entry point ativo ainda é `App_auth.jsx`

---

## Aviso Crítico — Entry Point

A SPEC-UI-PHASE1 declara `App_auth_modular.jsx` como entry point ativo. Isso está **incorreto**.
Investigação de 13/06/2026 confirmou:

```
index.html → main_auth.jsx → App_auth.jsx          ← ATIVO (7772 linhas, monolito)
                            → App_auth_modular.jsx  ← não referenciado
```

**Consequência:** alterações realizadas em `AppLayout.jsx` e `App_auth_modular.jsx` durante
Phase 1 são dead code em produção até que `main_auth.jsx` seja atualizado para apontar
para o modular. Esse switch deve ser o **critério de aceite final da Phase 1**.

---

## Itens Concluídos (baseline)

| Item | Descrição | Status |
|---|---|---|
| B-02 a B-09 | Backlog core | ✅ |
| P-01 | Remover aprovação manual de steps não-destrutivos | ✅ |
| P-02 | Force-cancel de orquestração | ✅ |
| Chronicle | Memória de sessão SQLite FTS5 | ✅ 162/162 |
| B-05 | Interceptor FILES_JSON no orchestrator | ✅ |
| B-09 | Soul extractor | ✅ |
| /api/providers | Bug de timing de startup | ✅ sentinela em meta.py |

---

## Fila — Ordem de Execução

---

### 🔴 AGORA — SPEC-SABRINA-PATCH-001

**Arquivo:** `docs/specs/SPEC-SABRINA-PATCH-001.md`  
**Esforço:** 15 min  
**Dependências:** Nenhuma  
**Bloqueia:** nada (patch independente)

Inserir bloco `"Geração de artefatos:\n"` em dois arquivos:
- `backend/agents/sabrina_agent.py`
- `backend/moe_router_simple.py`

Critério de aceite: pedido de geração de `.md` produz arquivo com estrutura de diretórios,
não código Python.

---

### 🟠 FASE 1 — SPEC-UI-PHASE1 (em execução)

**Arquivo:** `docs/specs/SPEC-UI-PHASE1.md`  
**Dependências:** SABRINA-PATCH-001 independente, pode rodar em paralelo  
**Bloqueia:** Phase 2, Phase 2B

Itens ainda pendentes na Phase 1:
- [ ] Wiring do `AppLayout` no `App_auth_modular.jsx`
- [ ] Left sidebar com dados reais de conversas
- [ ] `RightPanel.jsx` reescrito como coluna fixa (remover `position: fixed`)
- [ ] Settings como modal overlay
- [ ] i18n migrado para react-i18next (5 idiomas, arquivos JSON)
- [ ] Routing React Router (`/chat`, `/conversations`, `/skills`, `/doctor`)
- [ ] **Switch do entry point: `main_auth.jsx` aponta para `App_auth_modular.jsx`**

Critério de aceite final: `App_auth_modular.jsx` está servindo tráfego real. 162/162 testes.

---

### 🟡 B-03 — Rotação de chaves em 429/RESOURCE_EXHAUSTED

**Esforço:** ~2–3h  
**Dependências:** Phase 1 completo  
**Bloqueia:** Phase 2 (Model Selector depende de B-03/B-04)

Rotação automática só aciona em 401. Deve acionar também em:
- `429 Too Many Requests`
- `RESOURCE_EXHAUSTED` (Gemini)

Fix em `llm_manager_simple.py`: expandir condição de rotação.

---

### 🟡 B-04 — Inconsistência provider header vs settings

**Esforço:** ~2h  
**Dependências:** Phase 1 completo  
**Bloqueia:** Phase 2

Duas fontes de verdade para o provider ativo. Consolidar para fonte única
(preferência: DB + WebSocket event sincronizado).

---

### 🟡 UI/Settings — Itens pendentes

**Esforço:** ~2h  
**Dependências:** Phase 1 completo

- [ ] Campos do formulário de cadastro de chave não resetam ao trocar provider
- [ ] Separar LLM Local (Ollama: URL, modelo, timeout) de API Cloud em seções distintas

---

### 🟠 FASE 2 — SPEC-UI-PHASE2 (Model Selector)

**Arquivo:** `docs/specs/SPEC-UI-PHASE2-MODEL-SELECTOR.md`  
**Esforço:** ~1 dia  
**Dependências:** Phase 1, B-03, B-04  
**Bloqueia:** (nada crítico)

Seletor de modelo no chat input (session-only override via WebSocket).
Endpoint `GET /api/models/available` com discovery dinâmica do Ollama.

---

### 🟠 FASE 2B — SPEC-UI-PHASE2B (Step Disclosure)

**Arquivo:** `docs/specs/SPEC-UI-PHASE2B-STEP-DISCLOSURE.md`  
**Esforço:** 4–6h  
**Dependências:** Phase 1 completo  
**Bloqueia:** Phase 3 (Right Panel usa padrão similar para artefatos)

Itens de execução do agente renderizados como linhas colapsáveis no chat.
Click expande para mostrar output completo e artefatos.

Pode ser paralelizado com Phase 2 (Model Selector) — não há dependência entre eles.

---

### 🟡 F-01 — RPM Meter (camada de dados)

**Esforço:** ~4h  
**Dependências:** Phase 2 (infra de provider madura)

UI já existe em `Header.jsx` com `RPM_LIMITS` por provider. Falta:

1. `orchestrator.py`: contador em memória por provider, janela deslizante de 60s
2. WebSocket event `{"type": "rpm_update", "provider": "gemini", "rpm": 3}`
3. `useChatSocket.js`: handler do evento → `setRecentRpm`
4. `App_auth_modular.jsx`: passa `recentRpm` para `<Header>`

---

### 🟡 Botão de Cancelamento de Orquestração

**Esforço:** ~3h  
**Dependências:** Phase 1 completo

Modelo `llama3.2:1b` entra em loop infinito de `[[add_step:]]` sem mecanismo de
interrupção pelo frontend.

Fluxo:
1. Frontend: botão "Cancelar" visível durante `orchStatus === 'running'`
2. WebSocket message `{"type": "cancel"}` para o backend
3. `orchestrator.py`: flag de cancelamento que interrompe o loop de steps

---

### 🟢 FASE 3 — Right Panel (Conteúdo Real)

**Dependências:** Phase 1, Phase 2B (padrão de disclosure reutilizável)

Conteudo do painel direito:
- Consumo da sessão (tokens, requests)
- Artefatos gerados (lista de `files_written` events)
- Previews de artefatos recentes

O padrão `StepDisclosure` se aplica também aos artefatos aqui.

---

### 🟢 FASE 4 — Integrações Externas

**Dependências:** Phase 3  
Escopo a definir em spec dedicada.

---

### 🔵 Backlog Técnico — Source of Truth do Prompt da Sabrina

**Esforço:** ~1h  
**Prioridade:** Baixa (não bloqueia nada)

Unificar `SABRINA_SYSTEM_PROMPT` para uma única fonte.
Opção recomendada: arquivo dedicado `backend/prompts/sabrina.py` importado pelos dois.

---

## Resumo Visual

```
AGORA              Phase 1               B-03  B-04  UI/Settings
  │                   │                    │      │
  ▼                   ▼                    ▼      ▼
SABRINA-        Three-Zone Shell     ─────────────────────
PATCH-001       + entry switch                   │
                    │                         Phase 2
                    │                      Model Selector
                    │                            │
                    │                       Phase 2B        F-01   Cancelar
                    │                    Step Disclosure      │        │
                    │                            │            │        │
                    └──────────────────────┬───────────┬─────────
                                          │           │
                                       Phase 3     Phase 4
                                    Right Panel  Integrações
```

---

## Contagem de Testes

| Marco | Testes |
|---|---|
| Baseline atual | 125/125 |
| Phase 1 completo | 162/162 (i18n + routing) |
| Phase 2 | +testes model selector |
| Phase 2B | sem novos testes unitários (componente UI) |
