import aiosqlite
import asyncio
from aiogram import Bot

from config.config import DB_NAME

async def check_and_expire_subscriptions(bot: Bot):
    while True:
        try:
            async with aiosqlite.connect(DB_NAME) as db:
                # Найти всех оплаченных, у кого прошло > 30 дней
                cursor = await db.execute("""
                    SELECT user_id, is_trial, is_paid, days_left
                    FROM users 
                    WHERE (is_paid = 1 OR is_trial = 1 AND has_stopped = 0)
                        AND datetime(last_payment_date, '+' || days_left || ' days') < datetime('now')
                """)
                expired_users = await cursor.fetchall()
                for user in expired_users:
                    user_id = user[0]
                    is_trial = bool(user[1])
                    is_paid = bool(user[2])
                    try:
                        if is_paid:
                            await bot.send_message(
                                chat_id=user_id,
                                text="⚠️ **Ваша подписка истекла!**\n\n Продлите её в меню бота, чтобы продолжить получать уведомления.",
                            )
                            print(
                                f"Уведомление об окончании подписки отправлено пользователю {user_id}"
                            )
                        if is_trial:
                            await bot.send_message(
                                chat_id=user_id,
                                text="⚠️ **Ваша пробная подписка истекла!**\n\n Купите подписку, чтобы продолжить получать уведомления.",
                            )
                            print(
                                f"Уведомление об окончании подписки отправлено пользователю {user_id}"
                            )
                    except Exception as e:
                        print(
                            f"Не удалось отправить сообщение пользователю {user_id}: {e}"
                        )

                if expired_users:
                    user_ids = [user[0] for user in expired_users]
                    placeholders = ",".join("?" for _ in user_ids)

                    await db.execute(
                        f"""
                        UPDATE users 
                        SET is_trial = 0, is_paid = 0, has_dlc = 0, days_left = 0
                        WHERE user_id IN ({placeholders})
                    """,
                        user_ids,
                    )

                    await db.commit()
                    print(
                        f"Статусы подписок для {len(user_ids)} пользователей успешно обновлены в БД."
                    )

                await db.commit()

        except Exception as e:
            print(f"Ошибка в работе воркера подписок: {e}")

        # Засыпаем на час
        await asyncio.sleep(3600)
