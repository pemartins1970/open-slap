"""
🚀 MAIN AUTH - Backend com Autenticação e Persistência
Implementação completa segundo WINDSURF_AGENT.md
"""

import os
import json
import asyncio
import uuid
import hashlib
import platform
import sys
from datetime import datetime
from typing import Dict, Any, Optional, List

from pathlib import Path
from dotenv import load_dotenv

from fastapi import FastAPI, HTTPException, status, Depends, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
import aiohttp

BASE_DIR = Path(__file__).resolve().parents[1]
load_dotenv(dotenv_path=BASE_DIR / ".env", override=False)

# Importar módulos locais
from .auth import (
    create_user, authenticate_user, create_access_token, 
    verify_token, get_current_user
)
from .db import (
    create_conversation, get_user_conversations, get_conversation_messages,
    save_message, delete_conversation, get_conversation_by_session,
    create_friction_event, list_friction_events, count_pending_friction_events,
    mark_friction_event_sent, delete_friction_event
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
security_optional = HTTPBearer(auto_error=False)

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
    lines.append(f"_Enviado automaticamente pelo {meta.get('product', 'open-slap')} v1.x_")
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
        async with session.post(url, headers=headers, json={"title": title, "body": body, "labels": labels}) as resp:
            data = await resp.json()
            if resp.status >= 300:
                raise RuntimeError(f"GitHub issue create failed: {resp.status} {data}")
            html_url = data.get("html_url")
            if not html_url:
                raise RuntimeError("GitHub issue create missing html_url")
            return str(html_url)

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

@app.get("/api/friction/config")
async def friction_config():
    return {"mode": _friction_mode()}

@app.get("/api/friction/pending_count")
async def friction_pending_count():
    if _friction_mode() == "disabled":
        return {"mode": "disabled", "pending": 0}
    return {"mode": _friction_mode(), "pending": count_pending_friction_events()}

@app.get("/api/friction/pending")
async def friction_pending(limit: int = 100):
    if _friction_mode() == "disabled":
        raise HTTPException(status_code=404, detail="Friction module disabled")
    rows = list_friction_events(sent=0, limit=limit)
    items: List[Dict[str, Any]] = []
    for r in rows:
        payload = json.loads(r.get("payload_json", "{}"))
        items.append({"id": r.get("id"), "payload": payload, "created_at": r.get("created_at")})
    return {"mode": _friction_mode(), "events": items}

@app.post("/api/friction/report")
async def friction_report(
    report: FrictionReportInput,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_optional),
):
    mode = _friction_mode()
    if mode == "disabled":
        raise HTTPException(status_code=404, detail="Friction module disabled")

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
    return {"sent": [r for r in results if r["status"] == "sent"], "errors": [r for r in results if r["status"] == "error"]}

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
