"""
Backend com Autenticação e Persistência - Versão Refatorada
"""

import os
import sys
import asyncio
import logging
from pathlib import Path
from dotenv import load_dotenv

# FastAPI e middleware
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles

# Importações locais refatoradas
from .config.settings import settings
from .middleware.auth import AuthRequiredMiddleware
from .models.schemas import (
    ChatMessage,
    FrictionReportInput,
    CommandExecuteInput,
    CommandPlanInput,
)
from .utils.auth_helpers import PUBLIC_PATHS, PUBLIC_PATH_PREFIXES
from .utils.system import generate_system_map_ascii
from .deps import BASE_DIR, DEFAULT_DELIVERIES_ROOT

# Configuração inicial
BASE_DIR = Path(__file__).resolve().parents[1]
load_dotenv(dotenv_path=BASE_DIR / ".env", override=False)
logger = logging.getLogger(__name__)

# Configuração do loop de eventos para Windows
if sys.platform == "win32":
    try:
        _pol = getattr(asyncio, "WindowsProactorEventLoopPolicy", None)
        if _pol:
            asyncio.set_event_loop_policy(_pol())
    except Exception:
        pass

# Constantes de configuração
DEFAULT_DELIVERIES_ROOT = os.path.join(os.path.expanduser("~"), "OpenSlap", "Entregas")
MEDIA_DIR = BASE_DIR / "media" / "workspace"
DEFAULT_WORKDIR = MEDIA_DIR

# Garante que o diretório de trabalho exista
try:
    DEFAULT_WORKDIR.mkdir(parents=True, exist_ok=True)
except Exception as _workdir_err:
    try:
        DEFAULT_WORKDIR = (MEDIA_DIR / "workspace").resolve()
        DEFAULT_WORKDIR.mkdir(parents=True, True)
    except Exception:
        DEFAULT_WORKDIR = MEDIA_DIR

# Criação da aplicação FastAPI
app = FastAPI(
    title="OpenSlap Backend",
    description="Backend com autenticação e persistência",
    version="2.1.1"
)

# Adiciona middleware de autenticação
app.add_middleware(AuthRequiredMiddleware)

# Configuração CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

# Servir arquivos estáticos
if MEDIA_DIR.exists():
    app.mount("/media", StaticFiles(directory=str(MEDIA_DIR)), name="media")

# Importação e registro de rotas
from .routes import (
    auth_routes,
    conversations_tasks,
    commands_routes,
    connectors_routes,
    delivery_routes,
    feedback_plan_routes,
    forge_routes,
    friction_routes,
    health_routes,
    media_routes,
    memory_connectors_routes,
    onboarding_routes,
    padxml_routes,
    profile_routes,
    project_routes,
    search_skills_routes,
    settings_routes,
    system_routes,
)

# Registra as rotas na aplicação
app.include_router(auth_routes.router, prefix="/api/auth", tags=["auth"])
app.include_router(conversations_tasks.router, prefix="/api/conversations", tags=["conversations"])
app.include_router(commands_routes.router, prefix="/api/commands", tags=["commands"])
app.include_router(connectors_routes.router, prefix="/api/connectors", tags=["connectors"])
app.include_router(delivery_routes.router, prefix="/api/delivery", tags=["delivery"])
app.include_router(feedback_plan_routes.router, prefix="/api/feedback", tags=["feedback"])
app.include_router(forge_routes.router, prefix="/api/forge", tags=["forge"])
app.include_router(friction_routes.router, prefix="/api/friction", tags=["friction"])
app.include_router(health_routes.router, prefix="/api/health", tags=["health"])
app.include_router(media_routes.router, prefix="/api/media", tags=["media"])
app.include_router(memory_connectors_routes.router, prefix="/api/memory", tags=["memory"])
app.include_router(onboarding_routes.router, prefix="/api/onboarding", tags=["onboarding"])
app.include_router(padxml_routes.router, prefix="/api/padxml", tags=["padxml"])
app.include_router(profile_routes.router, prefix="/api/profile", tags=["profile"])
app.include_router(project_routes.router, prefix="/api/projects", tags=["projects"])
app.include_router(search_skills_routes.router, prefix="/api/skills", tags=["skills"])
app.include_router(settings_routes.router, prefix="/api/settings", tags=["settings"])
app.include_router(system_routes.router, prefix="/api/system", tags=["system"])

# Funções de sistema
def generate_system_map():
    """Gera mapa do sistema em ASCII"""
    return generate_system_map_ascii(
        base_dir=str(BASE_DIR),
        target_dirs=["frontend/src", "backend"]
    )

# Variáveis globais para compatibilidade
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

# Função principal para compatibilidade
def create_app():
    """Cria e retorna a aplicação FastAPI configurada"""
    return app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
