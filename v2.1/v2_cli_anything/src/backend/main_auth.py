"""
🚀 MAIN AUTH - Backend com Autenticação e Persistência
"""

import os
import json
import plistlib
import asyncio
import uuid
import hashlib
import platform
import sys
import re
import mimetypes
import base64
import ctypes
import subprocess
import secrets
import time
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List

from pathlib import Path
from dotenv import load_dotenv

from urllib.parse import urlparse

mimetypes.init()
mimetypes.add_type("application/javascript", ".js", strict=True)
mimetypes.add_type("application/javascript", ".mjs", strict=True)
mimetypes.add_type("text/css", ".css", strict=True)
mimetypes.types_map[".js"] = "application/javascript"
mimetypes.types_map[".mjs"] = "application/javascript"
mimetypes.types_map[".css"] = "text/css"
mimetypes.common_types[".js"] = "application/javascript"
mimetypes.common_types[".mjs"] = "application/javascript"
mimetypes.common_types[".css"] = "text/css"

from fastapi import (
    FastAPI,
    HTTPException,
    status,
    Depends,
    WebSocket,
    WebSocketDisconnect,
    BackgroundTasks,
    Query,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
import aiohttp
import sqlite3

BASE_DIR = Path(__file__).resolve().parents[1]
load_dotenv(dotenv_path=BASE_DIR / ".env", override=False)
logger = logging.getLogger(__name__)

if sys.platform == "win32":
    try:
        _pol = getattr(asyncio, "WindowsProactorEventLoopPolicy", None)
        if _pol:
            asyncio.set_event_loop_policy(_pol())
    except Exception:
        pass

# Importar módulos locais
from .auth import (
    create_user,
    authenticate_user,
    create_access_token,
    verify_token,
    get_current_user,
    create_password_reset,
    confirm_password_reset,
)
from .db import (
    create_conversation,
    get_user_conversations,
    get_conversation_messages,
    get_message,
    save_message,
    delete_conversation,
    get_conversation_by_session_for_user,
    update_conversation_title,
    search_user_messages,
    add_task_todo,
    list_task_todos,
    list_pending_todos,
    update_task_todo,
    get_task_todo,
    get_user_skills,
    upsert_user_skills,
    upsert_message_feedback,
    get_message_feedback,
    create_plan_tasks,
    get_plan_tasks,
    update_plan_task_status,
    create_project,
    get_user_projects,
    get_project,
    update_project_context,
    update_project_name,
    delete_project,
    set_conversation_project,
    decay_memory,
    reinforce_memory_usage,
    prune_low_salience_memories,
    get_consolidated_memory_snapshot,
    get_db_path,
    record_expert_rating,
    get_expert_rating_summary,
    get_message_with_preceding_user_message,
    create_orchestration_run,
    update_orchestration_run,
    get_orchestration_run,
    create_friction_event,
    list_friction_events,
    count_pending_friction_events,
    mark_friction_event_sent,
    delete_friction_event,
    upsert_user_llm_settings,
    get_user_llm_settings,
    upsert_user_security_settings,
    get_user_security_settings,
    add_user_command_autoapprove,
    list_user_command_autoapprove,
    delete_user_command_autoapprove,
    add_conversation_cli_summary,
    has_conversation_cli_summary,
    upsert_user_api_key_ciphertext,
    get_user_api_key_ciphertext,
    delete_user_api_key,
    add_user_llm_provider_key_ciphertext,
    list_user_llm_provider_keys,
    get_active_user_llm_provider_key_ciphertext,
    set_active_user_llm_provider_key,
    delete_user_llm_provider_key,
    get_user_onboarding_completed,
    set_user_onboarding_completed,
    upsert_user_connector_secret_ciphertext,
    get_user_connector_secret_ciphertext,
    delete_user_connector_secret,
    list_user_connector_keys,
    create_telegram_link_code,
    consume_telegram_link_code,
    upsert_telegram_link,
    revoke_telegram_link,
    list_telegram_links,
    get_telegram_linked_user_id,
    upsert_user_system_profile,
    get_user_system_profile,
    update_user_system_profile_data,
    delete_user_system_profile,
    upsert_system_kv_cache,
    get_system_kv_cache,
    upsert_user_soul,
    get_user_soul,
    append_soul_event,
    set_soul_event_salience,
    list_soul_events,
    list_imported_soul_events,
    set_soul_event_pinned,
    delete_imported_soul_event,
    get_cached_answer,
    put_cached_answer,
    search_user_memory,
    log_cli_command,
)
from .forge_harnesses import discover_harnesses, build_harnesses_context_block
from .runtime import llm_manager, moe_router
from .cli_bridge import (
    parse_cli_command_text,
    build_dynamic_whitelist,
    _sanitize_text,
    _is_safe_token,
    _is_safe_param_key,
    _safe_str_value,
    _collect_artifacts,
)
from .padxml import normalize_padxml, validate_padxml_v1
from .deps import (
    SECURITY_SETTINGS_DEFAULT,
    _dpapi_protect_text,
    _dpapi_unprotect_text,
    _ensure_connectors_allowed,
    _get_effective_security_settings,
    _get_user_connector_secret,
    _get_user_connector_secret_raw,
    _sanitize_api_key,
    security,
    security_optional,
)
from .routes.connectors_settings import router as connectors_settings_router
from .routes.conversations_tasks import router as conversations_tasks_router
from .routes.settings import router as settings_router
from .routes.autoapprove import router as autoapprove_router
from .routes.meta import router as meta_router

# Configurações
app = FastAPI(title="Agêntico Backend", version="1.0.0")

MEDIA_DIR = BASE_DIR.parent / "media"
MEDIA_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/media", StaticFiles(directory=str(MEDIA_DIR)), name="media")

DEFAULT_WORKDIR = Path(
    (os.getenv("OPENSLAP_WORKDIR") or "").strip()
    or str(Path(os.path.expanduser("~")) / "OpenSlap" / "Workspace")
).resolve()
try:
    DEFAULT_WORKDIR.mkdir(parents=True, exist_ok=True)
except Exception:
    DEFAULT_WORKDIR = MEDIA_DIR


def _ensure_workdir_ready() -> Optional[str]:
    try:
        p = Path(DEFAULT_WORKDIR)
        p.mkdir(parents=True, exist_ok=True)
        t = p / f".writetest_{uuid.uuid4().hex[:8]}"
        t.write_text("ok", encoding="utf-8")
        t2 = p / f".writetest_{uuid.uuid4().hex[:8]}.py"
        t2.write_text("print('ok')\n", encoding="utf-8")
        try:
            t.unlink()
        except Exception:
            pass
        try:
            t2.unlink()
        except Exception:
            pass
        return None
    except Exception as e:
        return str(e)


_workdir_err = _ensure_workdir_ready()
if _workdir_err:
    try:
        DEFAULT_WORKDIR = (MEDIA_DIR / "workspace").resolve()
        DEFAULT_WORKDIR.mkdir(parents=True, exist_ok=True)
    except Exception:
        DEFAULT_WORKDIR = MEDIA_DIR


def _env_flag(v: Optional[str], default: bool = False) -> bool:
    s = str(v if v is not None else ("1" if default else "0")).strip().lower()
    return s in ("1", "true", "yes", "on")


def _env_int(v: Optional[str], default: int) -> int:
    try:
        return (
            int(str(v or "").strip()) if v is not None and str(v).strip() else default
        )
    except Exception:
        return default


def _env_float(v: Optional[str], default: float) -> float:
    try:
        return (
            float(str(v or "").strip()) if v is not None and str(v).strip() else default
        )
    except Exception:
        return default


def _env_list(v: Optional[str]) -> List[str]:
    raw = str(v or "").strip()
    if not raw:
        return []
    parts = [p.strip() for p in raw.split(",")]
    return [p for p in parts if p]


class Settings:
    def __init__(self):
        self.enable_web_retrieval = _env_flag(
            os.getenv("OPENSLAP_WEB_RETRIEVAL"), False
        )
        self.web_retrieval_timeout_s = _env_float(
            os.getenv("OPENSLAP_WEB_RETRIEVAL_TIMEOUT_S"), 6.0
        )
        self.enable_url_fetch = _env_flag(os.getenv("OPENSLAP_URL_FETCH"), True)
        self.url_fetch_timeout_s = _env_float(
            os.getenv("OPENSLAP_URL_FETCH_TIMEOUT_S"), 8.0
        )
        self.url_fetch_max_chars = _env_int(
            os.getenv("OPENSLAP_URL_FETCH_MAX_CHARS"), 12000
        )
        self.url_fetch_allow_hosts = _env_list(
            os.getenv("OPENSLAP_URL_FETCH_ALLOW_HOSTS")
        )
        self.enable_cac = _env_flag(os.getenv("OPENSLAP_CAC"), True)
        self.cache_max_age_hours = _env_int(os.getenv("OPENSLAP_CAC_MAX_AGE_HOURS"), 24)
        self.enable_rag_sqlite = _env_flag(os.getenv("OPENSLAP_RAG_SQLITE"), True)
        self.enable_system_profile = _env_flag(
            os.getenv("OPENSLAP_SYSTEM_PROFILE"), True
        )
        self.attach_system_profile = _env_flag(
            os.getenv("OPENSLAP_ATTACH_SYSTEM_PROFILE"), True
        )
        self.system_profile_max_chars = _env_int(
            os.getenv("OPENSLAP_SYSTEM_PROFILE_MAX_CHARS"), 24000
        )
        self.enable_os_commands = _env_flag(os.getenv("OPENSLAP_OS_COMMANDS"), True)
        self.os_command_timeout_s = _env_int(
            os.getenv("OPENSLAP_OS_COMMAND_TIMEOUT_S"), 12
        )
        self.os_command_max_output_chars = _env_int(
            os.getenv("OPENSLAP_OS_COMMAND_MAX_OUTPUT_CHARS"), 12000
        )
        self.os_command_allowed_roots_raw = str(
            os.getenv("OPENSLAP_OS_COMMAND_ALLOWED_ROOTS") or ""
        ).strip()
        self.enable_external_software = _env_flag(
            os.getenv("OPENSLAP_EXTERNAL_SOFTWARE"), True
        )
        self.enable_agno_poc = _env_flag(os.getenv("OPENSLAP_USE_AGNO"), False)
        self.agno_db_file = str(os.getenv("OPENSLAP_AGNO_DB_FILE") or "").strip()
        self.cors_origins = _env_list(os.getenv("OPENSLAP_CORS_ORIGINS")) or [
            "http://localhost",
            "http://localhost:5173",
            "http://localhost:3000",
            "http://127.0.0.1:5173",
            "http://127.0.0.1:3000",
            "http://openslap.test",
        ]


settings = Settings()


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


def _extract_bearer_token_from_headers(headers: Dict[str, str]) -> Optional[str]:
    raw = (headers.get("authorization") or headers.get("Authorization") or "").strip()
    if not raw:
        return None
    if raw.lower().startswith("bearer "):
        token = raw[7:].strip()
        return token or None
    return None


def _is_public_path(path: str) -> bool:
    p = (path or "").strip()
    if not p:
        return False
    if p in PUBLIC_PATHS:
        return True
    return any(p.startswith(prefix) for prefix in PUBLIC_PATH_PREFIXES)


PROTECTED_PATHS = {"/auth/me"}
PROTECTED_PATH_PREFIXES = ("/api/", "/local/")


def _requires_auth(path: str) -> bool:
    p = (path or "").strip()
    if not p:
        return True
    if p in PROTECTED_PATHS:
        return True
    return any(p.startswith(prefix) for prefix in PROTECTED_PATH_PREFIXES)


class AuthRequiredMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.method.upper() == "OPTIONS":
            return await call_next(request)
        if _is_public_path(request.url.path) or not _requires_auth(request.url.path):
            return await call_next(request)
        token = _extract_bearer_token_from_headers(dict(request.headers))
        if not token:
            return JSONResponse(
                status_code=401, content={"detail": "Token não fornecido"}
            )
        user = get_current_user(token)
        if not user:
            return JSONResponse(status_code=401, content={"detail": "Token inválido"})
        request.state.current_user = user
        return await call_next(request)


app.add_middleware(AuthRequiredMiddleware)


@app.get("/media/{file_path:path}", include_in_schema=False)
async def _serve_media_direct(file_path: str):
    media_path = (MEDIA_DIR / file_path).resolve()
    try:
        if MEDIA_DIR.resolve() in media_path.parents and media_path.is_file():
            r = FileResponse(str(media_path))
            r.headers["Cache-Control"] = "no-store"
            r.headers["Pragma"] = "no-cache"
            return r
    except Exception:
        pass
    from fastapi import HTTPException

    raise HTTPException(status_code=404, detail="Arquivo não encontrado")


@app.get("/open_slap.png", include_in_schema=False)
async def _serve_root_open_slap_png():
    fname = "open_slap.png"
    p = (MEDIA_DIR / fname).resolve()
    if p.is_file():
        r = FileResponse(str(p))
        r.headers["Cache-Control"] = "no-store"
        r.headers["Pragma"] = "no-cache"
        return r
    dist_p = (BASE_DIR / "frontend" / "dist" / fname).resolve()
    if dist_p.is_file():
        r = FileResponse(str(dist_p))
        r.headers["Cache-Control"] = "no-store"
        r.headers["Pragma"] = "no-cache"
        return r
    raise HTTPException(status_code=404, detail="Arquivo não encontrado")


@app.get("/pemartins.jpg", include_in_schema=False)
async def _serve_root_pemartins_jpg():
    fname = "pemartins.jpg"
    p = (MEDIA_DIR / fname).resolve()
    if p.is_file():
        r = FileResponse(str(p))
        r.headers["Cache-Control"] = "no-store"
        r.headers["Pragma"] = "no-cache"
        return r
    dist_p = (BASE_DIR / "frontend" / "dist" / fname).resolve()
    if dist_p.is_file():
        r = FileResponse(str(dist_p))
        r.headers["Cache-Control"] = "no-store"
        r.headers["Pragma"] = "no-cache"
        return r
    raise HTTPException(status_code=404, detail="Arquivo não encontrado")


@app.get("/doacoes.txt", include_in_schema=False)
async def _serve_root_doacoes_txt():
    fname = "doacoes.txt"
    p = (MEDIA_DIR / fname).resolve()
    if p.is_file():
        r = FileResponse(str(p))
        r.headers["Cache-Control"] = "no-store"
        r.headers["Pragma"] = "no-cache"
        return r
    dist_p = (BASE_DIR / "frontend" / "dist" / fname).resolve()
    if dist_p.is_file():
        r = FileResponse(str(dist_p))
        r.headers["Cache-Control"] = "no-store"
        r.headers["Pragma"] = "no-cache"
        return r
    raise HTTPException(status_code=404, detail="Arquivo não encontrado")


@app.get("/btn_donateCC_LG.gif", include_in_schema=False)
async def _serve_root_btn_donate():
    fname = "btn_donateCC_LG.gif"
    p = (MEDIA_DIR / fname).resolve()
    if p.is_file():
        r = FileResponse(str(p))
        r.headers["Cache-Control"] = "no-store"
        r.headers["Pragma"] = "no-cache"
        return r
    dist_p = (BASE_DIR / "frontend" / "dist" / fname).resolve()
    if dist_p.is_file():
        r = FileResponse(str(dist_p))
        r.headers["Cache-Control"] = "no-store"
        r.headers["Pragma"] = "no-cache"
        return r
    raise HTTPException(status_code=404, detail="Arquivo não encontrado")


# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

# Segurança

# Componentes

# Armazenamento de sessões WebSocket
active_connections: Dict[str, WebSocket] = {}
delivery_registry: Dict[str, Dict[str, Any]] = {}
pending_command_registry: Dict[str, Dict[str, Any]] = {}
artifact_registry: Dict[str, Dict[str, Any]] = {}
DEFAULT_DELIVERIES_ROOT = os.path.join(os.path.expanduser("~"), "OpenSlap", "Entregas")
PROJECT_WIZARD_ID = "start_project_v1"
project_wizard_registry: Dict[int, Dict[str, Any]] = {}
ENABLE_WEB_RETRIEVAL = settings.enable_web_retrieval
WEB_RETRIEVAL_TIMEOUT_S = settings.web_retrieval_timeout_s
ENABLE_URL_FETCH = settings.enable_url_fetch
URL_FETCH_TIMEOUT_S = settings.url_fetch_timeout_s
URL_FETCH_MAX_CHARS = settings.url_fetch_max_chars
URL_FETCH_ALLOW_HOSTS = [str(x).strip().lower() for x in (settings.url_fetch_allow_hosts or []) if str(x).strip()]
ENABLE_CAC = settings.enable_cac
CACHE_MAX_AGE_HOURS = settings.cache_max_age_hours
ENABLE_RAG_SQLITE = settings.enable_rag_sqlite
ENABLE_SYSTEM_PROFILE = settings.enable_system_profile
ATTACH_SYSTEM_PROFILE = settings.attach_system_profile
SYSTEM_PROFILE_MAX_CHARS = settings.system_profile_max_chars
ENABLE_OS_COMMANDS = settings.enable_os_commands
OS_COMMAND_TIMEOUT_S = settings.os_command_timeout_s
OS_COMMAND_MAX_OUTPUT_CHARS = settings.os_command_max_output_chars
OS_COMMAND_ALLOWED_ROOTS_RAW = settings.os_command_allowed_roots_raw
ENABLE_EXTERNAL_SOFTWARE = settings.enable_external_software
FORGE_IDE_MODE = _env_flag(os.getenv("FORGE_IDE_MODE"), False)
FORGE_IDE_EMAIL = str(os.getenv("FORGE_IDE_EMAIL") or "forge@localhost").strip().lower()
FORGE_IDE_TOKEN_TTL_MINUTES = _env_int(os.getenv("FORGE_IDE_TOKEN_TTL_MINUTES"), 120)

_system_map_cache: Dict[str, Any] = {"ascii": "", "generated_at": ""}

def _generate_system_map_ascii() -> str:
    root = Path(str(BASE_DIR))
    target_dirs = [
        root / "frontend" / "src",
        root / "backend",
    ]
    ignore_dirs = {
        ".git",
        ".venv",
        "node_modules",
        "dist",
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        "media",
        ".trae",
    }

    def _tree(dir_path: Path, depth: int = 0, max_depth: int = 2) -> List[str]:
        if depth > max_depth:
            return []
        lines2: List[str] = []
        try:
            entries = sorted(
                list(dir_path.iterdir()),
                key=lambda p: (not p.is_dir(), p.name.lower()),
            )
        except Exception:
            return []
        filtered = [p for p in entries if p.name not in ignore_dirs]
        for i, p in enumerate(filtered):
            name = p.name
            is_last = i == (len(filtered) - 1)
            prefix = ("│  " * depth) + ("└─ " if is_last else "├─ ")
            if p.is_dir():
                lines2.append(f"{prefix}{name}/")
                lines2.extend(_tree(p, depth + 1, max_depth))
            else:
                lines2.append(f"{prefix}{name}")
        return lines2

    counts = {"py": 0, "js": 0, "ts": 0}
    for d in target_dirs:
        try:
            if not d.exists():
                continue
            for p in d.rglob("*"):
                if p.is_dir():
                    if p.name in ignore_dirs:
                        continue
                    continue
                suf = p.suffix.lower()
                if suf == ".py":
                    counts["py"] += 1
                elif suf == ".js":
                    counts["js"] += 1
                elif suf in {".ts", ".tsx"}:
                    counts["ts"] += 1
        except Exception:
            continue

    lines: List[str] = []
    lines.append("Open Slap! — Mapa do Sistema")
    lines.append("")
    lines.append("Arquivos (amostra):")
    lines.append(f"- backend: .py={counts['py']}")
    lines.append(f"- frontend: .js={counts['js']} .ts/.tsx={counts['ts']}")
    lines.append("")
    lines.append("Estrutura (parcial):")
    for d in target_dirs:
        try:
            rel = str(d.relative_to(root)).replace("\\", "/")
        except Exception:
            rel = str(d).replace("\\", "/")
        lines.append(rel + "/")
        lines.extend(_tree(d, depth=0, max_depth=2))
        lines.append("")
    lines.append("Fluxos principais:")
    lines.append("- Chat → WS → execução (software_operator) → resumo persistido → histórico")
    lines.append("- CTA 'Salvar informações' → /api/padxml/save_message → padxml.db → leitura via API")
    lines.append("- Permissões de comando → 'apenas agora' ou 'automaticamente' (revogável)")
    return "\n".join(lines).strip() + "\n"


def _strip_assistant_directives(text: str) -> str:
    s = (text or "").strip()
    if not s:
        return ""
    s = re.sub(r"\[\[assistant_split(?::\d{1,5})?\]\]", "", s, flags=re.IGNORECASE)
    s = re.sub(r"\[\[open_settings:[a-z0-9_-]+\]\]", "", s, flags=re.IGNORECASE)
    s = re.sub(
        r"\[\[(?:set_expert|force_expert):[a-z0-9_-]+\]\]", "", s, flags=re.IGNORECASE
    )
    s = re.sub(r"\[\[clear_expert\]\]", "", s, flags=re.IGNORECASE)
    s = re.sub(r"\n{3,}", "\n\n", s).strip()
    return s


def _is_local_client(request: Request) -> bool:
    try:
        host = (request.client.host if request.client else "") or ""
    except Exception:
        host = ""
    host = str(host).strip().lower()
    if host in ("127.0.0.1", "localhost", "::1"):
        return True
    return False


def _ensure_forge_user() -> Dict[str, Any]:
    from .auth import auth_manager
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


def _build_ide_context_block(ide_ctx: Dict[str, Any]) -> str:
    if not isinstance(ide_ctx, dict) or not ide_ctx:
        return ""

    parts: List[str] = ["--- IDE context ---"]

    ws = ide_ctx.get("workspace") or {}
    if isinstance(ws, dict):
        name = str(ws.get("name") or "").strip()
        root = str(ws.get("rootPath") or ws.get("root") or "").strip()
        if name or root:
            parts.append(f"workspace: {name}".rstrip() if name else "workspace: (sem nome)")
        if root:
            parts.append(f"root: {root}")

    editor = ide_ctx.get("editor") or {}
    if isinstance(editor, dict):
        active_file = str(editor.get("activeFile") or "").strip()
        language = str(editor.get("languageId") or "").strip()
        selection = editor.get("selection") or {}
        if active_file:
            parts.append(f"activeFile: {active_file}" + (f" ({language})" if language else ""))
        if isinstance(selection, dict):
            s = selection.get("text")
            if isinstance(s, str) and s.strip():
                s2 = s.strip()
                if len(s2) > 1200:
                    s2 = s2[:1200].rstrip() + "…"
                parts.append("selection:\n" + s2)

    diag = ide_ctx.get("diagnostics")
    if isinstance(diag, list) and diag:
        parts.append(f"diagnostics_count: {len(diag)}")

    parts.append("--- End IDE context ---")
    return "\n".join(parts).strip()


def _is_project_wizard_start(internal_prompt: str) -> bool:
    return f"WIZARD_ID: {PROJECT_WIZARD_ID}" in (internal_prompt or "")


def _project_wizard_intro_and_first_question() -> str:
    intro = (
        "Para entender melhor o projeto, preciso te fazer algumas perguntas. "
        "Quanto mais detalhadas as respostas, melhor. Mas caso não saiba o que responder "
        "(e isso é normal, não fique intimidado), apenas diga que não sabe. Responda a seu tempo. "
        "Quando terminarmos, terei informações suficientes para organizar os grupos de trabalho."
    )
    q1 = "Pergunta 1 * Qual é o objetivo principal do projeto de tecnologia que você deseja iniciar?"
    return f"{intro}\n\n[[assistant_split:1200]]\n\n{q1}"


def _project_wizard_next_step_text(stage: str) -> str:
    if stage == "q2":
        return "Pergunta 2 * Quem é o público-alvo para este projeto?"
    if stage == "q3":
        return "Pergunta 3 * Existe um prazo específico para a conclusão do projeto?"
    if stage == "q4":
        return "Pergunta 4 * Há restrições técnicas, orçamentárias ou de recursos que precisamos considerar?"
    if stage == "q5":
        return "Pergunta 5 * O projeto envolverá integrações com sistemas externos ou dados sensíveis que precisamos proteger?"
    return ""


def _project_wizard_has_question(user_message: str) -> bool:
    msg = (user_message or "").strip()
    if not msg:
        return False
    if "?" in msg:
        return True
    lower = msg.lower()
    starters = (
        "como ",
        "o que ",
        "oq ",
        "por que",
        "pq ",
        "qual ",
        "quais ",
        "onde ",
        "quando ",
        "dúvida",
        "duvida",
    )
    return any(lower.startswith(s) for s in starters)


def _project_wizard_detect_blog_ambiguity(user_message: str) -> bool:
    lower = (user_message or "").lower()
    if "blog" not in lower:
        return False
    known = ("wordpress", "ghost", "medium", "substack", "blogger", "wix", "webflow")
    if any(k in lower for k in known):
        return False
    if any(
        k in lower
        for k in (
            "do zero",
            "do 0",
            "custom",
            "sob medida",
            "próprio",
            "proprio",
            "localmente",
        )
    ):
        return False
    return True


def _project_wizard_handle_message(
    *,
    user_id: int,
    conversation_id: int,
    user_message: str,
    internal_prompt: str,
) -> Optional[Dict[str, Any]]:
    state = project_wizard_registry.get(int(conversation_id))
    if not state:
        if not _is_project_wizard_start(internal_prompt):
            return None
        state = {
            "stage": "q1",
            "answers": {},
            "asked_blog_clarify": False,
            "awaiting_summary_confirm": False,
        }
        project_wizard_registry[int(conversation_id)] = state
        content = _project_wizard_intro_and_first_question()
        return {"content": content, "done": False}

    if state.get("awaiting_summary_confirm"):
        lower = (user_message or "").strip().lower()
        if (
            lower
            in {
                "sim",
                "s",
                "confirmo",
                "confirmado",
                "ok",
                "certo",
                "perfeito",
                "isso",
                "isso mesmo",
            }
            or "sim" in lower
        ):
            try:
                _a = state.get("answers") or {}
                pieces = []
                if _a.get("q1"):
                    pieces.append(f"Objetivo: {_a.get('q1')}")
                if _a.get("blog_clarify"):
                    pieces.append(f"Abordagem do blog: {_a.get('blog_clarify')}")
                if _a.get("q2"):
                    pieces.append(f"Público-alvo: {_a.get('q2')}")
                if _a.get("q3"):
                    pieces.append(f"Prazo: {_a.get('q3')}")
                if _a.get("q4"):
                    pieces.append(f"Restrições: {_a.get('q4')}")
                if _a.get("q5"):
                    pieces.append(f"Integrações/dados sensíveis: {_a.get('q5')}")
                if pieces:
                    append_soul_event(
                        int(user_id), "project_wizard", " | ".join(pieces)[:900]
                    )
            except Exception:
                pass
            out = (
                "Perfeito. Tenho o conjunto mínimo de informações para prosseguirmos. "
                "Estou delegando este projeto ao seu CTO particular. Ele e sua equipe irão planejar, desenvolver "
                "e estruturar tudo. Eventualmente, por conta de nossas limitações e/ou ambiente, pode ser necessário "
                "que você auxilie no processo em atividades que não podemos fazer por você.\n\n"
                "[[set_expert:cto]]"
            )
            try:
                project_wizard_registry.pop(int(conversation_id), None)
            except Exception:
                pass
            return {"content": out, "done": True}
        return {
            "content": "Entendi. O que você quer ajustar ou corrigir no resumo?",
            "done": False,
        }

    stage = str(state.get("stage") or "q1")
    answers = state.get("answers") or {}
    answers[stage] = (user_message or "").strip()
    state["answers"] = answers

    if _project_wizard_has_question(user_message):
        answer_text = (
            "Entendi sua dúvida. Vou responder de forma prática conforme avançarmos, "
            "porque as próximas respostas (objetivo, público, prazo e restrições) impactam diretamente a recomendação."
        )
    else:
        answer_text = "Entendi. Anotado."

    if (
        stage == "q1"
        and _project_wizard_detect_blog_ambiguity(user_message)
        and not state.get("asked_blog_clarify")
    ):
        state["stage"] = "blog_clarify"
        state["asked_blog_clarify"] = True
        q = (
            "Entendi. Você precisa criar um blog. Seria um novo sistema de blog, que desenvolveríamos aqui, "
            "localmente, ou você apenas deseja ajuda para criar um blog em um dos diversos sistemas disponíveis "
            "na internet, e quer ajuda neste processo?"
        )
        return {
            "content": f"{answer_text}\n\n[[assistant_split:1200]]\n\n{q}",
            "done": False,
        }

    if stage == "blog_clarify":
        state["stage"] = "q2"
        q = _project_wizard_next_step_text("q2")
        return {
            "content": f"{answer_text}\n\n[[assistant_split:1200]]\n\n{q}",
            "done": False,
        }

    next_stage_map = {"q1": "q2", "q2": "q3", "q3": "q4", "q4": "q5"}
    if stage in next_stage_map:
        next_stage = next_stage_map[stage]
        state["stage"] = next_stage
        q = _project_wizard_next_step_text(next_stage)
        return {
            "content": f"{answer_text}\n\n[[assistant_split:1200]]\n\n{q}",
            "done": False,
        }

    if stage == "q5":
        state["awaiting_summary_confirm"] = True
        summary_lines = []
        if answers.get("q1"):
            summary_lines.append(f"- Objetivo: {answers.get('q1')}")
        if answers.get("blog_clarify"):
            summary_lines.append(f"- Abordagem do blog: {answers.get('blog_clarify')}")
        if answers.get("q2"):
            summary_lines.append(f"- Público-alvo: {answers.get('q2')}")
        if answers.get("q3"):
            summary_lines.append(f"- Prazo: {answers.get('q3')}")
        if answers.get("q4"):
            summary_lines.append(f"- Restrições: {answers.get('q4')}")
        if answers.get("q5"):
            summary_lines.append(f"- Integrações/dados sensíveis: {answers.get('q5')}")
        summary = (
            "\n".join(summary_lines)
            if summary_lines
            else "- (sem detalhes suficientes)"
        )
        out = (
            "Perfeito. Aqui está o que eu entendi até agora:\n"
            f"{summary}\n\n"
            "Confirma que está correto?"
        )
        return {"content": out, "done": False}

    state["stage"] = "q2"
    q = _project_wizard_next_step_text("q2")
    return {
        "content": f"{answer_text}\n\n[[assistant_split:1200]]\n\n{q}",
        "done": False,
    }


def _todo_items_from_user_message(user_message: str) -> List[str]:
    text = (user_message or "").strip()
    if not text:
        return []

    lines = [ln.strip() for ln in text.splitlines()]
    lines = [ln for ln in lines if ln]

    items: List[str] = []

    bullet_re = re.compile(r"^(\[\s*[xX]?\s*\]|[-*•]|\d+[.)])\s+(.*)$")
    bullet_hits = 0
    for ln in lines:
        m = bullet_re.match(ln)
        if not m:
            continue
        candidate = (m.group(2) or "").strip()
        if candidate:
            bullet_hits += 1
            items.append(candidate)

    if bullet_hits:
        deduped: List[str] = []
        seen = set()
        for it in items:
            one = " ".join(it.split()).strip()
            one = one[:240] if len(one) > 240 else one
            k = one.lower()
            if one and k not in seen:
                seen.add(k)
                deduped.append(one)
        return deduped

    lower = " ".join(text.lower().split())
    if any(
        k in lower
        for k in ("tarefas:", "tarefa:", "todo:", "to-do:", "pendências:", "pendencia:")
    ):
        parts = re.split(r"[;,]\s*|\s+\be\b\s+|\s+\bou\b\s+", text)
        for p in parts:
            p = p.strip()
            if not p:
                continue
            if ":" in p:
                p = p.split(":", 1)[1].strip()
            p = " ".join(p.split()).strip()
            if p:
                items.append(p[:240] if len(p) > 240 else p)

    if not items:
        try:
            if ":" in text and any(k in lower for k in ("tarefas", "todo", "to-do", "pendenc", "pendênc")):
                head, tail = text.split(":", 1)
                tail = (tail or "").strip()
                if tail and any(sep in tail for sep in (";", ",")):
                    parts = re.split(r"[;,]\s*|\s+\be\b\s+|\s+\bou\b\s+", tail)
                    for p in parts:
                        p = p.strip()
                        if not p:
                            continue
                        p = " ".join(p.split()).strip()
                        if p:
                            items.append(p[:240] if len(p) > 240 else p)
        except Exception:
            pass

    if not items:
        action_starts = (
            "comprar",
            "pagar",
            "agendar",
            "marcar",
            "enviar",
            "ligar",
            "resolver",
            "verificar",
            "atualizar",
            "preencher",
            "finalizar",
            "revisar",
            "estudar",
        )
        implied = (
            "preciso",
            "tenho que",
            "devo",
            "não esquecer",
            "nao esquecer",
            "lembrar",
            "me lembre",
        )
        compact = " ".join(text.split()).strip()
        compact_lower = compact.lower()
        if compact_lower.startswith(action_starts):
            if 6 <= len(compact) <= 240:
                items.append(compact)
        elif any(k in compact_lower for k in implied):
            candidate = ""
            try:
                m = re.search(
                    r"\bpreciso de\b\s+(.*?)(?:\s+(?:pode|poderia)\b|\?|$)",
                    compact,
                    flags=re.IGNORECASE,
                )
                if m and (m.group(1) or "").strip():
                    candidate = (m.group(1) or "").strip()
            except Exception:
                candidate = ""
            if not candidate:
                try:
                    candidate = re.sub(
                        r"^[^a-z0-9áàâãéèêíìîóòôõúùûçñ]+",
                        "",
                        compact,
                        flags=re.IGNORECASE,
                    ).strip()
                    candidate = re.sub(
                        r"^(?:sabrina|sabina|oi|olá|ola)\s*[,!:.\-–—]*\s*",
                        "",
                        candidate,
                        flags=re.IGNORECASE,
                    ).strip()
                    candidate = re.sub(
                        r"^(?:eu\s+)?(?:preciso|tenho que|devo)\b\s*(?:de\b\s*)?",
                        "",
                        candidate,
                        flags=re.IGNORECASE,
                    ).strip()
                    candidate = re.sub(
                        r"\s*(?:pode|poderia)\s+.*$",
                        "",
                        candidate,
                        flags=re.IGNORECASE,
                    ).strip()
                    candidate = candidate.strip(" .!?")
                except Exception:
                    candidate = ""
            candidate = " ".join(candidate.split()).strip()
            if candidate and 6 <= len(candidate) <= 240:
                if not re.match(
                    r"^(?:comprar|pagar|agendar|marcar|enviar|ligar|resolver|verificar|atualizar|preencher|finalizar|revisar|estudar)\b",
                    candidate,
                    flags=re.IGNORECASE,
                ):
                    candidate = candidate[:1].upper() + candidate[1:]
                if len(candidate) > 140:
                    candidate = candidate[:140].rstrip(" .!?") + "…"
                items.append(candidate)

    out: List[str] = []
    seen = set()
    for it in items:
        one = " ".join(it.split()).strip()
        one = one[:240] if len(one) > 240 else one
        k = one.lower()
        if one and k not in seen:
            seen.add(k)
            out.append(one)
    return out


def _looks_like_personal_todo_capture(user_message: str) -> bool:
    lower = " ".join(str(user_message or "").lower().split()).strip()
    if not lower:
        return False
    if "tarefas pessoais" in lower or "minhas tarefas pessoais" in lower:
        return True
    if "transforme em todos" in lower or "transformar em todos" in lower:
        return True
    return False


def _get_or_create_task_inbox_id(user_id: int) -> int:
    inbox_session_id = f"task-inbox:{int(user_id)}"
    inbox = get_conversation_by_session_for_user(int(user_id), inbox_session_id)
    inbox_id = int(inbox["id"]) if inbox and inbox.get("id") else None
    if inbox_id:
        return inbox_id
    return int(
        create_conversation(int(user_id), inbox_session_id, "Inbox", kind="task")
    )


def _record_activity_done(user_id: int, text: str, *, task_conversation_id: Optional[int] = None) -> None:
    msg = " ".join(str(text or "").split()).strip()
    if not msg:
        return
    msg = msg[:520] if len(msg) > 520 else msg
    target_id = int(task_conversation_id) if task_conversation_id else _get_or_create_task_inbox_id(int(user_id))
    try:
        todo_id = add_task_todo(
            int(user_id),
            int(target_id),
            msg,
            kind="step",
            actor="agent",
            origin="assistant",
            scope=("project" if task_conversation_id else "personal"),
            priority="low",
        )
        update_task_todo(int(user_id), int(todo_id), status="done")
    except Exception:
        pass


# Modelos Pydantic
class UserRegister(BaseModel):
    email: str
    password: str


class UserLogin(BaseModel):
    email: str
    password: str


class PasswordResetRequest(BaseModel):
    email: str


class PasswordResetConfirm(BaseModel):
    email: str
    code: str
    new_password: str


class ChatMessage(BaseModel):
    content: str


class TelegramLinkConsumeInput(BaseModel):
    code: str
    telegram_user_id: str
    chat_id: str


class TelegramUnlinkInput(BaseModel):
    telegram_user_id: str
    chat_id: str


class TelegramInboundInput(BaseModel):
    telegram_user_id: str
    chat_id: str
    message: str
    message_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class SkillsUpdate(BaseModel):
    skills: List[Dict[str, Any]]


class FrictionReportInput(BaseModel):
    code: str
    layer: str
    action_attempted: str
    blocked_by: str
    session_id: str
    user_message: Optional[str] = None
    os: Optional[str] = None
    runtime: Optional[str] = None
    skill_active: Optional[str] = None
    connector_active: Optional[str] = None
    product: str = "open-slap"
    tier: str = "free"


class CommandExecuteInput(BaseModel):
    confirm: bool = False


class CommandPlanInput(BaseModel):
    command: str
    cwd: Optional[str] = None


def _split_semicolon_paths(s: str) -> List[str]:
    parts = []
    for p in (s or "").split(";"):
        v = p.strip()
        if v:
            parts.append(v)
    return parts


def _get_allowed_command_roots(*, user_id: int) -> List[str]:
    roots = [
        os.path.abspath(str(BASE_DIR)),
        os.path.abspath(DEFAULT_DELIVERIES_ROOT),
        os.path.abspath(os.path.join(DEFAULT_DELIVERIES_ROOT, str(user_id))),
    ]
    for extra in _split_semicolon_paths(OS_COMMAND_ALLOWED_ROOTS_RAW):
        roots.append(os.path.abspath(extra))
    uniq = []
    seen = set()
    for r in roots:
        k = r.lower()
        if k not in seen:
            seen.add(k)
            uniq.append(r)
    return uniq


def _is_under_allowed_roots(path: str, roots: List[str]) -> bool:
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


def _normalize_cwd(*, cwd: Optional[str], user_id: int) -> str:
    v = str(cwd or "").strip().strip("`\"' ,")
    if not v:
        return os.path.abspath(str(BASE_DIR))
    return os.path.abspath(v)

def _normalize_command_key(command: str) -> str:
    tokens = [t for t in re.split(r"\s+", str(command or "").strip()) if t]
    return " ".join(tokens).strip().lower()

def _is_user_autoapproved_command(*, user_id: int, command: str) -> bool:
    try:
        key = _normalize_command_key(command)
        if not key:
            return False
        items = list_user_command_autoapprove(int(user_id), limit=400) or []
        return key in set([str(x or "").strip().lower() for x in items if x])
    except Exception:
        return False


def _command_policy_evaluate(
    *, command: str, cwd: Optional[str], user_id: int
) -> Dict[str, Any]:
    cmd = str(command or "").strip()
    if not cmd:
        return {
            "allowed": False,
            "blocked_reason": "Comando vazio",
            "requires_confirmation": True,
            "risk_level": 3,
        }

    lower = cmd.lower()
    roots = _get_allowed_command_roots(user_id=user_id)
    eff_cwd = _normalize_cwd(cwd=cwd, user_id=user_id)
    cwd_ok = _is_under_allowed_roots(eff_cwd, roots)

    deny_patterns = [
        r"\bdiskpart\b",
        r"\bformat(?:-volume)?\b",
        r"\bbcdedit\b",
        r"\breg\s+delete\b",
        r"\bnetsh\s+advfirewall\s+set\b",
        r"\bshutdown\b",
        r"\brestart-computer\b",
        r"\bstop-computer\b",
        r"\bremove-item\b",
        r"\brmdir\b|\brd\b",
        r"\bdel\b|\berase\b",
        r"\bset-itemproperty\b|\bnew-itemproperty\b",
        r"\bstart-service\b|\bstop-service\b|\brestart-service\b",
        r"\bicacls\b|\btakeown\b",
    ]
    for pat in deny_patterns:
        if re.search(pat, lower):
            return {
                "allowed": False,
                "blocked_reason": "Comando potencialmente destrutivo (bloqueado por política).",
                "requires_confirmation": True,
                "risk_level": 3,
                "cwd": eff_cwd,
                "cwd_allowed": cwd_ok,
            }

    tokens = [t for t in re.split(r"\s+", cmd) if t]
    first = tokens[0].lower() if tokens else ""

    safe_cmds = {
        "whoami",
        "systeminfo",
        "ipconfig",
        "route",
        "netstat",
        "tasklist",
        "ver",
        "where",
        "ping",
        "tracert",
        "nslookup",
    }
    safe_ps_prefixes = ("get-", "test-", "resolve-")
    safe_ps_exact = {
        "get-process",
        "get-service",
        "get-ciminstance",
        "get-computerinfo",
        "get-netipconfiguration",
        "get-nettcpconnection",
        "get-netfirewallprofile",
        "get-mpcomputerstatus",
        "get-mpthreat",
        "get-winevent",
        "invoke-webrequest",
    }

    looks_read_only = False
    if first in safe_cmds:
        looks_read_only = True
    if first in safe_ps_exact or any(first.startswith(p) for p in safe_ps_prefixes):
        looks_read_only = True

    has_redirection = bool(re.search(r"[<>]{1,2}|\|\s*out-file\b", lower))
    if looks_read_only and not has_redirection:
        return {
            "allowed": True,
            "blocked_reason": "",
            "requires_confirmation": False,
            "risk_level": 0,
            "cwd": eff_cwd,
            "cwd_allowed": cwd_ok,
            "allowed_roots": roots,
        }

    # Heurística: scripts Python temporários gerados pelo agente apenas para leitura (HTTP GET)
    # Ex.: python C:\...\media\workspace\temp_tool_*.py
    if first in {"python", "python3", "py"} and "temp_tool_" in lower and ".py" in lower:
        try:
            # Extrair caminho do script
            script_path = None
            for t in tokens[1:]:
                if t.lower().endswith(".py"):
                    script_path = t.strip().strip('"\''",")
                    break
            if script_path:
                sp = Path(script_path)
                if sp.exists() and sp.is_file():
                    # Ler com limite de tamanho
                    text = sp.read_text(encoding="utf-8", errors="ignore")
                    lt = text.lower()
                    # Critérios de leitura segura:
                    # - Usa apenas GET/consulta web; não faz escrita em disco nem subprocessos
                    web_reads = any(
                        pat in lt
                        for pat in [
                            "requests.get(",
                            "urllib.request.urlopen(",
                            "http.client",
                            "aiohttp",
                        ]
                    ) and re.search(r"https?://", lt) is not None
                    no_writes = all(
                        kw not in lt
                        for kw in [
                            "open(",
                            ".write(",
                            "os.remove(",
                            "shutil.",
                            "subprocess",
                            "psutil",
                            "winreg",
                        ]
                    )
                    no_shell = ("os.system(" not in lt) and ("Popen(" not in lt)
                    if web_reads and no_writes and no_shell and not has_redirection:
                        return {
                            "allowed": True,
                            "blocked_reason": "",
                            "requires_confirmation": False,
                            "risk_level": 0,
                            "cwd": eff_cwd,
                            "cwd_allowed": cwd_ok,
                            "allowed_roots": roots,
                        }
        except Exception:
            pass

    if not cwd_ok:
        return {
            "allowed": False,
            "blocked_reason": "Diretório de execução fora das pastas permitidas.",
            "requires_confirmation": True,
            "risk_level": 2,
            "cwd": eff_cwd,
            "cwd_allowed": cwd_ok,
            "allowed_roots": roots,
        }

    if _is_user_autoapproved_command(user_id=int(user_id), command=cmd):
        return {
            "allowed": True,
            "blocked_reason": "",
            "requires_confirmation": False,
            "risk_level": 0,
            "auto_approved": True,
            "cwd": eff_cwd,
            "cwd_allowed": cwd_ok,
            "allowed_roots": roots,
        }

    return {
        "allowed": True,
        "blocked_reason": "",
        "requires_confirmation": True,
        "risk_level": 1,
        "cwd": eff_cwd,
        "cwd_allowed": cwd_ok,
        "allowed_roots": roots,
    }


async def _run_powershell_command(
    *, command: str, cwd: str, timeout_s: int
) -> Dict[str, Any]:
    started = datetime.utcnow()
    proc = await asyncio.create_subprocess_exec(
        "powershell",
        "-NoProfile",
        "-Command",
        command,
        cwd=cwd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        stdout_b, stderr_b = await asyncio.wait_for(
            proc.communicate(), timeout=max(1, int(timeout_s))
        )
    except asyncio.TimeoutError:
        try:
            proc.kill()
        except Exception:
            pass
        return {
            "ok": False,
            "exit_code": None,
            "stdout": "",
            "stderr": "Timeout ao executar comando.",
            "duration_ms": int((datetime.utcnow() - started).total_seconds() * 1000),
        }

    stdout = _decode_best_effort(stdout_b or b"").strip()
    stderr = _decode_best_effort(stderr_b or b"").strip()
    exit_code = int(proc.returncode) if proc.returncode is not None else None
    duration_ms = int((datetime.utcnow() - started).total_seconds() * 1000)

    combined = "\n".join([x for x in [stdout, stderr] if x]).strip()
    if combined and len(combined) > OS_COMMAND_MAX_OUTPUT_CHARS:
        combined = (
            combined[: OS_COMMAND_MAX_OUTPUT_CHARS - 1200].rstrip()
            + "\n\n[... saída truncada ...]"
        )

    ok = exit_code == 0 if exit_code is not None else False
    return {
        "ok": ok,
        "exit_code": exit_code,
        "output": combined,
        "stdout": stdout,
        "stderr": stderr,
        "duration_ms": duration_ms,
    }


def _extract_tagged_json_blocks(
    text: str, *, start_tag: str, end_tag: str
) -> List[Dict[str, Any]]:
    if not text:
        return []
    blocks: List[Dict[str, Any]] = []
    idx = 0
    while True:
        start = text.find(start_tag, idx)
        if start == -1:
            break
        end = text.find(end_tag, start + len(start_tag))
        if end == -1:
            break
        payload = text[start + len(start_tag) : end].strip()
        obj: Any = None
        try:
            obj = json.loads(payload) if payload else None
        except Exception:
            obj = None
        if isinstance(obj, dict):
            blocks.append(
                {
                    "start": start,
                    "end": end + len(end_tag),
                    "obj": obj,
                    "raw": payload,
                }
            )
        idx = end + len(end_tag)
    return blocks


async def _process_command_blocks(
    *,
    text: str,
    user_id: int,
    session_id: str,
    conversation_id: int,
) -> str:
    if not text:
        return text
    cmd_blocks = _extract_tagged_json_blocks(
        text, start_tag="<COMMAND_JSON>", end_tag="</COMMAND_JSON>"
    )
    if not cmd_blocks:
        return text
    sec = _get_effective_security_settings(int(user_id))

    out_parts: List[str] = []
    cursor = 0
    for b in cmd_blocks:
        out_parts.append(text[cursor : b["start"]])
        cursor = b["end"]

        obj = b.get("obj") or {}
        cmd = str(obj.get("command") or "").strip()
        cwd = str(obj.get("cwd") or "").strip()
        title = str(obj.get("title") or "").strip()
        intent = str(obj.get("intent") or "").strip()

        if not ENABLE_OS_COMMANDS:
            out_parts.append(
                "⚠️ Execução de comandos está desabilitada no servidor (OPENSLAP_OS_COMMANDS=0)."
            )
            continue
        if not sec.get("allow_os_commands"):
            out_parts.append(
                "⚠️ Execução de comandos está desabilitada nas permissões desta conta."
            )
            continue

        plan = _command_policy_evaluate(command=cmd, cwd=cwd, user_id=int(user_id))
        if not plan.get("allowed"):
            out_parts.append(
                f"❌ Comando bloqueado: {plan.get('blocked_reason') or 'não permitido'}"
            )
            continue

        if plan.get("requires_confirmation"):
            request_id = uuid.uuid4().hex[:16]
            pending_command_registry[request_id] = {
                "id": request_id,
                "user_id": int(user_id),
                "session_id": str(session_id),
                "conversation_id": int(conversation_id),
                "created_at": datetime.utcnow().isoformat(),
                "command": cmd,
                "cwd": plan.get("cwd"),
                "title": title,
                "intent": intent,
                "risk_level": int(plan.get("risk_level") or 1),
                "requires_confirmation": True,
            }
            pending_payload = {
                "id": request_id,
                "command": cmd,
                "cwd": plan.get("cwd"),
                "title": title,
                "intent": intent,
                "risk_level": int(plan.get("risk_level") or 1),
                "requires_confirmation": True,
            }
            out_parts.append("<COMMAND_REQUEST_JSON>")
            out_parts.append(json.dumps(pending_payload, ensure_ascii=False))
            out_parts.append("</COMMAND_REQUEST_JSON>")
            continue

        run_res = await _run_powershell_command(
            command=cmd,
            cwd=str(plan.get("cwd") or os.path.abspath(str(BASE_DIR))),
            timeout_s=OS_COMMAND_TIMEOUT_S,
        )
        prefix = f"✅ Comando executado{f' — {title}' if title else ''}:\n{cmd}"
        detail = run_res.get("output") or "(sem saída)"
        out_parts.append(f"{prefix}\n\n{detail}")

    out_parts.append(text[cursor:])
    return "".join(out_parts).strip()


def _extract_cli_output_fields(output_json: str) -> Dict[str, str]:
    stdout = ""
    stderr = ""
    try:
        out_obj = json.loads(str(output_json or "") or "{}")
        stdout = str(out_obj.get("stdout") or "")
        stderr = str(out_obj.get("stderr") or "")
    except Exception:
        stdout = ""
        stderr = ""
    return {"stdout": stdout, "stderr": stderr}


def _extract_cli_artifacts(output_json: str) -> List[Dict[str, Any]]:
    try:
        out_obj = json.loads(str(output_json or "") or "{}")
        arts = out_obj.get("artifacts") or []
        if isinstance(arts, list):
            out: List[Dict[str, Any]] = []
            for a in arts:
                if isinstance(a, dict):
                    out.append(a)
            return out
    except Exception:
        return []
    return []


def _register_cli_artifacts(artifacts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for a in artifacts or []:
        p = str((a or {}).get("path") or "").strip()
        if not p:
            continue
        try:
            fp = Path(p).resolve()
        except Exception:
            continue
        if not fp.is_file():
            continue
        artifact_id = uuid.uuid4().hex[:16]
        artifact_registry[artifact_id] = {"path": str(fp)}
        out.append(
            {
                "id": artifact_id,
                "name": fp.name,
                "path": str(fp),
                "size": int((a or {}).get("size") or 0),
                "mtime": int((a or {}).get("mtime") or 0),
                "url": f"/api/artifacts/{artifact_id}",
            }
        )
    if len(artifact_registry) > 250:
        try:
            for k in list(artifact_registry.keys())[:50]:
                artifact_registry.pop(k, None)
        except Exception:
            pass
    return out


async def _generate_software_operator_retry_command(
    *,
    error_text: str,
    expert: Dict[str, Any],
    llm_override: Optional[Dict[str, Any]],
    user_context: str,
) -> str:
    err = str(error_text or "").strip()
    if not err:
        err = "Erro não especificado."
    prompt = (
        f"O comando anterior falhou com este erro: {err}. "
        "Tente ajustar os parâmetros ou use um comando alternativo."
    )
    out = ""
    async for chunk in llm_manager.stream_generate(
        prompt,
        expert,
        user_context=user_context or "",
        llm_override=llm_override,
    ):
        if isinstance(chunk, str):
            out += chunk
    return str(out or "").strip()


async def _run_external_software_skill(
    *,
    command_text: str,
    user_id: int,
    conversation_id: int,
    sec: Dict[str, Any],
    expert: Dict[str, Any],
    llm_override: Optional[Dict[str, Any]] = None,
    user_context: str = "",
    websocket: Optional[WebSocket] = None,
) -> str:
    if not ENABLE_EXTERNAL_SOFTWARE:
        return "⚠️ External software skill desabilitada (OPENSLAP_EXTERNAL_SOFTWARE=0)."
    if sec.get("sandbox") or not sec.get("allow_os_commands"):
        return "⚠️ Execução de softwares externos está desabilitada nas permissões desta conta."

    execution_id = uuid.uuid4().hex[:16]

    async def _send_evt(payload: Dict[str, Any]) -> None:
        if not websocket:
            return
        try:
            await websocket.send_json(payload)
        except Exception:
            pass

    def _build_persisted_summary(*, res_obj: Dict[str, Any], stdout_text: str, stderr_text: str) -> str:
        vs = str(res_obj.get("visual_state_summary") or "").strip()
        if vs:
            return vs[:800]
        pick = (stdout_text or "").strip() or (stderr_text or "").strip()
        if not pick:
            return ""
        lines = [ln.strip() for ln in pick.splitlines() if ln.strip()]
        return "\n".join(lines[:6])[:800]

    async def _run_one_attempt(*, command_line: str, attempt: int) -> Dict[str, Any]:
        timeout_final = int(
            str(os.getenv("OPENSLAP_CLI_TIMEOUT_S") or "25").strip() or "25"
        )
        started_at_ms = int(time.time() * 1000)
        app_name, action, params = parse_cli_command_text(command_line or "")
        if not (app_name and action):
            err_payload = {
                "status": "error",
                "command_executed": str(command_line or "").strip(),
                "output": json.dumps(
                    {"stdout": "", "stderr": "Comando inválido."},
                    ensure_ascii=False,
                ),
                "visual_state_summary": "",
                "app_name": app_name or "",
                "action": action or "",
            }
            await _send_evt(
                {
                    "type": "software_operator",
                    "execution_id": execution_id,
                    "attempt": int(attempt),
                    "status": "error",
                    "command_executed": str(command_line or "").strip(),
                    "started_at_ms": started_at_ms,
                    "timeout_s": timeout_final,
                    "stdout": "",
                    "stderr": "Comando inválido.",
                    "visual_state_summary": "",
                    "artifacts": [],
                }
            )
            return err_payload

        await _send_evt(
            {
                "type": "software_operator",
                "execution_id": execution_id,
                "attempt": int(attempt),
                "status": "running",
                "command": str(command_line or "").strip(),
                "started_at_ms": started_at_ms,
                "timeout_s": timeout_final,
            }
        )
        _installed_sw = get_installed_software() if sys.platform == "win32" else []
        wl = build_dynamic_whitelist(_installed_sw)
        app_key = _sanitize_text(app_name)
        if app_key not in wl or not _is_safe_token(action):
            err_out = {
                "status": "error",
                "command_executed": str(command_line or "").strip(),
                "output": json.dumps({"stdout": "", "stderr": "Executável/ação inválidos."}, ensure_ascii=False),
                "visual_state_summary": "",
                "app_name": app_name or "",
                "action": action or "",
            }
            await _send_evt(
                {
                    "type": "software_operator",
                    "execution_id": execution_id,
                    "attempt": int(attempt),
                    "status": "error",
                    "command_executed": str(command_line or "").strip(),
                    "started_at_ms": started_at_ms,
                    "timeout_s": timeout_final,
                    "stdout": "",
                    "stderr": "Executável/ação inválidos.",
                    "visual_state_summary": "",
                    "artifacts": [],
                }
            )
            return err_out

        exe = _sanitize_text((wl.get(app_key) or {}).get("exe") or app_key)
        native_cmd = app_key in {"winget", "apt", "brew"}
        if native_cmd:
            args: List[str] = [exe, _sanitize_text(action)]
        else:
            args = [exe, "--action", _sanitize_text(action)]
        safe_params: Dict[str, Any] = {}
        cwd_dir: Optional[str] = None
        for k, v in (params or {}).items():
            key = _sanitize_text(k)
            if not _is_safe_param_key(key):
                continue
            if key == "cwd":
                sval = _safe_str_value(v)
                if sval:
                    try:
                        p = Path(sval).resolve()
                        if p.exists() and p.is_dir():
                            cwd_dir = str(p)
                    except Exception:
                        pass
                continue
            if v is True:
                args.append(f"--{key}")
                safe_params[key] = True
                continue
            if v in (False, None, ""):
                continue
            sval = _safe_str_value(v)
            if not sval:
                continue
            args.extend([f"--{key}", sval])
            safe_params[key] = sval

        if not cwd_dir:
            cwd_dir = str(DEFAULT_WORKDIR)

        if app_key == "winget":
            flags = {"--accept-source-agreements", "--accept-package-agreements"}
            present = set([a for a in args if a.startswith("--accept-")])
            for f in flags - present:
                args.append(f)
            if action == "install" and "--silent" not in args:
                args.append("--silent")
        if app_key == "apt":
            if action in {"install", "remove", "update", "upgrade"} and "-y" not in args and "--yes" not in args:
                args.append("-y")

        if app_key == "python-inline":
            if not sec.get("allow_file_write"):
                msg = "Escrita de arquivos está desabilitada nas permissões desta conta."
                await _send_evt(
                    {
                        "type": "software_operator",
                        "execution_id": execution_id,
                        "attempt": int(attempt),
                        "status": "error",
                        "started_at_ms": started_at_ms,
                        "timeout_s": timeout_final,
                        "stdout": "",
                        "stderr": msg,
                        "visual_state_summary": "",
                        "artifacts": [],
                    }
                )
                return {
                    "status": "error",
                    "command_executed": " ".join(args),
                    "output": json.dumps({"stdout": "", "stderr": msg}, ensure_ascii=False),
                    "visual_state_summary": "",
                    "app_name": app_name,
                    "action": action,
                }
            _built_in_py = {"vision_screen_text_boxes", "screenshot"}
            code_text = str((params or {}).get("code") or "").strip()
            if not code_text and str(action or "").strip().lower() in _built_in_py:
                out_name = str((params or {}).get("out") or "vision_analysis.png").strip()
                out_name = Path(out_name).name or "vision_analysis.png"
                if not out_name.lower().endswith(".png"):
                    out_name = f"{out_name}.png"
                code_text = f"""
import os
import sys
from mss import mss
from PIL import Image, ImageOps, ImageFilter, ImageChops, ImageDraw

ACTION = {json.dumps(str(action or '').strip().lower())}
OUT_NAME = {json.dumps(out_name)}

def _capture_screen():
    with mss() as sct:
        mon = sct.monitors[1] if len(sct.monitors) > 1 else sct.monitors[0]
        shot = sct.grab(mon)
        return Image.frombytes("RGB", (shot.width, shot.height), shot.rgb)

def _find_text_like_boxes(img):
    max_w = 960
    scale = 1.0
    if img.width > max_w:
        scale = max_w / float(img.width)
        img_s = img.resize((max(1, int(img.width * scale)), max(1, int(img.height * scale))), Image.BILINEAR)
    else:
        img_s = img
    gray = ImageOps.autocontrast(img_s.convert("L"))
    blur = gray.filter(ImageFilter.GaussianBlur(radius=1))
    diff = ImageOps.autocontrast(ImageChops.difference(gray, blur))
    mask = diff.point(lambda p: 255 if p > 35 else 0).convert("L")
    mask = mask.filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.MinFilter(5))
    w, h = mask.size
    data = mask.tobytes()
    visited = bytearray(w * h)
    boxes = []
    for idx in range(w * h):
        if visited[idx] or data[idx] == 0:
            continue
        stack = [idx]
        visited[idx] = 1
        x0 = x1 = idx % w
        y0 = y1 = idx // w
        area = 0
        while stack:
            i = stack.pop()
            area += 1
            x = i % w
            y = i // w
            if x < x0:
                x0 = x
            if x > x1:
                x1 = x
            if y < y0:
                y0 = y
            if y > y1:
                y1 = y
            if x > 0:
                j = i - 1
                if not visited[j] and data[j] != 0:
                    visited[j] = 1
                    stack.append(j)
            if x + 1 < w:
                j = i + 1
                if not visited[j] and data[j] != 0:
                    visited[j] = 1
                    stack.append(j)
            if y > 0:
                j = i - w
                if not visited[j] and data[j] != 0:
                    visited[j] = 1
                    stack.append(j)
            if y + 1 < h:
                j = i + w
                if not visited[j] and data[j] != 0:
                    visited[j] = 1
                    stack.append(j)
        bw = x1 - x0 + 1
        bh = y1 - y0 + 1
        if area < 50:
            continue
        if bw < 14 or bh < 10:
            continue
        if bw * bh > int(w * h * 0.25):
            continue
        boxes.append((x0, y0, x1, y1))

    def _overlaps(a, b, m):
        return not (a[2] + m < b[0] or b[2] + m < a[0] or a[3] + m < b[1] or b[3] + m < a[1])

    merged = []
    for b in boxes:
        placed = False
        for k in range(len(merged)):
            a = merged[k]
            if _overlaps(a, b, 6):
                merged[k] = (min(a[0], b[0]), min(a[1], b[1]), max(a[2], b[2]), max(a[3], b[3]))
                placed = True
                break
        if not placed:
            merged.append(b)

    inv = 1.0 / scale if scale != 0 else 1.0
    out = []
    for (x0, y0, x1, y1) in merged:
        out.append((int(x0 * inv), int(y0 * inv), int((x1 + 1) * inv), int((y1 + 1) * inv)))
    return out

def main():
    img = _capture_screen()
    if ACTION == "screenshot":
        img.save(OUT_NAME)
        print(OUT_NAME)
        return 0
    boxes = _find_text_like_boxes(img)
    draw = ImageDraw.Draw(img)
    for (x0, y0, x1, y1) in boxes:
        x0 = max(0, x0 - 4)
        y0 = max(0, y0 - 4)
        x1 = min(img.width - 1, x1 + 4)
        y1 = min(img.height - 1, y1 + 4)
        draw.rectangle([x0, y0, x1, y1], outline=(255, 0, 0), width=3)
    img.save(OUT_NAME)
    print(OUT_NAME)
    return 0

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as e:
        sys.stderr.write(str(e) + "\\n")
        raise
""".strip()

            if not code_text:
                msg = "Parâmetro --code ausente para python-inline."
                await _send_evt(
                    {
                        "type": "software_operator",
                        "execution_id": execution_id,
                        "attempt": int(attempt),
                        "status": "error",
                        "started_at_ms": started_at_ms,
                        "timeout_s": timeout_final,
                        "stdout": "",
                        "stderr": msg,
                        "visual_state_summary": "",
                        "artifacts": [],
                    }
                )
                return {
                    "status": "error",
                    "command_executed": " ".join(args),
                    "output": json.dumps({"stdout": "", "stderr": msg}, ensure_ascii=False),
                    "visual_state_summary": "",
                    "app_name": app_name,
                    "action": action,
                }
            try:
                base_dir = Path(cwd_dir or DEFAULT_WORKDIR)
                base_dir.mkdir(parents=True, exist_ok=True)
                tool_path = base_dir / f"temp_tool_{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')}.py"
                await _send_evt(
                    {
                        "type": "software_operator",
                        "execution_id": execution_id,
                        "attempt": int(attempt),
                        "status": "running",
                        "stdout_chunk": "[AUTO-BUILD] Criando ferramenta customizada para esta tarefa...\n",
                        "stderr_chunk": "",
                        "command": "autobuild:python-inline",
                        "started_at_ms": started_at_ms,
                        "timeout_s": timeout_final,
                    }
                )
                if (
                    "<DIR>" in code_text
                    or "<CWD>" in code_text
                    or "<WORKDIR>" in code_text
                    or "<OUTPUT>" in code_text
                    or "<OUT>" in code_text
                ):
                    repl = str(base_dir).replace("\\", "\\\\")
                    code_text = (
                        code_text.replace("<DIR>", repl)
                        .replace("<CWD>", repl)
                        .replace("<WORKDIR>", repl)
                        .replace("<OUTPUT>", repl)
                        .replace("<OUT>", repl)
                    )
                tool_path.write_text(code_text, encoding="utf-8", errors="ignore")
                exe_py = sys.executable or "python"
                args = [exe_py, str(tool_path)]
                cwd_dir = str(base_dir)
            except Exception as e:
                msg = f"Falha ao criar ferramenta temporária: {e}"
                await _send_evt(
                    {
                        "type": "software_operator",
                        "execution_id": execution_id,
                        "attempt": int(attempt),
                        "status": "error",
                        "started_at_ms": started_at_ms,
                        "timeout_s": timeout_final,
                        "stdout": "",
                        "stderr": msg,
                        "visual_state_summary": "",
                        "artifacts": [],
                    }
                )
                return {
                    "status": "error",
                    "command_executed": " ".join(args),
                    "output": json.dumps({"stdout": "", "stderr": msg}, ensure_ascii=False),
                    "visual_state_summary": "",
                    "app_name": app_name,
                    "action": action,
                }

        stdout_acc = []
        stderr_acc = []
        started = asyncio.get_event_loop().time()
        try:
            proc = await asyncio.create_subprocess_exec(
                *args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd_dir or None,
            )
        except NotImplementedError:
            loop = asyncio.get_event_loop()

            def _run_sync():
                try:
                    r = subprocess.run(
                        args,
                        capture_output=True,
                        text=True,
                        timeout=max(1, int(timeout_final)),
                        check=False,
                        cwd=cwd_dir or None,
                    )
                    return {
                        "timeout": False,
                        "returncode": int(r.returncode or 0),
                        "stdout": str(r.stdout or ""),
                        "stderr": str(r.stderr or ""),
                    }
                except subprocess.TimeoutExpired as e:
                    return {
                        "timeout": True,
                        "returncode": -1,
                        "stdout": str(getattr(e, "stdout", "") or ""),
                        "stderr": str(getattr(e, "stderr", "") or "")
                        + f"\nTimeout após {timeout_final}s\n",
                    }

            res_sync = await loop.run_in_executor(None, _run_sync)
            retcode = int(res_sync.get("returncode") or 0)
            status = "success" if retcode == 0 and not res_sync.get("timeout") else "error"
            full_stdout = str(res_sync.get("stdout") or "")[-8000:]
            full_stderr = str(res_sync.get("stderr") or "")[-8000:]

            artifacts_dir = (
                _safe_str_value((params or {}).get("artifacts_dir"))
                or _sanitize_text(os.getenv((wl.get(app_key) or {}).get("artifacts_env") or ""))
                or _sanitize_text(os.getenv("OPENSLAP_CLI_ARTIFACTS_DIR") or "")
            )
            if not artifacts_dir and app_key == "python-inline":
                artifacts_dir = _sanitize_text(cwd_dir or "") or _sanitize_text(
                    str(DEFAULT_WORKDIR)
                )
            arts_info = _collect_artifacts(artifacts_dir)
            visual_summary = _sanitize_text(arts_info.get("summary") or "")
            reg_artifacts = _register_cli_artifacts(arts_info.get("files") or [])

            await _send_evt(
                {
                    "type": "software_operator",
                    "execution_id": execution_id,
                    "attempt": int(attempt),
                    "status": status,
                    "command_executed": " ".join(args),
                    "started_at_ms": started_at_ms,
                    "timeout_s": timeout_final,
                    "return_ms": int(time.time() * 1000) - started_at_ms,
                    "stdout": full_stdout,
                    "stderr": full_stderr,
                    "visual_state_summary": visual_summary[:4000],
                    "artifacts": reg_artifacts,
                }
            )
            return {
                "status": status,
                "command_executed": " ".join(args),
                "output": json.dumps(
                    {
                        "stdout": full_stdout,
                        "stderr": full_stderr,
                        "return_ms": int(time.time() * 1000) - started_at_ms,
                        "params": safe_params,
                        "artifacts": arts_info.get("files") or [],
                    },
                    ensure_ascii=False,
                ),
                "visual_state_summary": visual_summary[:4000],
                "app_name": app_name,
                "action": action,
            }
        except FileNotFoundError:
            msg = f"Executável não encontrado: {exe}. Considere instalar via winget (ex.: winget install --id <PACKAGE_ID>)."
            await _send_evt(
                {
                    "type": "software_operator",
                    "execution_id": execution_id,
                    "attempt": int(attempt),
                    "status": "error",
                    "command_executed": " ".join(args),
                    "started_at_ms": started_at_ms,
                    "timeout_s": timeout_final,
                    "stdout": "",
                    "stderr": msg,
                    "visual_state_summary": "",
                    "artifacts": [],
                }
            )
            return {
                "status": "error",
                "command_executed": " ".join(args),
                "output": json.dumps({"stdout": "", "stderr": msg}, ensure_ascii=False),
                "visual_state_summary": "",
                "app_name": app_name,
                "action": action,
            }

        async def _read_stream(stream, is_err: bool):
            while True:
                try:
                    line = await asyncio.wait_for(stream.readline(), timeout=0.5)
                except asyncio.TimeoutError:
                    # periodic timeout to allow outer timeout check
                    line = None
                if line is None:
                    # no new data, continue loop to check timeout/returncode
                    if proc.returncode is not None:
                        break
                    continue
                if not line:
                    break
                text = line.decode(errors="ignore")
                if not text:
                    continue
                if is_err:
                    stderr_acc.append(text)
                else:
                    stdout_acc.append(text)
                try:
                    await _send_evt(
                        {
                            "type": "software_operator",
                            "execution_id": execution_id,
                            "attempt": int(attempt),
                            "status": "running",
                            "command": " ".join(args),
                            "started_at_ms": started_at_ms,
                            "timeout_s": timeout_final,
                            "elapsed_ms": int(time.time() * 1000) - started_at_ms,
                            "stdout_chunk": "" if is_err else text,
                            "stderr_chunk": text if is_err else "",
                        }
                    )
                except Exception:
                    pass

        readers = []
        if proc.stdout:
            readers.append(asyncio.create_task(_read_stream(proc.stdout, False)))
        if proc.stderr:
            readers.append(asyncio.create_task(_read_stream(proc.stderr, True)))

        async def _wait_with_timeout():
            timed_out = False
            while proc.returncode is None:
                if (asyncio.get_event_loop().time() - started) > timeout_final:
                    try:
                        proc.kill()
                    except Exception:
                        pass
                    timed_out = True
                    break
                await asyncio.sleep(0.1)
            if timed_out:
                try:
                    await asyncio.wait_for(proc.wait(), timeout=2.0)
                except Exception:
                    pass
                return False
            return True

        done_ok = await _wait_with_timeout()
        try:
            await asyncio.gather(*readers, return_exceptions=True)
        except Exception:
            pass
        retcode = proc.returncode
        status = "success" if retcode == 0 else "error"
        if not done_ok:
            status = "error"
            stderr_acc.append(f"\nTimeout após {timeout_final}s\n")

        full_stdout = "".join(stdout_acc)[-8000:]
        full_stderr = "".join(stderr_acc)[-8000:]

        artifacts_dir = (
            _safe_str_value((params or {}).get("artifacts_dir"))
            or _sanitize_text(os.getenv((wl.get(app_key) or {}).get("artifacts_env") or ""))
            or _sanitize_text(os.getenv("OPENSLAP_CLI_ARTIFACTS_DIR") or "")
        )
        if not artifacts_dir and app_key == "python-inline":
            artifacts_dir = _sanitize_text(cwd_dir or "") or _sanitize_text(
                str(DEFAULT_WORKDIR)
            )
        arts_info = _collect_artifacts(artifacts_dir)
        visual_summary = _sanitize_text(arts_info.get("summary") or "")
        reg_artifacts = _register_cli_artifacts(arts_info.get("files") or [])

        await _send_evt(
            {
                "type": "software_operator",
                "execution_id": execution_id,
                "attempt": int(attempt),
                "status": status,
                "command_executed": " ".join(args),
                "started_at_ms": started_at_ms,
                "timeout_s": timeout_final,
                "return_ms": int(time.time() * 1000) - started_at_ms,
                "stdout": full_stdout,
                "stderr": full_stderr,
                "visual_state_summary": visual_summary[:4000],
                "artifacts": reg_artifacts,
            }
        )
        return {
            "status": status,
            "command_executed": " ".join(args),
            "output": json.dumps(
                {
                    "stdout": full_stdout,
                    "stderr": full_stderr,
                    "return_ms": int(time.time() * 1000) - started_at_ms,
                    "params": safe_params,
                    "artifacts": arts_info.get("files") or [],
                },
                ensure_ascii=False,
            ),
            "visual_state_summary": visual_summary[:4000],
            "app_name": app_name,
            "action": action,
        }

    attempt_1_text = str(command_text or "").strip()
    res = await _run_one_attempt(command_line=attempt_1_text, attempt=1)

    if str(res.get("status") or "").strip().lower() == "error":
        fields = _extract_cli_output_fields(str(res.get("output") or ""))
        err_text = (
            str(fields.get("stderr") or "").strip()
            or str(res.get("output") or "").strip()
        )
        try:
            retry_cmd = await _generate_software_operator_retry_command(
                error_text=err_text[:2500],
                expert=expert,
                llm_override=llm_override,
                user_context=user_context or "",
            )
            retry_cmd = str(retry_cmd or "").strip()
            if retry_cmd:
                res = await _run_one_attempt(command_line=retry_cmd, attempt=2)
        except Exception:
            pass

    try:
        log_cli_command(
            user_id=int(user_id),
            conversation_id=int(conversation_id),
            app_name=str(res.get("app_name") or ""),
            action=str(res.get("action") or ""),
            command_executed=str(res.get("command_executed") or ""),
            status=str(res.get("status") or "error"),
            output=str(res.get("output") or ""),
            visual_state_summary=str(res.get("visual_state_summary") or ""),
        )
    except Exception:
        pass

    try:
        appn = str(res.get("app_name") or "").strip()
        act = str(res.get("action") or "").strip()
        cmd = str(res.get("command_executed") or "").strip()
        st = str(res.get("status") or "error").strip()
        vis = str(res.get("visual_state_summary") or "").strip()
        extra = f" | {vis[:160].strip()}" if vis else ""
        _record_activity_done(
            int(user_id),
            f"[EXEC] {appn} {act} → {cmd} | status={st}{extra}",
        )
    except Exception:
        pass

    ok = str(res.get("status") or "").strip().lower() == "success"
    try:
        record_expert_rating(int(user_id), "software_operator", bool(ok))
    except Exception:
        pass

    try:
        if ENABLE_MEMORY_WRITE:
            summary = str(res.get("visual_state_summary") or "").strip()
            if summary:
                payload = (
                    f"External software: {str(res.get('command_executed') or '').strip()}\n"
                    f"Status: {str(res.get('status') or '').strip()}\n"
                    f"{summary}"
                ).strip()
                append_soul_event(int(user_id), "external_software", payload[:900])
    except Exception:
        pass

    fields = _extract_cli_output_fields(str(res.get("output") or ""))
    stdout = str(fields.get("stdout") or "")
    stderr = str(fields.get("stderr") or "")

    try:
        summary2 = _build_persisted_summary(res_obj=res, stdout_text=stdout, stderr_text=stderr)
        if summary2 and add_conversation_cli_summary(int(user_id), int(conversation_id), str(execution_id), summary2):
            msg_id = save_message(
                int(conversation_id),
                "assistant",
                summary2,
                expert_id="software_operator",
            )
            await _send_evt(
                {
                    "type": "history",
                    "message": {
                        "id": msg_id,
                        "role": "assistant",
                        "content": summary2,
                        "created_at": datetime.utcnow().isoformat() + "Z",
                        "expert_id": "software_operator",
                    },
                }
            )
    except Exception:
        pass

    out_lines: List[str] = []
    out_lines.append(
        f"Comando executado: {str(res.get('command_executed') or '').strip()}"
    )
    out_lines.append(f"Status: {str(res.get('status') or '').strip()}")
    if stdout.strip():
        out_lines.append("")
        out_lines.append("stdout:")
        out_lines.append(stdout.strip()[-2000:])
    if stderr.strip():
        out_lines.append("")
        out_lines.append("stderr:")
        out_lines.append(stderr.strip()[-2000:])
    vis = str(res.get("visual_state_summary") or "").strip()
    if vis:
        out_lines.append("")
        out_lines.append("Resumo visual:")
        out_lines.append(vis[:1500])
    return "\n".join(out_lines).strip()


def _get_agno_db_file_path() -> str:
    raw = str(getattr(settings, "agno_db_file", "") or "").strip()
    if raw:
        try:
            return str(Path(raw).expanduser().resolve())
        except Exception:
            return str(raw)
    try:
        base_dir = Path(get_db_path()).resolve().parent
    except Exception:
        base_dir = Path(str(BASE_DIR)).resolve()
    return str((base_dir / "agno_sessions.db").resolve())


async def _maybe_run_tool_needed_with_agno(
    *,
    prompt: str,
    user_id: int,
    conversation_id: int,
    sec: Dict[str, Any],
    expert: Dict[str, Any],
    llm_override: Optional[Dict[str, Any]],
    user_context: str,
    websocket: WebSocket,
) -> Optional[Dict[str, Any]]:
    if not bool(getattr(settings, "enable_agno_poc", False)):
        return None

    if not expert or not expert.get("tool_needed"):
        return None

    provider = str((llm_override or {}).get("provider") or "").strip().lower()
    model_id = str((llm_override or {}).get("model") or "").strip()
    base_url = str((llm_override or {}).get("base_url") or "").strip().rstrip("/")
    api_key = str((llm_override or {}).get("api_key") or "").strip()
    if not api_key:
        return None
    if provider not in {"groq", "openai", "openrouter"}:
        return None
    if not model_id:
        model_id = "gpt-4o-mini"
    if not base_url:
        if provider == "groq":
            base_url = "https://api.groq.com/openai/v1"
        elif provider == "openrouter":
            base_url = "https://openrouter.ai/api/v1"
        else:
            base_url = "https://api.openai.com/v1"

    try:
        from agno.agent import Agent
        from agno.db.sqlite import SqliteDb
        from agno.models.openai import OpenAIChat
        from agno.tools import tool
    except Exception:
        return None

    async def _ws_status(content: str) -> None:
        try:
            await websocket.send_json({"type": "status", "content": content})
        except Exception:
            pass

    async def _ws_chunk(content: str) -> None:
        try:
            await websocket.send_json({"type": "chunk", "content": content})
        except Exception:
            pass

    @tool(name="external_software")
    async def external_software(command_line: str) -> str:
        cmd = str(command_line or "").strip()
        if not cmd:
            return "Comando vazio."
        return await _run_external_software_skill(
            command_text=cmd,
            user_id=int(user_id),
            conversation_id=int(conversation_id),
            sec=sec,
            expert=expert,
            llm_override=llm_override,
            user_context=user_context,
            websocket=websocket,
        )

    db_file = _get_agno_db_file_path()
    db = SqliteDb(db_file=db_file)

    agent = Agent(
        name="Sabrina (Agno POC)",
        model=OpenAIChat(id=model_id, base_url=base_url, api_key=api_key),
        tools=[external_software],
        db=db,
        store_media=False,
        store_tool_messages=False,
        add_history_to_context=True,
        num_history_runs=3,
        markdown=False,
        instructions=[
            "Quando o usuário pedir automação local, use a ferramenta external_software.",
            "Para captura e análise de tela com retângulos em texto, use: python-inline --action vision_screen_text_boxes --out vision_analysis.png",
            "Após chamar a ferramenta, responda com o resultado e aponte o nome do arquivo gerado (se houver).",
        ],
    )

    session_id = f"openslap_conv_{int(conversation_id)}"
    await _ws_status(f"Agno POC: sessão SQLite={db_file}")

    full_response = ""
    saw_any_event = False
    try:
        await _ws_status("Agno POC: executando agente...")
        async for ev in agent.arun(
            prompt,
            stream=True,
            user_id=str(user_id),
            session_id=session_id,
        ):
            saw_any_event = True
            ev_content = getattr(ev, "content", None)
            if isinstance(ev_content, str) and ev_content:
                full_response += ev_content
                await _ws_chunk(ev_content)
                continue
            ev_name = str(getattr(ev, "event", "") or "").strip().lower()
            if "tool_call_started" in ev_name:
                await _ws_status("▶ Agno POC: chamando ferramenta...")
            elif "tool_call_completed" in ev_name:
                await _ws_status("✅ Agno POC: ferramenta finalizada.")
    except Exception:
        return None

    if not full_response.strip() and saw_any_event:
        try:
            out = await agent.arun(
                prompt,
                stream=False,
                user_id=str(user_id),
                session_id=session_id,
            )
            out_content = getattr(out, "content", None)
            if isinstance(out_content, str) and out_content.strip():
                full_response = out_content
        except Exception:
            pass

    if not full_response.strip():
        return None

    return {
        "content": full_response,
        "expert_info": {"provider": "agno", "model": model_id, "tokens": None},
    }


class SoulInput(BaseModel):
    data: Dict[str, Any]


class SoulEventInput(BaseModel):
    content: str
    source: Optional[str] = None


def _safe_llm_settings(inp: Dict[str, Any]) -> Dict[str, Any]:
    raw_provider = (inp or {}).get("provider")
    provider = (
        str(raw_provider).strip().lower() if raw_provider is not None else None
    ) or None
    base_url = (inp or {}).get("base_url")
    if isinstance(base_url, str):
        base_url = base_url.strip().strip("`\"' ,").rstrip("/")

    if provider == "gemini":
        bu = str(base_url or "").strip()
        if not bu:
            bu = "https://generativelanguage.googleapis.com/v1"
        if bu.endswith("/v1beta") and "generativelanguage.googleapis.com" in bu:
            bu = bu[:-6] + "v1"
        base_url = bu
    elif provider == "groq":
        base_url = str(base_url or "https://api.groq.com/openai/v1").strip()
    elif provider == "openai":
        base_url = str(base_url or "https://api.openai.com/v1").strip()
    elif provider == "openrouter":
        base_url = str(base_url or "https://openrouter.ai/api/v1").strip()
    elif provider == "ollama":
        base_url = str(base_url or "http://localhost:11434").strip()
    return {
        "mode": str((inp or {}).get("mode") or "env"),
        "provider": provider,
        "model": (inp or {}).get("model"),
        "base_url": base_url,
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


def _extract_files_json(text: str) -> Optional[Dict[str, Any]]:
    if not text:
        return None
    start_tag = "<FILES_JSON>"
    end_tag = "</FILES_JSON>"
    start = text.find(start_tag)
    end = text.find(end_tag)
    if start == -1 or end == -1 or end <= start:
        return None
    payload = text[start + len(start_tag) : end].strip()
    if not payload:
        return None
    try:
        obj = json.loads(payload)
    except Exception:
        return None
    if not isinstance(obj, dict):
        return None
    return obj


def _safe_join(base_path: str, rel_path: str) -> Optional[str]:
    if not base_path or not rel_path:
        return None
    base_abs = os.path.abspath(base_path)
    target_abs = os.path.abspath(os.path.join(base_abs, rel_path))
    if not target_abs.startswith(base_abs.rstrip("\\/") + os.sep):
        return None
    return target_abs


def _slugify_path_component(text: str, *, max_len: int = 60) -> str:
    s = str(text or "").strip().lower()
    if not s:
        return ""
    s = re.sub(r"[\r\n\t]+", " ", s)
    s = re.sub(r"[^a-z0-9áàâãéèêíìîóòôõúùûçñ _.-]+", "", s, flags=re.IGNORECASE)
    s = s.replace(" ", "-").replace("_", "-")
    s = re.sub(r"-{2,}", "-", s).strip(" .-_")
    if max_len and len(s) > int(max_len):
        s = s[: int(max_len)].rstrip(" .-_")
    return s


def _get_project_folder_for_conversation(
    *, user_id: int, conversation_id: int
) -> Optional[str]:
    try:
        import sqlite3 as _sq_proj

        with _sq_proj.connect(str(get_db_path())) as _c_proj:
            row = _c_proj.execute(
                "SELECT project_id FROM conversations WHERE id=? AND user_id=?",
                (int(conversation_id), int(user_id)),
            ).fetchone()
            if not row or not row[0]:
                return None
            pid = int(row[0])
            prow = _c_proj.execute(
                "SELECT name FROM projects WHERE id=? AND user_id=?",
                (pid, int(user_id)),
            ).fetchone()
            pname = str(prow[0] or "").strip() if prow else ""
            slug = _slugify_path_component(pname) if pname else ""
            return slug or f"project-{pid}"
    except Exception:
        return None


def _hash_question(text: str) -> str:
    s = (text or "").strip().lower()
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


ENABLE_MEMORY_WRITE = str(
    os.getenv("OPENSLAP_MEMORY_WRITE") or "1"
).strip().lower() in (
    "1",
    "true",
    "yes",
    "on",
)
ENABLE_MEMORY_SNAPSHOT_CONTEXT = str(
    os.getenv("OPENSLAP_MEMORY_SNAPSHOT_CONTEXT") or "1"
).strip().lower() in (
    "1",
    "true",
    "yes",
    "on",
)
MEMORY_SNAPSHOT_MAX_CHARS = int(
    os.getenv("OPENSLAP_MEMORY_SNAPSHOT_MAX_CHARS") or "3500"
)


def _normalize_memory_text(text: str) -> str:
    s = str(text or "").strip().lower()
    s = re.sub(r"\s+", " ", s)
    s = re.sub(r"[^a-z0-9áàâãéèêíìîóòôõúùûçñ _:/.-]+", "", s, flags=re.IGNORECASE)
    return s.strip()


def _extract_memory_candidates(user_message: str) -> List[str]:
    msg = str(user_message or "").strip()
    if not msg:
        return []
    if len(msg) > 800:
        return []

    m = msg.lower()
    out: List[str] = []

    rx_name = re.search(
        r"\b(meu nome é|pode me chamar de|me chama de)\s+([^\n,.!?:;]{1,40})",
        msg,
        flags=re.IGNORECASE,
    )
    if rx_name:
        name = (rx_name.group(2) or "").strip().strip("\"'`")
        if name:
            out.append(f"Nome do usuário: {name}")

    if ("fale" in m or "responda" in m) and ("português" in m or "pt-br" in m):
        out.append("Preferência de idioma: pt-BR")

    if "windows" in m and any(t in m for t in ["uso", "meu pc", "no meu pc", "aqui é"]):
        out.append("Ambiente: Windows")
    elif "linux" in m and any(t in m for t in ["uso", "no meu pc", "aqui é"]):
        out.append("Ambiente: Linux")
    elif "mac" in m and any(t in m for t in ["uso", "no meu pc", "aqui é"]):
        out.append("Ambiente: macOS")

    if any(
        t in m
        for t in ["não use", "nao use", "nunca use", "evite", "não faça", "nao faca"]
    ):
        text = msg.strip()
        if len(text) <= 240:
            out.append(f"Regra do usuário: {text}")

    if "agente" in m and any(
        k in m for k in ("aprend", "evolu", "com o tempo", "ao longo do tempo")
    ):
        out.append(
            "Preferência: agentes aprendem incrementalmente (evitar antecipar tudo)"
        )
    if "uma coisa de cada vez" in m or "uma pergunta de cada vez" in m:
        out.append("Preferência: 1 pergunta por vez (mensagens curtas)")

    deduped: List[str] = []
    seen = set()
    for item in out:
        norm = _normalize_memory_text(item)
        if not norm or norm in seen:
            continue
        seen.add(norm)
        deduped.append(item[:240].strip())
    return deduped


def _auto_memorize_user_message(user_id: int, user_message: str) -> int:
    candidates = _extract_memory_candidates(user_message)
    if not candidates:
        return 0

    existing = list_soul_events(int(user_id), limit=80)
    existing_norm = {
        _normalize_memory_text((e or {}).get("content") or "") for e in (existing or [])
    }

    inserted = 0
    for item in candidates:
        norm = _normalize_memory_text(item)
        if not norm or norm in existing_norm:
            continue
        append_soul_event(int(user_id), "auto", item)
        existing_norm.add(norm)
        inserted += 1
    return inserted


def _is_runtime_introspection_query(text: str) -> bool:
    t = (text or "").strip().lower()
    if not t:
        return False

    # High confidence triggers that work on their own
    direct_triggers = [
        "sistema local",
        "onde você está rodando",
        "onde você está executando",
        "onde voce esta rodando",
        "onde voce esta executando",
        "servidor local",
        "me descreva o ambiente",
        "descreva seu ambiente",
        "sobre o seu ambiente",
        "informações do sistema",
        "informacoes do sistema",
    ]
    if any(x in t for x in direct_triggers):
        return True

    # Ambiguous tokens that require context
    ambiguous_tokens = ["ambiente", "windows", "hardware", "sistema operacional"]
    context_tokens = [
        "rodando",
        "executando",
        "qual versão",
        "qual versao",
        "onde",
        "descreva",
        "sobre",
    ]

    if any(amb in t for amb in ambiguous_tokens) and any(
        ctx in t for ctx in context_tokens
    ):
        return True

    return False


def _runtime_introspection_answer(
    *, current_user: Dict[str, Any], session_id: str
) -> str:
    os_name = platform.system()
    os_release = platform.release()
    py = sys.version.split(" ")[0]
    base_dir = os.path.abspath(str(BASE_DIR))
    deliveries_root = os.path.abspath(DEFAULT_DELIVERIES_ROOT)
    lines = [
        "Você está usando o Open Slap! (servidor local) rodando neste computador.",
        f"- Runtime: Python {py} + FastAPI/uvicorn",
        f"- Sistema: {os_name} {os_release}",
        f"- Projeto (raiz): {base_dir}",
        f"- Sessão: {session_id}",
        f"- Usuário (id): {current_user.get('id')}",
        f"- Entregas padrão: {deliveries_root}",
        "",
        "O modelo (Gemini/Groq/OpenAI/Ollama) pode ser remoto ou local, mas ele não enxerga seu hardware diretamente: ele recebe texto via este servidor local, que aplica as permissões (ex.: salvar arquivos em pastas permitidas) e guarda histórico no SQLite.",
    ]
    return "\n".join([line for line in lines if line is not None]).strip()


def _get_total_memory_bytes() -> Optional[int]:
    if sys.platform == "win32":

        class _MEMORYSTATUSEX(ctypes.Structure):
            _fields_ = [
                ("dwLength", ctypes.c_uint32),
                ("dwMemoryLoad", ctypes.c_uint32),
                ("ullTotalPhys", ctypes.c_ulonglong),
                ("ullAvailPhys", ctypes.c_ulonglong),
                ("ullTotalPageFile", ctypes.c_ulonglong),
                ("ullAvailPageFile", ctypes.c_ulonglong),
                ("ullTotalVirtual", ctypes.c_ulonglong),
                ("ullAvailVirtual", ctypes.c_ulonglong),
                ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
            ]

        st = _MEMORYSTATUSEX()
        st.dwLength = ctypes.sizeof(_MEMORYSTATUSEX)
        ok = ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(st))
        if not ok:
            return None
        return int(st.ullTotalPhys)
    if sys.platform == "darwin":
        try:
            res = subprocess.run(
                ["sysctl", "-n", "hw.memsize"],
                capture_output=True,
                timeout=3,
            )
            raw = (res.stdout or b"").decode("utf-8", errors="ignore").strip()
            return int(raw) if raw.isdigit() else None
        except Exception:
            return None
    if sys.platform.startswith("linux"):
        try:
            with open("/proc/meminfo", "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    if line.lower().startswith("memtotal:"):
                        parts = line.split()
                        if len(parts) >= 2 and str(parts[1]).isdigit():
                            return int(parts[1]) * 1024
        except Exception:
            return None
    return None


def _decode_best_effort(raw: bytes) -> str:
    if not raw:
        return ""
    candidates = [("cp850", "replace"), ("utf-8", "replace"), ("latin-1", "replace")]
    best = ""
    best_score = -1
    for enc, err in candidates:
        try:
            s = raw.decode(enc, errors=err)
        except Exception:
            continue
        score = -s.count("�")
        if score > best_score:
            best_score = score
            best = s
    return best


def _truncate_text(value: str, limit: int) -> str:
    s = (value or "").strip()
    if not s:
        return ""
    if limit and len(s) > int(limit):
        return s[: int(limit)] + "\n…"
    return s


def _run_bash_text(command: str, timeout_s: int = 8) -> str:
    cmd = (command or "").strip()
    if not cmd:
        return ""
    try:
        res = subprocess.run(
            ["bash", "-lc", cmd],
            capture_output=True,
            timeout=max(1, int(timeout_s)),
        )
        return (res.stdout or b"").decode("utf-8", errors="ignore").strip()
    except Exception:
        return ""


def _safe_plist_loads(raw: bytes) -> Any:
    if not raw:
        return None
    try:
        return plistlib.loads(raw)
    except Exception:
        return None


def _shrink_macos_system_profiler(obj: Any) -> Any:
    if not obj:
        return None
    if isinstance(obj, dict):
        return obj
    if isinstance(obj, list) and obj and isinstance(obj[0], dict):
        root = obj[0]
        items = root.get("_items")
        if isinstance(items, list) and items and isinstance(items[0], dict):
            keep: Dict[str, Any] = {}
            for k in [
                "machine_name",
                "machine_model",
                "model_name",
                "model_identifier",
                "chip_type",
                "cpu_type",
                "number_processors",
                "number_cores",
                "memory",
                "physical_memory",
                "serial_number",
            ]:
                if k in items[0]:
                    keep[k] = items[0].get(k)
            return keep or items[0]
        return root
    return None


def _shrink_macos_diskutil(obj: Any, max_disks: int = 24) -> Any:
    if not obj or not isinstance(obj, dict):
        return None
    all_disks = obj.get("AllDisksAndPartitions")
    if not isinstance(all_disks, list):
        return None
    compact: List[Dict[str, Any]] = []
    for row in all_disks[: max(1, int(max_disks))]:
        if not isinstance(row, dict):
            continue
        keep: Dict[str, Any] = {}
        for k in ["DeviceIdentifier", "Size", "Content", "MountPoint", "VolumeName"]:
            if k in row:
                keep[k] = row.get(k)
        parts = row.get("Partitions")
        if isinstance(parts, list):
            keep_parts: List[Dict[str, Any]] = []
            for p in parts[:10]:
                if not isinstance(p, dict):
                    continue
                kp: Dict[str, Any] = {}
                for k in [
                    "DeviceIdentifier",
                    "Size",
                    "Content",
                    "MountPoint",
                    "VolumeName",
                ]:
                    if k in p:
                        kp[k] = p.get(k)
                if kp:
                    keep_parts.append(kp)
            if keep_parts:
                keep["Partitions"] = keep_parts
        if keep:
            compact.append(keep)
    return {"AllDisksAndPartitions": compact}


def _shrink_linux_lsblk(obj: Any, max_nodes: int = 80) -> Any:
    if not obj or not isinstance(obj, dict):
        return None
    bds = obj.get("blockdevices")
    if not isinstance(bds, list):
        return None

    kept_count = 0

    def shrink_node(node: Any) -> Any:
        nonlocal kept_count
        if kept_count >= max(1, int(max_nodes)):
            return None
        if not isinstance(node, dict):
            return None
        kept_count += 1
        keep: Dict[str, Any] = {}
        for k in [
            "name",
            "kname",
            "size",
            "type",
            "mountpoint",
            "fstype",
            "model",
            "serial",
            "uuid",
            "rota",
            "rm",
        ]:
            if k in node:
                keep[k] = node.get(k)
        kids = node.get("children")
        if isinstance(kids, list):
            out_kids = []
            for c in kids:
                sc = shrink_node(c)
                if sc is not None:
                    out_kids.append(sc)
            if out_kids:
                keep["children"] = out_kids
        return keep

    out = []
    for n in bds:
        sn = shrink_node(n)
        if sn is not None:
            out.append(sn)
    return {"blockdevices": out}


def _collect_systeminfo_text(timeout_s: int = 12) -> str:
    try:
        if sys.platform == "win32":
            res = subprocess.run(
                ["cmd", "/c", "systeminfo"],
                capture_output=True,
                timeout=max(1, int(timeout_s)),
            )
            out = _decode_best_effort(res.stdout or b"")
            err = _decode_best_effort(res.stderr or b"")
            txt = (out or "").strip()
            if not txt and err:
                txt = err.strip()
            return txt
        if sys.platform == "darwin":
            res = subprocess.run(
                ["system_profiler", "SPSoftwareDataType"],
                capture_output=True,
                timeout=max(1, int(timeout_s)),
            )
            soft = (res.stdout or b"").decode("utf-8", errors="ignore").strip()
            try:
                res_hw = subprocess.run(
                    ["system_profiler", "SPHardwareDataType"],
                    capture_output=True,
                    timeout=max(1, int(timeout_s)),
                )
                hw = (res_hw.stdout or b"").decode("utf-8", errors="ignore").strip()
            except Exception:
                hw = ""
            combined = "\n\n".join([p for p in [soft, hw] if p]).strip()
            return combined
        if sys.platform.startswith("linux"):
            parts: List[str] = []
            try:
                res = subprocess.run(
                    ["uname", "-a"],
                    capture_output=True,
                    timeout=max(1, int(timeout_s)),
                )
                parts.append(
                    (res.stdout or b"").decode("utf-8", errors="ignore").strip()
                )
            except Exception:
                pass
            try:
                res = subprocess.run(
                    [
                        "bash",
                        "-lc",
                        "lsb_release -a 2>/dev/null || cat /etc/os-release 2>/dev/null || true",
                    ],
                    capture_output=True,
                    timeout=max(1, int(timeout_s)),
                )
                txt = (res.stdout or b"").decode("utf-8", errors="ignore").strip()
                if txt:
                    parts.append(txt)
            except Exception:
                pass
            return "\n\n".join([p for p in parts if p]).strip()
    except Exception:
        return ""
    return ""


def _collect_macos_diskutil_list_plist(timeout_s: int = 8) -> Any:
    if sys.platform != "darwin":
        return None
    try:
        res = subprocess.run(
            ["diskutil", "list", "-plist"],
            capture_output=True,
            timeout=max(1, int(timeout_s)),
        )
        return _safe_plist_loads(res.stdout or b"")
    except Exception:
        return None


def _collect_macos_system_profiler_plist(datatype: str, timeout_s: int = 10) -> Any:
    if sys.platform != "darwin":
        return None
    dt = str(datatype or "").strip()
    if not dt:
        return None
    try:
        res = subprocess.run(
            ["system_profiler", dt, "-xml"],
            capture_output=True,
            timeout=max(1, int(timeout_s)),
        )
        return _safe_plist_loads(res.stdout or b"")
    except Exception:
        return None


def _collect_linux_lsblk_json(timeout_s: int = 8) -> Any:
    if not sys.platform.startswith("linux"):
        return None
    txt = _run_bash_text(
        "lsblk -J -b -o NAME,KNAME,SIZE,TYPE,MOUNTPOINT,FSTYPE,MODEL,SERIAL,UUID,ROTA,RM 2>/dev/null || true",
        timeout_s=timeout_s,
    )
    if not txt:
        return None
    try:
        return json.loads(txt)
    except Exception:
        return None


def _collect_df_bytes_map(timeout_s: int = 6) -> Dict[str, Dict[str, Any]]:
    out: Dict[str, Dict[str, Any]] = {}
    cmd = ""
    if sys.platform.startswith("linux"):
        cmd = "df -T -B1 2>/dev/null || df -B1 2>/dev/null || true"
    else:
        cmd = "df -k 2>/dev/null || true"
    txt = _run_bash_text(cmd, timeout_s=timeout_s)
    if not txt:
        return out
    lines = [ln for ln in txt.splitlines() if ln.strip()]
    if len(lines) < 2:
        return out
    header = (lines[0] or "").lower()
    for ln in lines[1:]:
        parts = [p for p in ln.split() if p]
        if len(parts) < 6:
            continue
        if "type" in header:
            device_id = parts[0]
            fs = parts[1]
            size = parts[2]
            free = parts[4]
            mountpoint = parts[6] if len(parts) >= 7 else parts[-1]
        else:
            device_id = parts[0]
            fs = ""
            size = parts[1]
            free = parts[3]
            mountpoint = parts[5] if len(parts) >= 6 else parts[-1]
        if not mountpoint:
            continue
        size_bytes = int(size) if str(size).isdigit() else None
        free_bytes = int(free) if str(free).isdigit() else None
        out[str(mountpoint)] = {
            "device_id": str(device_id).strip(),
            "file_system": str(fs).strip(),
            "size_bytes": size_bytes,
            "free_bytes": free_bytes,
        }
    return out


def _collect_df_texts(timeout_s: int = 6) -> Dict[str, str]:
    if sys.platform == "win32":
        return {}
    h = _run_bash_text("df -h 2>/dev/null | head -n 120 || true", timeout_s=timeout_s)
    H = _run_bash_text("df -H 2>/dev/null | head -n 120 || true", timeout_s=timeout_s)
    return {"df_h": h, "df_H": H}


_installed_cache_ts = None
_installed_cache: List[Dict[str, Any]] = []
_installed_removed: List[Dict[str, Any]] = []


def _merge_sw_items(base: List[Dict[str, Any]], extra: List[Dict[str, Any]], max_items: int = 1200) -> List[Dict[str, Any]]:
    out = []
    seen = set()
    for src in (base or []) + (extra or []):
        if not isinstance(src, dict):
            continue
        name = str(src.get("name") or "").strip()
        if not name:
            continue
        key = name.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(
            {
                "name": name[:120],
                "version": str(src.get("version") or "").strip()[:60],
                "id": str(src.get("id") or "").strip()[:120],
                "source": str(src.get("source") or "").strip()[:60],
            }
        )
        if len(out) >= max_items:
            break
    return out


def _collect_windows_registry_sw(timeout_s: int = 10) -> List[Dict[str, Any]]:
    obj = _collect_powershell_json(
        "$paths=@("
        "'HKLM:\\Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\*',"
        "'HKLM:\\Software\\WOW6432Node\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\*',"
        "'HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\*'"
        "); "
        "Get-ItemProperty $paths -ErrorAction SilentlyContinue | "
        "Where-Object { $_.DisplayName } | "
        "Select-Object DisplayName,DisplayVersion,Publisher | ConvertTo-Json -Compress",
        timeout_s=timeout_s,
    )
    rows: List[Dict[str, Any]] = []
    if isinstance(obj, dict):
        rows = [obj]
    elif isinstance(obj, list):
        rows = obj
    items: List[Dict[str, Any]] = []
    for r in rows:
        if not isinstance(r, dict):
            continue
        name = str(r.get("DisplayName") or "").strip()
        if not name:
            continue
        items.append(
            {
                "name": name,
                "version": str(r.get("DisplayVersion") or "").strip(),
                "id": str(r.get("Publisher") or "").strip(),
                "source": "registry",
            }
        )
    return items


def _collect_windows_optional_features(timeout_s: int = 10) -> List[Dict[str, Any]]:
    obj = _collect_powershell_json(
        "Get-WindowsOptionalFeature -Online -ErrorAction SilentlyContinue | "
        "Where-Object { $_.FeatureName -like 'IIS*' -and $_.State -eq 'Enabled' } | "
        "Select-Object FeatureName | ConvertTo-Json -Compress",
        timeout_s=timeout_s,
    )
    rows: List[Dict[str, Any]] = []
    if isinstance(obj, dict):
        rows = [obj]
    elif isinstance(obj, list):
        rows = obj
    items: List[Dict[str, Any]] = []
    enabled = any(
        isinstance(r, dict)
        and str(r.get("FeatureName") or "").strip().lower().startswith("iis")
        for r in rows
    )
    if enabled:
        items.append({"name": "IIS (Windows Feature)", "version": "", "id": "iis", "source": "windows-feature"})
    return items


def _collect_macos_brew_sw(timeout_s: int = 8) -> List[Dict[str, Any]]:
    txt = _run_bash_text(
        "command -v brew >/dev/null 2>&1 && brew list --versions 2>/dev/null | head -n 200 || true",
        timeout_s=timeout_s,
    )
    items: List[Dict[str, Any]] = []
    for line in (txt or "").splitlines():
        parts = line.strip().split()
        if not parts:
            continue
        name = parts[0]
        version = parts[1] if len(parts) >= 2 else ""
        items.append({"name": name, "version": version, "id": "", "source": "brew"})
    return items


def _collect_linux_pkg_sw(timeout_s: int = 8) -> List[Dict[str, Any]]:
    # Try dpkg, then rpm, then snap/flatpak
    txt = _run_bash_text("dpkg -l 2>/dev/null | awk '/^ii/ {print $2\"\\t\"$3}' | head -n 400 || true", timeout_s=timeout_s)
    items: List[Dict[str, Any]] = []
    if txt.strip():
        for line in txt.splitlines():
            parts = line.strip().split("\t")
            if not parts:
                continue
            name = parts[0]
            ver = parts[1] if len(parts) >= 2 else ""
            items.append({"name": name, "version": ver, "id": "", "source": "dpkg"})
        return items
    txt2 = _run_bash_text("rpm -qa 2>/dev/null | head -n 400 || true", timeout_s=timeout_s)
    if txt2.strip():
        for line in txt2.splitlines():
            name = line.strip()
            if not name:
                continue
            items.append({"name": name, "version": "", "id": "", "source": "rpm"})
    # Snap / Flatpak (optional)
    snap = _run_bash_text("command -v snap >/dev/null 2>&1 && snap list 2>/dev/null | awk 'NR>1{print $1\"\\t\"$2}' | head -n 200 || true", timeout_s=timeout_s)
    for line in (snap or "").splitlines():
        parts = line.strip().split("\t")
        if parts:
            items.append({"name": parts[0], "version": parts[1] if len(parts) >= 2 else "", "id": "", "source": "snap"})
    flat = _run_bash_text("command -v flatpak >/dev/null 2>&1 && flatpak list --app 2>/dev/null | awk -F'\\t' '{print $1\"\\t\"$2}' | head -n 200 || true", timeout_s=timeout_s)
    for line in (flat or "").splitlines():
        parts = line.strip().split("\t")
        if parts:
            items.append({"name": parts[0], "version": parts[1] if len(parts) >= 2 else "", "id": "", "source": "flatpak"})
    return items


def get_installed_software(max_age_s: int = 21600) -> List[Dict[str, Any]]:
    global _installed_cache_ts, _installed_cache, _installed_removed
    now = datetime.utcnow().timestamp()
    if _installed_cache_ts and (now - float(_installed_cache_ts)) < max_age_s and _installed_cache:
        return list(_installed_cache)
    try:
        db_cached = get_system_kv_cache("installed_sw_snapshot", max_age_s=max_age_s) or {}
        if isinstance(db_cached.get("items"), list) and db_cached["items"]:
            _installed_cache = db_cached["items"]
            _installed_removed = db_cached.get("removed", [])
            _installed_cache_ts = now
            return list(_installed_cache)
    except Exception:
        pass
    items: List[Dict[str, Any]] = []
    if sys.platform == "win32":
        try:
            res = subprocess.run(
                ["winget", "list", "--source", "winget"],
                capture_output=True,
                text=True,
                timeout=12,
                check=False,
            )
            txt = (res.stdout or "") + "\n" + (res.stderr or "")
            lines = [ln for ln in txt.splitlines() if ln.strip()]
            winget_items: List[Dict[str, Any]] = []
            for ln in lines:
                if ln.lower().startswith("name ") or ln.startswith("-"):
                    continue
                parts = [p for p in re.split(r"\s{2,}", ln.strip()) if p]
                if len(parts) < 2:
                    continue
                name = parts[0]
                version = parts[1] if len(parts) >= 2 else ""
                moniker = ""
                source = ""
                if len(parts) >= 3:
                    moniker = parts[2]
                if len(parts) >= 4:
                    source = parts[3]
                winget_items.append(
                    {
                        "name": name[:80],
                        "version": version[:40],
                        "id": moniker[:80],
                        "source": source[:40],
                    }
                )
            reg_items = _collect_windows_registry_sw(timeout_s=10)
            feat_items = _collect_windows_optional_features(timeout_s=8)
            items = _merge_sw_items(winget_items, reg_items + feat_items, max_items=1200)
        except Exception:
            items = []
    elif sys.platform == "darwin":
        try:
            brew_items = _collect_macos_brew_sw(timeout_s=8)
            items = _merge_sw_items([], brew_items, max_items=800)
        except Exception:
            items = []
    else:
        try:
            linux_items = _collect_linux_pkg_sw(timeout_s=8)
            items = _merge_sw_items([], linux_items, max_items=1200)
        except Exception:
            items = []
    prev = {}
    try:
        prev = get_system_kv_cache("installed_sw_snapshot", max_age_s=10**9) or {}
    except Exception:
        prev = {}
    prev_items = prev.get("items") if isinstance(prev.get("items"), list) else []
    prev_names = {str((x or {}).get("name") or "").strip().lower(): (x or {}) for x in prev_items}
    curr_names = {str((x or {}).get("name") or "").strip().lower(): (x or {}) for x in items}
    removed_list: List[Dict[str, Any]] = []
    for name, meta in prev_names.items():
        if name and name not in curr_names:
            removed_list.append(meta)
    _installed_cache = items[:400]
    _installed_removed = removed_list[:100]
    _installed_cache_ts = now
    try:
        upsert_system_kv_cache(
            "installed_sw_snapshot",
            {"items": _installed_cache, "removed": _installed_removed, "ts": now},
        )
    except Exception:
        pass
    return list(_installed_cache)


def _score_productivity(name: str, pkg_id: str) -> int:
    n = (name or "").lower()
    i = (pkg_id or "").lower()
    score = 0
    keywords = [
        ("draw", 6),
        ("diagram", 6),
        ("notepad++", 6),
        ("vscode", 6),
        ("code", 5),
        ("git", 6),
        ("python", 5),
        ("node", 5),
        ("npm", 4),
        ("pnpm", 4),
        ("yarn", 4),
        ("java", 4),
        ("jdk", 4),
        ("postgres", 5),
        ("sqlite", 5),
        ("irfanview", 6),
        ("imagemagick", 6),
        ("gimp", 5),
        ("inkscape", 5),
        ("blender", 4),
        ("7-zip", 5),
        ("winrar", 4),
        ("curl", 4),
        ("wget", 4),
        ("powershell", 3),
    ]
    for kw, w in keywords:
        if kw in n or kw in i:
            score += w
    return score


def _top20_productivity(installed: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    scored = []
    for it in installed or []:
        name = str(it.get("name") or "")
        pkg_id = str(it.get("id") or "")
        s = _score_productivity(name, pkg_id)
        if s > 0:
            scored.append((s, it))
    scored.sort(key=lambda x: (-x[0], str((x[1] or {}).get("name") or "")))
    return [x[1] for x in scored[:20]]


_SW_CATEGORIES: List[tuple] = [
    ("captura/visão", ["sharex", "greenshot", "snagit", "lightshot", "capture", "screenshot", "obs", "camtasia"]),
    ("edição de imagem", ["gimp", "inkscape", "irfanview", "imagemagick", "photoshop", "affinity", "paint.net", "krita", "pixelmator"]),
    ("diagrama", ["draw.io", "drawio", "visio", "lucidchart", "dia", "pencil", "mermaid", "plantuml", "excalidraw"]),
    ("vídeo/áudio", ["obs", "vlc", "ffmpeg", "audacity", "kdenlive", "davinci", "handbrake", "avisynth", "virtualdub"]),
    ("dev/runtime", ["python", "node", "nodejs", "git", "java", "jdk", "go ", "rust", "ruby", "php", "dotnet", ".net", "powershell", "wsl"]),
    ("editor/ide", ["vscode", "code", "notepad++", "sublime", "vim", "neovim", "emacs", "cursor", "jetbrains", "intellij", "pycharm"]),
    ("compressão", ["7-zip", "winrar", "bandizip", "peazip"]),
    ("automação/util", ["autohotkey", "autoit", "nircmd", "everything", "total commander", "winget", "chocolatey", "scoop"]),
]


def _build_software_tool_context(installed: List[Dict[str, Any]]) -> str:
    if not installed:
        return (
            "Softwares instalados disponíveis como ferramentas:\n"
            "  [universal] python-inline — sempre disponível para lógica customizada\n"
            "  Nenhum outro software detectado no inventário.\n"
        )
    categorized: Dict[str, List[str]] = {}
    uncategorized: List[str] = []
    for item in installed:
        name = str(item.get("name") or "").strip()
        pkg_id = str(item.get("id") or "").strip()
        if not name:
            continue
        label_str = name if not pkg_id else f"{name} [{pkg_id}]"
        nl = name.lower()
        il = pkg_id.lower()
        matched = False
        for cat_label, keywords in _SW_CATEGORIES:
            if any(kw in nl or kw in il for kw in keywords):
                categorized.setdefault(cat_label, []).append(label_str)
                matched = True
                break
        if not matched:
            uncategorized.append(label_str)
    lines = ["Softwares instalados disponíveis como ferramentas:"]
    lines.append("  [universal] python-inline — sempre disponível para lógica customizada")
    for cat_label, _ in _SW_CATEGORIES:
        items = categorized.get(cat_label)
        if items:
            entry = ", ".join(items[:6])
            if len(items) > 6:
                entry += f" (+{len(items) - 6})"
            lines.append(f"  [{cat_label}] {entry}")
    if uncategorized:
        sample = ", ".join(uncategorized[:10])
        if len(uncategorized) > 10:
            sample += f" (+{len(uncategorized) - 10} outros)"
        lines.append(f"  [outros] {sample}")
    return "\n".join(lines)


def _collect_web_services_info(installed: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    installed = installed or []
    if sys.platform == "win32":
        services = _collect_powershell_json(
            "Get-CimInstance Win32_Service -ErrorAction SilentlyContinue | "
            "Where-Object { "
            "$n=$_.Name; $d=$_.DisplayName; "
            "($n -in @('W3SVC','WAS','IISADMIN','Apache2.4','nginx','MySQL80','MariaDB','Redis','Memcached','com.docker.service','dockerdesktopservice','docker','caddy')) "
            "-or ($n -like 'Tomcat*') "
            "-or ($d -match '(?i)IIS|Internet Information Services|Apache|Nginx|Tomcat|Docker|Caddy|LiteSpeed|Wamp|XAMPP|Laragon') "
            "} | "
            "Select-Object Name,DisplayName,@{n='Status';e={$_.State}},@{n='StartType';e={$_.StartMode}} | "
            "ConvertTo-Json -Compress",
            timeout_s=9,
        )
        processes = _collect_powershell_json(
            "Get-Process -ErrorAction SilentlyContinue | "
            "Where-Object { $_.Name -match '^(nginx|httpd|apache2|php|php-cgi|mysqld|mariadbd|postgres|redis-server|laragon|dockerd|docker)$' } | "
            "Select-Object Name,Id,Path | ConvertTo-Json -Compress",
            timeout_s=8,
        )
        ports = _collect_powershell_json(
            "Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue | "
            "Where-Object { $_.LocalPort -in @(80,443,8000,8080,3000,5173,3306,5432,6379) } | "
            "Select-Object LocalAddress,LocalPort,OwningProcess | ConvertTo-Json -Compress",
            timeout_s=8,
        )
        commands = _collect_powershell_json(
            "Get-Command -ErrorAction SilentlyContinue docker,docker-compose,nginx,httpd,apache2,caddy,php,mariadb,mysql | "
            "Select-Object Name,Source | ConvertTo-Json -Compress",
            timeout_s=8,
        )
        dirs = _collect_powershell_json(
            "@{"
            "laragon=(Test-Path 'C:\\laragon');"
            "xampp=(Test-Path 'C:\\xampp');"
            "wamp64=(Test-Path 'C:\\wamp64');"
            "wamp=(Test-Path 'C:\\wamp');"
            "apache24=(Test-Path 'C:\\Apache24\\bin\\httpd.exe');"
            "nginxDir=(Test-Path 'C:\\nginx');"
            "iisAppCmd=(Test-Path 'C:\\Windows\\System32\\inetsrv\\appcmd.exe');"
            "dockerDesktop=(Test-Path 'C:\\Program Files\\Docker\\Docker\\Docker Desktop.exe');"
            "} | ConvertTo-Json -Compress",
            timeout_s=6,
        )
        iis_reg = _collect_powershell_json(
            "if (Test-Path 'HKLM:\\Software\\Microsoft\\InetStp') { "
            "Get-ItemProperty 'HKLM:\\Software\\Microsoft\\InetStp' "
            "| Select-Object VersionString,InstallPath,MajorVersion,MinorVersion "
            "| ConvertTo-Json -Compress "
            "} else { $null }",
            timeout_s=6,
        )

        def _flat_text(items2: List[Dict[str, Any]]) -> str:
            parts = []
            for it in items2 or []:
                if not isinstance(it, dict):
                    continue
                parts.append(str(it.get("name") or ""))
                parts.append(str(it.get("id") or ""))
                parts.append(str(it.get("source") or ""))
            return "\n".join(parts).lower()

        installed_hay = _flat_text(installed)

        def _has_installed(*tokens: str) -> bool:
            return any(t and t.lower() in installed_hay for t in tokens)

        def _cmd_names(obj: Any) -> List[str]:
            rows: List[Dict[str, Any]] = []
            if isinstance(obj, dict):
                rows = [obj]
            elif isinstance(obj, list):
                rows = [x for x in obj if isinstance(x, dict)]
            names = []
            for r in rows:
                nm = str(r.get("Name") or r.get("name") or "").strip().lower()
                if nm:
                    names.append(nm)
            return sorted(set(names))

        cmd_set = set(_cmd_names(commands))

        def _svc_rows(obj: Any) -> List[Dict[str, Any]]:
            if isinstance(obj, dict):
                return [obj]
            if isinstance(obj, list):
                return [x for x in obj if isinstance(x, dict)]
            return []

        svc_rows = _svc_rows(services)
        proc_rows = _svc_rows(processes)

        def _any_service_name(*names: str) -> bool:
            want = {str(n).lower() for n in names if n}
            for r in svc_rows:
                nm = str(r.get("Name") or "").strip().lower()
                dn = str(r.get("DisplayName") or "").strip().lower()
                if nm in want or dn in want:
                    return True
            return False

        installed_detected: List[str] = []
        running_detected: List[str] = []

        is_iis = (
            bool((dirs or {}).get("iisAppCmd"))
            or bool(iis_reg)
            or _any_service_name("w3svc", "was", "iisadmin")
            or _has_installed("internet information services", "iis")
        )
        if is_iis:
            installed_detected.append("IIS")

        if bool((dirs or {}).get("laragon")) or _has_installed("laragon"):
            installed_detected.append("Laragon")

        if bool((dirs or {}).get("xampp")) or _has_installed("xampp"):
            installed_detected.append("XAMPP")

        if bool((dirs or {}).get("wamp64")) or bool((dirs or {}).get("wamp")) or _has_installed("wampserver", "wamp"):
            installed_detected.append("WampServer")

        if bool((dirs or {}).get("dockerDesktop")) or ("docker" in cmd_set) or _any_service_name("com.docker.service", "dockerdesktopservice") or _has_installed("docker desktop", "docker"):
            installed_detected.append("Docker")

        if ("docker-compose" in cmd_set) or _has_installed("docker compose", "docker-compose"):
            installed_detected.append("Docker Compose")

        if bool((dirs or {}).get("apache24")) or _any_service_name("apache2.4") or _has_installed("apache http server", "apachehaus", "httpd", "apache"):
            installed_detected.append("Apache HTTP Server")

        if bool((dirs or {}).get("nginxDir")) or ("nginx" in cmd_set) or _any_service_name("nginx") or _has_installed("nginx"):
            installed_detected.append("Nginx")

        if any(str(r.get("Name") or "").strip().lower().startswith("tomcat") for r in svc_rows) or _has_installed("tomcat"):
            installed_detected.append("Tomcat")

        if ("caddy" in cmd_set) or _any_service_name("caddy") or _has_installed("caddy"):
            installed_detected.append("Caddy")

        if _has_installed("litespeed", "openlitespeed"):
            installed_detected.append("LiteSpeed")

        if _has_installed("mariadb") or _any_service_name("mariadb"):
            installed_detected.append("MariaDB")
        if _has_installed("mysql") or _any_service_name("mysql80"):
            installed_detected.append("MySQL")
        if _has_installed("postgres") or any(str(r.get("Name") or "").lower().startswith("postgresql") for r in svc_rows):
            installed_detected.append("PostgreSQL")

        for r in svc_rows:
            name = str(r.get("Name") or "").strip().lower()
            status = str(r.get("Status") or r.get("status") or "").strip().lower()
            if status not in {"running", "started"}:
                continue
            if name == "w3svc":
                running_detected.append("IIS")
            if name in {"apache2.4", "nginx", "mysql80", "mariadb", "redis"}:
                running_detected.append(name)
            if name.startswith("postgresql"):
                running_detected.append("postgresql")

        for p in proc_rows:
            nm = str(p.get("Name") or p.get("name") or "").strip().lower()
            path = str(p.get("Path") or p.get("path") or "").strip().lower()
            if "laragon" in nm or "laragon" in path:
                running_detected.append("Laragon")
            if nm == "dockerd":
                running_detected.append("Docker")

        detected = sorted(set([*installed_detected, *running_detected]))
        return {
            "services": svc_rows,
            "processes": proc_rows,
            "listen_ports": ports or [],
            "commands": commands or [],
            "dirs": dirs or {},
            "iis_registry": iis_reg or {},
            "detected": detected,
            "installed_detected": sorted(set([x for x in installed_detected if x])),
            "running_detected": sorted(set([x for x in running_detected if x])),
        }

    try:
        res = subprocess.run(
            [
                "bash",
                "-lc",
                "lsof -iTCP -sTCP:LISTEN -P -n 2>/dev/null | head -n 200 || netstat -an 2>/dev/null | head -n 200 || true",
            ],
            capture_output=True,
            timeout=6,
        )
        txt = (res.stdout or b"").decode("utf-8", errors="ignore").strip()
        processes_txt = _run_bash_text(
            "ps -axo pid=,comm=,args= 2>/dev/null | egrep -i '(nginx|apache2|httpd|php-fpm|php|caddy|traefik|mysql|mysqld|mariadbd|postgres|redis-server|node|deno)' | head -n 200 || true",
            timeout_s=6,
        )
        services_txt = _run_bash_text(
            "command -v systemctl >/dev/null 2>&1 && systemctl list-units --type=service --all 2>/dev/null | egrep -i '(nginx|apache|httpd|php|mysql|mariadb|postgres|redis|caddy|traefik)' | head -n 120 || true",
            timeout_s=6,
        )
        running_detected: List[str] = []
        hay = "\n".join([txt or "", processes_txt or "", services_txt or ""]).lower()
        for token in [
            "nginx",
            "apache",
            "apache2",
            "httpd",
            "php",
            "php-fpm",
            "mysql",
            "mariadb",
            "postgres",
            "redis",
            "caddy",
            "traefik",
        ]:
            if token in hay:
                running_detected.append(token)
        running_detected = sorted(set([x for x in running_detected if x]))

        installed_hay = "\n".join(
            [
                "\n".join(
                    [
                        str((it or {}).get("name") or ""),
                        str((it or {}).get("id") or ""),
                        str((it or {}).get("source") or ""),
                    ]
                )
                for it in (installed or [])
                if isinstance(it, dict)
            ]
        ).lower()

        def _has_installed(*tokens: str) -> bool:
            return any(t and t.lower() in installed_hay for t in tokens)

        installed_detected: List[str] = []
        if _has_installed("docker"):
            installed_detected.append("docker")
        if _has_installed("docker-compose", "docker compose"):
            installed_detected.append("docker-compose")
        if _has_installed("nginx"):
            installed_detected.append("nginx")
        if _has_installed("apache2", "httpd", "apache"):
            installed_detected.append("apache")
        if _has_installed("tomcat"):
            installed_detected.append("tomcat")
        if _has_installed("caddy"):
            installed_detected.append("caddy")
        if _has_installed("litespeed", "openlitespeed"):
            installed_detected.append("litespeed")
        if _has_installed("servbay"):
            installed_detected.append("servbay")
        if _has_installed("xampp"):
            installed_detected.append("xampp")
        if _has_installed("mysql"):
            installed_detected.append("mysql")
        if _has_installed("mariadb"):
            installed_detected.append("mariadb")
        if _has_installed("postgres"):
            installed_detected.append("postgres")

        if sys.platform == "darwin":
            docker_app = _run_bash_text("test -d '/Applications/Docker.app' && echo yes || true", timeout_s=3).strip()
            servbay_app = _run_bash_text("test -d '/Applications/ServBay.app' && echo yes || true", timeout_s=3).strip()
            if docker_app:
                installed_detected.append("docker")
            if servbay_app:
                installed_detected.append("servbay")

        installed_detected = sorted(set([x for x in installed_detected if x]))
        detected = sorted(set([*installed_detected, *running_detected]))
        return {
            "listen_summary": txt,
            "processes_summary": processes_txt,
            "services_summary": services_txt,
            "detected": detected,
            "installed_detected": installed_detected,
            "running_detected": running_detected,
        }
    except Exception:
        return {}


def _collect_powershell_json(command: str, timeout_s: int = 10) -> Any:
    if sys.platform != "win32":
        return None
    cmd = (command or "").strip()
    if not cmd:
        return None
    try:
        res = subprocess.run(
            ["powershell", "-NoProfile", "-Command", cmd],
            capture_output=True,
            timeout=max(1, int(timeout_s)),
        )
    except Exception:
        return None
    out = _decode_best_effort(res.stdout or b"").strip()
    if not out:
        return None
    try:
        return json.loads(out)
    except Exception:
        return None


def _fmt_bytes_gib(value: Any) -> str:
    try:
        n = int(value)
    except Exception:
        return ""
    if n <= 0:
        return ""
    return f"{(n / (1024 ** 3)):.1f} GiB"


def _collect_bios_info() -> Dict[str, Any]:
    obj = _collect_powershell_json(
        "Get-CimInstance Win32_BIOS | Select-Object Manufacturer, SMBIOSBIOSVersion, ReleaseDate | ConvertTo-Json -Compress",
        timeout_s=10,
    )
    if not isinstance(obj, dict):
        return {}
    return {
        "manufacturer": str(obj.get("Manufacturer") or "").strip(),
        "version": str(obj.get("SMBIOSBIOSVersion") or "").strip(),
        "release_date": str(obj.get("ReleaseDate") or "").strip(),
    }


def _collect_disks_info() -> List[Dict[str, Any]]:
    if sys.platform == "win32":
        obj = _collect_powershell_json(
            'Get-CimInstance Win32_LogicalDisk -Filter "DriveType=3" | Select-Object DeviceID, VolumeName, FileSystem, Size, FreeSpace | ConvertTo-Json -Compress',
            timeout_s=10,
        )
        items: List[Dict[str, Any]] = []
        if isinstance(obj, dict):
            obj = [obj]
        if not isinstance(obj, list):
            return items
        for row in obj:
            if not isinstance(row, dict):
                continue
            device_id = str(row.get("DeviceID") or "").strip()
            if not device_id:
                continue
            _size_s = str(row.get("Size") or "").strip()
            _free_s = str(row.get("FreeSpace") or "").strip()
            items.append(
                {
                    "device_id": device_id,
                    "volume_name": str(row.get("VolumeName") or "").strip(),
                    "file_system": str(row.get("FileSystem") or "").strip(),
                    "size_bytes": int(_size_s) if _size_s.isdigit() else None,
                    "free_bytes": int(_free_s) if _free_s.isdigit() else None,
                }
            )
        return items

    df_map = _collect_df_bytes_map(timeout_s=6)
    if sys.platform.startswith("linux"):
        lsblk = _collect_linux_lsblk_json(timeout_s=8)
        out: List[Dict[str, Any]] = []
        if isinstance(lsblk, dict) and isinstance(lsblk.get("blockdevices"), list):
            stack = list(lsblk.get("blockdevices") or [])
            while stack:
                node = stack.pop(0)
                if not isinstance(node, dict):
                    continue
                for child in node.get("children") or []:
                    stack.append(child)
                mount = node.get("mountpoint")
                if not mount:
                    continue
                mp = str(mount)
                df_row = df_map.get(mp) or {}
                kname = str(node.get("kname") or node.get("name") or "").strip()
                dev = df_row.get("device_id") or (
                    f"/dev/{kname}" if kname and not kname.startswith("/") else kname
                )
                fstype = str(
                    node.get("fstype") or df_row.get("file_system") or ""
                ).strip()
                size_b = df_row.get("size_bytes")
                if not isinstance(size_b, int):
                    try:
                        size_b = (
                            int(node.get("size"))
                            if node.get("size") is not None
                            else None
                        )
                    except Exception:
                        size_b = None
                free_b = df_row.get("free_bytes")
                label = str(node.get("uuid") or node.get("model") or "").strip()
                out.append(
                    {
                        "device_id": str(dev or "").strip(),
                        "volume_name": label,
                        "file_system": fstype,
                        "size_bytes": size_b,
                        "free_bytes": free_b if isinstance(free_b, int) else None,
                    }
                )
        if out:
            return out
    out: List[Dict[str, Any]] = []
    for mp, row in df_map.items():
        if not isinstance(row, dict):
            continue
        out.append(
            {
                "device_id": str(row.get("device_id") or "").strip(),
                "volume_name": str(mp).strip(),
                "file_system": str(row.get("file_system") or "").strip(),
                "size_bytes": row.get("size_bytes")
                if isinstance(row.get("size_bytes"), int)
                else None,
                "free_bytes": row.get("free_bytes")
                if isinstance(row.get("free_bytes"), int)
                else None,
            }
        )
    return out


def _build_system_profile(user_id: int) -> Dict[str, Any]:
    os_name = platform.system()
    os_release = platform.release()
    os_version = platform.version()
    machine = platform.machine()
    py = sys.version.split(" ")[0]
    total_mem = _get_total_memory_bytes()
    systeminfo_txt = _collect_systeminfo_text(timeout_s=12)
    if systeminfo_txt and len(systeminfo_txt) > SYSTEM_PROFILE_MAX_CHARS:
        systeminfo_txt = systeminfo_txt[:SYSTEM_PROFILE_MAX_CHARS] + "\n…"
    bios = _collect_bios_info()
    disks = _collect_disks_info()
    df_texts = _collect_df_texts(timeout_s=6)
    mac_hw = _collect_macos_system_profiler_plist("SPHardwareDataType", timeout_s=10)
    mac_sw = _collect_macos_system_profiler_plist("SPSoftwareDataType", timeout_s=10)
    mac_diskutil = _collect_macos_diskutil_list_plist(timeout_s=8)
    linux_lsblk = _collect_linux_lsblk_json(timeout_s=8)
    mac_hw_small = _shrink_macos_system_profiler(mac_hw)
    mac_sw_small = _shrink_macos_system_profiler(mac_sw)
    mac_diskutil_small = _shrink_macos_diskutil(mac_diskutil)
    linux_lsblk_small = _shrink_linux_lsblk(linux_lsblk)
    installed = get_installed_software()
    web_services = _collect_web_services_info(installed)
    top_prod = _top20_productivity(installed)
    removed = list(_installed_removed)

    data = {
        "os_name": os_name,
        "os_release": os_release,
        "os_version": os_version,
        "machine": machine,
        "python": py,
        "total_memory_bytes": total_mem,
        "bios": bios,
        "disks": disks,
        "df": df_texts,
        "installed_software": installed,
        "top20_productivity": top_prod,
        "removed_since_last_scan": removed,
        "macos": {
            "system_profiler_hardware": mac_hw_small,
            "system_profiler_software": mac_sw_small,
            "diskutil_list": mac_diskutil_small,
        },
        "linux": {"lsblk": linux_lsblk_small},
        "web_services": web_services,
    }

    mem_line = ""
    if isinstance(total_mem, int) and total_mem > 0:
        gib = total_mem / (1024**3)
        mem_line = f"{gib:.1f} GiB"

    lines = [
        "# Perfil do sistema (local)",
        f"- Usuário (id): {user_id}",
        f"- Gerado em (UTC): {datetime.utcnow().isoformat()}",
        f"- SO: {os_name} {os_release}",
        f"- Build: {os_version}",
        f"- Arquitetura: {machine}",
        f"- Python: {py}",
        f"- Memória total: {mem_line}" if mem_line else None,
    ]
    md = "\n".join([line for line in lines if line]).strip()
    if isinstance(bios, dict) and any(
        (bios.get("manufacturer"), bios.get("version"), bios.get("release_date"))
    ):
        bios_lines = [
            "## BIOS",
            (
                f"- Fabricante: {bios.get('manufacturer')}"
                if bios.get("manufacturer")
                else None
            ),
            f"- Versão: {bios.get('version')}" if bios.get("version") else None,
            f"- Data: {bios.get('release_date')}" if bios.get("release_date") else None,
        ]
        md = f"{md}\n\n" + "\n".join([line for line in bios_lines if line]).strip()
    if isinstance(disks, list) and disks:
        disk_lines = [
            "## Discos",
            "| Unidade | Label | FS | Total | Livre |",
            "|---|---|---|---:|---:|",
        ]
        for d in disks:
            if not isinstance(d, dict):
                continue
            disk_lines.append(
                f"| {d.get('device_id') or ''} | {d.get('volume_name') or ''} | {d.get('file_system') or ''} | {_fmt_bytes_gib(d.get('size_bytes'))} | {_fmt_bytes_gib(d.get('free_bytes'))} |"
            )
        md = f"{md}\n\n" + "\n".join(disk_lines).strip()
    if systeminfo_txt:
        md = f"{md}\n\n## systeminfo\n\n{systeminfo_txt}".strip()
    if isinstance(df_texts, dict) and (df_texts.get("df_h") or df_texts.get("df_H")):
        md_parts: List[str] = []
        if df_texts.get("df_h"):
            md_parts.append("## df -h\n\n```")
            md_parts.append(_truncate_text(str(df_texts.get("df_h") or ""), 4000))
            md_parts.append("```")
        if df_texts.get("df_H"):
            md_parts.append("## df -H\n\n```")
            md_parts.append(_truncate_text(str(df_texts.get("df_H") or ""), 4000))
            md_parts.append("```")
        md = f"{md}\n\n" + "\n\n".join([p for p in md_parts if p]).strip()
    if sys.platform == "darwin" and (mac_hw_small or mac_diskutil_small):
        extra: List[str] = []
        if mac_hw_small:
            extra.append("## system_profiler SPHardwareDataType (xml)\n\n```")
            extra.append(
                _truncate_text(
                    json.dumps(mac_hw_small, ensure_ascii=False)
                    if mac_hw_small is not None
                    else "",
                    6000,
                )
            )
            extra.append("```")
        if mac_diskutil_small:
            extra.append("## diskutil list -plist\n\n```")
            extra.append(
                _truncate_text(
                    json.dumps(mac_diskutil_small, ensure_ascii=False)
                    if mac_diskutil_small is not None
                    else "",
                    6000,
                )
            )
            extra.append("```")
        md = f"{md}\n\n" + "\n\n".join([x for x in extra if x]).strip()
    if sys.platform.startswith("linux") and linux_lsblk_small:
        md = (
            f"{md}\n\n## lsblk -J\n\n```"
            f"\n{_truncate_text(json.dumps(linux_lsblk_small, ensure_ascii=False) if linux_lsblk_small is not None else '', 6000)}"
            f"\n```"
        ).strip()
    if web_services:
        svc_lines: List[str] = ["## Serviços web locais"]
        if isinstance(web_services, dict) and isinstance(web_services.get("installed_detected"), list) and web_services.get("installed_detected"):
            svc_lines.append(
                "- Instalado: "
                + ", ".join([str(x) for x in web_services.get("installed_detected") if x])
            )
        if isinstance(web_services, dict) and isinstance(web_services.get("running_detected"), list) and web_services.get("running_detected"):
            svc_lines.append(
                "- Em execução: "
                + ", ".join([str(x) for x in web_services.get("running_detected") if x])
            )
        if isinstance(web_services, dict) and isinstance(
            web_services.get("services"), list
        ):
            for s in web_services.get("services") or []:
                if not isinstance(s, dict):
                    continue
                name = str(s.get("Name") or s.get("name") or "").strip()
                status = str(s.get("Status") or s.get("status") or "").strip()
                if name:
                    svc_lines.append(f"- {name}: {status}".strip())
        if isinstance(web_services, dict) and isinstance(
            web_services.get("listen_ports"), list
        ):
            ports_list = []
            for p in web_services.get("listen_ports") or []:
                if not isinstance(p, dict):
                    continue
                port = p.get("LocalPort") or p.get("local_port")
                if port is None:
                    continue
                ports_list.append(str(port))
            ports_list = sorted(set([x for x in ports_list if x.isdigit()]))
            if ports_list:
                svc_lines.append(f"- Portas em escuta: {', '.join(ports_list)}")
        if isinstance(web_services, dict) and web_services.get("services_summary"):
            svc_lines.append("")
            svc_lines.append("```")
            svc_lines.append(str(web_services.get("services_summary") or "")[:800])
            svc_lines.append("```")
        if isinstance(web_services, dict) and web_services.get("processes_summary"):
            svc_lines.append("")
            svc_lines.append("```")
            svc_lines.append(str(web_services.get("processes_summary") or "")[:800])
            svc_lines.append("```")
        if isinstance(web_services, dict) and web_services.get("listen_summary"):
            svc_lines.append("")
            svc_lines.append("```")
            svc_lines.append(str(web_services.get("listen_summary") or "")[:800])
            svc_lines.append("```")
        md = f"{md}\n\n" + "\n".join([x for x in svc_lines if x]).strip()
    if isinstance(top_prod, list) and top_prod:
        md_lines = ["## Softwares de produtividade (TOP 20)"]
        for it in top_prod:
            nm = str((it or {}).get("name") or "").strip()
            pid = str((it or {}).get("id") or "").strip()
            ver = str((it or {}).get("version") or "").strip()
            if nm:
                label = nm
                if ver:
                    label = f"{label} {ver}"
                if pid:
                    label = f"{label} [{pid}]"
                md_lines.append(f"- {label}")
        md = f"{md}\n\n" + "\n".join(md_lines).strip()
    if isinstance(removed, list) and removed:
        md_lines = ["## Softwares removidos desde o último scan"]
        for it in removed[:20]:
            nm = str((it or {}).get("name") or "").strip()
            pid = str((it or {}).get("id") or "").strip()
            ver = str((it or {}).get("version") or "").strip()
            if nm:
                label = nm
                if ver:
                    label = f"{label} {ver}"
                if pid:
                    label = f"{label} [{pid}]"
                md_lines.append(f"- {label}")
        md = f"{md}\n\n" + "\n".join(md_lines).strip()
    return {"markdown": md, "data": data}


def _format_system_profile_summary(profile_data: Dict[str, Any]) -> str:
    if not profile_data:
        return ""
    os_name = str(profile_data.get("os_name") or "")
    os_release = str(profile_data.get("os_release") or "")
    os_version = str(profile_data.get("os_version") or "")
    machine = str(profile_data.get("machine") or "")
    mem = profile_data.get("total_memory_bytes")
    mem_line = ""
    if isinstance(mem, int) and mem > 0:
        mem_line = f"{(mem / (1024 ** 3)):.1f} GiB RAM"
    parts = [
        p
        for p in [
            f"{os_name} {os_release}".strip(),
            f"build {os_version}".strip(),
            machine,
            mem_line,
        ]
        if p
    ]
    return " • ".join(parts).strip()


def _is_system_profile_detail_query(text: str) -> bool:
    t = (text or "").strip().lower()
    if not t:
        return False
    patterns = [
        r"\bbios\b",
        r"\buefi\b",
        r"\bplaca[-\s]?m[ãa]e\b",
        r"\bmotherboard\b",
        r"\b(hd|hdd|ssd)\b",
        r"\bdiscos?\b",
        r"\barmazenamento\b",
        r"\bstorage\b",
        r"\bdrive\b",
        r"\bvolumes?\b",
        r"\blaragon\b",
        r"\bapache\b",
        r"\bnginx\b",
        r"\biis\b",
        r"\bw3svc\b",
        r"\bporta(s)?\b",
        r"\bport\b",
        r"\bservi[cç]os?\b",
        r"\bservices?\b",
    ]
    return any(re.search(p, t) for p in patterns)


def _format_system_profile_details(profile_data: Dict[str, Any]) -> str:
    if not profile_data:
        return ""
    bios = profile_data.get("bios")
    disks = profile_data.get("disks")
    web_services = profile_data.get("web_services")
    parts: List[str] = []
    if isinstance(bios, dict) and any(
        (bios.get("manufacturer"), bios.get("version"), bios.get("release_date"))
    ):
        b = []
        if bios.get("manufacturer"):
            b.append(str(bios.get("manufacturer")))
        if bios.get("version"):
            b.append(str(bios.get("version")))
        if bios.get("release_date"):
            b.append(str(bios.get("release_date")))
        if b:
            parts.append("BIOS: " + " • ".join([x for x in b if x]).strip())
    if isinstance(disks, list) and disks:
        d_lines: List[str] = []
        for d in disks:
            if not isinstance(d, dict):
                continue
            dev = str(d.get("device_id") or "").strip()
            if not dev:
                continue
            total = _fmt_bytes_gib(d.get("size_bytes"))
            free = _fmt_bytes_gib(d.get("free_bytes"))
            fs = str(d.get("file_system") or "").strip()
            label = str(d.get("volume_name") or "").strip()
            extras = " • ".join(
                [
                    x
                    for x in [
                        label,
                        fs,
                        f"{total} total" if total else "",
                        f"{free} livre" if free else "",
                    ]
                    if x
                ]
            ).strip()
            d_lines.append(f"{dev}: {extras}".strip(" :"))
        if d_lines:
            parts.append("Discos: " + " | ".join(d_lines))
    if web_services:
        try:
            if isinstance(web_services, dict) and isinstance(
                web_services.get("services"), list
            ):
                svc = []
                for s in web_services.get("services") or []:
                    if not isinstance(s, dict):
                        continue
                    name = str(s.get("Name") or s.get("name") or "").strip()
                    status = str(s.get("Status") or s.get("status") or "").strip()
                    if name and status:
                        svc.append(f"{name}={status}")
                if svc:
                    parts.append("Serviços: " + " • ".join(svc[:10]))
            if isinstance(web_services, dict) and isinstance(
                web_services.get("listen_ports"), list
            ):
                ports_list = []
                for p in web_services.get("listen_ports") or []:
                    if not isinstance(p, dict):
                        continue
                    port = p.get("LocalPort") or p.get("local_port")
                    if port is None:
                        continue
                    ports_list.append(str(port))
                ports_list = sorted(set([x for x in ports_list if x.isdigit()]))
                if ports_list:
                    parts.append("Portas: " + ", ".join(ports_list[:20]))
        except Exception:
            pass
    return "\n".join(parts).strip()


def _system_profile_direct_answer(
    *, user_message: str, profile_data: Dict[str, Any]
) -> str:
    t = (user_message or "").strip().lower()
    want_bios = any(
        x in t for x in ["bios", "uefi", "placa-mãe", "placa mae", "motherboard"]
    )
    want_disks = any(
        x in t
        for x in [
            "hd",
            "hdd",
            "ssd",
            "disco",
            "armazenamento",
            "storage",
            "drive",
            "volume",
        ]
    )
    want_services = bool(
        re.search(r"\b(laragon|apache|nginx|iis|w3svc|servi[cç]os?|services?)\b", t)
    )
    want_ports = bool(re.search(r"\b(porta(s)?|port)\b", t))
    bios = profile_data.get("bios") if isinstance(profile_data, dict) else None
    disks = profile_data.get("disks") if isinstance(profile_data, dict) else None
    web_services = (
        profile_data.get("web_services") if isinstance(profile_data, dict) else None
    )

    lines: List[str] = []
    if want_bios or (not want_bios and not want_disks):
        if isinstance(bios, dict) and any(
            (bios.get("manufacturer"), bios.get("version"), bios.get("release_date"))
        ):
            lines.append("BIOS:")
            if bios.get("manufacturer"):
                lines.append(f"- Fabricante: {bios.get('manufacturer')}")
            if bios.get("version"):
                lines.append(f"- Versão: {bios.get('version')}")
            if bios.get("release_date"):
                lines.append(f"- Data: {bios.get('release_date')}")
        elif want_bios:
            lines.append("Não encontrei dados de BIOS no perfil do sistema salvo.")

    if want_disks or (not want_bios and not want_disks):
        if isinstance(disks, list) and disks:
            lines.append("Discos (armazenamento):")
            for d in disks:
                if not isinstance(d, dict):
                    continue
                dev = str(d.get("device_id") or "").strip()
                if not dev:
                    continue
                label = str(d.get("volume_name") or "").strip()
                fs = str(d.get("file_system") or "").strip()
                total = _fmt_bytes_gib(d.get("size_bytes"))
                free = _fmt_bytes_gib(d.get("free_bytes"))
                extras = " • ".join(
                    [
                        x
                        for x in [
                            label,
                            fs,
                            f"{total} total" if total else "",
                            f"{free} livre" if free else "",
                        ]
                        if x
                    ]
                ).strip()
                lines.append(f"- {dev}: {extras}".strip(" :"))
        elif want_disks:
            lines.append("Não encontrei dados de disco no perfil do sistema salvo.")

    if want_services or want_ports:
        detected = []
        services_lines: List[str] = []
        ports_list: List[str] = []
        try:
            if isinstance(web_services, dict):
                detected = [
                    str(x).strip()
                    for x in (web_services.get("detected") or [])
                    if str(x or "").strip()
                ]
                if isinstance(web_services.get("services"), list):
                    for s in web_services.get("services") or []:
                        if not isinstance(s, dict):
                            continue
                        name = str(s.get("DisplayName") or s.get("display_name") or s.get("Name") or s.get("name") or "").strip()
                        status = str(s.get("Status") or s.get("status") or "").strip()
                        if name:
                            services_lines.append(
                                f"- {name}" + (f" • {status}" if status else "")
                            )
                if isinstance(web_services.get("listen_ports"), list):
                    for p in web_services.get("listen_ports") or []:
                        if not isinstance(p, dict):
                            continue
                        port = p.get("LocalPort") or p.get("local_port")
                        if port is None:
                            continue
                        ports_list.append(str(port))
        except Exception:
            detected = []
            services_lines = []
            ports_list = []
        ports_list = sorted(set([x for x in ports_list if x.isdigit()]))

        if detected or services_lines or ports_list:
            lines.append("Serviços web:")
            if detected:
                lines.append("- Detectados: " + ", ".join(detected[:10]))
            if want_ports and ports_list:
                lines.append("- Portas em LISTEN (amostra): " + ", ".join(ports_list[:20]))
            if want_services and services_lines:
                lines.extend(services_lines[:12])
        else:
            lines.append("Não encontrei dados de serviços/portas no perfil do sistema salvo.")

    return "\n".join([line for line in lines if line]).strip()


def _get_user_api_key(user_id: int, provider: Optional[str] = None) -> Optional[str]:
    prov = str(provider or "").strip().lower()
    if prov:
        ct2 = get_active_user_llm_provider_key_ciphertext(int(user_id), prov)
        if ct2:
            raw2 = _dpapi_unprotect_text(ct2) or ""
            key2 = _sanitize_api_key(raw2)
            if key2:
                return key2

    ct = get_user_api_key_ciphertext(int(user_id))
    if not ct:
        return None
    raw = _dpapi_unprotect_text(ct) or ""
    key = _sanitize_api_key(raw)
    return key or None


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
    # Fallback quick scan if custom order missed
    for p in ["openai", "groq", "gemini", "openrouter"]:
        if _get_env_api_key_for_provider(p):
            return p
    return None

def _is_allowed_write_root(base_path: str) -> bool:
    base_abs = os.path.abspath(base_path or "")
    user_home = os.path.abspath(os.path.expanduser("~"))
    if base_abs.startswith(user_home.rstrip("\\/") + os.sep) or base_abs == user_home:
        return True
    project_root = os.path.abspath(str(BASE_DIR))
    if (
        base_abs.startswith(project_root.rstrip("\\/") + os.sep)
        or base_abs == project_root
    ):
        return True
    return False


def _default_landing_bundle(base_path: str) -> Dict[str, Any]:
    index_html = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Landing Page</title>
  <link rel="stylesheet" href="style.css" />
</head>
<body>
  <header class="header">
    <div class="container">
      <div class="brand">Projeto</div>
      <nav class="nav">
        <a href="#features">Recursos</a>
        <a href="#cta">Começar</a>
      </nav>
    </div>
  </header>

  <main>
    <section class="hero">
      <div class="container">
        <h1>Uma ideia clara, um produto simples</h1>
        <p>Uma landing page pronta para você ajustar com o seu conteúdo.</p>
        <div class="actions">
          <a class="button primary" href="#cta">Quero ver</a>
          <a class="button secondary" href="#features">Saiba mais</a>
        </div>
      </div>
    </section>

    <section id="features" class="section">
      <div class="container grid">
        <div class="card">
          <h2>Objetivo</h2>
          <p>Explique em 1 frase para quem é e o que resolve.</p>
        </div>
        <div class="card">
          <h2>Benefício</h2>
          <p>Destaque o ganho principal: tempo, dinheiro ou clareza.</p>
        </div>
        <div class="card">
          <h2>Próximo passo</h2>
          <p>Direcione para um contato, cadastro ou demonstração.</p>
        </div>
      </div>
    </section>

    <section id="cta" class="section cta">
      <div class="container">
        <h2>Quer evoluir esta página?</h2>
        <p>Diga o nome do projeto, público-alvo e 3 recursos principais.</p>
        <a class="button primary" href="mailto:contato@exemplo.com">Fale comigo</a>
      </div>
    </section>
  </main>

  <footer class="footer">
    <div class="container">
      <span>Feito localmente</span>
    </div>
  </footer>
</body>
</html>
"""
    style_css = """:root {
  --bg: #0b1020;
  --panel: rgba(255, 255, 255, 0.06);
  --text: #e7ecff;
  --muted: rgba(231, 236, 255, 0.72);
  --primary: #6d5efc;
  --primary2: #22c55e;
}

* { box-sizing: border-box; }
html, body { height: 100%; }
body {
  margin: 0;
  font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif;
  color: var(--text);
  background: radial-gradient(1200px 600px at 20% 10%, rgba(109, 94, 252, 0.35), transparent 55%),
              radial-gradient(900px 500px at 80% 20%, rgba(34, 197, 94, 0.25), transparent 55%),
              var(--bg);
}

a { color: inherit; text-decoration: none; }

.container {
  max-width: 1000px;
  margin: 0 auto;
  padding: 0 18px;
}

.header {
  position: sticky;
  top: 0;
  background: rgba(11, 16, 32, 0.72);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  z-index: 10;
}

.header .container {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 64px;
}

.brand { font-weight: 700; letter-spacing: 0.2px; }

.nav { display: flex; gap: 14px; color: var(--muted); }
.nav a:hover { color: var(--text); }

.hero { padding: 64px 0 28px; }
.hero h1 { font-size: 42px; line-height: 1.1; margin: 0; }
.hero p { margin: 14px 0 0; color: var(--muted); max-width: 62ch; }

.actions { margin-top: 22px; display: flex; gap: 12px; flex-wrap: wrap; }

.button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 12px 16px;
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.12);
  background: rgba(255, 255, 255, 0.06);
}
.button.primary {
  background: linear-gradient(135deg, var(--primary), var(--primary2));
  border-color: transparent;
  color: #0b1020;
  font-weight: 700;
}
.button.secondary:hover { border-color: rgba(255, 255, 255, 0.25); }

.section { padding: 28px 0 56px; }
.grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px;
}
.card {
  background: var(--panel);
  border: 1px solid rgba(255, 255, 255, 0.10);
  border-radius: 16px;
  padding: 18px;
}
.card h2 { margin: 0; font-size: 18px; }
.card p { margin: 10px 0 0; color: var(--muted); }

.cta .container {
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.10);
  border-radius: 18px;
  padding: 22px;
}
.cta h2 { margin: 0; }
.cta p { margin: 10px 0 16px; color: var(--muted); }

.footer {
  border-top: 1px solid rgba(255, 255, 255, 0.08);
  padding: 20px 0;
  color: var(--muted);
}

@media (max-width: 880px) {
  .grid { grid-template-columns: 1fr; }
  .hero h1 { font-size: 34px; }
}
"""
    return {
        "base_path": base_path,
        "files": [
            {"path": "index.html", "content": index_html},
            {"path": "style.css", "content": style_css},
        ],
    }


def _format_recent_chat_context(messages: List[Dict[str, Any]], limit: int = 8) -> str:
    if not messages:
        return ""
    recent = messages[-max(1, int(limit)) :]
    lines: List[str] = []
    for m in recent:
        role = str(m.get("role") or "")
        content = str(m.get("content") or "")
        content = content.strip().replace("\r", " ").replace("\n", " ")
        if len(content) > 280:
            content = content[:280] + "…"
        if not content:
            continue
        if role == "user":
            lines.append(f"Usuário: {content}")
        elif role == "assistant":
            lines.append(f"Assistente: {content}")
    return "\n".join(lines).strip()


def _needs_web_retrieval(user_message: str) -> bool:
    msg = (user_message or "").lower()
    if re.search(r"https?://", msg):
        return True
    if any(
        k in msg for k in ("atualidade", "atualmente", "hoje", "agora", "neste momento")
    ):
        return True
    if re.search(r"\b20(2[0-9]|3[0-9])\b", msg):
        return True
    if any(
        k in msg
        for k in (
            "mais caro",
            "probabilidade",
            "odds",
            "elenco",
            "joga",
            "transfer",
            "campeonato",
        )
    ):
        return True
    if any(
        k in msg
        for k in (
            "não procede",
            "nao procede",
            "isso está errado",
            "isso esta errado",
            "informação não procede",
            "informacao nao procede",
        )
    ):
        return True
    return False


async def _web_retrieve_context(query: str) -> str:
    if not ENABLE_WEB_RETRIEVAL or not query:
        return ""
    url = "https://api.duckduckgo.com/"
    params = {
        "q": query,
        "format": "json",
        "no_html": "1",
        "skip_disambig": "1",
    }
    timeout = aiohttp.ClientTimeout(total=max(1, WEB_RETRIEVAL_TIMEOUT_S))
    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url, params=params) as resp:
                if resp.status != 200:
                    return ""
                data = await resp.json()
    except Exception:
        return ""
    abstract = str((data or {}).get("AbstractText") or "").strip()
    heading = str((data or {}).get("Heading") or "").strip()
    related = (data or {}).get("RelatedTopics") or []
    related_texts: List[str] = []
    for item in related[:6]:
        if isinstance(item, dict) and "Text" in item:
            t = str(item.get("Text") or "").strip()
            if t:
                related_texts.append(t)
        elif isinstance(item, dict) and "Topics" in item:
            topics = item.get("Topics")
            if not isinstance(topics, list):
                continue
            for sub in topics[:3]:
                if isinstance(sub, dict) and "Text" in sub:
                    t = str(sub.get("Text") or "").strip()
                    if t:
                        related_texts.append(t)
    parts: List[str] = []
    title = heading or "Resultado"
    if abstract:
        parts.append(f"{title}: {abstract}")
    for t in related_texts[:6]:
        parts.append(f"- {t}")
    out = "\n".join(parts).strip()
    if len(out) > 1400:
        out = out[:1400] + "…"
    return out


def _extract_urls(text: str) -> List[str]:
    if not text:
        return []
    urls = re.findall(r"https?://[^\s<>()\"']+", str(text), flags=re.IGNORECASE)
    cleaned: List[str] = []
    for u in urls:
        u = str(u or "").strip().strip("`'\".,);]}>")
        if not u:
            continue
        if u.lower().startswith("http://"):
            continue
        if u not in cleaned:
            cleaned.append(u)
    return cleaned


def _url_fetch_diagnostics(text: str) -> Dict[str, Any]:
    urls = _extract_urls(text)
    allowed: List[str] = []
    blocked: List[str] = []
    for u in urls:
        if _is_allowed_fetch_url(u):
            allowed.append(u)
        else:
            blocked.append(u)
    hosts_blocked: List[str] = []
    for u in blocked:
        try:
            h = str(urlparse(u).hostname or "").lower().strip()
        except Exception:
            h = ""
        if h and h not in hosts_blocked:
            hosts_blocked.append(h)
    return {
        "urls": urls,
        "allowed_urls": allowed,
        "blocked_urls": blocked,
        "blocked_hosts": hosts_blocked,
    }


def _is_allowed_fetch_url(url: str) -> bool:
    if not url:
        return False
    try:
        parsed = urlparse(url)
    except Exception:
        return False
    scheme = str(parsed.scheme or "").lower().strip()
    if scheme != "https":
        return False
    host = str(parsed.hostname or "").lower().strip()
    if not host:
        return False
    if host in ("localhost",):
        return False
    if re.match(r"^(127\.|10\.|192\.168\.|172\.(1[6-9]|2[0-9]|3[0-1])\.)", host):
        return False
    if host == "0.0.0.0":
        return False
    if URL_FETCH_ALLOW_HOSTS:
        if not any(host == h or host.endswith("." + h) for h in URL_FETCH_ALLOW_HOSTS):
            return False
    return True


async def _fetch_text_url(url: str, *, timeout_s: float, max_chars: int) -> str:
    timeout = aiohttp.ClientTimeout(total=max(1, float(timeout_s)))
    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(
                url,
                headers={
                    "User-Agent": "OpenSlap/1.0 (+https://openslap.test)",
                    "Accept": "text/plain,text/markdown,text/html,application/json;q=0.9,*/*;q=0.1",
                },
            ) as resp:
                if resp.status != 200:
                    return ""
                ct = str(resp.headers.get("content-type") or "").lower().strip()
                if ct:
                    is_textual = (
                        ct.startswith("text/")
                        or "application/json" in ct
                        or ct.endswith("+json")
                        or "application/xml" in ct
                        or ct.endswith("+xml")
                        or "application/xhtml+xml" in ct
                    )
                    if not is_textual:
                        return ""
                max_bytes = 0
                try:
                    max_bytes = int(max(4096, min(2_000_000, int(max_chars) * 4)))
                except Exception:
                    max_bytes = 200_000
                raw_bytes = await resp.content.read(max_bytes + 1)
                raw = raw_bytes.decode("utf-8", errors="ignore")
    except Exception:
        return ""
    txt = str(raw or "").strip()
    if not txt:
        return ""
    if max_chars and len(txt) > int(max_chars):
        txt = txt[: int(max_chars)] + "…"
    return txt


async def _github_repo_context(url: str, *, timeout_s: float, max_chars: int) -> str:
    try:
        parsed = urlparse(url)
        path = str(parsed.path or "").strip("/")
        parts = [p for p in path.split("/") if p]
        if len(parts) < 2:
            return ""
        owner, repo = parts[0], parts[1]
        if repo.endswith(".git"):
            repo = repo[: -4]
    except Exception:
        return ""

    api_base = "https://api.github.com"
    timeout = aiohttp.ClientTimeout(total=max(1, float(timeout_s)))
    meta: Dict[str, Any] = {}
    readme_txt = ""
    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(
                f"{api_base}/repos/{owner}/{repo}",
                headers={"User-Agent": "OpenSlap/1.0 (+https://openslap.test)"},
            ) as resp:
                if resp.status == 200:
                    meta = await resp.json()
            async with session.get(
                f"{api_base}/repos/{owner}/{repo}/readme",
                headers={
                    "User-Agent": "OpenSlap/1.0 (+https://openslap.test)",
                    "Accept": "application/vnd.github.raw",
                },
            ) as resp:
                if resp.status == 200:
                    readme_txt = await resp.text(errors="ignore")
    except Exception:
        meta = meta or {}
        readme_txt = readme_txt or ""

    lines: List[str] = []
    full_name = str(meta.get("full_name") or "").strip() if isinstance(meta, dict) else ""
    desc = str(meta.get("description") or "").strip() if isinstance(meta, dict) else ""
    stars = meta.get("stargazers_count") if isinstance(meta, dict) else None
    default_branch = str(meta.get("default_branch") or "").strip() if isinstance(meta, dict) else ""
    html_url = str(meta.get("html_url") or "").strip() if isinstance(meta, dict) else ""
    if full_name:
        lines.append(f"Repositório: {full_name}")
    if html_url:
        lines.append(f"URL: {html_url}")
    if desc:
        lines.append(f"Descrição: {desc}")
    if isinstance(stars, int):
        lines.append(f"Stars: {stars}")
    if default_branch:
        lines.append(f"Branch padrão: {default_branch}")
    if readme_txt and str(readme_txt).strip():
        readme_txt = str(readme_txt).strip()
        if max_chars and len(readme_txt) > int(max_chars):
            readme_txt = readme_txt[: int(max_chars)] + "…"
        lines.append("README (trecho):")
        lines.append(readme_txt)
    out = "\n".join([x for x in lines if x]).strip()
    return out


async def _url_fetch_context(user_message: str) -> str:
    if not ENABLE_URL_FETCH:
        return ""
    urls = _extract_urls(user_message)
    if not urls:
        return ""
    allowed = [u for u in urls if _is_allowed_fetch_url(u)]
    if not allowed:
        return ""

    parts: List[str] = []
    for u in allowed[:3]:
        try:
            parsed = urlparse(u)
            host = str(parsed.hostname or "").lower().strip()
            if host.endswith("github.com"):
                ctx = await _github_repo_context(
                    u, timeout_s=URL_FETCH_TIMEOUT_S, max_chars=max(2000, int(URL_FETCH_MAX_CHARS))
                )
            else:
                ctx = await _fetch_text_url(
                    u, timeout_s=URL_FETCH_TIMEOUT_S, max_chars=max(2000, int(URL_FETCH_MAX_CHARS))
                )
        except Exception:
            ctx = ""
        if ctx:
            parts.append(f"Fonte: {u}\n{ctx}".strip())
    out = "\n\n---\n\n".join([p for p in parts if p]).strip()
    if URL_FETCH_MAX_CHARS and len(out) > int(URL_FETCH_MAX_CHARS):
        out = out[: int(URL_FETCH_MAX_CHARS)] + "…"
    return out


def _write_files_bundle(bundle: Dict[str, Any]) -> Dict[str, Any]:
    base_path = str(bundle.get("base_path") or "").strip().strip("`\"' ,")
    files = bundle.get("files") or []
    if not base_path:
        raise Exception("FILES_JSON sem base_path")
    if not isinstance(files, list) or not files:
        raise Exception("FILES_JSON sem arquivos")
    if not _is_allowed_write_root(base_path):
        raise Exception("Destino não permitido para escrita")

    written: List[str] = []
    for f in files:
        if not isinstance(f, dict):
            continue
        rel_path = str(f.get("path") or "").strip().lstrip("\\/").replace("/", os.sep)
        content = f.get("content")
        if not rel_path or content is None:
            continue
        abs_path = _safe_join(base_path, rel_path)
        if not abs_path:
            raise Exception("Path inválido (travessia de diretório bloqueada)")
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        with open(abs_path, "w", encoding="utf-8") as fp:
            fp.write(str(content))
        written.append(abs_path)
    if not written:
        raise Exception("Nenhum arquivo válido para escrita")
    return {"base_path": base_path, "written": written}


def _format_rag_memory(items: List[Dict[str, Any]]) -> str:
    if not items:
        return ""
    lines: List[str] = []
    for it in items[:10]:
        src = str(it.get("src") or "")
        content = (
            str(it.get("content") or "").strip().replace("\r", " ").replace("\n", " ")
        )
        if not content:
            continue
        if len(content) > 240:
            content = content[:240] + "…"
        tag = "Chat" if src == "chat" else "SOUL"
        lines.append(f"- [{tag}] {content}")
    return "\n".join(lines).strip()


@app.get("/local/{delivery_id}")
@app.get("/local/{delivery_id}/")
async def local_delivery_index(delivery_id: str):
    info = delivery_registry.get(delivery_id)
    if not info:
        raise HTTPException(status_code=404, detail="Entrega não encontrada")
    base_path = str(info.get("base_path") or "")
    abs_path = _safe_join(base_path, "index.html")
    if not abs_path or not os.path.isfile(abs_path):
        raise HTTPException(status_code=404, detail="index.html não encontrado")
    media_type = mimetypes.guess_type(abs_path)[0] or "text/html"
    return FileResponse(abs_path, media_type=media_type)


@app.get("/local/{delivery_id}/{file_path:path}")
async def local_delivery_file(delivery_id: str, file_path: str):
    info = delivery_registry.get(delivery_id)
    if not info:
        raise HTTPException(status_code=404, detail="Entrega não encontrada")
    base_path = str(info.get("base_path") or "")
    safe_rel = (file_path or "").lstrip("\\/")
    abs_path = _safe_join(base_path, safe_rel)
    if not abs_path or not os.path.isfile(abs_path):
        raise HTTPException(status_code=404, detail="Arquivo não encontrado")
    media_type = mimetypes.guess_type(abs_path)[0] or "application/octet-stream"
    return FileResponse(abs_path, media_type=media_type)


def _build_soul_markdown(
    soul_data: Dict[str, Any], events: List[Dict[str, Any]]
) -> str:
    profile = soul_data or {}
    lines: List[str] = []
    lines.append("# SOUL")
    lines.append("")
    lines.append("## Perfil")
    lines.append("")
    ordered_fields = [
        ("Nome", "name"),
        ("Faixa etária", "age_range"),
        ("Sexo", "gender"),
        ("Escolaridade", "education"),
        ("Interesses", "interests"),
        ("Objetivos", "goals"),
        ("Preferências de aprendizado", "learning_style"),
        ("Idioma", "language"),
        ("Público", "audience"),
        ("Observações", "notes"),
    ]
    for label, key in ordered_fields:
        value = profile.get(key)
        if value is None:
            continue
        if isinstance(value, list):
            value = ", ".join([str(v) for v in value if str(v).strip()])
        value_str = str(value).strip()
        if value_str:
            lines.append(f"- {label}: {value_str}")
    lines.append("")
    if events:
        lines.append("## Atualizações")
        lines.append("")
        for ev in events:
            created_at = str(ev.get("created_at") or "").strip()
            source = str(ev.get("source") or "unknown").strip()
            content = str(ev.get("content") or "").strip()
            if not content:
                continue
            prefix = f"- {created_at} ({source}):" if created_at else f"- ({source}):"
            lines.append(prefix)
            lines.append(f"  {content}")
        lines.append("")
    return "\n".join(lines).strip() + "\n"


def _sanitize_llm_override_for_context(llm_override: Dict[str, Any]) -> Dict[str, Any]:
    safe = dict(llm_override or {})
    for k in ("api_key", "key", "keys", "token", "access_token", "authorization"):
        if k in safe:
            safe.pop(k, None)
    return safe


def _build_runtime_context_block(
    *,
    user_id: int,
    conversation_id: int,
    sec: Dict[str, Any],
    llm_override: Dict[str, Any],
) -> str:
    db_path = ""
    session_id = ""
    project_id = None
    try:
        db_path = str(get_db_path() or "")
        import sqlite3 as _sq_ctx

        with _sq_ctx.connect(db_path) as _c:
            row = _c.execute(
                "SELECT session_id, project_id FROM conversations WHERE id=?",
                (int(conversation_id),),
            ).fetchone()
            if row:
                session_id = str(row[0] or "")
                project_id = int(row[1]) if row[1] is not None else None
    except Exception:
        db_path = str(get_db_path() or "")
        session_id = ""
        project_id = None

    llm_safe = _sanitize_llm_override_for_context(llm_override or {})
    llm_mode = str(llm_safe.get("mode") or "").strip().lower()
    llm_provider = str(llm_safe.get("provider") or "").strip().lower()
    llm_model = str(llm_safe.get("model") or "").strip()
    llm_base_url = str(llm_safe.get("base_url") or "").strip()

    expert_ids = []
    try:
        expert_ids = [str(e.get("id") or "") for e in (moe_router.get_experts() or [])]
        expert_ids = [e for e in expert_ids if e]
    except Exception:
        expert_ids = []

    skill_ids = []
    try:
        skill_ids = [str(s.get("id") or "") for s in (get_user_skills(int(user_id)) or [])]
        skill_ids = [s for s in skill_ids if s]
    except Exception:
        skill_ids = []

    parts: List[str] = []
    parts.append("Runtime/system (uso interno):")
    parts.append(f"- os: {platform.system()} {platform.release()} ({platform.machine()})")
    parts.append(f"- sqlite_db: {db_path}" if db_path else "- sqlite_db: (desconhecido)")
    parts.append(f"- conversation_id: {int(conversation_id)}")
    if session_id:
        parts.append(f"- session_id: {session_id}")
    if project_id is not None:
        parts.append(f"- project_id: {int(project_id)}")
    parts.append(f"- security: sandbox={bool(sec.get('sandbox'))}, allow_connectors={bool(sec.get('allow_connectors'))}, allow_web={bool(sec.get('allow_web_retrieval'))}, allow_file_write={bool(sec.get('allow_file_write'))}")
    parts.append(f"- features: external_software={bool(ENABLE_EXTERNAL_SOFTWARE)}, memory_write={bool(ENABLE_MEMORY_WRITE)}, cac={bool(ENABLE_CAC)}")
    parts.append(f"- llm: mode={llm_mode or '(auto)'}, provider={llm_provider or '(auto)'}, model={llm_model or '(default)'}, base_url={llm_base_url or '(default)'}")
    if expert_ids:
        parts.append(f"- experts: {', '.join(expert_ids[:18])}{'…' if len(expert_ids) > 18 else ''}")
    if skill_ids:
        parts.append(f"- skills: {', '.join(skill_ids[:18])}{'…' if len(skill_ids) > 18 else ''}")
    parts.append("- rag: usa memórias do usuário (SQLite) como contexto de recuperação")
    return "\n".join(parts).strip()


def _friction_mode() -> str:
    return (os.getenv("SLAP_FRICTION_MODE", "disabled") or "disabled").strip().lower()


def _normalize_os(value: Optional[str]) -> str:
    if value:
        v = value.strip().lower()
        if v in ("win", "windows"):
            return "win"
        if v in ("mac", "darwin", "osx"):
            return "mac"
        if v in ("linux",):
            return "linux"
        return v
    sysname = platform.system().lower()
    if "windows" in sysname:
        return "win"
    if "darwin" in sysname:
        return "mac"
    if "linux" in sysname:
        return "linux"
    return sysname or "unknown"


def _default_runtime(value: Optional[str]) -> str:
    if value:
        return value
    return f"python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"


def _hash_session_id(raw_session_id: str) -> str:
    salt = os.getenv("SLAP_FRICTION_SESSION_SALT", "") or ""
    data = f"{salt}:{raw_session_id}".encode("utf-8", errors="ignore")
    return hashlib.sha256(data).hexdigest()


def _friction_payload(inp: FrictionReportInput) -> Dict[str, Any]:
    now = datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
    return {
        "meta": {
            "version": "1.0",
            "product": inp.product,
            "tier": inp.tier,
            "timestamp": now,
            "session_id": _hash_session_id(inp.session_id),
        },
        "event": {
            "type": "security_friction",
            "code": inp.code,
            "layer": inp.layer,
            "action_attempted": inp.action_attempted,
            "blocked_by": inp.blocked_by,
            "user_message": inp.user_message,
        },
        "context": {
            "os": _normalize_os(inp.os),
            "runtime": _default_runtime(inp.runtime),
            "skill_active": inp.skill_active,
            "connector_active": inp.connector_active,
        },
    }


def _friction_frontend_payload(
    *,
    report: FrictionReportInput,
    event_id: int,
    mode: str,
    github_url: Optional[str],
    status: str,
) -> Dict[str, Any]:
    normalized_mode = (mode or "").strip().lower()
    sent = bool(github_url) and status == "sent"
    if normalized_mode == "auto" and sent:
        message = "Essa ação foi bloqueada por política de segurança. O evento acima foi encaminhado automaticamente para o GitHub do desenvolvedor para análise."
    elif normalized_mode == "auto":
        message = "Essa ação foi bloqueada por política de segurança. O evento foi registrado e ficou em fila para envio ao GitHub."
    else:
        message = "Essa ação foi bloqueada por política de segurança. O evento foi registrado e pode ser enviado para análise."

    return {
        "blocked": True,
        "code": report.code,
        "friction_event_id": str(event_id),
        "github_url": github_url,
        "message": message,
        "product": report.product,
        "layer": report.layer,
        "mode": normalized_mode,
        "status": status,
        "event_id": event_id,
    }


def _issue_markdown(payload: Dict[str, Any]) -> str:
    meta = payload.get("meta", {})
    event = payload.get("event", {})
    ctx = payload.get("context", {})
    lines: List[str] = []
    lines.append(f"**[FRICTION] {event.get('code')} — {event.get('layer')}**")
    lines.append("")
    lines.append("| Campo | Valor |")
    lines.append("|---|---|")
    lines.append(f"| Produto | {meta.get('product', '')} |")
    lines.append(f"| Tier | {meta.get('tier', '')} |")
    lines.append(f"| Camada | {event.get('layer', '')} |")
    lines.append(f"| Código | {event.get('code', '')} |")
    lines.append(f"| Ação tentada | {event.get('action_attempted', '')} |")
    lines.append(f"| Bloqueado por | {event.get('blocked_by', '')} |")
    lines.append(f"| OS | {ctx.get('os', '')} |")
    lines.append(f"| Runtime | {ctx.get('runtime', '')} |")
    lines.append(f"| Skill ativo | {ctx.get('skill_active', '') or 'null'} |")
    lines.append(f"| Connector ativo | {ctx.get('connector_active', '') or 'null'} |")
    lines.append("")
    user_message = event.get("user_message")
    if user_message:
        lines.append("**Mensagem do usuário:**")
        lines.append(f"> {user_message}")
        lines.append("")
    lines.append("---")
    lines.append(
        f"_Enviado automaticamente pelo {meta.get('product', 'open-slap')} v1.x_"
    )
    return "\n".join(lines)


async def _create_github_issue(payload: Dict[str, Any], submission_mode: str) -> str:
    token = os.getenv("SLAP_FRICTION_GITHUB_TOKEN", "") or ""
    repo = os.getenv("SLAP_FRICTION_GITHUB_REPO", "") or ""
    if not token or not repo:
        raise RuntimeError("GitHub friction env vars missing")

    event = payload.get("event", {})
    meta = payload.get("meta", {})
    code = event.get("code", "TRAVA")
    layer = event.get("layer", "security")
    title = f"[FRICTION] {code} — {layer}"
    body = _issue_markdown(payload)
    normalized_mode = (submission_mode or "").strip().lower()
    labels = ["friction-report", "security-layer", "layer:" + str(layer)]
    product = (meta.get("product") or "").strip().lower()
    if product:
        labels.append("product:" + product)
    if normalized_mode == "auto":
        labels.append("auto-submitted")
    else:
        labels.append("demand-submitted")
    if event.get("user_message"):
        labels.append("user-reported")
    url = f"https://api.github.com/repos/{repo}/issues"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "open-slap-friction/1.0",
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(
            url, headers=headers, json={"title": title, "body": body, "labels": labels}
        ) as resp:
            data = await resp.json()
            if resp.status >= 300:
                raise RuntimeError(f"GitHub issue create failed: {resp.status} {data}")
            html_url = data.get("html_url")
            if not html_url:
                raise RuntimeError("GitHub issue create missing html_url")
            return str(html_url)


# Middleware de autenticação
async def get_current_user_ws(
    websocket: WebSocket, token: str
) -> Optional[Dict[str, Any]]:
    """Obtém usuário atual para WebSocket"""
    if not token:
        await websocket.close(code=4001, reason="Token não fornecido")
        return None

    payload = verify_token(token)
    if payload is None:
        await websocket.close(code=4001, reason="Token inválido")
        return None

    user = get_current_user(token)
    if user is None:
        await websocket.close(code=4001, reason="Usuário não encontrado")
        return None

    return user


# Endpoints de Autenticação
@app.post("/auth/register")
async def register(user: UserRegister):
    """Registra novo usuário"""
    try:
        created_user = create_user(user.email, user.password)
        return {
            "message": "Usuário criado com sucesso",
            "user": {"id": created_user["id"], "email": created_user["email"]},
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao criar usuário: {str(e)}")


@app.post("/auth/login")
async def login(user: UserLogin):
    """Faz login do usuário"""
    authenticated_user = authenticate_user(user.email, user.password)

    if not authenticated_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(data={"sub": str(authenticated_user["id"])})

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": authenticated_user,
    }


@app.post("/auth/password-reset/request")
async def password_reset_request(payload: PasswordResetRequest):
    code = create_password_reset(payload.email)
    response = {
        "message": "Se a conta existir, você receberá instruções para redefinir a senha."
    }
    if code:
        response["recovery_code"] = code
    return response


@app.post("/auth/password-reset/confirm")
async def password_reset_confirm(payload: PasswordResetConfirm):
    ok = confirm_password_reset(payload.email, payload.code, payload.new_password)
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Não foi possível redefinir a senha",
        )
    return {"message": "Senha redefinida com sucesso"}


@app.get("/auth/me")
async def get_me(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Obtém informações do usuário atual"""
    token = credentials.credentials
    current_user = get_current_user(token)

    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido"
        )

    return current_user


@app.post("/forge/token")
async def forge_token(request: Request):
    if not FORGE_IDE_MODE:
        raise HTTPException(status_code=404, detail="Forge IDE Mode desativado")
    if not _is_local_client(request):
        raise HTTPException(status_code=403, detail="Acesso permitido apenas via localhost")

    user = _ensure_forge_user()
    from datetime import timedelta
    from .auth import auth_manager

    token = auth_manager.create_access_token(
        data={"sub": str(user["id"]), "forge": True},
        expires_delta=timedelta(minutes=int(FORGE_IDE_TOKEN_TTL_MINUTES)),
    )
    return {"access_token": token, "token_type": "bearer", "user": user}


@app.get("/forge/status")
async def forge_status(request: Request):
    if not FORGE_IDE_MODE:
        return {"forge_mode": False}
    if not _is_local_client(request):
        raise HTTPException(status_code=403, detail="Acesso permitido apenas via localhost")
    user = _ensure_forge_user()
    return {"forge_mode": True, "user": {"id": user.get("id"), "email": user.get("email")}}


@app.get("/api/forge/harnesses")
async def forge_harnesses(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if not FORGE_IDE_MODE:
        raise HTTPException(status_code=404, detail="Forge IDE Mode desativado")
    token = credentials.credentials
    payload = verify_token(token) or {}
    if not payload.get("forge"):
        raise HTTPException(status_code=403, detail="Token Forge requerido")
    user = get_current_user(token)
    if not user:
        raise HTTPException(status_code=401, detail="Não autenticado")
    return {"harnesses": discover_harnesses()}


app.include_router(conversations_tasks_router)
app.include_router(settings_router)
app.include_router(autoapprove_router)
app.include_router(meta_router)


@app.get("/api/search/messages")
async def search_messages_endpoint(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    q: str = Query(""),
    kind: Optional[str] = Query(None),
    limit: int = Query(50),
):
    token = credentials.credentials
    current_user = get_current_user(token)
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado")
    results = search_user_messages(current_user["id"], q, limit=int(limit), kind=kind)
    return {"results": results}


@app.get("/api/skills")
async def list_skills_endpoint(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    token = credentials.credentials
    current_user = get_current_user(token)
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado")
    skills = get_user_skills(current_user["id"]) or []
    return {"skills": skills}


@app.put("/api/skills")
async def put_skills_endpoint(
    payload: SkillsUpdate,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    token = credentials.credentials
    current_user = get_current_user(token)
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado")
    skills = payload.skills if isinstance(payload.skills, list) else []
    upsert_user_skills(current_user["id"], skills)
    return {"ok": True, "count": len(skills)}


@app.get("/api/connectors")
async def list_connectors_endpoint(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    token = credentials.credentials
    current_user = get_current_user(token)
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado")
    sec = _get_effective_security_settings(int(current_user["id"]))
    if sec.get("sandbox") or not sec.get("allow_connectors"):
        return {
            "connectors": {
                "github": {"connected": False},
                "google_calendar": {"connected": False},
                "gmail": {"connected": False},
                "google_drive": {"connected": False},
                "tera": {"connected": False},
                "telegram": {"connected": False},
                "automation_client": {"connected": False},
            }
        }
    keys = set(
        [
            k.strip().lower()
            for k in (list_user_connector_keys(current_user["id"]) or [])
            if k
        ]
    )
    return {
        "connectors": {
            "github": {"connected": "github" in keys},
            "google_calendar": {"connected": "google_calendar" in keys},
            "gmail": {"connected": "gmail" in keys},
            "google_drive": {"connected": "google_drive" in keys},
            "tera": {"connected": "tera" in keys},
            "telegram": {"connected": "telegram" in keys},
            "automation_client": {"connected": "automation_client" in keys},
        }
    }


def _require_mcp_secret(request: Request) -> None:
    expected = str(os.getenv("OPENSLAP_MCP_SECRET") or "").strip()
    if not expected:
        raise HTTPException(
            status_code=503,
            detail="OPENSLAP_MCP_SECRET não configurado.",
        )
    provided = str(request.headers.get("X-MCP-Secret") or "").strip()
    if not (provided and secrets.compare_digest(provided, expected)):
        raise HTTPException(status_code=401, detail="Não autorizado")


app.include_router(connectors_settings_router)


@app.post("/connectors/telegram/link")
async def mcp_telegram_link_endpoint(
    payload: TelegramLinkConsumeInput, request: Request
):
    _require_mcp_secret(request)
    user_id = consume_telegram_link_code(payload.code)
    if not user_id:
        raise HTTPException(status_code=400, detail="Código inválido ou expirado.")
    upsert_telegram_link(
        int(user_id),
        str(payload.telegram_user_id or "").strip(),
        str(payload.chat_id or "").strip(),
    )
    return {"ok": True, "user_id": int(user_id)}


@app.post("/connectors/telegram/unlink")
async def mcp_telegram_unlink_endpoint(payload: TelegramUnlinkInput, request: Request):
    _require_mcp_secret(request)
    ok = revoke_telegram_link(
        str(payload.telegram_user_id or "").strip(),
        str(payload.chat_id or "").strip(),
    )
    return {"ok": bool(ok)}


@app.get("/connectors/telegram/status")
async def mcp_telegram_status_endpoint(
    request: Request,
    telegram_user_id: str = Query(...),
    chat_id: str = Query(...),
):
    _require_mcp_secret(request)
    user_id = get_telegram_linked_user_id(
        str(telegram_user_id or "").strip(),
        str(chat_id or "").strip(),
    )
    return {"linked": bool(user_id), "user_id": int(user_id) if user_id else None}


@app.post("/connectors/telegram/inbound")
async def mcp_telegram_inbound_endpoint(
    payload: TelegramInboundInput, request: Request
):
    _require_mcp_secret(request)
    tuid = str(payload.telegram_user_id or "").strip()
    cid = str(payload.chat_id or "").strip()
    user_message = str(payload.message or "")
    if not (tuid and cid and user_message.strip()):
        raise HTTPException(status_code=400, detail="Payload inválido.")

    user_id = get_telegram_linked_user_id(tuid, cid)
    if not user_id:
        raise HTTPException(status_code=403, detail="Chat não vinculado.")

    sec = _get_effective_security_settings(int(user_id))
    if sec.get("sandbox") or not sec.get("allow_connectors"):
        raise HTTPException(
            status_code=403, detail="Conectores desabilitados nas permissões."
        )

    session_id = f"telegram:{tuid}:{cid}"
    conversation = get_conversation_by_session_for_user(int(user_id), session_id)
    conversation_id = int(conversation["id"]) if conversation else None
    if not conversation_id:
        conversation_id = create_conversation(
            int(user_id),
            session_id,
            f"Telegram {datetime.now().strftime('%d/%m %H:%M')}",
            kind="conversation",
        )

    save_message(int(conversation_id), "user", user_message)

    stored_llm = get_user_llm_settings(int(user_id))
    llm_override = _safe_llm_settings((stored_llm or {}).get("settings") or {})
    expert = await moe_router.select_expert_llm_first(
        user_message, force_expert_id=None, llm_override=llm_override
    )

    user_context = ""
    try:
        stored_soul = get_user_soul(int(user_id))
        soul_events = list_soul_events(int(user_id), limit=20)
        if stored_soul:
            user_context = (stored_soul.get("markdown") or "").strip()
            if not user_context:
                user_context = _build_soul_markdown(
                    stored_soul.get("data") or {}, soul_events
                ).strip()
        elif soul_events:
            user_context = _build_soul_markdown({}, soul_events).strip()
    except Exception:
        user_context = ""

    full_response = ""
    expert_info = None
    async for chunk in llm_manager.stream_generate(
        user_message,
        expert,
        user_context=user_context,
        llm_override=llm_override,
    ):
        if isinstance(chunk, str):
            full_response += chunk
        else:
            expert_info = chunk

    persisted_response = full_response.strip()
    if persisted_response:
        save_message(
            int(conversation_id),
            "assistant",
            persisted_response,
            expert_id=(expert_info or {}).get("id")
            if isinstance(expert_info, dict)
            else None,
            provider=(expert_info or {}).get("provider")
            if isinstance(expert_info, dict)
            else None,
            model=(expert_info or {}).get("model")
            if isinstance(expert_info, dict)
            else None,
            tokens=(expert_info or {}).get("tokens")
            if isinstance(expert_info, dict)
            else None,
        )

    return {"ok": True, "reply": persisted_response}


 


@app.get("/api/system_profile")
async def get_system_profile_endpoint(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    token = credentials.credentials
    current_user = get_current_user(token)
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado")
    sec = _get_effective_security_settings(int(current_user["id"]))
    enabled = bool(ENABLE_SYSTEM_PROFILE) and bool(sec.get("allow_system_profile"))
    stored = get_user_system_profile(current_user["id"])
    if not stored:
        return {
            "data": {},
            "markdown": "",
            "updated_at": None,
            "enabled": enabled,
        }
    if not enabled:
        return {
            "data": {},
            "markdown": "",
            "updated_at": stored.get("updated_at"),
            "enabled": False,
        }
    return {
        "data": stored.get("data") or {},
        "markdown": stored.get("markdown") or "",
        "updated_at": stored.get("updated_at"),
        "enabled": enabled,
    }


@app.post("/api/system_profile/refresh")
async def refresh_system_profile_endpoint(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    token = credentials.credentials
    current_user = get_current_user(token)
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado")
    sec = _get_effective_security_settings(int(current_user["id"]))
    if not sec.get("allow_system_profile"):
        raise HTTPException(
            status_code=403, detail="Perfil do sistema desabilitado nas permissões."
        )
    if not ENABLE_SYSTEM_PROFILE:
        raise HTTPException(
            status_code=400, detail="Perfil do sistema está desabilitado."
        )
    bundle = _build_system_profile(int(current_user["id"]))
    upsert_user_system_profile(
        current_user["id"], bundle.get("markdown") or "", bundle.get("data") or {}
    )
    stored = get_user_system_profile(current_user["id"]) or {}
    return {
        "data": stored.get("data") or {},
        "markdown": stored.get("markdown") or "",
        "updated_at": stored.get("updated_at"),
    }


@app.delete("/api/system_profile")
async def delete_system_profile_endpoint(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    token = credentials.credentials
    current_user = get_current_user(token)
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado")
    deleted = delete_user_system_profile(current_user["id"])
    return {"deleted": bool(deleted)}


@app.get("/api/soul")
async def get_soul_endpoint(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    token = credentials.credentials
    current_user = get_current_user(token)
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado")
    stored = get_user_soul(current_user["id"])
    events = list_soul_events(current_user["id"], limit=50)
    if not stored:
        md = _build_soul_markdown({}, events)
        return {"data": {}, "markdown": md, "updated_at": None, "events": events}
    md = stored.get("markdown") or _build_soul_markdown(
        stored.get("data") or {}, events
    )
    return {
        "data": stored.get("data") or {},
        "markdown": md,
        "updated_at": stored.get("updated_at"),
        "events": events,
    }


@app.put("/api/soul")
async def put_soul_endpoint(
    payload: SoulInput, credentials: HTTPAuthorizationCredentials = Depends(security)
):
    token = credentials.credentials
    current_user = get_current_user(token)
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado")
    events = list_soul_events(current_user["id"], limit=50)
    md = _build_soul_markdown(payload.data or {}, events)
    upsert_user_soul(current_user["id"], payload.data or {}, md)
    stored = get_user_soul(current_user["id"])
    return {
        "data": (stored or {}).get("data") or payload.data or {},
        "markdown": md,
        "updated_at": (stored or {}).get("updated_at"),
        "events": events,
    }


@app.post("/api/soul/events")
async def append_soul_event_endpoint(
    payload: SoulEventInput,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    token = credentials.credentials
    current_user = get_current_user(token)
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado")
    content = (payload.content or "").strip()
    if not content:
        raise HTTPException(status_code=400, detail="Conteúdo vazio")
    source = (payload.source or "user").strip() or "user"
    append_soul_event(current_user["id"], source, content)
    stored = get_user_soul(current_user["id"]) or {"data": {}}
    events = list_soul_events(current_user["id"], limit=50)
    md = _build_soul_markdown(stored.get("data") or {}, events)
    upsert_user_soul(current_user["id"], stored.get("data") or {}, md)
    stored2 = get_user_soul(current_user["id"])
    return {
        "data": (stored2 or {}).get("data") or {},
        "markdown": md,
        "updated_at": (stored2 or {}).get("updated_at"),
        "events": events,
    }


# ── Feedback ──────────────────────────────────────────────────────────────────
class FeedbackInput(BaseModel):
    message_id: int
    rating: int  # 1 = thumbs up, -1 = thumbs down


@app.post("/api/feedback")
async def post_feedback(
    payload: FeedbackInput,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """
    Rate an assistant message.
    rating=1  (thumbs up):
      - Save Q&A to answer_cache for future retrieval
      - Append to soul_events with high salience
      - Record expert positive rating
    rating=-1 (thumbs down):
      - Remove from answer_cache if present
      - Record expert negative rating
    """
    user = get_current_user(credentials.credentials)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    if payload.rating not in (1, -1):
        raise HTTPException(status_code=400, detail="rating must be 1 or -1")

    upsert_message_feedback(user["id"], payload.message_id, payload.rating)

    # Retrieve the Q&A pair for this message
    pair = get_message_with_preceding_user_message(payload.message_id)

    if payload.rating == 1 and pair:
        user_msg_content, asst_msg_content = pair[0].get("content", ""), pair[1].get(
            "content", ""
        )
        expert_id = pair[1].get("expert_id") or "general"

        # 1. Cache the Q&A so it's returned on identical future questions
        if ENABLE_CAC and user_msg_content.strip() and asst_msg_content.strip():
            try:
                qh = _hash_question(user_msg_content)
                put_cached_answer(user["id"], qh, user_msg_content, asst_msg_content)
            except Exception:
                pass

        # 2. Write a high-salience memory so RAG retrieves this exchange
        if ENABLE_MEMORY_WRITE and asst_msg_content.strip():
            try:
                summary = asst_msg_content[:300].strip()
                append_soul_event(
                    user["id"], "feedback_positive", f"Useful answer (👍): {summary}"
                )
                # Boost salience of the newly written event
                import sqlite3 as _sq_fb

                with _sq_fb.connect(str(get_db_path())) as _c_fb:
                    _c_fb.execute(
                        """
                        UPDATE user_soul_events
                        SET salience=0.95, confidence=0.9,
                            last_used_at=CURRENT_TIMESTAMP
                        WHERE user_id=? AND source='feedback_positive'
                        ORDER BY id DESC LIMIT 1
                    """,
                        (user["id"],),
                    )
                    _c_fb.commit()
            except Exception:
                pass

        # 3. Increment expert positive rating
        try:
            record_expert_rating(user["id"], expert_id, positive=True)
        except Exception:
            pass

    elif payload.rating == -1:
        # Remove from CAC if the bad answer was cached
        if pair:
            user_msg_content = pair[0].get("content", "")
            expert_id = pair[1].get("expert_id") or "general"
            if ENABLE_CAC and user_msg_content.strip():
                try:
                    qh = _hash_question(user_msg_content)
                    import sqlite3 as _sq_neg

                    with _sq_neg.connect(str(get_db_path())) as _c_neg:
                        _c_neg.execute(
                            "DELETE FROM answer_cache WHERE user_id=? AND question_hash=?",
                            (user["id"], qh),
                        )
                        _c_neg.commit()
                except Exception:
                    pass
            # Record negative rating for expert
            try:
                record_expert_rating(user["id"], expert_id, positive=False)
            except Exception:
                pass

    return {"ok": True}


@app.get("/api/feedback/{message_id}")
async def get_feedback(
    message_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    user = get_current_user(credentials.credentials)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    rating = get_message_feedback(user["id"], message_id)
    return {"rating": rating}


# ── Plan tasks ────────────────────────────────────────────────────────────────


class PlanApproveInput(BaseModel):
    conversation_id: int
    tasks: List[Dict[str, Any]]  # [{"title": str, "skill_id": str|None}]


@app.post("/api/plan/approve")
async def approve_plan(
    payload: PlanApproveInput,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """Accept a plan and break it into tracked sub-tasks in the sidebar."""
    user = get_current_user(credentials.credentials)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    if not payload.tasks:
        raise HTTPException(status_code=400, detail="tasks list is empty")
    tasks = list(payload.tasks or [])
    try:
        has_project = any(
            str((t or {}).get("skill_id") or "").strip().lower() == "project"
            for t in tasks
        )
        if not has_project:
            tasks.append(
                {
                    "title": "Gerente de Projeto: registrar atividades e decisões no TODO",
                    "skill_id": "project",
                }
            )
    except Exception:
        pass
    ids = create_plan_tasks(user["id"], payload.conversation_id, tasks)
    try:
        _record_activity_done(
            int(user["id"]),
            f"[PLAN] Aprovado: {len(ids)} tarefa(s) na conversa {int(payload.conversation_id)}",
        )
    except Exception:
        pass
    return {"ok": True, "task_ids": ids, "count": len(ids)}


@app.get("/api/plan/tasks/{conversation_id}")
async def get_plan_tasks_endpoint(
    conversation_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    user = get_current_user(credentials.credentials)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    tasks = get_plan_tasks(conversation_id)
    return {"tasks": tasks}


class PlanTaskStatusInput(BaseModel):
    status: str
    conversation_id: Optional[int] = None


@app.put("/api/plan/tasks/{task_id}/status")
async def update_plan_task(
    task_id: int,
    payload: PlanTaskStatusInput,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    user = get_current_user(credentials.credentials)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    if payload.status not in ("pending", "active", "done", "skipped"):
        raise HTTPException(status_code=400, detail="invalid status")
    update_plan_task_status(task_id, payload.status, payload.conversation_id)
    return {"ok": True}


# ═══════════════════════════════════════════════════════════════════════════════
# ORCHESTRATION ENGINE
# Drives the plan→build loop autonomously:
#   for each pending plan_task, create a sub-conversation, inject the skill
#   prompt + project context, call the LLM (non-streaming), save the response,
#   and mark the task done before moving to the next one.
# ═══════════════════════════════════════════════════════════════════════════════
async def _run_orchestration(
    run_id: int,
    user_id: int,
    parent_conversation_id: int,
    user_llm_override: Dict[str, Any],
    websocket: Optional[WebSocket] = None,
) -> None:
    """Background coroutine — must not raise; all errors are logged."""
    log: List[Dict[str, Any]] = []

    def _log(task_id, status, msg):
        log.append({"task_id": task_id, "status": status, "msg": msg})
        try:
            update_orchestration_run(run_id, "running", log)
        except Exception:
            pass

    async def _send_status(text: str) -> None:
        if not websocket:
            return
        try:
            await websocket.send_json({"type": "status", "content": str(text or "")})
        except Exception:
            return

    try:
        tasks = get_plan_tasks(parent_conversation_id)
        pending = [t for t in tasks if t.get("status") in ("pending", "active")]
        try:
            pending.sort(
                key=lambda x: 0
                if str(x.get("skill_id") or "").strip().lower() == "software_operator"
                else 1
            )
        except Exception:
            pass

        try:
            has_operator = any(
                str(t.get("skill_id") or "").strip().lower() == "software_operator"
                for t in pending
            )
            if has_operator:
                non_exec = [
                    t
                    for t in pending
                    if str(t.get("skill_id") or "").strip().lower()
                    != "software_operator"
                ]
                for t in non_exec:
                    try:
                        update_plan_task_status(t["id"], "skipped")
                        _log(
                            t["id"],
                            "skipped",
                            "Aggressive skip: priorizando execução do software_operator",
                        )
                        await _send_status(
                            f"Pulando '{t.get('title', '')}' para priorizar automação"
                        )
                    except Exception:
                        pass
                pending = [
                    t
                    for t in pending
                    if str(t.get("skill_id") or "").strip().lower()
                    == "software_operator"
                ]
        except Exception:
            pass

        if not pending:
            update_orchestration_run(run_id, "completed", log)
            return

        # Shared project context (if any)
        # _project_id and _proj_ctx are initialised here so they are always
        # in scope even if the try block raises or finds nothing.
        _project_id: Optional[int] = None
        _proj_ctx = ""
        try:
            import sqlite3 as _sq_orch

            with _sq_orch.connect(get_db_path()) as _c_orch:
                _conv_row = _c_orch.execute(
                    "SELECT project_id FROM conversations WHERE id=?",
                    (parent_conversation_id,),
                ).fetchone()
                if _conv_row and _conv_row[0]:
                    _project_id = int(_conv_row[0])
                    _proj_row = _c_orch.execute(
                        "SELECT name, context_md FROM projects WHERE id=?",
                        (_project_id,),
                    ).fetchone()
                    if _proj_row and _proj_row[1]:
                        _proj_ctx = (
                            f"Project: {_proj_row[0]}\n" f"{_proj_row[1].strip()}"
                        )
        except Exception:
            pass

        # User skills for prompt resolution
        user_skills = get_user_skills(user_id) or []
        skill_map = {s.get("id", ""): s for s in user_skills}

        prev_outputs: List[Dict[str, str]] = []

        for task in pending:
            task_id = task["id"]
            title = task.get("title", "")
            skill_id = task.get("skill_id") or ""

            _log(task_id, "active", f"Starting: {title}")
            await _send_status(f"Orquestração: iniciando — {title}")

            # 1. Mark task active
            try:
                update_plan_task_status(task_id, "active")
            except Exception:
                pass

            # 2. Resolve skill prompt
            skill_prompt = ""
            skill_obj = skill_map.get(skill_id)
            if skill_obj:
                content = skill_obj.get("content") or {}
                if isinstance(content, dict):
                    skill_prompt = str(content.get("prompt") or "")
                elif isinstance(content, str):
                    skill_prompt = content

            # 3. Build expert for this skill
            _forced = skill_id if skill_id else None
            try:
                _tnorm = str(title or "").strip().lower()
                if _forced and _forced.strip().lower() == "software_operator":
                    if ("agente" in _tnorm) or ("agent" in _tnorm):
                        _forced = "general"
            except Exception:
                pass
            expert = moe_router.select_expert(title, force_expert_id=_forced if _forced else None)

            # 4. Build system context
            user_ctx_parts = []
            if _proj_ctx:
                user_ctx_parts.append(
                    f"--- Shared project context ---\n{_proj_ctx}\n--- End project context ---"
                )
            # Inject link context from recent conversation if allowed
            try:
                if bool(_get_effective_security_settings(int(user_id)).get("allow_web_retrieval")):
                    recent_messages = get_conversation_messages(parent_conversation_id) or []
                    recent_texts = []
                    for m in recent_messages[-8:]:
                        if str(m.get("role") or "").strip() == "user":
                            recent_texts.append(str(m.get("content") or ""))
                    recent_blob = "\n\n".join(recent_texts).strip()
                    if recent_blob:
                        url_ctx = await _url_fetch_context(recent_blob)
                        if url_ctx:
                            user_ctx_parts.append(f"--- Link context (summarized) ---\n{url_ctx}\n--- End link context ---")
            except Exception:
                pass
            try:
                _rt = _build_runtime_context_block(
                    user_id=int(user_id),
                    conversation_id=int(parent_conversation_id),
                    sec=_get_effective_security_settings(int(user_id)),
                    llm_override=user_llm_override,
                )
                if _rt:
                    user_ctx_parts.append(
                        f"--- Runtime context ---\n{_rt}\n--- End runtime context ---"
                    )
            except Exception:
                pass
            if skill_prompt:
                user_ctx_parts.append(
                    f"--- Active skill: {skill_id or title} ---\n{skill_prompt}\n--- End skill ---"
                )
            # For agent creation tasks, ask the LLM to emit a FILES_JSON bundle
            try:
                _tn = str(title or "").strip().lower()
                if (("agente" in _tn) or ("agent" in _tn)) and bool(_get_effective_security_settings(int(user_id)).get("allow_file_write")):
                    proj_folder = _get_project_folder_for_conversation(user_id=int(user_id), conversation_id=int(parent_conversation_id))
                    task_folder = _slugify_path_component(str(title or ""), max_len=48) or f"task-{int(task_id)}"
                    if proj_folder:
                        base_dir_hint = os.path.join(DEFAULT_DELIVERIES_ROOT, str(user_id), proj_folder, f"agent-{int(run_id)}", task_folder)
                    else:
                        base_dir_hint = os.path.join(DEFAULT_DELIVERIES_ROOT, str(user_id), f"agent-{int(run_id)}", task_folder)
                    user_ctx_parts.append(
                        "Deliverables:\n"
                        "- Emit a <FILES_JSON>...</FILES_JSON> block to save local files.\n"
                        f"- Use base_path: {base_dir_hint}\n"
                        "- Include files:\n"
                        "  - agent.json (fields: name, description, prompt, default_skill_id, skill_ids[])\n"
                        "  - prompt.md (the finalized agent prompt)\n"
                        "  - skills.json (list of skills with ids)\n"
                        "- Do not include markdown fences inside <FILES_JSON>."
                    )
            except Exception:
                pass
            if prev_outputs:
                try:
                    recent = prev_outputs[-3:]
                    lines: List[str] = []
                    for po in recent:
                        t = str(po.get("title") or "").strip()
                        out = str(po.get("output") or "").strip()
                        if not out:
                            continue
                        if len(out) > 1600:
                            out = out[:1600].rstrip() + "…"
                        lines.append(f"- {t}\n{out}")
                    if lines:
                        user_ctx_parts.append(
                            "--- Previous task outputs ---\n"
                            + "\n\n".join(lines).strip()
                            + "\n--- End previous outputs ---"
                        )
                except Exception:
                    pass
            # Pull top memories
            try:
                snap = get_consolidated_memory_snapshot(user_id)
                if snap:
                    user_ctx_parts.append(f"User memory:\n{snap}")
            except Exception:
                pass
            user_context = "\n\n".join(user_ctx_parts)

            # 5. Compose the orchestration prompt
            prompt = (
                f"You are executing task: {title}\n\n"
                f"This task is part of a larger project plan. "
                f"Complete this specific task thoroughly and concisely. "
                f"Output your work directly — no preamble about what you are going to do."
            )
            if skill_prompt:
                prompt = f"{skill_prompt}\n\nTask to execute: {title}"

            # 6. Create a sub-conversation to store the output
            try:
                _title_norm = str(title or "").strip().lower()
                _sub_kind = (
                    "conversation"
                    if ("agente" in _title_norm or "agent" in _title_norm)
                    else "task"
                )
                sub_conv_id = create_conversation(
                    user_id,
                    f"orch-{run_id}-task-{task_id}",
                    f"[Auto] {title[:60]}",
                    kind=_sub_kind,
                    source="orchestrator",
                )
                # Link sub-conversation to same project
                try:
                    set_conversation_project(sub_conv_id, _project_id)
                except Exception:
                    pass
                update_plan_task_status(task_id, "active", conversation_id=sub_conv_id)
            except Exception as e:
                _log(task_id, "error", f"Could not create sub-conversation: {e}")
                continue

            # 7. Save user (orchestrator) message
            try:
                save_message(sub_conv_id, "user", prompt, expert_id=expert.get("id"))
            except Exception:
                pass

            # 8. Call LLM (collect streaming chunks into full response)
            full_response = ""
            try:
                if (
                    expert
                    and str(expert.get("id") or "").strip().lower() == "software_operator"
                ):
                    tnorm = str(title or "").strip().lower()
                    if "captura" in tnorm and "tela" in tnorm:
                        full_response = (
                            "python-inline --action vision_screen_text_boxes --out vision_analysis.png"
                        )
                if not full_response:
                    async for chunk in llm_manager.stream_generate(
                        prompt,
                        expert,
                        user_context=user_context,
                        llm_override=user_llm_override,
                    ):
                        if isinstance(chunk, str):
                            full_response += chunk
            except Exception as e:
                _log(task_id, "error", f"LLM error: {e}")
                try:
                    update_plan_task_status(task_id, "failed")
                except Exception:
                    update_plan_task_status(task_id, "skipped")
                continue

            if (
                full_response.strip()
                and expert
                and str(expert.get("id") or "").strip().lower() == "software_operator"
            ):
                try:
                    if websocket:
                        await websocket.send_json(
                            {
                                "type": "status",
                                "content": "▶ Executando: automação",
                            }
                        )
                except Exception:
                    pass
                sec = _get_effective_security_settings(int(user_id))
                try:
                    full_response = await _run_external_software_skill(
                        command_text=full_response,
                        user_id=int(user_id),
                        conversation_id=int(sub_conv_id),
                        sec=sec,
                        expert=expert,
                        llm_override=user_llm_override,
                        user_context=user_context,
                        websocket=websocket,
                    )
                except Exception as e:
                    try:
                        import traceback as _tb

                        tb_txt = _tb.format_exc()
                    except Exception:
                        tb_txt = ""
                    msg = f"software_operator error: {type(e).__name__}: {str(e).strip() or repr(e)}"
                    _log(task_id, "error", msg)
                    try:
                        save_message(
                            sub_conv_id,
                            "assistant",
                            (msg + ("\n\n" + tb_txt[:1200] if tb_txt else "")),
                            expert_id=expert.get("id"),
                        )
                    except Exception:
                        pass
                    try:
                        update_plan_task_status(task_id, "skipped", conversation_id=sub_conv_id)
                    except Exception:
                        pass
                    continue

            # 9. Save assistant response
            if full_response.strip():
                try:
                    save_message(
                        sub_conv_id,
                        "assistant",
                        full_response,
                        expert_id=expert.get("id"),
                    )
                except Exception:
                    pass
                # If the assistant produced a FILES_JSON bundle, write files locally
                try:
                    sec_write = _get_effective_security_settings(int(user_id))
                    if bool(sec_write.get("allow_file_write")):
                        bundle = _extract_files_json(full_response)
                        if bundle:
                            res = _write_files_bundle(bundle)
                            created = res.get("written") or []
                            if created:
                                _record_activity_done(int(user_id), f"[FILES] Criados {len(created)} arquivo(s) para agente: {', '.join(created[:4])}{'…' if len(created) > 4 else ''}")
                except Exception:
                    pass
                try:
                    prev_outputs.append(
                        {"title": str(title or "").strip(), "output": full_response.strip()}
                    )
                except Exception:
                    pass

                try:
                    _record_activity_done(
                        int(user_id),
                        f"[ORCH] Entrega: {str(title or '').strip()} | skill={str(skill_id or '').strip()} | {full_response.strip()[:220]}",
                    )
                except Exception:
                    pass

                if str(skill_id or "").strip().lower() == "project":
                    try:
                        pm_items = _todo_items_from_user_message(full_response)
                        for it in pm_items[:24]:
                            _record_activity_done(int(user_id), f"[PM] {it}")
                    except Exception:
                        pass

                # Write a memory entry for the completed task
                if ENABLE_MEMORY_WRITE:
                    try:
                        append_soul_event(
                            user_id,
                            "orchestration",
                            f"Completed task '{title}': {full_response[:200].strip()}",
                        )
                    except Exception:
                        pass

            # 10. Mark task done
            update_plan_task_status(task_id, "done", conversation_id=sub_conv_id)
            _log(task_id, "done", f"Completed: {title} ({len(full_response)} chars)")
            await _send_status(f"Orquestração: concluída — {title}")

        update_orchestration_run(run_id, "completed", log)
        try:
            _record_activity_done(
                int(user_id),
                f"[ORCH] Concluído run_id={int(run_id)} (conversa {int(parent_conversation_id)})",
            )
        except Exception:
            pass

    except Exception as e:
        try:
            log.append({"task_id": None, "status": "fatal", "msg": str(e)})
            update_orchestration_run(run_id, "failed", log)
        except Exception:
            pass
        try:
            _record_activity_done(
                int(user_id),
                f"[ORCH] Falhou run_id={int(run_id)} (conversa {int(parent_conversation_id)}): {str(e)[:260]}",
            )
        except Exception:
            pass


# ── Orchestration HTTP endpoints ──────────────────────────────────────────────


@app.post("/api/plan/orchestrate/{conversation_id}")
async def start_orchestration(
    conversation_id: int,
    background_tasks: BackgroundTasks,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """
    Start autonomous plan execution for all pending tasks in a conversation.
    Returns immediately with run_id; poll /api/plan/orchestrate/{run_id}/status.
    """
    user = get_current_user(credentials.credentials)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    tasks = get_plan_tasks(conversation_id)
    pending = [t for t in tasks if t.get("status") in ("pending", "active")]
    if not pending:
        raise HTTPException(status_code=400, detail="No pending tasks to execute.")

    # Resolve LLM settings for this user
    stored_llm = get_user_llm_settings(user["id"])
    llm_override = _safe_llm_settings((stored_llm or {}).get("settings") or {})
    api_key = _get_user_api_key(user["id"], llm_override.get("provider"))
    if api_key:
        llm_override["api_key"] = api_key

    run_id = create_orchestration_run(user["id"], conversation_id)
    try:
        _record_activity_done(
            int(user["id"]),
            f"[ORCH] Iniciado run_id={int(run_id)} (conversa {int(conversation_id)}; pendentes={len(pending)})",
        )
    except Exception:
        pass

    ws = None
    try:
        import sqlite3 as _sq_orch_ws

        with _sq_orch_ws.connect(str(get_db_path())) as _cws:
            row = _cws.execute(
                "SELECT session_id FROM conversations WHERE id=?",
                (int(conversation_id),),
            ).fetchone()
            sess = str(row[0] or "") if row else ""
        if sess:
            ws = active_connections.get(sess)
    except Exception:
        ws = None

    # Run in background so the HTTP response returns immediately
    background_tasks.add_task(
        _run_orchestration,
        run_id,
        user["id"],
        conversation_id,
        llm_override,
        websocket=ws,
    )

    return {"ok": True, "run_id": run_id, "pending_count": len(pending)}


@app.get("/api/plan/orchestrate/{run_id}/status")
async def get_orchestration_status(
    run_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """Poll orchestration progress."""
    user = get_current_user(credentials.credentials)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    run = get_orchestration_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found.")
    return {
        "run_id": run_id,
        "status": run.get("status"),
        "log": run.get("log", []),
        "started_at": run.get("started_at"),
        "finished_at": run.get("finished_at"),
    }


# ── Projects ─────────────────────────────────────────────────────────────────


class ProjectCreateInput(BaseModel):
    name: str
    context_md: Optional[str] = ""


class ProjectUpdateInput(BaseModel):
    name: Optional[str] = None
    context_md: Optional[str] = None


@app.get("/api/projects")
async def list_projects(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    user = get_current_user(credentials.credentials)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return {"projects": get_user_projects(user["id"])}


@app.post("/api/projects")
async def create_project_endpoint(
    payload: ProjectCreateInput,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    user = get_current_user(credentials.credentials)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    name = (payload.name or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="name is required")
    try:
        pid = create_project(user["id"], name, payload.context_md or "")
        return {"ok": True, "project_id": pid}
    except Exception as e:
        logger.exception("create_project_failed user_id=%s", str(user.get("id")))
        debug = (os.getenv("OPENSLAP_DEBUG_ERRORS") or "").strip().lower() in {"1", "true", "yes", "on"}
        detail = str(e) if debug else "Internal Server Error"
        raise HTTPException(status_code=500, detail=detail)


@app.put("/api/projects/{project_id}")
async def update_project_endpoint(
    project_id: int,
    payload: ProjectUpdateInput,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    user = get_current_user(credentials.credentials)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    proj = get_project(project_id, user["id"])
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")
    name = payload.name if isinstance(payload.name, str) else None
    context_md = payload.context_md if isinstance(payload.context_md, str) else None
    if name is None and context_md is None:
        raise HTTPException(status_code=400, detail="No fields to update")
    if name is not None:
        clean_name = name.strip()
        if not clean_name:
            raise HTTPException(status_code=400, detail="name is required")
        update_project_name(project_id, user["id"], clean_name)
    if context_md is not None:
        update_project_context(project_id, user["id"], context_md)
    return {"ok": True}


@app.delete("/api/projects/{project_id}")
async def delete_project_endpoint(
    project_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    user = get_current_user(credentials.credentials)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    ok = delete_project(project_id, user["id"])
    if not ok:
        raise HTTPException(status_code=404, detail="Project not found")
    return {"ok": True}


# ── Memory management ─────────────────────────────────────────────────────────


@app.post("/api/memory/decay")
async def trigger_memory_decay(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """Manually trigger memory decay + pruning for the current user."""
    user = get_current_user(credentials.credentials)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    decayed = decay_memory(user["id"])
    pruned = prune_low_salience_memories(user["id"])
    return {"ok": True, "decayed": decayed, "pruned": pruned}


@app.get("/api/memory/snapshot")
async def get_memory_snapshot(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """Return consolidated memory snapshot (top memories by salience)."""
    user = get_current_user(credentials.credentials)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    snapshot = get_consolidated_memory_snapshot(user["id"])
    return {"snapshot": snapshot}

@app.api_route("/api/memory/dream", methods=["POST", "GET"])
async def run_memory_dream(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    user = get_current_user(credentials.credentials)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    decayed = decay_memory(user["id"])
    pruned = prune_low_salience_memories(user["id"])
    snapshot = get_consolidated_memory_snapshot(user["id"])
    return {"ok": True, "decayed": decayed, "pruned": pruned, "snapshot": snapshot}
@app.get("/api/memory/search_raw")
async def search_raw_memory(
    q: str,
    limit: int = 50,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    user = get_current_user(credentials.credentials)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    query = (q or "").strip()
    if not query:
        raise HTTPException(status_code=400, detail="q is required")
    lim = max(1, min(int(limit or 50), 200))
    results = search_user_messages(user["id"], query, limit=lim, kind=None)
    return {"results": results}


class MemoryImportPayload(BaseModel):
    markdown: str = ""
    provider: Optional[str] = None
    label: Optional[str] = None
    salience: Optional[float] = None
    split_by_category: bool = False

@app.post("/api/memory/import")
async def import_external_memory(
    payload: MemoryImportPayload,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    user = get_current_user(credentials.credentials)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    md = (payload.markdown or "").strip()
    if not md:
        raise HTTPException(status_code=400, detail="markdown is required")
    provider = (payload.provider or "").strip().lower()
    label = (payload.label or "").strip()
    split = bool(payload.split_by_category)
    import_id = uuid.uuid4().hex[:12]
    meta = []
    if provider:
        meta.append(f"provider: {provider}")
    if label:
        meta.append(f"label: {label}")
    meta.append(f"import_id: {import_id}")
    meta_line = f"External memory import ({', '.join(meta)})"
    stamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%SZ")
    source_parts = ["imported"]
    if provider:
        source_parts.append(provider)
    source_parts.append(import_id)
    source = ":".join(source_parts)
    sal = payload.salience
    try:
        sal = float(sal) if sal is not None else 0.8
    except Exception:
        sal = 0.8
    def split_sections(text: str) -> List[Dict[str, str]]:
        lines = (text or "").replace("\r", "").split("\n")
        cats = [
            ("demographics", ["informações demográficas", "demographic information"], {"1"}),
            ("interests", ["interesses e preferências", "interests and preferences"], {"2"}),
            ("relationships", ["relacionamentos", "relationships"], {"3"}),
            ("events", ["eventos, projetos e planos", "events, projects and plans"], {"4"}),
            ("instructions", ["instruções", "instructions"], {"5"}),
        ]
        starts: List[Dict[str, Any]] = []
        for i, raw in enumerate(lines):
            line = (raw or "").strip()
            if not line:
                continue
            m = re.match(r"^\s{0,3}#{0,6}\s*(?:(\d{1})\s*[.)-]\s*)?(.*)$", raw)
            if not m:
                continue
            num = (m.group(1) or "").strip()
            rest = (m.group(2) or "").strip().lower()
            for key, phrases, nums in cats:
                hit_num = bool(num and num in nums)
                hit_phrase = any(p in rest for p in phrases)
                if hit_num or hit_phrase:
                    starts.append({"idx": i, "key": key, "title": raw.strip()})
                    break
        if not starts:
            return [{"key": "import", "title": "import", "markdown": text.strip()}]
        starts.sort(key=lambda x: int(x["idx"]))
        uniq: List[Dict[str, Any]] = []
        seen = set()
        for s in starts:
            k = str(s["key"])
            if k in seen:
                continue
            seen.add(k)
            uniq.append(s)
        out = []
        for j, s in enumerate(uniq):
            a = int(s["idx"])
            b = int(uniq[j + 1]["idx"]) if j + 1 < len(uniq) else len(lines)
            chunk = "\n".join(lines[a:b]).strip()
            if not chunk:
                continue
            out.append({"key": str(s["key"]), "title": str(s["title"]), "markdown": chunk})
        return out or [{"key": "import", "title": "import", "markdown": text.strip()}]

    sections = split_sections(md) if split else [{"key": "import", "title": "import", "markdown": md}]
    created_ids: List[int] = []
    for s in sections:
        sec_key = str(s.get("key") or "import")
        sec_title = str(s.get("title") or "").strip()
        sec_md = str(s.get("markdown") or "").strip()
        if not sec_md:
            continue
        sec_meta = f"{meta_line} — imported_at: {stamp}"
        if split and sec_title and sec_title != "import":
            sec_meta = f"{meta_line} — imported_at: {stamp} — section: {sec_title}"
        content = f"{sec_meta}\n\n{sec_md}"
        eid = append_soul_event(int(user["id"]), source, content)
        created_ids.append(int(eid))
        sec_sal = 0.9 if sec_key == "instructions" else float(sal)
        set_soul_event_salience(int(user["id"]), int(eid), float(sec_sal))
        if sec_key == "instructions":
            set_soul_event_pinned(int(user["id"]), int(eid), True)

    if not created_ids:
        raise HTTPException(status_code=400, detail="No valid sections found")
    return {"ok": True, "event_id": created_ids[0], "event_ids": created_ids, "import_id": import_id, "source": source}

class MemoryImportPinPayload(BaseModel):
    pinned: bool = True

@app.get("/api/memory/imports")
async def list_external_memory_imports(
    limit: int = Query(25, ge=1, le=200),
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    user = get_current_user(credentials.credentials)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    items = list_imported_soul_events(int(user["id"]), limit=int(limit))
    groups: Dict[str, Dict[str, Any]] = {}
    for it in items:
        src = str(it.get("source") or "")
        parts = src.split(":")
        import_id = ""
        provider2 = ""
        if len(parts) >= 2 and re.fullmatch(r"[0-9a-f]{10,64}", parts[-1] or ""):
            import_id = parts[-1]
            provider2 = parts[1] if len(parts) >= 3 else ""
        key = import_id if import_id else f"legacy_{it.get('id')}"
        g = groups.get(key)
        if not g:
            groups[key] = {
                "import_id": key,
                "provider": provider2,
                "source": src,
                "created_at": it.get("created_at"),
                "count": 0,
                "pinned": False,
                "items": [],
            }
            g = groups[key]
        g["count"] = int(g["count"]) + 1
        g["pinned"] = bool(g["pinned"]) or bool(it.get("pinned"))
        g["items"].append(
            {
                "id": it.get("id"),
                "source": src,
                "created_at": it.get("created_at"),
                "salience": it.get("salience"),
                "pinned": it.get("pinned"),
                "content": it.get("content"),
            }
        )
    out = list(groups.values())
    out.sort(key=lambda x: str(x.get("created_at") or ""), reverse=True)
    return {"imports": out}

@app.post("/api/memory/imports/{import_id}/pin")
async def pin_external_memory_import(
    import_id: str,
    payload: MemoryImportPinPayload,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    user = get_current_user(credentials.credentials)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    iid = (import_id or "").strip()
    if not iid:
        raise HTTPException(status_code=400, detail="import_id is required")
    pinned = bool(payload.pinned)
    touched = 0
    if iid.startswith("legacy_"):
        try:
            event_id = int(iid.split("_", 1)[1])
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid legacy import_id")
        ok = set_soul_event_pinned(int(user["id"]), int(event_id), pinned)
        return {"ok": bool(ok)}
    items = list_imported_soul_events(int(user["id"]), limit=500)
    for it in items:
        src = str(it.get("source") or "")
        if src.endswith(f":{iid}") or src == f"imported:{iid}":
            if set_soul_event_pinned(int(user["id"]), int(it.get("id")), pinned):
                touched += 1
    return {"ok": True, "touched": touched}

@app.delete("/api/memory/imports/{import_id}")
async def delete_external_memory_import(
    import_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    user = get_current_user(credentials.credentials)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    iid = (import_id or "").strip()
    if not iid:
        raise HTTPException(status_code=400, detail="import_id is required")
    deleted = 0
    if iid.startswith("legacy_"):
        try:
            event_id = int(iid.split("_", 1)[1])
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid legacy import_id")
        ok = delete_imported_soul_event(int(user["id"]), int(event_id))
        return {"ok": bool(ok)}
    items = list_imported_soul_events(int(user["id"]), limit=500)
    for it in items:
        src = str(it.get("source") or "")
        if src.endswith(f":{iid}") or src == f"imported:{iid}":
            if delete_imported_soul_event(int(user["id"]), int(it.get("id"))):
                deleted += 1
    return {"ok": True, "deleted": deleted}

@app.get("/api/padxml/software")
async def list_padxml_software(
    limit: int = Query(20, ge=1, le=200),
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    user = get_current_user(credentials.credentials)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    db_path = os.path.join(str(BASE_DIR), "src", "backend", "data", "padxml.db")
    if not os.path.exists(db_path):
        return {"items": []}
    items: List[Dict[str, Any]] = []
    try:
        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                """
                SELECT record_id, record_type, provider, source_url, collected_at, payload_json, created_at
                FROM padxml_records
                WHERE record_type = 'software'
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (int(limit),),
            ).fetchall()
            for r in rows:
                try:
                    payload = json.loads(r["payload_json"])
                except Exception:
                    payload = {}
                content = payload.get("content") or {}
                items.append(
                    {
                        "record_id": r["record_id"],
                        "record_type": r["record_type"],
                        "name": content.get("name"),
                        "version": content.get("version"),
                        "os": content.get("os"),
                        "arch": content.get("arch"),
                        "provider": r["provider"],
                        "source_url": r["source_url"],
                        "collected_at": r["collected_at"],
                        "created_at": r["created_at"],
                    }
                )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PADXML list failed: {e}")
    return {"items": items}

class PadxmlSaveMessageInput(BaseModel):
    conversation_id: Optional[int] = None
    local_message_id: Optional[int] = None
    message_id: Optional[int] = None
    content: str = ""
    title: Optional[str] = None

@app.post("/api/padxml/save_message")
async def save_message_as_padxml(
    payload: PadxmlSaveMessageInput,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    user = get_current_user(credentials.credentials)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    content = str(payload.content or "").strip()
    if not content:
        raise HTTPException(status_code=400, detail="content is required")

    conv_id = payload.conversation_id
    mid = payload.local_message_id or payload.message_id
    url = f"https://open-slap.local/conversations/{conv_id or 0}/messages/{mid or 0}"
    title = str(payload.title or "").strip()
    if not title:
        first = next((ln.strip() for ln in content.splitlines() if ln.strip()), "")
        title = (first[:120] if first else "Saved information")

    sha = hashlib.sha256(content.encode("utf-8")).hexdigest()
    now = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    padxml = {
        "schema_version": "padxml.v1",
        "record_type": "article",
        "record_id": "",
        "source": {
            "provider": "open_slap",
            "url": url,
            "collected_at": now,
            "robots": {"allowed": True},
            "crawl_policy": {"rate_limit_rps": 0.0, "user_agent": "OpenSlap"},
            "checksums": {"content_sha256": sha},
            "evidence": [{"type": "url", "value": url}],
        },
        "content": {"title": title, "summary": content},
        "security": {"sanitized": True, "contains_pii": False},
    }
    normalize_padxml(padxml)
    ok, errs = validate_padxml_v1(padxml)
    if not ok:
        raise HTTPException(status_code=400, detail="PADXML invalid: " + "; ".join(errs))

    db_path = os.path.join(str(BASE_DIR), "src", "backend", "data", "padxml.db")
    try:
        with sqlite3.connect(db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS padxml_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    record_id TEXT NOT NULL UNIQUE,
                    record_type TEXT NOT NULL,
                    provider TEXT NOT NULL,
                    source_url TEXT NOT NULL,
                    collected_at TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_padxml_by_type ON padxml_records(record_type)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_padxml_by_provider ON padxml_records(provider)"
            )
            payload_json = json.dumps(padxml, ensure_ascii=False, separators=(",", ":"))
            cur = conn.execute(
                """
                INSERT OR IGNORE INTO padxml_records
                (record_id, record_type, provider, source_url, collected_at, payload_json)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    padxml["record_id"],
                    padxml["record_type"],
                    padxml["source"]["provider"],
                    padxml["source"]["url"],
                    padxml["source"]["collected_at"],
                    payload_json,
                ),
            )
            conn.commit()
            action = "inserted" if cur.rowcount and int(cur.rowcount) > 0 else "skipped"
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PADXML save failed: {e}")

    return {"ok": True, "action": action, "record_id": padxml["record_id"]}


# ── Onboarding ────────────────────────────────────────────────────────────────


@app.get("/api/onboarding/status")
async def get_onboarding_status(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """Returns whether the user has completed onboarding."""
    user = get_current_user(credentials.credentials)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    stored = get_user_onboarding_completed(user["id"])
    if stored is not None:
        return {"completed": bool(stored), "conversation_count": None, "source": "flag"}
    # Onboarding is considered complete when user has at least one conversation
    with __import__("sqlite3").connect(str(get_db_path())) as conn:
        row = conn.execute(
            "SELECT COUNT(*) FROM conversations WHERE user_id=?", (user["id"],)
        ).fetchone()
        count = row[0] if row else 0
    completed = count > 0
    return {"completed": completed, "conversation_count": count, "source": "conversations"}


@app.post("/api/onboarding/complete")
async def complete_onboarding(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    user = get_current_user(credentials.credentials)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    set_user_onboarding_completed(user["id"], True)
    return {"ok": True, "completed": True}


@app.post("/api/onboarding/reset")
async def reset_onboarding(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    user = get_current_user(credentials.credentials)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    set_user_onboarding_completed(user["id"], False)
    return {"ok": True, "completed": False}


# WebSocket com autenticação
async def _ws_idle_keepalive(
    websocket: WebSocket,
    done_evt: asyncio.Event,
    last_emit_ref: List[float],
    interval_s: int = 12,
    idle_s: int = 10,
) -> None:
    while True:
        if done_evt.is_set():
            return
        await asyncio.sleep(max(1, int(interval_s)))
        if done_evt.is_set():
            return
        try:
            if (time.time() - float(last_emit_ref[0])) >= float(idle_s):
                await websocket.send_json(
                    {"type": "status", "content": "Ainda processando..."}
                )
                last_emit_ref[0] = time.time()
        except Exception:
            return


@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """Endpoint WebSocket com autenticação"""
    token = websocket.query_params.get("token") or _extract_bearer_token_from_headers(
        dict(websocket.headers)
    )
    if not token:
        await websocket.close(code=4001, reason="Token não fornecido")
        return

    ws_payload = verify_token(token) or {}
    is_forge_ws = bool(ws_payload.get("forge"))

    # Verificar usuário
    current_user = await get_current_user_ws(websocket, token)
    if not current_user:
        return

    # Aceitar conexão
    await websocket.accept()
    active_connections[session_id] = websocket

    try:
        # Obter ou criar conversa
        conversation = get_conversation_by_session_for_user(
            current_user["id"], session_id
        )
        conversation_id = conversation["id"] if conversation else None
        conversation_kind = (
            conversation.get("kind") if conversation else "conversation"
        ) or "conversation"

        # Enviar histórico se existir
        if conversation_id:
            messages = get_conversation_messages(conversation_id)
            for message in messages:
                await websocket.send_json({"type": "history", "message": message})

        # Loop de mensagens
        while True:
            try:
                # Receber mensagem do cliente
                _ka_task = None
                _done_evt = None
                data = await websocket.receive_json()

                if data.get("type") == "chat":
                    user_message = data.get("content", "")
                    if not (user_message or "").strip():
                        continue
                    internal_prompt = str(data.get("internal_prompt") or "").strip()
                    sec = _get_effective_security_settings(int(current_user["id"]))
                    ide_ctx_raw = data.get("ide_context")
                    ide_ctx = ide_ctx_raw if isinstance(ide_ctx_raw, dict) else {}
                    _done_evt = asyncio.Event()
                    _last_emit = [time.time()]
                    _ka_task = asyncio.create_task(
                        _ws_idle_keepalive(websocket, _done_evt, _last_emit)
                    )

                    async def _ws_send(payload: Dict[str, Any]) -> None:
                        await websocket.send_json(payload)
                        _last_emit[0] = time.time()

                    # Skill active — pull its system prompt from user's skill list
                    ws_skill_id = (data.get("skill_id") or "").strip()
                    ws_skill_web_search = bool(data.get("skill_web_search"))
                    _active_skill_prompt: str = ""
                    if ws_skill_id:
                        try:
                            _user_skills = get_user_skills(current_user["id"]) or []
                            _sk = next(
                                (
                                    s
                                    for s in _user_skills
                                    if str(s.get("id") or "") == ws_skill_id
                                ),
                                None,
                            )
                            if _sk:
                                _sk_content = _sk.get("content") or {}
                                if isinstance(_sk_content, dict):
                                    _active_skill_prompt = str(
                                        _sk_content.get("prompt") or ""
                                    ).strip()
                                elif isinstance(_sk_content, str):
                                    _active_skill_prompt = _sk_content.strip()
                        except Exception:
                            _active_skill_prompt = ""

                    if not conversation_id:
                        conversation_id = create_conversation(
                            current_user["id"],
                            session_id,
                            f"Conversa {datetime.now().strftime('%d/%m %H:%M')}",
                            kind="conversation",
                        )
                        conversation_kind = "conversation"

                    # Salvar mensagem do usuário
                    _user_msg_id = save_message(conversation_id, "user", user_message)
                    try:
                        client_message_id = str(data.get("client_message_id") or "").strip()
                        saved_user_msg = get_message(int(_user_msg_id)) if _user_msg_id else None
                        if client_message_id and saved_user_msg:
                            await websocket.send_json(
                                {
                                    "type": "user_ack",
                                    "client_message_id": client_message_id,
                                    "message": saved_user_msg,
                                }
                            )
                            _last_emit[0] = time.time()
                    except Exception:
                        pass
                    try:
                        logger.info(
                            "ws_chat_start user_id=%s session_id=%s conversation_id=%s chars=%s",
                            str(current_user.get("id")),
                            str(session_id),
                            str(conversation_id),
                            str(len(user_message or "")),
                        )
                    except Exception:
                        pass

                    todo_items = _todo_items_from_user_message(user_message)
                    if todo_items:
                        if conversation_kind == "task":
                            for t in todo_items:
                                add_task_todo(
                                    current_user["id"],
                                    conversation_id,
                                    t,
                                    kind="step",
                                    actor="human",
                                    origin="user",
                                    scope="project",
                                    priority="medium",
                                    source_conversation_id=int(conversation_id),
                                    source_message_id=int(_user_msg_id)
                                    if _user_msg_id
                                    else None,
                                )
                            await websocket.send_json(
                                {
                                    "type": "status",
                                    "content": f"TODO registrado ({len(todo_items)})",
                                }
                            )
                            _last_emit[0] = time.time()
                        else:
                            inbox_session_id = f"task-inbox:{int(current_user['id'])}"
                            inbox = get_conversation_by_session_for_user(
                                current_user["id"], inbox_session_id
                            )
                            inbox_id = inbox["id"] if inbox else None
                            if not inbox_id:
                                inbox_id = create_conversation(
                                    current_user["id"],
                                    inbox_session_id,
                                    "Inbox",
                                    kind="task",
                                )
                            for t in todo_items:
                                add_task_todo(
                                    current_user["id"],
                                    int(inbox_id),
                                    t,
                                    kind="step",
                                    actor="human",
                                    origin="user",
                                    scope="personal",
                                    priority="medium",
                                    source_conversation_id=int(conversation_id),
                                    source_message_id=int(_user_msg_id)
                                    if _user_msg_id
                                    else None,
                                )
                            await websocket.send_json(
                                {
                                    "type": "status",
                                    "content": f"TODO enviado para Inbox ({len(todo_items)})",
                                }
                            )
                            _last_emit[0] = time.time()
                            if _looks_like_personal_todo_capture(user_message) and not internal_prompt:
                                msg = (
                                    f"✅ Registrei {len(todo_items)} TODO(s) na sua Inbox (Pessoal). "
                                    "Veja em Settings → Tarefas → Pessoal."
                                )
                                msg_id = save_message(
                                    conversation_id,
                                    "assistant",
                                    msg,
                                    expert_id="general",
                                    provider="runtime",
                                    model="todo",
                                    tokens=None,
                                )
                                await websocket.send_json(
                                    {
                                        "type": "done",
                                        "content": msg,
                                        "expert": {"id": "general"},
                                        "provider": "runtime",
                                        "model": "todo",
                                        "tokens": None,
                                        "message_id": msg_id,
                                    }
                                )
                                _last_emit[0] = time.time()
                                continue

                    wizard = _project_wizard_handle_message(
                        user_id=int(current_user["id"]),
                        conversation_id=int(conversation_id),
                        user_message=user_message,
                        internal_prompt=internal_prompt,
                    )
                    if wizard:
                        full_response = str(wizard.get("content") or "")
                        persisted_response = _strip_assistant_directives(full_response)
                        msg_id = save_message(
                            conversation_id,
                            "assistant",
                            persisted_response,
                            expert_id="general",
                            provider="runtime",
                            model="wizard",
                            tokens=None,
                        )
                        expert = moe_router.select_expert(
                            user_message, force_expert_id="general"
                        )
                        await websocket.send_json(
                            {
                                "type": "done",
                                "content": full_response,
                                "expert": expert,
                                "provider": "runtime",
                                "model": "wizard",
                                "tokens": None,
                                "message_id": msg_id,
                            }
                        )
                        _last_emit[0] = time.time()
                        continue

                    recent_messages = get_conversation_messages(conversation_id)
                    recent_context = _format_recent_chat_context(
                        recent_messages, limit=8
                    )

                    # Enviar status de processamento
                    await websocket.send_json(
                        {"type": "status", "content": "Processando mensagem..."}
                    )
                    _last_emit[0] = time.time()

                    if _is_runtime_introspection_query(user_message):
                        full_response = _runtime_introspection_answer(
                            current_user=current_user, session_id=session_id
                        )
                        save_message(
                            conversation_id,
                            "assistant",
                            full_response,
                            expert_id=None,
                            provider="runtime",
                            model="introspection",
                            tokens=None,
                        )
                        await websocket.send_json(
                            {
                                "type": "done",
                                "content": full_response,
                                "expert": None,
                                "provider": "runtime",
                                "model": "introspection",
                                "tokens": None,
                            }
                        )
                        _last_emit[0] = time.time()
                        continue

                    if (
                        ENABLE_SYSTEM_PROFILE
                        and sec.get("allow_system_profile")
                        and _is_system_profile_detail_query(user_message)
                    ):
                        stored_profile = get_user_system_profile(current_user["id"])
                        profile_data = (stored_profile or {}).get("data") or {}
                        details = _system_profile_direct_answer(
                            user_message=user_message, profile_data=profile_data
                        )
                        if not details:
                            try:
                                bundle = _build_system_profile(int(current_user["id"]))
                                upsert_user_system_profile(
                                    current_user["id"],
                                    bundle.get("markdown") or "",
                                    bundle.get("data") or {},
                                )
                                stored_profile = get_user_system_profile(
                                    current_user["id"]
                                )
                                profile_data = (stored_profile or {}).get("data") or {}
                                details = _system_profile_direct_answer(
                                    user_message=user_message, profile_data=profile_data
                                )
                            except Exception:
                                details = details or ""
                        if details:
                            full_response = details
                            save_message(
                                conversation_id,
                                "assistant",
                                full_response,
                                expert_id=None,
                                provider="runtime",
                                model="system_profile",
                                tokens=None,
                            )
                            await websocket.send_json(
                                {
                                    "type": "done",
                                    "content": full_response,
                                    "expert": None,
                                    "provider": "runtime",
                                    "model": "system_profile",
                                    "tokens": None,
                                }
                            )
                            _last_emit[0] = time.time()
                            continue

                    # Roteamento e geração de resposta
                    _forced_plan_text = ""
                    # MoE selection — honour user override if provided
                    _force_expert = (data.get("force_expert_id") or "").strip() or None
                    expert = await moe_router.select_expert_llm_first(
                        user_message, force_expert_id=_force_expert
                    )
                    try:
                        if expert and bool(expert.get("tool_needed")):
                            await websocket.send_json(
                                {
                                    "type": "status",
                                    "content": "🎯 Intenção de ação detectada. Preparando ambiente local...",
                                }
                            )
                            _last_emit[0] = time.time()
                            err_prep = _ensure_workdir_ready()
                            if err_prep:
                                await websocket.send_json(
                                    {
                                        "type": "status",
                                        "content": f"Erro preparando diretório de trabalho: {err_prep}",
                                    }
                                )
                                _last_emit[0] = time.time()
                            else:
                                await websocket.send_json(
                                    {
                                        "type": "status",
                                        "content": f"Diretório de trabalho OK: {str(DEFAULT_WORKDIR)}",
                                    }
                                )
                                _last_emit[0] = time.time()
                            plan_text = (
                                "```plan\n"
                                "Executar automação local solicitada pelo usuário | software_operator\n"
                                "```"
                            )
                            _forced_plan_text = plan_text
                            await _ws_send({"type": "chunk", "content": plan_text})
                    except Exception:
                        pass
                    # Adjust confidence using per-user historical expert ratings
                    try:
                        _expert_ratings = get_expert_rating_summary(
                            int(current_user["id"])
                        )
                        if expert and _expert_ratings:
                            _eid = expert.get("id", "")
                            _approval = _expert_ratings.get(_eid)
                            if (
                                _approval is not None
                                and expert.get("confidence") is not None
                            ):
                                # Blend keyword confidence with historical approval rate
                                expert["confidence"] = 0.7 * float(
                                    expert["confidence"]
                                ) + 0.3 * float(_approval)
                                if _approval < 0.3 and _env_flag(
                                    os.getenv("OPENSLAP_DEBUG_ROUTER"), False
                                ):
                                    expert["selection_reason"] = (
                                        f"{expert.get('selection_reason', '')} "
                                        f"[low approval {_approval:.0%}]"
                                    ).strip()
                    except Exception:
                        pass

                    lower_msg = (user_message or "").lower()
                    path_match = re.search(r"([A-Za-z]:\\[^\n\r]+)", user_message or "")
                    requested_base_path = (
                        path_match.group(1).strip().strip("`\"' ,")
                        if path_match
                        else ""
                    )

                    is_file_request = (
                        "criar" in lower_msg
                        or "gere" in lower_msg
                        or "gerar" in lower_msg
                        or "salv" in lower_msg
                    ) and (
                        "arquivo" in lower_msg
                        or "landing" in lower_msg
                        or "landpage" in lower_msg
                        or "página" in lower_msg
                        or "pagina" in lower_msg
                        or "site" in lower_msg
                        or ".html" in lower_msg
                    )

                    delivery_id = uuid.uuid4().hex[:12] if is_file_request else ""
                    base_path_for_write = requested_base_path
                    if is_file_request and not base_path_for_write:
                        proj_folder = _get_project_folder_for_conversation(
                            user_id=int(current_user["id"]),
                            conversation_id=int(conversation_id),
                        )
                        if proj_folder:
                            base_path_for_write = os.path.join(
                                DEFAULT_DELIVERIES_ROOT,
                                str(current_user["id"]),
                                proj_folder,
                                delivery_id,
                            )
                        else:
                            base_path_for_write = os.path.join(
                                DEFAULT_DELIVERIES_ROOT,
                                str(current_user["id"]),
                                delivery_id,
                            )

                    # Gerar resposta com streaming
                    full_response = ""
                    expert_info = None

                    user_context = ""
                    if not sec.get("sandbox"):
                        stored_soul = get_user_soul(current_user["id"])
                        soul_events = list_soul_events(current_user["id"], limit=20)
                        if stored_soul:
                            user_context = (stored_soul.get("markdown") or "").strip()
                            if not user_context:
                                user_context = _build_soul_markdown(
                                    stored_soul.get("data") or {}, soul_events
                                ).strip()
                        elif soul_events:
                            user_context = _build_soul_markdown({}, soul_events).strip()

                    if (
                        ENABLE_MEMORY_SNAPSHOT_CONTEXT
                        and not is_file_request
                        and not sec.get("sandbox")
                    ):
                        try:
                            snap = (
                                get_consolidated_memory_snapshot(current_user["id"])
                                or ""
                            ).strip()
                            if snap:
                                snap = snap[: int(MEMORY_SNAPSHOT_MAX_CHARS)].rstrip()
                                block = f"Memória consolidada (uso interno):\n{snap}"
                                user_context = (
                                    f"{block}\n\n{user_context}".strip()
                                    if user_context
                                    else block
                                )
                        except Exception:
                            pass

                    # ── Project shared context ────────────────────────────
                    _proj_ctx = ""
                    try:
                        if sec.get("sandbox"):
                            raise Exception("sandbox")
                        import sqlite3 as _sq2

                        with _sq2.connect(
                            str(
                                __import__("pathlib").Path(
                                    __import__("os").environ.get(
                                        "OPENSLAP_DB_PATH", "data/auth.db"
                                    )
                                )
                            )
                        ) as _c2:
                            _conv_row = _c2.execute(
                                "SELECT project_id FROM conversations WHERE id=?",
                                (conversation_id,),
                            ).fetchone()
                            if _conv_row and _conv_row[0]:
                                _proj_row = _c2.execute(
                                    "SELECT name, context_md FROM projects WHERE id=?",
                                    (_conv_row[0],),
                                ).fetchone()
                                if _proj_row and _proj_row[1]:
                                    _proj_ctx = (
                                        f"Project: {_proj_row[0]}\n"
                                        f"{_proj_row[1].strip()}"
                                    )
                    except Exception:
                        pass
                    if _proj_ctx:
                        user_context = (
                            f"--- Shared project context ---\n{_proj_ctx}\n"
                            f"--- End project context ---\n\n{user_context}"
                        ).strip()

                    llm_override = {}
                    if not sec.get("sandbox"):
                        try:
                            _rt = _build_runtime_context_block(
                                user_id=int(current_user["id"]),
                                conversation_id=int(conversation_id),
                                sec=sec,
                                llm_override=llm_override,
                            )
                            if _rt:
                                user_context = (
                                    f"--- Runtime context ---\n{_rt}\n--- End runtime context ---\n\n{user_context}"
                                ).strip()
                        except Exception:
                            pass

                    if is_forge_ws and not sec.get("sandbox"):
                        try:
                            _ide_block = _build_ide_context_block(ide_ctx)
                            if _ide_block:
                                user_context = (
                                    f"{_ide_block}\n\n{user_context}".strip()
                                    if user_context
                                    else _ide_block
                                )
                        except Exception:
                            pass
                        try:
                            _h_block = build_harnesses_context_block()
                            if _h_block:
                                block = (
                                    f"--- Forge harnesses ---\n{_h_block}\n--- End Forge harnesses ---"
                                )
                                user_context = (
                                    f"{block}\n\n{user_context}".strip()
                                    if user_context
                                    else block
                                )
                        except Exception:
                            pass

                    # ── Active connector context ───────────────────────────────
                    _conn_ctx_parts: List[str] = []
                    try:
                        if (not sec.get("allow_connectors")) or sec.get("sandbox"):
                            raise Exception("connectors disabled")
                        _gh_token = _get_user_connector_secret(
                            current_user["id"], "github"
                        )
                        if _gh_token and any(
                            k in user_message.lower()
                            for k in (
                                "issue",
                                "pr",
                                "pull request",
                                "repo",
                                "github",
                                "commit",
                                "branch",
                                "code review",
                            )
                        ):
                            import aiohttp as _aio

                            async with _aio.ClientSession(
                                timeout=_aio.ClientTimeout(total=5)
                            ) as _s:
                                _gh_h = {
                                    "Authorization": f"token {_gh_token}",
                                    "Accept": "application/vnd.github+json",
                                }
                                # User repos (top 5)
                                async with _s.get(
                                    "https://api.github.com/user/repos"
                                    "?sort=updated&per_page=5",
                                    headers=_gh_h,
                                ) as _rr:
                                    if _rr.status == 200:
                                        _repos = await _rr.json()
                                        _names = [
                                            r["full_name"]
                                            for r in _repos
                                            if r.get("full_name")
                                        ]
                                        if _names:
                                            _conn_ctx_parts.append(
                                                f"GitHub — recent repos: {', '.join(_names)}"
                                            )
                                # Open issues (top 5)
                                async with _s.get(
                                    "https://api.github.com/issues"
                                    "?filter=assigned&state=open&per_page=5",
                                    headers=_gh_h,
                                ) as _ir:
                                    if _ir.status == 200:
                                        _issues = await _ir.json()
                                        _ititles = [
                                            f"#{i.get('number')} {i.get('title', '')[:60]}"
                                            for i in _issues
                                            if isinstance(i, dict)
                                        ]
                                        if _ititles:
                                            _conn_ctx_parts.append(
                                                "GitHub — open issues assigned to you: "
                                                + "; ".join(_ititles)
                                            )
                    except Exception:
                        pass
                    try:
                        if (not sec.get("allow_connectors")) or sec.get("sandbox"):
                            raise Exception("connectors disabled")
                        _cal_token = _get_user_connector_secret(
                            current_user["id"], "google_calendar"
                        )
                        if _cal_token and any(
                            k in user_message.lower()
                            for k in (
                                "meeting",
                                "calendar",
                                "agenda",
                                "event",
                                "schedule",
                                "appointment",
                                "reunião",
                                "hoje",
                            )
                        ):
                            import aiohttp as _aio2

                            async with _aio2.ClientSession(
                                timeout=_aio2.ClientTimeout(total=5)
                            ) as _s2:
                                import datetime as _dt

                                _now = _dt.datetime.utcnow().isoformat() + "Z"
                                _end = (
                                    _dt.datetime.utcnow() + _dt.timedelta(days=3)
                                ).isoformat() + "Z"
                                async with _s2.get(
                                    "https://www.googleapis.com/calendar/v3/calendars/primary/events"
                                    f"?timeMin={_now}&timeMax={_end}&maxResults=5"
                                    "&orderBy=startTime&singleEvents=true",
                                    headers={"Authorization": f"Bearer {_cal_token}"},
                                ) as _cr:
                                    if _cr.status == 200:
                                        _cdata = await _cr.json()
                                        _evts = _cdata.get("items") or []
                                        _enames = [
                                            e.get("summary", "(no title)")[:50]
                                            for e in _evts
                                            if isinstance(e, dict)
                                        ]
                                        if _enames:
                                            _conn_ctx_parts.append(
                                                "Google Calendar — upcoming events (3 days): "
                                                + "; ".join(_enames)
                                            )
                    except Exception:
                        pass
                    # ── Gmail context ─────────────────────────────────────────
                    try:
                        if (not sec.get("allow_connectors")) or sec.get("sandbox"):
                            raise Exception("connectors disabled")
                        _gmail_token = _get_user_connector_secret(
                            current_user["id"], "gmail"
                        )
                        if _gmail_token and any(
                            k in user_message.lower()
                            for k in (
                                "email",
                                "mail",
                                "inbox",
                                "gmail",
                                "mensagem",
                                "e-mail",
                                "thread",
                                "reply",
                                "responder",
                                "newsletter",
                            )
                        ):
                            import aiohttp as _aio3

                            async with _aio3.ClientSession(
                                timeout=_aio3.ClientTimeout(total=5)
                            ) as _s3:
                                # Search recent unread emails
                                async with _s3.get(
                                    "https://gmail.googleapis.com/gmail/v1/users/me/messages"
                                    "?q=is:unread&maxResults=5",
                                    headers={"Authorization": f"Bearer {_gmail_token}"},
                                ) as _gmr:
                                    if _gmr.status == 200:
                                        _gmdata = await _gmr.json()
                                        _msg_ids = [
                                            m["id"]
                                            for m in (_gmdata.get("messages") or [])[:5]
                                        ]
                                        _subjects: List[str] = []
                                        for _mid in _msg_ids[:3]:
                                            async with _s3.get(
                                                f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{_mid}"
                                                "?format=metadata&metadataHeaders=Subject,From",
                                                headers={
                                                    "Authorization": f"Bearer {_gmail_token}"
                                                },
                                            ) as _mdr:
                                                if _mdr.status == 200:
                                                    _md = await _mdr.json()
                                                    _hdrs = {
                                                        h["name"]: h["value"]
                                                        for h in (
                                                            _md.get("payload", {}).get(
                                                                "headers"
                                                            )
                                                            or []
                                                        )
                                                    }
                                                    _subj = _hdrs.get(
                                                        "Subject", "(no subject)"
                                                    )[:60]
                                                    _frm = _hdrs.get("From", "")[:40]
                                                    _subjects.append(
                                                        f'"{_subj}" from {_frm}'
                                                    )
                                        if _subjects:
                                            _conn_ctx_parts.append(
                                                "Gmail — recent unread emails: "
                                                + "; ".join(_subjects)
                                            )
                    except Exception:
                        pass

                    # ── Google Drive context ───────────────────────────────────
                    try:
                        if (not sec.get("allow_connectors")) or sec.get("sandbox"):
                            raise Exception("connectors disabled")
                        _drive_token = _get_user_connector_secret(
                            current_user["id"], "google_drive"
                        )
                        if _drive_token and any(
                            k in user_message.lower()
                            for k in (
                                "file",
                                "document",
                                "doc",
                                "sheet",
                                "spreadsheet",
                                "drive",
                                "arquivo",
                                "planilha",
                                "relatório",
                                "report",
                                "slide",
                                "presentation",
                                "folder",
                                "pasta",
                            )
                        ):
                            import aiohttp as _aio4

                            async with _aio4.ClientSession(
                                timeout=_aio4.ClientTimeout(total=5)
                            ) as _s4:
                                # Extract possible filename hint from message
                                _query_words = [
                                    w
                                    for w in user_message.split()
                                    if len(w) > 3 and w[0].isupper()
                                ]
                                _drive_q = (
                                    " ".join(_query_words[:3]) if _query_words else ""
                                )
                                _drive_search = (
                                    f"name contains '{_drive_q}' and "
                                    if _drive_q
                                    else ""
                                ) + "trashed=false"
                                async with _s4.get(
                                    "https://www.googleapis.com/drive/v3/files"
                                    f"?q={_drive_search}&pageSize=5"
                                    "&fields=files(id,name,mimeType,modifiedTime)",
                                    headers={"Authorization": f"Bearer {_drive_token}"},
                                ) as _drr:
                                    if _drr.status == 200:
                                        _drdata = await _drr.json()
                                        _files = _drdata.get("files") or []
                                        _type_map = {
                                            "application/vnd.google-apps.spreadsheet": "Sheet",
                                            "application/vnd.google-apps.document": "Doc",
                                            "application/vnd.google-apps.presentation": "Slides",
                                            "application/vnd.google-apps.folder": "Folder",
                                        }
                                        _fnames = [
                                            f"{_type_map.get(f.get('mimeType', ''), 'File')}: {f['name'][:50]}"
                                            for f in _files
                                            if f.get("name")
                                        ]
                                        if _fnames:
                                            _conn_ctx_parts.append(
                                                "Google Drive — matching files: "
                                                + "; ".join(_fnames)
                                            )
                    except Exception:
                        pass

                    if _conn_ctx_parts:
                        _conn_block = "\n".join(f"• {c}" for c in _conn_ctx_parts)
                        user_context = (
                            f"{user_context}\n\nConnector context:\n{_conn_block}"
                        ).strip()

                    if (
                        ENABLE_SYSTEM_PROFILE
                        and ATTACH_SYSTEM_PROFILE
                        and sec.get("allow_system_profile")
                    ):
                        stored_profile = get_user_system_profile(current_user["id"])
                        if not stored_profile:
                            try:
                                bundle = _build_system_profile(int(current_user["id"]))
                                upsert_user_system_profile(
                                    current_user["id"],
                                    bundle.get("markdown") or "",
                                    bundle.get("data") or {},
                                )
                                stored_profile = get_user_system_profile(
                                    current_user["id"]
                                )
                            except Exception:
                                stored_profile = stored_profile or None
                        summary = _format_system_profile_summary(
                            (stored_profile or {}).get("data") or {}
                        )
                        if summary:
                            if user_context:
                                user_context = f"{user_context}\n\nPerfil do sistema (uso interno):\n{summary}".strip()
                            else:
                                user_context = f"Perfil do sistema (uso interno):\n{summary}".strip()
                        try:
                            _is_sw_op = (
                                expert is not None
                                and str((expert or {}).get("id") or "").strip().lower()
                                == "software_operator"
                            )
                            _needs_sw_ctx = _is_sw_op or bool(
                                (expert or {}).get("tool_needed")
                            )
                            _installed_for_ctx: List[Dict[str, Any]] = []
                            d = (stored_profile or {}).get("data") or {}
                            if isinstance(d.get("top20_productivity"), list):
                                _installed_for_ctx = d.get("top20_productivity") or []
                            elif sys.platform == "win32":
                                _installed_for_ctx = get_installed_software()

                            if _needs_sw_ctx:
                                _sw_block = _build_software_tool_context(
                                    _installed_for_ctx
                                )
                                user_context = f"{user_context}\n\n{_sw_block}".strip()
                            elif _installed_for_ctx:
                                names = []
                                for it in _installed_for_ctx[:20]:
                                    nm = str((it or {}).get("name") or "").strip()
                                    pid = str((it or {}).get("id") or "").strip()
                                    if nm:
                                        label = nm if not pid else f"{nm} [{pid}]"
                                        names.append(label)
                                if names:
                                    block = "Softwares instalados relevantes:\n- " + "\n- ".join(names)
                                    user_context = f"{user_context}\n\n{block}".strip()
                        except Exception:
                            pass

                    stored_llm = get_user_llm_settings(current_user["id"])
                    llm_override = _safe_llm_settings(
                        (stored_llm or {}).get("settings") or {}
                    )
                    api_key = _get_user_api_key(current_user["id"], llm_override.get("provider"))
                    if api_key:
                        llm_override["api_key"] = api_key

                    _lower_user_msg = str(user_message or "").lower()
                    _looks_like_automation_request = (
                        ("software_operator" in _lower_user_msg)
                        or ("captura" in _lower_user_msg and "tela" in _lower_user_msg)
                        or ("capture" in _lower_user_msg and "tela" in _lower_user_msg)
                        or ("screenshot" in _lower_user_msg)
                        or ("vision_analysis.png" in _lower_user_msg)
                    )
                    _looks_like_url_request = bool(
                        re.search(r"https?://", _lower_user_msg)
                    )
                    _skip_cac = bool(
                        expert
                        and (
                            bool(expert.get("tool_needed"))
                            or str(expert.get("id") or "").strip().lower()
                            == "software_operator"
                        )
                    ) or bool(_looks_like_automation_request) or bool(_looks_like_url_request)
                    if ENABLE_CAC and not is_file_request and not _skip_cac:
                        qh = _hash_question(
                            user_message
                            if not internal_prompt
                            else f"{user_message}\n\n{internal_prompt}"
                        )
                        cached = get_cached_answer(
                            current_user["id"], qh, max_age_hours=CACHE_MAX_AGE_HOURS
                        )
                        if cached and cached.get("answer"):
                            full_response = str(cached.get("answer") or "")
                            save_message(
                                conversation_id,
                                "assistant",
                                full_response,
                                expert_id=expert["id"] if expert else None,
                                provider="cache",
                                model="cac",
                                tokens=None,
                            )
                            await websocket.send_json(
                                {
                                    "type": "chunk",
                                    "content": full_response,
                                }
                            )
                            await websocket.send_json(
                                {
                                    "type": "done",
                                    "content": full_response,
                                    "expert": expert,
                                    "provider": "cache",
                                    "model": "cac",
                                    "tokens": None,
                                }
                            )
                            continue

                    user_message_for_llm = user_message
                    if is_file_request and base_path_for_write:
                        user_message_for_llm = f"{user_message}\n\nA pasta destino para salvar arquivos é: {base_path_for_write}"
                    elif recent_context:
                        user_message_for_llm = f"Contexto recente da conversa:\n{recent_context}\n\nPergunta atual:\n{user_message}"

                    rag_context = ""
                    if (
                        ENABLE_RAG_SQLITE
                        and not is_file_request
                        and not sec.get("sandbox")
                    ):
                        rag_items = search_user_memory(
                            current_user["id"], user_message, limit=6
                        )
                        rag_context = _format_rag_memory(rag_items)
                    if rag_context:
                        user_message_for_llm = f"{user_message_for_llm}\n\nMemória relevante (RAG local):\n{rag_context}"

                    # Inject active skill system prompt into context
                    if internal_prompt:
                        _internal_header = f"--- Instruções internas ---\n{internal_prompt}\n--- Fim instruções ---"
                        if user_context:
                            user_context = f"{_internal_header}\n\n{user_context}"
                        else:
                            user_context = _internal_header

                    if _active_skill_prompt:
                        skill_header = f"--- Active skill ---\n{_active_skill_prompt}\n--- End skill ---"
                        if user_context:
                            user_context = f"{skill_header}\n\n{user_context}"
                        else:
                            user_context = skill_header

                    web_context = ""
                    url_context = ""
                    url_fetch_notice = ""
                    if (
                        bool(sec.get("allow_web_retrieval"))
                        and ENABLE_URL_FETCH
                        and re.search(r"https?://", user_message or "", flags=re.I)
                    ):
                        _url_diag = _url_fetch_diagnostics(user_message)
                        _urls_any = _url_diag.get("urls") or []
                        _urls_allowed = _url_diag.get("allowed_urls") or []
                        _hosts_blocked = _url_diag.get("blocked_hosts") or []
                        if _urls_any and not _urls_allowed and _hosts_blocked:
                            url_fetch_notice = (
                                "Nota: não consegui ler o(s) link(s) enviado(s) por segurança "
                                "(link não elegível: host local/rede privada, não-HTTPS, IP literal, ou host bloqueado). "
                                f"Hosts bloqueados: {', '.join([str(h) for h in _hosts_blocked[:6]])}. "
                                "Se você colar aqui o texto relevante (ou enviar um link de um host permitido), "
                                "eu consigo analisar e planejar normalmente."
                            ).strip()
                        elif _hosts_blocked:
                            url_fetch_notice = (
                                "Nota: alguns links não puderam ser lidos por segurança "
                                "(link não elegível: host local/rede privada, não-HTTPS, IP literal, ou host bloqueado). "
                                f"Hosts bloqueados: {', '.join([str(h) for h in _hosts_blocked[:6]])}. "
                                "Se você colar aqui o trecho relevante desses links, eu incorporo na análise."
                            ).strip()
                        await websocket.send_json(
                            {"type": "status", "content": "Lendo links fornecidos..."}
                        )
                        _last_emit[0] = time.time()
                        url_context = await _url_fetch_context(user_message)
                        if url_context:
                            user_message_for_llm = f"{user_message_for_llm}\n\nContexto dos links fornecidos (pode estar incompleto):\n{url_context}"
                        elif (_urls_allowed and not url_context) and not url_fetch_notice:
                            url_fetch_notice = (
                                "Nota: tentei ler o(s) link(s) enviado(s), mas não consegui obter conteúdo. "
                                "Se você colar aqui o texto relevante, eu continuo a análise."
                            ).strip()

                    # Web search rules:
                    # - Skill with web_search=true: always attempts (bypasses global flag)
                    # - Keyword heuristic: only when ENABLE_WEB_RETRIEVAL=1
                    _wants_web_skill = ws_skill_web_search
                    _wants_web_heuristic = (
                        ENABLE_WEB_RETRIEVAL and _needs_web_retrieval(user_message)
                    )
                    _wants_web = bool(sec.get("allow_web_retrieval")) and (
                        _wants_web_skill or _wants_web_heuristic
                    )
                    if _wants_web:
                        await websocket.send_json(
                            {"type": "status", "content": "Buscando na web..."}
                        )
                        _last_emit[0] = time.time()
                        web_context = await _web_retrieve_context(user_message)
                        if web_context:
                            await websocket.send_json(
                                {
                                    "type": "status",
                                    "content": "Analisando resultados da web...",
                                }
                            )
                            _last_emit[0] = time.time()
                    if web_context:
                        user_message_for_llm = f"{user_message_for_llm}\n\nContexto da web (pode estar incompleto):\n{web_context}"

                    _agno_result = None
                    if (
                        expert
                        and bool(expert.get("tool_needed"))
                        and not is_file_request
                        and bool(getattr(settings, "enable_agno_poc", False))
                    ):
                        _agno_result = await _maybe_run_tool_needed_with_agno(
                            prompt=user_message_for_llm,
                            user_id=int(current_user["id"]),
                            conversation_id=int(conversation_id),
                            sec=sec,
                            expert=expert,
                            llm_override=llm_override,
                            user_context=user_context,
                            websocket=websocket,
                        )
                        if _agno_result:
                            full_response = str(_agno_result.get("content") or "")
                            expert_info = _agno_result.get("expert_info") or {
                                "provider": "agno",
                                "model": None,
                                "tokens": None,
                            }

                    _is_sw_op_stream = (
                        expert is not None
                        and str((expert or {}).get("id") or "").strip().lower()
                        == "software_operator"
                        and not is_file_request
                    )
                    if not _agno_result:
                        async for chunk in llm_manager.stream_generate(
                            user_message_for_llm,
                            expert,
                            user_context=user_context,
                            llm_override=llm_override,
                        ):
                            if isinstance(chunk, str):
                                full_response += chunk
                                if not is_file_request and not _is_sw_op_stream:
                                    await _ws_send(
                                        {"type": "chunk", "content": chunk}
                                    )
                            else:
                                expert_info = chunk

                    if (
                        expert
                        and str(expert.get("id") or "").strip().lower()
                        == "software_operator"
                        and not is_file_request
                    ):
                        try:
                            _cmd_line = str(full_response or "").strip()
                            _app, _act, _ = parse_cli_command_text(_cmd_line)
                            _label = (
                                f"▶ Executando: {_app} ({_act})"
                                if (_app and _act)
                                else "▶ Executando: automação"
                            )
                            await websocket.send_json(
                                {
                                    "type": "status",
                                    "content": _label,
                                }
                            )
                        except Exception:
                            pass
                        full_response = await _run_external_software_skill(
                            command_text=full_response,
                            user_id=int(current_user["id"]),
                            conversation_id=int(conversation_id),
                            sec=sec,
                            expert=expert,
                            llm_override=llm_override,
                            user_context=user_context,
                            websocket=websocket,
                        )

                    files_bundle = (
                        _extract_files_json(full_response) if is_file_request else None
                    )
                    if is_file_request:
                        if not sec.get("allow_file_write"):
                            full_response = "⚠️ Escrita de arquivos está desabilitada nas permissões desta conta."
                        else:
                            if (
                                files_bundle
                                and base_path_for_write
                                and not str(files_bundle.get("base_path") or "").strip()
                            ):
                                files_bundle["base_path"] = base_path_for_write
                            if not files_bundle and base_path_for_write:
                                files_bundle = _default_landing_bundle(
                                    base_path_for_write
                                )
                            if not files_bundle:
                                full_response = "❌ Não consegui gerar o pacote de arquivos para salvar."
                            else:
                                try:
                                    write_result = _write_files_bundle(files_bundle)
                                    created_list = write_result.get("written") or []
                                    delivery_registry[delivery_id] = {
                                        "base_path": str(
                                            write_result.get("base_path") or ""
                                        ),
                                        "user_id": current_user["id"],
                                        "created_at": datetime.utcnow().isoformat(),
                                    }
                                    preview_url = f"/local/{delivery_id}/index.html"
                                    summary = (
                                        "✅ Arquivos criados:\n"
                                        + "\n".join([f"- {p}" for p in created_list])
                                        + f"\n\nPreview: {preview_url}"
                                    )
                                    full_response = summary
                                    _record_activity_done(
                                        int(current_user["id"]),
                                        f"[FILES] Criados {len(created_list)} arquivo(s) em {str(write_result.get('base_path') or '')}",
                                    )
                                except Exception as write_err:
                                    full_response = f"❌ Falha ao salvar arquivos localmente: {str(write_err)}"
                    elif "<COMMAND_JSON>" in full_response:
                        try:
                            full_response = await _process_command_blocks(
                                text=full_response,
                                user_id=int(current_user["id"]),
                                session_id=str(session_id),
                                conversation_id=int(conversation_id),
                            )
                        except Exception:
                            pass
                    elif ENABLE_CAC and not (expert and expert.get("tool_needed")):
                        try:
                            qh = _hash_question(user_message)
                            if full_response.strip():
                                put_cached_answer(
                                    current_user["id"], qh, user_message, full_response
                                )
                        except Exception:
                            pass

                    if ENABLE_MEMORY_WRITE and not is_file_request:
                        try:
                            _auto_memorize_user_message(
                                int(current_user["id"]), user_message
                            )
                        except Exception:
                            pass
                        # Phase 2: momentum — reinforce RAG memories that were used
                        try:
                            if rag_items:
                                _used_ids = [
                                    int(r.get("id"))
                                    for r in rag_items
                                    if r.get("id") is not None
                                ]
                                reinforce_memory_usage(
                                    int(current_user["id"]), _used_ids
                                )
                        except Exception:
                            pass
                        # Phase 3: periodic decay (1% of requests to avoid latency)
                        try:
                            import random as _rnd

                            if _rnd.random() < 0.01:
                                decay_memory(int(current_user["id"]))
                                prune_low_salience_memories(int(current_user["id"]))
                        except Exception:
                            pass

                    try:
                        if (
                            _forced_plan_text
                            and "```plan" not in full_response
                            and "PLAN_TASKS:" not in full_response
                        ):
                            full_response = (
                                f"{_forced_plan_text}\n\n{str(full_response or '').strip()}"
                            ).strip()
                    except Exception:
                        pass

                    try:
                        if (
                            url_fetch_notice
                            and not is_file_request
                            and str(url_fetch_notice) not in str(full_response or "")
                        ):
                            full_response = (
                                f"{str(full_response or '').strip()}\n\n---\n\n{url_fetch_notice}"
                            ).strip()
                    except Exception:
                        pass

                    # Plan detection — look for structured plan in assistant response
                    _plan_detected = False
                    _plan_tasks_detected: List[Dict[str, Any]] = []
                    try:
                        if "```plan" in full_response or "PLAN_TASKS:" in full_response:
                            import re as _re2

                            _plan_block = _re2.search(
                                r"```plan\s*(.*?)```", full_response, _re2.DOTALL
                            )
                            if _plan_block:
                                _raw = _plan_block.group(1).strip()
                                for _line in _raw.splitlines():
                                    _line = _line.strip().lstrip("-•*").strip()
                                    if _line:
                                        _parts = _line.split("|")
                                        _title = _parts[0].strip()
                                        _skill = (
                                            _parts[1].strip()
                                            if len(_parts) > 1
                                            else None
                                        )
                                        if not _skill:
                                            try:
                                                _last_token = (_line.split() or [""])[-1].strip().lower()
                                                if _last_token in ("software_operator", "project"):
                                                    _skill = _last_token
                                            except Exception:
                                                pass
                                        if _title:
                                            _plan_tasks_detected.append(
                                                {
                                                    "title": _title,
                                                    "skill_id": _skill or None,
                                                }
                                            )
                                _plan_detected = bool(_plan_tasks_detected)
                    except Exception:
                        pass

                    try:
                        if _plan_detected:
                            await _ws_send(
                                {
                                    "type": "status",
                                    "content": "ℹ Plano detectado. Clique em “Aprovar” para executar.",
                                }
                            )
                    except Exception:
                        pass

                    # Salvar mensagem do assistente
                    save_message(
                        conversation_id,
                        "assistant",
                        full_response,
                        expert_id=expert["id"] if expert else None,
                        provider=expert_info.get("provider") if expert_info else None,
                        model=expert_info.get("model") if expert_info else None,
                        tokens=expert_info.get("tokens") if expert_info else None,
                    )

                    # Enviar mensagem final
                    # Retrieve saved assistant message id for feedback
                    _last_msg_id = None
                    try:
                        import sqlite3 as _sq

                        with _sq.connect(str(get_db_path())) as _c:
                            row = _c.execute(
                                "SELECT id FROM messages WHERE conversation_id=? AND role='assistant' ORDER BY id DESC LIMIT 1",
                                (conversation_id,),
                            ).fetchone()
                            if row:
                                _last_msg_id = row[0]
                    except Exception:
                        pass

                    _debug_router = _env_flag(
                        os.getenv("OPENSLAP_DEBUG_ROUTER"), False
                    ) or bool(data.get("debug_router"))
                    payload = {
                        "type": "done",
                        "content": full_response,
                        "expert": expert,
                        "message_id": _last_msg_id,
                        "plan_detected": _plan_detected,
                        "plan_tasks": _plan_tasks_detected,
                        "provider": (
                            expert_info.get("provider") if expert_info else None
                        ),
                        "model": expert_info.get("model") if expert_info else None,
                        "tokens": (
                            expert_info.get("tokens") if expert_info else None
                        ),
                    }
                    if _debug_router:
                        payload["selection_reason"] = (expert or {}).get(
                            "selection_reason", ""
                        )
                        payload["matched_keywords"] = (expert or {}).get(
                            "matched_keywords", []
                        )
                    await _ws_send(payload)
                    try:
                        logger.info(
                            "ws_chat_done user_id=%s session_id=%s conversation_id=%s expert_id=%s chars=%s",
                            str(current_user.get("id")),
                            str(session_id),
                            str(conversation_id),
                            str((expert or {}).get("id") or ""),
                            str(len(full_response or "")),
                        )
                    except Exception:
                        pass

            except WebSocketDisconnect:
                try:
                    logger.info(
                        "ws_disconnect user_id=%s session_id=%s",
                        str(current_user.get("id")),
                        str(session_id),
                    )
                except Exception:
                    pass
                break
            except Exception as e:
                try:
                    logger.exception(
                        "ws_error user_id=%s session_id=%s",
                        str(current_user.get("id")),
                        str(session_id),
                    )
                except Exception:
                    pass
                await websocket.send_json(
                    {"type": "error", "content": f"Erro: {str(e)}"}
                )
                break
            finally:
                try:
                    if _done_evt is not None:
                        _done_evt.set()
                except Exception:
                    pass
                try:
                    if _ka_task is not None:
                        _ka_task.cancel()
                except Exception:
                    pass

    finally:
        # Limpar conexão
        if session_id in active_connections:
            del active_connections[session_id]


# Endpoints existentes (compatibilidade)
@app.get("/health")
async def health_check():
    """Health check"""
    providers = []
    providers_error = None
    try:
        providers = await asyncio.wait_for(llm_manager.get_provider_status(), timeout=0.8)
    except Exception as e:
        providers_error = str(e)
    return {
        "status": "ok",
        "version": "1.0.0",
        "auth_enabled": True,
        "sessions": len(active_connections),
        "providers": providers,
        "providers_error": providers_error,
        "experts": moe_router.get_experts(),
    }


@app.get("/api/artifacts/{artifact_id}", include_in_schema=False)
async def get_artifact(
    artifact_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    token = credentials.credentials
    current_user = get_current_user(token)
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado")
    info = artifact_registry.get(str(artifact_id or "").strip())
    if not info:
        raise HTTPException(status_code=404, detail="Artefato não encontrado")
    p = Path(str(info.get("path") or "")).resolve()
    if not p.is_file():
        raise HTTPException(status_code=404, detail="Artefato não encontrado")
    r = FileResponse(str(p), filename=p.name)
    r.headers["Cache-Control"] = "no-store"
    r.headers["Pragma"] = "no-cache"
    return r


@app.get("/api/system_profile/installed_software")
async def get_installed_sw(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    current_user = get_current_user(token)
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado")
    items = get_installed_software()
    top20 = _top20_productivity(items)
    return {"installed": items, "top20": top20}


@app.post("/api/system_profile/refresh_inventory")
async def refresh_inventory(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    current_user = get_current_user(token)
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado")
    # force refresh by invalidating cache and re-scan
    global _installed_cache_ts
    _installed_cache_ts = None
    items = get_installed_software(max_age_s=0)
    top20 = _top20_productivity(items)
    try:
        bundle = _build_system_profile(int(current_user["id"]))
        upsert_user_system_profile(
            current_user["id"],
            bundle.get("markdown") or "",
            bundle.get("data") or {},
        )
    except Exception:
        pass
    return {"ok": True, "count": len(items), "top20_count": len(top20)}

@app.get("/api/system_map")
async def get_system_map(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    current_user = get_current_user(token)
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado")
    sec = _get_effective_security_settings(int(current_user["id"]))
    if not sec.get("allow_system_profile"):
        raise HTTPException(status_code=403, detail="Permissão negada")
    global _system_map_cache
    if not str(_system_map_cache.get("ascii") or "").strip():
        ascii_map = _generate_system_map_ascii()
        _system_map_cache = {
            "ascii": ascii_map,
            "generated_at": datetime.utcnow().isoformat() + "Z",
        }
    return {"ascii": _system_map_cache.get("ascii") or "", "generated_at": _system_map_cache.get("generated_at") or ""}


@app.post("/api/system_map/refresh")
async def refresh_system_map(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    current_user = get_current_user(token)
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado")
    sec = _get_effective_security_settings(int(current_user["id"]))
    if not sec.get("allow_system_profile"):
        raise HTTPException(status_code=403, detail="Permissão negada")
    global _system_map_cache
    ascii_map = _generate_system_map_ascii()
    _system_map_cache = {
        "ascii": ascii_map,
        "generated_at": datetime.utcnow().isoformat() + "Z",
    }
    return {"ascii": _system_map_cache.get("ascii") or "", "generated_at": _system_map_cache.get("generated_at") or ""}


@app.get("/api/doctor")
async def doctor_endpoint(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    token = credentials.credentials
    current_user = get_current_user(token)
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado")

    user_id = int(current_user["id"])
    stored_llm = get_user_llm_settings(user_id)
    llm_settings = _safe_llm_settings((stored_llm or {}).get("settings") or {})
    llm_mode = str(llm_settings.get("mode") or "env").strip().lower()
    llm_provider = str(llm_settings.get("provider") or "").strip().lower()
    llm_model = str(llm_settings.get("model") or "").strip()
    llm_base_url = str(llm_settings.get("base_url") or "").strip()
    stored_key = _get_user_api_key(user_id, llm_provider) or ""
    api_key = stored_key
    api_key_source = "stored" if stored_key else "none"
    has_api_key = bool(api_key)

    system_profile = get_user_system_profile(user_id) or {}
    profile_data = system_profile.get("data") or {}
    profile_updated_at = system_profile.get("updated_at")

    providers = await llm_manager.get_provider_status()

    checks: List[Dict[str, Any]] = []
    recommendations: List[str] = []

    checks.append(
        {
            "id": "system_profile",
            "label": "Perfil do sistema coletado",
            "ok": bool(system_profile.get("markdown")),
            "detail": (
                f"Atualizado em: {profile_updated_at}"
                if profile_updated_at
                else "Ainda não coletado"
            ),
            "action": "refresh_system_profile",
        }
    )

    disks = profile_data.get("disks") if isinstance(profile_data, dict) else None
    disk_hint = ""
    if isinstance(disks, list) and disks:
        for d in disks:
            if not isinstance(d, dict):
                continue
            dev = str(d.get("device_id") or "").strip()
            free_b = d.get("free_bytes")
            total_b = d.get("size_bytes")
            if dev and isinstance(free_b, int) and isinstance(total_b, int):
                disk_hint = f"{dev}: {_fmt_bytes_gib(free_b)} livre de {_fmt_bytes_gib(total_b)}"
                break
    if disk_hint:
        checks.append(
            {
                "id": "disk_space",
                "label": "Espaço em disco (amostra)",
                "ok": True,
                "detail": disk_hint,
            }
        )

    if sys.platform == "win32":
        av_raw = _collect_powershell_json(
            "Get-CimInstance -Namespace root/SecurityCenter2 -ClassName AntivirusProduct "
            "| Select-Object displayName,productState,timestamp "
            "| ConvertTo-Json -Depth 4"
        )
        av_items: List[Dict[str, Any]] = []
        if isinstance(av_raw, list):
            av_items = [x for x in av_raw if isinstance(x, dict)]
        elif isinstance(av_raw, dict):
            av_items = [av_raw]
        av_names = []
        for it in av_items:
            name = str(it.get("displayName") or "").strip()
            if name:
                av_names.append(name)
        if av_names:
            checks.append(
                {
                    "id": "antivirus_products",
                    "label": "Antivírus (Security Center)",
                    "ok": True,
                    "detail": ", ".join(av_names[:4])
                    + (f" (+{len(av_names) - 4})" if len(av_names) > 4 else ""),
                }
            )
        else:
            checks.append(
                {
                    "id": "antivirus_products",
                    "label": "Antivírus (Security Center)",
                    "ok": False,
                    "detail": "Não foi possível listar (permissões/recurso indisponível?)",
                }
            )

        defender_raw = _collect_powershell_json(
            "Get-MpComputerStatus "
            "| Select-Object AMServiceEnabled,AntivirusEnabled,AntispywareEnabled,RealTimeProtectionEnabled,IoavProtectionEnabled,OnAccessProtectionEnabled,BehaviorMonitorEnabled,NISEnabled,SignatureLastUpdated "
            "| ConvertTo-Json -Depth 4"
        )
        if isinstance(defender_raw, dict):
            rtp = bool(defender_raw.get("RealTimeProtectionEnabled"))
            sig = defender_raw.get("SignatureLastUpdated")
            detail = f"Real-time: {'ON' if rtp else 'OFF'}" + (
                f" • Assinaturas: {sig}" if sig else ""
            )
            checks.append(
                {
                    "id": "defender_status",
                    "label": "Microsoft Defender",
                    "ok": rtp,
                    "detail": detail,
                }
            )
            if not rtp and not av_names:
                recommendations.append(
                    "Ative a proteção em tempo real do Microsoft Defender (ou confirme o antivírus instalado)."
                )
        else:
            checks.append(
                {
                    "id": "defender_status",
                    "label": "Microsoft Defender",
                    "ok": False,
                    "detail": "Não foi possível consultar (cmdlet Get-MpComputerStatus indisponível?)",
                }
            )

        fw_raw = _collect_powershell_json(
            "Get-NetFirewallProfile | Select-Object Name,Enabled,DefaultInboundAction,DefaultOutboundAction | ConvertTo-Json -Depth 4"
        )
        fw_items: List[Dict[str, Any]] = []
        if isinstance(fw_raw, list):
            fw_items = [x for x in fw_raw if isinstance(x, dict)]
        elif isinstance(fw_raw, dict):
            fw_items = [fw_raw]
        if fw_items:
            enabled_all = all(bool(x.get("Enabled")) for x in fw_items)
            detail = "; ".join(
                [
                    f"{str(x.get('Name') or '').strip()}: {'ON' if bool(x.get('Enabled')) else 'OFF'}"
                    for x in fw_items
                    if str(x.get("Name") or "").strip()
                ]
            )
            checks.append(
                {
                    "id": "firewall_profiles",
                    "label": "Firewall do Windows",
                    "ok": bool(enabled_all),
                    "detail": detail or "Perfis consultados",
                }
            )
            if not enabled_all:
                recommendations.append(
                    "Ative o Firewall do Windows para todos os perfis (Domínio/Privado/Público)."
                )
        else:
            checks.append(
                {
                    "id": "firewall_profiles",
                    "label": "Firewall do Windows",
                    "ok": False,
                    "detail": "Não foi possível consultar (cmdlet Get-NetFirewallProfile indisponível?)",
                }
            )

    effective_provider = llm_provider
    if llm_mode == "local" and not effective_provider:
        effective_provider = "ollama"
    if llm_mode == "api" and not effective_provider:
        effective_provider = "openai"
    if llm_mode == "api" and not api_key:
        env_key = _get_env_api_key_for_provider(effective_provider) or ""
        if env_key:
            api_key = env_key
            api_key_source = "env"
            has_api_key = True

    if llm_mode == "local":
        ollama_status = providers.get("ollama") or {}
        checks.append(
            {
                "id": "ollama_online",
                "label": "Ollama online",
                "ok": bool(ollama_status.get("online")),
                "detail": (
                    f"Modelo: {ollama_status.get('model')}"
                    if ollama_status.get("online")
                    else "Não foi possível conectar em http://localhost:11434"
                ),
            }
        )
        checks.append(
            {
                "id": "local_model_set",
                "label": "Modelo local configurado",
                "ok": bool(llm_model),
                "detail": llm_model or "Defina um modelo (ex.: qwen2.5:1.5b)",
            }
        )
        if not ollama_status.get("online"):
            recommendations.append(
                "Inicie o Ollama e confirme a URL base (padrão: http://localhost:11434)."
            )
        if not llm_model:
            recommendations.append(
                "Configure um modelo local leve para começar (ex.: qwen2.5:1.5b) e depois aumente conforme a máquina."
            )

    if llm_mode == "api":
        checks.append(
            {
                "id": "api_key_set",
                "label": "Chave de API cadastrada",
                "ok": bool(has_api_key),
                "detail": (
                    (
                        "Chave protegida no servidor local"
                        if api_key_source == "stored"
                        else "Chave carregada do .env"
                    )
                    if has_api_key
                    else "Cadastre uma chave nas Configurações de LLM ou no .env"
                ),
            }
        )

        def _sanitize_base_url(v: str) -> str:
            s = str(v or "").strip()
            if (
                (s.startswith("`") and s.endswith("`"))
                or (s.startswith('"') and s.endswith('"'))
                or (s.startswith("'") and s.endswith("'"))
            ):
                s = s[1:-1].strip()
            return s.strip(" ,")

        async def _test_api_provider(
            provider_id: str, base_url: str, key: str
        ) -> Dict[str, Any]:
            p = (provider_id or "").strip().lower()
            bu = _sanitize_base_url(base_url)
            k = _sanitize_api_key(key)
            if not bu:
                if p == "groq":
                    bu = "https://api.groq.com/openai/v1"
                elif p == "openai":
                    bu = "https://api.openai.com/v1"
                elif p == "gemini":
                    bu = "https://generativelanguage.googleapis.com/v1"

            timeout = aiohttp.ClientTimeout(total=6)
            try:
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    if p == "gemini":
                        url = f"{bu}/models"
                        headers = {"x-goog-api-key": k}
                    else:
                        url = f"{bu}/models"
                        headers = {"Authorization": f"Bearer {k}"}

                    async with session.get(url, headers=headers) as resp:
                        status = int(resp.status)
                        if status == 200:
                            return {
                                "online": True,
                                "detail": "Teste usando a chave cadastrada: OK",
                                "status": status,
                                "base_url": bu,
                            }
                        if status in {401, 403}:
                            return {
                                "online": False,
                                "detail": "Credenciais recusadas (401/403)",
                                "status": status,
                                "base_url": bu,
                            }
                        if status == 404:
                            return {
                                "online": False,
                                "detail": "Endpoint não encontrado (base URL incorreta?)",
                                "status": status,
                                "base_url": bu,
                            }
                        return {
                            "online": False,
                            "detail": f"HTTP {status}",
                            "status": status,
                            "base_url": bu,
                        }
            except asyncio.TimeoutError:
                return {
                    "online": False,
                    "detail": "Timeout ao testar o provider",
                    "status": None,
                    "base_url": bu,
                }
            except Exception:
                return {
                    "online": False,
                    "detail": "Falhou ao testar conectividade/credenciais",
                    "status": None,
                    "base_url": bu,
                }

        provider_result: Optional[Dict[str, Any]] = None
        if (
            effective_provider
            and has_api_key
            and effective_provider in {"groq", "openai", "gemini"}
        ):
            provider_result = await _test_api_provider(
                effective_provider, llm_base_url, api_key
            )
            checks.append(
                {
                    "id": "provider_online",
                    "label": f"Provider {effective_provider} online",
                    "ok": bool(provider_result.get("online")),
                    "detail": provider_result.get("detail") or "",
                }
            )
        elif effective_provider in {"groq", "openai", "gemini"} and not has_api_key:
            checks.append(
                {
                    "id": "provider_online",
                    "label": f"Provider {effective_provider} online",
                    "ok": False,
                    "detail": "Sem chave cadastrada",
                }
            )

        if not has_api_key:
            recommendations.append(
                "Cadastre a chave do provider (Groq/OpenAI/Gemini) para usar modo API."
            )
        else:
            if effective_provider in {"groq", "openai"} and not llm_model:
                recommendations.append(
                    "Defina um modelo (ou deixe em branco para usar o padrão do servidor)."
                )
            if provider_result is not None and not bool(provider_result.get("online")):
                if effective_provider == "groq":
                    recommendations.append(
                        "Verifique se há internet/firewall, e se a base URL é https://api.groq.com/openai/v1."
                    )
                if effective_provider == "openai":
                    recommendations.append(
                        "Verifique se há internet/firewall, e se a base URL é https://api.openai.com/v1."
                    )
                if effective_provider == "gemini":
                    recommendations.append(
                        "Verifique se a base URL é https://generativelanguage.googleapis.com/v1 e se a chave começa com AIza."
                    )

    checks.append(
        {
            "id": "llm_mode",
            "label": "Modo LLM",
            "ok": True,
            "detail": llm_mode,
        }
    )
    if effective_provider:
        checks.append(
            {
                "id": "llm_provider",
                "label": "Provider selecionado",
                "ok": True,
                "detail": effective_provider,
            }
        )
    if llm_base_url:
        checks.append(
            {
                "id": "llm_base_url",
                "label": "Base URL",
                "ok": True,
                "detail": llm_base_url,
            }
        )

    overall_ok = all(
        bool(c.get("ok"))
        for c in checks
        if c.get("id")
        in {
            "system_profile",
            "ollama_online",
            "local_model_set",
            "api_key_set",
            "provider_online",
        }
    )
    if not recommendations and llm_mode in {"local", "api"}:
        if overall_ok:
            recommendations.append(
                "Tudo pronto. Se quiser mais performance em máquinas modernas, aumente o modelo e o contexto."
            )
        else:
            recommendations.append(
                "Revise os itens marcados como FALHOU e rode o diagnóstico novamente."
            )

    return {
        "ok": overall_ok,
        "checks": checks,
        "recommendations": recommendations,
        "llm": {
            "mode": llm_mode,
            "provider": effective_provider or llm_provider or "",
            "model": llm_model,
            "base_url": llm_base_url,
            "has_api_key": bool(has_api_key),
        },
        "system_profile": {
            "updated_at": profile_updated_at,
            "summary": _format_system_profile_summary(profile_data),
        },
        "providers": providers,
    }


@app.get("/api/commands/config")
async def commands_config(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    token = credentials.credentials
    current_user = get_current_user(token)
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado")
    sec = _get_effective_security_settings(int(current_user["id"]))
    user_id = int(current_user["id"])
    roots = _get_allowed_command_roots(user_id=user_id)
    return {
        "enabled": bool(ENABLE_OS_COMMANDS) and bool(sec.get("allow_os_commands")),
        "timeout_s": int(OS_COMMAND_TIMEOUT_S),
        "max_output_chars": int(OS_COMMAND_MAX_OUTPUT_CHARS),
        "allowed_roots": roots,
    }


@app.post("/api/commands/plan")
async def commands_plan(
    payload: CommandPlanInput,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    token = credentials.credentials
    current_user = get_current_user(token)
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado")
    sec = _get_effective_security_settings(int(current_user["id"]))
    if not sec.get("allow_os_commands"):
        return {
            "enabled": False,
            "allowed": False,
            "blocked_reason": "Execução de comandos desabilitada nas permissões desta conta",
        }
    if not ENABLE_OS_COMMANDS:
        return {
            "enabled": False,
            "allowed": False,
            "blocked_reason": "Execução de comandos desabilitada",
        }
    plan = _command_policy_evaluate(
        command=payload.command, cwd=payload.cwd, user_id=int(current_user["id"])
    )
    return {"enabled": True, **plan}


@app.post("/api/commands/pending/{request_id}/execute")
async def commands_execute_pending(
    request_id: str,
    payload: CommandExecuteInput,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    token = credentials.credentials
    current_user = get_current_user(token)
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado")
    sec = _get_effective_security_settings(int(current_user["id"]))
    if not sec.get("allow_os_commands"):
        raise HTTPException(
            status_code=403,
            detail="Execução de comandos desabilitada nas permissões desta conta.",
        )
    if not ENABLE_OS_COMMANDS:
        raise HTTPException(
            status_code=400, detail="Execução de comandos desabilitada no servidor."
        )

    req = pending_command_registry.get(request_id)
    if not req:
        raise HTTPException(
            status_code=404, detail="Solicitação não encontrada ou expirada."
        )
    if int(req.get("user_id") or 0) != int(current_user["id"]):
        raise HTTPException(
            status_code=403, detail="Sem permissão para esta solicitação."
        )

    cmd = str(req.get("command") or "").strip()
    cwd = str(req.get("cwd") or os.path.abspath(str(BASE_DIR)))
    plan = _command_policy_evaluate(
        command=cmd, cwd=cwd, user_id=int(current_user["id"])
    )
    if not plan.get("allowed"):
        raise HTTPException(
            status_code=400, detail=plan.get("blocked_reason") or "Comando bloqueado."
        )
    if plan.get("requires_confirmation") and not bool(payload.confirm):
        raise HTTPException(
            status_code=412, detail="Confirmação necessária para executar este comando."
        )

    run_res = await _run_powershell_command(
        command=cmd, cwd=str(plan.get("cwd") or cwd), timeout_s=OS_COMMAND_TIMEOUT_S
    )
    output = run_res.get("output") or ""

    try:
        save_message(
            int(req.get("conversation_id") or 0),
            "assistant",
            f"✅ Comando executado:\n{cmd}\n\n{output or '(sem saída)'}",
            expert_id=None,
            provider="runtime",
            model="os_command",
            tokens=None,
        )
    except Exception:
        pass

    try:
        del pending_command_registry[request_id]
    except Exception:
        pass

    return {
        "request_id": request_id,
        "command": cmd,
        "cwd": str(plan.get("cwd") or cwd),
        **run_res,
    }

@app.post("/api/commands/pending/{request_id}/autoapprove")
async def commands_autoapprove_pending(
    request_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    token = credentials.credentials
    current_user = get_current_user(token)
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado")
    sec = _get_effective_security_settings(int(current_user["id"]))
    if not sec.get("allow_os_commands"):
        raise HTTPException(
            status_code=403,
            detail="Execução de comandos desabilitada nas permissões desta conta.",
        )
    if not ENABLE_OS_COMMANDS:
        raise HTTPException(
            status_code=400, detail="Execução de comandos desabilitada no servidor."
        )
    req = pending_command_registry.get(request_id)
    if not req:
        raise HTTPException(status_code=404, detail="Solicitação não encontrada ou expirada.")
    if int(req.get("user_id") or 0) != int(current_user["id"]):
        raise HTTPException(status_code=403, detail="Sem permissão para esta solicitação.")

    cmd = str(req.get("command") or "").strip()
    if not cmd:
        raise HTTPException(status_code=400, detail="Comando vazio.")
    plan = _command_policy_evaluate(command=cmd, cwd=str(req.get("cwd") or ""), user_id=int(current_user["id"]))
    if not plan.get("allowed"):
        raise HTTPException(status_code=400, detail=plan.get("blocked_reason") or "Comando bloqueado.")
    if int(plan.get("risk_level") or 1) != 1:
        raise HTTPException(status_code=400, detail="Apenas comandos de baixo risco podem ser autoaprovados.")

    key = _normalize_command_key(cmd)
    ok = add_user_command_autoapprove(int(current_user["id"]), key)
    return {"ok": True, "added": bool(ok), "command_norm": key}

@app.get("/api/friction/config")
async def friction_config(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    token = credentials.credentials
    current_user = get_current_user(token)
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado")
    return {"mode": _friction_mode()}


@app.get("/api/friction/pending_count")
async def friction_pending_count(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    token = credentials.credentials
    current_user = get_current_user(token)
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado")
    if _friction_mode() == "disabled":
        return {"mode": "disabled", "pending": 0}
    return {"mode": _friction_mode(), "pending": count_pending_friction_events()}


@app.get("/api/friction/pending")
async def friction_pending(
    limit: int = 100, credentials: HTTPAuthorizationCredentials = Depends(security)
):
    token = credentials.credentials
    current_user = get_current_user(token)
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado")
    if _friction_mode() == "disabled":
        raise HTTPException(status_code=404, detail="Friction module disabled")
    rows = list_friction_events(sent=0, limit=limit)
    items: List[Dict[str, Any]] = []
    for r in rows:
        payload = json.loads(r.get("payload_json", "{}"))
        items.append(
            {"id": r.get("id"), "payload": payload, "created_at": r.get("created_at")}
        )
    return {"mode": _friction_mode(), "events": items}


@app.post("/api/friction/report")
async def friction_report(
    report: FrictionReportInput,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    mode = _friction_mode()
    if mode == "disabled":
        raise HTTPException(status_code=404, detail="Friction module disabled")

    token = credentials.credentials
    current_user = get_current_user(token)
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado")

    payload = _friction_payload(report)
    event_id = create_friction_event(payload, mode=mode)

    if mode == "auto":
        try:
            issue_url = await _create_github_issue(payload, submission_mode="auto")
            mark_friction_event_sent(event_id, issue_url)
            print(f"#friction_event_id={event_id} github_url={issue_url}")
            resp = _friction_frontend_payload(
                report=report,
                event_id=event_id,
                mode=mode,
                github_url=issue_url,
                status="sent",
            )
            print("#" + resp["message"])
            return resp
        except Exception as e:
            resp = _friction_frontend_payload(
                report=report,
                event_id=event_id,
                mode=mode,
                github_url=None,
                status="queued",
            )
            resp["error"] = str(e)
            return resp

    return _friction_frontend_payload(
        report=report,
        event_id=event_id,
        mode=mode,
        github_url=None,
        status="queued",
    )


@app.post("/api/friction/pending/send")
async def friction_send_pending(
    limit: int = 50,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    if _friction_mode() == "disabled":
        raise HTTPException(status_code=404, detail="Friction module disabled")

    token = credentials.credentials
    current_user = get_current_user(token)
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado")

    rows = list_friction_events(sent=0, limit=limit)
    results: List[Dict[str, Any]] = []
    for r in rows:
        event_id = int(r.get("id"))
        payload = json.loads(r.get("payload_json", "{}"))
        try:
            issue_url = await _create_github_issue(payload, submission_mode="demand")
            mark_friction_event_sent(event_id, issue_url)
            results.append({"id": event_id, "status": "sent", "github_url": issue_url})
        except Exception as e:
            results.append({"id": event_id, "status": "error", "error": str(e)})
    return {
        "sent": [r for r in results if r["status"] == "sent"],
        "errors": [r for r in results if r["status"] == "error"],
    }


@app.post("/api/friction/pending/{event_id}/discard")
async def friction_discard_pending(
    event_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    if _friction_mode() == "disabled":
        raise HTTPException(status_code=404, detail="Friction module disabled")

    token = credentials.credentials
    current_user = get_current_user(token)
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado")

    ok = delete_friction_event(event_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Evento não encontrado")
    return {"status": "discarded", "id": event_id}


@app.delete("/api/session/{session_id}")
async def clear_session(
    session_id: str, credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Limpa sessão"""
    token = credentials.credentials
    current_user = get_current_user(token)
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado")
    if session_id in active_connections:
        await active_connections[session_id].close()
        del active_connections[session_id]

    return {"message": "Sessão limpa"}


# ── Produção: servir o frontend buildado ──────────────────────────────────────
# Quando o Vite já rodou `npm run build`, o FastAPI serve tudo sozinho.
# Em desenvolvimento, o Vite roda separado na porta 3000 com proxy.
_FRONTEND_DIST = BASE_DIR / "frontend" / "dist"
if _FRONTEND_DIST.exists():
    app.mount(
        "/assets",
        StaticFiles(directory=str(_FRONTEND_DIST / "assets")),
        name="spa-assets",
    )

    @app.get("/{full_path:path}", include_in_schema=False)
    async def _serve_spa(full_path: str):
        """Catch-all: serve index.html para qualquer rota não-API (SPA)."""
        # Priorizar arquivos em /media mesmo que o Mount não capture por algum motivo
        if full_path.startswith("media/"):
            media_path = (MEDIA_DIR / full_path[len("media/") :]).resolve()
            try:
                if MEDIA_DIR.resolve() in media_path.parents and media_path.is_file():
                    return FileResponse(str(media_path))
            except Exception:
                pass
        if full_path and "." in full_path:
            try:
                requested = (_FRONTEND_DIST / full_path).resolve()
                dist_root = _FRONTEND_DIST.resolve()
                if dist_root in requested.parents and requested.is_file():
                    return FileResponse(str(requested))
            except Exception:
                pass
        index = _FRONTEND_DIST / "index.html"
        if not index.exists():
            from fastapi.responses import JSONResponse

            return JSONResponse(
                {"detail": "Frontend não buildado. Rode: npm run build"},
                status_code=503,
            )
        return FileResponse(str(index))


# Inicialização
if __name__ == "__main__":
    import uvicorn
    from pathlib import Path

    # Criar diretório de dados
    os.makedirs("data", exist_ok=True)

    print("🚀 Iniciando Agêntico Backend com Autenticação")
    print("📍 Endpoints disponíveis:")
    print("   POST /auth/register - Registrar usuário")
    print("   POST /auth/login - Fazer login")
    print("   GET  /auth/me - Obter usuário atual")
    print("   GET  /api/conversations - Listar conversas")
    print("   POST /api/conversations - Criar conversa")
    print("   GET  /api/conversations/{id} - Obter mensagens")
    print("   DELETE /api/conversations/{id} - Deletar conversa")
    print("   WS   /ws/{session_id}?token={jwt} - Chat com streaming")

    reload_env = (os.getenv("OPENSLAP_RELOAD") or "").strip().lower()
    should_reload = reload_env in {"1", "true", "yes", "on"}
    backend_dir = str(Path(__file__).resolve().parent)
    uvicorn.run(
        "main_auth:app",
        host=os.getenv("OPENSLAP_HOST", "127.0.0.1"),
        port=int(os.getenv("OPENSLAP_PORT", "5150")),
        reload=should_reload,
        reload_dirs=[backend_dir] if should_reload else None,
        reload_excludes=["data/*", "*.db", "*.sqlite", "**/*.db", "**/*.sqlite"] if should_reload else None,
    )
