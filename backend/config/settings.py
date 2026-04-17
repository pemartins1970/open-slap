"""
Configurações da Aplicação
"""

import os
from typing import List, Optional
from pathlib import Path

from ..utils.env import (
    env_flag as _env_flag,
    env_int as _env_int,
    env_float as _env_float,
    env_list as _env_list,
)


class Settings:
    """Configurações centralizadas da aplicação"""
    
    def __init__(self):
        # Web Retrieval
        self.enable_web_retrieval = _env_flag(
            os.getenv("OPENSLAP_WEB_RETRIEVAL"), False
        )
        self.web_retrieval_timeout_s = _env_float(
            os.getenv("OPENSLAP_WEB_RETRIEVAL_TIMEOUT_S"), 6.0
        )
        
        # URL Fetch
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
        
        # Cache
        self.enable_cac = _env_flag(os.getenv("OPENSLAP_CAC"), True)
        self.cache_max_age_hours = _env_int(os.getenv("OPENSLAP_CAC_MAX_AGE_HOURS"), 24)
        
        # RAG
        self.enable_rag_sqlite = _env_flag(os.getenv("OPENSLAP_RAG_SQLITE"), True)
        
        # System Profile
        self.enable_system_profile = _env_flag(
            os.getenv("OPENSLAP_SYSTEM_PROFILE"), True
        )
        self.attach_system_profile = _env_flag(
            os.getenv("OPENSLAP_ATTACH_SYSTEM_PROFILE"), True
        )
        self.system_profile_max_chars = _env_int(
            os.getenv("OPENSLAP_SYSTEM_PROFILE_MAX_CHARS"), 24000
        )
        
        # OS Commands
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
        
        # External Software
        self.enable_external_software = _env_flag(
            os.getenv("OPENSLAP_EXTERNAL_SOFTWARE"), True
        )
        
        # Agno
        self.enable_agno_poc = _env_flag(os.getenv("OPENSLAP_USE_AGNO"), False)
        self.agno_db_file = str(os.getenv("OPENSLAP_AGNO_DB_FILE") or "").strip()
        
        # CORS
        self.cors_origins = _env_list(os.getenv("OPENSLAP_CORS_ORIGINS")) or [
            "http://localhost",
            "http://localhost:5173",
            "http://localhost:3000",
            "http://127.0.0.1:5173",
            "http://127.0.0.1:3000",
            "http://openslap.test",
        ]


# Instância global de configurações
settings = Settings()
