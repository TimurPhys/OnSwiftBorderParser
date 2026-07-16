import asyncio
from vonage import Auth, Vonage
from vonage_voice import CreateCallRequest, Phone, ToPhone

from config.config import VONAGE_APP_ID, VONAGE_PRIVATE_KEY, VONAGE_VIRTUAL_NUMBER

client = Vonage(
    Auth(
        application_id=VONAGE_APP_ID,
        private_key=VONAGE_PRIVATE_KEY,
    )
)


async def send_voice_alert(message, voice_to_number):
    ncco_payload = [
        {
            "action": "talk",
            "text": message,
            "language": "en-US",  # Меняйте код языка, если нужно (en-US, lv-LV и т.д.)
            "style": 0,
        }
    ]

    try:
        response = await asyncio.to_thread(
            client.voice.create_call,
            CreateCallRequest(
                ncco=ncco_payload,
                to=[ToPhone(number=voice_to_number)],
                from_=Phone(number=VONAGE_VIRTUAL_NUMBER),
            ),
        )
        if hasattr(response, "status"):
            if response.status == "started":
                print(f" Успешно: Звонок инициирован. ID: {response.uuid}")
                return {"success": True, "uuid": response.uuid}

            elif response.status in ["rejected", "failed"]:
                # Сюда попадет та самая ошибка CLI правил или блокировка триала
                print(
                    f"❌ Ошибка телефонии: Звонок отклонен сетью. Статус: {response.status}"
                )
                return {
                    "success": False,
                    "error": f"Call rejected by network. Status: {response.status}",
                }

        return {"success": True, "raw_response": response}

    except Exception as e:
        print(f"❌ Непредвиденная ошибка: {e}")
        return {"success": False, "error": str(e)}
