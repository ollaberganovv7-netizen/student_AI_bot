from __future__ import annotations
import asyncio
import logging
import sys

# Ensure standard output supports UTF-8 to prevent console crash on emojis
if sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

from aiogram import Bot, Dispatcher, F
from aiogram.types import CallbackQuery, Message
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from utils.fsm_sqlite_storage import SQLiteStorage

from config import BOT_TOKEN
from database.db import init_db
from middlewares.register import RegisterMiddleware
from middlewares.throttling import ThrottlingMiddleware, GenerationLockMiddleware

from handlers import start, presentation, documents, payment, admin, coursework, tezis, maqola, uslubiy, template_fill, quiz, reactions
from utils.scanner import update_templates_json

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)


async def main():
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN topilmadi! .env faylini tekshiring.")
        sys.exit(1)

    try:
        # Initialize database
        logger.info("Ma'lumotlar bazasi ishga tushirilmoqda...")
        await init_db()
        logger.info("Ma'lumotlar bazasi tayyor")

        # Update templates catalog
        logger.info("Taqdimot dizaynlari katalogi yangilanmoqda...")
        update_templates_json()
        logger.info("Katalog yangilandi")
    except Exception as e:
        logger.error(f"Xatolik yuz berdi: {e}", exc_info=True)
        sys.exit(1)

    # Create bot & dispatcher
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    fsm_storage = SQLiteStorage(db_path="fsm_storage.db")
    dp = Dispatcher(storage=fsm_storage)

    # Register middleware on all updates
    # Order matters: throttling FIRST (to drop spam early), then register, then lock
    throttle = ThrottlingMiddleware(message_rate=0.5, callback_rate=0.3)
    gen_lock = GenerationLockMiddleware()

    dp.message.middleware(throttle)
    dp.callback_query.middleware(throttle)

    dp.message.middleware(RegisterMiddleware())
    dp.callback_query.middleware(RegisterMiddleware())

    dp.message.middleware(gen_lock)
    dp.callback_query.middleware(gen_lock)

    # Include routers (start.router LAST among service routers so its catch-all
    # F.web_app_data handler doesn't intercept state-filtered handlers)
    dp.include_router(admin.router)       # Admin first (priority)
    dp.include_router(presentation.router)
    dp.include_router(template_fill.router)
    dp.include_router(documents.router)
    dp.include_router(coursework.router)
    dp.include_router(tezis.router)       # Tezis handler
    dp.include_router(maqola.router)      # Maqola handler
    dp.include_router(uslubiy.router)     # Uslubiy ishlanma handler
    dp.include_router(quiz.router)        # Quiz handler
    dp.include_router(reactions.router)    # Channel reactions handler
    dp.include_router(payment.router)
    dp.include_router(start.router)       # Start + webapp submit (catch-all web_app_data)

    # Debug: log unhandled callbacks/messages
    from aiogram import Router as _R
    _debug_router = _R()

    @_debug_router.callback_query()
    async def _debug_unhandled_cb(cb: CallbackQuery):
        logger.warning(f"UNHANDLED callback: data='{cb.data}' from user={cb.from_user.id}")
        await cb.answer()

    @_debug_router.message(F.text.in_(["🚀 Yaratish", "✅ Yaratish"]))
    async def _fallback_yaratish(msg: Message):
        from keyboards.main_kb import main_menu_kb
        await msg.answer(
            "⚠️ <b>Oldingi sessiya tugagan.</b>\n\nIltimos, asosiy menyudan qayta boshlang.",
            reply_markup=main_menu_kb(), parse_mode="HTML"
        )

    @_debug_router.message()
    async def _debug_unhandled_msg(msg: Message):
        logger.warning(f"UNHANDLED message: text='{msg.text}' from user={msg.from_user.id}")

    dp.include_router(_debug_router)  # Last router — catches everything unhandled

    # Set bot commands menu
    from aiogram.types import BotCommand, MenuButtonDefault
    commands = [
        BotCommand(command="start", description="Botni ishga tushirish"),
        BotCommand(command="stop", description="Jarayonni to'xtatish"),
        BotCommand(command="buy", description="Balansni to'ldirish"),
        BotCommand(command="help", description="Yordam va qo'llab-quvvatlash"),
    ]
    await bot.set_my_commands(commands)
    
    # Remove Mini App from the menu button (revert to default)
    await bot.set_chat_menu_button(menu_button=MenuButtonDefault())

    # Start polling
    try:
        logger.info("Bot ishga tushdi")
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    except KeyboardInterrupt:
        logger.info("Bot to'xtatildi (Ctrl+C)")
    finally:
        await bot.session.close()
        logger.info("Bot sessiyasi yopildi")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Dastur to'xtatildi")
        sys.exit(0)
