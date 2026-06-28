import os
import re

file_path = r'handlers\documents.py'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

pattern = r'''    if can_afford:\s*if is_mustaqil:\s*kb = InlineKeyboardMarkup\(inline_keyboard=\[\s*\[InlineKeyboardButton\(text="✅ Mavzu yozib yaratish", callback_data=f"doc_confirm:\{service_type\}"\)\],\s*\[InlineKeyboardButton\(text="📄 Fayldan yaratish", callback_data=f"doc_file:\{service_type\}"\)\],\s*\[InlineKeyboardButton\(text="❌ Bekor qilish", callback_data="doc_cancel"\)\]\s*\]\)\s*else:\s*kb = InlineKeyboardMarkup\(inline_keyboard=\[\s*\[InlineKeyboardButton\(text="✅ Davom etish", callback_data=f"doc_confirm:\{service_type\}"\)\],\s*\[InlineKeyboardButton\(text="❌ Bekor qilish", callback_data="doc_cancel"\)\]\s*\]\)\s*status_line = "✅ <b>Balansingiz yetarli!</b>"\s*else:\s*needed = price_std - balance\s*kb = InlineKeyboardMarkup\(inline_keyboard=\[\s*\[InlineKeyboardButton\(text="💳 Balans to'ldirish", callback_data="doc_topup"\)\],\s*\[InlineKeyboardButton\(text="❌ Bekor qilish", callback_data="doc_cancel"\)\]\s*\]\)\s*status_line = f"⚠️ <b>Balansingiz yetarli emas!</b>\\n🔴 Yetishmayapti: <b>\{format_price\(price_std - balance\)\}</b>"\s*await message\.answer\(\s*f"\{service_label\}\\n\\n"\s*f"──────────────────\\n"\s*f"💰 <b>Narx:</b> \{format_price\(price_std\)\} — \{format_price\(price_pro\)\}\\n"\s*f"   <i>\(Standart va Pro sifatiga qarab\)</i>\\n"\s*f"👛 <b>Sizning balansingiz:</b> \{balance_display\}\\n"\s*f"──────────────────\\n"\s*f"\{status_line\}",\s*reply_markup=kb,\s*parse_mode="HTML"\s*\)'''

replacement = r'''    if is_mustaqil:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Mavzu yozib yaratish", callback_data=f"doc_confirm:{service_type}")],
            [InlineKeyboardButton(text="📄 Fayldan yaratish", callback_data=f"doc_file:{service_type}")],
            [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="doc_cancel")]
        ])
    else:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Davom etish", callback_data=f"doc_confirm:{service_type}")],
            [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="doc_cancel")]
        ])

    await message.answer(
        f"{service_label}\n\n"
        f"──────────────────\n"
        f"💰 <b>Narx:</b> {format_price(price_std)} — {format_price(price_pro)}\n"
        f"   <i>(Standart va Pro sifatiga qarab)</i>\n"
        f"👛 <b>Sizning balansingiz:</b> {balance_display}\n"
        f"──────────────────",
        reply_markup=kb,
        parse_mode="HTML"
    )'''

new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)
if new_content != content:
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("documents.py updated!")
else:
    print("documents.py regex failed!")

