"""
Twilio MCP - Model Context Protocol para Twilio
Integração com Twilio API para SMS, WhatsApp e chamadas telefônicas

Documentação: https://www.twilio.com/docs/api
"""

import json
import logging
from typing import Dict, Any, List, Optional, AsyncGenerator
import aiohttp
import base64

logger = logging.getLogger(__name__)


class TwilioMCP:
    def __init__(self):
        self.name = "twilio"
        self.display_name = "Twilio"
        self.version = "1.0.0"
        self.description = "SMS, WhatsApp e chamadas telefônicas via API"
        self.icon = "📞"
        self.category = "communication"
        self.tier = "pro"
        self.base_url = "https://api.twilio.com/2010-04-01"
        
    def get_manifest(self) -> Dict[str, Any]:
        return {
            "manifest_version": "1.0",
            "id": self.name,
            "name": self.display_name,
            "version": self.version,
            "category": "social_communication",
            "tier": self.tier,
            "icon": self.icon,
            "description": self.description,
            "compatible_with": ["openslap"],
            "permissions": ["twilio:sms:write", "twilio:calls:write", "twilio:messages:read", "twilio:conversations:read"],
            "tools": [
                "send_sms", "send_whatsapp", "make_call", "list_messages", "get_message",
                "get_call", "list_calls", "create_messaging_service", "list_phone_numbers",
                "buy_phone_number", "send_bulk_sms"
            ],
            "agents": ["communication_bot", "support_agent", "notification_service"],
            "install_type": "builtin",
            "auth": "api_key_secret"
        }
    
    async def execute_tool(self, tool_name: str, params: Dict, credentials: Dict) -> Dict:
        account_sid = credentials.get("account_sid")
        auth_token = credentials.get("auth_token")
        
        if not account_sid or not auth_token:
            return {"success": False, "error": "account_sid e auth_token são obrigatórios"}
        
        # Auth Basic para Twilio
        auth_str = f"{account_sid}:{auth_token}"
        auth_bytes = base64.b64encode(auth_str.encode()).decode()
        headers = {
            "Authorization": f"Basic {auth_bytes}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        try:
            if tool_name == "send_sms":
                return await self._send_sms(account_sid, headers, params)
            elif tool_name == "send_whatsapp":
                return await self._send_whatsapp(account_sid, headers, params)
            elif tool_name == "make_call":
                return await self._make_call(account_sid, headers, params)
            elif tool_name == "list_messages":
                return await self._list_messages(account_sid, headers, params)
            elif tool_name == "get_message":
                return await self._get_message(account_sid, headers, params)
            elif tool_name == "list_calls":
                return await self._list_calls(account_sid, headers, params)
            else:
                return {"success": False, "error": f"Tool '{tool_name}' não encontrada"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _send_sms(self, account_sid: str, headers: Dict, params: Dict) -> Dict:
        to = params.get("to")
        from_number = params.get("from")
        body = params.get("body")
        
        if not all([to, from_number, body]):
            return {"success": False, "error": "to, from e body são obrigatórios"}
        
        url = f"{self.base_url}/Accounts/{account_sid}/Messages.json"
        
        data = aiohttp.FormData()
        data.add_field("To", to)
        data.add_field("From", from_number)
        data.add_field("Body", body)
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, data=data) as response:
                if response.status in [200, 201]:
                    data_resp = await response.json()
                    return {
                        "success": True,
                        "message_sid": data_resp.get("sid"),
                        "status": data_resp.get("status"),
                        "to": to,
                        "body_preview": body[:50] + "..." if len(body) > 50 else body
                    }
                error_text = await response.text()
                return {"success": False, "error": f"Erro ao enviar SMS: {response.status} - {error_text}"}
    
    async def _send_whatsapp(self, account_sid: str, headers: Dict, params: Dict) -> Dict:
        to = params.get("to")
        from_number = params.get("from")
        body = params.get("body")
        
        if not all([to, from_number, body]):
            return {"success": False, "error": "to, from e body são obrigatórios"}
        
        # WhatsApp requer prefixo whatsapp:
        to = f"whatsapp:{to}" if not to.startswith("whatsapp:") else to
        from_number = f"whatsapp:{from_number}" if not from_number.startswith("whatsapp:") else from_number
        
        url = f"{self.base_url}/Accounts/{account_sid}/Messages.json"
        
        data = aiohttp.FormData()
        data.add_field("To", to)
        data.add_field("From", from_number)
        data.add_field("Body", body)
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, data=data) as response:
                if response.status in [200, 201]:
                    data_resp = await response.json()
                    return {
                        "success": True,
                        "message_sid": data_resp.get("sid"),
                        "status": data_resp.get("status"),
                        "to": to,
                        "channel": "whatsapp"
                    }
                error_text = await response.text()
                return {"success": False, "error": f"Erro ao enviar WhatsApp: {response.status}"}
    
    async def _make_call(self, account_sid: str, headers: Dict, params: Dict) -> Dict:
        to = params.get("to")
        from_number = params.get("from")
        url_twiml = params.get("url")  # URL com TwiML
        
        if not all([to, from_number, url_twiml]):
            return {"success": False, "error": "to, from e url (TwiML) são obrigatórios"}
        
        url = f"{self.base_url}/Accounts/{account_sid}/Calls.json"
        
        data = aiohttp.FormData()
        data.add_field("To", to)
        data.add_field("From", from_number)
        data.add_field("Url", url_twiml)
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, data=data) as response:
                if response.status in [200, 201]:
                    data_resp = await response.json()
                    return {
                        "success": True,
                        "call_sid": data_resp.get("sid"),
                        "status": data_resp.get("status"),
                        "to": to
                    }
                error_text = await response.text()
                return {"success": False, "error": f"Erro ao fazer chamada: {response.status}"}
    
    async def _list_messages(self, account_sid: str, headers: Dict, params: Dict) -> Dict:
        url = f"{self.base_url}/Accounts/{account_sid}/Messages.json"
        
        query_params = {}
        if "to" in params:
            query_params["To"] = params["to"]
        if "from" in params:
            query_params["From"] = params["from"]
        if "date_sent" in params:
            query_params["DateSent"] = params["date_sent"]
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=query_params) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        "success": True,
                        "messages": data.get("messages", []),
                        "count": len(data.get("messages", []))
                    }
                return {"success": False, "error": f"Erro: {response.status}"}
    
    async def _get_message(self, account_sid: str, headers: Dict, params: Dict) -> Dict:
        message_sid = params.get("message_sid")
        if not message_sid:
            return {"success": False, "error": "message_sid é obrigatório"}
        
        url = f"{self.base_url}/Accounts/{account_sid}/Messages/{message_sid}.json"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    return {"success": True, "message": data}
                return {"success": False, "error": f"Mensagem não encontrada: {response.status}"}
    
    async def _list_calls(self, account_sid: str, headers: Dict, params: Dict) -> Dict:
        url = f"{self.base_url}/Accounts/{account_sid}/Calls.json"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        "success": True,
                        "calls": data.get("calls", []),
                        "count": len(data.get("calls", []))
                    }
                return {"success": False, "error": f"Erro: {response.status}"}
    
    async def stream_tool_execution(self, tool_name: str, params: Dict, credentials: Dict) -> AsyncGenerator[Dict, None]:
        yield {"type": "tool_call", "tool": tool_name, "status": "executing", "message": f"📞 Executando {tool_name} no Twilio..."}
        result = await self.execute_tool(tool_name, params, credentials)
        if result["success"]:
            yield {"type": "tool_result", "tool": tool_name, "status": "completed", "result": result}
        else:
            yield {"type": "tool_result", "tool": tool_name, "status": "error", "error": result.get("error")}


twilio_mcp = TwilioMCP()
