from aiogram.filters import BaseFilter
from aiogram.types import TelegramObject

from vpn_platform.config import get_settings


class AdminOnlyFilter(BaseFilter):
    """Fail-closed admin gate: an empty ADMIN_TELEGRAM_IDS allowlist denies everyone."""

    async def __call__(self, event: TelegramObject) -> bool:
        user = getattr(event, "from_user", None)
        if user is None:
            return False
        return user.id in get_settings().admin_ids
