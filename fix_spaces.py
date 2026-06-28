import codecs

with codecs.open('utils/i18n.py', 'r', 'utf-8') as f:
    content = f.read()

# Replace the literal string "\u2003" with actual ideographic spaces
# 1 ideographic space (U+3000) is very wide.
content = content.replace('\\u2003\\u2003\\u2003🎓', '　　　🎓')
content = content.replace('\\u2003\\u2003<i>Akademik', '　　<i>Akademik')
content = content.replace('\\u2003\\u2003\\u2003Salom', '　　　Salom')
content = content.replace('\\u2003\\u2003\\u2003\\u2003<b>{balance}', '　　　　<b>{balance}')

content = content.replace('\\u2003<i>Академический', '　<i>Академический')
content = content.replace('\\u2003\\u2003\\u2003Привет', '　　　Привет')

content = content.replace('\\u2003\\u2003<i>Academic', '　　<i>Academic')
content = content.replace('\\u2003\\u2003\\u2003Hello', '　　　Hello')

with codecs.open('utils/i18n.py', 'w', 'utf-8') as f:
    f.write(content)
