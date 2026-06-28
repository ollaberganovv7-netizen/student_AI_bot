import codecs

with codecs.open('handlers/documents.py', 'r', 'utf-8') as f:
    lines = f.readlines()

new_block = '''    )
    is_admin = db_user.id in ADMIN_IDS
    from utils.helpers import is_free_trial
    free_trial = is_free_trial(db_user) and not is_admin
    balance = db_user.balance or 0
    
    if is_admin or free_trial or balance >= price:
        text += f"<i>Reja yoki ma'lumotlarni o'zgartirish uchun tugmalardan foydalaning.</i>"
    else:
        needed = price - balance
        from handlers.payment import get_cards_text
        text += (
            f"⚠️ <b>Sizning hisobingizda mablag' yetarli emas!</b>\\n"
            f"🔴 Yetishmayapti: <b>{format_price(needed)}</b>\\n\\n"
            f"{get_cards_text()}\\n"
            f"🧾 <i>Chekni to'g'ridan-to'g'ri shu yerga yuborishingiz mumkin.</i>"
        )
'''

# We know the line is exactly at index 599-600
for i, line in enumerate(lines):
    if "Reja yoki ma'lumotlarni" in line and "    )" in lines[i+1]:
        # found it!
        lines[i] = ""
        lines[i+1] = new_block
        print(f"Replaced at line {i+1}!")

with codecs.open('handlers/documents.py', 'w', 'utf-8') as f:
    f.writelines(lines)
