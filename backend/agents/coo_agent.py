from typing import Dict, Any, List
from .base import BaseAgent, agent_registry

COO_SYSTEM_PROMPT = """
Você é o COO do Open Slap!. Sua função é orquestrar operações: processos, fluxos de trabalho,
eficiência operacional, integração entre áreas e execução do dia a dia.

Competências principais:
- Mapear e otimizar fluxos de trabalho e processos
- Coordenar integração entre equipes (dev, QA, devops, produto)
- Identificar gargalos e propor melhorias operacionais
- Definir métricas de desempenho operacional (KPIs)
- Gerenciar capacidade e alocação de recursos
- Automatizar processos repetitivos
- Garantir que políticas e procedimentos sejam seguidos

Regras de resposta:
- Responda sempre no mesmo idioma utilizado pelo usuário na mensagem recebida.
- Seja pragmático: foque no que desbloqueia a operação.
- Quando identificar um gargalo, proponha solução com passo a passo.
- Use dados para embasar recomendações operacionais.
- Se faltar contexto, peça antes de assumir.
"""

COO_SKILLS = [
    {
        "name": "map_workflow",
        "description": "Mapeia fluxo de trabalho atual e propõe otimizações",
        "input_schema": {
            "process_description": "string (descrição do processo atual)",
            "pain_points": "array (gargalos ou problemas conhecidos)",
            "teams_involved": "array (equipes envolvidas no fluxo)"
        },
        "output_schema": {
            "current_flow": "object (mapeamento do fluxo atual)",
            "bottlenecks": "array (gargalos identificados)",
            "optimized_flow": "object (fluxo otimizado proposto)",
            "expected_gains": "object (ganhos esperados: tempo, custo, qualidade)"
        }
    },
    {
        "name": "operational_health_check",
        "description": "Audita saúde operacional do projeto ou equipe",
        "input_schema": {
            "area": "string (área a ser auditada: dev, ops, QA, produto)",
            "metrics": "object (métricas atuais disponíveis)",
            "recent_incidents": "array (incidentes ou desvios recentes)"
        },
        "output_schema": {
            "status": "string (verde/amarelo/vermelho)",
            "issues": "array (problemas encontrados)",
            "recommendations": "array (ações recomendadas com prioridade)",
            "kpi_suggestions": "array (KPIs sugeridos para monitoramento)"
        }
    },
]


class COOAgent(BaseAgent):
    name = "coo"
    description = "COO — operações, processos, fluxos e eficiência"
    system_prompt = COO_SYSTEM_PROMPT
    skills = COO_SKILLS


agent_registry.register(COOAgent())
