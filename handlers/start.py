from __future__ import annotations
import json

from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
from aiogram.fsm.context import FSMContext

from database.models import User
from database.db import process_referral, get_referral_stats, update_user_language, save_rating
from keyboards.main_kb import main_menu_kb, back_to_menu_kb, lang_select_kb
from utils.helpers import has_access, format_price
from utils.i18n import t, btn
from config import PRICING, REFERRAL_BONUS_INVITER, REFERRAL_BONUS_INVITEE

router = Router()


def _lang(db_user: User) -> str:
    return (db_user.language or "uz") if db_user else "uz"


def build_welcome_text(db_user: User = None) -> str:
    """Build the dynamic main menu welcome message with user balance and prices."""
    lang = _lang(db_user)
    import html as _html
    name = _html.escape((db_user.full_name if db_user and db_user.full_name else "do'st").split()[0])
    balance = (db_user.balance or 0) if db_user else 0
    free_trial = db_user and not db_user.free_used

    if free_trial:
        balance_line = "🎁 1 ta BEPUL generation!"
    else:
        balance_line = format_price(balance)

    return t("welcome", lang,
             name=name,
             balance=balance_line,
             pres_price=format_price(PRICING['presentation_std_low']),
             essay_price=format_price(PRICING['essay_std']),
             must_price=format_price(PRICING['mustaqil_std']),
             kurs_price=format_price(PRICING['coursework_low']),
             tezis_price=format_price(PRICING['tezis_5']),
             uslubiy_price=format_price(PRICING['uslubiy_low']))


# Legacy fallback (used in places without user object)
WELCOME_TEXT = (
    "\U0001f393 <b>STUDENT(AI) BOT</b>\n\n"
    "Akademik ishlaringiz uchun AI yordamchisi.\n\n"
    "\U0001f680 <b>Quyidagi tugmalardan birini tanlang:</b>"
)


# ─── Language selection ──────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("set_lang:"))
async def cb_set_lang(callback: CallbackQuery, db_user: User, state: FSMContext):
    lang = callback.data.split(":")[1]
    if lang not in ("uz", "ru", "en"):
        lang = "uz"
    await update_user_language(db_user.id, lang)
    db_user.language = lang
    await callback.message.edit_text(t("lang_set", lang), parse_mode="HTML")
    await callback.message.answer(
        build_welcome_text(db_user),
        reply_markup=main_menu_kb(lang),
        parse_mode="HTML",
    )
    await callback.answer()


# ─── /start ──────────────────────────────────────────────────────────────────

@router.message(CommandStart(deep_link=True))
async def cmd_start_ref(message: Message, db_user: User, state: FSMContext):
    """Handle /start deep links: ref_XXXX for referrals, menu_XXX for Mini App menu."""
    await state.clear()
    lang = _lang(db_user)
    args = message.text.split(maxsplit=1)
    deep_link = args[1] if len(args) > 1 else ""

    # ── Mini App Generate deep links (gen_presentation, gen_referat, etc.) ──
    if deep_link.startswith("gen_"):
        await _show_submit_button(message, db_user)
        return

    # ── Mini App Menu deep links ──
    if deep_link.startswith("menu_"):
        menu_type = deep_link.replace("menu_", "")
        await _handle_menu_action(message, db_user, state, menu_type)
        return

    # ── Referral deep links ──
    if deep_link.startswith("ref_"):
        try:
            referrer_id = int(deep_link.replace("ref_", ""))
            success = await process_referral(
                referrer_id=referrer_id,
                new_user_id=db_user.id,
                bonus_inviter=REFERRAL_BONUS_INVITER,
                bonus_invitee=REFERRAL_BONUS_INVITEE,
            )
            if success:
                await message.answer(
                    t("referral_success", lang, bonus=format_price(REFERRAL_BONUS_INVITEE)),
                    parse_mode="HTML",
                )
        except (ValueError, Exception):
            pass

    # Show language selection then menu
    await message.answer(t("lang_prompt", lang), reply_markup=lang_select_kb(), parse_mode="HTML")


