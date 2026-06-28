import codecs

with codecs.open('utils/i18n.py', 'r', 'utf-8') as f:
    content = f.read()

import re

# We will completely replace the 'welcome' dict to ensure professional formatting
# using EM Spaces (\u2003) which Telegram doesn't collapse.

new_welcome = '''    "welcome": {
        "uz": (
            "┌──────────────────────────┐\\n"
            "\\u2003\\u2003\\u2003🎓 <b>STUDENT AI</b>\\n"
            "\\u2003\\u2003<i>Akademik AI yordamchi</i>\\n"
            "└──────────────────────────┘\\n\\n"
            "\\u2003\\u2003\\u2003Salom, <b>{name}</b>! 👋\\n\\n"
            "╔══════════ 💳 ══════════╗\\n"
            "\\u2003\\u2003\\u2003\\u2003<b>{balance}</b>\\n"
            "╚════════════════════════╝\\n\\n"
            "▸ 🎨 <b>Taqdimot</b> <i>PPTX</i>  ─  <code>{pres_price}+</code>\\n"
            "▸ 📄 <b>Referat</b> <i>DOCX</i>  ─  <code>{essay_price}+</code>\\n"
            "▸ 📚 <b>Mustaqil ish</b>  ─  <code>{must_price}+</code>\\n"
            "▸ 📘 <b>Kurs ishi</b>  ─  <code>{kurs_price}+</code>\\n"
            "▸ 📝 <b>Tezis / Maqola</b>  ─  <code>{tezis_price}+</code>\\n"
            "▸ 📗 <b>Uslubiy ishlanma</b>  ─  <code>{uslubiy_price}+</code>\\n\\n"
            "┌ 💎 <b>Afzalliklar</b>\\n"
            "├ ⚡ 5 daqiqada tayyor\\n"
            "├ 🏛 Akademik formatga mos\\n"
            "├ 🇺🇿 O'zbek tilida sifatli\\n"
            "└ 🔄 24/7 ishlaymiz"
        ),
        "ru": (
            "┌──────────────────────────┐\\n"
            "\\u2003\\u2003\\u2003🎓 <b>STUDENT AI</b>\\n"
            "\\u2003<i>Академический AI ассистент</i>\\n"
            "└──────────────────────────┘\\n\\n"
            "\\u2003\\u2003\\u2003Привет, <b>{name}</b>! 👋\\n\\n"
            "╔══════════ 💳 ══════════╗\\n"
            "\\u2003\\u2003\\u2003\\u2003<b>{balance}</b>\\n"
            "╚════════════════════════╝\\n\\n"
            "▸ 🎨 <b>Презентация</b> <i>PPTX</i>  ─  <code>{pres_price}+</code>\\n"
            "▸ 📄 <b>Реферат</b> <i>DOCX</i>  ─  <code>{essay_price}+</code>\\n"
            "▸ 📚 <b>Самост. работа</b>  ─  <code>{must_price}+</code>\\n"
            "▸ 📘 <b>Курсовая</b>  ─  <code>{kurs_price}+</code>\\n"
            "▸ 📝 <b>Тезис / Статья</b>  ─  <code>{tezis_price}+</code>\\n"
            "▸ 📗 <b>Метод. пособие</b>  ─  <code>{uslubiy_price}+</code>\\n\\n"
            "┌ 💎 <b>Преимущества</b>\\n"
            "├ ⚡ Готово за 5 минут\\n"
            "├ 🏛 Академический формат\\n"
            "├ 📝 Качественный текст\\n"
            "└ 🔄 Работаем 24/7"
        ),
        "en": (
            "┌──────────────────────────┐\\n"
            "\\u2003\\u2003\\u2003🎓 <b>STUDENT AI</b>\\n"
            "\\u2003\\u2003<i>Academic AI Assistant</i>\\n"
            "└──────────────────────────┘\\n\\n"
            "\\u2003\\u2003\\u2003Hello, <b>{name}</b>! 👋\\n\\n"
            "╔══════════ 💳 ══════════╗\\n"
            "\\u2003\\u2003\\u2003\\u2003<b>{balance}</b>\\n"
            "╚════════════════════════╝\\n\\n"
            "▸ 🎨 <b>Presentation</b> <i>PPTX</i>  ─  <code>{pres_price}+</code>\\n"
            "▸ 📄 <b>Essay</b> <i>DOCX</i>  ─  <code>{essay_price}+</code>\\n"
            "▸ 📚 <b>Independent work</b>  ─  <code>{must_price}+</code>\\n"
            "▸ 📘 <b>Coursework</b>  ─  <code>{kurs_price}+</code>\\n"
            "▸ 📝 <b>Thesis / Article</b>  ─  <code>{tezis_price}+</code>\\n"
            "▸ 📗 <b>Methodical guide</b>  ─  <code>{uslubiy_price}+</code>\\n\\n"
            "┌ 💎 <b>Why choose us</b>\\n"
            "├ ⚡ Ready in 5 minutes\\n"
            "├ 🏛 Academic format\\n"
            "├ 📝 High quality text\\n"
            "└ 🔄 Available 24/7"
        ),
    },'''

# Find the welcome block boundaries
start_idx = content.find('    "welcome": {')
# find next key block
end_idx = content.find('    "account": {')

if start_idx != -1 and end_idx != -1:
    content = content[:start_idx] + new_welcome + "\\n\\n" + content[end_idx:]
    with codecs.open('utils/i18n.py', 'w', 'utf-8') as f:
        f.write(content)
    print("Updated successfully")
else:
    print("Could not find blocks")

