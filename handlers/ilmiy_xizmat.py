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
import base64
import httpx
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

from services.docx_service import generate_docx
from utils.helpers import format_price, is_free_trial
from utils.i18n import t, btn
from config import ADMIN_IDS, PRICING

router = Router()

# ─── FSM States ──────────────────────────────────────────────────────────────

class IlmiyXizmatStates(StatesGroup):
    waiting_topic         = State()   # Mavzu kutilmoqda
    waiting_pages         = State()   # Sahifa soni kutilmoqda
    waiting_author        = State()   # Muallif ismi kutilmoqda
    waiting_confirm       = State()   # Tasdiqlash kutilmoqda
    waiting_payment_check = State()   # To'lov cheki kutilmoqda
    generating            = State()   # AI yozmoqda


# ─── Service config ───────────────────────────────────────────────────────────

SERVICE_CONFIG = {
    # KEY: (icon, display_name_uz, pages_default, price_key, type)
    # type: "maqola" | "tezis"
    "a_sci": (
        "🔬", "Ilmiy maqola", 8, "maqola_7", "maqola",
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
    """ACADEMIC PRO — Master AI Writer Engine. 8 ta xizmat uchun."""

    # ═══════════════════════════════════════════════
    # UMUMIY AKADEMIK PRO BAZA — barcha xizmatlarga
    # ═══════════════════════════════════════════════
    BASE = f"""Sen ACADEMIC PRO — yuqori darajadagi ilmiy, akademik, analitik va professional matnlar yaratishga ixtisoslashgan AI yozuvchisan.
Til: {lang_instruction}

## ASOSIY PRINSIP
"Avval aniqlik, keyin mazmun, keyin uslub."
Chiroyli yozish hech qachon faktlarning aniqligidan ustun turmaydi.

## TOPIC LOCK — MAVZU QULFI
Foydalanuvchi mavzuni berganidan keyin har bir paragraf, har bir dalil va har bir xulosa FAQAT asosiy mavzuga xizmat qilishi kerak.
TAQIQLANADI: mavzudan chetga chiqish | keraksiz tarixiy ma'lumot | mavzuga aloqasiz statistikalar | umumiy va mazmunsiz gaplar | matnni sun'iy uzaytirish | bir fikrni qayta takrorlash.

## ANTI-HALLUCINATION
- Bilmasang — O'YLAB TOPMA.
- Manba topilmasa: [MANBA TASDIQLANISHI KERAK] deb belgila.
- Tekshirilmagan statistika: [STATISTIKA TASDIQLANISHI KERAK] deb belgila.
- Mavjud bo'lmagan mualliflar, maqolalar, jurnallar, kitoblar va DOI larni HECH QACHON to'qib chiqarma.
- Agar manba haqiqatdan mavjud bo'lishiga ishonchsiz bo'lsang — uni qo'shma.

## CLAIM → EVIDENCE TIZIMI
Har bir muhim ilmiy da'vo: DA'VO → DALIL → MANBA → TAHLIL mantiqida qurilsin.
Faqat "tadqiqotlar shuni ko'rsatadiki..." deb yozish YETARLI EMAS — qaysi tadqiqotlar, kim, qachon, nima natija?

## SOURCE QUALITY ENGINE
A daraja (ustunlik): peer-reviewed maqolalar, nufuzli jurnallar, monografiyalar, xalqaro tashkilot hisobotlari.
B daraja: konferensiya materiallari, rasmiy statistik ma'lumotlar.
C daraja: ishonchli professional tashkilotlar, sifatli tahliliy nashrlar.
D daraja (ilmiy asosiy dalil sifatida ISHLATMA): bloglar, forumlar, noma'lum saytlar.

## HUMAN-LIKE ACADEMIC STYLE — ANTI-PLAGIAT
Matn robot tomonidan yozilgandek ko'rinmasin.
TAQIQLANGAN IBORALAR: "Shuni ta'kidlash joizki" | "Mazkur masala nihoyatda dolzarbdir" | "Yuqoridagilardan kelib chiqib" | "Bugungi kunda" | "O'z navbatida" | "Xulosa qilib aytganda" | "Ta'kidlash lozim" | "Alohida qayd etish kerak" | "Muhim jihati shundaki" | "Ushbu bo'limda".
Jumla uzunligini tabiiy ravishda o'zgartir. Har bir paragrafni turlicha boshlа. Fikr rivojlansin.

## XULOSA ENGINE
Xulosada: tadqiqot nimani ko'rsatdi | qaysi muammo aniqlandi | qanday ilmiy natija olindi | uning amaliy ahamiyati | keyingi tadqiqotlarga tavsiya.
TAQIQLANADI: maqolani qayta ko'chirish | "demak, mavzu juda muhim" bilan tugatish | umumiy gaplar.

## YAKUNIY SIFAT AUDITI (ichki, foydalanuvchiga ko'rsatma)
Matnni yuborishdan oldin: mavzudan chetga chiqmadimmi | faktlar ishonchlimi | manbalar real va mosmi | fikrlar bog'langanmi | da'volar asoslanganmi | takroriy gaplar bormi | akademik uslub saqlanganmi | kirish-asosiy qism-xulosa mosligi | haqiqiy natija chiqarilganmi | adabiyotlar matn bilan mosmi.

## MUHIM QOIDALAR
- Markdown (**, #, *, -) ISHLATMA — faqat toza matn.
- Bo'lim sarlavhalarini KATTA HARFLARDA yoz.
- Paragraflar orasida bo'sh qator qo'y.
- Foydalanuvchi bergan ism, kafedra, muassasa ma'lumotlarini o'zgartirishsiz ishlat."""

    # ═══════════════════════════════════════════════
    # HAR BIR XIZMAT UCHUN MAXSUS QO'SHIMCHA
    # ═══════════════════════════════════════════════

    SERVICE_EXTRA = {

        # 1. Ilmiy maqola (a_sci)
        "a_sci": """
## SEN ILMIY MAQOLA YOZUVCHISAN
Xalqaro VAK/Scopus/WoS talablariga mos IMRAD strukturasida yoz:
ANNOTATSIYA (3 tilda: o'zbek, ingliz, rus) → KALIT SO'ZLAR → KIRISH → ADABIYOTLAR SHARHI → METODOLOGIYA → ASOSIY QISM → NATIJALAR → MUHOKAMA → XULOSA → FOYDALANILGAN ADABIYOTLAR.
ANNOTATSIYA: dolzarblik | muammo | maqsad | metod | asosiy natija | ahamiyat (100-200 so'z har tilda).
KIRISH: katta muammo → aniq muammo → ilmiy bo'shliq → tadqiqot maqsadi → vazifalar.
ADABIYOTLAR SHARHI: manbalarni faqat sanab o'tma — taqqosla, farqini ko'rsat, qaysi masala o'rganilmagan ekanini aniqla.
NATIJALAR: aniq raqamlar, faktlar, jadvallar (agar bo'lsa).
MUHOKAMA: natijalarni mavjud ilmiy qarashlar bilan taqqosla.
Manba formati: APA yoki GOST (foydalanuvchi ko'rsatsa unga mos).
Faqat haqiqiy mavjud manbalarni foydalanilgan adabiyotlarga kirit.""",

        # 2. Ilmiy konferensiya tezisi (t_conf)
        "t_conf": """
## SEN ILMIY KONFERENSIYA TEZISI YOZUVCHISAN
Konferensiya tezisi — to'liq maqolaning ZICHI va QISQASI, lekin mustaqil ilmiy asar.
Struktura: SARLAVHA → MUALLIF → ANNOTATSIYA (ixtiyoriy) → KIRISH (dolzarblik, muammo) → ASOSIY FIKR (eng muhim natija/topilma) → DALILLAR (faqat eng kuchli) → XULOSA → MANBALAR (3-7 ta, faqat haqiqiylari).
Hajm odatda 1-3 sahifa (600-1500 so'z).
Har bir jumla foydali bo'lsin. Keraksiz kirish gaplarni olib tashla.
MUAMMO → MAQSAD → ASOSIY FIKR → DALIL → NATIJA → XULOSA mantiqida quril.""",

        # 3. Ilmiy maqola tezisi (t_art)
        "t_art": """
## SEN ILMIY MAQOLA TEZISI YOZUVCHISAN
Tezis — maqolaning oddiy qisqartirilgan shakli emas. U mustaqil ilmiy fikrni zich ifodalaydi.
Struktura: MUAMMO → MAQSAD → ASOSIY FIKR → DALIL → NATIJA → XULOSA.
Har bir jumla kerakli. Har bir da'vo — dalil bilan.
Ortiqcha kirish so'zlar, umumiy gaplar, muqaddima yoqma.
Manbalar: faqat eng muhim 3-5 ta, haqiqiy mavjud bo'lganlari.""",

        # 4. Ilmiy-ommabop maqola (a_pop_sci)
        "a_pop_sci": """
## SEN ILMIY-OMMABOP MAQOLA YOZUVCHISAN
Ilmiy-ommabop maqola — murakkab ilmiy fikrni ODDIY va QIZIQARLI tarzda tushuntiradi.
O'quvchi: ilmiy bilimga ega bo'lmagan keng jamiyat.
Uslub: rasmiy bo'lmagan, jonli, ammo aniq va faktlarga asoslangan.
Tuzilma: QIZIQARLI KIRISH (misol, voqea, savol) → MUAMMO TUSHUNTIRISH → ILMIY FAKT (sodda tilda) → AMALIY AHAMIYAT → XULOSA.
TAQIQLANADI: ilmiy jargon (zarur bo'lsa — tushuntirib yoz) | quruq faktlar ro'yxati | o'quvchini zeriktiradigan uslub.
Manbalar: mavjud va ishonchli, oddiy tilda izohla.""",

        # 5. Dissertatsiya / Bitiruv malakaviy ishi tezisi (t_diss)
        "t_diss": """
## SEN DISSERTATSIYA / BITIRUV MALAKAVIY ISHI TEZISI YOZUVCHISAN
Bu — dissertatsiya yoki BMIning ilmiy konferensiya yoki mudofaa uchun tayyorlangan tezisi.
Struktura: SARLAVHA → MUALLIF MA'LUMOTLARI → ILMIY RAHBAR → ANNOTATSIYA → KIRISH (dolzarblik, yangilik, maqsad) → ASOSIY NATIJALAR (tadqiqot topilmalari) → ILMIY YANGILIK → AMALIY AHAMIYAT → XULOSA → MANBALAR.
Ilmiy yangilik qismida: "Birinchi marta..." yoki "... yangi yondashuv taklif etildi" kabi aniq yangilik ifodalansin.
Amaliy ahamiyatda: natijalari qayerda, qanday qo'llanishi mumkin.
Uslub: rasmiy, ilmiy, aniq.""",

        # 6. Ommabop maqola (pop)
        "a_pop": """
## SEN OMMABOP MAQOLA YOZUVCHISAN
Ommabop maqola — keng auditoriya uchun yoziladigan, faktlarga asoslangan, qulay o'qiladigan matn.
Uslub: jonli, tushunarli, ilmiy jargonsiz, ammo aniq.
Tuzilma: DIQQATNI TORTUVCHI KIRISH → ASOSIY MUAMMO → FAKTLAR VA MISOLLAR → TAHLIL → XULOSA.
TAQIQLANADI: akademik og'ir uslub | faqat faktlar sanab o'tish | boring kirish gaplar.
Manbalar: ishonchli va tekshirilgan, ammo ommabop tarzda ko'rsat.""",

        # 7. Ommabop / Tahliliy tezislar (t_pop)
        "t_pop": """
## SEN OMMABOP/TAHLILIY TEZIS YOZUVCHISAN
Bu tezis ommabop yoki tahliliy maqolaning asosiy fikrlarini zich ifodalaydi.
Uslub: tushunарli, qulay, ammo tahliliy chuqurlikka ega.
Mantiq: MUAMMO → ASOSIY FIKR → DALILLAR → XULOSA.
Fakt → sabab → oqibat → taqqoslash → muammo → yechim → xulosa zanjiriga amal qil.
O'quvchi savolga javob olsin: "Nima sabab bo'ldi, bu nimaga olib keladi, qanday xulosa?"
Qisqa, aniq, foydali. Har bir jumla — maqsadli.""",

        # 8. Badiiy-publitsistik maqola (a_art)
        "a_art": """
## SEN BADIIY-PUBLITSISTIK MAQOLA YOZUVCHISAN
Badiiy-publitsistik maqola — badiiy uslub va publitsistik tahlilni birlashtiradi.
Uslub: jonli, obrazli, emotsional, ammo faktlarga asoslangan.
Tuzilma: OBRAZLI KIRISH (metafora, savol, voqea) → MUAMMO TAHLILI → DALILLAR (badiiy tarzda) → HISSIY XULOSA.
TAQIQLANADI: quruq faktlar ro'yxati | akademik jargon | emotsiyasiz tasvir.
Manbalar: faktlarni tasdiqlash uchun ishlat, ammo badiiy uslubda yo'nalтир.
O'quvchi maqolani o'qib hissiyot ham, bilim ham olishi kerak.""",
    }

    # Noma'lum service_key bo'lsa ham default bilan ishlaydi
    extra = SERVICE_EXTRA.get(service_key, """
## SEN AKADEMIK MATN YOZUVCHISAN
Mavzuni chuqur tahlil qil, faktlarga asoslan, ilmiy uslubda yoz.
Tuzilma: KIRISH → ASOSIY QISM → XULOSA → FOYDALANILGAN ADABIYOTLAR.""")

    return BASE + extra

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

    if free_trial:
        price_text = "🎁 BEPUL (birinchi marta)"
    else:
        # User requested 5000 - 15000 for this
        if "maqola" in svc_type:
            price_text = "💳 5 000 - 15 000 so'm (sahifa soniga qarab)"
        else:
            price_text = f"💳 {format_price(price)} so'mdan boshlab"

    # WebApp URL - maqola_settings.html bilan bir xil format (root papka)
    base_url = os.getenv("WEBAPP_URL", "https://ollaberganovv7-netizen.github.io/student_AI_bot").split("?")[0]
    if not base_url.endswith("/"):
        base_url += "/"
    import time as _time
    webapp_url = f"{base_url}ilmiy_xizmat.html?service={service_key}&t={int(_time.time())}"

    await message.answer(
        f"{icon} <b>{name_uz}</b>\n\n"
        f"<i>{description}</i>\n\n"
        f"💰 <b>Narxi:</b> {price_text}\n"
        f"📊 <b>Balansingiz:</b> {format_price(balance)}\n\n"
        f"👇 <b>Ma'lumotlarni to'ldirish uchun pastdagi tugmani bosing:</b>",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(
                    text=f"{icon} Ma'lumotlarni to'ldirish",
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
            keywords=data_in.get("keywords", "").strip(),
            research_details=data_in.get("research_details", "").strip()
        )
        await state.set_state(IlmiyXizmatStates.waiting_confirm)

        # To'lov tekshiruvi
        is_admin = False # Hozircha admin tekshiruvini o'chirib turamiz, test qilishlari uchun
        free_trial = is_free_trial(db_user)
        
        # Dynamic pricing based on pages (matching WebApp)
        if service_key == "a_sci":
            min_p = 8
            base = 5000
            step = 1400
        elif service_key in ["a_pop_sci", "a_pop", "a_art"]:
            min_p = 3
            base = 3000
            step = 500
        elif service_key in ["t_conf", "t_pop"]:
            min_p = 1
            base = 2000
            step = 500
        elif service_key == "t_art":
            min_p = 1
            base = 1500
            step = 500
        elif service_key == "t_diss":
            min_p = 2
            base = 3500
            step = 500
        else:
            min_p = 1
            base = 3000
            step = 500
            
        calc_price = base + max(0, (pages - min_p)) * step
        price = round(calc_price / 1000) * 1000
        
        if free_trial:
            price = 0

        # Agar yetarli balans bo'lsa yoki tekin bo'lsa, to'g'ridan-to'g'ri yaratish
        if (db_user.balance or 0) >= price or price == 0:
            if price > 0:
                await deduct_balance(db_user.id, price)
                
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

            lang_map = {
                "uz": "O'zbek tilida (Lotin alifbosida)",
                "ru": "Rus tilida (На русском языке)",
                "en": "Ingliz tilida (In English)"
            }
            lang_instruction = lang_map.get(lang, "O'zbek tilida")
            system_prompt = build_system_prompt(service_key, lang_instruction)

            await _run_generation(
                message=message, state=state, db_user=db_user,
                wait_msg=wait_msg, cancel_flag=cancel_flag, cancel_kb=cancel_kb,
                service_key=service_key, name_uz=name_uz, icon=icon,
                svc_type=svc_type, topic=topic, author=author, pages=pages,
                price_key=price_key, price=price, lang=lang,
                lang_instruction=lang_instruction, system_prompt=system_prompt,
                is_admin=is_admin, free_trial=free_trial,
            )
            return

        # ── Balans yetarli bo'lmasa To'lov tugmasi chiqadi ─────────────────
        from config import CARDS
        await state.update_data(
            pending_price=price,
            pending_service_key=service_key,
            pending_name_uz=name_uz,
            pending_icon=icon,
            pending_svc_type=svc_type,
            pending_topic=topic,
            pending_author=author,
            pending_pages=pages,
            pending_price_key=price_key,
            pending_lang=lang,
        )
        await state.set_state(IlmiyXizmatStates.waiting_payment_check)

        # Kartalar matni
        cards_text = ""
        for i, card in enumerate(CARDS[:2], 1):
            cards_text += f"\n🏦 <b>{i}-Karta:</b> <code>{card['number']}</code>\n👤 <b>Ega:</b> {card['holder']}\n"

        price_fmt = f"{price:,}".replace(",", " ")
        pay_kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💳 Hisobni to'ldirish (Chek yuborish)", callback_data="ilmiy_pay_upload")]
        ])

        await message.answer(
            f"💰 <b>To'lov ma'lumotlari</b>\n\n"
            f"📌 Xizmat: <b>{icon} {name_uz}</b>\n"
            f"📄 Sahifalar: <b>{pages} bet</b>\n"
            f"💵 To'lov miqdori: <b>{price_fmt} so'm</b>\n\n"
            f"Quyidagi kartalardan biriga o'tkazing:{cards_text}\n"
            f"✅ To'lovni amalga oshirgach, <b>to'lov cheki (skrinshotini)</b> yuboring.",
            parse_mode="HTML",
            reply_markup=pay_kb
        )

    except Exception as e:
        await state.clear()
        await message.answer(
            f"❌ Xatolik: <code>{str(e)[:200]}</code>",
            reply_markup=main_menu_kb(),
            parse_mode="HTML"
        )




# ─── To'lov cheki yutish handler ─────────────────────────────────────────────

@router.callback_query(F.data == "ilmiy_pay_upload", IlmiyXizmatStates.waiting_payment_check)
async def ilmiy_pay_upload(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(
        "📸 Iltimos, <b>to'lov cheki (skrinshot)</b>ini yuboring.\n"
        "Bot uni avtomatik tekshiradi.",
        parse_mode="HTML"
    )
    await callback.answer()


@router.message(IlmiyXizmatStates.waiting_payment_check, F.photo)
async def ilmiy_payment_photo(message: Message, state: FSMContext, db_user: User):
    """Foydalanuvchi to'lov skrinshotini yubordi. AI tekshiradi."""
    data = await state.get_data()
    price = data.get("pending_price", 0)
    pages = data.get("pending_pages", 8)
    service_name = data.get("pending_name_uz", "Xizmat")
    price_fmt = f"{price:,}".replace(",", " ")

    check_msg = await message.answer("🔍 <b>To'lov tekshirilmoqda...</b>", parse_mode="HTML")

    # Download photo
    try:
        photo = message.photo[-1]
        from aiogram import Bot
        bot: Bot = message.bot
        file = await bot.get_file(photo.file_id)
        file_bytes = await bot.download_file(file.file_path)
        img_b64 = base64.b64encode(file_bytes.read()).decode()
    except Exception as e:
        await check_msg.edit_text(f"❌ Rasm yuklanmadi: {e}")
        return

    # Claude vision - to'lov cheki tahlili
    from services.ai_service import _claude_client, CLAUDE_MODEL
    import re as _re

    prompt = (
        f"Bu to'lov cheki (skrinshoti). Tekshir:\n"
        f"1) Aynan {price_fmt} so'm o'tkazilganmi?\n"
        f"2) To'lov muvaffaqiyatli yakunlanganmi?\n"
        "Faqat JSON qaytargin: {\"verified\": true/false, \"found_amount\": <raqam yoki null>, \"reason\": \"izoh\"}"
    )

    verified = False
    found_amount = None
    reason = "AI tekshirishda xatolik"

    try:
        if _claude_client:
            vision_resp = await _claude_client.messages.create(
                model=CLAUDE_MODEL,
                max_tokens=300,
                messages=[{
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/jpeg",
                                "data": img_b64,
                            }
                        },
                        {"type": "text", "text": prompt}
                    ]
                }]
            )
            result_text = vision_resp.content[0].text
            json_match = _re.search(r"\{.*?\}", result_text, _re.DOTALL)
            if json_match:
                result_json = json.loads(json_match.group())
                verified = result_json.get("verified", False)
                found_amount = result_json.get("found_amount")
                reason = result_json.get("reason", "")
        else:
            reason = "Claude API sozlanmagan"
    except Exception as e:
        reason = f"AI xatolik: {e}"
        verified = False
    found_amount = None
    reason = "AI tekshirishda xatolik"

    try:
        if _claude_client:
            vision_resp = await _claude_client.messages.create(
                model=CLAUDE_MODEL,
                max_tokens=300,
                messages=[{
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/jpeg",
                                "data": img_b64,
                            }
                        },
                        {"type": "text", "text": prompt}
                    ]
                }]
            )
            result_text = vision_resp.content[0].text
            import re as _re
            json_match = _re.search(r"\{.*?\}", result_text, _re.DOTALL)
            if json_match:
                result_json = json.loads(json_match.group())
                verified = result_json.get("verified", False)
                found_amount = result_json.get("found_amount")
                reason = result_json.get("reason", "")
        else:
            reason = "Claude API sozlanmagan"
    except Exception as e:
        reason = f"AI xatolik: {e}"
        verified = False

    if verified:
        # AI tasdiqladi - generatsiyani boshlash
        await check_msg.edit_text(
            f"✅ <b>To'lov tasdiqlandi!</b>\n"
            f"💵 Miqdor: {price_fmt} so'm\n"
            f"🚀 Hujjat yaratilmoqda...",
            parse_mode="HTML"
        )
        await _start_generation_after_payment(message, state, db_user)
    else:
        # Adminga yuborish
        from config import ADMIN_IDS
        admin_kb = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=f"admin_pay_ok:{message.from_user.id}"),
                InlineKeyboardButton(text="❌ Rad etish", callback_data=f"admin_pay_no:{message.from_user.id}")
            ]
        ])
        
        import json as _json
        state_data_str = _json.dumps({
            "user_id": message.from_user.id,
            "user_name": message.from_user.full_name,
            "price": price,
            "pages": pages,
            "service_name": service_name,
            "reason": reason,
            "found_amount": found_amount
        })
        
        sent_to_admin = False
        from aiogram.exceptions import TelegramBadRequest
        for admin_id in ADMIN_IDS:
            try:
                await message.bot.send_photo(
                    chat_id=admin_id,
                    photo=photo.file_id,
                    caption=(
                        f"⚠️ <b>To'lov tekshirish talab etiladi</b>\n\n"
                        f"👤 Foydalanuvchi: {message.from_user.full_name} (@{message.from_user.username})\n"
                        f"🆔 ID: <code>{message.from_user.id}</code>\n"
                        f"📄 Xizmat: {service_name} ({pages} bet)\n"
                        f"💵 Kerakli summa: <b>{price_fmt} so'm</b>\n"
                        f"🔍 AI topgani: {found_amount or 'topilmadi'}\n"
                        f"📝 Sabab: {reason}"
                    ),
                    parse_mode="HTML",
                    reply_markup=admin_kb
                )
                sent_to_admin = True
            except Exception:
                continue

        await check_msg.edit_text(f"❌ Rasm yuklanmadi: {e}")
        return

    # Claude vision - to'lov cheki tahlili
    from services.ai_service import _claude_client, CLAUDE_MODEL
    import re as _re

    prompt = (
        f"Bu to'lov cheki (skrinshoti). Tekshir:\n"
        f"1) Aynan {price_fmt} so'm o'tkazilganmi?\n"
        f"2) To'lov muvaffaqiyatli yakunlanganmi?\n"
        "Faqat JSON qaytargin: {\"verified\": true/false, \"found_amount\": <raqam yoki null>, \"reason\": \"izoh\"}"
    )

    verified = False
    found_amount = None
    reason = "AI tekshirishda xatolik"

    try:
        if _claude_client:
            vision_resp = await _claude_client.messages.create(
                model=CLAUDE_MODEL,
                max_tokens=300,
                messages=[{
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/jpeg",
                                "data": img_b64,
                            }
                        },
                        {"type": "text", "text": prompt}
                    ]
                }]
            )
            result_text = vision_resp.content[0].text
            json_match = _re.search(r"\{.*?\}", result_text, _re.DOTALL)
            if json_match:
                result_json = json.loads(json_match.group())
                verified = result_json.get("verified", False)
                found_amount = result_json.get("found_amount")
                reason = result_json.get("reason", "")
        else:
            reason = "Claude API sozlanmagan"
    except Exception as e:
        reason = f"AI xatolik: {e}"
        verified = False
    found_amount = None
    reason = "AI tekshirishda xatolik"

    try:
        if _claude_client:
            vision_resp = await _claude_client.messages.create(
                model=CLAUDE_MODEL,
                max_tokens=300,
                messages=[{
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/jpeg",
                                "data": img_b64,
                            }
                        },
                        {"type": "text", "text": prompt}
                    ]
                }]
            )
            result_text = vision_resp.content[0].text
            import re as _re
            json_match = _re.search(r"\{.*?\}", result_text, _re.DOTALL)
            if json_match:
                result_json = json.loads(json_match.group())
                verified = result_json.get("verified", False)
                found_amount = result_json.get("found_amount")
                reason = result_json.get("reason", "")
        else:
            reason = "Claude API sozlanmagan"
    except Exception as e:
        reason = f"AI xatolik: {e}"
        verified = False

    if verified:
        # AI tasdiqladi - generatsiyani boshlash
        await check_msg.edit_text(
            f"✅ <b>To'lov tasdiqlandi!</b>\n"
            f"💵 Miqdor: {price_fmt} so'm\n"
            f"🚀 Hujjat yaratilmoqda...",
            parse_mode="HTML"
        )
        await _start_generation_after_payment(message, state, db_user)
    else:
        # Adminga yuborish
        admin_id = ADMIN_IDS[0] if ADMIN_IDS else None
        if admin_id:
            admin_kb = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=f"admin_pay_ok:{message.from_user.id}"),
                    InlineKeyboardButton(text="❌ Rad etish", callback_data=f"admin_pay_no:{message.from_user.id}")
                ]
            ])
            # Store user data for admin approval
            import json as _json
            state_data_str = _json.dumps({
                "user_id": message.from_user.id,
                "user_name": message.from_user.full_name,
                "price": price,
                "pages": pages,
                "service_name": service_name,
                "reason": reason,
                "found_amount": found_amount
            })
            # Forward photo to admin
            await bot.send_photo(
                admin_id,
                photo.file_id,
                caption=(
                    f"⚠️ <b>To'lov tekshirish talab etiladi</b>\n\n"
                    f"👤 Foydalanuvchi: {message.from_user.full_name} (@{message.from_user.username})\n"
                    f"🆔 ID: <code>{message.from_user.id}</code>\n"
                    f"📄 Xizmat: {service_name} ({pages} bet)\n"
                    f"💵 Kerakli summa: <b>{price_fmt} so'm</b>\n"
                    f"🔍 AI topgani: {found_amount or 'topilmadi'}\n"
                    f"📝 Sabab: {reason}"
                ),
                parse_mode="HTML",
                reply_markup=admin_kb
            )

        await check_msg.edit_text(
            f"⚠️ <b>To'lov avtomatik tasdiqlanmadi.</b>\n\n"
            f"🔍 Sabab: {reason}\n\n"
            f"📨 Administrator tekshirmoqda. 5-10 daqiqa kuting.",
            parse_mode="HTML"
        )


