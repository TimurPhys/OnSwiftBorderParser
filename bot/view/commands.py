from aiogram.types import BotCommand
from aiogram import Bot


async def set_main_menu(bot: Bot):
    """Регистрирует команды в интерфейсе Telegram"""
    main_menu_commands = [
        BotCommand(command="/start", description="🚀 Начать работу"),
    ]
    await bot.set_my_commands(main_menu_commands)
    print("📋 Меню команд успешно обновлено в Telegram!")
