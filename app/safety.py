from __future__ import annotations

import re
from typing import Tuple

from .ai_provider import ai


CRISIS_PATTERNS = [
    r"самоуби(й|т)|свести сч[её]ты с жизнью|не хочу жить",
    r"суицид|убить себя",
    r"серьезн[ао] депресс",
]

NSFW_PATTERNS = [
    r"порн|18\+\+|обнажен",
    r"опис(ани|ывать) интим",
    r"секс(уальн|)\b",
]


def is_crisis(text: str) -> bool:
    lowered = text.lower()
    return any(re.search(p, lowered) for p in CRISIS_PATTERNS)


def is_nsfw_request(text: str) -> bool:
    lowered = text.lower()
    return any(re.search(p, lowered) for p in NSFW_PATTERNS)


async def moderate_text(text: str) -> Tuple[bool, str | None]:
    """Returns (flagged, reason)."""
    result = await ai.moderate(text)
    if not result:
        return False, None
    flagged = bool(getattr(result, "flagged", False) if hasattr(result, "flagged") else result.get("flagged", False))
    if not flagged:
        return False, None
    # Try to infer a simple reason
    categories = getattr(result, "categories", None) or result.get("categories", {})
    reason = ", ".join([k for k, v in categories.items() if v]) if isinstance(categories, dict) else "unsafe"
    return True, reason or "unsafe"


CRISIS_REPLY_RU = (
    "Мне очень жаль, что тебе так тяжело. Я рядом и готова выслушать. "
    "Пожалуйста, обратись за срочной помощью: 112 (Экстренные службы). "
    "В России: Линия доверия МЧС: 8-800-200-99-94. «Я рядом» — 8-800-600-31-14. "
    "Если есть возможность — свяжись с близкими или специалистом. Ты не один."
)

NSFW_REFUSAL_RU = (
    "Давай оставим откровенный контент за границами. Я за уютный, тёплый флирт без пошлостей. 😊"
)


def crisis_response() -> str:
    return CRISIS_REPLY_RU


def nsfw_refusal() -> str:
    return NSFW_REFUSAL_RU