async def _start_generation_after_payment(message: Message, state: FSMContext, db_user: User):
    """To'lov tasdiqlangandan keyin generatsiyani boshlash."""
    data = await state.get_data()
    service_key = data.get("pending_service_key")
    name_uz     = data.get("pending_name_uz")
    icon        = data.get("pending_icon")
    svc_type    = data.get("pending_svc_type")
    topic       = data.get("pending_topic")
    author      = data.get("pending_author")
    pages       = data.get("pending_pages")
    price_key   = data.get("pending_price_key")
    price       = data.get("pending_price", 0)
    lang        = data.get("pending_lang", "uz")

    lang_map = {
        "uz": "O'zbek tilida (Lotin alifbosida)",
        "ru": "Rus tilida (На русском языке)",
        "en": "Ingliz tilida (In English)"
    }
    lang_instruction = lang_map.get(lang, "O'zbek tilida")
    system_prompt    = build_system_prompt(service_key, lang_instruction)

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

    await _run_generation(
        message=message, state=state, db_user=db_user,
        wait_msg=wait_msg, cancel_flag=cancel_flag, cancel_kb=cancel_kb,
        service_key=service_key, name_uz=name_uz, icon=icon,
        svc_type=svc_type, topic=topic, author=author, pages=pages,
        price_key=price_key, price=price, lang=lang,
        lang_instruction=lang_instruction, system_prompt=system_prompt,
        is_admin=False, free_trial=False,
    )


