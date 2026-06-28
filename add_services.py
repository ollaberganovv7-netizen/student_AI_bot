import codecs

# 1. Update i18n.py
with codecs.open('utils/i18n.py', 'r', 'utf-8') as f:
    content = f.read()

uz_new = '''            "▸ 📘 <b>Kurs ishi</b>  ─  <code>{kurs_price}+</code>\\n"
            "▸ 📋 <b>Avtomatik quiz tuzish</b>  ─  <code>{quiz_price}+</code>\\n"
            "▸ 🎓 <b>Diplom ishi</b>  ─  <code>{diplom_price}+</code>\\n\\n"'''
content = content.replace('            "▸ 📘 <b>Kurs ishi</b>  ─  <code>{kurs_price}+</code>\\n\\n"', uz_new)

ru_new = '''            "▸ 📘 <b>Курсовая</b>  ─  <code>{kurs_price}+</code>\\n"
            "▸ 📋 <b>Автоматическое создание квизов</b>  ─  <code>{quiz_price}+</code>\\n"
            "▸ 🎓 <b>Дипломная работа</b>  ─  <code>{diplom_price}+</code>\\n\\n"'''
content = content.replace('            "▸ 📘 <b>Курсовая</b>  ─  <code>{kurs_price}+</code>\\n\\n"', ru_new)

en_new = '''            "▸ 📘 <b>Coursework</b>  ─  <code>{kurs_price}+</code>\\n"
            "▸ 📋 <b>Automatic quiz creation</b>  ─  <code>{quiz_price}+</code>\\n"
            "▸ 🎓 <b>Diploma work</b>  ─  <code>{diplom_price}+</code>\\n\\n"'''
content = content.replace('            "▸ 📘 <b>Coursework</b>  ─  <code>{kurs_price}+</code>\\n\\n"', en_new)

with codecs.open('utils/i18n.py', 'w', 'utf-8') as f:
    f.write(content)

# 2. Update start.py
with codecs.open('handlers/start.py', 'r', 'utf-8') as f:
    start_content = f.read()

old_format = '''             kurs_price=format_price(PRICING['coursework_low']),
             tezis_price=format_price(PRICING['tezis_5']),
             uslubiy_price=format_price(PRICING['uslubiy_low']))'''

new_format = '''             kurs_price=format_price(PRICING['coursework_low']),
             quiz_price=format_price(PRICING.get('quiz_std', 5000)),
             diplom_price=format_price(PRICING.get('diplom_low', 25000)),
             tezis_price=format_price(PRICING.get('tezis_5', 4000)),
             uslubiy_price=format_price(PRICING.get('uslubiy_low', 15000)))'''

start_content = start_content.replace(old_format, new_format)

with codecs.open('handlers/start.py', 'w', 'utf-8') as f:
    f.write(start_content)

print("Updated text successfully")
