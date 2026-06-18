"""
Notion MCP - Model Context Protocol para Notion
Integração com Notion API para páginas, databases e wikis

Documentação: https://developers.notion.com/
"""

import json
import logging
from typing import Dict, Any, List, Optional, AsyncGenerator
import aiohttp

logger = logging.getLogger(__name__)


class NotionMCP:
    def __init__(self):
        self.name = "notion"
        self.display_name = "Notion"
        self.version = "1.0.0"
        self.description = "Crie e edite páginas, databases e wikis no Notion"
        self.icon = "📝"
        self.category = "productivity"
        self.tier = "pro"
        self.base_url = "https://api.notion.com/v1"
        
    def get_manifest(self) -> Dict[str, Any]:
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
            "permissions": ["notion:pages:write", "notion:pages:read", "notion:databases:write", "notion:databases:read"],
            "tools": [
                "create_page", "get_page", "update_page", "archive_page",
                "query_database", "create_database", "add_database_item", "update_database_item",
                "list_databases", "get_database", "search", "append_blocks"
            ],
            "agents": ["documentation_writer", "knowledge_manager"],
            "install_type": "builtin",
            "auth": "api_token"
        }
    
    async def execute_tool(self, tool_name: str, params: Dict, credentials: Dict) -> Dict:
        token = credentials.get("token") or credentials.get("access_token")
        if not token:
            return {"success": False, "error": "Notion Token não configurado"}
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json"
        }
        
        try:
            if tool_name == "create_page":
                return await self._create_page(headers, params)
            elif tool_name == "get_page":
                return await self._get_page(headers, params)
            elif tool_name == "update_page":
                return await self._update_page(headers, params)
            elif tool_name == "query_database":
                return await self._query_database(headers, params)
            elif tool_name == "create_database":
                return await self._create_database(headers, params)
            elif tool_name == "add_database_item":
                return await self._add_database_item(headers, params)
            elif tool_name == "list_databases":
                return await self._list_databases(headers, params)
            elif tool_name == "search":
                return await self._search(headers, params)
            elif tool_name == "append_blocks":
                return await self._append_blocks(headers, params)
            else:
                return {"success": False, "error": f"Tool '{tool_name}' não encontrada"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _create_page(self, headers: Dict, params: Dict) -> Dict:
        parent = params.get("parent")
        title = params.get("title")
        content = params.get("content", [])
        
        if not parent or not title:
            return {"success": False, "error": "parent e title são obrigatórios"}
        
        payload = {
            "parent": {"page_id": parent} if not parent.startswith("https") else {"database_id": parent},
            "properties": {
                "title": [{"text": {"content": title}}]
            }
        }
        
        if content:
            payload["children"] = [{"object": "block", "type": "paragraph", 
                                   "paragraph": {"rich_text": [{"type": "text", "text": {"content": c}}]}} 
                                  for c in content]
        
        url = f"{self.base_url}/pages"
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    return {"success": True, "page": {"id": data["id"], "url": data["url"], "title": title}}
                return {"success": False, "error": f"Erro: {response.status}"}
    
    async def _get_page(self, headers: Dict, params: Dict) -> Dict:
        page_id = params.get("page_id")
        if not page_id:
            return {"success": False, "error": "page_id é obrigatório"}
        
        url = f"{self.base_url}/pages/{page_id}"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        "success": True,
                        "page": {"id": data["id"], "url": data["url"], 
                                "created_time": data["created_time"], "last_edited_time": data["last_edited_time"]}
                    }
                return {"success": False, "error": f"Página não encontrada: {response.status}"}
    
    async def _update_page(self, headers: Dict, params: Dict) -> Dict:
        page_id = params.get("page_id")
        title = params.get("title")
        
        if not page_id:
            return {"success": False, "error": "page_id é obrigatório"}
        
        payload = {}
        if title:
            payload["properties"] = {"title": [{"text": {"content": title}}]}
        
        if "archived" in params:
            payload["archived"] = params["archived"]
        
        url = f"{self.base_url}/pages/{page_id}"
        
        async with aiohttp.ClientSession() as session:
            async with session.patch(url, headers=headers, json=payload) as response:
                if response.status == 200:
                    return {"success": True, "message": "Página atualizada com sucesso"}
                return {"success": False, "error": f"Erro: {response.status}"}
    
    async def _query_database(self, headers: Dict, params: Dict) -> Dict:
        database_id = params.get("database_id")
        if not database_id:
            return {"success": False, "error": "database_id é obrigatório"}
        
        url = f"{self.base_url}/databases/{database_id}/query"
        payload = {"page_size": params.get("limit", 100)}
        
        if "filter" in params:
            payload["filter"] = params["filter"]
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    return {"success": True, "results": data["results"], "count": len(data["results"])}
                return {"success": False, "error": f"Erro: {response.status}"}
    
    async def _create_database(self, headers: Dict, params: Dict) -> Dict:
        parent = params.get("parent")
        title = params.get("title")
        properties = params.get("properties", {})
        
        if not parent or not title:
            return {"success": False, "error": "parent e title são obrigatórios"}
        
        url = f"{self.base_url}/databases"
        payload = {
            "parent": {"page_id": parent},
            "title": [{"text": {"content": title}}],
            "properties": properties
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    return {"success": True, "database": {"id": data["id"], "title": title}}
                return {"success": False, "error": f"Erro: {response.status}"}
    
    async def _add_database_item(self, headers: Dict, params: Dict) -> Dict:
        database_id = params.get("database_id")
        properties = params.get("properties", {})
        
        if not database_id:
            return {"success": False, "error": "database_id é obrigatório"}
        
        url = f"{self.base_url}/pages"
        payload = {
            "parent": {"database_id": database_id},
            "properties": properties
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    return {"success": True, "item": {"id": data["id"], "url": data["url"]}}
                return {"success": False, "error": f"Erro: {response.status}"}
    
    async def _list_databases(self, headers: Dict, params: Dict) -> Dict:
        url = f"{self.base_url}/search"
        payload = {"filter": {"value": "database", "property": "object"}, "page_size": params.get("limit", 100)}
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    return {"success": True, "databases": [{"id": d["id"], "title": d["title"][0]["text"]["content"]} 
                                                            for d in data["results"]]}
                return {"success": False, "error": f"Erro: {response.status}"}
    
    async def _search(self, headers: Dict, params: Dict) -> Dict:
        query = params.get("query", "")
        url = f"{self.base_url}/search"
        payload = {"query": query, "page_size": params.get("limit", 20)}
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    return {"success": True, "results": data["results"], "count": len(data["results"])}
                return {"success": False, "error": f"Erro: {response.status}"}
    
    async def _append_blocks(self, headers: Dict, params: Dict) -> Dict:
        block_id = params.get("block_id")
        children = params.get("children", [])
        
        if not block_id or not children:
            return {"success": False, "error": "block_id e children são obrigatórios"}
        
        url = f"{self.base_url}/blocks/{block_id}/children"
        payload = {"children": children}
        
        async with aiohttp.ClientSession() as session:
            async with session.patch(url, headers=headers, json=payload) as response:
                if response.status == 200:
                    return {"success": True, "message": "Blocos adicionados com sucesso"}
                return {"success": False, "error": f"Erro: {response.status}"}
    
    async def stream_tool_execution(self, tool_name: str, params: Dict, credentials: Dict) -> AsyncGenerator[Dict, None]:
        yield {"type": "tool_call", "tool": tool_name, "status": "executing", "message": f"📝 Executando {tool_name} no Notion..."}
        result = await self.execute_tool(tool_name, params, credentials)
        if result["success"]:
            yield {"type": "tool_result", "tool": tool_name, "status": "completed", "result": result}
        else:
            yield {"type": "tool_result", "tool": tool_name, "status": "error", "error": result.get("error")}


notion_mcp = NotionMCP()
