from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from config import SERVICE_NAMES, PRICING
from utils.i18n import btn


def lang_select_kb() -> InlineKeyboardMarkup:
    """Language selection keyboard."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🇺🇿 O'zbekcha", callback_data="set_lang:uz")],
        [InlineKeyboardButton(text="🇷🇺 Русский", callback_data="set_lang:ru")],
        [InlineKeyboardButton(text="🇬🇧 English", callback_data="set_lang:en")]
    ])


def main_menu_kb(lang: str = "uz") -> ReplyKeyboardMarkup:
    """Main menu with core services (Reply Keyboard)."""
    return ReplyKeyboardMarkup(
        keyboard=[
            # 1-qator: Tezis (Chapda) | Maqola (O'ngda)
            [KeyboardButton(text=btn("t_conf", lang)), KeyboardButton(text=btn("a_sci", lang))],
            # 2-qator
            [KeyboardButton(text=btn("t_art", lang)), KeyboardButton(text=btn("a_pop_sci", lang))],
            # 3-qator
            [KeyboardButton(text=btn("t_diss", lang)), KeyboardButton(text=btn("a_pop", lang))],
            # 4-qator
            [KeyboardButton(text=btn("t_pop", lang)), KeyboardButton(text=btn("a_art", lang))],
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
