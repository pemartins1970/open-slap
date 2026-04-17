"""
Utilitários para LLM Manager
"""

from typing import Any


def sanitize_text(v: Any) -> str:
    """Sanitiza texto removendo aspas e espaços"""
    s = str(v or "").strip()
    if (
        (s.startswith("`") and s.endswith("`"))
        or (s.startswith('"') and s.endswith('"'))
        or (s.startswith("'") and s.endswith("'"))
    ):
        s = s[1:-1].strip()
    s = s.strip(" ,")
    return s


def sanitize_api_key(v: Any) -> str:
    """Sanitiza chave API removendo espaços"""
    s = sanitize_text(v)
    return "".join(s.split())


def sanitize_url_base(v: Any) -> str:
    """Sanitiza URL base removendo barra final"""
    return sanitize_text(v).rstrip("/")


def normalize_openai_compatible_base_url(v: Any) -> str:
    """Normaliza URL base compatível com OpenAI"""
    base = sanitize_url_base(v)
    if not base:
        return base
    for suffix in ("/chat/completions", "/models"):
        if base.endswith(suffix):
            base = base[: -len(suffix)].rstrip("/")
    return base


def normalize_ollama_url(v: Any) -> str:
    """Normaliza URL do Ollama"""
    base = sanitize_url_base(v)
    if not base:
        return base
    for suffix in (
        "/api/generate",
        "/api/chat",
        "/api/tags",
        "/v1",
        "/api",
        "/openai/v1",
    ):
        if base.endswith(suffix):
            base = base[: -len(suffix)].rstrip("/")
    return base


def normalize_model_name(value: str) -> str:
    """Normaliza nome do modelo"""
    v = str(value or "").strip()
    v = v.strip("`\"' ,")
    if v.startswith("models/"):
        v = v.split("/", 1)[1]
    return v


def normalize_gemini_base_url(value: str) -> str:
    """Normaliza URL base do Gemini"""
    v = str(value or "").strip()
    v = v.strip("`\"' ,").rstrip("/")
    if v.endswith("/v1beta"):
        v = v[:-6].rstrip("/")
    elif not v.endswith("/v1"):
        v = f"{v.rstrip('/')}/v1"
    return v


def alternate_gemini_base_urls(value: str) -> list[str]:
    """Gera URLs alternativas para Gemini"""
    v = normalize_gemini_base_url(value)
    if v.endswith("/v1beta"):
        return [v[:-6] + "v1", v]
    elif v.endswith("/v1"):
        return [v, v[:-2] + "v1beta"]
    return [v]
