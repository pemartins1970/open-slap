import logging
from typing import Dict, Any
from backend.agents.cto_agent import CTOAgent
from backend.agents.security_tester import SecurityTesterAgent
from backend.project_brain import project_brain

logger = logging.getLogger(__name__)

class ReviewLoop:
    """Orquestra a validação técnica e de segurança antes de qualquer execução."""

    def __init__(self):
        self.cto = CTOAgent()
        self.security = SecurityTesterAgent()

    async def validate_plan(self, project_id: str, proposed_code: str, intent: str) -> Dict[str, Any]:
        """Executa a validação cruzada entre CTO e Security."""
        
        # 1. Validação Técnica (CTO)
        cto_result = await self.cto.process_intent(project_id, intent)
        if cto_result.get("error"):
            return cto_result # Falha estrutural ou de intenção

        # 2. Validação de Segurança (Security Tester)
        # O Security Tester analisa o código proposto em busca de vulnerabilidades
        security_result = await self.security.analyze_code(proposed_code)
        
        if security_result.get("risk_level") == "high":
            return {
                "status": "rejected",
                "reason": f"Segurança: Código com risco alto detectado: {security_result.get('details')}"
            }

        # 3. Registro de Sucesso no Brain
        project_brain.log_decision(project_id, f"Plano validado: {intent}")
        
        return {
            "status": "approved",
            "message": "O plano e o código foram validados pelo time de agentes."
        }

# Instância única para ser usada pelo orquestrador
review_loop = ReviewLoop()
