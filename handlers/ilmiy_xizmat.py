from __future__ import annotations
"""
handlers/ilmiy_xizmat.py

8 ta yangi xizmat tugmalarini ushlab oladi va ularni to'g'ri
maqola/tezis generatoriga yo'naltiradi.

Tugmalar:
  Tezislar:
    📝 Ilmiy konferensiya tezisi      -> t_conf
    📝 Ilmiy maqola tezisi            -> t_art
    🎓 Dissertatsiya/BMI tezisi       -> t_diss
    📊 Ommabop / Tahliliy tezislar    -> t_pop

  Maqolalar:
    🔬 Ilmiy maqola                   -> a_sci
    🔭 Ilmiy-ommabop maqola           -> a_pop_sci
    📰 Ommabop maqola                 -> a_pop
    🎭 Badiiy-publitsistik maqola     -> a_art
"""

import os
import asyncio
import json
from aiogram import Router, F
from aiogram.types import (
    Message, CallbackQuery, BufferedInputFile,
    ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove,
    InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database.models import User
from database.db import create_request, deduct_balance, mark_free_used
from keyboards.main_kb import main_menu_kb
from services.ai_service import client, OPENAI_MODEL
from services.docx_service import generate_docx
from utils.helpers import format_price, is_free_trial
from utils.i18n import t, btn
from config import ADMIN_IDS, PRICING

router = Router()

# ─── FSM States ──────────────────────────────────────────────────────────────

class IlmiyXizmatStates(StatesGroup):
    waiting_topic   = State()   # Mavzu kutilmoqda
    waiting_pages   = State()   # Sahifa soni kutilmoqda
    waiting_author  = State()   # Muallif ismi kutilmoqda
    waiting_confirm = State()   # Tasdiqlash kutilmoqda
    generating      = State()   # AI yozmoqda


# ─── Service config ───────────────────────────────────────────────────────────

SERVICE_CONFIG = {
    # KEY: (icon, display_name_uz, pages_default, price_key, type)
    # type: "maqola" | "tezis"
    "a_sci": (
        "🔬", "Ilmiy maqola", 7, "maqola_7", "maqola",
        "OAK (Oliy attestatsiya komissiyasi) talablariga mos TO'LIQ ilmiy maqola",
    ),
    "a_pop_sci": (
        "🔭", "Ilmiy-ommabop maqola", 4, "maqola_5", "maqola",
        "Ilmiy-ommabop maqola (keng kitobxon uchun, storytelling uslubida)",
    ),
    "a_pop": (
        "📰", "Ommabop maqola", 4, "maqola_5", "maqola",
        "Ommabop publitsistik maqola (jurnalistik uslub, Lid va Faktlar bilan)",
    ),
    "a_art": (
        "🎭", "Badiiy-publitsistik maqola", 4, "maqola_5", "maqola",
        "Badiiy-publitsistik maqola (obrazlar, metaforalar, sub'ektiv pozitsiya)",
    ),
    "t_conf": (
        "📝", "Ilmiy konferensiya tezisi", 2, "tezis_2", "tezis",
        "OAK/Konferensiya talablariga mos ilmiy konferensiya tezisi",
    ),
    "t_art": (
        "📝", "Ilmiy maqola tezisi (Abstract)", 1, "tezis_1", "tezis",
        "OAK jurnali uchun maqola annotatsiyasi (Abstract/Tezis)",
    ),
    "t_diss": (
        "🎓", "Dissertatsiya / BMI tezisi", 3, "tezis_3", "tezis",
        "Dissertatsiya yoki Bitiruv malakaviy ishi tezisi (Avtoreferat uslubida)",
    ),
    "t_pop": (
        "📊", "Ommabop / Tahliliy tezislar", 2, "tezis_2", "tezis",
        "Ommabop yoki tahliliy tezis (Executive Summary / Key Takeaways uslubida)",
    ),
}

# ─── OAK-compliant AI prompts per service ────────────────────────────────────

def build_system_prompt(service_key: str, lang_instruction: str) -> str:
    """Har bir xizmat turi uchun OAK talablariga mos system prompt."""

    base = (
        "Sen professional O'zbekiston akademik muhitini yaxshi biluvchi mutaxassissen. "
        "Markdown belgilarini (**, ##, ```) ISHLATMA. Faqat oddiy matn yoz. "
        "QAT'IY TAQIQ: 'Mavzu:', 'Muallif:', sarlavhani qayta yozma.\n\n"
    )

    prompts = {
        "a_sci": base + (
            "OAK (Oliy attestatsiya komissiyasi) TALABLARI bo'yicha TO'LIQ ilmiy maqola yozasan.\n"
            "MAJBURIY TUZILISH (IMRAD standarti):\n"
            "1. Annotatsiya (100-250 so'z): Muammo -> Maqsad -> Metod -> Natija -> Xulosa\n"
            "2. Kalit so'zlar: 5-10 ta atama\n"
            "3. Kirish: Dolzarblik, o'rganilganlik darajasi, maqsad\n"
            "4. Tadqiqot metodologiyasi\n"
            "5. Natijalar va muhokama (jadvallar, tahlil)\n"
            "6. Xulosa\n"
            "7. Adabiyotlar (10-20 ta, APA/GOST)\n"
            "ILMIY YANGILIK bo'lishi shart. Plagiat qabul qilinmaydi (70-80% originallik).\n"
            "Har bir fikrga manba ko'rsatilsin [1, 12-b.] formatida.\n"
            f"Til: {lang_instruction}"
        ),
        "a_pop_sci": base + (
            "Ilmiy-ommabop maqola yozasan. MAQSAD: 'Tushuntirish va qiziqtirish'.\n"
            "QOIDALAR:\n"
            "- Murakkab atamalar ISHLATILMAYDI yoki darhol oddiy tilda izohlanadi\n"
            "- Hayotiy o'xshatishlar (analogiyalar) bilan tushuntir\n"
            "- Jonli va qiziqarli til — akademik 'quruq' stildan qoch\n"
            "- Diqqat tortuvchi sarlavha (savol ko'rinishida)\n"
            "- Lid (birinchi abzats): eng qiziqarli fakt yoki savol\n"
            "- Hikoya (storytelling) ko'rinishida faktlarni yetkazing\n"
            "- Mutaxassislar fikri va iqtiboslar matnga ishonch beradi\n"
            f"Hajm: 1000-3000 so'z. Til: {lang_instruction}"
        ),
        "a_pop": base + (
            "Ommabop (publitsistik) maqola yozasan. Formula: 'FAKT + TAHLIL + TA'SIRCHAN DIL'\n"
            "KLASSIK JURNALISTIKA STRUKTURASI:\n"
            "1. E'tiborni tortuvchi sarlavha (qisqa, mazmunli)\n"
            "2. Lid (2-3 jumla): Kim? Nima? Qachon? Qayerda? Nega?\n"
            "3. Asosiy qism: Faktlar, tahlil, mutaxassislar fikri\n"
            "4. Xulosa: Muallifning pozitsiyasi yoki o'quvchiga savol\n"
            "QOIDALAR:\n"
            "- Barcha faktlar tekshirilgan va aniq bo'lsin\n"
            "- Bahsli masalalarda ko'p tomonlama yondashuv\n"
            "- Muallifning hissiyoti va munosabatiga yo'l qo'yiladi\n"
            f"Til: {lang_instruction}"
        ),
        "a_art": base + (
            "Badiiy-publitsistik maqola yozasan (Esse/Ocherk uslubida).\n"
            "ASOSIY TAMOYILLAR:\n"
            "- Barcha faktlar REAL (to'qima yoki o'ylab topilgan voqea bo'lmasin)\n"
            "- Voqealar metaforalar, epitetlar, o'xshatishlar orqali JONLANTIRILADI\n"
            "- Muallif o'z munosabati, hissiyoti va kechinmalarini OCHIQ bildiradi\n"
            "- Til nihoyatda BOY, bo'yoqdor, ta'sirchan\n"
            "- Dialoglar va tasviriy detallardan keng foydalaniladi\n"
            "TUZILISH:\n"
            "1. Kirish: Tasviriy epizod (o'quvchini voqea joyiga olib kirish)\n"
            "2. Asosiy qism: Badiiy lavhalar, dialoglar, qahramon portreti\n"
            "3. Kulminatsiya va Xulosa: Falsafiy mushohada, ma'naviy chaqiriq\n"
            "MAQSAD: Kitobxonning QALBIGA ta'sir o'tkazish.\n"
            f"Til: {lang_instruction}"
        ),
        "t_conf": base + (
            "OAK va Konferensiya talablariga mos ILMIY KONFERENSIYA TEZISI yozasan.\n"
            "MUHIM: Tezis — to'liq maqola EMAS! Faqat muhim natijalar siqiq matnda.\n"
            "MAJBURIY STRUKTURA:\n"
            "UO'K: [tegishli kod]\n"
            "[SARLAVHA — 10-12 so'z]\n"
            "[Muallif F.I.Sh., Tashkilot, email]\n\n"
            "Dolzarbligi. [1-2 jumla]\n"
            "Tadqiqot maqsadi: [1 jumla]\n"
            "Metodlar. [1-2 jumla]\n"
            "Natijalar. [ASOSIY QISM — matnning 50-60%! Yangi natijalar, ko'rsatkichlar]\n"
            "Xulosa. [1-2 jumla]\n\n"
            "Adabiyotlar: [1-3 ta manba]\n\n"
            "QAT'IY TAQIQLAR:\n"
            "- Lirik chekinishlar, umumiy gaplar, darslik ta'riflari YO'Q\n"
            "- Faqat muallifning shaxsiy ilmiy NATIJASI aks etsin\n"
            "- Hajm: 1-3 sahifa (200-500 so'z)\n"
            f"Til: {lang_instruction}"
        ),
        "t_art": base + (
            "OAK jurnali uchun ilmiy maqola ANNOTATSIYASI (Abstract/Tezis) yozasan.\n"
            "FORMAT (100-250 so'z): Muammo -> Maqsad -> Metod -> Natija -> Xulosa\n"
            "Uchta tilda: O'zbek + Rus + Ingliz (har biri 100-250 so'z)\n"
            "Kalit so'zlar: 5-10 ta (uchta tilda)\n"
            "QAT'IY: Sarlavha, muallif ma'lumoti, keyin annotatsiya.\n"
            f"Til: {lang_instruction}"
        ),
        "t_diss": base + (
            "OAK talabi bo'yicha DISSERTATSIYA TEZISI (AVTOREFERAT) yozasan.\n"
            "3 ta ASOSIY BO'LIM:\n\n"
            "I. KIRISH (Dissertatsiya pasporti) — MAJBURIY PUNKTLAR:\n"
            "   - Tadqiqot mavzusining dolzarbligi va zarurati\n"
            "   - Respublika ustuvor yo'nalishlariga mosligi\n"
            "   - Tadqiqot maqsadi va vazifalari\n"
            "   - Tadqiqot obyekti va predmeti\n"
            "   - Tadqiqot metodologiyasi\n"
            "   - ILMIY YANGILIK (3-5 ta yangi g'oya, bullet point)\n"
            "   - Amaliy va nazariy ahamiyati\n"
            "   - Natijalarning joriy qilinishi\n"
            "   - Tuzilishi va hajmi\n\n"
            "II. ASOSIY MAZMUN:\n"
            "   - Har bir bob bo'yicha qisqartirilgan natijalar\n"
            "   - Har bob oxirida muallifning xulosasi\n\n"
            "III. XULOSA VA E'LON QILINGAN ISHLAR:\n"
            "   - 5-10 ta ilmiy-amaliy tavsiya\n"
            "   - Chop etilgan maqolalar ro'yxati\n\n"
            f"Hajm: PhD=24-32 sahifa, BMI=3-5 sahifa. Til: {lang_instruction}"
        ),
        "t_pop": base + (
            "Ommabop/Tahliliy tezis (Executive Summary / Key Takeaways) yozasan.\n"
            "MAQSAD: Qaror qabul qiluvchilar uchun tezkor, amaliy xulosalar.\n"
            "FORMAT:\n"
            "1. Asosiy muammo/mavzu (2-3 jumla)\n"
            "2. Tahlil natijalari (bullet points: 5-8 ta asosiy fikr)\n"
            "3. Muhim ko'rsatkichlar va faktlar (raqamlar bilan)\n"
            "4. Tavsiyalar (3-5 ta amaliy tavsiya)\n"
            "5. Xulosa (1-2 jumla)\n"
            "USLUB: Sodda, londa, raqam va faktlarga tayangan.\n"
            "Akademik jargonan qochiladi — biznes/siyosat tiliga moslashtiriladi.\n"
            f"Til: {lang_instruction}"
        ),
    }
    return prompts.get(service_key, base)


# ─── Entry handlers (button triggers) ─────────────────────────────────────────

async def _start_service(message: Message, state: FSMContext, db_user: User, service_key: str):
    """Umumiy entry point — barcha 8 xizmat uchun. WebApp orqali."""
    cfg = SERVICE_CONFIG[service_key]
    icon, name_uz, pages_default, price_key, svc_type, description = cfg

    lang = db_user.language or "uz"
    balance = db_user.balance or 0
    free_trial = is_free_trial(db_user) and db_user.id not in ADMIN_IDS

    price = PRICING.get(price_key, 3000)
    if free_trial:
        price = 0

    # State'ga xizmat ma'lumotlarini saqlash
    await state.update_data(
        service_key=service_key,
        service_name=name_uz,
        service_type=svc_type,
        pages_default=pages_default,
        price_key=price_key,
        lang=lang,
    )
    await state.set_state(IlmiyXizmatStates.waiting_topic)

    price_text = "🎁 BEPUL (birinchi marta)" if free_trial else f"💳 {format_price(price)}"

    # WebApp URL
    base_url = os.getenv("WEBAPP_URL", "https://arslon.github.io/student_bot/webapp/").split("?")[0]
    if not base_url.endswith("/"):
        base_url += "/"
    webapp_url = f"{base_url}ilmiy_xizmat.html?service={service_key}"

    await message.answer(
        f"{icon} <b>{name_uz}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"<i>{description}</i>\n\n"
        f"💰 <b>Narxi:</b> {price_text}\n"
        f"📊 <b>Balansingiz:</b> {format_price(balance)}\n\n"
        f"👇 <b>Quyidagi tugmani bosib ma'lumotlarni to'ldiring:</b>",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(
                    text=f"{icon} To'ldirish va Yaratish",
                    web_app=WebAppInfo(url=webapp_url)
                )],
                [KeyboardButton(text="❌ Bekor qilish")],
            ],
            resize_keyboard=True
        ),
        parse_mode="HTML"
    )


