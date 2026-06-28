import codecs

with codecs.open('keyboards/main_kb.py', 'r', 'utf-8') as f:
    content = f.read()

old_kb = '''        keyboard=[
            [KeyboardButton(text=btn("referat", lang))],
            [KeyboardButton(text=btn("mustaqil", lang))],
            [KeyboardButton(text=btn("presentation", lang))],
            [KeyboardButton(text=btn("kurs", lang))],
            [KeyboardButton(text=btn("diplom", lang))],
            [KeyboardButton(text=btn("quiz", lang))],
            [KeyboardButton(text=btn("receipt", lang))],
        ],'''

new_kb = '''        keyboard=[
            [KeyboardButton(text=btn("referat", lang)), KeyboardButton(text=btn("mustaqil", lang))],
            [KeyboardButton(text=btn("presentation", lang)), KeyboardButton(text=btn("kurs", lang))],
            [KeyboardButton(text=btn("diplom", lang)), KeyboardButton(text=btn("quiz", lang))],
            [KeyboardButton(text=btn("receipt", lang))],
        ],'''

content = content.replace(old_kb, new_kb)

with codecs.open('keyboards/main_kb.py', 'w', 'utf-8') as f:
    f.write(content)

print("Updated keyboard layout to 2 buttons per row in main_kb.py")
