import asyncio

from aiogram import Bot

from datetime import datetime, timedelta

from jobs.async_parser import run_async_parser
from jobs.pushover import send_emergency_alert

from config.config import *

# --- АСИНХРОННЫЙ ГЛАВНЫЙ ЦИКЛ ПАРСИНГА ---
async def monitoring_loop(category, border_id, bot: Bot):
    global monitoring_counter, last_monitoring_date, first_monitoring_date, border_names
    while True:
        try:
            print("--- Фоновый запуск проверки ---")
            data = await run_async_parser(category=category, border_id=border_id)
            if data:
                last_monitoring_date = datetime.now()
                if last_monitoring_date - first_monitoring_date >= timedelta(days=1):
                    first_monitoring_date = datetime.now()
                    monitoring_counter = 0
                monitoring_counter += 1
                print(f"Итоговый словарь собранных данных за месяц:\n{data}")
                # await bot.send_message(ADMIN_ID, "Были найдены новые данные!")
                matched_slots = []
                other_slots = []

                # 1. Проходим по ID границ (ключи 1, 2 и т.д.)
                for b_id, dates_dict in data.items():
                    # Получаем красивое название границы или пишем просто "КПП №..."
                    border_name = border_names.get(int(b_id))

                    # 2. Проходим по датам внутри этой границы
                    for date_str, slots_list in dates_dict.items():

                        # 3. Проходим по кортежам (время, статус)
                        for time_slot, status in slots_list:
                            if status.strip().lower() == "свободно":
                                # Формируем красивую строчку для списка

                                slot_line = f"📍 **{border_name}** | 📅 {date_str} в ⏰ {time_slot}"

                                is_match = False  # Флаг, подошел ли конкретный слот
                                if ADMIN_ID in USER_FILTERS.keys():
                                    user_pref = USER_FILTERS[ADMIN_ID]

                                    border_match = False
                                    for border_id in user_pref["borders"]:
                                        if int(border_id) == int(b_id):
                                            border_match = True

                                    date_match = False
                                    if user_pref["date_start"] == "any":
                                        date_match = True
                                    else:
                                        try:
                                            # Из строки "05.07.2026" делаем объект даты
                                            current_slot_date = datetime.strptime(
                                                date_str.strip(), "%d.%m.%Y"
                                            ).date()
                                            if (
                                                user_pref["date_start"]
                                                <= current_slot_date
                                                <= user_pref["date_end"]
                                            ):
                                                date_match = True
                                        except Exception as e:
                                            print(f"Ошибка проверки даты: {e}")

                                    time_match = False
                                    if user_pref["time"] == "any":
                                        time_match = True
                                    else:
                                        try:
                                            slot_hour = int(time_slot.split(":")[0])
                                            if user_pref["time"] == "morning" and (
                                                6 <= slot_hour < 12
                                            ):
                                                time_match = True
                                            elif user_pref["time"] == "day" and (
                                                12 <= slot_hour < 18
                                            ):
                                                time_match = True
                                            elif user_pref["time"] == "night" and (
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

                if matched_slots:
                    slots_text = "\n".join(matched_slots)
                    message_text = (
                        f"🔥 <b>НАЙДЕНЫ ИДЕАЛЬНЫЕ СЛОТЫ ПО ФИЛЬТРУ!</b>\n\n"
                        f"{slots_text}\n\n"
                        f"Переходи <a href='https://www.eestipiir.ee/yphis/index.action'>на сайт границы</a> и бронируй!"
                    )
                    await bot.send_message(ADMIN_ID, message_text, parse_mode="HTML")
                    await send_emergency_alert(
                        slot_info=matched_slots[0].replace("**", "")
                    )

                elif other_slots:
                    # Объединяем все найденные слоты через перенос строки
                    slots_text = "\n".join(other_slots)
                    message_text = (
                        f"🔥 <b>НАЙДЕНЫ СВОБОДНЫЕ СЛОТЫ ДЛЯ ЗАПИСИ!</b>\n\n"
                        f"{slots_text}\n\n"
                        f"Переходи <a href='https://www.eestipiir.ee/yphis/index.action'>на сайт границы</a> и бронируй!"
                    )
                    await bot.send_message(ADMIN_ID, message_text, parse_mode="HTML")
                else:
                    print("Проверка завершена успешно: Свободных мест нет.")

        except asyncio.CancelledError:
            print("Фоновая задача остановлена пользователем.")
            break
        except Exception as e:
            print(f"Произошла ошибка парсинга {e}")
            await bot.send_message(ADMIN_ID, f"Произошла ошибка парсинга {e}")

        await asyncio.sleep(300)  # Спим 5 минут
