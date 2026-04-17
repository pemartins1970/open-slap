"""
Utilitários para manipulação de variáveis de ambiente.
"""
from typing import List, Optional


def env_flag(v: Optional[str], default: bool = False) -> bool:
    """Converte valor de env para booleano."""
    s = str(v if v is not None else ("1" if default else "0")).strip().lower()
    return s in ("1", "true", "yes", "on")


def env_int(v: Optional[str], default: int) -> int:
    """Converte valor de env para inteiro."""
    try:
        return (
            int(str(v or "").strip()) if v is not None and str(v).strip() else default
        )
    except Exception:
        return default


def env_float(v: Optional[str], default: float) -> float:
    """Converte valor de env para float."""
    try:
        return (
            float(str(v or "").strip()) if v is not None and str(v).strip() else default
        )
    except Exception:
        return default


def env_list(v: Optional[str]) -> List[str]:
    """Converte valor de env para lista de strings."""
    raw = str(v or "").strip()
    if not raw:
        return []
    parts = [p.strip() for p in raw.split(",")]
    return [p for p in parts if p]
