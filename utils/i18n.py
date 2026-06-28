from __future__ import annotations
"""
Internationalization (i18n) — bot interface translations.
Supports: uz (O'zbek), ru (Русский), en (English)
"""

TEXTS = {
    # ─── Language selection ──────────────────────────────────────────────
    "lang_prompt": {
        "uz": "🇺🇿 <b>Iltimos, tilni tanlang</b>\nSizga qulay tilni tanlab, davom eting.\n\n🇷🇺 <b>Пожалуйста, выберите язык</b>\nВыберите удобный язык и продолжите.\n\n🇬🇧 <b>Please select a language</b>\nChoose your preferred language to continue.",
        "ru": "🇺🇿 <b>Iltimos, tilni tanlang</b>\nSizga qulay tilni tanlab, davom eting.\n\n🇷🇺 <b>Пожалуйста, выберите язык</b>\nВыберите удобный язык и продолжите.\n\n🇬🇧 <b>Please select a language</b>\nChoose your preferred language to continue.",
        "en": "🇺🇿 <b>Iltimos, tilni tanlang</b>\nSizga qulay tilni tanlab, davom eting.\n\n🇷🇺 <b>Пожалуйста, выберите язык</b>\nВыберите удобный язык и продолжите.\n\n🇬🇧 <b>Please select a language</b>\nChoose your preferred language to continue.",
    },
    "lang_set": {
        "uz": "✅ Til o'zbek tiliga o'zgartirildi!",
        "ru": "✅ Язык изменён на русский!",
        "en": "✅ Language changed to English!",
    },

    # ─── Welcome / Main menu ─────────────────────────────────────────────
    "welcome": {
        "uz": (
            "ㅤㅤㅤㅤㅤ🎓 <b>STUDENT AI</b>\n\n"
            "✨ㅤㅤㅤㅤSalom, <b>{name}</b>! 👋ㅤㅤㅤㅤ✨\n\n"
            "▸ 📄 <b>Referat</b>\n"
            "▸ 📚 <b>Mustaqil ish</b>\n"
            "▸ 🎨 <b>Taqdimot</b>\n"
            "▸ 📘 <b>Kurs ishi</b>\n"
            "▸ 🎓 <b>Diplom ishi</b>\n"
            "▸ 📋 <b>Avtomatik quiz tuzish</b>\n\n"
            "┌ 💎 <b>Afzalliklar</b>\n"
            "├ ⚡ 5 daqiqada tayyor\n"
            "├ 🏛 Akademik formatga mos\n"
            "├ 🇺🇿 O'zbek tilida sifatli\n"
            "└ 🔄 24/7 ishlaymiz"
        ),
        "ru": (
            "ㅤㅤㅤㅤㅤ🎓 <b>STUDENT AI</b>\n\n"
            "✨ㅤㅤㅤㅤПривет, <b>{name}</b>! 👋ㅤㅤㅤㅤ✨\n\n"
            "▸ 📄 <b>Реферат</b>\n"
            "▸ 📚 <b>Самост. работа</b>\n"
            "▸ 🎨 <b>Презентация</b>\n"
            "▸ 📘 <b>Курсовая</b>\n"
            "▸ 🎓 <b>Дипломная работа</b>\n"
            "▸ 📋 <b>Автоматическое создание квизов</b>\n\n"
            "┌ 💎 <b>Преимущества</b>\n"
            "├ ⚡ Готово за 5 минут\n"
            "├ 🏛 Академический формат\n"
            "├ 📝 Качественный текст\n"
            "└ 🔄 Работаем 24/7"
        ),
        "en": (
            "ㅤㅤㅤㅤㅤ🎓 <b>STUDENT AI</b>\n\n"
            "✨ㅤㅤㅤㅤHello, <b>{name}</b>! 👋ㅤㅤㅤㅤ✨\n\n"
            "▸ 📄 <b>Essay</b>\n"
            "▸ 📚 <b>Independent work</b>\n"
            "▸ 🎨 <b>Presentation</b>\n"
            "▸ 📘 <b>Coursework</b>\n"
            "▸ 🎓 <b>Diploma work</b>\n"
            "▸ 📋 <b>Automatic quiz creation</b>\n\n"
            "┌ 💎 <b>Why choose us</b>\n"
            "├ ⚡ Ready in 5 minutes\n"
            "├ 🏛 Academic format\n"
            "├ 📝 High quality text\n"
            "└ 🔄 Available 24/7"
        ),
    },

    "account": {
        "uz": (
            "┌─ 👤 <b>MENING HISOBIM</b> ─┐\n\n"
            "  🆔  <code>{user_id}</code>\n"
            "  👤  {full_name}\n"
            "  💰  <b>{balance} so'm</b>\n\n"
            "└──────────────────────┘"
        ),
        "ru": (
            "┌─ 👤 <b>МОЙ АККАУНТ</b> ─┐\n\n"
            "  🆔  <code>{user_id}</code>\n"
            "  👤  {full_name}\n"
            "  💰  <b>{balance} сум</b>\n\n"
            "└──────────────────────┘"
        ),
        "en": (
            "┌─ 👤 <b>MY ACCOUNT</b> ─┐\n\n"
            "  🆔  <code>{user_id}</code>\n"
            "  👤  {full_name}\n"
            "  💰  <b>{balance} UZS</b>\n\n"
            "└──────────────────────┘"
        ),
    },

    # ─── Referral ────────────────────────────────────────────────────────
    "referral": {
        "uz": (
            "👥 <b>Referal dasturi</b>\n\n"
            "Do'stlaringizni taklif qiling — ikkalangiz ham bonus olasiz!\n\n"
            "🎁 <b>Siz olasiz:</b> {bonus_inviter}\n"
            "🎁 <b>Do'stingiz oladi:</b> {bonus_invitee}\n\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "📊 <b>Sizning statistika:</b>\n"
            "👤 Taklif qilganlar: <b>{count}</b> ta\n"
            "💰 Jami daromad: <b>{earnings}</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            "🔗 <b>Sizning havola:</b>\n"
            "<code>{link}</code>\n\n"
            "👆 Havolani bosib nusxa oling va do'stlaringizga yuboring!"
        ),
        "ru": (
            "👥 <b>Реферальная программа</b>\n\n"
            "Приглашайте друзей — оба получите бонус!\n\n"
            "🎁 <b>Вы получите:</b> {bonus_inviter}\n"
            "🎁 <b>Друг получит:</b> {bonus_invitee}\n\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "📊 <b>Ваша статистика:</b>\n"
            "👤 Приглашено: <b>{count}</b>\n"
            "💰 Заработано: <b>{earnings}</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            "🔗 <b>Ваша ссылка:</b>\n"
            "<code>{link}</code>\n\n"
            "👆 Нажмите чтобы скопировать и отправьте друзьям!"
        ),
        "en": (
            "👥 <b>Referral Program</b>\n\n"
            "Invite friends — both of you get a bonus!\n\n"
            "🎁 <b>You get:</b> {bonus_inviter}\n"
            "🎁 <b>Friend gets:</b> {bonus_invitee}\n\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "📊 <b>Your stats:</b>\n"
            "👤 Invited: <b>{count}</b>\n"
            "💰 Earned: <b>{earnings}</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            "🔗 <b>Your link:</b>\n"
            "<code>{link}</code>\n\n"
            "👆 Tap to copy and send to friends!"
        ),
    },
    "referral_success": {
        "uz": "🎉 <b>Tabriklaymiz!</b>\n\nDo'stingiz sizni taklif qildi va siz\n💰 <b>{bonus}</b> bonus oldingiz!",
        "ru": "🎉 <b>Поздравляем!</b>\n\nВас пригласил друг и вы получили\n💰 <b>{bonus}</b> бонус!",
        "en": "🎉 <b>Congratulations!</b>\n\nYour friend invited you and you received\n💰 <b>{bonus}</b> bonus!",
    },
    "referral_share": {
        "uz": "\nStudent(AI) Bot - akademik ishlar uchun AI yordamchi! 🎓\n\nMana havola: {link}",
        "ru": "\nStudent(AI) Bot - AI помощник для учёбы! 🎓\n\nСсылка: {link}",
        "en": "\nStudent(AI) Bot - AI assistant for academics! 🎓\n\nLink: {link}",
    },
    "referral_btn": {
        "uz": "📤 Do'stga yuborish",
        "ru": "📤 Отправить другу",
        "en": "📤 Send to friend",
    },

    # ─── Presentation ────────────────────────────────────────────────────
    "pres_quality_premium": {
        "uz": "💎 <b>Premium (Pro)</b>",
        "ru": "💎 <b>Премиум (Pro)</b>",
        "en": "💎 <b>Premium (Pro)</b>",
    },
    "pres_quality_standard": {
        "uz": "✨ <b>Standart</b>",
        "ru": "✨ <b>Стандарт</b>",
        "en": "✨ <b>Standard</b>",
    },
    "pres_quality_desc_premium": {
        "uz": "Chuqur ilmiy tahlil, manbalar [1][2], 1500+ so'z",
        "ru": "Глубокий научный анализ, источники [1][2], 1500+ слов",
        "en": "Deep scientific analysis, sources [1][2], 1500+ words",
    },
    "pres_quality_desc_standard": {
        "uz": "Sifatli akademik taqdimot, 1200+ so'z",
        "ru": "Качественная академическая презентация, 1200+ слов",
        "en": "Quality academic presentation, 1200+ words",
    },
    "pres_continue": {
        "uz": "✅ Davom etish",
        "ru": "✅ Продолжить",
        "en": "✅ Continue",
    },
    "pres_cancel_btn": {
        "uz": "❌ Bekor qilish",
        "ru": "❌ Отменить",
        "en": "❌ Cancel",
    },
    "pres_topup_btn": {
        "uz": "💳 Balans to'ldirish",
        "ru": "💳 Пополнить баланс",
        "en": "💳 Top Up Balance",
    },
    "pres_balance_ok": {
        "uz": "✅ <b>Balansingiz yetarli!</b>",
        "ru": "✅ <b>Баланс достаточен!</b>",
        "en": "✅ <b>Balance sufficient!</b>",
    },
    "pres_balance_low": {
        "uz": "⚠️ <b>Balansingiz yetarli emas!</b>\n🔴 Yetishmayapti: <b>{needed}</b>",
        "ru": "⚠️ <b>Недостаточно средств!</b>\n🔴 Не хватает: <b>{needed}</b>",
        "en": "⚠️ <b>Insufficient balance!</b>\n🔴 Need more: <b>{needed}</b>",
    },
    "pres_price_info": {
        "uz": "💰 <b>Narx:</b> {low} — {high}\n   <i>(slaydlar soniga qarab)</i>\n👛 <b>Sizning balansingiz:</b> {balance}",
        "ru": "💰 <b>Цена:</b> {low} — {high}\n   <i>(зависит от кол-ва слайдов)</i>\n👛 <b>Ваш баланс:</b> {balance}",
        "en": "💰 <b>Price:</b> {low} — {high}\n   <i>(depends on slide count)</i>\n👛 <b>Your balance:</b> {balance}",
    },
    "pres_choose_lang": {
        "uz": "📊 <b>Taqdimot yaratish ({quality})</b>\n\n1️⃣ <b>Tilni tanlang:</b>",
        "ru": "📊 <b>Создание презентации ({quality})</b>\n\n1️⃣ <b>Выберите язык:</b>",
        "en": "📊 <b>Create presentation ({quality})</b>\n\n1️⃣ <b>Choose language:</b>",
    },
    "pres_enter_topic": {
        "uz": "2️⃣ <b>Taqdimot mavzusini kiriting:</b>\n<i>(Masalan: O'zbekiston tarixi yoki Marketing)</i>",
        "ru": "2️⃣ <b>Введите тему презентации:</b>\n<i>(Например: История Узбекистана или Маркетинг)</i>",
        "en": "2️⃣ <b>Enter presentation topic:</b>\n<i>(Example: History of Uzbekistan or Marketing)</i>",
    },
    "pres_topic_empty": {
        "uz": "❗ Mavzu bo'sh bo'lishi mumkin emas.",
        "ru": "❗ Тема не может быть пустой.",
        "en": "❗ Topic cannot be empty.",
    },
    "pres_summary": {
        "uz": (
            "┌─ 📊 <b>TAQDIMOT</b> │ {quality} ─┐\n\n"
            "  📝  <b>Mavzu:</b> {topic}\n"
            "  🌐  <b>Til:</b> {pres_lang}\n"
            "  👤  <b>Muallif:</b> {author}\n"
            "  🎞  <b>Slaydlar:</b> {slides} ta\n"
            "  🎨  <b>Dizayn:</b> {style}\n"
            "  📂  <b>Bo'limlar:</b> {chapters}\n"
            "  📷  <b>Rasmlar:</b> {user_photos}\n\n"
            "└──────────────────────┘\n\n"
            "👇 <i>Tayyor bo'lsa «Yaratish» tugmasini bosing</i>"
        ),
        "ru": (
            "┌─ 📊 <b>ПРЕЗЕНТАЦИЯ</b> │ {quality} ─┐\n\n"
            "  📝  <b>Тема:</b> {topic}\n"
            "  🌐  <b>Язык:</b> {pres_lang}\n"
            "  👤  <b>Автор:</b> {author}\n"
            "  🎞  <b>Слайды:</b> {slides}\n"
            "  🎨  <b>Дизайн:</b> {style}\n"
            "  📂  <b>Разделы:</b> {chapters}\n"
            "  📷  <b>Фото:</b> {user_photos}\n\n"
            "└──────────────────────┘\n\n"
            "👇 <i>Когда готово, нажмите «Создать»</i>"
        ),
        "en": (
            "┌─ 📊 <b>PRESENTATION</b> │ {quality} ─┐\n\n"
            "  📝  <b>Topic:</b> {topic}\n"
            "  🌐  <b>Language:</b> {pres_lang}\n"
            "  👤  <b>Author:</b> {author}\n"
            "  🎞  <b>Slides:</b> {slides}\n"
            "  🎨  <b>Design:</b> {style}\n"
            "  📂  <b>Sections:</b> {chapters}\n"
            "  📷  <b>Photos:</b> {user_photos}\n\n"
            "└──────────────────────┘\n\n"
            "👇 <i>When ready, press «Create»</i>"
        ),
    },
    "pres_generating": {
        "uz": (
            "⚙️ <b>AI YARATMOQDA</b>\n"
            "━━━━━━━━━━━━━━━━━━━\n\n"
            "  📝  {topic}\n"
            "  🎞  {slides} ta slayd  ·  {quality}\n"
            "  👤  {author}{ai_img}\n"
            "  💰  {price}\n\n"
            "━━━━━━━━━━━━━━━━━━━\n"
            "⏳ <i>4-5 daqiqa kutish — sifat uchun!</i>"
        ),
        "ru": (
            "⚙️ <b>AI СОЗДАЁТ</b>\n"
            "━━━━━━━━━━━━━━━━━━━\n\n"
            "  📝  {topic}\n"
            "  🎞  {slides} слайдов  ·  {quality}\n"
            "  👤  {author}{ai_img}\n"
            "  💰  {price}\n\n"
            "━━━━━━━━━━━━━━━━━━━\n"
            "⏳ <i>Подождите 4-5 минут — ради качества!</i>"
        ),
        "en": (
            "⚙️ <b>AI CREATING</b>\n"
            "━━━━━━━━━━━━━━━━━━━\n\n"
            "  📝  {topic}\n"
            "  🎞  {slides} slides  ·  {quality}\n"
            "  👤  {author}{ai_img}\n"
            "  💰  {price}\n\n"
            "━━━━━━━━━━━━━━━━━━━\n"
            "⏳ <i>Please wait 4-5 minutes — for quality!</i>"
        ),
    },
    "pres_progress": {
        "uz": "🤖 <b>AI slayd yozmoqda...</b>\n\n<code>{bar}</code>  <b>{pct}%</b>\n📊 Slayd: <b>{done}</b> / {total}{next}\n\n📝 <b>Mavzu:</b> {topic}\n<i>⏱ Sifatli natija uchun 2-4 daqiqa kutish tavsiya etiladi</i>",
        "ru": "🤖 <b>AI пишет слайды...</b>\n\n<code>{bar}</code>  <b>{pct}%</b>\n📊 Слайд: <b>{done}</b> / {total}{next}\n\n📝 <b>Тема:</b> {topic}\n<i>⏱ Подождите 2-4 минуты для качественного результата</i>",
        "en": "🤖 <b>AI writing slides...</b>\n\n<code>{bar}</code>  <b>{pct}%</b>\n📊 Slide: <b>{done}</b> / {total}{next}\n\n📝 <b>Topic:</b> {topic}\n<i>⏱ Please wait 2-4 minutes for quality results</i>",
    },
    "pres_not_enough": {
        "uz": "⚠️ <b>Mablag' yetarli emas!</b>\nNarxi: {price}\nSizda: {balance}",
        "ru": "⚠️ <b>Недостаточно средств!</b>\nЦена: {price}\nУ вас: {balance}",
        "en": "⚠️ <b>Insufficient funds!</b>\nPrice: {price}\nYou have: {balance}",
    },
    "pres_done": {
        "uz": (
            "╔═══════════════════════╗\n"
            "   ✅ <b>TAYYOR!</b>\n"
            "╚═══════════════════════╝\n\n"
            "  📝  {topic}\n"
            "  🎞  {slides} ta  ·  {quality}\n"
            "  👤  {author}\n\n"
            "  {status}\n\n"
            "📥 <i>Faylni yuklab oling</i>"
        ),
        "ru": (
            "╔═══════════════════════╗\n"
            "   ✅ <b>ГОТОВО!</b>\n"
            "╚═══════════════════════╝\n\n"
            "  📝  {topic}\n"
            "  🎞  {slides}  ·  {quality}\n"
            "  👤  {author}\n\n"
            "  {status}\n\n"
            "📥 <i>Скачайте файл</i>"
        ),
        "en": (
            "╔═══════════════════════╗\n"
            "   ✅ <b>DONE!</b>\n"
            "╚═══════════════════════╝\n\n"
            "  📝  {topic}\n"
            "  🎞  {slides}  ·  {quality}\n"
            "  👤  {author}\n\n"
            "  {status}\n\n"
            "📥 <i>Download the file</i>"
        ),
    },
    "pres_admin_free": {
        "uz": "🛡️ <b>Admin uchun tekin</b>",
        "ru": "🛡️ <b>Бесплатно для админа</b>",
        "en": "🛡️ <b>Free for admin</b>",
    },
    "pres_deducted": {
        "uz": "💰 <b>Hisobdan yechildi:</b> {price}",
        "ru": "💰 <b>Списано:</b> {price}",
        "en": "💰 <b>Deducted:</b> {price}",
    },
    "pres_error": {
        "uz": "❌ Xatolik: {error}\n\nIltimos, qaytadan urinib ko'ring.",
        "ru": "❌ Ошибка: {error}\n\nПожалуйста, попробуйте ещё раз.",
        "en": "❌ Error: {error}\n\nPlease try again.",
    },
    "pres_cancel_gen": {
        "uz": "❌ Yaratish to'xtatildi. Hech narsa hisobdan yechilmadi.",
        "ru": "❌ Создание отменено. Ничего не списано.",
        "en": "❌ Generation cancelled. Nothing was charged.",
    },
    "pres_assembling": {
        "uz": "⏳ <b>Taqdimot fayli yig'ilmoqda...</b>",
        "ru": "⏳ <b>Файл презентации собирается...</b>",
        "en": "⏳ <b>Assembling presentation file...</b>",
    },
    "pres_ai_images": {
        "uz": "🎨 <b>AI rasmlar yaratilmoqda ({count} ta)...</b>",
        "ru": "🎨 <b>AI создаёт изображения ({count} шт.)...</b>",
        "en": "🎨 <b>AI generating images ({count})...</b>",
    },
    "pres_analyzing_photos": {
        "uz": "⏳ <b>Rasmlar tahlil qilinmoqda (AI Vision)...</b>",
        "ru": "⏳ <b>Анализ фотографий (AI Vision)...</b>",
        "en": "⏳ <b>Analyzing photos (AI Vision)...</b>",
    },
    "pres_smart_analyzing": {
        "uz": "🧠 <b>AI shablon strukturasini tahlil qilmoqda...</b>",
        "ru": "🧠 <b>AI анализирует структуру шаблона...</b>",
        "en": "🧠 <b>AI analyzing template structure...</b>",
    },
    "pres_filling_template": {
        "uz": "⏳ <b>Shablon to'ldirilmoqda...</b>",
        "ru": "⏳ <b>Заполнение шаблона...</b>",
        "en": "⏳ <b>Filling template...</b>",
    },
    "pres_session_expired": {
        "uz": "⚠️ <b>Sessiya muddati tugagan.</b>\n\nIltimos, asosiy menyudan qayta boshlang.",
        "ru": "⚠️ <b>Сессия истекла.</b>\n\nПожалуйста, начните заново из меню.",
        "en": "⚠️ <b>Session expired.</b>\n\nPlease start again from the menu.",
    },
    "pres_topup_hint": {
        "uz": "💳 Balansni to'ldirish uchun /buy buyrug'ini yuboring yoki pastdagi menyudan foydalaning.",
        "ru": "💳 Для пополнения используйте /buy или кнопку в меню.",
        "en": "💳 To top up, use /buy or the button in the menu.",
    },
    "pres_plan_saved": {
        "uz": "✅ <b>{n}-bo'lim saqlandi:</b> {title}\n\n📌 <b>{next}-bo'lim nomini yozing:</b>\n<i>({n}/{total} kiritildi)</i>",
        "ru": "✅ <b>Раздел {n} сохранён:</b> {title}\n\n📌 <b>Введите название раздела {next}:</b>\n<i>({n}/{total} введено)</i>",
        "en": "✅ <b>Section {n} saved:</b> {title}\n\n📌 <b>Enter section {next} title:</b>\n<i>({n}/{total} entered)</i>",
    },
    "pres_plan_done": {
        "uz": "✅ <b>Reja tayyor!</b>",
        "ru": "✅ <b>План готов!</b>",
        "en": "✅ <b>Plan ready!</b>",
    },
    "pres_plan_cancelled": {
        "uz": "❌ Reja kiritish bekor qilindi.",
        "ru": "❌ Ввод плана отменён.",
        "en": "❌ Plan input cancelled.",
    },
    "pres_ai_img_select": {
        "uz": "🖼 <b>AI rasmlar sonini tanlang</b>\n\nHozirgi: <b>{current} ta</b>\n💰 Har bir rasm: <b>1 000 so'm</b>\n\n<i>Rasmlar faqat kontent slaydlariga qo'yiladi\n(Reja va Xulosa slaydlariga qo'yilmaydi)</i>",
        "ru": "🖼 <b>Выберите кол-во AI изображений</b>\n\nСейчас: <b>{current} шт.</b>\n💰 Каждое: <b>1 000 сум</b>\n\n<i>Изображения добавляются только к слайдам контента\n(Не к Плану и Заключению)</i>",
        "en": "🖼 <b>Choose AI image count</b>\n\nCurrent: <b>{current}</b>\n💰 Each image: <b>1,000 UZS</b>\n\n<i>Images are added to content slides only\n(Not to Plan or Conclusion)</i>",
    },
    "pres_photo_upload": {
        "uz": "📷 <b>Rasmlaringizni yuboring</b>\n\nHozir saqlangan: {count} ta rasm\n\nRasm yuboring — bot ularni slaydlarga joylashtiradi.\n<i>Tugagach ✅ Tayyor tugmasini bosing.</i>",
        "ru": "📷 <b>Отправьте ваши фото</b>\n\nСохранено: {count} шт.\n\nОтправьте фото — бот разместит их на слайдах.\n<i>Когда закончите, нажмите ✅ Готово.</i>",
        "en": "📷 <b>Send your photos</b>\n\nSaved: {count} photos\n\nSend photos — bot will place them on slides.\n<i>When done, press ✅ Done.</i>",
    },
    "pres_photo_received": {
        "uz": "✅ Rasm qabul qilindi! Jami: {count} ta\n<i>Yana yuborishingiz yoki ✅ Tayyor bosishingiz mumkin.</i>",
        "ru": "✅ Фото принято! Всего: {count} шт.\n<i>Отправьте ещё или нажмите ✅ Готово.</i>",
        "en": "✅ Photo received! Total: {count}\n<i>Send more or press ✅ Done.</i>",
    },
    "pres_photos_cleared": {
        "uz": "🗑 Barcha rasmlar o'chirildi.",
        "ru": "🗑 Все фото удалены.",
        "en": "🗑 All photos cleared.",
    },
    "pres_photos_saved": {
        "uz": "✅ {count} ta rasm saqlandi! Endi taqdimotni yaratasiz.",
        "ru": "✅ {count} фото сохранено! Теперь создавайте презентацию.",
        "en": "✅ {count} photos saved! Now create your presentation.",
    },
    "pres_photo_hint": {
        "uz": "⚠️ <b>Iltimos, rasmlarni oddiy fayl yoki rasm shaklida yuboring!</b>\n\nAgar AI o'zi rasm chizishini xohlasangiz, hozir shunchaki <b>✅ Tayyor</b> tugmasini bosing va keyingi bosqichda <b>🖼 AI Rasm</b> tugmasini tanlang.",
        "ru": "⚠️ <b>Пожалуйста, отправьте изображения как файл или фото!</b>\n\nЕсли хотите AI изображения, нажмите <b>✅ Готово</b> и выберите <b>🖼 AI Изображения</b> на следующем шаге.",
        "en": "⚠️ <b>Please send images as file or photo!</b>\n\nIf you want AI images, press <b>✅ Done</b> and choose <b>🖼 AI Images</b> on the next step.",
    },
    "pres_use_buttons": {
        "uz": "⚠️ <b>Iltimos, quyidagi tugmalardan birini tanlang!</b>\n\nTaqdimotni yaratish uchun <b>✅ Yaratish</b> tugmasini bosing.",
        "ru": "⚠️ <b>Пожалуйста, выберите одну из кнопок!</b>\n\nДля создания презентации нажмите <b>✅ Создать</b>.",
        "en": "⚠️ <b>Please choose one of the buttons!</b>\n\nTo create presentation press <b>✅ Create</b>.",
    },
    "main_menu_btn": {
        "uz": "🏠 Asosiy menyu",
        "ru": "🏠 Главное меню",
        "en": "🏠 Main Menu",
    },
    "none_label": {
        "uz": "Yo'q",
        "ru": "Нет",
        "en": "None",
    },
    "photos_label": {
        "uz": "{count} ta rasm",
        "ru": "{count} фото",
        "en": "{count} photos",
    },

    # ─── Template Fill ────────────────────────────────────────────────────
    "tfill_intro": {
        "uz": "📎 <b>Shablon to'ldirish rejimi</b>\n\nBu rejimda siz tayyor PPTX shablonni tanlaysiz va AI uni materialingiz asosida to'ldiradi. Dizayn saqlanib qoladi!\n\n💰 <b>Narx:</b> {price}\n👛 <b>Balansingiz:</b> {balance}\n✅ <b>Balansingiz yetarli!</b>",
        "ru": "📎 <b>Режим заполнения шаблона</b>\n\nВ этом режиме вы выбираете готовый PPTX шаблон, а AI заполняет его по вашему материалу. Дизайн сохраняется!\n\n💰 <b>Цена:</b> {price}\n👛 <b>Ваш баланс:</b> {balance}\n✅ <b>Баланс достаточен!</b>",
        "en": "📎 <b>Template fill mode</b>\n\nIn this mode you choose a PPTX template and AI fills it with your content. Design is preserved!\n\n💰 <b>Price:</b> {price}\n👛 <b>Your balance:</b> {balance}\n✅ <b>Balance sufficient!</b>",
    },
    "tfill_send_material": {
        "uz": "2️⃣ <b>Material yuboring:</b>\n\nQuyidagilardan BIRINI yuboring:\n• 📝 <b>Mavzu yozing</b> — AI o'zi ma'lumot topadi\n• 📄 <b>Fayl yuboring</b> (TXT, DOCX, PDF) — AI materialdan foydalanadi\n\nAI materialni o'qiydi, tahlil qiladi va taqdimot uchun moslashtiradi.",
        "ru": "2️⃣ <b>Отправьте материал:</b>\n\nОтправьте ОДНО из:\n• 📝 <b>Напишите тему</b> — AI найдёт информацию сам\n• 📄 <b>Отправьте файл</b> (TXT, DOCX, PDF) — AI использует ваш материал\n\nAI прочитает, проанализирует и адаптирует для презентации.",
        "en": "2️⃣ <b>Send material:</b>\n\nSend ONE of:\n• 📝 <b>Write a topic</b> — AI will find info\n• 📄 <b>Send a file</b> (TXT, DOCX, PDF) — AI will use your material\n\nAI will read, analyze and adapt it for the presentation.",
    },
    "tfill_choose_template": {
        "uz": "3️⃣ <b>Shablonni tanlang</b>\n\nPastdagi tugma orqali katalogdan tayyor shablonni tanlang.\nAI shu shablonni materialingiz bilan to'ldiradi.",
        "ru": "3️⃣ <b>Выберите шаблон</b>\n\nНажмите кнопку ниже и выберите шаблон из каталога.\nAI заполнит его вашим материалом.",
        "en": "3️⃣ <b>Choose template</b>\n\nPress the button below and choose a template.\nAI will fill it with your material.",
    },
    "tfill_file_read": {
        "uz": "⏳ <b>Fayl o'qilmoqda...</b>",
        "ru": "⏳ <b>Чтение файла...</b>",
        "en": "⏳ <b>Reading file...</b>",
    },
    "tfill_file_done": {
        "uz": "✅ <b>Fayl o'qildi!</b>\n\n📄 <b>Fayl:</b> {filename}\n📊 <b>Belgilar:</b> {chars}\n📝 <b>Mavzu:</b> {topic}",
        "ru": "✅ <b>Файл прочитан!</b>\n\n📄 <b>Файл:</b> {filename}\n📊 <b>Символов:</b> {chars}\n📝 <b>Тема:</b> {topic}",
        "en": "✅ <b>File read!</b>\n\n📄 <b>File:</b> {filename}\n📊 <b>Characters:</b> {chars}\n📝 <b>Topic:</b> {topic}",
    },
    "tfill_file_error": {
        "uz": "❌ Faylni yuklashda xatolik: {error}",
        "ru": "❌ Ошибка загрузки файла: {error}",
        "en": "❌ File upload error: {error}",
    },
    "tfill_file_empty": {
        "uz": "⚠️ <b>Fayldan matn ajratib olinmadi yoki juda kam.</b>\n\nIltimos, boshqa fayl yuboring yoki mavzuni matn sifatida yozing.",
        "ru": "⚠️ <b>Текст не извлечён или слишком мало.</b>\n\nОтправьте другой файл или напишите тему текстом.",
        "en": "⚠️ <b>No text extracted or too little.</b>\n\nSend another file or write the topic as text.",
    },
    "tfill_bad_format": {
        "uz": "⚠️ <b>Fayl formati qo'llab-quvvatlanmaydi:</b> {ext}\n\nQo'llab-quvvatlanadigan formatlar: TXT, DOCX, PDF\nIltimos, boshqa formatda yuboring yoki mavzuni matn sifatida yozing.",
        "ru": "⚠️ <b>Формат не поддерживается:</b> {ext}\n\nПоддерживаются: TXT, DOCX, PDF\nОтправьте в другом формате или напишите тему текстом.",
        "en": "⚠️ <b>Unsupported format:</b> {ext}\n\nSupported: TXT, DOCX, PDF\nSend another format or write the topic as text.",
    },
    "tfill_template_error": {
        "uz": "❌ Shablon tanlanmadi. Qaytadan urinib ko'ring.",
        "ru": "❌ Шаблон не выбран. Попробуйте снова.",
        "en": "❌ Template not selected. Try again.",
    },
    "tfill_generating": {
        "uz": "🤖 <b>AI shablon to'ldirmoqda...</b>\n\n📝 <b>Mavzu:</b> {topic}\n🎨 <b>Shablon:</b> {style}\n\n⏳ <i>2-5 daqiqa davom etadi...</i>",
        "ru": "🤖 <b>AI заполняет шаблон...</b>\n\n📝 <b>Тема:</b> {topic}\n🎨 <b>Шаблон:</b> {style}\n\n⏳ <i>Займёт 2-5 минут...</i>",
        "en": "🤖 <b>AI filling template...</b>\n\n📝 <b>Topic:</b> {topic}\n🎨 <b>Template:</b> {style}\n\n⏳ <i>Takes 2-5 minutes...</i>",
    },
    "tfill_template_empty": {
        "uz": "❌ Shablon topilmadi yoki bo'sh.",
        "ru": "❌ Шаблон не найден или пустой.",
        "en": "❌ Template not found or empty.",
    },
    "tfill_from_cache": {
        "uz": "⚡ <b>Keshdan olinmoqda...</b>",
        "ru": "⚡ <b>Загрузка из кеша...</b>",
        "en": "⚡ <b>Loading from cache...</b>",
    },
    "tfill_photos_loading": {
        "uz": "⏳ <b>Rasmlar yuklanmoqda...</b>",
        "ru": "⏳ <b>Загрузка фотографий...</b>",
        "en": "⏳ <b>Loading photos...</b>",
    },
    "tfill_images_search": {
        "uz": "🖼 <b>Rasmlar qidirilmoqda ({count} ta)...</b>",
        "ru": "🖼 <b>Поиск изображений ({count} шт.)...</b>",
        "en": "🖼 <b>Searching images ({count})...</b>",
    },
    "tfill_done": {
        "uz": "✅ <b>Shablon muvaffaqiyatli to'ldirildi!</b>\n\n📝 <b>Mavzu:</b> {topic}\n📊 <b>Slaydlar:</b> {slides} ta\n🎨 <b>Shablon:</b> {style}\n👤 <b>Muallif:</b> {author}\n────────────────────\n{status}\n\n📥 <i>Faylni yuklab olishingiz mumkin.</i>",
        "ru": "✅ <b>Шаблон успешно заполнен!</b>\n\n📝 <b>Тема:</b> {topic}\n📊 <b>Слайдов:</b> {slides}\n🎨 <b>Шаблон:</b> {style}\n👤 <b>Автор:</b> {author}\n────────────────────\n{status}\n\n📥 <i>Вы можете скачать файл.</i>",
        "en": "✅ <b>Template filled successfully!</b>\n\n📝 <b>Topic:</b> {topic}\n📊 <b>Slides:</b> {slides}\n🎨 <b>Template:</b> {style}\n👤 <b>Author:</b> {author}\n────────────────────\n{status}\n\n📥 <i>You can download the file.</i>",
    },
    # ─── Documents (Referat / Mustaqil ish) ─────────────────────────────
    "doc_enter_topic": {
        "uz": "📝 <b>Mavzuni kiriting:</b>\n<i>(Masalan: O'zbekiston iqtisodiyoti rivoji)</i>",
        "ru": "📝 <b>Введите тему:</b>\n<i>(Например: Развитие экономики Узбекистана)</i>",
        "en": "📝 <b>Enter topic:</b>\n<i>(Example: Economic development of Uzbekistan)</i>",
    },
    "doc_enter_subject": {
        "uz": "🎓 <b>Fan nomini kiriting:</b>\n<i>(Masalan: Iqtisodiyot nazariyasi)</i>",
        "ru": "🎓 <b>Введите название предмета:</b>\n<i>(Например: Экономическая теория)</i>",
        "en": "🎓 <b>Enter subject name:</b>\n<i>(Example: Economic Theory)</i>",
    },
    "doc_choose_quality": {
        "uz": "💎 <b>Xizmat sifatini tanlang:</b>\n<i>(Pro versiya 2 barobar sifatli va qimmatroq)</i>",
        "ru": "💎 <b>Выберите качество:</b>\n<i>(Pro версия в 2 раза качественнее и дороже)</i>",
        "en": "💎 <b>Choose quality:</b>\n<i>(Pro version is 2x better quality and more expensive)</i>",
    },
    "doc_preparing_plan": {
        "uz": "⏳ <b>AI eng yaxshi rejani tayyorlamoqda...</b>",
        "ru": "⏳ <b>AI готовит лучший план...</b>",
        "en": "⏳ <b>AI is preparing the best plan...</b>",
    },
    "doc_send_file": {
        "uz": "📎 <b>Faylingizni yuboring</b>\n\nQo'llab-quvvatlanadigan formatlar:\n• <b>.txt</b> — oddiy matn\n• <b>.docx</b> — Word hujjati\n• <b>.pdf</b> — PDF hujjati\n\n<i>AI faylni o'qib, unda yozilgan topshiriqni bajaradi va mustaqil ish sifatida formatlaydi.</i>",
        "ru": "📎 <b>Отправьте файл</b>\n\nПоддерживаемые форматы:\n• <b>.txt</b> — текстовый файл\n• <b>.docx</b> — документ Word\n• <b>.pdf</b> — документ PDF\n\n<i>AI прочитает файл, выполнит задание и оформит как самостоятельную работу.</i>",
        "en": "📎 <b>Send your file</b>\n\nSupported formats:\n• <b>.txt</b> — text file\n• <b>.docx</b> — Word document\n• <b>.pdf</b> — PDF document\n\n<i>AI will read the file, complete the task and format it as independent work.</i>",
    },
    "doc_file_empty": {
        "uz": "❌ Fayl bo'sh yoki o'qib bo'lmadi.",
        "ru": "❌ Файл пуст или не читается.",
        "en": "❌ File is empty or unreadable.",
    },
    "doc_generating": {
        "uz": (
            "⚙️ <b>AI YARATMOQDA</b>\n"
            "━━━━━━━━━━━━━━━━━━━\n\n"
            "  �  {topic}\n"
            "  �  {pages} bet\n\n"
            "━━━━━━━━━━━━━━━━━━━\n"
            "⏳ <i>4-5 daqiqa kutib turing — sifatli natija uchun!</i>"
        ),
        "ru": (
            "⚙️ <b>AI СОЗДАЁТ</b>\n"
            "━━━━━━━━━━━━━━━━━━━\n\n"
            "  �  {topic}\n"
            "  �  {pages} стр.\n\n"
            "━━━━━━━━━━━━━━━━━━━\n"
            "⏳ <i>Подождите 4-5 минут — ради качества!</i>"
        ),
        "en": (
            "⚙️ <b>AI CREATING</b>\n"
            "━━━━━━━━━━━━━━━━━━━\n\n"
            "  �  {topic}\n"
            "  �  {pages} pages\n\n"
            "━━━━━━━━━━━━━━━━━━━\n"
            "⏳ <i>Please wait 4-5 minutes — for quality!</i>"
        ),
    },
    "doc_done": {
        "uz": (
            "╔═══════════════════════╗\n"
            "   ✅ <b>TAYYOR!</b>\n"
            "╚═══════════════════════╝\n\n"
            "  �  {topic}\n"
            "  �  {pages} bet  ·  💰 {price}\n\n"
            "📥 <i>Faylni yuklab oling</i>"
        ),
        "ru": (
            "╔═══════════════════════╗\n"
            "   ✅ <b>ГОТОВО!</b>\n"
            "╚═══════════════════════╝\n\n"
            "  �  {topic}\n"
            "  �  {pages} стр.  ·  💰 {price}\n\n"
            "📥 <i>Скачайте файл</i>"
        ),
        "en": (
            "╔═══════════════════════╗\n"
            "   ✅ <b>DONE!</b>\n"
            "╚═══════════════════════╝\n\n"
            "  �  {topic}\n"
            "  �  {pages} pages  ·  💰 {price}\n\n"
            "� <i>Download the file</i>"
        ),
    },
    "doc_cancel_gen": {
        "uz": "❌ Hujjat yaratish to'xtatildi. Hech narsa hisobdan yechilmadi.",
        "ru": "❌ Создание отменено. Ничего не списано.",
        "en": "❌ Document creation cancelled. Nothing was charged.",
    },
    "doc_analyzing": {
        "uz": "🧠 <b>AI faylni tahlil qilmoqda...</b>\n📋 Bo'limlar ro'yxati aniqlanmoqda...",
        "ru": "🧠 <b>AI анализирует файл...</b>\n📋 Определяются разделы...",
        "en": "🧠 <b>AI analyzing file...</b>\n📋 Identifying sections...",
    },
    "doc_sections_found": {
        "uz": "🧠 <b>AI tahlil qildi!</b>\n\n📋 <b>{count} ta bo'lim aniqlandi</b>",
        "ru": "🧠 <b>AI проанализировал!</b>\n\n📋 <b>Найдено {count} разделов</b>",
        "en": "🧠 <b>AI analyzed!</b>\n\n📋 <b>{count} sections found</b>",
    },
    "doc_creating_docx": {
        "uz": "⏳ <b>DOCX fayl yaratilmoqda...</b>",
        "ru": "⏳ <b>Создание файла DOCX...</b>",
        "en": "⏳ <b>Creating DOCX file...</b>",
    },
    "doc_file_done": {
        "uz": "✅ <b>Mustaqil ish tayyor!</b>\n📎 Fayl asosida yaratildi ({count} bo'lim)\n🌐 Til: {lang}\n💰 {status}",
        "ru": "✅ <b>Самостоятельная работа готова!</b>\n📎 Создано на основе файла ({count} разделов)\n🌐 Язык: {lang}\n💰 {status}",
        "en": "✅ <b>Independent work ready!</b>\n📎 Created from file ({count} sections)\n🌐 Language: {lang}\n💰 {status}",
    },
    "doc_choose_lang": {
        "uz": "Hujjat tilini tanlang:",
        "ru": "Выберите язык документа:",
        "en": "Choose document language:",
    },

    # ─── Coursework ──────────────────────────────────────────────────────
    "cw_enter_topic": {
        "uz": "📘 <b>Yangi kurs ishi yaratamiz!</b>\n\nBoshlash uchun <b>mavzuni</b> yuboring.\n<i>(Masalan: Raqamli iqtisodiyotda blokcheyn texnologiyalari)</i>",
        "ru": "📘 <b>Создаём курсовую работу!</b>\n\nОтправьте <b>тему</b>.\n<i>(Например: Блокчейн-технологии в цифровой экономике)</i>",
        "en": "📘 <b>Creating coursework!</b>\n\nSend the <b>topic</b>.\n<i>(Example: Blockchain technologies in digital economy)</i>",
    },
    "cw_generating": {
        "uz": "⏳ <b>Kurs ishi tayyorlanmoqda...</b>\n\n🤖 AI mavzuni chuqur tahlil qilmoqda.\n⏳ <i>4-5 daqiqa kutib turing — sifatli natija uchun!</i>",
        "ru": "⏳ <b>Курсовая готовится...</b>\n\n🤖 AI глубоко анализирует тему.\n⏳ <i>Подождите 4-5 минут — ради качества!</i>",
        "en": "⏳ <b>Creating coursework...</b>\n\n🤖 AI deeply analyzing the topic.\n⏳ <i>Please wait 4-5 minutes — for quality!</i>",
    },
    "cw_done": {
        "uz": "✅ <b>Kurs ishi tayyor!</b>\n\n📌 Mavzu: {topic}\n📑 Hajmi: {pages} bet\n💰 Narxi: {price}",
        "ru": "✅ <b>Курсовая готова!</b>\n\n📌 Тема: {topic}\n📑 Объём: {pages} стр.\n💰 Цена: {price}",
        "en": "✅ <b>Coursework ready!</b>\n\n📌 Topic: {topic}\n📑 Pages: {pages}\n💰 Price: {price}",
    },
    "cw_cancel_gen": {
        "uz": "❌ Kurs ishi yaratish to'xtatildi. Hech narsa hisobdan yechilmadi.",
        "ru": "❌ Создание курсовой отменено. Ничего не списано.",
        "en": "❌ Coursework creation cancelled. Nothing was charged.",
    },
    "cw_preparing_plan": {
        "uz": "⏳ <b>Reja tayyorlanmoqda...</b>\n\nBu bir necha soniya vaqt oladi.",
        "ru": "⏳ <b>Подготовка плана...</b>\n\nЭто займёт несколько секунд.",
        "en": "⏳ <b>Preparing plan...</b>\n\nThis will take a few seconds.",
    },

    # ─── Maqola / Tezis ─────────────────────────────────────────────────
    "pres_engine_select": {
        "uz": (
            "🔧 <b>Dizayn usulini tanlang:</b>\n\n"
            "🤖 <b>AI + Shablon</b> — Bizning AI kontent yozadi, siz shablon tanlaysiz\n"
            "🌐 <b>Presenton</b> — AI o'zi dizayn qiladi (bepul, lokal)\n"
            "💎 <b>Gamma</b> — Professional AI dizayn (pullik, bulutli)\n\n"
            "📌 Hozirgi: <b>{current}</b>"
        ),
        "ru": (
            "🔧 <b>Выберите способ дизайна:</b>\n\n"
            "🤖 <b>AI + Шаблон</b> — Наш AI пишет контент, вы выбираете шаблон\n"
            "🌐 <b>Presenton</b> — AI сам делает дизайн (бесплатно, локально)\n"
            "💎 <b>Gamma</b> — Профессиональный AI дизайн (платно, облако)\n\n"
            "📌 Сейчас: <b>{current}</b>"
        ),
        "en": (
            "🔧 <b>Choose design engine:</b>\n\n"
            "🤖 <b>AI + Template</b> — Our AI writes content, you pick a template\n"
            "🌐 <b>Presenton</b> — AI creates the design itself (free, local)\n"
            "💎 <b>Gamma</b> — Professional AI design (paid, cloud)\n\n"
            "📌 Current: <b>{current}</b>"
        ),
    },
    "pres_engine_set": {
        "uz": "✅ Dizayn usuli o'zgartirildi: <b>{engine}</b>",
        "ru": "✅ Способ дизайна изменён: <b>{engine}</b>",
        "en": "✅ Design engine changed: <b>{engine}</b>",
    },
    "pres_generating_ext": {
        "uz": "🌐 <b>{engine} taqdimot yaratmoqda...</b>\n\n📝 <b>Mavzu:</b> {topic}\n🎞️ <b>Slaydlar:</b> {slides} ta\n\n⏳ <i>4-5 daqiqa kutib turing — sifatli natija uchun!</i>",
        "ru": "🌐 <b>{engine} создаёт презентацию...</b>\n\n📝 <b>Тема:</b> {topic}\n🎞️ <b>Слайдов:</b> {slides}\n\n⏳ <i>Подождите 4-5 минут — ради качества!</i>",
        "en": "🌐 <b>{engine} is creating presentation...</b>\n\n📝 <b>Topic:</b> {topic}\n🎞️ <b>Slides:</b> {slides}\n\n⏳ <i>Please wait 4-5 minutes — for quality!</i>",
    },
    "pres_ext_done": {
        "uz": "✅ <b>Taqdimot tayyor!</b> ({engine})\n\n📝 <b>Mavzu:</b> {topic}\n📊 <b>Slaydlar:</b> {slides} ta\n────────────────────\n{status}",
        "ru": "✅ <b>Презентация готова!</b> ({engine})\n\n📝 <b>Тема:</b> {topic}\n📊 <b>Слайдов:</b> {slides}\n────────────────────\n{status}",
        "en": "✅ <b>Presentation ready!</b> ({engine})\n\n📝 <b>Topic:</b> {topic}\n📊 <b>Slides:</b> {slides}\n────────────────────\n{status}",
    },
    "pres_ext_failed": {
        "uz": "❌ <b>{engine} xatolik berdi.</b>\n\n<i>Iltimos, boshqa usulni tanlang yoki qayta urinib ko'ring.</i>",
        "ru": "❌ <b>{engine} вернул ошибку.</b>\n\n<i>Выберите другой способ или попробуйте снова.</i>",
        "en": "❌ <b>{engine} returned an error.</b>\n\n<i>Please choose another engine or try again.</i>",
    },
    "maq_fill_settings": {
        "uz": "❗ Iltimos, oldin <b>⚙️ Sozlamalarni ochish</b> tugmasini bosib, mavzu va ismingizni kiriting.",
        "ru": "❗ Сначала нажмите <b>⚙️ Открыть настройки</b> и заполните тему и имя.",
        "en": "❗ Please press <b>⚙️ Open settings</b> first and enter topic and name.",
    },
    "maq_cancel_gen": {
        "uz": "❌ Maqola yaratish to'xtatildi. Hech narsa hisobdan yechilmadi.",
        "ru": "❌ Создание статьи отменено. Ничего не списано.",
        "en": "❌ Article creation cancelled. Nothing was charged.",
    },
    "tez_cancel_gen": {
        "uz": "❌ Tezis yaratish to'xtatildi. Hech narsa hisobdan yechilmadi.",
        "ru": "❌ Создание тезиса отменено. Ничего не списано.",
        "en": "❌ Thesis creation cancelled. Nothing was charged.",
    },

    # ─── Payment ─────────────────────────────────────────────────────────
    "pay_chek_amount": {
        "uz": "⚠️ Iltimos, faqat <b>raqam</b> yuboring. Masalan: <code>5000</code>",
        "ru": "⚠️ Введите только <b>число</b>. Например: <code>5000</code>",
        "en": "⚠️ Please send only a <b>number</b>. Example: <code>5000</code>",
    },
    "pay_chek_accepted": {
        "uz": "✅ Summa qabul qilindi: <b>{amount} so'm</b>\n\n📸 <b>Endi chek rasmini yuboring:</b>",
        "ru": "✅ Сумма принята: <b>{amount} сум</b>\n\n📸 <b>Теперь отправьте фото чека:</b>",
        "en": "✅ Amount accepted: <b>{amount} UZS</b>\n\n📸 <b>Now send the receipt photo:</b>",
    },
    "pay_screenshot_sent": {
        "uz": "✅ <b>Chek muvaffaqiyatli yuborildi!</b>\n\n⏳ Admin tekshirib, tez orada tasdiqlaydi.",
        "ru": "✅ <b>Чек успешно отправлен!</b>\n\n⏳ Администратор проверит и подтвердит.",
        "en": "✅ <b>Receipt sent successfully!</b>\n\n⏳ Admin will review and confirm shortly.",
    },
    "pay_success": {
        "uz": "🎉 <b>Muvaffaqiyatli to'lov!</b>\n\n💰 Balansingizga <b>{amount}</b> qo'shildi.\n🚀 Endi xizmatlardan foydalanishingiz mumkin!",
        "ru": "🎉 <b>Оплата успешна!</b>\n\n💰 На баланс зачислено <b>{amount}</b>.\n🚀 Теперь можете пользоваться сервисами!",
        "en": "🎉 <b>Payment successful!</b>\n\n💰 <b>{amount}</b> added to your balance.\n🚀 You can now use the services!",
    },

    "tfill_summary": {
        "uz": "📎 <b>Shablon to'ldirish — Xulosa</b>\n\n📝 <b>Mavzu:</b> {topic}\n🗺️ <b>Til:</b> {pres_lang}\n🎨 <b>Shablon:</b> {style}\n📷 <b>Rasmlar:</b> {photos}\n💰 <b>Narx:</b> {price}\n\n<i>Tayyor bo'lsa \"✅ Yaratish\" tugmasini bosing.</i>",
        "ru": "📎 <b>Заполнение шаблона — Итог</b>\n\n📝 <b>Тема:</b> {topic}\n🗺️ <b>Язык:</b> {pres_lang}\n🎨 <b>Шаблон:</b> {style}\n📷 <b>Фото:</b> {photos}\n💰 <b>Цена:</b> {price}\n\n<i>Когда готовы, нажмите \"✅ Создать\".</i>",
        "en": "📎 <b>Template Fill — Summary</b>\n\n📝 <b>Topic:</b> {topic}\n🗺️ <b>Language:</b> {pres_lang}\n🎨 <b>Template:</b> {style}\n📷 <b>Photos:</b> {photos}\n💰 <b>Price:</b> {price}\n\n<i>When ready, press \"✅ Create\".</i>",
    },

    # ─── Cancel / Stop ───────────────────────────────────────────────────
    "cancelled": {
        "uz": "❌ Amaliyot bekor qilindi.",
        "ru": "❌ Операция отменена.",
        "en": "❌ Operation cancelled.",
    },
    "stopped": {
        "uz": "🛑 <b>Jarayon to'xtatildi.</b>\n\nAsosiy menyuga qaytdik.",
        "ru": "🛑 <b>Процесс остановлен.</b>\n\nВозврат в главное меню.",
        "en": "🛑 <b>Process stopped.</b>\n\nReturning to main menu.",
    },

    # ─── Help ────────────────────────────────────────────────────────────
    "help": {
        "uz": "ℹ️ <b>Yordam markazi</b>\n\n<b>Qanday ishlaydi?</b>\n1. Xizmatni tanlang\n2. Mavzu kiriting\n3. Fayl tayyor bo'ladi\n\n💰 <b>To'lov:</b> /buy\n🆘 <b>Admin:</b> {admin}",
        "ru": "ℹ️ <b>Центр помощи</b>\n\n<b>Как это работает?</b>\n1. Выберите услугу\n2. Введите тему\n3. Файл будет готов\n\n💰 <b>Оплата:</b> /buy\n🆘 <b>Админ:</b> {admin}",
        "en": "ℹ️ <b>Help Center</b>\n\n<b>How it works?</b>\n1. Choose a service\n2. Enter a topic\n3. File will be ready\n\n💰 <b>Payment:</b> /buy\n🆘 <b>Admin:</b> {admin}",
    },
}

