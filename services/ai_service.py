from __future__ import annotations
import os
import json
import asyncio
import logging
from openai import AsyncOpenAI
from config import OPENAI_API_KEY, OPENAI_MODEL, ANTHROPIC_API_KEY, CLAUDE_MODEL

logger = logging.getLogger(__name__)
openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY)
client = openai_client  # backward-compatible alias

# ══════════════════════════════════════════════════════════════════════════════
# HUMANIZER: Anti-plagiarism rules to make AI text sound human-written
# ══════════════════════════════════════════════════════════════════════════════
HUMANIZER_RULES_UZ = (
    "\n\nENG MUHIM QOIDA — INSON KABI YOZ (ANTI-PLAGIAT):\n"
    "Sening matnni sun'iy intellekt yozganini HECH KIM bilmasligi kerak. "
    "Quyidagi qoidalarga QAT'IY rioya qil:\n"
    "1. Quyidagi AI-shablon so'zlarni HECH QACHON ISHLATMA: "
    "'Xulosa qilib aytganda', 'Ta'kidlash joizki', 'Shuni ta'kidlash kerakki', "
    "'Shuni yodda tutish kerakki', 'Shuni aytish kerakki', "
    "'Umuman olganda', 'Muhim jihati shundaki', 'Sir emaski', "
    "'Aytib o'tish joizki', 'E'tibor qaratish lozim', 'Alohida qayd etish kerak', "
    "'Yuqoridagilardan kelib chiqib', 'Ushbu kontekstda', 'Muhim ahamiyatga ega', "
    "'Bu bo'limda ... o'rganiladi', 'Bu bo'limda ... ko'rib chiqiladi', "
    "'Ushbu bo'limda', 'bu yerda biz', 'quyida ko'rib chiqamiz', "
    "'misollar orqali o'rganiladi', 'batafsil tahlil qilinadi', "
    "'Keling ... ko'rib chiqaylik', 'Kelgusida', 'Shu bilan birga'.\n"
    "2. Gaplar uzunligini DOIMO O'ZGARTIRIB TUR: bitta uzun gapdan keyin "
    "qisqa gap yoz. Keyin yana o'rtacha. Monoton ritm bo'lmasin.\n"
    "3. Abzatslar bir xil tuzilishda bo'lmasin — ba'zisini savol bilan boshlash, "
    "ba'zisini fakt bilan, ba'zisini misol bilan.\n"
    "4. Ba'zan norasmiy akademik uslub ishlat — haqiqiy professor gapirgandek, "
    "lekin ilmiy asosda.\n"
    "5. Ortiqcha mukammallikdan qoching — haqiqiy odamlar ba'zan oddiy so'zlar ishlatadilar.\n"
    "6. QAT'IY TIL QOIDASI: Matn FAQAT TOZA O'ZBEK TILIDA yozilishi SHART! Ingliz, rus yoki "
    "boshqa chet el so'zlarini (masalan, 'traditional', 'development', 'process', 'smart' kabi) "
    "UMUMAN ISHLATMANG. Ularning o'rniga faqat toza o'zbekcha atamalarni "
    "(masalan, 'an'anaviy', 'rivojlanish', 'jarayon', 'aqlli') ishlating.\n"
    "7. Har bir abzatsni bir xil so'z bilan boshlaMA — har safar yangi, kutilmagan boshlanish bo'lsin.\n"
)

HUMANIZER_RULES_RU = (
    "\n\nСАМОЕ ВАЖНОЕ ПРАВИЛО — ПИШИ КАК ЧЕЛОВЕК (АНТИПЛАГИАТ):\n"
    "Никто НЕ ДОЛЖЕН понять, что текст написан ИИ. "
    "СТРОГО соблюдай следующие правила:\n"
    "1. НИКОГДА не используй эти AI-штампы: "
    "'В заключение хочется сказать', 'Стоит отметить', 'Важно подчеркнуть', "
    "'Следует отметить', 'Необходимо подчеркнуть', 'Нельзя не отметить', "
    "'В целом можно сказать', 'Таким образом', 'Исходя из вышесказанного', "
    "'В данном контексте', 'Особо следует выделить', 'Имеет важное значение'.\n"
    "2. ПОСТОЯННО чередуй длину предложений: длинное, потом короткое, потом среднее. "
    "Никакого монотонного ритма.\n"
    "3. Абзацы НЕ должны быть одинаковой структуры — один начинай с вопроса, "
    "другой с факта, третий с примера.\n"
    "4. Используй живой академический язык — как настоящий профессор рассказывает, "
    "но с научной основой.\n"
    "5. Избегай чрезмерного совершенства — настоящие люди иногда используют простые слова.\n"
    "6. НЕ начинай каждый абзац одинаково — каждый раз новое, неожиданное начало.\n"
)

HUMANIZER_RULES_EN = (
    "\n\nMOST IMPORTANT RULE — WRITE LIKE A HUMAN (ANTI-PLAGIARISM):\n"
    "Nobody should be able to tell this was written by AI. "
    "STRICTLY follow these rules:\n"
    "1. NEVER use these AI-cliche phrases: "
    "'In conclusion', 'It is worth noting', 'It is important to note', "
    "'It should be noted', 'It is crucial to emphasize', "
    "'Overall', 'Furthermore', 'Moreover', 'In this context', "
    "'It is significant that', 'One cannot overstate'.\n"
    "2. CONSTANTLY vary sentence length: long, then short, then medium. "
    "No monotonous rhythm.\n"
    "3. Paragraphs should NOT have identical structure — start one with a question, "
    "another with a fact, another with an example.\n"
    "4. Use natural academic language — like a real professor explains, "
    "but with scientific basis.\n"
    "5. Avoid excessive perfection — real people sometimes use simple words.\n"
    "6. Do NOT start every paragraph the same way — each time a new, unexpected opening.\n"
)

def _get_humanizer_rules(language: str) -> str:
    """Return humanizer rules in the appropriate language."""
    if language in ("ru", "русский", "На русском языке"):
        return HUMANIZER_RULES_RU
    elif language in ("en", "English", "In English"):
        return HUMANIZER_RULES_EN
    return HUMANIZER_RULES_UZ

# Short version for slides/presentations (less text, so shorter rules)
HUMANIZER_SLIDES = (
    "ANTI-PLAGIAT QOIDA: Matnni haqiqiy inson yozgandek tabiiy bo'lsin. "
    "'Xulosa qilib aytganda', 'Ta'kidlash joizki', 'Muhim jihati shundaki', "
    "'Shuni aytish kerakki', 'Umuman olganda', 'Bu bo'limda ... o'rganiladi', "
    "'Bu bo'limda ... ko'rib chiqiladi', 'Ushbu bo'limda', 'misollar orqali o'rganiladi' "
    "kabi AI-shablon iboralarni UMUMAN ISHLATMA! "
    "Har bir punkt — tabiiy, jonli va o'ziga xos bo'lsin.\n"
)

# Claude client (primary)
_claude_client = None
if ANTHROPIC_API_KEY:
    try:
        import anthropic
        _claude_client = anthropic.AsyncAnthropic(api_key=ANTHROPIC_API_KEY)
        logger.info(f"✅ Claude initialized: {CLAUDE_MODEL}")
    except ImportError:
        logger.warning("anthropic package not installed, using OpenAI only")


async def _call_claude(messages, max_tokens=3000, temperature=0.8, json_mode=False):
    """Call Claude API with Extended Thinking + Prompt Caching."""
    if not _claude_client:
        raise RuntimeError("Claude not available")

    import re

    # Extract system message
    system_text = ""
    user_messages = []
    for m in messages:
        if m["role"] == "system":
            system_text += m["content"] + "\n"
        else:
            user_messages.append(m)

    if not user_messages:
        user_messages = [{"role": "user", "content": "..."}]

    if json_mode:
        system_text += (
            "\n\nMUHIM QOIDA: Javobingda FAQAT JSON yoz. "
            "Markdown (```), izoh yoki boshqa matn QOSHMA. "
            "Javob { yoki [ bilan boshlanishi SHART."
        )

    kwargs = {
        "model": CLAUDE_MODEL,
        "max_tokens": max_tokens,
        "messages": user_messages,
    }

    # Prompt Caching: cache system prompt (saves 90% on repeated calls)
    if system_text.strip():
        kwargs["system"] = [
            {
                "type": "text",
                "text": system_text.strip(),
                "cache_control": {"type": "ephemeral"},
            }
        ]

    # Extended Thinking: Claude thinks before answering (better quality)
    # Note: thinking requires temperature=1 and uses budget_tokens
    use_thinking = (max_tokens >= 1500 and not json_mode)
    if use_thinking:
        kwargs["temperature"] = 1  # required for thinking
        kwargs["thinking"] = {
            "type": "enabled",
            "budget_tokens": min(2000, max_tokens // 2),
        }
        kwargs["max_tokens"] = max_tokens + 2000  # extra room for thinking
    else:
        kwargs["temperature"] = temperature

    resp = await _claude_client.messages.create(**kwargs)

    # Extract text from response (skip thinking blocks)
    content = ""
    for block in resp.content:
        if block.type == "text":
            content = block.text
            break

    if not content:
        raise ValueError("Claude returned empty content")

    content = content.strip()

    # Clean JSON: remove markdown wrappers if present
    if json_mode:
        content = re.sub(r'^```(?:json)?\s*', '', content)
        content = re.sub(r'\s*```\s*$', '', content)
        content = content.strip()

    return content


async def _call_openai(messages, max_tokens=3000, temperature=0.8, json_mode=False):
    """Call OpenAI API."""
    kwargs = {
        "model": OPENAI_MODEL,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
    }
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}
    resp = await openai_client.chat.completions.create(**kwargs)
    content = resp.choices[0].message.content
    if content is None:
        raise ValueError("OpenAI returned None content")
    return content.strip()


async def _call_ai(messages, max_tokens=3000, temperature=0.8, json_mode=False, retries=2):
    """Call Claude (primary) → OpenAI (fallback) with retries."""
    # Try Claude first
    if _claude_client:
        for attempt in range(retries):
            try:
                result = await _call_claude(messages, max_tokens, temperature, json_mode)
                return result
            except Exception as e:
                logger.warning(f"Claude attempt {attempt+1}/{retries} failed: {e}")
                if attempt < retries - 1:
                    await asyncio.sleep(1)
        logger.warning("Claude failed, falling back to OpenAI...")
    
    # Fallback to OpenAI
    for attempt in range(retries):
        try:
            result = await _call_openai(messages, max_tokens, temperature, json_mode)
            return result
        except Exception as e:
            logger.warning(f"OpenAI attempt {attempt+1}/{retries} failed: {e}")
            if attempt < retries - 1:
                await asyncio.sleep(2 ** attempt)
            else:
                raise

