"""
Modelos Pydantic da Aplicação
"""

from typing import Optional
from pydantic import BaseModel


class ChatMessage(BaseModel):
    """Mensagem de chat"""
    content: str


class FrictionReportInput(BaseModel):
    """Relatório de fricção"""
    code: str
    layer: str
    action_attempted: str
    description: str
    user_id: Optional[int] = None
    session_id: Optional[str] = None
    tier: str = "free"


class CommandExecuteInput(BaseModel):
    """Entrada para execução de comando"""
    confirm: bool = False


class CommandPlanInput(BaseModel):
    """Entrada para planejamento de comando"""
    command: str
    cwd: Optional[str] = None


class UserMessage(BaseModel):
    """Mensagem do usuário"""
    content: str
    session_id: Optional[str] = None
    ide_context: Optional[dict] = None


class SystemInfo(BaseModel):
    """Informações do sistema"""
    platform: str
    architecture: str
    processor: str
    python_version: str
    memory_info: Optional[dict] = None


class CommandOutput(BaseModel):
    """Saída de comando executado"""
    success: bool
    returncode: int
    stdout: str
    stderr: str
    started_at: str
    duration_seconds: float
    error: Optional[str] = None


class Artifact(BaseModel):
    """Artefato gerado"""
    id: str
    path: str
    type: str
    size: int
    created_at: str
    metadata: Optional[dict] = None