# ─── Admin tasdiqlash/rad etish handler ──────────────────────────────────────

@router.callback_query(F.data.startswith("admin_pay_ok:"))
async def admin_approve_payment(callback: CallbackQuery, state: FSMContext):
    """Admin to'lovni tasdiqladi."""
    user_id = int(callback.data.split(":")[1])
    await callback.message.edit_caption(
        callback.message.caption + "\n\n✅ <b>ADMIN TASDIQLADI</b>",
        parse_mode="HTML",
        reply_markup=None
    )
    # User'ga xabar
    bot = callback.message.bot
    await bot.send_message(
        user_id,
        "✅ <b>To'lovingiz tasdiqlandi!</b>\n🚀 Hujjat yaratilmoqda...",
        parse_mode="HTML"
    )
    # Generatsiyani boshlash - FSM storage dan o'qib
    from aiogram.fsm.storage.base import StorageKey
    storage = getattr(callback.bot, 'fsm_storage', None)
    if storage:
        key = StorageKey(bot_id=callback.bot.id, chat_id=user_id, user_id=user_id)
        
        # We need db_user and state
        from database.db import get_user
        from aiogram.fsm.context import FSMContext
        db_user = await get_user(user_id)
        
        # Create a mock state
        user_state = FSMContext(storage=storage, key=key)
        
        # Create a mock message to pass to _start_generation_after_payment
        class MockMessage:
            def __init__(self, bot, chat_id):
                self.bot = bot
                self.chat = type('Chat', (), {'id': chat_id})
                self.from_user = type('User', (), {'id': chat_id})
                
            async def answer(self, text, **kwargs):
                return await self.bot.send_message(self.chat.id, text, **kwargs)
                
        mock_msg = MockMessage(callback.bot, user_id)
        
        import asyncio
        asyncio.create_task(_start_generation_after_payment(mock_msg, user_state, db_user))
        
    await callback.answer("✅ Tasdiqlandi, hujjat yaratilmoqda!")


