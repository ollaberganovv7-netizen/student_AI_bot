from __future__ import annotations
"""
Internationalization (i18n) — bot interface translations.
Supports: uz (O'zbek), ru (Русский), en (English)
"""

TEXTS = {
    # ─── Language selection ──────────────────────────────────────────────
    "lang_prompt": {
        "uz": "🇺🇿 <b>Iltimos, tilni tanlang</b>\nSizga qulay tilni tanlab, davom eting.\n\n🇷🇺 <b>Пожалуйста, выберите язык</b>\nВыберите удобный язык и продолжите.\n\n🇬🇧 <b>Please select a language</b>\nChoose your preferred language to continue.",
        "ru": "🇺🇿 <b>Iltimos, tilni tanlang</b>\nSizga qulay tilni tanlab, davom eting.\n\n🇷🇺 <b>Пожалуйста, выберите язык</b>\nВыберите удобный язык и продолжите.\n\n🇬🇧 <b>Please select a language</b>\nChoose your preferred language to continue.",
        "en": "🇺🇿 <b>Iltimos, tilni tanlang</b>\nSizga qulay tilni tanlab, davom eting.\n\n🇷🇺 <b>Пожалуйста, выберите язык</b>\nВыберите удобный язык и продолжите.\n\n🇬🇧 <b>Please select a language</b>\nChoose your preferred language to continue.",
    },
    "lang_set": {
        "uz": "✅ Til o'zbek tiliga o'zgartirildi!",
        "ru": "✅ Язык изменён на русский!",
        "en": "✅ Language changed to English!",
    },

    # ─── Welcome / Main menu ─────────────────────────────────────────────
    "welcome": {
        "uz": (
            "ㅤㅤㅤㅤㅤㅤㅤㅤ<b>USTOZ AI</b>\n\n"
            "<i>Intellektual yordamchingizga xush kelibsiz, <b>{name}</b>!</i> 👋\n\n"
            "<b>🎓 ILMIY YO'NALISHLAR:</b>\n"
            " ┣ 📝 <i>Konferensiya tezisi</i>\n"
            " ┣ 🔬 <i>Ilmiy maqola tezisi & maqola</i>\n"
            " ┗ 🎓 <i>Dissertatsiya / Malakaviy ish</i>\n\n"
            "<b>📰 OMMABOP YO'NALISHLAR:</b>\n"
            " ┣ 📊 <i>Tahliliy tezislar</i>\n"
            " ┣ 🔭 <i>Ilmiy-ommabop maqolalar</i>\n"
            " ┗ 🎭 <i>Badiiy-publitsistik maqolalar</i>\n\n"
            "👇 <b>Iltimos, pastdagi menyudan xizmat turini tanlang:</b>"
        ),
        "ru": (
            "ㅤㅤㅤㅤㅤㅤㅤㅤ<b>USTOZ AI</b>\n\n"
            "<i>Добро пожаловать, <b>{name}</b>!</i> 👋\n\n"
            "<b>🎓 НАУЧНЫЕ НАПРАВЛЕНИЯ:</b>\n"
            " ┣ 📝 <i>Тезис для конференции</i>\n"
            " ┣ 🔬 <i>Научная статья и тезис</i>\n"
            " ┗ 🎓 <i>Диссертация / ВКР</i>\n\n"
            "<b>📰 ПОПУЛЯРНЫЕ НАПРАВЛЕНИЯ:</b>\n"
            " ┣ 📊 <i>Аналитические тезисы</i>\n"
            " ┣ 🔭 <i>Научно-популярные статьи</i>\n"
            " ┗ 🎭 <i>Художественно-публицистические статьи</i>\n\n"
            "👇 <b>Пожалуйста, выберите услугу из меню ниже:</b>"
        ),
        "en": (
            "ㅤㅤㅤㅤㅤㅤㅤㅤ<b>USTOZ AI</b>\n\n"
            "<i>Welcome to your intellectual assistant, <b>{name}</b>!</i> 👋\n\n"
            "<b>🎓 SCIENTIFIC DIRECTIONS:</b>\n"
            " ┣ 📝 <i>Conference thesis</i>\n"
            " ┣ 🔬 <i>Scientific article thesis & article</i>\n"
            " ┗ 🎓 <i>Dissertation / Qualification work</i>\n\n"
            "<b>📰 POPULAR DIRECTIONS:</b>\n"
            " ┣ 📊 <i>Analytical theses</i>\n"
            " ┣ 🔭 <i>Popular science articles</i>\n"
            " ┗ 🎭 <i>Artistic-journalistic articles</i>\n\n"
            "👇 <b>Please select a service from the menu below:</b>"
        )
    },
    
    "lang_prompt": {
        "uz": "🇺🇿 <b>Iltimos, tilni tanlang</b>\nSizga qulay tilni tanlab, davom eting.\n\n🇷🇺 <b>Пожалуйста, выберите язык</b>\nВыберите удобный язык и продолжите.\n\n🇬🇧 <b>Please select a language</b>\nChoose your preferred language to continue.",
        "ru": "🇺🇿 <b>Iltimos, tilni tanlang</b>\nSizga qulay tilni tanlab, davom eting.\n\n🇷🇺 <b>Пожалуйста, выберите язык</b>\nВыберите удобный язык и продолжите.\n\n🇬🇧 <b>Please select a language</b>\nChoose your preferred language to continue.",
        "en": "🇺🇿 <b>Iltimos, tilni tanlang</b>\nSizga qulay tilni tanlab, davom eting.\n\n🇷🇺 <b>Пожалуйста, выберите язык</b>\nВыберите удобный язык и продолжите.\n\n🇬🇧 <b>Please select a language</b>\nChoose your preferred language to continue.",
    },
    "lang_set": {
        "uz": "✅ Til o'zbek tiliga o'zgartirildi!",
        "ru": "✅ Язык изменён на русский!",
        "en": "✅ Language changed to English!",
    },

    # ─── Welcome / Main menu ─────────────────────────────────────────────
    "pay_success": {
        "uz": "🎉 <b>Muvaffaqiyatli to'lov!</b>\n\n💰 Balansingizga <b>{amount}</b> qo'shildi.\n🚀 Endi xizmatlardan foydalanishingiz mumkin!",
        "ru": "🎉 <b>Оплата успешна!</b>\n\n💰 На баланс зачислено <b>{amount}</b>.\n🚀 Теперь можете пользоваться сервисами!",
        "en": "🎉 <b>Payment successful!</b>\n\n💰 <b>{amount}</b> added to your balance.\n🚀 You can now use the services!",
    },

    "tfill_summary": {
        "uz": "📎 <b>Shablon to'ldirish — Xulosa</b>\n\n📝 <b>Mavzu:</b> {topic}\n🗺️ <b>Til:</b> {pres_lang}\n🎨 <b>Shablon:</b> {style}\n📷 <b>Rasmlar:</b> {photos}\n💰 <b>Narx:</b> {price}\n\n<i>Tayyor bo'lsa \"✅ Yaratish\" tugmasini bosing.</i>",
        "ru": "📎 <b>Заполнение шаблона — Итог</b>\n\n📝 <b>Тема:</b> {topic}\n🗺️ <b>Язык:</b> {pres_lang}\n🎨 <b>Шаблон:</b> {style}\n📷 <b>Фото:</b> {photos}\n💰 <b>Цена:</b> {price}\n\n<i>Когда готовы, нажмите \"✅ Создать\".</i>",
        "en": "📎 <b>Template Fill — Summary</b>\n\n📝 <b>Topic:</b> {topic}\n🗺️ <b>Language:</b> {pres_lang}\n🎨 <b>Template:</b> {style}\n📷 <b>Photos:</b> {photos}\n💰 <b>Price:</b> {price}\n\n<i>When ready, press \"✅ Create\".</i>",
    },

    # ─── Cancel / Stop ───────────────────────────────────────────────────
    "cancelled": {
        "uz": "❌ Amaliyot bekor qilindi.",
        "ru": "❌ Операция отменена.",
        "en": "❌ Operation cancelled.",
    },
    "stopped": {
        "uz": "🛑 <b>Jarayon to'xtatildi.</b>\n\nAsosiy menyuga qaytdik.",
        "ru": "🛑 <b>Процесс остановлен.</b>\n\nВозврат в главное меню.",
        "en": "🛑 <b>Process stopped.</b>\n\nReturning to main menu.",
    },

    # ─── Help ────────────────────────────────────────────────────────────
    "help": {
        "uz": "ℹ️ <b>Yordam markazi</b>\n\n<b>Qanday ishlaydi?</b>\n1. Xizmatni tanlang\n2. Mavzu kiriting\n3. Fayl tayyor bo'ladi\n\n💰 <b>To'lov:</b> /buy\n🆘 <b>Admin:</b> {admin}",
        "ru": "ℹ️ <b>Центр помощи</b>\n\n<b>Как это работает?</b>\n1. Выберите услугу\n2. Введите тему\n3. Файл будет готов\n\n💰 <b>Оплата:</b> /buy\n🆘 <b>Админ:</b> {admin}",
        "en": "ℹ️ <b>Help Center</b>\n\n<b>How it works?</b>\n1. Choose a service\n2. Enter a topic\n3. File will be ready\n\n💰 <b>Payment:</b> /buy\n🆘 <b>Admin:</b> {admin}",
    },
}

