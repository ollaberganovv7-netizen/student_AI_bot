from __future__ import annotations
import asyncio, json, os, io, logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, BufferedInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.exceptions import TelegramBadRequest

from database.models import User
from database.db import create_request, deduct_balance, mark_free_used
from keyboards.main_kb import main_menu_kb, back_to_menu_kb
from keyboards.documents_kb import referat_summary_kb, doc_initial_settings_kb
from services.ai_service import generate_document_plan, generate_document_section
from services.docx_service import generate_docx
from services.template_loader import load_template_and_example
from utils.helpers import format_price, is_free_trial
from utils.i18n import t
from config import ADMIN_IDS, PRICING

logger = logging.getLogger(__name__)
router = Router()

def _lang(db_user) -> str:
    return (db_user.language or "uz") if db_user else "uz"

class UslubiyStates(StatesGroup):
    entering_topic    = State()
    entering_subject  = State()
    entering_university = State()
    choosing_mashgulot = State()
    choosing_pages    = State()
    reviewing_summary = State()


# ─── Keyboards ──────────────────────────────────────────────────────────────

def uslubiy_pages_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📄 20-25 bet - 13,000 so'm", callback_data="usl_pages:25:13000")],
        [InlineKeyboardButton(text="📄 25-30 bet - 16,000 so'm", callback_data="usl_pages:30:16000")],
        [InlineKeyboardButton(text="📄 30-35 bet - 19,000 so'm", callback_data="usl_pages:35:19000")],
        [InlineKeyboardButton(text="📄 35-40 bet - 22,000 so'm", callback_data="usl_pages:40:22000")],
        [InlineKeyboardButton(text="📄 40-50 bet - 25,000 so'm", callback_data="usl_pages:50:25000")],
        [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="main_menu")]
    ])


def uslubiy_mashgulot_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="1", callback_data="usl_mash:1"),
            InlineKeyboardButton(text="2", callback_data="usl_mash:2"),
            InlineKeyboardButton(text="3", callback_data="usl_mash:3"),
            InlineKeyboardButton(text="4", callback_data="usl_mash:4"),
        ],
        [
            InlineKeyboardButton(text="5", callback_data="usl_mash:5"),
            InlineKeyboardButton(text="6", callback_data="usl_mash:6"),
            InlineKeyboardButton(text="7", callback_data="usl_mash:7"),
            InlineKeyboardButton(text="8", callback_data="usl_mash:8"),
        ],
        [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="main_menu")]
    ])


# ─── Helpers ────────────────────────────────────────────────────────────────

async def _auto_generate_plan(state: FSMContext, topic: str, language: str):
    """Общая логика генерации плана (убирает дублирование)."""
    try:
        plan_data = await generate_document_plan(
            service_type="uslubiy",
            topic=topic,
            language=language,
            detail_level="pro"
        )
        plan = plan_data.get("plan", "")
        if plan:
            sections = [s.strip() for s in plan.split('\n') if s.strip()]
            await state.update_data(manual_plan=plan, num_chapters=len(sections))
    except Exception as e:
        logger.error(f"Error generating uslubiy plan: {e}")


async def safe_delete_message(bot, chat_id, message_id):
    """Безопасное удаление сообщения (без краша если уже удалено)."""
    try:
        await bot.delete_message(chat_id=chat_id, message_id=message_id)
    except TelegramBadRequest:
        pass


# ─── Step 1: Start ──────────────────────────────────────────────────────────

@router.message(F.text.in_(["📘 Uslubiy Ishlanma", "📘 Uslubiy ishlanma"]))
async def start_uslubiy_creation(message: Message, state: FSMContext, db_user: User):
    price_low  = PRICING.get("uslubiy_low", 15000)
    price_high = PRICING.get("uslubiy_high", 25000)
    is_admin = db_user.id in ADMIN_IDS
    balance = db_user.balance or 0
    balance_display = "🛡️ Admin (tekin)" if is_admin else format_price(balance)

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Davom etish", callback_data="usl_confirm")],
        [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="usl_cancel")]
    ])

    await state.update_data(service_type="uslubiy")
    await message.answer(
        "📘 <b>Uslubiy Ishlanma</b>\n"
        "<i>To'liq akademik uslubiy ishlanma — mundarija, kirish, boblar, xulosa, adabiyotlar</i>\n\n"
        "──────────\n"
        f"💰 <b>Narx:</b> {format_price(price_low)} — {format_price(price_high)}\n"
        f"   <i>(Sahifalar soniga qarab)</i>\n"
        f"👛 <b>Sizning balansingiz:</b> {balance_display}\n"
        "──────────\n",
        reply_markup=kb,
        parse_mode="HTML"
    )

