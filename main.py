import asyncio
from aiogram import Bot, Dispatcher

from bot.bot import router
from bot.form import form_router

from bot.payment import payment_router
from bot.view.commands import set_main_menu
import config.config as config

from db.db import init_db

from jobs.caller import send_voice_alert

bot = Bot(token=config.BOT_TOKEN)
dp = Dispatcher()


async def main():
    print("Запуск...")
    await init_db()

    await set_main_menu(bot)
    dp.include_router(router)
    dp.include_router(form_router)
    dp.include_router(payment_router)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