async def _handle_menu_action(message: Message, db_user: User, state: FSMContext, menu_type: str):
    """Route Mini App menu selections to the appropriate service handler."""
    lang = _lang(db_user)

    if menu_type == "presentation":
        from handlers.presentation import start_presentation
        # Create a copy with correct text so handler can read it
        fake = message.model_copy(update={"text": btn("presentation", lang)})
        await start_presentation(fake, db_user=db_user, state=state)
    elif menu_type == "referat":
        from handlers.documents import start_referat_creation
        fake = message.model_copy(update={"text": "📚 Referat yaratish"})
        await start_referat_creation(fake, state=state, db_user=db_user)
    elif menu_type == "mustaqil":
        from handlers.documents import start_referat_creation
        fake = message.model_copy(update={"text": "📄 Mustaqil ish yaratish"})
        await start_referat_creation(fake, state=state, db_user=db_user)
    elif menu_type == "kurs":
        from handlers.coursework import start_coursework
        await start_coursework(message, state=state, db_user=db_user)
    elif menu_type == "tezis":
        from handlers.tezis import start_tezis
        await start_tezis(message, state=state, db_user=db_user)
    elif menu_type == "maqola":
        from handlers.maqola import start_maqola
        await start_maqola(message, state=state, db_user=db_user)
    elif menu_type == "uslubiy":
        from handlers.uslubiy import start_uslubiy_creation
        await start_uslubiy_creation(message, state=state, db_user=db_user)
    elif menu_type == "topup":
        from handlers.payment import payment_start
        await payment_start(message, state=state, db_user=db_user)
    elif menu_type == "account":
        await _show_account(message, db_user)
    elif menu_type == "referral":
        await _show_referral(message, db_user)
    elif menu_type == "help":
        await _show_help(message, db_user)
    else:
        await message.answer(build_welcome_text(db_user), reply_markup=main_menu_kb(lang), parse_mode="HTML")


import os

async def _show_submit_button(message: Message, db_user: User):
    """Show a KeyboardButton with WebApp pointing to submit.html so sendData works."""
    webapp_url = os.getenv("WEBAPP_URL", "https://arslon.github.io/student_bot/webapp/")
    base = webapp_url.split("?")[0]
    if not base.endswith("/"): base += "/"
    submit_url = base + "submit.html"

    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🚀 Yaratishni boshlash", web_app=WebAppInfo(url=submit_url))],
            [KeyboardButton(text="❌ Bekor qilish")],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )
    await message.answer(
        "✅ <b>Ma'lumotlar tayyor!</b>\n\n"
        "Quyidagi tugmani bosing va yaratish avtomatik boshlanadi:",
        reply_markup=kb,
        parse_mode="HTML",
    )


