from __future__ import annotations
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
import os

def referat_quality_kb() -> InlineKeyboardMarkup:
    """Select between Standart and Pro version."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✨ Standart (Oddiy)", callback_data="ref_quality:standard")],
        [InlineKeyboardButton(text="💎 Pro (2x Sifat & Hajm)", callback_data="ref_quality:pro")],
        [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="main_menu")]
    ])

def page_count_kb(is_pro: bool = False) -> InlineKeyboardMarkup:
    """Keyboard to select pages with dynamic prices based on Pro status (3x for Pro)."""
    mult = 3 if is_pro else 1
    p1, p2, p3, p4 = 3000*mult, 4000*mult, 5000*mult, 6000*mult
    
    prefix = "💎 Pro | " if is_pro else ""
    
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"{prefix}10-15 bet - {p1} so'm", callback_data=f"pages:15:{p1}")],
        [InlineKeyboardButton(text=f"{prefix}15-20 bet - {p2} so'm", callback_data=f"pages:20:{p2}")],
        [InlineKeyboardButton(text=f"{prefix}20-25 bet - {p3} so'm", callback_data=f"pages:25:{p3}")],
        [InlineKeyboardButton(text=f"{prefix}25-30 bet - {p4} so'm", callback_data=f"pages:30:{p4}")],
        [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="main_menu")]
    ])

def _build_settings_url(balance: int, name: str, topic: str = "", doc_type: str = "", quality: str = "", lang: str = "uz") -> str:
    webapp_url = os.getenv("WEBAPP_URL", "https://arslon.github.io/student_bot/webapp/")
    base_url = webapp_url.split("?")[0]
    if not base_url.endswith("/"): base_url += "/"
    import urllib.parse
    import time
    v = int(time.time())
    topic_enc = urllib.parse.quote(topic[:60]) if topic else ""
    name_enc = urllib.parse.quote(name) if name else ""
    return f"{base_url}settings_new.html?balance={balance}&name={name_enc}&doc_type={doc_type}&quality={quality}&topic={topic_enc}&lang={lang}&v={v}"

def doc_initial_settings_kb(balance: int, name: str, doc_type: str = "referat", lang: str = "uz") -> ReplyKeyboardMarkup:
    """Initial keyboard with only Settings webapp + Cancel. Shown right after confirm."""
    settings_url = _build_settings_url(balance, name, doc_type=doc_type, lang=lang)
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="⚙️ Sozlamalarni to'ldiring", web_app=WebAppInfo(url=settings_url))],
            [KeyboardButton(text="❌ Bekor qilish")]
        ],
        resize_keyboard=True,
        one_time_keyboard=False
    )

def referat_summary_kb(balance: int, price: int, name: str, topic: str = "", doc_type: str = "", quality: str = "", lang: str = "uz", is_admin: bool = False) -> ReplyKeyboardMarkup:
    """Reply keyboard for referat summary screen with Mini Apps."""
    settings_url = _build_settings_url(balance, name, topic, doc_type, quality, lang=lang)
    webapp_url = os.getenv("WEBAPP_URL", "https://arslon.github.io/student_bot/webapp/")
    base_url = webapp_url.split("?")[0]
    if not base_url.endswith("/"): base_url += "/"
    import time
    v = int(time.time())
    plan_url = f"{base_url}plan.html?v={v}"
    
    keyboard = []
    
    if is_admin or balance >= price:
        keyboard = [
            [KeyboardButton(text="⚙️ Sozlamalarni tahrirlash", web_app=WebAppInfo(url=settings_url))],
            [KeyboardButton(text="📝 Reja qo'shish", web_app=WebAppInfo(url=plan_url))],
            [KeyboardButton(text="🖼 AI Rasm qo'shish")]
        ]
        keyboard.append([KeyboardButton(text="✅ Yaratish"), KeyboardButton(text="❌ Bekor qilish")])
    else:
        keyboard.append([KeyboardButton(text="❌ Bekor qilish")])
        
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        one_time_keyboard=False
    )

def back_to_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏠 Bosh menyu", callback_data="main_menu")]
    ])

def confirm_generation_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚀 Yaratish", callback_data="coursework_start")],
        [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="main_menu")]
    ])



