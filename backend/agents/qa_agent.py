from typing import Dict, Any, List
from .base import BaseAgent, agent_registry

QA_SYSTEM_PROMPT = """
Você é o QA Lead do Open Slap!. Sua função é garantir qualidade em todo o ciclo de desenvolvimento:
análise de requisitos, estratégia de testes, revisão de código, identificação de regressões e validação de entregáveis.

Competências principais:
- Definir estratégias de teste (unitário, integração, E2E, carga, segurança)
- Escrever e revisar test cases e test plans
- Identificar edge cases, condições de contorno e cenários de falha
- Analisar código em busca de bugs, race conditions e problemas de concorrência
- Revisar PRs com foco em qualidade, cobertura e manutenibilidade
- Propor fixtures, mocks e dados de teste realistas
- Auditar logs e traces em busca de anomalias
- Gerar relatórios de cobertura e risco

Linguagens e ferramentas que domina:
- Python: pytest, pytest-asyncio, httpx, factory_boy, faker
- TypeScript/JS: vitest, jest, playwright, supertest
- Ferramentas: coverage.py, hypothesis (property-based), locust (carga)

Regras de resposta:
- Responda sempre no mesmo idioma utilizado pelo usuário na mensagem recebida.
- Seja direto: priorize o que bloqueia a entrega.
- Quando identificar um bug, descreva: sintoma → causa raiz → impacto → fix sugerido.
- Quando propor testes, escreva o código completo pronto para copiar/executar.
- Nunca aprove um entregável sem critérios de aceite claros.
- Se o pedido for vago, peça exatamente o que falta para dar uma resposta útil.
"""

QA_SKILLS = [
    {
        "name": "write_test_plan",
        "description": "Gera plano de testes completo para uma feature ou módulo",
        "input_schema": {
            "feature": "string (descrição da feature ou módulo)",
            "stack": "string (linguagem/frameworks envolvidos)",
            "risks": "array (riscos conhecidos ou áreas críticas)"
        },
        "output_schema": {
            "test_plan": "object (escopo, estratégia, critérios de aceite)",
            "test_cases": "array (casos de teste com steps e expected result)",
            "coverage_targets": "object (% unitário, integração, E2E)"
        }
    },
    {
        "name": "review_code_quality",
        "description": "Revisa código com foco em bugs, edge cases e testabilidade",
        "input_schema": {
            "code": "string (trecho ou arquivo de código)",
            "context": "string (o que o código deve fazer)"
        },
        "output_schema": {
            "issues": "array (bugs, code smells, riscos)",
            "test_suggestions": "array (testes sugeridos com código)",
            "severity": "string (critical/high/medium/low)"
        }
    },
    {
        "name": "generate_test_cases",
        "description": "Gera casos de teste automatizados prontos para execução",
        "input_schema": {
            "target": "string (função, endpoint ou componente)",
            "framework": "string (pytest, jest, playwright etc.)",
            "scenarios": "array (cenários feliz, triste, edge cases)"
        },
        "output_schema": {
            "test_code": "string (código de teste completo)",
            "fixtures": "array (fixtures e mocks necessários)",
            "commands": "array (comandos para executar)"
        }
    },
    {
        "name": "analyze_failure",
        "description": "Analisa erro, log ou traceback e propõe diagnóstico e fix",
        "input_schema": {
            "error": "string (mensagem de erro ou traceback)",
            "context": "string (o que estava sendo feito quando o erro ocorreu)"
        },
        "output_schema": {
            "root_cause": "string (causa raiz identificada)",
            "impact": "string (o que está quebrado/afetado)",
            "fix": "string (correção sugerida com código se aplicável)",
            "regression_tests": "array (testes para evitar regressão)"
        }
    },
]


class QAAgent(BaseAgent):
    name = "qa"
    description = "QA Lead — testes, qualidade, revisão de código e análise de falhas"
    system_prompt = QA_SYSTEM_PROMPT
    skills = QA_SKILLS


agent_registry.register(QAAgent())
