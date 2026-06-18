# SPEC: Agent LLM Integration — Opção A
**Projeto**: Open Slap! v3  
**Data**: 2026-05-28  
**Prioridade**: P1 (bloqueia toda funcionalidade v3)  
**Assignee**: Opencode  

---

## Contexto e Objetivo

Os 6 agentes novos (PO, PMO, Frontend, Backend, DevOps, Documentation) existem como módulos registrados mas não fazem nenhuma chamada LLM. O método `execute()` retorna o system_prompt como dado — é um stub. Este spec implementa a **Opção A**: cada agente é um caller LLM independente que usa seu próprio system_prompt e o `llm_manager` existente.

**Premissa de hardware**: o usuário primário usa LLM remota (Gemini, Groq, OpenAI, OpenRouter). Ollama é fallback opcional, não primário.

---

## Escopo

### Arquivos a modificar

| Arquivo | Tipo de mudança |
|---------|-----------------|
| `backend/agents/base.py` | Adicionar `stream_execute()`, corrigir `execute_on_agent()`, implementar `execute()` padrão |
| `backend/agents/po_agent.py` | Remover stub `execute()`, ajustar nome de registro |
| `backend/agents/pmo_agent.py` | Idem |
| `backend/agents/frontend_dev_agent.py` | Idem + registrar como `frontend` |
| `backend/agents/backend_dev_agent.py` | Idem + registrar como `backend` |
| `backend/agents/devops_agent.py` | Idem + registrar como `devops` |
| `backend/agents/documentation_agent.py` | Idem |
| `backend/ws/orchestrator.py` | Adicionar delegação ao AgentRegistry antes do fallback direto |

### Arquivos a NÃO modificar neste sprint

- `llm_manager_simple.py` — funciona como está, não tocar
- `moe_router_simple.py` — funciona como está, não tocar  
- `main_auth_refactored.py` — não tocar
- Agentes legados (`cto_agent.py`, `security_tester.py`, `review_loop.py`) — não tocar ainda (P6 do QA)

---

## Mudanças Detalhadas

### 1. `backend/agents/base.py` — SUBSTITUIR CONTEÚDO COMPLETO

```python
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, AsyncGenerator, Dict, List, Optional, Type

logger = logging.getLogger(__name__)


@dataclass
class AgentResult:
    status: str                              # "success" | "error"
    data: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None


class BaseAgent:
    """
    Agente base com capacidade real de chamada LLM.
    Subclasses definem name, description, system_prompt e skills.
    O execute() padrão coleta o stream e devolve AgentResult.
    Para streaming direto no WebSocket, use stream_execute().
    """
    name: str = ""
    description: str = ""
    system_prompt: str = ""
    skills: List[Dict[str, Any]] = []

    def _build_expert_dict(self) -> Dict[str, Any]:
        """Constrói o dict de expert no formato esperado pelo llm_manager."""
        return {
            "id": self.name,
            "name": self.name,
            "prompt": self.system_prompt,
            "description": self.description,
        }

    async def stream_execute(
        self,
        intent: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> AsyncGenerator[str, None]:
        """
        Faz a chamada LLM e faz yield de chunks de texto.
        Filtra metadados (dicts) que o llm_manager pode emitir antes do primeiro chunk.
        """
        # Import local para evitar circular import e permitir lazy loading
        from backend.llm_manager_simple import llm_manager  # noqa: PLC0415

        ctx = context or {}
        user_context: str = ctx.get("user_context", "") or ""
        llm_override: Optional[Dict[str, Any]] = ctx.get("llm_override")

        expert_dict = self._build_expert_dict()

        try:
            async for chunk in llm_manager.stream_generate(
                prompt=intent,
                expert=expert_dict,
                user_context=user_context,
                llm_override=llm_override,
            ):
                if isinstance(chunk, str):
                    yield chunk
        except Exception as exc:
            logger.error(
                "Agent %s stream_execute error: %s", self.name, exc, exc_info=True
            )
            yield f"❌ Erro no agente {self.name}: {exc}"

    async def execute(
        self,
        intent: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> AgentResult:
        """
        Executa o agente e retorna AgentResult com a resposta completa.
        Subclasses podem sobrescrever para lógica customizada (ex.: multi-step).
        """
        chunks: List[str] = []
        async for chunk in self.stream_execute(intent, context):
            chunks.append(chunk)

        response = "".join(chunks)

        if response.startswith("❌"):
            return AgentResult(status="error", error=response, data={"agent": self.name})

        return AgentResult(
            status="success",
            data={"response": response, "agent": self.name},
        )

    def get_manifest(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "system_prompt": self.system_prompt[:200] + "...",
            "skills": [s["name"] for s in self.skills],
        }


class AgentRegistry:
    def __init__(self) -> None:
        self._agents: Dict[str, BaseAgent] = {}

    def register(self, agent: BaseAgent) -> None:
        self._agents[agent.name] = agent

    def get(self, name: str) -> Optional[BaseAgent]:
        return self._agents.get(name)

    def list_all(self) -> List[Dict[str, Any]]:
        return [a.get_manifest() for a in self._agents.values()]

    async def execute_on_agent(
        self,
        name: str,
        intent: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> AgentResult:
        """Async — awaita agent.execute() corretamente."""
        agent = self.get(name)
        if not agent:
            return AgentResult(status="error", error=f"Agent '{name}' not found")
        return await agent.execute(intent, context)


agent_registry = AgentRegistry()
```

