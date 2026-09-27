from aiogram import types, Dispatcher
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.enums import ParseMode
from database import add_transaction, get_treasury_balance, get_user_contribution, add_business_income
from config import BUSINESS_TAX_PERCENT
from keyboards import treasury_menu, back_to_main

class TreasuryStates(StatesGroup):
    waiting_amount = State()
    waiting_comment = State()
    waiting_business_amount = State()

async def start_deposit(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "➕ <b>Пополнение казны</b>\n\nВведи сумму:",
        parse_mode=ParseMode.HTML
    )
    await state.set_state(TreasuryStates.waiting_amount)
    await state.update_data(operation_type="deposit")
    await callback.answer()

async def start_withdraw(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "➖ <b>Снятие из казны</b>\n\nВведи сумму:",
        parse_mode=ParseMode.HTML
    )
    await state.set_state(TreasuryStates.waiting_amount)
    await state.update_data(operation_type="withdraw")
    await callback.answer()

async def start_business_withdraw(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        f"🏢 <b>Снятие с бизнеса ({BUSINESS_TAX_PERCENT}%)</b>\n\n"
        f"Введи сумму снятия с бизнеса:\n"
        f"{BUSINESS_TAX_PERCENT}% пойдёт в отдельную категорию",
        parse_mode=ParseMode.HTML
    )
    await state.set_state(TreasuryStates.waiting_business_amount)
    await callback.answer()

async def process_amount(message: types.Message, state: FSMContext):
    try:
        amount = int(message.text)
        if amount <= 0:
            await message.answer("❌ Сумма должна быть положительной")
            return
    except ValueError:
        await message.answer("❌ Введи число")
        return

    data = await state.get_data()
    operation_type = data.get("operation_type")

    if operation_type == "withdraw":
        balance = get_treasury_balance()
        if amount > balance:
            await message.answer(f"❌ Недостаточно средств в казне! Баланс: {balance:,} ₽")
            await state.clear()
            return

        user_contribution = get_user_contribution(message.from_user.id)
        if amount > user_contribution:
            await message.answer(f"❌ Ты не можешь снять больше, чем у тебя в казне! Твоя доля: {user_contribution:,} ₽")
            await state.clear()
            return

    await state.update_data(amount=amount)
    await message.answer("💬 Введи комментарий (или отправь '-' чтобы пропустить):")
    await state.set_state(TreasuryStates.waiting_comment)

async def process_business_amount(message: types.Message, state: FSMContext):
    try:
        business_amount = int(message.text)
        if business_amount <= 0:
            await message.answer("❌ Сумма должна быть положительной")
            return
    except ValueError:
        await message.answer("❌ Введи число")
        return

    treasury_amount = int(business_amount * BUSINESS_TAX_PERCENT / 100)

    add_business_income(
        message.from_user.id,
        business_amount,
        treasury_amount,
        ""
    )

    await message.answer(
        f"✅ В категорию <b>5% с бизнесов</b> поступило {treasury_amount:,} ₽\n"
        f"({BUSINESS_TAX_PERCENT}% от {business_amount:,} ₽)",
        parse_mode=ParseMode.HTML,
        reply_markup=back_to_main()
    )
    await state.clear()

async def process_comment(message: types.Message, state: FSMContext):
    data = await state.get_data()
    amount = data.get("amount")
    operation_type = data.get("operation_type")
    comment = message.text if message.text != "-" else ""

    add_transaction(message.from_user.id, operation_type, amount, comment)

    emoji = "➕" if operation_type == "deposit" else "➖"
    action = "пополнено" if operation_type == "deposit" else "снято"

    await message.answer(
        f"{emoji} Казна {action} на <b>{amount:,} ₽</b>\n"
        f"💬 Комментарий: {comment or 'нет'}",
        parse_mode=ParseMode.HTML,
        reply_markup=back_to_main()
    )
    await state.clear()

def register_treasury_handlers(dp: Dispatcher):
    dp.callback_query.register(start_deposit, lambda c: c.data == "treasury_deposit")
    dp.callback_query.register(start_withdraw, lambda c: c.data == "treasury_withdraw")
    dp.callback_query.register(start_business_withdraw, lambda c: c.data == "treasury_business")
    dp.message.register(process_amount, TreasuryStates.waiting_amount)
    dp.message.register(process_business_amount, TreasuryStates.waiting_business_amount)
    dp.message.register(process_comment, TreasuryStates.waiting_comment)
