import asyncio
from aiogram import Bot, Dispatcher
import os
from dotenv import load_dotenv, find_dotenv

from bot.bot import router

load_dotenv(find_dotenv())

BOT_TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


async def main():
    print("Запуск...")
    dp.include_router(router)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
