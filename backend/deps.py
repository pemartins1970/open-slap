import base64
import ctypes
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional, List

from fastapi import HTTPException, Request
from pydantic import BaseModel

from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from cryptography.fernet import Fernet, InvalidToken

# Diretórios base
BASE_DIR = Path(__file__).resolve().parents[1]
MEDIA_DIR = BASE_DIR.parent / "media"
MEDIA_DIR.mkdir(parents=True, exist_ok=True)

# Configurações Forge IDE
FORGE_IDE_MODE = os.getenv("FORGE_IDE_MODE", "false").lower() in ("1", "true", "yes", "on")
FORGE_IDE_EMAIL = str(os.getenv("FORGE_IDE_EMAIL") or "forge@localhost").strip().lower()
FORGE_IDE_TOKEN_TTL_MINUTES = int(os.getenv("FORGE_IDE_TOKEN_TTL_MINUTES") or "120")


def _is_local_client(request: Request) -> bool:
    """Verifica se a requisição vem de um cliente local."""
    try:
        host = (request.client.host if request.client else "") or ""
    except Exception:
        host = ""
    host = str(host).strip().lower()
    if host in ("127.0.0.1", "localhost", "::1"):
        return True
    return False


def _ensure_forge_user() -> Dict[str, Any]:
    """Garante que o usuário Forge IDE existe no banco de dados."""
    from .auth import auth_manager, create_user
    import sqlite3
    from datetime import timedelta as _td

    db_path = str(getattr(auth_manager, "db_path", "") or "").strip()
    if not db_path:
        raise HTTPException(status_code=500, detail="Auth DB path inválido")

    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT id, email, created_at FROM users WHERE email = ?",
            (FORGE_IDE_EMAIL,),
        ).fetchone()
        if row:
            return dict(row)

    import secrets
    pwd = secrets.token_hex(16)
    try:
        create_user(FORGE_IDE_EMAIL, pwd)
    except Exception:
        pass

    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT id, email, created_at FROM users WHERE email = ?",
            (FORGE_IDE_EMAIL,),
        ).fetchone()
        if not row:
            raise HTTPException(status_code=500, detail="Falha ao provisionar usuário Forge")
        return dict(row)


class SkillsUpdate(BaseModel):
    """Modelo para atualização de skills do usuário."""
    skills: List[Dict[str, Any]]


def _require_mcp_secret(request: Request) -> None:
    """Verifica se o header X-MCP-Secret está presente e válido."""
    import os
    expected = os.getenv("OPENSLAP_MCP_SECRET", "").strip()
    if not expected:
        raise HTTPException(status_code=500, detail="MCP secret não configurado")
    provided = request.headers.get("X-MCP-Secret", "").strip()
    if provided != expected:
        raise HTTPException(status_code=401, detail="MCP secret inválido")


class TelegramLinkConsumeInput(BaseModel):
    """Input para consumir código de link do Telegram."""
    code: str
    telegram_user_id: str
    chat_id: str


class TelegramUnlinkInput(BaseModel):
    """Input para desvincular Telegram."""
    telegram_user_id: str
    chat_id: str


class TelegramInboundInput(BaseModel):
    """Input para mensagens inbound do Telegram."""
    telegram_user_id: str
    chat_id: str
    message: str
    message_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class SystemProfileRefreshInput(BaseModel):
    """Input para refresh do system profile."""
    force: bool = False


class SoulInput(BaseModel):
    """Input para atualização do soul."""
    data: Dict[str, Any]


class SoulEventInput(BaseModel):
    """Input para adicionar evento ao soul."""
    content: str
    source: Optional[str] = None


class FeedbackInput(BaseModel):
    """Input para feedback de mensagem."""
    message_id: int
    rating: int


class PlanApproveInput(BaseModel):
    """Input para aprovação de plano."""
    conversation_id: int
    tasks: List[Dict[str, Any]]


class PlanTaskStatusInput(BaseModel):
    """Input para atualização de status de tarefa."""
    status: str
    conversation_id: Optional[int] = None


class OrchestrationStartInput(BaseModel):
    """Input para iniciar orquestração."""
    auto_approve: bool = False


class ConnectorSecretInput(BaseModel):
    """Input para atualizar secret de conector."""
    secret_ciphertext: str


# Registro de entregas (movido de main_auth.py para evitar import circular)
delivery_registry: Dict[str, Dict[str, Any]] = {}

# Cache do mapa do sistema (movido de main_auth.py para evitar import circular)
_system_map_cache: Dict[str, Any] = {"ascii": "", "generated_at": ""}

