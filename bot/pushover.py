import httpx
import config

PUSHOVER_USER_KEY = config.PUSHOVER_USER_KEY
PUSHOVER_API_TOKEN = config.PUSHOVER_API_TOKEN


async def send_emergency_alert(slot_info: str):
    url = "https://api.pushover.net/1/messages.json"
    data = {
        "token": PUSHOVER_API_TOKEN,
        "user": PUSHOVER_USER_KEY,
        "message": f"🚨 СРОЧНО! НАЙДЕН СЛОТ!\n\nИнфо: {slot_info}",
        "title": "ГРАНИЦА: СВОБОДНОЕ МЕСТО!",
        "sound": "siren",
        "priority": 2,  # Emergency call
        "retry": 30,
        "expire": 3600,
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url=url, data=data)
            if response.status_code == 200:
                print("🚨 Критический алерт в Pushover успешно отправлен!")
            else:
                print(f"Ошибка Pushover: {response.text}")
        except Exception as e:
            print(f"Не удалось связаться с Pushover: {e}")
