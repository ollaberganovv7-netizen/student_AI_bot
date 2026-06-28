from __future__ import annotations
import asyncio, json, os, io, logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, BufferedInputFile
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database.models import User
from database.db import create_request, deduct_balance, mark_free_used
from keyboards.main_kb import main_menu_kb, back_to_menu_kb
from keyboards.documents_kb import page_count_kb, referat_summary_kb, doc_initial_settings_kb
from services.ai_service import generate_document_plan, generate_document_section
from services.docx_service import generate_docx, generate_docx_from_template
from services.template_loader import load_template_and_example
from utils.helpers import format_price, is_free_trial
from utils.i18n import t
from config import ADMIN_IDS
def _lang(db_user) -> str:
    return (db_user.language or "uz") if db_user else "uz"
logger = logging.getLogger(__name__)
router = Router()
class DocumentStates(StatesGroup):
    entering_topic    = State()
    entering_subject  = State()
    choosing_quality  = State()
    choosing_pages    = State()
    reviewing_summary = State()
    waiting_for_file      = State()   # Mustaqil ish: fayl kutilmoqda
    waiting_file_language = State()   # Mustaqil ish: fayl o'qildi, til kutilmoqda
# ─── Step 1: Start ──────────────────────────────────────────────────────────
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import PRICING, ADMIN_IDS
@router.message(F.text.in_(["📚 Referat Yaratish", "📄 Mustaqil Ish Yaratish"]))
async def start_referat_creation(message: Message, state: FSMContext, db_user: User):
    is_referat = "Referat" in message.text
    service_label = "📚 <b>Referat</b>" if is_referat else "📄 <b>Mustaqil Ish</b>"
    price_std = PRICING["essay_std"] if is_referat else PRICING["mustaqil_std"]
    price_pro = PRICING["essay_pre"] if is_referat else PRICING["mustaqil_pre"]
    service_type = "referat" if is_referat else "mustaqil"
    is_admin = db_user.id in ADMIN_IDS
    free_trial = is_free_trial(db_user) and not is_admin
    balance = db_user.balance or 0
    can_afford = is_admin or free_trial or balance >= price_std
    if free_trial:
        balance_display = "🎁 Birinchi marta BEPUL!"
    elif is_admin:
        balance_display = "🛡️ Admin (tekin)"
    else:
        balance_display = format_price(balance)
    is_mustaqil = not is_referat
    if can_afford:
        if is_mustaqil:
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="✅ Mavzu yozib yaratish", callback_data=f"doc_confirm:{service_type}")],
                [InlineKeyboardButton(text="📎 Fayldan yaratish", callback_data=f"doc_file:{service_type}")],
                [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="doc_cancel")]
            ])
        else:
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="✅ Davom etish", callback_data=f"doc_confirm:{service_type}")],
                [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="doc_cancel")]
            ])
        status_line = "✅ <b>Balansingiz yetarli!</b>"
    else:
        needed = price_std - balance
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💳 Balans to'ldirish", callback_data="doc_topup")],
            [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="doc_cancel")]
        ])
        status_line = f"⚠️ <b>Balansingiz yetarli emas!</b>\n🔴 Yetishmayapti: <b>{format_price(price_std - balance)}</b>"
    await message.answer(
        f"{service_label}\n\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"💰 <b>Narx:</b> {format_price(price_std)} — {format_price(price_pro)}\n"
        f"   <i>(Standart va Pro sifatiga qarab)</i>\n"
        f"👛 <b>Sizning balansingiz:</b> {balance_display}\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"{status_line}",
        reply_markup=kb,
        parse_mode="HTML"
    )
@router.callback_query(F.data.startswith("doc_confirm:"))
async def confirm_document(callback: CallbackQuery, state: FSMContext, db_user: User):
    service_type = callback.data.split(":")[1]  # 'referat' or 'mustaqil'
    await state.update_data(
        service_type=service_type,
        is_referat=(service_type == "referat"),
        author=db_user.full_name or "Foydalanuvchi"
    )
    await state.set_state(DocumentStates.reviewing_summary)
    await callback.message.delete()
    await callback.message.answer(
        "⚙️ <b>Kerakli sozlamalaringizni to'ldiring:</b>\n\n"
        "<i>Mavzu, fan, sifat, sahifalar soni va boshqa ma'lumotlarni webapp orqali kiriting.</i>",
        reply_markup=doc_initial_settings_kb(
            db_user.balance or 0, db_user.full_name or "", doc_type=service_type, lang=_lang(db_user)
        ),
        parse_mode="HTML"
    )
    await callback.answer()
