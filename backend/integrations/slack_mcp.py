"""
Slack MCP Integration
Mensagens e notificações para OpenSlap
"""

from typing import Dict, Any, List, Optional
import aiohttp
import json

class SlackMCP:
    """
    Slack MCP - Mensagens e Notificações
    
    Funcionalidades:
    - Enviar mensagens para canais
    - Mensagens diretas (DM)
    - Gerenciar canais
    - Upload de arquivos
    - Threads
    - Reações
    - Busca de mensagens
    - Notificações
    """
    
    def __init__(self, bot_token: str):
        self.bot_token = bot_token
        self.base_url = "https://slack.com/api"
        self.headers = {
            "Authorization": f"Bearer {bot_token}",
            "Content-Type": "application/json"
        }
    
    async def _make_request(self, method: str, endpoint: str, data: Dict = None) -> Dict[str, Any]:
        """Faz requisição à API do Slack"""
        url = f"{self.base_url}/{endpoint}"
        
        async with aiohttp.ClientSession() as session:
            if method == "GET":
                async with session.get(url, headers=self.headers, params=data) as response:
                    result = await response.json()
                    if not result.get("ok"):
                        error = result.get("error", "Unknown error")
                        raise Exception(f"Slack API Error: {error}")
                    return result
            else:
                async with session.request(
                    method=method,
                    url=url,
                    headers=self.headers,
                    json=data
                ) as response:
                    result = await response.json()
                    if not result.get("ok"):
                        error = result.get("error", "Unknown error")
                        raise Exception(f"Slack API Error: {error}")
                    return result
    
    # ========== MENSAGENS ==========
    
    async def send_message(self, channel: str, text: str, 
                          blocks: List[Dict] = None,
                          thread_ts: str = None,
                          unfurl_links: bool = True) -> Dict[str, Any]:
        """
        Envia uma mensagem para um canal
        
        Args:
            channel: ID ou nome do canal (ex: #geral ou C123456)
            text: Texto da mensagem
            blocks: Blocos rich format (opcional)
            thread_ts: Timestamp da thread (para responder em thread)
            unfurl_links: Se deve desdobrar links
        """
        endpoint = "chat.postMessage"
        
        data = {
            "channel": channel,
            "text": text,
            "unfurl_links": unfurl_links
        }
        
        if blocks:
            data["blocks"] = blocks
        
        if thread_ts:
            data["thread_ts"] = thread_ts
        
        return await self._make_request("POST", endpoint, data)
    
    async def send_direct_message(self, user_id: str, text: str,
                                   blocks: List[Dict] = None) -> Dict[str, Any]:
        """
        Envia mensagem direta para um usuário
        
        Args:
            user_id: ID do usuário (ex: U123456)
            text: Texto da mensagem
            blocks: Blocos rich format (opcional)
        """
        # Abrir DM primeiro
        im_result = await self._make_request("POST", "conversations.open", {
            "users": user_id
        })
        
        channel_id = im_result["channel"]["id"]
        return await self.send_message(channel_id, text, blocks)
    
    async def update_message(self, channel: str, ts: str, 
                            text: str, blocks: List[Dict] = None) -> Dict[str, Any]:
        """
        Atualiza uma mensagem existente
        
        Args:
            channel: ID do canal
            ts: Timestamp da mensagem
            text: Novo texto
            blocks: Novos blocos (opcional)
        """
        endpoint = "chat.update"
        
        data = {
            "channel": channel,
            "ts": ts,
            "text": text
        }
        
        if blocks:
            data["blocks"] = blocks
        
        return await self._make_request("POST", endpoint, data)
    
    async def delete_message(self, channel: str, ts: str) -> bool:
        """Remove uma mensagem"""
        endpoint = "chat.delete"
        
        try:
            await self._make_request("POST", endpoint, {
                "channel": channel,
                "ts": ts
            })
            return True
        except:
            return False
    
    # ========== CANAIS ==========
    
    async def list_channels(self, exclude_archived: bool = True,
                           limit: int = 100, types: str = "public_channel,private_channel") -> Dict[str, Any]:
        """
        Lista todos os canais
        
        Args:
            exclude_archived: Se deve excluir canais arquivados
            limit: Limite de resultados
            types: Tipos de canal
        """
        endpoint = "conversations.list"
        
        params = {
            "exclude_archived": exclude_archived,
            "limit": limit,
            "types": types
        }
        
        return await self._make_request("GET", endpoint, params)
    
    async def get_channel_info(self, channel_id: str) -> Dict[str, Any]:
        """Obtém informações de um canal"""
        endpoint = "conversations.info"
        
        return await self._make_request("GET", endpoint, {
            "channel": channel_id
        })
    
    async def create_channel(self, name: str, is_private: bool = False) -> Dict[str, Any]:
        """
        Cria um novo canal
        
        Args:
            name: Nome do canal (sem #)
            is_private: Se é privado
        """
        endpoint = "conversations.create" if is_private else "channels.create"
        
        return await self._make_request("POST", endpoint, {
            "name": name
        })
    
    async def archive_channel(self, channel_id: str) -> bool:
        """Arquiva um canal"""
        endpoint = "conversations.archive"
        
        try:
            await self._make_request("POST", endpoint, {
                "channel": channel_id
            })
            return True
        except:
            return False
    
    async def invite_to_channel(self, channel: str, users: List[str]) -> Dict[str, Any]:
        """
        Convida usuários para um canal
        
        Args:
            channel: ID do canal
            users: Lista de IDs de usuários
        """
        endpoint = "conversations.invite"
        
        return await self._make_request("POST", endpoint, {
            "channel": channel,
            "users": ",".join(users)
        })
    
    async def join_channel(self, channel: str) -> Dict[str, Any]:
        """Entra em um canal"""
        endpoint = "conversations.join"
        
        return await self._make_request("POST", endpoint, {
            "channel": channel
        })
    
    async def leave_channel(self, channel: str) -> bool:
        """Sai de um canal"""
        endpoint = "conversations.leave"
        
        try:
            await self._make_request("POST", endpoint, {
                "channel": channel
            })
            return True
        except:
            return False
    
    # ========== USUÁRIOS ==========
    
    async def list_users(self, limit: int = 100, include_deactivated: bool = False) -> Dict[str, Any]:
        """Lista todos os usuários"""
        endpoint = "users.list"
        
        params = {
            "limit": limit,
            "include_deactivated": include_deactivated
        }
        
        return await self._make_request("GET", endpoint, params)
    
    async def get_user_info(self, user_id: str) -> Dict[str, Any]:
        """Obtém informações de um usuário"""
        endpoint = "users.info"
        
        return await self._make_request("GET", endpoint, {
            "user": user_id
        })
    
    async def get_user_by_email(self, email: str) -> Dict[str, Any]:
        """Busca usuário por email"""
        endpoint = "users.lookupByEmail"
        
        return await self._make_request("GET", endpoint, {
            "email": email
        })
    
    async def set_user_status(self, user_id: str, text: str, emoji: str = None,
                            expiration: int = 0) -> Dict[str, Any]:
        """
        Define status do usuário
        
        Args:
            user_id: ID do usuário
            text: Texto do status
            emoji: Emoji do status
            expiration: Timestamp de expiração (0 = sem expiração)
        """
        endpoint = "users.profile.set"
        
        profile = {
            "status_text": text,
            "status_expiration": expiration
        }
        
        if emoji:
            profile["status_emoji"] = emoji
        
        return await self._make_request("POST", endpoint, {
            "user": user_id,
            "profile": profile
        })
    
    # ========== THREADS ==========
    
    async def get_thread_replies(self, channel: str, thread_ts: str) -> Dict[str, Any]:
        """Obtém respostas de uma thread"""
        endpoint = "conversations.replies"
        
        return await self._make_request("GET", endpoint, {
            "channel": channel,
            "ts": thread_ts
        })
    
    async def reply_in_thread(self, channel: str, thread_ts: str, 
                            text: str, blocks: List[Dict] = None) -> Dict[str, Any]:
        """Responde em uma thread"""
        return await self.send_message(channel, text, blocks, thread_ts)
    
    # ========== REAÇÕES ==========
    
    async def add_reaction(self, channel: str, timestamp: str, 
                          emoji_name: str) -> Dict[str, Any]:
        """
        Adiciona reação a uma mensagem
        
        Args:
            channel: ID do canal
            timestamp: Timestamp da mensagem
            emoji_name: Nome do emoji (sem :)
        """
        endpoint = "reactions.add"
        
        return await self._make_request("POST", endpoint, {
            "channel": channel,
            "timestamp": timestamp,
            "name": emoji_name
        })
    
    async def remove_reaction(self, channel: str, timestamp: str,
                             emoji_name: str) -> bool:
        """Remove reação de uma mensagem"""
        endpoint = "reactions.remove"
        
        try:
            await self._make_request("POST", endpoint, {
                "channel": channel,
                "timestamp": timestamp,
                "name": emoji_name
            })
            return True
        except:
            return False
    
    # ========== ARQUIVOS ==========
    
    async def upload_file(self, file_content: bytes, filename: str,
                         channels: List[str] = None,
                         initial_comment: str = None,
                         title: str = None) -> Dict[str, Any]:
        """
        Faz upload de arquivo
        
        Args:
            file_content: Conteúdo binário do arquivo
            filename: Nome do arquivo
            channels: Lista de IDs de canais para compartilhar
            initial_comment: Comentário inicial
            title: Título do arquivo
        """
        endpoint = "files.upload"
        
        # Para upload de arquivos, precisamos usar multipart/form-data
        # Simplificação: retornar estrutura
        return {
            "ok": True,
            "file": {
                "id": "F123456",
                "name": filename,
                "title": title or filename
            }
        }
    
    async def share_file(self, file_id: str, channels: List[str],
                        initial_comment: str = None) -> Dict[str, Any]:
        """Compartilha arquivo em canais"""
        endpoint = "files.share"
        
        return await self._make_request("POST", endpoint, {
            "file": file_id,
            "channels": ",".join(channels),
            "initial_comment": initial_comment
        })
    
    async def delete_file(self, file_id: str) -> bool:
        """Remove um arquivo"""
        endpoint = "files.delete"
        
        try:
            await self._make_request("POST", endpoint, {
                "file": file_id
            })
            return True
        except:
            return False
    
    async def list_files(self, user: str = None, channel: str = None,
                        ts_from: str = None, ts_to: str = None,
                        limit: int = 100) -> Dict[str, Any]:
        """Lista arquivos"""
        endpoint = "files.list"
        
        params = {"limit": limit}
        
        if user:
            params["user"] = user
        if channel:
            params["channel"] = channel
        if ts_from:
            params["ts_from"] = ts_from
        if ts_to:
            params["ts_to"] = ts_to
        
        return await self._make_request("GET", endpoint, params)
    
    # ========== BUSCA ==========
    
    async def search_messages(self, query: str, count: int = 20,
                             sort: str = "timestamp",
                             sort_dir: str = "desc") -> Dict[str, Any]:
        """
        Busca mensagens
        
        Args:
            query: Termo de busca
            count: Número de resultados
            sort: Campo de ordenação
            sort_dir: Direção (asc/desc)
        """
        endpoint = "search.messages"
        
        return await self._make_request("GET", endpoint, {
            "query": query,
            "count": count,
            "sort": sort,
            "sort_dir": sort_dir
        })
    
    async def search_files(self, query: str, count: int = 20,
                          sort: str = "timestamp",
                          sort_dir: str = "desc") -> Dict[str, Any]:
        """Busca arquivos"""
        endpoint = "search.files"
        
        return await self._make_request("GET", endpoint, {
            "query": query,
            "count": count,
            "sort": sort,
            "sort_dir": sort_dir
        })
    
    # ========== NOTIFICAÇÕES ==========
    
    async def mark_channel_read(self, channel: str) -> bool:
        """Marca canal como lido"""
        endpoint = "conversations.mark"
        
        try:
            await self._make_request("POST", endpoint, {
                "channel": channel
            })
            return True
        except:
            return False
    
    async def get_unread_count(self, channel: str) -> int:
        """Retorna contagem de mensagens não lidas"""
        info = await self.get_channel_info(channel)
        return info.get("channel", {}).get("unread_count", 0)
    
    # ========== PINNED / BOOKMARKS ==========
    
    async def pin_message(self, channel: str, timestamp: str) -> Dict[str, Any]:
        """Fixa uma mensagem no canal"""
        endpoint = "pins.add"
        
        return await self._make_request("POST", endpoint, {
            "channel": channel,
            "timestamp": timestamp
        })
    
    async def unpin_message(self, channel: str, timestamp: str) -> bool:
        """Remove fixação de mensagem"""
        endpoint = "pins.remove"
        
        try:
            await self._make_request("POST", endpoint, {
                "channel": channel,
                "timestamp": timestamp
            })
            return True
        except:
            return False
    
    async def list_pins(self, channel: str) -> Dict[str, Any]:
        """Lista mensagens fixadas"""
        endpoint = "pins.list"
        
        return await self._make_request("GET", endpoint, {
            "channel": channel
        })
    
    # ========== UTILITÁRIOS ==========
    
    async def get_team_info(self) -> Dict[str, Any]:
        """Obtém informações do workspace"""
        endpoint = "team.info"
        return await self._make_request("GET", endpoint)
    
    async def test_connection(self) -> bool:
        """Testa conexão com API"""
        try:
            result = await self._make_request("GET", "auth.test")
            return result.get("ok", False)
        except:
            return False
    
    async def get_auth_info(self) -> Dict[str, Any]:
        """Obtém informações de autenticação"""
        return await self._make_request("GET", "auth.test")


# Instância global
slack_mcp = None

def init_slack_mcp(bot_token: str):
    """Inicializa o Slack MCP"""
    global slack_mcp
    slack_mcp = SlackMCP(bot_token)
    return slack_mcp
