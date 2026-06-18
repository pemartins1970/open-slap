from typing import Dict, Any, List
from .base import BaseAgent, agent_registry

CFO_SYSTEM_PROMPT = """
Você é o CFO do Open Slap!. Sua função é orquestrar decisões financeiras: análise de custos, orçamento, ROI,
planejamento financeiro e sustentabilidade econômica do projeto.

Competências principais:
- Analisar custos de infraestrutura (cloud, LLMs, terceiros)
- Estimar orçamento para features, sprints e releases
- Calcular ROI e payback de iniciativas técnicas
- Identificar desperdícios e oportunidades de otimização de custos
- Modelar cenários financeiros (melhor caso, esperado, pior caso)
- Avaliar trade-offs entre custo e qualidade técnica
- Gerar relatórios financeiros e dashboards de acompanhamento

Regras de resposta:
- Responda sempre no mesmo idioma utilizado pelo usuário na mensagem recebida.
- Seja direto: números primeiro, explicação depois.
- Sempre justifique premissas usadas em estimativas.
- Quando sugerir corte de custo, avalie o impacto técnico também.
- Se faltarem dados para uma análise, peça exatamente o que precisa.
"""

CFO_SKILLS = [
    {
        "name": "estimate_cost",
        "description": "Estima custo de uma feature, sprint ou iniciativa",
        "input_schema": {
            "initiative": "string (descrição da iniciativa)",
            "effort_hours": "number (horas estimadas de desenvolvimento)",
            "resources": "array (recursos envolvidos: dev, infra, LLM calls etc.)",
            "timeframe": "string (prazo estimado)"
        },
        "output_schema": {
            "total_cost": "number (custo total estimado)",
            "breakdown": "object (detalhamento por recurso)",
            "assumptions": "array (premissas consideradas)",
            "confidence": "string (baixa/média/alta)"
        }
    },
    {
        "name": "calculate_roi",
        "description": "Calcula ROI e payback de uma iniciativa",
        "input_schema": {
            "investment": "number (investimento total)",
            "expected_benefits": "object (benefícios esperados por período)",
            "time_horizon": "string (horizonte de análise em meses)"
        },
        "output_schema": {
            "roi_percent": "number (ROI percentual)",
            "payback_months": "number (meses para payback)",
            "npv": "number (valor presente líquido)",
            "scenarios": "object (melhor, esperado, pior caso)"
        }
    },
    {
        "name": "cost_optimization_review",
        "description": "Revisa gastos atuais e sugere otimizações",
        "input_schema": {
            "current_costs": "object (gastos por categoria)",
            "usage_metrics": "object (métricas de uso: LLM tokens, cloud resources etc.)",
            "constraints": "object (restrições: orçamento máximo, SLAs etc.)"
        },
        "output_schema": {
            "savings_opportunities": "array (oportunidades com impacto estimado)",
            "recommended_actions": "array (ações prioritárias)",
            "projected_savings": "number (economia mensal projetada)"
        }
    },
]


class CFOAgent(BaseAgent):
    name = "cfo"
    description = "CFO — orçamento, custos, ROI e planejamento financeiro"
    system_prompt = CFO_SYSTEM_PROMPT
    skills = CFO_SKILLS


agent_registry.register(CFOAgent())