# ── 4 ta maqola tugmasi ──────────────────────────────────────────────────────

@router.message(F.text == "🔬 Ilmiy maqola")
async def start_a_sci(message: Message, state: FSMContext, db_user: User):
    await _start_service(message, state, db_user, "a_sci")

@router.message(F.text == "🔭 Ilmiy-ommabop maqola")
async def start_a_pop_sci(message: Message, state: FSMContext, db_user: User):
    await _start_service(message, state, db_user, "a_pop_sci")

@router.message(F.text == "📰 Ommabop maqola")
async def start_a_pop(message: Message, state: FSMContext, db_user: User):
    await _start_service(message, state, db_user, "a_pop")

@router.message(F.text == "🎭 Badiiy-publitsistik maqola")
async def start_a_art(message: Message, state: FSMContext, db_user: User):
    await _start_service(message, state, db_user, "a_art")


# ── 4 ta tezis tugmasi ───────────────────────────────────────────────────────

@router.message(F.text == "📝 Ilmiy konferensiya tezisi")
async def start_t_conf(message: Message, state: FSMContext, db_user: User):
    await _start_service(message, state, db_user, "t_conf")

@router.message(F.text == "📝 Ilmiy maqola tezisi")
async def start_t_art(message: Message, state: FSMContext, db_user: User):
    await _start_service(message, state, db_user, "t_art")

