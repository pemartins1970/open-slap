# MoE Router - Mixture of Experts Router

## Visão Geral

Sistema completo de roteamento de especialistas (Mixture of Experts) para seleção inteligente de agentes especializados baseado no tipo de tarefa e capacidades.

## Características

### 🚀 Funcionalidades Principais
- **Expert Registry** - Registro e gerenciamento de especialistas
- **Task-based Selection** - Seleção automática baseada no tipo de tarefa
- **Capability Matching** - Análise de compatibilidade de habilidades
- **Performance Scoring** - Sistema de pontuação baseado em métricas
- **Load Balancing** - Balanceamento de carga entre especialistas
- **Result Aggregation** - Agregação de resultados múltiplos

### 🏗️ Arquitetura
```
MoE Router
├── Expert Registry    # Registro de especialistas
├── Expert Selector    # Lógica de seleção
├── Task Analyzer     # Análise de tarefas
├── Score Calculator  # Cálculo de pontuação
└── Result Aggregator # Agregação de resultados
```

## Especialistas Disponíveis

### 1. System Architect
- **ID:** architect
- **Especialidade:** Design de arquitetura e decisões estratégicas
- **Tipos de Tarefa:** design, planning, analysis
- **Performance:** 90% accuracy, 80% speed, 95% reliability
- **Capacidade:** 3 tarefas simultâneas

### 2. Backend Developer
- **ID:** backend_dev
- **Especialidade:** APIs, bancos de dados, lógica server-side
- **Tipos de Tarefa:** coding, deployment, debugging
- **Performance:** 85% accuracy, 90% speed, 88% reliability
- **Capacidade:** 5 tarefas simultâneas

### 3. Frontend Developer
- **ID:** frontend_dev
- **Especialidade:** Interfaces de usuário e aplicações client-side
- **Tipos de Tarefa:** coding, design, optimization
- **Performance:** 82% accuracy, 85% speed, 86% reliability
- **Capacidade:** 4 tarefas simultâneas

### 4. Security Specialist
- **ID:** security_expert
- **Especialidade:** Segurança de sistemas e auditorias
- **Tipos de Tarefa:** security, analysis, testing
- **Performance:** 92% accuracy, 70% speed, 94% reliability
- **Capacidade:** 2 tarefas simultâneas

## Tipos de Tarefa

```python
class TaskType(Enum):
    CODING = "coding"           # Desenvolvimento de código
    DESIGN = "design"           # Design de sistemas
    ANALYSIS = "analysis"         # Análise técnica
    DEBUGGING = "debugging"       # Debug e correção
    DOCUMENTATION = "documentation" # Documentação
    PLANNING = "planning"       # Planejamento
    TESTING = "testing"          # Testes
    DEPLOYMENT = "deployment"    # Deploy
    SECURITY = "security"        # Segurança
    OPTIMIZATION = "optimization" # Otimização
```

## Algoritmo de Seleção

### Fatores de Pontuação

1. **Task Type Match (50%)**
   - Especialista especializado no tipo de tarefa
   - Bonus: +0.5 pontos

2. **Capability Matching (30%)**
   - Similaridade entre requisitos e capacidades
   - Algoritmo Jaccard similarity

3. **Performance Metrics (20%)**
   - Média das métricas de performance
   - Accuracy, speed, reliability

4. **Availability (10%)**
   - Disponibilidade atual do especialista
   - Baseado em carga atual

### Fórmula de Pontuação
```
Score = (TaskMatch × 0.5) + (CapabilityMatch × 0.3) + 
        (Performance × 0.2) + (Availability × 0.1)
```

## Métodos de Agregação

### 1. Best Confidence
Seleciona resultado do especialista com maior performance geral.

### 2. Weighted Average
Média ponderada baseada nas métricas de performance dos especialistas.

### 3. Majority Vote
Votação por maioria entre especialistas (para resultados estruturados).

### 4. Consensus
Consenso baseado no especialista mais especializado.

## Uso Básico

### Python
```python
from src.core.moe_router import MoERouter, Task, TaskType

async def main():
    # Criar router
    router = MoERouter()
    
    # Criar tarefa
    task = Task(
        id="task-1",
        type=TaskType.CODING,
        description="Create REST API for user management",
        requirements=["python", "fastapi", "database"],
        priority=8,
        estimated_duration=60,
        context={"project": "user_management"},
        created_at=datetime.now()
    )
    
    # Rotear tarefa
    result = await router.route_task(task)
    
    print(f"Expert: {result.expert_contributions[0][0]}")
    print(f"Confidence: {result.confidence_score}")
    print(f"Processing time: {result.processing_time}")

asyncio.run(main())
```

### Teste Simplificado
```python
from test_moe_simple import SimpleMoERouter

router = SimpleMoERouter()
result = await router.route_task(task)
```

## Estruturas de Dados

