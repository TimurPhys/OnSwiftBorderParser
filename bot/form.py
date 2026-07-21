from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton
from datetime import datetime
import re
from bot.view.kb import *
import config.config as cfg
from db.db import save_user_filter

form_router = Router()


class SearchPreferences(StatesGroup):
    waiting_for_border = State()
    waiting_for_date = State()
    waiting_for_time = State()
    waiting_for_number = State()


# 2. Стартуем опрос по команде /set_filter
@form_router.callback_query(F.data == "set_filter")
async def class_start_filter(callback: CallbackQuery, state: FSMContext):
    inline_kb_borders = get_inline_borders_kb()
    await callback.message.answer(
        "📝 Настраиваем фильтр для звонков.\n\nКакая **граница** интересует? (можно выбрать несколько)",
        reply_markup=inline_kb_borders.as_markup(),
    )
    await state.set_state(SearchPreferences.waiting_for_border)
    await callback.answer()


# 3. Ловим границу
@form_router.callback_query(SearchPreferences.waiting_for_border)
async def process_border(callback: CallbackQuery, state: FSMContext):
    # Если нажали кнопку продолжить
    if callback.data == "border_continue":
        user_data = await state.get_data()
        chosen_borders = user_data.get("borders", [])

        if not chosen_borders:
            await callback.answer(
                "⚠️ Выберите хотя бы один пункт перед продолжением!", show_alert=True
            )
            return

        names_str = ", ".join([cfg.border_names.get(b) for b in chosen_borders])

        builder = InlineKeyboardBuilder()
        builder.button(text="📅 Искать на любую дату", callback_data="date_any")
        await callback.message.edit_text(
            f"📍 Выбраны пункты: **{cfg.border_names.get(names_str)}**\n\n"
            f"Укажи период дат, в который ты готов ехать.\n"
            f"Напиши его текстом в формате: `ДД.ММ - ДД.ММ`\n\n"
            f"ℹ️ *Пример: 05.07 - 05.08* (или просто нажмите кнопку ниже, если дата не важна)",
            reply_markup=builder.as_markup(),
            parse_mode="Markdown",
        )
        await state.set_state(SearchPreferences.waiting_for_date)
        await callback.answer()
        return

    # Логика обработки нескольких границ

    current_choice = int(callback.data.lower().split("_")[1])

    user_data = await state.get_data()
    chosen_borders = user_data.get("borders", [])

    if current_choice not in chosen_borders:
        chosen_borders.append(current_choice)

    await state.update_data(borders=chosen_borders)

    builder = InlineKeyboardBuilder()
    for b_id, b_name in cfg.border_names.items():
        if b_id not in chosen_borders:
            builder.button(text=f"📍 {b_name}", callback_data=f"border_{b_id}")

    builder.adjust(1)
    builder.row(
        InlineKeyboardButton(text="➡️ Продолжить", callback_data="border_continue")
    )

    names_str = ", ".join([cfg.border_names.get(b) for b in chosen_borders])

    await callback.message.edit_text(
        f"📝 Уже выбрано: **{names_str}**\n\n"
        f"Вы можете выбрать еще пункты из списка ниже или нажать 'Продолжить':",
        reply_markup=builder.as_markup(),
        parse_mode="Markdown",
    )
    await callback.answer()


@form_router.callback_query(SearchPreferences.waiting_for_date, F.data == "date_any")
async def process_date_callback(callback: CallbackQuery, state: FSMContext):
    await state.update_data(date_start="any", date_end="any")
    await ask_for_time(callback.message, state)
    await callback.answer()


