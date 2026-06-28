import codecs

with codecs.open('utils/i18n.py', 'r', 'utf-8') as f:
    content = f.read()

old_block = '''    "choose_lang": {
        "uz": "🇺🇿 Tugmalar, va boshqaruv xabarlarini tilini tanlash uchun quyidagi tugmalardan foydalaning.\\n🇷🇺 Используйте следующие кнопки для выбора языка интерфейса.\\n🇬🇧 Use the following buttons to select the interface language.",
        "ru": "🇺🇿 Tugmalar, va boshqaruv xabarlarini tilini tanlash uchun quyidagi tugmalardan foydalaning.\\n🇷🇺 Используйте следующие кнопки для выбора языка интерфейса.\\n🇬🇧 Use the following buttons to select the interface language.",
        "en": "🇺🇿 Tugmalar, va boshqaruv xabarlarini tilini tanlash uchun quyidagi tugmalardan foydalaning.\\n🇷🇺 Используйте следующие кнопки для выбора языка интерфейса.\\n🇬🇧 Use the following buttons to select the interface language.",
    },'''

new_text = "🌐 <b>Iltimos, tilni tanlang</b>\\nSizga qulay tilni tanlab, davom eting.\\n\\n<b>Пожалуйста, выберите язык</b>\\nВыберите удобный язык и продолжите.\\n\\n<b>Please select a language</b>\\nChoose your preferred language to continue."

new_block = f'''    "choose_lang": {{
        "uz": "{new_text}",
        "ru": "{new_text}",
        "en": "{new_text}",
    }},'''

if 'Tugmalar, va boshqaruv' in content:
    import re
    # We will use regex to safely replace the choose_lang block
    pattern = r'"choose_lang":\s*\{[^}]+\},'
    content = re.sub(pattern, new_block, content)
    with codecs.open('utils/i18n.py', 'w', 'utf-8') as f:
        f.write(content)
    print("Updated i18n.py successfully!")
else:
    print("Could not find the old block.")
