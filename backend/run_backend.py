#!/usr/bin/env python3
"""
Script para iniciar o backend do Open Slap! v2.1.1
Resolução de imports relativos e configuração de ambiente
"""

import sys
import os

# Adicionar diretório src ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Importar e executar o main_auth
if __name__ == "__main__":
    from backend.main_auth import app
    import uvicorn
    
    print("?? Iniciando Agêntico Backend com Autenticação")
    print("?? MCP Registry System integrado")
    print("?? Endpoints disponíveis:")
    print("   POST /auth/register - Registrar usuário")
    print("   POST /auth/login - Fazer login")
    print("   GET  /auth/me - Obter usuário atual")
    print("   GET  /api/conversations - Listar conversas")
    print("   POST /api/conversations - Criar conversa")
    print("   GET  /api/conversations/{id} - Obter mensagens")
    print("   DELETE /api/conversations/{id} - Deletar conversa")
    print("   GET  /api/mcps - Listar MCPs instalados")
    print("   POST /api/mcps/install - Instalar MCP")
    print("   PATCH /api/mcps/{id}/toggle - Ativar/desativar MCP")
    print("   WS   /ws/{session_id}?token={jwt} - Chat com streaming")
    
    reload_env = (os.getenv("OPENSLAP_RELOAD") or "").strip().lower()
    should_reload = reload_env in {"1", "true", "yes", "on"}
    
    uvicorn.run(
        app,
        host=os.getenv("OPENSLAP_HOST", "127.0.0.1"),
        port=int(os.getenv("OPENSLAP_PORT", "5150")),
        reload=should_reload,
        reload_dirs=[os.path.dirname(__file__)] if should_reload else None,
        reload_excludes=["data/*", "*.db", "*.sqlite", "**/*.db", "**/*.sqlite"] if should_reload else None,
    )
