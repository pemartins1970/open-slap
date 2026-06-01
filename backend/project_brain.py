"""
Project Brain - Sistema de memória contextual de projetos
Stub temporário para resolver imports quebrados
"""

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class ProjectBrain:
    """Gerenciador de contexto e memória de projetos"""
    
    def __init__(self):
        self._projects: Dict[str, Dict[str, Any]] = {}
        logger.debug("ProjectBrain inicializado")
    
    def get_project_context(self, project_id: str) -> Optional[Dict[str, Any]]:
        """
        Recupera o contexto completo de um projeto
        
        Args:
            project_id: ID do projeto
            
        Returns:
            Dicionário com essence e spec do projeto, ou None
        """
        if project_id not in self._projects:
            logger.warning(f"Projeto {project_id} não encontrado no Brain")
            return None
        
        return self._projects.get(project_id)
    
    def save_project_context(self, project_id: str, essence: str, spec: Dict[str, Any]) -> None:
        """Salva o contexto de um projeto"""
        self._projects[project_id] = {
            "essence": essence,
            "spec": spec
        }
        logger.info(f"Contexto do projeto {project_id} salvo no Brain")
    
    def update_project_spec(self, project_id: str, spec_updates: Dict[str, Any]) -> bool:
        """Atualiza a especificação de um projeto"""
        if project_id not in self._projects:
            return False
        
        self._projects[project_id]["spec"].update(spec_updates)
        logger.info(f"Spec do projeto {project_id} atualizada")
        return True
    
    def log_decision(self, project_id: str, decision: str) -> None:
        """Registra uma decisão tomada no contexto do projeto"""
        if project_id not in self._projects:
            logger.warning(f"Tentativa de log em projeto inexistente: {project_id}")
            return
        
        if "decisions" not in self._projects[project_id]:
            self._projects[project_id]["decisions"] = []
        
        self._projects[project_id]["decisions"].append({
            "timestamp": logger.handlers[0].formatter.formatTime(logging.LogRecord("", 0, "", 0, "", (), None)) if logger.handlers else "unknown",
            "decision": decision
        })
        logger.info(f"Decisão registrada no projeto {project_id}: {decision}")

# Singleton global
project_brain = ProjectBrain()