# Registro de comandos pendentes (movido de main_auth.py para evitar import circular)
pending_command_registry: Dict[str, Dict[str, Any]] = {}

# Registro de artefatos (movido de main_auth.py para evitar import circular)
artifact_registry: Dict[str, Dict[str, Any]] = {}

# Armazenamento de sessões WebSocket (movido de main_auth.py para evitar import circular)
from fastapi import WebSocket
active_connections: Dict[str, WebSocket] = {}


from .db import get_user_connector_secret_ciphertext, get_user_security_settings

security = HTTPBearer()
security_optional = HTTPBearer(auto_error=False)

SECURITY_SETTINGS_DEFAULT: Dict[str, Any] = {
    "sandbox": False,
    "allow_os_commands": True,
    "allow_file_write": True,
    "allow_web_retrieval": True,
    "allow_connectors": True,
    "allow_system_profile": True,
}


def _safe_security_settings(inp: Dict[str, Any]) -> Dict[str, Any]:
    raw = inp or {}
    out = dict(SECURITY_SETTINGS_DEFAULT)
    for k in SECURITY_SETTINGS_DEFAULT.keys():
        v = raw.get(k, None)
        if v is None:
            continue
        out[k] = bool(v)
    if out.get("sandbox"):
        out["allow_os_commands"] = False
        out["allow_file_write"] = False
        out["allow_web_retrieval"] = False
        out["allow_connectors"] = False
        out["allow_system_profile"] = False
    return out


def _get_effective_security_settings(user_id: int) -> Dict[str, Any]:
    stored = get_user_security_settings(int(user_id)) or {}
    settings = _safe_security_settings((stored or {}).get("settings") or {})
    return {
        **settings,
        "updated_at": (stored or {}).get("updated_at"),
    }


_DPAPI_ENTROPY = b"OpenSlapApiKey-v1"
_SECRETS_FILE_KEY = "OPENSLAP_SECRETS_KEY"
_SECRETS_FILE_NAME = ".secrets_key"


class _DataBlob(ctypes.Structure):
    _fields_ = [
        ("cbData", ctypes.c_uint32),
        ("pbData", ctypes.POINTER(ctypes.c_byte)),
    ]


def _bytes_to_blob(data: bytes) -> _DataBlob:
    buf = ctypes.create_string_buffer(data)
    return _DataBlob(len(data), ctypes.cast(buf, ctypes.POINTER(ctypes.c_byte)))


def _blob_to_bytes(blob: _DataBlob) -> bytes:
    if not blob.pbData:
        return b""
    return ctypes.string_at(blob.pbData, blob.cbData)


def _load_or_create_secrets_key() -> bytes:
    env_key = str(os.getenv(_SECRETS_FILE_KEY) or "").strip()
    if env_key:
        try:
            key_bytes = env_key.encode("ascii")
            Fernet(key_bytes)
            return key_bytes
        except Exception:
            pass
    secret_file = Path(os.path.expanduser("~")).resolve() / "OpenSlap" / _SECRETS_FILE_NAME
    try:
        secret_file.parent.mkdir(parents=True, exist_ok=True)
        if secret_file.exists():
            raw = secret_file.read_text(encoding="utf-8").strip()
            if raw:
                try:
                    key_bytes = raw.encode("ascii")
                    Fernet(key_bytes)
                    return key_bytes
                except Exception:
                    pass
        created = Fernet.generate_key()
        secret_file.write_text(created.decode("ascii"), encoding="utf-8")
        return created
    except Exception:
        return Fernet.generate_key()


_FERNET = Fernet(_load_or_create_secrets_key())


def _dpapi_protect_text(value: str) -> str:
    plaintext = (value or "").encode("utf-8")
    if not plaintext:
        raise HTTPException(status_code=400, detail="Chave vazia.")
    
    if sys.platform != "win32":
        token = _FERNET.encrypt(plaintext).decode("ascii")
        return f"fernet:{token}"

    import ctypes
    in_blob = _bytes_to_blob(plaintext)
    entropy_blob = _bytes_to_blob(_DPAPI_ENTROPY)
    out_blob = _DataBlob()

    ok = ctypes.windll.crypt32.CryptProtectData(
        ctypes.byref(in_blob),
        None,
        ctypes.byref(entropy_blob),
        None,
        None,
        0,
        ctypes.byref(out_blob),
    )
    if not ok:
        raise HTTPException(
            status_code=500, detail="Falha ao proteger a chave (DPAPI)."
        )

    try:
        protected = _blob_to_bytes(out_blob)
    finally:
        if out_blob.pbData:
            ctypes.windll.kernel32.LocalFree(out_blob.pbData)

    return base64.b64encode(protected).decode("ascii")


