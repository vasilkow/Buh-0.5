from aiogram import types, Dispatcher
from aiogram.enums import ParseMode
from aiogram.filters import Command
from database import admin_set_balance, admin_set_user_share, admin_add_to_balance, admin_reset_all, get_treasury_balance, get_user_contribution
from config import ADMIN_IDS
from keyboards import main_menu

def is_admin(user_id):
    return user_id in ADMIN_IDS

async def cmd_setbalance(message: types.Message):
    if not is_admin(message.from_user.id):
        await message.answer("❌ У тебя нет прав администратора")
        return

    args = message.text.split()
    if len(args) != 2:
        await message.answer("Использование: /setbalance <сумма>")
        return

    try:
        new_balance = int(args[1])
        if new_balance < 0:
            await message.answer("❌ Баланс не может быть отрицательным")
            return

        admin_set_balance(message.from_user.id, new_balance)
        await message.answer(
            f"✅ Общий баланс установлен: <b>{new_balance:,} ₽</b>",
            parse_mode=ParseMode.HTML,
            reply_markup=main_menu()
        )
    except ValueError:
        await message.answer("❌ Введи число")

async def cmd_setshare(message: types.Message):
    if not is_admin(message.from_user.id):
        await message.answer("❌ У тебя нет прав администратора")
        return

    args = message.text.split()
    if len(args) != 3:
        await message.answer("Использование: /setshare <user_id> <сумма>")
        return

    try:
        user_id = int(args[1])
        new_share = int(args[2])

        if new_share < 0:
            await message.answer("❌ Доля не может быть отрицательной")
            return

        admin_set_user_share(user_id, new_share)
        await message.answer(
            f"✅ Доля пользователя {user_id} установлена: <b>{new_share:,} ₽</b>",
            parse_mode=ParseMode.HTML,
            reply_markup=main_menu()
        )
    except ValueError:
        await message.answer("❌ Введи числа")

async def cmd_addbalance(message: types.Message):
    if not is_admin(message.from_user.id):
        await message.answer("❌ У тебя нет прав администратора")
        return

    args = message.text.split()
    if len(args) != 2:
        await message.answer("Использование: /addbalance <сумма>")
        return

    try:
        amount = int(args[1])
        if amount <= 0:
            await message.answer("❌ Сумма должна быть положительной")
            return

        new_balance = admin_add_to_balance(message.from_user.id, amount)
        await message.answer(
            f"✅ Добавлено {amount:,} ₽\nНовый баланс: <b>{new_balance:,} ₽</b>",
            parse_mode=ParseMode.HTML,
            reply_markup=main_menu()
        )
    except ValueError:
        await message.answer("❌ Введи число")

async def cmd_reset(message: types.Message):
    if not is_admin(message.from_user.id):
        await message.answer("❌ У тебя нет прав администратора")
        return

    admin_reset_all()
    await message.answer(
        "✅ Все данные сброшены",
        reply_markup=main_menu()
    )

async def cmd_admin(message: types.Message):
    if not is_admin(message.from_user.id):
        await message.answer("❌ У тебя нет прав администратора")
        return

    balance = get_treasury_balance()

    text = (
        "⚙️ <b>Админ-панель</b>\n\n"
        f"💵 Текущий баланс: {balance:,} ₽\n\n"
        "<b>Команды:</b>\n"
        "/setbalance <сумма> — установить общий баланс\n"
        "/setshare <user_id> <сумма> — установить долю пользователя\n"
        "/addbalance <сумма> — добавить к балансу\n"
        "/reset — сбросить все данные"
    )

    await message.answer(text, parse_mode=ParseMode.HTML, reply_markup=main_menu())

def register_admin_handlers(dp: Dispatcher):
    dp.message.register(cmd_admin, Command("admin"))
    dp.message.register(cmd_setbalance, Command("setbalance"))
    dp.message.register(cmd_setshare, Command("setshare"))
    dp.message.register(cmd_addbalance, Command("addbalance"))
    dp.message.register(cmd_reset, Command("reset"))
