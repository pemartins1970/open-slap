import asyncio
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import logging
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import aiofiles
import os
from .llm_manager import LLMManager, BaseProvider, OllamaProvider, GeminiProvider, APIKeyManager, LLMResponse
try:
    from .moe_router import MoERouter, Task, TaskType
except ImportError:
    # Fallback to simple MoE if sklearn is not available
    from test_moe_simple import SimpleMoERouter as MoERouter
    from test_moe_simple import Task, TaskType

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MessageType(Enum):
    """MCP Message types"""
    REQUEST = "request"
    RESPONSE = "response"
    NOTIFICATION = "notification"
    ERROR = "error"

class SessionStatus(Enum):
    """Session status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    EXPIRED = "expired"

@dataclass
class MCPMessage:
    """MCP Message structure"""
    id: str
    type: MessageType
    method: Optional[str] = None
    params: Optional[Dict[str, Any]] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, Any]] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

@dataclass
class MCPSession:
    """MCP Session structure"""
    id: str
    user_id: str
    status: SessionStatus
    created_at: datetime
    last_activity: datetime
    context: Dict[str, Any]
    metadata: Dict[str, Any]
    
    def update_activity(self):
        self.last_activity = datetime.now()
    
    def is_expired(self, timeout_minutes: int = 30) -> bool:
        return datetime.now() - self.last_activity > timedelta(minutes=timeout_minutes)

@dataclass
class MCPContext:
    """MCP Context structure"""
    session_id: str
    project_id: Optional[str] = None
    conversation_history: List[Dict[str, Any]] = None
    working_directory: Optional[str] = None
    environment_vars: Dict[str, str] = None
    agent_preferences: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.conversation_history is None:
            self.conversation_history = []
        if self.environment_vars is None:
            self.environment_vars = {}
        if self.agent_preferences is None:
            self.agent_preferences = {}

class SessionManager:
    """Manages MCP sessions"""
    
    def __init__(self):
        self.sessions: Dict[str, MCPSession] = {}
        self.session_timeout_minutes = 30
    
    def create_session(self, user_id: str, metadata: Dict[str, Any] = None) -> MCPSession:
        """Create a new session"""
        session_id = str(uuid.uuid4())
        session = MCPSession(
            id=session_id,
            user_id=user_id,
            status=SessionStatus.ACTIVE,
            created_at=datetime.now(),
            last_activity=datetime.now(),
            context={},
            metadata=metadata or {}
        )
        self.sessions[session_id] = session
        logger.info(f"Created session {session_id} for user {user_id}")
        return session
    
    def get_session(self, session_id: str) -> Optional[MCPSession]:
        """Get session by ID"""
        session = self.sessions.get(session_id)
        if session and session.is_expired(self.session_timeout_minutes):
            session.status = SessionStatus.EXPIRED
            logger.info(f"Session {session_id} expired")
            return None
        return session
    
    def update_session(self, session_id: str, **kwargs) -> bool:
        """Update session data"""
        session = self.get_session(session_id)
        if not session:
            return False
        
        session.update_activity()
        for key, value in kwargs.items():
            if hasattr(session, key):
                setattr(session, key, value)
        
        return True
    
    def delete_session(self, session_id: str) -> bool:
        """Delete session"""
        if session_id in self.sessions:
            del self.sessions[session_id]
            logger.info(f"Deleted session {session_id}")
            return True
        return False
    
    def cleanup_expired_sessions(self):
        """Clean up expired sessions"""
        expired_count = 0
        for session_id, session in list(self.sessions.items()):
            if session.is_expired(self.session_timeout_minutes):
                session.status = SessionStatus.EXPIRED
                del self.sessions[session_id]
                expired_count += 1
        
        if expired_count > 0:
            logger.info(f"Cleaned up {expired_count} expired sessions")
    
    def get_active_sessions(self) -> List[MCPSession]:
        """Get all active sessions"""
        return [s for s in self.sessions.values() if s.status == SessionStatus.ACTIVE]

class ContextManager:
    """Manages MCP context"""
    
    def __init__(self, storage_path: str = "storage/contexts"):
        self.storage_path = storage_path
        self.contexts: Dict[str, MCPContext] = {}
        self._ensure_storage_dir()
    
    def _ensure_storage_dir(self):
        """Ensure storage directory exists"""
        os.makedirs(self.storage_path, exist_ok=True)
    
    def create_context(self, session_id: str, **kwargs) -> MCPContext:
        """Create new context"""
        context = MCPContext(session_id=session_id, **kwargs)
        self.contexts[session_id] = context
        asyncio.create_task(self._save_context(context))
        return context
    
    def get_context(self, session_id: str) -> Optional[MCPContext]:
        """Get context by session ID"""
        if session_id not in self.contexts:
            # Try to load from storage
            asyncio.create_task(self._load_context(session_id))
        return self.contexts.get(session_id)
    
    def update_context(self, session_id: str, **kwargs) -> bool:
        """Update context"""
        context = self.get_context(session_id)
        if not context:
            return False
        
        for key, value in kwargs.items():
            if hasattr(context, key):
                setattr(context, key, value)
        
        asyncio.create_task(self._save_context(context))
        return True
    
    def add_to_history(self, session_id: str, message: Dict[str, Any]):
        """Add message to conversation history"""
        context = self.get_context(session_id)
        if context:
            context.conversation_history.append({
                **message,
                'timestamp': datetime.now().isoformat()
            })
            
            # Keep only last 50 messages
            if len(context.conversation_history) > 50:
                context.conversation_history = context.conversation_history[-50:]
            
            asyncio.create_task(self._save_context(context))
    
    async def _save_context(self, context: MCPContext):
        """Save context to file"""
        try:
            file_path = os.path.join(self.storage_path, f"{context.session_id}.json")
            async with aiofiles.open(file_path, 'w') as f:
                data = asdict(context)
                data['conversation_history'] = context.conversation_history
                await f.write(json.dumps(data, default=str, indent=2))
        except Exception as e:
            logger.error(f"Failed to save context {context.session_id}: {e}")
    
    async def _load_context(self, session_id: str):
        """Load context from file"""
        try:
            file_path = os.path.join(self.storage_path, f"{session_id}.json")
            if os.path.exists(file_path):
                async with aiofiles.open(file_path, 'r') as f:
                    content = await f.read()
                    data = json.loads(content)
                    context = MCPContext(**data)
                    self.contexts[session_id] = context
        except Exception as e:
            logger.error(f"Failed to load context {session_id}: {e}")

class MessageRouter:
    """Routes MCP messages to appropriate handlers"""
    
    def __init__(self):
        self.handlers: Dict[str, Callable] = {}
        self.middleware: List[Callable] = []
    
    def register_handler(self, method: str, handler: Callable):
        """Register a message handler"""
        self.handlers[method] = handler
        logger.info(f"Registered handler for method: {method}")
    
    def add_middleware(self, middleware: Callable):
        """Add middleware to message processing"""
        self.middleware.append(middleware)
    
    async def route_message(self, message: MCPMessage, session: MCPSession) -> MCPMessage:
        """Route message to appropriate handler"""
        # Apply middleware
        for middleware in self.middleware:
            message = await middleware(message, session)
            if message is None:
                return None
        
        # Route to handler
        if message.method in self.handlers:
            try:
                result = await self.handlers[message](message.params, session)
                return MCPMessage(
                    id=message.id,
                    type=MessageType.RESPONSE,
                    result=result
                )
            except Exception as e:
                logger.error(f"Handler error for {message.method}: {e}")
                return MCPMessage(
                    id=message.id,
                    type=MessageType.ERROR,
                    error={"code": -1, "message": str(e)}
                )
        else:
            return MCPMessage(
                id=message.id,
                type=MessageType.ERROR,
                error={"code": -32601, "message": "Method not found"}
            )

class MCPServer:
    """Main MCP Server implementation"""
    
    def __init__(self, host: str = "localhost", port: int = 8000):
        self.host = host
        self.port = port
        self.app = FastAPI(title="MCP Server", version="1.0.0")
        self.session_manager = SessionManager()
        self.context_manager = ContextManager()
        self.message_router = MessageRouter()
        self.llm_manager = None  # Will be injected
        self.moe_router = MoERouter()  # MoE Router
        
        self._setup_middleware()
        self._register_handlers()
        self._setup_routes()
    
    def _setup_middleware(self):
        """Setup FastAPI middleware"""
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    
    def _register_handlers(self):
        """Register default message handlers"""
        self.message_router.register_handler("session/create", self._handle_create_session)
        self.message_router.register_handler("session/get", self._handle_get_session)
        self.message_router.register_handler("context/update", self._handle_update_context)
        self.message_router.register_handler("context/get", self._handle_get_context)
        self.message_router.register_handler("message/send", self._handle_send_message)
        self.message_router.register_handler("system/status", self._handle_system_status)
        self.message_router.register_handler("moe/route_task", self._handle_moe_route_task)
        self.message_router.register_handler("moe/expert_status", self._handle_moe_expert_status)
    
    def _setup_routes(self):
        """Setup HTTP routes"""
        
        @self.app.get("/health")
        async def health_check():
            return {"status": "healthy", "timestamp": datetime.now().isoformat()}
        
        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            await self._handle_websocket(websocket)
        
        @self.app.post("/mcp")
        async def mcp_endpoint(message: Dict[str, Any]):
            return await self._handle_http_message(message)
    
    def set_llm_manager(self, llm_manager):
        """Inject LLM Manager"""
        self.llm_manager = llm_manager
    
    async def _handle_websocket(self, websocket: WebSocket):
        """Handle WebSocket connections"""
        await websocket.accept()
        session = None
        
        try:
            while True:
                data = await websocket.receive_text()
                try:
                    message_data = json.loads(data)
                    message = MCPMessage(**message_data)
                except (json.JSONDecodeError, TypeError) as e:
                    error_response = MCPMessage(
                        id="error",
                        type=MessageType.ERROR,
                        error={"code": -32700, "message": f"Parse error: {str(e)}"}
                    )
                    await websocket.send_text(json.dumps(asdict(error_response), default=str))
                    continue
                
                # Get or create session
                if not session:
                    if message.method == "session/create":
                        session = self.session_manager.create_session(
                            user_id=message.params.get("user_id", "anonymous"),
                            metadata=message.params.get("metadata", {})
                        )
                    else:
                        error_response = MCPMessage(
                            id=message.id,
                            type=MessageType.ERROR,
                            error={"code": -32000, "message": "No session established"}
                        )
                        await websocket.send_text(json.dumps(asdict(error_response), default=str))
                        continue
                
                # Route message
                try:
                    response = await self.message_router.route_message(message, session)
                    if response:
                        await websocket.send_text(json.dumps(asdict(response), default=str))
                except Exception as e:
                    error_response = MCPMessage(
                        id=message.id,
                        type=MessageType.ERROR,
                        error={"code": -32603, "message": f"Internal error: {str(e)}"}
                    )
                    await websocket.send_text(json.dumps(asdict(error_response), default=str))
        
        except WebSocketDisconnect:
            if session:
                self.session_manager.delete_session(session.id)
                logger.info(f"WebSocket disconnected, session {session.id} cleaned up")
    
    async def _handle_http_message(self, message_data: Dict[str, Any]):
        """Handle HTTP messages"""
        message = MCPMessage(**message_data)
        
        # Special handling for session creation
        if message.method == "session/create":
            # Create temporary session for this request
            temp_session = self.session_manager.create_session(
                user_id=message.params.get("user_id", "anonymous"),
                metadata=message.params.get("metadata", {})
            )
            response = await self.message_router.route_message(message, temp_session)
            return asdict(response, default=str) if response else {"error": "No response"}
        
        # Get session from params for other methods
        session_id = message.params.get("session_id")
        if not session_id:
            return {"error": "session_id required"}
            
        session = self.session_manager.get_session(session_id)
        
        if not session:
            return {"error": "Invalid or expired session"}
        
        # Route message
        response = await self.message_router.route_message(message, session)
        return asdict(response, default=str) if response else {"error": "No response"}
    
    # Message Handlers
    async def _handle_create_session(self, params: Dict[str, Any], session: MCPSession):
        """Handle session creation"""
        user_id = params.get("user_id", "anonymous")
        metadata = params.get("metadata", {})
        
        new_session = self.session_manager.create_session(user_id, metadata)
        self.context_manager.create_context(new_session.id)
        
        return {
            "session_id": new_session.id,
            "status": new_session.status.value,
            "created_at": new_session.created_at.isoformat()
        }
    
    async def _handle_get_session(self, params: Dict[str, Any], session: MCPSession):
        """Handle session retrieval"""
        return {
            "session_id": session.id,
            "user_id": session.user_id,
            "status": session.status.value,
            "last_activity": session.last_activity.isoformat()
        }
    
    async def _handle_update_context(self, params: Dict[str, Any], session: MCPSession):
        """Handle context update"""
        context_updates = params.get("updates", {})
        success = self.context_manager.update_context(session.id, **context_updates)
        
        return {"success": success}
    
    async def _handle_get_context(self, params: Dict[str, Any], session: MCPSession):
        """Handle context retrieval"""
        context = self.context_manager.get_context(session.id)
        if context:
            return asdict(context, default=str)
        return {"error": "Context not found"}
    
    async def _handle_send_message(self, params: Dict[str, Any], session: MCPSession):
        """Handle message sending to LLM"""
        if not self.llm_manager:
            return {"error": "LLM Manager not configured"}
        
        message_content = params.get("message", "")
        provider = params.get("provider", "ollama")
        model = params.get("model", None)
        
        try:
            # Add to context history
            self.context_manager.add_to_history(session.id, {
                "role": "user",
                "content": message_content
            })
            
            # Generate response
            response = await self.llm_manager.generate(
                message_content,
                provider=provider,
                model=model
            )
            
            # Add response to context
            self.context_manager.add_to_history(session.id, {
                "role": "assistant",
                "content": response.content,
                "provider": response.provider,
                "model": response.model
            })
            
            return {
                "content": response.content,
                "provider": response.provider,
                "model": response.model,
                "response_time": response.response_time
            }
        
        except Exception as e:
            logger.error(f"LLM generation error: {e}")
            return {"error": str(e)}
    
    async def _handle_system_status(self, params: Dict[str, Any], session: MCPSession):
        """Handle system status request"""
        status = {
            "server": "running",
            "active_sessions": len(self.session_manager.get_active_sessions()),
            "llm_providers": [],
            "moe_experts": len(self.moe_router.registry.experts),
            "timestamp": datetime.now().isoformat()
        }
        
        if self.llm_manager:
            provider_status = await self.llm_manager.validate_providers()
            status["llm_providers"] = provider_status
        
        return status
    
    async def _handle_moe_route_task(self, params: Dict[str, Any], session: MCPSession):
        """Handle MoE task routing"""
        try:
            # Create task from params
            task = Task(
                id=params.get("task_id", str(uuid.uuid4())),
                type=TaskType(params.get("task_type", "coding")),
                description=params.get("description", ""),
                requirements=params.get("requirements", []),
                priority=params.get("priority", 5),
                estimated_duration=params.get("estimated_duration", 30),
                context=params.get("context", {}),
                created_at=datetime.now()
            )
            
            # Route task through MoE
            result = await self.moe_router.route_task(
                task, 
                use_multiple_experts=params.get("use_multiple_experts", False)
            )
            
            # Add to context history
            self.context_manager.add_to_history(session.id, {
                "role": "moe_router",
                "content": f"Routed task {task.id} to expert(s)",
                "task_id": task.id,
                "expert_id": result.expert_contributions[0][0] if result.expert_contributions else None,
                "confidence": result.confidence_score
            })
            
            return {
                "task_id": task.id,
                "result": result.primary_result,
                "confidence": result.confidence_score,
                "expert_contributions": result.expert_contributions,
                "processing_time": result.processing_time,
                "aggregation_method": result.aggregation_method
            }
            
        except Exception as e:
            logger.error(f"MoE routing error: {e}")
            return {"error": str(e)}
    
    async def _handle_moe_expert_status(self, params: Dict[str, Any], session: MCPSession):
        """Handle MoE expert status request"""
        try:
            expert_status = self.moe_router.get_expert_status()
            active_tasks = self.moe_router.get_active_tasks()
            
            return {
                "experts": expert_status,
                "active_tasks": active_tasks,
                "total_experts": len(self.moe_router.registry.experts),
                "available_experts": len(self.moe_router.registry.get_available_experts())
            }
            
        except Exception as e:
            logger.error(f"MoE expert status error: {e}")
            return {"error": str(e)}
    
    async def start(self):
        """Start the MCP server"""
        import uvicorn
        
        # Start cleanup task
        asyncio.create_task(self._cleanup_task())
        
        logger.info(f"Starting MCP Server on {self.host}:{self.port}")
        config = uvicorn.Config(self.app, host=self.host, port=self.port)
        server = uvicorn.Server(config)
        await server.serve()
    
    async def _cleanup_task(self):
        """Background cleanup task"""
        while True:
            await asyncio.sleep(300)  # Run every 5 minutes
            self.session_manager.cleanup_expired_sessions()

# Usage example
async def main():
    from .llm_manager import LLMManager, BaseProvider, OllamaProvider, GeminiProvider, APIKeyManager, LLMResponse
    from .moe_router import MoERouter, Task, TaskType
    
    # Create MCP server
    mcp_server = MCPServer()
    
    # Inject LLM Manager
    llm_manager = LLMManager()
    mcp_server.set_llm_manager(llm_manager)
    
    # Start server
    await mcp_server.start()

if __name__ == "__main__":
    asyncio.run(main())