def _dpapi_unprotect_text(ciphertext_b64: str) -> Optional[str]:
    raw = (ciphertext_b64 or "").strip()
    if not raw:
        return None
    if raw.startswith("fernet:"):
        token = raw.split(":", 1)[-1].strip()
        if not token:
            return None
        try:
            plaintext = _FERNET.decrypt(token.encode("ascii"))
            return plaintext.decode("utf-8")
        except (InvalidToken, Exception):
            return None
    if sys.platform != "win32":
        return None
    try:
        protected = base64.b64decode(raw.encode("ascii"), validate=False)
    except Exception:
        return None

    in_blob = _bytes_to_blob(protected)
    entropy_blob = _bytes_to_blob(_DPAPI_ENTROPY)
    out_blob = _DataBlob()

    ok = ctypes.windll.crypt32.CryptUnprotectData(
        ctypes.byref(in_blob),
        None,
        ctypes.byref(entropy_blob),
        None,
        None,
        0,
        ctypes.byref(out_blob),
    )
    if not ok:
        return None

    try:
        plaintext = _blob_to_bytes(out_blob)
    finally:
        if out_blob.pbData:
            ctypes.windll.kernel32.LocalFree(out_blob.pbData)

    try:
        return plaintext.decode("utf-8")
    except Exception:
        return None


def _sanitize_api_key(v: str) -> str:
    s = str(v or "").strip()
    if (
        (s.startswith("`") and s.endswith("`"))
        or (s.startswith('"') and s.endswith('"'))
        or (s.startswith("'") and s.endswith("'"))
    ):
        s = s[1:-1].strip()
    s = s.strip()
    if s.lower().startswith("authorization:"):
        s = s.split(":", 1)[-1].strip()
    if s.lower().startswith("bearer "):
        s = s.split(None, 1)[-1].strip()
    if "," in s:
        parts = [p.strip() for p in s.split(",") if p.strip()]
        if parts:
            s = parts[0]
    s = s.strip(" ,")
    s = "".join(s.split())
    return s


def _get_user_connector_secret(user_id: int, connector_key: str) -> Optional[str]:
    ct = get_user_connector_secret_ciphertext(int(user_id), str(connector_key or "").strip())
    if not ct:
        return None
    raw = _dpapi_unprotect_text(ct) or ""
    secret = _sanitize_api_key(raw)
    return secret or None


def _get_user_connector_secret_raw(user_id: int, connector_key: str) -> Optional[str]:
    ct = get_user_connector_secret_ciphertext(int(user_id), str(connector_key or "").strip())
    if not ct:
        return None
    raw = (_dpapi_unprotect_text(ct) or "").strip()
    return raw or None


def _ensure_connectors_allowed(user_id: int) -> None:
    sec = _get_effective_security_settings(int(user_id))
    if sec.get("sandbox") or not sec.get("allow_connectors"):
        raise HTTPException(
            status_code=403, detail="Conectores desabilitados nas permissões."
        )

def _get_env_api_key_for_provider(provider_id: str) -> Optional[str]:
    p = str(provider_id or "").strip().lower()
    if not p:
        return None
    if p == "openai":
        key = _sanitize_api_key(os.getenv("OPENAI_API_KEY") or "")
        return key or None
    if p == "openrouter":
        key = _sanitize_api_key(os.getenv("OPENROUTER_API_KEY") or "")
        return key or None
    if p == "groq":
        raw = str(os.getenv("GROQ_API_KEYS") or "").strip()
        first = raw.split(",", 1)[0] if raw else ""
        key = _sanitize_api_key(first)
        return key or None
    if p == "gemini":
        raw = str(os.getenv("GEMINI_API_KEYS") or "").strip()
        first = raw.split(",", 1)[0] if raw else ""
        key = _sanitize_api_key(first)
        return key or None
    return None


def _infer_env_provider() -> Optional[str]:
    order_raw = str(os.getenv("PROVIDER_ORDER") or "").strip()
    default_order = ["gemini", "groq", "openai", "openrouter"]
    order = (
        [p.strip().lower() for p in order_raw.split(",") if p.strip()]
        if order_raw
        else default_order
    )
    for p in order:
        if p == "ollama":
            continue
        if _get_env_api_key_for_provider(p):
            return p
    for p in ["openai", "groq", "gemini", "openrouter"]:
        if _get_env_api_key_for_provider(p):
            return p
    return None
