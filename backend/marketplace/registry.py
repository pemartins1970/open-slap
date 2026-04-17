"""
Marketplace Registry - Registro de MCPs disponíveis
Inspirado nos toolkits da Shopify e Stripe

Este módulo mantém o catálogo de MCPs que podem ser instalados pelos usuários,
incluindo integrações pré-construídas para serviços populares.
"""

from typing import Dict, Any, List, Optional
import logging

from ..integrations.shopify_mcp import shopify_mcp
from ..integrations.stripe_mcp import stripe_mcp
from ..integrations.google_aistudio_mcp import google_aistudio_mcp

logger = logging.getLogger(__name__)


class MarketplaceRegistry:
    """
    Registro de MCPs disponíveis no marketplace
    """
    
    def __init__(self):
        self._mcps: Dict[str, Dict[str, Any]] = {}
        self._register_builtin_mcps()
    
    def _register_builtin_mcps(self):
        """Registra MCPs built-in disponíveis para instalação"""
        
        # Shopify MCP
        shopify_manifest = shopify_mcp.get_manifest()
        self._mcps["shopify"] = {
            **shopify_manifest,
            "installed_count": 0,
            "rating": 4.8,
            "reviews": 124,
            "author": "OpenSlap Team",
            "author_url": "https://openslap.dev",
            "documentation_url": "https://shopify.dev/docs/apps/build/ai-toolkit",
            "pricing": {
                "free_tier": {
                    "features": ["Listar produtos", "Consultar pedidos", "Ver analytics básico"],
                    "limits": "100 chamadas/mês"
                },
                "pro_tier": {
                    "price": "$19/mês",
                    "features": ["Todas as ferramentas", "Atualização de preços", "Gestão de inventário", "SEO", "Prioridade de suporte"],
                    "limits": "Ilimitado"
                }
            },
            "tags": ["e-commerce", "shopify", "vendas", "produtos", "analytics"],
            "featured": True,
            "new": False
        }
        
        # Stripe MCP
        stripe_manifest = stripe_mcp.get_manifest()
        self._mcps["stripe"] = {
            **stripe_manifest,
            "installed_count": 0,
            "rating": 4.9,
            "reviews": 89,
            "author": "OpenSlap Team",
            "author_url": "https://openslap.dev",
            "documentation_url": "https://docs.stripe.com/agents",
            "pricing": {
                "free_tier": {
                    "features": ["Criar Payment Links", "Listar cobranças", "Consultar saldo"],
                    "limits": "50 transações/mês"
                },
                "pro_tier": {
                    "price": "$29/mês",
                    "features": ["Todas as ferramentas", "Reembolsos", "Faturas", "Disputas", "Webhooks", "API prioritária"],
                    "limits": "Ilimitado"
                }
            },
            "tags": ["pagamentos", "stripe", "faturamento", "assinaturas", "financeiro"],
            "featured": True,
            "new": True
        }
        
        # Google AI Studio MCP - REFORÇO SUPREMO!
        gemini_manifest = google_aistudio_mcp.get_manifest()
        self._mcps["google_aistudio"] = {
            **gemini_manifest,
            "installed_count": 0,
            "rating": 5.0,
            "reviews": 256,
            "author": "OpenSlap Team",
            "author_url": "https://openslap.dev",
            "documentation_url": "https://ai.google.dev/api",
            "pricing": {
                "free_tier": {
                    "features": [
                        "Geração de texto com Gemini Flash",
                        "Chat completion",
                        "Listar modelos",
                        "Até 60 req/min"
                    ],
                    "limits": "60 RPM, 1.000.000 tokens/mês"
                },
                "pro_tier": {
                    "price": "$39/mês",
                    "features": [
                        "Todos os modelos Gemini (Pro, Flash, Ultra)",
                        "Streaming de respostas",
                        "Embeddings",
                        "Análise multimodal (imagem, vídeo, áudio)",
                        "Fine-tuning de modelos",
                        "Upload de arquivos",
                        "Geração de imagens (Imagen)",
                        "API rate limits aumentados",
                        "Suporte prioritário"
                    ],
                    "limits": "Ilimitado"
                }
            },
            "tags": [
                "ai",
                "gemini",
                "google",
                "llm",
                "geração-texto",
                "embeddings",
                "multimodal",
                "fine-tuning",
                "vision"
            ],
            "featured": True,
            "new": False,
            "badge": "🏆 ARTILHARIA PRINCIPAL"
        }
        
        # Placeholder MCPs para futuras integrações
        self._register_future_mcps()
        
        logger.info(f"Marketplace registry inicializado com {len(self._mcps)} MCPs")
    
    def _register_future_mcps(self):
        """Registra MCPs planejados para desenvolvimento futuro"""
        
        future_mcps = [
            {
                "id": "hubspot",
                "name": "HubSpot",
                "version": "1.0.0",
                "category": "content_marketing",
                "tier": "pro",
                "icon": "🎯",
                "description": "CRM e marketing automation. Gerencie leads, pipelines e campanhas.",
                "compatible_with": ["openslap"],
                "permissions": ["hubspot:contacts:read", "hubspot:deals:write"],
                "tools": ["create_contact", "update_deal", "list_pipelines", "send_email"],
                "agents": ["crm_specialist", "sales_rep"],
                "install_type": "builtin",
                "status": "coming_soon",
                "tags": ["crm", "marketing", "leads", "sales"]
            },
            {
                "id": "slack",
                "name": "Slack",
                "version": "1.0.0",
                "category": "social_communication",
                "tier": "free",
                "icon": "💬",
                "description": "Envie mensagens, gerencie canais e automatize notificações no Slack.",
                "compatible_with": ["openslap"],
                "permissions": ["slack:chat:write", "slack:channels:read"],
                "tools": ["send_message", "create_channel", "list_users", "get_channel_history"],
                "agents": ["notification_bot"],
                "install_type": "builtin",
                "status": "coming_soon",
                "tags": ["comunicação", "notificações", "chat", "automação"]
            },
            {
                "id": "github",
                "name": "GitHub",
                "version": "1.0.0",
                "category": "development",
                "tier": "pro",
                "icon": "🐙",
                "description": "Gerencie repositórios, issues, PRs e workflows do GitHub.",
                "compatible_with": ["openslap"],
                "permissions": ["github:repos:read", "github:issues:write"],
                "tools": ["create_issue", "list_prs", "merge_pr", "get_repo_info", "create_branch"],
                "agents": ["devops_engineer", "code_reviewer"],
                "install_type": "builtin",
                "status": "coming_soon",
                "tags": ["git", "repositórios", "issues", "devops"]
            },
            {
                "id": "notion",
                "name": "Notion",
                "version": "1.0.0",
                "category": "productivity",
                "tier": "pro",
                "icon": "📝",
                "description": "Crie e edite páginas, databases e wikis no Notion.",
                "compatible_with": ["openslap"],
                "permissions": ["notion:pages:write", "notion:databases:read"],
                "tools": ["create_page", "update_page", "query_database", "create_database"],
                "agents": ["documentation_writer", "knowledge_manager"],
                "install_type": "builtin",
                "status": "coming_soon",
                "tags": ["documentação", "wiki", "colaboração", "produtividade"]
            },
            {
                "id": "airtable",
                "name": "Airtable",
                "version": "1.0.0",
                "category": "productivity",
                "tier": "pro",
                "icon": "📊",
                "description": "Base de dados relacional e spreadsheets avançadas.",
                "compatible_with": ["openslap"],
                "permissions": ["airtable:records:write", "airtable:bases:read"],
                "tools": ["create_record", "update_record", "list_records", "get_base_schema"],
                "agents": ["data_analyst"],
                "install_type": "builtin",
                "status": "coming_soon",
                "tags": ["database", "spreadsheets", "dados", "planilhas"]
            },
            {
                "id": "salesforce",
                "name": "Salesforce",
                "version": "1.0.0",
                "category": "content_marketing",
                "tier": "enterprise",
                "icon": "☁️",
                "description": "CRM enterprise. Gestão completa de vendas e relacionamento.",
                "compatible_with": ["openslap"],
                "permissions": ["salesforce:sobjects:write"],
                "tools": ["create_lead", "update_opportunity", "query_soql", "get_report"],
                "agents": ["sales_manager", "enterprise_specialist"],
                "install_type": "builtin",
                "status": "coming_soon",
                "tags": ["crm", "enterprise", "sales", "b2b"]
            },
            {
                "id": "zapier",
                "name": "Zapier",
                "version": "1.0.0",
                "category": "productivity",
                "tier": "pro",
                "icon": "⚡",
                "description": "Automação de workflows entre 5000+ apps.",
                "compatible_with": ["openslap"],
                "permissions": ["zapier:zaps:write", "zapier:apps:read"],
                "tools": ["create_zap", "trigger_zap", "list_apps", "get_zap_history"],
                "agents": ["automation_specialist"],
                "install_type": "builtin",
                "status": "coming_soon",
                "tags": ["automação", "workflows", "integrações", "zaps"]
            },
            {
                "id": "twilio",
                "name": "Twilio",
                "version": "1.0.0",
                "category": "social_communication",
                "tier": "pro",
                "icon": "📞",
                "description": "SMS, WhatsApp e chamadas telefônicas via API.",
                "compatible_with": ["openslap"],
                "permissions": ["twilio:sms:write", "twilio:calls:write"],
                "tools": ["send_sms", "make_call", "list_messages", "get_message_status"],
                "agents": ["communication_bot", "support_agent"],
                "install_type": "builtin",
                "status": "coming_soon",
                "tags": ["sms", "whatsapp", "telefone", "comunicação"]
            }
        ]
        
        for mcp in future_mcps:
            self._mcps[mcp["id"]] = {
                **mcp,
                "installed_count": 0,
                "rating": None,
                "reviews": 0,
                "author": "OpenSlap Team",
                "author_url": "https://openslap.dev",
                "documentation_url": None,
                "pricing": {
                    "free_tier": None,
                    "pro_tier": None
                },
                "featured": False,
                "new": True
            }
    
    def get_all_mcps(self, include_coming_soon: bool = False) -> List[Dict[str, Any]]:
        """
        Retorna todos os MCPs disponíveis no marketplace
        
        Args:
            include_coming_soon: Se True, inclui MCPs ainda em desenvolvimento
        """
        mcps = []
        for mcp_id, mcp_data in self._mcps.items():
            if mcp_data.get("status") == "coming_soon" and not include_coming_soon:
                continue
            mcps.append({
                "id": mcp_id,
                **mcp_data
            })
        return mcps
    
    def get_mcp(self, mcp_id: str) -> Optional[Dict[str, Any]]:
        """Retorna detalhes de um MCP específico"""
        if mcp_id in self._mcps:
            return {
                "id": mcp_id,
                **self._mcps[mcp_id]
            }
        return None
    
    def get_mcp_instance(self, mcp_id: str) -> Optional[Any]:
        """Retorna a instância do MCP para execução"""
        if mcp_id == "shopify":
            return shopify_mcp
        elif mcp_id == "stripe":
            return stripe_mcp
        elif mcp_id == "google_aistudio":
            return google_aistudio_mcp
        return None
    
    def get_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Retorna MCPs de uma categoria específica"""
        return [
            {"id": mcp_id, **mcp_data}
            for mcp_id, mcp_data in self._mcps.items()
            if mcp_data.get("category") == category and mcp_data.get("status") != "coming_soon"
        ]
    
    def get_featured(self) -> List[Dict[str, Any]]:
        """Retorna MCPs em destaque"""
        return [
            {"id": mcp_id, **mcp_data}
            for mcp_id, mcp_data in self._mcps.items()
            if mcp_data.get("featured") and mcp_data.get("status") != "coming_soon"
        ]
    
    def get_new(self) -> List[Dict[str, Any]]:
        """Retorna MCPs novos"""
        return [
            {"id": mcp_id, **mcp_data}
            for mcp_id, mcp_data in self._mcps.items()
            if mcp_data.get("new") and mcp_data.get("status") != "coming_soon"
        ]
    
    def search(self, query: str) -> List[Dict[str, Any]]:
        """Pesquisa MCPs por nome, descrição ou tags"""
        query = query.lower()
        results = []
        
        for mcp_id, mcp_data in self._mcps.items():
            if mcp_data.get("status") == "coming_soon":
                continue
                
            searchable_text = f"{mcp_data.get('name', '')} {mcp_data.get('description', '')} {' '.join(mcp_data.get('tags', []))}".lower()
            
            if query in searchable_text:
                results.append({"id": mcp_id, **mcp_data})
        
        return results
    
    def get_categories(self) -> List[Dict[str, Any]]:
        """Retorna lista de categorias com contagem de MCPs"""
        categories = {}
        
        for mcp_id, mcp_data in self._mcps.items():
            if mcp_data.get("status") == "coming_soon":
                continue
                
            cat = mcp_data.get("category", "custom")
            if cat not in categories:
                categories[cat] = {"count": 0, "mcps": []}
            categories[cat]["count"] += 1
            categories[cat]["mcps"].append(mcp_id)
        
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
        
        return [
            {
                "id": cat_id,
                "name": category_names.get(cat_id, cat_id),
                "count": data["count"],
                "mcps": data["mcps"]
            }
            for cat_id, data in categories.items()
        ]
    
    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas do marketplace"""
        available = [m for m in self._mcps.values() if m.get("status") != "coming_soon"]
        coming_soon = [m for m in self._mcps.values() if m.get("status") == "coming_soon"]
        
        return {
            "total_mcps": len(self._mcps),
            "available_now": len(available),
            "coming_soon": len(coming_soon),
            "featured": len([m for m in available if m.get("featured")]),
            "free_tier": len([m for m in available if m.get("tier") == "free"]),
            "pro_tier": len([m for m in available if m.get("tier") == "pro"]),
            "enterprise_tier": len([m for m in available if m.get("tier") == "enterprise"])
        }


# Instância global
marketplace_registry = MarketplaceRegistry()


# Funções de conveniência
def get_available_mcps(include_coming_soon: bool = False) -> List[Dict[str, Any]]:
    """Retorna todos os MCPs disponíveis"""
    return marketplace_registry.get_all_mcps(include_coming_soon)


def get_mcp_details(mcp_id: str) -> Optional[Dict[str, Any]]:
    """Retorna detalhes de um MCP específico"""
    return marketplace_registry.get_mcp(mcp_id)


def get_mcp_executor(mcp_id: str) -> Optional[Any]:
    """Retorna o executor de um MCP para execução de tools"""
    return marketplace_registry.get_mcp_instance(mcp_id)
