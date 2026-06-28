import codecs
import re

with codecs.open('handlers/uslubiy.py', 'r', 'utf-8', errors='ignore') as f:
    content = f.read()

# Find the end of safe_delete_message function
match1 = re.search(r'def safe_delete_message.*?\n\s*pass\n+', content, re.DOTALL)
if not match1:
    print("Could not find safe_delete_message")
else:
    start_idx = match1.end()
    
    # Find the start of confirm_uslubiy
    match2 = re.search(r'@router\.callback_query\(F\.data == "usl_confirm"\)', content)
    if not match2:
        print("Could not find usl_confirm")
    else:
        end_idx = match2.start()
        
        new_block = '''# ─── Step 1: Start ──────────────────────────────────────────────────────────

@router.message(F.text.in_(["📘 Uslubiy Ishlanma", "📘 Uslubiy ishlanma"]))
async def start_uslubiy_creation(message: Message, state: FSMContext, db_user: User):
    price_low  = PRICING.get("uslubiy_low", 15000)
    price_high = PRICING.get("uslubiy_high", 25000)
    is_admin = db_user.id in ADMIN_IDS
    balance = db_user.balance or 0
    balance_display = "🛡️ Admin (tekin)" if is_admin else format_price(balance)

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Davom etish", callback_data="usl_confirm")],
        [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="usl_cancel")]
    ])

    await state.update_data(service_type="uslubiy")
    await message.answer(
        "📘 <b>Uslubiy Ishlanma</b>\\n"
        "<i>To'liq akademik uslubiy ishlanma — mundarija, kirish, boblar, xulosa, adabiyotlar</i>\\n\\n"
        "──────────\\n"
        f"💰 <b>Narx:</b> {format_price(price_low)} — {format_price(price_high)}\\n"
        f"   <i>(Sahifalar soniga qarab)</i>\\n"
        f"👛 <b>Sizning balansingiz:</b> {balance_display}\\n"
        "──────────\\n",
        reply_markup=kb,
        parse_mode="HTML"
    )

'''
        new_content = content[:start_idx] + new_block + content[end_idx:]
        with codecs.open('handlers/uslubiy.py', 'w', 'utf-8') as f:
            f.write(new_content)
        print("Fixed successfully!")

