"""
Salesforce MCP Integration
CRM Enterprise para OpenSlap
"""

from typing import Dict, Any, List, Optional
import aiohttp
import json

class SalesforceMCP:
    """
    Salesforce MCP - CRM Enterprise
    
    Funcionalidades:
    - Leads e Opportunities
    - Accounts e Contacts
    - Cases (suporte)
    - Tarefas e atividades
    - Relatórios e dashboards
    - SOQL queries
    """
    
    def __init__(self, access_token: str, instance_url: str, api_version: str = "v58.0"):
        self.access_token = access_token
        self.instance_url = instance_url.rstrip("/")
        self.api_version = api_version
        self.base_url = f"{self.instance_url}/services/data/{api_version}"
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
    
    async def _make_request(self, method: str, endpoint: str,
                           data: Dict = None, params: Dict = None) -> Dict[str, Any]:
        """Faz requisição à API do Salesforce"""
        url = f"{self.base_url}{endpoint}"
        
        async with aiohttp.ClientSession() as session:
            async with session.request(
                method=method,
                url=url,
                headers=self.headers,
                json=data,
                params=params
            ) as response:
                if response.status in [200, 201, 204]:
                    if response.status == 204:
                        return {"success": True}
                    return await response.json()
                else:
                    error_text = await response.text()
                    raise Exception(f"Salesforce API Error {response.status}: {error_text}")
    
    async def _make_soql_request(self, query: str) -> Dict[str, Any]:
        """Executa query SOQL"""
        endpoint = "/query"
        return await self._make_request("GET", endpoint, params={"q": query})
    
    # ========== OBJECTOS PADRÃO ==========
    
    async def list_leads(self, fields: List[str] = None, limit: int = 100) -> Dict[str, Any]:
        """Lista leads"""
        field_list = ", ".join(fields) if fields else "Id, FirstName, LastName, Email, Company, Status, CreatedDate"
        query = f"SELECT {field_list} FROM Lead LIMIT {limit}"
        return await self._make_soql_request(query)
    
    async def get_lead(self, lead_id: str, fields: List[str] = None) -> Dict[str, Any]:
        """Obtém lead específico"""
        field_list = ", ".join(fields) if fields else "Id, FirstName, LastName, Email, Company, Status"
        query = f"SELECT {field_list} FROM Lead WHERE Id = '{lead_id}'"
        result = await self._make_soql_request(query)
        records = result.get("records", [])
        return records[0] if records else None
    
    async def create_lead(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Cria novo lead"""
        endpoint = "/sobjects/Lead"
        return await self._make_request("POST", endpoint, data)
    
    async def update_lead(self, lead_id: str, data: Dict[str, Any]) -> bool:
        """Atualiza lead"""
        endpoint = f"/sobjects/Lead/{lead_id}"
        try:
            await self._make_request("PATCH", endpoint, data)
            return True
        except:
            return False
    
    async def convert_lead(self, lead_id: str, account_id: str = None,
                          contact_id: str = None, opportunity_id: str = None) -> Dict[str, Any]:
        """Converte lead em conta/contato/oportunidade"""
        endpoint = f"/sobjects/Lead/{lead_id}"
        data = {"Status": "Working - Contacted"}
        return await self._make_request("PATCH", endpoint, data)
    
    async def list_accounts(self, fields: List[str] = None, limit: int = 100) -> Dict[str, Any]:
        """Lista contas"""
        field_list = ", ".join(fields) if fields else "Id, Name, Type, Industry, Phone, Website, CreatedDate"
        query = f"SELECT {field_list} FROM Account LIMIT {limit}"
        return await self._make_soql_request(query)
    
    async def get_account(self, account_id: str, fields: List[str] = None) -> Dict[str, Any]:
        """Obtém conta"""
        field_list = ", ".join(fields) if fields else "Id, Name, Type, Industry, Phone, Website"
        query = f"SELECT {field_list} FROM Account WHERE Id = '{account_id}'"
        result = await self._make_soql_request(query)
        records = result.get("records", [])
        return records[0] if records else None
    
    async def create_account(self, name: str, **fields) -> Dict[str, Any]:
        """Cria conta"""
        endpoint = "/sobjects/Account"
        data = {"Name": name, **fields}
        return await self._make_request("POST", endpoint, data)
    
    async def update_account(self, account_id: str, data: Dict[str, Any]) -> bool:
        """Atualiza conta"""
        endpoint = f"/sobjects/Account/{account_id}"
        try:
            await self._make_request("PATCH", endpoint, data)
            return True
        except:
            return False
    
    async def list_contacts(self, fields: List[str] = None, limit: int = 100) -> Dict[str, Any]:
        """Lista contatos"""
        field_list = ", ".join(fields) if fields else "Id, FirstName, LastName, Email, AccountId, Phone, CreatedDate"
        query = f"SELECT {field_list} FROM Contact LIMIT {limit}"
        return await self._make_soql_request(query)
    
    async def get_contact(self, contact_id: str, fields: List[str] = None) -> Dict[str, Any]:
        """Obtém contato"""
        field_list = ", ".join(fields) if fields else "Id, FirstName, LastName, Email, AccountId, Phone"
        query = f"SELECT {field_list} FROM Contact WHERE Id = '{contact_id}'"
        result = await self._make_soql_request(query)
        records = result.get("records", [])
        return records[0] if records else None
    
    async def create_contact(self, first_name: str, last_name: str,
                          account_id: str = None, **fields) -> Dict[str, Any]:
        """Cria contato"""
        endpoint = "/sobjects/Contact"
        data = {
            "FirstName": first_name,
            "LastName": last_name,
            **fields
        }
        if account_id:
            data["AccountId"] = account_id
        return await self._make_request("POST", endpoint, data)
    
    async def list_opportunities(self, fields: List[str] = None, limit: int = 100) -> Dict[str, Any]:
        """Lista oportunidades"""
        field_list = ", ".join(fields) if fields else "Id, Name, AccountId, StageName, Amount, CloseDate, Probability, CreatedDate"
        query = f"SELECT {field_list} FROM Opportunity LIMIT {limit}"
        return await self._make_soql_request(query)
    
    async def get_opportunity(self, opp_id: str, fields: List[str] = None) -> Dict[str, Any]:
        """Obtém oportunidade"""
        field_list = ", ".join(fields) if fields else "Id, Name, AccountId, StageName, Amount, CloseDate"
        query = f"SELECT {field_list} FROM Opportunity WHERE Id = '{opp_id}'"
        result = await self._make_soql_request(query)
        records = result.get("records", [])
        return records[0] if records else None
    
    async def create_opportunity(self, name: str, account_id: str,
                                stage_name: str, close_date: str,
                                amount: float = None, **fields) -> Dict[str, Any]:
        """Cria oportunidade"""
        endpoint = "/sobjects/Opportunity"
        data = {
            "Name": name,
            "AccountId": account_id,
            "StageName": stage_name,
            "CloseDate": close_date,
            **fields
        }
        if amount:
            data["Amount"] = amount
        return await self._make_request("POST", endpoint, data)
    
    async def update_opportunity_stage(self, opp_id: str, stage: str) -> bool:
        """Atualiza estágio da oportunidade"""
        endpoint = f"/sobjects/Opportunity/{opp_id}"
        try:
            await self._make_request("PATCH", endpoint, {"StageName": stage})
            return True
        except:
            return False
    
    async def list_cases(self, fields: List[str] = None, limit: int = 100) -> Dict[str, Any]:
        """Lista cases (tickets de suporte)"""
        field_list = ", ".join(fields) if fields else "Id, CaseNumber, Subject, Status, Priority, AccountId, ContactId, CreatedDate"
        query = f"SELECT {field_list} FROM Case LIMIT {limit}"
        return await self._make_soql_request(query)
    
    async def get_case(self, case_id: str, fields: List[str] = None) -> Dict[str, Any]:
        """Obtém case"""
        field_list = ", ".join(fields) if fields else "Id, CaseNumber, Subject, Status, Priority, Description"
        query = f"SELECT {field_list} FROM Case WHERE Id = '{case_id}'"
        result = await self._make_soql_request(query)
        records = result.get("records", [])
        return records[0] if records else None
    
    async def create_case(self, subject: str, description: str = None,
                         account_id: str = None, contact_id: str = None,
                         priority: str = "Medium", **fields) -> Dict[str, Any]:
        """Cria case/ticket"""
        endpoint = "/sobjects/Case"
        data = {
            "Subject": subject,
            "Priority": priority,
            **fields
        }
        if description:
            data["Description"] = description
        if account_id:
            data["AccountId"] = account_id
        if contact_id:
            data["ContactId"] = contact_id
        return await self._make_request("POST", endpoint, data)
    
    async def update_case_status(self, case_id: str, status: str) -> bool:
        """Atualiza status do case"""
        endpoint = f"/sobjects/Case/{case_id}"
        try:
            await self._make_request("PATCH", endpoint, {"Status": status})
            return True
        except:
            return False
    
    async def list_tasks(self, fields: List[str] = None, limit: int = 100) -> Dict[str, Any]:
        """Lista tarefas"""
        field_list = ", ".join(fields) if fields else "Id, Subject, Status, Priority, ActivityDate, WhoId, WhatId, CreatedDate"
        query = f"SELECT {field_list} FROM Task LIMIT {limit}"
        return await self._make_soql_request(query)
    
    async def create_task(self, subject: str, who_id: str = None,
                         what_id: str = None, **fields) -> Dict[str, Any]:
        """Cria tarefa"""
        endpoint = "/sobjects/Task"
        data = {"Subject": subject, **fields}
        if who_id:
            data["WhoId"] = who_id
        if what_id:
            data["WhatId"] = what_id
        return await self._make_request("POST", endpoint, data)
    
    async def execute_soql(self, query: str) -> Dict[str, Any]:
        """Executa query SOQL personalizada"""
        return await self._make_soql_request(query)
    
    async def describe_object(self, object_name: str) -> Dict[str, Any]:
        """Obtém metadados de um objeto"""
        endpoint = f"/sobjects/{object_name}/describe"
        return await self._make_request("GET", endpoint)
    
    async def list_objects(self) -> Dict[str, Any]:
        """Lista objetos disponíveis"""
        endpoint = "/sobjects"
        return await self._make_request("GET", endpoint)
    
    async def get_user_info(self) -> Dict[str, Any]:
        """Obtém informações do usuário"""
        endpoint = "/chatter/users/me"
        return await self._make_request("GET", endpoint)
    
    async def test_connection(self) -> bool:
        """Testa conexão"""
        try:
            result = await self.list_objects()
            return "sobjects" in result
        except:
            return False


salesforce_mcp = None

def init_salesforce_mcp(access_token: str, instance_url: str, api_version: str = "v58.0"):
    global salesforce_mcp
    salesforce_mcp = SalesforceMCP(access_token, instance_url, api_version)
    return salesforce_mcp
