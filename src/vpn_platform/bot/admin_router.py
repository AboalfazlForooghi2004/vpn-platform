from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from vpn_platform.bot.admin import AdminOnlyFilter

admin_router = Router(name="admin")
admin_router.message.filter(AdminOnlyFilter())


@admin_router.message(Command("admin"))
async def admin_overview(message: Message) -> None:
    """Entry point of the admin panel; the router-level filter gates it."""
    await message.answer(
        "پنل مدیریت فعال است. review رسیدها فعلاً از طریق admin API انجام می‌شود."
    )
