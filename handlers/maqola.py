from __future__ import annotations
"""
handlers/maqola.py

Ilmiy maqola yaratish handler — tezis kodi asosida qurilgan.
Foydalanuvchi mavzu va parametrlarni kiritadi, AI esa doc_templates/maqola_structure.txt
va doc_examples/maqola_example.* fayllarini o'qib, sifatli maqola yozadi.
"""

import asyncio
import io
import os
import json
from aiogram import Router, F
from aiogram.types import (
    Message, CallbackQuery, BufferedInputFile, WebAppInfo,
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database.models import User
from database.db import create_request, deduct_balance, mark_free_used
from keyboards.main_kb import main_menu_kb
from services.ai_service import client, OPENAI_MODEL
from services.docx_service import generate_docx
from services.template_loader import load_template_and_example
from utils.helpers import format_price, is_free_trial
from utils.i18n import t
from config import ADMIN_IDS, PRICING

router = Router()

class MaqolaStates(StatesGroup):
    reviewing_settings = State()
    waiting_for_file   = State()


# ── File extractor (shared logic) ────────────────────────────────────────────

async def extract_text_from_file(message: Message) -> str:
    doc = message.document
    file = await message.bot.get_file(doc.file_id)
    buf = io.BytesIO()
    await message.bot.download_file(file.file_path, buf)
    buf.seek(0)
    name = (doc.file_name or "").lower()

    if name.endswith(".txt"):
        return buf.read().decode("utf-8", errors="ignore")
    elif name.endswith(".docx"):
        from docx import Document as DocxDocument
        doc_obj = DocxDocument(buf)
        return "\n".join(p.text for p in doc_obj.paragraphs if p.text.strip())
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
        raise ValueError("Qo'llab-quvvatlanmaydigan fayl formati. Iltimos .txt, .docx yoki .pdf yuboring.")


# ── Keyboard ──────────────────────────────────────────────────────────────────

def maqola_settings_kb():
    base_url = os.getenv("WEBAPP_URL", "https://arslon.github.io/student_bot/webapp/").split("?")[0]
    if not base_url.endswith("/"): base_url += "/"
    url = f"{base_url}maqola_settings.html"
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="⚙️ Sozlamalarni ochish", web_app=WebAppInfo(url=url))],
            [KeyboardButton(text="📎 Fayldan yaratish")],
            [KeyboardButton(text="🚀 Yaratish")],
            [KeyboardButton(text="❌ Bekor qilish")]
        ],
        resize_keyboard=True
    )


# ── Entry point ───────────────────────────────────────────────────────────────

@router.message(F.text == "📝 Maqola yaratish")
async def start_maqola(message: Message, state: FSMContext, db_user: User):
    balance = db_user.balance or 0
    await state.set_state(MaqolaStates.reviewing_settings)
    await message.answer(
        "📝 <b>Ilmiy maqola yaratish</b>\n\n"
        f"💳 <b>Balansingiz:</b> {format_price(balance)}\n\n"
        "ℹ️ <i>1. Sozlamalarni oching va to'ldiring\n"
        "2. SAQLASH VA YARATISH tugmasini bosing</i>",
        reply_markup=maqola_settings_kb(),
        parse_mode="HTML"
    )


# ── WebApp data handlers ──────────────────────────────────────────────────────

@router.message(F.web_app_data, MaqolaStates.reviewing_settings)
async def maqola_webapp_data(message: Message, state: FSMContext, db_user: User):
    try:
        data = json.loads(message.web_app_data.data)
        if data.get("type") not in ("maqola_settings", "tezis_settings"):
            return
        await state.update_data(
            topic=data["topic"],
            name=data["author"],
            university=data.get("university", ""),
            structure=data["structure"],
            lang=data["language"],
            pages=data["pages"],
            images=data.get("images", 0)
        )
        await maqola_generate(message, state, db_user)
    except Exception as e:
        print("Maqola WebApp parsing error:", e)


@router.message(F.web_app_data, MaqolaStates.waiting_for_file)
async def maqola_webapp_data_file(message: Message, state: FSMContext, db_user: User):
    await maqola_webapp_data(message, state, db_user)


