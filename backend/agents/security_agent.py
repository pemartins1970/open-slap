from typing import Dict, Any, List
from .base import BaseAgent, agent_registry

SECURITY_SYSTEM_PROMPT = """
Você é o Consultor de Segurança do Open Slap!. Sua função é analisar código, identificar
vulnerabilidades, propor hardening, revisar configurações de segurança e garantir boas práticas
de segurança no ciclo de desenvolvimento.

Competências principais:
- Revisar código em busca de vulnerabilidades (OWASP Top 10)
- Analisar configurações de segurança (CORS, auth, rate limiting, TLS)
- Identizar vazamento de secrets, tokens e credenciais no código
- Propor hardening de endpoints, middlewares e dependências
- Validar práticas de autenticação e autorização
- Revisar políticas de CORS, CSP e headers de segurança
- Analisar dependências para CVEs conhecidas
- Propor testes de segurança automatizados

OWASP Top 10 que domina:
- Broken Access Control, Cryptographic Failures, Injection, Insecure Design
- Security Misconfiguration, Vulnerable Components, Auth Failures
- Data Integrity Failures, Logging/Monitoring, SSRF

Regras de resposta:
- Responda sempre no mesmo idioma utilizado pelo usuário na mensagem recebida.
- Seja direto: vulnerabilidade → risco → impacto → correção.
- Classifique cada achado por severidade (critical/high/medium/low/info).
- Sempre proponha um fix concreto, não apenas descreva o problema.
- Quando aprovar uma configuração, explique por que é segura.
- Se faltar contexto para analisar, peça o trecho ou arquivo específico.
"""

SECURITY_SKILLS = [
    {
        "name": "review_code_security",
        "description": "Revisa código em busca de vulnerabilidades de segurança",
        "input_schema": {
            "code": "string (código ou arquivo para análise)",
            "context": "string (o que o código faz e em que ambiente roda)"
        },
        "output_schema": {
            "vulnerabilities": "array (achados com severidade, linha e descrição)",
            "fixes": "array (correções sugeridas com código)",
            "risk_score": "number (0-100)",
            "priority": "string (imediata/alta/média/baixa)"
        }
    },
    {
        "name": "harden_config",
        "description": "Revisa e propõe hardening de configurações de segurança",
        "input_schema": {
            "config_type": "string (CORS, CSP, auth, rate_limit, TLS, headers)",
            "current_config": "string (configuração atual)",
            "environment": "string (dev, staging, production)"
        },
        "output_schema": {
            "issues": "array (problemas de configuração encontrados)",
            "hardened_config": "string (configuração proposta)",
            "rationale": "string (explicação de cada mudança)",
            "residual_risks": "array (riscos que permanecem após hardening)"
        }
    },
    {
        "name": "audit_dependencies",
        "description": "Analisa dependências em busca de CVEs conhecidas",
        "input_schema": {
            "dependencies": "object (nome: versão das dependências)",
            "ecosystem": "string (pip, npm, maven, etc.)"
        },
        "output_schema": {
            "vulnerable": "array (dependências com CVE conhecida)",
            "safe": "array (dependências sem CVEs conhecidas)",
            "recommended_updates": "object (dependência: versão recomendada)",
            "critical_count": "number (CVEs críticas encontradas)"
        }
    },
]


class SecurityAgent(BaseAgent):
    name = "security"
    description = "Segurança — análise de vulnerabilidades, hardening e revisão de configurações"
    system_prompt = SECURITY_SYSTEM_PROMPT
    skills = SECURITY_SKILLS


agent_registry.register(SecurityAgent())
