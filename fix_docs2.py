import codecs

with codecs.open('handlers/documents.py', 'r', 'utf-8') as f:
    content = f.read()

# Fix 1: The broken block inside the receipt handler
bad_part_1 = '''                f"──────────\\n\\n"
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
            f"🔴 Yetishmayapti: <b>{format_price(needed)}</b>\\n\\n"
            f"{get_cards_text()}\\n"
            f"🧾 <i>Chekni to'g'ridan-to'g'ri shu yerga yuborishingiz mumkin.</i>"
        )'''

good_part_1 = '''                f"──────────\\n\\n"
                f"<i>Reja yoki ma'lumotlarni o'zgartirish uchun tugmalardan foydalaning.</i>"
            )'''

if bad_part_1 in content:
    content = content.replace(bad_part_1, good_part_1)
    print("Fixed bad part 1!")
else:
    print("Could not find bad part 1!")
    # let's try finding a substring to see where it breaks
    if 'is_admin = db_user.id in ADMIN_IDS' in content:
        print("Found is_admin")

with codecs.open('handlers/documents.py', 'w', 'utf-8') as f:
    f.write(content)