# ─── Button labels per language ──────────────────────────────────────────────
BUTTONS = {
    "presentation": {"uz": "🆕 Taqdimot (Slayd) yaratish", "ru": "🆕 Презентация (Слайд)", "en": "🆕 Create Presentation"},
    "presentation_pro": {"uz": "🚀 Slayd Pro (Premium)", "ru": "🚀 Слайд Про (Премиум)", "en": "🚀 Slide Pro (Premium)"},
    "mustaqil": {"uz": "📄 Mustaqil ish yaratish", "ru": "📄 Самост. работа", "en": "📄 Independent Work"},
    "referat": {"uz": "📚 Referat yaratish", "ru": "📚 Реферат", "en": "📚 Essay"},
    "kurs": {"uz": "📘 Kurs ishi yaratish", "ru": "📘 Курсовая работа", "en": "📘 Coursework"},
    "tezis": {"uz": "🎓 Tezis yaratish", "ru": "🎓 Тезис", "en": "🎓 Thesis"},
    "maqola": {"uz": "📝 Maqola yaratish", "ru": "📝 Статья", "en": "📝 Article"},
    "uslubiy": {"uz": "📗 Uslubiy ishlanma", "ru": "📗 Метод. пособие", "en": "📗 Methodical Guide"},
    "topup": {"uz": "💳 Hisobni to'ldirish", "ru": "💳 Пополнить баланс", "en": "💳 Top Up Balance"},
    "receipt": {"uz": "📸 Chekni yuborish", "ru": "📸 Отправить чек", "en": "📸 Send Receipt"},
    "referral": {"uz": "👥 Do'stni taklif qilish", "ru": "👥 Пригласить друга", "en": "👥 Invite Friend"},
    "account": {"uz": "📊 Mening hisobim", "ru": "📊 Мой аккаунт", "en": "📊 My Account"},
    "back": {"uz": "🏠 Bosh menyu", "ru": "🏠 Главное меню", "en": "🏠 Main Menu"},
    "pres_engine": {"uz": "🔧 Dizayn usuli", "ru": "🔧 Способ дизайна", "en": "🔧 Design Engine"},
    "pres_settings": {"uz": "⚙️ Sozlamalar", "ru": "⚙️ Настройки", "en": "⚙️ Settings"},
    "pres_design": {"uz": "🎨 Dizayn Tanlash", "ru": "🎨 Выбрать дизайн", "en": "🎨 Choose Design"},
    "pres_plan": {"uz": "📝 Reja qo'shish", "ru": "📝 Добавить план", "en": "📝 Add Plan"},
    "pres_content": {"uz": "🧩 Kontent", "ru": "🧩 Контент", "en": "🧩 Content"},
    "pres_photo": {"uz": "📷 Rasm yuklash", "ru": "📷 Загрузить фото", "en": "📷 Upload Photo"},
    "pres_ai_img": {"uz": "🖼 AI Rasm", "ru": "🖼 AI Изображения", "en": "🖼 AI Images"},
    "pres_create": {"uz": "✅ Yaratish", "ru": "✅ Создать", "en": "✅ Create"},
    "cancel": {"uz": "❌ Bekor qilish", "ru": "❌ Отменить", "en": "❌ Cancel"},
    "quiz": {"uz": "📋 Avtomatik quiz tuzish", "ru": "📋 Автоматический тест", "en": "📋 Auto Quiz Maker"},
    "diplom": {"uz": "🎓 Diplom ishi yaratish", "ru": "🎓 Дипломная работа", "en": "🎓 Diploma Work"},
    "pres_design_catalog": {"uz": "🎨 Dizayn tanlash (Katalog)", "ru": "🎨 Выбрать дизайн (Каталог)", "en": "🎨 Choose Design (Catalog)"},
    "pres_plain_design": {"uz": "Rasmsiz/Oddiy Dizayn", "ru": "Без фото/Простой дизайн", "en": "Plain/Simple Design"},
}


def t(key: str, lang: str = "uz", **kwargs) -> str:
    """Get translated text. Falls back to Uzbek."""
    text_dict = TEXTS.get(key, {})
    text = text_dict.get(lang, text_dict.get("uz", key))
    if kwargs:
        try:
            text = text.format(**kwargs)
        except (KeyError, IndexError):
            pass
    return text


def btn(key: str, lang: str = "uz") -> str:
    """Get translated button label."""
    btn_dict = BUTTONS.get(key, {})
    return btn_dict.get(lang, btn_dict.get("uz", key))