@router.callback_query(F.data == "doc_cancel")
async def cancel_document(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(t("cancelled", "uz"))
    await callback.answer()
@router.callback_query(F.data == "doc_topup")
async def topup_from_document(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        t("pres_topup_hint", "uz"),
        parse_mode="HTML"
    )
    await callback.answer()
# ─── File upload flow (Mustaqil ish only) ───────────────────────────────────
async def _read_file(message: Message) -> str:
    """Extract text from .txt / .docx / .pdf document."""
    doc  = message.document
    file = await message.bot.get_file(doc.file_id)
    buf  = io.BytesIO()
    await message.bot.download_file(file.file_path, buf)
    buf.seek(0)
    name = (doc.file_name or "").lower()
    if name.endswith(".txt"):
        return buf.read().decode("utf-8", errors="ignore")
    elif name.endswith(".docx"):
        from docx import Document as DocxDoc
        return "\n".join(p.text for p in DocxDoc(buf).paragraphs if p.text.strip())
    elif name.endswith(".pdf"):
        import pdfplumber
        parts = []
        with pdfplumber.open(buf) as pdf:
            for page in pdf.pages:
                t = page.extract_text()
                if t:
                    parts.append(t)
        return "\n".join(parts)
    else:
        raise ValueError("Qo'llab-quvvatlanmaydigan format. .txt, .docx yoki .pdf yuboring.")
@router.callback_query(F.data.startswith("doc_file:"))
async def ask_for_file(callback: CallbackQuery, state: FSMContext):
    service_type = callback.data.split(":")[1]   # 'mustaqil'
    await state.update_data(service_type=service_type, is_referat=False)
    await state.set_state(DocumentStates.waiting_for_file)
    await callback.message.edit_text(
        t("doc_send_file", "uz"),
        parse_mode="HTML"
    )
    await callback.answer()
@router.message(F.document, DocumentStates.waiting_for_file)
async def receive_file_for_mustaqil(message: Message, state: FSMContext, db_user: User):
    proc = await message.answer(t("tfill_file_read", "uz"), parse_mode="HTML")
    try:
        source_text = await _read_file(message)
        if not source_text.strip():
            await proc.edit_text(t("doc_file_empty", "uz"))
            return
        source_text = source_text[:15000]
        # Detect complexity marker
        lower = source_text.lower()
        is_murakkab = any(kw in lower for kw in [
            "murakkab", "мураккаб", "сложный", "complex", "qiyin topshiriq"
        ])
        price    = 7000 if is_murakkab else 5000
        mode     = "murakkab" if is_murakkab else "normal"
        balance  = db_user.balance or 0
        is_admin = db_user.id in ADMIN_IDS
        free_trial = is_free_trial(db_user) and not is_admin
        if free_trial:
            price = 0
        if not is_admin and not free_trial and balance < price:
            await proc.edit_text(
                f"⚠️ <b>{'Murakkab topshiriq' if is_murakkab else 'Mustaqil ish'} aniqlandi!</b>\n"
                f"💰 Narxi: <b>{format_price(price)}</b>\n"
                f"💳 Balansingiz: <b>{format_price(balance)}</b>\n\n"
                "❌ Balans yetarli emas.",
                parse_mode="HTML"
            )
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
            try:
                section_plan = await call_openai_with_retry(
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user",   "content": planning_prompt}
                    ],
                    temp=0.5,
                    max_tok=2000
                )
            except:
                section_plan = ""
            # Phase 2: Writing
            try:
                await wait_msg.edit_text(
                    f"✍️ <b>AI yozmoqda...</b>\n\n"
                    f"📄 <b>Bo'lim {i}/{total_sec}</b>\n"
                    f"{bar}\n\n"
                    f"📝 <b>2-bosqich — Yozish:</b> <i>{section_title}</i>\n\n"
                    f"<i>Reja tayyor — to'liq matn yozilmoqda...</i>",
                    parse_mode="HTML"
                )
            except:
                pass
            await asyncio.sleep(0.5)
            write_prompt = (
                f"Write the '{section_title}' section of the academic document.\n\n"
                f"MANDATORY:\n"
                f"- Obey ALL instructions from the file content.\n"
                f"- Write in {lang_instruction}.\n"
                f"- DO NOT artificially limit the length. If the assignment requires huge detail, provide it.\n"
                f"- Do NOT write the section title — only the content.\n"
                f"- No markdown. Only full academic paragraphs.\n"
                + (f"\nYOUR PRE-WRITING ANALYSIS (use as blueprint):\n{section_plan}" if section_plan else "")
            )
            section_text = await call_openai_with_retry(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user",   "content": write_prompt}
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
            await wait_msg.edit_text(f"❌ Xatolik yuz berdi: {e}")
        except:
            await callback.message.bot.send_message(callback.message.chat.id, f"❌ Xatolik: {e}")
        await state.clear()
@router.message(DocumentStates.entering_topic)
async def enter_topic(message: Message, state: FSMContext):
    await state.update_data(topic=message.text.strip())
    await state.set_state(DocumentStates.entering_subject)
    await message.answer(
        t("doc_enter_subject", "uz"),
        reply_markup=back_to_menu_kb(),
        parse_mode="HTML"
    )
@router.message(DocumentStates.entering_subject)
async def enter_subject(message: Message, state: FSMContext):
    await state.update_data(subject=message.text.strip())
    await state.set_state(DocumentStates.choosing_quality)
    from keyboards.documents_kb import referat_quality_kb
    await message.answer(
        t("doc_choose_quality", "uz"),
        reply_markup=referat_quality_kb(),
        parse_mode="HTML"
    )
@router.callback_query(F.data.startswith("ref_quality:"), DocumentStates.choosing_quality)
async def choose_quality(callback: CallbackQuery, state: FSMContext):
    quality = callback.data.split(":")[1]
    is_pro = (quality == "pro")
    await state.update_data(quality=quality, is_pro=is_pro)
    await state.set_state(DocumentStates.choosing_pages)
    from keyboards.documents_kb import page_count_kb
    await callback.message.edit_text(
        f"📑 <b>{'💎 Pro' if is_pro else '✨ Standart'} | Hajmni tanlang:</b>",
        reply_markup=page_count_kb(is_pro=is_pro),
        parse_mode="HTML"
    )
    await callback.answer()
@router.callback_query(F.data.startswith("pages:"), DocumentStates.choosing_pages)
async def choose_pages(callback: CallbackQuery, state: FSMContext, db_user: User):
    _, pages, price = callback.data.split(":")
    await state.update_data(num_pages=int(pages), price=int(price))
    # Auto-generate a plan first
    data = await state.get_data()
    topic = data.get("topic")
    wait_msg = await callback.message.edit_text(
        t("doc_preparing_plan", "uz"),
        parse_mode="HTML"
    )
    try:
        # For Pro version, we explicitly ask for a much longer plan
        is_pro = data.get("is_pro", False)
        plan_prompt = "7-10 ta juda batafsil bo'lim" if is_pro else "5-6 ta bo'lim"
        plan_data = await generate_document_plan(
            service_type="essay", 
            topic=topic, 
            language=data.get("language", "uz"),
            detail_level="pro" if is_pro else "standard"
        )
        plan = plan_data.get("plan", "")
        sections = [s.strip() for s in plan.split('\n') if s.strip()]
        await state.update_data(manual_plan=plan, num_chapters=len(sections))
    except Exception as e:
        logger.error(f"Document plan generation error: {e}")
    await wait_msg.delete()
    await state.set_state(DocumentStates.reviewing_summary)
    await show_referat_summary(callback.message, state, db_user)
    await callback.answer()
@router.message(F.web_app_data, DocumentStates.reviewing_summary)
async def handle_referat_webapp(message: Message, state: FSMContext, db_user: User):
    try:
        try:
            await message.delete()
        except TelegramBadRequest:
            pass
        data = json.loads(message.web_app_data.data)
        action = data.get("action", "")
        if action == "plan_update":
            await state.update_data(manual_plan=data.get("manual_plan"), num_chapters=data.get("num_chapters"))
            await show_referat_summary(message, state, db_user)
        elif action == "content_update":
            await state.update_data(extra_info=data.get("extra_info"), tone=data.get("tone"))
            await show_referat_summary(message, state, db_user)
        elif action == "full_settings":
            # Full settings from webapp — topic, subject, quality, pages, price, etc.
            quality = data.get("quality", "standard")
            ai_images = data.get("ai_images", 3)
            await state.update_data(
                topic=data.get("topic"),
                subject=data.get("subject"),
                author=data.get("author", db_user.full_name or "Foydalanuvchi"),
                language=data.get("language", "uz"),
                quality=quality,
                is_pro=(quality == "pro"),
                num_pages=data.get("num_pages", 15),
                price=data.get("price", 3000),
                base_price=data.get("price", 3000),
                ai_images_count=ai_images,
            )
            # Auto-generate plan
            topic = data.get("topic")
            wait_msg = await message.answer(
                t("doc_preparing_plan", "uz"),
                parse_mode="HTML"
            )
            try:
                plan_data = await generate_document_plan(
                    service_type="essay",
                    topic=topic,
                    language=data.get("language", "uz"),
                    detail_level="pro" if quality == "pro" else "standard"
                )
                plan = plan_data.get("plan", "")
                sections = [s.strip() for s in plan.split('\n') if s.strip()]
                await state.update_data(manual_plan=plan, num_chapters=len(sections))
            except Exception as e:
                logger.error(f"Plan generation in webapp error: {e}")
            await wait_msg.delete()
            await show_referat_summary(message, state, db_user)
        else:
            # Legacy settings update (author, language only)
            if "author" in data:
                await state.update_data(author=data.get("author"), language=data.get("language"))
            await show_referat_summary(message, state, db_user)
    except json.JSONDecodeError as e:
        logger.error(f"Referat WebApp JSON decode error: {e}")
        await message.answer("⚠️ Ma'lumotlarni o'qishda xatolik. Qaytadan urinib ko'ring.")
    except Exception as e:
        logger.error(f"Referat WebApp error: {e}")
        await message.answer("⚠️ Kutilmagan xatolik yuz berdi.")
async def show_referat_summary(message: Message, state: FSMContext, db_user: User):
    import html as _html
    data = await state.get_data()
    topic = _html.escape(data.get("topic") or "")
    subject = _html.escape(data.get("subject") or "")
    pages = data.get("num_pages")
    price = data.get("price")
    author = _html.escape(data.get("author", "Foydalanuvchi"))
    quality_val = data.get("quality", "standard")
    quality_label = "💎 Pro" if quality_val == "pro" else "✨ Standart"
    text = (
        f"┌─ 📝 <b>HUJJAT</b> │ {quality_label} ─┐\n\n"
        f"  📚  <b>Mavzu:</b> {topic}\n"
        f"  🎓  <b>Fan:</b> {subject}\n"
        f"  👤  <b>Muallif:</b> {author}\n"
        f"  📄  <b>Sahifalar:</b> {pages} bet\n"
        f"  💰  <b>Narxi:</b> {format_price(price)}\n\n"
        f"└──────────────────────┘\n\n"
        f"<i>Reja yoki ma'lumotlarni o'zgartirish uchun tugmalardan foydalaning.</i>"
    )
    summary_id = data.get("summary_msg_id")
    if summary_id:
        try:
            await message.bot.delete_message(chat_id=message.chat.id, message_id=summary_id)
        except TelegramBadRequest:
            pass
    doc_type = data.get("service_type", "referat")
    msg = await message.answer(text, reply_markup=referat_summary_kb(
        db_user.balance or 0, db_user.full_name or "",
        topic=topic, doc_type=doc_type, quality=quality_val, lang=_lang(db_user)
    ), parse_mode="HTML")
    await state.update_data(summary_msg_id=msg.message_id)
@router.message(F.text.contains("AI Rasm"), DocumentStates.reviewing_summary)
async def choose_ai_images_referat(message: Message, state: FSMContext, db_user: User):
    """Let user choose how many AI images to add (0-10, 1000 so'm each)."""
    buttons = []
    buttons.append([InlineKeyboardButton(text="❌ Rasmsiz (0)", callback_data="ref_img:0")])
    for i in range(1, 11, 2):
        row = []
        row.append(InlineKeyboardButton(text=f"🖼 {i} ta (+{i*1000} so'm)", callback_data=f"ref_img:{i}"))
        if i + 1 <= 10:
            row.append(InlineKeyboardButton(text=f"🖼 {i+1} ta (+{(i+1)*1000} so'm)", callback_data=f"ref_img:{i+1}"))
        buttons.append(row)
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    data = await state.get_data()
    current = data.get("ai_images_count", 0)
    await message.answer(
        f"� <b>AI rasm qo'shish</b>\n\n"
        f"Hozirgi: {current} ta rasm\n"
        f"Har bir rasm: 1 000 so'm\n\n"
        f"Nechta rasm kerak?",
        reply_markup=kb, parse_mode="HTML"
    )
@router.callback_query(F.data.startswith("ref_img:"))
        await message.answer("⚠️ Ma'lumotlarni o'qishda xatolik. Qaytadan urinib ko'ring.")
    except Exception as e:
        logger.error(f"Referat WebApp error: {e}")
        await message.answer("⚠️ Kutilmagan xatolik yuz berdi.")
async def show_referat_summary(message: Message, state: FSMContext, db_user: User):
async def show_referat_summary(message: Message, state: FSMContext, db_user: User):
# GAP
# GAP
    )
    def is_cancelled():
        return cancel_flag.get("cancelled", False)
    try:
        # Generate plan on the fly if not provided manually to save tokens during summary stage
        if not plan:
            try:
                await wait_msg.edit_text(t("doc_preparing_plan", "uz"), parse_mode="HTML")
                quality = data.get("quality", "standard")
                plan_data = await generate_document_plan(
                    service_type="essay",
                    topic=topic,
                    language=data.get("language", "uz"),
                    detail_level="pro" if quality == "pro" else "standard",
                    num_chapters=data.get("num_chapters", 2),
                    await state.set_state(DocumentStates.reviewing_summary)
            await show_referat_summary(message, state, db_user)
            return
        else:
    try:
        # Generate plan on the fly if not provided manually to save tokens during summary stage
        if not plan:
            try:
                await wait_msg.edit_text(t("doc_preparing_plan", "uz"), parse_mode="HTML")
                quality = data.get("quality", "standard")
                plan_data = await generate_document_plan(
                    service_type="essay",
                    topic=topic,
                    language=data.get("language", "uz"),
                    detail_level="pro" if quality == "pro" else "standard",
                    num_chapters=data.get("num_chapters", 2),
    await show_referat_summary(callback.message, state, db_user)
@router.message(F.text.contains("Yaratish"), DocumentStates.reviewing_summary)
async def generate_referat(message: Message, state: FSMContext, db_user: User):
    data = await state.get_data()
    price = data.get("price", 3000)
    topic = data.get("topic")
    pages = data.get("num_pages")
    plan = data.get("manual_plan", "")
    lang = _lang(db_user)
    is_admin = db_user.id in ADMIN_IDS
    free_trial = is_free_trial(db_user) and not is_admin
    if free_trial:
        price = 0
    if not is_admin and not free_trial and (db_user.balance or 0) < price:
        await message.answer(t("pres_balance_ok", lang).replace("✅", "⚠️").replace("yetarli", "yetarli emas"), reply_markup=main_menu_kb())
        return
    # Cancellation support
    cancel_flag = {"cancelled": False}
    await state.update_data(cancel_flag=cancel_flag)
    cancel_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="doc_cancel_gen")]
    ])
    await callback.answer(f"✅ {count} ta AI rasm tanlandi" if count > 0 else "✅ Rasmsiz")
    await show_referat_summary(callback.message, state, db_user)
