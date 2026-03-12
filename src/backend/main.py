"""
🚀 MAIN AUTH - Backend com Autenticação e Persistência
Implementação completa segundo WINDSURF_AGENT.md
"""

import os
import json
import asyncio
import uuid
from datetime import datetime
from typing import Dict, Any, Optional

from pathlib import Path
from dotenv import load_dotenv

from fastapi import FastAPI, HTTPException, status, Depends, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

BASE_DIR = Path(__file__).resolve().parents[1]
load_dotenv(dotenv_path=BASE_DIR / ".env", override=False)

# Importar módulos locais
from .auth import (
    create_user, authenticate_user, create_access_token, 
    verify_token, get_current_user
)
from .db import (
    create_conversation, get_user_conversations, get_conversation_messages,
    save_message, delete_conversation, get_conversation_by_session
)
from .llm_manager_simple import LLMManager
from .moe_router_simple import MoERouter

# Configurações
app = FastAPI(title="Agêntico Backend", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Segurança
security = HTTPBearer()

# Componentes
llm_manager = LLMManager()
moe_router = MoERouter()

# Armazenamento de sessões WebSocket
active_connections: Dict[str, WebSocket] = {}

# Modelos Pydantic
class UserRegister(BaseModel):
    email: str
    password: str

class UserLogin(BaseModel):
    email: str
    password: str

class ChatMessage(BaseModel):
    content: str

class ConversationCreate(BaseModel):
    title: str

# Middleware de autenticação
async def get_current_user_ws(websocket: WebSocket, token: str) -> Optional[Dict[str, Any]]:
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
            "user": {
                "id": created_user["id"],
                "email": created_user["email"]
            }
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao criar usuário: {str(e)}"
        )

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
        "user": authenticated_user
    }

@app.get("/auth/me")
async def get_me(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Obtém informações do usuário atual"""
    token = credentials.credentials
    current_user = get_current_user(token)
    
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido"
        )
    
    return current_user

# Endpoints de Conversas
@app.get("/api/conversations")
async def list_conversations(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Lista conversas do usuário"""
    token = credentials.credentials
    current_user = get_current_user(token)
    
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado")
    
    conversations = get_user_conversations(current_user["id"])
    return {"conversations": conversations}

@app.post("/api/conversations")
async def create_conversation_endpoint(
    conversation: ConversationCreate,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Cria nova conversa"""
    token = credentials.credentials
    current_user = get_current_user(token)
    
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado")
    
    session_id = str(uuid.uuid4())
    conversation_id = create_conversation(
        current_user["id"], 
        session_id, 
        conversation.title
    )
    
    return {
        "conversation_id": conversation_id,
        "session_id": session_id,
        "title": conversation.title
    }

@app.get("/api/conversations/{conversation_id}")
async def get_conversation(
    conversation_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(security)
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
    conversation_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(security)
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

# WebSocket com autenticação
@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """Endpoint WebSocket com autenticação"""
    # Obter token do query parameter
    token = websocket.query_params.get("token")
    
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
        conversation = get_conversation_by_session(session_id)
        if not conversation:
            # Criar nova conversa automaticamente
            conversation_id = create_conversation(
                current_user["id"],
                session_id,
                f"Conversa {datetime.now().strftime('%d/%m %H:%M')}"
            )
        else:
            conversation_id = conversation["id"]
        
        # Enviar histórico se existir
        messages = get_conversation_messages(conversation_id)
        for message in messages:
            await websocket.send_json({
                "type": "history",
                "message": message
            })
        
        # Loop de mensagens
        while True:
            try:
                # Receber mensagem do cliente
                data = await websocket.receive_json()
                
                if data.get("type") == "chat":
                    user_message = data.get("content", "")
                    
                    # Salvar mensagem do usuário
                    save_message(conversation_id, "user", user_message)
                    
                    # Enviar status de processamento
                    await websocket.send_json({
                        "type": "status",
                        "content": "Processando mensagem..."
                    })
                    
                    # Roteamento e geração de resposta
                    expert = moe_router.select_expert(user_message)
                    
                    # Gerar resposta com streaming
                    full_response = ""
                    expert_info = None
                    
                    async for chunk in llm_manager.stream_generate(user_message, expert):
                        if isinstance(chunk, str):
                            full_response += chunk
                            await websocket.send_json({
                                "type": "chunk",
                                "content": chunk
                            })
                        else:
                            expert_info = chunk
                    
                    # Salvar mensagem do assistente
                    save_message(
                        conversation_id, 
                        "assistant", 
                        full_response,
                        expert_id=expert["id"] if expert else None,
                        provider=expert_info.get("provider") if expert_info else None,
                        model=expert_info.get("model") if expert_info else None,
                        tokens=expert_info.get("tokens") if expert_info else None
                    )
                    
                    # Enviar mensagem final
                    await websocket.send_json({
                        "type": "done",
                        "content": full_response,
                        "expert": expert,
                        "provider": expert_info.get("provider") if expert_info else None,
                        "model": expert_info.get("model") if expert_info else None,
                        "tokens": expert_info.get("tokens") if expert_info else None
                    })
                
            except WebSocketDisconnect:
                break
            except Exception as e:
                print(f"[main] Erro no WebSocket: {e}")
                await websocket.send_json({
                    "type": "error",
                    "content": f"Erro: {str(e)}"
                })
                break
    
    finally:
        # Limpar conexão
        if session_id in active_connections:
            del active_connections[session_id]

# Endpoints existentes (compatibilidade)
@app.get("/health")
async def health_check():
    """Health check"""
    return {
        "status": "ok",
        "version": "1.0.0",
        "auth_enabled": True,
        "sessions": len(active_connections),
        "providers": await llm_manager.get_provider_status(),
        "experts": moe_router.get_experts()
    }

@app.get("/api/experts")
async def get_experts():
    """Lista de especialistas"""
    return {"experts": moe_router.get_experts()}

@app.get("/api/providers")
async def get_providers():
    """Status dos providers"""
    return {"providers": await llm_manager.get_provider_status()}

@app.delete("/api/session/{session_id}")
async def clear_session(session_id: str):
    """Limpa sessão"""
    if session_id in active_connections:
        await active_connections[session_id].close()
        del active_connections[session_id]
    
    return {"message": "Sessão limpa"}

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
        host="0.0.0.0",
        port=8000,
        reload=True
    )
