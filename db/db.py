import aiosqlite
from datetime import datetime, timedelta

from config.config import DB_NAME


async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                is_paid INTEGER DEFAULT 0,
                last_payment_date TEXT
            )
        """)
        await db.commit()
    print("База данных успешно инициализирована (Async).")


async def set_user_paid(user_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        await db.execute(
            """
            INSERT INTO users (user_id, is_paid, last_payment_date)
            VALUES (?, 1, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                        is_paid = 1,
                        last_payment_date = ?
        """,
            (user_id, now_str, now_str),
        )
        await db.commit()
    print(f"Пользователь {user_id} совершил оплату в {now_str}.")


async def check_user_payment(user_id: int) -> dict:
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT is_paid, last_payment_date FROM users WHERE user_id = ?", (user_id,))
        row = await cursor.fetchone()

    if row:
        if not bool(row[0]):
            return {"exists": True, "is_paid": False}

        last_payment_date = datetime.strptime(row[1], "%Y-%m-%d %H:%M:%S")
        if datetime.now() <= last_payment_date + timedelta(
            days=30
        ):  # Проверяем, что срок подписки еще не прошел
            return {"exists": True, "is_paid": True}
        else:
            return {"exists": True, "is_paid": False}

    return {"exists": False}
