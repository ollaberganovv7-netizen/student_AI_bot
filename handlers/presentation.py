from __future__ import annotations
import asyncio
import io
import logging
from aiogram import Router, F, Bot
from aiogram.types import (
    CallbackQuery, Message, BufferedInputFile,
    ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove,
    InlineKeyboardMarkup, InlineKeyboardButton
)
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

logger = logging.getLogger(__name__)

from database.models import User
from database.db import mark_free_used, create_request, deduct_balance
from keyboards.presentation_kb import (
    language_kb, style_kb, back_to_menu_kb, quality_kb, 
    chapters_kb, slides_grid_kb, design_selection_kb, summary_kb
)
from keyboards.main_kb import main_menu_kb
from services.ai_service import generate_presentation_content, generate_akademik_content, generate_test_presentation_content, client, OPENAI_MODEL
from services.pptx_service import generate_pptx, analyze_template
from services.akademik_pptx_service import generate_akademik_pptx
from services.test_pptx_service import generate_test_pptx
from services.template_filler_service import analyze_template_deep, fill_template
from services.ai_service import generate_content_for_template
from utils.helpers import format_price, is_free_trial, safe_topic, get_template_path
from utils.generation_manager import run_with_queue
from utils.i18n import t, btn
from config import PRICING, PRES_LANGUAGES, PRES_STYLES, ADMIN_IDS
import json

def _lang(db_user) -> str:
    return (db_user.language or "uz") if db_user else "uz"

router = Router()

class PresentationStates(StatesGroup):
    choosing_language    = State()
    entering_topic       = State()
    reviewing_summary    = State()
    waiting_for_receipt  = State()
    entering_manual_plan = State()   # old (unused now)
    choosing_plan_count  = State()   # new: how many chapters?
    entering_plan_step   = State()   # new: enter each chapter title one by one
    choosing_style       = State()
    waiting_for_photos   = State()   # user uploading their own images

# ─── Step 1: Quality selection ───────────────────────────────────────────────

@router.message(F.text.in_([
    "🎓 Taqdimot (Slayd) yaratish", "🎓 Slayd Pro (Premium)",
    "🎓 Создать презентацию (Слайды)", "🎓 Слайд Pro (Премиум)",
    "🎓 Create Presentation", "🎓 Slide Pro (Premium)",
    "🆕 Taqdimot (Slayd) yaratish", "🚀 Slayd Pro (Premium)",
    "🆕 Создать презентацию (Слайды)", "🚀 Слайд Про (Премиум)",
    "🆕 Create Presentation", "🚀 Slide Pro (Premium)",
]))
async def start_presentation(message: Message, db_user: User, state: FSMContext):
    is_admin = db_user.id in ADMIN_IDS
    balance = db_user.balance or 0
    lang = _lang(db_user)

    price_low = PRICING["presentation_std_low"]
    price_high = PRICING["presentation_pre_high"]

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("pres_continue", lang), callback_data="pres_confirm:standard")],
        [InlineKeyboardButton(text=t("pres_cancel_btn", lang), callback_data="pres_cancel")]
    ])
    
    await message.answer(
        f"📊 <b>Taqdimot (Slayd) yaratish</b>\n"
        f"➖➖➖➖➖➖➖➖➖➖➖➖➖➖➖➖\n"
        f"💰 <b>Narx:</b> {format_price(price_low)} — {format_price(price_high)}\n"
        f"   <i>(Slaydlar soni, tili va dizayniga qarab)</i>\n"
        f"➖➖➖➖➖➖➖➖➖➖➖➖➖➖➖➖",
        reply_markup=kb,
        parse_mode="HTML"
    )

@router.callback_query(F.data.startswith("pres_confirm:"))
async def confirm_presentation(callback: CallbackQuery, state: FSMContext, db_user: User):
    await state.update_data(
        quality="standard",
        author=db_user.full_name or "Foydalanuvchi",
        language="uz",
        num_slides=10
    )
    await state.set_state(PresentationStates.reviewing_summary)
    await callback.message.delete()
    await callback.message.answer(
        "⚙️ <b>Kerakli sozlamalaringizni tanlang:</b>\n\n"
        "<i>Mavzu, sifat, dizayn, reja va boshqa ma'lumotlarni kiriting.</i>",
        reply_markup=summary_kb(db_user.balance or 0, 0, db_user.full_name or "", "standard", lang=_lang(db_user), is_admin=(db_user.id in ADMIN_IDS)),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data == "pres_cancel")
async def cancel_presentation_inline(callback: CallbackQuery, state: FSMContext):
    # Set cancelled flag so running generation can detect it
    await state.update_data(cancelled=True)
    await state.clear()
    await callback.message.edit_text(t("cancelled", "uz"))
    await callback.answer()

@router.callback_query(F.data == "pres_cancel_generating")
async def cancel_generating(callback: CallbackQuery, state: FSMContext):
    """Cancel during active generation — sets the shared cancel flag."""
    data = await state.get_data()
    cancel_flag = data.get("cancel_flag")
    if cancel_flag and isinstance(cancel_flag, dict):
        cancel_flag["cancelled"] = True
    await state.clear()
    await callback.message.edit_text(t("pres_cancel_gen", "uz"))
    await callback.answer()

