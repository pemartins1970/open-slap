# SPEC P6: Migração Seletiva dos Agentes Legados
**Projeto**: Open Slap! v3  
**Data**: 2026-05-30  
**Prioridade**: P6  
**Depende de**: P1 concluído ✅  

---

## Diagnóstico dos Agentes Legados

Antes de implementar, é necessário entender o que cada agente legado realmente é:

| Agente | Tipo Real | Tem system_prompt? | Faz chamada LLM? | Candidato a BaseAgent? |
|--------|-----------|-------------------|-----------------|----------------------|
| `CTOAgent` | Validador de regras | Não | Não | ❌ |
| `SecurityTesterAgent` | Auditor HTTP ativo | Não | Não | ❌ |
| `ReviewLoop` | Orquestrador interno | Não | Não | ❌ |

**Conclusão:** nenhum dos três deve herdar de `BaseAgent`. `BaseAgent` assume um agente conversacional que chama LLM com um `system_prompt`. Forçar essa herança nos três legados seria a abstração errada — quebraria o contrato semântico do `BaseAgent` e adicionaria `stream_execute()` / `execute()` em classes que nunca vão usá-los.

O objetivo real do P6 é diferente do que o enunciado sugeria: **eliminar o bloco `else` (fallback) do orchestrator**, que é o sintoma da bifurcação arquitetural. Isso é alcançável sem migrar os legados para BaseAgent.

---

## Objetivo Real

Eliminar a bifurcação no `ws/orchestrator.py`:

```python
# Estado atual — dois caminhos paralelos
if agent:          # agentes novos via AgentRegistry
    ...
else:              # agentes legados via llm_manager direto
    ...
```

Para isso, o CTO precisa ter um `system_prompt` e ser registrado no `AgentRegistry` como agente conversacional — porque o MoE router já tem um expert `cto` com keywords e descrição. O `CTOAgent` legado (validador de regras) permanece intacto para uso interno do `ReviewLoop`.

`SecurityTesterAgent` e `ReviewLoop` não aparecem no fluxo de chat e não têm ID no MoE router — não precisam de nenhuma mudança.

---

## Escopo

### Arquivos a criar

| Arquivo | Descrição |
|---------|-----------|
| `backend/agents/cto_chat_agent.py` | CTOChatAgent — BaseAgent com system_prompt conversacional |

### Arquivos a modificar

| Arquivo | Mudança |
|---------|---------|
| `backend/agents/__init__.py` | Registrar `CTOChatAgent` com name=`"cto"` |
| `backend/ws/orchestrator.py` | Remover bloco `else` (fallback) após todos os experts do MoE terem correspondente no registry |

### Arquivos a NÃO modificar

- `backend/agents/cto_agent.py` — permanece como validador interno
- `backend/agents/security_tester.py` — permanece como auditor HTTP
- `backend/agents/review_loop.py` — permanece como orquestrador interno
- `backend/agents/base.py` — não tocar

---

## Implementação Detalhada

### 1. `backend/agents/cto_chat_agent.py` — CRIAR

```python
"""
CTOChatAgent — Agente CTO conversacional para o fluxo de chat.

Distinto do CTOAgent (validador de regras em cto_agent.py), este agente
herda de BaseAgent e responde via LLM usando o system_prompt do CTO.
O CTOAgent legado permanece intacto para uso interno do ReviewLoop.
"""
from backend.agents.base import BaseAgent, agent_registry

CTO_SYSTEM_PROMPT = """Você é o CTO do time de agentes do Open Slap!, um sistema \
de desenvolvimento assistido por IA. Seu papel é:

- Tomar decisões técnicas fundamentadas: arquitetura, stack, padrões de código
- Revisar e validar planos de desenvolvimento propostos pelo time
- Identificar riscos técnicos, dívida técnica e trade-offs
- Orientar sobre boas práticas de segurança, escalabilidade e manutenibilidade
- Ser direto e preciso: você fala com desenvolvedores, não com usuários finais

Quando receber uma solicitação:
1. Avalie o contexto técnico completo antes de responder
2. Aponte riscos e alternativas quando relevante
3. Dê respostas acionáveis, não genéricas
4. Se a solicitação for vaga, peça especificidade antes de propor soluções

Você tem autoridade técnica final sobre decisões de arquitetura e segurança."""

CTO_SKILLS = [
    {"name": "architecture_review", "description": "Revisão de arquitetura e decisões técnicas"},
    {"name": "code_review", "description": "Revisão de código e padrões"},
    {"name": "security_assessment", "description": "Avaliação de riscos de segurança"},
    {"name": "tech_planning", "description": "Planejamento técnico e roadmap"},
]


class CTOChatAgent(BaseAgent):
    name = "cto"
    description = "CTO — Decisões técnicas, arquitetura e revisão de código"
    system_prompt = CTO_SYSTEM_PROMPT
    skills = CTO_SKILLS


agent_registry.register(CTOChatAgent())
```

