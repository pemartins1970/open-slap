import base64
import ctypes
import os
import sys
from typing import Any, Dict, Optional

from fastapi import HTTPException
from fastapi.security import HTTPBearer

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


def _dpapi_protect_text(value: str) -> str:
    if sys.platform != "win32":
        raise HTTPException(
            status_code=400,
            detail="Armazenamento seguro de chave só está disponível no Windows.",
        )
    plaintext = (value or "").encode("utf-8")
    if not plaintext:
        raise HTTPException(status_code=400, detail="Chave vazia.")

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
    if sys.platform != "win32":
        return None
    raw = (ciphertext_b64 or "").strip()
    if not raw:
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
