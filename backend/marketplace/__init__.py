"""
Marketplace Module - MCPs disponíveis para instalação
Sistema de marketplace de integrações para o OpenSlap
"""

from .registry import marketplace_registry, get_available_mcps, get_mcp_details

__all__ = [
    "marketplace_registry",
    "get_available_mcps",
    "get_mcp_details"
]
