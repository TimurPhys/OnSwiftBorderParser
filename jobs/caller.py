import asyncio
import logging
from datetime import datetime, timedelta
from vonage import Auth, Vonage
from vonage_voice import CreateCallRequest, Phone, ToPhone
from db.db import get_user_last_call_date, update_user_last_call_date
import config.config as cfg

logger = logging.getLogger(__name__)

client = Vonage(
    Auth(
        application_id=cfg.VONAGE_APP_ID,
        private_key=cfg.VONAGE_PRIVATE_KEY,
    )
)


async def send_voice_alert(user_id, message, voice_to_number):
    last_call_date = await get_user_last_call_date(user_id)

    if last_call_date is not None:
        last_call_date_dt = last_call_date.strptime("%Y-%m-%d %H:%M:%S")
        if datetime.now() >= last_call_date_dt + timedelta(
            hours=cfg.INTERVAL_BETWEEN_CALLS
        ):  # Можно сделать звонок, прошло 2 часа
            await update_user_last_call_date(user_id)
            await send_call(
                message=message,
                number=voice_to_number,
            )
        else:
            logging.info(
                f"С прошлого звонка еще не прошло {cfg.INTERVAL_BETWEEN_CALLS} часа"
            )
            return "INTERVAL_NOT_REACHED"
    else:
        await send_call(
            message=message,
            number=voice_to_number,
        )
    if user_id != cfg.ADMIN_ID:
        await update_user_last_call_date(user_id)
    else:
        logging.info("Производим звонок админу!!!")


async def send_call(message, number):
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
                to=[ToPhone(number=number)],
                from_=Phone(number=cfg.VONAGE_VIRTUAL_NUMBER),
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
