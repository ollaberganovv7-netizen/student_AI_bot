import codecs
with codecs.open('keyboards/main_kb.py', 'r', 'utf-8') as f:
    content = f.read()

content = content.replace('],\\n            [KeyboardButton', '],\n            [KeyboardButton')

with codecs.open('keyboards/main_kb.py', 'w', 'utf-8') as f:
    f.write(content)
