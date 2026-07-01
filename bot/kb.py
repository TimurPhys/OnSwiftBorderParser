from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

kb_category = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="A (Мотоцикл)"), KeyboardButton(text="B (Легковое авто)")],
        [
            KeyboardButton(text="BC (Легковое авто с грузом)"),
            KeyboardButton(text="C (Грузовое авто с грузом)"),
        ],
        [
            KeyboardButton(text="D (Автобус)"),
            KeyboardButton(text="CE (Грузовое авто без груза)"),
        ],
    ],
    resize_keyboard=True,
)

kb_borders = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="1 - Нарва"), KeyboardButton(text="3 - Лухамаа")],
        [KeyboardButton(text="2 - Койдула"), KeyboardButton(text="Отслеживать ВСЕ")],
    ],
    resize_keyboard=True,
)

kb_confirm = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="🚀 Запустить мониторинг"),
            KeyboardButton(text="❌ Сбросить настройки"),
        ]
    ],
    resize_keyboard=True,
)

def get_inline_borders_kb():
    builder = InlineKeyboardBuilder()
    # Текст на кнопке, и что кнопка отправляет в код (callback_data)
    builder.button(text="📍 Нарва (Narva)", callback_data="border_1")
    builder.button(text="📍 Лухамаа (Luhamaa)", callback_data="border_2")
    builder.button(text="📍 Койдула (Koidula)", callback_data="border_3")
    builder.adjust(1)  # Кнопки одна под другой
    return builder

def get_inline_times_kb():
    builder = InlineKeyboardBuilder()
    builder.button(text="🕒 Любое время", callback_data="time_any")
    builder.button(text="🌅 Утро (06:00 - 12:00)", callback_data="time_morning")
    builder.button(text="☀️ День (12:00 - 18:00)", callback_data="time_day")
    builder.button(text="🌙 Вечер/Ночь (18:00 - 06:00)", callback_data="time_night")
    builder.adjust(1)
    return builder