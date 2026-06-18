# AI Gateway Integration Guide

## Overview

Este documento descreve como integrar o Open Slap! v3.0 com o AI Gateway construído em `C:\AI-Gateway`, permitindo roteamento inteligente de requisições para múltiplos providers (NVidia, OpenRouter, Gemini, Groq) com rotação automática de chaves.

## Arquitetura de Integração

```
┌─────────────────────────────────────────────────────────────┐
│                    Open Slap! v3.0                            │
│  ┌───────────────────────────────────────────────────────┐  │
│  │              Agent Orchestrator                        │  │
│  │  - Agent Router                                        │  │
│  │  - Workflow Engine                                     │  │
│  │  - State Machine                                       │  │
│  └───────────────────────────────────────────────────────┘  │
│                            │                                 │
│                            ▼                                 │
│  ┌───────────────────────────────────────────────────────┐  │
│  │           AI Gateway Client Layer                      │  │
│  │  - Provider Selection                                  │  │
│  │  - Model Routing                                       │  │
│  │  - Fallback Handling                                   │  │
│  └───────────────────────────────────────────────────────┘  │
│                            │                                 │
│                            ▼                                 │
└────────────────────────────┼─────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                    AI Gateway (localhost:8000)              │
│  - NVidia NIM API                                           │
│  - OpenRouter API                                           │
│  - Google Gemini API                                        │
│  - Groq API                                                 │
│  - Key Rotation System                                      │
└─────────────────────────────────────────────────────────────┘
```

## Configuração

### 1. Configurar Variáveis de Ambiente

No arquivo `.env` do Open Slap! v3.0:

```env
# AI Gateway Configuration
AI_GATEWAY_ENABLED=true
AI_GATEWAY_URL=http://localhost:8000/v1
AI_GATEWAY_API_KEY=gateway-key

# Fallback para LLM direto (se gateway falhar)
GEMINI_API_KEYS=your_gemini_key
GROQ_API_KEYS=your_groq_key
OPENAI_API_KEY=your_openai_key
```

### 2. Instalar Dependências

No `backend/requirements.txt`, adicionar:

```txt
httpx==0.25.2
pydantic==2.5.0
```

### 3. Criar Cliente do AI Gateway

```python
# backend/integrations/ai_gateway_client.py

import httpx
from typing import Dict, Any, List, Optional, AsyncGenerator
import logging
from backend.config import settings

logger = logging.getLogger(__name__)

class AIGatewayClient:
    """Cliente para comunicação com AI Gateway"""
    
    def __init__(self):
        self.base_url = settings.AI_GATEWAY_URL
        self.api_key = settings.AI_GATEWAY_API_KEY
        self.enabled = settings.AI_GATEWAY_ENABLED
        self.timeout = 120.0
        
    async def chat_completion(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False
    ) -> Dict[str, Any]:
        """Envia requisição de chat completion para o AI Gateway"""
        
        if not self.enabled:
            logger.warning("AI Gateway desabilitado, usando fallback")
            raise AIGatewayError("AI Gateway desabilitado")
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "stream": stream
        }
        
        if max_tokens:
            payload["max_tokens"] = max_tokens
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    json=payload,
                    headers=headers
                )
                response.raise_for_status()
                return response.json()
                
        except httpx.HTTPStatusError as e:
            logger.error(f"Erro HTTP no AI Gateway: {e.response.status_code}")
            raise AIGatewayError(f"Erro no AI Gateway: {e.response.status_code}")
        except httpx.RequestError as e:
            logger.error(f"Erro de conexão com AI Gateway: {e}")
            raise AIGatewayError("Falha de conexão com AI Gateway")
    
    async def stream_completion(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> AsyncGenerator[str, None]:
        """Streaming de chat completion do AI Gateway"""
        
        if not self.enabled:
            logger.warning("AI Gateway desabilitado, usando fallback")
            raise AIGatewayError("AI Gateway desabilitado")
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "stream": True
        }
        
        if max_tokens:
            payload["max_tokens"] = max_tokens
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                async with client.stream(
                    "POST",
                    f"{self.base_url}/chat/completions",
                    json=payload,
                    headers=headers
                ) as response:
                    response.raise_for_status()
                    async for chunk in response.aiter_bytes():
                        yield chunk.decode('utf-8')
                        
        except Exception as e:
            logger.error(f"Erro no streaming do AI Gateway: {e}")
            raise AIGatewayError(f"Erro no streaming: {e}")
    
    async def health_check(self) -> bool:
        """Verifica se o AI Gateway está saudável"""
        
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url.replace('/v1', '')}/health")
                return response.status_code == 200
        except Exception as e:
            logger.error(f"Health check falhou: {e}")
            return False


class AIGatewayError(Exception):
    """Exceção específica para erros do AI Gateway"""
    pass


# Instância global
ai_gateway = AIGatewayClient()
```