**Importante:** o `name = "cto"` deve corresponder exatamente ao `id` do expert CTO no MoE router. Verificar antes de implementar.

---

### 2. `backend/agents/__init__.py` — ADICIONAR IMPORT

Adicionar ao final das importações existentes:

```python
from backend.agents.cto_chat_agent import CTOChatAgent  # noqa: F401
```

O padrão é o mesmo dos outros 6 agentes já registrados.

---

### 3. `backend/ws/orchestrator.py` — VERIFICAR e SIMPLIFICAR

**Antes de remover o `else`**, verificar quais IDs de expert o MoE router pode selecionar e se todos têm correspondente no `AgentRegistry`:

```
MoE experts conhecidos → AgentRegistry
─────────────────────────────────────
"frontend"     → FrontendDevAgent  ✅
"backend"      → BackendDevAgent   ✅
"devops"       → DevopsAgent       ✅
"cto"          → CTOChatAgent      ✅ (após este sprint)
"general"      → ???               ❓ verificar
"security"     → ???               ❓ verificar
```

Se `general` e `security` existirem no MoE sem correspondente no registry, o `else` ainda é necessário para eles. Nesse caso, **não remover o `else`** — apenas documentar quais IDs ainda usam o fallback.

A remoção completa do `else` só é segura quando **todos** os IDs possíveis do MoE router tiverem correspondente no `AgentRegistry`.

**Ação para o Opencode:** listar todos os `id` definidos em `moe_router_simple.py` e confirmar quais têm e quais não têm correspondente no registry após a criação do `CTOChatAgent`.

---

## Testes a adicionar

### Adições em `backend/tests/test_agent_llm.py`

```python
@pytest.mark.asyncio
async def test_cto_chat_agent_registered():
    """CTOChatAgent deve estar registrado com name='cto'."""
    from backend.agents.base import agent_registry
    # Importar para garantir que o registro ocorreu
    import backend.agents.cto_chat_agent  # noqa: F401
    agent = agent_registry.get("cto")
    assert agent is not None
    assert agent.name == "cto"
    assert len(agent.system_prompt) > 100  # system_prompt não é placeholder


@pytest.mark.asyncio
async def test_cto_chat_agent_execute():
    """CTOChatAgent deve executar via LLM (mockado)."""
    from backend.agents.cto_chat_agent import CTOChatAgent
    agent = CTOChatAgent()
    with patch("backend.llm_manager_simple.llm_manager") as mock_llm:
        mock_llm.stream_generate = fake_stream  # reutilizar fixture existente
        result = await agent.execute("Avalie a arquitetura do projeto", {})
    assert result.status == "success"
    assert result.data["agent"] == "cto"


def test_cto_agent_legado_intacto():
    """CTOAgent legado não deve ser afetado por este sprint."""
    from backend.agents.cto_agent import CTOAgent
    agent = CTOAgent()
    assert hasattr(agent, "process_intent")
    assert not hasattr(agent, "stream_execute")  # não é BaseAgent
```

---

## Critérios de Aceite

1. `agent_registry.get("cto")` retorna `CTOChatAgent` instanciado
2. Mensagem de chat que o MoE rotearia para `cto` recebe resposta do `CTOChatAgent` via LLM
3. `CTOAgent` legado (`cto_agent.py`) permanece inalterado e `ReviewLoop` continua funcional
4. `pytest backend/tests/` — 100% passando, sem regressões
5. Opencode confirma quais IDs do MoE ainda usam fallback (documentar no `CURRENT_STATE.md`)

---

## O que este sprint NÃO faz

- Não migra `SecurityTesterAgent` para BaseAgent — é auditor HTTP, não agente conversacional
- Não migra `ReviewLoop` para BaseAgent — é orquestrador interno
- Não remove o bloco `else` do orchestrator se houver IDs do MoE sem correspondente no registry
- Não cria agentes conversacionais para `security` ou `general` se esses IDs existirem no MoE — isso seria P2.5, não P6

---

## Contexto para o Opencode

Ler antes de implementar:
- `backend/agents/base.py` — contrato do BaseAgent
- `backend/moe_router_simple.py` — listar todos os `id` de experts definidos
- `backend/agents/__init__.py` — padrão de registro existente
- `backend/agents/cto_agent.py` — NÃO modificar, apenas entender
