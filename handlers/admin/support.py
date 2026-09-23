from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state
from aiogram.types import Message, CallbackQuery
from data.loader import rt, bot
from aiogram import F
from handlers.admin.start import AdminState, del_mes
from utils.db.api.support import DBsupport
from utils.system.inline_btns import create_markup
from utils.system.adminka import AdminIs


@rt.message(F.text == 'Поддержка', AdminIs(), StateFilter(default_state))
async def mail_message(message: Message, state: FSMContext):
    url = await DBsupport.return_support()
    markup = await create_markup('inline', [[['Отмена', 'cancel']]])
    await message.answer(f"Поддержка: {url}\n\nВведите ссылку для смены", reply_markup=markup)
    await state.set_state(AdminState.support)


@rt.message(AdminState.support, AdminIs())
async def markup_all_mail_skip(message: Message, state: FSMContext):
    await DBsupport.update_support(message.text)
    await message.answer(f"Успешно")
    await state.clear()