@router.message(F.text.contains("Yaratish"), DocumentStates.reviewing_summary)
async def generate_referat(message: Message, state: FSMContext, db_user: User):
    data = await state.get_data()
    price = data.get("price", 3000)
    topic = data.get("topic")
    pages = data.get("num_pages")
    plan = data.get("manual_plan", "")
    lang = _lang(db_user)
    is_admin = db_user.id in ADMIN_IDS
    free_trial = is_free_trial(db_user) and not is_admin
    if free_trial:
        price = 0
    if not is_admin and not free_trial and (db_user.balance or 0) < price:
        await message.answer(t("pres_balance_ok", lang).replace("✅", "⚠️").replace("yetarli", "yetarli emas"), reply_markup=main_menu_kb())
        return
    # Cancellation support
    cancel_flag = {"cancelled": False}
    await state.update_data(cancel_flag=cancel_flag)
    cancel_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="doc_cancel_gen")]
    ])
    wait_msg = await message.answer(
        t("doc_generating", lang, topic=topic, pages=pages),
        parse_mode="HTML",
        reply_markup=cancel_kb
    )
    def is_cancelled():
        return cancel_flag.get("cancelled", False)
    try:
        # Dynamic word count calculation to hit the page target
        sections = [s.strip() for s in plan.split('\n') if s.strip()] if plan else [topic]
        num_sections = len(sections)
        # 1 page is ~250-280 words with our 14pt 1.5 spacing format
        # Use 300 to overshoot slightly and guarantee page count
        total_target_words = pages * 300 
        words_per_section = int(total_target_words / num_sections)
        # Load structure template + quality example
        return cancel_flag.get("cancelled", False)
    try:
        # Dynamic word count calculation to hit the page target
        sections = [s.strip() for s in plan.split('\n') if s.strip()] if plan else [topic]
        num_sections = len(sections)
