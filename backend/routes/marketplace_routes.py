"""
Marketplace Routes - Endpoints para o marketplace de MCPs
API para descoberta, instalação e execução de integrações
"""

from fastapi import APIRouter, HTTPException, Depends, Body, Query
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from ..deps import security
from ..main_auth import get_current_user
from ..marketplace.registry import (
    marketplace_registry,
    get_mcp_details,
    get_mcp_executor
)
from ..services.mcp_service import install_mcp_for_user, get_user_mcps

marketplace_router = APIRouter(prefix="/api/marketplace", tags=["marketplace"])


# Pydantic Models
class MCPSearchRequest(BaseModel):
    """Request para pesquisa de MCPs"""
    query: str = Field(..., description="Termo de pesquisa")


class MCPInstallRequest(BaseModel):
    """Request para instalação de MCP do marketplace"""
    mcp_id: str = Field(..., description="ID do MCP no marketplace")
    credentials: Optional[Dict[str, str]] = Field({}, description="Credenciais da integração")


class MCPExecuteRequest(BaseModel):
    """Request para execução de tool de MCP"""
    tool_name: str = Field(..., description="Nome da ferramenta")
    params: Dict[str, Any] = Field({}, description="Parâmetros da ferramenta")


class MCPCredentialsRequest(BaseModel):
    """Request para salvar credenciais de MCP"""
    credentials: Dict[str, str] = Field(..., description="Credenciais da integração")


