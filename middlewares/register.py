from __future__ import annotations
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery

from database.db import get_or_create_user


class RegisterMiddleware(BaseMiddleware):
    """
    Automatically registers every user in the DB on first interaction.
    Attaches `db_user` to data so handlers can use it without another DB call.
    """

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        # Extract the telegram user object
        tg_user = None
        if isinstance(event, Message):
            tg_user = event.from_user
        elif isinstance(event, CallbackQuery):
            tg_user = event.from_user

        if tg_user:
            db_user = await get_or_create_user(
                user_id=tg_user.id,
                username=tg_user.username,
                full_name=tg_user.full_name,
            )
            data["db_user"] = db_user
            
            # Print user info to terminal for easy ID lookup
            action = "Message" if isinstance(event, Message) else "Callback"
            text = getattr(event, "text", getattr(event, "data", ""))
            log_msg = f"[USER LOG] ID: {tg_user.id} | Name: {tg_user.full_name} | Username: {tg_user.username} | {action}: {text}"
            try:
                print(log_msg)
            except UnicodeEncodeError:
                import sys
                sys.stdout.buffer.write((log_msg + "\n").encode("utf-8", "ignore"))

        return await handler(event, data)
