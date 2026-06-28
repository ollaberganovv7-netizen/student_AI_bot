import codecs

with codecs.open('utils/i18n.py', 'r', 'utf-8') as f:
    content = f.read()

# Replace normal spaces with Hangul Fillers (U+3164) to prevent collapsing
content = content.replace('✨    Salom, <b>{name}</b>! 👋    ✨', '✨ㅤㅤㅤㅤSalom, <b>{name}</b>! 👋ㅤㅤㅤㅤ✨')
content = content.replace('✨    Привет, <b>{name}</b>! 👋    ✨', '✨ㅤㅤㅤㅤПривет, <b>{name}</b>! 👋ㅤㅤㅤㅤ✨')
content = content.replace('✨    Hello, <b>{name}</b>! 👋    ✨', '✨ㅤㅤㅤㅤHello, <b>{name}</b>! 👋ㅤㅤㅤㅤ✨')

with codecs.open('utils/i18n.py', 'w', 'utf-8') as f:
    f.write(content)

print("Centered greeting successfully")
