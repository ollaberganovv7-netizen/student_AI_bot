with open('handlers/admin.py', 'r', encoding='utf-8') as f:
    text = f.read()

code_to_find = '''    )

@router.message(Command("zero"))
async def admin_zero_balance_cmd(message: Message):
    if not is_admin(message.from_user.id):
        return
    args = message.text.split()
    if len(args) < 2:
        await message.answer("⚠️ Format: /zero <user_id>")
        return
    
    try:
        user_id = int(args[1])
        user = await set_balance(user_id, 0)
        if user:
            await message.answer(f"✅ Foydalanuvchi {user_id} balansi nolga tenglashtirildi.")
            try:
                await message.bot.send_message(user_id, "⚠️ Sizning balansingiz admin tomonidan nolga tenglashtirildi.")
            except:
                pass
        else:
            await message.answer("❌ Foydalanuvchi topilmadi.")
    except ValueError:
        await message.answer("❌ Noto'g'ri ID formati.")

'''

parts = text.split(code_to_find)
if len(parts) > 1:
    new_text = parts[0] + code_to_find + '    )\n\n'.join(parts[1:])
    with open('handlers/admin.py', 'w', encoding='utf-8') as f:
        f.write(new_text)
    print('Fixed!')
else:
    print('Not found')
