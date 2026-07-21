from config.config import (
    PAYMENT_SUBSCRIPTION_LINK,
    PAYMENT_SUBSCRIPTION_AND_CALLS_LINK,
    PAYMENT_CALLS_LINK,
    ADMIN_ID,
)
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from datetime import datetime, timedelta

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


def get_inline_plans(type: int, user_id: int):
    builder = InlineKeyboardBuilder()
    if type == 1:
        builder.button(
            text="Докупить звонки",
            url=f"{PAYMENT_CALLS_LINK}?client_reference_id={user_id}?offer_type=3",
        )
    elif type == 2:
        builder.button(
            text="Купить подписку (5 €)",
            callback_data="type_1",
            url=f"{PAYMENT_SUBSCRIPTION_LINK}?client_reference_id={user_id}?offer_type=1",
        )
        builder.button(
            text="Купить подписку + звонки (8 €)",
            callback_data="type_2",
            url=f"{PAYMENT_SUBSCRIPTION_AND_CALLS_LINK}?client_reference_id={user_id}?offer_type=2",
        )
    builder.adjust(1)
    return builder


def get_user_interface(user: dict, user_id: int):
    builder = InlineKeyboardBuilder()
    builder.button(text="Статистика", callback_data="check")
    builder.button(text="Помощь (Настройки)", callback_data="help")
    if not user["exists"] and user_id == ADMIN_ID:
        start_text = f"Здравствуйте, администратор. Предоставляю вам полный контроль над ботом и мониторингом."
        builder.button(text="Настроить фильтр", callback_data="set_filter")
        builder.button(text="Панель админа", callback_data="admin_panel")
    else:
        last_payment_date = user["last_payment_date"]
        if user["is_trial"]:
            end_of_subscription = datetime.strftime(
                datetime.strptime(last_payment_date, "%Y-%m-%d %H:%M:%S")
                + timedelta(days=7),
                "%Y-%m-%d",
            )
            start_text = f"Ваш профиль активен и находится в пробном периоде. Вы будете получать уведомления о свободных местах на границе до {end_of_subscription}."
            builder.button(
                text="Тарифы",
                callback_data="list_plans_2",
            )
        else:
            end_of_subscription = datetime.strftime(
                datetime.strptime(last_payment_date, "%Y-%m-%d %H:%M:%S")
                + timedelta(days=31),
                "%Y-%m-%d",
            )
            if user["is_paid"] and not user["has_dlc"]:
                start_text = f"Ваш профиль активен и действует стандратная подписка без звонков. Вы будете получать уведомления о свободных местах на границе до {end_of_subscription}."
                builder.button(
                    text="Тарифы",
                    callback_data="list_plans_1",
                )
            elif user["is_paid"] and user["has_dlc"]:
                start_text = f"Ваш профиль активен и действует полная подписка со звонками. Вы будете получать уведомления и звонки о свободных местах на границе до {end_of_subscription}."
                builder.button(text="Настроить фильтр", callback_data="set_filter")
    builder.adjust(2)
    return builder, start_text


def get_monitoring_kb():
    builder = InlineKeyboardBuilder()
    builder.button(text="Начать мониторинг", callback_data="start_monitoring")
    builder.button(text="Остановить мониторинг", callback_data="stop_monitoring")
    builder.adjust(1)
    return builder


def get_inline_init_buttons(user_id: int):
    builder = InlineKeyboardBuilder()
    builder.button(
        text="Купить подписку (5 €)",
        callback_data="type_1",
        url=f"{PAYMENT_SUBSCRIPTION_LINK}?client_reference_id={user_id}?offer_type=1",
    )
    builder.button(
        text="Купить подписку + звонки (8 €)",
        callback_data="type_2",
        url=f"{PAYMENT_SUBSCRIPTION_AND_CALLS_LINK}?client_reference_id={user_id}?offer_type=2",
    )
    builder.button(text="Начать пробный период (7-дней)", callback_data="trial")
    builder.adjust(1)
    return builder


def get_inline_buttons():
    builder = InlineKeyboardBuilder()
    builder.button(text="Да", callback_data="yes_confirm")
    builder.button(text="Нет", callback_data="no_deny")
    return builder

def get_settings_buttons():
    builder = InlineKeyboardBuilder()
    builder.button(text="Тестовый звонок", callback_data="test_call")
    builder.button(text="Остановить подписку", callback_data="stop_subscription")
    return builder


def get_inline_borders_kb():
    builder = InlineKeyboardBuilder()
    # Текст на кнопке, и что кнопка отправляет в код (callback_data)
    builder.button(text="📍 Нарва (Narva)", callback_data="border_1")
    builder.button(text="📍 Койдула (Koidula)", callback_data="border_2")
    builder.button(text="📍 Лухамаа (Luhamaa)", callback_data="border_3")
    builder.button(text="➡️ Продолжить", callback_data="border_continue")
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
