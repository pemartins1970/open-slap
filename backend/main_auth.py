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

# Importar utilitários
from .utils.env import (
    env_flag as _env_flag,
    env_int as _env_int,
    env_float as _env_float,
    env_list as _env_list,
)
from .utils.auth_helpers import (
    extract_bearer_token_from_headers,
    is_public_path,
    requires_auth,
    PUBLIC_PATHS,
    PUBLIC_PATH_PREFIXES,
    PROTECTED_PATHS,
    PROTECTED_PATH_PREFIXES,
)
from .utils.commands import (
    split_semicolon_paths,
    normalize_command_key,
    normalize_cwd,
    is_under_allowed_roots,
)
from .utils.system import (
    generate_system_map_ascii,
    format_system_profile_summary,
)

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
    get_user_auth_settings,
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

# Alias para compatibilidade
get_telegram_user_by_link_code = get_telegram_linked_user_id

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
from .routes.auth_routes import router as auth_routes_router
from .routes.project_routes import router as project_routes_router
# Novos routers extraídos
from .routes.media_routes import media_router
from .routes.forge_routes import forge_router
from .routes.search_skills_routes import search_skills_router
from .routes.connectors_routes import connectors_router
from .routes.profile_routes import profile_router
from .routes.feedback_plan_routes import feedback_plan_router
from .routes.memory_connectors_routes import memory_connectors_router
from .routes.delivery_routes import delivery_router
from .routes.padxml_routes import padxml_router
from .routes.onboarding_routes import onboarding_router
from .routes.health_routes import health_router
from .routes.system_routes import system_router
from .routes.commands_routes import commands_router
from .routes.friction_routes import friction_router
from .routes.mcp_registry_routes import mcp_registry_router
from .routes.referral_routes import referral_router
from .routes.marketplace_routes import marketplace_router

# Serviços
from .services.wizard_service import (
    is_project_wizard_start,
    handle_wizard_message,
    project_wizard_registry,
    PROJECT_WIZARD_ID
)

# Configurações
app = FastAPI(title="Agêntico Backend", version="1.0.0")

from .deps import MEDIA_DIR
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


class AuthRequiredMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.method.upper() == "OPTIONS":
            return await call_next(request)
        if is_public_path(request.url.path) or not requires_auth(request.url.path):
            return await call_next(request)
        token = extract_bearer_token_from_headers(dict(request.headers))
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


# Endpoints de mídia extraídos para media_routes.py


# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

# Rate Limiting e Account Lockout
from .middleware.rate_limiter import add_rate_limiting, add_account_lockout

# Rate limiting por endpoint
add_rate_limiting(app, {
    "/auth/login": {"limit": 5, "window": 300},      # 5 tentativas em 5 minutos
    "/auth/register": {"limit": 3, "window": 300},   # 3 registros em 5 minutos
    "/auth/password-reset": {"limit": 3, "window": 300}, # 3 resets em 5 minutos
    "/api/conversations": {"limit": 100, "window": 60}, # 100 conversas por minuto
    "/ws/": {"limit": 1000, "window": 60},       # 1000 mensagens por minuto
})

# Account lockout após falhas
add_account_lockout(app, max_attempts=5, lockout_duration=900)  # 5 tentativas, 15 min bloqueio

# Segurança

# Componentes

DEFAULT_DELIVERIES_ROOT = os.path.join(os.path.expanduser("~"), "OpenSlap", "Entregas")
# Wizard ID e Registry agora gerenciados via services/wizard_service.py
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
from .deps import (
    FORGE_IDE_MODE,
    FORGE_IDE_EMAIL,
    FORGE_IDE_TOKEN_TTL_MINUTES,
    _is_local_client,
    _ensure_forge_user,
    delivery_registry,
    _system_map_cache,
    pending_command_registry,
    artifact_registry,
    active_connections,
)

# Aliases para funções de sistema
_generate_system_map_ascii = lambda: generate_system_map_ascii(
    base_dir=str(BASE_DIR),
    target_dirs=["frontend/src", "backend"]
)


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


# Funções do Wizard migradas para services/wizard_service.py



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


# Modelos Pydantic (Migrados para os respectivos APIRouters)
# UserRegister, UserLogin, PasswordReset, ProjectInput agora vivem em seus módulos de rota.

class ChatMessage(BaseModel):
    content: str


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


# Import referral service
from .services.referral_service import add_referral_tracking, track_external_click

