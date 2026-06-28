import codecs
import re

with codecs.open('handlers/documents.py', 'r', 'utf-8') as f:
    content = f.read()

# I will replace all instances of:
# f"<i>Reja yoki ma'lumotlarni o'zgartirish uchun tugmalardan foydalaning.</i>"
# with the dynamic text

def replacer(match):
    return '''    is_admin = db_user.id in ADMIN_IDS
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
        )'''

# Find all places where the literal string is appended to text
pattern = r'f"<i>Reja yoki ma\'lumotlarni o\'zgartirish uchun tugmalardan foydalaning\.</i>"'

# We need to make sure we replace it correctly. 
# Usually it looks like: text += f"<i>...</i>" or it's part of the text = ( ... ) block.
# Let's see how it looks in documents.py

