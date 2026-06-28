import codecs

# 1. UPDATE DOCUMENTS.PY
with codecs.open('handlers/documents.py', 'r', 'utf-8') as f:
    doc_content = f.read()

# Update service label
doc_content = doc_content.replace(
    'service_label = "📚 <b>Referat</b>" if is_referat else "📄 <b>Mustaqil Ish</b>"',
    'service_label = "ㅤㅤㅤㅤㅤ📚 <b>Referat</b>" if is_referat else "ㅤㅤㅤㅤ📄 <b>Mustaqil Ish</b>"'
)

# Remove balance text
old_msg = '''    await message.answer(
        f"{service_label}\\n\\n"
        f"━━━━━━━━━━━━━━━━\\n"
        f"💰 <b>Narx:</b> {format_price(price_std)} — {format_price(price_pro)}\\n"
        f"   <i>(Standart va Pro sifatiga qarab)\\n"'''

# wait, there's no trailing quote there, let's use exact match
old_msg_exact = '''    await message.answer(
        f"{service_label}\\n\\n"
        f"━━━━━━━━━━━━━━━━\\n"
        f"💰 <b>Narx:</b> {format_price(price_std)} — {format_price(price_pro)}\\n"
        f"   <i>(Standart va Pro sifatiga qarab)</i>\\n"
        f"👛 <b>Sizning balansingiz:</b> {balance_display}\\n"
        f"━━━━━━━━━━━━━━━━\\n",'''

new_msg_exact = '''    await message.answer(
        f"{service_label}\\n\\n"
        f"━━━━━━━━━━━━━━━━\\n"
        f"💰 <b>Narx:</b> {format_price(price_std)} — {format_price(price_pro)}\\n"
        f"   <i>(Standart va Pro sifatiga qarab)</i>\\n"
        f"━━━━━━━━━━━━━━━━\\n",'''

doc_content = doc_content.replace(old_msg_exact, new_msg_exact)

with codecs.open('handlers/documents.py', 'w', 'utf-8') as f:
    f.write(doc_content)

# 2. UPDATE COURSEWORK.PY
with codecs.open('handlers/coursework.py', 'r', 'utf-8') as f:
    cw_content = f.read()

# Update label
cw_content = cw_content.replace(
    '"📘 <b>Kurs Ishi</b>\\n"',
    '"ㅤㅤㅤㅤㅤ📘 <b>Kurs Ishi</b>\\n"'
)

# Remove balance text
cw_old = '''        f"   <i>(sahifalar soniga qarab)</i>\\n"
        f"👛 <b>Sizning balansingiz:</b> {balance_display}\\n"
        "──────────\\n",'''

cw_new = '''        f"   <i>(sahifalar soniga qarab)</i>\\n"
        "──────────\\n",'''

cw_content = cw_content.replace(cw_old, cw_new)

with codecs.open('handlers/coursework.py', 'w', 'utf-8') as f:
    f.write(cw_content)

print("Updated documents.py and coursework.py")