@router.callback_query(F.data.startswith("admin_pay_no:"))
async def admin_reject_payment(callback: CallbackQuery):
    """Admin to'lovni rad etdi."""
    user_id = int(callback.data.split(":")[1])
    await callback.message.edit_caption(
        callback.message.caption + "\n\n❌ <b>ADMIN RAD ETDI</b>",
        parse_mode="HTML",
        reply_markup=None
    )
    bot = callback.message.bot
    await bot.send_message(
        user_id,
        "❌ <b>To'lovingiz tasdiqlanmadi.</b>\n\n"
        "Sabab: Yuborilgan summa yoki karta raqami mos kelmadi.\n"
        "To'g'ri to'lov qilib, yana chek yuboring.",
        parse_mode="HTML"
    )
    await callback.answer("❌ Rad etildi!")


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
    keywords = data.get("keywords", "")
    research_details = data.get("research_details", "")
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
    extra_context = ""
    if keywords:
        extra_context += f"Kalit so'zlar: {keywords}\n"
    if research_details:
        extra_context += f"Tadqiqot maqsadi va natijalari: {research_details}\n"
    if extra_context:
        system_prompt += "\n\nMUHIM QO'SHIMCHA MA'LUMOTLAR (Foydalanuvchi taqdim etgan va barcha yozuv jarayonida albatta inobatga olinishi shart! Aslo o'zingizdan mos kelmaydigan boshqa fakt to'qib chiqarmang):\n" + extra_context

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
                None, generate_docx, service_key, topic, content, author
            )
            doc_file = BufferedInputFile(doc_buf, filename=f"{name_uz[:25]}.docx")

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
                    options={"pages": pages_default, "price": price}
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
                ("barcha_annotatsiyalar", "ANNOTATSIYA",
                 f"'{topic}' maqolasi uchun O'ZBEK, INGLIZ va RUS tillarida annotatsiya va kalit so'zlar yoz.\\n"
                 f"DIQQAT: Ingliz (ABSTRACT/KEYWORDS) va Rus (АННОТАЦИЯ/КЛЮЧЕВЫЕ СЛОВА) tilidagi tarjimalar JUDA SIFATLI, grammatik jihatdan BEKAM-U KO'ST, professionallar darajasida va aniq ILMIY USLUBDA bo'lishi SHART! Har bir terminni asl ilmiy ma'nosida tarjima qil.\\n"
                 f"AYNAN shu formatda yozing (boshqa hech qanday qo'shimcha so'z, markdown yoki sarlavha qoshmang):\\n"
                 f"[O'zbek tilida 100-150 so'zlik annotatsiya matni]\\n"
                 f"KALIT SOʻZLAR: [5-8 ta o'zbekcha kalit so'zlar]\\n"
                 f"ABSTRACT\\n"
                 f"[English abstract 100-150 words]\\n"
                 f"KEYWORDS: [5-8 english keywords]\\n"
                 f"АННОТАЦИЯ\\n"
                 f"[Аннотация на русском 100-150 слов]\\n"
                 f"КЛЮЧЕВЫЕ СЛОВА: [5-8 русских ключевых слов]"),
                ("kirish", "KIRISH",
                 f"'{topic}' maqolasining KIRISH qismini yoz. "
                 f"Dolzarblik, o'rganilganlik, maqsad. {w} so'z. Sarlavha YOZMA. Xulosa yoki adabiyotlar ro'yxatini QO'SHMA! Xulosa yoki adabiyotlar ro'yxatini QO'SHMA!"),
                ("1", f"1. {plan_titles.get('1','Asosiy bo\'lim')}",
                 f"'{topic}' bo'limi '{plan_titles.get('1','')}' uchun akademik matn. "
                 f"{w} so'z. Sarlavha YOZMA. Xulosa yoki adabiyotlar ro'yxatini QO'SHMA! Xulosa yoki adabiyotlar ro'yxatini QO'SHMA!"),
                ("1.1", f"1.1. {plan_titles.get('1.1','Kichik bo\'lim')}",
                 f"'{topic}' bo'limi '{plan_titles.get('1.1','')}' uchun nazariy tahlil. "
                 f"{w} so'z. Sarlavha YOZMA. Xulosa yoki adabiyotlar ro'yxatini QO'SHMA! Xulosa yoki adabiyotlar ro'yxatini QO'SHMA!"),
                ("1.2", f"1.2. {plan_titles.get('1.2','Kichik bo\'lim')}",
                 f"'{topic}' bo'limi '{plan_titles.get('1.2','')}' uchun empirik tahlil. "
                 f"{w} so'z. Sarlavha YOZMA. Xulosa yoki adabiyotlar ro'yxatini QO'SHMA! Xulosa yoki adabiyotlar ro'yxatini QO'SHMA!"),
                ("2", f"2. {plan_titles.get('2','Ikkinchi bo\'lim')}",
                 f"'{topic}' bo'limi '{plan_titles.get('2','')}' uchun chuqur tahlil. "
                 f"{w} so'z. Sarlavha YOZMA. Xulosa yoki adabiyotlar ro'yxatini QO'SHMA! Xulosa yoki adabiyotlar ro'yxatini QO'SHMA!"),
                ("2.1", f"2.1. {plan_titles.get('2.1','Kichik bo\'lim')}",
                 f"'{topic}' bo'limi '{plan_titles.get('2.1','')}' uchun amaliy misollar. "
                 f"{w} so'z. Sarlavha YOZMA. Xulosa yoki adabiyotlar ro'yxatini QO'SHMA! Xulosa yoki adabiyotlar ro'yxatini QO'SHMA!"),
                ("2.2", f"2.2. {plan_titles.get('2.2','Kichik bo\'lim')}",
                 f"'{topic}' bo'limi '{plan_titles.get('2.2','')}' uchun taqqoslash. "
                 f"{w} so'z. Sarlavha YOZMA. Xulosa yoki adabiyotlar ro'yxatini QO'SHMA! Xulosa yoki adabiyotlar ro'yxatini QO'SHMA!"),
                ("xulosa", "XULOSA",
                 f"'{topic}' maqolasining XULOSA va TAVSIYALAR qismini yoz. "
                 f"{max(100, w//2)} so'z. Sarlavha umuman YOZMA (hatto 'Xulosa' deb ham yozma). Faqat matnni o'zini yoz!"),
                ("adabiyotlar", "FOYDALANILGAN ADABIYOTLAR",
                 f"'{topic}' mavzusiga oid 10-15 ta REAL ilmiy manba ro'yxati. "
                 f"OAK talablari bo'yicha APA yoki GOST formatida. Kamida 5-6 ta O'zbek muallifi (kitob yoki maqolalari, nashriyot, yili, betlari) bo'lsin. "
                 f"Sarlavha umuman YOZMA. Faqat ro'yxatni o'zini yoz. Ro'yxatni raqam va nuqta bilan boshla (1., 2., 3., va hokazo). [1] kabi qavslardan foydalanma!"),
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

            full_parts = []
            for key, (sec_name, sec_content) in sections_content.items():
                if key not in ["barcha_annotatsiyalar", "kirish", "xulosa", "adabiyotlar"]:
                    full_parts.append(f"\n## {sec_name}\n\n{sec_content}\n")
                else:
                    full_parts.append(f"\n{sec_name}\n\n{sec_content}\n")
            full_text = "\n".join(full_parts)

            doc_buf = await asyncio.get_event_loop().run_in_executor(
                None, generate_docx, service_key, topic, full_text, author
            )
            doc_file = BufferedInputFile(doc_buf, filename=f"{name_uz[:25]}.docx")

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
                    options={"pages": pages_default, "price": price}
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



