from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message

router = Router()

@router.message(Command('start'))
async def cmd_start(message: Message):
    text = (
        "🎥 <b>YouTube Checker Bot</b>\n\n"
        "Бот для проверки статистики канала и видео на YouTube.\n\n"
        "<b>Команды:</b>\n"
        "/channel <code>@username или ID</code> — статистика канала\n"
        "/video <code>ссылка или ID</code> — статистика видео\n"
        "/history <code>ID видео</code> — динамика просмотров\n"
        "/check <code>ID видео</code> — проверка на признаки бана\n\n"
        "<b>Примеры:</b>\n"
        "/channel @MrBeast\n"
        "/video https://youtube.com/watch?v=VIDEO_ID"
    )
    await message.answer(text, parse_mode='HTML')
