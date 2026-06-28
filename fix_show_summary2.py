import codecs
import re

with codecs.open('handlers/documents.py', 'r', 'utf-8') as f:
    content = f.read()

pattern = r'f"└─+┘\\n\\n"\\s+f"<i>Reja yoki ma\'lumotlarni o\'zgartirish uchun tugmalardan foydalaning\.</i>"\\s+\)'

def replacer(match):
    matched_box = match.group(0).split('f"<i>')[0].strip() # gets the box part
    return f'''{matched_box}
    )
    
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
            f"🔴 Yetishmayapti: <b>{{format_price(needed)}}</b>\\n\\n"
            f"{{get_cards_text()}}\\n"
            f"🧾 <i>Chekni to'g'ridan-to'g'ri shu yerga yuborishingiz mumkin.</i>"
        )'''

new_content, count = re.subn(pattern, replacer, content)

if count > 0:
    with codecs.open('handlers/documents.py', 'w', 'utf-8') as f:
        f.write(new_content)
    print(f"Replaced {count} instances using regex!")
else:
    print("Could not find pattern!")
