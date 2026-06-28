from __future__ import annotations
"""
Template Fill Handler
---------------------
Handles the "📎 Shablon to'ldirish" flow:

1. User sends topic OR uploads a document (TXT, DOCX, PDF)
2. User selects a template from the catalog
3. AI analyzes the material + template structure
4. AI generates perfectly-fitted content
5. Bot fills the template and sends the PPTX
"""

import asyncio
import io
import json
import logging

from aiogram import Router, F, Bot
from aiogram.types import (
    CallbackQuery, Message, BufferedInputFile,
    ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove,
    InlineKeyboardMarkup, InlineKeyboardButton
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types.web_app_info import WebAppInfo

from database.models import User
from database.db import deduct_balance
from keyboards.main_kb import main_menu_kb
from utils.generation_manager import cache_get, cache_set, run_with_queue
from services.ai_service import generate_content_for_template, client
from services.template_filler_service import analyze_template_deep, fill_template
from services.file_reader_service import read_document, summarize_for_prompt
from utils.helpers import format_price, safe_topic, get_template_path
from utils.i18n import t
from config import PRICING, ADMIN_IDS

def _lang(db_user) -> str:
    return (db_user.language or "uz") if db_user else "uz"

import os

logger = logging.getLogger(__name__)

router = Router()


# ══════════════════════════════════════════════════════════════════════════════
# STATES
# ══════════════════════════════════════════════════════════════════════════════

class TemplateFillStates(StatesGroup):
    choosing_language        = State()
    entering_topic_or_file   = State()   # user sends topic text OR uploads a document
    choosing_template        = State()   # user selects template via WebApp
    confirming               = State()   # summary + confirm
    waiting_for_photos       = State()   # optional: user uploads images


# ══════════════════════════════════════════════════════════════════════════════
# ENTRY POINT
# ══════════════════════════════════════════════════════════════════════════════

@router.message(F.text == "📎 Shablon to'ldirish")
async def start_template_fill(message: Message, db_user: User, state: FSMContext):
    """Entry point — start the template fill flow."""
    is_admin = db_user.id in ADMIN_IDS
    balance = db_user.balance or 0
    price = PRICING.get("presentation_std_low", 3000)

    can_afford = is_admin or balance >= price

    lang = _lang(db_user)
    if not can_afford:
        needed = price - balance
        await message.answer(
            t("pres_balance_low", lang, needed=format_price(needed)),
            reply_markup=main_menu_kb(),
            parse_mode="HTML"
        )
        return

    await state.clear()
    await state.set_state(TemplateFillStates.choosing_language)
    await state.update_data(
        quality="standard",
        author=db_user.full_name or "Talaba"
    )

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🇺🇿 O'zbekcha", callback_data="tfill_lang:uz")],
        [InlineKeyboardButton(text="🇷🇺 Русский", callback_data="tfill_lang:ru")],
        [InlineKeyboardButton(text="🇬🇧 English", callback_data="tfill_lang:en")],
        [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="tfill_cancel")],
    ])

    await message.answer(
        t("tfill_intro", lang, price=format_price(price), balance=format_price(balance)),
        reply_markup=kb,
        parse_mode="HTML"
    )


# ══════════════════════════════════════════════════════════════════════════════
# LANGUAGE SELECTION
# ══════════════════════════════════════════════════════════════════════════════

@router.callback_query(F.data.startswith("tfill_lang:"), TemplateFillStates.choosing_language)
async def choose_language(callback: CallbackQuery, state: FSMContext):
    lang = callback.data.split(":")[1]
    await state.update_data(language=lang)
    await state.set_state(TemplateFillStates.entering_topic_or_file)

    await callback.message.edit_text(
        t("tfill_send_material", lang),
        parse_mode="HTML"
    )
    await callback.answer()


# ══════════════════════════════════════════════════════════════════════════════
# TOPIC / FILE INPUT
# ══════════════════════════════════════════════════════════════════════════════

@router.message(F.text, TemplateFillStates.entering_topic_or_file)
async def receive_topic_text(message: Message, state: FSMContext):
    """User sent a topic as text."""
    topic = safe_topic(message.text or "", max_len=200)
    if not topic:
        await message.answer(t("pres_topic_empty", "uz"))
        return

    await state.update_data(topic=topic, user_material="")
    await _ask_template_selection(message, state)


