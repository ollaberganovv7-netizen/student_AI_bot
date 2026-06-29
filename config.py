from __future__ import annotations
import os
from dotenv import load_dotenv

load_dotenv()

# Bot
BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
ADMIN_IDS: list[int] = [int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()]
ADMIN_USERNAME: str = os.getenv("ADMIN_USERNAME", "@admin_username")

# Claude (primary)
ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
CLAUDE_MODEL: str = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-6")

# OpenAI (fallback)
OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o")

# Gemini AI (research + Google Search)
GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

# Image search (free)
UNSPLASH_ACCESS_KEY: str = os.getenv("UNSPLASH_ACCESS_KEY", "")
PEXELS_API_KEY: str = os.getenv("PEXELS_API_KEY", "")


# Database
DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./student_bot.db")

# Payment cards
CARDS = []
for i in range(1, 5):
    num = os.getenv(f"CARD_NUMBER_{i}")
    holder = os.getenv(f"CARD_HOLDER_{i}")
    if num and holder:
        CARDS.append({"number": num, "holder": holder})

# Fallback to old variables if new ones aren't set
if not CARDS:
    old_num = os.getenv("CARD_NUMBER")
    old_holder = os.getenv("CARD_HOLDER")
    if old_num and old_holder:
        CARDS.append({"number": old_num, "holder": old_holder})
    else:
        CARDS.append({"number": "8600 0000 0000 0000", "holder": "Bot Owner"})

# Payment Tokens (from @BotFather)
PAYME_TOKEN: str = os.getenv("PAYME_TOKEN", "")
CLICK_TOKEN: str = os.getenv("CLICK_TOKEN", "")

# Pricing (UZS)
PRICING = {
    "presentation_std_low": 3000,   # 10-14 slides
    "presentation_std_mid": 7000,   # 15-22 slides
    "presentation_std_high": 9000,  # 23-30 slides
    "presentation_pre_low": 8000,   # 10-14 slides
    "presentation_pre_mid": 12000,  # 15-22 slides
    "presentation_pre_high": 16000, # 23-30 slides
    "essay_std": 5000,
    "essay_pre": 15000,
    "mustaqil_std": 5000,
    "mustaqil_pre": 12000,
    "coursework_low": 15000,        # 20-25 pages
    "coursework_high": 25000,       # 40-50 pages
    "tezis_5": 4000,
    "tezis_10": 6000,
    "tezis_15": 8000,
    "tezis_20": 10000,
    "maqola_5": 4000,
    "maqola_10": 6000,
    "maqola_15": 8000,
    "maqola_20": 10000,
    "other": 5000,
    "uslubiy_low": 15000,         # 20-25 pages
    "uslubiy_high": 25000,        # 40-50 pages
}

# Top-up packages
TOPUP_OPTIONS = {
    "topup_3": {"label": "💵 3 000 so'm", "amount": 3000},
    "topup_5": {"label": "💵 5 000 so'm", "amount": 5000},
    "topup_10": {"label": "💵 10 000 so'm", "amount": 10000},
    "topup_20": {"label": "💵 20 000 so'm", "amount": 20000},
    "topup_50": {"label": "💵 50 000 so'm", "amount": 50000},
}

# Service type to display name
SERVICE_NAMES: dict[str, str] = {
    "essay": "📚 Referat",
    "article": "✅ Maqola",
    "report": "📄 Mustaqil Ish",
    "thesis": "🎓 Tezis",
    "resume": "🧾 Rezyume",
    "glossary": "📘 Glossary",
    "tech_map": "🧩 Texnologik xarita",
    "coursework": "📘 Kurs ishi",
    "uslubiy": "📗 Uslubiy ishlanma",
    "keys": "📝 Keys",
}

# Referral system
REFERRAL_BONUS_INVITER = 1000   # bonus for the person who invited (so'm)
REFERRAL_BONUS_INVITEE = 1000   # bonus for the new user who joined (so'm)

# Presentation languages
PRES_LANGUAGES: dict[str, str] = {
    "uz": "🇺🇿 O'zbek",
    "ru": "🇷🇺 Rus",
    "en": "🇬🇧 Ingliz",
}

# Slide options
SLIDE_OPTIONS: dict[str, dict] = {
    "10": {"label": "📊 10 tagacha slayd", "price_key": "presentation_10"},
    "15": {"label": "📊 15 tagacha slayd", "price_key": "presentation_15"},
}

# Presentation styles
PRES_STYLES: dict[str, dict] = {
    "classic": {
        "label": "🎨 Klassik PowerPoint uslubi",
        "file": "templates/classic.pptx",
    },
    "modern": {
        "label": "✨ Zamonaviy uslub",
        "file": "templates/modern.pptx",
    },
    "test_template": {
        "label": "🎓 Test (Universitet)",
        "file": "templates/power point/test.pptx",
    },
}
