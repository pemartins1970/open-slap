# MCP Server - Model Context Protocol Server

## Visão Geral

Servidor MCP completo para gerenciamento de contexto, sessões e comunicação entre componentes do sistema agêntico.

## Características

### 🚀 Funcionalidades Principais
- **Session Management** - Criação e gerenciamento de sessões
- **Context Management** - Armazenamento e recuperação de contexto
- **Message Routing** - Roteamento inteligente de mensagens
- **WebSocket Support** - Comunicação em tempo real
- **HTTP API** - Endpoints RESTful
- **LLM Integration** - Integração nativa com LLM Manager

### 🏗️ Arquitetura
```
MCP Server
├── Session Manager    # Gerencia sessões de usuário
├── Context Manager    # Armazena contexto e histórico
├── Message Router     # Roteia mensagens para handlers
├── WebSocket Handler  # Comunicação real-time
└── HTTP API          # Endpoints RESTful
```

## Instalação e Setup

### 1. Instalar Dependências
```bash
pip install -r requirements.txt
```

### 2. Estrutura de Diretórios
```bash
mkdir -p storage/contexts
mkdir -p storage/sessions
```

## Uso Básico

### Python
```python
import asyncio
from src.core.mcp_server import MCPServer
from src.core.llm_manager import LLMManager

async def main():
    # Create MCP server
    mcp_server = MCPServer(host="localhost", port=8000)
    
    # Inject LLM Manager
    llm_manager = LLMManager()
    mcp_server.set_llm_manager(llm_manager)
    
    # Start server
    await mcp_server.start()

asyncio.run(main())
```

### Testar Sistema
```bash
python test_mcp.py
```

## API Endpoints

### Health Check
```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-03-04T10:00:00"
}
```

### MCP Messages
```http
POST /mcp
Content-Type: application/json

{
  "id": "msg-1",
  "type": "request",
  "method": "session/create",
  "params": {
    "user_id": "user123",
    "metadata": {"client": "web"}
  }
}
```

### WebSocket
```javascript
const ws = new WebSocket('ws://localhost:8000/ws');

// Send message
ws.send(JSON.stringify({
  id: "ws-msg-1",
  type: "request",
  method: "session/create",
  params: { user_id: "user123" }
}));
```

## MCP Methods

### Session Management

#### Create Session
```json
{
  "id": "session-1",
  "type": "request",
  "method": "session/create",
  "params": {
    "user_id": "user123",
    "metadata": {"client": "web"}
  }
}
```

#### Get Session
```json
{
  "id": "session-2",
  "type": "request",
  "method": "session/get",
  "params": {
    "session_id": "abc-123"
  }
}
```

### Context Management

#### Update Context
```json
{
  "id": "context-1",
  "type": "request",
  "method": "context/update",
  "params": {
    "session_id": "abc-123",
    "updates": {
      "project_id": "proj-456",
      "working_directory": "/path/to/project"
    }
  }
}
```

#### Get Context
```json
{
  "id": "context-2",
  "type": "request",
  "method": "context/get",
  "params": {
    "session_id": "abc-123"
  }
}
```

### Message Handling

#### Send Message to LLM
```json
{
  "id": "message-1",
  "type": "request",
  "method": "message/send",
  "params": {
    "session_id": "abc-123",
    "message": "Hello, how are you?",
    "provider": "ollama",
    "model": "llama2"
  }
}
```

#### System Status
```json
{
  "id": "status-1",
  "type": "request",
  "method": "system/status",
  "params": {
    "session_id": "abc-123"
  }
}
```

## Estruturas de Dados

### MCP Message
```python
@dataclass
class MCPMessage:
    id: str
    type: MessageType
    method: Optional[str]
    params: Optional[Dict[str, Any]]
    result: Optional[Dict[str, Any]]
    error: Optional[Dict[str, Any]]
    timestamp: datetime
```

### Session
```python
@dataclass
class MCPSession:
    id: str
    user_id: str
    status: SessionStatus
    created_at: datetime
    last_activity: datetime
    context: Dict[str, Any]
    metadata: Dict[str, Any]
```

### Context
```python
@dataclass
class MCPContext:
    session_id: str
    project_id: Optional[str]
    conversation_history: List[Dict[str, Any]]
    working_directory: Optional[str]
    environment_vars: Dict[str, str]
    agent_preferences: Dict[str, Any]
```

## Configuração

### Environment Variables
```bash
# Server configuration
MCP_HOST=localhost
MCP_PORT=8000

# Storage paths
MCP_STORAGE_PATH=./storage
MCP_CONTEXTS_PATH=./storage/contexts

# Session settings
MCP_SESSION_TIMEOUT=30  # minutes
```

### Custom Handlers
```python
# Register custom message handler
async def custom_handler(params: Dict[str, Any], session: MCPSession):
    return {"custom_result": "success"}

mcp_server.message_router.register_handler("custom/method", custom_handler)
```

### Middleware
```python
# Add middleware for logging
async def logging_middleware(message: MCPMessage, session: MCPSession):
    logger.info(f"Processing {message.method} for session {session.id}")
    return message

mcp_server.message_router.add_middleware(logging_middleware)
```

## Performance

### Session Management
- **Memory Storage** para sessões ativas
- **File Persistence** para contextos
- **Auto Cleanup** de sessões expiradas
- **Concurrent Support** para múltiplos usuários

### Context Storage
- **JSON Files** para persistência
- **Async I/O** para performance
- **History Limit** (50 mensagens)
- **Lazy Loading** de contextos

### Message Processing
- **Async Handlers** para non-blocking
- **Error Handling** robusto
- **Type Safety** com dataclasses
- **Logging** completo

## Monitoramento

### Health Checks
```bash
curl http://localhost:8000/health
```

### System Status
```json
{
  "server": "running",
  "active_sessions": 3,
  "llm_providers": {
    "ollama": true,
    "gemini": false
  },
  "timestamp": "2024-03-04T10:00:00"
}
```

### Logs
```python
# MCP server logs
INFO: Created session abc-123 for user user123
INFO: Registered handler for method: message/send
INFO: Cleaned up 2 expired sessions
```

## Testes

### Unit Tests
```bash
pytest tests/test_mcp_server.py -v
```

### Integration Tests
```bash
python test_mcp.py
```

### Manual Testing
```bash
# Start server
python -m src.core.mcp_server

# Test health
curl http://localhost:8000/health

# Test MCP message
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{"id":"test","type":"request","method":"system/status","params":{}}'
```

## Troubleshooting

### Common Issues

**Port Already in Use**
```bash
# Change port
mcp_server = MCPServer(port=8001)
```

**Session Not Found**
```bash
# Check session timeout
# Default: 30 minutes of inactivity
```

**Context Not Loading**
```bash
# Check storage directory
ls -la storage/contexts/
```

**WebSocket Connection Failed**
```bash
# Check CORS settings
# Verify WebSocket library version
```

## Próximos Passos

1. **MoE Router** - Sistema de especialistas
2. **Interface Web** - Dashboard completo
3. **Authentication** - Sistema de usuários
4. **Rate Limiting** - Controle de uso
5. **Metrics** - Monitoramento avançado

## Contribuição

1. Fork projeto
2. Criar branch para feature
3. Implementar tests
4. Submit PR

## Licença

Projeto privado - uso local autorizado
