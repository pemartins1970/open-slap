"""
Middleware de Autenticação
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from ..utils.auth_helpers import (
    extract_bearer_token_from_headers,
    is_public_path,
    requires_auth,
)
from ..auth import get_current_user


class AuthRequiredMiddleware(BaseHTTPMiddleware):
    """Middleware que exige autenticação para endpoints protegidos"""
    
    async def dispatch(self, request: Request, call_next):
        # Permite requisições OPTIONS (CORS preflight)
        if request.method.upper() == "OPTIONS":
            return await call_next(request)
        
        # Verifica se o path é público ou não requer autenticação
        if is_public_path(request.url.path) or not requires_auth(request.url.path):
            return await call_next(request)
        
        # Extrai token do cabeçalho
        token = extract_bearer_token_from_headers(dict(request.headers))
        if not token:
            return JSONResponse(
                status_code=401, 
                content={"detail": "Token não fornecido"}
            )
        
        # Valida token e obtém usuário
        user = get_current_user(token)
        if not user:
            return JSONResponse(
                status_code=401, 
                content={"detail": "Token inválido"}
            )
        
        # Adiciona usuário ao request state
        request.state.current_user = user
        return await call_next(request)
