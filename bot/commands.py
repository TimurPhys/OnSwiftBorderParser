from aiogram.types import BotCommand
from aiogram import Bot


async def set_main_menu(bot: Bot):
    """Регистрирует команды в интерфейсе Telegram"""
    main_menu_commands = [
        BotCommand(
            command="/start", description="🚀 Настроить и запустить мониторинг границы"
        ),
        BotCommand(command="/stop", description="🛑 Остановить проверку слотов"),
    ]
    await bot.set_my_commands(main_menu_commands)
    print("📋 Меню команд успешно обновлено в Telegram!")
