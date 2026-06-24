import asyncio
from aiogram import F, Router
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from async_parser import AsyncBorderParser  # Импортируем наш новый парсер
from async_parser import run_async_parser
from bot.kb import *

router = Router()

# Глобальная переменная, которая хранит статус: запущен ли мониторинг
monitoring_task = None


# Описываем шаги опроса (FSM)
class SetupSteps(StatesGroup):
    choosing_category = State()
    choosing_border = State()
    confirm_start = State()


# --- ЛОГИКА БОТА ---


@router.message(F.text == "/start")
async def start_cmd(message: Message, state: FSMContext):
    global monitoring_task
    if monitoring_task and not monitoring_task.done():
        await message.answer("Мониторинг уже запущен! Напиши /stop, чтобы остановить.")
        return

    await message.answer(
        "Привет, хозяин! Давай настроим парсер.\nШаг 1: Выбери категорию транспорта:",
        reply_markup=kb_category,
    )
    await state.set_state(SetupSteps.choosing_category)


@router.message(SetupSteps.choosing_category)
async def process_category(message: Message, state: FSMContext):
    category = "B" if "B" in message.text else "C"
    await state.update_data(category=category)

    await message.answer(
        "Шаг 2: Какой пункт пересечения отслеживать?", reply_markup=kb_borders
    )
    await state.set_state(SetupSteps.choosing_border)


@router.message(SetupSteps.choosing_border)
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

    await state.update_data(border_id=border_id)
    user_data = await state.get_data()

    await message.answer(
        f"Настройки сохранены!\n"
        f"🚗 Категория: {user_data['category']}\n"
        f"📍 КПП ID: {user_data['border_id']}\n\n"
        f"Подтверди запуск:",
        reply_markup=kb_confirm,
    )
    await state.set_state(SetupSteps.confirm_start)


@router.message(SetupSteps.confirm_start, F.text == "🚀 Запустить мониторинг")
async def start_monitoring(message: Message, state: FSMContext):
    global monitoring_task
    user_data = await state.get_data()
    print(user_data)
    await state.clear()

    await message.answer(
        "Принято! Запускаю фоновую задачу. Буду проверять каждые 5 минут...",
        reply_markup=ReplyKeyboardRemove(),
    )

    # Запускаем бесконечный цикл парсинга в фоне (асинхронно!)
    monitoring_task = asyncio.create_task(
        monitoring_loop(user_data["category"], user_data["border_id"])
    )


@router.message(SetupSteps.confirm_start, F.text == "❌ Сбросить настройки")
async def cancel_settings(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Настройки сброшены, можете начать настройку сначала",
        reply_markup=ReplyKeyboardRemove(),
    )


@router.message(F.text == "/stop")
async def stop_monitoring(message: Message):
    global monitoring_task
    if monitoring_task and not monitoring_task.done():
        monitoring_task.cancel()
        await message.answer("🛑 Мониторинг успешно остановлен.")
    else:
        await message.answer("Мониторинг и так не работал.")


# --- АСИНХРОННЫЙ ГЛАВНЫЙ ЦИКЛ ПАРСИНГА ---
async def monitoring_loop(category, border_id):
    while True:
        try:
            print("--- Фоновый запуск проверки ---")
            data = await run_async_parser(category=category, border_id=border_id)
            print(f"Итоговый словарь собранных данных за месяц:\n{data}")

        except asyncio.CancelledError:
            print("Фоновая задача остановлена пользователем.")
            break

        await asyncio.sleep(300)  # Спим 5 минут