# Endpoints
@marketplace_router.get("/")
async def list_marketplace_mcps(
    category: Optional[str] = None,
    featured_only: bool = False,
    new_only: bool = False,
    tier: Optional[str] = None,
    include_coming_soon: bool = False,
    credentials = Depends(security)
) -> Dict[str, Any]:
    """
    Lista MCPs disponíveis no marketplace
    
    Query Parameters:
    - category: Filtrar por categoria
    - featured_only: Retorna apenas MCPs em destaque
    - new_only: Retorna apenas MCPs novos
    - tier: Filtrar por tier (free/pro/enterprise)
    - include_coming_soon: Inclui MCPs em desenvolvimento
    """
    try:
        token = credentials.credentials
        current_user = get_current_user(token)
        
        if not current_user:
            raise HTTPException(status_code=401, detail="Não autenticado")
        
        # Obter MCPs
        if featured_only:
            mcps = marketplace_registry.get_featured()
        elif new_only:
            mcps = marketplace_registry.get_new()
        elif category:
            mcps = marketplace_registry.get_by_category(category)
        else:
            mcps = marketplace_registry.get_all_mcps(include_coming_soon)
        
        # Filtrar por tier
        if tier:
            mcps = [m for m in mcps if m.get("tier") == tier]
        
        # Verificar quais estão instalados pelo usuário
        user_id = current_user.get("id")
        installed_mcps = await get_user_mcps(user_id, active_only=False)
        installed_ids = {mcp.get("id") for mcp in installed_mcps}
        
        for mcp in mcps:
            mcp["is_installed"] = mcp["id"] in installed_ids
        
        return {
            "success": True,
            "total": len(mcps),
            "filters": {
                "category": category,
                "featured_only": featured_only,
                "new_only": new_only,
                "tier": tier,
                "include_coming_soon": include_coming_soon
            },
            "mcps": mcps
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao listar MCPs: {str(e)}")


@marketplace_router.get("/stats")
async def get_marketplace_stats(
    credentials = Depends(security)
) -> Dict[str, Any]:
    """
    Retorna estatísticas do marketplace
    """
    try:
        token = credentials.credentials
        current_user = get_current_user(token)
        
        if not current_user:
            raise HTTPException(status_code=401, detail="Não autenticado")
        
        stats = marketplace_registry.get_stats()
        categories = marketplace_registry.get_categories()
        
        return {
            "success": True,
            "stats": stats,
            "categories": categories
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter estatísticas: {str(e)}")


@marketplace_router.get("/categories")
async def list_categories(
    credentials = Depends(security)
) -> Dict[str, Any]:
    """
    Lista todas as categorias disponíveis no marketplace
    """
    try:
        token = credentials.credentials
        current_user = get_current_user(token)
        
        if not current_user:
            raise HTTPException(status_code=401, detail="Não autenticado")
        
        categories = marketplace_registry.get_categories()
        
        return {
            "success": True,
            "categories": categories
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao listar categorias: {str(e)}")


@marketplace_router.get("/search")
async def search_mcps(
    query: str = Query(..., description="Termo de pesquisa"),
    credentials = Depends(security)
) -> Dict[str, Any]:
    """
    Pesquisa MCPs no marketplace
    
    Query Parameters:
    - query: Termo de pesquisa (nome, descrição, tags)
    """
    try:
        token = credentials.credentials
        current_user = get_current_user(token)
        
        if not current_user:
            raise HTTPException(status_code=401, detail="Não autenticado")
        
        results = marketplace_registry.search(query)
        
        return {
            "success": True,
            "query": query,
            "total_results": len(results),
            "mcps": results
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na pesquisa: {str(e)}")


@marketplace_router.get("/{mcp_id}")
async def get_mcp_info(
    mcp_id: str,
    credentials = Depends(security)
) -> Dict[str, Any]:
    """
    Obtém detalhes de um MCP específico
    
    Path Parameters:
    - mcp_id: ID do MCP no marketplace
    """
    try:
        token = credentials.credentials
        current_user = get_current_user(token)
        
        if not current_user:
            raise HTTPException(status_code=401, detail="Não autenticado")
        
        mcp = get_mcp_details(mcp_id)
        
        if not mcp:
            raise HTTPException(status_code=404, detail=f"MCP '{mcp_id}' não encontrado")
        
        # Verificar se está instalado
        user_id = current_user.get("id")
        installed_mcps = await get_user_mcps(user_id, active_only=False)
        mcp["is_installed"] = any(m.get("id") == mcp_id for m in installed_mcps)
        
        return {
            "success": True,
            "mcp": mcp
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter MCP: {str(e)}")


@marketplace_router.post("/{mcp_id}/install")
async def install_marketplace_mcp(
    mcp_id: str,
    request: MCPInstallRequest,
    credentials = Depends(security)
) -> Dict[str, Any]:
    """
    Instala um MCP do marketplace para o usuário
    
    Path Parameters:
    - mcp_id: ID do MCP no marketplace
    
    Body:
    - credentials: Credenciais da integração (opcional)
    """
    try:
        token = credentials.credentials
        current_user = get_current_user(token)
        
        if not current_user:
            raise HTTPException(status_code=401, detail="Não autenticado")
        
        # Verificar se MCP existe no marketplace
        mcp = get_mcp_details(mcp_id)
        if not mcp:
            raise HTTPException(status_code=404, detail=f"MCP '{mcp_id}' não encontrado no marketplace")
        
        # Verificar se não é coming_soon
        if mcp.get("status") == "coming_soon":
            raise HTTPException(status_code=400, detail=f"MCP '{mcp_id}' ainda não está disponível")
        
        user_id = current_user.get("id")
        
        # Preparar manifesto para instalação
        manifest = {
            "manifest_version": "1.0",
            "id": mcp_id,
            "name": mcp.get("name"),
            "version": mcp.get("version"),
            "category": mcp.get("category"),
            "tier": mcp.get("tier"),
            "icon": mcp.get("icon"),
            "description": mcp.get("description"),
            "compatible_with": mcp.get("compatible_with", ["openslap"]),
            "permissions": mcp.get("permissions", []),
            "tools": mcp.get("tools", []),
            "agents": mcp.get("agents", []),
            "install_type": mcp.get("install_type", "builtin"),
            "endpoint": mcp.get("endpoint"),
            "auth": mcp.get("auth"),
            "credentials": request.credentials  # Salvar credenciais se fornecidas
        }
        
        # Instalar via MCP service
        from ..services.mcp_service import install_mcp_for_user
        result = await install_mcp_for_user(user_id, manifest)
        
        if result.get("success"):
            return {
                "success": True,
                "message": f"MCP '{mcp_id}' instalado com sucesso",
                "mcp": {
                    "id": mcp_id,
                    "name": mcp.get("name"),
                    "installed_at": result.get("installed_at"),
                    "credentials_configured": bool(request.credentials)
                }
            }
        else:
            raise HTTPException(
                status_code=400,
                detail=result.get("error", "Falha ao instalar MCP")
            )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao instalar MCP: {str(e)}")


@marketplace_router.post("/{mcp_id}/execute/{tool_name}")
async def execute_mcp_tool(
    mcp_id: str,
    tool_name: str,
    request: MCPExecuteRequest,
    credentials = Depends(security)
) -> Dict[str, Any]:
    """
    Executa uma ferramenta de um MCP instalado
    
    Path Parameters:
    - mcp_id: ID do MCP
    - tool_name: Nome da ferramenta a executar
    
    Body:
    - params: Parâmetros da ferramenta
    """
    try:
        token = credentials.credentials
        current_user = get_current_user(token)
        
        if not current_user:
            raise HTTPException(status_code=401, detail="Não autenticado")
        
        user_id = current_user.get("id")
        
        # Verificar se MCP está instalado
        from ..db import get_mcp_manifest
        mcp_manifest = get_mcp_manifest(user_id, mcp_id)
        
        if not mcp_manifest:
            raise HTTPException(status_code=404, detail=f"MCP '{mcp_id}' não instalado. Instale primeiro no marketplace.")
        
        # Verificar se tool existe
        available_tools = mcp_manifest.get("tools", [])
        if tool_name not in available_tools:
            raise HTTPException(
                status_code=400,
                detail=f"Tool '{tool_name}' não disponível. Ferramentas: {available_tools}"
            )
        
        # Obter executor do MCP
        executor = get_mcp_executor(mcp_id)
        if not executor:
            raise HTTPException(status_code=500, detail=f"Executor para MCP '{mcp_id}' não disponível")
        
        # Obter credenciais salvas
        saved_credentials = mcp_manifest.get("credentials", {})
        
        # Executar tool
        result = await executor.execute_tool(tool_name, request.params, saved_credentials)
        
        return {
            "success": result.get("success"),
            "mcp_id": mcp_id,
            "tool": tool_name,
            "result": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao executar tool: {str(e)}")


@marketplace_router.get("/{mcp_id}/tools")
async def list_mcp_tools(
    mcp_id: str,
    credentials = Depends(security)
) -> Dict[str, Any]:
    """
    Lista ferramentas disponíveis de um MCP
    
    Path Parameters:
    - mcp_id: ID do MCP
    """
    try:
        token = credentials.credentials
        current_user = get_current_user(token)
        
        if not current_user:
            raise HTTPException(status_code=401, detail="Não autenticado")
        
        mcp = get_mcp_details(mcp_id)
        
        if not mcp:
            raise HTTPException(status_code=404, detail=f"MCP '{mcp_id}' não encontrado")
        
        tools = mcp.get("tools", [])
        
        # Descrições das tools (expandir conforme necessário)
        tool_descriptions = {
            # Shopify
            "list_products": "Lista produtos da loja Shopify",
            "get_product": "Obtém detalhes de um produto específico",
            "create_product": "Cria um novo produto",
            "update_product": "Atualiza um produto existente",
            "update_price": "Atualiza o preço de uma variante",
            "update_inventory": "Atualiza o estoque de um produto",
            "list_orders": "Lista pedidos da loja",
            "get_order": "Obtém detalhes de um pedido",
            "list_customers": "Lista clientes da loja",
            "search_products": "Pesquisa produtos por nome",
            "get_sales_analytics": "Obtém analytics de vendas",
            "optimize_seo": "Analisa e sugere melhorias de SEO",
            # Stripe
            "create_payment_link": "Cria um link de pagamento",
            "create_product": "Cria um produto no Stripe",
            "create_price": "Cria um preço para um produto",
            "create_customer": "Cria um cliente",
            "list_charges": "Lista cobranças/transações",
            "get_charge": "Obtém detalhes de uma cobrança",
            "create_refund": "Cria um reembolso",
            "get_balance": "Obtém saldo da conta",
            "list_customers": "Lista clientes",
            "get_customer": "Obtém detalhes de um cliente",
            "update_customer": "Atualiza um cliente",
            "list_invoices": "Lista faturas",
            "get_invoice": "Obtém detalhes de uma fatura",
            "create_invoice": "Cria uma fatura",
            "create_invoice_item": "Adiciona item a fatura",
            "finalize_invoice": "Finaliza uma fatura draft",
            "pay_invoice": "Paga uma fatura",
            "void_invoice": "Cancela uma fatura",
            "list_refunds": "Lista reembolsos",
            "get_refund": "Obtém detalhes de reembolso",
            "list_disputes": "Lista disputas/chargebacks",
            "get_dispute": "Obtém detalhes de disputa",
            "close_dispute": "Fecha uma disputa",
            "create_coupon": "Cria cupom de desconto",
            "list_coupons": "Lista cupons",
            "delete_coupon": "Deleta um cupom",
            # Google AI Studio / Gemini
            "generate_content": "Gera texto com modelos Gemini",
            "stream_generate_content": "Gera texto em tempo real (streaming)",
            "generate_content_with_system_prompt": "Gera texto com instruções de sistema",
            "chat_completion": "Chat completion com histórico",
            "list_models": "Lista modelos Gemini disponíveis",
            "get_model": "Obtém detalhes de um modelo",
            "embed_content": "Gera embeddings para texto",
            "batch_embed_contents": "Gera embeddings em lote",
            "count_tokens": "Conta tokens em um texto",
            "upload_file": "Faz upload de arquivo",
            "list_files": "Lista arquivos enviados",
            "get_file": "Obtém detalhes de um arquivo",
            "delete_file": "Deleta um arquivo",
            "generate_image": "Gera imagens com Imagen",
            "analyze_image": "Analiza imagem com Gemini Vision",
            "analyze_video": "Analiza vídeo com Gemini",
            "analyze_audio": "Transcreve e analiza áudio",
            "list_tuned_models": "Lista modelos fine-tuned",
            "create_tuned_model": "Cria modelo fine-tuned",
            "get_tuned_model": "Obtém detalhes de modelo tuned",
            "set_generation_config": "Configura parâmetros de geração",
            "get_generation_config": "Obtém configuração atual"
        }
        
        tools_with_desc = [
            {
                "name": tool,
                "description": tool_descriptions.get(tool, f"Execute {tool}")
            }
            for tool in tools
        ]
        
        return {
            "success": True,
            "mcp_id": mcp_id,
            "mcp_name": mcp.get("name"),
            "total_tools": len(tools),
            "tools": tools_with_desc
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao listar tools: {str(e)}")


@marketplace_router.post("/{mcp_id}/credentials")
async def save_mcp_credentials(
    mcp_id: str,
    request: MCPCredentialsRequest,
    credentials = Depends(security)
) -> Dict[str, Any]:
    """
    Salva ou atualiza credenciais de um MCP instalado
    
    Path Parameters:
    - mcp_id: ID do MCP
    
    Body:
    - credentials: Credenciais da integração
    """
    try:
        token = credentials.credentials
        current_user = get_current_user(token)
        
        if not current_user:
            raise HTTPException(status_code=401, detail="Não autenticado")
        
        user_id = current_user.get("id")
        
        # Verificar se MCP está instalado
        from ..db import get_mcp_manifest, update_mcp_credentials
        mcp_manifest = get_mcp_manifest(user_id, mcp_id)
        
        if not mcp_manifest:
            raise HTTPException(status_code=404, detail=f"MCP '{mcp_id}' não instalado")
        
        # Atualizar credenciais (função hipotética - adicionar ao db.py se necessário)
        # update_mcp_credentials(user_id, mcp_id, request.credentials)
        
        # Por enquanto, atualizar no manifesto
        mcp_manifest["credentials"] = request.credentials
        from ..db import update_mcp_manifest
        update_mcp_manifest(user_id, mcp_id, mcp_manifest)
        
        return {
            "success": True,
            "message": f"Credenciais do MCP '{mcp_id}' atualizadas",
            "mcp_id": mcp_id,
            "credentials_keys": list(request.credentials.keys())
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao salvar credenciais: {str(e)}")


@marketplace_router.get("/featured/list")
async def get_featured_mcps(
    credentials = Depends(security)
) -> Dict[str, Any]:
    """
    Retorna MCPs em destaque no marketplace
    """
    try:
        token = credentials.credentials
        current_user = get_current_user(token)
        
        if not current_user:
            raise HTTPException(status_code=401, detail="Não autenticado")
        
        featured = marketplace_registry.get_featured()
        
        return {
            "success": True,
            "total": len(featured),
            "mcps": featured
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter featured: {str(e)}")


@marketplace_router.get("/new/list")
async def get_new_mcps(
    credentials = Depends(security)
) -> Dict[str, Any]:
    """
    Retorna MCPs novos no marketplace
    """
    try:
        token = credentials.credentials
        current_user = get_current_user(token)
        
        if not current_user:
            raise HTTPException(status_code=401, detail="Não autenticado")
        
        new_mcps = marketplace_registry.get_new()
        
        return {
            "success": True,
            "total": len(new_mcps),
            "mcps": new_mcps
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter novos MCPs: {str(e)}")