### Expert
```python
@dataclass
class Expert:
    id: str
    name: str
    description: str
    capabilities: List[str]
    task_types: List[TaskType]
    status: ExpertStatus
    performance_metrics: Dict[str, float]
    current_load: int
    max_concurrent_tasks: int
    last_active: datetime
    specialization_score: float
```

### Task
```python
@dataclass
class Task:
    id: str
    type: TaskType
    description: str
    requirements: List[str]
    priority: int  # 1-10
    estimated_duration: int  # minutos
    context: Dict[str, Any]
    created_at: datetime
```

### Resultado Agregado
```python
@dataclass
class AggregatedResult:
    primary_result: Dict[str, Any]
    expert_contributions: List[Tuple[str, Dict[str, Any]]]
    confidence_score: float
    aggregation_method: str
    processing_time: float
```

## Performance

### Métricas
- **Selection Time:** < 50ms para seleção de especialista
- **Routing Accuracy:** > 85% de acerto na seleção
- **Load Balancing:** Distribuição uniforme de tarefas
- **Confidence Score:** Média > 0.7

### Otimizações
- **Caching** de pontuações de especialistas
- **Pre-computation** de similaridades
- **Async processing** para múltiplas tarefas
- **Load prediction** para balanceamento

## Testes

### Unit Tests
```bash
python test_moe_simple.py
```

### Integration Tests
```bash
python test_moe.py  # Com sklearn
```

### Testes de Performance
```python
# Teste com múltiplas tarefas paralelas
tasks = [create_task(i) for i in range(10)]
results = await asyncio.gather(*[router.route_task(t) for t in tasks])
```

## Configuração

### Environment Variables
```bash
# MoE Router settings
MOE_MAX_EXPERTS=10
MOE_DEFAULT_AGGREGATION=best_confidence
MOE_LOAD_BALANCING=true
MOE_CONFIDENCE_THRESHOLD=0.7
```

### Custom Experts
```python
# Adicionar especialista customizado
custom_expert = Expert(
    id="custom_expert",
    name="Custom Specialist",
    description="Specialist in custom domain",
    capabilities=["custom_skill1", "custom_skill2"],
    task_types=[TaskType.CODING],
    status=ExpertStatus.IDLE,
    performance_metrics={"accuracy": 0.9, "speed": 0.85, "reliability": 0.88},
    current_load=0,
    max_concurrent_tasks=3,
    last_active=datetime.now(),
    specialization_score=0.8
)

router.registry.register_expert(custom_expert)
```

## Monitoramento

### Status dos Especialistas
```python
status = router.get_expert_status()
print(f"Total experts: {len(status)}")
print(f"Available: {len([e for e in status.values() if e['status'] == 'idle'])}")
```

### Tarefas Ativas
```python
active = router.get_active_tasks()
print(f"Active tasks: {len(active)}")
for task_id, info in active.items():
    print(f"Task {task_id}: {info['assigned_expert']}")
```

## Integração com MCP Server

### MCP Methods
```json
{
  "method": "moe/route_task",
  "params": {
    "task_id": "task-1",
    "task_type": "coding",
    "description": "Create API",
    "requirements": ["python", "fastapi"],
    "priority": 8,
    "estimated_duration": 60,
    "use_multiple_experts": false
  }
}
```

### Expert Status
```json
{
  "method": "moe/expert_status",
  "params": {}
}
```

## Troubleshooting

### Common Issues

**Nenhum Especialista Disponível**
```python
# Verificar status dos especialistas
status = router.get_expert_status()
busy_experts = [e for e in status.values() if e['status'] == 'busy']
print(f"Busy experts: {len(busy_experts)}")
```

**Baixa Confiança na Seleção**
```python
# Ajustar pesos de pontuação
# Aumentar peso de task type match para 60%
# Adicionar mais keywords às capacidades
```

**Load Imbalance**
```python
# Verificar distribuição de carga
loads = [e['current_load'] / e['max_concurrent_tasks'] for e in status.values()]
print(f"Load variance: {np.var(loads)}")
```

## Próximos Passos

1. **Machine Learning Integration**
   - Implementar TF-IDF vectorização
   - Adicionar aprendizado de seleção
   - Otimizar pesos dinamicamente

2. **Advanced Aggregation**
   - Implementar agregação baseada em conteúdo
   - Adicionar sistema de votação ponderado
   - Detecção de conflitos

3. **Expert Learning**
   - Coletar feedback de performance
   - Ajustar métricas automaticamente
   - Aprender preferências de domínio

4. **Multi-Modal Support**
   - Suporte a tarefas de diferentes tipos
   - Análise de imagens e documentos
   - Processamento de áudio

## Contribuição

1. Fork projeto
2. Criar branch para feature
3. Implementar especialista customizado
4. Adicionar testes
5. Submit PR

## Licença

Projeto privado - uso local autorizado
