from aiohttp import web
from aiogram import Bot
import json
from db.db import just_bought_subscription

async def stripe_webhook(request):
    """Этот метод принимает POST-запросы от Stripe"""
    try:
        # Достаем экземпляр Bot из глобального состояния приложения aiohttp
        bot: Bot = request.app['bot']

        payload = await request.text()
        event = json.loads(payload)

        if event.get('type') == 'checkout.session.completed':
            session = event['data']['object']
            telegram_user_id = session.get('client_reference_id')
            
            if telegram_user_id:
                user_id = int(telegram_user_id)
                
                # Начисляем подписку в базу данных
                # await just_bought_subscription(user_id)
                
                # Сразу отправляем пользователю радостное сообщение в Telegram
                try:
                    await bot.send_message(
                        chat_id=user_id, 
                        text="🎉 **Оплата прошла успешно!**\n\nПодписка активирована на 30 дней. Спасибо, что пользуетесь нашим ботом!"
                    )
                except Exception as tg_err:
                    print(f"Не удалось отправить сообщение юзеру: {tg_err}")

        # Stripe требует, чтобы мы ВСЕГДА возвращали статус 200 OK, 
        # иначе он решит, что наш сервер упал, и начнет слать повторные запросы.
        return web.Response(text='OK', status=200)
        
    except Exception as e:
        print(f"Ошибка при обработке вебхука: {e}")
        return web.Response(text='Error', status=400)