@router.message(F.document, TemplateFillStates.entering_topic_or_file)
async def receive_document_file(message: Message, state: FSMContext):
    """User uploaded a document file."""
    doc = message.document
    filename = doc.file_name or "unknown.txt"
    ext = os.path.splitext(filename.lower())[1]

    supported = {".txt", ".md", ".docx", ".doc", ".pdf"}
    if ext not in supported:
        await message.answer(
            t("tfill_bad_format", "uz", ext=ext),
            parse_mode="HTML"
        )
        return

    # Download file
    wait_msg = await message.answer(t("tfill_file_read", "uz"), parse_mode="HTML")

    try:
        file = await message.bot.get_file(doc.file_id)
        buf = io.BytesIO()
        await message.bot.download_file(file.file_path, buf)
        file_bytes = buf.getvalue()
    except Exception as e:
        await wait_msg.edit_text(t("tfill_file_error", "uz", error=str(e)))
        return

    # Read document
    text = read_document(file_bytes, filename)

    if not text or len(text.strip()) < 50:
        await wait_msg.edit_text(
            t("tfill_file_empty", "uz"),
            parse_mode="HTML"
        )
        return

    # Extract a topic from the first line/paragraph
    first_line = text.split("\n")[0].strip()[:100]
    topic = first_line if len(first_line) > 10 else filename.rsplit(".", 1)[0]

    # Summarize for prompt
    material = summarize_for_prompt(text, max_chars=8000)

    await state.update_data(topic=topic, user_material=material)

    try:
        await wait_msg.delete()
    except:
        pass

    await message.answer(
        t("tfill_file_done", "uz", filename=filename, chars=f"{len(text):,}", topic=topic),
        parse_mode="HTML"
    )
    await _ask_template_selection(message, state)


async def _ask_template_selection(message: Message, state: FSMContext):
    """Show template selection keyboard."""
    await state.set_state(TemplateFillStates.choosing_template)

    webapp_url = os.getenv("WEBAPP_URL", "https://arslon.github.io/student_bot/webapp/")
    base_url = webapp_url.split("?")[0]
    if not base_url.endswith("/"):
        base_url += "/"

    import time
    v = int(time.time())
    catalog_url = f"{base_url}catalog.html?mode=fill&v={v}"

    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🎨 Shablon tanlash", web_app=WebAppInfo(url=catalog_url))],
            [KeyboardButton(text="❌ Bekor qilish")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )

    await message.answer(
        t("tfill_choose_template", "uz"),
        reply_markup=kb,
        parse_mode="HTML"
    )


# ══════════════════════════════════════════════════════════════════════════════
# TEMPLATE SELECTION (via WebApp)
# ══════════════════════════════════════════════════════════════════════════════

@router.message(F.web_app_data, TemplateFillStates.choosing_template)
async def receive_template_selection(message: Message, state: FSMContext, db_user: User):
    """User selected a template from the WebApp catalog."""
    try:
        try:
            await message.delete()
        except:
            pass

        data = json.loads(message.web_app_data.data)
        template_id = data.get("template_id", "")
        template_name = data.get("template_name", "Shablon")

        await state.update_data(
            style=template_id,
            style_name=template_name
        )

        await _show_fill_summary(message, state, db_user)

    except Exception as e:
        logger.error(f"WebApp data error: {e}")
        await message.answer(t("tfill_template_error", "uz"))


@router.message(F.text == "❌ Bekor qilish", TemplateFillStates.choosing_template)
async def cancel_template_selection(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(t("cancelled", "uz"), reply_markup=main_menu_kb())


# ══════════════════════════════════════════════════════════════════════════════
# SUMMARY & CONFIRM
# ══════════════════════════════════════════════════════════════════════════════

async def _show_fill_summary(message: Message, state: FSMContext, db_user: User):
    """Show summary of template fill settings."""
    await state.set_state(TemplateFillStates.confirming)
    data = await state.get_data()

    topic = data.get("topic", "—")
    lang = data.get("language", "uz")
    style_name = data.get("style_name", "—")
    author = data.get("author", "Talaba")
    has_material = bool(data.get("user_material"))

    lang_label = {"uz": "O'zbekcha 🇺🇿", "ru": "Русский 🇷🇺", "en": "English 🇺🇸"}.get(lang, lang)
    material_label = "📄 Fayl yuklangan" if has_material else "🤖 AI o'zi yozadi"

    user_photos = data.get("user_photos", [])
    photos_label = f"📷 {len(user_photos)} ta rasm" if user_photos else "Yo'q"

    price = PRICING.get("presentation_std_low", 3000)
    is_admin = db_user.id in ADMIN_IDS

    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📷 Rasm yuklash")],
            [KeyboardButton(text="✅ Shablonni to'ldirish")],
            [KeyboardButton(text="❌ Bekor qilish")]
        ],
        resize_keyboard=True
    )

    ulang = (db_user.language or "uz") if db_user else "uz"
    price_label = t("pres_admin_free", ulang) if is_admin else format_price(price)
    await message.answer(
        t("tfill_summary", ulang,
            topic=topic, pres_lang=lang_label, style=style_name,
            photos=photos_label, price=price_label
        ),
        reply_markup=kb,
        parse_mode="HTML"
    )


# ── Photo upload ─────────────────────────────────────────────────────────────