**Pontos críticos:**
- `execute_on_agent` agora é `async def` com `await` — corrige o bug de coroutine não executada
- `stream_execute` filtra `isinstance(chunk, str)` para descartar o dict de metadados que o llm_manager emite antes do primeiro chunk real
- Import do llm_manager é local (dentro da função) para evitar circular import no momento do import do módulo
- `execute()` padrão implementado em BaseAgent — subclasses não precisam sobrescrever a menos que tenham lógica multi-step

---

### 2. Agentes individuais — padrão de modificação

Para cada um dos 6 agentes (PO, PMO, Frontend, Backend, DevOps, Documentation):

**Remover**: o método `execute()` inteiro (o stub que retorna o system_prompt como dado)  
**Manter**: `name`, `description`, `system_prompt`, `skills`, a linha `agent_registry.register(...)`  
**Ajustar**: `name` de registro conforme tabela abaixo

#### Tabela de mapeamento de nomes

O MoE router usa IDs específicos para rotear mensagens. Para que o AgentRegistry e o MoE router falem o mesmo idioma, os agentes devem se registrar com os IDs que o MoE já conhece.

| Arquivo | `name` atual | `name` correto | ID no MoE |
|---------|-------------|----------------|-----------|
| `frontend_dev_agent.py` | `"frontend_dev"` (presumido) | `"frontend"` | `frontend` |
| `backend_dev_agent.py` | `"backend_dev"` (presumido) | `"backend"` | `backend` |
| `devops_agent.py` | `"devops"` (presumido) | `"devops"` | `devops` ✅ sem mudança |
| `po_agent.py` | `"po"` | `"po"` | sem MoE ID — sem mudança |
| `pmo_agent.py` | `"pmo"` | `"pmo"` | sem MoE ID — sem mudança |
| `documentation_agent.py` | `"documentation"` (presumido) | `"documentation"` | sem MoE ID — sem mudança |

> **Nota**: PO, PMO e Documentation não têm ID correspondente no MoE router. Eles existem no AgentRegistry e podem ser chamados diretamente (ex.: por um orquestrador futuro), mas não serão ativados automaticamente pelo fluxo de chat neste sprint. Isso é intencional — é preferível a criar IDs no MoE sem roteamento definido.

#### Exemplo — `frontend_dev_agent.py` após modificação

```python
# [manter imports existentes]
# [manter FRONTEND_DEV_SYSTEM_PROMPT e FRONTEND_DEV_SKILLS como estão]

class FrontendDevAgent(BaseAgent):
    name = "frontend"                        # ← alterado de "frontend_dev"
    description = "Frontend Dev Agent — componentes UI"
    system_prompt = FRONTEND_DEV_SYSTEM_PROMPT
    skills = FRONTEND_DEV_SKILLS
    # execute() REMOVIDO — herda de BaseAgent


agent_registry.register(FrontendDevAgent())
```

O mesmo padrão se aplica a `backend_dev_agent.py` (name = `"backend"`) e aos demais.

