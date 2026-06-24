import asyncio
from aiogram import Bot, Dispatcher
import os
from dotenv import load_dotenv, find_dotenv

from bot.bot import router
from bot.commands import set_main_menu

load_dotenv(find_dotenv())

BOT_TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


async def main():
    print("Запуск...")
    await set_main_menu(bot)
    dp.include_router(router)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
