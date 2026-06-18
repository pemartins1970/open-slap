"""
Slack MCP - Model Context Protocol para Slack
Integração completa com Slack API para mensagens, canais e automações

Funcionalidades:
- Enviar mensagens para canais e usuários
- Gerenciar canais (criar, listar, arquivar)
- Upload de arquivos
- Reações e threads
- Slack Bots e interações

Documentação: https://api.slack.com/
"""

import json
import logging
from typing import Dict, Any, List, Optional, AsyncGenerator
from datetime import datetime
import aiohttp

logger = logging.getLogger(__name__)


class SlackMCP:
    """
    MCP para integração com Slack
    Permite agentes enviarem mensagens e gerenciarem workspaces
    """
    
    def __init__(self):
        self.name = "slack"
        self.display_name = "Slack"
        self.version = "1.0.0"
        self.description = "Envie mensagens, gerencie canais e automatize notificações no Slack"
        self.icon = "💬"
        self.category = "communication"
        self.tier = "free"
        self.base_url = "https://slack.com/api"
        
    def get_manifest(self) -> Dict[str, Any]:
        """Retorna o manifesto do MCP para registro"""
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
            "permissions": [
                "slack:chat:write",
                "slack:chat:read",
                "slack:channels:read",
                "slack:channels:write",
                "slack:users:read",
                "slack:files:write",
                "slack:reactions:write"
            ],
            "tools": [
                "send_message",
                "send_message_to_user",
                "send_thread_reply",
                "create_channel",
                "list_channels",
                "get_channel_info",
                "archive_channel",
                "list_users",
                "get_user_info",
                "upload_file",
                "add_reaction",
                "get_conversation_history",
                "get_thread_replies",
                "update_message",
                "delete_message",
                "get_workspace_info",
                "invite_user_to_channel",
                "set_channel_topic"
            ],
            "agents": [
                "notification_bot",
                "community_manager",
                "support_agent"
            ],
            "install_type": "builtin",
            "endpoint": None,
            "auth": "oauth_token"
        }
    
    async def execute_tool(
        self,
        tool_name: str,
        params: Dict[str, Any],
        credentials: Dict[str, str]
    ) -> Dict[str, Any]:
        """Executa uma ferramenta do MCP Slack"""
        token = credentials.get("bot_token") or credentials.get("access_token")
        
        if not token:
            return {
                "success": False,
                "error": "Bot Token ou Access Token do Slack não configurado"
            }
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        try:
            if tool_name == "send_message":
                return await self._send_message(headers, params)
            elif tool_name == "send_message_to_user":
                return await self._send_message_to_user(headers, params)
            elif tool_name == "send_thread_reply":
                return await self._send_thread_reply(headers, params)
            elif tool_name == "create_channel":
                return await self._create_channel(headers, params)
            elif tool_name == "list_channels":
                return await self._list_channels(headers, params)
            elif tool_name == "get_channel_info":
                return await self._get_channel_info(headers, params)
            elif tool_name == "archive_channel":
                return await self._archive_channel(headers, params)
            elif tool_name == "list_users":
                return await self._list_users(headers, params)
            elif tool_name == "get_user_info":
                return await self._get_user_info(headers, params)
            elif tool_name == "upload_file":
                return await self._upload_file(headers, params)
            elif tool_name == "add_reaction":
                return await self._add_reaction(headers, params)
            elif tool_name == "get_conversation_history":
                return await self._get_conversation_history(headers, params)
            elif tool_name == "get_thread_replies":
                return await self._get_thread_replies(headers, params)
            elif tool_name == "update_message":
                return await self._update_message(headers, params)
            elif tool_name == "delete_message":
                return await self._delete_message(headers, params)
            elif tool_name == "get_workspace_info":
                return await self._get_workspace_info(headers, params)
            elif tool_name == "invite_user_to_channel":
                return await self._invite_user_to_channel(headers, params)
            elif tool_name == "set_channel_topic":
                return await self._set_channel_topic(headers, params)
            else:
                return {"success": False, "error": f"Ferramenta '{tool_name}' não encontrada"}
                
        except Exception as e:
            logger.error(f"Erro ao executar tool {tool_name}: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def _send_message(self, headers: Dict, params: Dict) -> Dict:
        """Envia mensagem para um canal"""
        channel = params.get("channel")
        text = params.get("text")
        
        if not channel or not text:
            return {"success": False, "error": "channel e text são obrigatórios"}
        
        url = f"{self.base_url}/chat.postMessage"
        payload = {
            "channel": channel,
            "text": text,
            "unfurl_links": params.get("unfurl_links", True)
        }
        
        if "blocks" in params:
            payload["blocks"] = params["blocks"]
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as response:
                data = await response.json()
                
                if data.get("ok"):
                    return {
                        "success": True,
                        "message": {
                            "ts": data.get("ts"),
                            "channel": data.get("channel"),
                            "text": text
                        },
                        "message_url": f"https://slack.com/archives/{channel}/p{data.get('ts', '').replace('.', '')}"
                    }
                else:
                    return {"success": False, "error": data.get("error", "Erro ao enviar mensagem")}
    
    async def _send_message_to_user(self, headers: Dict, params: Dict) -> Dict:
        """Envia mensagem direta para um usuário"""
        user = params.get("user")
        text = params.get("text")
        
        if not user or not text:
            return {"success": False, "error": "user e text são obrigatórios"}
        
        # Abrir conversa direta
        im_url = f"{self.base_url}/conversations.open"
        im_payload = {"users": user}
        
        async with aiohttp.ClientSession() as session:
            async with session.post(im_url, headers=headers, json=im_payload) as im_response:
                im_data = await im_response.json()
                
                if not im_data.get("ok"):
                    return {"success": False, "error": im_data.get("error", "Erro ao abrir DM")}
                
                channel = im_data.get("channel", {}).get("id")
                
                # Enviar mensagem
                url = f"{self.base_url}/chat.postMessage"
                payload = {
                    "channel": channel,
                    "text": text
                }
                
                async with session.post(url, headers=headers, json=payload) as response:
                    data = await response.json()
                    
                    if data.get("ok"):
                        return {
                            "success": True,
                            "message": {
                                "ts": data.get("ts"),
                                "channel": channel,
                                "recipient": user
                            },
                            "message": f"Mensagem enviada para usuário {user}"
                        }
                    else:
                        return {"success": False, "error": data.get("error", "Erro ao enviar DM")}
    
    async def _send_thread_reply(self, headers: Dict, params: Dict) -> Dict:
        """Responde em uma thread"""
        channel = params.get("channel")
        thread_ts = params.get("thread_ts")
        text = params.get("text")
        
        if not channel or not thread_ts or not text:
            return {"success": False, "error": "channel, thread_ts e text são obrigatórios"}
        
        url = f"{self.base_url}/chat.postMessage"
        payload = {
            "channel": channel,
            "thread_ts": thread_ts,
            "text": text
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as response:
                data = await response.json()
                
                if data.get("ok"):
                    return {
                        "success": True,
                        "message": {
                            "ts": data.get("ts"),
                            "thread_ts": thread_ts,
                            "channel": channel
                        },
                        "message": "Resposta enviada na thread"
                    }
                else:
                    return {"success": False, "error": data.get("error", "Erro ao responder thread")}
    
    async def _create_channel(self, headers: Dict, params: Dict) -> Dict:
        """Cria um novo canal"""
        name = params.get("name")
        is_private = params.get("is_private", False)
        
        if not name:
            return {"success": False, "error": "name é obrigatório"}
        
        # Formatar nome (sem espaços, lowercase)
        name = name.lower().replace(" ", "-").replace("_", "-")
        
        url = f"{self.base_url}/{'conversations.create' if is_private else 'channels.create'}"
        payload = {
            "name": name,
            "is_private": is_private
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as response:
                data = await response.json()
                
                if data.get("ok"):
                    channel = data.get("channel", {})
                    return {
                        "success": True,
                        "channel": {
                            "id": channel.get("id"),
                            "name": channel.get("name"),
                            "is_private": channel.get("is_private"),
                            "created": channel.get("created")
                        },
                        "message": f"Canal '#{name}' criado com sucesso"
                    }
                else:
                    return {"success": False, "error": data.get("error", "Erro ao criar canal")}
    
    async def _list_channels(self, headers: Dict, params: Dict) -> Dict:
        """Lista canais do workspace"""
        exclude_archived = params.get("exclude_archived", True)
        limit = params.get("limit", 100)
        
        url = f"{self.base_url}/conversations.list"
        payload = {
            "exclude_archived": exclude_archived,
            "limit": limit,
            "types": "public_channel,private_channel"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as response:
                data = await response.json()
                
                if data.get("ok"):
                    channels = data.get("channels", [])
                    return {
                        "success": True,
                        "channels": [
                            {
                                "id": c.get("id"),
                                "name": c.get("name"),
                                "is_private": c.get("is_private"),
                                "is_archived": c.get("is_archived"),
                                "num_members": c.get("num_members"),
                                "topic": c.get("topic", {}).get("value"),
                                "created": c.get("created")
                            }
                            for c in channels
                        ],
                        "count": len(channels)
                    }
                else:
                    return {"success": False, "error": data.get("error", "Erro ao listar canais")}
    
    async def _get_channel_info(self, headers: Dict, params: Dict) -> Dict:
        """Obtém informações de um canal"""
        channel = params.get("channel")
        if not channel:
            return {"success": False, "error": "channel é obrigatório"}
        
        url = f"{self.base_url}/conversations.info"
        payload = {"channel": channel}
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as response:
                data = await response.json()
                
                if data.get("ok"):
                    channel_data = data.get("channel", {})
                    return {
                        "success": True,
                        "channel": {
                            "id": channel_data.get("id"),
                            "name": channel_data.get("name"),
                            "is_private": channel_data.get("is_private"),
                            "num_members": channel_data.get("num_members"),
                            "topic": channel_data.get("topic", {}).get("value"),
                            "purpose": channel_data.get("purpose", {}).get("value"),
                            "created": channel_data.get("created")
                        }
                    }
                else:
                    return {"success": False, "error": data.get("error", "Erro ao obter info do canal")}
    
    async def _archive_channel(self, headers: Dict, params: Dict) -> Dict:
        """Arquiva um canal"""
        channel = params.get("channel")
        if not channel:
            return {"success": False, "error": "channel é obrigatório"}
        
        url = f"{self.base_url}/conversations.archive"
        payload = {"channel": channel}
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as response:
                data = await response.json()
                
                if data.get("ok"):
                    return {
                        "success": True,
                        "message": f"Canal '{channel}' arquivado com sucesso"
                    }
                else:
                    return {"success": False, "error": data.get("error", "Erro ao arquivar canal")}
    
    async def _list_users(self, headers: Dict, params: Dict) -> Dict:
        """Lista usuários do workspace"""
        limit = params.get("limit", 100)
        
        url = f"{self.base_url}/users.list"
        payload = {"limit": limit}
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as response:
                data = await response.json()
                
                if data.get("ok"):
                    members = data.get("members", [])
                    # Filtrar bots e usuários deletados
                    users = [
                        {
                            "id": m.get("id"),
                            "name": m.get("name"),
                            "real_name": m.get("real_name"),
                            "email": m.get("profile", {}).get("email"),
                            "is_bot": m.get("is_bot"),
                            "is_admin": m.get("is_admin"),
                            "status": m.get("profile", {}).get("status_text")
                        }
                        for m in members
                        if not m.get("deleted") and not m.get("is_bot")
                    ]
                    
                    return {
                        "success": True,
                        "users": users,
                        "count": len(users)
                    }
                else:
                    return {"success": False, "error": data.get("error", "Erro ao listar usuários")}
    
    async def _get_user_info(self, headers: Dict, params: Dict) -> Dict:
        """Obtém informações de um usuário"""
        user = params.get("user")
        if not user:
            return {"success": False, "error": "user é obrigatório"}
        
        url = f"{self.base_url}/users.info"
        payload = {"user": user}
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as response:
                data = await response.json()
                
                if data.get("ok"):
                    user_data = data.get("user", {})
                    return {
                        "success": True,
                        "user": {
                            "id": user_data.get("id"),
                            "name": user_data.get("name"),
                            "real_name": user_data.get("real_name"),
                            "email": user_data.get("profile", {}).get("email"),
                            "phone": user_data.get("profile", {}).get("phone"),
                            "title": user_data.get("profile", {}).get("title"),
                            "status": user_data.get("profile", {}).get("status_text"),
                            "is_admin": user_data.get("is_admin"),
                            "is_bot": user_data.get("is_bot")
                        }
                    }
                else:
                    return {"success": False, "error": data.get("error", "Erro ao obter info do usuário")}
    
    async def _upload_file(self, headers: Dict, params: Dict) -> Dict:
        """Faz upload de arquivo"""
        channel = params.get("channel")
        file_path = params.get("file_path")
        content = params.get("content")
        filename = params.get("filename", "file.txt")
        title = params.get("title", "Arquivo")
        
        if not channel:
            return {"success": False, "error": "channel é obrigatório"}
        
        if not file_path and not content:
            return {"success": False, "error": "file_path ou content é obrigatório"}
        
        url = f"{self.base_url}/files.upload"
        
        # Preparar dados
        data = aiohttp.FormData()
        data.add_field("channels", channel)
        data.add_field("title", title)
        data.add_field("filename", filename)
        
        if content:
            data.add_field("content", content)
        elif file_path:
            try:
                with open(file_path, "rb") as f:
                    data.add_field("file", f, filename=filename)
            except Exception as e:
                return {"success": False, "error": f"Erro ao ler arquivo: {str(e)}"}
        
        # Mudar header para multipart
        upload_headers = {"Authorization": headers["Authorization"]}
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=upload_headers, data=data) as response:
                data = await response.json()
                
                if data.get("ok"):
                    file_data = data.get("file", {})
                    return {
                        "success": True,
                        "file": {
                            "id": file_data.get("id"),
                            "name": file_data.get("name"),
                            "url": file_data.get("url_private"),
                            "permalink": file_data.get("permalink")
                        },
                        "message": "Arquivo enviado com sucesso"
                    }
                else:
                    return {"success": False, "error": data.get("error", "Erro ao fazer upload")}
    
    async def _add_reaction(self, headers: Dict, params: Dict) -> Dict:
        """Adiciona reação a uma mensagem"""
        channel = params.get("channel")
        timestamp = params.get("timestamp")
        name = params.get("name")
        
        if not all([channel, timestamp, name]):
            return {"success": False, "error": "channel, timestamp e name são obrigatórios"}
        
        url = f"{self.base_url}/reactions.add"
        payload = {
            "channel": channel,
            "timestamp": timestamp,
            "name": name
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as response:
                data = await response.json()
                
                if data.get("ok"):
                    return {
                        "success": True,
                        "message": f"Reação :{name}: adicionada"
                    }
                else:
                    return {"success": False, "error": data.get("error", "Erro ao adicionar reação")}
    
    async def _get_conversation_history(self, headers: Dict, params: Dict) -> Dict:
        """Obtém histórico de conversas de um canal"""
        channel = params.get("channel")
        limit = params.get("limit", 100)
        
        if not channel:
            return {"success": False, "error": "channel é obrigatório"}
        
        url = f"{self.base_url}/conversations.history"
        payload = {
            "channel": channel,
            "limit": limit
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as response:
                data = await response.json()
                
                if data.get("ok"):
                    messages = data.get("messages", [])
                    return {
                        "success": True,
                        "messages": [
                            {
                                "ts": m.get("ts"),
                                "user": m.get("user"),
                                "text": m.get("text"),
                                "type": m.get("type"),
                                "reply_count": m.get("reply_count", 0),
                                "has_reactions": bool(m.get("reactions"))
                            }
                            for m in messages
                        ],
                        "count": len(messages)
                    }
                else:
                    return {"success": False, "error": data.get("error", "Erro ao obter histórico")}
    
    async def _get_thread_replies(self, headers: Dict, params: Dict) -> Dict:
        """Obtém respostas de uma thread"""
        channel = params.get("channel")
        thread_ts = params.get("thread_ts")
        
        if not channel or not thread_ts:
            return {"success": False, "error": "channel e thread_ts são obrigatórios"}
        
        url = f"{self.base_url}/conversations.replies"
        payload = {
            "channel": channel,
            "ts": thread_ts
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as response:
                data = await response.json()
                
                if data.get("ok"):
                    messages = data.get("messages", [])
                    return {
                        "success": True,
                        "thread_ts": thread_ts,
                        "messages": messages,
                        "count": len(messages)
                    }
                else:
                    return {"success": False, "error": data.get("error", "Erro ao obter thread")}
    
    async def _get_workspace_info(self, headers: Dict, params: Dict) -> Dict:
        """Obtém informações do workspace"""
        url = f"{self.base_url}/team.info"
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers) as response:
                data = await response.json()
                
                if data.get("ok"):
                    team = data.get("team", {})
                    return {
                        "success": True,
                        "workspace": {
                            "id": team.get("id"),
                            "name": team.get("name"),
                            "domain": team.get("domain"),
                            "email_domain": team.get("email_domain"),
                            "icon": team.get("icon", {}).get("image_132")
                        }
                    }
                else:
                    return {"success": False, "error": data.get("error", "Erro ao obter info do workspace")}
    
    async def _invite_user_to_channel(self, headers: Dict, params: Dict) -> Dict:
        """Convida usuário para um canal"""
        channel = params.get("channel")
        user = params.get("user")
        
        if not channel or not user:
            return {"success": False, "error": "channel e user são obrigatórios"}
        
        url = f"{self.base_url}/conversations.invite"
        payload = {
            "channel": channel,
            "users": user
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as response:
                data = await response.json()
                
                if data.get("ok"):
                    return {
                        "success": True,
                        "message": f"Usuário '{user}' convidado para o canal"
                    }
                else:
                    return {"success": False, "error": data.get("error", "Erro ao convidar usuário")}
    
    async def _set_channel_topic(self, headers: Dict, params: Dict) -> Dict:
        """Define tópico de um canal"""
        channel = params.get("channel")
        topic = params.get("topic")
        
        if not channel or topic is None:
            return {"success": False, "error": "channel e topic são obrigatórios"}
        
        url = f"{self.base_url}/conversations.setTopic"
        payload = {
            "channel": channel,
            "topic": topic
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as response:
                data = await response.json()
                
                if data.get("ok"):
                    return {
                        "success": True,
                        "message": "Tópico atualizado com sucesso",
                        "topic": topic
                    }
                else:
                    return {"success": False, "error": data.get("error", "Erro ao definir tópico")}
    
    async def _update_message(self, headers: Dict, params: Dict) -> Dict:
        """Atualiza uma mensagem existente"""
        channel = params.get("channel")
        ts = params.get("ts")
        text = params.get("text")
        
        if not all([channel, ts, text]):
            return {"success": False, "error": "channel, ts e text são obrigatórios"}
        
        url = f"{self.base_url}/chat.update"
        payload = {
            "channel": channel,
            "ts": ts,
            "text": text
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as response:
                data = await response.json()
                
                if data.get("ok"):
                    return {
                        "success": True,
                        "message": "Mensagem atualizada com sucesso"
                    }
                else:
                    return {"success": False, "error": data.get("error", "Erro ao atualizar mensagem")}
    
    async def _delete_message(self, headers: Dict, params: Dict) -> Dict:
        """Deleta uma mensagem"""
        channel = params.get("channel")
        ts = params.get("ts")
        
        if not channel or not ts:
            return {"success": False, "error": "channel e ts são obrigatórios"}
        
        url = f"{self.base_url}/chat.delete"
        payload = {
            "channel": channel,
            "ts": ts
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as response:
                data = await response.json()
                
                if data.get("ok"):
                    return {
                        "success": True,
                        "message": "Mensagem deletada com sucesso"
                    }
                else:
                    return {"success": False, "error": data.get("error", "Erro ao deletar mensagem")}
    
    async def stream_tool_execution(
        self,
        tool_name: str,
        params: Dict[str, Any],
        credentials: Dict[str, str]
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Streaming SSE para feedback em tempo real"""
        yield {
            "type": "tool_call",
            "tool": tool_name,
            "status": "executing",
            "message": f"💬 Executando {tool_name} no Slack..."
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
slack_mcp = SlackMCP()
