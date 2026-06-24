from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

kb_category = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="B (Легковые)"), KeyboardButton(text="C (Грузовые)")]
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
