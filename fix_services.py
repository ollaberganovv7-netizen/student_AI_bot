import codecs

with codecs.open('utils/i18n.py', 'r', 'utf-8') as f:
    content = f.read()

uz_old = '''            "▸ 📘 <b>Kurs ishi</b>  ─  <code>{kurs_price}+</code>\\n"
            "\\n"
            "┌ 💎 <b>Afzalliklar</b>\\n"'''
uz_new = '''            "▸ 📘 <b>Kurs ishi</b>  ─  <code>{kurs_price}+</code>\\n"
            "▸ 📋 <b>Avtomatik quiz tuzish</b>  ─  <code>{quiz_price}+</code>\\n"
            "▸ 🎓 <b>Diplom ishi</b>  ─  <code>{diplom_price}+</code>\\n\\n"
            "┌ 💎 <b>Afzalliklar</b>\\n"'''
content = content.replace(uz_old, uz_new)

ru_old = '''            "▸ 📘 <b>Курсовая</b>  ─  <code>{kurs_price}+</code>\\n"
            "\\n"
            "┌ 💎 <b>Преимущества</b>\\n"'''
ru_new = '''            "▸ 📘 <b>Курсовая</b>  ─  <code>{kurs_price}+</code>\\n"
            "▸ 📋 <b>Автоматическое создание квизов</b>  ─  <code>{quiz_price}+</code>\\n"
            "▸ 🎓 <b>Дипломная работа</b>  ─  <code>{diplom_price}+</code>\\n\\n"
            "┌ 💎 <b>Преимущества</b>\\n"'''
content = content.replace(ru_old, ru_new)

en_old = '''            "▸ 📘 <b>Coursework</b>  ─  <code>{kurs_price}+</code>\\n"
            "\\n"
            "┌ 💎 <b>Why choose us</b>\\n"'''
en_new = '''            "▸ 📘 <b>Coursework</b>  ─  <code>{kurs_price}+</code>\\n"
            "▸ 📋 <b>Automatic quiz creation</b>  ─  <code>{quiz_price}+</code>\\n"
            "▸ 🎓 <b>Diploma work</b>  ─  <code>{diplom_price}+</code>\\n\\n"
            "┌ 💎 <b>Why choose us</b>\\n"'''
content = content.replace(en_old, en_new)

with codecs.open('utils/i18n.py', 'w', 'utf-8') as f:
    f.write(content)

print("Fixed services in i18n.py")
