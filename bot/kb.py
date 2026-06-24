from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

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