@router.message(F.text == "🎓 Dissertatsiya / Bitiruv malakaviy ishi tezisi")
async def start_t_diss(message: Message, state: FSMContext, db_user: User):
    await _start_service(message, state, db_user, "t_diss")

@router.message(F.text == "📊 Ommabop / Tahliliy tezislar")
async def start_t_pop(message: Message, state: FSMContext, db_user: User):
    await _start_service(message, state, db_user, "t_pop")


# ─── WebApp data handler ─────────────────────────────────────────────────────

@router.message(F.web_app_data, IlmiyXizmatStates.waiting_topic)
async def ilmiy_webapp_received(message: Message, state: FSMContext, db_user: User):
    """WebApp'dan ma'lumotlar keldi — darhol generatsiyani boshlash."""
    try:
        raw = message.web_app_data.data
        data_in = json.loads(raw)

        if data_in.get("type") != "ilmiy_xizmat":
            return  # boshqa webapp

        service_key = data_in.get("service_key")
        topic       = data_in.get("topic", "").strip()
        author      = data_in.get("author", "Tadqiqotchi").strip()
        university  = data_in.get("university", "").strip()
        lang        = data_in.get("language", "uz")
        pages       = int(data_in.get("pages", 5))

        if not topic or len(topic) < 5:
            await message.answer("❌ Mavzu juda qisqa. Qayta urinib ko'ring.")
            return

        cfg = SERVICE_CONFIG.get(service_key)
        if not cfg:
            await message.answer("❌ Noma'lum xizmat turi.")
            return

        icon, name_uz, pages_default, price_key, svc_type, _ = cfg

        await state.update_data(
            service_key=service_key,
            service_name=name_uz,
            service_type=svc_type,
            pages_default=pages,
            price_key=price_key,
            lang=lang,
            topic=topic,
            author=author,
            university=university,
        )
        await state.set_state(IlmiyXizmatStates.waiting_confirm)

        # To'g'ridan-to'g'ri generatsiyaga o'tish
        is_admin   = db_user.id in ADMIN_IDS
        free_trial = is_free_trial(db_user) and not is_admin
        price      = PRICING.get(price_key, 3000)
        if free_trial or is_admin:
            price = 0

        if not is_admin and not free_trial and (db_user.balance or 0) < price:
            await message.answer(
                f"❌ <b>Balans yetarli emas!</b>\n"
                f"Kerak: {format_price(price)}\n"
                f"Mavjud: {format_price(db_user.balance or 0)}\n\n"
                f"💳 /buy orqali to'ldiring.",
                reply_markup=main_menu_kb(lang),
                parse_mode="HTML"
            )
            await state.clear()
            return

        # Tasdiqlash xabari va generatsiyani boshlash
        cancel_flag = {"cancelled": False}
        await state.update_data(cancel_flag=cancel_flag)
        await state.set_state(IlmiyXizmatStates.generating)

        cancel_kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ To'xtatish", callback_data="ilmiy_stop")]
        ])

        wait_msg = await message.answer(
            f"⏳ <b>{name_uz} yaratilmoqda...</b>\n"
            f"📌 Mavzu: <i>{topic}</i>\n"
            f"👤 Muallif: {author}\n\n"
            f"🧠 AI yozmoqda... 3-5 daqiqa sabr qiling.\n"
            f"⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜",
            parse_mode="HTML",
            reply_markup=cancel_kb
        )

        # Tilga mos yo'riqnoma
        lang_map = {
            "uz": "O'zbek tilida (Lotin alifbosida)",
            "ru": "Rus tilida (На русском языке)",
            "en": "Ingliz tilida (In English)"
        }
        lang_instruction = lang_map.get(lang, "O'zbek tilida")
        system_prompt    = build_system_prompt(service_key, lang_instruction)

        await _run_generation(
            message=message,
            state=state,
            db_user=db_user,
            wait_msg=wait_msg,
            cancel_flag=cancel_flag,
            cancel_kb=cancel_kb,
            service_key=service_key,
            name_uz=name_uz,
            icon=icon,
            svc_type=svc_type,
            topic=topic,
            author=author,
            pages=pages,
            price_key=price_key,
            price=price,
            lang=lang,
            lang_instruction=lang_instruction,
            system_prompt=system_prompt,
            is_admin=is_admin,
            free_trial=free_trial,
        )

    except Exception as e:
        await state.clear()
        await message.answer(
            f"❌ Xatolik: <code>{str(e)[:200]}</code>",
            reply_markup=main_menu_kb(),
            parse_mode="HTML"
        )


