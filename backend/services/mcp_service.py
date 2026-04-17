"""
MCP Service - Serviço de gestão de Model Context Protocol (MCP)
Gerencia instalação, ativação e integração de MCPs dinâmicos
"""

import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from ..db import (
    get_installed_mcps,
    get_active_mcps,
    install_mcp,
    toggle_mcp,
    uninstall_mcp,
    get_mcp_manifest
)

logger = logging.getLogger(__name__)


class MCPService:
    """Serviço de gestão de MCPs com validação e integração"""
    
    def __init__(self):
        self.mcp_cache = {}
        self.manifest_schema = self._define_manifest_schema()
        
    def _define_manifest_schema(self) -> Dict[str, Any]:
        """Define o schema esperado para manifestos MCP"""
        return {
            "required_fields": [
                "manifest_version",
                "id", 
                "name",
                "version",
                "category",
                "description"
            ],
            "optional_fields": [
                "tier",
                "icon",
                "compatible_with",
                "permissions",
                "tools",
                "agents",
                "install_type",
                "endpoint",
                "auth"
            ],
            "valid_categories": [
                "content_marketing",
                "development", 
                "productivity",
                "security",
                "cloud_services",
                "ai_ml",
                "social_communication",
                "entertainment_gaming",
                "mobile_development",
                "design_creativity",
                "custom"
            ],
            "valid_tiers": ["free", "pro", "enterprise"],
            "valid_install_types": ["mcp", "builtin", "plugin"]
        }
    
    def validate_manifest(self, manifest: Dict[str, Any]) -> Dict[str, Any]:
        """
        Valida um manifesto MCP contra o schema
        """
        errors = []
        warnings = []
        
        # Verificar campos obrigatórios
        for field in self.manifest_schema["required_fields"]:
            if field not in manifest:
                errors.append(f"Campo obrigatório ausente: {field}")
        
        # Validar categoria
        if "category" in manifest:
            if manifest["category"] not in self.manifest_schema["valid_categories"]:
                errors.append(f"Categoria inválida: {manifest['category']}")
        
        # Validar compatible_with (CRÍTICO)
        if "compatible_with" in manifest:
            compatible_with = manifest["compatible_with"]
            if not isinstance(compatible_with, list):
                errors.append("compatible_with deve ser uma lista")
            elif "openslap" not in compatible_with:
                errors.append("MCP não é compatível com Open Slap! (openslap não está em compatible_with)")
        else:
            warnings.append("Campo compatible_with ausente - assumindo compatibilidade apenas com openslap")
        
        # Validar tier se presente
        if "tier" in manifest:
            if manifest["tier"] not in self.manifest_schema["valid_tiers"]:
                warnings.append(f"Tier não reconhecido: {manifest['tier']}")
        
        # Validar install_type se presente
        if "install_type" in manifest:
            if manifest["install_type"] not in self.manifest_schema["valid_install_types"]:
                warnings.append(f"Install type não reconhecido: {manifest['install_type']}")
        
        # Validar formato de versão
        if "version" in manifest:
            version = manifest["version"]
            if not isinstance(version, str) or not version.count(".") >= 1:
                warnings.append(f"Formato de versão incomum: {version}")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }
    
    async def install_mcp_for_user(
        self,
        user_id: int,
        manifest: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Instala um MCP para um usuário com validação completa
        """
        try:
            # Validar manifesto
            validation = self.validate_manifest(manifest)
            if not validation["valid"]:
                return {
                    "success": False,
                    "error": "Manifesto inválido",
                    "validation_errors": validation["errors"]
                }
            
            mcp_id = manifest["id"]
            
            # Verificar se já está instalado
            existing = get_mcp_manifest(user_id, mcp_id)
            if existing:
                return {
                    "success": False,
                    "error": f"MCP '{mcp_id}' já está instalado",
                    "installed_at": existing.get("installed_at")
                }
            
            # Instalar no banco
            success = install_mcp(user_id, mcp_id, manifest)
            
            if success:
                # Limpar cache do usuário
                if user_id in self.mcp_cache:
                    del self.mcp_cache[user_id]
                
                logger.info(f"MCP '{mcp_id}' instalado para usuário {user_id}")
                
                return {
                    "success": True,
                    "mcp_id": mcp_id,
                    "manifest": manifest,
                    "installed_at": datetime.utcnow().isoformat(),
                    "warnings": validation["warnings"]
                }
            else:
                return {
                    "success": False,
                    "error": "Falha ao instalar MCP no banco de dados"
                }
                
        except Exception as e:
            logger.error(f"Erro ao instalar MCP: {str(e)}")
            return {
                "success": False,
                "error": f"Erro interno: {str(e)}"
            }
    
    async def get_user_mcps(
        self,
        user_id: int,
        active_only: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Obtém MCPs do usuário com cache e metadados
        """
        try:
            # Verificar cache
            cache_key = f"{user_id}_{'active' if active_only else 'all'}"
            if cache_key in self.mcp_cache:
                cache_entry = self.mcp_cache[cache_key]
                if (datetime.utcnow() - cache_entry["cached_at"]).seconds < 300:  # 5 min
                    return cache_entry["mcps"]
            
            # Obter do banco
            if active_only:
                mcps = get_active_mcps(user_id)
            else:
                mcps = get_installed_mcps(user_id)
            
            # Enriquecer com metadados
            enriched_mcps = []
            for mcp in mcps:
                manifest = mcp.get("manifest", {})
                enriched_mcp = {
                    "id": mcp.get("id"),
                    "manifest": manifest,
                    "installed_at": mcp.get("installed_at"),
                    "is_active": mcp.get("is_active", True)
                }
                
                # Adicionar metadados calculados
                enriched_mcp.update({
                    "display_name": manifest.get("name", mcp.get("id")),
                    "category_display": self._get_category_display(manifest.get("category")),
                    "tier_display": manifest.get("tier", "free").title(),
                    "permissions_count": len(manifest.get("permissions", [])),
                    "tools_count": len(manifest.get("tools", [])),
                    "agents_count": len(manifest.get("agents", []))
                })
                
                enriched_mcps.append(enriched_mcp)
            
            # Cache para próximas consultas
            self.mcp_cache[cache_key] = {
                "mcps": enriched_mcps,
                "cached_at": datetime.utcnow()
            }
            
            return enriched_mcps
            
        except Exception as e:
            logger.error(f"Erro ao obter MCPs do usuário: {str(e)}")
            return []
    
    async def toggle_mcp_for_user(
        self,
        user_id: int,
        mcp_id: str,
        is_active: bool
    ) -> Dict[str, Any]:
        """
        Ativa/desativa um MCP para o usuário
        """
        try:
            # Verificar se MCP existe
            manifest = get_mcp_manifest(user_id, mcp_id)
            if not manifest:
                return {
                    "success": False,
                    "error": f"MCP '{mcp_id}' não encontrado"
                }
            
            # Toggle no banco
            success = toggle_mcp(user_id, mcp_id, is_active)
            
            if success:
                # Limpar cache MCP service
                for key in list(self.mcp_cache.keys()):
                    if key.startswith(f"{user_id}_"):
                        del self.mcp_cache[key]
                
                # Limpar cache SkillService (CRÍTICO)
                from .skill_service import skill_service
                if user_id in skill_service.skill_cache:
                    del skill_service.skill_cache[user_id]
                
                # Se desativando, remover do registry de skills
                if not is_active:
                    user_prefix = f"user_{user_id}_"
                    skill_id = f"{user_prefix}{mcp_id}"
                    if skill_id in skill_service.mcp_registry:
                        del skill_service.mcp_registry[skill_id]
                        logger.info(f"MCP '{mcp_id}' removido do registry de skills (desativado)")
                
                logger.info(f"MCP '{mcp_id}' {'ativado' if is_active else 'desativado'} para usuário {user_id}")
                
                return {
                    "success": True,
                    "mcp_id": mcp_id,
                    "is_active": is_active,
                    "manifest": manifest
                }
            else:
                return {
                    "success": False,
                    "error": "Falha ao atualizar estado do MCP"
                }
                
        except Exception as e:
            logger.error(f"Erro ao fazer toggle do MCP: {str(e)}")
            return {
                "success": False,
                "error": f"Erro interno: {str(e)}"
            }
    
    async def uninstall_mcp_for_user(
        self,
        user_id: int,
        mcp_id: str
    ) -> Dict[str, Any]:
        """
        Remove um MCP instalado
        """
        try:
            # Verificar se MCP existe
            manifest = get_mcp_manifest(user_id, mcp_id)
            if not manifest:
                return {
                    "success": False,
                    "error": f"MCP '{mcp_id}' não encontrado"
                }
            
            # Remover do banco
            success = uninstall_mcp(user_id, mcp_id)
            
            if success:
                # Limpar cache
                for key in list(self.mcp_cache.keys()):
                    if key.startswith(f"{user_id}_"):
                        del self.mcp_cache[key]
                
                logger.info(f"MCP '{mcp_id}' removido para usuário {user_id}")
                
                return {
                    "success": True,
                    "mcp_id": mcp_id,
                    "manifest": manifest
                }
            else:
                return {
                    "success": False,
                    "error": "Falha ao remover MCP"
                }
                
        except Exception as e:
            logger.error(f"Erro ao remover MCP: {str(e)}")
            return {
                "success": False,
                "error": f"Erro interno: {str(e)}"
            }
    
    async def get_mcp_analytics(
        self,
        user_id: int
    ) -> Dict[str, Any]:
        """
        Retorna analytics detalhados dos MCPs do usuário
        """
        try:
            all_mcps = await self.get_user_mcps(user_id, active_only=False)
            active_mcps = await self.get_user_mcps(user_id, active_only=True)
            
            # Estatísticas básicas
            total_mcps = len(all_mcps)
            active_count = len(active_mcps)
            inactive_count = total_mcps - active_count
            
            # Análise por categoria
            categories = {}
            for mcp in all_mcps:
                category = mcp.get("manifest", {}).get("category", "unknown")
                if category not in categories:
                    categories[category] = {"total": 0, "active": 0}
                categories[category]["total"] += 1
                if mcp.get("is_active"):
                    categories[category]["active"] += 1
            
            # Análise por tier
            tiers = {}
            for mcp in all_mcps:
                tier = mcp.get("manifest", {}).get("tier", "free")
                if tier not in tiers:
                    tiers[tier] = 0
                tiers[tier] += 1
            
            # Instalações por mês (últimos 6 meses)
            installations_by_month = {}
            for mcp in all_mcps:
                installed_at = mcp.get("installed_at")
                if installed_at:
                    # Simplificar para análise - formatar como YYYY-MM
                    month_key = installed_at[:7] if len(installed_at) > 7 else installed_at
                    if month_key not in installations_by_month:
                        installations_by_month[month_key] = 0
                    installations_by_month[month_key] += 1
            
            # Top permissões
            all_permissions = []
            for mcp in all_mcps:
                permissions = mcp.get("manifest", {}).get("permissions", [])
                all_permissions.extend(permissions)
            
            permission_counts = {}
            for permission in all_permissions:
                if permission not in permission_counts:
                    permission_counts[permission] = 0
                permission_counts[permission] += 1
            
            return {
                "total_mcps": total_mcps,
                "active_mcps": active_count,
                "inactive_mcps": inactive_count,
                "categories": categories,
                "tiers": tiers,
                "installations_by_month": installations_by_month,
                "top_permissions": dict(sorted(permission_counts.items(), key=lambda x: x[1], reverse=True)[:10]),
                "last_updated": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Erro ao obter analytics de MCPs: {str(e)}")
            return {"error": str(e)}
    
    def _get_category_display(self, category: Optional[str]) -> str:
        """Retorna nome amigável da categoria"""
        category_names = {
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
        return category_names.get(category, category or "Desconhecida")


# Instância global do serviço
mcp_service = MCPService()


# Funções de compatibilidade com código existente
async def install_mcp_for_user(user_id: int, manifest: Dict[str, Any]) -> Dict[str, Any]:
    """Função wrapper para compatibilidade"""
    return await mcp_service.install_mcp_for_user(user_id, manifest)


async def get_user_mcps(user_id: int, active_only: bool = False) -> List[Dict[str, Any]]:
    """Função wrapper para compatibilidade"""
    return await mcp_service.get_user_mcps(user_id, active_only)


async def toggle_mcp_for_user(user_id: int, mcp_id: str, is_active: bool) -> Dict[str, Any]:
    """Função wrapper para compatibilidade"""
    return await mcp_service.toggle_mcp_for_user(user_id, mcp_id, is_active)


async def uninstall_mcp_for_user(user_id: int, mcp_id: str) -> Dict[str, Any]:
    """Função wrapper para compatibilidade"""
    return await mcp_service.uninstall_mcp_for_user(user_id, mcp_id)


async def get_mcp_analytics(user_id: int) -> Dict[str, Any]:
    """Função wrapper para compatibilidade"""
    return await mcp_service.get_mcp_analytics(user_id)
