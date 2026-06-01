"""
Utilitários para autenticação e autorização.
"""
from typing import Dict, Any, Optional


# Constantes de paths públicos e protegidos
PUBLIC_PATH_PREFIXES = ("/auth/", "/assets/", "/media/")
PUBLIC_PATHS = {
    "/",
    "/index.html",
    "/open_slap.png",
    "/pemartins.jpg",
    "/btn_donateCC_LG.gif",
    "/doacoes.txt",
    "/health",
    "/auth/register",
    "/auth/login",
    "/auth/password-reset/request",
    "/auth/password-reset/confirm",
    "/forge/token",
    "/forge/status",
}

PROTECTED_PATHS = {"/auth/me"}
PROTECTED_PATH_PREFIXES = ("/api/", "/local/")


def extract_bearer_token_from_headers(headers: Dict[str, str]) -> Optional[str]:
    """Extrai token bearer dos headers."""
    raw = (headers.get("authorization") or headers.get("Authorization") or "").strip()
    if not raw:
        return None
    if raw.lower().startswith("bearer "):
        token = raw[7:].strip()
        return token or None
    return None


def is_public_path(path: str) -> bool:
    """Verifica se o path é público (não requer auth)."""
    p = (path or "").strip()
    if not p:
        return False
    if p in PUBLIC_PATHS:
        return True
    return any(p.startswith(prefix) for prefix in PUBLIC_PATH_PREFIXES)


def requires_auth(path: str) -> bool:
    """Verifica se o path requer autenticação."""
    p = (path or "").strip()
    if not p:
        return True
    if p in PROTECTED_PATHS:
        return True
    return any(p.startswith(prefix) for prefix in PROTECTED_PATH_PREFIXES)
