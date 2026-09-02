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
            "          🎓 <b>USTOZ AI</b> 🧠\n\n"
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
            "          🎓 <b>USTOZ AI</b> 🧠\n\n"
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
            "          🎓 <b>USTOZ AI</b> 🧠\n\n"
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

}