# ── File upload flow ──────────────────────────────────────────────────────────

@router.message(F.text == "📎 Fayldan yaratish", MaqolaStates.reviewing_settings)
async def maqola_ask_for_file(message: Message, state: FSMContext):
    await state.set_state(MaqolaStates.waiting_for_file)
    await message.answer(
        "📎 <b>Faylingizni yuboring</b>\n\n"
        "Quyidagi format qo'llab-quvvatlanadi:\n"
        "• <b>.txt</b> — oddiy matn\n"
        "• <b>.docx</b> — Word hujjati\n"
        "• <b>.pdf</b> — PDF hujjati\n\n"
        "<i>Fayl yuborilgandan so'ng, sozlamalarni to'ldiring va yaratish boshlaydi.</i>",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="❌ Bekor qilish")]],
            resize_keyboard=True
        ),
        parse_mode="HTML"
    )


@router.message(F.document, MaqolaStates.waiting_for_file)
async def maqola_receive_file(message: Message, state: FSMContext, db_user: User):
    proc = await message.answer(t("tfill_file_read", "uz"), parse_mode="HTML")
    try:
        source_text = await extract_text_from_file(message)
        if not source_text.strip():
            await proc.edit_text(t("doc_file_empty", "uz"))
            return
        source_text = source_text[:12000]
        await state.update_data(source_text=source_text)
        await state.set_state(MaqolaStates.reviewing_settings)
        await proc.delete()
        await message.answer(
            f"✅ <b>Fayl muvaffaqiyatli o'qildi!</b>\n"
            f"📝 Hajm: ~{len(source_text.split())} so'z\n\n"
            "Endi sozlamalarni to'ldiring (mavzu, muallif, sahifalar soni).\n"
            "ℹ️ Agar mavzu bo'sh qolsa, AI fayldan o'zi aniqlaydi.",
            reply_markup=maqola_settings_kb(),
            parse_mode="HTML"
        )
    except ValueError as e:
        await proc.edit_text(f"❌ {e}")
    except Exception as e:
        await proc.edit_text(f"❌ Xatolik: {str(e)}")


# ── Cancel handlers ───────────────────────────────────────────────────────────

@router.message(F.text == "❌ Bekor qilish", MaqolaStates.reviewing_settings)
async def maqola_cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(t("cancelled", "uz"), reply_markup=main_menu_kb())