@router.callback_query(F.data == "usl_confirm")
async def confirm_uslubiy(callback: CallbackQuery, state: FSMContext, db_user: User):
    await state.update_data(
        service_type="uslubiy",
        quality="pro",
        author=db_user.full_name or "Foydalanuvchi"
    )
    await state.set_state(UslubiyStates.reviewing_summary)
    await safe_delete_message(callback.bot, callback.message.chat.id, callback.message.message_id)
    await callback.message.answer(
        "\u2699\ufe0f <b>Kerakli sozlamalaringizni to'ldiring:</b>\n\n"
        "<i>Mavzu, fan, universitet, mashg'ulotlar soni va boshqa ma'lumotlarni kiriting.</i>",
        reply_markup=doc_initial_settings_kb(
            db_user.balance or 0, db_user.full_name or "", doc_type="uslubiy", lang=_lang(db_user)
        ),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "usl_cancel")
async def cancel_uslubiy(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(t("cancelled", "uz"))
    await callback.answer()


@router.callback_query(F.data == "usl_topup")
async def topup_from_uslubiy(callback: CallbackQuery, state: FSMContext):
    # Не очищаем state, чтобы пользователь мог вернуться после оплаты
    await callback.message.edit_text(
        t("pres_topup_hint", "uz"),
        parse_mode="HTML"
    )
    await callback.answer()


# ─── Step 2: Topic & Subject ────────────────────────────────────────────────

@router.message(UslubiyStates.entering_topic)
async def enter_topic(message: Message, state: FSMContext):
    await state.update_data(topic=message.text.strip())
    await state.set_state(UslubiyStates.entering_subject)
    await message.answer(
        "📚 <b>Fan nomini kiriting:</b>\n"
        "<i>(Masalan: Oliy matematika, Jahon tarixi)</i>",
        reply_markup=back_to_menu_kb(),
        parse_mode="HTML"
    )

@router.message(UslubiyStates.entering_subject)
async def enter_subject(message: Message, state: FSMContext):
    await state.update_data(subject=message.text.strip())
    await state.set_state(UslubiyStates.entering_university)
    await message.answer(
        "🏫 <b>Universitet nomini kiriting:</b>\n"
        "<i>(Masalan: O'zbekiston Milliy Universiteti)</i>",
        reply_markup=back_to_menu_kb(),
        parse_mode="HTML"
    )


@router.message(UslubiyStates.entering_university)
async def enter_university(message: Message, state: FSMContext):
    await state.update_data(university=message.text.strip())
    await state.set_state(UslubiyStates.choosing_mashgulot)
    await message.answer(
        "📊 <b>Qancha mashg'ulot borligini tanlang:</b>\n"
        "<i>(Har bir mashg'ulot uchun alohida materiallar va reja yoziladi)</i>",
        reply_markup=uslubiy_mashgulot_kb(),
        parse_mode="HTML"
    )

@router.callback_query(F.data.startswith("usl_mash:"), UslubiyStates.choosing_mashgulot)
async def choose_mashgulot(callback: CallbackQuery, state: FSMContext):
    _, mash_count = callback.data.split(":")
    await state.update_data(num_mashgulot=int(mash_count))
    await state.set_state(UslubiyStates.choosing_pages)
    await callback.message.edit_text(
        "📑 <b>Hujjat hajmini (sahifalar sonini) tanlang:</b>",
        reply_markup=uslubiy_pages_kb(),
        parse_mode="HTML"
    )
    await callback.answer()


# ─── Step 3: Pages ──────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("usl_pages:"), UslubiyStates.choosing_pages)
async def choose_pages(callback: CallbackQuery, state: FSMContext, db_user: User):
    _, pages, price = callback.data.split(":")
    await state.update_data(
        num_pages=int(pages), 
        price=int(price),
        quality="pro",
        author=db_user.full_name or "Foydalanuvchi"
    )

    # Auto-generate plan
    data = await state.get_data()
    topic = data.get("topic")

    wait_msg = await callback.message.edit_text(
        t("doc_preparing_plan", "uz"),
        parse_mode="HTML"
    )

    await _auto_generate_plan(state, topic, data.get("language", "uz"))

    await safe_delete_message(callback.bot, callback.message.chat.id, wait_msg.message_id)
    await state.set_state(UslubiyStates.reviewing_summary)
    await show_uslubiy_summary(callback.message, state, db_user)
    await callback.answer()


# ─── Summary & WebApp ───────────────────────────────────────────────────────

@router.message(F.web_app_data, UslubiyStates.reviewing_summary)
async def handle_uslubiy_webapp(message: Message, state: FSMContext, db_user: User):
    try:
        await safe_delete_message(message.bot, message.chat.id, message.message_id)
        data = json.loads(message.web_app_data.data)
        action = data.get("action", "")

        if action == "plan_update":
            await state.update_data(manual_plan=data.get("manual_plan"), num_chapters=data.get("num_chapters"))
            await show_uslubiy_summary(message, state, db_user)
        elif action == "content_update":
            await state.update_data(extra_info=data.get("extra_info"), tone=data.get("tone"))
            await show_uslubiy_summary(message, state, db_user)
        elif action == "full_settings":
            # Full settings from webapp
            ai_images = data.get("ai_images", 3)
            await state.update_data(
                topic=data.get("topic"),
                subject=data.get("subject"),
                university=data.get("university", ""),
                num_mashgulot=data.get("num_mashgulot", 2),
                author=data.get("author", db_user.full_name or "Foydalanuvchi"),
                language=data.get("language", "uz"),
                quality="pro",
                num_pages=data.get("num_pages", 25),
                price=data.get("price", 13000),
                ai_images_count=ai_images,
            )
            # Auto-generate plan
            topic = data.get("topic")
            wait_msg = await message.answer(
                t("doc_preparing_plan", "uz"),
                parse_mode="HTML"
            )
            await _auto_generate_plan(state, data.get("topic"), data.get("language", "uz"))
            await safe_delete_message(message.bot, message.chat.id, wait_msg.message_id)
            await show_uslubiy_summary(message, state, db_user)
        else:
            if "author" in data:
                await state.update_data(author=data.get("author"), language=data.get("language"))
            await show_uslubiy_summary(message, state, db_user)
    except json.JSONDecodeError:
        logger.error("Uslubiy WebApp: invalid JSON from web_app_data")
        await message.answer("⚠️ Ma'lumotlarni o'qishda xatolik. Qaytadan urinib ko'ring.")
    except Exception as e:
        logger.error(f"Uslubiy WebApp Error: {e}")
        await message.answer("⚠️ Kutilmagan xatolik yuz berdi.")


async def show_uslubiy_summary(message: Message, state: FSMContext, db_user: User):
    data = await state.get_data()
    topic = data.get("topic")
    subject = data.get("subject", "")
    university = data.get("university")
    pages = data.get("num_pages")
    price = data.get("price")
    author = data.get("author", "Foydalanuvchi")
    mash_count = data.get("num_mashgulot", 2)

    text = (
        f"📗 <b>Uslubiy Ishlanma</b>\n\n"
        f"📚 <b>Mavzu:</b> {topic}\n"
        f"📖 <b>Fan:</b> {subject}\n"
        f"🏫 <b>Universitet:</b> {university}\n"
        f"👤 <b>Muallif:</b> {author}\n"
        f"📊 <b>Mashg'ulotlar soni:</b> {mash_count} ta\n"
        f"📄 <b>Sahifalar:</b> ~{pages} bet\n"
        f"💰 <b>Narxi:</b> {format_price(price)}\n\n"
    )
    is_admin = db_user.id in ADMIN_IDS
    free_trial = is_free_trial(db_user) and not is_admin
    balance = db_user.balance or 0
    
    if is_admin or free_trial or balance >= price:
        text += f"<i>Reja yoki ma'lumotlarni o'zgartirish uchun tugmalardan foydalaning.</i>"
    else:
        needed = price - balance
        from handlers.payment import get_cards_text
        text += (
            f"⚠️ <b>Sizning hisobingizda mablag' yetarli emas!</b>\n"
            f"🔴 Yetishmayapti: <b>{format_price(needed)}</b>\n\n"
            f"{get_cards_text()}\n"
            f"🧾 <i>Chekni to'g'ridan-to'g'ri shu yerga yuborishingiz mumkin.</i>"
        )


    summary_id = data.get("summary_msg_id")
    if summary_id:
        await safe_delete_message(message.bot, message.chat.id, summary_id)

    msg = await message.answer(text, reply_markup=referat_summary_kb(
        balance=db_user.balance or 0, price=price, name=db_user.full_name or "", 
        topic=topic, doc_type="uslubiy", quality="pro", lang=_lang(db_user),
        is_admin=is_admin
    ), parse_mode="HTML")
    await state.update_data(summary_msg_id=msg.message_id)


# ─── Generation ─────────────────────────────────────────────────────────────

@router.message(F.text == "🚀 Yaratish", UslubiyStates.reviewing_summary)
async def generate_uslubiy(message: Message, state: FSMContext, db_user: User):
    data = await state.get_data()
    price = data.get("price", 13000)
    topic = data.get("topic")
    pages = data.get("num_pages")
    university = data.get("university", "")

    is_admin = db_user.id in ADMIN_IDS
    free_trial = is_free_trial(db_user) and not is_admin
    if free_trial:
        price = 0
    if not is_admin and not free_trial and (db_user.balance or 0) < price:
        await message.answer(t("pres_balance_low", "uz", needed=format_price(price - (db_user.balance or 0))), reply_markup=main_menu_kb(), parse_mode="HTML")
        return

    cancel_flag = {"cancelled": False}
    await state.update_data(cancel_flag=cancel_flag)

    cancel_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="usl_cancel_gen")]
    ])

    wait_msg = await message.answer(
        f"⏳ <b>Uslubiy ishlanma yaratilmoqda...</b>\n"
        f"📌 Mavzu: <i>{topic}</i>\n"
        f"📑 Hajmi: {pages} bet\n"
        f"🤖 AI professional uslubiy ishlanma yozmoqda...\n"
        f"⏳ <i>4-5 daqiqa kutib turing — sifatli natija uchun!</i>",
        parse_mode="HTML",
        reply_markup=cancel_kb
    )

    def is_cancelled():
        return cancel_flag.get("cancelled", False)

    try:
        from services.ai_service import _call_ai as _ai_call
        template_context = load_template_and_example("uslubiy")

        async def call_ai(msgs, temp=0.7, max_tok=4000):
            return await _ai_call(msgs, max_tokens=max_tok, temperature=temp)

        words_target = pages * 260
        lang = data.get("language", "uz")

        system_prompt = (
            "Sen professional harbiy-akademik uslubiy ishlanma yozuvchisisiz. "
            "USLUBIY ISHLANMA — bu mashg'ulotlarni rejalashtirish va o'tkazish uchun "
            "pedagog xodimlarning asosiy o'quv-uslubiy vositasi. "
            "Matnni O'zbek tilida (lotin alifbosi) yoz. "
            "Markdown belgilarini (**, #, ```) ISHLATMA. Faqat oddiy matn yoz. "
            "Sarlavhalarni KATTA HARFLARDA yoz.\n\n"
            f"STRUKTURANI AYNAN QUYIDAGI TARTIBDA YOZ:\n{template_context}\n"
        )

        num_mashgulot = data.get("num_mashgulot", 2)
        num_questions = 3  # Fiks qilingan, foydalanuvchi tanlamaydi
        
        # Calculate words target proportionally
        total_words = pages * 250
        words_per_mashgulot = max(800, total_words // num_mashgulot)
        base_w = words_per_mashgulot // 10
        
        # 1. Umumiy qism
        uslubiy_sections = [
            ("O'QUV MAQSADLAR VA TASHKILIY KO'RSATMALAR", 
             f"Mavzu: {topic}\n\nQAT'IY QOIDA: '1. MAVZU' yoki shunga o'xshash sarlavha qo'yma! Faqat quyidagilarni yoz:\n"
             f"- Mavzu nomini KATTA HARFLARDA yoz.\n"
             f"- To'g'ridan-to'g'ri 'O'QUV MAQSADLAR:' deb boshla va {num_questions} ta o'quv maqsadini aniq qilib yoz.\n"
             "- Keyin to'g'ridan-to'g'ri tashkiliy ko'rsatmalar, Bumerang, Klaster kabi metodlarni batafsil tushuntir.\n"
             f"- Jami kamida {int(base_w * 1.5)} so'z")
        ]

        # 2. Mashg'ulotlar tsikli
        for i in range(1, num_mashgulot + 1):
            is_seminar = (i == num_mashgulot and num_mashgulot > 1)
            mash_type = "Seminar mashg'ulot" if is_seminar else "Guruh mashg'ulot"
            
            if i == 1:
                jadval_qismi = (
                    f"QAT'IY QOIDA: Sarlavha yozma! To'g'ridan-to'g'ri 'MASHG'ULOTLARGA AJRATILGAN O'QUV SOATLARI' jadvalidan boshla.\n"
                    f"- Jadvalda jami {num_mashgulot} ta mashg'ulot ro'yxatini va vaqt taqsimotini yoz.\n"
                )
            else:
                jadval_qismi = ""
            
            uslubiy_sections.append(
                (f"{i}-MASHG'ULOT PASPORTI",
                 f"Mavzu: {topic}\n\n{jadval_qismi}"
                 f"QAT'IY QOIDA: 'Mashg'ulot pasporti' yoki shunga o'xshash sarlavha YOZMA!\n"
                 f"To'g'ridan-to'g'ri quyidagi qatorlarni yozishdan boshla:\n"
                 f"Mashg'ulot o'tkazish vaqti: ...\n"
                 f"Mashg'ulot joyi: ...\n"
                 f"Mashg'ulotning asosiy uslubi: {mash_type}\n"
                 f"O'quv-uslubiy vositalar: ...\n"
                 f"Foydalanilgan adabiyotlar:\n"
                 f"- Jami kamida 150 so'z")
            )

            uslubiy_sections.append(
                (f"{i}-MASHG'ULOT O'TKAZISH USLUBLARI",
                 f"Mavzu: {topic} ({i}-mashg'ulot)\n\nQAT'IY QOIDA: Hech qanday sarlavha yozma!\n"
                 f"To'g'ridan-to'g'ri 'O'QUV SAVOLLARINING KETMA-KETLIGI' jadvalidan boshla (Kirish, Asosiy ({num_questions} ta savol), Yakuniy qismlar uchun).\n"
                 "- Keyin mashg'ulot o'tkazishning asosiy uslublari (tayyorlash, ma'ruza) haqida yoz.\n"
                 f"- Jami kamida {int(base_w * 1.0)} so'z")
            )

            uslubiy_sections.append(
                (f"{i}-MASHG'ULOT USLUBIY KO'RSATMALAR",
                 f"Mavzu: {topic} ({i}-mashg'ulot)\n\nQAT'IY QOIDA: Hech qanday sarlavha yozma!\n"
                 f"To'g'ridan-to'g'ri har bir o'quv savoli uchun o'qituvchiga uslubiy ko'rsatmalar yozishdan boshla.\n"
                 "- Qaysi interaktiv metodlar qo'llanilishini batafsil tushuntir.\n"
                 f"- Jami kamida {int(base_w * 1.5)} so'z")
            )

            uslubiy_sections.append(
                (f"{i}-MASHG'ULOT YAKUNI",
                 f"Mavzu: {topic} ({i}-mashg'ulot)\n\nQAT'IY QOIDA: Hech qanday sarlavha yozma!\n"
                 f"To'g'ridan-to'g'ri mashg'ulot yakuni (tahlili) qanday o'tishini yozishdan boshla.\n"
                 "- Yakunlash tartibi, baholash va mustaqil o'rganish uchun kamida 15 ta kichik savollar ro'yxatini yoz.\n"
                 f"- Jami kamida {int(base_w * 1.0)} so'z")
            )

            if not is_seminar:
                half_q = max(1, num_questions // 2)
                q1_range = f"1 dan {half_q} gacha"
                q2_range = f"{half_q + 1} dan {num_questions} gacha" if half_q < num_questions else "qolgan barcha"
                
                uslubiy_sections.append(
                    (f"{i}-MASHG'ULOT MATERIALLARI - 1",
                     f"Mavzu: {topic} ({i}-mashg'ulot)\n\nQAT'IY QOIDA: Hech qanday sarlavha yozma!\n"
                     f"To'g'ridan-to'g'ri {q1_range} bo'lgan o'quv savollari bo'yicha BATAFSIL akademik matnni yozishdan boshla.\n"
                     "- Barcha nazariya, tasnif jadvallarini yoz.\n"
                     "- Rasmlar uchun pleysholderlar qo'y: [ 🖼️ SHU YERGA RASM JOYLANG: <tavsif> ]\n"
                     f"- Jami kamida {int(base_w * 2.5)} so'z")
                )
                uslubiy_sections.append(
                    (f"{i}-MASHG'ULOT MATERIALLARI - 2",
                     f"Mavzu: {topic} ({i}-mashg'ulot)\n\nQAT'IY QOIDA: Hech qanday sarlavha yozma!\n"
                     f"To'g'ridan-to'g'ri {q2_range} o'quv savollari bo'yicha BATAFSIL akademik matnni yozishdan boshla.\n"
                     "- Har bir qism uchun rasm pleysholderini qo'y: [ 🖼️ SHU YERGA RASM JOYLANG: <tavsif> ]\n"
                     f"- Jami kamida {int(base_w * 2.5)} so'z")
                )
            else:
                uslubiy_sections.append(
                    ("SEMINAR REJASI",
                     f"Mavzu: {topic}\n\nQAT'IY QOIDA: Faqat 'SEMINAR REJASI' deb sarlavha yoz va davom et.\n"
                     f"Tashkilot nomi, fan nomi, vaqt, {num_questions} ta o'quv savollar ro'yxati, referat topshirig'i, adabiyotlar va tayyorgarlik uchun uslubiy ko'rsatmalar.\n"
                     f"- Jami kamida {int(base_w * 2.5)} so'z")
                )

        full_content = []
        total = len(uslubiy_sections)

        for i, (section_name, prompt) in enumerate(uslubiy_sections, 1):
            if is_cancelled():
                await state.clear()
                return

            filled = int(((i - 1) / total) * 10)
            bar = "🟩" * filled + "⬜" * (10 - filled)
            try:
                await wait_msg.edit_text(
                    f"🤖 <b>AI uslubiy ishlanma yozmoqda...</b>\n\n"
                    f"📊 <b>{i-1}/{total}</b> bo'lim tayyor\n"
                    f"{bar}\n\n"
                    f"⏭ <b>Hozir yozilmoqda:</b> <i>{section_name}</i>\n\n"
                    f"<i>Professional uslubiy ishlanma uchun sabr qiling...</i>",
                    parse_mode="HTML",
                    reply_markup=cancel_kb
                )
            except TelegramBadRequest:
                pass

            text = await call_ai(
                [{"role": "system", "content": system_prompt},
                 {"role": "user", "content": prompt}],
                temp=0.7,
                max_tok=8000
            )
            full_content.append(text)

        # Done
        try:
            await wait_msg.edit_text(
                f"✅ <b>Barcha {total} ta bo'lim tayyor!</b>\n\n"
                f"{'🟩' * total}\n\n"
                f"⏳ <b>DOCX fayl yaratilmoqda...</b>",
                parse_mode="HTML"
            )
        except TelegramBadRequest:
            pass

        content = "\n\n".join(full_content)
        plan_for_mundarija = ""  # Uslubiy uchun mundarija kerak emas

        docx_bytes = await asyncio.get_event_loop().run_in_executor(
            None,
            generate_docx,
            "uslubiy",
            topic,
            content,
            data.get("author", "Foydalanuvchi"),
            plan_for_mundarija,
            {"university": university, "subject": data.get("subject", "")}
        )

        if free_trial:
            await mark_free_used(db_user.id)
        elif db_user.id not in ADMIN_IDS:
            await deduct_balance(db_user.id, price)

        await create_request(user_id=db_user.id, service_type="uslubiy", topic=topic, options={"pages": pages})

        await wait_msg.delete()
        file_name = f"Uslubiy_ishlanma_{topic[:20]}.docx"
        lang = _lang(db_user)
        await message.answer_document(
            document=BufferedInputFile(docx_bytes, filename=file_name),
            caption=t("doc_done", lang, topic=topic, pages=pages, price=format_price(price)),
            parse_mode="HTML"
        )
        # Ask for rating
        from handlers.start import rating_kb
        rate_text = {"uz": "Iltimos, ishimizni baholang:", "ru": "Пожалуйста, оцените нашу работу:", "en": "Please rate our work:"}
        await message.answer(rate_text.get(lang, rate_text["uz"]), reply_markup=rating_kb("uslubiy"))
        await state.clear()
    except Exception as e:
        logger.error(f"Uslubiy generation error: {e}")
        await message.answer(t("pres_error", "uz", error=str(e)), parse_mode="HTML")
        await state.clear()


@router.callback_query(F.data == "usl_cancel_gen")
async def cancel_uslubiy_gen(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    cancel_flag = data.get("cancel_flag")
    if cancel_flag and isinstance(cancel_flag, dict):
        cancel_flag["cancelled"] = True
    await state.clear()
    await callback.message.edit_text(t("doc_cancel_gen", "uz"))
    await callback.answer()


@router.message(F.text == "❌ Bekor qilish", UslubiyStates.reviewing_summary)
async def cancel_uslubiy_summary(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(t("cancelled", "uz"), reply_markup=main_menu_kb())