@router.message(F.web_app_data)
async def handle_webapp_submit(message: Message, db_user: User, state: FSMContext):
    """Receive job data from submit.html and start generation."""
    try:
        data = json.loads(message.web_app_data.data)
    except (json.JSONDecodeError, AttributeError):
        return

    if data.get("action") != "generate":
        return

    service = data.get("service", "")
    topic = data.get("topic", "")
    language = data.get("language", "uz")
    quality = data.get("quality", "standard")

    if not topic:
        await message.answer("⚠️ Mavzu topilmadi. Qayta urinib ko'ring.")
        return

    lang = _lang(db_user)

    if service == "presentation":
        from handlers.presentation import finalize_presentation_logic
        num_slides = int(data.get("num_slides", 10))
        template_id = data.get("template_id", "plain")
        style = "classic" if template_id == "plain" else template_id

        await state.update_data(
            topic=topic,
            num_slides=num_slides,
            quality=quality,
            language=language,
            style=style,
            manual_plan=None,
            num_chapters=4,
            subject="",
            university="",
            ai_images_count=3,
            ai_images_extra=0,
        )
        await finalize_presentation_logic(message, state, db_user, style)

    elif service in ("referat", "mustaqil"):
        from handlers.documents import generate_referat
        doc_type = "essay" if service == "referat" else "report"
        pages = int(data.get("pages", 12))
        subject = data.get("subject", "")
        # Calculate price based on page tiers
        if pages <= 10:
            price = 5000
        elif pages <= 20:
            price = 10000
        elif pages <= 25:
            price = 15000
        else:
            price = 20000

        await state.update_data(
            service_type=doc_type, topic=topic, language=language,
            quality=quality, num_pages=pages, subject=subject,
            university="", manual_plan="", extra_info="",
            source_text="", mode="normal", price=price,
        )
        await generate_referat(message, state=state, db_user=db_user)

    elif service == "kurs":
        from handlers.coursework import generate_coursework
        pages = int(data.get("pages", 25))
        price = PRICING.get("coursework_high" if pages > 30 else "coursework_low", 15000)
        await state.update_data(
            topic=topic, language=language, pages=pages,
            manual_plan="", extra_info="", price=price,
        )
        # generate_coursework expects a CallbackQuery, so call directly with message
        await _run_coursework(message, state, db_user)

    elif service == "tezis":
        from handlers.tezis import tezis_generate
        pages = int(data.get("pages", 10))
        await state.update_data(
            topic=topic, language=language, pages=pages,
            author=db_user.full_name or "Muallif",
            source_text="", mode="normal",
        )
        await tezis_generate(message, state=state, db_user=db_user)

    elif service == "maqola":
        from handlers.maqola import maqola_generate
        pages = int(data.get("pages", 10))
        await state.update_data(
            topic=topic, language=language, pages=pages,
            author=db_user.full_name or "Muallif",
            source_text="", mode="normal",
        )
        await maqola_generate(message, state=state, db_user=db_user)

    elif service == "uslubiy":
        from handlers.uslubiy import generate_uslubiy
        pages = int(data.get("pages", 25))
        price = PRICING.get("uslubiy_high" if pages > 30 else "uslubiy_low", 15000)
        await state.update_data(
            topic=topic, language=language, pages=pages,
            manual_plan="", extra_info="", price=price,
        )
        await generate_uslubiy(message, state=state, db_user=db_user)

    else:
        await message.answer("⚠️ Noma'lum xizmat turi.", reply_markup=main_menu_kb(lang))


async def _run_coursework(message: Message, state: FSMContext, db_user: User):
    """Adapter: run coursework generation from a Message (generate_coursework expects CallbackQuery)."""
    from handlers.coursework import generate_coursework as _cw_gen
    from config import ADMIN_IDS
    data = await state.get_data()
    topic = data.get("topic")
    price = data.get("price", 15000)
    pages = data.get("pages", 25)
    language = data.get("language", "uz")

    is_admin = db_user.id in ADMIN_IDS
    free_trial = not db_user.free_used and not is_admin
    if free_trial:
        price = 0
    if not is_admin and not free_trial and (db_user.balance or 0) < price:
        await message.answer("⚠️ Balansingiz yetarli emas!", reply_markup=main_menu_kb())
        return

    await state.update_data(num_pages=pages)

    # Since generate_coursework expects CallbackQuery, we replicate its core logic here
    from services.ai_service import generate_document_section, generate_document_plan
    from services.doc_builder import build_document
    from database.db import deduct_balance, mark_free_used
    from keyboards.main_kb import main_menu_kb

    cancel_flag = {"cancelled": False}
    await state.update_data(cancel_flag=cancel_flag)

    cancel_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cw_cancel_gen")]
    ])
    wait_msg = await message.answer(
        f"⏳ <b>Kurs ishi yaratilmoqda...</b>\n📝 Mavzu: {topic}\n📄 Sahifalar: {pages}\n⏳ <i>4-5 daqiqa kutib turing — sifatli natija uchun!</i>",
        parse_mode="HTML", reply_markup=cancel_kb,
    )

    def is_cancelled():
        return cancel_flag.get("cancelled", False)

    try:
        plan = data.get("manual_plan") or ""
        if not plan:
            plan_data = await generate_document_plan("coursework", topic, language, "pro")
            plan = plan_data.get("plan", "")

        sections = [s.strip() for s in plan.split('\n') if s.strip()]
        total_words = pages * 260
        words_per = total_words // max(len(sections), 1)

        full_content = []
        for i, sec in enumerate(sections):
            if is_cancelled():
                break
            try:
                await wait_msg.edit_text(
                    f"⏳ <b>Kurs ishi yaratilmoqda...</b>\n📝 {sec}\n📊 {i+1}/{len(sections)}",
                    parse_mode="HTML", reply_markup=cancel_kb,
                )
            except:
                pass
            text = await generate_document_section(
                topic=topic, section_title=sec, extra_details=f"~{words_per} so'z yozing",
                language=language, quality="pro", service_type="coursework"
            )
            full_content.append(text)

        if is_cancelled():
            await wait_msg.edit_text("❌ Bekor qilindi.", parse_mode="HTML")
            await state.clear()
            return

        joined = "\n\n".join(full_content)
        file_path = await build_document(
            content=joined, topic=topic, doc_type="coursework",
            author=db_user.full_name or "Muallif", language=language,
        )
        from aiogram.types import FSInputFile
        await message.answer_document(FSInputFile(file_path), caption=f"📚 Kurs ishi: {topic}")
        if free_trial:
            await mark_free_used(db_user.id)
        elif db_user.id not in ADMIN_IDS:
            await deduct_balance(db_user.id, price)
        await message.answer("✅ Tayyor!", reply_markup=main_menu_kb())
        await state.clear()
    except Exception as e:
        await wait_msg.edit_text(f"❌ Xatolik: {e}", parse_mode="HTML")
        await state.clear()


