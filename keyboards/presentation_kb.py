from keyboards.documents_kb import _build_settings_url
from __future__ import annotations
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import PRES_LANGUAGES, SLIDE_OPTIONS, PRES_STYLES, PRICING
from utils.i18n import btn


def language_kb() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text=label, callback_data=f"pres_lang:{code}")]
        for code, label in PRES_LANGUAGES.items()
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

from aiogram.types.web_app_info import WebAppInfo
import os

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def design_selection_kb(lang: str = "uz") -> ReplyKeyboardMarkup:
    # Use environment variable or fallback
    webapp_url = os.getenv("WEBAPP_URL", "https://arslon.github.io/student_bot/webapp/catalog.html")
    
    # Ensure it ends with catalog.html
    if "index.html" in webapp_url:
        webapp_url = webapp_url.replace("index.html", "catalog.html")
    elif "catalog.html" not in webapp_url:
        if not webapp_url.endswith("/"):
            webapp_url += "/"
        webapp_url += "catalog.html"
    
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=btn("pres_design_catalog", lang), web_app=WebAppInfo(url=webapp_url))],
            [KeyboardButton(text=btn("pres_plain_design", lang))],
            [KeyboardButton(text=btn("back", lang))]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )


def quality_kb() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="✨ Standart", callback_data="pres_quality:standard")],
        [InlineKeyboardButton(text="💎 Premium", callback_data="pres_quality:premium")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def chapters_kb() -> InlineKeyboardMarkup:
    """Keyboard for selecting number of chapters (3-6) or manual entry."""
    buttons = [
        [
            InlineKeyboardButton(text="3", callback_data="pres_chapters:3"),
            InlineKeyboardButton(text="4", callback_data="pres_chapters:4"),
            InlineKeyboardButton(text="5", callback_data="pres_chapters:5"),
            InlineKeyboardButton(text="6", callback_data="pres_chapters:6"),
        ],
        [InlineKeyboardButton(text="✍️ Rejani o'zim yozaman (Manual)", callback_data="pres_chapters:manual")],
        [InlineKeyboardButton(text="❌ To'xtatish", callback_data="back_to_menu")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def slides_grid_kb() -> InlineKeyboardMarkup:
    """Keyboard for selecting slide count in a grid (10-30)."""
    keyboard = []
    # 5 buttons per row, starting from 10
    for row in range(10, 31, 5):
        buttons = []
        for i in range(row, min(row + 5, 31)):
            buttons.append(InlineKeyboardButton(text=str(i), callback_data=f"pres_slides:{i}"))
        keyboard.append(buttons)
    
    keyboard.append([InlineKeyboardButton(text="❌ To'xtatish", callback_data="back_to_menu")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def style_kb() -> InlineKeyboardMarkup:
    # We use the webapp for design selection, but this is a fallback
    buttons = [
        [InlineKeyboardButton(text=info["label"], callback_data=f"pres_style:{key}")]
        for key, info in PRES_STYLES.items()
    ]
    buttons.append([InlineKeyboardButton(text="🏠 Bosh menyu", callback_data="main_menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def summary_kb(balance: int, price: int, name: str, quality: str = "standard", topic: str = "", lang: str = "uz", is_admin: bool = False) -> ReplyKeyboardMarkup:
    """Reply keyboard for summary screen with Mini Apps."""
    settings_url = _build_settings_url(balance, name, topic=topic, quality=quality, lang=lang)
    webapp_url = os.getenv("WEBAPP_URL", "https://arslon.github.io/student_bot/webapp/")
    base_url = webapp_url.split("?")[0]
    if not base_url.endswith("/"): base_url += "/"
    import time
    v = int(time.time())
    catalog_url = f"{base_url}catalog.html?v={v}"
    plan_url = f"{base_url}plan.html?v={v}"
    
    keyboard = []
    
    if is_admin or balance >= price:
        keyboard = [
            [KeyboardButton(text=btn("pres_settings", lang), web_app=WebAppInfo(url=settings_url))],
            [KeyboardButton(text=btn("pres_design", lang), web_app=WebAppInfo(url=catalog_url))],
            [KeyboardButton(text=btn("pres_plan", lang), web_app=WebAppInfo(url=plan_url))],
            [KeyboardButton(text=btn("pres_photo", lang))]
        ]
        keyboard.append([KeyboardButton(text=btn("pres_create", lang)), KeyboardButton(text=btn("cancel", lang))])
    else:
        keyboard.append([KeyboardButton(text="💳 Hisobni to'ldirish")])
        keyboard.append([KeyboardButton(text=btn("cancel", lang))])
        
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        one_time_keyboard=False
    )


def back_to_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏠 Bosh menyu", callback_data="main_menu")]
    ])


