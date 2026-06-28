import codecs

with codecs.open('utils/i18n.py', 'r', 'utf-8') as f:
    content = f.read()

# For UZ
uz_old = '''            "▸ 🎨 <b>Taqdimot</b>\\n"
            "▸ 📄 <b>Referat</b>\\n"
            "▸ 📚 <b>Mustaqil ish</b>\\n"
            "▸ 📘 <b>Kurs ishi</b>\\n"
            "▸ 📋 <b>Avtomatik quiz tuzish</b>\\n"
            "▸ 🎓 <b>Diplom ishi</b>\\n\\n"'''
uz_new = '''            "▸ 📄 <b>Referat</b>\\n"
            "▸ 📚 <b>Mustaqil ish</b>\\n"
            "▸ 🎨 <b>Taqdimot</b>\\n"
            "▸ 📘 <b>Kurs ishi</b>\\n"
            "▸ 🎓 <b>Diplom ishi</b>\\n"
            "▸ 📋 <b>Avtomatik quiz tuzish</b>\\n\\n"'''

content = content.replace(uz_old, uz_new)

# For RU
ru_old = '''            "▸ 🎨 <b>Презентация</b>\\n"
            "▸ 📄 <b>Реферат</b>\\n"
            "▸ 📚 <b>Самост. работа</b>\\n"
            "▸ 📘 <b>Курсовая</b>\\n"
            "▸ 📋 <b>Автоматическое создание квизов</b>\\n"
            "▸ 🎓 <b>Дипломная работа</b>\\n\\n"'''
ru_new = '''            "▸ 📄 <b>Реферат</b>\\n"
            "▸ 📚 <b>Самост. работа</b>\\n"
            "▸ 🎨 <b>Презентация</b>\\n"
            "▸ 📘 <b>Курсовая</b>\\n"
            "▸ 🎓 <b>Дипломная работа</b>\\n"
            "▸ 📋 <b>Автоматическое создание квизов</b>\\n\\n"'''

content = content.replace(ru_old, ru_new)

# For EN
en_old = '''            "▸ 🎨 <b>Presentation</b>\\n"
            "▸ 📄 <b>Essay</b>\\n"
            "▸ 📚 <b>Independent work</b>\\n"
            "▸ 📘 <b>Coursework</b>\\n"
            "▸ 📋 <b>Automatic quiz creation</b>\\n"
            "▸ 🎓 <b>Diploma work</b>\\n\\n"'''
en_new = '''            "▸ 📄 <b>Essay</b>\\n"
            "▸ 📚 <b>Independent work</b>\\n"
            "▸ 🎨 <b>Presentation</b>\\n"
            "▸ 📘 <b>Coursework</b>\\n"
            "▸ 🎓 <b>Diploma work</b>\\n"
            "▸ 📋 <b>Automatic quiz creation</b>\\n\\n"'''

content = content.replace(en_old, en_new)

with codecs.open('utils/i18n.py', 'w', 'utf-8') as f:
    f.write(content)

print("Reordered services in welcome message")
