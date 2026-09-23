from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state
from aiogram.types import Message, CallbackQuery
from data.loader import rt, bot
from aiogram import F
from handlers.admin.start import AdminState, del_mes
from utils.db.api.users import DBuser
from utils.system.inline_btns import create_markup
from utils.system.adminka import AdminIs


@rt.message(F.text == 'Комиссия пользователя', AdminIs(), StateFilter(default_state))
async def mail_message(message: Message, state: FSMContext):
    markup = await create_markup('inline', [[['Отмена', 'cancel']]])
    await message.answer(f"Введите id пользователя: ", reply_markup=markup)
    await state.set_state(AdminState.user_id)


@rt.message(AdminState.user_id, AdminIs())
async def markup_all_mail_skip(message: Message, state: FSMContext):
    markup = await create_markup('inline', [[['Отмена', 'cancel']]])
    try:
        com = await DBuser.return_commission(int(message.text))
        await state.update_data(ids=int(message.text))
    except:
        await message.answer(f"Введен неверный айди")
        await state.clear()
        return
    await message.answer(f"Комиссия пользователя {com}\n Введите новую комиссию для пользователя", reply_markup=markup)
    await state.set_state(AdminState.commission_one)


@rt.message(AdminState.commission_one, AdminIs())
async def markup_all_mail_skip(message: Message, state: FSMContext):
    data = await state.get_data()
    await DBuser.update_commission_one_user(data["ids"], int(message.text))
    await message.answer(f"Комиссия пользователя изменена")
    await state.clear()