async def _run_generation(
    message, state, db_user, wait_msg, cancel_flag, cancel_kb,
    service_key, name_uz, icon, svc_type, topic, author, pages,
    price_key, price, lang, lang_instruction, system_prompt,
    is_admin, free_trial
):
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
                None, generate_docx, service_key, topic, content, author
            )
            doc_file = BufferedInputFile(doc_buf, filename=f"{name_uz[:25]}.docx")

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
                    options={"pages": pages, "price": price}
                )

            await wait_msg.delete()
            await wait_msg.bot.send_document(
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
                ("barcha_annotatsiyalar", "ANNOTATSIYA",
                 f"'{topic}' maqolasi uchun O'ZBEK, INGLIZ va RUS tillarida annotatsiya va kalit so'zlar yoz.\\n"
                 f"DIQQAT: Ingliz (ABSTRACT/KEYWORDS) va Rus (АННОТАЦИЯ/КЛЮЧЕВЫЕ СЛОВА) tilidagi tarjimalar JUDA SIFATLI, grammatik jihatdan BEKAM-U KO'ST, professionallar darajasida va aniq ILMIY USLUBDA bo'lishi SHART! Har bir terminni asl ilmiy ma'nosida tarjima qil.\\n"
                 f"AYNAN shu formatda yozing (boshqa hech qanday qo'shimcha so'z, markdown yoki sarlavha qoshmang):\\n"
                 f"[O'zbek tilida 100-150 so'zlik annotatsiya matni]\\n"
                 f"KALIT SOʻZLAR: [5-8 ta o'zbekcha kalit so'zlar]\\n"
                 f"ABSTRACT\\n"
                 f"[English abstract 100-150 words]\\n"
                 f"KEYWORDS: [5-8 english keywords]\\n"
                 f"АННОТАЦИЯ\\n"
                 f"[Аннотация на русском 100-150 слов]\\n"
                 f"КЛЮЧЕВЫЕ СЛОВА: [5-8 русских ключевых слов]"),
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
                 f"{max(100, w//2)} so'z. Sarlavha umuman YOZMA (hatto 'Xulosa' deb ham yozma). Faqat matnni o'zini yoz!"),
                ("adabiyotlar", "FOYDALANILGAN ADABIYOTLAR",
                 f"'{topic}' mavzusiga oid 10-15 ta REAL ilmiy manba ro'yxati. "
                 f"OAK talablari bo'yicha APA yoki GOST formatida. Kamida 5-6 ta O'zbek muallifi (kitob yoki maqolalari, nashriyot, yili, betlari) bo'lsin. "
                 f"Sarlavha umuman YOZMA. Faqat ro'yxatni o'zini yoz. Ro'yxatni raqam va nuqta bilan boshla (1., 2., 3., va hokazo). [1] kabi qavslardan foydalanma!"),
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

            full_parts = []
            for key, (sec_name, sec_content) in sections_content.items():
                if key not in ["barcha_annotatsiyalar", "kirish", "xulosa", "adabiyotlar"]:
                    full_parts.append(f"\n## {sec_name}\n\n{sec_content}\n")
                else:
                    full_parts.append(f"\n{sec_name}\n\n{sec_content}\n")
            full_text = "\n".join(full_parts)

            doc_buf = await asyncio.get_event_loop().run_in_executor(
                None, generate_docx, service_key, topic, full_text, author
            )
            doc_file = BufferedInputFile(doc_buf, filename=f"{name_uz[:25]}.docx")

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
                    options={"pages": pages, "price": price}
                )

            await wait_msg.delete()
            await wait_msg.bot.send_document(
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
        await wait_msg.bot.send_message(
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