## Mapeamento de Agentes para Modelos

### Configuração de Routing

```python
# backend/llm/agent_model_mapping.py

AGENT_MODEL_MAPPING = {
    # CTO - Para arquitetura e decisões técnicas complexas
    "cto": {
        "primary": "openai/gpt-4",
        "fallback": ["anthropic/claude-3-opus", "openai/gpt-4-turbo"],
        "temperature": 0.3,
        "max_tokens": 4096
    },
    
    # PO - Para requisitos e user stories
    "po": {
        "primary": "anthropic/claude-3-opus",
        "fallback": ["openai/gpt-4", "openai/gpt-4-turbo"],
        "temperature": 0.7,
        "max_tokens": 4096
    },
    
    # PMO - Para planejamento e documentação PMP
    "pmo": {
        "primary": "openai/gpt-4",
        "fallback": ["anthropic/claude-3-sonnet", "openai/gpt-4-turbo"],
        "temperature": 0.5,
        "max_tokens": 4096
    },
    
    # Frontend Developer - Para código React/Vue
    "frontend_dev": {
        "primary": "openai/gpt-4",
        "fallback": ["anthropic/claude-3-sonnet", "openai/gpt-4-turbo"],
        "temperature": 0.2,
        "max_tokens": 8192
    },
    
    # Backend Developer - Para código Python/Go
    "backend_dev": {
        "primary": "openai/gpt-4",
        "fallback": ["anthropic/claude-3-sonnet", "openai/gpt-4-turbo"],
        "temperature": 0.2,
        "max_tokens": 8192
    },
    
    # DevOps - Para scripts de infra e CI/CD
    "devops": {
        "primary": "anthropic/claude-3-sonnet",
        "fallback": ["openai/gpt-4", "openai/gpt-4-turbo"],
        "temperature": 0.3,
        "max_tokens": 4096
    },
    
    # QA - Para testes e validação
    "qa": {
        "primary": "openai/gpt-4-turbo",
        "fallback": ["openai/gpt-4", "anthropic/claude-3-sonnet"],
        "temperature": 0.4,
        "max_tokens": 4096
    },
    
    # Security - Para análise de segurança
    "security": {
        "primary": "anthropic/claude-3-opus",
        "fallback": ["openai/gpt-4", "openai/gpt-4-turbo"],
        "temperature": 0.2,
        "max_tokens": 4096
    },
    
    # Documentation - Para geração de docs
    "documentation": {
        "primary": "openai/gpt-4",
        "fallback": ["anthropic/claude-3-sonnet", "openai/gpt-4-turbo"],
        "temperature": 0.5,
        "max_tokens": 8192
    }
}

class AgentModelRouter:
    """Roteia chamadas de agentes para modelos apropriados via AI Gateway"""
    
    def __init__(self, gateway_client: AIGatewayClient):
        self.gateway = gateway_client
    
    async def agent_call(
        self,
        agent_type: str,
        prompt: str,
        context: Optional[Dict[str, Any]] = None,
        stream: bool = False
    ) -> str:
        """Executa chamada do agente via AI Gateway com fallback"""
        
        mapping = AGENT_MODEL_MAPPING.get(agent_type, AGENT_MODEL_MAPPING["cto"])
        
        # Prepara mensagens
        system_prompt = self._get_system_prompt(agent_type)
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]
        
        # Adiciona contexto se disponível
        if context:
            context_msg = self._format_context(context)
            messages.insert(1, {"role": "system", "content": context_msg})
        
        # Tenta modelo primário
        try:
            if stream:
                response = ""
                async for chunk in self.gateway.stream_completion(
                    model=mapping["primary"],
                    messages=messages,
                    temperature=mapping["temperature"],
                    max_tokens=mapping["max_tokens"]
                ):
                    response += chunk
                return response
            else:
                response = await self.gateway.chat_completion(
                    model=mapping["primary"],
                    messages=messages,
                    temperature=mapping["temperature"],
                    max_tokens=mapping["max_tokens"]
                )
                return response["choices"][0]["message"]["content"]
                
        except AIGatewayError as e:
            logger.warning(f"Falha no modelo primário {mapping['primary']}: {e}")
            
            # Tenta fallbacks
            for fallback_model in mapping.get("fallback", []):
                try:
                    logger.info(f"Tentando fallback: {fallback_model}")
                    response = await self.gateway.chat_completion(
                        model=fallback_model,
                        messages=messages,
                        temperature=mapping["temperature"],
                        max_tokens=mapping["max_tokens"]
                    )
                    return response["choices"][0]["message"]["content"]
                    
                except AIGatewayError as e:
                    logger.warning(f"Fallback {fallback_model} falhou: {e}")
                    continue
            
            # Se todos falharem, usa LLM direto
            logger.error("Todos os modelos do AI Gateway falharam, usando LLM direto")
            return await self._fallback_to_direct_llm(
                agent_type,
                messages,
                mapping["temperature"],
                mapping["max_tokens"]
            )
    
    def _get_system_prompt(self, agent_type: str) -> str:
        """Retorna prompt de sistema específico para cada agente"""
        
        prompts = {
            "cto": """You are a Chief Technology Officer with 15+ years of experience in software architecture and engineering. You excel at:
- Designing scalable, maintainable architectures
- Making technology stack decisions
- Conducting high-level code reviews
- Identifying technical risks and mitigation strategies
- Communicating complex technical concepts clearly

Always provide detailed, well-reasoned responses with specific recommendations.""",
            
            "po": """You are a Product Owner focused on delivering user value and business outcomes. You excel at:
- Gathering and clarifying requirements
- Writing clear, actionable User Stories
- Prioritizing features based on value
- Understanding user needs and pain points
- Translating business requirements into technical specifications

Always focus on user value and provide specific, actionable requirements.""",
            
            "pmo": """You are a Project Management Professional (PMP) certified PMO with expertise in both traditional project management and agile methodologies. You excel at:
- Creating detailed project plans and WBS
- Managing timelines and milestones
- Identifying and mitigating risks
- Coordinating between stakeholders
- Ensuring projects stay on track and within budget

Always provide structured, detailed plans with clear milestones and deliverables.""",
            
            "frontend_dev": """You are a Senior Frontend Developer with expertise in modern web technologies. You excel at:
- Building responsive, accessible UI components
- Writing clean, maintainable React/Vue code
- Implementing state management solutions
- Optimizing performance and user experience
- Following best practices and design patterns

Always provide production-ready code with proper error handling and comments.""",
            
            "backend_dev": """You are a Senior Backend Developer with expertise in building scalable APIs and services. You excel at:
- Designing RESTful APIs and microservices
- Writing efficient database queries
- Implementing business logic
- Ensuring security and data integrity
- Following best practices for scalability

Always provide production-ready code with proper error handling, validation, and documentation.""",
            
            "devops": """You are a DevOps Engineer with expertise in CI/CD, infrastructure, and automation. You excel at:
- Configuring CI/CD pipelines
- Managing cloud infrastructure
- Automating deployments
- Implementing monitoring and alerting
- Writing infrastructure as code

Always provide ready-to-use scripts and configurations with clear instructions.""",
            
            "qa": """You are a Quality Assurance Engineer with expertise in automated testing. You excel at:
- Creating comprehensive test plans
- Writing unit, integration, and E2E tests
- Identifying edge cases and potential bugs
- Performance testing and optimization
- Ensuring software quality and reliability

Always provide detailed test cases with clear pass/fail criteria.""",
            
            "security": """You are a Security Engineer with expertise in application security and OWASP standards. You excel at:
- Identifying security vulnerabilities
- Conducting security code reviews
- Implementing security best practices
- Penetration testing and vulnerability assessment
- Ensuring compliance with security standards

Always provide specific security recommendations with clear severity ratings.""",
            
            "documentation": """You are a Technical Writer with expertise in creating clear, comprehensive documentation. You excel at:
- Writing API documentation
- Creating user guides and tutorials
- Documenting architecture and design decisions
- Maintaining CHANGELOG and release notes
- Creating installation and deployment guides

Always provide well-structured, easy-to-understand documentation with examples."""
        }
        
        return prompts.get(agent_type, "You are a helpful AI assistant.")
    
    def _format_context(self, context: Dict[str, Any]) -> str:
        """Formata contexto para inclusão nas mensagens"""
        
        context_parts = []
        
        if "project" in context:
            context_parts.append(f"Project: {context['project']}")
        
        if "stage" in context:
            context_parts.append(f"Current Stage: {context['stage']}")
        
        if "decisions" in context:
            context_parts.append(f"Previous Decisions: {context['decisions']}")
        
        if "constraints" in context:
            context_parts.append(f"Constraints: {context['constraints']}")
        
        return "\n".join(context_parts)
    
    async def _fallback_to_direct_llm(
        self,
        agent_type: str,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: int
    ) -> str:
        """Fallback para LLM direto quando AI Gateway falha"""
        
        # Importa o gerenciador de LLM existente
        from backend.llm_manager import llm_manager
        
        logger.info("Usando fallback para LLM direto")
        
        # Usa o primeiro provider disponível
        response = await llm_manager.generate(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        return response
```

