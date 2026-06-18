from typing import Dict, Any, List
from .base import BaseAgent, agent_registry

DATA_SYSTEM_PROMPT = """
Você é o Cientista de Dados do Open Slap!. Sua função é analisar dados, construir modelos,
gerar visualizações, validar hipóteses e extrair insights acionáveis a partir de dados.

Competências principais:
- Analisar dados estruturados e não estruturados
- Construir e validar modelos de machine learning
- Gerar visualizações e dashboards para comunicação de insights
- Realizar análises estatísticas (descritiva, inferencial, preditiva)
- Limpar, transformar e preparar dados para análise
- Identificar padrões, tendências e anomalias em dados
- Projetar e interpretar experimentos (A/B testing, testes de hipótese)
- Documentar metodologias e premissas das análises

Ferramentas e bibliotecas que domina:
- Python: pandas, numpy, scikit-learn, matplotlib, seaborn, plotly, statsmodels
- SQL: consultas, agregações, janelas, otimização
- Visualização: gráficos de distribuição, séries temporais, correlação, comparação

Regras de resposta:
- Responda sempre no mesmo idioma utilizado pelo usuário na mensagem recebida.
- Seja direto: insight primeiro, metodologia depois.
- Sempre valide premissas antes de propor conclusões.
- Quando apresentar dados, prefira visualizações a tabelas grandes.
- Se os dados forem insuficientes para uma conclusão, diga claramente.
- Documente limitações da análise junto com os resultados.
"""

DATA_SKILLS = [
    {
        "name": "analyze_dataset",
        "description": "Analisa dataset e gera insights estatísticos",
        "input_schema": {
            "data_description": "string (descrição dos dados disponíveis)",
            "columns": "array (colunas com tipos e descrição)",
            "questions": "array (perguntas a serem respondidas)",
            "sample_size": "number (número de registros, se disponível)"
        },
        "output_schema": {
            "summary_statistics": "object (médias, medianas, distribuições, correlações)",
            "insights": "array (insights encontrados com confiança)",
            "visualization_suggestions": "array (gráficos sugeridos para cada insight)",
            "limitations": "array (limitações da análise)"
        }
    },
    {
        "name": "design_experiment",
        "description": "Projeta experimento (A/B test, teste de hipótese)",
        "input_schema": {
            "hypothesis": "string (hipótese a ser testada)",
            "metrics": "array (métricas de sucesso)",
            "population": "string (descrição da população)",
            "constraints": "object (restrições: tamanho amostral, duração, etc.)"
        },
        "output_schema": {
            "experiment_design": "object (grupos, variáveis, aleatorização)",
            "sample_size_calculation": "object (tamanho amostral necessário, poder estatístico)",
            "analysis_plan": "string (método de análise proposto)",
            "risks": "array (riscos ao experimento e como mitigar)"
        }
    },
    {
        "name": "suggest_model",
        "description": "Sugere modelo de ML para problema dado",
        "input_schema": {
            "problem_type": "string (classificação, regressão, clustering, séries temporais)",
            "data_characteristics": "object (tamanho, features, target, balanceamento)",
            "constraints": "object (latência, interpretabilidade, recursos)"
        },
        "output_schema": {
            "recommended_models": "array (modelos sugeridos com justificativa)",
            "expected_performance": "object (estimativa de performance por modelo)",
            "preprocessing_steps": "array (etapas de preparação dos dados)",
            "evaluation_metrics": "array (métricas de avaliação recomendadas)",
            "implementation_notes": "string (observações para implementação)"
        }
    },
]


class DataAgent(BaseAgent):
    name = "data"
    description = "Cientista de Dados — análise, ML, estatística e visualização"
    system_prompt = DATA_SYSTEM_PROMPT
    skills = DATA_SKILLS


agent_registry.register(DataAgent())
