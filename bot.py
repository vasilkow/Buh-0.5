from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from config import BOT_TOKEN, ADMIN_IDS
from database import init_db
from handlers.basic import register_basic_handlers
from handlers.treasury import register_treasury_handlers
from handlers.debts import register_debts_handlers
from handlers.settings import register_settings_handlers
from handlers.admin import register_admin_handlers

async def main():
    init_db()
    
    bot = Bot(token=BOT_TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    
    register_basic_handlers(dp)
    register_treasury_handlers(dp)
    register_debts_handlers(dp)
    register_settings_handlers(dp)
    register_admin_handlers(dp)
    
    print("🚀 Бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
