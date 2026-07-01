import asyncio
from aiogram import F, Router, Bot
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from datetime import datetime, timedelta
from config import *

from async_parser import run_async_parser
from bot.pushover import send_emergency_alert
from bot.kb import *

router = Router()

# Глобальная переменная, которая хранит статус: запущен ли мониторинг
monitoring_task = None
monitoring_counter = 0
first_monitoring_date = None
last_monitoring_date = None


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
    category = message.text.split(" ")[0]
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


@router.message(SetupSteps.confirm_start, F.text == "🚀 Запустить мониторинг")
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


@router.message(SetupSteps.confirm_start, F.text == "❌ Сбросить настройки")
async def cancel_settings(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Настройки сброшены, можете начать настройку сначала",
        reply_markup=ReplyKeyboardRemove(),
    )


@router.message(F.text == "/stop")
async def stop_monitoring(message: Message):
    global monitoring_task, monitoring_counter
    if monitoring_task and not monitoring_task.done():
        monitoring_task.cancel()
        monitoring_counter = 0
        await message.answer("🛑 Мониторинг успешно остановлен.")
    else:
        await message.answer("Мониторинг и так не работал.")


@router.message(F.text == "/check")
async def check_monitorings(message: Message):
    global monitoring_task
    if monitoring_task and not monitoring_task.done():
        await message.answer(
            f"🟢 **Мониторинг активен**\n"
            f"📊 Проверок сегодня: {monitoring_counter}\n"
            f"⏱ Последняя: {last_monitoring_date.strftime('%H:%M:%S')}",
            parse_mode="Markdown",
        )
    else:
        await message.answer(
            "🔴 **Мониторинг остановлен**\n" "Для запуска используй команду /start",
            parse_mode="Markdown",
        )


# --- АСИНХРОННЫЙ ГЛАВНЫЙ ЦИКЛ ПАРСИНГА ---
async def monitoring_loop(category, border_id, bot: Bot):
    global monitoring_counter, last_monitoring_date, first_monitoring_date
    border_names = {1: "Нарва", 2: "Койдула", 3: "Лухамаа"}
    while True:
        try:
            print("--- Фоновый запуск проверки ---")
            data = await run_async_parser(category=category, border_id=border_id)
            if data:
                last_monitoring_date = datetime.now()
                if last_monitoring_date - first_monitoring_date >= timedelta(days=1):
                    first_monitoring_date = datetime.now()
                    monitoring_counter = 0
                monitoring_counter += 1
                print(f"Итоговый словарь собранных данных за месяц:\n{data}")
                # await bot.send_message(MY_ID, "Были найдены новые данные!")
                matched_slots = []
                other_slots = []

                # 1. Проходим по ID границ (ключи 1, 2 и т.д.)
                for b_id, dates_dict in data.items():
                    # Получаем красивое название границы или пишем просто "КПП №..."
                    border_name = border_names.get(int(b_id))

                    # 2. Проходим по датам внутри этой границы
                    for date_str, slots_list in dates_dict.items():

                        # 3. Проходим по кортежам (время, статус)
                        for time_slot, status in slots_list:
                            if status.strip().lower() == "свободно":
                                # Формируем красивую строчку для списка

                                slot_line = f"📍 **{border_name}** | 📅 {date_str} в ⏰ {time_slot}"

                                is_match = False  # Флаг, подошел ли конкретный слот
                                if MY_ID in USER_FILTERS:
                                    user_pref = USER_FILTERS[MY_ID]
                                    border_match = user_pref["border"] in b_id

                                    date_match = False
                                    if user_pref["date_start"] == "any":
                                        date_match = True
                                    else:
                                        try:
                                            # Из строки "05.07.2026" делаем объект даты
                                            current_slot_date = datetime.strptime(
                                                date_str.strip(), "%d.%m.%Y"
                                            ).date()
                                            if (
                                                user_pref["date_start"]
                                                <= current_slot_date
                                                <= user_pref["date_end"]
                                            ):
                                                date_match = True
                                        except Exception as e:
                                            print(f"Ошибка проверки даты: {e}")

                                    time_match = False
                                    if user_pref["time"] == "any":
                                        time_match = True
                                    else:
                                        try:
                                            slot_hour = int(time_slot.split(":")[0])
                                            if user_pref["time"] == "morning" and (
                                                6 <= slot_hour < 12
                                            ):
                                                time_match = True
                                            elif user_pref["time"] == "day" and (
                                                12 <= slot_hour < 18
                                            ):
                                                time_match = True
                                            elif user_pref["time"] == "night" and (
                                                slot_hour >= 18 or slot_hour < 6
                                            ):
                                                time_match = True
                                        except Exception:
                                            pass

                                    # Если все три условия сошлись — этот слот идеален
                                    if border_match and date_match and time_match:
                                        is_match = True

                                # Сортируем слоты по спискам
                                if is_match:
                                    matched_slots.append(slot_line)
                                else:
                                    other_slots.append(slot_line)

                if matched_slots:
                    slots_text = "\n".join(other_slots)
                    message_text = (
                        f"🔥 <b>НАЙДЕНЫ ИДЕАЛЬНЫЕ СЛОТЫ ПО ФИЛЬТРУ!</b>\n\n"
                        f"{slots_text}\n\n"
                        f"Переходи <a href='https://www.eestipiir.ee/yphis/index.action'>на сайт границы</a> и бронируй!"
                    )
                    await bot.send_message(MY_ID, message_text, parse_mode="HTML")
                    await send_emergency_alert(slot_info=matched_slots[0].replace("**", ""))

                elif other_slots:
                    # Объединяем все найденные слоты через перенос строки
                    slots_text = "\n".join(other_slots)
                    message_text = (
                        f"🔥 <b>НАЙДЕНЫ СВОБОДНЫЕ СЛОТЫ ДЛЯ ЗАПИСИ!</b>\n\n"
                        f"{slots_text}\n\n"
                        f"Переходи <a href='https://www.eestipiir.ee/yphis/index.action'>на сайт границы</a> и бронируй!"
                    )
                    await bot.send_message(MY_ID, message_text, parse_mode="HTML")
                else:
                    print("Проверка завершена успешно: Свободных мест нет.")

        except asyncio.CancelledError:
            print("Фоновая задача остановлена пользователем.")
            break
        except Exception as e:
            print(f"Произошла ошибка парсинга {e}")
            await bot.send_message(MY_ID, f"Произошла ошибка парсинга {e}")

        await asyncio.sleep(300)  # Спим 5 минут
