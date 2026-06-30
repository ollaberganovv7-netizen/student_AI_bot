with open('services/ai_service.py', 'r', encoding='utf-8') as f:
    text = f.read()

target = 'Vazifa: Referat uchun REJA tuzing.\n'
replacement = target + '            f"DIQQAT: Rejada AYNAN {num_chapters} ta Asosiy Bob bo\'lishi SHART! Undan oshib ketmasin yoki kamaymasin.\\n"\n'

if target in text:
    text = text.replace(target, replacement)
    with open('services/ai_service.py', 'w', encoding='utf-8') as f:
        f.write(text)
    print('Successfully updated ai_service.py')
else:
    print('Target not found!')
