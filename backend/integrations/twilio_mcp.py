"""
Twilio MCP Integration
SMS, WhatsApp e Telefone para OpenSlap
"""

from typing import Dict, Any, List, Optional
import aiohttp
from aiohttp import BasicAuth
import json

class TwilioMCP:
    """
    Twilio MCP - Comunicação SMS, WhatsApp e Voz
    
    Funcionalidades:
    - SMS e MMS
    - WhatsApp Business
    - Chamadas de voz
    - Verificação (2FA)
    - Gerenciamento de números
    """
    
    def __init__(self, account_sid: str, auth_token: str):
        self.account_sid = account_sid
        self.auth_token = auth_token
        self.base_url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}"
        self.auth = BasicAuth(account_sid, auth_token)
    
    async def _make_request(self, method: str, endpoint: str,
                           data: Dict = None, params: Dict = None) -> Dict[str, Any]:
        """Faz requisição à API do Twilio"""
        url = f"{self.base_url}{endpoint}"
        
        async with aiohttp.ClientSession() as session:
            async with session.request(
                method=method,
                url=url,
                auth=self.auth,
                data=data,
                params=params
            ) as response:
                if response.status in [200, 201, 202, 204]:
                    try:
                        return await response.json()
                    except:
                        return {"success": True, "status": response.status}
                else:
                    error_text = await response.text()
                    raise Exception(f"Twilio API Error {response.status}: {error_text}")
    
    # ========== SMS ==========
    
    async def send_sms(self, to: str, from_number: str, body: str,
                      media_url: str = None, status_callback: str = None) -> Dict[str, Any]:
        """
        Envia SMS
        
        Args:
            to: Número destino (ex: +5511999999999)
            from_number: Número Twilio
            body: Texto da mensagem
            media_url: URL de mídia (opcional, para MMS)
            status_callback: URL para callback de status
        """
        endpoint = "/Messages.json"
        
        data = {
            "To": to,
            "From": from_number,
            "Body": body
        }
        
        if media_url:
            data["MediaUrl"] = media_url
        if status_callback:
            data["StatusCallback"] = status_callback
        
        return await self._make_request("POST", endpoint, data)
    
    async def get_message(self, message_sid: str) -> Dict[str, Any]:
        """Obtém detalhes de uma mensagem"""
        endpoint = f"/Messages/{message_sid}.json"
        return await self._make_request("GET", endpoint)
    
    async def list_messages(self, to: str = None, from_number: str = None,
                           date_sent: str = None, limit: int = 50) -> Dict[str, Any]:
        """Lista mensagens"""
        endpoint = "/Messages.json"
        
        params = {"PageSize": limit}
        if to:
            params["To"] = to
        if from_number:
            params["From"] = from_number
        if date_sent:
            params["DateSent"] = date_sent
        
        return await self._make_request("GET", endpoint, params=params)
    
    async def delete_message(self, message_sid: str) -> bool:
        """Remove mensagem"""
        endpoint = f"/Messages/{message_sid}.json"
        try:
            await self._make_request("DELETE", endpoint)
            return True
        except:
            return False
    
    # ========== WHATSAPP ==========
    
    async def send_whatsapp(self, to: str, from_number: str, body: str,
                          media_url: str = None, template_sid: str = None) -> Dict[str, Any]:
        """
        Envia mensagem WhatsApp
        
        Args:
            to: Número destino (ex: whatsapp:+5511999999999)
            from_number: Número Twilio (ex: whatsapp:+14155238886)
            body: Texto ou template
            media_url: URL de mídia
            template_sid: ID do template (para mensagens template)
        """
        endpoint = "/Messages.json"
        
        data = {
            "To": to if to.startswith("whatsapp:") else f"whatsapp:{to}",
            "From": from_number if from_number.startswith("whatsapp:") else f"whatsapp:{from_number}"
        }
        
        if template_sid:
            data["ContentSid"] = template_sid
        else:
            data["Body"] = body
        
        if media_url:
            data["MediaUrl"] = media_url
        
        return await self._make_request("POST", endpoint, data)
    
    async def send_whatsapp_template(self, to: str, from_number: str,
                                     template_name: str, language: str = "pt_BR",
                                     components: List[Dict] = None) -> Dict[str, Any]:
        """Envia template de WhatsApp"""
        endpoint = "/Messages.json"
        
        content_variables = {}
        if components:
            for comp in components:
                if comp.get("type") == "body":
                    params = comp.get("parameters", [])
                    for i, param in enumerate(params):
                        content_variables[str(i)] = param.get("text", "")
        
        data = {
            "To": f"whatsapp:{to}",
            "From": f"whatsapp:{from_number}",
            "ContentSid": template_name
        }
        
        if content_variables:
            data["ContentVariables"] = json.dumps(content_variables)
        
        return await self._make_request("POST", endpoint, data)
    
    # ========== CHAMADAS ==========
    
    async def make_call(self, to: str, from_number: str,
                       twiml: str = None, url: str = None,
                       status_callback: str = None) -> Dict[str, Any]:
        """
        Inicia chamada de voz
        
        Args:
            to: Número destino
            from_number: Número Twilio
            twiml: XML de instruções de voz
            url: URL com TwiML
        """
        endpoint = "/Calls.json"
        
        data = {
            "To": to,
            "From": from_number
        }
        
        if twiml:
            data["Twiml"] = twiml
        elif url:
            data["Url"] = url
        
        if status_callback:
            data["StatusCallback"] = status_callback
        
        return await self._make_request("POST", endpoint, data)
    
    async def get_call(self, call_sid: str) -> Dict[str, Any]:
        """Obtém detalhes de chamada"""
        endpoint = f"/Calls/{call_sid}.json"
        return await self._make_request("GET", endpoint)
    
    async def end_call(self, call_sid: str) -> bool:
        """Encerra chamada"""
        endpoint = f"/Calls/{call_sid}.json"
        try:
            await self._make_request("POST", endpoint, {"Status": "completed"})
            return True
        except:
            return False
    
    async def list_calls(self, to: str = None, from_number: str = None,
                        status: str = None, limit: int = 50) -> Dict[str, Any]:
        """Lista chamadas"""
        endpoint = "/Calls.json"
        
        params = {"PageSize": limit}
        if to:
            params["To"] = to
        if from_number:
            params["From"] = from_number
        if status:
            params["Status"] = status
        
        return await self._make_request("GET", endpoint, params=params)
    
    # ========== VERIFICAÇÃO (2FA) ==========
    
    async def send_verification(self, to: str, channel: str = "sms",
                               service_sid: str = None, locale: str = "pt") -> Dict[str, Any]:
        """
        Envia código de verificação
        
        Args:
            to: Número/email para verificação
            channel: sms, voice, email, whatsapp
            service_sid: SID do serviço de verificação
        """
        if not service_sid:
            raise ValueError("service_sid é obrigatório para verificação")
        
        url = f"https://verify.twilio.com/v2/Services/{service_sid}/Verifications"
        
        data = {
            "To": to,
            "Channel": channel,
            "Locale": locale
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=data, auth=self.auth) as response:
                if response.status in [200, 201]:
                    return await response.json()
                else:
                    error_text = await response.text()
                    raise Exception(f"Twilio Verify Error {response.status}: {error_text}")
    
    async def check_verification(self, to: str, code: str,
                                service_sid: str = None) -> Dict[str, Any]:
        """Verifica código"""
        if not service_sid:
            raise ValueError("service_sid é obrigatório para verificação")
        
        url = f"https://verify.twilio.com/v2/Services/{service_sid}/VerificationCheck"
        
        data = {
            "To": to,
            "Code": code
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=data, auth=self.auth) as response:
                if response.status in [200, 201]:
                    return await response.json()
                else:
                    error_text = await response.text()
                    raise Exception(f"Twilio Verify Error {response.status}: {error_text}")
    
    # ========== NÚMEROS ==========
    
    async def list_incoming_numbers(self, phone_number: str = None,
                                    limit: int = 50) -> Dict[str, Any]:
        """Lista números de telefone"""
        endpoint = "/IncomingPhoneNumbers.json"
        
        params = {"PageSize": limit}
        if phone_number:
            params["PhoneNumber"] = phone_number
        
        return await self._make_request("GET", endpoint, params=params)
    
    async def get_available_numbers(self, country: str = "BR",
                                    area_code: str = None,
                                    limit: int = 10) -> Dict[str, Any]:
        """Lista números disponíveis para compra"""
        endpoint = f"/AvailablePhoneNumbers/{country}/Local.json"
        
        params = {"PageSize": limit}
        if area_code:
            params["AreaCode"] = area_code
        
        return await self._make_request("GET", endpoint, params=params)
    
    async def purchase_number(self, phone_number: str) -> Dict[str, Any]:
        """Compra número de telefone"""
        endpoint = "/IncomingPhoneNumbers.json"
        data = {"PhoneNumber": phone_number}
        return await self._make_request("POST", endpoint, data)
    
    # ========== UTILITÁRIOS ==========
    
    async def get_account_info(self) -> Dict[str, Any]:
        """Obtém informações da conta"""
        url = f"https://api.twilio.com/2010-04-01/Accounts/{self.account_sid}.json"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, auth=self.auth) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    raise Exception(f"Twilio API Error {response.status}: {error_text}")
    
    async def test_connection(self) -> bool:
        """Testa conexão"""
        try:
            await self.get_account_info()
            return True
        except:
            return False


twilio_mcp = None

def init_twilio_mcp(account_sid: str, auth_token: str):
    global twilio_mcp
    twilio_mcp = TwilioMCP(account_sid, auth_token)
    return twilio_mcp
