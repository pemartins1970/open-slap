"""
HubSpot MCP Integration
CRM e Marketing Automation para OpenSlap
"""

from typing import Dict, Any, List, Optional
import aiohttp
import json
from datetime import datetime, timedelta

class HubSpotMCP:
    """
    HubSpot MCP - CRM e Marketing Automation
    
    Funcionalidades:
    - Gestão de contatos e empresas
    - Deals (negócios/oportunidades)
    - Tarefas e atividades
    - Email marketing
    - Automação de workflows
    - Analytics e relatórios
    """
    
    def __init__(self, access_token: str):
        self.access_token = access_token
        self.base_url = "https://api.hubapi.com"
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
    
    async def _make_request(self, method: str, endpoint: str, data: Dict = None) -> Dict[str, Any]:
        """Faz requisição à API do HubSpot"""
        url = f"{self.base_url}{endpoint}"
        
        async with aiohttp.ClientSession() as session:
            async with session.request(
                method=method,
                url=url,
                headers=self.headers,
                json=data
            ) as response:
                if response.status == 200 or response.status == 201:
                    return await response.json()
                else:
                    error_text = await response.text()
                    raise Exception(f"HubSpot API Error {response.status}: {error_text}")
    
    # ========== CONTACTS ==========
    
    async def create_contact(self, email: str, firstname: str = None, lastname: str = None, 
                            phone: str = None, company: str = None, **properties) -> Dict[str, Any]:
        """
        Cria um novo contato no HubSpot
        
        Args:
            email: Email do contato (obrigatório)
            firstname: Primeiro nome
            lastname: Sobrenome
            phone: Telefone
            company: Empresa
            **properties: Propriedades adicionais
        """
        endpoint = "/crm/v3/objects/contacts"
        
        properties_dict = {
            "email": email,
            "firstname": firstname or "",
            "lastname": lastname or "",
            "phone": phone or "",
            "company": company or ""
        }
        properties_dict.update(properties)
        
        data = {"properties": properties_dict}
        
        return await self._make_request("POST", endpoint, data)
    
    async def get_contact(self, contact_id: str) -> Dict[str, Any]:
        """Obtém detalhes de um contato"""
        endpoint = f"/crm/v3/objects/contacts/{contact_id}"
        return await self._make_request("GET", endpoint)
    
    async def get_contact_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Busca contato por email"""
        endpoint = f"/crm/v3/objects/contacts/{email}?idProperty=email"
        try:
            return await self._make_request("GET", endpoint)
        except:
            return None
    
    async def list_contacts(self, limit: int = 100, after: str = None) -> Dict[str, Any]:
        """
        Lista todos os contatos
        
        Args:
            limit: Número máximo de resultados (max 100)
            after: Token de paginação
        """
        endpoint = f"/crm/v3/objects/contacts?limit={limit}"
        if after:
            endpoint += f"&after={after}"
        return await self._make_request("GET", endpoint)
    
    async def update_contact(self, contact_id: str, **properties) -> Dict[str, Any]:
        """Atualiza um contato existente"""
        endpoint = f"/crm/v3/objects/contacts/{contact_id}"
        data = {"properties": properties}
        return await self._make_request("PATCH", endpoint, data)
    
    async def delete_contact(self, contact_id: str) -> bool:
        """Remove um contato"""
        endpoint = f"/crm/v3/objects/contacts/{contact_id}"
        try:
            await self._make_request("DELETE", endpoint)
            return True
        except:
            return False
    
    async def search_contacts(self, query: str, limit: int = 100) -> Dict[str, Any]:
        """
        Busca contatos por texto
        
        Args:
            query: Termo de busca
            limit: Limite de resultados
        """
        endpoint = "/crm/v3/objects/contacts/search"
        data = {
            "query": query,
            "limit": limit,
            "properties": ["email", "firstname", "lastname", "phone", "company"]
        }
        return await self._make_request("POST", endpoint, data)
    
    # ========== COMPANIES ==========
    
    async def create_company(self, name: str, domain: str = None, 
                             industry: str = None, **properties) -> Dict[str, Any]:
        """
        Cria uma nova empresa
        
        Args:
            name: Nome da empresa
            domain: Domínio do site
            industry: Indústria/setor
            **properties: Propriedades adicionais
        """
        endpoint = "/crm/v3/objects/companies"
        
        properties_dict = {
            "name": name,
            "domain": domain or "",
            "industry": industry or ""
        }
        properties_dict.update(properties)
        
        data = {"properties": properties_dict}
        return await self._make_request("POST", endpoint, data)
    
    async def get_company(self, company_id: str) -> Dict[str, Any]:
        """Obtém detalhes de uma empresa"""
        endpoint = f"/crm/v3/objects/companies/{company_id}"
        return await self._make_request("GET", endpoint)
    
    async def list_companies(self, limit: int = 100, after: str = None) -> Dict[str, Any]:
        """Lista todas as empresas"""
        endpoint = f"/crm/v3/objects/companies?limit={limit}"
        if after:
            endpoint += f"&after={after}"
        return await self._make_request("GET", endpoint)
    
    async def update_company(self, company_id: str, **properties) -> Dict[str, Any]:
        """Atualiza uma empresa"""
        endpoint = f"/crm/v3/objects/companies/{company_id}"
        data = {"properties": properties}
        return await self._make_request("PATCH", endpoint, data)
    
    async def associate_contact_to_company(self, contact_id: str, company_id: str) -> Dict[str, Any]:
        """Associa um contato a uma empresa"""
        endpoint = f"/crm/v3/objects/contacts/{contact_id}/associations/companies/{company_id}"
        return await self._make_request("PUT", endpoint)
    
    # ========== DEALS ==========
    
    async def create_deal(self, dealname: str, amount: float = None, 
                         dealstage: str = None, pipeline: str = None,
                         closedate: str = None, **properties) -> Dict[str, Any]:
        """
        Cria um novo negócio/deal
        
        Args:
            dealname: Nome do negócio
            amount: Valor do negócio
            dealstage: Estágio do funil
            pipeline: Pipeline de vendas
            closedate: Data de fechamento (YYYY-MM-DD)
            **properties: Propriedades adicionais
        """
        endpoint = "/crm/v3/objects/deals"
        
        properties_dict = {
            "dealname": dealname,
            "amount": str(amount) if amount else "0",
            "dealstage": dealstage or "",
            "pipeline": pipeline or "",
            "closedate": closedate or ""
        }
        properties_dict.update(properties)
        
        data = {"properties": properties_dict}
        return await self._make_request("POST", endpoint, data)
    
    async def get_deal(self, deal_id: str) -> Dict[str, Any]:
        """Obtém detalhes de um negócio"""
        endpoint = f"/crm/v3/objects/deals/{deal_id}"
        return await self._make_request("GET", endpoint)
    
    async def list_deals(self, limit: int = 100, after: str = None) -> Dict[str, Any]:
        """Lista todos os negócios"""
        endpoint = f"/crm/v3/objects/deals?limit={limit}"
        if after:
            endpoint += f"&after={after}"
        return await self._make_request("GET", endpoint)
    
    async def update_deal(self, deal_id: str, **properties) -> Dict[str, Any]:
        """Atualiza um negócio"""
        endpoint = f"/crm/v3/objects/deals/{deal_id}"
        data = {"properties": properties}
        return await self._make_request("PATCH", endpoint, data)
    
    async def associate_deal_to_contact(self, deal_id: str, contact_id: str) -> Dict[str, Any]:
        """Associa um negócio a um contato"""
        endpoint = f"/crm/v3/objects/deals/{deal_id}/associations/contacts/{contact_id}"
        return await self._make_request("PUT", endpoint)
    
    async def associate_deal_to_company(self, deal_id: str, company_id: str) -> Dict[str, Any]:
        """Associa um negócio a uma empresa"""
        endpoint = f"/crm/v3/objects/deals/{deal_id}/associations/companies/{company_id}"
        return await self._make_request("PUT", endpoint)
    
    # ========== TASKS ==========
    
    async def create_task(self, subject: str, task_type: str = "TODO",
                         due_date: str = None, notes: str = None,
                         owner_id: str = None) -> Dict[str, Any]:
        """
        Cria uma tarefa/engagement
        
        Args:
            subject: Assunto da tarefa
            task_type: Tipo (TODO, CALL, EMAIL, etc)
            due_date: Data de vencimento (timestamp)
            notes: Notas da tarefa
            owner_id: ID do responsável
        """
        endpoint = "/engagements/v1/engagements"
        
        data = {
            "engagement": {
                "active": True,
                "type": "TASK",
                "ownerId": owner_id
            },
            "metadata": {
                "subject": subject,
                "taskType": task_type,
                "reminders": [],
                "notes": notes or ""
            }
        }
        
        if due_date:
            data["engagement"]["timestamp"] = int(due_date)
        
        return await self._make_request("POST", endpoint, data)
    
    async def get_task(self, task_id: str) -> Dict[str, Any]:
        """Obtém detalhes de uma tarefa"""
        endpoint = f"/engagements/v1/engagements/{task_id}"
        return await self._make_request("GET", endpoint)
    
    async def complete_task(self, task_id: str) -> Dict[str, Any]:
        """Marca uma tarefa como concluída"""
        endpoint = f"/engagements/v1/engagements/{task_id}"
        data = {
            "engagement": {
                "active": False,
                "type": "TASK"
            }
        }
        return await self._make_request("PUT", endpoint, data)
    
    # ========== EMAIL MARKETING ==========
    
    async def create_email(self, subject: str, content: str, 
                          recipient_email: str = None, 
                          contact_id: str = None) -> Dict[str, Any]:
        """
        Registra um email enviado
        
        Args:
            subject: Assunto do email
            content: Conteúdo do email
            recipient_email: Email do destinatário
            contact_id: ID do contato no HubSpot
        """
        endpoint = "/engagements/v1/engagements"
        
        data = {
            "engagement": {
                "active": True,
                "type": "EMAIL"
            },
            "metadata": {
                "subject": subject,
                "html": content,
                "text": content
            }
        }
        
        if contact_id:
            data["associations"] = {
                "contactIds": [int(contact_id)]
            }
        
        return await self._make_request("POST", endpoint, data)
    
    # ========== ANALYTICS ==========
    
    async def get_deal_pipeline_report(self) -> Dict[str, Any]:
        """Obtém relatório do pipeline de vendas"""
        endpoint = "/crm/v3/pipelines/deals"
        return await self._make_request("GET", endpoint)
    
    async def get_contact_lifecycle_stages(self) -> Dict[str, Any]:
        """Obtém distribuição de estágios do lifecycle"""
        endpoint = "/crm/v3/properties/contacts/lifecyclestage/options"
        return await self._make_request("GET", endpoint)
    
    async def count_contacts(self) -> int:
        """Retorna o total de contatos"""
        endpoint = "/crm/v3/objects/contacts?limit=1&count=1"
        result = await self._make_request("GET", endpoint)
        return result.get("total", 0)
    
    async def count_deals(self) -> int:
        """Retorna o total de negócios"""
        endpoint = "/crm/v3/objects/deals?limit=1&count=1"
        result = await self._make_request("GET", endpoint)
        return result.get("total", 0)
    
    # ========== WORKFLOWS ==========
    
    async def list_workflows(self, limit: int = 100) -> Dict[str, Any]:
        """Lista todos os workflows de automação"""
        endpoint = f"/automation/v4/workflows?limit={limit}"
        return await self._make_request("GET", endpoint)
    
    async def get_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """Obtém detalhes de um workflow"""
        endpoint = f"/automation/v4/workflows/{workflow_id}"
        return await self._make_request("GET", endpoint)
    
    async def enroll_contact_in_workflow(self, workflow_id: str, email: str) -> Dict[str, Any]:
        """
        Inscreve um contato em um workflow
        
        Args:
            workflow_id: ID do workflow
            email: Email do contato
        """
        endpoint = f"/automation/v4/workflows/{workflow_id}/enrollments/contacts/{email}"
        return await self._make_request("PUT", endpoint)
    
    async def unenroll_contact_from_workflow(self, workflow_id: str, email: str) -> bool:
        """Remove um contato de um workflow"""
        endpoint = f"/automation/v4/workflows/{workflow_id}/enrollments/contacts/{email}"
        try:
            await self._make_request("DELETE", endpoint)
            return True
        except:
            return False


# Instância global para uso no sistema
hubspot_mcp = None

def init_hubspot_mcp(access_token: str):
    """Inicializa o HubSpot MCP"""
    global hubspot_mcp
    hubspot_mcp = HubSpotMCP(access_token)
    return hubspot_mcp
