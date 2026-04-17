"""
MCP Registry Routes - Endpoints para gestão de MCPs
Registry dinâmico de Model Context Protocol
"""

from fastapi import APIRouter, HTTPException, Depends, Body
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from ..deps import security
from ..main_auth import get_current_user
from ..services.mcp_service import (
    install_mcp_for_user,
    get_user_mcps,
    toggle_mcp_for_user,
    uninstall_mcp_for_user,
    get_mcp_analytics
)

mcp_registry_router = APIRouter(prefix="/api/mcps", tags=["mcp-registry"])


# Pydantic Models
class MCPManifest(BaseModel):
    """Model para validação de manifestos MCP"""
    manifest_version: str = Field(..., description="Versão do formato do manifesto")
    id: str = Field(..., description="ID único do MCP")
    name: str = Field(..., description="Nome do MCP")
    version: str = Field(..., description="Versão do MCP")
    category: str = Field(..., description="Categoria do MCP")
    tier: Optional[str] = Field("free", description="Tier (free/pro/enterprise)")
    icon: Optional[str] = Field(None, description="Emoji ou ícone")
    description: str = Field(..., description="Descrição do MCP")
    compatible_with: Optional[List[str]] = Field(None, description="Sistemas compatíveis")
    permissions: Optional[List[str]] = Field([], description="Permissões necessárias")
    tools: Optional[List[str]] = Field([], description="Ferramentas disponíveis")
    agents: Optional[List[str]] = Field([], description="Agentes disponíveis")
    install_type: Optional[str] = Field("mcp", description="Tipo de instalação")
    endpoint: Optional[str] = Field(None, description="Endpoint do MCP")
    auth: Optional[str] = Field(None, description="Tipo de autenticação")


class MCPInstallRequest(BaseModel):
    """Request para instalação de MCP"""
    manifest: MCPManifest = Field(..., description="Manifesto do MCP")


class MCPToggleRequest(BaseModel):
    """Request para ativar/desativar MCP"""
    is_active: bool = Field(..., description="Estado desejado")


