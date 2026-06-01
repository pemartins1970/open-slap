import logging
from backend.project_brain import project_brain
from backend.security_guardrail import SecurityGuardrail

logger = logging.getLogger(__name__)

class CTOAgent:
    """Orquestrador técnico que valida intenções contra o Brain do projeto."""
    
    async def process_intent(self, project_id: str, intent_text: str):
        # 1. Recuperar contexto do projeto (Essência + Specs)
        context = project_brain.get_project_context(project_id)
        if not context:
            return {"error": "Projeto não encontrado."}
        
        # 2. Validar a intenção com B.E.N. (Segurança)
        safety_check = SecurityGuardrail.evaluate(intent_text)
        if safety_check["action"] == "block":
            return {"error": "Intenção bloqueada por diretrizes de segurança."}
            
        # 3. CTO toma a decisão técnica baseada na 'Constituição' (Spec)
        # Se for uma alteração crítica, ele pode exigir aprovação humana
        logger.info(f"CTO validou intenção para o projeto {project_id}")
        return {"status": "validated", "spec": context["spec"]}