@router.message(F.text == "❌ Bekor qilish", MaqolaStates.waiting_for_file)
async def maqola_cancel_file(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(t("cancelled", "uz"), reply_markup=main_menu_kb())


# ── Main generation ───────────────────────────────────────────────────────────

@router.message(F.text == "🚀 Yaratish", MaqolaStates.reviewing_settings)
async def maqola_generate(message: Message, state: FSMContext, db_user: User):
    data = await state.get_data()
    pages = data.get("pages", 5)
    topic = data.get("topic")
    name  = data.get("name")

    if not topic or not name:
        await message.answer(t("maq_fill_settings", "uz"), parse_mode="HTML")
        return

    structure   = data.get("structure", "Standart")
    lang        = data.get("lang", "uz")
    university  = data.get("university", "")
    images_count = min(int(data.get("images", 0)), 15)

    base_price = PRICING.get(f"maqola_{pages}", 4000)
    price      = base_price + images_count * 1000
    is_admin   = db_user.id in ADMIN_IDS
    free_trial = is_free_trial(db_user) and not is_admin
    if free_trial:
        # Free trial: only AI images cost money
        price = images_count * 1000

    if not is_admin and not free_trial and (db_user.balance or 0) < price:
        await message.answer(t("pres_balance_low", "uz", needed=format_price(price - (db_user.balance or 0))), reply_markup=main_menu_kb(), parse_mode="HTML")
        return

    cancel_flag = {"cancelled": False}
    await state.update_data(cancel_flag=cancel_flag)

    cancel_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="maqola_cancel_gen")]
    ])

    try:
        await message.answer("⏳", reply_markup=ReplyKeyboardRemove())
    except:
        pass
    wait_msg = await message.bot.send_message(
        chat_id=message.chat.id,
        text="⏳ <b>Maqola yaratilmoqda...</b>\n"
             "📝 Bo'limlar ketma-ket yozilmoqda...\n"
             "⏳ <i>4-5 daqiqa kutib turing — sifatli natija uchun!</i>",
        parse_mode="HTML",
        reply_markup=cancel_kb
    )

    def is_cancelled():
        return cancel_flag.get("cancelled", False)

    total_words = pages * 250

    try:
        lang_instruction = (
            "O'zbek tilida (Lotin alifbosida)" if lang == "uz"
            else "Rus tilida (На русском)" if lang == "ru"
            else "Ingliz tilida (In English)"
        )
        source_text = data.get("source_text", "")
        template_context = load_template_and_example("maqola")

        if images_count > 0:
            image_instruction = (
                "\n\nRASMLAR QOIDASI:\n"
                f"Matnda jami {images_count} ta joyga AI rasm avtomatik qo'yiladi. "
                f"Shu {images_count} ta eng muhim joyda AYNAN shu formatda yoz:\n"
                "[ RASM: (rasmda nima tasvirlangan bo'lishi kerakligi 2-3 so'z) ]\n"
                "Masalan: [ RASM: qurilmaning umumiy ko'rinishi ]\n\n"
                "QOLGAN barcha boshqa joylarda (har bir bo'limda yana 1-2 ta) "
                "qo'lda rasm qo'yish uchun shu formatda yoz:\n"
                "[ SHU YERGA RASM JOYLANG: (qanday rasm kerakligi 2-3 so'z) ]\n"
                "Masalan: [ SHU YERGA RASM JOYLANG: tajriba natijalari grafigi ]\n\n"
                "JAMI matnda 6-10 ta rasm joy bo'lsin (AI + qo'lda)."
            )
        else:
            image_instruction = (
                "\n\nRASMLAR QOIDASI:\n"
                "Matn ichida rasm joylashishi kerak bo'lgan joyda shu formatda yoz:\n"
                "[ SHU YERGA RASM JOYLANG: (qanday rasm qo'yish kerakligi haqida 2-3 so'z) ]\n"
                "Masalan: [ SHU YERGA RASM JOYLANG: qurilmaning umumiy ko'rinishi ]\n"
                "Har bir content bo'limda 1-2 ta rasm joy qo'y."
            )

        system_prompt = (
            f"{template_context}\n"
            "Sen professional ilmiy maqola yozuvchisisiz. 30+ yillik tajribaga ega "
            "akademik tadqiqotchi va jurnal muharririsiz. "
            "Har bir paragraf aniq dalil, misollar va tahlilga ega bo'lishi kerak. "
            "Markdown belgilarini (**, #, ```) ISHLATMA. Faqat oddiy matn yoz.\n\n"
            "QAT'IY TAQIQLAR:\n"
            "- 'Mavzu:', 'Muallif:', 'Author:', 'Topic:' so'zlarini HECH QACHON yozma.\n"
            "- Bo'lim nomlarini TAKRORLATMA (ANNOTATSIYA, KIRISH, XULOSA, KALIT SO'ZLAR deb yozma).\n"
            "- Maqola sarlavhasini matn ichida TAKRORLATMA.\n"
            "- Faqat SO'RALGAN KONTENTNI yoz — sarlavhasiz, yorliqsiz, prefixsiz.\n"
            "- Har bir javobni TO'G'RIDAN-TO'G'RI matn bilan boshlash kerak."
            f"{image_instruction}"
        )

        source_block = ""
        if source_text:
            source_block = (
                f"\n\n--- MANBA MATERIAL ---\n{source_text}\n--- MANBA TUGADI ---\n\n"
                "MUHIM: Yozishda shu materialni asos qilib ol. "
                "Kengaytir, tahlil qil, qayta yoz. Aynan ko'chirma!"
            )

        from services.ai_service import _call_ai as _ai_call
        async def call_ai(msgs, temp=0.7, max_tok=4000):
            return await _ai_call(msgs, max_tokens=max_tok, temperature=temp)

        # ── Step 1: Generate plan (section titles) ──────────────────────────
        try:
            await wait_msg.edit_text(
                "🧠 <b>AI reja tuzmoqda...</b>\n⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜",
                parse_mode="HTML", reply_markup=cancel_kb
            )
        except:
            pass

        plan_prompt = (
            f"Mavzu: {topic}\nTil: {lang_instruction}\n\n"
            "Vazifa: Ilmiy maqola uchun 6 ta bo'lim nomi tuz.\n"
            "QAT'IY FORMAT — faqat shu formatda javob ber:\n"
            "1. [birinchi asosiy bo'lim nomi]\n"
            "1.1. [birinchi kichik bo'lim nomi]\n"
            "1.2. [ikkinchi kichik bo'lim nomi]\n"
            "2. [ikkinchi asosiy bo'lim nomi]\n"
            "2.1. [uchinchi kichik bo'lim nomi]\n"
            "2.2. [to'rtinchi kichik bo'lim nomi]\n\n"
            "FAQAT shu 6 qatorni yoz, boshqa hech narsa qo'shma."
        )
        plan_text = await call_ai(
            [{"role": "user", "content": plan_prompt}],
            temp=0.5, max_tok=500
        )

        # Parse plan titles
        import re as re_mod
        plan_titles = {}
        for line in plan_text.split("\n"):
            line = line.strip()
            m = re_mod.match(r'^(\d+(?:\.\d+)?)\.\s*(.+)', line)
            if m:
                plan_titles[m.group(1)] = m.group(2).strip()

        if is_cancelled():
            await state.clear()
            return

        # ── Step 2: Define sections ─────────────────────────────────────────
        # 1 sahifa ≈ 250 so'z. Annotatsiya+kalit+xulosa+adabiyotlar ≈ 0.5 sahifa
        # Qolgan 7 ta content bo'lim sahifalarni teng taqsimlaydi
        content_words = max(700, total_words - 150)  # 150 = short sections
        w = content_words // 7  # per content section

        maqola_sections = [
            ("annotatsiya", "ANNOTATSIYA",
             f"'{topic}' mavzusidagi maqola uchun annotatsiya yoz. "
             f"Muammo, metodologiya, natijalar haqida. "
             f"Hajmi: {max(80, w // 3)} so'z. {lang_instruction}. "
             "FAQAT annotatsiya matnini yoz — 'ANNOTATSIYA', 'Mavzu' so'zlarini YOZMA."),

            ("kalit_sozlar", "KALIT SO'ZLAR",
             f"'{topic}' mavzusiga oid 7 ta kalit so'z yoz. "
             "FAQAT vergul bilan ajratilgan so'zlarni yoz, boshqa hech narsa qo'shma. "
             "Misol: so'z1, so'z2, so'z3, so'z4, so'z5, so'z6, so'z7"),

            ("kirish", "KIRISH",
             f"'{topic}' mavzusidagi maqolaning KIRISH qismini yoz. "
             f"Muammo, dolzarblik, maqsad, tarix haqida. "
             f"Hajmi: {w} so'z. {lang_instruction}. "
             "FAQAT matn yoz — 'KIRISH' sarlavhasini YOZMA."),

            ("1", f"1. {plan_titles.get('1', 'Asosiy bolim')}",
             f"'{topic}' maqolasi, '{plan_titles.get('1', '')}' bo'limi uchun "
             f"chuqur akademik matn yoz. Sarlavha YOZMA, faqat matn. "
             f"Hajmi: {w} so'z. {lang_instruction}.{source_block}"),

            ("1.1", f"1.1. {plan_titles.get('1.1', 'Kichik bolim')}",
             f"'{topic}' maqolasi, '{plan_titles.get('1.1', '')}' bo'limi uchun "
             f"batafsil akademik matn yoz. Nazariya, faktlar, misollar. Sarlavha YOZMA. "
             f"Hajmi: {w} so'z. {lang_instruction}.{source_block}"),

            ("1.2", f"1.2. {plan_titles.get('1.2', 'Kichik bolim')}",
             f"'{topic}' maqolasi, '{plan_titles.get('1.2', '')}' bo'limi uchun "
             f"batafsil akademik matn yoz. Tahlil, taqqoslash, dalillar. Sarlavha YOZMA. "
             f"Hajmi: {w} so'z. {lang_instruction}.{source_block}"),

            ("2", f"2. {plan_titles.get('2', 'Ikkinchi bolim')}",
             f"'{topic}' maqolasi, '{plan_titles.get('2', '')}' bo'limi uchun "
             f"chuqur akademik matn yoz. Sarlavha YOZMA, faqat matn. "
             f"Hajmi: {w} so'z. {lang_instruction}.{source_block}"),

            ("2.1", f"2.1. {plan_titles.get('2.1', 'Kichik bolim')}",
             f"'{topic}' maqolasi, '{plan_titles.get('2.1', '')}' bo'limi uchun "
             f"batafsil akademik matn yoz. Amaliy misollar, statistika. Sarlavha YOZMA. "
             f"Hajmi: {w} so'z. {lang_instruction}.{source_block}"),

            ("2.2", f"2.2. {plan_titles.get('2.2', 'Kichik bolim')}",
             f"'{topic}' maqolasi, '{plan_titles.get('2.2', '')}' bo'limi uchun "
             f"batafsil akademik matn yoz. Xulosa va tahlil. Sarlavha YOZMA. "
             f"Hajmi: {w} so'z. {lang_instruction}.{source_block}"),

            ("xulosa", "XULOSA",
             f"'{topic}' maqolasi uchun xulosa va takliflar yoz. "
             f"Natijalar, ilmiy hissa, tavsiyalar. Sarlavha YOZMA, faqat matn. "
             f"Hajmi: {max(80, w // 2)} so'z. {lang_instruction}."),

            ("adabiyotlar", "FOYDALANILGAN ADABIYOTLAR",
             f"'{topic}' mavzusiga oid "
             f"8-12 ta REAL ilmiy manba ro'yxatini yoz. {lang_instruction}.\n"
             "QAT'IY QOIDALAR:\n"
             "- Kamida 4-5 ta O'ZBEK mualliflari va O'zbekiston nashriyotlari manbasi bo'lsin.\n"
             "- Qolgan 3-5 ta xorijiy mualliflar bo'lishi mumkin.\n"
             "- O'zbek manbalari formati: Familiya I.Sh. Kitob nomi. — T.: Nashriyot, Yil. — B son.\n"
             "  Masalan: Karimov B.R. Pedagogika asoslari. — T.: Fan, 2022. — 245 b.\n"
             "- Xorijiy manba formati: Author F.I. Title. Publisher, Year.\n"
             "- Har bir manba REAL va ishonchli ko'rinsin.\n"
             "- Faqat ro'yxatni yoz, boshqa hech narsa qo'shma."),
        ]

        # ── Step 3: Generate each section ───────────────────────────────────
        sections_content = {}
        total = len(maqola_sections)

        for idx, (key, section_name, prompt) in enumerate(maqola_sections, 1):
            if is_cancelled():
                await state.clear()
                return

            filled = int(((idx - 1) / total) * 10)
            bar = "🟩" * filled + "⬜" * (10 - filled)
            try:
                await wait_msg.edit_text(
                    f"✍️ <b>AI maqola yozmoqda...</b>\n\n"
                    f"📊 <b>{idx - 1}/{total}</b> bo'lim tayyor\n"
                    f"{bar}\n\n"
                    f"⏭ <b>Hozir yozilmoqda:</b> <i>{section_name}</i>\n\n"
                    f"<i>Professional maqola uchun sabr qiling...</i>",
                    parse_mode="HTML", reply_markup=cancel_kb
                )
            except:
                pass

            text = await call_ai(
                [{"role": "system", "content": system_prompt},
                 {"role": "user", "content": prompt}],
                temp=0.7,
                max_tok=6000
            )
            sections_content[key] = text

        # ── Step 4: Generate AI images ─────────────────────────────────────
        generated_images = {}  # {"description": image_bytes}
        if images_count > 0 and not is_cancelled():
            import re as re_img
            # Collect all [ RASM: ... ] placeholders
            all_placeholders = []
            for key, text in sections_content.items():
                for m in re_img.finditer(r'\[\s*RASM:\s*(.+?)\s*\]', text):
                    desc = m.group(1).strip()
                    if desc and desc not in [p[1] for p in all_placeholders]:
                        all_placeholders.append((m.group(0), desc))

            # Limit to user-selected count
            placeholders_to_gen = all_placeholders[:images_count]
            img_total = len(placeholders_to_gen)

            for img_idx, (placeholder_text, desc) in enumerate(placeholders_to_gen, 1):
                if is_cancelled():
                    break
                try:
                    await wait_msg.edit_text(
                        f"🎨 <b>AI rasmlar yaratilmoqda...</b>\n\n"
                        f"📊 <b>{img_idx}/{img_total}</b>\n"
                        f"🖼️ <i>{desc}</i>",
                        parse_mode="HTML", reply_markup=cancel_kb
                    )
                except:
                    pass
                try:
                    img_resp = await client.images.generate(
                        model="gpt-image-1-mini",
                        prompt=(
                            f"Scientific academic illustration for an article about '{topic}'. "
                            f"The image should show: {desc}. "
                            "Style: clean, professional, educational diagram or illustration. "
                            "No text, no watermarks. White or light background."
                        ),
                        n=1, size="1024x1024", quality="medium"
                    )
                    img_url = img_resp.data[0].url
                    import httpx
                    async with httpx.AsyncClient() as http_client:
                        resp = await http_client.get(img_url)
                        if resp.status_code == 200:
                            generated_images[placeholder_text] = resp.content
                except Exception as e:
                    print(f"DALL-E error for '{desc}': {e}")

        # ── Step 5: Build DOCX from template ────────────────────────────────
        try:
            await wait_msg.edit_text(
                f"✅ <b>Barcha bo'limlar tayyor!</b>\n"
                f"{'🟩' * 10}\n\n⏳ <b>DOCX fayl yaratilmoqda...</b>",
                parse_mode="HTML"
            )
        except:
            pass

        from services.docx_service import generate_maqola_from_template

        docx_bytes = await asyncio.get_event_loop().run_in_executor(
            None,
            generate_maqola_from_template,
            topic, sections_content, name, university, plan_titles,
            generated_images
        )

        if free_trial:
            await mark_free_used(db_user.id)
            if price > 0: await deduct_balance(db_user.id, price)
            status_note = "🎁 <b>Birinchi marta BEPUL!</b>"
        elif not is_admin:
            await deduct_balance(db_user.id, price)
            status_note = f"💰 <b>Hisobdan yechildi:</b> {format_price(price)}"
        else:
            status_note = "🛡️ <b>Admin uchun tekin</b>"

        await create_request(db_user.id, "maqola", topic=topic)

        await wait_msg.delete()
        await message.answer_document(
            BufferedInputFile(docx_bytes, filename=f"maqola_{topic[:20]}.docx"),
            caption=(
                f"✅ <b>Maqola tayyor!</b>\n\n"
                f"📝 <b>Mavzu:</b> {topic}\n"
                f"👤 <b>Muallif:</b> {name}\n"
                + (f"🏫 <b>Universitet:</b> {university}\n" if university else "")
                + (f"🖼️ <b>Rasmlar:</b> {len(generated_images)} ta\n" if generated_images else "")
                + f"📄 <b>Hajmi:</b> {pages} sahifa (~{total_words} so'z)\n"
                f"────────────────────\n"
                f"{status_note}"
            ),
            reply_markup=main_menu_kb(),
            parse_mode="HTML"
        )
        await state.clear()

    except Exception as e:
        try:
            await wait_msg.edit_text(f"❌ <b>Xatolik yuz berdi:</b> {str(e)}", parse_mode="HTML")
        except:
            await message.answer(f"❌ <b>Xatolik yuz berdi:</b> {str(e)}", parse_mode="HTML")
        await state.clear()

@router.callback_query(F.data == "maqola_cancel_gen")
async def cancel_maqola_gen(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    cancel_flag = data.get("cancel_flag")
    if cancel_flag and isinstance(cancel_flag, dict):
        cancel_flag["cancelled"] = True
    await state.clear()
    await callback.message.edit_text(t("maq_cancel_gen", "uz"))
    await callback.answer()
