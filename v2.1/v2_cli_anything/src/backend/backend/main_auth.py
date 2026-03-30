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
from datetime import datetime
from typing import Dict, Any, Optional, List

from pathlib import Path
from dotenv import load_dotenv

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
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
import aiohttp

BASE_DIR = Path(__file__).resolve().parents[1]
load_dotenv(dotenv_path=BASE_DIR / ".env", override=False)

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
    save_message,
    delete_conversation,
    get_conversation_by_session_for_user,
    update_conversation_title,
    search_user_messages,
    add_task_todo,
    list_task_todos,
    list_pending_todos,
    update_task_todo,
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
    upsert_user_api_key_ciphertext,
    get_user_api_key_ciphertext,
    delete_user_api_key,
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
    upsert_user_soul,
    get_user_soul,
    append_soul_event,
    list_soul_events,
    get_cached_answer,
    put_cached_answer,
    search_user_memory,
)
from .llm_manager_simple import LLMManager
from .moe_router_simple import MoERouter

# Configurações
app = FastAPI(title="Agêntico Backend", version="1.0.0")

MEDIA_DIR = BASE_DIR.parent / "media"
MEDIA_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/media", StaticFiles(directory=str(MEDIA_DIR)), name="media")


def _env_flag(v: Optional[str], default: bool = False) -> bool:
    s = str(v if v is not None else ("1" if default else "0")).strip().lower()
    return s in ("1", "true", "yes", "on")


def _env_int(v: Optional[str], default: int) -> int:
    try:
        return int(str(v or "").strip()) if v is not None and str(v).strip() else default
    except Exception:
        return default


def _env_float(v: Optional[str], default: float) -> float:
    try:
        return float(str(v or "").strip()) if v is not None and str(v).strip() else default
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
        self.enable_web_retrieval = _env_flag(os.getenv("OPENSLAP_WEB_RETRIEVAL"), False)
        self.web_retrieval_timeout_s = _env_float(os.getenv("OPENSLAP_WEB_RETRIEVAL_TIMEOUT_S"), 6.0)
        self.enable_cac = _env_flag(os.getenv("OPENSLAP_CAC"), True)
        self.cache_max_age_hours = _env_int(os.getenv("OPENSLAP_CAC_MAX_AGE_HOURS"), 24)
        self.enable_rag_sqlite = _env_flag(os.getenv("OPENSLAP_RAG_SQLITE"), True)
        self.enable_system_profile = _env_flag(os.getenv("OPENSLAP_SYSTEM_PROFILE"), True)
        self.attach_system_profile = _env_flag(os.getenv("OPENSLAP_ATTACH_SYSTEM_PROFILE"), True)
        self.system_profile_max_chars = _env_int(os.getenv("OPENSLAP_SYSTEM_PROFILE_MAX_CHARS"), 24000)
        self.enable_os_commands = _env_flag(os.getenv("OPENSLAP_OS_COMMANDS"), True)
        self.os_command_timeout_s = _env_int(os.getenv("OPENSLAP_OS_COMMAND_TIMEOUT_S"), 12)
        self.os_command_max_output_chars = _env_int(os.getenv("OPENSLAP_OS_COMMAND_MAX_OUTPUT_CHARS"), 12000)
        self.os_command_allowed_roots_raw = str(os.getenv("OPENSLAP_OS_COMMAND_ALLOWED_ROOTS") or "").strip()
        self.cors_origins = _env_list(os.getenv("OPENSLAP_CORS_ORIGINS")) or [
            "http://localhost",
            "http://localhost:5173",
            "http://127.0.0.1:5173",
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
    "/auth/register",
    "/auth/login",
    "/auth/password-reset/request",
    "/auth/password-reset/confirm",
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


class AuthRequiredMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.method.upper() == "OPTIONS":
            return await call_next(request)
        if _is_public_path(request.url.path):
            return await call_next(request)
        token = _extract_bearer_token_from_headers(dict(request.headers))
        if not token:
            return JSONResponse(status_code=401, content={"detail": "Token não fornecido"})
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
    allow_methods=["*"],
    allow_headers=["*"],
)

# Segurança
security = HTTPBearer()
security_optional = HTTPBearer(auto_error=False)

# Componentes
llm_manager = LLMManager()
moe_router = MoERouter()

# Armazenamento de sessões WebSocket
active_connections: Dict[str, WebSocket] = {}
delivery_registry: Dict[str, Dict[str, Any]] = {}
pending_command_registry: Dict[str, Dict[str, Any]] = {}
DEFAULT_DELIVERIES_ROOT = os.path.join(os.path.expanduser("~"), "OpenSlap", "Entregas")
PROJECT_WIZARD_ID = "start_project_v1"
project_wizard_registry: Dict[int, Dict[str, Any]] = {}
ENABLE_WEB_RETRIEVAL = settings.enable_web_retrieval
WEB_RETRIEVAL_TIMEOUT_S = settings.web_retrieval_timeout_s
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


def _strip_assistant_directives(text: str) -> str:
    s = (text or "").strip()
    if not s:
        return ""
    s = re.sub(r"\[\[assistant_split(?::\d{1,5})?\]\]", "", s, flags=re.IGNORECASE)
    s = re.sub(r"\[\[open_settings:[a-z0-9_-]+\]\]", "", s, flags=re.IGNORECASE)
    s = re.sub(r"\[\[(?:set_expert|force_expert):[a-z0-9_-]+\]\]", "", s, flags=re.IGNORECASE)
    s = re.sub(r"\[\[clear_expert\]\]", "", s, flags=re.IGNORECASE)
    s = re.sub(r"\n{3,}", "\n\n", s).strip()
    return s


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
    starters = ("como ", "o que ", "oq ", "por que", "pq ", "qual ", "quais ", "onde ", "quando ", "dúvida", "duvida")
    return any(lower.startswith(s) for s in starters)


def _project_wizard_detect_blog_ambiguity(user_message: str) -> bool:
    lower = (user_message or "").lower()
    if "blog" not in lower:
        return False
    known = ("wordpress", "ghost", "medium", "substack", "blogger", "wix", "webflow")
    if any(k in lower for k in known):
        return False
    if any(k in lower for k in ("do zero", "do 0", "custom", "sob medida", "próprio", "proprio", "localmente")):
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
        if lower in {"sim", "s", "confirmo", "confirmado", "ok", "certo", "perfeito", "isso", "isso mesmo"} or "sim" in lower:
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
                    append_soul_event(int(user_id), "project_wizard", " | ".join(pieces)[:900])
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

    if stage == "q1" and _project_wizard_detect_blog_ambiguity(user_message) and not state.get("asked_blog_clarify"):
        state["stage"] = "blog_clarify"
        state["asked_blog_clarify"] = True
        q = (
            "Entendi. Você precisa criar um blog. Seria um novo sistema de blog, que desenvolveríamos aqui, "
            "localmente, ou você apenas deseja ajuda para criar um blog em um dos diversos sistemas disponíveis "
            "na internet, e quer ajuda neste processo?"
        )
        return {"content": f"{answer_text}\n\n[[assistant_split:1200]]\n\n{q}", "done": False}

    if stage == "blog_clarify":
        state["stage"] = "q2"
        q = _project_wizard_next_step_text("q2")
        return {"content": f"{answer_text}\n\n[[assistant_split:1200]]\n\n{q}", "done": False}

    next_stage_map = {"q1": "q2", "q2": "q3", "q3": "q4", "q4": "q5"}
    if stage in next_stage_map:
        next_stage = next_stage_map[stage]
        state["stage"] = next_stage
        q = _project_wizard_next_step_text(next_stage)
        return {"content": f"{answer_text}\n\n[[assistant_split:1200]]\n\n{q}", "done": False}

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
        summary = "\n".join(summary_lines) if summary_lines else "- (sem detalhes suficientes)"
        out = (
            "Perfeito. Aqui está o que eu entendi até agora:\n"
            f"{summary}\n\n"
            "Confirma que está correto?"
        )
        return {"content": out, "done": False}

    state["stage"] = "q2"
    q = _project_wizard_next_step_text("q2")
    return {"content": f"{answer_text}\n\n[[assistant_split:1200]]\n\n{q}", "done": False}


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
    if any(k in lower for k in ("tarefas:", "tarefa:", "todo:", "to-do:", "pendências:", "pendencia:")):
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
        implied = ("preciso", "tenho que", "devo", "não esquecer", "nao esquecer", "lembrar", "me lembre")
        compact = " ".join(text.split()).strip()
        compact_lower = compact.lower()
        if compact_lower.startswith(action_starts) or any(k in compact_lower for k in implied):
            if 6 <= len(compact) <= 240:
                items.append(compact)

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


