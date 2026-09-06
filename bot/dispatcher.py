from aiogram import Bot, Dispatcher
from config import Config
from bot.services.database import DatabaseService
from bot.services.profile import ProfileService
from bot.services.view import ViewService
from bot.handlers.command import CommandHandler
from bot.handlers.message import MessageHandler
from bot.handlers.callback import CallbackHandler
from bot.services.keyboard import KeyboardFactory

def setup_dispatcher() -> tuple[Bot, Dispatcher]:
    bot = Bot(token=Config.TELEGRAM_TOKEN)
    dp = Dispatcher()

    db = DatabaseService()
    profile = ProfileService(db)
    view = ViewService(db)

    command_handler = CommandHandler(db, profile, view, bot)
    message_handler = MessageHandler(db, profile, view)
    callback_handler = CallbackHandler(db, profile, view, bot)

    @dp.message()
    async def main_message_handler(message):
        # Перенаправляем в соответствующий обработчик
        if message.text and message.text.startswith("/"):
            await command_handler.handle(message)
        else:
            await message_handler.handle(message)

    @dp.callback_query()
    async def main_callback_handler(callback):
        await callback_handler.handle(callback)

    return bot, dp