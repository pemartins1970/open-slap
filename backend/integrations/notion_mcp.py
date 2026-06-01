"""
Notion MCP Integration
Documentação e Wikis para OpenSlap
"""

from typing import Dict, Any, List, Optional, Union
import aiohttp
import json
from datetime import datetime

class NotionMCP:
    """
    Notion MCP - Documentação e Wikis
    
    Funcionalidades:
    - Gestão de páginas e bancos de dados
    - Blocos de conteúdo
    - Propriedades e filtros
    - Comentários
    - Busca
    """
    
    def __init__(self, token: str):
        self.token = token
        self.base_url = "https://api.notion.com/v1"
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json"
        }
    
    async def _make_request(self, method: str, endpoint: str, data: Dict = None) -> Dict[str, Any]:
        """Faz requisição à API do Notion"""
        url = f"{self.base_url}{endpoint}"
        
        async with aiohttp.ClientSession() as session:
            async with session.request(
                method=method,
                url=url,
                headers=self.headers,
                json=data
            ) as response:
                if response.status in [200, 201]:
                    return await response.json()
                else:
                    error_text = await response.text()
                    raise Exception(f"Notion API Error {response.status}: {error_text}")
    
    # ========== PÁGINAS ==========
    
    async def get_page(self, page_id: str) -> Dict[str, Any]:
        """Obtém uma página"""
        endpoint = f"/pages/{page_id}"
        return await self._make_request("GET", endpoint)
    
    async def create_page(self, parent_id: str, title: str = None,
                         properties: Dict = None, icon: Dict = None,
                         cover: Dict = None) -> Dict[str, Any]:
        """
        Cria nova página
        
        Args:
            parent_id: ID do pai (database ou page)
            title: Título da página
            properties: Propriedades adicionais
            icon: Ícone (emoji ou arquivo)
            cover: Capa da página
        """
        endpoint = "/pages"
        
        # Determina tipo do pai
        if parent_id.startswith("db_"):
            parent = {"database_id": parent_id.replace("db_", "")}
        else:
            parent = {"page_id": parent_id}
        
        data = {
            "parent": parent,
            "properties": properties or {}
        }
        
        # Adiciona título
        if title:
            if "database_id" in parent:
                # Para database, usa propriedade Name
                data["properties"]["Name"] = {
                    "title": [{"text": {"content": title}}]
                }
            else:
                # Para página
                data["properties"]["title"] = {
                    "title": [{"text": {"content": title}}]
                }
        
        if icon:
            data["icon"] = icon
        if cover:
            data["cover"] = cover
        
        return await self._make_request("POST", endpoint, data)
    
    async def update_page(self, page_id: str, properties: Dict = None,
                         icon: Dict = None, cover: Dict = None,
                         archived: bool = None) -> Dict[str, Any]:
        """Atualiza página"""
        endpoint = f"/pages/{page_id}"
        
        data = {}
        if properties:
            data["properties"] = properties
        if icon:
            data["icon"] = icon
        if cover:
            data["cover"] = cover
        if archived is not None:
            data["archived"] = archived
        
        return await self._make_request("PATCH", endpoint, data)
    
    async def delete_page(self, page_id: str) -> bool:
        """Remove página (arquiva)"""
        try:
            await self.update_page(page_id, archived=True)
            return True
        except:
            return False
    
    # ========== BLOCOS DE CONTEÚDO ==========
    
    async def get_page_blocks(self, page_id: str, start_cursor: str = None,
                            page_size: int = 100) -> Dict[str, Any]:
        """Obtém blocos de uma página"""
        endpoint = f"/blocks/{page_id}/children"
        
        params = {"page_size": page_size}
        if start_cursor:
            params["start_cursor"] = start_cursor
        
        return await self._make_request("GET", endpoint, params)
    
    async def append_blocks(self, block_id: str, blocks: List[Dict]) -> Dict[str, Any]:
        """
        Adiciona blocos a uma página ou bloco
        
        Tipos de bloco:
        - paragraph: Parágrafo
        - heading_1/2/3: Títulos
        - bulleted_list_item: Lista com marcadores
        - numbered_list_item: Lista numerada
        - to_do: Checkbox
        - code: Código
        - quote: Citação
        - divider: Divisor
        - image: Imagem
        - file: Arquivo
        - bookmark: Bookmark
        - table: Tabela
        - column_list: Layout de colunas
        """
        endpoint = f"/blocks/{block_id}/children"
        
        return await self._make_request("PATCH", endpoint, {
            "children": blocks
        })
    
    async def delete_block(self, block_id: str) -> bool:
        """Remove bloco"""
        endpoint = f"/blocks/{block_id}"
        try:
            await self._make_request("DELETE", endpoint)
            return True
        except:
            return False
    
    # ========== DATABASES ==========
    
    async def get_database(self, database_id: str) -> Dict[str, Any]:
        """Obtém database"""
        endpoint = f"/databases/{database_id}"
        return await self._make_request("GET", endpoint)
    
    async def create_database(self, parent_page_id: str, title: str,
                             properties: Dict, 
                             is_inline: bool = False) -> Dict[str, Any]:
        """
        Cria novo database
        
        Propriedades comuns:
        - title: Título
        - rich_text: Texto rico
        - number: Número
        - select: Seleção única
        - multi_select: Seleção múltipla
        - date: Data
        - people: Pessoas
        - files: Arquivos
        - checkbox: Checkbox
        - url: URL
        - email: Email
        - phone_number: Telefone
        - formula: Fórmula
        - relation: Relação
        - rollup: Rollup
        - created_time: Data de criação
        - created_by: Criador
        - last_edited_time: Última edição
        - last_edited_by: Último editor
        """
        endpoint = "/databases"
        
        data = {
            "parent": {"page_id": parent_page_id},
            "title": [{"text": {"content": title}}],
            "properties": properties,
            "is_inline": is_inline
        }
        
        return await self._make_request("POST", endpoint, data)
    
    async def update_database(self, database_id: str, title: str = None,
                           properties: Dict = None,
                           description: str = None) -> Dict[str, Any]:
        """Atualiza database"""
        endpoint = f"/databases/{database_id}"
        
        data = {}
        if title:
            data["title"] = [{"text": {"content": title}}]
        if properties:
            data["properties"] = properties
        if description:
            data["description"] = [{"text": {"content": description}}]
        
        return await self._make_request("PATCH", endpoint, data)
    
    async def query_database(self, database_id: str, 
                            filter: Dict = None,
                            sorts: List[Dict] = None,
                            start_cursor: str = None,
                            page_size: int = 100) -> Dict[str, Any]:
        """
        Consulta database com filtros
        
        Exemplo de filter:
        {
            "property": "Status",
            "select": {"equals": "Done"}
        }
        
        Exemplo de sorts:
        [
            {
                "property": "Created",
                "direction": "descending"
            }
        ]
        """
        endpoint = f"/databases/{database_id}/query"
        
        data = {"page_size": page_size}
        
        if filter:
            data["filter"] = filter
        if sorts:
            data["sorts"] = sorts
        if start_cursor:
            data["start_cursor"] = start_cursor
        
        return await self._make_request("POST", endpoint, data)
    
    # ========== USERS ==========
    
    async def list_users(self, start_cursor: str = None,
                        page_size: int = 100) -> Dict[str, Any]:
        """Lista usuários do workspace"""
        endpoint = "/users"
        
        params = {"page_size": page_size}
        if start_cursor:
            params["start_cursor"] = start_cursor
        
        return await self._make_request("GET", endpoint, params)
    
    async def get_user(self, user_id: str) -> Dict[str, Any]:
        """Obtém usuário"""
        endpoint = f"/users/{user_id}"
        return await self._make_request("GET", endpoint)
    
    async def get_bot_user(self) -> Dict[str, Any]:
        """Obtém informações do bot"""
        endpoint = "/users/me"
        return await self._make_request("GET", endpoint)
    
    # ========== COMENTÁRIOS ==========
    
    async def list_comments(self, block_id: str, start_cursor: str = None,
                           page_size: int = 100) -> Dict[str, Any]:
        """Lista comentários de um bloco"""
        endpoint = f"/comments"
        
        params = {
            "block_id": block_id,
            "page_size": page_size
        }
        if start_cursor:
            params["start_cursor"] = start_cursor
        
        return await self._make_request("GET", endpoint, params)
    
    async def create_comment(self, page_id: str, text: str,
                            discussion_id: str = None) -> Dict[str, Any]:
        """Adiciona comentário"""
        endpoint = "/comments"
        
        data = {
            "parent": {"page_id": page_id},
            "rich_text": [{"text": {"content": text}}]
        }
        
        if discussion_id:
            data["discussion_id"] = discussion_id
        
        return await self._make_request("POST", endpoint, data)
    
    # ========== BUSCA ==========
    
    async def search(self, query: str = None, filter: Dict = None,
                    sort: Dict = None, start_cursor: str = None,
                    page_size: int = 100) -> Dict[str, Any]:
        """
        Busca páginas e databases
        
        Filtros:
        - page: Apenas páginas
        - database: Apenas databases
        """
        endpoint = "/search"
        
        data = {"page_size": page_size}
        
        if query:
            data["query"] = query
        if filter:
            data["filter"] = filter
        if sort:
            data["sort"] = sort
        if start_cursor:
            data["start_cursor"] = start_cursor
        
        return await self._make_request("POST", endpoint, data)
    
    # ========== HELPERS PARA BLOCOS ==========
    
    @staticmethod
    def create_paragraph_block(text: str) -> Dict:
        """Cria bloco de parágrafo"""
        return {
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{"type": "text", "text": {"content": text}}]
            }
        }
    
    @staticmethod
    def create_heading_block(text: str, level: int = 1) -> Dict:
        """Cria bloco de título"""
        heading_type = f"heading_{level}"
        return {
            "object": "block",
            "type": heading_type,
            heading_type: {
                "rich_text": [{"type": "text", "text": {"content": text}}]
            }
        }
    
    @staticmethod
    def create_code_block(code: str, language: str = "plain text") -> Dict:
        """Cria bloco de código"""
        return {
            "object": "block",
            "type": "code",
            "code": {
                "rich_text": [{"type": "text", "text": {"content": code}}],
                "language": language
            }
        }
    
    @staticmethod
    def create_todo_block(text: str, checked: bool = False) -> Dict:
        """Cria bloco de tarefa"""
        return {
            "object": "block",
            "type": "to_do",
            "to_do": {
                "rich_text": [{"type": "text", "text": {"content": text}}],
                "checked": checked
            }
        }
    
    @staticmethod
    def create_bulleted_list_item(text: str) -> Dict:
        """Cria item de lista com marcador"""
        return {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [{"type": "text", "text": {"content": text}}]
            }
        }
    
    @staticmethod
    def create_numbered_list_item(text: str) -> Dict:
        """Cria item de lista numerada"""
        return {
            "object": "block",
            "type": "numbered_list_item",
            "numbered_list_item": {
                "rich_text": [{"type": "text", "text": {"content": text}}]
            }
        }
    
    @staticmethod
    def create_quote_block(text: str) -> Dict:
        """Cria bloco de citação"""
        return {
            "object": "block",
            "type": "quote",
            "quote": {
                "rich_text": [{"type": "text", "text": {"content": text}}]
            }
        }
    
    @staticmethod
    def create_divider_block() -> Dict:
        """Cria divisor"""
        return {
            "object": "block",
            "type": "divider",
            "divider": {}
        }
    
    @staticmethod
    def create_image_block(url: str, caption: str = None) -> Dict:
        """Cria bloco de imagem"""
        block = {
            "object": "block",
            "type": "image",
            "image": {
                "type": "external",
                "external": {"url": url}
            }
        }
        
        if caption:
            block["image"]["caption"] = [
                {"type": "text", "text": {"content": caption}}
            ]
        
        return block
    
    @staticmethod
    def create_bookmark_block(url: str) -> Dict:
        """Cria bloco de bookmark"""
        return {
            "object": "block",
            "type": "bookmark",
            "bookmark": {"url": url}
        }
    
    # ========== UTILITÁRIOS ==========
    
    async def test_connection(self) -> bool:
        """Testa conexão"""
        try:
            result = await self.search(page_size=1)
            return "results" in result
        except:
            return False


# Instância global
notion_mcp = None

def init_notion_mcp(token: str):
    """Inicializa o Notion MCP"""
    global notion_mcp
    notion_mcp = NotionMCP(token)
    return notion_mcp
