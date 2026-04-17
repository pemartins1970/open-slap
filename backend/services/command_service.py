"""
Serviço de Gerenciamento de Comandos
"""

import os
import re
import json
import uuid
import asyncio
import subprocess
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path

from ..config.settings import settings


def split_semicolon_paths(s: str) -> List[str]:
    """Divide caminhos separados por ponto e vírgula"""
    parts = []
    for p in (s or "").split(";"):
        v = p.strip()
        if v:
            parts.append(v)
    return parts


def get_allowed_command_roots(*, user_id: int) -> List[str]:
    """Obtém raízes permitidas para comandos do usuário"""
    from ..deps import BASE_DIR, DEFAULT_DELIVERIES_ROOT
    
    roots = [
        os.path.abspath(str(BASE_DIR)),
        os.path.abspath(DEFAULT_DELIVERIES_ROOT),
    ]
    
    # Adiciona raízes configuradas
    configured_roots = split_semicolon_paths(settings.os_command_allowed_roots_raw)
    for root in configured_roots:
        abs_root = os.path.abspath(root)
        if os.path.exists(abs_root):
            roots.append(abs_root)
    
    # Remove duplicatas
    uniq = []
    for r in roots:
        if r not in uniq:
            uniq.append(r)
    return uniq


def command_policy_evaluate(
    *, command: str, cwd: Optional[str], user_id: int
) -> Dict[str, Any]:
    """Avalia política de execução de comando"""
    cmd = str(command or "").strip()
    if not cmd:
        return {"allowed": False, "reason": "Comando vazio"}
    
    # Verifica se o comando é auto-aprovado para o usuário
    if is_user_autoapproved_command(user_id=user_id, command=cmd):
        return {"allowed": True, "auto_approved": True}
    
    # Verifica se o diretório está permitido
    if cwd and not is_under_allowed_roots(cwd, user_id=user_id):
        return {
            "allowed": False,
            "reason": f"Diretório não permitido: {cwd}"
        }
    
    return {"allowed": True, "requires_approval": True}


def is_user_autoapproved_command(*, user_id: int, command: str) -> bool:
    """Verifica se o comando é auto-aprovado para o usuário"""
    try:
        from ..utils.commands import normalize_command_key
        from ..deps import pending_command_registry
        
        key = normalize_command_key(command)
        if not key:
            return False
        
        user_commands = pending_command_registry.get(str(user_id), {})
        return user_commands.get(key, {}).get("auto_approved", False)
    except Exception:
        return False


def is_under_allowed_roots(path: str, *, user_id: int) -> bool:
    """Verifica se o caminho está sob as raízes permitidas"""
    try:
        from ..utils.commands import normalize_cwd
        
        abs_path = os.path.abspath(normalize_cwd(path))
        allowed_roots = get_allowed_command_roots(user_id=user_id)
        
        for root in allowed_roots:
            if abs_path.startswith(os.path.abspath(root) + os.sep) or abs_path == os.path.abspath(root):
                return True
        return False
    except Exception:
        return False


async def run_powershell_command(
    *, command: str, cwd: str, timeout_s: int
) -> Dict[str, Any]:
    """Executa comando PowerShell de forma assíncrona"""
    started = datetime.utcnow()
    
    try:
        # Prepara o comando PowerShell
        ps_command = f"cd '{cwd}'; {command}"
        
        # Executa o processo
        proc = await asyncio.create_subprocess_shell(
            f"powershell -Command \"{ps_command}\"",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=cwd
        )
        
        # Captura saída
        stdout, stderr = await asyncio.wait_for(
            proc.communicate(), timeout=timeout_s
        )
        
        # Converte para string
        stdout_text = stdout.decode('utf-8', errors='replace').strip()
        stderr_text = stderr.decode('utf-8', errors='replace').strip()
        
        return {
            "success": proc.returncode == 0,
            "returncode": proc.returncode,
            "stdout": stdout_text,
            "stderr": stderr_text,
            "started_at": started.isoformat(),
            "duration_seconds": (datetime.utcnow() - started).total_seconds()
        }
        
    except asyncio.TimeoutError:
        return {
            "success": False,
            "error": "Timeout",
            "stdout": "",
            "stderr": f"Comando excedeu timeout de {timeout_s}s",
            "started_at": started.isoformat(),
            "duration_seconds": timeout_s
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "stdout": "",
            "stderr": f"Erro ao executar comando: {str(e)}",
            "started_at": started.isoformat(),
            "duration_seconds": (datetime.utcnow() - started).total_seconds()
        }


def extract_tagged_json_blocks(
    text: str, *, start_tag: str, end_tag: str
) -> List[Dict[str, Any]]:
    """Extrai blocos JSON marcados com tags"""
    if not text:
        return []
    
    blocks = []
    pattern = f"{re.escape(start_tag)}(.*?){re.escape(end_tag)}"
    matches = re.findall(pattern, text, re.DOTALL | re.IGNORECASE)
    
    for match in matches:
        try:
            block = json.loads(match.strip())
            if isinstance(block, dict):
                blocks.append(block)
        except json.JSONDecodeError:
            continue
    
    return blocks


def extract_cli_output_fields(output_json: str) -> Dict[str, str]:
    """Extrai campos stdout/stderr de saída JSON"""
    stdout = ""
    stderr = ""
    try:
        out_obj = json.loads(str(output_json or "") or "{}")
        stdout = str(out_obj.get("stdout") or "")
        stderr = str(out_obj.get("stderr") or "")
    except (json.JSONDecodeError, TypeError):
        pass
    return {"stdout": stdout, "stderr": stderr}


def extract_cli_artifacts(output_json: str) -> List[Dict[str, Any]]:
    """Extrai artefatos de saída JSON"""
    try:
        out_obj = json.loads(str(output_json or "") or "{}")
        arts = out_obj.get("artifacts") or []
        if isinstance(arts, list):
            return [a for a in arts if isinstance(a, dict)]
    except (json.JSONDecodeError, TypeError):
        pass
    return []


def register_cli_artifacts(artifacts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Registra artefatos CLI no sistema"""
    from ..deps import artifact_registry
    
    out: List[Dict[str, Any]] = []
    for a in artifacts or []:
        p = str((a or {}).get("path") or "").strip()
        if not p:
            continue
        
        artifact_id = str(uuid.uuid4())
        artifact_info = {
            "id": artifact_id,
            "path": p,
            "type": str((a or {}).get("type") or "file").strip(),
            "size": int((a or {}).get("size") or 0),
            "created_at": datetime.utcnow().isoformat(),
            "metadata": {k: v for k, v in (a or {}).items() if k not in ["path", "type", "size"]}
        }
        
        artifact_registry[artifact_id] = artifact_info
        out.append(artifact_info)
    
    return out
