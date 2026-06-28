from __future__ import annotations
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def admin_main_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 Kutayotgan to'lovlar", callback_data="admin:pending_payments")],
        [InlineKeyboardButton(text="➕ Balans qo'shish",       callback_data="admin:add_balance")],
        [InlineKeyboardButton(text="� Foydalanuvchi qidirish", callback_data="admin:search_user")],
        [InlineKeyboardButton(text="�📊 Statistika",           callback_data="admin:stats")],
        [InlineKeyboardButton(text="📢 Xabar yuborish",       callback_data="admin:broadcast")],
        [InlineKeyboardButton(text="💰 Narxlarni ko'rish",    callback_data="admin:pricing")],
        [InlineKeyboardButton(text="📋 So'nggi so'rovlar",    callback_data="admin:recent_requests")],
        [InlineKeyboardButton(text="🔬 Lab generator",       callback_data="admin:lab_gen")],
        [InlineKeyboardButton(text="🔥 Reaktsiyalar",       callback_data="admin:reactions")],
        [InlineKeyboardButton(text="🖼 AI Rasm (faylga)",   callback_data="admin:ai_rasm")],
    ])


def lab_variant_kb() -> InlineKeyboardMarkup:
    """Keyboard to select variant number (1-30) in a grid."""
    rows = []
    for start in range(1, 31, 5):
        row = [
            InlineKeyboardButton(
                text=str(v),
                callback_data=f"admin:lab_v:{v}"
            )
            for v in range(start, min(start + 5, 31))
        ]
        rows.append(row)
    rows.append([InlineKeyboardButton(text="⬅️ Admin panel", callback_data="admin:back")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def payment_action_kb(payment_id: int, user_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="✅ Tasdiqlash",
                callback_data=f"admin:approve:{payment_id}:{user_id}"
            ),
            InlineKeyboardButton(
                text="❌ Rad etish",
                callback_data=f"admin:reject:{payment_id}:{user_id}"
            ),
        ],
        [InlineKeyboardButton(text="⬅️ Admin panel", callback_data="admin:back")],
    ])


def admin_back_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Admin panel", callback_data="admin:back")]
    ])
