import asyncio
from aiogram import Bot, Dispatcher

from aiohttp import web

from bot.bot import router
from bot.form import form_router

from bot.payment import payment_router
from bot.view.commands import set_main_menu
import config.config as config

from db.db import init_db

from jobs.webhook import stripe_webhook

bot = Bot(token=config.BOT_TOKEN)
dp = Dispatcher()


async def main():
    print("Запуск...")
    await init_db()

    app = web.Application()
    app["bot"] = bot
    app.router.add_post("/webhook/stripe", stripe_webhook)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 8080)
    await site.start()
    print("🌐 Веб-сервер Stripe Webhook запущен на порту 8080.")

    await set_main_menu(bot)
    dp.include_router(router)
    dp.include_router(form_router)
    dp.include_router(payment_router)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