@router.callback_query(F.data == "topup_menu")
async def topup_from_presentation(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    from keyboards.main_kb import main_menu_kb
    await callback.message.edit_text(
        t("pres_topup_hint", "uz"),
        parse_mode="HTML"
    )
    await callback.answer()
    await callback.message.answer(
        t("pres_topup_hint", "uz"),
        reply_markup=main_menu_kb()
    )


# ─── Step 2: Language selected ───────────────────────────────────────────────

@router.callback_query(F.data.startswith("pres_lang:"), PresentationStates.choosing_language)
async def choose_language(callback: CallbackQuery, state: FSMContext):
    lang_code = callback.data.split(":")[1]
    await state.update_data(language=lang_code)
    await state.set_state(PresentationStates.entering_topic)
    await callback.message.edit_text(
        t("pres_enter_topic", lang_code),
        reply_markup=back_to_menu_kb(),
        parse_mode="HTML"
    )
    await callback.answer()

# ─── Step 2: Topic entered ────────────────────────────────────────────────────

@router.message(PresentationStates.entering_topic)
async def enter_topic(message: Message, state: FSMContext, db_user: User):
    topic = safe_topic(message.text or "")
    lang = _lang(db_user)
    if not topic:
        await message.answer(t("pres_topic_empty", lang))
        return
    
    # Set default settings
    await state.update_data(
        topic=topic,
        language="uz",
        num_slides=10,
        quality="standard",
        num_chapters=4,
        author=db_user.full_name or "Foydalanuvchi"
    )
    
    await state.set_state(PresentationStates.reviewing_summary)
    await show_summary(message, state, db_user)

async def show_summary(message: Message, state: FSMContext, db_user: User):
    data = await state.get_data()
    topic = data.get("topic")
    lang = data.get("language", "uz")
    slides = data.get("num_slides", 10)
    quality = data.get("quality", "standard")
    author = data.get("author", "Foydalanuvchi")
    
    lang_label = {"uz": "O'zbekcha 🇺🇿", "ru": "Русский 🇷🇺", "en": "English 🇺🇸"}.get(lang, lang)
    quality_label = "💎 Premium" if quality == "premium" else "✨ Standart"
    
    text = (
        f"📊 <b>Taqdimot Haqida | {quality_label}</b>\n\n"
        f"🗺️ <b>Taqdimot tili:</b> {lang_label}\n"
        f"👤 <b>Taqdimot Muallifi:</b> {author}\n"
        f"🎞️ <b>Listlari Soni:</b> {slides} ta\n"
        f"📂 <b>Mundarija bo'limlari:</b> {data.get('num_chapters', 4)} ta\n"
        f"💎 <b>Yaratish usuli:</b> Mavzu asosida\n\n"
        f"<i>Ushbu sozlamalar asosida slaydingiz yaratiladi. \"Sozlamalar\" tugmasi orqali ularni o'zgartirishingiz mumkin.</i>"
    )
    
    await message.answer(
        text,
        reply_markup=summary_kb(db_user.balance or 0, 0, db_user.full_name or "", quality, lang=_lang(db_user), is_admin=(db_user.id in ADMIN_IDS)),
        parse_mode="HTML"
    )

@router.message(F.web_app_data, PresentationStates.reviewing_summary)
async def handle_webapp_data_summary(message: Message, state: FSMContext, db_user: User):
    try:
        # Delete the service "You sent data" message to keep chat clean
        try:
            await message.delete()
        except TelegramBadRequest:
            pass

        data = json.loads(message.web_app_data.data)
        if "template_id" in data:
            # Design selected
            await state.update_data(style=data["template_id"], style_name=data["template_name"])
        elif data.get("action") == "plan_update":
            mode = data.get("mode")
            if mode == "auto":
                num = int(data.get("num_chapters"))
                await state.update_data(num_chapters=num, manual_plan=None)
                await show_summary(message, state, db_user, edit=True)
            else:
                # Manual mode: plan text already built in webapp
                plan = data.get("manual_plan", "")
                num = int(data.get("num_chapters", len(plan.split('\n'))))
                await state.update_data(manual_plan=plan, num_chapters=num)
                await show_summary(message, state, db_user, edit=True)
            return
        elif data.get("action") == "content_update":
            await state.update_data(
                extra_info=data.get("extra_info"),
                tone=data.get("tone"),
                add_images=data.get("add_images")
            )
        elif data.get("type") == "settings" or data.get("action") == "full_settings":
            # Full settings from webapp (initial or edit)
            quality = data.get("quality", "standard")
            if quality == "pro": quality = "premium"
            slides = int(data.get("num_pages", data.get("slides", 10)))
            ai_images = int(data.get("ai_images", 3))
            ai_images_extra = int(data.get("ai_images_extra", 0))
            await state.update_data(
                topic=data.get("topic", "").strip(),
                author=data.get("author", db_user.full_name or "Foydalanuvchi"),
                reviewer=data.get("reviewer", ""),
                manual_plan=data.get("plan", ""),
                language=data.get("language", "uz"),
                subject=data.get("subject", ""),
                university=data.get("university", ""),
                num_slides=slides,
                quality=quality,
                num_chapters=min(max(slides // 3, 3), 6),
                ai_images_count=ai_images,
                ai_images_extra=ai_images_extra,
            )
        else:
            # Legacy settings update
            slides = int(data.get("slides", 10))
            update_dict = dict(
                author=data.get("author"),
                language=data.get("language"),
                num_slides=slides,
                quality="premium" if data.get("premium") else "standard",
                ai_images=bool(data.get("ai_images", False))
            )
            if data.get("topic"):
                update_dict["topic"] = data["topic"].strip()
            await state.update_data(**update_dict)
        
        await show_summary(message, state, db_user, edit=True)
    except json.JSONDecodeError as e:
        logger.error(f"WebApp JSON decode error: {e}")
        await message.answer("⚠️ Ma'lumotlarni o'qishda xatolik. Qaytadan urinib ko'ring.")
    except Exception as e:
        logger.error(f"WebApp data error: {e}")
        await message.answer("⚠️ Kutilmagan xatolik yuz berdi.")

async def show_summary(message: Message, state: FSMContext, db_user: User, edit: bool = False):
    data = await state.get_data()
    topic = data.get("topic")
    lang = data.get("language", "uz")
    slides = data.get("num_slides", 10)
    quality = data.get("quality", "standard")
    author = data.get("author", "Foydalanuvchi")
    style_name = data.get("style_name", "Standart (Oq fon)")
    ai_images_count = data.get("ai_images_count", 3)
    ai_images_extra = data.get("ai_images_extra", 0)
    
    ulang = (db_user.language or "uz") if db_user else "uz"
    lang_label = {"uz": "O'zbekcha 🇺🇿", "ru": "Русский 🇷🇺", "en": "English 🇺🇸"}.get(lang, lang)
    quality_label = "💎 Premium" if quality == "premium" else "✨ Standart"
    
    user_photos  = data.get("user_photos", [])   # list of file_ids
    user_photos_label = t("photos_label", ulang, count=len(user_photos)) if user_photos else t("none_label", ulang)
    if ai_images_extra > 0:
        ai_img_label = f"🎨 {ai_images_count} ta (3 bepul + {ai_images_extra} × 1 000 so'm)"
    elif ai_images_count > 0:
        ai_img_label = f"🎨 {ai_images_count} ta (bepul)"
    else:
        ai_img_label = t("none_label", ulang)
    
    text = t("pres_summary", ulang,
        quality=quality_label, topic=topic, pres_lang=lang_label,
        author=author, slides=slides, style=style_name,
        chapters=data.get('num_chapters', 'AI'),
        ai_img=ai_img_label, user_photos=user_photos_label
    )
    quality = data.get("quality", "standard")
    
    # Calculate price for presentation summary
    num_slides = data.get("num_slides", 10)
    ai_images_extra = int(data.get("ai_images_extra", 0))
    from config import PRICING
    if quality == "premium":
        if num_slides <= 14: price = PRICING["presentation_pre_low"]
        elif num_slides <= 22: price = PRICING["presentation_pre_mid"]
        else: price = PRICING["presentation_pre_high"]
    else:
        if num_slides <= 14: price = PRICING["presentation_std_low"]
        elif num_slides <= 22: price = PRICING["presentation_std_mid"]
        else: price = PRICING["presentation_std_high"]
    price += ai_images_extra * 1000

    kb = summary_kb(db_user.balance or 0, price, db_user.full_name or "", quality, topic=topic or "", lang=ulang, is_admin=(db_user.id in ADMIN_IDS))

    
    summary_id = data.get("summary_msg_id")
    if summary_id:
        try:
            await message.bot.delete_message(chat_id=message.chat.id, message_id=summary_id)
        except TelegramBadRequest:
            pass

    msg = await message.answer(text, reply_markup=kb, parse_mode="HTML")
    await state.update_data(summary_msg_id=msg.message_id)

# ─── Step-by-step manual plan input ─────────────────────────────────────────

@router.message(F.text.in_({"❌ Bekor qilish", "❌ Отменить", "❌ Cancel"}), PresentationStates.entering_plan_step)
async def cancel_plan_step(message: Message, state: FSMContext, db_user: User):
    await state.set_state(PresentationStates.reviewing_summary)
    lang = _lang(db_user)
    await message.answer(t("pres_plan_cancelled", lang), reply_markup=ReplyKeyboardRemove())
    await show_summary(message, state, db_user)

@router.message(F.text, PresentationStates.entering_plan_step)
async def receive_plan_step(message: Message, state: FSMContext, db_user: User):
    text = (message.text or "").strip()
    data = await state.get_data()
    chapters = data.get("manual_plan_chapters", [])
    total = data.get("manual_plan_total", 4)

    chapters.append(text)
    await state.update_data(manual_plan_chapters=chapters)

    current = len(chapters)

    if current < total:
        # Ask for next chapter
        lang = _lang(db_user)
        await message.answer(
            t("pres_plan_saved", lang, n=current, title=text, next=current+1, total=total),
            parse_mode="HTML"
        )
    else:
        # All chapters entered — build the plan
        plan_text = "\n".join(chapters)
        await state.update_data(
            manual_plan=plan_text,
            num_chapters=total,
            manual_plan_chapters=[]
        )
        await state.set_state(PresentationStates.reviewing_summary)
        lang = _lang(db_user)
        await message.answer(
            t("pres_plan_done", lang) + "\n\n"
            + "\n".join([f"{i+1}. {c}" for i, c in enumerate(chapters)]),
            parse_mode="HTML",
            reply_markup=ReplyKeyboardRemove()
        )
        await show_summary(message, state, db_user)

# ─── AI Image count selection ─────────────────────────────────────────────────

@router.message(F.text.in_({"🖼 AI Rasm", "🖼 AI РР·РѕР±СЂР°Р¶РµРЅРёСЏ", "🖼 AI Images"}), PresentationStates.reviewing_summary)
async def ask_ai_image_count(message: Message, state: FSMContext):
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    data = await state.get_data()
    current = data.get("ai_images_count", 0)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="0 (Yo'q)", callback_data="ai_img:0"),
            InlineKeyboardButton(text="1 ta", callback_data="ai_img:1"),
            InlineKeyboardButton(text="2 ta", callback_data="ai_img:2"),
        ],
        [
            InlineKeyboardButton(text="3 ta", callback_data="ai_img:3"),
            InlineKeyboardButton(text="4 ta", callback_data="ai_img:4"),
            InlineKeyboardButton(text="5 ta", callback_data="ai_img:5"),
        ],
    ])
    await message.answer(
        t("pres_ai_img_select", "uz", current=current),
        reply_markup=kb,
        parse_mode="HTML"
    )

