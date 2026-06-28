from __future__ import annotations
"""
Channel Post Reactions handler.
Adds inline reaction buttons to channel posts and tracks who clicked.
"""

import logging
from aiogram import Router, F, Bot
from aiogram.types import (
    CallbackQuery, Message,
    InlineKeyboardMarkup, InlineKeyboardButton,
)
from aiogram.filters import Command

from sqlalchemy import select, and_, func, delete
from database.db import async_session
from database.models import PostReaction
from config import ADMIN_IDS

logger = logging.getLogger(__name__)
router = Router()

# Available reaction emojis
REACTIONS = ["🔥", "👍", "❤️", "😂", "😮", "👎"]


def _reaction_kb(chat_id: int, message_id: int, counts: dict[str, int] = None) -> InlineKeyboardMarkup:
    """Build reaction buttons with counts."""
    if counts is None:
        counts = {}
    buttons = []
    row = []
    for emoji in REACTIONS:
        count = counts.get(emoji, 0)
        label = f"{emoji} {count}" if count > 0 else emoji
        row.append(InlineKeyboardButton(
            text=label,
            callback_data=f"react:{chat_id}:{message_id}:{emoji}"
        ))
        if len(row) == 3:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    # Stats button for admin
    total = sum(counts.values()) if counts else 0
    buttons.append([InlineKeyboardButton(
        text=f"📊 {total}" if total > 0 else "📊",
        callback_data=f"rstats:{chat_id}:{message_id}"
    )])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


async def _get_counts(chat_id: int, message_id: int) -> dict[str, int]:
    """Get reaction counts for a message."""
    async with async_session() as session:
        result = await session.execute(
            select(PostReaction.emoji, func.count(PostReaction.id))
            .where(and_(
                PostReaction.chat_id == chat_id,
                PostReaction.message_id == message_id
            ))
            .group_by(PostReaction.emoji)
        )
        return dict(result.all())


async def _toggle_reaction(chat_id: int, message_id: int, user_id: int, user_name: str, emoji: str) -> bool:
    """Toggle a reaction. Returns True if added, False if removed."""
    async with async_session() as session:
        # Check if user already reacted with this emoji
        existing = await session.execute(
            select(PostReaction).where(and_(
                PostReaction.chat_id == chat_id,
                PostReaction.message_id == message_id,
                PostReaction.user_id == user_id,
                PostReaction.emoji == emoji
            ))
        )
        reaction = existing.scalar_one_or_none()

        if reaction:
            # Remove reaction (toggle off)
            await session.delete(reaction)
            await session.commit()
            return False
        else:
            # Remove any other reaction by this user on this message
            await session.execute(
                delete(PostReaction).where(and_(
                    PostReaction.chat_id == chat_id,
                    PostReaction.message_id == message_id,
                    PostReaction.user_id == user_id,
                ))
            )
            # Add new reaction
            new_reaction = PostReaction(
                chat_id=chat_id,
                message_id=message_id,
                user_id=user_id,
                user_name=user_name,
                emoji=emoji,
            )
            session.add(new_reaction)
            await session.commit()
            return True


# ══════════════════════════════════════════════════════════════════════════════
# AUTO-ADD REACTIONS TO CHANNEL POSTS
# ══════════════════════════════════════════════════════════════════════════════

@router.channel_post()
async def auto_add_reactions(message: Message):
    """Automatically add reaction buttons to every new channel post."""
    logger.info(f"Channel post received: chat={message.chat.id} msg={message.message_id}")
    try:
        kb = _reaction_kb(message.chat.id, message.message_id)
        await message.edit_reply_markup(reply_markup=kb)
        logger.info("Reaction buttons added successfully")
    except Exception as e:
        logger.error(f"Could not add reactions to channel post: {e}")


# ══════════════════════════════════════════════════════════════════════════════
# HANDLE REACTION CLICK
# ══════════════════════════════════════════════════════════════════════════════

@router.callback_query(F.data.startswith("react:"))
async def handle_reaction(callback: CallbackQuery):
    """Handle reaction button click."""
    parts = callback.data.split(":")
    if len(parts) < 4:
        await callback.answer("❌ Xato")
        return

    chat_id = int(parts[1])
    message_id = int(parts[2])
    emoji = parts[3]

    user = callback.from_user
    user_name = user.full_name or user.first_name or "User"

    added = await _toggle_reaction(chat_id, message_id, user.id, user_name, emoji)

    if added:
        await callback.answer(f"{emoji} Qo'shildi!")
    else:
        await callback.answer(f"{emoji} Olib tashlandi!")

    # Update button counts
    counts = await _get_counts(chat_id, message_id)
    kb = _reaction_kb(chat_id, message_id, counts)

    try:
        await callback.message.edit_reply_markup(reply_markup=kb)
    except Exception:
        pass


