import os
import json
import asyncio
from typing import Any, Dict, Optional

import aiohttp
from asyncio_throttle import Throttler
from dotenv import load_dotenv
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
load_dotenv(dotenv_path=BASE_DIR / ".env", override=False)


def _sanitize_text(v: Any) -> str:
    s = str(v or "").strip()
    if (
        (s.startswith("`") and s.endswith("`"))
        or (s.startswith('"') and s.endswith('"'))
        or (s.startswith("'") and s.endswith("'"))
    ):
        s = s[1:-1].strip()
    return s.strip(" ,")


def _env_int(name: str, default: int) -> int:
    raw = str(os.getenv(name) or "").strip()
    try:
        return int(raw)
    except Exception:
        return int(default)


class TelegramMCPServer:
    def __init__(self) -> None:
        self.bot_token = _sanitize_text(os.getenv("TELEGRAM_BOT_TOKEN"))
        self.backend_url = _sanitize_text(
            os.getenv("OPENSLAP_BACKEND_URL") or "http://127.0.0.1:5150"
        ).rstrip("/")
        self.mcp_secret = _sanitize_text(os.getenv("OPENSLAP_MCP_SECRET"))
        per_min = _env_int("OPENSLAP_TELEGRAM_RATE_LIMIT_PER_MIN", 20)
        if per_min < 1:
            per_min = 1
        self.throttler = Throttler(rate_limit=per_min, period=60.0)
        self._offset = 0

    def _headers(self) -> Dict[str, str]:
        return {"X-MCP-Secret": self.mcp_secret}

    def _tg_url(self, method: str) -> str:
        return f"https://api.telegram.org/bot{self.bot_token}/{method.lstrip('/')}"

    async def _tg_get(self, session: aiohttp.ClientSession, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        async with self.throttler:
            async with session.get(self._tg_url(method), params=params) as resp:
                data = await resp.json(content_type=None)
                return {"status": resp.status, "data": data}

    async def _tg_post(self, session: aiohttp.ClientSession, method: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        async with self.throttler:
            async with session.post(self._tg_url(method), json=payload) as resp:
                data = await resp.json(content_type=None)
                return {"status": resp.status, "data": data}

    async def _backend_get(self, session: aiohttp.ClientSession, path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        url = f"{self.backend_url}/{path.lstrip('/')}"
        async with self.throttler:
            async with session.get(url, params=params or {}, headers=self._headers()) as resp:
                data = await resp.json(content_type=None)
                return {"status": resp.status, "data": data}

    async def _backend_post(self, session: aiohttp.ClientSession, path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.backend_url}/{path.lstrip('/')}"
        async with self.throttler:
            async with session.post(url, json=payload, headers=self._headers()) as resp:
                data = await resp.json(content_type=None)
                return {"status": resp.status, "data": data}

    async def _send_text(self, session: aiohttp.ClientSession, chat_id: str, text: str) -> None:
        payload = {"chat_id": chat_id, "text": text}
        await self._tg_post(session, "sendMessage", payload)

    async def _status(self, session: aiohttp.ClientSession, telegram_user_id: str, chat_id: str) -> bool:
        resp = await self._backend_get(
            session,
            "/connectors/telegram/status",
            params={"telegram_user_id": telegram_user_id, "chat_id": chat_id},
        )
        if resp["status"] >= 400:
            return False
        return bool((resp.get("data") or {}).get("linked"))

    async def _handle_text(self, session: aiohttp.ClientSession, telegram_user_id: str, chat_id: str, text: str, message_id: Optional[str]) -> None:
        msg = (text or "").strip()
        if not msg:
            return

        lower = msg.lower()
        if lower.startswith("/start"):
            await self._send_text(
                session,
                chat_id,
                "Open Slap Telegram\n\n"
                "1) No app: Conectores → Telegram → Gerar código\n"
                "2) Aqui: /link SEU_CODIGO\n"
                "3) Para desconectar: /unlink",
            )
            return

        if lower.startswith("/link"):
            parts = msg.split(None, 1)
            code = parts[1].strip() if len(parts) > 1 else ""
            if not code:
                await self._send_text(session, chat_id, "Use: /link SEU_CODIGO")
                return
            resp = await self._backend_post(
                session,
                "/connectors/telegram/link",
                {"code": code, "telegram_user_id": telegram_user_id, "chat_id": chat_id},
            )
            if resp["status"] >= 400:
                await self._send_text(session, chat_id, "Falha ao vincular. Gere um novo código no app e tente de novo.")
                return
            await self._send_text(session, chat_id, "✅ Vinculado. Pode mandar mensagens.")
            return

        if lower.startswith("/unlink"):
            resp = await self._backend_post(
                session,
                "/connectors/telegram/unlink",
                {"telegram_user_id": telegram_user_id, "chat_id": chat_id},
            )
            if resp["status"] >= 400:
                await self._send_text(session, chat_id, "Falha ao desvincular.")
                return
            await self._send_text(session, chat_id, "✅ Desvinculado.")
            return

        linked = await self._status(session, telegram_user_id, chat_id)
        if not linked:
            await self._send_text(session, chat_id, "Este chat ainda não está vinculado. No app, gere um código e use: /link SEU_CODIGO")
            return

        resp = await self._backend_post(
            session,
            "/connectors/telegram/inbound",
            {
                "telegram_user_id": telegram_user_id,
                "chat_id": chat_id,
                "message": msg,
                "message_id": message_id,
            },
        )
        reply = str((resp.get("data") or {}).get("reply") or "").strip()
        if not reply:
            reply = "Não consegui responder agora."
        await self._send_text(session, chat_id, reply)

    async def run(self) -> None:
        if not self.bot_token:
            raise RuntimeError("TELEGRAM_BOT_TOKEN não configurado.")
        if not self.mcp_secret:
            raise RuntimeError("OPENSLAP_MCP_SECRET não configurado.")
        if not self.backend_url:
            raise RuntimeError("OPENSLAP_BACKEND_URL não configurado.")

        timeout = aiohttp.ClientTimeout(total=40)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            while True:
                params = {
                    "timeout": 30,
                    "offset": self._offset,
                    "allowed_updates": json.dumps(["message"]),
                }
                polled = await self._tg_get(session, "getUpdates", params=params)
                data = polled.get("data") or {}
                ok = bool(data.get("ok"))
                if not ok:
                    await asyncio.sleep(2)
                    continue
                updates = data.get("result") or []
                if not isinstance(updates, list):
                    await asyncio.sleep(1)
                    continue
                for upd in updates:
                    if not isinstance(upd, dict):
                        continue
                    upd_id = upd.get("update_id")
                    if isinstance(upd_id, int):
                        self._offset = max(self._offset, upd_id + 1)
                    msg = upd.get("message") or {}
                    if not isinstance(msg, dict):
                        continue
                    chat = msg.get("chat") or {}
                    frm = msg.get("from") or {}
                    chat_id = str((chat or {}).get("id") or "").strip()
                    user_id = str((frm or {}).get("id") or "").strip()
                    text = str(msg.get("text") or "")
                    message_id = str(msg.get("message_id") or "").strip() or None
                    if not (chat_id and user_id):
                        continue
                    try:
                        await self._handle_text(session, user_id, chat_id, text, message_id)
                    except Exception:
                        continue


async def _main() -> None:
    server = TelegramMCPServer()
    await server.run()


if __name__ == "__main__":
    asyncio.run(_main())
