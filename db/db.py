import aiosqlite
from datetime import datetime

from config.config import DB_NAME


async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                is_superuser INTEGER DEFAULT 0, -- 👈 Флаг суперюзера
                is_trial INTEGER DEFAULT 0,
                is_paid INTEGER DEFAULT 0,  
                has_dlc INTEGER DEFAULT 0,
                last_payment_date TEXT,
                days_left INTEGER DEFAULT NULL,
                has_stopped INTEGER DEFAULT 0,
                last_call_date TEXT DEFAULT NULL
            );
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS user_filters (
                user_id INTEGER PRIMARY KEY,
                borders TEXT NOT NULL,          -- ID границ через запятую, например: "1,2"
                date_start TEXT DEFAULT 'any',  -- Строка "any" или дата в формате "YYYY-MM-DD"
                date_end TEXT DEFAULT 'any',    -- Строка "any" или дата в формате "YYYY-MM-DD"
                time_slot TEXT DEFAULT 'any',   -- "any", "morning", "day", "night"
                number TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE
            );
        """)
        await db.commit()
    print("База данных успешно инициализирована (Async).")


# Начинаем пробный период у пользователя (до этого провека существует ли пользователь в базе)
async def start_trial_subscription(user_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        await db.execute(
            """
            INSERT INTO users (user_id, is_trial, is_paid, has_dlc, last_payment_date, days_left, has_stopped)
            VALUES (?, 1, 0, 0, ?, 7, 0)
            ON CONFLICT(user_id) DO UPDATE SET
                is_trial = 1,
                last_payment_date = excluded.last_payment_date,
                days_left = 7,
                has_stopped = 0
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
            INSERT INTO users (user_id, is_trial, is_paid, has_dlc, last_payment_date, days_left, has_stopped)
            VALUES (?, 0, 1, 0, ?, 30, 0)
            ON CONFLICT(user_id) DO UPDATE SET
                        is_trial = 0,
                        is_paid = 1,
                        has_dlc = 0,
                        last_payment_date = ?,
                        days_left = 30,
                        has_stopped = 0
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
            INSERT INTO users (user_id, is_trial, is_paid, has_dlc, last_payment_date, days_left, has_stopped)
            VALUES (?, 0, 1, 1, ?, 30, 0)
            ON CONFLICT(user_id) DO UPDATE SET
                        is_trial = 0,
                        is_paid = 1,
                        has_dlc = 1,
                        last_payment_date = ?,
                        days_left = 30,
                        has_stopped = 0
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
        db.row_factory = aiosqlite.Row

        async with db.execute(
            "SELECT * FROM users WHERE user_id = ?", (user_id,)
        ) as cursor:
            row = await cursor.fetchone()

            if not row:
                return {"exists": False}

            user_data = dict(row)

            for key in (
                "is_trial",
                "is_paid",
                "has_dlc",
                "has_stopped",
                "is_superuser",
            ):
                if key in user_data:
                    user_data[key] = bool(user_data[key])

            # Добавляем флаг существования и возвращаем
            return {"exists": True, **user_data}


async def get_user_last_call_date(user_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            """
            SELECT last_call_date FROM users WHERE user_id = ?
        """,
            (user_id,),
        )
        row = await cursor.fetchone()
        if row:
            return row[0]
        return None


