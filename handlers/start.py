from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

router = Router()


@router.message(Command('start'))
async def cmd_start(message: Message):
    text = (
        "🎥 <b>YouTube Checker Bot</b>\n\n"
        "Проверка статистики канала и видео на YouTube.\n\n"
        "<b>Команды:</b>\n"
        "/channel <code>@username или ID</code> — статистика канала\n"
        "/video <code>ссылка или ID</code> — статистика видео\n"
        "/history <code>ID видео</code> — динамика просмотров\n"
        "/check <code>ID видео</code> — быстрая проверка\n"
        "/deepcheck <code>ID</code> <code>ключ1,ключ2</code> — полная проверка\n"
        "/compare <code>ID1,ID2,ID3</code> — сравнение видео\n"
        "/monitor <code>ID видео</code> — ежедневный мониторинг в 9:00\n"
        "/unmonitor <code>ID видео</code> — убрать из мониторинга\n\n"
        "<b>Примеры:</b>\n"
        "/channel @MrBeast\n"
        "/video https://youtube.com/watch?v=dQw4w9WgXcQ\n"
        "/deepcheck dQw4w9WgXcQ minecraft,обзор"
    )
    await message.answer(text, parse_mode='HTML')