---

### 3. `backend/ws/orchestrator.py` — adicionar delegação ao AgentRegistry

Localizar o bloco de chamada ao LLM (após o comentário `# 5. Chamar LLM e transmitir chunks via WebSocket`) e substituir pelo padrão abaixo.

**Antes** (trecho atual):
```python
# 5. Chamar LLM e transmitir chunks via WebSocket
full_response = ""
try:
    async for chunk in llm_manager.stream_generate(
        prompt=user_message,
        expert=expert,
        user_context=combined_context,
        llm_override=user_llm_override,
    ):
        if isinstance(chunk, str):
            full_response += chunk
            await websocket.send_json({
                "type": "chunk",
                "content": chunk
            })
except Exception as e:
    ...
```

**Depois**:
```python
# 5. Chamar LLM — via AgentRegistry se disponível, senão direto
from backend.agents.base import agent_registry  # noqa: PLC0415

full_response = ""
agent = agent_registry.get(expert.get("id", ""))

try:
    if agent:
        # Opção A: agente gerencia seu próprio system_prompt e chama o LLM
        async for chunk in agent.stream_execute(
            intent=user_message,
            context={
                "user_context": combined_context,
                "llm_override": user_llm_override,
            },
        ):
            full_response += chunk
            await websocket.send_json({"type": "chunk", "content": chunk})
    else:
        # Fallback: comportamento existente (agentes legados, experts sem registry)
        async for chunk in llm_manager.stream_generate(
            prompt=user_message,
            expert=expert,
            user_context=combined_context,
            llm_override=user_llm_override,
        ):
            if isinstance(chunk, str):
                full_response += chunk
                await websocket.send_json({"type": "chunk", "content": chunk})
except Exception as e:
    logger.error(f"Erro na geração: {str(e)}", exc_info=True)
    await websocket.send_json({
        "type": "error",
        "content": f"Erro interno: {str(e)}"
    })
    return
```

**Por que este design:**
- O import de `agent_registry` é local para evitar circular import (o orchestrator já importa de `backend.main_auth` de forma local)
- O fallback preserva 100% do comportamento existente para agentes legados (CTO, Security, ReviewLoop) que ainda não foram migrados para BaseAgent
- Nenhuma mudança no protocolo WebSocket — o cliente continua recebendo `{"type": "chunk", "content": "..."}` idêntico

---

## Testes a adicionar

### `backend/tests/test_agent_llm.py` — novo arquivo