@router.callback_query(F.data.startswith("ai_img:"), PresentationStates.reviewing_summary)
async def set_ai_image_count(callback: CallbackQuery, state: FSMContext, db_user: User):
    count = int(callback.data.split(":")[1])
    await state.update_data(ai_images_count=count)
    label = f"{count} ta (+{count * 1000} so'm)" if count > 0 else "Yo'q"
    await callback.message.edit_text(f"✅ AI rasmlar: <b>{label}</b>", parse_mode="HTML")
    await callback.answer()
    await show_summary(callback.message, state, db_user)

# ─── Photo upload flow ────────────────────────────────────────────────────────

@router.message(F.text.in_({"📷 Rasm yuklash", "📷 Загрузить фото", "📷 Upload Photo"}), PresentationStates.reviewing_summary)
async def ask_for_photos(message: Message, state: FSMContext):
    await state.set_state(PresentationStates.waiting_for_photos)
    data = await state.get_data()
    existing = data.get("user_photos", [])
    await message.answer(
        t("pres_photo_upload", "uz", count=len(existing)),
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="✅ Tayyor")], [KeyboardButton(text="🗑 Rasmlarni o'chirish")]],
            resize_keyboard=True
        ),
        parse_mode="HTML"
    )

@router.message(F.photo, PresentationStates.waiting_for_photos)
async def receive_photo(message: Message, state: FSMContext):
    data = await state.get_data()
    photos = data.get("user_photos", [])
    # Get the best quality photo (last in array)
    file_id = message.photo[-1].file_id
    photos.append(file_id)
    await state.update_data(user_photos=photos)
    await message.answer(t("pres_photo_received", "uz", count=len(photos)), parse_mode="HTML")

@router.message(F.text == "🗑 Rasmlarni o'chirish", PresentationStates.waiting_for_photos)
async def clear_photos(message: Message, state: FSMContext):
    await state.update_data(user_photos=[])
    await message.answer(t("pres_photos_cleared", "uz"))

@router.message(F.text == "✅ Tayyor", PresentationStates.waiting_for_photos)
async def done_photos(message: Message, state: FSMContext, db_user: User):
    await state.set_state(PresentationStates.reviewing_summary)
    data = await state.get_data()
    count = len(data.get("user_photos", []))
    await message.answer(
        t("pres_photos_saved", "uz", count=count),
        reply_markup=ReplyKeyboardRemove()
    )
    await show_summary(message, state, db_user)

@router.message(F.text, PresentationStates.waiting_for_photos)
async def fallback_text_photos(message: Message):
    await message.answer(t("pres_photo_hint", "uz"), parse_mode="HTML")

@router.message(F.text.contains("Yaratish"), PresentationStates.reviewing_summary)
async def start_generation_text(message: Message, state: FSMContext, db_user: User):
    data = await state.get_data()
    style = data.get("style", "classic")
    await finalize_presentation_logic(message, state, db_user, style)

