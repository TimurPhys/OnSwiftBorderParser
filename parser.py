import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import time


class BorderParser:
    def __init__(self):
        self.session = requests.Session()
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)...",
            "Referer": "www.eestipiir.ee",
        }
        self.init_session()

    def init_session(self):
        """Инициализируем (или обновляем) сессию, зайдя на главную/страницу формы"""
        print("Начинаем инициализацию сессии...")
        # Заходим на страницу, которая предшествует запросу слотов
        steps = [
            ("https://www.eestipiir.ee/yphis/preReserveSelectVehicle.action", None),
            (
                "https://www.eestipiir.ee/yphis/preReserveSelectWaitingArea.action",
                {
                    "placeInQueue.id": "",
                    "placeInQueue.version": "",
                    "placeInQueue.vehicleInQueue.vehicleCategory.name": "B",
                },
            ),
            (
                "https://www.eestipiir.ee/yphis/preReserveSelectQueueType.action",
                {
                    "placeInQueue.id": "",
                    "placeInQueue.version": "",
                    "placeInQueue.borderCrossingPoint.id": 3,
                },
            ),
            (
                "https://www.eestipiir.ee/yphis/preReserveSelectQueueType.action",
                {
                    "placeInQueue.id": "",
                    "placeInQueue.version": "",
                    "queueType": 1,
                },
            ),
        ]
        try:
            for url, payload in steps:
                if payload is None:
                    response = self.session.get(url, headers=self.headers, timeout=15)
                else:
                    response = self.session.post(
                        url, payload, headers=self.headers, timeout=10
                    )

                response.raise_for_status()

            print("🎉 Сессия успешно инициализирована! Все шаги пройдены.")
            return True
        except Exception as e:
            print(f"❌ Ошибка при инициализации сессии: {e}")
            return False

    def get_slots(self, string_date, counter):
        """Делает запрос за конкретную дату"""
        url = "https://www.eestipiir.ee/yphis/findOpenTimeslot.action"
        params = {"preferredDate": string_date, "_": str(counter)}

        response = self.session.get(
            url, params=params, headers=self.headers, timeout=10
        )
        return response


# def session_parser():
#     while True:
#         parser = BorderParser()  # Каждый раз создаем новую сессию при входе
#         try:
#             print(
#                 f"\n--- Новый запуск проверки: {datetime.now().strftime('%H:%M:%S')} ---"
#             )

#             # СБРАСЫВАЕМ значения в начале каждой 5-минутной проверки
#             current_date = datetime.now()
#             base_counter = 1782292979566

#             monthly_data = {}  # Сюда соберем данные за все 30 дней

#             for i in range(0, 31, 4):  # Заглядываем на месяц вперед с сегодняшнего дня
#                 # Каждая итерация (новая дата) увеличивает счетчик на 1
#                 print(i)

#                 base_counter = base_counter + i
#                 current_date = current_date + timedelta(days=4)

#                 try:
#                     response = parser.get_slots(
#                         current_date.strftime("%d.%m.%Y"), base_counter
#                     )
#                     soup = BeautifulSoup(response.text, "html.parser")
#                     day_data = parse_soup(soup)  # Твоя функция парсинга
#                     if len(day_data) == 0:
#                         raise Exception("Нет данных")

#                     monthly_data.update(day_data)
#                 except Exception as e:
#                     print(e)
#                     print("Пробуем зайти заново")
#                     parser.init_session()
#                     continue

#                 time.sleep(1.5)  # Пауза между запросами дат, чтобы не злить сервер

#         except Exception as err:
#             # Если произошла любая критическая ошибка — шлем уведомление в ТГ, но НЕ выключаем скрипт
#             print(f"Критическая ошибка: {err}")

#             # На всякий случай пересоздаем объект парсера, чтобы сбросить куки
#             parser = BorderParser()

#         print(f"Окончательные данные: {monthly_data}")
#         print("Проверка окончена. Засыпаю на 5 минут.")
#         time.sleep(300)
