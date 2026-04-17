"""
Utilitários para manipulação de comandos e execução.
"""
import os
import re
from typing import Dict, Any, Optional, List


def split_semicolon_paths(s: str) -> List[str]:
    """Divide string por ponto-e-vírgula e retorna lista de partes não-vazias."""
    parts = []
    for p in (s or "").split(";"):
        v = p.strip()
        if v:
            parts.append(v)
    return parts


def normalize_command_key(command: str) -> str:
    """Normaliza uma chave de comando para comparação."""
    tokens = [t for t in re.split(r"\s+", str(command or "").strip()) if t]
    return " ".join(tokens).strip().lower()


def normalize_cwd(*, cwd: Optional[str], base_dir: str) -> str:
    """Normaliza o diretório de trabalho atual."""
    v = str(cwd or "").strip().strip("`\"' ,")
    if not v:
        return os.path.abspath(str(base_dir))
    return os.path.abspath(v)


def is_under_allowed_roots(path: str, roots: List[str]) -> bool:
    """Verifica se um path está sob os diretórios raiz permitidos."""
    if not path:
        return False
    target = os.path.abspath(path)
    for r in roots or []:
        base = os.path.abspath(r)
        if target.lower() == base.lower():
            return True
        if target.lower().startswith(base.rstrip("\\/").lower() + os.sep.lower()):
            return True
    return False
