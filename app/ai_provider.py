from __future__ import annotations

import asyncio
from typing import List, Dict, Any

from openai import AsyncOpenAI

from .config import settings


class AIProvider:
    def __init__(self) -> None:
        self._client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self._model = settings.OPENAI_CHAT_MODEL

    async def generate_reply(
        self,
        system_prompt: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 400,
    ) -> str:
        response = await self._client.chat.completions.create(
            model=self._model,
            temperature=temperature,
            max_tokens=max_tokens,
            messages=[{"role": "system", "content": system_prompt}, *messages],
        )
        return response.choices[0].message.content or ""

    async def moderate(self, text: str) -> Dict[str, Any] | None:
        """Return moderation result dict or None if moderation API not available."""
        try:
            result = await self._client.moderations.create(
                model=settings.OPENAI_MODERATION_MODEL,
                input=text,
            )
            # Align to moderation output shape
            if hasattr(result, "results"):
                return result.results[0].__dict__ if result.results else {"flagged": False}
            return None
        except Exception:
            return None


ai = AIProvider()
