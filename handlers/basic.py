from aiogram import types, Dispatcher
from aiogram.filters import CommandStart
from aiogram.enums import ParseMode
from database import get_user, create_user, get_treasury_balance, get_user_contribution, get_transactions, get_user_stats, get_all_users_balance, get_total_business_income
from keyboards import main_menu, treasury_menu, debts_menu, settings_menu, back_to_main

async def cmd_start(message: types.Message):
    create_user(message.from_user.id, message.from_user.username or "User")
    await message.answer(
        "💼 <b>Добро пожаловать в Казну!</b>\n\n"
        "Этот бот ведёт бухгалтерию вашей казны.\n\n"
        "Используй кнопки ниже для навигации 👇",
        parse_mode=ParseMode.HTML,
        reply_markup=main_menu()
    )

async def cmd_treasury(message: types.Message):
    balance = get_treasury_balance()
    contribution = get_user_contribution(message.from_user.id)
    business_income = get_total_business_income()

    if balance > 0:
        share_percent = (contribution / balance) * 100
    else:
        share_percent = 0

    text = (
        "💰 <b>Казна</b>\n\n"
        f"💵 <b>Общий баланс:</b> {balance:,} ₽\n"
        f"👤 <b>Твоя доля:</b> {contribution:,} ₽ ({share_percent:.1f}%)\n"
        f"🏢 <b>5% с бизнесов:</b> {business_income:,} ₽\n\n"
        "Выбери действие:"
    )

    await message.answer(text, parse_mode=ParseMode.HTML, reply_markup=treasury_menu())

async def cmd_my_stats(message: types.Message):
    stats = get_user_stats(message.from_user.id)
    contribution = get_user_contribution(message.from_user.id)

    text = (
        "📊 <b>Твоя статистика</b>\n\n"
        f"💰 Пополнил: {stats['deposits']:,} ₽\n"
        f"💸 Снял: {stats['withdraws']:,} ₽\n"
        f"🔄 Общий оборот: {stats['turnover']:,} ₽\n"
        f"📝 Операций: {stats['operations']}\n"
        f"💼 Сейчас в казне: {contribution:,} ₽"
    )

    await message.answer(text, parse_mode=ParseMode.HTML, reply_markup=main_menu())

async def cmd_history(message: types.Message):
    transactions = get_transactions(10)

    if not transactions:
        await message.answer("📜 История пуста", reply_markup=main_menu())
        return

    text = "📜 <b>Последние 10 операций:</b>\n\n"
    for t in transactions:
        emoji = "➕" if t["type"] == "deposit" else "➖"
        text += f"{emoji} <b>{t['username']}</b>: {t['amount']:,} ₽\n"
        if t["comment"]:
            text += f"   💬 {t['comment']}\n"
        text += f"   📅 {t['date'][:16]}\n\n"

    await message.answer(text, parse_mode=ParseMode.HTML, reply_markup=main_menu())

async def cmd_all_users(message: types.Message):
    stats = get_all_users_balance()

    if not stats:
        await message.answer("👥 Пока нет участников", reply_markup=main_menu())
        return

    text = "👥 <b>Все участники:</b>\n\n"
    for s in stats:
        balance = max(0, s["balance"])
        text += f"👤 <b>{s['username']}</b>\n"
        text += f"   💼 В казне: {balance:,} ₽\n\n"

    await message.answer(text, parse_mode=ParseMode.HTML, reply_markup=main_menu())

async def cmd_debts(message: types.Message):
    await message.answer(
        "💳 <b>Долги</b>\n\nВыбери действие:",
        parse_mode=ParseMode.HTML,
        reply_markup=debts_menu()
    )

async def cmd_settings(message: types.Message):
    user = get_user(message.from_user.id)
    status = "ВКЛ" if user and user["notifications_enabled"] else "ВЫКЛ"

    kb = settings_menu()
    kb.inline_keyboard[0][0].text = f"🔔 Уведомления: {status}"

    await message.answer(
        "⚙️ <b>Настройки</b>\n\nВыбери действие:",
        parse_mode=ParseMode.HTML,
        reply_markup=kb
    )

async def handle_back(message: types.Message):
    await message.answer("🏠 Главное меню", reply_markup=main_menu())

def register_basic_handlers(dp: Dispatcher):
    dp.message.register(cmd_start, CommandStart())
    dp.message.register(cmd_treasury, lambda m: m.text == "💰 Казна")
    dp.message.register(cmd_my_stats, lambda m: m.text == "📊 Моя статистика")
    dp.message.register(cmd_history, lambda m: m.text == "📜 История")
    dp.message.register(cmd_all_users, lambda m: m.text == "👥 Все участники")
    dp.message.register(cmd_debts, lambda m: m.text == "💳 Долги")
    dp.message.register(cmd_settings, lambda m: m.text == "⚙️ Настройки")
    dp.message.register(handle_back, lambda m: m.text == "◀️ Назад")
