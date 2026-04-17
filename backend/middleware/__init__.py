"""
Middleware da Aplicação
"""

from .auth import AuthRequiredMiddleware

__all__ = ["AuthRequiredMiddleware"]