# Endpoints
@mcp_registry_router.get("/")
async def list_mcps(
    active_only: bool = False,
    credentials = Depends(security)
) -> Dict[str, Any]:
    """
    Lista MCPs instalados do usuário
    
    Query Parameters:
    - active_only: Se True, retorna apenas MCPs ativos
    """
    try:
        token = credentials.credentials
        current_user = get_current_user(token)
        
        if not current_user:
            raise HTTPException(status_code=401, detail="Não autenticado")
        
        user_id = current_user.get("id")
        mcps = await get_user_mcps(user_id, active_only=active_only)
        
        return {
            "success": True,
            "user_id": user_id,
            "active_only": active_only,
            "total_mcps": len(mcps),
            "mcps": mcps
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao listar MCPs: {str(e)}")


@mcp_registry_router.get("/analytics")
async def get_mcps_analytics(
    credentials = Depends(security)
) -> Dict[str, Any]:
    """
    Retorna analytics detalhados dos MCPs do usuário
    """
    try:
        token = credentials.credentials
        current_user = get_current_user(token)
        
        if not current_user:
            raise HTTPException(status_code=401, detail="Não autenticado")
        
        user_id = current_user.get("id")
        analytics = await get_mcp_analytics(user_id)
        
        return {
            "success": True,
            "user_id": user_id,
            "analytics": analytics
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter analytics: {str(e)}")


@mcp_registry_router.post("/install")
async def install_mcp(
    request: MCPInstallRequest,
    credentials = Depends(security)
) -> Dict[str, Any]:
    """
    Instala um novo MCP para o usuário
    
    Body:
    - manifest: Manifesto completo do MCP
    """
    try:
        token = credentials.credentials
        current_user = get_current_user(token)
        
        if not current_user:
            raise HTTPException(status_code=401, detail="Não autenticado")
        
        user_id = current_user.get("id")
        manifest_dict = request.manifest.dict()
        
        result = await install_mcp_for_user(user_id, manifest_dict)
        
        if result.get("success"):
            return {
                "success": True,
                "message": f"MCP '{request.manifest.id}' instalado com sucesso",
                "mcp": result
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


@mcp_registry_router.patch("/{mcp_id}/toggle")
async def toggle_mcp(
    mcp_id: str,
    request: MCPToggleRequest,
    credentials = Depends(security)
) -> Dict[str, Any]:
    """
    Ativa ou desativa um MCP instalado
    
    Path Parameters:
    - mcp_id: ID do MCP
    
    Body:
    - is_active: Estado desejado
    """
    try:
        token = credentials.credentials
        current_user = get_current_user(token)
        
        if not current_user:
            raise HTTPException(status_code=401, detail="Não autenticado")
        
        user_id = current_user.get("id")
        result = await toggle_mcp_for_user(user_id, mcp_id, request.is_active)
        
        if result.get("success"):
            action = "ativado" if request.is_active else "desativado"
            return {
                "success": True,
                "message": f"MCP '{mcp_id}' {action} com sucesso",
                "mcp": result
            }
        else:
            raise HTTPException(
                status_code=404,
                detail=result.get("error", "MCP não encontrado")
            )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao atualizar MCP: {str(e)}")


@mcp_registry_router.delete("/{mcp_id}")
async def uninstall_mcp(
    mcp_id: str,
    credentials = Depends(security)
) -> Dict[str, Any]:
    """
    Remove um MCP instalado
    
    Path Parameters:
    - mcp_id: ID do MCP a ser removido
    """
    try:
        token = credentials.credentials
        current_user = get_current_user(token)
        
        if not current_user:
            raise HTTPException(status_code=401, detail="Não autenticado")
        
        user_id = current_user.get("id")
        result = await uninstall_mcp_for_user(user_id, mcp_id)
        
        if result.get("success"):
            return {
                "success": True,
                "message": f"MCP '{mcp_id}' removido com sucesso",
                "mcp": result
            }
        else:
            raise HTTPException(
                status_code=404,
                detail=result.get("error", "MCP não encontrado")
            )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao remover MCP: {str(e)}")


@mcp_registry_router.get("/{mcp_id}")
async def get_mcp_details(
    mcp_id: str,
    credentials = Depends(security)
) -> Dict[str, Any]:
    """
    Obtém detalhes de um MCP específico
    
    Path Parameters:
    - mcp_id: ID do MCP
    """
    try:
        token = credentials.credentials
        current_user = get_current_user(token)
        
        if not current_user:
            raise HTTPException(status_code=401, detail="Não autenticado")
        
        user_id = current_user.get("id")
        
        # Obter todos os MCPs e encontrar o específico
        mcps = await get_user_mcps(user_id, active_only=False)
        target_mcp = None
        
        for mcp in mcps:
            if mcp.get("id") == mcp_id:
                target_mcp = mcp
                break
        
        if not target_mcp:
            raise HTTPException(status_code=404, detail=f"MCP '{mcp_id}' não encontrado")
        
        return {
            "success": True,
            "mcp": target_mcp
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter detalhes do MCP: {str(e)}")


@mcp_registry_router.get("/categories/list")
async def list_categories() -> Dict[str, Any]:
    """
    Lista todas as categorias disponíveis para MCPs
    """
    try:
        categories = {
            "content_marketing": "Conteúdo e Marketing",
            "development": "Desenvolvimento",
            "productivity": "Produtividade",
            "security": "Segurança",
            "cloud_services": "Serviços Cloud",
            "ai_ml": "IA e Machine Learning",
            "social_communication": "Social e Comunicação",
            "entertainment_gaming": "Entretenimento e Games",
            "mobile_development": "Desenvolvimento Mobile",
            "design_creativity": "Design e Criatividade",
            "custom": "Custom"
        }
        
        return {
            "success": True,
            "categories": categories,
            "total_categories": len(categories)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao listar categorias: {str(e)}")


@mcp_registry_router.post("/validate")
async def validate_manifest(
    manifest: MCPManifest
) -> Dict[str, Any]:
    """
    Valida um manifesto MCP sem instalá-lo
    
    Body:
    - manifest: Manifesto a ser validado
    """
    try:
        from ..services.mcp_service import mcp_service
        
        manifest_dict = manifest.dict()
        validation = mcp_service.validate_manifest(manifest_dict)
        
        return {
            "success": True,
            "valid": validation["valid"],
            "errors": validation["errors"],
            "warnings": validation["warnings"],
            "manifest": manifest_dict
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao validar manifesto: {str(e)}")
