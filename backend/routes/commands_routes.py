"""
Rotas de comandos — config, plan, execute, autoapprove.
Extraídas de main_auth.py.
"""
import uuid
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import BaseModel

from ..deps import security, _get_effective_security_settings, pending_command_registry
from ..main_auth import get_current_user

commands_router = APIRouter(prefix="/api", tags=["commands"])


class CommandExecuteInput(BaseModel):
    confirm: bool = False


class CommandPlanInput(BaseModel):
    command: str
    cwd: Optional[str] = None


@commands_router.get("/commands/config")
async def get_commands_config(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """Retorna configuração atual de comandos."""
    # Lazy imports para evitar circular
    from ..main_auth import (
        _get_allowed_command_roots,
        ENABLE_OS_COMMANDS,
        OS_COMMAND_TIMEOUT_S,
        OS_COMMAND_MAX_OUTPUT_CHARS,
    )
    token = credentials.credentials
    current_user = get_current_user(token)
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado")

    security_settings = _get_effective_security_settings(int(current_user["id"]))
    return {
        "enable_os_commands": ENABLE_OS_COMMANDS and security_settings.get("os_commands_enabled", True),
        "timeout_s": OS_COMMAND_TIMEOUT_S,
        "max_output_chars": OS_COMMAND_MAX_OUTPUT_CHARS,
        "allowed_roots": _get_allowed_command_roots(user_id=int(current_user["id"])),
    }


@commands_router.post("/commands/plan")
async def plan_command(
    payload: CommandPlanInput,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """Avalia um comando e retorna política de execução."""
    # Lazy import para evitar circular
    from ..main_auth import _command_policy_evaluate
    token = credentials.credentials
    current_user = get_current_user(token)
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado")

    cmd = (payload.command or "").strip()
    if not cmd:
        raise HTTPException(status_code=400, detail="Comando vazio")

    policy = _command_policy_evaluate(
        command=cmd,
        cwd=payload.cwd,
        user_id=int(current_user["id"]),
    )

    # Se requer confirmação, registrar comando pendente
    if policy.get("requires_confirmation"):
        request_id = str(uuid.uuid4())
        pending_command_registry[request_id] = {
            "user_id": int(current_user["id"]),
            "command": cmd,
            "cwd": policy.get("cwd"),
            "policy": policy,
            "timestamp": __import__("datetime").datetime.utcnow().isoformat(),
        }
        policy["request_id"] = request_id

    return policy


@commands_router.post("/commands/pending/{request_id}/execute")
async def execute_pending_command(
    request_id: str,
    payload: CommandExecuteInput,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """Executa um comando previamente planejado."""
    token = credentials.credentials
    current_user = get_current_user(token)
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado")

    pending = pending_command_registry.get(request_id)
    if not pending:
        raise HTTPException(status_code=404, detail="Requisição não encontrada ou expirada")

    if pending["user_id"] != int(current_user["id"]):
        raise HTTPException(status_code=403, detail="Acesso negado")

    if not payload.confirm:
        return {
            "ok": False,
            "message": "Confirmação necessária",
            "command": pending["command"],
        }

    # Verificar se ainda é permitido
    # Lazy imports para evitar circular
    from ..main_auth import (
        _command_policy_evaluate,
        _run_powershell_command,
        OS_COMMAND_TIMEOUT_S,
        OS_COMMAND_MAX_OUTPUT_CHARS,
    )
    policy = _command_policy_evaluate(
        command=pending["command"],
        cwd=pending.get("cwd"),
        user_id=int(current_user["id"]),
    )

    if not policy.get("allowed"):
        raise HTTPException(status_code=403, detail=policy.get("blocked_reason", "Comando bloqueado"))

    # Executar
    result = await _run_powershell_command(
        command=pending["command"],
        cwd=policy.get("cwd", pending.get("cwd", ".")),
        timeout_s=OS_COMMAND_TIMEOUT_S,
    )

    # Limpar registro pendente
    pending_command_registry.pop(request_id, None)

    # Truncar saída se necessário
    stdout = result.get("stdout", "")
    stderr = result.get("stderr", "")
    max_chars = OS_COMMAND_MAX_OUTPUT_CHARS
    if len(stdout) > max_chars:
        stdout = stdout[:max_chars] + "\n... [truncado]"
    if len(stderr) > max_chars:
        stderr = stderr[:max_chars] + "\n... [truncado]"

    return {
        "ok": result.get("returncode") == 0,
        "returncode": result.get("returncode"),
        "stdout": stdout,
        "stderr": stderr,
        "duration_ms": result.get("duration_ms"),
    }


@commands_router.post("/commands/pending/{request_id}/autoapprove")
async def autoapprove_pending_command(
    request_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """Auto-aprova um comando para execução futura."""
    token = credentials.credentials
    current_user = get_current_user(token)
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado")

    pending = pending_command_registry.get(request_id)
    if not pending:
        raise HTTPException(status_code=404, detail="Requisição não encontrada ou expirada")

    if pending["user_id"] != int(current_user["id"]):
        raise HTTPException(status_code=403, detail="Acesso negado")

    # Adicionar à lista de comandos auto-aprovados
    # Lazy imports para evitar circular
    from ..main_auth import _normalize_command_key, add_user_command_autoapprove
    command_key = _normalize_command_key(pending["command"])
    add_user_command_autoapprove(int(current_user["id"]), command_key)

    return {
        "ok": True,
        "message": "Comando adicionado à lista de auto-aprovados",
        "command_key": command_key,
    }
