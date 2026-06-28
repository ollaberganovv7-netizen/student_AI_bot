import codecs

with codecs.open('handlers/uslubiy.py', 'r', 'utf-8') as f:
    content = f.read()

# 1. Modify the text generation
old_text = '''        f"💰 <b>Narxi:</b> {format_price(price)}\\n\\n"
        f"<i>Reja yoki ma'lumotlarni o'zgartirish uchun tugmalardan foydalaning.</i>"
    )'''

new_text = '''        f"💰 <b>Narxi:</b> {format_price(price)}\\n\\n"
    )
    is_admin = db_user.id in ADMIN_IDS
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
content = content.replace(old_text, new_text)

# 2. Add the receipt handler
receipt_handler = '''@router.message(UslubiyStates.reviewing_summary, F.photo)
async def receive_uslubiy_receipt(message: Message, state: FSMContext, bot: Bot, db_user: User):
    photo = message.photo[-1]
    file_id = photo.file_id
    
    data = await state.get_data()
    price = data.get("price", 13000)
    
    wait_msg = await message.answer("⏳ Chek tekshirilmoqda. Iltimos biroz kuting...")
    
    try:
        import base64
        from io import BytesIO
        file_info = await bot.get_file(file_id)
        file_bytes = BytesIO()
        await bot.download_file(file_info.file_path, file_bytes)
        base64_img = base64.b64encode(file_bytes.getvalue()).decode("utf-8")
        
        from services.ai_service import verify_receipt_with_ai
        result = await verify_receipt_with_ai(base64_img, price)
        
        await wait_msg.delete()
        
        if result.get("verified") and result.get("amount", 0) >= price:
            from database.db import add_balance
            db_user = await add_balance(db_user.id, price)
            await message.answer(f"✅ To'lov muvaffaqiyatli tasdiqlandi! Balansingizga {format_price(price)} qo'shildi.\\nEndi <b>✅ Yaratish</b> tugmasini bosishingiz mumkin.", parse_mode="HTML")
            
            # Re-render summary
            from keyboards.documents_kb import referat_summary_kb
            from utils.i18n import t
            
            topic = data.get("topic")
            subject = data.get("subject", "")
            university = data.get("university", "")
            author = data.get("author", "")
            mash_count = data.get("mashgulot_count", 0)
            pages = data.get("num_pages")
            
            text = (
                f"📝 <b>USLUBIY ISHLANMA | ✨ Pro</b>\\n\\n"
                f"📚 <b>Mavzu:</b> {topic}\\n"
                f"🎓 <b>Fan:</b> {subject}\\n"
                f"🏫 <b>Universitet:</b> {university}\\n"
                f"👤 <b>Muallif:</b> {author}\\n"
                f"🔢 <b>Mashg'ulotlar soni:</b> {mash_count} ta\\n"
                f"📄 <b>Sahifalar:</b> ~{pages} bet\\n"
                f"💰 <b>Narxi:</b> {format_price(price)}\\n\\n"
                f"<i>Reja yoki ma'lumotlarni o'zgartirish uchun tugmalardan foydalaning.</i>"
            )
            msg = await message.answer(text, reply_markup=referat_summary_kb(
                balance=db_user.balance or 0, price=price, name=db_user.full_name or "", 
                topic=topic, doc_type="uslubiy", quality="pro", lang=db_user.language or "uz"
            ), parse_mode="HTML")
            await state.update_data(summary_msg_id=msg.message_id)
            return
        else:
            reason = result.get("reason", "Noma'lum xatolik")
            await message.answer(f"⚠️ Chekni avtomatik tasdiqlab bo'lmadi.\\nSabab: <i>{reason}</i>\\n\\nChek adminga qo'lda tasdiqlash uchun yuborilmoqda...", parse_mode="HTML")
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Error checking receipt: {e}")
        try:
            await wait_msg.delete()
        except:
            pass
        await message.answer("⚠️ Chekni avtomatik tekshirishda xatolik yuz berdi. Adminga yuborilmoqda...")
        
    from database.db import create_payment
    payment = await create_payment(user_id=db_user.id, amount=price, package="doc_uslubiy", screenshot_file_id=file_id)
    
    from keyboards.admin_kb import payment_action_kb
    admin_text = (
        f"💰 <b>Yangi to'lov so'rovi! (Uslubiy)</b>\\n\\n"
        f"👤 Foydalanuvchi: {db_user.full_name}\\n"
        f"🆔 ID: <code>{db_user.id}</code>\\n"
        f"💵 Summa: {format_price(price)}\\n"
        f"🧾 ID: #{payment.id}"
    )
    
    from config import ADMIN_IDS
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_photo(chat_id=admin_id, photo=file_id, caption=admin_text, reply_markup=payment_action_kb(payment.id, db_user.id), parse_mode="HTML")
        except Exception:
            pass

@router.message(F.text == "✅ Yaratish", UslubiyStates.reviewing_summary)'''

content = content.replace('@router.message(F.text == "✅ Yaratish", UslubiyStates.reviewing_summary)', receipt_handler)

with codecs.open('handlers/uslubiy.py', 'w', 'utf-8') as f:
    f.write(content)
print("Updated uslubiy.py!")
