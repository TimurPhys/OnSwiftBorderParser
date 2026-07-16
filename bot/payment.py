from aiogram import Bot, Router, F
from aiogram.types import Message, LabeledPrice, CallbackQuery, PreCheckoutQuery
from config.config import PAYMENTS_TOKEN

from db.db import set_user_paid

payment_router = Router()


@payment_router.callback_query(F.data == "buy_subscription")
async def buy(
    callback: CallbackQuery,
):
    await callback.bot.send_invoice(
        chat_id=int(callback.message.chat.id),
        title="Подписка на 31 день",
        description="Доступ к системе уведомлений о границе Эстония-Россия на 31 дней.",
        payload="month_subscription_payload",
        provider_token=PAYMENTS_TOKEN,
        currency="EUR",
        prices=[LabeledPrice(label="Подписка на 1 месяц", amount=5 * 100)],
        start_parameter="subscribe_31_days",
    )
    await callback.answer()


@payment_router.pre_checkout_query()
async def process_pre_checkout(pre_checkout_query: PreCheckoutQuery):
    # Здесь можно поставить всякие проверки
    await pre_checkout_query.answer(ok=True)


@payment_router.message(F.successful_payment)
async def process_successful_payment(message: Message):
    # Получаем информацию о платеже
    payment_info = message.successful_payment
    user_id = message.from_user.id

    await set_user_paid(user_id)

    amount = payment_info.total_amount / 100
    currency = payment_info.currency

    thanks_text = (
        f"🎉 **Оплата прошла успешно!**\n\n"
        f"Сумма: {amount} {currency}\n"
        f"Доступ предоставлен на 30 дней. Теперь ты будешь оперативно получать голосовые уведомления!"
    )
    await message.answer(thanks_text, parse_mode="Markdown")