## Implementação nos Agentes

### Exemplo: CTO Agent com AI Gateway

```python
# backend/agents/cto_agent_v3.py

from typing import Dict, Any
from backend.integrations.ai_gateway_client import ai_gateway
from backend.llm.agent_model_mapping import AgentModelRouter
from backend.memory.project_memory import ProjectMemory
import logging

logger = logging.getLogger(__name__)

class CTOAgentV3:
    """CTO Agent integrado com AI Gateway"""
    
    def __init__(self, project_id: str):
        self.project_id = project_id
        self.memory = ProjectMemory(project_id)
        self.router = AgentModelRouter(ai_gateway)
    
    async def create_architecture_plan(
        self,
        requirements: str,
        constraints: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Cria plano de arquitetura via AI Gateway"""
        
        # Recupera contexto do projeto
        context = await self.memory.get_project_context()
        
        prompt = f"""
Based on the following requirements, create a detailed architecture plan:

Requirements:
{requirements}

Constraints:
{constraints}

Previous Decisions:
{context.get('decisions', 'None')}

Provide:
1. Recommended technology stack
2. System architecture diagram description
3. Component breakdown
4. Data flow description
5. Security considerations
6. Scalability strategy
"""
        
        try:
            response = await self.router.agent_call(
                agent_type="cto",
                prompt=prompt,
                context={
                    "project": self.project_id,
                    "stage": "planning",
                    "constraints": constraints
                }
            )
            
            # Armazena decisão
            await self.memory.store_decision(
                agent="cto",
                decision="Architecture plan created",
                rationale=response[:500]  # Primeiros 500 chars
            )
            
            return {
                "status": "success",
                "plan": response,
                "agent": "cto",
                "via_gateway": True
            }
            
        except Exception as e:
            logger.error(f"Erro ao criar plano via AI Gateway: {e}")
            return {
                "status": "error",
                "error": str(e),
                "agent": "cto",
                "via_gateway": False
            }
    
    async def review_code_change(
        self,
        code_diff: str,
        file_path: str
    ) -> Dict[str, Any]:
        """Revisa mudança de código via AI Gateway"""
        
        prompt = f"""
Review the following code change:

File: {file_path}

Diff:
{code_diff}

Provide:
1. Assessment of code quality
2. Potential bugs or issues
3. Security concerns
4. Performance implications
5. Suggestions for improvement
6. Approval/rejection recommendation
"""
        
        try:
            response = await self.router.agent_call(
                agent_type="cto",
                prompt=prompt,
                context={
                    "project": self.project_id,
                    "stage": "building"
                }
            )
            
            return {
                "status": "success",
                "review": response,
                "agent": "cto",
                "via_gateway": True
            }
            
        except Exception as e:
            logger.error(f"Erro ao revisar código via AI Gateway: {e}")
            return {
                "status": "error",
                "error": str(e),
                "agent": "cto",
                "via_gateway": False
            }
```

