from aiogram.filters import BaseFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
import config.config as cfg
from db.db import get_user_instance


class IsSubscriptionActive(BaseFilter):
    async def __call__(self, callback: CallbackQuery) -> bool:
        user_id = int(callback.from_user.id)
        user = await get_user_instance(user_id)

        if not user:
            return False

        has_stopped = user.get("has_stopped", 0) == 1
        is_superuser = user.get("is_superuser") == 1
        is_active = (user.get("is_paid", 0) == 1) or (user.get("is_trial", 0) == 1)

        if user_id != cfg.ADMIN_ID and not is_superuser:
            return is_active and not has_stopped
        else:
            return True
