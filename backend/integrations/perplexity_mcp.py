"""
Perplexity MCP Integration
AI Search Tools para OpenSlap
"""

from typing import Dict, Any, List, Optional, AsyncGenerator
import aiohttp
import json

class PerplexityMCP:
    """
    Perplexity MCP - Ferramentas de Pesquisa IA
    
    Funcionalidades:
    - Deep search e research
    - Pro search com fontes
    - YouTube search
    - News search
    - Academic search
    - URL summarization
    """
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.perplexity.ai"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        self.models = {
            "online": "sonar",
            "pro": "sonar-pro",
            "reasoning": "sonar-reasoning",
            "deep": "sonar-deep-research"
        }
    
    async def _make_request(self, endpoint: str, data: Dict) -> Dict[str, Any]:
        """Faz requisição à API do Perplexity"""
        url = f"{self.base_url}{endpoint}"
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url,
                headers=self.headers,
                json=data
            ) as response:
                if response.status in [200, 201]:
                    return await response.json()
                else:
                    error_text = await response.text()
                    raise Exception(f"Perplexity API Error {response.status}: {error_text}")
    
    async def _make_streaming_request(self, endpoint: str,
                                     data: Dict) -> AsyncGenerator[str, None]:
        """Faz requisição streaming"""
        url = f"{self.base_url}{endpoint}"
        data["stream"] = True
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url,
                headers=self.headers,
                json=data
            ) as response:
                async for line in response.content:
                    line = line.decode("utf-8").strip()
                    if line.startswith("data: "):
                        data_str = line[6:]
                        if data_str == "[DONE]":
                            break
                        try:
                            chunk = json.loads(data_str)
                            content = chunk.get("choices", [{}])[0].get("delta", {}).get("content", "")
                            if content:
                                yield content
                        except:
                            pass
    
    # ========== SEARCH METHODS ==========
    
    async def search(self, query: str, model: str = "online",
                    max_tokens: int = 2000, temperature: float = 0.7,
                    return_citations: bool = True) -> Dict[str, Any]:
        """
        Pesquisa geral com resposta completa
        
        Args:
            query: Pergunta ou tópico
            model: online, pro, reasoning, deep
        """
        endpoint = "/chat/completions"
        
        model_id = self.models.get(model, model)
        
        data = {
            "model": model_id,
            "messages": [
                {
                    "role": "system",
                    "content": "Você é um assistente de pesquisa. Forneça respostas precisas e bem fundamentadas com fontes quando possível."
                },
                {
                    "role": "user",
                    "content": query
                }
            ],
            "max_tokens": max_tokens,
            "temperature": temperature,
            "return_images": False,
            "return_related_questions": True
        }
        
        return await self._make_request(endpoint, data)
    
    async def search_stream(self, query: str, model: str = "online",
                          max_tokens: int = 2000) -> AsyncGenerator[str, None]:
        """Pesquisa com streaming de resposta"""
        endpoint = "/chat/completions"
        
        model_id = self.models.get(model, model)
        
        data = {
            "model": model_id,
            "messages": [
                {
                    "role": "user",
                    "content": query
                }
            ],
            "max_tokens": max_tokens,
            "stream": True
        }
        
        async for chunk in self._make_streaming_request(endpoint, data):
            yield chunk
    
    async def deep_search(self, query: str, context: str = None,
                         max_tokens: int = 4000) -> Dict[str, Any]:
        """
        Pesquisa profunda para research completo
        
        Busca aprofundada com análise extensiva
        """
        endpoint = "/chat/completions"
        
        content = query
        if context:
            content = f"Contexto: {context}\n\nPergunta: {query}"
        
        data = {
            "model": "sonar-deep-research",
            "messages": [
                {
                    "role": "system",
                    "content": "Você é um pesquisador especializado. Realize análise profunda, identifique fontes primárias, e forneça conclusões bem fundamentadas."
                },
                {
                    "role": "user",
                    "content": content
                }
            ],
            "max_tokens": max_tokens,
            "temperature": 0.5,
            "return_related_questions": True
        }
        
        return await self._make_request(endpoint, data)
    
    async def pro_search(self, query: str, focus: str = "comprehensive",
                        max_tokens: int = 3000) -> Dict[str, Any]:
        """
        Pro search com análise detalhada
        
        Args:
            focus: comprehensive, scientific, business, technical
        """
        endpoint = "/chat/completions"
        
        focus_prompts = {
            "comprehensive": "Forneça uma análise completa e abrangente",
            "scientific": "Foque em fontes científicas e pesquisas acadêmicas",
            "business": "Análise de negócios com dados de mercado",
            "technical": "Detalhamento técnico com especificações"
        }
        
        system_content = focus_prompts.get(focus, focus_prompts["comprehensive"])
        
        data = {
            "model": "sonar-pro",
            "messages": [
                {
                    "role": "system",
                    "content": system_content
                },
                {
                    "role": "user",
                    "content": query
                }
            ],
            "max_tokens": max_tokens,
            "return_citations": True
        }
        
        return await self._make_request(endpoint, data)
    
    async def news_search(self, query: str, timeframe: str = "week",
                         max_results: int = 10) -> Dict[str, Any]:
        """
        Busca notícias recentes
        
        Args:
            timeframe: day, week, month, year
        """
        endpoint = "/chat/completions"
        
        time_context = {
            "day": "nas últimas 24 horas",
            "week": "na última semana",
            "month": "no último mês",
            "year": "no último ano"
        }
        
        period = time_context.get(timeframe, "recentemente")
        
        data = {
            "model": "sonar",
            "messages": [
                {
                    "role": "system",
                    "content": f"Você é um especialista em notícias. Busque notícias recentes {period}, priorizando fontes jornalísticas confiáveis."
                },
                {
                    "role": "user",
                    "content": f"Notícias sobre: {query}"
                }
            ],
            "max_tokens": 2000,
            "search_recency_filter": timeframe
        }
        
        return await self._make_request(endpoint, data)
    
    async def academic_search(self, query: str, max_tokens: int = 3000) -> Dict[str, Any]:
        """Busca acadêmica e científica"""
        endpoint = "/chat/completions"
        
        data = {
            "model": "sonar-pro",
            "messages": [
                {
                    "role": "system",
                    "content": "Você é um pesquisador acadêmico. Busque papers, estudos peer-reviewed, e fontes científicas. Inclua referências quando possível."
                },
                {
                    "role": "user",
                    "content": f"Pesquisa acadêmica sobre: {query}"
                }
            ],
            "max_tokens": max_tokens,
            "return_citations": True,
            "search_domain_filter": ["academia.edu", "arxiv.org", "pubmed.ncbi.nlm.nih.gov", "scholar.google.com"]
        }
        
        return await self._make_request(endpoint, data)
    
    async def summarize_url(self, url: str, detail_level: str = "comprehensive") -> Dict[str, Any]:
        """
        Resume conteúdo de URL
        
        Args:
            detail_level: brief, comprehensive, detailed
        """
        endpoint = "/chat/completions"
        
        length_prompts = {
            "brief": "Resuma em 2-3 parágrafos principais",
            "comprehensive": "Forneça um resumo completo mantendo pontos importantes",
            "detailed": "Análise detalhada com todos os pontos relevantes"
        }
        
        prompt = length_prompts.get(detail_level, length_prompts["comprehensive"])
        
        data = {
            "model": "sonar",
            "messages": [
                {
                    "role": "system",
                    "content": f"Você é um especialista em análise de conteúdo. {prompt}"
                },
                {
                    "role": "user",
                    "content": f"Analise e resuma o conteúdo de: {url}"
                }
            ],
            "max_tokens": 2000
        }
        
        return await self._make_request(endpoint, data)
    
    async def research_with_files(self, query: str,
                                  file_urls: List[str] = None,
                                  max_tokens: int = 4000) -> Dict[str, Any]:
        """
        Pesquisa com análise de arquivos
        
        Combina search com análise de documentos
        """
        endpoint = "/chat/completions"
        
        content_parts = [query]
        if file_urls:
            content_parts.append("\n\nAnalise também estes arquivos:")
            for url in file_urls:
                content_parts.append(f"- {url}")
        
        data = {
            "model": "sonar-deep-research",
            "messages": [
                {
                    "role": "system",
                    "content": "Você é um pesquisador especializado em análise de documentos e pesquisa online. Integre informações de fontes múltiplas."
                },
                {
                    "role": "user",
                    "content": "\n".join(content_parts)
                }
            ],
            "max_tokens": max_tokens
        }
        
        return await self._make_request(endpoint, data)
    
    # ========== UTILITÁRIOS ==========
    
    def extract_citations(self, response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extrai citações de uma resposta"""
        citations = response.get("citations", [])
        return citations
    
    def extract_related_questions(self, response: Dict[str, Any]) -> List[str]:
        """Extrai perguntas relacionadas"""
        return response.get("related_questions", [])
    
    def get_answer_text(self, response: Dict[str, Any]) -> str:
        """Extrai texto da resposta"""
        try:
            return response["choices"][0]["message"]["content"]
        except (KeyError, IndexError):
            return ""
    
    async def test_connection(self) -> bool:
        """Testa conexão"""
        try:
            result = await self.search("test", max_tokens=10)
            return "choices" in result
        except:
            return False


perplexity_mcp = None

def init_perplexity_mcp(api_key: str):
    global perplexity_mcp
    perplexity_mcp = PerplexityMCP(api_key)
    return perplexity_mcp