@router.message(F.text.in_({"❌ Bekor qilish", "❌ Отменить", "❌ Cancel"}), PresentationStates.reviewing_summary)
async def cancel_generation(message: Message, state: FSMContext, db_user: User):
    await state.clear()
    lang = _lang(db_user)
    await message.answer(t("cancelled", lang), reply_markup=main_menu_kb(lang))

@router.message(F.text, PresentationStates.reviewing_summary)
async def fallback_text_summary(message: Message, db_user: User, state: FSMContext):
    # Let /stop, /start, /help etc. pass through to start.py handlers
    if message.text and message.text.startswith("/"):
        await state.clear()
        lang = _lang(db_user)
        await message.answer(t("cancelled", lang), reply_markup=main_menu_kb(lang))
        return
    lang = _lang(db_user)
    await message.answer(t("pres_use_buttons", lang), parse_mode="HTML")

@router.callback_query(F.data == "pres_start_generation", PresentationStates.reviewing_summary)
async def start_generation_callback(callback: CallbackQuery, state: FSMContext, db_user: User):
    data = await state.get_data()
    style = data.get("style", "classic")
    await finalize_presentation_logic(callback.message, state, db_user, style)
    await callback.answer()

async def finalize_presentation_logic(message: Message, state: FSMContext, db_user: User, style: str):
    data = await state.get_data()
    topic = data.get("topic")
    num_slides = data.get("num_slides") or 10
    num_slides = int(num_slides)  # ensure int
    quality = data.get("quality", "standard")
    language = data.get("language", "uz")
    manual_plan = data.get("manual_plan")
    num_chapters = data.get("num_chapters", 4)
    subject = data.get("subject", "")
    university = data.get("university", "")
    logger.debug(f"num_slides={num_slides}, num_chapters={num_chapters}, quality={quality}")

    # Calculate price based on slide count
    ai_images_count = int(data.get("ai_images_count", 3))
    ai_images_extra = int(data.get("ai_images_extra", 0))
    if quality == "premium":
        if num_slides <= 14: price = PRICING["presentation_pre_low"]
        elif num_slides <= 22: price = PRICING["presentation_pre_mid"]
        else: price = PRICING["presentation_pre_high"]
    else:
        if num_slides <= 14: price = PRICING["presentation_std_low"]
        elif num_slides <= 22: price = PRICING["presentation_std_mid"]
        else: price = PRICING["presentation_std_high"]
    
    # Dynamic image pricing: only EXTRA images cost 1000 so'm each (3 are free)
    price += ai_images_extra * 1000

    # Admin / free trial check
    is_admin = db_user.id in ADMIN_IDS
    free_trial = is_free_trial(db_user) and not is_admin

    lang = _lang(db_user)
    if free_trial:
        # First generation is free (only AI images extra cost applies)
        price = ai_images_extra * 1000
    if not is_admin and not free_trial and (db_user.balance or 0) < price:
        await message.answer(
            t("pres_not_enough", lang, price=format_price(price), balance=format_price(db_user.balance or 0)),
            reply_markup=main_menu_kb(),
            parse_mode="HTML"
        )
        return

    if free_trial:
        price_note = "🎁 Birinchi marta BEPUL!"
    elif is_admin:
        price_note = t("pres_admin_free", lang)
    else:
        price_note = format_price(price)
    ai_img_line = f"\n🎨 <b>AI rasmlar:</b> {ai_images_count} ta" if ai_images_count > 0 else ""

    # Use a dict to track cancellation (mutable, shared across async tasks)
    cancel_flag = {"cancelled": False}
    
    # Store cancel flag reference in state so cancel handler can set it
    await state.update_data(cancel_flag=cancel_flag, generating=True)
    
    cancel_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="pres_cancel_generating")]
    ])
    
    qlabel = "Premium" if quality == "premium" else "Standard"
    wait_msg = await message.answer(
        t("pres_generating", lang,
            topic=topic, slides=num_slides, quality=qlabel,
            ai_img=ai_img_line, author=db_user.full_name or "User", price=price_note
        ),
        parse_mode="HTML",
        reply_markup=cancel_kb
    )

    try:
        # Helper to check if user cancelled
        def is_cancelled():
            return cancel_flag.get("cancelled", False)

        # Pass manual plan to AI instructions via topic or extra details
        full_topic = topic
        forced_titles = None

        if manual_plan:
            # Parse chapter titles from plan ("1. Kirish" → "Kirish")
            raw_lines = [l.strip() for l in manual_plan.strip().split('\n') if l.strip()]
            chapter_titles = []
            for line in raw_lines:
                import re
                clean = re.sub(r'^\d+\.\s*', '', line).strip()
                if clean:
                    chapter_titles.append(clean)
            
            # We need to fill (num_slides - 2) content slides (excluding Reja and Xulosa)
            content_slides_needed = num_slides - 2
            if content_slides_needed < len(chapter_titles):
                # If they asked for fewer slides than chapters, truncate chapters
                chapter_titles = chapter_titles[:content_slides_needed]
            
            expanded_titles = []
            if len(chapter_titles) > 0 and content_slides_needed > 0:
                base_count = content_slides_needed // len(chapter_titles)
                remainder = content_slides_needed % len(chapter_titles)
                
                for i, title in enumerate(chapter_titles):
                    # Distribute remainder to the first few chapters
                    count_for_this = base_count + (1 if i < remainder else 0)
                    if count_for_this == 1:
                        expanded_titles.append(title)
                    else:
                        for part in range(1, count_for_this + 1):
                            expanded_titles.append(f"{title} ({part}-qism)")
            
            forced_titles = expanded_titles
            
        # Resolve template path first to check for maket mode
        template_path = PRES_STYLES.get(style, {}).get("file")
        if not template_path:
            template_path = get_template_path(style)

        # Analyze template so AI can tailor content
        tpl_info = analyze_template(template_path) if template_path else {}
        tpl_context = ""
        is_maket_mode = False

        if template_path and ("maket" in template_path.lower() or "modern" in template_path.lower()):
            is_maket_mode = False  # Always duplicate slides to match user's count
        
        # User picks N → total = N+2 (1 title + (N+1) content slides)
        # AI service subtracts 1 for title, so pass N+2 to get N+1 content slides
        total_slides = num_slides + 2
        ai_slides_count = total_slides

        if tpl_info.get("total_slides", 0) > 1:
            if is_maket_mode and "slides" in tpl_info:
                # Provide detailed slide-by-slide block info for Maket Mode
                limits = []
                for s in tpl_info["slides"][1:]:  # skip title slide (index 0)
                    idx = s["index"]
                    body_blocks = s.get("body_blocks", 1)
                    blocks = s.get("blocks", [])
                    total_words = s.get("estimated_words", 40)
                    
                    if body_blocks >= 2:
                        # Multi-column slide — tell AI to generate separate blocks
                        block_desc = ", ".join([f"{i+1}-blok: {b['words']} so'z" for i, b in enumerate(blocks) if b['type'] == 'body'])
                        limits.append(f"Slayd {idx}: {body_blocks} ta alohida blok (kolonka) → {block_desc}. "
                                      f"Har bir blok uchun ALOHIDA punkt yozing!")
                    else:
                        limits.append(f"Slayd {idx}: maximal {total_words} ta so'z")
                
                limits_str = "\n".join(limits)
                tpl_context = (
                    f"\n\nSHABLON STRUKTURASI:\n"
                    f"Shablon {tpl_info['total_slides']} ta tayyor slayddan iborat.\n"
                    f"MUHIM! Slaydlar turli xil dizaynga ega: ba'zilari 1 ta matn bloki, ba'zilari 2 ta kolonka.\n"
                    f"2 ta blokli (kolonnali) slaydlar uchun — points massivida 2 ta ALOHIDA element qaytaring.\n"
                    f"1 ta blokli slaydlar uchun — 1-3 ta element qaytaring.\n\n"
                    f"SLAYDLAR BO'YICHA LIMITLAR:\n"
                    f"{limits_str}\n\n"
                    f"DIQQAT: Agar belgilangan so'zdan oshib ketsa, matn slaydga sig'may qoladi!"
                )
            else:
                tpl_context = (
                    f"\n\nSHABLON MA'LUMOTI: Shablon {tpl_info['total_slides']} ta tayyor slayddan iborat. "
                    f"AI matn har bir slaydga to'g'ri sig'ishi kerak. "
                    f"Har bir punktni 40-60 so'z atrofida yozing."
                )

        # Define a progress callback — shows "Slayd N/total" style progress
        import asyncio as _asyncio
        _last_progress_text = [""]
        async def update_progress(completed, total, next_title=""):
            pct = int((completed / max(total, 1)) * 100)
            filled = int(pct / 5)  # 20 blocks total
            bar = "█" * filled + "░" * (20 - filled)
            next_line = f"\n⏭ <i>{next_title}</i>" if next_title else ""
            text = t("pres_progress", lang, bar=bar, pct=pct, done=completed, total=total, next=next_line, topic=topic)
            if text != _last_progress_text[0]:
                _last_progress_text[0] = text
                try:
                    await wait_msg.edit_text(text, parse_mode="HTML")
                    await _asyncio.sleep(1.0)
                except TelegramBadRequest:
                    pass
                except Exception as e:
                    logger.warning(f"Progress update error: {e}")

        # Check cancellation before expensive AI call
        if is_cancelled():
            await state.clear()
            return

        raw_content = await run_with_queue(
            db_user.id,
            generate_presentation_content,
            topic=full_topic + tpl_context,
            language=language,
            num_slides=ai_slides_count,
            style=style,
            quality=quality,
            num_chapters=num_chapters,
            forced_titles=forced_titles,
            progress_callback=update_progress
        )

        # Parse JSON
        logger.debug(f"AI Raw Response (first 200 chars): {raw_content[:200]}")
        try:
            clean_json = raw_content.replace("```json", "").replace("```", "").strip()

            import json
            def repair_json(json_str):
                try:
                    return json.loads(json_str)
                except json.JSONDecodeError:
                    for fix in ['"}', '"]}', '"]}]}', ']}', '}']:
                        try:
                            return json.loads(json_str + fix)
                        except json.JSONDecodeError:
                            pass
                    raise

            try:
                raw_data = repair_json(clean_json)
            except Exception:
                import re
                clean_json_fixed = re.sub(r'(?<!\\)"(?![:,\]}])', '\\"', clean_json)
                raw_data = repair_json(clean_json_fixed)

            raw_slides = raw_data.get("slides", raw_data) if isinstance(raw_data, dict) else raw_data

            def normalize_slide(s):
                if not isinstance(s, dict):
                    return {"title": str(s), "points": []}
                title = (
                    s.get("title") or s.get("sarlavha") or s.get("name") or
                    s.get("заголовок") or s.get("slide_title") or
                    f"Slide {s.get('slayd', '')}"
                )
                body = s.get("content") or s.get("points") or s.get("matn") or s.get("text") or s.get("mazmun") or ""
                subtitle = s.get("subtitle", "")
                if isinstance(body, str):
                    items = [p.strip() for p in body.split(". ") if p.strip()]
                    merged = []
                    current = ""
                    for p in items:
                        if len(current) < 200:
                            current = (current + ". " + p).strip(". ")
                        else:
                            merged.append(current + ".")
                            current = p
                    if current:
                        merged.append(current if current.endswith(".") else current + ".")
                    content = merged if merged else [body]
                elif not isinstance(body, list):
                    content = [str(body)]
                else:
                    content = body
                img_kw = s.get("image_keyword") or ""
                result = {"title": str(title), "content": content, "image_keyword": str(img_kw)}
                if subtitle:
                    result["subtitle"] = str(subtitle)
                if s.get("needs_image"):
                    result["needs_image"] = True
                return result

            slides_data = [normalize_slide(s) for s in raw_slides]
            logger.debug(f"Normalized {len(slides_data)} slides OK.")

        except Exception as e:
            logger.error(f"JSON Parse error: {e}\nRaw content (first 200): {raw_content[:200]}")
            slides_data = [{"title": topic, "points": [raw_content[:500]]}]
        author = data.get("author", "Foydalanuvchi")
        reviewer = data.get("reviewer", "")
        # ─── AKADEMIK TEMPLATE BRANCH ───────────────────────────────────
        if template_path and "akademik" in template_path.lower():
            try:
                await wait_msg.edit_text(t("pres_assembling", lang), parse_mode="HTML")
            except TelegramBadRequest:
                pass

            # Progress callback for akademik
            async def akademik_progress(completed, total, next_title=""):
                bar_filled = int((completed / total) * 10)
                bar = "🟩" * bar_filled + "⬜" * (10 - bar_filled)
                text = (
                    f"🎓 <b>Akademik taqdimot yaratilmoqda...</b>\n\n"
                    f"📊 <b>{completed}/{total}</b> bosqich bajarildi\n"
                    f"{bar}"
                )
                try:
                    await wait_msg.edit_text(text, parse_mode="HTML")
                except TelegramBadRequest:
                    pass

            # Generate structured akademik content via AI
            tag_data = await generate_akademik_content(
                topic=topic,
                language=language,
                subject_name=topic,
                completed_by=author,
                training_session="Ma'ruza mashg'uloti",
                quality=quality,
                progress_callback=akademik_progress,
            )

            # Generate AI images for akademik template
            image_data = {}
            image_tags = ["QUESTION_1_CONTENT_IMAGE", "QUESTION_2_CONTENT_IMAGE", "QUESTION_3_CONTENT_IMAGE"]
            
            if ai_images_count > 0:
                try:
                    await wait_msg.edit_text(f"🎨 <b>AI rasmlar yaratilmoqda ({min(ai_images_count, 3)} ta)...</b>", parse_mode="HTML")
                except TelegramBadRequest:
                    pass

                gen_count = 0
                for img_tag in image_tags[:ai_images_count]:
                    if is_cancelled():
                        await state.clear()
                        return
                    # Determine which question this image is for
                    q_num = img_tag.split("_")[1]  # "1", "2", or "3"
                    q_title = tag_data.get(f"QUESTION_{q_num}", topic)
                    try:
                        img_resp = await client.images.generate(
                            model="gpt-image-1-mini",
                            prompt=(
                                f"Educational scientific illustration for an academic lecture about: '{q_title}'. "
                                f"The overall topic is: '{topic}'. "
                                "Style: clean, professional, academic infographic or diagram. "
                                "Realistic and informative visual. No text, no letters, no words, no watermarks. "
                                "High resolution, white or neutral background."
                            ),
                            size="1024x1024",
                            quality="medium",
                            n=1
                        )
                        import httpx
                        async with httpx.AsyncClient() as http:
                            img_bytes = (await http.get(img_resp.data[0].url)).content
                        image_data[img_tag] = img_bytes
                        gen_count += 1
                        try:
                            await wait_msg.edit_text(f"🎨 <b>AI rasmlar: {gen_count}/{min(ai_images_count, 3)}</b>", parse_mode="HTML")
                        except TelegramBadRequest:
                            pass
                    except Exception as e:
                        logger.error(f"DALL-E error for {img_tag}: {e}")

            try:
                await wait_msg.edit_text("⏳ <b>Taqdimot fayli yig'ilmoqda...</b>", parse_mode="HTML")
            except TelegramBadRequest:
                pass

            # Generate the PPTX using akademik service
            pptx_bytes = await asyncio.get_event_loop().run_in_executor(
                None, generate_akademik_pptx, template_path, tag_data, image_data
            )

            # Mark free trial or deduct balance
            if is_admin:
                status_note = t("pres_admin_free", lang)
            elif free_trial:
                await mark_free_used(db_user.id)
                if price > 0: await deduct_balance(db_user.id, price)
                status_note = "🎁 Birinchi marta BEPUL!"
            else:
                await deduct_balance(db_user.id, price)
                status_note = t("pres_deducted", lang, price=format_price(price))

            try:
                await wait_msg.delete()
            except TelegramBadRequest:
                pass

            await message.answer_document(
                document=BufferedInputFile(pptx_bytes, filename=f"akademik_{topic[:30]}.pptx"),
                caption=t("pres_done", lang, topic=topic, slides="24", quality=qlabel, author=author, status=status_note),
                reply_markup=main_menu_kb(lang),
                parse_mode="HTML"
            )
            return
        # ─── END AKADEMIK BRANCH ────────────────────────────────────────

        # ─── TEST TEMPLATE BRANCH ───────────────────────────────────────
        if template_path and "test.pptx" in template_path.lower():
            try:
                await wait_msg.edit_text(t("pres_assembling", lang), parse_mode="HTML")
            except TelegramBadRequest:
                pass

            async def test_progress(completed, total, next_title=""):
                bar_filled = int((completed / max(total, 1)) * 10)
                bar = "🟩" * bar_filled + "⬜" * (10 - bar_filled)
                text = (
                    f"🎓 <b>Test taqdimoti yaratilmoqda...</b>\n\n"
                    f"📊 <b>{completed}/{total}</b> bosqich bajarildi\n"
                    f"{bar}\n"
                    f"<i>{next_title}</i>"
                )
                try:
                    await wait_msg.edit_text(text, parse_mode="HTML")
                except TelegramBadRequest:
                    pass

            test_content = await generate_test_presentation_content(
                topic=topic,
                language=language,
                author=author,
                progress_callback=test_progress
            )

            try:
                await wait_msg.edit_text("⏳ <b>Taqdimot fayli yig'ilmoqda...</b>", parse_mode="HTML")
            except TelegramBadRequest:
                pass

            pptx_bytes = await asyncio.get_event_loop().run_in_executor(
                None, generate_test_pptx, test_content, template_path
            )

            if is_admin:
                status_note = t("pres_admin_free", lang)
            elif free_trial:
                await mark_free_used(db_user.id)
                if price > 0: await deduct_balance(db_user.id, price)
                status_note = "🎁 Birinchi marta BEPUL!"
            else:
                await deduct_balance(db_user.id, price)
                status_note = t("pres_deducted", lang, price=format_price(price))

            try:
                await wait_msg.delete()
            except TelegramBadRequest:
                pass

            await message.answer_document(
                document=BufferedInputFile(pptx_bytes, filename=f"test_taqdimot_{topic[:30]}.pptx"),
                caption=t("pres_done", lang, topic=topic, slides="Test", quality=qlabel, author=author, status=status_note),
                reply_markup=main_menu_kb(lang),
                parse_mode="HTML"
            )
            return
        # ─── END TEST TEMPLATE BRANCH ───────────────────────────────────

        slide_images = {}
        
        # 1. Download and smartly map user photos using GPT-4o Vision
        user_photos = data.get("user_photos", [])
        downloaded_photos = []
        for file_id in user_photos:
            try:
                file = await message.bot.get_file(file_id)
                buf = io.BytesIO()
                await message.bot.download_file(file.file_path, buf)
                downloaded_photos.append(buf.getvalue())
            except Exception as e:
                logger.warning(f"Failed to download user photo: {e}")

        if downloaded_photos:
            try:
                await wait_msg.edit_text(t("pres_analyzing_photos", lang), parse_mode="HTML")
            except TelegramBadRequest:
                pass
            
            import base64
            
            # Build Claude vision message
            slides_text = "\n".join([f"Slide {i+1}: {s.get('title')} - {str(s.get('points'))[:100]}" for i, s in enumerate(slides_data)])
            vision_content = [
                {
                    "type": "text",
                    "text": (
                        "You are a presentation assistant. Match each provided image to the most appropriate slide index (1 to N). "
                        "Return ONLY a JSON list of integers representing the slide index for each image in the order they were provided. "
                        "Do not assign multiple images to the same slide if possible. Example output: [3, 1, 5]\n\n"
                        f"Slides Content:\n{slides_text}"
                    )
                }
            ]
            
            for img_bytes in downloaded_photos:
                b64 = base64.b64encode(img_bytes).decode('utf-8')
                vision_content.append({
                    "type": "image",
                    "source": {"type": "base64", "media_type": "image/jpeg", "data": b64}
                })
                
            try:
                from services.ai_service import _claude_client, CLAUDE_MODEL
                if _claude_client:
                    vision_resp = await _claude_client.messages.create(
                        model=CLAUDE_MODEL,
                        max_tokens=200,
                        temperature=0,
                        messages=[{"role": "user", "content": vision_content}]
                    )
                    mapping_str = vision_resp.content[0].text.replace("```json", "").replace("```", "").strip()
                else:
                    raise RuntimeError("Claude not available for vision")
                mapping = json.loads(mapping_str)
                
                used_slides = set()
                for i, target_slide in enumerate(mapping):
                    if i < len(downloaded_photos):
                        if isinstance(target_slide, int) and 1 <= target_slide <= len(slides_data):
                            if target_slide not in used_slides:
                                slide_images[target_slide] = downloaded_photos[i]
                                used_slides.add(target_slide)
            except Exception as e:
                logger.warning(f"Vision mapping failed: {e}. Falling back to sequential mapping.")
                for i, img_bytes in enumerate(downloaded_photos):
                    if i + 1 <= len(slides_data):
                        slide_images[i + 1] = img_bytes

        # 2. AUTO-IMAGES: Gemini AI generation for slides
        from services.image_search_service import generate_image_gemini
        EXCLUDED_TITLES = {"reja", "xulosa", "kirish", "план", "заключение", "введение",
                           "plan", "conclusion", "introduction", "mundarija"}
        auto_img_count = 0

        # Collect eligible slides (skip title/reja/xulosa + already have image)
        eligible = []
        for idx, sd in enumerate(slides_data):
            slide_idx_key = idx + 1
            if slide_idx_key in slide_images:
                continue
            stitle = sd.get("title", "").lower().strip()
            if any(word in stitle for word in EXCLUDED_TITLES):
                continue
            eligible.append(idx)

        # Evenly distribute photos across eligible slides
        target_photos = min(ai_images_count, len(eligible))
        if eligible and target_photos > 0:
            step = max(1, len(eligible) / target_photos)
            img_slide_indices = [eligible[int(i * step)] for i in range(target_photos)]

            try:
                await wait_msg.edit_text("🎨 <b>AI rasmlar generatsiya qilinmoqda...</b>", parse_mode="HTML")
            except TelegramBadRequest:
                pass

            for i, idx in enumerate(img_slide_indices):
                if is_cancelled():
                    await state.clear()
                    return
                sd = slides_data[idx]
                slide_idx_key = idx + 1
                slide_title = sd.get("title", topic)
                # Use AI-generated English keyword for better image relevance
                image_keyword = sd.get("image_keyword", "")
                if image_keyword:
                    query = (
                        f"Educational illustration about '{image_keyword}'. "
                        f"Context: academic presentation on '{topic}', slide titled '{slide_title}'. "
                        f"Professional, clean infographic or diagram. No text, no letters, no watermarks."
                    )
                else:
                    query = (
                        f"Educational illustration for academic presentation about '{topic}'. "
                        f"This slide is about: '{slide_title}'. "
                        f"Professional, clean, suitable for university presentation."
                    )
                try:
                    img_bytes = await generate_image_gemini(query)
                    if img_bytes:
                        slide_images[slide_idx_key] = img_bytes
                        auto_img_count += 1
                        try:
                            await wait_msg.edit_text(
                                f"🎨 <b>AI rasmlar: {auto_img_count}/{target_photos}</b>",
                                parse_mode="HTML"
                            )
                        except TelegramBadRequest:
                            pass
                except Exception as e:
                    logger.error(f"Gemini image gen error for slide {idx}: {e}")

        if auto_img_count > 0:
            logger.debug(f"Gemini AI images added: {auto_img_count}/{target_photos}")

        try:
            await wait_msg.edit_text(t("pres_assembling", lang), parse_mode="HTML")
        except TelegramBadRequest:
            pass

        # ─── SMART TEMPLATE FILL: use deep analyzer for multi-slide templates ──
        deep_analysis = await asyncio.get_event_loop().run_in_executor(
            None, analyze_template_deep, template_path
        ) if template_path else None

        # Smart fill for all templates EXCEPT General folder (old simple templates)
        is_general_template = template_path and "/General/" in template_path
        # For tagged templates, always use smart fill
        has_template_tags = deep_analysis is not None and any(
            b.tag for s in deep_analysis.slides for b in s.text_blocks
        )
        use_smart_fill = (
            deep_analysis is not None
            and not is_general_template
            and (has_template_tags or deep_analysis.total_slides >= num_slides * 0.8)
            and (not is_maket_mode or has_template_tags)
        )
        logger.debug(f"use_smart_fill={use_smart_fill}, has_tags={has_template_tags}, "
                     f"template_slides={deep_analysis.total_slides if deep_analysis else 0}, "
                     f"num_slides={num_slides}")

        if use_smart_fill:
            # Re-generate content tailored to exact template structure
            try:
                await wait_msg.edit_text(t("pres_smart_analyzing", lang), parse_mode="HTML")
            except TelegramBadRequest:
                pass

            async def smart_progress(completed, total, next_title=""):
                bar_filled = int((completed / max(total, 1)) * 10)
                bar = "🟩" * bar_filled + "⬜" * (10 - bar_filled)
                next_line = f"\n⏭ <i>{next_title}</i>" if next_title else ""
                try:
                    await wait_msg.edit_text(
                        f"🧠 <b>Shablon to'ldirilmoqda...</b>\n\n"
                        f"📊 {completed}/{total} bosqich\n{bar}{next_line}",
                        parse_mode="HTML"
                    )
                except TelegramBadRequest:
                    pass

            smart_content = await generate_content_for_template(
                topic=topic,
                language=language,
                template_analysis=deep_analysis.to_dict(),
                user_material="",
                quality=quality,
                author=author,
                forced_titles=forced_titles,
                num_chapters=num_chapters,
                progress_callback=smart_progress,
            )

            try:
                await wait_msg.edit_text(t("pres_filling_template", lang), parse_mode="HTML")
            except TelegramBadRequest:
                pass

            pptx_bytes = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: fill_template(
                    template_path=template_path,
                    slides_content=smart_content,
                    topic=topic,
                    author=author,
                    slide_images=slide_images,
                    analysis=deep_analysis,
                    target_slides=total_slides,
                    subject=subject,
                    university=university,
                    doc_type_label="Taqdimot",
                    reviewer=reviewer,
                )
            )
        else:
            # Fallback: old method for single-slide templates or maket mode
            pptx_bytes = await asyncio.get_event_loop().run_in_executor(
                None, 
                lambda: generate_pptx(slides_data, template_path, topic, author, slide_images, is_maket_mode,
                                      subject=subject, university=university, doc_type_label="Taqdimot", reviewer=reviewer)
            )

        # Mark free trial or deduct balance
        if is_admin:
            status_note = t("pres_admin_free", lang)
        elif free_trial:
            await mark_free_used(db_user.id)
            if price > 0: await deduct_balance(db_user.id, price)
            status_note = "🎁 Birinchi marta BEPUL!"
        else:
            await deduct_balance(db_user.id, price)
            status_note = t("pres_deducted", lang, price=format_price(price))

        try:
            await wait_msg.delete()
        except TelegramBadRequest:
            pass
            
        await message.answer_document(
            document=BufferedInputFile(pptx_bytes, filename=f"taqdimot_{topic[:30]}.pptx"),
            caption=t("pres_done", lang, topic=topic, slides=num_slides, quality=qlabel, author=db_user.full_name or "User", status=status_note),
            reply_markup=main_menu_kb(lang),
            parse_mode="HTML"
        )
        # Ask for rating
        from handlers.start import rating_kb
        rate_text = {"uz": "Iltimos, ishimizni baholang:", "ru": "Пожалуйста, оцените нашу работу:", "en": "Please rate our work:"}
        await message.answer(rate_text.get(lang, rate_text["uz"]), reply_markup=rating_kb("presentation"))
    except Exception as e:
        logger.exception(f"Presentation generation error: {e}")
        await message.answer(t("pres_error", lang, error=str(e)), reply_markup=main_menu_kb(lang), parse_mode="HTML")
        await state.clear()