# 4. ЛОВИМ ДАТУ (Вариант Б: Если пользователь ввел ПЕРИОД текстом)
@form_router.message(SearchPreferences.waiting_for_date)
async def process_date_text(message: Message, state: FSMContext):
    text = message.text.strip()

    # Регулярка, которая ищет две даты вида ХХ.ХХ (разделенные дефисом, пробелом или словом "до")
    match = re.search(r"(\d{2})\.(\d{2})\s*(?:-|до|\s)\s*(\d{2})\.(\d{2})", text)

    if not match:
        await message.answer(
            "❌ **Неверный формат!**\n"
            "Пожалуйста, введи период строго по примеру:\n"
            "`05.07 - 05.08`"
        )
        return  # Не пускаем дальше, пока не введет нормально

    # Извлекаем день и месяц для старта и конца
    start_day, start_month, end_day, end_month = match.groups()
    current_year = datetime.now().year

    try:
        # Собираем полноценные объекты дат (добавляем текущий год)
        date_start = datetime(current_year, int(start_month), int(start_day)).date()
        date_end = datetime(current_year, int(end_month), int(end_day)).date()

        # Проверка: если дата конца меньше даты старта (например, переход через Новый Год)
        if date_end < date_start:
            date_end = datetime(current_year + 1, int(end_month), int(end_day)).date()

    except ValueError:
        await message.answer(
            "❌ Такой даты не существует (например, 32.05). Попробуй еще раз:"
        )
        return

    # Сохраняем обе даты в FSM state
    await state.update_data(date_start=date_start, date_end=date_end)

    # Переходим к выбору времени
    await ask_for_time(message, state)


async def ask_for_time(message: Message, state: FSMContext):
    user_data = await state.get_data()

    if user_data.get("date_start") == "any":
        period_str = "Любая дата"
    else:
        period_str = f"с {user_data['date_start'].strftime('%d.%m')} по {user_data['date_end'].strftime('%d.%m')}"

    builder = get_inline_times_kb()

    await message.answer(
        f"📅 Период поиска: **{period_str}**\n\nУкажи желаемое время суток:",
        reply_markup=builder.as_markup(),
    )
    await state.set_state(SearchPreferences.waiting_for_time)


@form_router.callback_query(SearchPreferences.waiting_for_time)
async def process_number(callback: CallbackQuery, state: FSMContext):
    time_val = callback.data.split("_")[1]
    await state.update_data(time=time_val)
    await callback.message.edit_text(
        text="Пожалуйста введите ваш номер телефона с кодом страны. Пример: +37112347817. Пожалуйста, проверьте дважды проверьте подлинность написания."
    )
    await state.set_state(SearchPreferences.waiting_for_number)
    await callback.answer()


@form_router.message(SearchPreferences.waiting_for_number)
async def process_number(message: Message, state: FSMContext):
    user_text = message.text
    if user_text[0] == "+" and user_text[1:].isdigit():
        number = user_text[1:]
        await state.update_data(number=number)
        user_data = await state.get_data()
        await message.answer(text="Ваш номер телефона успешно принят.")

        last_test_call_time = user_data.get("last_test_call_time")
        await state.clear()
        if last_test_call_time:
            await state.update_data(last_test_call_time=last_test_call_time)

        filter = {
            "borders": user_data["borders"],
            "date_start": user_data["date_start"],
            "date_end": user_data["date_end"],
            "time": user_data["time"],
            "number": user_data["number"],
        }
        await save_user_filter(user_id=int(message.from_user.id), filter=filter)
        print(filter)

        borders_str = ", ".join([cfg.border_names.get(b) for b in user_data["borders"]])
        # Убираем кнопки и пишем финальный статус
        await message.answer(
            f"✅ **Фильтр успешно активирован!**\n\n"
            f"📍 Пункты: {borders_str}\n"
            f"📅 Дата: {str(user_data['date_start']) + ' по ' + str(user_data['date_end']) if user_data['date_start'] != 'any' else 'любая'}\n"
            f"🕒 Время суток: {cfg.trans[user_data['time']]}\n"
            f"📞 Номер телефона: +{user_data['number']}\n\n"
            f"Если парсер найдет этот слот, бот вам позвонит!"
        )
    else:
        await message.answer(
            text="Неправильный формат написания. Пример: +37112347817, где +371 - код страны, а 12347817 - номер телефона."
        )
