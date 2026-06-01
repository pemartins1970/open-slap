"""
Zapier MCP Integration
Automação de Workflows para OpenSlap
"""

from typing import Dict, Any, List, Optional
import aiohttp
import json

class ZapierMCP:
    """
    Zapier MCP - Automação de Workflows
    
    Funcionalidades:
    - Triggers (gatilhos)
    - Webhooks
    - Zaps (workflows)
    - Histórico de execuções
    - Apps e integrações
    """
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://nla.zapier.com/api/v1"
        self.webhook_base = "https://hooks.zapier.com/hooks"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "X-Api-Key": api_key
        }
    
    async def _make_request(self, method: str, endpoint: str,
                           data: Dict = None, params: Dict = None,
                           use_webhook: bool = False) -> Dict[str, Any]:
        """Faz requisição à API do Zapier"""
        base = self.webhook_base if use_webhook else self.base_url
        url = f"{base}{endpoint}"
        
        async with aiohttp.ClientSession() as session:
            async with session.request(
                method=method,
                url=url,
                headers=self.headers if not use_webhook else {},
                json=data,
                params=params
            ) as response:
                if response.status in [200, 201, 202]:
                    try:
                        return await response.json()
                    except:
                        return {"success": True, "status": response.status}
                else:
                    error_text = await response.text()
                    raise Exception(f"Zapier API Error {response.status}: {error_text}")
    
    # ========== WEBHOOKS ==========
    
    async def trigger_webhook(self, webhook_url: str, payload: Dict[str, Any]) -> bool:
        """
        Dispara webhook do Zapier
        
        Args:
            webhook_url: URL completa do webhook (ex: https://hooks.zapier.com/hooks/catch/...)
            payload: Dados a enviar
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    webhook_url,
                    json=payload,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    return response.status in [200, 201, 202]
        except Exception as e:
            raise Exception(f"Erro ao disparar webhook: {str(e)}")
    
    async def catch_webhook(self, hook_id: str, payload: Dict[str, Any]) -> bool:
        """Envia dados para webhook catch"""
        endpoint = f"/catch/{hook_id}"
        try:
            result = await self._make_request("POST", endpoint, payload, use_webhook=True)
            return True
        except:
            return False
    
    # ========== EXPOSED ACTIONS (BETA) ==========
    
    async def list_actions(self, limit: int = 100) -> Dict[str, Any]:
        """
        Lista ações expostas disponíveis
        Requer Zapier Natural Language Actions (NLA)
        """
        endpoint = f"/exposed?limit={limit}"
        return await self._make_request("GET", endpoint)
    
    async def execute_action(self, action_id: str, instructions: str,
                            params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Executa ação exposta usando linguagem natural
        
        Args:
            action_id: ID da ação
            instructions: Instruções em linguagem natural
            params: Parâmetros adicionais
        """
        endpoint = "/exposed/execute"
        data = {
            "action_id": action_id,
            "instructions": instructions,
            "params": params or {}
        }
        return await self._make_request("POST", endpoint, data)
    
    async def execute_action_async(self, action_id: str, instructions: str,
                                   params: Dict[str, Any] = None) -> str:
        """
        Executa ação de forma assíncrona
        Retorna execution_id para consulta posterior
        """
        endpoint = "/exposed/execute/async"
        data = {
            "action_id": action_id,
            "instructions": instructions,
            "params": params or {}
        }
        result = await self._make_request("POST", endpoint, data)
        return result.get("execution_id")
    
    async def get_execution_status(self, execution_id: str) -> Dict[str, Any]:
        """Obtém status de execução assíncrona"""
        endpoint = f"/exposed/execute/{execution_id}"
        return await self._make_request("GET", endpoint)
    
    # ========== ZAPS ==========
    
    async def list_zaps(self, limit: int = 100, status: str = None) -> List[Dict]:
        """Lista Zaps (automações)"""
        params = {"limit": limit}
        if status:
            params["status"] = status
        
        endpoint = f"/zaps?{self._encode_params(params)}"
        return await self._make_request("GET", endpoint)
    
    async def get_zap(self, zap_id: str) -> Dict[str, Any]:
        """Obtém detalhes de um Zap"""
        endpoint = f"/zaps/{zap_id}"
        return await self._make_request("GET", endpoint)
    
    async def run_zap(self, zap_id: str, data: Dict[str, Any] = None) -> bool:
        """Executa um Zap manualmente"""
        endpoint = f"/zaps/{zap_id}/run"
        try:
            await self._make_request("POST", endpoint, data)
            return True
        except:
            return False
    
    async def enable_zap(self, zap_id: str) -> bool:
        """Ativa um Zap"""
        endpoint = f"/zaps/{zap_id}"
        try:
            await self._make_request("PATCH", endpoint, {"status": "on"})
            return True
        except:
            return False
    
    async def disable_zap(self, zap_id: str) -> bool:
        """Desativa um Zap"""
        endpoint = f"/zaps/{zap_id}"
        try:
            await self._make_request("PATCH", endpoint, {"status": "off"})
            return True
        except:
            return False
    
    # ========== HISTORY ==========
    
    async def get_zap_history(self, zap_id: str, limit: int = 50) -> List[Dict]:
        """Obtém histórico de execuções de um Zap"""
        endpoint = f"/zaps/{zap_id}/history?limit={limit}"
        return await self._make_request("GET", endpoint)
    
    async def get_task_details(self, zap_id: str, task_id: str) -> Dict[str, Any]:
        """Obtém detalhes de uma execução específica"""
        endpoint = f"/zaps/{zap_id}/history/{task_id}"
        return await self._make_request("GET", endpoint)
    
    # ========== APPS ==========
    
    async def list_apps(self, limit: int = 100, category: str = None) -> List[Dict]:
        """Lista apps disponíveis no Zapier"""
        params = {"limit": limit}
        if category:
            params["category"] = category
        
        endpoint = f"/apps?{self._encode_params(params)}"
        return await self._make_request("GET", endpoint)
    
    async def get_app(self, app_id: str) -> Dict[str, Any]:
        """Obtém detalhes de um app"""
        endpoint = f"/apps/{app_id}"
        return await self._make_request("GET", endpoint)
    
    # ========== UTILITÁRIOS ==========
    
    def _encode_params(self, params: Dict) -> str:
        """Codifica parâmetros para URL"""
        from urllib.parse import urlencode
        return urlencode(params)
    
    def build_webhook_url(self, hook_path: str) -> str:
        """Constrói URL completa do webhook"""
        return f"{self.webhook_base}/{hook_path.lstrip('/')}"
    
    async def test_connection(self) -> bool:
        """Testa conexão"""
        try:
            result = await self.list_actions(limit=1)
            return True
        except:
            return False


zapier_mcp = None

def init_zapier_mcp(api_key: str):
    global zapier_mcp
    zapier_mcp = ZapierMCP(api_key)
    return zapier_mcp