# ─── Topic received (fallback uchun) ─────────────────────────────────────────
@router.message(IlmiyXizmatStates.waiting_topic, F.text != "❌ Bekor qilish")
async def got_topic(message: Message, state: FSMContext, db_user: User):
    topic = message.text.strip()
    if len(topic) < 5:
        await message.answer("⚠️ Mavzu juda qisqa. Iltimos, aniqroq yozing.")
        return

    data = await state.get_data()
    service_key = data["service_key"]
    cfg = SERVICE_CONFIG[service_key]
    icon, name_uz, pages_default, price_key, svc_type, description = cfg

    await state.update_data(topic=topic)
    await state.set_state(IlmiyXizmatStates.waiting_author)

    await message.answer(
        f"✅ <b>Mavzu qabul qilindi:</b>\n<i>{topic}</i>\n\n"
        f"👤 <b>Muallif ismini kiriting:</b>\n"
        f"<i>(Masalan: Karimov Bobur Rashidovich)</i>\n\n"
        f"<i>Yoki /skip yuboring (Muallif: Tadqiqotchi)</i>",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="/skip")],
                [KeyboardButton(text="❌ Bekor qilish")]
            ],
            resize_keyboard=True
        ),
        parse_mode="HTML"
    )


# ─── Author received ──────────────────────────────────────────────────────────

