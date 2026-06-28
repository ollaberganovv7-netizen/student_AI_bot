import codecs

# 1. Update i18n.py to add 'diplom' button translation
with codecs.open('utils/i18n.py', 'r', 'utf-8') as f:
    i18n_content = f.read()

quiz_btn = '"quiz": {"uz": "📋 Avtomatik quiz tuzish", "ru": "📋 Автоматический тест", "en": "📋 Auto Quiz Maker"},'
diplom_btn = '"diplom": {"uz": "🎓 Diplom ishi yaratish", "ru": "🎓 Дипломная работа", "en": "🎓 Diploma Work"},'

if '"diplom": {' not in i18n_content:
    i18n_content = i18n_content.replace(quiz_btn, quiz_btn + '\n    ' + diplom_btn)
    with codecs.open('utils/i18n.py', 'w', 'utf-8') as f:
        f.write(i18n_content)
    print("Added diplom translation to i18n.py")

# 2. Update main_kb.py to remove the 'receipt' button
with codecs.open('keyboards/main_kb.py', 'r', 'utf-8') as f:
    kb_content = f.read()

old_kb = '''        keyboard=[
            [KeyboardButton(text=btn("referat", lang)), KeyboardButton(text=btn("mustaqil", lang))],
            [KeyboardButton(text=btn("presentation", lang)), KeyboardButton(text=btn("kurs", lang))],
            [KeyboardButton(text=btn("diplom", lang)), KeyboardButton(text=btn("quiz", lang))],
            [KeyboardButton(text=btn("receipt", lang))],
        ],'''

new_kb = '''        keyboard=[
            [KeyboardButton(text=btn("referat", lang)), KeyboardButton(text=btn("mustaqil", lang))],
            [KeyboardButton(text=btn("presentation", lang)), KeyboardButton(text=btn("kurs", lang))],
            [KeyboardButton(text=btn("diplom", lang)), KeyboardButton(text=btn("quiz", lang))],
        ],'''

kb_content = kb_content.replace(old_kb, new_kb)

with codecs.open('keyboards/main_kb.py', 'w', 'utf-8') as f:
    f.write(kb_content)
print("Removed receipt button from main_kb.py")

