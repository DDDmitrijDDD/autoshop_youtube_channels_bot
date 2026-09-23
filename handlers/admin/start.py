import configparser
from aiogram import types, F
from aiogram.filters import CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup, default_state
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, ReplyKeyboardMarkup
from data.loader import rt, bot
from utils.db.api.users import DBuser
from utils.system.inline_btns import create_markup
from utils.system.adminka import AdminIs


class AdminState(StatesGroup):
    user_id2 = State()
    data_channel = State()
    info_channel = State()
    edit_info = State()
    data_channel_update = State()
    viewing_page = State()
    comment2 = State()
    commission_one = State()
    comment = State()
    user_id = State()
    commission = State()
    support_url = State()
    support = State()
    canal = State()
    bal_rek = State()
    rek = State()
    rek_input = State()
    rek_change = State()
    add_rek = State()
    add_rek2 = State()
    tech_work = State()
    all_user = State()
    all_mail = State()
    send_mail = State()
    finish_mail = State()
    one_mail = State()
    card = State()
    change_card = State()
    ban = State()
    cards = State()
    dels = State()


async def del_mes(chat: int, id_: int) -> None:
    """
    удаляет сообщение
    :param chat: id чата
    :param id_: id сообщения
    """
    try: await bot.delete_message(chat, id_)
    except Exception: ...


@rt.message(CommandStart(), AdminIs(), StateFilter(default_state))
async def command_start(message: Message, state: FSMContext):
    """старт бота"""
    await state.clear()
    all_user = await DBuser.all_user_id()
    if message.from_user.id not in all_user:
        await DBuser.add_new_user(message.from_user.id, f'@{message.from_user.username}', message.from_user.first_name)
        markup = await create_markup('reply', [[["Каналы"], ["Продажи on/off"]],
                                               [["Общая Комиссия"], ["Комиссия пользователя"]],
                                               [["Статистика"], ["Поддержка"]],
                                               [['Рассылка'], ["Бан"]]])
        await message.answer(f"Ты админ", reply_markup=markup)
    else:
        markup = await create_markup('reply', [[["Каналы"], ["Продажи on/off"]],
                                               [["Общая Комиссия"], ["Комиссия пользователя"]],
                                               [["Статистика"], ["Поддержка"]],
                                               [['Рассылка'], ["Бан"]]])
        await message.answer(f"Ты админ", reply_markup=markup)



@rt.callback_query(AdminIs(), F.data == 'cancel')
async def cancel_callback(call: CallbackQuery, state: FSMContext):
    """инлайн-кнопка с "cancel" """
    await state.clear()
    await command_start(call.message, state)

