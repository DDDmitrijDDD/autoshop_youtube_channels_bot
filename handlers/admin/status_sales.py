from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state
from aiogram.types import Message, CallbackQuery
from data.loader import rt, bot
from aiogram import F
from handlers.admin.start import AdminState, del_mes
from utils.db.api.commission import DBcommission
from utils.db.api.sales import DBsales
from utils.system.inline_btns import create_markup
from utils.system.adminka import AdminIs


@rt.message(F.text == 'Продажи on/off', AdminIs(), StateFilter(default_state))
async def mail_message(message: Message, state: FSMContext):
    sales = await DBsales.return_sales()
    if sales == 1:
        markup = await create_markup('inline', [[['Выключить', 'off']]])
        await message.answer(f"Продажи включены", reply_markup=markup)
    else:
        markup = await create_markup('inline', [[['Включить', 'on']]])
        await message.answer(f"Продажи выключены", reply_markup=markup)


@rt.callback_query(AdminIs(), F.data == 'on')
async def cancel_callback(call: CallbackQuery, state: FSMContext):
    await DBsales.sales_on()
    await call.message.answer(f"Продажи включены")
    await state.clear()


@rt.callback_query(AdminIs(), F.data == 'off')
async def cancel_callback(call: CallbackQuery, state: FSMContext):
    await DBsales.sales_off()
    await call.message.answer(f"Продажи выключены")
    await state.clear()