@router.message(CommandStart())
async def cmd_start(message: Message, db_user: User, state: FSMContext):
    await state.clear()
    lang = _lang(db_user)
    # Show language selection
    await message.answer(t("lang_prompt", lang), reply_markup=lang_select_kb(), parse_mode="HTML")


# ─── Navigation ──────────────────────────────────────────────────────────────

@router.message(F.text.contains("Bosh menyu") | F.text.contains("Main Menu") | F.text.contains("\u0413\u043b\u0430\u0432\u043d\u043e\u0435 \u043c\u0435\u043d\u044e"))
async def msg_main_menu(message: Message, db_user: User, state: FSMContext):
    await state.clear()
    lang = _lang(db_user)
    await message.answer(build_welcome_text(db_user), reply_markup=main_menu_kb(lang), parse_mode="HTML")

@router.message(F.text.contains("Bekor qilish") | F.text.contains("Cancel") | F.text.contains("\u041e\u0442\u043c\u0435\u043d"))
async def msg_global_cancel(message: Message, db_user: User, state: FSMContext):
    await state.clear()
    lang = _lang(db_user)
    await message.answer(
        t("cancelled", lang) + "\n\n" + build_welcome_text(db_user),
        reply_markup=main_menu_kb(lang), parse_mode="HTML",
    )

@router.callback_query(F.data == "main_menu")
async def cb_main_menu(callback: CallbackQuery, db_user: User, state: FSMContext):
    await state.clear()
    lang = _lang(db_user)
    await callback.message.delete()
    await callback.message.answer(
        build_welcome_text(db_user), reply_markup=main_menu_kb(lang), parse_mode="HTML",
    )
    await callback.answer()


# ─── Account ─────────────────────────────────────────────────────────────────

@router.message(F.text.contains("Mening hisobim") | F.text.contains("My Account") | F.text.contains("\u041c\u043e\u0439 \u0430\u043a\u043a\u0430\u0443\u043d\u0442"))
async def msg_my_account(message: Message, db_user: User):
    await _show_account(message, db_user)

@router.callback_query(F.data == "my_account")
async def cb_my_account(callback: CallbackQuery, db_user: User):
    await _show_account(callback.message, db_user, is_callback=True)
    await callback.answer()

async def _show_account(msg: Message, db_user: User, is_callback=False):
    lang = _lang(db_user)
    text = t("account", lang,
             user_id=db_user.id,
             full_name=db_user.full_name or "\u2014",
             balance=format_price(db_user.balance or 0))
    if is_callback:
        await msg.edit_text(text, reply_markup=back_to_menu_kb(lang), parse_mode="HTML")
    else:
        await msg.answer(text, reply_markup=back_to_menu_kb(lang), parse_mode="HTML")


# ─── Commands ────────────────────────────────────────────────────────────────

@router.message(Command("stop"))
async def cmd_stop(message: Message, db_user: User, state: FSMContext):
    await state.clear()
    lang = _lang(db_user)
    await message.answer(t("stopped", lang), reply_markup=main_menu_kb(lang), parse_mode="HTML")