class ConversationCreate(BaseModel):
    title: str


class TitleUpdate(BaseModel):
    title: str


class GitHubConnectInput(BaseModel):
    token: str


class TokenConnectInput(BaseModel):
    token: str


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


class TodoCreate(BaseModel):
    text: str


class AutomationClientSettingsInput(BaseModel):
    base_url: str
    api_key: Optional[str] = None


class TodoUpdate(BaseModel):
    text: Optional[str] = None
    status: Optional[str] = None


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


class LlmSettingsInput(BaseModel):
    mode: str
    provider: Optional[str] = None
    model: Optional[str] = None
    base_url: Optional[str] = None
    api_key: Optional[str] = None


class LanguageSettingsInput(BaseModel):
    lang: str


class SecuritySettingsInput(BaseModel):
    sandbox: Optional[bool] = None
    allow_os_commands: Optional[bool] = None
    allow_file_write: Optional[bool] = None
    allow_web_retrieval: Optional[bool] = None
    allow_connectors: Optional[bool] = None
    allow_system_profile: Optional[bool] = None


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
MEMORY_SNAPSHOT_MAX_CHARS = int(os.getenv("OPENSLAP_MEMORY_SNAPSHOT_MAX_CHARS") or "3500")


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

    if "agente" in m and any(k in m for k in ("aprend", "evolu", "com o tempo", "ao longo do tempo")):
        out.append("Preferência: agentes aprendem incrementalmente (evitar antecipar tudo)")
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
    context_tokens = ["rodando", "executando", "qual versão", "qual versao", "onde", "descreva", "sobre"]

    if any(amb in t for amb in ambiguous_tokens) and any(ctx in t for ctx in context_tokens):
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
                for k in ["DeviceIdentifier", "Size", "Content", "MountPoint", "VolumeName"]:
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
                    ["bash", "-lc", "lsb_release -a 2>/dev/null || cat /etc/os-release 2>/dev/null || true"],
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


