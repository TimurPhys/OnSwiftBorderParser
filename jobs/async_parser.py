import httpx
from datetime import datetime, timedelta
import asyncio
from bs4 import BeautifulSoup


class AsyncBorderParser:
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)...",
            "Referer": "www.eestipiir.ee",
        }
        self.client = httpx.AsyncClient(headers=self.headers, timeout=15.0)
        # self.init_session()

    async def init_session(self, category="B", border_id=3):
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
                    "placeInQueue.vehicleInQueue.vehicleCategory.name": category,
                },
            ),
            (
                "https://www.eestipiir.ee/yphis/preReserveSelectQueueType.action",
                {
                    "placeInQueue.id": "",
                    "placeInQueue.version": "",
                    "placeInQueue.borderCrossingPoint.id": str(border_id),
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
                    res = await self.client.get(url=url, headers=self.headers)
                else:
                    res = await self.client.post(
                        url=url, data=payload, headers=self.headers
                    )

                res.raise_for_status()
            return True
        except Exception as e:
            print(f"❌ Ошибка при инициализации сессии: {e}")
            return False

    async def get_slots(self, string_date, counter):
        """Делает запрос за конкретную дату"""
        url = "https://www.eestipiir.ee/yphis/findOpenTimeslot.action"
        params = {"preferredDate": string_date, "_": str(counter)}

        return await self.client.get(url, params=params)


async def run_async_parser(category="B", border_id=3):
    print("🚀 Запуск изолированного асинхронного парсера...")
    monthly_data = {}

    # 1. Создаем объект парсера
    parser = AsyncBorderParser()

    # 2. Тестируем цепочку авторизации/инициализации сессии
    # Передаем категорию "B" и КПП 3 (Нарва), как ты настроил
    if border_id != "ALL":
        init_success = await parser.init_session(category=category, border_id=border_id)
        if not init_success:
            print(
                "❌ Тест провален: Не удалось инициализировать сессию (ошибка на шагах POST)."
            )
            return
        print("✅ Сессия успешно создана. Начинаем пробный обход дат за месяц...")

        # Сделаем тестовый проход по тем же шагам (раз в 4 дня)
        data = await send_request(parser)
        monthly_data.update({border_id: data})
    else:
        for i in range(1, 4):
            init_success = await parser.init_session(category=category, border_id=i)
            if not init_success:
                print(
                    "❌ Тест провален: Не удалось инициализировать сессию (ошибка на шагах POST)."
                )
                return
            print("✅ Сессия успешно создана. Начинаем пробный обход дат за месяц...")

            data = await send_request(parser)
            monthly_data.update({i: data})

    # Закрываем клиент, чтобы не висел в памяти (опционально для httpx)
    await parser.client.aclose()

    return monthly_data


async def send_request(parser: AsyncBorderParser):
    start_date = datetime.now()
    base_counter = 1782292979566
    monthly_data = {}

    for i in range(0, 31, 4):
        current_date = start_date + timedelta(days=i)
        date_str = current_date.strftime("%d.%m.%Y")
        current_counter = base_counter + i

        print(
            f"🔎 Отправка асинхронного запроса на {date_str} (counter: {current_counter})..."
        )

        try:
            # Вызываем твой асинхронный метод
            response = await parser.get_slots(date_str, current_counter)

            # Передаем HTML в BeautifulSoup и парсим
            soup = BeautifulSoup(response.text, "html.parser")
            day_data = parse_soup(soup)  # Твоя функция парсинга HTML

            if day_data:
                print(f"   ↳ Данные найдены!")
                monthly_data.update(day_data)
            else:
                print(f"   ↳ Свободных мест нет (или вернулась стандартная заглушка)")

        except Exception as e:
            print(f"❌ Ошибка при обработке даты {date_str}: {e}")

        # Небольшая пауза между запросами, чтобы бэкенд не ругался
        await asyncio.sleep(1.5)

    print("\n🏁 Тест завершен!")
    return monthly_data


def parse_soup(soup):
    slots = soup.find_all("div", id="timeslot")
    data = {}

    for slot in slots:
        # Безопасно достаем "data-time" (на случай, если у какого-то div его не окажется)
        data_time_attr = slot.get("data-time")
        if not data_time_attr:
            continue

        # Разбиваем строку "19.07.2026 23:00" на дату и время
        slot_date, slot_time = data_time_attr.split(" ")
        slot_text = slot.get_text(strip=True)

        # Классифицируем статус
        if slot_text in ["Забронировано", "Недоступно", "Not available", "Full"]:
            status = "Занято"
        else:
            status = "Свободно"

        # Трюк: если даты еще нет в словаре, создаем пустой список.
        # Если есть — просто берем существующий список и добавляем туда кортеж (время, статус)
        data.setdefault(slot_date, [])
        data[slot_date].append((slot_time, status))

    return data
