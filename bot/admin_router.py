import asyncio
from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery
from datetime import datetime

from bot.view.kb import get_monitoring_kb
from bot.monitoring_loop import monitoring_loop

from db.db import get_user_stats

import config.config as cfg

admin_router = Router()


@admin_router.callback_query(F.data == "admin_panel")
async def show_admin_panel(callback: CallbackQuery):
    monitoring_state = (
        "<b>Активен</b>"
        if cfg.monitoring_task and not cfg.monitoring_task.done()
        else "<b>Не активен</b>"
    )
    user_stats = await get_user_stats()
    message_text = (
        f"<b>Мониторинг: </b>\n"
        f"Текущее состояние мониторинга: {monitoring_state}\n\n"
        f"<b>Статистика пользователей</b>\n"
        f"Количество пользователей с пробной подпиской: <b>{user_stats['trial']}</b>\n"
        f"Количество пользователей c подпиской: <b>{user_stats['paid']}</b>\n"
        f"Количество пользователей с полной подпиской: <b>{user_stats['have_dlc']}</b>"
    )

    kb = get_monitoring_kb()
    await callback.message.answer(
        text=message_text,
        parse_mode="HTML",
        reply_markup=kb.as_markup(),
    )
    await callback.answer()


@admin_router.callback_query(F.data == "start_monitoring")
async def start_monitoring(callback: CallbackQuery, bot: Bot):
    await callback.message.edit_text(
        "Принято! Запускаю фоновую задачу. Буду проверять каждые 5 минут...",
    )
    cfg.first_monitoring_date = datetime.now()
    cfg.monitoring_task = asyncio.create_task(monitoring_loop("B", "ALL", bot))


@admin_router.callback_query(F.data == "stop_monitoring")
async def start_monitoring(callback: CallbackQuery, bot: Bot):
    if cfg.monitoring_task and not cfg.monitoring_task.done():
        cfg.monitoring_task.cancel()
        cfg.monitoring_counter = 0
        await callback.message.edit_text(
            "🛑 Мониторинг успешно остановлен. Персональные фильтры не сброшены.",
        )
    else:
        await callback.message.edit_text("Мониторинг и так не работал.")
