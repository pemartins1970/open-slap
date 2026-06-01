import aiohttp
import logging
from typing import Dict, Any, List, Optional, AsyncGenerator
from backend.config import settings

logger = logging.getLogger(__name__)

class AIGatewayClient:
    def __init__(self):
        self.base_url = settings.AI_GATEWAY_URL.rstrip("/")
        self.api_key = settings.AI_GATEWAY_API_KEY
        self.enabled = settings.AI_GATEWAY_ENABLED
        self.timeout = aiohttp.ClientTimeout(total=120)

    async def chat_completion(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> Dict[str, Any]:
        if not self.enabled:
            raise AIGatewayDisabled("AI Gateway disabled via settings")

        payload: Dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
        }
        if max_tokens:
            payload["max_tokens"] = max_tokens

        headers = {
            "Content-Type": "application/json",
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.post(
                    f"{self.base_url}/v1/chat/completions",
                    json=payload,
                    headers=headers,
                ) as resp:
                    if resp.status != 200:
                        text = await resp.text()
                        logger.error(f"AI Gateway error {resp.status}: {text[:200]}")
                        raise AIGatewayError(f"AI Gateway returned {resp.status}")
                    return await resp.json()
        except aiohttp.ClientConnectorError as e:
            logger.error(f"AI Gateway connection failed: {e}")
            raise AIGatewayError(f"Cannot connect to AI Gateway at {self.base_url}")
        except AIGatewayError:
            raise
        except Exception as e:
            logger.error(f"AI Gateway unexpected error: {e}")
            raise AIGatewayError(str(e))

    async def health_check(self) -> bool:
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
                async with session.get(f"{self.base_url}/health") as resp:
                    return resp.status == 200
        except Exception:
            return False


class AIGatewayError(Exception):
    pass


class AIGatewayDisabled(AIGatewayError):
    pass


ai_gateway = AIGatewayClient()
