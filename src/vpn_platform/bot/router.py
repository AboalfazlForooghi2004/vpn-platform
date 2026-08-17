from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import KeyboardButton, Message, ReplyKeyboardMarkup

router = Router(name="customer")

MAIN_MENU = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="خرید اشتراک"), KeyboardButton(text="اشتراک‌های من")],
        [KeyboardButton(text="دریافت کانفیگ Amnezia"), KeyboardButton(text="تمدید")],
        [KeyboardButton(text="آموزش اتصال"), KeyboardButton(text="پشتیبانی")],
    ],
    resize_keyboard=True,
    input_field_placeholder="یک گزینه را انتخاب کنید",
)


@router.message(CommandStart())
async def start(message: Message) -> None:
    await message.answer(
        "به سرویس AmneziaWG خوش آمدید.\nهر اشتراک MVP برای یک دستگاه و یک کانفیگ مستقل است.",
        reply_markup=MAIN_MENU,
    )
