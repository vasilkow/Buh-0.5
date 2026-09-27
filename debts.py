from aiogram import types, Dispatcher
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.enums import ParseMode
from database import add_debt, get_user_debts, close_debt
from keyboards import debts_menu, back_to_main

class DebtStates(StatesGroup):
    waiting_debtor_name = State()
    waiting_amount = State()
    waiting_percent = State()
    waiting_due_date = State()
    waiting_comment = State()

async def show_owed_to_me(callback: types.CallbackQuery):
    debts = get_user_debts(callback.from_user.id)

    if not debts["owed_to_me"]:
        await callback.message.edit_text(
            "📤 <b>Мне должны</b>\n\nНет активных долгов",
            parse_mode=ParseMode.HTML
        )
        await callback.answer()
        return

    text = "📤 <b>Мне должны:</b>\n\n"
    for debt in debts["owed_to_me"]:
        return_amount = debt["amount"] + (debt["amount"] * debt["percent"] / 100)
        text += f"👤 <b>{debt['debtor_name']}</b>\n"
        text += f"   💰 Долг: {debt['amount']:,} ₽\n"
        if debt["percent"] > 0:
            text += f"   📈 Процент: {debt['percent']}%\n"
            text += f"   💵 Вернёт: {return_amount:,.0f} ₽\n"
        if debt["due_date"]:
            text += f"   📅 Срок: {debt['due_date']}\n"
        if debt["comment"]:
            text += f"   💬 {debt['comment']}\n"
        text += f"   🆔 ID: {debt['id']}\n\n"

    await callback.message.edit_text(text, parse_mode=ParseMode.HTML)
    await callback.answer()

async def start_add_debt(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "➕ <b>Добавить долг</b>\n\n"
        "Введи имя должника:",
        parse_mode=ParseMode.HTML
    )
    await state.set_state(DebtStates.waiting_debtor_name)
    await callback.answer()

async def process_debtor_name(message: types.Message, state: FSMContext):
    debtor_name = message.text.strip()
    if len(debtor_name) < 2:
        await message.answer("❌ Имя должно содержать минимум 2 символа")
        return

    await state.update_data(debtor_name=debtor_name)
    await message.answer("💰 Введи сумму долга:")
    await state.set_state(DebtStates.waiting_amount)

async def process_amount(message: types.Message, state: FSMContext):
    try:
        amount = int(message.text)
        if amount <= 0:
            await message.answer("❌ Сумма должна быть положительной")
            return
        await state.update_data(amount=amount)
        await message.answer("📈 Введи процент (или 0 если без процентов):")
        await state.set_state(DebtStates.waiting_percent)
    except ValueError:
        await message.answer("❌ Введи число")

async def process_percent(message: types.Message, state: FSMContext):
    try:
        percent = int(message.text)
        if percent < 0:
            await message.answer("❌ Процент не может быть отрицательным")
            return
        await state.update_data(percent=percent)
        await message.answer("📅 Введи срок возврата (ДД.ММ.ГГГГ) или '-' чтобы пропустить:")
        await state.set_state(DebtStates.waiting_due_date)
    except ValueError:
        await message.answer("❌ Введи число")

async def process_due_date(message: types.Message, state: FSMContext):
    due_date = message.text if message.text != "-" else None
    await state.update_data(due_date=due_date)
    await message.answer("💬 Введи комментарий (или '-' чтобы пропустить):")
    await state.set_state(DebtStates.waiting_comment)

async def process_comment(message: types.Message, state: FSMContext):
    data = await state.get_data()
    comment = message.text if message.text != "-" else ""

    add_debt(
        creditor_id=message.from_user.id,
        debtor_name=data["debtor_name"],
        amount=data["amount"],
        percent=data["percent"],
        due_date=data["due_date"],
        comment=comment
    )

    return_amount = data["amount"] + (data["amount"] * data["percent"] / 100)

    await message.answer(
        f"✅ Долг добавлен!\n\n"
        f"👤 Должник: {data['debtor_name']}\n"
        f"💰 Сумма: {data['amount']:,} ₽\n"
        f"📈 Процент: {data['percent']}%\n"
        f"💵 Вернёт: {return_amount:,.0f} ₽\n"
        f"📅 Срок: {data['due_date'] or 'не указан'}\n"
        f"💬 Комментарий: {comment or 'нет'}",
        parse_mode=ParseMode.HTML,
        reply_markup=back_to_main()
    )
    await state.clear()

def register_debts_handlers(dp: Dispatcher):
    dp.callback_query.register(show_owed_to_me, lambda c: c.data == "debts_owed_to_me")
    dp.callback_query.register(start_add_debt, lambda c: c.data == "debts_add")
    dp.message.register(process_debtor_name, DebtStates.waiting_debtor_name)
    dp.message.register(process_amount, DebtStates.waiting_amount)
    dp.message.register(process_percent, DebtStates.waiting_percent)
    dp.message.register(process_due_date, DebtStates.waiting_due_date)
    dp.message.register(process_comment, DebtStates.waiting_comment)
