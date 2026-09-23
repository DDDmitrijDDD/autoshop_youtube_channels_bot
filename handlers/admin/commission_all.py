from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state
from aiogram.types import Message, CallbackQuery
from data.loader import rt, bot
from aiogram import F
from handlers.admin.start import AdminState, del_mes
from utils.db.api.commission import DBcommission
from utils.db.api.users import DBuser
from utils.system.inline_btns import create_markup
from utils.system.adminka import AdminIs


@rt.message(F.text == 'Общая Комиссия', AdminIs(), StateFilter(default_state))
async def mail_message(message: Message, state: FSMContext):
    com = await DBcommission.return_commission()
    markup = await create_markup('inline', [[['Отмена', 'cancel']]])
    await message.answer(f"Комиссия: {com}% \n\nВведите новую комиссию: ", reply_markup=markup)
    await state.set_state(AdminState.commission)


@rt.message(AdminState.commission, AdminIs())
async def markup_all_mail_skip(message: Message, state: FSMContext):
    await DBcommission.update_commission(int(message.text))
    await DBuser.update_commission_all(int(message.text))
    await message.answer(f"Успешно")
    await state.clear()