# ─── Fallback: catch stale pres_* callbacks after bot restart ────────────────
@router.callback_query(F.data.startswith("pres_"))
async def fallback_pres_callback(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        t("pres_session_expired", "uz"),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=t("main_menu_btn", "uz"), callback_data="back_to_menu")]
        ]),
        parse_mode="HTML"
    )
    await callback.answer()
@router.message(F.text == "💳 Hisobni to'ldirish", PresentationStates.reviewing_summary)
async def prompt_pres_receipt(message: Message, state: FSMContext):
    data = await state.get_data()
    price = data.get("price", 3000)
    from handlers.payment import get_cards_text
    cards_text = get_cards_text()
    
    text = (
        f"💳 <b>To'lovni amalga oshiring</b>\n\n"
        f"Taqdimot yaratish uchun mablag' yetarli emas.\n"
        f"Taqdimot narxi: <b>{format_price(price)}</b>\n\n"
        f"Quyidagi kartalardan biriga o'tkazing:\n\n{cards_text}\n\n"
        f"To'lovni amalga oshirib, chek skrinshotini shu yerga yuboring:"
    )
    from keyboards.main_kb import back_to_menu_kb
    await message.answer(text, parse_mode="HTML", reply_markup=back_to_menu_kb())
    await state.set_state(PresentationStates.waiting_for_receipt)

