"""
Rate Limiting Middleware - Proteção contra abuso de endpoints
Implementa rate limiting por IP e endpoint
"""

import time
import logging
from typing import Dict, List, Optional
from collections import defaultdict, deque
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)

class RateLimitEntry:
    """Entrada de rate limit para um IP específico"""
    def __init__(self, window_size: int = 60):
        self.window_size = window_size  # segundos
        self.requests = deque()  # timestamps das requisições
    
    def is_allowed(self, limit: int) -> bool:
        """Verifica se requisição é permitida"""
        now = time.time()
        
        # Remover requisições antigas fora da janela
        while self.requests and self.requests[0] < now - self.window_size:
            self.requests.popleft()
        
        # Verificar se excedeu o limite
        if len(self.requests) >= limit:
            return False
        
        # Adicionar requisição atual
        self.requests.append(now)
        return True
    
    def get_remaining_time(self) -> float:
        """Tempo restante para reset do rate limit"""
        if not self.requests:
            return 0
        
        oldest = self.requests[0]
        reset_time = oldest + self.window_size
        remaining = reset_time - time.time()
        return max(0, remaining)

class RateLimiterMiddleware(BaseHTTPMiddleware):
    """Middleware de rate limiting para FastAPI"""
    
    def __init__(self, app, default_limits: Dict[str, Dict[str, int]] = None):
        super().__init__(app)
        # Configurações default: {endpoint: {limit: X, window: Y}}
        self.default_limits = default_limits or {
            "/auth/login": {"limit": 5, "window": 300},      # 5 tentativas em 5 minutos
            "/auth/register": {"limit": 3, "window": 300},   # 3 registros em 5 minutos
            "/auth/password-reset": {"limit": 3, "window": 300}, # 3 resets em 5 minutos
            "/api/conversations": {"limit": 100, "window": 60}, # 100 conversas por minuto
            "/ws/": {"limit": 1000, "window": 60},       # 1000 mensagens por minuto
        }
        
        # Rate limits por IP
        self.rate_limits: Dict[str, RateLimitEntry] = defaultdict(lambda: RateLimitEntry())
        
        # Contadores globais (para endpoints sensíveis)
        self.global_counters: Dict[str, deque] = defaultdict(deque)
        
    async def dispatch(self, request: Request, call_next):
        """Processa requisição com rate limiting"""
        path = request.url.path
        
        # Verificar se endpoint tem rate limiting
        if not self._should_rate_limit(path):
            return await call_next(request)
        
        client_ip = self._get_client_ip(request)
        limit_config = self._get_limit_config(path)
        
        # Rate limiting por IP
        ip_key = f"{client_ip}:{path}"
        ip_rate_entry = self.rate_limits[ip_key]
        
        if not ip_rate_entry.is_allowed(limit_config["limit"]):
            remaining_time = ip_rate_entry.get_remaining_time()
            
            logger.warning(
                f"Rate limit exceeded for IP {client_ip} on {path}. "
                f"Limit: {limit_config['limit']}/{limit_config['window']}s. "
                f"Retry after: {remaining_time:.1f}s"
            )
            
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": "Rate limit exceeded",
                    "message": f"Muitas tentativas. Tente novamente em {remaining_time:.0f} segundos.",
                    "retry_after": int(remaining_time),
                    "limit": limit_config["limit"],
                    "window": limit_config["window"]
                },
                headers={
                    "Retry-After": str(int(remaining_time)),
                    "X-RateLimit-Limit": str(limit_config["limit"]),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(time.time() + remaining_time))
                }
            )
        
        # Adicionar headers informativos
        response = await call_next(request)
        remaining_requests = limit_config["limit"] - len(ip_rate_entry.requests)
        
        response.headers["X-RateLimit-Limit"] = str(limit_config["limit"])
        response.headers["X-RateLimit-Remaining"] = str(max(0, remaining_requests))
        response.headers["X-RateLimit-Reset"] = str(int(time.time() + ip_rate_entry.get_remaining_time()))
        
        return response
    
    def _should_rate_limit(self, path: str) -> bool:
        """Verifica se path deve ter rate limiting"""
        # Rate limiting apenas para endpoints específicos
        for endpoint in self.default_limits.keys():
            if path.startswith(endpoint):
                return True
        return False
    
    def _get_limit_config(self, path: str) -> Dict[str, int]:
        """Obtém configuração de rate limit para path"""
        for endpoint, config in self.default_limits.items():
            if path.startswith(endpoint):
                return config
        
        # Default se não encontrar configuração específica
        return {"limit": 100, "window": 60}
    
    def _get_client_ip(self, request: Request) -> str:
        """Obtém IP real do cliente"""
        # Tentar obter IP real através de headers
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip.strip()
        
        # Fallback para IP direto
        return request.client.host if request.client else "unknown"

