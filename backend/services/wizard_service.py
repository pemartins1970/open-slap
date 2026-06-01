from typing import Dict, Any, Optional, List
from ..db import save_wizard_state, load_wizard_state, delete_wizard_state

# ID do Wizard de Projeto
PROJECT_WIZARD_ID = "start_project_v1"

# Registro em memória como fallback (backup)
# Em produção, usaremos primarily banco de dados SQLite
project_wizard_registry: Dict[int, Dict[str, Any]] = {}

def is_project_wizard_start(internal_prompt: str) -> bool:
    """Detecta se o comando interno indica o início de um novo projeto."""
    return f"WIZARD_ID: {PROJECT_WIZARD_ID}" in (internal_prompt or "")

def get_wizard_state(conversation_id: int) -> Optional[Dict[str, Any]]:
    """Recupera o estado atual do wizard para uma conversa específica."""
    # Tenta carregar do banco de dados primeiro
    state = load_wizard_state(conversation_id)
    if state:
        return state
    
    # Fallback para memória (compatibilidade)
    return project_wizard_registry.get(int(conversation_id))

def set_wizard_state(conversation_id: int, state: Dict[str, Any], user_id: Optional[int] = None):
    """Define ou atualiza o estado do wizard para uma conversa."""
    # Salva no banco de dados se tiver user_id
    if user_id is not None:
        save_wizard_state(conversation_id, user_id, state)
    
    # Mantém backup em memória
    project_wizard_registry[int(conversation_id)] = state

def clear_wizard_state(conversation_id: int):
    """Remove o estado do wizard ao concluir ou cancelar."""
    # Remove do banco de dados
    delete_wizard_state(conversation_id)
    
    # Remove da memória
    if int(conversation_id) in project_wizard_registry:
        del project_wizard_registry[int(conversation_id)]

def get_next_step_text(stage: str) -> str:
    """Retorna o texto de instrução para o próximo passo do wizard (legado)."""
    steps = {
        "q2": "Pergunta 2 * Quem é o público-alvo para este projeto?",
        "q3": "Pergunta 3 * Existe um prazo específico para a conclusão do projeto?",
        "q4": "Pergunta 4 * Há restrições técnicas, orçamentárias ou de recursos que precisamos considerar?",
        "q5": "Pergunta 5 * O projeto envolverá integrações com sistemas externos ou dados sensíveis que precisamos proteger?",
    }
    return steps.get(stage, "")

def has_question(user_message: str) -> bool:
    """Detecta se a mensagem do usuário parece conter uma pergunta."""
    msg = (user_message or "").strip()
    if not msg:
        return False
    if "?" in msg:
        return True
    
    lower = msg.lower()
    starters = (
        "como ", "o que ", "oq ", "por que", "pq ", "qual ", 
        "quais ", "onde ", "quando ", "dúvida", "duvida"
    )
    return any(lower.startswith(s) for s in starters)

def detect_blog_ambiguity(user_message: str) -> bool:
    """Verifica se há ambiguidade na criação de um blog (SaaS vs Custom)."""
    lower = (user_message or "").lower()
    if "blog" not in lower:
        return False
    
    known_platforms = ("wordpress", "ghost", "medium", "substack", "blogger", "wix", "webflow")
    if any(k in lower for k in known_platforms):
        return False
        
    custom_keywords = ("do zero", "do 0", "custom", "sob medida", "próprio", "proprio", "localmente")
    if any(k in lower for k in custom_keywords):
        return False
        
    return True

def handle_wizard_message(
    conversation_id: int,
    user_message: str,
    internal_prompt: str,
    user_id: Optional[int] = None,  # usado para persistência futura no DB
) -> Optional[Dict[str, Any]]:
    """
    Orquestra o estado do wizard.
    Retorna o estado se houver processamento interno, ou None para delegar ao LLM.

    Args:
        conversation_id: ID da conversa ativa.
        user_message: Mensagem enviada pelo usuário.
        internal_prompt: Prompt interno com metadados do sistema (ex: WIZARD_ID).
        user_id: ID do usuário (reservado para persistência futura no DB).
    """
    state = get_wizard_state(conversation_id)

    if not state:
        if not is_project_wizard_start(internal_prompt):
            return None

        # Inicializa o estado para o kickoff dinâmico conduzido pela Sabrina
        state = {
            "stage": "dynamic_kickoff",
            "answers": {},
            "project_id": None,
            "user_id": user_id,
        }
        set_wizard_state(conversation_id, state, user_id)
        return None  # Delega à Sabrina (LLM) a condução inicial

    if state.get("stage") == "dynamic_kickoff":
        return None  # Deixa Sabrina continuar a entrevista

    return None

