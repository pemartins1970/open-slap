"""
Integrações com serviços externos
"""

from .ai_gateway_client import AIGatewayClient, ai_gateway, AIGatewayError, AIGatewayDisabled

__all__ = ["AIGatewayClient", "ai_gateway", "AIGatewayError", "AIGatewayDisabled"]

from .shopify_mcp import shopify_mcp, ShopifyMCP
from .stripe_mcp import stripe_mcp, StripeMCP
from .google_aistudio_mcp import google_aistudio_mcp, GoogleAIStudioMCP

__all__ = [
    "shopify_mcp",
    "ShopifyMCP", 
    "stripe_mcp",
    "StripeMCP",
    "google_aistudio_mcp",
    "GoogleAIStudioMCP"
]
