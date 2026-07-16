import asyncio
from aiogram import Bot, Dispatcher

from bot.bot import router
from bot.form import form_router
from bot.commands import set_main_menu
import config.config as config

from jobs.caller import send_voice_alert

bot = Bot(token=config.BOT_TOKEN)
dp = Dispatcher()


async def main():
    print("Запуск...")

    res = await send_voice_alert("It is a test call!", "37128751517")
    print(f"Статус: {res['success']}")
    # await set_main_menu(bot)
    # dp.include_router(router)
    # dp.include_router(form_router)
    # await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