async def update_user_last_call_date(user_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        await db.execute(
            """
        UPDATE users
            SET last_call_date = ?
        WHERE user_id = ?;
        """,
            (now_str, user_id),
        )
        await db.commit()


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


async def stop_subscription(user_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            """
            UPDATE users
            SET 
                days_left = MAX(0, days_left - CAST(julianday('now') - julianday(last_payment_date) AS INTEGER)),
                has_stopped = 1
            WHERE user_id = ?;
            """,
            (user_id,),
        )
        await db.commit()


async def resume_subscription(user_id):
    async with aiosqlite.connect(DB_NAME) as db:
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        await db.execute(
            """
            UPDATE users
            SET
                has_stopped = 0,
                last_payment_date = ?
            WHERE user_id = ?;
            """,
            (now_str, user_id),
        )
        print(f"Подписка пользователя {user_id} успешно возобновлена")
        await db.commit()


async def get_all_valid_users_ids():
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("""
        SELECT user_id FROM users WHERE (is_trial == 1 OR is_paid == 1 OR is_superuser == 1)
    """)
        rows = await cursor.fetchall()
    return [row[0] for row in rows]


async def save_user_filter(user_id: int, filter: dict):
    async with aiosqlite.connect(DB_NAME) as db:
        # Превращаем список ['1', '2'] в строку "1,2" для хранения в БД
        borders_str = ",".join(map(str, filter["borders"]))

        await db.execute(
            """
        INSERT OR REPLACE INTO user_filters (user_id, borders, date_start, date_end, time_slot, number)
        VALUES (?, ?, ?, ?, ?, ?);
        """,
            (
                user_id,
                borders_str,
                str(filter["date_start"]),
                str(filter["date_end"]),
                filter["time"],
                filter["number"],
            ),
        )

        await db.commit()


async def delete_user_filter(user_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "DELETE FROM user_filters WHERE user_id = ?", (user_id,)
        )
        await db.commit()

        # cursor.rowcount показывает, сколько строк было удалено
        return cursor.rowcount > 0


async def user_has_filters(user_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute(
            "SELECT 1 FROM user_filters WHERE user_id = ? LIMIT 1", (user_id,)
        ) as cursor:
            row = await cursor.fetchone()
            # Вернет True, если запись есть, и False, если row == None
            return row is not None


async def get_user_filters(user_ids) -> dict | None:
    user_filters = {}
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.cursor() as cursor:
            # Включаем Row-фабрику, чтобы обращаться по именам колонок
            cursor.row_factory = aiosqlite.Row

            if len(user_ids) == 1:
                query = "SELECT * FROM user_filters WHERE user_id = ?;"
                await cursor.execute(query, (user_ids[0],))

            # Если проверяем ПАЧКУ пользователей (в цикле мониторинга)
            else:
                placeholders = ", ".join(["?"] * len(user_ids))
                query = f"SELECT * FROM user_filters WHERE user_id IN ({placeholders});"
                await cursor.execute(query, list(user_ids))

            rows = await cursor.fetchall()

            for row in rows:
                u_id = row["user_id"]
                # Обработка границ (парсинг строки в список чисел)
                borders_raw = row["borders"]
                borders = (
                    [int(x) for x in borders_raw.split(",") if x] if borders_raw else []
                )

                d_start = row["date_start"]
                d_end = row["date_end"]

                # Парсинг дат, если они заданы конкретным диапазоном
                if d_start != "any" and d_start is not None:
                    try:
                        d_start = datetime.strptime(d_start, "%Y-%m-%d").date()
                        d_end = datetime.strptime(d_end, "%Y-%m-%d").date()
                    except ValueError:
                        try:
                            d_start = datetime.strptime(d_start, "%d.%m.%Y").date()
                            d_end = datetime.strptime(d_end, "%d.%m.%Y").date()
                        except ValueError:
                            # Фалбэк на случай, если в базе совсем битая дата
                            d_start, d_end = "any", "any"
                user_filters[u_id] = {
                    "borders": borders,
                    "date_start": d_start,
                    "date_end": d_end,
                    "time": row["time_slot"],
                    "number": row["number"],
                }
            return user_filters


async def get_superusers_list() -> list | None:
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("""
            SELECT user_id FROM users WHERE is_superuser = 1
        """)
        rows = await cursor.fetchall()
        if rows:
            return [int(row[0]) for row in rows]
        return None


async def change_superuser_state(user_id, new_state):
    async with aiosqlite.connect(DB_NAME) as db:
        if new_state == 1:
            await db.execute(
                f"""
            INSERT INTO users (user_id, is_superuser)
                VALUES (?, 1)
                ON CONFLICT(user_id) DO UPDATE SET
                        is_superuser = 1
            """,
                (user_id,),
            )

        elif new_state == 0:
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            await db.execute(
                f"""
                        INSERT INTO users (user_id, is_superuser, last_payment_date)
                            VALUES (?, 0, ?)
                            ON CONFLICT(user_id) DO UPDATE SET
                                    is_superuser = 0,
                                    last_payment_date = ?
                        """,
                (user_id, now_str, now_str),
            )

        await db.commit()