# ══════════════════════════════════════════════════════════════════════════════
# 📊 STATS BUTTON — show who reacted (admin only, sends private message)
# ══════════════════════════════════════════════════════════════════════════════

@router.callback_query(F.data.startswith("rstats:"))
async def show_reaction_stats(callback: CallbackQuery):
    """Show who reacted when 📊 button is clicked (admin only)."""
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("⚠️ Faqat admin ko'ra oladi!", show_alert=True)
        return

    parts = callback.data.split(":")
    if len(parts) < 3:
        await callback.answer("❌ Xato")
        return

    chat_id = int(parts[1])
    message_id = int(parts[2])

    # Get all reactions for this message
    async with async_session() as session:
        result = await session.execute(
            select(PostReaction)
            .where(and_(
                PostReaction.chat_id == chat_id,
                PostReaction.message_id == message_id
            ))
            .order_by(PostReaction.emoji, PostReaction.created_at)
        )
        reactions = result.scalars().all()

    if not reactions:
        await callback.answer("📭 Hech kim reaktsiya qo'ymagan!", show_alert=True)
        return

    # Build summary for popup (max 200 chars for callback answer)
    grouped: dict[str, list] = {}
    for r in reactions:
        grouped.setdefault(r.emoji, []).append(r.user_name or "User")

    lines = []
    for emoji, names in grouped.items():
        names_str = ", ".join(names[:5])
        if len(names) > 5:
            names_str += f" +{len(names)-5}"
        lines.append(f"{emoji}: {names_str}")

    text = "\n".join(lines)
    text += f"\n\nJami: {len(reactions)} ta"

    # Show as alert popup (up to 200 chars)
    if len(text) <= 200:
        await callback.answer(text, show_alert=True)
    else:
        # Too long for popup — send as private message to admin
        try:
            await callback.bot.send_message(
                callback.from_user.id,
                f"📊 <b>Reaktsiyalar</b> (post #{message_id})\n\n" + text,
                parse_mode="HTML"
            )
            await callback.answer("📊 Ma'lumot shaxsiy chatga yuborildi!")
        except Exception:
            await callback.answer(text[:200], show_alert=True)


# ══════════════════════════════════════════════════════════════════════════════
# ADMIN: SEE WHO REACTED — /reactions command (reply to a forwarded post)
# ══════════════════════════════════════════════════════════════════════════════

@router.message(Command("reactions"))
async def show_reactions(message: Message):
    """Admin command: show who reacted to a channel post.
    Usage: /reactions <chat_id> <message_id>
    Or reply to a message with /reactions
    """
    if message.from_user.id not in ADMIN_IDS:
        return

    args = message.text.split()

    if len(args) >= 3:
        try:
            chat_id = int(args[1])
            msg_id = int(args[2])
        except ValueError:
            await message.answer("❌ Format: /reactions CHAT_ID MESSAGE_ID")
            return
    else:
        await message.answer(
            "📊 <b>Reaktsiyalarni ko'rish</b>\n\n"
            "Format: <code>/reactions CHAT_ID MESSAGE_ID</code>\n\n"
            "Chat ID va Message ID ni inline tugma callback_data dan olishingiz mumkin.",
            parse_mode="HTML"
        )
        return

    # Get all reactions for this message
    async with async_session() as session:
        result = await session.execute(
            select(PostReaction)
            .where(and_(
                PostReaction.chat_id == chat_id,
                PostReaction.message_id == msg_id
            ))
            .order_by(PostReaction.emoji, PostReaction.created_at)
        )
        reactions = result.scalars().all()

    if not reactions:
        await message.answer("📭 Bu postga hech kim reaktsiya qo'ymagan.")
        return

    # Group by emoji
    grouped: dict[str, list] = {}
    for r in reactions:
        grouped.setdefault(r.emoji, []).append(r)

    text = f"📊 <b>Reaktsiyalar</b> (post #{msg_id})\n\n"
    total = 0
    for emoji, items in grouped.items():
        text += f"{emoji} <b>({len(items)}):</b>\n"
        for r in items:
            text += f"  • {r.user_name} (ID: {r.user_id})\n"
        text += "\n"
        total += len(items)

    text += f"👥 <b>Jami:</b> {total} ta reaktsiya"
    await message.answer(text, parse_mode="HTML")