class AccountLockoutMiddleware(BaseHTTPMiddleware):
    """Middleware para bloqueio de conta após múltiplas falhas"""
    
    def __init__(self, app, max_attempts: int = 5, lockout_duration: int = 900):
        super().__init__(app)
        self.max_attempts = max_attempts
        self.lockout_duration = lockout_duration  # 15 minutos
        self.failed_attempts: Dict[str, List[float]] = defaultdict(list)
    
    async def dispatch(self, request: Request, call_next):
        """Processa requisição com account lockout"""
        if not request.url.path.startswith("/auth/login"):
            return await call_next(request)
        
        # Obter email da requisição (se disponível)
        client_ip = self._get_client_ip(request)
        
        # Verificar se está bloqueado
        if self._is_account_locked(client_ip):
            lock_time = self._get_lock_time_remaining(client_ip)
            
            logger.warning(
                f"Account locked for IP {client_ip} due to multiple failed attempts. "
                f"Unlock in: {lock_time:.1f}s"
            )
            
            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail={
                    "error": "Account temporarily locked",
                    "message": f"Conta bloqueada por múltiplas tentativas. Tente novamente em {lock_time:.0f} segundos.",
                    "unlock_after": int(lock_time)
                },
                headers={"Retry-After": str(int(lock_time))}
            )
        
        # Processar requisição
        response = await call_next(request)
        
        # Verificar se falhou login
        if response.status_code == 401:
            self._record_failed_attempt(client_ip)
        elif response.status_code == 200:
            # Login bem-sucedido, limpar tentativas
            self._clear_failed_attempts(client_ip)
        
        return response
    
    def _is_account_locked(self, identifier: str) -> bool:
        """Verifica se conta/IP está bloqueado"""
        if identifier not in self.failed_attempts:
            return False
        
        # Verificar tentativas recentes
        now = time.time()
        recent_attempts = [
            attempt for attempt in self.failed_attempts[identifier]
            if now - attempt < self.lockout_duration
        ]
        
        return len(recent_attempts) >= self.max_attempts
    
    def _get_lock_time_remaining(self, identifier: str) -> float:
        """Tempo restante para desbloqueio"""
        if identifier not in self.failed_attempts:
            return 0
        
        now = time.time()
        oldest_attempt = min(self.failed_attempts[identifier])
        unlock_time = oldest_attempt + self.lockout_duration
        
        return max(0, unlock_time - now)
    
    def _record_failed_attempt(self, identifier: str) -> None:
        """Registra tentativa falha"""
        now = time.time()
        self.failed_attempts[identifier].append(now)
        
        # Limpar tentativas antigas
        self.failed_attempts[identifier] = [
            attempt for attempt in self.failed_attempts[identifier]
            if now - attempt < self.lockout_duration
        ]
    
    def _clear_failed_attempts(self, identifier: str) -> None:
        """Limpa tentativas falhas após login bem-sucedido"""
        if identifier in self.failed_attempts:
            del self.failed_attempts[identifier]
    
    def _get_client_ip(self, request: Request) -> str:
        """Obtém IP real do cliente"""
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip.strip()
        
        return request.client.host if request.client else "unknown"

# Funções de conveniência para adicionar middlewares
def add_rate_limiting(app, custom_limits: Dict[str, Dict[str, int]] = None):
    """Adiciona rate limiting middleware à aplicação"""
    app.add_middleware(RateLimiterMiddleware, default_limits=custom_limits)

def add_account_lockout(app, max_attempts: int = 5, lockout_duration: int = 900):
    """Adiciona account lockout middleware à aplicação"""
    app.add_middleware(
        AccountLockoutMiddleware, 
        max_attempts=max_attempts, 
        lockout_duration=lockout_duration
    )
