from aiogram import F, Router, Bot
from aiogram.types import (
    Message,
    CallbackQuery,
)
from aiogram.fsm.context import FSMContext
import config.config as cfg
from bot.view.kb import *

from db.db import get_user_instance, start_trial_subscription, get_user_filters

router = Router()


async def delete_last_message(old_msg_id, user_id, bot: Bot, state: FSMContext):
    if old_msg_id:
        try:
            await bot.delete_message(chat_id=user_id, message_id=old_msg_id)
        except Exception as e:
            # Ошибка может быть, если сообщение старше 48 часов
            # (Telegram запрещает удалять такие сообщения ботам)
            print(f"Не удалось удалить старое сообщение: {e}")

        # Очищаем данные в FSM, чтобы не пытаться удалить его повторно
        await state.update_data(last_msg_id=None)


# --- ЛОГИКА БОТА ---
@router.message(F.text == "/start")
async def start_cmd(message: Message, state: FSMContext, bot: Bot):
    user_data = await state.get_data()
    user_id = int(message.from_user.id)
    old_msg_id = user_data.get("last_msg_id")
    await delete_last_message(old_msg_id, user_id, bot, state)

    user = await get_user_instance(user_id)

    if not user["exists"] and user_id != ADMIN_ID:
        welcome_text = (
            "👋 **Привет! Я твой личный бот-информатор по границам Эстония-Россия**\n\n"
            "Я собираю информацию о свободных местах каждые 5 минут с сайта GoSwift "
            "и присылаю уведомления, если есть свободные места** "
            "Чтобы начать пользоваться, активируй подписку на 31 дней 👇"
        )

        user_id = int(message.from_user.id)
        kb = get_inline_init_buttons(user_id)
        sent_message = await message.answer(
            text=welcome_text, reply_markup=kb.as_markup(), parse_mode="Markdown"
        )
        await state.update_data(last_msg_id=sent_message.message_id)

    # Пользователь уже существует и записан
    else:
        kb, start_text = get_user_interface(user, user_id)
        await message.answer(text=start_text, reply_markup=kb.as_markup())


@router.callback_query(F.data == "trial")
async def ask_to_start_trial(callback: CallbackQuery):
    kb = get_inline_buttons()
    await callback.message.edit_text(
        text="Вы уверены, что хотите начать пробный период?",
        reply_markup=kb.as_markup(),
    )
    await callback.answer()


@router.callback_query(F.data == "yes_confirm")
async def start_trial(callback: CallbackQuery):
    user_id = int(callback.from_user.id)
    print(user_id)
    try:
        await start_trial_subscription(user_id)
        await callback.message.edit_text(
            text="Пробный период подписки успешно начат. Теперь вы сможете сразу видеть свободные места на границе, если они появляются."
        )
        await callback.answer()
    except Exception as e:
        print(f"Произошла непредвиденная ошибка {e}")
        await callback.answer(text=f"Произошла непредвиденная ошибка {e}")


@router.callback_query(F.data == "no_deny")
async def start_trial(callback: CallbackQuery):
    try:
        await callback.message.delete()
        await callback.answer()
    except Exception as e:
        print(f"Произошла непредвиденная ошибка {e}")
        await callback.answer(text=f"Произошла непредвиденная ошибка {e}")


@router.callback_query(F.data.startswith("list_plans"))
async def list_plans(callback: CallbackQuery, state: FSMContext):
    plans = int(callback.data.split("_")[-1])
    user_id = int(callback.from_user.id)
    kb = get_inline_plans(plans, user_id)

    if plans == 1:
        sent_message = await callback.message.edit_text(
            text="Так как у вас уже куплена стандратная подписка, вам доступна покупка звонков.",
            reply_markup=kb.as_markup(),
        )
    elif plans == 2:
        sent_message = await callback.message.edit_text(
            text="Выберите план, который вам больше нравится",
            reply_markup=kb.as_markup(),
        )

    await state.update_data(last_msg_id=sent_message.message_id)
    await callback.answer()


## --- Получение статистики ---
@router.callback_query(F.data == "check")
async def check_monitorings(callback: CallbackQuery):
    if cfg.monitoring_task and not cfg.monitoring_task.done():
        if cfg.last_monitoring_date is None:
            await callback.message.answer(
                "Мониторинг только запустился, подождите, пока соберутся данные."
            )
        else:
            user_id = int(callback.from_user.id)
            user_filters = await get_user_filters([user_id])
            user_filter = user_filters.get(user_id)

            print(user_filter)

            message_str = (
                f"🟢 <b>Мониторинг активен</b>\n"
                f"📊 Проверок сегодня: {cfg.monitoring_counter}\n"
                f"⏱ Последняя: {cfg.last_monitoring_date.strftime('%H:%M:%S')}\n\n"
            )

            if user_filter is not None:
                borders_str = ", ".join(
                    [cfg.border_names.get(b) for b in user_filter["borders"]]
                )
                if user_filter["date_start"] != "any":
                    date_text = f"{str(user_filter['date_start'])} по {str(user_filter['date_end'])}"
                else:
                    date_text = "Любая"
                message_str += (
                    f"<b>Персональные настройки:</b>\n"
                    f"📍 Пункты: {borders_str}\n"
                    f"📅 Дата: {date_text}\n"
                    f"🕒 Время суток: {cfg.trans[user_filter['time']]}\n"
                    f"📞 Номер телефона: +{user_filter['number']}\n\n"
                )
            else:
                message_str += f"<b>Персональные настройки:</b> Отсутствуют\n\n"

            await callback.message.answer(text=message_str, parse_mode="HTML")
    else:
        await callback.message.answer(
            "🔴 **Мониторинг в данным момент не работает**\n"
            "Происходят технические работы",
            parse_mode="Markdown",
        )

    await callback.answer()