@router.message(Command("buy"))
async def cmd_buy(message: Message, state: FSMContext, db_user: User):
    from handlers.payment import payment_start
    await payment_start(message, state, db_user)

@router.message(Command("help"))
async def cmd_help(message: Message, db_user: User):
    await _show_help(message, db_user)

async def _show_help(msg: Message, db_user: User, is_callback=False):
    from config import ADMIN_USERNAME
    lang = _lang(db_user)
    text = t("help", lang, admin=ADMIN_USERNAME)
    if is_callback:
        await msg.edit_text(text, reply_markup=back_to_menu_kb(lang), parse_mode="HTML")
    else:
        await msg.answer(text, reply_markup=back_to_menu_kb(lang), parse_mode="HTML")

@router.callback_query(F.data == "help")
async def cb_help(callback: CallbackQuery, db_user: User):
    await _show_help(callback.message, db_user, is_callback=True)
    await callback.answer()


# ─── Referral system ────────────────────────────────────────────────────────

@router.message(F.text.contains("taklif qilish") | F.text.contains("Invite") | F.text.contains("\u041f\u0440\u0438\u0433\u043b\u0430\u0441\u0438\u0442\u044c"))
async def msg_referral(message: Message, db_user: User):
    await _show_referral(message, db_user)

@router.callback_query(F.data == "referral")
async def cb_referral(callback: CallbackQuery, db_user: User):
    await _show_referral(callback.message, db_user, is_callback=True)
    await callback.answer()

async def _show_referral(msg: Message, db_user: User, is_callback=False):
    lang = _lang(db_user)
    bot_info = await msg.bot.me()
    bot_username = bot_info.username
    ref_link = f"https://t.me/{bot_username}?start=ref_{db_user.id}"
    stats = await get_referral_stats(db_user.id)

    text = t("referral", lang,
             bonus_inviter=format_price(REFERRAL_BONUS_INVITER),
             bonus_invitee=format_price(REFERRAL_BONUS_INVITEE),
             count=stats["count"],
             earnings=format_price(stats["earnings"]),
             link=ref_link)

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=t("referral_btn", lang),
            switch_inline_query=t("referral_share", lang, link=ref_link),
        )],
        [InlineKeyboardButton(text=btn("back", lang), callback_data="main_menu")],
    ])

    if is_callback:
        await msg.edit_text(text, reply_markup=kb, parse_mode="HTML")
    else:
        await msg.answer(text, reply_markup=kb, parse_mode="HTML")


# ─── Rating system ───────────────────────────────────────────────────────────

def rating_kb(service_type: str) -> InlineKeyboardMarkup:
    """Build 1-5 star rating keyboard after document generation."""
    stars = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣"]
    buttons = [
        InlineKeyboardButton(text=stars[i], callback_data=f"rate:{service_type}:{i+1}")
        for i in range(5)
    ]
    return InlineKeyboardMarkup(inline_keyboard=[buttons])


@router.callback_query(F.data.startswith("rate:"))
async def handle_rating(callback: CallbackQuery, db_user: User):
    parts = callback.data.split(":")
    service_type = parts[1]
    rating = int(parts[2])
    lang = _lang(db_user)

    await save_rating(db_user.id, service_type, rating)

    thanks = {
        "uz": f"⭐ Rahmat! Siz {rating}/5 baho berdingiz.",
        "ru": f"⭐ Спасибо! Вы оценили на {rating}/5.",
        "en": f"⭐ Thanks! You rated {rating}/5."
    }
    await callback.message.edit_text(thanks.get(lang, thanks["uz"]))
    await callback.answer()
async def handle_rating(callback: CallbackQuery, db_user: User):
    parts = callback.data.split(":")
    service_type = parts[1]
    rating = int(parts[2])
    lang = _lang(db_user)

    await save_rating(db_user.id, service_type, rating)

    thanks = {
        "uz": f"⭐ Rahmat! Siz {rating}/5 baho berdingiz.",
        "ru": f"⭐ Спасибо! Вы оценили на {rating}/5.",
        "en": f"⭐ Thanks! You rated {rating}/5."
    }
    await callback.message.edit_text(thanks.get(lang, thanks["uz"]))
    await callback.answer()