async def _web_retrieve_context(query: str) -> str:
    if not ENABLE_WEB_RETRIEVAL or not query:
        return ""
    
    # Adicionar tracking à URL de pesquisa
    search_url = "https://api.duckduckgo.com/"
    tracked_url = add_referral_tracking(search_url, "Open Slap!")
    
    # Registrar clique de pesquisa
    track_external_click(
        tracked_url,
        source_type="web_search",
        metadata={"query": query, "search_engine": "duckduckgo"}
    )
    
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
            # Adicionar tracking à URL antes de acessar
            tracked_url = add_referral_tracking(u, "Open Slap!")
            
            # Registrar clique de URL externa
            track_external_click(
                tracked_url,
                source_type="user_message",
                metadata={"original_url": u, "context": "url_fetch"}
            )
            
            parsed = urlparse(tracked_url)
            host = str(parsed.hostname or "").lower().strip()
            if host.endswith("github.com"):
                ctx = await _github_repo_context(
                    tracked_url, timeout_s=URL_FETCH_TIMEOUT_S, max_chars=max(2000, int(URL_FETCH_MAX_CHARS))
                )
            else:
                ctx = await _fetch_text_url(
                    tracked_url, timeout_s=URL_FETCH_TIMEOUT_S, max_chars=max(2000, int(URL_FETCH_MAX_CHARS))
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


# Endpoints de delivery extraídos para delivery_routes.py


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


# Rotas /auth/* gerenciadas por auth_routes_router (incluído abaixo via include_router)
# Remoção das duplicatas — fix crítico reportado na revisão externa.


# Endpoints Forge extraídos para forge_routes.py


app.include_router(conversations_tasks_router)
app.include_router(settings_router)
app.include_router(autoapprove_router)
app.include_router(meta_router)
app.include_router(auth_routes_router)
app.include_router(project_routes_router)
# Novos routers extraídos
app.include_router(media_router)
app.include_router(forge_router)
app.include_router(search_skills_router)
app.include_router(connectors_router)
app.include_router(profile_router)
app.include_router(feedback_plan_router)
app.include_router(memory_connectors_router)
app.include_router(delivery_router)
app.include_router(padxml_router)
app.include_router(onboarding_router)
app.include_router(health_router)
app.include_router(system_router)
app.include_router(commands_router)
app.include_router(friction_router)
app.include_router(mcp_registry_router)
app.include_router(referral_router)
app.include_router(marketplace_router)


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


# Endpoints de orchestration extraídos para feedback_plan_routes.py


# Rotas de Projetos migradas para project_routes_router


# Endpoints de padxml extraídos para padxml_routes.py

# Endpoints de onboarding extraídos para onboarding_routes.py

# WebSocket handler extraído para ws.orchestrator
# Importar orquestrador
from .ws.orchestrator import ws_orchestrator


@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """Endpoint WebSocket simplificado — delega para o orquestrador."""
    token = websocket.query_params.get("token") or _extract_bearer_token_from_headers(
        dict(websocket.headers)
    )
    if not token:
        await websocket.close(code=4001, reason="Token não fornecido")
        return

    current_user = await get_current_user_ws(websocket, token)
    if not current_user:
        return

    # Delegar para o orquestrador
    await ws_orchestrator.handle_connection(websocket, session_id, current_user)


# Endpoints extraídos para routes/system_routes.py, commands_routes.py, friction_routes.py
# NOTA: health_check e get_artifact definidos nas linhas 7090+ (removidos duplicados)

# Endpoints migrados:
# - /api/system_profile/*
# - /api/system_map/*
# - /api/doctor
# - /api/commands/*
# - /api/friction/*
# - /api/session/*


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


# MCP Loader - Carrega MCPs ativos no boot
async def initialize_mcp_system():
    """Inicializa o sistema de MCPs no boot"""
    try:
        from services.skill_service import skill_service
        from db import get_all_users
        
        print("?? Inicializando sistema de MCPs...")
        
        # Obter todos os usuários ativos
        users = get_all_users() or []
        
        # Carregar MCPs para cada usuário
        for user in users:
            user_id = user.get("id")
            if user_id:
                await skill_service.load_user_mcps(user_id)
                print(f"   MCPs carregados para usuário {user_id}")
        
        print(f"?? Sistema MCP inicializado para {len(users)} usuários")
        
    except Exception as e:
        print(f"?? Erro ao inicializar sistema MCP: {str(e)}")
        logger.error(f"MCP initialization error: {str(e)}")


# Inicialização
if __name__ == "__main__":
    import uvicorn
    from pathlib import Path

    # Criar diretório de dados
    os.makedirs("data", exist_ok=True)

    print("?? Iniciando Agêntico Backend com Autenticação")
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