@router.message(IlmiyXizmatStates.waiting_author, F.text != "❌ Bekor qilish")
async def got_author(message: Message, state: FSMContext, db_user: User):
    author_text = message.text.strip()
    if author_text == "/skip":
        author = "Tadqiqotchi"
    else:
        author = author_text

    data = await state.get_data()
    service_key = data["service_key"]
    cfg = SERVICE_CONFIG[service_key]
    icon, name_uz, pages_default, price_key, svc_type, _ = cfg

    topic = data["topic"]
    lang = data.get("lang", "uz")
    free_trial = is_free_trial(db_user) and db_user.id not in ADMIN_IDS
    price = PRICING.get(price_key, 3000)
    if free_trial or db_user.id in ADMIN_IDS:
        price = 0

    await state.update_data(author=author)
    await state.set_state(IlmiyXizmatStates.waiting_confirm)

    price_text = "🎁 BEPUL" if (free_trial or db_user.id in ADMIN_IDS) else format_price(price)
    balance = db_user.balance or 0

    confirm_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"✅ Yaratishni boshlash", callback_data="ilmiy_start_gen")],
        [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="ilmiy_cancel")],
    ])

    await message.answer(
        f"📋 <b>Ma'lumotlarni tekshiring:</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"{icon} <b>Xizmat:</b> {name_uz}\n"
        f"📌 <b>Mavzu:</b> {topic}\n"
        f"👤 <b>Muallif:</b> {author}\n"
        f"📄 <b>Hajm:</b> ~{pages_default} sahifa\n"
        f"💰 <b>Narx:</b> {price_text}\n"
        f"💳 <b>Balans:</b> {format_price(balance)}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"✅ Tasdiqlaysizmi?",
        reply_markup=confirm_kb,
        parse_mode="HTML"
    )


