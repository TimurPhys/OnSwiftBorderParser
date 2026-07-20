import aiosqlite
from datetime import datetime

from config.config import DB_NAME


async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                is_trial INTEGER DEFAULT 0,
                is_paid INTEGER DEFAULT 0,  
                has_dlc INTEGER DEFAULT 0,
                last_payment_date TEXT
            )
        """)
        await db.commit()
    print("База данных успешно инициализирована (Async).")


# Начинаем пробный период у пользователя (до этого провека существует ли пользователь в базе)
async def start_trial_subscription(user_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        await db.execute(
            """
            INSERT INTO users (user_id, is_trial, is_paid, has_dlc, last_payment_date)
            VALUES (?, 1, 0, 0, ?)
        """,
            (user_id, now_str),
        )
        await db.commit()
    print(f"Пользователь {user_id} оформил пробный период в {now_str}.")


## Три сценария покупки -
# 1. Просто купить подписку за 5 евро
# 2. Купить полный вариант со звонками за 5+3 = 8 евро
# 3. Докупить возможность получать звонки за 3 евро


# ----- 1. Просто купить подписку за 5 евро -----
async def just_bought_subscription(user_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        await db.execute(
            """
            INSERT INTO users (user_id, is_trial, is_paid, has_dlc, last_payment_date)
            VALUES (?, 0, 1, 0, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                        is_trial = 0,
                        is_paid = 1,
                        has_dlc = 0,
                        last_payment_date = ?
        """,
            (user_id, now_str, now_str),
        )
        await db.commit()
    print(f"Пользователь {user_id} купил подписку в {now_str}.")


# ----- 2. Купить полный вариант со звонками за 5+3 = 8 евро -----
async def bought_full_package(user_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        await db.execute(
            """
            INSERT INTO users (user_id, is_trial, is_paid, has_dlc, last_payment_date)
            VALUES (?, 0, 1, 1, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                        is_trial = 0,
                        is_paid = 1,
                        has_dlc = 1,
                        last_payment_date = ?
        """,
            (user_id, now_str, now_str),
        )
        await db.commit()
    print(f"Пользователь {user_id} купил полную подписку со звонками в {now_str}.")


# ----- 3. Докупить возможность получать звонки за 3 евро -----
async def has_purchased_calls(user_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            """
            UPDATE users
            SET has_dlc = 1
            WHERE user_id = ?
        """,
            (user_id,),
        )
        await db.commit()
    print(f"Пользователь {user_id} докупил возможность получать звонки.")


## 3 сценария проверки
# 1. Оплатил ли человек подписку и может ли он просто получать сообщения
# 2. Действителен ли у человека пробный период
# 3. Есть ли человека возможность получать звонки


# Просто получить объект пользователя (если существует)
async def get_user_instance(user_id: int) -> dict:
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "SELECT is_trial, is_paid, has_dlc, last_payment_date FROM users WHERE user_id = ?",
            (user_id,),
        )
        row = await cursor.fetchone()
        if row is None:
            return {"exists": False}

        return {
            "exists": True,
            "user_id": user_id,
            "is_trial": bool(row[0]),
            "is_paid": bool(row[1]),
            "has_dlc": bool(row[2]),
            "last_payment_date": row[3],
        }


async def get_user_stats() -> dict:
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.cursor() as cursor:
            cursor.row_factory = aiosqlite.Row

            await cursor.execute("""
            SELECT 
                SUM(CASE WHEN is_trial = 1 THEN 1 ELSE 0 END) AS total_trial,
                SUM(CASE WHEN is_paid = 1 THEN 1 ELSE 0 END) AS total_paid,
                SUM(CASE WHEN is_paid = 1 AND has_dlc = 1 THEN 1 ELSE 0 END) AS total_paid_with_dlc
            FROM 
                users;
            """)
            row = await cursor.fetchone()
            trial = row["total_trial"] or 0
            paid = row["total_paid"] or 0
            have_dlc = row["total_paid_with_dlc"] or 0

            return {"trial": trial, "paid": paid, "have_dlc": have_dlc}


async def get_all_valid_users_ids():
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("""
        SELECT user_id FROM users WHERE (is_trial == 1 OR is_paid == 1)
    """)
        row = await cursor.fetchall()
        return row