@router.message(F.text == "📷 Rasm yuklash", TemplateFillStates.confirming)
async def ask_photos(message: Message, state: FSMContext):
    await state.set_state(TemplateFillStates.waiting_for_photos)
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


@router.message(F.photo, TemplateFillStates.waiting_for_photos)
async def receive_photo(message: Message, state: FSMContext):
    data = await state.get_data()
    photos = data.get("user_photos", [])
    file_id = message.photo[-1].file_id
    photos.append(file_id)
    await state.update_data(user_photos=photos)
    await message.answer(t("pres_photo_received", "uz", count=len(photos)))


@router.message(F.text == "🗑 Rasmlarni o'chirish", TemplateFillStates.waiting_for_photos)
async def clear_photos(message: Message, state: FSMContext):
    await state.update_data(user_photos=[])
    await message.answer(t("pres_photos_cleared", "uz"))


@router.message(F.text == "✅ Tayyor", TemplateFillStates.waiting_for_photos)
async def done_photos(message: Message, state: FSMContext, db_user: User):
    await state.set_state(TemplateFillStates.confirming)
    data = await state.get_data()
    count = len(data.get("user_photos", []))
    await message.answer(t("pres_photos_saved", "uz", count=count), reply_markup=ReplyKeyboardRemove())
    await _show_fill_summary(message, state, db_user)


# ══════════════════════════════════════════════════════════════════════════════
# GENERATION
# ══════════════════════════════════════════════════════════════════════════════

@router.message(F.text == "✅ Shablonni to'ldirish", TemplateFillStates.confirming)
async def start_fill_generation(message: Message, state: FSMContext, db_user: User):
    """Main generation flow — analyze template, generate content, fill, export."""
    data = await state.get_data()
    topic = data.get("topic", "Taqdimot")
    language = data.get("language", "uz")
    quality = data.get("quality", "standard")
    style = data.get("style", "classic")
    author = data.get("author", "Talaba")
    user_material = data.get("user_material", "")

    # Resolve template path
    template_path = get_template_path(style)

    # Price
    price = PRICING.get("presentation_std_low", 3000)
    is_admin = db_user.id in ADMIN_IDS

    lang = _lang(db_user)
    if not is_admin and (db_user.balance or 0) < price:
        await message.answer(
            t("pres_not_enough", lang, price=format_price(price), balance=format_price(db_user.balance or 0)),
            reply_markup=main_menu_kb(),
            parse_mode="HTML"
        )
        return

    cancel_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="tfill_cancel_gen")]
    ])

    wait_msg = await message.answer(
        t("tfill_generating", lang, topic=topic, style=data.get('style_name', '—')),
        parse_mode="HTML",
        reply_markup=cancel_kb
    )

    try:
        # ── STEP 1: Analyze template ──
        analysis = await asyncio.get_event_loop().run_in_executor(
            None, analyze_template_deep, template_path
        )

        if analysis.total_slides == 0:
            await wait_msg.edit_text(t("tfill_template_empty", lang))
            return

        try:
            await wait_msg.edit_text(
                f"🤖 <b>AI shablon to'ldirmoqda...</b>\n\n"
                f"📊 <b>Shablon:</b> {analysis.total_slides} ta slayd topildi\n"
                f"⏳ <i>2. AI kontent yaratmoqda...</i>",
                parse_mode="HTML",
                reply_markup=cancel_kb
            )
        except:
            pass

        # ── STEP 2: Generate content ──
        _last_progress = [""]
        async def progress_cb(completed, total, next_title=""):
            pct = int((completed / max(total, 1)) * 100)
            filled = int(pct / 5)  # 20 blocks total
            bar = "█" * filled + "░" * (20 - filled)
            next_line = f"\n⏭ <b>Keyingi:</b> <i>{next_title}</i>" if next_title else ""
            text = (
                f"🤖 <b>AI shablon to'ldirmoqda...</b>\n\n"
                f"<code>{bar}</code>  <b>{pct}%</b>\n"
                f"📊 Bosqich: <b>{completed}</b> / {total}{next_line}\n\n"
                f"<i>⏱ Sifatli natija uchun 1-3 daqiqa kutish tavsiya etiladi</i>"
            )
            if text != _last_progress[0]:
                _last_progress[0] = text
                try:
                    await wait_msg.edit_text(text, parse_mode="HTML", reply_markup=cancel_kb)
                except:
                    pass

        # Check cache first
        style_name = data.get("style_name", "unknown")
        cached = cache_get(topic, style_name, analysis.total_slides, language, quality)
        if cached:
            slides_content = cached
            try:
                await wait_msg.edit_text(t("tfill_from_cache", lang), parse_mode="HTML")
            except:
                pass
        else:
            slides_content = await run_with_queue(
                db_user.id,
                generate_content_for_template,
                topic=topic,
                language=language,
                template_analysis=analysis.to_dict(),
                user_material=user_material,
                quality=quality,
                author=author,
                progress_callback=progress_cb,
            )
            cache_set(topic, style_name, analysis.total_slides, language, slides_content, quality)

        # ── STEP 3: Download user photos ──
        slide_images = {}
        user_photos = data.get("user_photos", [])

        if user_photos:
            try:
                await wait_msg.edit_text(
                    t("tfill_photos_loading", lang),
                    parse_mode="HTML"
                )
            except:
                pass

            downloaded = []
            for file_id in user_photos:
                try:
                    file = await message.bot.get_file(file_id)
                    buf = io.BytesIO()
                    await message.bot.download_file(file.file_path, buf)
                    downloaded.append(buf.getvalue())
                except Exception as e:
                    logger.error(f"Photo download error: {e}")

            # Map photos to slides with image placeholders
            img_slide_indices = [
                sa.index for sa in analysis.slides if sa.image_placeholders
            ]
            for i, img_bytes in enumerate(downloaded):
                if i < len(img_slide_indices):
                    slide_images[img_slide_indices[i]] = img_bytes

        # ── STEP 4: Search images for slides that need them ──
        # Find slides with image placeholders that don't have user photos
        slides_needing_images = [
            (sa.index, slides_content[sa.index].get("image_keyword", ""))
            for sa in analysis.slides
            if sa.image_placeholders and sa.index not in slide_images and sa.index < len(slides_content)
        ]

        if slides_needing_images:
            try:
                await wait_msg.edit_text(
                    t("tfill_images_search", lang, count=len(slides_needing_images)),
                    parse_mode="HTML"
                )
            except:
                pass

            for slide_idx, keyword in slides_needing_images:
                if not keyword:
                    keyword = topic
                img_bytes = await _search_and_download_image(keyword)
                if img_bytes:
                    slide_images[slide_idx] = img_bytes

        # ── STEP 5: Fill template ──
        try:
            await wait_msg.edit_text(
                t("pres_filling_template", lang),
                parse_mode="HTML"
            )
        except:
            pass

        pptx_bytes = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: fill_template(
                template_path=template_path,
                slides_content=slides_content,
                topic=topic,
                author=author,
                slide_images=slide_images,
                analysis=analysis,
            )
        )

        # ── STEP 6: Deduct balance and send file ──
        if is_admin:
            status_note = t("pres_admin_free", lang)
        else:
            await deduct_balance(db_user.id, price)
            status_note = t("pres_deducted", lang, price=format_price(price))

        try:
            await wait_msg.delete()
        except:
            pass

        await message.answer_document(
            document=BufferedInputFile(pptx_bytes, filename=f"taqdimot_{topic[:30]}.pptx"),
            caption=t("tfill_done", lang,
                topic=topic, slides=analysis.total_slides,
                style=data.get('style_name', '—'), author=author, status=status_note
            ),
            reply_markup=main_menu_kb(),
            parse_mode="HTML"
        )
        await state.clear()

    except Exception as e:
        import traceback
        traceback.print_exc()
        logger.error(f"Template fill error: {e}")
        await message.answer(
            t("pres_error", lang, error=str(e)),
            reply_markup=main_menu_kb(),
            parse_mode="HTML"
        )
        await state.clear()


