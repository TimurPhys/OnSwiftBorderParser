import asyncio
from aiogram import F, Router, Bot
from aiogram.filters import Command
from aiogram.types import (
    Message,
    ReplyKeyboardRemove,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from datetime import datetime
from config.config import *

from bot.view.kb import *
from bot.monitoring_loop import monitoring_loop

from db.db import check_user_payment

router = Router()

# Глобальная переменная, которая хранит статус: запущен ли мониторинг
monitoring_task = None
monitoring_counter = 0
first_monitoring_date = None
last_monitoring_date = None
border_names = {1: "Нарва", 2: "Койдула", 3: "Лухамаа"}


# Описываем шаги опроса (FSM)
class SetupSteps(StatesGroup):
    choosing_category = State()
    choosing_border = State()
    confirm_start = State()


# --- ЛОГИКА БОТА ---
@router.message(F.text == "/start")
async def start_cmd(message: Message, state: FSMContext):
    user_id = int(message.from_user.id)
    res = await check_user_payment(user_id)

    if not res["exists"]:
        welcome_text = (
            "👋 **Привет! Я твой личный бот-информатор по границам Эстония-Россия**\n\n"
            "Я собираю информацию о свободных местах каждые 5 минут с сайта GoSwift "
            "и присылаю уведомления, если есть свободные места** "
            "Чтобы начать пользоваться, активируй подписку на 31 дней 👇"
        )

        payment_keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="💳 Оформить подписку (31 дней)",
                        # Замени ссылку на свою реальную платежную ссылку или вебхук
                        callback_data="buy_subscription",
                    )
                ]
            ]
        )

        await message.answer(
            text=welcome_text, reply_markup=payment_keyboard, parse_mode="Markdown"
        )


@router.message(SetupSteps.choosing_category, ~Command("stop"))
async def process_category(message: Message, state: FSMContext):
    category = message.text.split(" ")[0]
    await state.update_data(category=category)

    await message.answer(
        "Шаг 2: Какой пункт пересечения отслеживать?", reply_markup=kb_borders
    )
    await state.set_state(SetupSteps.choosing_border)


@router.message(SetupSteps.choosing_border, ~Command("stop"))
async def process_border(message: Message, state: FSMContext):
    border_text = message.text
    # Парсим ID границы из текста кнопки
    if "1" in border_text:
        border_id = 1
    elif "2" in border_text:
        border_id = 2
    elif "3" in border_text:
        border_id = 3
    else:
        border_id = "ALL"  # Для логики "Все"

    if "ВСЕ" not in border_text:
        border_name = border_text.split(" - ")[1]
    else:
        border_name = "Отслеживать ВСЕ"
    await state.update_data(border_id=border_id)
    user_data = await state.get_data()

    await message.answer(
        f"Настройки сохранены!\n"
        f"🚗 Категория: {user_data['category']}\n"
        f"📍 Название КПП: {border_name}\n\n"
        f"Подтверди запуск:",
        reply_markup=kb_confirm,
    )
    await state.set_state(SetupSteps.confirm_start)


@router.message(
    SetupSteps.confirm_start, F.text == "🚀 Запустить мониторинг", ~Command("stop")
)
async def start_monitoring(message: Message, state: FSMContext, bot: Bot):
    global monitoring_task, first_monitoring_date
    user_data = await state.get_data()
    print(user_data)
    await state.clear()
    await message.answer(
        "Принято! Запускаю фоновую задачу. Буду проверять каждые 5 минут...",
        reply_markup=ReplyKeyboardRemove(),
    )

    # Запускаем бесконечный цикл парсинга в фоне (асинхронно!)
    first_monitoring_date = datetime.now()
    monitoring_task = asyncio.create_task(
        monitoring_loop(user_data["category"], user_data["border_id"], bot)
    )


@router.message(
    SetupSteps.confirm_start, F.text == "❌ Сбросить настройки", ~Command("stop")
)
async def cancel_settings(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Настройки сброшены, можете начать настройку сначала",
        reply_markup=ReplyKeyboardRemove(),
    )


@router.message(F.text == "/stop")
async def stop_monitoring(message: Message, state: FSMContext):
    global monitoring_task, monitoring_counter, USER_FILTERS
    current_state = await state.get_state()
    if current_state is not None:
        await state.clear()
        USER_FILTERS.clear()
        await message.answer(
            "❌ Заполнение прервано. Вы вернулись в начало.",
            reply_markup=ReplyKeyboardRemove(),
        )
    elif monitoring_task and not monitoring_task.done():
        monitoring_task.cancel()
        monitoring_counter = 0
        await message.answer(
            "🛑 Мониторинг успешно остановлен. Персональные фильтры не сброшены.",
            reply_markup=ReplyKeyboardRemove(),
        )
    else:
        await message.answer(
            "Мониторинг и так не работал.", reply_markup=ReplyKeyboardRemove()
        )


@router.message(F.text == "/check")
async def check_monitorings(message: Message):
    global monitoring_task
    if monitoring_task and not monitoring_task.done():
        user_pref = USER_FILTERS.get(message.from_user.id)
        message_str = (
            f"🟢 <b>Мониторинг активен</b>\n"
            f"📊 Проверок сегодня: {monitoring_counter}\n"
            f"⏱ Последняя: {last_monitoring_date.strftime('%H:%M:%S')}\n\n"
        )

        if user_pref is not None:
            borders_str = ", ".join([border_names.get(b) for b in user_pref["borders"]])
            message_str += (
                f"<b>Персональные настройки:</b>\n"
                f"📍 Пункты: {borders_str}\n"
                f"📅 Дата: {user_pref['date_start']} по {user_pref['date_end']}\n"
                f"🕒 Время суток: {user_pref['time']}\n\n"
            )
        else:
            message_str += f"<b>Персональные настройки:</b> Отсутствуют\n\n"

        await message.answer(text=message_str, parse_mode="HTML")
    else:
        await message.answer(
            "🔴 **Мониторинг остановлен**\n" "Для запуска используй команду /start",
            parse_mode="Markdown",
        )
