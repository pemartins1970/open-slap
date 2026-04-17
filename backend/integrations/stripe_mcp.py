"""
Stripe MCP - Model Context Protocol para integração com Stripe
Baseado no Stripe Agents Toolkit (https://docs.stripe.com/agents)

Funcionalidades:
- Criar e gerenciar Payment Links
- Processar pagamentos
- Gerenciar produtos e preços
- Análise de transações
- Gestão de clientes
- Reembolsos e disputas
"""

import json
import logging
from typing import Dict, Any, List, Optional, AsyncGenerator
from datetime import datetime
import aiohttp

logger = logging.getLogger(__name__)


class StripeMCP:
    """
    MCP para integração com Stripe
    Permite agentes processarem pagamentos e gerenciarem finanças
    """
    
    def __init__(self):
        self.name = "stripe"
        self.display_name = "Stripe"
        self.version = "1.0.0"
        self.description = "Processamento de pagamentos, assinaturas e gestão financeira via Stripe"
        self.icon = "💳"
        self.category = "payments"
        self.tier = "pro"
        
    def get_manifest(self) -> Dict[str, Any]:
        """Retorna o manifesto do MCP para registro"""
        return {
            "manifest_version": "1.0",
            "id": self.name,
            "name": self.display_name,
            "version": self.version,
            "category": "productivity",
            "tier": self.tier,
            "icon": self.icon,
            "description": self.description,
            "compatible_with": ["openslap"],
            "permissions": [
                "stripe:payment_links:write",
                "stripe:products:write",
                "stripe:prices:write",
                "stripe:customers:read",
                "stripe:charges:read",
                "stripe:refunds:write",
                "stripe:balance:read"
            ],
            "tools": [
                "create_payment_link",
                "create_product",
                "create_price",
                "create_customer",
                "list_charges",
                "get_charge",
                "create_refund",
                "get_balance",
                "list_customers",
                "get_customer",
                "update_customer",
                "list_invoices",
                "get_invoice",
                "create_invoice",
                "create_invoice_item",
                "finalize_invoice",
                "pay_invoice",
                "void_invoice",
                "list_refunds",
                "get_refund",
                "list_disputes",
                "get_dispute",
                "close_dispute",
                "create_coupon",
                "list_coupons",
                "delete_coupon"
            ],
            "agents": ["payment_specialist", "billing_manager", "finance_analyst"],
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
        Executa uma ferramenta do MCP Stripe
        
        Args:
            tool_name: Nome da ferramenta a executar
            params: Parâmetros da ferramenta
            credentials: {secret_key (rk_* ou sk_*)}
        """
        secret_key = credentials.get("secret_key")
        
        if not secret_key:
            return {
                "success": False,
                "error": "Chave secreta Stripe não configurada. Use restricted key (rk_*) para segurança."
            }
        
        base_url = "https://api.stripe.com/v1"
        headers = {
            "Authorization": f"Bearer {secret_key}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        try:
            if tool_name == "create_payment_link":
                return await self._create_payment_link(base_url, headers, params)
            elif tool_name == "create_product":
                return await self._create_product(base_url, headers, params)
            elif tool_name == "create_price":
                return await self._create_price(base_url, headers, params)
            elif tool_name == "create_customer":
                return await self._create_customer(base_url, headers, params)
            elif tool_name == "list_charges":
                return await self._list_charges(base_url, headers, params)
            elif tool_name == "get_charge":
                return await self._get_charge(base_url, headers, params)
            elif tool_name == "create_refund":
                return await self._create_refund(base_url, headers, params)
            elif tool_name == "get_balance":
                return await self._get_balance(base_url, headers, params)
            elif tool_name == "list_customers":
                return await self._list_customers(base_url, headers, params)
            elif tool_name == "get_customer":
                return await self._get_customer(base_url, headers, params)
            elif tool_name == "update_customer":
                return await self._update_customer(base_url, headers, params)
            elif tool_name == "list_invoices":
                return await self._list_invoices(base_url, headers, params)
            elif tool_name == "get_invoice":
                return await self._get_invoice(base_url, headers, params)
            elif tool_name == "create_invoice":
                return await self._create_invoice(base_url, headers, params)
            elif tool_name == "create_invoice_item":
                return await self._create_invoice_item(base_url, headers, params)
            elif tool_name == "finalize_invoice":
                return await self._finalize_invoice(base_url, headers, params)
            elif tool_name == "pay_invoice":
                return await self._pay_invoice(base_url, headers, params)
            elif tool_name == "void_invoice":
                return await self._void_invoice(base_url, headers, params)
            elif tool_name == "list_refunds":
                return await self._list_refunds(base_url, headers, params)
            elif tool_name == "get_refund":
                return await self._get_refund(base_url, headers, params)
            elif tool_name == "list_disputes":
                return await self._list_disputes(base_url, headers, params)
            elif tool_name == "get_dispute":
                return await self._get_dispute(base_url, headers, params)
            elif tool_name == "close_dispute":
                return await self._close_dispute(base_url, headers, params)
            elif tool_name == "create_coupon":
                return await self._create_coupon(base_url, headers, params)
            elif tool_name == "list_coupons":
                return await self._list_coupons(base_url, headers, params)
            elif tool_name == "delete_coupon":
                return await self._delete_coupon(base_url, headers, params)
            else:
                return {"success": False, "error": f"Ferramenta '{tool_name}' não encontrada"}
                
        except Exception as e:
            logger.error(f"Erro ao executar tool {tool_name}: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def _build_form_data(self, params: Dict[str, Any], prefix: str = "") -> str:
        """Converte dict para form-urlencoded format do Stripe"""
        items = []
        for key, value in params.items():
            full_key = f"{prefix}[{key}]" if prefix else key
            if isinstance(value, dict):
                items.append(self._build_form_data(value, full_key))
            elif isinstance(value, list):
                for i, item in enumerate(value):
                    if isinstance(item, dict):
                        items.append(self._build_form_data(item, f"{full_key}[{i}]"))
                    else:
                        items.append(f"{full_key}[{i}]={item}")
            else:
                items.append(f"{full_key}={value}")
        return "&".join(items)
    
    # === PAYMENT LINKS ===
    
    async def _create_payment_link(
        self,
        base_url: str,
        headers: Dict[str, str],
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Cria um Payment Link para receber pagamentos"""
        line_items = params.get("line_items", [])
        if not line_items:
            return {"success": False, "error": "line_items é obrigatório"}
        
        # Constrói o form data
        form_data = []
        for i, item in enumerate(line_items):
            if "price" in item:
                form_data.append(f"line_items[{i}][price]={item['price']}")
            if "quantity" in item:
                form_data.append(f"line_items[{i}][quantity]={item['quantity']}")
        
        if "after_completion" in params:
            form_data.append(f"after_completion[type]={params['after_completion']}")
        
        if "allow_promotion_codes" in params:
            form_data.append(f"allow_promotion_codes={str(params['allow_promotion_codes']).lower()}")
        
        body = "&".join(form_data)
        
        url = f"{base_url}/payment_links"
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, data=body) as response:
                data = await response.json()
                if response.status == 200:
                    return {
                        "success": True,
                        "payment_link": {
                            "id": data.get("id"),
                            "url": data.get("url"),
                            "object": data.get("object")
                        },
                        "message": f"Payment Link criado: {data.get('url')}"
                    }
                else:
                    return {
                        "success": False,
                        "error": data.get("error", {}).get("message", "Erro ao criar Payment Link")
                    }
    
    # === PRODUCTS & PRICES ===
    
    async def _create_product(
        self,
        base_url: str,
        headers: Dict[str, str],
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Cria um produto no Stripe"""
        name = params.get("name")
        if not name:
            return {"success": False, "error": "name é obrigatório"}
        
        form_data = [f"name={name}"]
        
        if "description" in params:
            form_data.append(f"description={params['description']}")
        if "images" in params:
            for i, img in enumerate(params["images"]):
                form_data.append(f"images[{i}]={img}")
        
        body = "&".join(form_data)
        url = f"{base_url}/products"
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, data=body) as response:
                data = await response.json()
                if response.status == 200:
                    return {
                        "success": True,
                        "product": {
                            "id": data.get("id"),
                            "name": data.get("name"),
                            "object": data.get("object")
                        },
                        "message": f"Produto '{name}' criado"
                    }
                else:
                    return {"success": False, "error": data.get("error", {}).get("message", "Erro ao criar produto")}
    
    async def _create_price(
        self,
        base_url: str,
        headers: Dict[str, str],
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Cria um preço para um produto"""
        product = params.get("product")
        unit_amount = params.get("unit_amount")
        currency = params.get("currency", "usd")
        
        if not product or unit_amount is None:
            return {"success": False, "error": "product e unit_amount são obrigatórios"}
        
        form_data = [
            f"product={product}",
            f"unit_amount={unit_amount}",
            f"currency={currency}"
        ]
        
        if "recurring" in params:
            form_data.append(f"recurring[interval]={params['recurring']}")
        
        body = "&".join(form_data)
        url = f"{base_url}/prices"
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, data=body) as response:
                data = await response.json()
                if response.status == 200:
                    return {
                        "success": True,
                        "price": {
                            "id": data.get("id"),
                            "product": data.get("product"),
                            "unit_amount": data.get("unit_amount"),
                            "currency": data.get("currency"),
                            "object": data.get("object")
                        },
                        "message": f"Preço criado: ${unit_amount/100:.2f} {currency.upper()}"
                    }
                else:
                    return {"success": False, "error": data.get("error", {}).get("message", "Erro ao criar preço")}
    
    # === CUSTOMERS ===
    
    async def _create_customer(
        self,
        base_url: str,
        headers: Dict[str, str],
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Cria um cliente"""
        email = params.get("email")
        
        form_data = []
        if email:
            form_data.append(f"email={email}")
        if "name" in params:
            form_data.append(f"name={params['name']}")
        if "phone" in params:
            form_data.append(f"phone={params['phone']}")
        if "description" in params:
            form_data.append(f"description={params['description']}")
        
        body = "&".join(form_data) if form_data else ""
        url = f"{base_url}/customers"
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, data=body) as response:
                data = await response.json()
                if response.status == 200:
                    return {
                        "success": True,
                        "customer": {
                            "id": data.get("id"),
                            "email": data.get("email"),
                            "name": data.get("name"),
                            "object": data.get("object")
                        },
                        "message": f"Cliente criado: {data.get('email', data.get('id'))}"
                    }
                else:
                    return {"success": False, "error": data.get("error", {}).get("message", "Erro ao criar cliente")}
    
    async def _list_customers(
        self,
        base_url: str,
        headers: Dict[str, str],
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Lista clientes"""
        limit = params.get("limit", 10)
        email = params.get("email")
        
        query = f"limit={limit}"
        if email:
            query += f"&email={email}"
        
        url = f"{base_url}/customers?{query}"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                data = await response.json()
                if response.status == 200:
                    return {
                        "success": True,
                        "customers": data.get("data", []),
                        "count": len(data.get("data", [])),
                        "has_more": data.get("has_more", False)
                    }
                else:
                    return {"success": False, "error": data.get("error", {}).get("message", "Erro ao listar clientes")}
    
    async def _get_customer(
        self,
        base_url: str,
        headers: Dict[str, str],
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Obtém detalhes de um cliente"""
        customer_id = params.get("customer_id")
        if not customer_id:
            return {"success": False, "error": "customer_id é obrigatório"}
        
        url = f"{base_url}/customers/{customer_id}"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                data = await response.json()
                if response.status == 200:
                    return {
                        "success": True,
                        "customer": data
                    }
                else:
                    return {"success": False, "error": data.get("error", {}).get("message", "Cliente não encontrado")}
    
    async def _update_customer(
        self,
        base_url: str,
        headers: Dict[str, str],
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Atualiza um cliente"""
        customer_id = params.get("customer_id")
        if not customer_id:
            return {"success": False, "error": "customer_id é obrigatório"}
        
        form_data = []
        if "email" in params:
            form_data.append(f"email={params['email']}")
        if "name" in params:
            form_data.append(f"name={params['name']}")
        if "phone" in params:
            form_data.append(f"phone={params['phone']}")
        if "description" in params:
            form_data.append(f"description={params['description']}")
        
        if not form_data:
            return {"success": False, "error": "Nenhum campo para atualizar"}
        
        body = "&".join(form_data)
        url = f"{base_url}/customers/{customer_id}"
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, data=body) as response:
                data = await response.json()
                if response.status == 200:
                    return {
                        "success": True,
                        "customer": data,
                        "message": "Cliente atualizado com sucesso"
                    }
                else:
                    return {"success": False, "error": data.get("error", {}).get("message", "Erro ao atualizar cliente")}
    
    # === CHARGES ===
    
    async def _list_charges(
        self,
        base_url: str,
        headers: Dict[str, str],
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Lista cobranças/transações"""
        limit = params.get("limit", 10)
        
        url = f"{base_url}/charges?limit={limit}"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                data = await response.json()
                if response.status == 200:
                    charges = data.get("data", [])
                    total_amount = sum(charge.get("amount", 0) for charge in charges)
                    return {
                        "success": True,
                        "charges": charges,
                        "count": len(charges),
                        "total_amount": total_amount / 100,  # Convert from cents
                        "has_more": data.get("has_more", False)
                    }
                else:
                    return {"success": False, "error": data.get("error", {}).get("message", "Erro ao listar cobranças")}
    
    async def _get_charge(
        self,
        base_url: str,
        headers: Dict[str, str],
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Obtém detalhes de uma cobrança"""
        charge_id = params.get("charge_id")
        if not charge_id:
            return {"success": False, "error": "charge_id é obrigatório"}
        
        url = f"{base_url}/charges/{charge_id}"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                data = await response.json()
                if response.status == 200:
                    return {"success": True, "charge": data}
                else:
                    return {"success": False, "error": data.get("error", {}).get("message", "Cobrança não encontrada")}
    
    # === REFUNDS ===
    
    async def _create_refund(
        self,
        base_url: str,
        headers: Dict[str, str],
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Cria um reembolso"""
        charge_id = params.get("charge_id") or params.get("payment_intent")
        if not charge_id:
            return {"success": False, "error": "charge_id ou payment_intent é obrigatório"}
        
        form_data = [f"charge={charge_id}"]
        
        if "amount" in params:
            form_data.append(f"amount={params['amount']}")
        if "reason" in params:
            form_data.append(f"reason={params['reason']}")
        
        body = "&".join(form_data)
        url = f"{base_url}/refunds"
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, data=body) as response:
                data = await response.json()
                if response.status == 200:
                    return {
                        "success": True,
                        "refund": {
                            "id": data.get("id"),
                            "amount": data.get("amount"),
                            "status": data.get("status"),
                            "charge": data.get("charge"),
                            "object": data.get("object")
                        },
                        "message": f"Reembolso de ${data.get('amount', 0)/100:.2f} criado"
                    }
                else:
                    return {"success": False, "error": data.get("error", {}).get("message", "Erro ao criar reembolso")}
    
    async def _list_refunds(
        self,
        base_url: str,
        headers: Dict[str, str],
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Lista reembolsos"""
        limit = params.get("limit", 10)
        
        url = f"{base_url}/refunds?limit={limit}"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                data = await response.json()
                if response.status == 200:
                    return {
                        "success": True,
                        "refunds": data.get("data", []),
                        "count": len(data.get("data", [])),
                        "has_more": data.get("has_more", False)
                    }
                else:
                    return {"success": False, "error": data.get("error", {}).get("message", "Erro ao listar reembolsos")}
    
    async def _get_refund(
        self,
        base_url: str,
        headers: Dict[str, str],
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Obtém detalhes de um reembolso"""
        refund_id = params.get("refund_id")
        if not refund_id:
            return {"success": False, "error": "refund_id é obrigatório"}
        
        url = f"{base_url}/refunds/{refund_id}"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                data = await response.json()
                if response.status == 200:
                    return {"success": True, "refund": data}
                else:
                    return {"success": False, "error": data.get("error", {}).get("message", "Reembolso não encontrado")}
    
    # === BALANCE ===
    
    async def _get_balance(
        self,
        base_url: str,
        headers: Dict[str, str],
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Obtém saldo da conta"""
        url = f"{base_url}/balance"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                data = await response.json()
                if response.status == 200:
                    available = data.get("available", [])
                    pending = data.get("pending", [])
                    
                    return {
                        "success": True,
                        "balance": {
                            "available": [{"amount": b["amount"]/100, "currency": b["currency"]} for b in available],
                            "pending": [{"amount": b["amount"]/100, "currency": b["currency"]} for b in pending]
                        },
                        "total_available": sum(b["amount"] for b in available) / 100,
                        "total_pending": sum(b["amount"] for b in pending) / 100
                    }
                else:
                    return {"success": False, "error": data.get("error", {}).get("message", "Erro ao obter saldo")}
    
    # === INVOICES ===
    
    async def _list_invoices(
        self,
        base_url: str,
        headers: Dict[str, str],
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Lista faturas"""
        limit = params.get("limit", 10)
        status = params.get("status")
        
        query = f"limit={limit}"
        if status:
            query += f"&status={status}"
        
        url = f"{base_url}/invoices?{query}"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                data = await response.json()
                if response.status == 200:
                    return {
                        "success": True,
                        "invoices": data.get("data", []),
                        "count": len(data.get("data", [])),
                        "has_more": data.get("has_more", False)
                    }
                else:
                    return {"success": False, "error": data.get("error", {}).get("message", "Erro ao listar faturas")}
    
    async def _get_invoice(
        self,
        base_url: str,
        headers: Dict[str, str],
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Obtém detalhes de uma fatura"""
        invoice_id = params.get("invoice_id")
        if not invoice_id:
            return {"success": False, "error": "invoice_id é obrigatório"}
        
        url = f"{base_url}/invoices/{invoice_id}"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                data = await response.json()
                if response.status == 200:
                    return {"success": True, "invoice": data}
                else:
                    return {"success": False, "error": data.get("error", {}).get("message", "Fatura não encontrada")}
    
    async def _create_invoice(
        self,
        base_url: str,
        headers: Dict[str, str],
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Cria uma fatura (draft)"""
        customer_id = params.get("customer_id")
        if not customer_id:
            return {"success": False, "error": "customer_id é obrigatório"}
        
        form_data = [f"customer={customer_id}"]
        
        if "collection_method" in params:
            form_data.append(f"collection_method={params['collection_method']}")
        if "auto_advance" in params:
            form_data.append(f"auto_advance={str(params['auto_advance']).lower()}")
        if "description" in params:
            form_data.append(f"description={params['description']}")
        
        body = "&".join(form_data)
        url = f"{base_url}/invoices"
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, data=body) as response:
                data = await response.json()
                if response.status == 200:
                    return {
                        "success": True,
                        "invoice": {
                            "id": data.get("id"),
                            "customer": data.get("customer"),
                            "status": data.get("status"),
                            "amount_due": data.get("amount_due", 0) / 100,
                            "object": data.get("object")
                        },
                        "message": f"Fatura criada: {data.get('id')}"
                    }
                else:
                    return {"success": False, "error": data.get("error", {}).get("message", "Erro ao criar fatura")}
    
    async def _create_invoice_item(
        self,
        base_url: str,
        headers: Dict[str, str],
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Adiciona um item a uma fatura"""
        customer_id = params.get("customer_id")
        price_id = params.get("price_id")
        
        if not customer_id:
            return {"success": False, "error": "customer_id é obrigatório"}
        
        form_data = [f"customer={customer_id}"]
        
        if price_id:
            form_data.append(f"price={price_id}")
        if "amount" in params:
            form_data.append(f"amount={params['amount']}")
        if "currency" in params:
            form_data.append(f"currency={params['currency']}")
        if "description" in params:
            form_data.append(f"description={params['description']}")
        if "invoice" in params:
            form_data.append(f"invoice={params['invoice']}")
        
        body = "&".join(form_data)
        url = f"{base_url}/invoiceitems"
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, data=body) as response:
                data = await response.json()
                if response.status == 200:
                    return {
                        "success": True,
                        "invoice_item": {
                            "id": data.get("id"),
                            "amount": data.get("amount", 0) / 100,
                            "description": data.get("description"),
                            "object": data.get("object")
                        },
                        "message": "Item adicionado à fatura"
                    }
                else:
                    return {"success": False, "error": data.get("error", {}).get("message", "Erro ao adicionar item")}
    
    async def _finalize_invoice(
        self,
        base_url: str,
        headers: Dict[str, str],
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Finaliza uma fatura draft"""
        invoice_id = params.get("invoice_id")
        if not invoice_id:
            return {"success": False, "error": "invoice_id é obrigatório"}
        
        url = f"{base_url}/invoices/{invoice_id}/finalize"
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers) as response:
                data = await response.json()
                if response.status == 200:
                    return {
                        "success": True,
                        "invoice": {
                            "id": data.get("id"),
                            "status": data.get("status"),
                            "amount_due": data.get("amount_due", 0) / 100
                        },
                        "message": "Fatura finalizada"
                    }
                else:
                    return {"success": False, "error": data.get("error", {}).get("message", "Erro ao finalizar fatura")}
    
    async def _pay_invoice(
        self,
        base_url: str,
        headers: Dict[str, str],
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Paga uma fatura"""
        invoice_id = params.get("invoice_id")
        if not invoice_id:
            return {"success": False, "error": "invoice_id é obrigatório"}
        
        url = f"{base_url}/invoices/{invoice_id}/pay"
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers) as response:
                data = await response.json()
                if response.status == 200:
                    return {
                        "success": True,
                        "invoice": {
                            "id": data.get("id"),
                            "status": data.get("status"),
                            "charge": data.get("charge")
                        },
                        "message": "Fatura paga com sucesso"
                    }
                else:
                    return {"success": False, "error": data.get("error", {}).get("message", "Erro ao pagar fatura")}
    
    async def _void_invoice(
        self,
        base_url: str,
        headers: Dict[str, str],
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Cancela (void) uma fatura"""
        invoice_id = params.get("invoice_id")
        if not invoice_id:
            return {"success": False, "error": "invoice_id é obrigatório"}
        
        url = f"{base_url}/invoices/{invoice_id}/void"
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers) as response:
                data = await response.json()
                if response.status == 200:
                    return {
                        "success": True,
                        "invoice": {
                            "id": data.get("id"),
                            "status": data.get("status")
                        },
                        "message": "Fatura cancelada"
                    }
                else:
                    return {"success": False, "error": data.get("error", {}).get("message", "Erro ao cancelar fatura")}
    
    # === DISPUTES ===
    
    async def _list_disputes(
        self,
        base_url: str,
        headers: Dict[str, str],
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Lista disputas/chargebacks"""
        limit = params.get("limit", 10)
        
        url = f"{base_url}/disputes?limit={limit}"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                data = await response.json()
                if response.status == 200:
                    return {
                        "success": True,
                        "disputes": data.get("data", []),
                        "count": len(data.get("data", [])),
                        "has_more": data.get("has_more", False)
                    }
                else:
                    return {"success": False, "error": data.get("error", {}).get("message", "Erro ao listar disputas")}
    
    async def _get_dispute(
        self,
        base_url: str,
        headers: Dict[str, str],
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Obtém detalhes de uma disputa"""
        dispute_id = params.get("dispute_id")
        if not dispute_id:
            return {"success": False, "error": "dispute_id é obrigatório"}
        
        url = f"{base_url}/disputes/{dispute_id}"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                data = await response.json()
                if response.status == 200:
                    return {"success": True, "dispute": data}
                else:
                    return {"success": False, "error": data.get("error", {}).get("message", "Disputa não encontrada")}
    
    async def _close_dispute(
        self,
        base_url: str,
        headers: Dict[str, str],
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Fecha uma disputa (aceita ou contesta)"""
        dispute_id = params.get("dispute_id")
        if not dispute_id:
            return {"success": False, "error": "dispute_id é obrigatório"}
        
        url = f"{base_url}/disputes/{dispute_id}/close"
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers) as response:
                data = await response.json()
                if response.status == 200:
                    return {
                        "success": True,
                        "dispute": data,
                        "message": "Disputa fechada"
                    }
                else:
                    return {"success": False, "error": data.get("error", {}).get("message", "Erro ao fechar disputa")}
    
    # === COUPONS ===
    
    async def _create_coupon(
        self,
        base_url: str,
        headers: Dict[str, str],
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Cria um cupom de desconto"""
        form_data = []
        
        if "id" in params:
            form_data.append(f"id={params['id']}")
        if "name" in params:
            form_data.append(f"name={params['name']}")
        if "percent_off" in params:
            form_data.append(f"percent_off={params['percent_off']}")
        if "amount_off" in params:
            form_data.append(f"amount_off={params['amount_off']}")
        if "currency" in params:
            form_data.append(f"currency={params['currency']}")
        if "duration" in params:
            form_data.append(f"duration={params['duration']}")
        if "duration_in_months" in params:
            form_data.append(f"duration_in_months={params['duration_in_months']}")
        if "max_redemptions" in params:
            form_data.append(f"max_redemptions={params['max_redemptions']}")
        if "redeem_by" in params:
            form_data.append(f"redeem_by={params['redeem_by']}")
        
        if not form_data:
            return {"success": False, "error": "Nenhum parâmetro de cupom fornecido (percent_off ou amount_off)"}
        
        body = "&".join(form_data)
        url = f"{base_url}/coupons"
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, data=body) as response:
                data = await response.json()
                if response.status == 200:
                    return {
                        "success": True,
                        "coupon": {
                            "id": data.get("id"),
                            "name": data.get("name"),
                            "percent_off": data.get("percent_off"),
                            "amount_off": data.get("amount_off"),
                            "currency": data.get("currency"),
                            "duration": data.get("duration"),
                            "object": data.get("object")
                        },
                        "message": f"Cupom '{data.get('id')}' criado"
                    }
                else:
                    return {"success": False, "error": data.get("error", {}).get("message", "Erro ao criar cupom")}
    
    async def _list_coupons(
        self,
        base_url: str,
        headers: Dict[str, str],
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Lista cupons"""
        limit = params.get("limit", 10)
        
        url = f"{base_url}/coupons?limit={limit}"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                data = await response.json()
                if response.status == 200:
                    return {
                        "success": True,
                        "coupons": data.get("data", []),
                        "count": len(data.get("data", [])),
                        "has_more": data.get("has_more", False)
                    }
                else:
                    return {"success": False, "error": data.get("error", {}).get("message", "Erro ao listar cupons")}
    
    async def _delete_coupon(
        self,
        base_url: str,
        headers: Dict[str, str],
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Deleta um cupom"""
        coupon_id = params.get("coupon_id")
        if not coupon_id:
            return {"success": False, "error": "coupon_id é obrigatório"}
        
        url = f"{base_url}/coupons/{coupon_id}"
        
        async with aiohttp.ClientSession() as session:
            async with session.delete(url, headers=headers) as response:
                data = await response.json()
                if response.status == 200:
                    return {
                        "success": True,
                        "deleted": data.get("deleted"),
                        "id": data.get("id"),
                        "message": f"Cupom '{coupon_id}' deletado"
                    }
                else:
                    return {"success": False, "error": data.get("error", {}).get("message", "Erro ao deletar cupom")}
    
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
            "message": f"💳 Executando {tool_name} na Stripe..."
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
stripe_mcp = StripeMCP()
