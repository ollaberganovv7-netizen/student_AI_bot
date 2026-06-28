from __future__ import annotations
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from config import SERVICE_NAMES, PRICING
from utils.i18n import btn


def lang_select_kb() -> InlineKeyboardMarkup:
    """Language selection keyboard."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="\U0001f1fa\U0001f1ff O'zbekcha", callback_data="set_lang:uz")],
        [InlineKeyboardButton(text="\U0001f1f7\U0001f1fa \u0420\u0443\u0441\u0441\u043a\u0438\u0439", callback_data="set_lang:ru")],
        [InlineKeyboardButton(text="\U0001f1ec\U0001f1e7 English", callback_data="set_lang:en")]
    ])


def main_menu_kb(lang: str = "uz") -> ReplyKeyboardMarkup:
    """Main menu with core services (Reply Keyboard)."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=btn("referat", lang)), KeyboardButton(text=btn("mustaqil", lang))],
            [KeyboardButton(text=btn("presentation", lang)), KeyboardButton(text=btn("kurs", lang))],
            [KeyboardButton(text=btn("diplom", lang)), KeyboardButton(text=btn("quiz", lang))],
        ],
        resize_keyboard=True,
        is_persistent=True,
    )


def back_to_menu_kb(lang: str = "uz") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=btn("back", lang), callback_data="main_menu")]
    ])


def confirm_cancel_kb(confirm_data: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="\u2705 Tasdiqlash", callback_data=confirm_data),
            InlineKeyboardButton(text="\u274c Bekor qilish", callback_data="main_menu"),
        ]
    ])


def service_price_kb(service_type: str) -> InlineKeyboardMarkup:
    """Shows price and proceed/cancel buttons for document services."""
    price = PRICING.get(service_type, 0)
    label = SERVICE_NAMES.get(service_type, service_type)
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=f"\u2705 Davom etish \u2014 {price:,} so'm",
            callback_data=f"proceed:{service_type}"
        )],
        [InlineKeyboardButton(text="\U0001f3e0 Bosh menyu", callback_data="main_menu")],
    ])
