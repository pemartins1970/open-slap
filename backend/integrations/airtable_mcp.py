"""
Airtable MCP Integration
Base de dados relacional para OpenSlap
"""

from typing import Dict, Any, List, Optional, Union
import aiohttp
import json

class AirtableMCP:
    """
    Airtable MCP - Base de Dados Relacional
    
    Funcionalidades:
    - Gestão de bases e tabelas
    - Registros (CRUD)
    - Campos e tipos
    - Fórmulas e filtros
    - Anexos
    - Views
    """
    
    def __init__(self, api_key: str, base_id: str = None):
        self.api_key = api_key
        self.base_id = base_id
        self.base_url = "https://api.airtable.com/v0"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    async def _make_request(self, method: str, endpoint: str, 
                           data: Dict = None, params: Dict = None) -> Dict[str, Any]:
        """Faz requisição à API do Airtable"""
        url = f"{self.base_url}{endpoint}"
        
        async with aiohttp.ClientSession() as session:
            async with session.request(
                method=method,
                url=url,
                headers=self.headers,
                json=data,
                params=params
            ) as response:
                if response.status in [200, 201]:
                    return await response.json()
                else:
                    error_text = await response.text()
                    raise Exception(f"Airtable API Error {response.status}: {error_text}")
    
    # ========== BASES ==========
    
    async def list_bases(self) -> Dict[str, Any]:
        """Lista todas as bases disponíveis"""
        url = "https://api.airtable.com/v0/meta/bases"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=self.headers) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    raise Exception(f"Airtable API Error {response.status}: {error_text}")
    
    async def get_base_schema(self, base_id: str = None) -> Dict[str, Any]:
        """Obtém schema de uma base"""
        target_base = base_id or self.base_id
        
        url = f"https://api.airtable.com/v0/meta/bases/{target_base}/tables"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=self.headers) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    raise Exception(f"Airtable API Error {response.status}: {error_text}")
    
    # ========== TABELAS (TABLES) ==========
    
    async def list_tables(self, base_id: str = None) -> List[Dict[str, Any]]:
        """Lista tabelas de uma base"""
        schema = await self.get_base_schema(base_id)
        return schema.get("tables", [])
    
    async def get_table(self, table_name_or_id: str, base_id: str = None) -> Dict[str, Any]:
        """Obtém informações de uma tabela"""
        tables = await self.list_tables(base_id)
        
        for table in tables:
            if table["id"] == table_name_or_id or table["name"] == table_name_or_id:
                return table
        
        raise Exception(f"Tabela {table_name_or_id} não encontrada")
    
    # ========== REGISTROS ==========
    
    async def list_records(self, table_name: str, base_id: str = None,
                          view: str = None, fields: List[str] = None,
                          filter_by_formula: str = None,
                          max_records: int = None,
                          page_size: int = 100,
                          offset: str = None,
                          sort: List[Dict] = None) -> Dict[str, Any]:
        """
        Lista registros de uma tabela
        
        Args:
            table_name: Nome ou ID da tabela
            view: Nome da view para filtrar
            fields: Campos a retornar
            filter_by_formula: Fórmula de filtro Airtable
            max_records: Máximo de registros
            page_size: Registros por página
            offset: Token de paginação
            sort: Lista de ordenação [{"field": "Name", "direction": "asc"}]
        """
        target_base = base_id or self.base_id
        endpoint = f"/{target_base}/{table_name}"
        
        params = {"pageSize": page_size}
        
        if view:
            params["view"] = view
        if fields:
            for field in fields:
                params.setdefault("fields[]", []).append(field)
        if filter_by_formula:
            params["filterByFormula"] = filter_by_formula
        if max_records:
            params["maxRecords"] = max_records
        if offset:
            params["offset"] = offset
        if sort:
            for i, s in enumerate(sort):
                params[f"sort[{i}][field]"] = s["field"]
                params[f"sort[{i}][direction]"] = s.get("direction", "asc")
        
        return await self._make_request("GET", endpoint, params=params)
    
    async def get_record(self, table_name: str, record_id: str,
                        base_id: str = None) -> Dict[str, Any]:
        """Obtém um registro específico"""
        target_base = base_id or self.base_id
        endpoint = f"/{target_base}/{table_name}/{record_id}"
        return await self._make_request("GET", endpoint)
    
    async def create_record(self, table_name: str, fields: Dict[str, Any],
                           base_id: str = None) -> Dict[str, Any]:
        """
        Cria novo registro
        
        Args:
            fields: Dicionário de campos e valores
        """
        target_base = base_id or self.base_id
        endpoint = f"/{target_base}/{table_name}"
        
        data = {"fields": fields}
        return await self._make_request("POST", endpoint, data)
    
    async def create_records(self, table_name: str, records: List[Dict[str, Any]],
                            base_id: str = None) -> Dict[str, Any]:
        """Cria múltiplos registros (batch)"""
        target_base = base_id or self.base_id
        endpoint = f"/{target_base}/{table_name}"
        
        data = {"records": [{"fields": r} for r in records]}
        return await self._make_request("POST", endpoint, data)
    
    async def update_record(self, table_name: str, record_id: str,
                         fields: Dict[str, Any], base_id: str = None,
                         destructive: bool = False) -> Dict[str, Any]:
        """
        Atualiza registro
        
        Args:
            destructive: Se True, substitui todos os campos
        """
        target_base = base_id or self.base_id
        endpoint = f"/{target_base}/{table_name}/{record_id}"
        
        data = {"fields": fields}
        
        method = "PUT" if destructive else "PATCH"
        return await self._make_request(method, endpoint, data)
    
    async def update_records(self, table_name: str, records: List[Dict],
                            base_id: str = None,
                            destructive: bool = False) -> Dict[str, Any]:
        """Atualiza múltiplos registros"""
        target_base = base_id or self.base_id
        endpoint = f"/{target_base}/{table_name}"
        
        data = {"records": records}
        
        method = "PUT" if destructive else "PATCH"
        return await self._make_request(method, endpoint, data)
    
    async def delete_record(self, table_name: str, record_id: str,
                           base_id: str = None) -> Dict[str, Any]:
        """Remove um registro"""
        target_base = base_id or self.base_id
        endpoint = f"/{target_base}/{table_name}/{record_id}"
        return await self._make_request("DELETE", endpoint)
    
    async def delete_records(self, table_name: str, record_ids: List[str],
                            base_id: str = None) -> Dict[str, Any]:
        """Remove múltiplos registros"""
        target_base = base_id or self.base_id
        endpoint = f"/{target_base}/{table_name}"
        
        params = {"records[]": record_ids}
        return await self._make_request("DELETE", endpoint, params=params)
    
    # ========== ANEXOS ==========
    
    async def upload_attachment(self, table_name: str, record_id: str,
                               field_name: str, file_content: bytes,
                               filename: str, base_id: str = None) -> Dict[str, Any]:
        """Faz upload de anexo"""
        # Airtable requer upload via URL
        # Simplificação: retorna estrutura para upload via URL
        return {
            "fields": {
                field_name: [
                    {
                        "url": f"https://upload-url-for/{filename}",
                        "filename": filename
                    }
                ]
            }
        }
    
    # ========== VIEWS ==========
    
    async def list_views(self, table_name: str, base_id: str = None) -> List[Dict]:
        """Lista views de uma tabela"""
        table = await self.get_table(table_name, base_id)
        return table.get("views", [])
    
    # ========== UTILITÁRIOS ==========
    
    def create_formula_filter(self, conditions: List[tuple]) -> str:
        """
        Cria fórmula de filtro Airtable
        
        Exemplo: [("Status", "=", "Done"), ("Priority", "=", "High")]
        Resultado: AND({Status}="Done", {Priority}="High")
        """
        parts = []
        for field, op, value in conditions:
            if op == "=":
                parts.append(f'{{{field}}}="{value}"')
            elif op == "!=":
                parts.append(f'{{{field}}}!="{value}"')
            elif op == ">":
                parts.append(f'{{{field}}}>{value}')
            elif op == "<":
                parts.append(f'{{{field}}}<{value}')
            elif op == "contains":
                parts.append(f'FIND("{value}", {{{field}}})>0')
        
        if len(parts) == 1:
            return parts[0]
        return f"AND({', '.join(parts)})"
    
    async def test_connection(self) -> bool:
        """Testa conexão"""
        try:
            result = await self.list_bases()
            return "bases" in result
        except:
            return False


# Instância global
airtable_mcp = None

def init_airtable_mcp(api_key: str, base_id: str = None):
    """Inicializa o Airtable MCP"""
    global airtable_mcp
    airtable_mcp = AirtableMCP(api_key, base_id)
    return airtable_mcp