async def generate_document_plan(service_type: str, topic: str, language: str = "uz", detail_level: str = "standard", num_chapters: int = 2, num_subchapters: int = 2) -> dict:
    lang_map = {"uz": "O'zbek tilida", "ru": "На русском языке", "en": "In English"}
    lang_name = lang_map.get(language, "O'zbek tilida")
    if service_type == "coursework":
        prompt = (
            f"Mavzu: {topic}\n"
            f"Til: {lang_name}\n\n"
            "Vazifa: Kurs ishi uchun REJA tuzing.\n"
            "Quyidagi formatda ANIQ yozing (boshqa hech narsa qo'shmang):\n\n"
            "KIRISH\n"
            "1-Bob. [1-bob nomi]\n"
            "1.1. [birinchi paragraf nomi]\n"
            "1.2. [ikkinchi paragraf nomi]\n"
            "1.3. [uchinchi paragraf nomi]\n"
            "2-Bob. [2-bob nomi]\n"
            "2.1. [to'rtinchi paragraf nomi]\n"
            "2.2. [beshinchi paragraf nomi]\n"
            "2.3. [oltinchi paragraf nomi]\n"
            "XULOSA\n"
            "FOYDALANILGAN ADABIYOTLAR\n\n"
            f"Agar mavzuda '{topic}' deb yozilgan bo'lsa, "
            "bob va paragraflar nomlari shu mavzuga mos, ilmiy va professional bo'lsin.\n"
            "FAQAT shu formatda javob bering, boshqa izoh yoki tushuntirish qo'shmang."
        )
    else:
        # Build dynamic referat structure
        plan_structure = "KIRISH\n"
        romans = {1: 'I', 2: 'II', 3: 'III', 4: 'IV', 5: 'V', 6: 'VI'}
        for i in range(1, num_chapters + 1):
            roman = romans.get(i, str(i))
            plan_structure += f"{roman} BOB. [{i}-bob umumiy nomi]\n"
            for j in range(1, num_subchapters + 1):
                plan_structure += f"{i}.{j}. [{i}-bob, {j}-bo'lim nomi]\n"
        plan_structure += "XULOSA\nFOYDALANILGAN ADABIYOTLAR\n\n"

        prompt = (
            f"Mavzu: {topic}\n"
            f"Til: {lang_name}\n\n"
            "Vazifa: Referat uchun REJA tuzing.\n"
            "Quyidagi formatda ANIQ yozing (boshqa hech narsa qo'shmang):\n\n"
            f"{plan_structure}"
            f"Mavzu: '{topic}' — bo'lim nomlari shu mavzuga mos, ilmiy va aniq bo'lsin.\n"
            "QOIDALAR:\n"
            "- Markdown belgilari (**yulduzcha**, # kabi) ISHLATMA\n"
            "- Faqat oddiy matn, boshqa izoh yoki tushuntirish qo'shma\n"
            "- Bo'lim nomlari qisqa va aniq bo'lsin (5-10 so'z)"
        )
    try:
        plan_text = await _call_ai(
            [{"role": "user", "content": prompt}],
            max_tokens=500, temperature=0.7
        )
    except Exception:
        response = await client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[{"role": "user", "content": prompt}]
        )
        plan_text = response.choices[0].message.content.strip()
    return {"plan": plan_text}

async def generate_document_section(topic: str, section_title: str, extra_details: str = "", language: str = "uz", quality: str = "standard", service_type: str = "") -> str:
    is_pro = (quality == "pro")
    is_coursework = (service_type == "coursework")
    lang_map = {"uz": "O'zbek tilida (lotin)", "ru": "На русском языке", "en": "In English"}
    lang_name = lang_map.get(language, "O'zbek tilida")
    
    if is_coursework:
        refs_rule = (
            " Manbalar (havolalar) FAQAT o'zbek mualliflari va O'zbekiston nashriyotlariga "
            "tegishli bo'lsin. Masalan: '[1] Karimov A. Iqtisodiyot asoslari. - T.: Fan, 2022.' kabi. "
            "Matn ichida keltirilgan statistik ma'lumotlar yoki olimlarning fikrlariga kvadrat qavsda (masalan: [4, 25-b]) havola berib keting. "
            "Foydalanilgan adabiyotlar (manbalar) real, ishonchli va mavzuga mos bo'lsin."
        )
    else:
        refs_rule = " Matn ichida HECH QANDAY kvadrat qavsli havolalar (masalan: [4, 25-b]) aslo ishlata ko'rmang!"
    
    humanizer = _get_humanizer_rules(language)

    if is_pro:
        style_instruction = (
            "Siz fan doktori, professor darajasidagi akademik yozuvchisiz. "
            "Matnni juda yuqori ilmiy saviyada, chuqur tahliliy yondashuvda yozing. "
            "Har bir fikrni dalillar va statistik ma'lumotlar bilan asoslang. "
            "Turli olimlar va tadqiqotchilarning fikrlarini keltiring va taqqoslang. "
            "Matn akademik jargon va ilmiy terminologiyaga boy bo'lsin."
            + refs_rule
            + humanizer
        )
    else:
        style_instruction = (
            "Siz tajribali akademik yozuvchisiz. "
            "Matn tushunarli, mantiqiy va akademik uslubda bo'lsin. "
            "Asosiy fikrlarni misollar va dalillar bilan izohlang. "
            "Professional akademik til ishlating."
            + refs_rule
            + humanizer
        )
    xulosa_rule = ""
    if "xulosa" in section_title.lower():
        xulosa_rule = (
            "3. DIQQAT: Xulosada faqat foydalanuvchining (talabaning) mavzudan kelib chiqqan holdagi YAKUNIY SHAXSIY FIKRLARI bo'lishi kerak.\n"
            "4. HECH QANDAY adabiyotlarga yoki olimlarga havola (kvadrat qavsli tsitatalar) aslo ISHLATILMASIN!\n"
            "5. Yangi dalillar yoki avval aytilmagan ma'lumotlar kiritilmasin.\n"
        )
    else:
        if is_coursework:
            xulosa_rule = (
                "3. Matn ichida ilmiy manbalarga havolalar (masalan: [4, 25-b]) ALBATTA bo'lsin - har 2-3 abzatsda.\n"
                "4. Statistik ma'lumotlar, foizlar, yillar va aniq raqamlar keltiring (masalan: '2023-yil holatiga ko'ra...').\n"
                "5. Turli olimlarning fikrlarini keltiring va taqqoslang (masalan: 'Professor X ta'kidlashicha...').\n"
            )
        else:
            xulosa_rule = (
                "3. HECH QANDAY ilmiy manbalarga havola yoki kvadrat qavsli tsitatalar (masalan: [4, 25-b]) ISHLATILMASIN.\n"
                "4. Statistik ma'lumotlar, foizlar, yillar ishlating, lekin ularga qavs ichida manba ko'rsatmang.\n"
                "5. Matn ravon o'qilishi kerak, huddi bitta odam o'z tajribasidan yozgandek.\n"
            )

    if "adabiyot" in section_title.lower():
        base_rules = (
            "1. VAZIFA: Faqat raqamlangan adabiyotlar ro'yxatini (1, 2, 3...) yarating.\n"
            "2. HECH QANDAY odatiy matn, abzats, izoh yoki sarlavha yozmang. Faqat kitoblar/manbalar ro'yxati bo'lsin.\n"
        )
    else:
        base_rules = (
            "1. Matn faqat oddiy abzatslardan iborat bo'lsin. Raqamli ro'yxatlar (1), 2), a), b) va hokazo) ISHLATMA.\n"
            "2. Har bir bo'limda kamida 5-7 abzats matn bo'lishi SHART. Har bir abzats 4-6 jumladan iborat bo'lsin.\n"
        )

    anti_hallucination_rule = (
        "DIQQAT: Mavzuning ma'nosini to'g'ri tahlil qiling. Asossiz narsalarni o'ylab topmang (gallyutsinatsiya qilmang). "
        "Masalan, agar mavzu kasb, insonlar yoki tarix haqida bo'lsa, uni asossiz ravishda geografik joy yoki tabiat hodisasi deb yozmang. "
        "Matnni FAQAT toza O'zbek tilida yozing. Inglizcha yoki boshqa tildagi so'zlarni aslo ishlata ko'rmang!"
    )

    prompt = (
        f"Mavzu: {topic}\n"
        f"Bo'lim nomi: {section_title}\n"
        f"Talablar: {extra_details}\n"
        f"Til: {lang_name}\n\n"
        f"USLUB: {style_instruction}\n\n"
        "VAZIFA: Ushbu bo'lim uchun to'liq akademik matn yozing.\n\n"
        "QATIY QOIDALAR:\n"
        f"{base_rules}"
        f"{xulosa_rule}"
        f"{anti_hallucination_rule}\n"
        "6. Faqat matnning o'zini yuboring, qo'shimcha izoh yoki sarlavha qo'shma.\n"
        "7. SO'ZLAR SONI talabga QATIY javob bersin - agar X so'z talab qilinsa, AYNAN X so'z yozish SHART. Kam bo'lsa yangi abzatslar qo'shib UZAYTIR.\n"
        "8. Matn professional, chuqur va to'liq bo'lsin.\n"
        "9. DIQQAT: Oddiy boblar oxiriga (KIRISH, XULOSA, ASOSIY QISM) adabiyotlar ro'yxatini QO'SHMANG! Adabiyotlar ro'yxati (1, 2, 3...) FAQAT 'FOYDALANILGAN ADABIYOTLAR' nomli eng oxirgi bo'limda berilishi shart. Hech qachon ikkita o'xshash nomli adabiyotlar bo'limi yaratmang.\n"
        "10. Rasm placeholder yoki '[ SHU YERGA RASM JOYLANG: ... ]' kabi narsalar QOSHMA."
    )

    try:
        result = await _call_ai(
            [{"role": "system", "content": style_instruction},
             {"role": "user", "content": prompt}],
            max_tokens=4000, temperature=0.8
        )
    except Exception:
        response = await client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[{"role": "system", "content": style_instruction},
                      {"role": "user", "content": prompt}]
        )
        result = response.choices[0].message.content.strip()

    # Clean up duplicate headers: if AI started its response with the section title, remove it
    clean_title = section_title.lower().strip()
    result_lines = result.split('\n')
    while result_lines and (not result_lines[0].strip() or clean_title in result_lines[0].lower().replace('*', '').replace('#', '').strip()):
        result_lines.pop(0)

    # Prevent AI from hallucinating a bibliography inside a regular section!
    # If the text contains "FOYDALANILGAN ADABIYOTLAR" or "ADABIYOTLAR RO'YXATI", we cut it off!
    cleaned_lines = []
    for line in result_lines:
        upper_line = line.upper().replace('*', '').replace('#', '').strip()
        if "FOYDALANILGAN ADABIYOTLAR" in upper_line or "ADABIYOTLAR RO'YXATI" in upper_line:
            # Found a hallucinated bibliography header, stop adding lines
            break
        cleaned_lines.append(line)

    return '\n'.join(cleaned_lines).strip()