## Monitoramento e Observabilidade

### Métricas do AI Gateway

```python
# backend/monitoring/gateway_metrics.py

from prometheus_client import Counter, Histogram, Gauge
import time

# Métricas
gateway_requests_total = Counter(
    'ai_gateway_requests_total',
    'Total requests to AI Gateway',
    ['agent', 'model', 'status']
)

gateway_request_duration = Histogram(
    'ai_gateway_request_duration_seconds',
    'Request duration to AI Gateway',
    ['agent', 'model']
)

gateway_health = Gauge(
    'ai_gateway_health',
    'AI Gateway health status (1=healthy, 0=unhealthy)'
)

class GatewayMetrics:
    """Coleta métricas do AI Gateway"""
    
    @staticmethod
    async def record_request(
        agent: str,
        model: str,
        status: str,
        duration: float
    ):
        """Registra métricas de requisição"""
        
        gateway_requests_total.labels(
            agent=agent,
            model=model,
            status=status
        ).inc()
        
        gateway_request_duration.labels(
            agent=agent,
            model=model
        ).observe(duration)
    
    @staticmethod
    async def update_health_status(healthy: bool):
        """Atualiza status de saúde"""
        
        gateway_health.set(1 if healthy else 0)
    
    @staticmethod
    async def get_metrics_summary() -> Dict[str, Any]:
        """Retorna resumo das métricas"""
        
        return {
            "total_requests": gateway_requests_total._value.get(),
            "health_status": gateway_health._value.get(),
            "request_duration": gateway_request_duration._value.get()
        }
```

