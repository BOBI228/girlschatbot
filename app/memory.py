from __future__ import annotations

from typing import Dict, List, Tuple
from cachetools import LRUCache


class ConversationMemory:
    """In-memory short-term memory for recent messages per chat."""

    def __init__(self, max_messages: int = 12) -> None:
        self._store: LRUCache[int, List[Tuple[str, str]]] = LRUCache(maxsize=4096)
        self._max = max_messages
        self._adult_confirmed: Dict[int, bool] = {}

    def append(self, chat_id: int, role: str, content: str) -> None:
        history = self._store.get(chat_id, [])
        history.append((role, content))
        if len(history) > self._max:
            history = history[-self._max :]
        self._store[chat_id] = history

    def get_messages(self, chat_id: int) -> List[Dict[str, str]]:
        history = self._store.get(chat_id, [])
        return [{"role": role, "content": content} for role, content in history]

    def clear(self, chat_id: int) -> None:
        self._store.pop(chat_id, None)

    def set_adult(self, chat_id: int, is_adult: bool) -> None:
        self._adult_confirmed[chat_id] = is_adult

    def is_adult(self, chat_id: int) -> bool:
        return self._adult_confirmed.get(chat_id, False)


memory = ConversationMemory()
