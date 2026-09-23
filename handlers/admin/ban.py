from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state
from aiogram.types import Message, CallbackQuery
from data.loader import rt, bot
from aiogram import F
from handlers.admin.start import AdminState, del_mes
from utils.db.api.ban import DBban
from utils.db.api.users import DBuser
from utils.system.inline_btns import create_markup
from utils.system.adminka import AdminIs


@rt.message(F.text == 'Бан', AdminIs(), StateFilter(default_state))
async def mail_message(message: Message, state: FSMContext):
    markup = await create_markup('inline', [[['Отмена', 'cancel']]])
    await message.answer(f"Введите id пользователя: ", reply_markup=markup)
    await state.set_state(AdminState.user_id2)


@rt.message(AdminState.user_id2, AdminIs())
async def markup_all_mail_skip(message: Message, state: FSMContext):
    markup = await create_markup('inline', [[["Забанить", "ban"]],
                                            [['Отмена', 'cancel']]])
    try:
        user = await DBuser.return_all_info(int(message.text))
        await state.update_data(ids=int(message.text))
    except:
        await message.answer(f"Введен неверный айди")
        await state.clear()
        return
    await message.answer(f"""Пользователь {user["user_name"]}

Полное имя: {user["full_name"]}
Баланс: {user["balance"]}
Продано каналов: {user["sale"]}
Сумма всех продаж: {user["all_sale"]}
Активных объявлений: {user["announcements"]}
Объявлений на проверке: {user["examination"]}
Куплено каналов: {user["purchases"]}
Комиссия: {user["commission"]}""", reply_markup=markup)


@rt.callback_query(F.data == 'ban')
async def profile2(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await DBban.add_ban(data["ids"])
    await call.message.answer(f"Пользователь забанен")
    await state.clear()