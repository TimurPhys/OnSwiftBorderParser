import asyncio
import logging
from aiogram import Bot
from datetime import datetime, timedelta
from jobs.async_parser import run_async_parser
import config.config as cfg
from db.db import get_all_valid_users_ids, get_user_filters, update_user_last_call_date
from jobs.caller import send_voice_alert

logger = logging.getLogger(__name__)


# --- АСИНХРОННЫЙ ГЛАВНЫЙ ЦИКЛ ПАРСИНГА ---
async def monitoring_loop(category, border_id, bot: Bot):
    while True:
        try:
            print("--- Фоновый запуск проверки ---")
            data = await run_async_parser(category=category, border_id=border_id)
            if data:
                cfg.last_monitoring_date = datetime.now()
                if cfg.last_monitoring_date - cfg.first_monitoring_date >= timedelta(
                    days=1
                ):
                    cfg.first_monitoring_date = datetime.now()
                    cfg.monitoring_counter = 0
                cfg.monitoring_counter += 1
                print("Итоговый словарь собранных данных за месяц успешно получен")
                # На этом моменте получили готовые данные, теперь надо их разослать по пользователям
                found_valid_users_ids = await get_all_valid_users_ids()
                valid_users_ids = list(set(found_valid_users_ids + [cfg.ADMIN_ID]))

                user_filters = await get_user_filters(valid_users_ids)
                print(user_filters)

                for user_id in valid_users_ids:
                    matched_slots = []
                    other_slots = []
                    user_filter = user_filters.get(user_id)

                    # 1. Проходим по ID границ (ключи 1, 2 и т.д.)
                    for b_id, dates_dict in data.items():
                        # Получаем красивое название границы или пишем просто "КПП №..."
                        border_name = cfg.border_names.get(int(b_id))

                        # 2. Проходим по датам внутри этой границы
                        for date_str, slots_list in dates_dict.items():

                            # 3. Проходим по кортежам (время, статус)
                            for time_slot, status in slots_list:
                                if status.strip().lower() == "свободно":
                                    # Формируем красивую строчку для списка

                                    slot_line = f"📍 **{border_name}** | 📅 {date_str} в ⏰ {time_slot}"

                                    is_match = False  # Флаг, подошел ли конкретный слот
                                    if user_filter:
                                        border_match = False
                                        for border_id in user_filter["borders"]:
                                            if int(border_id) == int(b_id):
                                                border_match = True

                                        date_match = False
                                        if user_filter["date_start"] == "any":
                                            date_match = True
                                        else:
                                            try:
                                                # Из строки "05.07.2026" делаем объект даты
                                                current_slot_date = datetime.strptime(
                                                    date_str.strip(), "%d.%m.%Y"
                                                ).date()
                                                if (
                                                    user_filter["date_start"]
                                                    <= current_slot_date
                                                    <= user_filter["date_end"]
                                                ):
                                                    date_match = True
                                            except Exception as e:
                                                print(f"Ошибка проверки даты: {e}")

                                        time_match = False
                                        if user_filter["time"] == "any":
                                            time_match = True
                                        else:
                                            try:
                                                slot_hour = int(time_slot.split(":")[0])
                                                if user_filter[
                                                    "time"
                                                ] == "morning" and (
                                                    6 <= slot_hour < 12
                                                ):
                                                    time_match = True
                                                elif user_filter["time"] == "day" and (
                                                    12 <= slot_hour < 18
                                                ):
                                                    time_match = True
                                                elif user_filter[
                                                    "time"
                                                ] == "night" and (
                                                    slot_hour >= 18 or slot_hour < 6
                                                ):
                                                    time_match = True
                                            except Exception:
                                                pass

                                        # Если все три условия сошлись — этот слот идеален
                                        if border_match and date_match and time_match:
                                            is_match = True

                                    # Сортируем слоты по спискам
                                    if is_match:
                                        matched_slots.append(slot_line)
                                    else:
                                        other_slots.append(slot_line)

                    # Теперь разслылаем по пользователям, если что-то нашли
                    if matched_slots:
                        slots_text = "\n".join(matched_slots)
                        message_text = (
                            f"🔥 <b>НАЙДЕНЫ ИДЕАЛЬНЫЕ СЛОТЫ ПО ФИЛЬТРУ!</b>\n\n"
                            f"{slots_text}\n\n"
                            f"Переходи <a href='https://www.eestipiir.ee/yphis/index.action'>на сайт границы</a> и бронируй!"
                        )
                        await bot.send_message(user_id, message_text, parse_mode="HTML")
                        user_filter = user_filters.get(user_id)
                        number = user_filter.get("number")

                        await send_voice_alert(
                            user_id=user_id,
                            message="This is an automated message. A perfect match for your filters has been found!",
                            voice_to_number=number,
                        )

                    elif other_slots:
                        # Объединяем все найденные слоты через перенос строки
                        slots_text = "\n".join(other_slots)
                        message_text = (
                            f"🔥 <b>НАЙДЕНЫ СВОБОДНЫЕ СЛОТЫ ДЛЯ ЗАПИСИ!</b>\n\n"
                            f"{slots_text}\n\n"
                            f"Переходи <a href='https://www.eestipiir.ee/yphis/index.action'>на сайт границы</a> и бронируй!"
                        )
                        await bot.send_message(user_id, message_text, parse_mode="HTML")
                    else:
                        logger.info(
                            f"Проверка для пользователя {user_id} завершена успешно: Свободных мест нет."
                        )

        except asyncio.CancelledError:
            print("Фоновая задача остановлена пользователем.")
            break
        except Exception as e:
            print(f"Произошла ошибка парсинга {e}")
            await bot.send_message(cfg.ADMIN_ID, f"Произошла ошибка парсинга {e}")

        await asyncio.sleep(300)  # Спим 5 минут
