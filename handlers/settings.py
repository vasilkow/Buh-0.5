from aiogram import types, Dispatcher
from aiogram.enums import ParseMode
from database import toggle_notifications, get_user
from keyboards import settings_menu

async def toggle_notifications_handler(callback: types.CallbackQuery):
    new_status = toggle_notifications(callback.from_user.id)

    status_text = "ВКЛ" if new_status else "ВЫКЛ"

    kb = settings_menu()
    kb.inline_keyboard[0][0].text = f"🔔 Уведомления: {status_text}"

    await callback.message.edit_text(
        f"✅ Уведомления {status_text}",
        parse_mode=ParseMode.HTML,
        reply_markup=kb
    )
    await callback.answer()

def register_settings_handlers(dp: Dispatcher):
    dp.callback_query.register(toggle_notifications_handler, lambda c: c.data == "toggle_notifications")
