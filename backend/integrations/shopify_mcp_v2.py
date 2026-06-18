"""
Shopify MCP - Model Context Protocol para integração com Shopify
Baseado no Shopify AI Toolkit (https://shopify.dev/docs/apps/build/ai-toolkit)

Funcionalidades:
- Gerenciamento de produtos (CRUD)
- Atualização de preços e inventário
- Consultas de pedidos e clientes
- Análise de dados de vendas
- SEO e otimização de listings
"""

import json
import logging
from typing import Dict, Any, List, Optional, AsyncGenerator
from datetime import datetime
import aiohttp

logger = logging.getLogger(__name__)


class ShopifyMCP:
    """
    MCP para integração com Shopify
    Permite agentes gerenciarem lojas Shopify via API
    """
    
    def __init__(self):
        self.name = "shopify"
        self.display_name = "Shopify"
        self.version = "1.0.0"
        self.description = "Gerencie sua loja Shopify - produtos, pedidos, preços e SEO"
        self.icon = "🛒"
        self.category = "ecommerce"
        self.tier = "pro"
        
    def get_manifest(self) -> Dict[str, Any]:
        """Retorna o manifesto do MCP para registro"""
        return {
            "manifest_version": "1.0",
            "id": self.name,
            "name": self.display_name,
            "version": self.version,
            "category": "content_marketing",
            "tier": self.tier,
            "icon": self.icon,
            "description": self.description,
            "compatible_with": ["openslap"],
            "permissions": [
                "shopify:products:read",
                "shopify:products:write",
                "shopify:orders:read",
                "shopify:customers:read",
                "shopify:inventory:write",
                "shopify:analytics:read"
            ],
            "tools": [
                "list_products",
                "get_product",
                "create_product",
                "update_product",
                "update_price",
                "update_inventory",
                "list_orders",
                "get_order",
                "list_customers",
                "search_products",
                "get_sales_analytics",
                "optimize_seo"
            ],
            "agents": ["shopify_expert", "seo_specialist", "inventory_manager"],
            "install_type": "builtin",
            "endpoint": None,
            "auth": "api_key"
        }
    
    async def execute_tool(
        self,
        tool_name: str,
        params: Dict[str, Any],
        credentials: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Executa uma ferramenta do MCP Shopify
        
        Args:
            tool_name: Nome da ferramenta a executar
            params: Parâmetros da ferramenta
            credentials: {shop_domain, access_token}
        """
        shop_domain = credentials.get("shop_domain")
        access_token = credentials.get("access_token")
        
        if not shop_domain or not access_token:
            return {
                "success": False,
                "error": "Credenciais Shopify não configuradas"
            }
        
        base_url = f"https://{shop_domain}/admin/api/2024-01"
        headers = {
            "X-Shopify-Access-Token": access_token,
            "Content-Type": "application/json"
        }
        
        try:
            if tool_name == "list_products":
                return await self._list_products(base_url, headers, params)
            elif tool_name == "get_product":
                return await self._get_product(base_url, headers, params)
            elif tool_name == "create_product":
                return await self._create_product(base_url, headers, params)
            elif tool_name == "update_product":
                return await self._update_product(base_url, headers, params)
            elif tool_name == "update_price":
                return await self._update_price(base_url, headers, params)
            elif tool_name == "update_inventory":
                return await self._update_inventory(base_url, headers, params)
            elif tool_name == "list_orders":
                return await self._list_orders(base_url, headers, params)
            elif tool_name == "get_order":
                return await self._get_order(base_url, headers, params)
            elif tool_name == "list_customers":
                return await self._list_customers(base_url, headers, params)
            elif tool_name == "search_products":
                return await self._search_products(base_url, headers, params)
            elif tool_name == "get_sales_analytics":
                return await self._get_sales_analytics(base_url, headers, params)
            elif tool_name == "optimize_seo":
                return await self._optimize_seo(base_url, headers, params)
            else:
                return {"success": False, "error": f"Ferramenta '{tool_name}' não encontrada"}
                
        except Exception as e:
            logger.error(f"Erro ao executar tool {tool_name}: {str(e)}")
            return {"success": False, "error": str(e)}
    
    # === PRODUCTS ===
    
    async def _list_products(
        self,
        base_url: str,
        headers: Dict[str, str],
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Lista produtos da loja"""
        limit = params.get("limit", 50)
        page_info = params.get("page_info")
        
        url = f"{base_url}/products.json?limit={limit}"
        if page_info:
            url += f"&page_info={page_info}"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    products = data.get("products", [])
                    return {
                        "success": True,
                        "products": products,
                        "count": len(products),
                        "page_info": response.headers.get("link", "")
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Erro Shopify: {response.status}"
                    }
    
    async def _get_product(
        self,
        base_url: str,
        headers: Dict[str, str],
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Obtém detalhes de um produto específico"""
        product_id = params.get("product_id")
        if not product_id:
            return {"success": False, "error": "product_id é obrigatório"}
        
        url = f"{base_url}/products/{product_id}.json"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    return {"success": True, "product": data.get("product")}
                else:
                    return {"success": False, "error": f"Produto não encontrado: {response.status}"}
    
    async def _create_product(
        self,
        base_url: str,
        headers: Dict[str, str],
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Cria um novo produto"""
        required_fields = ["title"]
        for field in required_fields:
            if field not in params:
                return {"success": False, "error": f"Campo obrigatório: {field}"}
        
        product_data = {
            "product": {
                "title": params["title"],
                "body_html": params.get("description", ""),
                "vendor": params.get("vendor", ""),
                "product_type": params.get("product_type", ""),
                "tags": params.get("tags", []),
                "variants": params.get("variants", []),
                "images": params.get("images", [])
            }
        }
        
        url = f"{base_url}/products.json"
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=product_data) as response:
                if response.status == 201:
                    data = await response.json()
                    return {
                        "success": True,
                        "product": data.get("product"),
                        "message": "Produto criado com sucesso"
                    }
                else:
                    error_text = await response.text()
                    return {"success": False, "error": f"Erro ao criar produto: {error_text}"}
    
    async def _update_product(
        self,
        base_url: str,
        headers: Dict[str, str],
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Atualiza um produto existente"""
        product_id = params.get("product_id")
        if not product_id:
            return {"success": False, "error": "product_id é obrigatório"}
        
        update_fields = {}
        if "title" in params:
            update_fields["title"] = params["title"]
        if "description" in params:
            update_fields["body_html"] = params["description"]
        if "vendor" in params:
            update_fields["vendor"] = params["vendor"]
        if "tags" in params:
            update_fields["tags"] = params["tags"]
        if "status" in params:
            update_fields["status"] = params["status"]
        
        if not update_fields:
            return {"success": False, "error": "Nenhum campo para atualizar"}
        
        url = f"{base_url}/products/{product_id}.json"
        
        async with aiohttp.ClientSession() as session:
            async with session.put(url, headers=headers, json={"product": update_fields}) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        "success": True,
                        "product": data.get("product"),
                        "message": "Produto atualizado com sucesso"
                    }
                else:
                    error_text = await response.text()
                    return {"success": False, "error": f"Erro ao atualizar: {error_text}"}
    
    async def _update_price(
        self,
        base_url: str,
        headers: Dict[str, str],
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Atualiza o preço de uma variante de produto"""
        variant_id = params.get("variant_id")
        price = params.get("price")
        compare_at_price = params.get("compare_at_price")
        
        if not variant_id or price is None:
            return {"success": False, "error": "variant_id e price são obrigatórios"}
        
        update_data = {"variant": {"price": str(price)}}
        if compare_at_price:
            update_data["variant"]["compare_at_price"] = str(compare_at_price)
        
        url = f"{base_url}/variants/{variant_id}.json"
        
        async with aiohttp.ClientSession() as session:
            async with session.put(url, headers=headers, json=update_data) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        "success": True,
                        "variant": data.get("variant"),
                        "message": f"Preço atualizado para ${price}"
                    }
                else:
                    error_text = await response.text()
                    return {"success": False, "error": f"Erro ao atualizar preço: {error_text}"}
    
    async def _update_inventory(
        self,
        base_url: str,
        headers: Dict[str, str],
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Atualiza o inventário de um item"""
        inventory_item_id = params.get("inventory_item_id")
        location_id = params.get("location_id")
        quantity = params.get("quantity")
        
        if not all([inventory_item_id, location_id, quantity is not None]):
            return {"success": False, "error": "inventory_item_id, location_id e quantity são obrigatórios"}
        
        url = f"{base_url}/inventory_levels/set.json"
        data = {
            "location_id": location_id,
            "inventory_item_id": inventory_item_id,
            "available": quantity
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=data) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        "success": True,
                        "inventory_level": data.get("inventory_level"),
                        "message": f"Estoque atualizado para {quantity} unidades"
                    }
                else:
                    error_text = await response.text()
                    return {"success": False, "error": f"Erro ao atualizar estoque: {error_text}"}
    
    # === ORDERS ===
    
    async def _list_orders(
        self,
        base_url: str,
        headers: Dict[str, str],
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Lista pedidos da loja"""
        limit = params.get("limit", 50)
        status = params.get("status", "any")
        created_at_min = params.get("created_at_min")
        
        url = f"{base_url}/orders.json?limit={limit}&status={status}"
        if created_at_min:
            url += f"&created_at_min={created_at_min}"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    orders = data.get("orders", [])
                    return {
                        "success": True,
                        "orders": orders,
                        "count": len(orders)
                    }
                else:
                    return {"success": False, "error": f"Erro ao listar pedidos: {response.status}"}
    
    async def _get_order(
        self,
        base_url: str,
        headers: Dict[str, str],
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Obtém detalhes de um pedido específico"""
        order_id = params.get("order_id")
        if not order_id:
            return {"success": False, "error": "order_id é obrigatório"}
        
        url = f"{base_url}/orders/{order_id}.json"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    return {"success": True, "order": data.get("order")}
                else:
                    return {"success": False, "error": f"Pedido não encontrado: {response.status}"}
    
    # === CUSTOMERS ===
    
    async def _list_customers(
        self,
        base_url: str,
        headers: Dict[str, str],
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Lista clientes da loja"""
        limit = params.get("limit", 50)
        
        url = f"{base_url}/customers.json?limit={limit}"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    customers = data.get("customers", [])
                    return {
                        "success": True,
                        "customers": customers,
                        "count": len(customers)
                    }
                else:
                    return {"success": False, "error": f"Erro ao listar clientes: {response.status}"}
    
    # === SEARCH & ANALYTICS ===
    
    async def _search_products(
        self,
        base_url: str,
        headers: Dict[str, str],
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Pesquisa produtos por termo"""
        query = params.get("query")
        if not query:
            return {"success": False, "error": "query é obrigatório"}
        
        # Usa a API de produtos com filtro
        url = f"{base_url}/products.json?title={query}"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    products = data.get("products", [])
                    return {
                        "success": True,
                        "query": query,
                        "products": products,
                        "count": len(products)
                    }
                else:
                    return {"success": False, "error": f"Erro na pesquisa: {response.status}"}
    
    async def _get_sales_analytics(
        self,
        base_url: str,
        headers: Dict[str, str],
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Obtém analytics de vendas"""
        period = params.get("period", "30d")
        
        # Conta pedidos e soma valores
        url = f"{base_url}/orders.json?status=any&limit=250"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    orders = data.get("orders", [])
                    
                    total_sales = sum(float(order.get("total_price", 0)) for order in orders)
                    total_orders = len(orders)
                    
                    return {
                        "success": True,
                        "period": period,
                        "total_sales": round(total_sales, 2),
                        "total_orders": total_orders,
                        "average_order_value": round(total_sales / total_orders, 2) if total_orders > 0 else 0,
                        "orders": orders[:10]  # Primeiros 10 pedidos
                    }
                else:
                    return {"success": False, "error": f"Erro ao obter analytics: {response.status}"}
    
    async def _optimize_seo(
        self,
        base_url: str,
        headers: Dict[str, str],
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Otimiza SEO de um produto (simulação/análise)"""
        product_id = params.get("product_id")
        if not product_id:
            return {"success": False, "error": "product_id é obrigatório"}
        
        # Primeiro obtém o produto
        product_result = await self._get_product(base_url, headers, {"product_id": product_id})
        if not product_result["success"]:
            return product_result
        
        product = product_result["product"]
        
        # Análise de SEO
        seo_analysis = {
            "title_length": len(product.get("title", "")),
            "description_length": len(product.get("body_html", "")),
            "has_images": len(product.get("images", [])) > 0,
            "tags_count": len(product.get("tags", [])),
            "seo_score": 0,
            "suggestions": []
        }
        
        # Calcula score e sugestões
        score = 0
        suggestions = []
        
        if seo_analysis["title_length"] >= 50:
            score += 30
        else:
            suggestions.append("Título muito curto. Ideal: 50-70 caracteres")
        
        if seo_analysis["description_length"] >= 300:
            score += 40
        else:
            suggestions.append("Descrição muito curta. Ideal: 300+ caracteres")
        
        if seo_analysis["has_images"]:
            score += 20
        else:
            suggestions.append("Adicione imagens ao produto")
        
        if seo_analysis["tags_count"] >= 3:
            score += 10
        else:
            suggestions.append("Adicione mais tags (mínimo 3)")
        
        seo_analysis["seo_score"] = score
        seo_analysis["suggestions"] = suggestions
        
        return {
            "success": True,
            "product_id": product_id,
            "product_title": product.get("title"),
            "seo_analysis": seo_analysis,
            "optimized": score >= 80
        }
    
    # === STREAMING SSE ===
    
    async def stream_tool_execution(
        self,
        tool_name: str,
        params: Dict[str, Any],
        credentials: Dict[str, str]
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Executa ferramenta com streaming SSE para feedback em tempo real
        """
        yield {
            "type": "tool_call",
            "tool": tool_name,
            "status": "executing",
            "message": f"🛒 Executando {tool_name} na Shopify..."
        }
        
        result = await self.execute_tool(tool_name, params, credentials)
        
        if result["success"]:
            yield {
                "type": "tool_result",
                "tool": tool_name,
                "status": "completed",
                "result": result
            }
        else:
            yield {
                "type": "tool_result",
                "tool": tool_name,
                "status": "error",
                "error": result.get("error", "Erro desconhecido")
            }


# Instância global
shopify_mcp = ShopifyMCP()