async def generate_presentation_plan(topic, slides, language="uz"):
    prompt = f"Mavzu: {topic}, Slaydlar soni: {slides}, Til: {language}. Taqdimot rejasini tuzing."
    response = await client.chat.completions.create(model=OPENAI_MODEL, messages=[{"role": "user", "content": prompt}])
    return response.choices[0].message.content.strip()


async def generate_presentation_content(topic, language="uz", num_slides=10, style="standard", quality="standard", num_chapters=4, forced_titles=None, progress_callback=None):
    is_premium = (quality == "premium")
    kb_context = ""
    slides_data = []

    total_steps = num_slides + 2  

    if progress_callback:
        try:
            await progress_callback(0, total_steps, "Mavzuni chuqur tahlil qilish (Mini-tadqiqot)...")
        except Exception:
            pass

    # ==========================================
    # ETAP 1: ANALIZ TEMI (DEEP RESEARCH)
    # ==========================================
    research_text = ""
    if is_premium:
        analysis_prompt = (
            f"{kb_context}\n"
            f"Mavzu: {topic}\nTil: {language}\n\n"
            "VAZIFA: Ushbu mavzu bo'yicha juda chuqur akademik va analitik tadqiqot (mini-research) o'tkazing.\n"
            "Ushbu tadqiqot keyinchalik yuqori sifatli taqdimot tayyorlash uchun asos (poydevor) bo'ladi.\n\n"
            "Tadqiqot quyidagilarni o'z ichiga olishi shart:\n"
            "1. Tarixiy va nazariy kontekst\n"
            "2. Eng muhim faktlar, sanalar va statistik ma'lumotlar\n"
            "3. Amaliy misollar va global / mahalliy bozor yoki jamiyatga ta'siri\n"
            "4. Milliy manfaatlar va davlat xavfsizligi jihatlari (O'zbekiston kontekstida)\n"
            "5. Turli xil qarashlar yoki muammoli jihatlar\n\n"
            "Kamida 600-800 so'zdan iborat to'liq matn yozing."
        )
        try:
            research_text = await _call_ai(
                [{"role": "user", "content": analysis_prompt}],
                max_tokens=3000, temperature=0.8
            )
        except Exception as e:
            logger.error(f"Research failed: {e}")
            research_text = "Tadqiqot ma'lumotlari topilmadi."
    else:
        research_text = "Asosiy faktlarga tayangan holda standart ma'lumotlar."

    if progress_callback:
        try:
            await progress_callback(1, total_steps, "Struktura va slaydlar rejasini tuzish...")
        except Exception:
            pass

    # ==========================================
    # ETAP 2: SOSTAVLENIE PLANA
    # ==========================================
    if forced_titles:
        chapters = []
        for t in forced_titles:
            clean_t = t.split('(')[0].strip()
            if clean_t not in chapters:
                chapters.append(clean_t)
    else:
        plan_sys = (
            "Siz professional metodist va akademik tuzuvchisiz. "
            "Taqdimot uchun eng mantiqiy va izchil strukturani ishlab chiqasiz."
        )
        plan_prompt = (
            f"Mavzu: {topic}\nTil: {language}\n\n"
            f"Tadqiqot bazasi:\n{research_text[:1500]}\n\n"
            f"ANIQ {num_chapters} ta bo'lim nomi yoz. Kam bo'lmasin, ko'p bo'lmasin.\n"
            f"Har bir bo'lim alohida qatorda, raqam bilan:\n"
            f"1. Birinchi bo'lim\n"
            f"2. Ikkinchi bo'lim\n"
            f"...\n"
            f"{num_chapters}. Oxirgi bo'lim\n\n"
            f"FAQAT {num_chapters} ta raqamlangan bo'lim yoz, boshqa hech narsa qo'shma."
        )
        try:
            plan_text = await _call_ai(
                [{"role": "system", "content": plan_sys}, {"role": "user", "content": plan_prompt}],
                max_tokens=500, temperature=0.7
            )
            import re
            # Parse numbered list (1. xxx) or comma-separated
            lines = [l.strip() for l in plan_text.replace(',', '\n').split('\n') if l.strip()]
            chapters = []
            for l in lines:
                clean = re.sub(r'^[\d]+[\.\)\-\s]+', '', l).strip().strip('"\'')
                if clean and len(clean) > 2:
                    chapters.append(clean)
            chapters = chapters[:num_chapters]
        except Exception as e:
            logger.error(f"Plan generation failed: {e}")
            chapters = ["Asosiy tushunchalar", "Tahlil va metodologiya", "Amaliy ahamiyati"]

        if not chapters:
            chapters = ["Asosiy tushunchalar", "Tahlil va metodologiya", "Amaliy ahamiyati"]

    # ──────────────────────────────────────────────────────────────
    # NEW ACADEMIC STRUCTURE: Cover(1) + Iqtibos(1) + Maqsadlar(1) + O'quv savollari(1) + Adabiyotlar(1) + [Header + Info + Mini-Xulosa] per chapter + Umumiy Xulosa(1) + Rahmat(1)
    # ──────────────────────────────────────────────────────────────
    fixed_overhead = 6  # iqtibos, maqsadlar, o'quv_savollari, adabiyotlar, umumiy xulosa, rahmat
    slots_for_chapters = max(3, num_slides - fixed_overhead)
    # Each chapter needs at least: Header(1) + Info(1) + Conclusion(1) = 3 slides
    optimal_chapters = max(1, slots_for_chapters // 3)

    if len(chapters) > optimal_chapters:
        chapters = chapters[:optimal_chapters]

    # Set info_per_chapter to 2 for exactly 3 slides per chapter (1 header + 2 info)
    info_per_chapter = [2] * len(chapters)
    
    # Calculate total steps. 1 header + ipc info slides for each chapter
    total_steps = fixed_overhead + sum(1 + ipc for ipc in info_per_chapter) + 1

    # ==========================================
    # ETAP 3 & 4: KONTENT VA ADAPTATSIYA (SLAYD GENERATION)
    # ==========================================

    advanced_designer_rules = (
        "SEN PROFESSIONAL DIZAYNERSAN! Quyidagi qoidalarga QAT'IY amal qil:\n\n"
        "1. ROL: Ma'lumotni slaydlarga chiroyli taqsimlaysan.\n"
        "2. HAR BIR SLAYD = 1 ta asosiy g'oya.\n"
        "3. Punktlar soni: 3-5 ta. Har biri FAQAT 3-6 SO'ZDAN iborat bo'lsin!\n"
        "4. UZUN GAPLAR YOZMA! Faqat qisqa iboralar, xuddi taqdimotchi yozgandek.\n"
        "5. STATISTIKA va FAKTLAR ishlat — raqamlar, foizlar, yillar bilan boyit.\n"
        "6. Har bir slayd OLDINGI slaydning mantiqiy davomi bo'lsin.\n"
        "7. SARLAVHALAR qiziqarli va ilhomli bo'lsin, quruq emas!\n"
        "8. Soha bo'yicha REAL misollar keltir (mamlakatlar, kompaniyalar, hodisalar).\n"
        "9. Matn ichida qo'shtirnoq (\") ISHLATMA, faqat (')\n"
        "10. MUHIM: Har bir slaydda 1-2 ta eng muhim kalit so'zlarni yoki iboralarni **orasiga olib yozing (masalan, **muhim so'z**). Bu taqdimotda rangli qilib ajratiladi.\n"
        "11. image_keyword — INGLIZ tilida rasm qidirish uchun kalit so'z yoz.\n"
        f"12. {HUMANIZER_SLIDES}\n"
    )

    if is_premium:
        system_persona = (
            f"{kb_context}\n"
            "Siz dunyo miqyosidagi akademik professor, tahlilchi va dizaynersiz.\n"
            f"{advanced_designer_rules}"
        )
        max_tok = 3000
        temp = 0.9
    else:
        system_persona = (
            f"{kb_context}\n"
            "Siz malakali o'qituvchi, dizayner va kontent-meykersiz.\n"
            f"{advanced_designer_rules}"
        )
        max_tok = 2500
        temp = 0.8

    import json
    completed_steps = 1

    # ── 1. IQTIBOS slide (Slayd 2) ─────────────────────────────
    if progress_callback:
        try: await progress_callback(completed_steps, total_steps, "Iqtibos tanlanmoqda...")
        except: pass
        
    q_prompt = (
        f"Mavzu: {topic}\nTil: {language}\n"
        "O'zbekiston Respublikasi Prezidenti Shavkat Mirziyoyevning aynan ushbu mavzuga "
        "(yoki unga yaqin bo'lgan ta'lim, fan, yoshlar, taraqqiyot sohasiga) oid eng mos va ta'sirli iqtibosini keltiring.\n"
        "Iqtibos qisqa va aniq bo'lsin.\n"
        "FAQAT JSON: {\"content\": [\"Iqtibos matni...\", \"- Shavkat Mirziyoyev\"]}"
    )
    try:
        raw_q = await _call_ai([{"role": "user", "content": q_prompt}], max_tokens=1000, temperature=0.7, json_mode=True)
        q_data = json.loads(raw_q)
        q_content = q_data.get("content") or q_data.get("points") or ["Yangi O'zbekistonni barpo etishda biz, eng avvalo, yoshlarga, ularning kuch-g'ayratiga tayanamiz.", "- Shavkat Mirziyoyev"]
        
        slides_data.append({
            "title": "IQTIBOS",
            "content": q_content,
            "image_keyword": "Shavkat Mirziyoyev president of Uzbekistan portrait",
            "needs_image": True
        })
    except Exception:
        slides_data.append({
            "title": "IQTIBOS",
            "content": ["Yangi O'zbekistonni barpo etishda biz, eng avvalo, yoshlarga, ularning kuch-g'ayratiga tayanamiz.", "- Shavkat Mirziyoyev"],
            "image_keyword": "Shavkat Mirziyoyev president of Uzbekistan portrait",
            "needs_image": True
        })
    completed_steps += 1

    # ── 2. MAQSADLAR slide (Slayd 3) ───────────────────────────
    if progress_callback:
        try: await progress_callback(completed_steps, total_steps, "O'quv maqsadlari yozilmoqda...")
        except: pass
        
    m_prompt = (
        f"Mavzu: {topic}\nTil: {language}\n"
        "Ushbu taqdimot uchun 3-4 ta O'quv-tarbiyaviy maqsadlarni qisqa yozib bering.\n"
        "FAQAT JSON: {\"title\": \"O'quv-tarbiyaviy maqsadlar\", \"content\": [\"1...\", \"2...\"]}"
    )
    try:
        raw = await _call_ai([{"role": "user", "content": m_prompt}], max_tokens=1000, temperature=0.7, json_mode=True)
        m_data = json.loads(raw)
        m_data["title"] = "O'quv-tarbiyaviy maqsadlar"
        if "points" in m_data and "content" not in m_data: m_data["content"] = m_data.pop("points")
        slides_data.append(m_data)
    except Exception:
        slides_data.append({"title": "O'quv-tarbiyaviy maqsadlar", "content": ["Mavzuni chuqur o'rganish", "Amaliy ko'nikmalarni shakllantirish"]})
    completed_steps += 1

    # ── 3. O'QUV SAVOLLARI slide (Slayd 4) ─────────────────────
    items = [f"{idx+1}. {c}" for idx, c in enumerate(chapters)]
    slides_data.append({"title": "O'quv savollari", "content": items})
    completed_steps += 1



    # ── 5. CHAPTER SLIDES (Header + Info + Mini-Conclusion) ──────
    for ch_idx, chapter in enumerate(chapters):
        num_info = info_per_chapter[ch_idx]

        # 5.1 HEADER SLIDE
        slides_data.append({
            "title": f"{ch_idx+1}-o'quv savoli",
            "content": [chapter],
            "needs_image": True,
            "image_keyword": f"Abstract dramatic cinematic background for topic: {chapter}"
        })
        
        # 5.2 INFO SLIDES
        ch_prompt = (
            f"Mavzu: {topic}\nBo'lim: {chapter}\nTil: {language}\n\n"
            f"Tadqiqot bazasi:\n{research_text[:1500]}\n\n"
            f"Ushbu bo'lim uchun {num_info} ta BATAFSIL ma'lumot slaydi yarat:\n\n"
            f"Har bir slaydda alohida qiziqarli sub-mavzu bo'lsin.\n"
            f"content: 2-4 ta batafsil punkt (har biri 30-50 so'z)\n"
            f"image_keyword: ingliz tilida rasm kalit so'zi\n\n"
            "FAQAT JSON formatida javob ber (array):\n"
            "[\n  {\"title\": \"...\", \"content\": [\"...\"], \"image_keyword\": \"...\"}\n]"
        )
        try:
            raw = await _call_ai([{"role": "system", "content": system_persona}, {"role": "user", "content": ch_prompt}], max_tokens=max_tok + 1000, temperature=temp, json_mode=True)
            clean = raw.replace("```json", "").replace("```", "").strip()
            ch_slides = json.loads(clean)
            if isinstance(ch_slides, dict): ch_slides = ch_slides.get("slides", [ch_slides])
            
            for s_idx, s in enumerate(ch_slides[:num_info]):
                s["section_label"] = f"{ch_idx+1}-o'quv savoli"
                if "points" in s and "content" not in s: s["content"] = s.pop("points")
                s["needs_image"] = True
                slides_data.append(s)
                
            # Fallback padding
            for pad_idx in range(len(ch_slides), num_info):
                slides_data.append({"title": f"{chapter} — {pad_idx+1}-qism", "content": [f"'{chapter}' bo'yicha ma'lumot."], "section_label": f"{ch_idx+1}-o'quv savoli", "needs_image": True})
        except Exception as e:
            logger.error(f"Chapter '{chapter}' generation failed: {e}")
            for j in range(num_info):
                slides_data.append({"title": f"{chapter} — {j+1}-qism", "content": [f"'{chapter}' bo'yicha ma'lumot."], "section_label": f"{ch_idx+1}-o'quv savoli", "needs_image": True})

        completed_steps += (num_info + 1)
        if progress_callback:
            try: await progress_callback(completed_steps, total_steps, f"{ch_idx+1}-qism tayyor")
            except: pass

    # ── 4. XULOSA slide ───────────────────────────────────────
    x_rule = (
        "Xulosa juda chuqur va professional bo'lsin. Kamida 3 ta yirik punkt: "
        "(1) Asosiy topilmalarni jamlash, (2) Amaliy va nazariy ahamiyati, (3) Kelajakdagi istiqbollar. "
        "Eng asosiysi: Xulosa FOYDALANUVCHI (TALABA) nomidan, ya'ni I-shaxs ko'pligida ('biz shunday xulosaga keldikki', 'tahlillarimiz shuni ko'rsatadiki', 'bizningcha') yozilishi shart! Quruq ensiklopediya tilida yozmang."
    ) if is_premium else (
        "Ikki yirik punkt: (1) asosiy natijalar va (2) ahamiyat. "
        "Eng asosiysi: Xulosa FOYDALANUVCHI nomidan ('bizningcha', 'xulosa qilib aytganda') yozilishi shart!"
    )

    x_prompt = (
        f"Mavzu: {topic}\nTil: {language}\n"
        f"Tadqiqot bazasi: {research_text[:1000]}...\n\n"
        "Ushbu taqdimotning barcha qismlarini jamlovchi Umumiy Xulosa tayyorlang.\n"
        f"QOIDALAR: {x_rule}\n"
        "- FAQAT JSON formatida javob bering:\n"
        "{\"title\": \"Umumiy Xulosa\", \"content\": [\"1-punkt...\", \"2-punkt...\", \"...\"]}"
    )
    try:
        raw = await _call_ai(
            [{"role": "system", "content": system_persona}, {"role": "user", "content": x_prompt}],
            max_tokens=max_tok, temperature=temp, json_mode=True
        )
        data = json.loads(raw)
        data["title"] = "Umumiy Xulosa"
        if "points" in data and "content" not in data:
            data["content"] = data.pop("points")
        slides_data.append(data)
    except Exception as e:
        logger.error(f"Xulosa generation failed: {e}")
        slides_data.append({"title": "Umumiy Xulosa", "content": [
            "Ushbu mavzuni chuqur o'rganish va tahlil qilish natijasida shunday xulosaga keldikki, mazkur yo'nalish kelajakda yanada kengroq o'rganishni talab etadi.",
            "O'tkazilgan tahlillarimiz va o'rganilgan adabiyotlar shuni ko'rsatadiki, bu sohada amaliy tadqiqotlarni davom ettirish jamiyatimiz uchun muhim ahamiyat kasb etadi."
        ]})

    # ── ADABIYOTLAR slide (Oxirida) ─────────────────────────
    if progress_callback:
        try: await progress_callback(completed_steps, total_steps, "Adabiyotlar ro'yxati...")
        except: pass

    a_prompt = (
        f"Mavzu: {topic}\nTil: {language}\n"
        "Ushbu mavzu bo'yicha AYNAN MAVZUGA MOS va ISHONCHLI 4-5 ta haqiqiy akademik adabiyotlar (kitoblar, darsliklar yoki ilmiy maqolalar, mualliflari va yili bilan) ro'yxatini shakllantiring.\n"
        "Adabiyotlar to'qima bo'lmasin, soha bo'yicha nufuzli manbalar bo'lishi shart.\n"
        "FAQAT JSON: {\"content\": [\"1. Muallif. Kitob nomi. Yil\", \"2. ...\"]}"
    )
    try:
        raw = await _call_ai([{"role": "user", "content": a_prompt}], max_tokens=1000, temperature=0.7, json_mode=True)
        a_data = json.loads(raw)
        
        q_content = a_data.get("content") or a_data.get("points")
        if not q_content:
            raise ValueError("No content found")
            
        slides_data.append({
            "title": "Foydalanilgan adabiyotlar",
            "content": q_content
        })
    except Exception:
        slides_data.append({"title": "Foydalanilgan adabiyotlar", "content": [
            "1. Oliy ta'lim muassasalari fan dasturi asosidagi o'quv adabiyotlari",
            "2. Mavzuga doir xalqaro va milliy ilmiy maqolalar",
            "3. Ziyonet.uz va milliy elektron kutubxona manbalari"
        ]})
    completed_steps += 1

    # ── 5. RAHMAT slide ───────────────────────────────────────
    slides_data.append({
        "title": "E'tiboringiz uchun rahmat!",
        "content": ["Taqdimot bo'yicha savollaringiz bo'lsa, marhamat."],
        "needs_image": False,
        "is_final": True
    })

    completed_steps += 1
    if progress_callback:
        try: await progress_callback(completed_steps, total_steps, "Sifat nazorati")
        except: pass

    # ==========================================
    # ETAP 5: FINAL TEKSHIRUV (VALIDATION)
    # ==========================================
    for slide in slides_data:
        if "content" not in slide or not isinstance(slide.get("content"), list) or len(slide.get("content", [])) == 0:
            if "points" in slide and isinstance(slide["points"], list):
                slide["content"] = slide["points"]
            else:
                slide["content"] = ["Ma'lumotlar qayta ishlanmoqda..."]

    completed_steps += 1
    if progress_callback:
        try: await progress_callback(completed_steps, total_steps, "")
        except: pass

    return json.dumps({"slides": slides_data}, ensure_ascii=False)


async def generate_akademik_content(
    topic: str,
    language: str = "uz",
    subject_name: str = "",
    completed_by: str = "",
    training_session: str = "",
    quality: str = "standard",
    progress_callback=None,
) -> dict:
    """
    Generate structured content for akademik template.
    Returns a dict with all required tag values:
      TOPIC, SUBJECT_NAME, COMPLETED_BY, TRAINING_SESSION,
      EDUCATIONAL_GOALS, STUDY_QUESTIONS,
      QUESTION_1, QUESTION_1_CONTENT, QUESTION_1_CONCLUSION,
      QUESTION_2, QUESTION_2_CONTENT, QUESTION_2_CONCLUSION,
      QUESTION_3, QUESTION_3_CONTENT,
      GENERAL_CONCLUSION, REFERENCES_LIST
    """
    lang_name = {"uz": "o'zbek", "ru": "русский", "en": "English"}.get(language, "o'zbek")

    total_steps = 4
    completed = 0

    # Step 1: Generate the 3 questions and educational goals
    if progress_callback:
        try: await progress_callback(completed, total_steps, "Mavzuni tahlil qilish...")
        except: pass

    humanizer = _get_humanizer_rules(language)
    system_prompt = f"""Sen akademik professor va pedagogsan. Vazifang — berilgan mavzu bo'yicha ta'lim mashg'ulotining to'liq mazmunini tayyorlash.
Til: {lang_name}. 

FAQAT JSON formatida javob ber! Hech qanday izoh, tushuntirish yoki boshqa matn yozma!

JSON strukturasi:
{{
  "EDUCATIONAL_GOALS": "Mashg'ulotning ta'limiy maqsadlari (3-4 ta aniq maqsad, nuqtali vergul bilan ajratilgan)",
  "STUDY_QUESTIONS": "3 ta o'quv savolining nomlari (raqamlangan ro'yxat sifatida)",
  "QUESTION_1": "Birinchi o'quv savolining sarlavhasi",
  "QUESTION_1_CONTENT": "Birinchi o'quv savoli bo'yicha to'liq, chuqur ilmiy matn. Kamida 200 so'z. Akademik uslubda, dalillar va misollar bilan.",
  "QUESTION_1_CONCLUSION": "Birinchi savolga xulosa (2-3 jumlada)",
  "QUESTION_2": "Ikkinchi o'quv savolining sarlavhasi",
  "QUESTION_2_CONTENT": "Ikkinchi o'quv savoli bo'yicha to'liq, chuqur ilmiy matn. Kamida 200 so'z.",
  "QUESTION_2_CONCLUSION": "Ikkinchi savolga xulosa (2-3 jumlada)",
  "QUESTION_3": "Uchinchi o'quv savolining sarlavhasi",
  "QUESTION_3_CONTENT": "Uchinchi o'quv savoli bo'yicha to'liq, chuqur ilmiy matn. Kamida 200 so'z.",
  "GENERAL_CONCLUSION": "Umumiy xulosa — mavzuni yakunlovchi chuqur tahlil (4-5 jumla)",
  "REFERENCES_LIST": "5-7 ta akademik manba (kitoblar, maqolalar). Har birini yangi qatordan yozing."
}}

QOIDALAR:
1. Har bir CONTENT maydoni kamida 200 so'z bo'lishi SHART
2. Akademik, ilmiy uslubda yozing
3. Har bir javob faqat shu mavzuga tegishli bo'lsin
4. Faqat JSON qaytar, boshqa hech narsa yozma
{humanizer}"""

    user_prompt = f"Mavzu: {topic}"

    try:
        response = await _call_ai(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=4000,
            temperature=0.7,
            json_mode=True
        )
        
        completed = 2
        if progress_callback:
            try: await progress_callback(completed, total_steps, "Ma'lumotlar tahlil qilinmoqda...")
            except: pass

        # Parse JSON response
        clean = response.replace("```json", "").replace("```", "").strip()
        content = json.loads(clean)

    except Exception as e:
        logger.error(f"Akademik AI generation failed: {e}")
        # Fallback content
        content = {
            "EDUCATIONAL_GOALS": f"{topic} mavzusini o'rganish va tahlil qilish",
            "STUDY_QUESTIONS": f"1. {topic} asoslari\n2. {topic} amaliyoti\n3. {topic} istiqbollari",
            "QUESTION_1": f"{topic} asoslari",
            "QUESTION_1_CONTENT": f"{topic} mavzusining nazariy asoslari...",
            "QUESTION_1_CONCLUSION": f"{topic} nazariy jihatdan muhim.",
            "QUESTION_2": f"{topic} amaliyoti",
            "QUESTION_2_CONTENT": f"{topic} mavzusining amaliy qo'llanilishi...",
            "QUESTION_2_CONCLUSION": f"{topic} amaliyotda keng qo'llaniladi.",
            "QUESTION_3": f"{topic} istiqbollari",
            "QUESTION_3_CONTENT": f"{topic} mavzusining kelajakdagi rivojlanish yo'nalishlari...",
            "GENERAL_CONCLUSION": f"{topic} mavzusi bo'yicha umumiy xulosa.",
            "REFERENCES_LIST": "1. O'zbekiston Milliy Ensiklopediyasi\n2. Akademik tadqiqotlar jurnali"
        }

    # Add metadata fields
    content["TOPIC"] = topic
    content["SUBJECT_NAME"] = subject_name or topic
    content["COMPLETED_BY"] = completed_by or ""
    content["TRAINING_SESSION"] = training_session or "Ma'ruza mashg'uloti"

    completed = 3
    if progress_callback:
        try: await progress_callback(completed, total_steps, "Yakunlanmoqda...")
        except: pass

    completed = 4
    if progress_callback:
        try: await progress_callback(completed, total_steps, "")
        except: pass

    return content


# ══════════════════════════════════════════════════════════════════════════════
# TEMPLATE-FILL MODE: Generate content tailored to exact template structure
# ══════════════════════════════════════════════════════════════════════════════

async def generate_content_for_template(
    topic: str,
    language: str,
    template_analysis: dict,
    user_material: str = "",
    quality: str = "standard",
    author: str = "",
    forced_titles: list = None,
    num_chapters: int = 4,
    progress_callback=None,
) -> list:
    """
    Generate slide content that perfectly fits a specific template structure.

    Unlike generate_presentation_content(), this function:
    1. Receives the exact template analysis (slide types, text block sizes)
    2. Generates content PER SLIDE, respecting max_words for each block
    3. Auto-shortens/adapts text to physical template constraints
    4. Uses user material (document text) as the knowledge base

    Args:
        topic: presentation topic
        language: uz/ru/en
        template_analysis: dict from TemplateAnalysis.to_dict()
        user_material: extracted text from user's document (if any)
        quality: standard/premium
        author: author name
        progress_callback: async fn(completed, total, next_title)

    Returns:
        list of dicts, one per template slide:
        [{"title": "...", "subtitle": "...", "points": ["...", "..."], "image_keyword": "..."}]
    """
    slides_info = template_analysis.get("slides", [])
    total_slides = len(slides_info)

    if total_slides == 0:
        return []

    lang_name = {"uz": "o'zbek", "ru": "русский", "en": "English"}.get(language, "o'zbek")
    is_premium = quality == "premium"

    # Step 1: Deep analysis of user material
    if progress_callback:
        try:
            await progress_callback(0, total_slides + 2, "Material tahlil qilinmoqda...")
        except:
            pass

    material_context = ""
    if user_material:
        # Truncate material to fit in context
        max_material = 6000 if is_premium else 4000
        material_context = user_material[:max_material]
    
    # Step 2: Generate global plan
    if progress_callback:
        try:
            await progress_callback(1, total_slides + 2, "Slaydlar rejasi tuzilmoqda...")
        except:
            pass

    # Build a detailed description of what AI needs to generate per slide
    slides_spec = []
    any_tagged = False
    for s in slides_info:
        blocks = s.get("text_blocks", [])
        block_desc = []
        slide_tagged = s.get("has_tags", False)
        if slide_tagged:
            any_tagged = True

        for b in blocks:
            role = b["role"]
            mw = b["max_words"]
            all_tags = b.get("all_tags") or []
            tag = b.get("tag")

            # Enforce minimum words for content/body tags so AI writes full paragraphs
            if tag:
                tag_lower = tag.lower()
                if tag_lower.startswith("body") or tag_lower.startswith("content"):
                    mw = max(mw, 30)  # at least 30 words for body/content
                elif tag_lower.startswith("subtitle"):
                    mw = max(mw, 5)

            if all_tags and len(all_tags) > 1:
                # Multiple tags in one shape — report all of them
                tags_str = " + ".join(f"{{{{{t}}}}}" for t in all_tags)
                block_desc.append(f"{tags_str} (max {mw} so'z)")
            elif tag:
                block_desc.append(f"{{{{{tag}}}}} (max {mw} so'z)")
            else:
                block_desc.append(f"{role}: max {mw} so'z")

        img_count = s.get("image_count", 0)
        img_note = f", {img_count} ta rasm joyi" if img_count > 0 else ""

        slides_spec.append(
            f"Slayd {s['index']}: tur={s['slide_type']}, "
            f"bloklar=[{'; '.join(block_desc)}]{img_note}"
        )

    template_spec = "\n".join(slides_spec)

    # System prompt
    # ══════════════════════════════════════════════════════════════════
    # PHASE 1: Generate presentation PLAN (slide titles)
    # ══════════════════════════════════════════════════════════════════
    material_section = ""
    if material_context:
        material_section = (
            f"\nFOYDALANUVCHI MATERIALI:\n```\n{material_context[:3000]}\n```\n"
        )

    section_header_indices = set()
    if forced_titles:
        plan_titles = list(forced_titles)
    else:
        # ── Paired structure: each plan chapter = section header + content slides ──
        # Fixed slides: 1 title + 1 reja + 1 xulosa = 3
        fixed_slides = 3 if total_slides > 5 else 2  # small presentations skip reja
        content_slots = total_slides - fixed_slides
        effective_chapters = min(num_chapters or 4, max(1, content_slots // 2))
        # How many content slides per chapter (at least 1)
        slides_per_chapter = max(1, content_slots // effective_chapters)
        remainder = content_slots - (slides_per_chapter * effective_chapters)

        # Ask AI for chapter names only
        plan_prompt = (
            f"Mavzu: {topic}\nTil: {lang_name}\n"
            f"{material_section}\n"
            f"Shu mavzu bo'yicha {effective_chapters} ta BO'LIM nomi yoz.\n"
            f"Har bir bo'lim nomi NOYOB va TURLICHA bo'lsin.\n\n"
            f"JSON formatida qaytar:\n"
            f'{{"chapters": ["1-bo\'lim nomi", "2-bo\'lim nomi", ...]}}\n'
            f"JAMI ANIQ {effective_chapters} ta bo'lim."
        )
        try:
            plan_raw = await _call_ai(
                [{"role": "system", "content": f"Sen prezentatsiya rejasini tuzuvchisan. Til: {lang_name}."},
                 {"role": "user", "content": plan_prompt}],
                max_tokens=1000, temperature=0.7, json_mode=True,
            )
            if not plan_raw:
                raise ValueError("AI returned empty plan")
            plan_data = json.loads(plan_raw.replace("```json", "").replace("```", "").strip())
            chapter_names = plan_data.get("chapters", plan_data.get("plan", []))
            if not isinstance(chapter_names, list) or len(chapter_names) < 1:
                raise ValueError("Bad plan")
            # Trim to effective_chapters
            chapter_names = chapter_names[:effective_chapters]
            logger.info(f"Phase 1: Generated {len(chapter_names)} chapter names")
        except Exception as e:
            logger.warning(f"Plan generation failed ({e}), using default chapter names")
            chapter_names = [f"{topic} — {i+1}-bo'lim" for i in range(effective_chapters)]

        # ── Build paired plan: title, reja, [header, content...], xulosa ──
        plan_titles = [topic]  # slide 1: title
        if fixed_slides >= 3:
            plan_titles.append("Reja")  # slide 2: plan

        for ch_idx, ch_name in enumerate(chapter_names):
            # Section header slide (same title as chapter)
            header_idx = len(plan_titles)
            section_header_indices.add(header_idx)
            plan_titles.append(ch_name)
            # Content slides for this chapter
            ch_content_count = slides_per_chapter - 1  # -1 for the header itself
            if ch_idx < remainder:
                ch_content_count += 1  # distribute remainder
            for sub in range(ch_content_count):
                if ch_content_count == 1:
                    plan_titles.append(ch_name)  # same title — content slide
                else:
                    plan_titles.append(f"{ch_name} ({sub+1})")

        plan_titles.append("Xulosa")  # last slide

    # Trim or pad plan to match total_slides
    if len(plan_titles) > total_slides:
        plan_titles = plan_titles[:total_slides - 1] + [plan_titles[-1]]
    while len(plan_titles) < total_slides:
        plan_titles.insert(-1, f"{topic} — qo'shimcha")

    # Deduplicate titles
    seen_titles = {}
    for i, t in enumerate(plan_titles):
        t_lower = t.lower().strip()
        if t_lower in seen_titles:
            plan_titles[i] = f"{t} ({i+1})"
        seen_titles[t_lower] = i

    logger.info(f"Final plan ({len(plan_titles)} slides): {plan_titles[:5]}...")

    if progress_callback:
        try:
            await progress_callback(1, total_slides + 2, "Reja tayyor, kontent yozilmoqda...")
        except:
            pass

    # ══════════════════════════════════════════════════════════════════
    # PHASE 2: Generate CONTENT per batch using the plan
    # ══════════════════════════════════════════════════════════════════
    system = (
        f"Sen professional prezentatsiya dizaynerisan. Til: {lang_name}.\n"
        "Vazifang — berilgan material asosida shablon slaydlarini MUKAMMAL to'ldirish.\n\n"
        "QOIDALAR:\n"
        "1. Har bir slayd FAQAT berilgan sarlavhani ishlatsin — boshqa nom BERMA\n"
        "2. content_N/body_N = BATAFSIL paragraf (2-3 gap, 21-25 so'z)\n"
        "3. content/body (nomersiz) = BATAFSIL paragraf (3-4 gap, 30-50 so'z)\n"
        "4. subtitle_N = qisqa sarlavha (2-4 so'z) — HAR BIR subtitle_N ALBATTA to'ldirilsin!\n"
        "5. point_N = 1-2 so'zli kalit tushuncha\n"
        "6. image_keyword = inglizcha kalit so'z\n"
        "7. Qo'shtirnoq (\") ISHLATMA — faqat (')\n"
        "8. SANA YOZMA!\n"
        "9. Har bir slayddagi BARCHA {{tag}} uchun JSON da kalit BO'LISHI SHART\n"
        "10. Har bir slayd = 1 ta asosiy g'oya, BATAFSIL yoritilgan\n"
        f"11. {HUMANIZER_SLIDES}\n"
    )

    if any_tagged:
        system += (
            "11. {{subtitle_N}} + {{body_N}} / {{content_N}} birga kelsa:\n"
            "   subtitle_N = qisqa nom (2-4 so'z), body_N/content_N = BATAFSIL paragraf (21-25 so'z, 2-3 gap)\n"
        )

    json_example = (
        '{"slides": [\n'
        '  {"title": "...", "subtitle": "...", '
        '"content": "Bu mavzu bo\'yicha muhim ma\'lumotlar keltiriladi. Asosiy tamoyillar va amaliy natijalar ko\'rsatiladi. Zamonaviy yondashuvlar tahlil qilinadi.", '
        '"content_1": "Birinchi bo\'lim bo\'yicha batafsil tahlil beriladi. Bu yo\'nalishda muhim omillar mavjud bo\'lib ularning har biri alohida e\'tiborga loyiq hisoblanadi.", '
        '"content_2": "Ikkinchi bo\'lim asosiy g\'oyalar va ularning amaliy qo\'llanilishi haqida ma\'lumot beradi. Bu sohada zamonaviy texnologiyalar keng qo\'llanilmoqda.", '
        '"content_3": "Uchinchi jihat sifatida amaliy natijalar tahlil qilinadi. Olingan ma\'lumotlar asosida muhim xulosalar chiqarish mumkin bo\'ladi.", '
        '"content_4": "To\'rtinchi bo\'limda kelajak istiqbollari va rivojlanish tendensiyalari ko\'rsatiladi. Bu soha jadal rivojlanib bormoqda.", '
        '"body_1": "...", "body_2": "...", "body_3": "...", "body_4": "...", '
        '"subtitle_1": "Asosiy tushuncha", "subtitle_2": "Tarixiy ahamiyati", "subtitle_3": "Zamonaviy holat", "subtitle_4": "Kelajak istiqbollari", '
        '"point_1": "Kalit so\'z", "point_2": "...", '
        '"points": ["punkt1", "punkt2"], "image_keyword": "keyword"},\n'
        '  ...\n'
        ']}'
    )

    # Plan text for reja slide — use unique chapter names
    if forced_titles:
        plan_content_titles = [t for t in plan_titles[2:-1] if t.lower() not in ("reja", "kirish", "xulosa")]
        if num_chapters and num_chapters < len(plan_content_titles):
            plan_content_titles = plan_content_titles[:num_chapters]
    else:
        plan_content_titles = chapter_names  # already unique chapter names
    plan_text = "\n".join(f"{i+1}. {t}" for i, t in enumerate(plan_content_titles))

    async def _generate_batch(batch_slides_info, batch_plan_titles, batch_label):
        """Generate content for a batch of slides."""
        batch_size = len(batch_slides_info)
        # Build spec for this batch
        batch_spec_lines = []
        for idx, (s_info, ptitle) in enumerate(zip(batch_slides_info, batch_plan_titles)):
            blocks = s_info.get("text_blocks", [])
            block_desc = []
            for b in blocks:
                tag = b.get("tag")
                mw = b["max_words"]
                if tag:
                    tag_lower = tag.lower()
                    if tag_lower.startswith("body_") or tag_lower.startswith("content_"):
                        block_desc.append(f"{{{{{tag}}}}} (21-25 so'z)")
                        continue
                    elif tag_lower in ("body", "content"):
                        block_desc.append(f"{{{{{tag}}}}} (30-50 so'z)")
                        continue
                    elif tag_lower.startswith("subtitle"):
                        mw = max(mw, 5)
                    block_desc.append(f"{{{{{tag}}}}} (max {mw} so'z)")
                else:
                    block_desc.append(f"{b['role']}: max {mw} so'z")
            img_note = f", rasm joyi" if s_info.get("image_count", 0) > 0 else ""
            batch_spec_lines.append(
                f"Slayd: sarlavha='{ptitle}', tur={s_info.get('slide_type','info')}, "
                f"bloklar=[{'; '.join(block_desc)}]{img_note}"
            )

        batch_spec = "\n".join(batch_spec_lines)
        batch_prompt = (
            f"Mavzu: {topic}\nMuallif: {author or 'Talaba'}\n"
            f"{material_section}\n"
            f"TO'LIQ REJA (Reja slaydida AYNAN SHU ro'yxatni yoz):\n{plan_text}\n\n"
            f"SLAYDLAR ({batch_size} ta):\n{batch_spec}\n\n"
            f"Har bir slayd uchun kontent yarat. SARLAVHALARNI O'ZGARTIRMA!\n"
            f"REJA slaydida content/body = '1. ...\\n2. ...\\n3. ...' formatda yoz!\n"
            f"JSON formati:\n{json_example}\n\n"
            f"JAMI ANIQ {batch_size} ta slayd qaytaring.\n"
            f"QOIDA: Har bir slayddagi BARCHA {{{{tag}}}} uchun JSON kalit bo'lsin.\n"
        )

        max_tok = max(8000, batch_size * 1200)
        raw = await _call_ai(
            [{"role": "system", "content": system},
             {"role": "user", "content": batch_prompt}],
            max_tokens=max_tok,
            temperature=0.7,
            json_mode=True,
        )
        if not raw:
            raise ValueError("AI returned empty response")
        clean = raw.replace("```json", "").replace("```", "").strip()
        data = json.loads(clean)
        slides = data.get("slides", data) if isinstance(data, dict) else data
        if not isinstance(slides, list):
            slides = [slides]
        result = [s if isinstance(s, dict) else {"body": str(s)} for s in slides]
        logger.info(f"{batch_label}: got {len(result)} slides (needed {batch_size})")
        return result

    BATCH_SIZE = 7  # max slides per API call
    try:
        result_slides = []
        for batch_start in range(0, total_slides, BATCH_SIZE):
            batch_end = min(batch_start + BATCH_SIZE, total_slides)
            batch_info = slides_info[batch_start:batch_end]
            batch_titles = plan_titles[batch_start:batch_end]
            batch_label = f"Batch {batch_start//BATCH_SIZE + 1}"

            batch_result = await _generate_batch(batch_info, batch_titles, batch_label)
            result_slides.extend(batch_result)

            if progress_callback:
                try:
                    await progress_callback(batch_end, total_slides + 2, f"{batch_end}/{total_slides} slayd tayyor")
                except:
                    pass

        # ── Normalize slide count ──────────────────────────────────────
        if len(result_slides) > total_slides:
            result_slides = result_slides[:total_slides]
        elif len(result_slides) < total_slides:
            logger.warning(f"AI returned {len(result_slides)}, need {total_slides}. Padding...")
            for pad_i in range(len(result_slides), total_slides):
                ptitle = plan_titles[pad_i] if pad_i < len(plan_titles) else topic
                result_slides.append({"title": ptitle, "content": f"{ptitle} haqida ma'lumot."})

        # ── Enforce plan titles onto results ───────────────────────────
        for i, ptitle in enumerate(plan_titles):
            if i < len(result_slides):
                result_slides[i]["title"] = ptitle

        # ── Build point_N dict from chapter names ──────────────────
        points_dict = {}
        if not forced_titles and section_header_indices:
            ch_num = 0
            for idx in sorted(section_header_indices):
                if idx < len(plan_titles):
                    ch_num += 1
                    ch_name = plan_titles[idx]
                    points_dict[f"point_{ch_num}"] = f"{ch_num}. {ch_name}"

            # Inject ALL point_N into EVERY slide (template can use them anywhere)
            for slide in result_slides:
                for pk, pv in points_dict.items():
                    if pk not in slide:
                        slide[pk] = pv

            # Section header slides: also set subtitle/content
            ch_num = 0
            for idx in sorted(section_header_indices):
                if idx < len(result_slides):
                    ch_num += 1
                    ch_name = plan_titles[idx] if idx < len(plan_titles) else ""
                    result_slides[idx]["subtitle"] = f"{ch_num}-bo'lim"
                    result_slides[idx]["content"] = f"{ch_num}. {ch_name}"

    except Exception as e:
        logger.error(f"Template content generation failed: {e}")
        result_slides = []
        for i, s in enumerate(slides_info):
            ptitle = plan_titles[i] if i < len(plan_titles) else topic
            stype = s.get("slide_type", "info")
            if stype == "title":
                result_slides.append({"title": ptitle, "subtitle": f"Bajardi: {author}"})
            elif stype == "plan":
                result_slides.append({"title": "Reja", "content": plan_text})
            elif stype == "conclusion":
                result_slides.append({"title": "Xulosa", "content": f"{topic} bo'yicha umumiy xulosa."})
            else:
                result_slides.append({"title": ptitle, "content": f"{ptitle} haqida ma'lumot."})

    # ══════════════════════════════════════════════════════════════════
    # PHASE 3: Validate and clean
    # ══════════════════════════════════════════════════════════════════
    def _clean_text(text):
        """Remove garbage characters from text."""
        if not isinstance(text, str):
            return text
        import re as _re
        text = text.replace("_x000B_", " ")
        text = _re.sub(r"•\s*•", "•", text)
        text = _re.sub(r"\n{3,}", "\n\n", text)
        text = _re.sub(r"[ \t]{2,}", " ", text)
        return text.strip()

    for slide in result_slides:
        for key, val in slide.items():
            if isinstance(val, str):
                slide[key] = _clean_text(val)
            elif isinstance(val, list):
                slide[key] = [_clean_text(v) if isinstance(v, str) else v for v in val]

    logger.info(f"Phase 3: Validated {len(result_slides)} slides, plan titles enforced")

    # Step 3: Post-process — enforce word limits and fill missing content_N
    if progress_callback:
        try:
            await progress_callback(total_slides + 1, total_slides + 2, "Matn sifati tekshirilmoqda...")
        except:
            pass

    for i, slide_content in enumerate(result_slides):
        if i >= len(slides_info):
            break

        s_info = slides_info[i]
        blocks = s_info.get("text_blocks", [])

        # Enforce word limits on points
        points = slide_content.get("points", [])
        body_blocks = [b for b in blocks if b["role"] in ("body", "textbox")]

        if points and body_blocks:
            trimmed_points = []
            for j, point in enumerate(points):
                if j < len(body_blocks):
                    max_w = body_blocks[j]["max_words"]
                else:
                    max_w = body_blocks[-1]["max_words"] if body_blocks else 50

                words = str(point).split()
                if len(words) > max_w:
                    point = " ".join(words[:max_w]) + "..."
                trimmed_points.append(point)

            slide_content["points"] = trimmed_points

        # Enforce word limits on title
        title_blocks = [b for b in blocks if b["role"] == "title"]
        if title_blocks and slide_content.get("title"):
            max_title_w = title_blocks[0]["max_words"]
            title_words = slide_content["title"].split()
            if len(title_words) > max_title_w:
                slide_content["title"] = " ".join(title_words[:max_title_w])

    if progress_callback:
        try:
            await progress_callback(total_slides + 2, total_slides + 2, "")
        except:
            pass

    return result_slides


# ══════════════════════════════════════════════════════════════════════════════
# LECTURE STANDARD: Generate full university-standard lecture content
# ══════════════════════════════════════════════════════════════════════════════

async def generate_lecture_content(
    topic: str,
    language: str = "uz",
    university: str = "",
    kafedra: str = "",
    fan: str = "",
    author: str = "",
    slides_per_question: int = 6,
    user_material: str = "",
    progress_callback=None,
) -> dict:
    """
    Generate full lecture content in university-standard format.

    Returns dict matching lecture_pptx_service.generate_lecture_pptx() input:
    {
        "university", "kafedra", "fan", "topic", "author", "year", "city",
        "plan": [...],
        "kirish", "maqsad": {...},
        "adabiyotlar": [...],
        "savol_1": {"title", "slides": [{"title", "body"}], "xulosa"},
        "savol_2": {...}, "savol_3": {...},
        "iqtibos": {"text", "author"},
        "xulosa"
    }
    """
    total_steps = 6  # plan, kirish+maqsad, savol1, savol2, savol3, xulosa
    
    # Load structure template
    structure_text = ""
    try:
        import os
        struct_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "doc_templates", "lecture_standard_structure.txt"
        )
        if os.path.exists(struct_path):
            with open(struct_path, "r", encoding="utf-8") as f:
                structure_text = f.read()
    except:
        pass

    lang_name = {"uz": "o'zbek", "ru": "русский", "en": "English"}.get(language, "o'zbek")

    system_prompt = (
        f"Sen universitetda tajribali professor-o'qituvchisan. Til: {lang_name}.\n"
        "Vazifang — berilgan mavzu bo'yicha TO'LIQ ma'ruza taqdimoti kontentini yaratish.\n\n"
        "MUHIM QOIDALAR:\n"
        "1. Rasmiy-ilmiy uslub (og'zaki emas)\n"
        "2. Har bir fikr dalillangan bo'lsin\n"
        "3. Kalit atamalar BOSH HARF bilan\n"
        "4. Qisqa jumlalar (15-20 so'z)\n"
        "5. Har bir bullet point — 1 ta g'oya, 1-2 qator\n"
        "6. Ilmiy terminologiya to'g'ri ishlatilsin\n"
        "7. 3 ta o'quv savol — mantiqiy ketma-ketlikda\n"
        "8. Matn ichida qo'shtirnoq (\") ISHLATMANG — faqat (')\n"
        f"9. {HUMANIZER_SLIDES}\n"
    )

    material_section = ""
    if user_material:
        material_section = (
            f"\n\nFOYDALANUVCHI MATERIALI:\n```\n{user_material[:5000]}\n```\n"
            "SHU material asosida kontent yoz.\n"
        )

    # ── Step 1: Generate plan (3 questions) ──
    if progress_callback:
        try: await progress_callback(0, total_steps, "Reja tuzilmoqda...")
        except: pass

    plan_prompt = (
        f"Mavzu: {topic}\n"
        f"{material_section}\n"
        "Ushbu mavzu bo'yicha ma'ruza uchun 3 ta o'quv savol (reja) tuz.\n"
        "Har bir savol — mavzuning bir qismini qamrab olsin.\n"
        "1-savol: nazariy asos, tushunchalar, ta'riflar\n"
        "2-savol: amaliy jihat, usullar, metodlar\n"
        "3-savol: qo'llash, tahlil, amaliyot\n\n"
        "FAQAT JSON:\n"
        '{"plan": ["1-savol nomi", "2-savol nomi", "3-savol nomi"]}'
    )

    try:
        raw = await _call_ai(
            [{"role": "system", "content": system_prompt},
             {"role": "user", "content": plan_prompt}],
            max_tokens=500, temperature=0.7, json_mode=True
        )
        plan_data = json.loads(raw.replace("```json", "").replace("```", ""))
        plan = plan_data.get("plan", [])
    except:
        plan = [
            f"{topic} — asosiy tushunchalar",
            f"{topic} — usul va metodlar",
            f"{topic} — amaliy qo'llanilishi"
        ]

    if len(plan) < 3:
        plan = (plan + [f"{topic} — qo'shimcha", f"{topic} — tahlil", f"{topic} — amaliyot"])[:3]

    # ── Step 2: Kirish, maqsad, adabiyotlar ──
    if progress_callback:
        try: await progress_callback(1, total_steps, "Kirish va maqsad...")
        except: pass

    intro_prompt = (
        f"Mavzu: {topic}\n"
        f"Reja: {json.dumps(plan, ensure_ascii=False)}\n"
        f"{material_section}\n"
        "Quyidagilarni yarat:\n"
        "1. kirish — mavzuning dolzarbligi (3-4 jumla)\n"
        "2. maqsad — talimiy, tarbiyaviy, rivojlantiruvchi (har biri 1-2 jumla)\n"
        "3. adabiyotlar — 5 ta ilmiy manba (muallif, nomi, nashriyot, yil)\n\n"
        "FAQAT JSON:\n"
        '{"kirish": "...", "maqsad": {"talimiy": "...", "tarbiyaviy": "...", '
        '"rivojlantiruvchi": "..."}, "adabiyotlar": ["1. ...", "2. ...", ...]}'
    )

    try:
        raw = await _call_ai(
            [{"role": "system", "content": system_prompt},
             {"role": "user", "content": intro_prompt}],
            max_tokens=1000, temperature=0.7, json_mode=True
        )
        intro_data = json.loads(raw.replace("```json", "").replace("```", ""))
    except:
        intro_data = {
            "kirish": f"{topic} mavzusi bugungi kunda dolzarb hisoblanadi.",
            "maqsad": {"talimiy": "Mavzu bo'yicha bilim berish", "tarbiyaviy": "Mas'uliyatni shakllantirish", "rivojlantiruvchi": "Tahliliy fikrlashni rivojlantirish"},
            "adabiyotlar": [f"1. {topic} bo'yicha darslik, Toshkent, 2024"]
        }

    # ── Steps 3-5: Generate each savol content ──
    savol_contents = {}
    for q_idx in range(3):
        step = q_idx + 2
        savol_key = f"savol_{q_idx + 1}"
        roman = ["I", "II", "III"][q_idx]
        q_title = plan[q_idx] if q_idx < len(plan) else f"{topic} — {q_idx+1}-qism"

        if progress_callback:
            try: await progress_callback(step, total_steps, f"{roman}-savol: {q_title[:40]}...")
            except: pass

        savol_prompt = (
            f"Mavzu: {topic}\n"
            f"O'quv savol: {roman}-O'QUV SAVOLI: {q_title}\n"
            f"{material_section}\n"
            f"Ushbu o'quv savol bo'yicha {slides_per_question} ta slayd kontentini yarat.\n"
            "Har bir slayd uchun:\n"
            "- title: slayd sarlavhasi (BOSH HARFLARDA, 5-10 so'z)\n"
            "- body: asosiy matn (3-5 bullet point, har biri 1-2 qator)\n\n"
            "Oxirida savol bo'yicha qisqa xulosa yoz (2-3 jumla).\n\n"
            "FAQAT JSON:\n"
            '{"title": "savol nomi", "slides": [{"title": "...", "body": "punkt1\\npunkt2\\npunkt3"}, ...], '
            '"xulosa": "..."}'
        )

        try:
            raw = await _call_ai(
                [{"role": "system", "content": system_prompt},
                 {"role": "user", "content": savol_prompt}],
                max_tokens=2000, temperature=0.8, json_mode=True
            )
            q_data = json.loads(raw.replace("```json", "").replace("```", ""))
            savol_contents[savol_key] = q_data
        except Exception as e:
            logger.error(f"Lecture savol {q_idx+1} generation failed: {e}")
            savol_contents[savol_key] = {
                "title": q_title,
                "slides": [{"title": q_title, "body": f"{q_title} bo'yicha ma'lumot."}],
                "xulosa": f"{q_title} bo'yicha xulosa."
            }

    # ── Step 6: Xulosa + Iqtibos ──
    if progress_callback:
        try: await progress_callback(5, total_steps, "Xulosa va iqtibos...")
        except: pass

    xulosa_prompt = (
        f"Mavzu: {topic}\n"
        f"3 ta o'quv savol: {json.dumps(plan, ensure_ascii=False)}\n"
        "1. Umumiy xulosa yoz (5-7 jumla, barcha 3 savolni qamrab olsin)\n"
        "2. Mavzuga mos mashhur iqtibos (tsitata) tanlash va muallif ismini yoz\n\n"
        "FAQAT JSON:\n"
        '{"xulosa": "...", "iqtibos": {"text": "tsitata matni", "author": "muallif ismi"}}'
    )

    try:
        raw = await _call_ai(
            [{"role": "system", "content": system_prompt},
             {"role": "user", "content": xulosa_prompt}],
            max_tokens=800, temperature=0.7, json_mode=True
        )
        final_data = json.loads(raw.replace("```json", "").replace("```", ""))
    except:
        final_data = {
            "xulosa": f"{topic} mavzusi bo'yicha umumiy xulosa.",
            "iqtibos": {"text": "Ilm — eng yaxshi meros.", "author": "Al-Xorazmiy"}
        }

    if progress_callback:
        try: await progress_callback(total_steps, total_steps, "")
        except: pass

    # ── Assemble final content dict ──
    import datetime
    result = {
        "university": university or "O'ZBEKISTON RESPUBLIKASI",
        "kafedra": kafedra or "",
        "fan": fan or "",
        "topic": topic.upper(),
        "author": author or "Talaba",
        "year": str(datetime.datetime.now().year),
        "city": "Toshkent",
        "plan": plan,
        "kirish": intro_data.get("kirish", ""),
        "maqsad": intro_data.get("maqsad", {}),
        "adabiyotlar": intro_data.get("adabiyotlar", []),
        "savol_1": savol_contents.get("savol_1", {}),
        "savol_2": savol_contents.get("savol_2", {}),
        "savol_3": savol_contents.get("savol_3", {}),
        "iqtibos": final_data.get("iqtibos", {}),
        "xulosa": final_data.get("xulosa", ""),
    }

    return result


def lecture_content_to_slides(content: dict, max_slides: int = 17) -> list:
    """
    Convert structured lecture content dict → flat slides_data list
    for generate_pptx(). Respects max_slides limit.

    Output: [{"title": "...", "points": [...]}, ...]
    """
    slides = []

    # 1. Title slide
    slides.append({
        "title": content.get("topic", "MAVZU"),
        "points": [content.get("author", "")]
    })

    # 2. Reja
    plan = content.get("plan", [])
    slides.append({
        "title": "REJA",
        "points": [f"{i+1}. {p}" for i, p in enumerate(plan)]
    })

    # 3. Kirish
    kirish = content.get("kirish", "")
    if kirish:
        slides.append({
            "title": "KIRISH",
            "points": [kirish]
        })

    # 4. Maqsad
    maqsad = content.get("maqsad", {})
    if maqsad:
        if isinstance(maqsad, dict):
            pts = []
            if maqsad.get("talimiy"): pts.append(f"Ta'limiy: {maqsad['talimiy']}")
            if maqsad.get("tarbiyaviy"): pts.append(f"Tarbiyaviy: {maqsad['tarbiyaviy']}")
            if maqsad.get("rivojlantiruvchi"): pts.append(f"Rivojlantiruvchi: {maqsad['rivojlantiruvchi']}")
            slides.append({"title": "MASHG'ULOT MAQSADI", "points": pts})
        else:
            slides.append({"title": "MASHG'ULOT MAQSADI", "points": [str(maqsad)]})

    # 5. Adabiyotlar
    adab = content.get("adabiyotlar", [])
    if adab:
        slides.append({"title": "ADABIYOTLAR", "points": adab})

    # Fixed overhead so far (title, reja, kirish, maqsad, adab) = ~5
    # + xulosa at end = 1
    # Remaining budget for 3 questions:
    fixed_count = len(slides) + 1  # +1 for xulosa at end
    question_budget = max(3, max_slides - fixed_count)  # at least 1 slide per question

    # 6-N. Three questions
    for q_idx in range(3):
        savol_key = f"savol_{q_idx + 1}"
        roman = ["I", "II", "III"][q_idx]
        savol = content.get(savol_key, {})
        q_title = savol.get("title", plan[q_idx] if q_idx < len(plan) else "")

        # Section header
        slides.append({
            "title": f"{roman}-O'QUV SAVOLI",
            "points": [q_title]
        })

        # Content slides (distribute budget evenly)
        per_q = max(1, question_budget // 3)
        q_slides = savol.get("slides", [])[:per_q]
        for sc in q_slides:
            if isinstance(sc, dict):
                body = sc.get("body", sc.get("points", ""))
                if isinstance(body, str):
                    pts = [p.strip() for p in body.split("\n") if p.strip()]
                elif isinstance(body, list):
                    pts = body
                else:
                    pts = [str(body)]
                slides.append({"title": sc.get("title", ""), "points": pts})
            else:
                slides.append({"title": "", "points": [str(sc)]})

        # Mini conclusion
        xulosa_q = savol.get("xulosa", "")
        if xulosa_q:
            slides.append({
                "title": f"{roman}-O'QUV SAVOLGA XULOSA",
                "points": [xulosa_q]
            })

    # Last: Xulosa
    xulosa = content.get("xulosa", "")
    if xulosa:
        slides.append({"title": "XULOSA", "points": [xulosa]})

    # Trim to max_slides
    if len(slides) > max_slides:
        slides = slides[:max_slides - 1] + [slides[-1]]  # keep last (xulosa)

    return slides

async def generate_test_presentation_content(topic: str, language: str = "uz", author: str = "", progress_callback=None) -> dict:
    """
    Generate content for test.pptx.
    Structure:
    - Title
    - Reja
    - Kirish
    - For each Reja item:
        - 1 slide: 3 subpoints
        - 2 slides: detailed content
    """
    total_steps = 4
    if progress_callback:
        try: await progress_callback(0, total_steps, "Reja tuzilmoqda...")
        except: pass

    # 1. Generate plan with 3-4 items
    sys_prompt = "Siz professional taqdimot tuzuvchisiz."
    plan_prompt = (
        f"Mavzu: {topic}\nTil: {language}\n"
        "Shu mavzu bo'yicha 3 ta asosiy qismdan iborat reja tuzing. Faqat reja punktlarini vergul bilan ajratib yozing."
    )
    plan_text = await _call_ai(
        [{"role": "system", "content": sys_prompt}, {"role": "user", "content": plan_prompt}],
        max_tokens=200, temperature=0.7
    )
    plan = [p.strip() for p in plan_text.split(",") if p.strip()]
    if len(plan) < 3:
        plan = ["Asosiy tushunchalar", "Tahlil va metodologiya", "Amaliy ahamiyati"]
        
    if progress_callback:
        try: await progress_callback(1, total_steps, "Kirish qismi yozilmoqda...")
        except: pass
        
    # 2. Kirish
    kirish_prompt = (
        f"Mavzu: {topic}\nTil: {language}\n"
        "Shu taqdimot uchun qisqa 'Kirish' yozing (taxminan 50-60 so'z)."
    )
    kirish_text = await _call_ai([{"role": "user", "content": kirish_prompt}], max_tokens=300)
    
    sections = []
    
    # 3. Process each plan item
    for i, p in enumerate(plan):
        if progress_callback:
            try: await progress_callback(2, total_steps, f"{i+1}-qism yaratilmoqda...")
            except: pass
            
        subpoints_prompt = (
            f"Mavzu: {topic}\nBo'lim: {p}\nTil: {language}\n"
            "Shu bo'lim uchun 3 ta qisqa podpunkt (subpoint) yozing. Faqat podpunktlarni yangi qatordan yozing."
        )
        subpoints_text = await _call_ai([{"role": "user", "content": subpoints_prompt}], max_tokens=200)
        subpoints = [sp.strip("- *1234567890.") for sp in subpoints_text.split("\n") if sp.strip()]
        if len(subpoints) < 3:
            subpoints = ["Birinchi muhim jihat", "Ikkinchi xususiyat", "Uchinchi omil"]
        subpoints = subpoints[:3]
        
        # 2 slides of content
        content_prompt = (
            f"Mavzu: {topic}\nBo'lim: {p}\nPodpunktlar: {', '.join(subpoints)}\nTil: {language}\n"
            "Ushbu podpunktlarni batafsil tushuntirib, 2 ta slayddan iborat matn yozing.\n"
            "FAQAT JSON formatida javob bering:\n"
            "[\n"
            "  {\"title\": \"1-slayd sarlavhasi\", \"body\": \"matn...\"},\n"
            "  {\"title\": \"2-slayd sarlavhasi\", \"body\": \"matn...\"}\n"
            "]"
        )
        raw = await _call_ai([{"role": "system", "content": "Siz JSON qaytaruvchi botsiz."}, {"role": "user", "content": content_prompt}], max_tokens=800, json_mode=True)
        import json
        try:
            slides_content = json.loads(raw.replace("```json", "").replace("```", ""))
        except:
            slides_content = [
                {"title": p, "body": "Batafsil ma'lumotlar..."},
                {"title": f"{p} davomi", "body": "Qo'shimcha izohlar..."}
            ]
            
        sections.append({
            "title": p,
            "subpoints": subpoints,
            "slides_content": slides_content
        })

    if progress_callback:
        try: await progress_callback(total_steps, total_steps, "Tugatildi")
        except: pass

    return {
        "topic": topic.upper(),
        "author": author,
        "plan": plan,
        "kirish": kirish_text,
        "sections": sections
    }


async def verify_receipt_with_ai(image_base64: str, required_amount: int) -> dict:
    from config import CARDS, GEMINI_API_KEY
    card_list = ", ".join([f"{c['number']} ({c['holder']})" for c in CARDS])
    
    prompt = f"""
Siz kvitansiya/chekni tekshiradigan sun'iy intellektsiz.
Ushbu rasmda tolov cheki berilgan.
Siz quyidagilarni tekshirishingiz kerak:
1. To'lov miqdori (summa) kamida {required_amount} UZS (so'm) yoki undan ko'pmi?
2. Pul o'tkazilgan karta raqami yoki qabul qiluvchi quyidagilardan biriga mos keladimi?
Kartalar: {card_list}

Agar to'lov miqdori {required_amount} so'mdan kam bo'lsa, `verified` false bo'lishi kerak va `reason` ga AYNAN QUYIDAGI GAPNI yozing (hech narsani o'zgartirmang, faqat summalarni qo'ying):
"Umumiy summa {required_amount} so'm bo'lishi kerak, siz [kvitansiyadagi summa] so'mlik chek yubordingiz."

Agar pul to'g'ri kartaga to'g'ri miqdorda o'tkazilgan bo'lsa verified: true bo'lishi kerak.
Faqat JSON formatida javob bering, hech qanday ortiqcha matn qo'shmang:
{{
  "verified": true yoki false,
  "amount": (raqam, masalan 10000),
  "reason": "Qisqacha sabab"
}}
"""
    try:
        from google import genai
        import base64
        
        client = genai.Client(api_key=GEMINI_API_KEY)
        
        image_bytes = base64.b64decode(image_base64)
        
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[
                prompt,
                genai.types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg")
            ]
        )
        
        content = response.text
        import re
        json_match = re.search(r"\{.*\}", content, re.DOTALL)
        if json_match:
            return json.loads(json_match.group(0))
        return json.loads(content)
    except Exception as e:
        logger.error(f"Error in verify_receipt_with_ai: {e}")
        return {"verified": False, "amount": 0, "reason": "Tizim xatoligi yuz berdi yoki chek o'qilmadi."}

