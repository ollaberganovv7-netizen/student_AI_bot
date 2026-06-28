import codecs
import re

with codecs.open('handlers/admin.py', 'r', 'utf-8') as f:
    content = f.read()

# Fix the reply keyboard
pattern_kb = r'keyboard=\[\s*\[KeyboardButton\(text="[^"]+Yaratish"\)\],\s*\[KeyboardButton\(text="[^"]+Bekor qilish"\)\]\s*\],'
new_kb = '''keyboard=[
                [KeyboardButton(text="✅ Yaratish")],
                [KeyboardButton(text="❌ Bekor qilish")]
            ],'''
content = re.sub(pattern_kb, new_kb, content)

# Fix the message text block in admin_approve_payment
pattern_text = r'text=\(\s*f"[^"]+<b>Tabriklaymiz! To\'lovingiz tasdiqlandi\.</b>\\n\\n"\s*f"[^"]+Balansingizga <b>\{payment\.amount:,\} so\'m</b> qo\'shildi\.\\n\\n"\s*f"[^"]+<b>Balansingiz yetarli!</b>\\n"\s*f"Endi <b>[^"]+Yaratish</b> tugmasini bosing!"\s*\),'
new_text = '''text=(
                f"🎉 <b>Tabriklaymiz! To'lovingiz tasdiqlandi.</b>\\n\\n"
                f"💰 Balansingizga <b>{payment.amount:,} so'm</b> qo'shildi.\\n\\n"
                f"✅ <b>Balansingiz yetarli!</b>\\n"
                f"Endi <b>✅ Yaratish</b> tugmasini bosing!"
            ),'''
content = re.sub(pattern_text, new_text, content)

# Also fix the admin_add_balance_cmd success message if corrupted
pattern_add = r'f"[^"]+<b>Tabriklaymiz! Admin tomonidan balansingiz to\'ldirildi\.</b>\\n\\n"'
new_add = 'f"🎉 <b>Tabriklaymiz! Admin tomonidan balansingiz to\'ldirildi.</b>\\n\\n"'
content = re.sub(pattern_add, new_add, content)

pattern_add2 = r'f"[^"]+Balansingizga <b>\{amount:,\} so\'m</b> qo\'shildi\.\\n"'
new_add2 = 'f"💰 Balansingizga <b>{amount:,} so\'m</b> qo\'shildi.\\n"'
content = re.sub(pattern_add2, new_add2, content)

with codecs.open('handlers/admin.py', 'w', 'utf-8') as f:
    f.write(content)

print("Admin emojis fixed!")
