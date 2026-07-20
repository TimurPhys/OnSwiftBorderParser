import logging
import json

from aiohttp import web
from aiogram import Bot
from db.db import just_bought_subscription

logger = logging.getLogger(__name__)

async def stripe_webhook(request):
    """Этот метод принимает POST-запросы от Stripe"""

    # --- 1. ЗАЩИТА ОТ ДЕСЕРИАЛИЗАЦИИ И СЫРЫХ ДАННЫХ ---
    try:
        payload = await request.text()
        event = json.loads(payload)
    except (json.JSONDecodeError, TypeError) as json_err:
        logger.error(f"❌ Критический сбой: Stripe прислал невалидный JSON: {json_err}")
        # Возвращаем 400, чтобы не тратить ресурсы на обработку каши
        return web.Response(text='Invalid JSON', status=400)
    
    try:
        # Достаем бота из состояния aiohttp
        bot: Bot = request.app['bot']

        if event.get('type') == 'checkout.session.completed':
            session = event['data']['object']
            
            # Безопасное извлечение reference_id (защита от None/отсутствия поля)
            telegram_user_id = session.get('client_reference_id')
            
            if not telegram_user_id:
                logger.warning("⚠️ Передан платеж без client_reference_id. Пропускаем.")
                return web.Response(text='No user_id provided', status=200)

            # --- 2. ЗАЩИТА ОТ ОШИБОК ПРИВЕДЕНИЯ ТИПОВ ---
            try:
                user_id = int(telegram_user_id)
            except ValueError:
                logger.error(f"❌ Ошибка: client_reference_id '{telegram_user_id}' невозможно превратить в int.")
                return web.Response(text='Invalid user_id type', status=200)

            # --- 3. ЗАЩИТА ПРИ РАБОТЕ С БАЗОЙ ДАННЫХ (SQLite) ---
            try:
                await just_bought_subscription(user_id)
                logger.info(f"✅ База обновлена: подписка начислена юзеру {user_id}")
            except Exception as db_err:
                logger.error(f"❌ КРИТИЧЕСКАЯ ОШИБКА БД для юзера {user_id}: {db_err}")
                
                # ВНИМАНИЕ: Если база легла, мы возвращаем 500 ошибку!
                # Зачем? Чтобы Stripe понял, что у нас сбой, и ПОВТОРИЛ этот запрос позже (через час).
                # Иначе деньги с юзера спишутся, а подписку он не получит никогда.
                return web.Response(text='Database Error', status=500)

            # --- 4. ЗАЩИТА ОТ БЛОКИРОВОК И ОШИБОК TELEGRAM API ---
            try:
                await bot.send_message(
                    chat_id=user_id, 
                    text="🎉 **Оплата прошла успешно!**\n\nПодписка активирована на 30 дней. Спасибо, что пользуетесь нашим ботом!"
                )
                logger.info(f"✉️ Сообщение об успешной оплате отправлено юзеру {user_id}")
            except Exception as tg_err:
                # Если юзер заблокировал бота сразу после оплаты, база-то уже обновилась, 
                # поэтому глушим ошибку и не ломаем ответ для Stripe.
                logger.warning(f"⚠️ Не удалось отправить сообщение в ТГ юзеру {user_id}: {tg_err}")

        # Если тип события не checkout.session.completed (например, Stripe прислал отчет о другом действии)
        return web.Response(text='OK', status=200)
        
    except Exception as global_err:
        # Глобальный перехватчик на случай форс-мажора
        logger.critical(f"💥 Непредвиденная глобальная ошибка вебхука: {global_err}")
        return web.Response(text='Internal Server Error', status=500)
        
    except Exception as e:
        print(f"Ошибка при обработке вебхука: {e}")
        return web.Response(text='Error', status=400)