# ─── Confirm / Cancel callbacks ───────────────────────────────────────────────

@router.callback_query(F.data == "ilmiy_cancel")
async def ilmiy_cancel_cb(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Bekor qilindi.")
    await callback.message.answer(
        "🏠 Bosh menyuga qaytdingiz.",
        reply_markup=main_menu_kb()
    )
    await callback.answer()


@router.callback_query(F.data == "ilmiy_start_gen", IlmiyXizmatStates.waiting_confirm)
async def ilmiy_start_gen(callback: CallbackQuery, state: FSMContext, db_user: User):
    await callback.answer()
    data = await state.get_data()
    service_key = data["service_key"]
    cfg = SERVICE_CONFIG[service_key]
    icon, name_uz, pages_default, price_key, svc_type, _ = cfg

    topic   = data["topic"]
    author  = data.get("author", "Tadqiqotchi")
    pages   = data.get("pages_default", pages_default)
    lang    = data.get("lang", "uz")
    is_admin   = db_user.id in ADMIN_IDS
    free_trial = is_free_trial(db_user) and not is_admin

    price = PRICING.get(price_key, 3000)
    if free_trial or is_admin:
        price = 0

    if not is_admin and not free_trial and (db_user.balance or 0) < price:
        await callback.message.edit_text(
            f"❌ <b>Balans yetarli emas!</b>\n"
            f"Kerak: {format_price(price)}\n"
            f"Mavjud: {format_price(db_user.balance or 0)}\n\n"
            f"💳 /buy orqali to'ldiring.",
            parse_mode="HTML"
        )
        await state.clear()
        return

    await state.set_state(IlmiyXizmatStates.generating)

    cancel_flag = {"cancelled": False}
    await state.update_data(cancel_flag=cancel_flag)

    cancel_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ To'xtatish", callback_data="ilmiy_stop")]
    ])

    wait_msg = await callback.message.edit_text(
        f"⏳ <b>{name_uz} yaratilmoqda...</b>\n"
        f"📌 Mavzu: <i>{topic}</i>\n\n"
        f"🧠 AI yozmoqda... 3-5 daqiqa sabr qiling.\n"
        f"⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜",
        parse_mode="HTML",
        reply_markup=cancel_kb
    )

    lang_map = {
        "uz": "O'zbek tilida (Lotin alifbosida)",
        "ru": "Rus tilida (На русском языке)",
        "en": "Ingliz tilida (In English)"
    }
    lang_instruction = lang_map.get(lang, "O'zbek tilida")

    system_prompt = build_system_prompt(service_key, lang_instruction)

    try:
        from services.ai_service import _call_ai

        # ── Tezis: oddiy bir qadamli generatsiya ─────────────────────────────
        if svc_type == "tezis":
            user_prompt = (
                f"Mavzu: {topic}\n"
                f"Muallif: {author}\n"
                f"Iltimos, yuqorida berilgan ko'rsatmalarga qat'iy amal qilib yoz."
            )
            content = await _call_ai(
                [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=3000,
                temperature=0.65
            )

            if cancel_flag.get("cancelled"):
                await state.clear()
                return

            try:
                await wait_msg.edit_text(
                    "📝 <b>Tezis yozildi!</b> Hujjat tayyorlanmoqda...",
                    parse_mode="HTML"
                )
            except:
                pass

            # DOCX yaratish
            title_line = f"{icon} {name_uz.upper()}"
            author_line = f"Muallif: {author}"
            full_text = f"{title_line}\n{author_line}\n\nMavzu: {topic}\n\n{content}"

            doc_buf = await asyncio.get_event_loop().run_in_executor(
                None, generate_docx, full_text, topic
            )
            doc_file = BufferedInputFile(doc_buf.read(), filename=f"{name_uz[:25]}.docx")

            # To'lov va yozuv
            if not is_admin:
                if free_trial:
                    await mark_free_used(db_user.id)
                elif price > 0:
                    await deduct_balance(db_user.id, price)

            if not is_admin:
                await create_request(
                    user_id=db_user.id,
                    service_type=service_key,
                    topic=topic,
                    pages=pages_default,
                    price=price
                )

            await wait_msg.delete()
            await callback.bot.send_document(
                chat_id=wait_msg.chat.id,
                document=doc_file,
                caption=(
                    f"✅ <b>{name_uz} tayyor!</b>\n"
                    f"📌 Mavzu: <i>{topic}</i>\n"
                    f"👤 Muallif: {author}\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n"
                    f"🌟 <b>USTOZ AI</b> — Professional akademik yordamchi"
                ),
                parse_mode="HTML",
                reply_markup=main_menu_kb(lang)
            )
            await state.clear()

        # ── Maqola: bo'limma-bo'lim generatsiya ──────────────────────────────
        else:
            total_words = pages * 250

            # Step 1: Reja tuzish
            try:
                await wait_msg.edit_text(
                    f"🧠 <b>Reja tuzilmoqda...</b>\n"
                    f"⬛⬜⬜⬜⬜⬜⬜⬜⬜⬜",
                    parse_mode="HTML", reply_markup=cancel_kb
                )
            except:
                pass

            plan_prompt = (
                f"Mavzu: {topic}\nTil: {lang_instruction}\n\n"
                "Ushbu mavzu uchun ilmiy maqola reja tuzing. FAQAT shu formatda:\n"
                "1. [Birinchi asosiy bo'lim]\n"
                "1.1. [Kichik bo'lim]\n"
                "1.2. [Kichik bo'lim]\n"
                "2. [Ikkinchi asosiy bo'lim]\n"
                "2.1. [Kichik bo'lim]\n"
                "2.2. [Kichik bo'lim]\n"
                "Boshqa hech narsa yozma."
            )
            plan_text = await _call_ai(
                [{"role": "user", "content": plan_prompt}],
                max_tokens=400, temperature=0.5
            )

            import re as re_mod
            plan_titles = {}
            for line in plan_text.split("\n"):
                line = line.strip()
                m = re_mod.match(r'^(\d+(?:\.\d+)?)\.?\s+(.+)', line)
                if m:
                    plan_titles[m.group(1)] = m.group(2).strip()

            if cancel_flag.get("cancelled"):
                await state.clear()
                return

            w = max(200, total_words // 7)

            sections = [
                ("annotatsiya", "ANNOTATSIYA",
                 f"'{topic}' maqolasi uchun annotatsiya yoz (100-250 so'z). "
                 f"Format: Muammo -> Maqsad -> Metod -> Natija -> Xulosa. "
                 f"Muallif: {author}. Sarlavha YOZMA."),
                ("kalit", "KALIT SO'ZLAR",
                 f"'{topic}' mavzusiga oid 7 ta kalit so'z yoz. "
                 f"Faqat vergul bilan ajratilgan so'zlar."),
                ("kirish", "KIRISH",
                 f"'{topic}' maqolasining KIRISH qismini yoz. "
                 f"Dolzarblik, o'rganilganlik, maqsad. {w} so'z. Sarlavha YOZMA."),
                ("1", f"1. {plan_titles.get('1','Asosiy bo\'lim')}",
                 f"'{topic}' bo'limi '{plan_titles.get('1','')}' uchun akademik matn. "
                 f"{w} so'z. Sarlavha YOZMA."),
                ("1.1", f"1.1. {plan_titles.get('1.1','Kichik bo\'lim')}",
                 f"'{topic}' bo'limi '{plan_titles.get('1.1','')}' uchun nazariy tahlil. "
                 f"{w} so'z. Sarlavha YOZMA."),
                ("1.2", f"1.2. {plan_titles.get('1.2','Kichik bo\'lim')}",
                 f"'{topic}' bo'limi '{plan_titles.get('1.2','')}' uchun empirik tahlil. "
                 f"{w} so'z. Sarlavha YOZMA."),
                ("2", f"2. {plan_titles.get('2','Ikkinchi bo\'lim')}",
                 f"'{topic}' bo'limi '{plan_titles.get('2','')}' uchun chuqur tahlil. "
                 f"{w} so'z. Sarlavha YOZMA."),
                ("2.1", f"2.1. {plan_titles.get('2.1','Kichik bo\'lim')}",
                 f"'{topic}' bo'limi '{plan_titles.get('2.1','')}' uchun amaliy misollar. "
                 f"{w} so'z. Sarlavha YOZMA."),
                ("2.2", f"2.2. {plan_titles.get('2.2','Kichik bo\'lim')}",
                 f"'{topic}' bo'limi '{plan_titles.get('2.2','')}' uchun taqqoslash. "
                 f"{w} so'z. Sarlavha YOZMA."),
                ("xulosa", "XULOSA",
                 f"'{topic}' maqolasining XULOSA va TAVSIYALAR qismini yoz. "
                 f"{max(100, w//2)} so'z. Sarlavha YOZMA."),
                ("adabiyotlar", "FOYDALANILGAN ADABIYOTLAR",
                 f"'{topic}' mavzusiga oid 10-15 ta REAL ilmiy manba ro'yxati. "
                 f"APA yoki GOST formatida. 4-5 ta O'zbek muallifi bo'lsin. "
                 f"Faqat ro'yxat — hech narsa qo'shma."),
            ]

            sections_content = {}
            total_sections = len(sections)
            progress_chars = ["⬛", "🟩"]

            for idx, (key, section_name, user_prompt_text) in enumerate(sections, 1):
                if cancel_flag.get("cancelled"):
                    await state.clear()
                    return

                progress = int((idx / total_sections) * 10)
                bar = "🟩" * progress + "⬜" * (10 - progress)
                try:
                    await wait_msg.edit_text(
                        f"✍️ <b>Yozilmoqda: {section_name}</b>\n"
                        f"{bar} {idx}/{total_sections}\n\n"
                        f"📌 <i>{topic}</i>",
                        parse_mode="HTML", reply_markup=cancel_kb
                    )
                except:
                    pass

                section_content = await _call_ai(
                    [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt_text}
                    ],
                    max_tokens=2500,
                    temperature=0.7
                )
                sections_content[key] = (section_name, section_content)
                await asyncio.sleep(0.3)

            if cancel_flag.get("cancelled"):
                await state.clear()
                return

            # Hujjatni yig'ish
            try:
                await wait_msg.edit_text(
                    "📄 <b>Hujjat tayyorlanmoqda...</b>\n🟩🟩🟩🟩🟩🟩🟩🟩🟩🟩",
                    parse_mode="HTML"
                )
            except:
                pass

            full_parts = [f"{icon} {name_uz.upper()}\n\nMavzu: {topic}\nMuallif: {author}\n"]
            for key, (sec_name, sec_content) in sections_content.items():
                full_parts.append(f"\n{sec_name}\n\n{sec_content}\n")
            full_text = "\n".join(full_parts)

            doc_buf = await asyncio.get_event_loop().run_in_executor(
                None, generate_docx, full_text, topic
            )
            doc_file = BufferedInputFile(doc_buf.read(), filename=f"{name_uz[:25]}.docx")

            # To'lov va yozuv
            if not is_admin:
                if free_trial:
                    await mark_free_used(db_user.id)
                elif price > 0:
                    await deduct_balance(db_user.id, price)

            if not is_admin:
                await create_request(
                    user_id=db_user.id,
                    service_type=service_key,
                    topic=topic,
                    pages=pages_default,
                    price=price
                )

            await wait_msg.delete()
            await callback.bot.send_document(
                chat_id=wait_msg.chat.id,
                document=doc_file,
                caption=(
                    f"✅ <b>{name_uz} tayyor!</b>\n"
                    f"📌 Mavzu: <i>{topic}</i>\n"
                    f"👤 Muallif: {author}\n"
                    f"📄 ~{pages} sahifa\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n"
                    f"🌟 <b>USTOZ AI</b> — Professional akademik yordamchi"
                ),
                parse_mode="HTML",
                reply_markup=main_menu_kb(lang)
            )
            await state.clear()

    except Exception as e:
        await state.clear()
        try:
            await wait_msg.edit_text(
                f"❌ <b>Xatolik yuz berdi:</b>\n<code>{str(e)[:200]}</code>\n\n"
                f"Qayta urinib ko'ring.",
                parse_mode="HTML"
            )
        except:
            pass
        await callback.bot.send_message(
            chat_id=wait_msg.chat.id,
            text="🏠 Bosh menyu:",
            reply_markup=main_menu_kb()
        )


# ─── Stop generation ──────────────────────────────────────────────────────────

@router.callback_query(F.data == "ilmiy_stop")
async def ilmiy_stop(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    cf = data.get("cancel_flag")
    if isinstance(cf, dict):
        cf["cancelled"] = True
    await state.clear()
    await callback.message.edit_text("🛑 <b>To'xtatildi.</b>", parse_mode="HTML")
    await callback.message.answer("🏠 Bosh menyu:", reply_markup=main_menu_kb())
    await callback.answer("To'xtatildi")


# ─── Cancel from keyboard ─────────────────────────────────────────────────────

@router.message(F.text == "❌ Bekor qilish", IlmiyXizmatStates.waiting_topic)
@router.message(F.text == "❌ Bekor qilish", IlmiyXizmatStates.waiting_author)
@router.message(F.text == "❌ Bekor qilish", IlmiyXizmatStates.waiting_confirm)
async def ilmiy_cancel_kb(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ Bekor qilindi.", reply_markup=main_menu_kb())