# ─── Button labels per language ──────────────────────────────────────────────
BUTTONS = {
    "presentation": {"uz": "🆕 Taqdimot (Slayd) yaratish", "ru": "🆕 Презентация (Слайд)", "en": "🆕 Create Presentation"},
    "presentation_pro": {"uz": "🚀 Slayd Pro (Premium)", "ru": "🚀 Слайд Про (Премиум)", "en": "🚀 Slide Pro (Premium)"},
    "mustaqil": {"uz": "📄 Mustaqil ish yaratish", "ru": "📄 Самост. работа", "en": "📄 Independent Work"},
    "referat": {"uz": "📚 Referat yaratish", "ru": "📚 Реферат", "en": "📚 Essay"},
    "kurs": {"uz": "📘 Kurs ishi yaratish", "ru": "📘 Курсовая работа", "en": "📘 Coursework"},
    "tezis": {"uz": "🎓 Tezis yaratish", "ru": "🎓 Тезис", "en": "🎓 Thesis"},
    "maqola": {"uz": "📝 Maqola yaratish", "ru": "📝 Статья", "en": "📝 Article"},
    "uslubiy": {"uz": "📗 Uslubiy ishlanma", "ru": "📗 Метод. пособие", "en": "📗 Methodical Guide"},
    
    # --- New 8 Thesis & Article Types ---
    "t_conf": {"uz": "📝 Ilmiy konferensiya tezisi", "ru": "📝 Тезис для научной конференции", "en": "📝 Scientific Conference Thesis"},
    "t_art": {"uz": "📝 Ilmiy maqola tezisi", "ru": "📝 Тезис научной статьи", "en": "📝 Scientific Article Thesis"},
    "t_diss": {"uz": "🎓 Dissertatsiya / Bitiruv malakaviy ishi tezisi", "ru": "🎓 Тезис диссертации / ВКР", "en": "🎓 Dissertation / Graduation Thesis"},
    "t_pop": {"uz": "📊 Ommabop / Tahliliy tezislar", "ru": "📊 Популярные / Аналитические тезисы", "en": "📊 Popular / Analytical Theses"},
    "a_sci": {"uz": "🔬 Ilmiy maqola", "ru": "🔬 Научная статья", "en": "🔬 Scientific Article"},
    "a_pop_sci": {"uz": "🔭 Ilmiy-ommabop maqola", "ru": "🔭 Научно-популярная статья", "en": "🔭 Popular Science Article"},
    "a_pop": {"uz": "📰 Ommabop maqola", "ru": "📰 Популярная статья", "en": "📰 Popular Article"},
    "a_art": {"uz": "🎭 Badiiy-publitsistik maqola", "ru": "🎭 Художественно-публицистическая статья", "en": "🎭 Artistic-journalistic Article"},

    "topup": {"uz": "💳 Hisobni to'ldirish", "ru": "💳 Пополнить баланс", "en": "💳 Top Up Balance"},
    "receipt": {"uz": "📸 Chekni yuborish", "ru": "📸 Отправить чек", "en": "📸 Send Receipt"},
    "referral": {"uz": "👥 Do'stni taklif qilish", "ru": "👥 Пригласить друга", "en": "👥 Invite Friend"},
    "account": {"uz": "📊 Mening hisobim", "ru": "📊 Мой аккаунт", "en": "📊 My Account"},
    "back": {"uz": "🏠 Bosh menyu", "ru": "🏠 Главное меню", "en": "🏠 Main Menu"},
    "pres_engine": {"uz": "🔧 Dizayn usuli", "ru": "🔧 Способ дизайна", "en": "🔧 Design Engine"},
    "pres_settings": {"uz": "⚙️ Sozlamalar", "ru": "⚙️ Настройки", "en": "⚙️ Settings"},
    "pres_design": {"uz": "🎨 Dizayn Tanlash", "ru": "🎨 Выбрать дизайн", "en": "🎨 Choose Design"},
    "pres_plan": {"uz": "📝 Reja qo'shish", "ru": "📝 Добавить план", "en": "📝 Add Plan"},
    "pres_content": {"uz": "🧩 Kontent", "ru": "🧩 Контент", "en": "🧩 Content"},
    "pres_photo": {"uz": "📷 Rasm yuklash", "ru": "📷 Загрузить фото", "en": "📷 Upload Photo"},
    "pres_ai_img": {"uz": "🖼 AI Rasm", "ru": "🖼 AI Изображения", "en": "🖼 AI Images"},
    "pres_create": {"uz": "✅ Yaratish", "ru": "✅ Создать", "en": "✅ Create"},
    "cancel": {"uz": "❌ Bekor qilish", "ru": "❌ Отменить", "en": "❌ Cancel"},
    "quiz": {"uz": "📋 Avtomatik quiz tuzish", "ru": "📋 Автоматический тест", "en": "📋 Auto Quiz Maker"},
    "diplom": {"uz": "🎓 Diplom ishi yaratish", "ru": "🎓 Дипломная работа", "en": "🎓 Diploma Work"},
    "pres_design_catalog": {"uz": "🎨 Dizayn tanlash (Katalog)", "ru": "🎨 Выбрать дизайн (Каталог)", "en": "🎨 Choose Design (Catalog)"},
    "pres_plain_design": {"uz": "Rasmsiz/Oddiy Dizayn", "ru": "Без фото/Простой дизайн", "en": "Plain/Simple Design"},
}


def t(key: str, lang: str = "uz", **kwargs) -> str:
    """Get translated text. Falls back to Uzbek."""
    text_dict = TEXTS.get(key, {})
    text = text_dict.get(lang, text_dict.get("uz", key))
    if kwargs:
        try:
            text = text.format(**kwargs)
        except (KeyError, IndexError):
            pass
    return text


def btn(key: str, lang: str = "uz") -> str:
    """Get translated button label."""
    btn_dict = BUTTONS.get(key, {})
    return btn_dict.get(lang, btn_dict.get("uz", key))
