import codecs

new_welcome = '''    "welcome": {
        "uz": (
            "┌──────────────────────────┐\\n"
            "│      🎓 <b>STUDENT AI</b>       │\\n"
            "│   <i>Akademik AI yordamchi</i>  │\\n"
            "└──────────────────────────┘\\n\\n"
            "✨    Salom, <b>{name}</b>! 👋    ✨\\n\\n"
            "╔══════════ 💳 ══════════╗\\n"
            "║        <b>{balance}</b>        ║\\n"
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
            "│      🎓 <b>STUDENT AI</b>       │\\n"
            "│ <i>Академический ИИ помощник</i>│\\n"
            "└──────────────────────────┘\\n\\n"
            "✨    Привет, <b>{name}</b>! 👋   ✨\\n\\n"
            "╔══════════ 💳 ══════════╗\\n"
            "║        <b>{balance}</b>        ║\\n"
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
            "│      🎓 <b>STUDENT AI</b>       │\\n"
            "│  <i>Academic AI Assistant</i>   │\\n"
            "└──────────────────────────┘\\n\\n"
            "✨    Hello, <b>{name}</b>! 👋    ✨\\n\\n"
            "╔══════════ 💳 ══════════╗\\n"
            "║        <b>{balance}</b>        ║\\n"
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

with codecs.open('utils/i18n.py', 'r', 'utf-8') as f:
    content = f.read()

start_idx = content.find('    "welcome": {')
end_idx = content.find('    "account": {')

if start_idx != -1 and end_idx != -1:
    content = content[:start_idx] + new_welcome + "\\n\\n" + content[end_idx:]
    with codecs.open('utils/i18n.py', 'w', 'utf-8') as f:
        f.write(content)
    print("Replaced robustly")
else:
    print("Could not find blocks")