# GAP
# GAP
# GAP
                    "cheklov ishlatmang. Faqat faylda yozilganidek, aynan o'sha "
                    f"format va tuzilmada bajaring. Hajm: ~{pages * 280} so'z."
                ),
                language=data.get("language", "uz"),
                quality="pro",
                service_type="article"
            )
            full_content = [result]
        else:
            # ── NORMAL: template-guided section generation ────────────────────
            source_block = (
                f"\n\n--- YUBORILGAN FAYL MATNI (asosiy manba) ---\n"
                f"{source_text[:5000]}\n"
                "--- FAYL MATNI TUGADI ---\n\n"
                "MUHIM: Faylda berilgan ma'lumotlar asosida yozing.\n"
            ) if source_text else ""
            for i, sec in enumerate(sections, 1):
                if is_cancelled():
                    await state.clear()
                    return
                filled = int(((i - 1) / len(sections)) * 10)
                bar = "🟩" * filled + "⬜" * (10 - filled)
                try:
                    await wait_msg.edit_text(
                        f"🤖 <b>AI hujjat yozmoqda...</b>\n\n"
                        f"📊 <b>{i-1}/{len(sections)}</b> bo'lim tayyor\n"
                        f"{bar}\n\n"
                        f"⏭ <b>Hozir yozilmoqda:</b> <i>{sec}</i>\n\n"
# GAP
# GAP
                        f"⏳ <i>4-5 daqiqa kutib turing — sifatli natija uchun!</i>",
                        parse_mode="HTML",
                        reply_markup=cancel_kb
                    )
                except:
                    pass
                text = await generate_document_section(
                    topic=topic,
                    section_title=sec,
                    extra_details=(
                        f"{template_context}\n" if template_context else ""
                    ) + source_block + f"Ushbu bo'lim aynan {words_per_section} ta so'zdan iborat bo'lsin. " + data.get("extra_info", ""),
                    language=data.get("language", "uz"),
                    quality=data.get("quality", "standard"),
                    service_type="article"
                )
                full_content.append(f"# {sec}\n\n{text}")
        # Add bibliography
        try:
            bib_title = "FOYDALANILGAN ADABIYOTLAR RO'YXATI"
            try:
                await wait_msg.edit_text(f"⏳ <b>Hujjat yaratilmoqda...</b>\n📚 <i>Adabiyotlar ro'yxati shakllantirilmoqda...</i>")
            except TelegramBadRequest:
                pass
            bib_count = "10-15" if data.get("quality") == "pro" else "5-8"
            bib_text = await generate_document_section(
        # Add bibliography
        try:
            bib_title = "FOYDALANILGAN ADABIYOTLAR RO'YXATI"
            try:
                await wait_msg.edit_text(f"⏳ <b>Hujjat yaratilmoqda...</b>\n📚 <i>Adabiyotlar ro'yxati shakllantirilmoqda...</i>")
            except TelegramBadRequest:
                pass
            bib_count = "10-15" if data.get("quality") == "pro" else "5-8"
            bib_text = await generate_document_section(
                topic=topic, 
                section_title=bib_title, 
                extra_details=(
                    f"Mavzu bo'yicha kamida {bib_count} ta REAL ilmiy manbalarni yoz.\n"
                    "TARKIBI:\n"
                    "- 40% O'zbek mualliflari (O'zbekiston nashriyotlari: Fan, Iqtisod-Moliya, Sharq, TDIU). "
                    "Masalan: Karimov A.K., Abdullayev B.M., Xo'jayev N.R. kabi.\n"
                    "- 60% Xorijiy mualliflar (Pearson, McGraw-Hill, Cambridge, Springer). "
                    "Masalan: Samuelson P., Mankiw G., Porter M. kabi.\n"
                    "FORMAT: [1] Familiya I.O. Kitob nomi. — Shahar: Nashriyot, yil. — bet soni.\n"
                    "Faqat ro'yxat ber, boshqa hech narsa qo'shma. Izoh yoki sarlavha yozma."
                ),
                language=data.get("language", "uz"),
                quality="standard",
                service_type="article"
            )
            full_content.append(f"# {bib_title}\n\n{bib_text}")
        except Exception as bib_err:
            logger.error(f"Bibliography generation error: {bib_err}")
        content = "\n\n".join(full_content)
        doc_type = data.get("service_type", "referat")
        if doc_type == "referat":
            # Use ready-made template for referat
            docx_bytes = await asyncio.get_event_loop().run_in_executor(
                None,
                generate_docx_from_template,
                topic,
                content,
                data.get("author", "Foydalanuvchi"),
                plan,
                data.get("subject", ""),
                data.get("reviewer", ""),
                data.get("university", ""),
                data.get("specialty", "")
            )
        else:
            # Mustaqil ish uses code-generated DOCX
            docx_bytes = await asyncio.get_event_loop().run_in_executor(
                None, 
                generate_docx, 
                "report", 
                topic, 
                content,
                ),
                language=data.get("language", "uz"),
        doc_type = data.get("service_type", "referat")
        if doc_type == "referat":
            # Use ready-made template for referat
            docx_bytes = await asyncio.get_event_loop().run_in_executor(
                None,
                generate_docx_from_template,
                topic,
                content,
                data.get("author", "Foydalanuvchi"),
                plan,
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
        cancel_flag["cancelled"] = True
    await state.clear()
    await callback.message.edit_text(t("doc_cancel_gen", "uz"))
    await callback.answer()
@router.message(F.text == "❌ Bekor qilish", DocumentStates.reviewing_summary)
async def cancel_referat(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(t("cancelled", "uz"), reply_markup=main_menu_kb())
@router.message(F.text == "💳 Hisobni to'ldirish", DocumentStates.reviewing_summary)
async def prompt_doc_receipt(message: Message, state: FSMContext):
    data = await state.get_data()
    price = data.get("price", 3000)
    from handlers.payment import get_cards_text
    cards_text = get_cards_text()
    text = (
        f"💳 <b>To'lovni amalga oshiring</b>\n\n"
        f"Hujjat yaratish uchun mablag' yetarli emas.\n"
        f"Hujjat narxi: <b>{format_price(price)}</b>\n\n"
        f"Quyidagi kartalardan biriga o'tkazing:\n\n{cards_text}\n\n"
        f"To'lovni amalga oshirib, chek skrinshotini shu yerga yuboring:"
    )
    from keyboards.main_kb import back_to_menu_kb
    await message.answer(text, parse_mode="HTML", reply_markup=back_to_menu_kb())
    await state.set_state(DocumentStates.waiting_for_receipt)
@router.message(DocumentStates.waiting_for_receipt, F.photo)
async def receive_doc_receipt(message: Message, state: FSMContext, bot: Bot, db_user: User):
    photo: PhotoSize = message.photo[-1]
    file_id = photo.file_id
    data = await state.get_data()
    price = data.get("price", 3000)
    # Send waiting message
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
            await show_referat_summary(message, state, db_user)
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
    # Fallback to Admin
    from database.db import create_payment
    payment = await create_payment(user_id=db_user.id, amount=price, package="doc_payment", screenshot_file_id=file_id)
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
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
# GAP
        except Exception:
            pass
    await message.answer("✅ Chekingiz tasdiqlash uchun adminga yuborildi!\n\nTasdiqlanganidan so'ng sizga xabar beramiz, keyin yana <b>✅ Yaratish</b> tugmasini bosishingiz mumkin.")
    await state.set_state(DocumentStates.reviewing_summary)