def _collect_web_services_info() -> Dict[str, Any]:
    if sys.platform == "win32":
        services = _collect_powershell_json(
            "Get-Service -ErrorAction SilentlyContinue | "
            "Where-Object { $_.Name -in @('W3SVC','Apache2.4','nginx','MySQL80','MariaDB','postgresql-x64-17','postgresql-x64-16','Redis','Memcached') } | "
            "Select-Object Name, DisplayName, Status, StartType | ConvertTo-Json -Compress",
            timeout_s=8,
        )
        processes = _collect_powershell_json(
            "Get-Process -ErrorAction SilentlyContinue | "
            "Where-Object { $_.Name -in @('nginx','httpd','apache2','php','php-cgi','mysqld','mariadbd','postgres','redis-server','laragon') } | "
            "Select-Object Name, Id, Path | ConvertTo-Json -Compress",
            timeout_s=8,
        )
        ports = _collect_powershell_json(
            "Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue | "
            "Where-Object { $_.LocalPort -in @(80,443,8000,8080,3000,5173,3306,5432,6379) } | "
            "Select-Object LocalAddress, LocalPort, OwningProcess | ConvertTo-Json -Compress",
            timeout_s=8,
        )
        detected: List[str] = []
        try:
            if isinstance(services, dict):
                services = [services]
            if isinstance(services, list):
                for s in services:
                    if not isinstance(s, dict):
                        continue
                    name = str(s.get("Name") or "").strip().lower()
                    if name == "w3svc":
                        detected.append("IIS")
                    if name in ["apache2.4", "nginx", "mysql80", "mariadb"]:
                        detected.append(name)
                    if name.startswith("postgresql"):
                        detected.append("postgresql")
            if isinstance(processes, dict):
                processes = [processes]
            if isinstance(processes, list):
                for p in processes:
                    if not isinstance(p, dict):
                        continue
                    nm = str(p.get("Name") or p.get("name") or "").strip().lower()
                    path = str(p.get("Path") or p.get("path") or "").strip().lower()
                    if "laragon" in nm or "laragon" in path:
                        detected.append("Laragon")
        except Exception:
            pass
        detected = sorted(set([x for x in detected if x]))
        return {
            "services": services or [],
            "processes": processes or [],
            "listen_ports": ports or [],
            "detected": detected,
        }

    try:
        res = subprocess.run(
            ["bash", "-lc", "lsof -iTCP -sTCP:LISTEN -P -n 2>/dev/null | head -n 200 || netstat -an 2>/dev/null | head -n 200 || true"],
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
        detected: List[str] = []
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
                detected.append(token)
        detected = sorted(set([x for x in detected if x]))
        return {
            "listen_summary": txt,
            "processes_summary": processes_txt,
            "services_summary": services_txt,
            "detected": detected,
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
                dev = df_row.get("device_id") or (f"/dev/{kname}" if kname and not kname.startswith("/") else kname)
                fstype = str(node.get("fstype") or df_row.get("file_system") or "").strip()
                size_b = df_row.get("size_bytes")
                if not isinstance(size_b, int):
                    try:
                        size_b = int(node.get("size")) if node.get("size") is not None else None
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
                "size_bytes": row.get("size_bytes") if isinstance(row.get("size_bytes"), int) else None,
                "free_bytes": row.get("free_bytes") if isinstance(row.get("free_bytes"), int) else None,
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
    web_services = _collect_web_services_info()

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
            extra.append(_truncate_text(json.dumps(mac_hw_small, ensure_ascii=False) if mac_hw_small is not None else "", 6000))
            extra.append("```")
        if mac_diskutil_small:
            extra.append("## diskutil list -plist\n\n```")
            extra.append(_truncate_text(json.dumps(mac_diskutil_small, ensure_ascii=False) if mac_diskutil_small is not None else "", 6000))
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
        if isinstance(web_services, dict) and isinstance(web_services.get("detected"), list) and web_services.get("detected"):
            svc_lines.append("- Detectado: " + ", ".join([str(x) for x in web_services.get("detected") if x]))
        if isinstance(web_services, dict) and isinstance(web_services.get("services"), list):
            for s in web_services.get("services") or []:
                if not isinstance(s, dict):
                    continue
                name = str(s.get("Name") or s.get("name") or "").strip()
                status = str(s.get("Status") or s.get("status") or "").strip()
                if name:
                    svc_lines.append(f"- {name}: {status}".strip())
        if isinstance(web_services, dict) and isinstance(web_services.get("listen_ports"), list):
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
    triggers = [
        "bios",
        "uefi",
        "placa-mãe",
        "placa mae",
        "motherboard",
        "hd",
        "hdd",
        "ssd",
        "disco",
        "armazenamento",
        "storage",
        "drive",
        "volume",
        "laragon",
        "apache",
        "nginx",
        "iis",
        "w3svc",
        "porta",
        "port",
        "serviço",
        "servico",
    ]
    return any(x in t for x in triggers)


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
            if isinstance(web_services, dict) and isinstance(web_services.get("services"), list):
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
            if isinstance(web_services, dict) and isinstance(web_services.get("listen_ports"), list):
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
    bios = profile_data.get("bios") if isinstance(profile_data, dict) else None
    disks = profile_data.get("disks") if isinstance(profile_data, dict) else None

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

    return "\n".join([line for line in lines if line]).strip()


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


def _get_user_api_key(user_id: int) -> Optional[str]:
    ct = get_user_api_key_ciphertext(int(user_id))
    if not ct:
        return None
    raw = _dpapi_unprotect_text(ct) or ""
    key = _sanitize_api_key(raw)
    return key or None


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
        raise HTTPException(status_code=403, detail="Conectores desabilitados nas permissões.")


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


# Endpoints de Conversas
@app.get("/api/conversations")
async def list_conversations(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    kind: Optional[str] = Query("conversation"),
):
    """Lista conversas do usuário"""
    token = credentials.credentials
    current_user = get_current_user(token)

    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado")

    conversations = get_user_conversations(current_user["id"], kind=kind)
    return {"conversations": conversations}


@app.post("/api/conversations")
async def create_conversation_endpoint(
    conversation: ConversationCreate,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    kind: Optional[str] = Query("conversation"),
):
    """Cria nova conversa"""
    token = credentials.credentials
    current_user = get_current_user(token)

    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado")

    kind_to_save = (kind or "conversation").strip().lower()
    if kind_to_save not in ("conversation", "task"):
        kind_to_save = "conversation"

    title = (conversation.title or "").strip()
    if not title:
        raise HTTPException(status_code=400, detail="Título vazio")

    session_id = str(uuid.uuid4())
    conversation_id = create_conversation(
        current_user["id"], session_id, title, kind=kind_to_save
    )

    return {
        "conversation_id": conversation_id,
        "session_id": session_id,
        "title": conversation.title,
    }


@app.put("/api/conversations/{conversation_id}/title")
async def rename_conversation_endpoint(
    conversation_id: int,
    payload: TitleUpdate,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    token = credentials.credentials
    current_user = get_current_user(token)
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado")
    ok = update_conversation_title(conversation_id, current_user["id"], payload.title)
    if not ok:
        raise HTTPException(status_code=404, detail="Conversa não encontrada")
    return {"ok": True}


@app.get("/api/tasks")
async def list_tasks_endpoint(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    token = credentials.credentials
    current_user = get_current_user(token)
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado")
    tasks = get_user_conversations(current_user["id"], kind="task")
    return {"tasks": tasks}


@app.post("/api/tasks")
async def create_task_endpoint(
    task: ConversationCreate,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    token = credentials.credentials
    current_user = get_current_user(token)
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado")
    title = (task.title or "").strip()
    if not title:
        raise HTTPException(status_code=400, detail="Título vazio")
    session_id = str(uuid.uuid4())
    task_id = create_conversation(current_user["id"], session_id, title, kind="task")
    return {"task_id": task_id, "session_id": session_id, "title": title}


@app.put("/api/tasks/{task_id}/title")
async def rename_task_endpoint(
    task_id: int,
    payload: TitleUpdate,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    token = credentials.credentials
    current_user = get_current_user(token)
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado")
    ok = update_conversation_title(task_id, current_user["id"], payload.title)
    if not ok:
        raise HTTPException(status_code=404, detail="Tarefa não encontrada")
    return {"ok": True}


@app.get("/api/tasks/{task_id}/todos")
async def list_task_todos_endpoint(
    task_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    status: Optional[str] = Query(None),
):
    token = credentials.credentials
    current_user = get_current_user(token)
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado")
    todos = list_task_todos(current_user["id"], task_id, status=status)
    return {"todos": todos}


@app.post("/api/tasks/{task_id}/todos")
async def add_task_todo_endpoint(
    task_id: int,
    payload: TodoCreate,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    token = credentials.credentials
    current_user = get_current_user(token)
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado")
    todo_id = add_task_todo(current_user["id"], task_id, payload.text)
    return {"todo_id": todo_id}


@app.get("/api/tasks/todos")
async def list_global_todos_endpoint(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    token = credentials.credentials
    current_user = get_current_user(token)
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado")
    todos = list_pending_todos(current_user["id"])
    return {"todos": todos}


@app.put("/api/tasks/todos/{todo_id}")
async def update_task_todo_endpoint(
    todo_id: int,
    payload: TodoUpdate,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    token = credentials.credentials
    current_user = get_current_user(token)
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado")
    ok = update_task_todo(
        current_user["id"], todo_id, text=payload.text, status=payload.status
    )
    if not ok:
        raise HTTPException(status_code=404, detail="TODO não encontrado")
    return {"ok": True}


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
    results = search_user_messages(
        current_user["id"], q, limit=int(limit), kind=kind
    )
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
    keys = set([k.strip().lower() for k in (list_user_connector_keys(current_user["id"]) or []) if k])
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


@app.put("/api/connectors/github")
async def put_github_connector_endpoint(
    payload: GitHubConnectInput,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    token = credentials.credentials
    current_user = get_current_user(token)
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado")
    _ensure_connectors_allowed(int(current_user["id"]))
    cleaned = _sanitize_api_key(payload.token)
    ciphertext = _dpapi_protect_text(cleaned)
    upsert_user_connector_secret_ciphertext(current_user["id"], "github", ciphertext)
    return {"ok": True}


@app.delete("/api/connectors/github")
async def delete_github_connector_endpoint(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    token = credentials.credentials
    current_user = get_current_user(token)
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado")
    _ensure_connectors_allowed(int(current_user["id"]))
    ok = delete_user_connector_secret(current_user["id"], "github")
    return {"ok": bool(ok)}


@app.post("/api/connectors/github/test")
async def test_github_connector_endpoint(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    token = credentials.credentials
    current_user = get_current_user(token)
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado")
    _ensure_connectors_allowed(int(current_user["id"]))
    gh_token = _get_user_connector_secret(current_user["id"], "github")
    if not gh_token:
        raise HTTPException(status_code=400, detail="Conector GitHub não configurado.")

    headers = {"Authorization": f"token {gh_token}", "Accept": "application/vnd.github+json"}
    timeout = aiohttp.ClientTimeout(total=8)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.get("https://api.github.com/user", headers=headers) as resp:
            data = await resp.json(content_type=None)
            if resp.status >= 400:
                raise HTTPException(
                    status_code=400,
                    detail=f"Falha ao validar token do GitHub (HTTP {resp.status}).",
                )
            login = (data or {}).get("login")
            return {"ok": True, "user": {"login": login, "id": (data or {}).get("id")}}


def _google_bearer_headers(access_token: str) -> Dict[str, str]:
    return {"Authorization": f"Bearer {access_token}", "Accept": "application/json"}


async def _google_test_get(url: str, access_token: str) -> Dict[str, Any]:
    timeout = aiohttp.ClientTimeout(total=8)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.get(url, headers=_google_bearer_headers(access_token)) as resp:
            data = await resp.json(content_type=None)
            if resp.status >= 400:
                raise HTTPException(
                    status_code=400,
                    detail=f"Falha ao validar credencial (HTTP {resp.status}).",
                )
            return data or {}


@app.put("/api/connectors/google_drive")
async def put_google_drive_connector_endpoint(
    payload: TokenConnectInput,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    token = credentials.credentials
    current_user = get_current_user(token)
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado")
    _ensure_connectors_allowed(int(current_user["id"]))
    cleaned = _sanitize_api_key(payload.token)
    ciphertext = _dpapi_protect_text(cleaned)
    upsert_user_connector_secret_ciphertext(current_user["id"], "google_drive", ciphertext)
    return {"ok": True}


@app.delete("/api/connectors/google_drive")
async def delete_google_drive_connector_endpoint(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    token = credentials.credentials
    current_user = get_current_user(token)
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado")
    _ensure_connectors_allowed(int(current_user["id"]))
    ok = delete_user_connector_secret(current_user["id"], "google_drive")
    return {"ok": bool(ok)}


@app.post("/api/connectors/google_drive/test")
async def test_google_drive_connector_endpoint(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    token = credentials.credentials
    current_user = get_current_user(token)
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado")
    _ensure_connectors_allowed(int(current_user["id"]))
    access_token = _get_user_connector_secret(current_user["id"], "google_drive")
    if not access_token:
        raise HTTPException(status_code=400, detail="Conector Google Drive não configurado.")
    data = await _google_test_get(
        "https://www.googleapis.com/drive/v3/about?fields=user",
        access_token,
    )
    return {"ok": True, "drive": {"user": (data or {}).get("user")}}


@app.put("/api/connectors/google_calendar")
async def put_google_calendar_connector_endpoint(
    payload: TokenConnectInput,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    token = credentials.credentials
    current_user = get_current_user(token)
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado")
    _ensure_connectors_allowed(int(current_user["id"]))
    cleaned = _sanitize_api_key(payload.token)
    ciphertext = _dpapi_protect_text(cleaned)
    upsert_user_connector_secret_ciphertext(current_user["id"], "google_calendar", ciphertext)
    return {"ok": True}


@app.delete("/api/connectors/google_calendar")
async def delete_google_calendar_connector_endpoint(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    token = credentials.credentials
    current_user = get_current_user(token)
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado")
    _ensure_connectors_allowed(int(current_user["id"]))
    ok = delete_user_connector_secret(current_user["id"], "google_calendar")
    return {"ok": bool(ok)}


@app.post("/api/connectors/google_calendar/test")
async def test_google_calendar_connector_endpoint(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    token = credentials.credentials
    current_user = get_current_user(token)
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado")
    _ensure_connectors_allowed(int(current_user["id"]))
    access_token = _get_user_connector_secret(current_user["id"], "google_calendar")
    if not access_token:
        raise HTTPException(status_code=400, detail="Conector Google Calendar não configurado.")
    data = await _google_test_get(
        "https://www.googleapis.com/calendar/v3/users/me/calendarList?maxResults=1",
        access_token,
    )
    items = (data or {}).get("items") if isinstance(data, dict) else None
    first = items[0] if isinstance(items, list) and items else None
    return {"ok": True, "calendar": {"sample": first}}


@app.put("/api/connectors/gmail")
async def put_gmail_connector_endpoint(
    payload: TokenConnectInput,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    token = credentials.credentials
    current_user = get_current_user(token)
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado")
    _ensure_connectors_allowed(int(current_user["id"]))
    cleaned = _sanitize_api_key(payload.token)
    ciphertext = _dpapi_protect_text(cleaned)
    upsert_user_connector_secret_ciphertext(current_user["id"], "gmail", ciphertext)
    return {"ok": True}


@app.delete("/api/connectors/gmail")
async def delete_gmail_connector_endpoint(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    token = credentials.credentials
    current_user = get_current_user(token)
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado")
    _ensure_connectors_allowed(int(current_user["id"]))
    ok = delete_user_connector_secret(current_user["id"], "gmail")
    return {"ok": bool(ok)}


@app.post("/api/connectors/gmail/test")
async def test_gmail_connector_endpoint(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    token = credentials.credentials
    current_user = get_current_user(token)
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado")
    _ensure_connectors_allowed(int(current_user["id"]))
    access_token = _get_user_connector_secret(current_user["id"], "gmail")
    if not access_token:
        raise HTTPException(status_code=400, detail="Conector Gmail não configurado.")
    data = await _google_test_get(
        "https://gmail.googleapis.com/gmail/v1/users/me/profile",
        access_token,
    )
    email = (data or {}).get("emailAddress")
    return {"ok": True, "gmail": {"email": email}}


@app.put("/api/connectors/tera")
async def put_tera_connector_endpoint(
    payload: TokenConnectInput,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    token = credentials.credentials
    current_user = get_current_user(token)
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado")
    _ensure_connectors_allowed(int(current_user["id"]))
    cleaned = _sanitize_api_key(payload.token)
    ciphertext = _dpapi_protect_text(cleaned)
    upsert_user_connector_secret_ciphertext(current_user["id"], "tera", ciphertext)
    return {"ok": True}


@app.delete("/api/connectors/tera")
async def delete_tera_connector_endpoint(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    token = credentials.credentials
    current_user = get_current_user(token)
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado")
    _ensure_connectors_allowed(int(current_user["id"]))
    ok = delete_user_connector_secret(current_user["id"], "tera")
    return {"ok": bool(ok)}


@app.post("/api/connectors/tera/test")
async def test_tera_connector_endpoint(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    token = credentials.credentials
    current_user = get_current_user(token)
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado")
    _ensure_connectors_allowed(int(current_user["id"]))
    value = _get_user_connector_secret(current_user["id"], "tera")
    if not value:
        raise HTTPException(status_code=400, detail="Conector Tera não configurado.")
    return {"ok": True}


@app.put("/api/connectors/telegram")
async def put_telegram_connector_endpoint(
    payload: TokenConnectInput,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    token = credentials.credentials
    current_user = get_current_user(token)
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado")
    _ensure_connectors_allowed(int(current_user["id"]))
    cleaned = _sanitize_api_key(payload.token)
    ciphertext = _dpapi_protect_text(cleaned)
    upsert_user_connector_secret_ciphertext(current_user["id"], "telegram", ciphertext)
    return {"ok": True}


@app.delete("/api/connectors/telegram")
async def delete_telegram_connector_endpoint(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    token = credentials.credentials
    current_user = get_current_user(token)
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado")
    _ensure_connectors_allowed(int(current_user["id"]))
    ok = delete_user_connector_secret(current_user["id"], "telegram")
    return {"ok": bool(ok)}


@app.post("/api/connectors/telegram/test")
async def test_telegram_connector_endpoint(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    token = credentials.credentials
    current_user = get_current_user(token)
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado")
    _ensure_connectors_allowed(int(current_user["id"]))
    tg_token = _get_user_connector_secret(current_user["id"], "telegram")
    if not tg_token:
        raise HTTPException(status_code=400, detail="Conector Telegram não configurado.")
    url = f"https://api.telegram.org/bot{tg_token}/getMe"
    timeout = aiohttp.ClientTimeout(total=8)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.get(url) as resp:
            data = await resp.json(content_type=None)
            if resp.status >= 400 or not (data or {}).get("ok"):
                raise HTTPException(
                    status_code=400,
                    detail=f"Falha ao validar token do Telegram (HTTP {resp.status}).",
                )
            result = (data or {}).get("result") or {}
            return {
                "ok": True,
                "bot": {
                    "id": result.get("id"),
                    "username": result.get("username"),
                    "first_name": result.get("first_name"),
                },
            }


@app.post("/api/connectors/telegram/link-code")
async def create_telegram_link_code_endpoint(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    token = credentials.credentials
    current_user = get_current_user(token)
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado")
    _ensure_connectors_allowed(int(current_user["id"]))
    created = create_telegram_link_code(int(current_user["id"]), ttl_seconds=600)
    return {"code": created.get("code"), "expires_at": created.get("expires_at")}


@app.get("/api/connectors/telegram/links")
async def list_telegram_links_endpoint(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    token = credentials.credentials
    current_user = get_current_user(token)
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado")
    _ensure_connectors_allowed(int(current_user["id"]))
    links = list_telegram_links(int(current_user["id"]))
    return {"links": links}


@app.post("/connectors/telegram/link")
async def mcp_telegram_link_endpoint(payload: TelegramLinkConsumeInput, request: Request):
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
async def mcp_telegram_inbound_endpoint(payload: TelegramInboundInput, request: Request):
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
        raise HTTPException(status_code=403, detail="Conectores desabilitados nas permissões.")

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

    expert = moe_router.select_expert(user_message, force_expert_id=None)
    stored_llm = get_user_llm_settings(int(user_id))
    llm_override = _safe_llm_settings((stored_llm or {}).get("settings") or {})

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
            expert_id=(expert_info or {}).get("id") if isinstance(expert_info, dict) else None,
            provider=(expert_info or {}).get("provider") if isinstance(expert_info, dict) else None,
            model=(expert_info or {}).get("model") if isinstance(expert_info, dict) else None,
            tokens=(expert_info or {}).get("tokens") if isinstance(expert_info, dict) else None,
        )

    return {"ok": True, "reply": persisted_response}


@app.get("/api/automation_client")
async def get_automation_client_settings(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    token = credentials.credentials
    current_user = get_current_user(token)
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado")
    _ensure_connectors_allowed(int(current_user["id"]))
    raw = _get_user_connector_secret_raw(int(current_user["id"]), "automation_client") or ""
    obj: Dict[str, Any] = {}
    try:
        obj = json.loads(raw) if raw else {}
    except Exception:
        obj = {}
    base_url = str(obj.get("base_url") or "").strip()
    has_key = bool(str(obj.get("api_key") or "").strip())
    return {"settings": {"base_url": base_url}, "has_api_key": has_key}


@app.put("/api/automation_client")
async def put_automation_client_settings(
    payload: AutomationClientSettingsInput,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    token = credentials.credentials
    current_user = get_current_user(token)
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado")
    _ensure_connectors_allowed(int(current_user["id"]))
    base_url = str(payload.base_url or "").strip().strip("`\"' ,").rstrip("/")
    api_key = str(payload.api_key or "").strip()
    if not base_url:
        raise HTTPException(status_code=400, detail="base_url obrigatório.")
    if not (base_url.startswith("http://") or base_url.startswith("https://")):
        raise HTTPException(status_code=400, detail="base_url inválido (http/https).")
    existing_key = ""
    raw = _get_user_connector_secret_raw(int(current_user["id"]), "automation_client") or ""
    try:
        obj_prev = json.loads(raw) if raw else {}
    except Exception:
        obj_prev = {}
    existing_key = str((obj_prev or {}).get("api_key") or "").strip()
    if not api_key:
        api_key = existing_key
    if not api_key:
        raise HTTPException(status_code=400, detail="api_key obrigatório.")
    obj = {"base_url": base_url, "api_key": api_key}
    ciphertext = _dpapi_protect_text(json.dumps(obj, ensure_ascii=False))
    upsert_user_connector_secret_ciphertext(
        int(current_user["id"]), "automation_client", ciphertext
    )
    return {"ok": True, "settings": {"base_url": base_url}, "has_api_key": True}


@app.delete("/api/automation_client")
async def delete_automation_client_settings(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    token = credentials.credentials
    current_user = get_current_user(token)
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado")
    _ensure_connectors_allowed(int(current_user["id"]))
    ok = delete_user_connector_secret(int(current_user["id"]), "automation_client")
    return {"deleted": bool(ok), "has_api_key": False}


@app.post("/api/automation_client/test")
async def test_automation_client_settings(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    token = credentials.credentials
    current_user = get_current_user(token)
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado")
    _ensure_connectors_allowed(int(current_user["id"]))
    raw = _get_user_connector_secret_raw(int(current_user["id"]), "automation_client") or ""
    try:
        obj = json.loads(raw) if raw else {}
    except Exception:
        obj = {}
    base_url = str((obj or {}).get("base_url") or "").strip().rstrip("/")
    api_key = str((obj or {}).get("api_key") or "").strip()
    if not base_url or not api_key:
        raise HTTPException(status_code=400, detail="Cliente externo não configurado.")
    timeout = aiohttp.ClientTimeout(total=4)
    headers = {"Authorization": f"Bearer {api_key}"}
    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(f"{base_url}/health", headers=headers) as resp:
                return {"ok": resp.status < 500, "status": resp.status}
    except Exception:
        return {"ok": False, "status": None}


@app.get("/api/conversations/{conversation_id}")
async def get_conversation(
    conversation_id: int, credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Obtém mensagens de uma conversa"""
    token = credentials.credentials
    current_user = get_current_user(token)

    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado")

    messages = get_conversation_messages(conversation_id)
    return {"messages": messages}


@app.delete("/api/conversations/{conversation_id}")
async def delete_conversation_endpoint(
    conversation_id: int, credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Deleta uma conversa"""
    token = credentials.credentials
    current_user = get_current_user(token)

    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado")

    success = delete_conversation(conversation_id, current_user["id"])

    if not success:
        raise HTTPException(status_code=404, detail="Conversa não encontrada")

    return {"message": "Conversa deletada com sucesso"}


@app.get("/api/settings/llm")
async def get_llm_settings_endpoint(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    token = credentials.credentials
    current_user = get_current_user(token)
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado")
    stored = get_user_llm_settings(current_user["id"])
    settings = _safe_llm_settings((stored or {}).get("settings") or {})
    has_key = bool(get_user_api_key_ciphertext(current_user["id"]))
    return {
        "settings": settings,
        "has_api_key": has_key,
        "updated_at": (stored or {}).get("updated_at"),
    }


@app.put("/api/settings/llm")
async def put_llm_settings_endpoint(
    payload: LlmSettingsInput,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    token = credentials.credentials
    current_user = get_current_user(token)
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado")
    settings = _safe_llm_settings(payload.model_dump())
    upsert_user_llm_settings(current_user["id"], settings)
    if payload.api_key and payload.api_key.strip():
        cleaned = _sanitize_api_key(payload.api_key)
        ciphertext = _dpapi_protect_text(cleaned)
        upsert_user_api_key_ciphertext(current_user["id"], ciphertext)
    return {
        "settings": settings,
        "has_api_key": bool(get_user_api_key_ciphertext(current_user["id"])),
    }


@app.delete("/api/settings/llm/api_key")
async def delete_llm_api_key_endpoint(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    token = credentials.credentials
    current_user = get_current_user(token)
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado")
    deleted = delete_user_api_key(current_user["id"])
    return {
        "deleted": bool(deleted),
        "has_api_key": bool(get_user_api_key_ciphertext(current_user["id"])),
    }


@app.get("/api/settings/security")
async def get_security_settings_endpoint(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    token = credentials.credentials
    current_user = get_current_user(token)
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado")
    effective = _get_effective_security_settings(int(current_user["id"]))
    settings = {k: effective.get(k) for k in SECURITY_SETTINGS_DEFAULT.keys()}
    return {
        "settings": settings,
        "updated_at": effective.get("updated_at"),
    }


@app.put("/api/settings/security")
async def put_security_settings_endpoint(
    payload: SecuritySettingsInput,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    token = credentials.credentials
    current_user = get_current_user(token)
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado")
    prev = _get_effective_security_settings(int(current_user["id"]))
    merged = {k: prev.get(k) for k in SECURITY_SETTINGS_DEFAULT.keys()}
    for k, v in (payload.model_dump() or {}).items():
        if k in SECURITY_SETTINGS_DEFAULT and v is not None:
            merged[k] = bool(v)
    settings = _safe_security_settings(merged)
    upsert_user_security_settings(int(current_user["id"]), settings)
    return {"settings": settings}


@app.get("/api/settings/language")
async def get_language_settings_endpoint(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    token = credentials.credentials
    current_user = get_current_user(token)
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado")
    stored = get_user_system_profile(current_user["id"]) or {}
    data = stored.get("data") if isinstance(stored.get("data"), dict) else {}
    lang = str((data or {}).get("lang") or "pt").strip().lower()
    if lang not in ("pt", "en", "es", "ar", "zh"):
        lang = "pt"
    return {"lang": lang}


@app.put("/api/settings/language")
async def put_language_settings_endpoint(
    payload: LanguageSettingsInput,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    token = credentials.credentials
    current_user = get_current_user(token)
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado")
    lang = str(payload.lang or "").strip().lower()
    if lang not in ("pt", "en", "es", "ar", "zh"):
        raise HTTPException(status_code=400, detail="Idioma inválido.")
    update_user_system_profile_data(current_user["id"], {"lang": lang})
    return {"ok": True, "lang": lang}


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
        user_msg_content, asst_msg_content = pair[0].get("content", ""), pair[1].get("content", "")
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
                append_soul_event(user["id"], "feedback_positive",
                                  f"Useful answer (👍): {summary}")
                # Boost salience of the newly written event
                import sqlite3 as _sq_fb
                with _sq_fb.connect(str(get_db_path())) as _c_fb:
                    _c_fb.execute("""
                        UPDATE user_soul_events
                        SET salience=0.95, confidence=0.9,
                            last_used_at=CURRENT_TIMESTAMP
                        WHERE user_id=? AND source='feedback_positive'
                        ORDER BY id DESC LIMIT 1
                    """, (user["id"],))
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
                            (user["id"], qh)
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
    ids = create_plan_tasks(user["id"], payload.conversation_id, payload.tasks)
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
) -> None:
    """Background coroutine — must not raise; all errors are logged."""
    log: List[Dict[str, Any]] = []

    def _log(task_id, status, msg):
        log.append({"task_id": task_id, "status": status, "msg": msg})
        try:
            update_orchestration_run(run_id, "running", log)
        except Exception:
            pass

    try:
        tasks = get_plan_tasks(parent_conversation_id)
        pending = [t for t in tasks if t.get("status") in ("pending", "active")]

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
                    (parent_conversation_id,)
                ).fetchone()
                if _conv_row and _conv_row[0]:
                    _project_id = int(_conv_row[0])
                    _proj_row = _c_orch.execute(
                        "SELECT name, context_md FROM projects WHERE id=?",
                        (_project_id,)
                    ).fetchone()
                    if _proj_row and _proj_row[1]:
                        _proj_ctx = (
                            f"Project: {_proj_row[0]}\n"
                            f"{_proj_row[1].strip()}"
                        )
        except Exception:
            pass

        # User skills for prompt resolution
        user_skills = get_user_skills(user_id) or []
        skill_map = {s.get("id", ""): s for s in user_skills}

        for task in pending:
            task_id = task["id"]
            title = task.get("title", "")
            skill_id = task.get("skill_id") or ""

            _log(task_id, "active", f"Starting: {title}")

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
            expert = moe_router.select_expert(title, force_expert_id=skill_id if skill_id else None)

            # 4. Build system context
            user_ctx_parts = []
            if _proj_ctx:
                user_ctx_parts.append(
                    f"--- Shared project context ---\n{_proj_ctx}\n--- End project context ---"
                )
            if skill_prompt:
                user_ctx_parts.append(
                    f"--- Active skill: {skill_id or title} ---\n{skill_prompt}\n--- End skill ---"
                )
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
                sub_conv_id = create_conversation(
                    user_id,
                    f"orch-{run_id}-task-{task_id}",
                    f"[Auto] {title[:60]}",
                    kind="task",
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

            # 9. Save assistant response
            if full_response.strip():
                try:
                    save_message(
                        sub_conv_id, "assistant", full_response,
                        expert_id=expert.get("id")
                    )
                except Exception:
                    pass

                # Write a memory entry for the completed task
                if ENABLE_MEMORY_WRITE:
                    try:
                        append_soul_event(
                            user_id, "orchestration",
                            f"Completed task '{title}': {full_response[:200].strip()}"
                        )
                    except Exception:
                        pass

            # 10. Mark task done
            update_plan_task_status(task_id, "done", conversation_id=sub_conv_id)
            _log(task_id, "done", f"Completed: {title} ({len(full_response)} chars)")

        update_orchestration_run(run_id, "completed", log)

    except Exception as e:
        try:
            log.append({"task_id": None, "status": "fatal", "msg": str(e)})
            update_orchestration_run(run_id, "failed", log)
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
    api_key = _get_user_api_key(user["id"])
    if api_key:
        llm_override["api_key"] = api_key

    run_id = create_orchestration_run(user["id"], conversation_id)

    # Run in background so the HTTP response returns immediately
    background_tasks.add_task(
        _run_orchestration,
        run_id, user["id"], conversation_id, llm_override,
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
    context_md: str


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
    pid = create_project(user["id"], name, payload.context_md or "")
    return {"ok": True, "project_id": pid}


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
    update_project_context(project_id, user["id"], payload.context_md or "")
    return {"ok": True}


class ConversationProjectInput(BaseModel):
    project_id: Optional[int] = None


@app.put("/api/conversations/{conversation_id}/project")
async def set_conversation_project_endpoint(
    conversation_id: int,
    payload: ConversationProjectInput,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    user = get_current_user(credentials.credentials)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    set_conversation_project(conversation_id, payload.project_id)
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


# ── Onboarding ────────────────────────────────────────────────────────────────

@app.get("/api/onboarding/status")
async def get_onboarding_status(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """Returns whether the user has completed onboarding."""
    user = get_current_user(credentials.credentials)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    # Onboarding is considered complete when user has at least one conversation
    with __import__("sqlite3").connect(str(get_db_path())) as conn:
        row = conn.execute(
            "SELECT COUNT(*) FROM conversations WHERE user_id=?", (user["id"],)
        ).fetchone()
        count = row[0] if row else 0
    completed = count > 0
    return {"completed": completed, "conversation_count": count}


# WebSocket com autenticação
@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """Endpoint WebSocket com autenticação"""
    token = websocket.query_params.get("token") or _extract_bearer_token_from_headers(
        dict(websocket.headers)
    )
    if not token:
        await websocket.close(code=4001, reason="Token não fornecido")
        return

    # Verificar usuário
    current_user = await get_current_user_ws(websocket, token)
    if not current_user:
        return

    # Aceitar conexão
    await websocket.accept()
    active_connections[session_id] = websocket

    try:
        # Obter ou criar conversa
        conversation = get_conversation_by_session_for_user(current_user["id"], session_id)
        conversation_id = conversation["id"] if conversation else None
        conversation_kind = (conversation.get("kind") if conversation else "conversation") or "conversation"

        # Enviar histórico se existir
        if conversation_id:
            messages = get_conversation_messages(conversation_id)
            for message in messages:
                await websocket.send_json({"type": "history", "message": message})

        # Loop de mensagens
        while True:
            try:
                # Receber mensagem do cliente
                data = await websocket.receive_json()

                if data.get("type") == "chat":
                    user_message = data.get("content", "")
                    if not (user_message or "").strip():
                        continue
                    internal_prompt = str(data.get("internal_prompt") or "").strip()
                    sec = _get_effective_security_settings(int(current_user["id"]))

                    # Skill active — pull its system prompt from user's skill list
                    ws_skill_id = (data.get("skill_id") or "").strip()
                    ws_skill_web_search = bool(data.get("skill_web_search"))
                    _active_skill_prompt: str = ""
                    if ws_skill_id:
                        try:
                            _user_skills = get_user_skills(current_user["id"]) or []
                            _sk = next((s for s in _user_skills if str(s.get("id") or "") == ws_skill_id), None)
                            if _sk:
                                _sk_content = _sk.get("content") or {}
                                if isinstance(_sk_content, dict):
                                    _active_skill_prompt = str(_sk_content.get("prompt") or "").strip()
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
                    save_message(conversation_id, "user", user_message)

                    todo_items = _todo_items_from_user_message(user_message)
                    if todo_items:
                        if conversation_kind == "task":
                            for t in todo_items:
                                add_task_todo(current_user["id"], conversation_id, t)
                            await websocket.send_json(
                                {
                                    "type": "status",
                                    "content": f"TODO registrado ({len(todo_items)})",
                                }
                            )
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
                                add_task_todo(current_user["id"], int(inbox_id), t)
                            await websocket.send_json(
                                {
                                    "type": "status",
                                    "content": f"TODO enviado para Inbox ({len(todo_items)})",
                                }
                            )

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
                        continue

                    recent_messages = get_conversation_messages(conversation_id)
                    recent_context = _format_recent_chat_context(
                        recent_messages, limit=8
                    )

                    # Enviar status de processamento
                    await websocket.send_json(
                        {"type": "status", "content": "Processando mensagem..."}
                    )

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
                        continue

                    if (
                        ENABLE_SYSTEM_PROFILE
                        and sec.get("allow_system_profile")
                        and _is_system_profile_detail_query(
                            user_message
                        )
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
                            continue

                    # Roteamento e geração de resposta
                    # MoE selection — honour user override if provided
                    _force_expert = (data.get("force_expert_id") or "").strip() or None
                    expert = moe_router.select_expert(user_message, force_expert_id=_force_expert)
                    # Adjust confidence using per-user historical expert ratings
                    try:
                        _expert_ratings = get_expert_rating_summary(int(current_user["id"]))
                        if expert and _expert_ratings:
                            _eid = expert.get("id", "")
                            _approval = _expert_ratings.get(_eid)
                            if _approval is not None and expert.get("confidence") is not None:
                                # Blend keyword confidence with historical approval rate
                                expert["confidence"] = (
                                    0.7 * float(expert["confidence"])
                                    + 0.3 * float(_approval)
                                )
                                if _approval < 0.3:
                                    # Simple: keep original but log the low approval
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
                            snap = (get_consolidated_memory_snapshot(current_user["id"]) or "").strip()
                            if snap:
                                snap = snap[: int(MEMORY_SNAPSHOT_MAX_CHARS)].rstrip()
                                block = f"Memória consolidada (uso interno):\n{snap}"
                                user_context = f"{block}\n\n{user_context}".strip() if user_context else block
                        except Exception:
                            pass

                    # ── Project shared context ────────────────────────────
                    _proj_ctx = ""
                    try:
                        if sec.get("sandbox"):
                            raise Exception("sandbox")
                        import sqlite3 as _sq2
                        with _sq2.connect(str(__import__("pathlib").Path(
                            __import__("os").environ.get("OPENSLAP_DB_PATH", "data/auth.db")
                        ))) as _c2:
                            _conv_row = _c2.execute(
                                "SELECT project_id FROM conversations WHERE id=?",
                                (conversation_id,)
                            ).fetchone()
                            if _conv_row and _conv_row[0]:
                                _proj_row = _c2.execute(
                                    "SELECT name, context_md FROM projects WHERE id=?",
                                    (_conv_row[0],)
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

                    # ── Active connector context ───────────────────────────────
                    _conn_ctx_parts: List[str] = []
                    try:
                        if (not sec.get("allow_connectors")) or sec.get("sandbox"):
                            raise Exception("connectors disabled")
                        _gh_token = _get_user_connector_secret(current_user["id"], "github")
                        if _gh_token and any(
                            k in user_message.lower()
                            for k in ("issue", "pr", "pull request", "repo", "github",
                                      "commit", "branch", "code review")
                        ):
                            import aiohttp as _aio
                            async with _aio.ClientSession(
                                timeout=_aio.ClientTimeout(total=5)
                            ) as _s:
                                _gh_h = {"Authorization": f"token {_gh_token}",
                                         "Accept": "application/vnd.github+json"}
                                # User repos (top 5)
                                async with _s.get(
                                    "https://api.github.com/user/repos"
                                    "?sort=updated&per_page=5",
                                    headers=_gh_h
                                ) as _rr:
                                    if _rr.status == 200:
                                        _repos = await _rr.json()
                                        _names = [r["full_name"] for r in _repos if r.get("full_name")]
                                        if _names:
                                            _conn_ctx_parts.append(
                                                f"GitHub — recent repos: {', '.join(_names)}"
                                            )
                                # Open issues (top 5)
                                async with _s.get(
                                    "https://api.github.com/issues"
                                    "?filter=assigned&state=open&per_page=5",
                                    headers=_gh_h
                                ) as _ir:
                                    if _ir.status == 200:
                                        _issues = await _ir.json()
                                        _ititles = [
                                            f"#{i.get('number')} {i.get('title', '')[:60]}"
                                            for i in _issues if isinstance(i, dict)
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
                        _cal_token = _get_user_connector_secret(current_user["id"], "google_calendar")
                        if _cal_token and any(
                            k in user_message.lower()
                            for k in ("meeting", "calendar", "agenda", "event",
                                      "schedule", "appointment", "reunião", "hoje")
                        ):
                            import aiohttp as _aio2
                            async with _aio2.ClientSession(
                                timeout=_aio2.ClientTimeout(total=5)
                            ) as _s2:
                                import datetime as _dt
                                _now = _dt.datetime.utcnow().isoformat() + "Z"
                                _end = (_dt.datetime.utcnow() + _dt.timedelta(days=3)).isoformat() + "Z"
                                async with _s2.get(
                                    "https://www.googleapis.com/calendar/v3/calendars/primary/events"
                                    f"?timeMin={_now}&timeMax={_end}&maxResults=5"
                                    "&orderBy=startTime&singleEvents=true",
                                    headers={"Authorization": f"Bearer {_cal_token}"}
                                ) as _cr:
                                    if _cr.status == 200:
                                        _cdata = await _cr.json()
                                        _evts = _cdata.get("items") or []
                                        _enames = [
                                            e.get("summary", "(no title)")[:50]
                                            for e in _evts if isinstance(e, dict)
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
                        _gmail_token = _get_user_connector_secret(current_user["id"], "gmail")
                        if _gmail_token and any(
                            k in user_message.lower()
                            for k in ("email", "mail", "inbox", "gmail", "mensagem", "e-mail",
                                      "thread", "reply", "responder", "newsletter")
                        ):
                            import aiohttp as _aio3
                            async with _aio3.ClientSession(
                                timeout=_aio3.ClientTimeout(total=5)
                            ) as _s3:
                                # Search recent unread emails
                                async with _s3.get(
                                    "https://gmail.googleapis.com/gmail/v1/users/me/messages"
                                    "?q=is:unread&maxResults=5",
                                    headers={"Authorization": f"Bearer {_gmail_token}"}
                                ) as _gmr:
                                    if _gmr.status == 200:
                                        _gmdata = await _gmr.json()
                                        _msg_ids = [
                                            m["id"] for m in (_gmdata.get("messages") or [])[:5]
                                        ]
                                        _subjects: List[str] = []
                                        for _mid in _msg_ids[:3]:
                                            async with _s3.get(
                                                f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{_mid}"
                                                "?format=metadata&metadataHeaders=Subject,From",
                                                headers={"Authorization": f"Bearer {_gmail_token}"}
                                            ) as _mdr:
                                                if _mdr.status == 200:
                                                    _md = await _mdr.json()
                                                    _hdrs = {
                                                        h["name"]: h["value"]
                                                        for h in (_md.get("payload", {}).get("headers") or [])
                                                    }
                                                    _subj = _hdrs.get("Subject", "(no subject)")[:60]
                                                    _frm = _hdrs.get("From", "")[:40]
                                                    _subjects.append(f'"{_subj}" from {_frm}')
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
                        _drive_token = _get_user_connector_secret(current_user["id"], "google_drive")
                        if _drive_token and any(
                            k in user_message.lower()
                            for k in ("file", "document", "doc", "sheet", "spreadsheet",
                                      "drive", "arquivo", "planilha", "relatório", "report",
                                      "slide", "presentation", "folder", "pasta")
                        ):
                            import aiohttp as _aio4
                            async with _aio4.ClientSession(
                                timeout=_aio4.ClientTimeout(total=5)
                            ) as _s4:
                                # Extract possible filename hint from message
                                _query_words = [
                                    w for w in user_message.split()
                                    if len(w) > 3 and w[0].isupper()
                                ]
                                _drive_q = " ".join(_query_words[:3]) if _query_words else ""
                                _drive_search = (
                                    f"name contains '{_drive_q}' and " if _drive_q else ""
                                ) + "trashed=false"
                                async with _s4.get(
                                    "https://www.googleapis.com/drive/v3/files"
                                    f"?q={_drive_search}&pageSize=5"
                                    "&fields=files(id,name,mimeType,modifiedTime)",
                                    headers={"Authorization": f"Bearer {_drive_token}"}
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
                                            for f in _files if f.get("name")
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

                    stored_llm = get_user_llm_settings(current_user["id"])
                    llm_override = _safe_llm_settings(
                        (stored_llm or {}).get("settings") or {}
                    )
                    api_key = _get_user_api_key(current_user["id"])
                    if api_key:
                        llm_override["api_key"] = api_key

                    if ENABLE_CAC and not is_file_request:
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
                    if ENABLE_RAG_SQLITE and not is_file_request and not sec.get("sandbox"):
                        rag_items = search_user_memory(
                            current_user["id"], user_message, limit=6
                        )
                        rag_context = _format_rag_memory(rag_items)
                    if rag_context:
                        user_message_for_llm = f"{user_message_for_llm}\n\nMemória relevante (RAG local):\n{rag_context}"

                    # Inject active skill system prompt into context
                    if internal_prompt:
                        _internal_header = (
                            f"--- Instruções internas ---\n{internal_prompt}\n--- Fim instruções ---"
                        )
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
                    # Web search rules:
                    # - Skill with web_search=true: always attempts (bypasses global flag)
                    # - Keyword heuristic: only when ENABLE_WEB_RETRIEVAL=1
                    _wants_web_skill = ws_skill_web_search
                    _wants_web_heuristic = ENABLE_WEB_RETRIEVAL and _needs_web_retrieval(user_message)
                    _wants_web = bool(sec.get("allow_web_retrieval")) and (
                        _wants_web_skill or _wants_web_heuristic
                    )
                    if _wants_web:
                        await websocket.send_json(
                            {"type": "status", "content": "Buscando na web..."}
                        )
                        web_context = await _web_retrieve_context(user_message)
                        if web_context:
                            await websocket.send_json(
                                {
                                    "type": "status",
                                    "content": "Analisando resultados da web...",
                                }
                            )
                    if web_context:
                        user_message_for_llm = f"{user_message_for_llm}\n\nContexto da web (pode estar incompleto):\n{web_context}"

                    async for chunk in llm_manager.stream_generate(
                        user_message_for_llm,
                        expert,
                        user_context=user_context,
                        llm_override=llm_override,
                    ):
                        if isinstance(chunk, str):
                            full_response += chunk
                            if not is_file_request:
                                await websocket.send_json(
                                    {"type": "chunk", "content": chunk}
                                )
                        else:
                            expert_info = chunk

                    files_bundle = (
                        _extract_files_json(full_response) if is_file_request else None
                    )
                    if is_file_request:
                        if not sec.get("allow_file_write"):
                            full_response = (
                                "⚠️ Escrita de arquivos está desabilitada nas permissões desta conta."
                            )
                        else:
                            if (
                                files_bundle
                                and base_path_for_write
                                and not str(files_bundle.get("base_path") or "").strip()
                            ):
                                files_bundle["base_path"] = base_path_for_write
                            if not files_bundle and base_path_for_write:
                                files_bundle = _default_landing_bundle(base_path_for_write)
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
                    elif ENABLE_CAC:
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
                                    int(r.get("id")) for r in rag_items
                                    if r.get("id") is not None
                                ]
                                reinforce_memory_usage(int(current_user["id"]), _used_ids)
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
                                        _skill = _parts[1].strip() if len(_parts) > 1 else None
                                        if _title:
                                            _plan_tasks_detected.append(
                                                {"title": _title, "skill_id": _skill or None}
                                            )
                                _plan_detected = bool(_plan_tasks_detected)
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
                                (conversation_id,)
                            ).fetchone()
                            if row:
                                _last_msg_id = row[0]
                    except Exception:
                        pass

                    await websocket.send_json(
                        {
                            "type": "done",
                            "content": full_response,
                            "expert": expert,
                            "message_id": _last_msg_id,
                            "selection_reason": (expert or {}).get("selection_reason", ""),
                            "matched_keywords": (expert or {}).get("matched_keywords", []),
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
                    )

            except WebSocketDisconnect:
                break
            except Exception as e:
                print(f"[main] Erro no WebSocket: {e}")
                await websocket.send_json(
                    {"type": "error", "content": f"Erro: {str(e)}"}
                )
                break

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


@app.get("/api/experts")
async def get_experts(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Lista de especialistas"""
    token = credentials.credentials
    current_user = get_current_user(token)
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado")
    return {"experts": moe_router.get_experts()}


@app.get("/api/providers")
async def get_providers(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Status dos providers"""
    token = credentials.credentials
    current_user = get_current_user(token)
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado")
    return {"providers": await llm_manager.get_provider_status()}


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
    api_key = _get_user_api_key(user_id) or ""
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
                    "Chave protegida no servidor local"
                    if has_api_key
                    else "Cadastre uma chave nas Configurações de LLM"
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
            media_path = (MEDIA_DIR / full_path[len("media/"):]).resolve()
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
            return JSONResponse({"detail": "Frontend não buildado. Rode: npm run build"}, status_code=503)
        return FileResponse(str(index))


# Inicialização
if __name__ == "__main__":
    import uvicorn

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

    uvicorn.run(
        "main_auth:app",
        host=os.getenv("OPENSLAP_HOST", "127.0.0.1"),
        port=int(os.getenv("OPENSLAP_PORT", "5150")),
        reload=True,
    )