@router.message(F.text == "❌ Bekor qilish", TemplateFillStates.confirming)
async def cancel_confirming(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(t("cancelled", "uz"), reply_markup=main_menu_kb())


@router.callback_query(F.data == "tfill_cancel")
async def cancel_tfill_inline(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(t("cancelled", "uz"))
    await callback.answer()


@router.callback_query(F.data == "tfill_cancel_gen")
async def cancel_tfill_generation(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(t("pres_cancel_gen", "uz"))
    await callback.answer()


# ══════════════════════════════════════════════════════════════════════════════
# IMAGE SEARCH HELPER
# ══════════════════════════════════════════════════════════════════════════════

async def _search_and_download_image(keyword: str) -> bytes | None:
    """Search for a free image using DuckDuckGo and download it."""
    try:
        from duckduckgo_search import DDGS

        ddgs = DDGS()
        results = list(ddgs.images(
            keywords=f"{keyword} presentation slide",
            max_results=3,
        ))

        if not results:
            return None

        # Try downloading the first available image
        import httpx
        async with httpx.AsyncClient(timeout=10.0) as http:
            for result in results:
                try:
                    url = result.get("image", "")
                    if not url:
                        continue
                    resp = await http.get(url)
                    if resp.status_code == 200 and len(resp.content) > 1000:
                        return resp.content
                except:
                    continue

    except ImportError:
        logger.warning("duckduckgo_search not installed, skipping image search")
    except Exception as e:
        logger.error(f"Image search error for '{keyword}': {e}")

    return None