```python
"""
Testes de integração dos agentes com LLM.
Usa mock do llm_manager para não fazer chamadas reais de rede.
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from backend.agents.base import BaseAgent, AgentResult, AgentRegistry


# ── Fixtures ────────────────────────────────────────────────────────────────

async def fake_stream(*args, **kwargs):
    """Simula llm_manager.stream_generate retornando chunks."""
    yield {"provider": "mock", "model": "mock-model", "tokens": None}  # metadata dict
    yield "Resposta "
    yield "do agente."


class ConcreteAgent(BaseAgent):
    name = "test_agent"
    description = "Agente de teste"
    system_prompt = "Você é um agente de teste."
    skills = []


# ── Testes do BaseAgent ──────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_base_agent_stream_execute_filters_metadata():
    """stream_execute deve filtrar dicts de metadados e só emitir strings."""
    agent = ConcreteAgent()
    with patch("backend.llm_manager_simple.llm_manager") as mock_llm:
        mock_llm.stream_generate = fake_stream
        chunks = []
        async for chunk in agent.stream_execute("teste", {}):
            chunks.append(chunk)
    assert all(isinstance(c, str) for c in chunks)
    assert "".join(chunks) == "Resposta do agente."


@pytest.mark.asyncio
async def test_base_agent_execute_returns_agent_result():
    """execute() deve retornar AgentResult com status success e response."""
    agent = ConcreteAgent()
    with patch("backend.llm_manager_simple.llm_manager") as mock_llm:
        mock_llm.stream_generate = fake_stream
        result = await agent.execute("teste", {})
    assert result.status == "success"
    assert result.data["response"] == "Resposta do agente."
    assert result.data["agent"] == "test_agent"


@pytest.mark.asyncio
async def test_agent_registry_execute_on_agent_is_awaited():
    """execute_on_agent deve await o execute() do agente."""
    registry = AgentRegistry()
    agent = ConcreteAgent()
    registry.register(agent)
    with patch("backend.llm_manager_simple.llm_manager") as mock_llm:
        mock_llm.stream_generate = fake_stream
        result = await registry.execute_on_agent("test_agent", "teste", {})
    assert result.status == "success"


@pytest.mark.asyncio
async def test_agent_registry_returns_error_for_unknown_agent():
    registry = AgentRegistry()
    result = await registry.execute_on_agent("nao_existe", "teste")
    assert result.status == "error"
    assert "not found" in result.error


# ── Testes dos agentes concretos ─────────────────────────────────────────────

@pytest.mark.asyncio
@pytest.mark.parametrize("agent_module,agent_name", [
    ("backend.agents.frontend_dev_agent", "frontend"),
    ("backend.agents.backend_dev_agent", "backend"),
    ("backend.agents.devops_agent", "devops"),
    ("backend.agents.po_agent", "po"),
    ("backend.agents.pmo_agent", "pmo"),
    ("backend.agents.documentation_agent", "documentation"),
])
async def test_concrete_agent_name_matches_expected(agent_module, agent_name):
    """Cada agente deve ter o name correto para que o MoE router o encontre."""
    import importlib
    mod = importlib.import_module(agent_module)
    # Encontrar a classe do agente no módulo
    agent_class = None
    for attr in dir(mod):
        obj = getattr(mod, attr)
        if isinstance(obj, type) and issubclass(obj, BaseAgent) and obj is not BaseAgent:
            agent_class = obj
            break
    assert agent_class is not None, f"Nenhuma subclasse de BaseAgent em {agent_module}"
    assert agent_class.name == agent_name, (
        f"Esperado name='{agent_name}', encontrado '{agent_class.name}'"
    )


@pytest.mark.asyncio
async def test_concrete_agent_execute_calls_llm():
    """Agentes concretos devem delegar a chamada LLM via BaseAgent."""
    from backend.agents.backend_dev_agent import BackendDevAgent
    agent = BackendDevAgent()
    with patch("backend.llm_manager_simple.llm_manager") as mock_llm:
        mock_llm.stream_generate = fake_stream
        result = await agent.execute("crie uma rota FastAPI", {})
    assert result.status == "success"
    assert len(result.data["response"]) > 0
```

---

## Critérios de Aceite

1. `pytest backend/tests/test_agent_llm.py` — 100% passando
2. `pytest backend/tests/` — suite completa sem regressões (95 testes existentes continuam verdes)
3. Chat via WebSocket com mensagem "crie um componente React" deve rotear para `FrontendDevAgent` e retornar resposta gerada pelo LLM remoto
4. Chat via WebSocket com mensagem "configure um pipeline CI/CD" deve rotear para `DevopsAgent`
5. Mensagem que roteia para `cto` (agente legado, não no registry) deve continuar funcionando via fallback

---

## O que este sprint NÃO faz

- Não implementa streaming de chunks dentro de `execute()` para WebSocket com status de progresso por agente
- Não migra agentes legados (CTO, Security, ReviewLoop) para BaseAgent — isso é P6
- Não implementa o QA Agent — isso é P2
- Não integra AIGatewayClient como provider dos agentes — isso é P3
- Não implementa o orquestrador v3 (Plan → Build → Test → Deploy) — isso é P8

---

## Dependências e Riscos

**Risco 1 — Circular import**  
O import de `agent_registry` no orchestrator pode criar circular import se não for feito localmente. O spec usa import local dentro da função `_handle_chat_message`. Verificar se o `backend/__init__.py` faz imports que possam criar ciclo.

**Risco 2 — Nome dos agentes concretos**  
O spec presume os nomes de classe e `name` dos 6 agentes. Se o Opencode criou nomes diferentes, ajustar a tabela de mapeamento antes de implementar.

**Risco 3 — `llm_manager` timeout em testes**  
O `stream_generate` tem timeout de 6s (`HTTP_TIMEOUT_S`). Os testes parametrizados usam mock — sem risco de rede. Testes E2E reais (P7 do QA) dependem de provider configurado.
