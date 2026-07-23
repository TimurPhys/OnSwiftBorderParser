import asyncio
from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, Message, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import StateFilter
from datetime import datetime

from bot.view.kb import get_admin_kb, get_user_request_kb, remove_superuser_kb
from bot.monitoring_loop import monitoring_loop
from db.db import get_user_stats, get_superusers_list, change_superuser_state

import config.config as cfg

admin_router = Router()


class AdminPanel(StatesGroup):
    inside_super_user_panel = State()
    waiting_super_user_to_delete = State()


@admin_router.callback_query(F.data == "admin_panel", StateFilter(None))
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

    kb = get_admin_kb()
    await callback.message.answer(
        text=message_text,
        parse_mode="HTML",
        reply_markup=kb.as_markup(),
    )
    await callback.answer()


@admin_router.callback_query(F.data == "start_monitoring")
async def start_monitoring(callback: CallbackQuery, bot: Bot):
    if cfg.monitoring_task and not cfg.monitoring_task.done():
        await callback.message.edit_text("Мониторинг уже запущен.")
    else:
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


@admin_router.callback_query(F.data == "super_users")
async def ask_for_user(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AdminPanel.inside_super_user_panel)
    superusers = await get_superusers_list()
    print(superusers)
    text = (
        f"В этом меню вы можете убрать/добавить нового супер-пользователя, который сможет пользоваться этим ботом полностью без подписки.\n\n"
        f"На данный момент суперюзерами являются: \n"
    )
    if superusers:
        await state.update_data(superusers=superusers)
        for user in superusers:
            text += f"<a href='https://t.me/{user}'>ID: {user}</a>\n"
    else:
        text += "<b>Никто</b>"

    kb = get_user_request_kb(superusers)
    await callback.message.answer(text=text, reply_markup=kb, parse_mode="HTML")
    await callback.answer()


@admin_router.message(
    F.text == "Убрать пользователя", AdminPanel.inside_super_user_panel
)
async def process_superuser_delete(message: Message, state: FSMContext):
    await state.set_state(AdminPanel.waiting_super_user_to_delete)
    user_data = await state.get_data()
    superusers = user_data.get("superusers")
    kb = remove_superuser_kb(superusers)
    await message.answer(
        text="Какого суперюзера вы хотите удалить?", reply_markup=kb.as_markup()
    )


@admin_router.callback_query(
    F.data.startswith("user_"), AdminPanel.waiting_super_user_to_delete
)
async def delete_superuser(callback: CallbackQuery, state: FSMContext):
    try:
        user_data = await state.get_data()
        superusers = user_data.get("superusers")
        user_id = int(callback.data.split("_")[1])

        if user_id in superusers:
            await change_superuser_state(user_id, 0)
            await callback.message.answer(
                text=f"Пользователь <a href='https://t.me/{user_id}'>ID: {user_id}</a> успешно удален из списка суперпользователей",
                parse_mode="HTML",
            )
            await callback.answer()

            print(superusers)

            superusers.remove(user_id)
            await state.update_data(superusers=superusers)

            print(superusers)
            if len(superusers) > 0:
                kb = remove_superuser_kb(superusers)
                await callback.message.answer(
                    text="Какого еще суперюзера вы хотите удалить?",
                    reply_markup=kb.as_markup(),
                )
            else:
                await callback.message.edit_text(text="Все суперюзеры успешно удалены.")
                await state.clear()
    except Exception as e:
        await callback.message.answer(
            f"Не удалось удалить данного пользователя. Произошла ошибка: {e}"
        )


@admin_router.callback_query(
    F.data == "stop_deletion", AdminPanel.waiting_super_user_to_delete
)
async def delete_superuser(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(text="Удаление суперпользователй прекращено")
    await state.clear()


@admin_router.message(F.text == "Выйти", AdminPanel.inside_super_user_panel)
async def delete_superuser(message: Message, state: FSMContext):
    await message.answer(
        text="Удаление суперпользователй прекращено", reply_markup=ReplyKeyboardRemove()
    )
    await state.clear()


@admin_router.message(
    F.user_shared.request_id == 42, AdminPanel.inside_super_user_panel
)
async def process_superuser_share(message: Message, state: FSMContext):
    shared_user = message.user_shared
    if not shared_user:
        await message.answer("Не удалось получить данные пользователя.")
        return

    # Достаем user_id выбранного человека!
    target_user_id = int(shared_user.user_id)
    user_data = await state.get_data()
    superusers = user_data.get("superusers")
    if superusers:
        if target_user_id in superusers:
            kb = get_user_request_kb(superusers)
            await message.answer(
                text="Данный пользователь уже есть в списке суперюзеров.",
                reply_markup=kb,
            )
            return

    if target_user_id != cfg.ADMIN_ID:
        await change_superuser_state(target_user_id, 1)

        await message.answer(
            f"✅ Пользователь с ID <code>{target_user_id}</code> успешно назначен **SuperUser**!",
            parse_mode="HTML",
        )

        await state.clear()
    else:
        await message.answer(text="Админ, ты так-то и так здесь бог))")
