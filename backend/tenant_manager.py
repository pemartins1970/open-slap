"""
Tenant Manager - Sistema de Multi-tenancy
Stub temporário para resolver imports quebrados
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)

class TenantManager:
    """Gerenciador de tenants para isolamento de dados por usuário"""
    
    def __init__(self):
        self._current_tenant: Optional[str] = None
        logger.debug("TenantManager inicializado")
    
    def set_tenant(self, tenant_id: str) -> None:
        """Define o tenant atual para isolamento de dados"""
        self._current_tenant = tenant_id
        logger.debug(f"Tenant definido: {tenant_id}")
    
    def get_tenant(self) -> Optional[str]:
        """Retorna o tenant atual"""
        return self._current_tenant
    
    def clear_tenant(self) -> None:
        """Limpa o tenant atual"""
        self._current_tenant = None
        logger.debug("Tenant limpo")

# Singleton global
tenant_manager = TenantManager()