## Testes de Integração

### Teste de Conexão

```python
# backend/tests/test_ai_gateway_integration.py

import pytest
from backend.integrations.ai_gateway_client import ai_gateway, AIGatewayError

@pytest.mark.asyncio
async def test_gateway_health_check():
    """Testa health check do AI Gateway"""
    
    is_healthy = await ai_gateway.health_check()
    assert is_healthy is True

@pytest.mark.asyncio
async def test_gateway_chat_completion():
    """Testa chat completion básico"""
    
    response = await ai_gateway.chat_completion(
        model="openai/gpt-4",
        messages=[{"role": "user", "content": "Say 'test'"}],
        temperature=0.7
    )
    
    assert "choices" in response
    assert len(response["choices"]) > 0
    assert "message" in response["choices"][0]

@pytest.mark.asyncio
async def test_gateway_stream_completion():
    """Testa streaming completion"""
    
    chunks = []
    async for chunk in ai_gateway.stream_completion(
        model="openai/gpt-4",
        messages=[{"role": "user", "content": "Say 'test'"}],
        temperature=0.7
    ):
        chunks.append(chunk)
    
    assert len(chunks) > 0

@pytest.mark.asyncio
async def test_agent_router_with_gateway():
    """Testa roteamento de agente via AI Gateway"""
    
    from backend.llm.agent_model_mapping import AgentModelRouter
    
    router = AgentModelRouter(ai_gateway)
    
    response = await router.agent_call(
        agent_type="cto",
        prompt="What is a microservice?",
        stream=False
    )
    
    assert isinstance(response, str)
    assert len(response) > 0
```

## Troubleshooting

### Problemas Comuns

**1. AI Gateway não está respondendo**
```bash
# Verifique se o gateway está rodando
curl http://localhost:8000/health

# Deve retornar: {"status":"healthy"}
```

**2. Erro de conexão**
- Verifique se `AI_GATEWAY_URL` está correto no `.env`
- Verifique se o firewall não está bloqueando a porta 8000
- Verifique os logs do AI Gateway

**3. Chaves de API esgotadas**
- O AI Gateway deve rotacionar automaticamente
- Verifique se há chaves suficientes configuradas no `.env` do AI Gateway
- Monitore os logs de rotação de chaves

**4. Modelo não disponível**
- Verifique se o modelo está disponível no provider
- Tente usar um modelo diferente
- Verifique o mapeamento em `AGENT_MODEL_MAPPING`

### Logs de Debug

```python
# Adicione ao logger para debug detalhado

import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Isso vai mostrar detalhes de cada requisição ao AI Gateway
```

## Performance Considerations

### Otimizações

1. **Connection Pooling**: Reutilizar conexões HTTP
2. **Caching**: Cache respostas comuns
3. **Batching**: Agrupar múltiplas requisições quando possível
4. **Timeouts**: Configurar timeouts apropriados
5. **Retry Logic**: Implementar retry com backoff

### Exemplo de Configuração Otimizada

```python
# backend/integrations/ai_gateway_client_optimized.py

import httpx
from typing import Dict, Any, List, Optional

class OptimizedAIGatewayClient:
    """Cliente otimizado para AI Gateway"""
    
    def __init__(self):
        self.base_url = settings.AI_GATEWAY_URL
        # Connection pool com limites
        self.client = httpx.AsyncClient(
            timeout=120.0,
            limits=httpx.Limits(
                max_connections=100,
                max_keepalive_connections=20
            )
        )
    
    async def batch_chat_completion(
        self,
        requests: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Executa múltiplas requisições em paralelo"""
        
        tasks = [
            self.chat_completion(**req)
            for req in requests
        ]
        
        return await asyncio.gather(*tasks)
```

## Conclusão

Esta integração permite que o Open Slap! v3.0 utilize o AI Gateway para roteamento inteligente de requisições, com rotação automática de chaves e fallback para múltiplos providers, garantindo disponibilidade e performance otimizada para o sistema de agentes completo.
