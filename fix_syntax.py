import codecs

with codecs.open('utils/i18n.py', 'r', 'utf-8') as f:
    content = f.read()

content = content.replace('},\\n\\n    "account": {', '},\n\n    "account": {')

with codecs.open('utils/i18n.py', 'w', 'utf-8') as f:
    f.write(content)

print("Fixed syntax")
