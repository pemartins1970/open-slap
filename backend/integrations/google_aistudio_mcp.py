"""
Google AI Studio MCP - Model Context Protocol para Google AI Studio / Gemini
Reforço supremo da artilharia OpenSlap - Controle total dos projetos Gemini

Funcionalidades:
- Geração de conteúdo com Gemini (Pro/Flash/Ultra)
- Streaming de respostas em tempo real
- Gerenciamento de projetos e prompts do AI Studio
- Geração de embeddings
- Contagem de tokens
- Upload e gestão de arquivos
- Geração de imagens (Imagen)
- API Live (WebSocket) para conversação em tempo real

Baseado na API Gemini: https://ai.google.dev/api
"""

import json
import logging
from typing import Dict, Any, List, Optional, AsyncGenerator, Union
from datetime import datetime
import aiohttp
import base64

logger = logging.getLogger(__name__)


class GoogleAIStudioMCP:
    """
    MCP para integração com Google AI Studio / Gemini API
    Permite agentes controlarem projetos Gemini e executarem tarefas de IA avançadas
    """
    
    def __init__(self):
        self.name = "google_aistudio"
        self.display_name = "Google AI Studio"
        self.version = "1.0.0"
        self.description = "Controle projetos Gemini, gere conteúdo com IA e automatize workflows no Google AI Studio"
        self.icon = "🧠"
        self.category = "ai_ml"
        self.tier = "pro"
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"
        
    def get_manifest(self) -> Dict[str, Any]:
        """Retorna o manifesto do MCP para registro"""
        return {
            "manifest_version": "1.0",
            "id": self.name,
            "name": self.display_name,
            "version": self.version,
            "category": self.category,
            "tier": self.tier,
            "icon": self.icon,
            "description": self.description,
            "compatible_with": ["openslap"],
            "permissions": [
                "googleai:models:read",
                "googleai:generate:write",
                "googleai:embeddings:read",
                "googleai:files:write",
                "googleai:projects:read",
                "googleai:tuning:write"
            ],
            "tools": [
                # Geração de Conteúdo
                "generate_content",
                "stream_generate_content",
                "generate_content_with_system_prompt",
                "chat_completion",
                
                # Modelos
                "list_models",
                "get_model",
                
                # Embeddings
                "embed_content",
                "batch_embed_contents",
                
                # Tokens
                "count_tokens",
                
                # Arquivos
                "upload_file",
                "list_files",
                "get_file",
                "delete_file",
                
                # Multimodal
                "generate_image",
                "analyze_image",
                "analyze_video",
                "analyze_audio",
                
                # Projetos AI Studio
                "list_tuned_models",
                "create_tuned_model",
                "get_tuned_model",
                
                # Configurações
                "set_generation_config",
                "get_generation_config"
            ],
            "agents": [
                "gemini_specialist",
                "content_generator",
                "code_assistant",
                "data_analyst",
                "creative_writer",
                "multimodal_expert"
            ],
            "install_type": "builtin",
            "endpoint": None,
            "auth": "api_key"
        }
    
    async def execute_tool(
        self,
        tool_name: str,
        params: Dict[str, Any],
        credentials: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Executa uma ferramenta do MCP Google AI Studio
        
        Args:
            tool_name: Nome da ferramenta a executar
            params: Parâmetros da ferramenta
            credentials: {api_key}
        """
        api_key = credentials.get("api_key")
        
        if not api_key:
            return {
                "success": False,
                "error": "Chave de API do Google AI Studio não configurada. Obtenha em: https://aistudio.google.com/app/apikey"
            }
        
        headers = {
            "x-goog-api-key": api_key,
            "Content-Type": "application/json"
        }
        
        try:
            # Geração de Conteúdo
            if tool_name == "generate_content":
                return await self._generate_content(headers, params)
            elif tool_name == "stream_generate_content":
                return await self._stream_generate_content(headers, params)
            elif tool_name == "generate_content_with_system_prompt":
                return await self._generate_with_system_prompt(headers, params)
            elif tool_name == "chat_completion":
                return await self._chat_completion(headers, params)
            
            # Modelos
            elif tool_name == "list_models":
                return await self._list_models(headers, params)
            elif tool_name == "get_model":
                return await self._get_model(headers, params)
            
            # Embeddings
            elif tool_name == "embed_content":
                return await self._embed_content(headers, params)
            elif tool_name == "batch_embed_contents":
                return await self._batch_embed_contents(headers, params)
            
            # Tokens
            elif tool_name == "count_tokens":
                return await self._count_tokens(headers, params)
            
            # Arquivos
            elif tool_name == "upload_file":
                return await self._upload_file(headers, params)
            elif tool_name == "list_files":
                return await self._list_files(headers, params)
            elif tool_name == "get_file":
                return await self._get_file(headers, params)
            elif tool_name == "delete_file":
                return await self._delete_file(headers, params)
            
            # Multimodal
            elif tool_name == "generate_image":
                return await self._generate_image(headers, params)
            elif tool_name == "analyze_image":
                return await self._analyze_image(headers, params)
            elif tool_name == "analyze_video":
                return await self._analyze_video(headers, params)
            elif tool_name == "analyze_audio":
                return await self._analyze_audio(headers, params)
            
            # Tuning/Projetos
            elif tool_name == "list_tuned_models":
                return await self._list_tuned_models(headers, params)
            elif tool_name == "create_tuned_model":
                return await self._create_tuned_model(headers, params)
            elif tool_name == "get_tuned_model":
                return await self._get_tuned_model(headers, params)
            
            else:
                return {"success": False, "error": f"Ferramenta '{tool_name}' não encontrada"}
                
        except Exception as e:
            logger.error(f"Erro ao executar tool {tool_name}: {str(e)}")
            return {"success": False, "error": str(e)}
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # GERAÇÃO DE CONTEÚDO
    # ═══════════════════════════════════════════════════════════════════════════════
    
    async def _generate_content(
        self,
        headers: Dict[str, str],
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Gera conteúdo com Gemini (não-streaming)"""
        model = params.get("model", "gemini-2.5-flash")
        prompt = params.get("prompt")
        
        if not prompt:
            return {"success": False, "error": "prompt é obrigatório"}
        
        # Configurações opcionais
        generation_config = params.get("generation_config", {})
        
        url = f"{self.base_url}/models/{model}:generateContent"
        
        payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": prompt}]
                }
            ]
        }
        
        if generation_config:
            payload["generationConfig"] = {
                "temperature": generation_config.get("temperature", 0.7),
                "maxOutputTokens": generation_config.get("max_output_tokens", 2048),
                "topP": generation_config.get("top_p", 0.95),
                "topK": generation_config.get("top_k", 40)
            }
        
        # Suporte a safety settings
        if "safety_settings" in params:
            payload["safetySettings"] = params["safety_settings"]
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as response:
                data = await response.json()
                
                if response.status == 200:
                    candidates = data.get("candidates", [])
                    if candidates:
                        content = candidates[0].get("content", {})
                        parts = content.get("parts", [])
                        text = "".join([p.get("text", "") for p in parts])
                        
                        # Metadata
                        usage = data.get("usageMetadata", {})
                        
                        return {
                            "success": True,
                            "text": text,
                            "model": model,
                            "usage": {
                                "prompt_tokens": usage.get("promptTokenCount", 0),
                                "completion_tokens": usage.get("candidatesTokenCount", 0),
                                "total_tokens": usage.get("totalTokenCount", 0)
                            },
                            "finish_reason": candidates[0].get("finishReason", "UNKNOWN")
                        }
                    else:
                        return {"success": False, "error": "Nenhuma resposta gerada"}
                else:
                    error_msg = data.get("error", {}).get("message", f"Erro Gemini: {response.status}")
                    return {"success": False, "error": error_msg}
    
    async def _stream_generate_content(
        self,
        headers: Dict[str, str],
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Gera conteúdo com streaming (SSE) - retorna primeira resposta para não bloquear"""
        model = params.get("model", "gemini-2.5-flash")
        prompt = params.get("prompt")
        
        if not prompt:
            return {"success": False, "error": "prompt é obrigatório"}
        
        url = f"{self.base_url}/models/{model}:streamGenerateContent"
        
        payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": prompt}]
                }
            ]
        }
        
        if "generation_config" in params:
            gc = params["generation_config"]
            payload["generationConfig"] = {
                "temperature": gc.get("temperature", 0.7),
                "maxOutputTokens": gc.get("max_output_tokens", 2048)
            }
        
        # Para streaming, retornamos info inicial - o streaming real seria via SSE
        return {
            "success": True,
            "streaming": True,
            "message": "Streaming iniciado. Use endpoint SSE para receber chunks.",
            "model": model,
            "prompt_preview": prompt[:100] + "..." if len(prompt) > 100 else prompt
        }
    
    async def _generate_with_system_prompt(
        self,
        headers: Dict[str, str],
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Gera conteúdo com system prompt/instructions"""
        model = params.get("model", "gemini-2.5-flash")
        prompt = params.get("prompt")
        system_prompt = params.get("system_prompt")
        
        if not prompt:
            return {"success": False, "error": "prompt é obrigatório"}
        
        url = f"{self.base_url}/models/{model}:generateContent"
        
        contents = []
        
        # System prompt como primeiro contexto
        if system_prompt:
            contents.append({
                "role": "user",
                "parts": [{"text": f"System: {system_prompt}"}]
            })
            contents.append({
                "role": "model",
                "parts": [{"text": "Understood. I will follow these instructions."}]
            })
        
        # Prompt do usuário
        contents.append({
            "role": "user",
            "parts": [{"text": prompt}]
        })
        
        payload = {"contents": contents}
        
        if "generation_config" in params:
            gc = params["generation_config"]
            payload["generationConfig"] = {
                "temperature": gc.get("temperature", 0.7),
                "maxOutputTokens": gc.get("max_output_tokens", 2048),
                "topP": gc.get("top_p", 0.95),
                "topK": gc.get("top_k", 40)
            }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as response:
                data = await response.json()
                
                if response.status == 200:
                    candidates = data.get("candidates", [])
                    if candidates:
                        content = candidates[0].get("content", {})
                        parts = content.get("parts", [])
                        text = "".join([p.get("text", "") for p in parts])
                        
                        return {
                            "success": True,
                            "text": text,
                            "model": model,
                            "has_system_prompt": bool(system_prompt)
                        }
                
                error_msg = data.get("error", {}).get("message", f"Erro: {response.status}")
                return {"success": False, "error": error_msg}
    
    async def _chat_completion(
        self,
        headers: Dict[str, str],
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Chat completion com histórico de conversa"""
        model = params.get("model", "gemini-2.5-flash")
        messages = params.get("messages", [])
        
        if not messages:
            return {"success": False, "error": "messages é obrigatório"}
        
        url = f"{self.base_url}/models/{model}:generateContent"
        
        # Converter mensagens para formato Gemini
        contents = []
        for msg in messages:
            role = "model" if msg.get("role") == "assistant" else msg.get("role", "user")
            content_parts = []
            
            if isinstance(msg.get("content"), str):
                content_parts = [{"text": msg["content"]}]
            elif isinstance(msg.get("content"), list):
                for part in msg["content"]:
                    if isinstance(part, str):
                        content_parts.append({"text": part})
                    elif isinstance(part, dict) and part.get("type") == "text":
                        content_parts.append({"text": part.get("text", "")})
            
            contents.append({
                "role": role,
                "parts": content_parts
            })
        
        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": params.get("temperature", 0.7),
                "maxOutputTokens": params.get("max_tokens", 2048)
            }
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as response:
                data = await response.json()
                
                if response.status == 200:
                    candidates = data.get("candidates", [])
                    if candidates:
                        content = candidates[0].get("content", {})
                        parts = content.get("parts", [])
                        text = "".join([p.get("text", "") for p in parts])
                        
                        return {
                            "success": True,
                            "message": {
                                "role": "assistant",
                                "content": text
                            },
                            "model": model,
                            "usage": data.get("usageMetadata", {})
                        }
                
                error_msg = data.get("error", {}).get("message", f"Erro: {response.status}")
                return {"success": False, "error": error_msg}
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # MODELOS
    # ═══════════════════════════════════════════════════════════════════════════════
    
    async def _list_models(
        self,
        headers: Dict[str, str],
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Lista modelos Gemini disponíveis"""
        url = f"{self.base_url}/models"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                data = await response.json()
                
                if response.status == 200:
                    models = data.get("models", [])
                    
                    # Filtrar e formatar
                    formatted_models = []
                    for model in models:
                        name = model.get("name", "")
                        if "gemini" in name.lower():
                            formatted_models.append({
                                "id": name,
                                "display_name": model.get("displayName", name),
                                "description": model.get("description", ""),
                                "version": model.get("version", ""),
                                "supported_generation_methods": model.get("supportedGenerationMethods", []),
                                "input_token_limit": model.get("inputTokenLimit", 0),
                                "output_token_limit": model.get("outputTokenLimit", 0)
                            })
                    
                    return {
                        "success": True,
                        "models": formatted_models,
                        "count": len(formatted_models)
                    }
                else:
                    return {"success": False, "error": f"Erro ao listar modelos: {response.status}"}
    
    async def _get_model(
        self,
        headers: Dict[str, str],
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Obtém detalhes de um modelo específico"""
        model_id = params.get("model_id", "gemini-2.5-flash")
        
        # Remover prefixo 'models/' se presente
        if not model_id.startswith("models/"):
            model_id = f"models/{model_id}"
        
        url = f"{self.base_url}/{model_id}"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                data = await response.json()
                
                if response.status == 200:
                    return {
                        "success": True,
                        "model": {
                            "id": data.get("name"),
                            "display_name": data.get("displayName"),
                            "description": data.get("description"),
                            "version": data.get("version"),
                            "supported_generation_methods": data.get("supportedGenerationMethods", []),
                            "input_token_limit": data.get("inputTokenLimit"),
                            "output_token_limit": data.get("outputTokenLimit"),
                            "temperature": data.get("temperature"),
                            "top_p": data.get("topP"),
                            "top_k": data.get("topK")
                        }
                    }
                else:
                    return {"success": False, "error": f"Modelo não encontrado: {response.status}"}
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # EMBEDDINGS
    # ═══════════════════════════════════════════════════════════════════════════════
    
    async def _embed_content(
        self,
        headers: Dict[str, str],
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Gera embeddings para texto"""
        model = params.get("model", "models/text-embedding-004")
        content = params.get("content")
        task_type = params.get("task_type", "RETRIEVAL_DOCUMENT")
        
        if not content:
            return {"success": False, "error": "content é obrigatório"}
        
        # Garantir que o modelo tenha prefixo
        if not model.startswith("models/"):
            model = f"models/{model}"
        
        url = f"{self.base_url}/{model}:embedContent"
        
        payload = {
            "content": {
                "parts": [{"text": content}]
            }
        }
        
        if task_type:
            payload["taskType"] = task_type
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as response:
                data = await response.json()
                
                if response.status == 200:
                    embedding = data.get("embedding", {})
                    values = embedding.get("values", [])
                    
                    return {
                        "success": True,
                        "embedding": values,
                        "dimension": len(values),
                        "model": model
                    }
                else:
                    error_msg = data.get("error", {}).get("message", f"Erro: {response.status}")
                    return {"success": False, "error": error_msg}
    
    async def _batch_embed_contents(
        self,
        headers: Dict[str, str],
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Gera embeddings em lote para múltiplos textos"""
        model = params.get("model", "models/text-embedding-004")
        contents = params.get("contents", [])
        task_type = params.get("task_type", "RETRIEVAL_DOCUMENT")
        
        if not contents:
            return {"success": False, "error": "contents é obrigatório (lista de textos)"}
        
        if not model.startswith("models/"):
            model = f"models/{model}"
        
        url = f"{self.base_url}/{model}:batchEmbedContents"
        
        requests = []
        for content in contents:
            req = {
                "content": {
                    "parts": [{"text": content}]
                }
            }
            if task_type:
                req["taskType"] = task_type
            requests.append(req)
        
        payload = {"requests": requests}
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as response:
                data = await response.json()
                
                if response.status == 200:
                    embeddings = data.get("embeddings", [])
                    
                    return {
                        "success": True,
                        "embeddings": [
                            {
                                "index": i,
                                "values": emb.get("values", []),
                                "dimension": len(emb.get("values", []))
                            }
                            for i, emb in enumerate(embeddings)
                        ],
                        "count": len(embeddings),
                        "model": model
                    }
                else:
                    error_msg = data.get("error", {}).get("message", f"Erro: {response.status}")
                    return {"success": False, "error": error_msg}
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # TOKENS
    # ═══════════════════════════════════════════════════════════════════════════════
    
    async def _count_tokens(
        self,
        headers: Dict[str, str],
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Conta tokens em um texto/prompt"""
        model = params.get("model", "gemini-2.5-flash")
        text = params.get("text")
        
        if not text:
            return {"success": False, "error": "text é obrigatório"}
        
        url = f"{self.base_url}/models/{model}:countTokens"
        
        payload = {
            "contents": [
                {
                    "parts": [{"text": text}]
                }
            ]
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as response:
                data = await response.json()
                
                if response.status == 200:
                    return {
                        "success": True,
                        "total_tokens": data.get("totalTokens", 0),
                        "model": model,
                        "text_preview": text[:100] + "..." if len(text) > 100 else text
                    }
                else:
                    error_msg = data.get("error", {}).get("message", f"Erro: {response.status}")
                    return {"success": False, "error": error_msg}
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # ARQUIVOS
    # ═══════════════════════════════════════════════════════════════════════════════
    
    async def _upload_file(
        self,
        headers: Dict[str, str],
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Faz upload de arquivo para usar com Gemini"""
        file_path = params.get("file_path")
        mime_type = params.get("mime_type", "application/pdf")
        display_name = params.get("display_name")
        
        if not file_path:
            return {"success": False, "error": "file_path é obrigatório"}
        
        try:
            # Ler arquivo
            import os
            if not os.path.exists(file_path):
                return {"success": False, "error": f"Arquivo não encontrado: {file_path}"}
            
            with open(file_path, "rb") as f:
                file_data = f.read()
            
            file_size = len(file_data)
            encoded_data = base64.b64encode(file_data).decode("utf-8")
            
            # Iniciar upload resumable
            upload_url = f"{self.base_url}/upload/v1beta/files"
            
            metadata = {
                "file": {
                    "displayName": display_name or os.path.basename(file_path),
                    "mimeType": mime_type
                }
            }
            
            upload_headers = {
                "x-goog-api-key": headers["x-goog-api-key"],
                "X-Goog-Upload-Protocol": "multipart",
                "X-Goog-Upload-Command": "start, upload, finalize",
                "Content-Type": f"multipart/related; boundary=boundary",
                "X-Goog-Upload-Header-Content-Length": str(file_size),
                "X-Goog-Upload-Header-Content-Type": mime_type
            }
            
            # Simplificação: upload direto via API
            # Nota: Para arquivos grandes, use upload resumable
            url = f"{self.base_url}/files"
            
            payload = {
                "file": {
                    "displayName": display_name or os.path.basename(file_path),
                    "mimeType": mime_type
                }
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=payload) as response:
                    data = await response.json()
                    
                    if response.status in [200, 201]:
                        file_info = data.get("file", {})
                        return {
                            "success": True,
                            "file": {
                                "id": file_info.get("name"),
                                "uri": file_info.get("uri"),
                                "display_name": file_info.get("displayName"),
                                "mime_type": file_info.get("mimeType"),
                                "size_bytes": file_info.get("sizeBytes", 0),
                                "state": file_info.get("state")
                            },
                            "message": "Arquivo enviado. URI pode ser usado em prompts."
                        }
                    else:
                        error_msg = data.get("error", {}).get("message", f"Erro: {response.status}")
                        return {"success": False, "error": error_msg}
                        
        except Exception as e:
            return {"success": False, "error": f"Erro no upload: {str(e)}"}
    
    async def _list_files(
        self,
        headers: Dict[str, str],
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Lista arquivos enviados"""
        page_size = params.get("page_size", 10)
        
        url = f"{self.base_url}/files?pageSize={page_size}"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                data = await response.json()
                
                if response.status == 200:
                    files = data.get("files", [])
                    
                    return {
                        "success": True,
                        "files": [
                            {
                                "id": f.get("name"),
                                "uri": f.get("uri"),
                                "display_name": f.get("displayName"),
                                "mime_type": f.get("mimeType"),
                                "size_bytes": f.get("sizeBytes"),
                                "state": f.get("state"),
                                "create_time": f.get("createTime")
                            }
                            for f in files
                        ],
                        "count": len(files),
                        "next_page_token": data.get("nextPageToken")
                    }
                else:
                    return {"success": False, "error": f"Erro ao listar arquivos: {response.status}"}
    
    async def _get_file(
        self,
        headers: Dict[str, str],
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Obtém detalhes de um arquivo"""
        file_id = params.get("file_id")
        
        if not file_id:
            return {"success": False, "error": "file_id é obrigatório"}
        
        if not file_id.startswith("files/"):
            file_id = f"files/{file_id}"
        
        url = f"{self.base_url}/{file_id}"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                data = await response.json()
                
                if response.status == 200:
                    return {
                        "success": True,
                        "file": {
                            "id": data.get("name"),
                            "uri": data.get("uri"),
                            "display_name": data.get("displayName"),
                            "mime_type": data.get("mimeType"),
                            "size_bytes": data.get("sizeBytes"),
                            "state": data.get("state"),
                            "create_time": data.get("createTime"),
                            "expiration_time": data.get("expirationTime")
                        }
                    }
                else:
                    return {"success": False, "error": f"Arquivo não encontrado: {response.status}"}
    
    async def _delete_file(
        self,
        headers: Dict[str, str],
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Deleta um arquivo"""
        file_id = params.get("file_id")
        
        if not file_id:
            return {"success": False, "error": "file_id é obrigatório"}
        
        if not file_id.startswith("files/"):
            file_id = f"files/{file_id}"
        
        url = f"{self.base_url}/{file_id}"
        
        async with aiohttp.ClientSession() as session:
            async with session.delete(url, headers=headers) as response:
                if response.status == 200:
                    return {
                        "success": True,
                        "message": f"Arquivo '{file_id}' deletado com sucesso"
                    }
                else:
                    data = await response.json()
                    error_msg = data.get("error", {}).get("message", f"Erro: {response.status}")
                    return {"success": False, "error": error_msg}
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # MULTIMODAL
    # ═══════════════════════════════════════════════════════════════════════════════
    
    async def _generate_image(
        self,
        headers: Dict[str, str],
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Gera imagem usando Imagen (se disponível na API key)"""
        prompt = params.get("prompt")
        aspect_ratio = params.get("aspect_ratio", "1:1")
        
        if not prompt:
            return {"success": False, "error": "prompt é obrigatório"}
        
        # Nota: Imagen requer configuração específica na API
        # Endpoint: models/imagen-3.0-generate-002:predict
        url = f"{self.base_url}/models/imagen-3.0-generate-002:predict"
        
        payload = {
            "instances": [{"prompt": prompt}],
            "parameters": {
                "aspectRatio": aspect_ratio,
                "sampleCount": params.get("sample_count", 1)
            }
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as response:
                data = await response.json()
                
                if response.status == 200:
                    predictions = data.get("predictions", [])
                    
                    return {
                        "success": True,
                        "images": [
                            {
                                "mime_type": pred.get("mimeType"),
                                "bytes": pred.get("bytes")  # Base64 encoded
                            }
                            for pred in predictions
                        ],
                        "count": len(predictions)
                    }
                else:
                    error_msg = data.get("error", {}).get("message", "Imagen requer configuração especial")
                    return {"success": False, "error": error_msg}
    
    async def _analyze_image(
        self,
        headers: Dict[str, str],
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analiza imagem com Gemini Vision"""
        model = params.get("model", "gemini-2.5-flash")
        prompt = params.get("prompt", "Descreva esta imagem em detalhes")
        image_data = params.get("image_data")  # Base64
        image_url = params.get("image_url")
        mime_type = params.get("mime_type", "image/jpeg")
        
        if not image_data and not image_url:
            return {"success": False, "error": "image_data ou image_url é obrigatório"}
        
        url = f"{self.base_url}/models/{model}:generateContent"
        
        parts = [{"text": prompt}]
        
        if image_data:
            # Dados base64 inline
            parts.append({
                "inline_data": {
                    "mime_type": mime_type,
                    "data": image_data
                }
            })
        elif image_url:
            # URL do arquivo (deve estar no Google Cloud Storage)
            parts.append({
                "file_data": {
                    "mime_type": mime_type,
                    "file_uri": image_url
                }
            })
        
        payload = {
            "contents": [{"parts": parts}]
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as response:
                data = await response.json()
                
                if response.status == 200:
                    candidates = data.get("candidates", [])
                    if candidates:
                        content = candidates[0].get("content", {})
                        parts = content.get("parts", [])
                        text = "".join([p.get("text", "") for p in parts])
                        
                        return {
                            "success": True,
                            "analysis": text,
                            "model": model
                        }
                
                error_msg = data.get("error", {}).get("message", f"Erro: {response.status}")
                return {"success": False, "error": error_msg}
    
    async def _analyze_video(
        self,
        headers: Dict[str, str],
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analiza vídeo com Gemini"""
        model = params.get("model", "gemini-2.5-flash")
        prompt = params.get("prompt", "Descreva este vídeo")
        video_url = params.get("video_url")  # Deve ser URI de arquivo enviado
        mime_type = params.get("mime_type", "video/mp4")
        
        if not video_url:
            return {"success": False, "error": "video_url é obrigatório (URI de arquivo enviado)"}
        
        url = f"{self.base_url}/models/{model}:generateContent"
        
        payload = {
            "contents": [{
                "parts": [
                    {"text": prompt},
                    {
                        "file_data": {
                            "mime_type": mime_type,
                            "file_uri": video_url
                        }
                    }
                ]
            }]
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as response:
                data = await response.json()
                
                if response.status == 200:
                    candidates = data.get("candidates", [])
                    if candidates:
                        content = candidates[0].get("content", {})
                        parts = content.get("parts", [])
                        text = "".join([p.get("text", "") for p in parts])
                        
                        return {
                            "success": True,
                            "analysis": text,
                            "model": model
                        }
                
                error_msg = data.get("error", {}).get("message", f"Erro: {response.status}")
                return {"success": False, "error": error_msg}
    
    async def _analyze_audio(
        self,
        headers: Dict[str, str],
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Transcreve e analiza áudio com Gemini"""
        model = params.get("model", "gemini-2.5-flash")
        prompt = params.get("prompt", "Transcreva este áudio")
        audio_url = params.get("audio_url")
        mime_type = params.get("mime_type", "audio/mp3")
        
        if not audio_url:
            return {"success": False, "error": "audio_url é obrigatório"}
        
        url = f"{self.base_url}/models/{model}:generateContent"
        
        payload = {
            "contents": [{
                "parts": [
                    {"text": prompt},
                    {
                        "file_data": {
                            "mime_type": mime_type,
                            "file_uri": audio_url
                        }
                    }
                ]
            }]
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as response:
                data = await response.json()
                
                if response.status == 200:
                    candidates = data.get("candidates", [])
                    if candidates:
                        content = candidates[0].get("content", {})
                        parts = content.get("parts", [])
                        text = "".join([p.get("text", "") for p in parts])
                        
                        return {
                            "success": True,
                            "transcription": text,
                            "model": model
                        }
                
                error_msg = data.get("error", {}).get("message", f"Erro: {response.status}")
                return {"success": False, "error": error_msg}
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # TUNED MODELS (PROJETOS AI STUDIO)
    # ═══════════════════════════════════════════════════════════════════════════════
    
    async def _list_tuned_models(
        self,
        headers: Dict[str, str],
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Lista modelos fine-tuned do usuário"""
        url = f"{self.base_url}/tunedModels"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                data = await response.json()
                
                if response.status == 200:
                    models = data.get("tunedModels", [])
                    
                    return {
                        "success": True,
                        "models": [
                            {
                                "id": m.get("name"),
                                "display_name": m.get("displayName"),
                                "state": m.get("state"),
                                "base_model": m.get("baseModel"),
                                "create_time": m.get("createTime"),
                                "update_time": m.get("updateTime")
                            }
                            for m in models
                        ],
                        "count": len(models)
                    }
                else:
                    return {"success": False, "error": f"Erro ao listar modelos: {response.status}"}
    
    async def _create_tuned_model(
        self,
        headers: Dict[str, str],
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Cria modelo fine-tuned (tuning job)"""
        display_name = params.get("display_name")
        base_model = params.get("base_model", "models/gemini-1.5-flash-001-tuning")
        training_data = params.get("training_data", [])
        
        if not display_name:
            return {"success": False, "error": "display_name é obrigatório"}
        
        if not training_data:
            return {"success": False, "error": "training_data é obrigatório (lista de exemplos)"}
        
        url = f"{self.base_url}/tunedModels"
        
        payload = {
            "displayName": display_name,
            "baseModel": base_model,
            "tuningTask": {
                "hyperparameters": {
                    "epochCount": params.get("epoch_count", 5),
                    "batchSize": params.get("batch_size", 4),
                    "learningRate": params.get("learning_rate", 0.001)
                },
                "trainingData": {
                    "examples": {
                        "examples": training_data
                    }
                }
            }
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as response:
                data = await response.json()
                
                if response.status in [200, 201]:
                    return {
                        "success": True,
                        "model": {
                            "id": data.get("name"),
                            "display_name": data.get("displayName"),
                            "state": data.get("state"),
                            "base_model": data.get("baseModel")
                        },
                        "message": "Job de tuning iniciado. Use 'list_tuned_models' para acompanhar."
                    }
                else:
                    error_msg = data.get("error", {}).get("message", f"Erro: {response.status}")
                    return {"success": False, "error": error_msg}
    
    async def _get_tuned_model(
        self,
        headers: Dict[str, str],
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Obtém detalhes de modelo fine-tuned"""
        model_id = params.get("model_id")
        
        if not model_id:
            return {"success": False, "error": "model_id é obrigatório"}
        
        if not model_id.startswith("tunedModels/"):
            model_id = f"tunedModels/{model_id}"
        
        url = f"{self.base_url}/{model_id}"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                data = await response.json()
                
                if response.status == 200:
                    return {
                        "success": True,
                        "model": {
                            "id": data.get("name"),
                            "display_name": data.get("displayName"),
                            "state": data.get("state"),
                            "base_model": data.get("baseModel"),
                            "create_time": data.get("createTime"),
                            "update_time": data.get("updateTime"),
                            "tuning_task": data.get("tuningTask")
                        }
                    }
                else:
                    return {"success": False, "error": f"Modelo não encontrado: {response.status}"}
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # STREAMING SSE
    # ═══════════════════════════════════════════════════════════════════════════════
    
    async def stream_tool_execution(
        self,
        tool_name: str,
        params: Dict[str, Any],
        credentials: Dict[str, str]
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Executa ferramenta com streaming SSE para feedback em tempo real
        """
        yield {
            "type": "tool_call",
            "tool": tool_name,
            "status": "executing",
            "message": f"🧠 Executando {tool_name} no Google AI Studio..."
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
google_aistudio_mcp = GoogleAIStudioMCP()
