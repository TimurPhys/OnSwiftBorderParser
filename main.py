import asyncio
import logging
from aiogram import Bot, Dispatcher

from aiohttp import web

from bot.bot import router
from bot.form import form_router
from bot.admin_router import admin_router
from bot.view.commands import set_main_menu

import config.config as config
from db.db import init_db
from jobs.webhook import stripe_webhook
from jobs.cleaner import check_and_expire_subscriptions

bot = Bot(token=config.BOT_TOKEN)
dp = Dispatcher()

logging.basicConfig(level=logging.INFO)


async def main():
    print("Запуск...")
    await init_db()

    app = web.Application()
    app["bot"] = bot
    app.router.add_post("/stripe-webhook", stripe_webhook)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 8000)
    await site.start()
    print("🌐 Веб-сервер Stripe Webhook запущен на порту 8000.")

    asyncio.create_task(check_and_expire_subscriptions(bot))
    print("Чистильщик подписок запущен!")

    dp.include_router(router)
    dp.include_router(form_router)
    dp.include_router(admin_router)
    await set_main_menu(bot)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
