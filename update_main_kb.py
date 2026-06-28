import codecs

with codecs.open('keyboards/main_kb.py', 'r', 'utf-8') as f:
    content = f.read()

content = content.replace(
    '[KeyboardButton(text=btn("quiz", lang))],',
    '[KeyboardButton(text=btn("quiz", lang))],\\n            [KeyboardButton(text=btn("diplom", lang))],'
)

with codecs.open('keyboards/main_kb.py', 'w', 'utf-8') as f:
    f.write(content)

print("Updated main_kb.py")