@router.message(PresentationStates.waiting_for_receipt, F.photo)
async def receive_pres_receipt(message: Message, state: FSMContext, bot: Bot, db_user: User):
    photo: PhotoSize = message.photo[-1]
    file_id = photo.file_id
    
    data = await state.get_data()
    price = data.get("price", 3000)
    
    wait_msg = await message.answer("🔄 Chek tekshirilmoqda. Iltimos biroz kuting...")
    
    try:
        import base64
        from io import BytesIO
        file_info = await bot.get_file(file_id)
        file_bytes = BytesIO()
        await bot.download_file(file_info.file_path, file_bytes)
        base64_img = base64.b64encode(file_bytes.getvalue()).decode("utf-8")
        
        from services.ai_service import verify_receipt_with_ai
        result = await verify_receipt_with_ai(base64_img, price)
        
        await wait_msg.delete()
        
        if result.get("verified") and result.get("amount", 0) >= price:
            from database.db import add_balance
            db_user = await add_balance(db_user.id, price)
            await message.answer(f"✅ To'lov muvaffaqiyatli tasdiqlandi! Balansingizga {format_price(price)} qo'shildi.\nEndi <b>✅ Yaratish</b> tugmasini bosishingiz mumkin.", parse_mode="HTML")
            await show_summary(message, state, db_user)
            return
        else:
            reason = result.get("reason", "Noma'lum xatolik")
            await message.answer(f"⚠️ Chekni avtomatik tasdiqlab bo'lmadi.\nSabab: <i>{reason}</i>\n\nChek adminga qo'lda tasdiqlash uchun yuborilmoqda...", parse_mode="HTML")
    except Exception as e:
        logger.error(f"Error checking receipt: {e}")
        try:
            await wait_msg.delete()
        except:
            pass
        await message.answer("⚠️ Chekni avtomatik tekshirishda xatolik yuz berdi. Adminga yuborilmoqda...")
        
    from database.db import create_payment
    payment = await create_payment(user_id=db_user.id, amount=price, package="pres_payment", screenshot_file_id=file_id)
    
    from keyboards.admin_kb import payment_action_kb
    admin_text = (
        f"📝 <b>Yangi hujjat to'lovi (Chek)!</b>\n\n"
        f"👤 Foydalanuvchi: {db_user.full_name}\n"
        f"🆔 ID: <code>{db_user.id}</code>\n"
        f"💰 Summa: <b>{format_price(price)}</b>\n"
        f"💳 ID: #{payment.id}"
    )
    
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_photo(chat_id=admin_id, photo=file_id, caption=admin_text, reply_markup=payment_action_kb(payment.id, db_user.id), parse_mode="HTML")
        except Exception:
            pass
            
    await message.answer("✅ Chekingiz tasdiqlash uchun adminga yuborildi!\n\nTasdiqlanganidan so'ng sizga xabar beramiz, keyin yana <b>✅ Yaratish</b> tugmasini bosishingiz mumkin.")
    await state.set_state(PresentationStates.reviewing_summary)





