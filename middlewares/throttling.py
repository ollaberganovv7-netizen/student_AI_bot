from __future__ import annotations
"""
Anti-spam / Throttling middleware.

Protects the bot from:
- Rapid button clicks (DDoS-like behavior)
- Multiple parallel expensive AI requests from one user
- Spam users that try to drain OpenAI credits
"""
import time
import asyncio
import logging
from typing import Callable, Dict, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery

logger = logging.getLogger(__name__)


class ThrottlingMiddleware(BaseMiddleware):
    """
    Per-user rate limit:
    - Messages: at most 1 per `message_rate` seconds
    - Callbacks: at most 1 per `callback_rate` seconds

    If exceeded — silently drops the update (or shows a warning).
    """

    def __init__(self, message_rate: float = 0.5, callback_rate: float = 0.3):
        super().__init__()
        self.message_rate = message_rate
        self.callback_rate = callback_rate
        self._last_msg: Dict[int, float] = {}
        self._last_cb: Dict[int, float] = {}
        self._warned: Dict[int, float] = {}  # to avoid spamming "slow down" message

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        user_id = None
        is_message = False
        is_callback = False

        if isinstance(event, Message):
            user_id = event.from_user.id
            is_message = True
        elif isinstance(event, CallbackQuery):
            user_id = event.from_user.id
            is_callback = True

        if user_id is None:
            return await handler(event, data)

        now = time.time()

        if is_message:
            last = self._last_msg.get(user_id, 0)
            if now - last < self.message_rate:
                # Spam — drop silently
                return None
            self._last_msg[user_id] = now

        if is_callback:
            last = self._last_cb.get(user_id, 0)
            if now - last < self.callback_rate:
                # Tell user to slow down (only once per 5 sec)
                last_warn = self._warned.get(user_id, 0)
                if now - last_warn > 5:
                    self._warned[user_id] = now
                    try:
                        await event.answer("⏳ Sekinroq! Iltimos, kuting.", show_alert=False)
                    except Exception:
                        pass
                return None
            self._last_cb[user_id] = now

        return await handler(event, data)


class GenerationLockMiddleware(BaseMiddleware):
    """
    Prevents the same user from triggering multiple expensive AI generations
    in parallel. Saves money on OpenAI/AI API.

    Used as a lock around handlers that call AI services.
    Uses asyncio.Lock per user.
    """

    def __init__(self):
        super().__init__()
        self._locks: Dict[int, asyncio.Lock] = {}

    def get_lock(self, user_id: int) -> asyncio.Lock:
        if user_id not in self._locks:
            self._locks[user_id] = asyncio.Lock()
        return self._locks[user_id]

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        user_id = None
        if isinstance(event, (Message, CallbackQuery)):
            user_id = event.from_user.id

        if user_id is None:
            return await handler(event, data)

        # Pass the lock to the handler (handlers that do AI work can use it)
        data["user_lock"] = self.get_lock(user_id)
        return await handler(event, data)
