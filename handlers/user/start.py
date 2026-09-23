from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, CommandObject
from aiogram import F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import FSInputFile, InlineKeyboardButton, KeyboardButton, Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

from data.loader import rt, bot
from utils.db.api.statistics import DBstatistics
from utils.system.inline_btns import create_markup
from utils.db.api.support import DBsupport
from utils.db.api.users import DBuser
from utils.db.api.ban import DBban
from utils.db.api.sales import DBsales


class UserState(StatesGroup):
    info_channel = State()
    data_channel = State()
    data_channel_update = State()
    wallet = State()


@rt.message(CommandStart())
async def start_message(message: Message, state: FSMContext, command: CommandObject):
    ban = await DBban.return_ban()
    if message.from_user.id in ban:
        await message.answer(f"Вы заблокированы!")
    else:
        await state.clear()
        support = await DBsupport.return_support()
        photo = FSInputFile(f"photo/start.png")
        name = await bot.get_me()
        all_user = await DBuser.all_user_id()
        sales = await DBsales.return_sales()
        if sales == 1:
            markup_rep = await create_markup('reply', [
                [['🎬 Купить канал'], ['➕ Продать канал']],
                [["👤 Личный кабинет"]]])
        else:
            markup_rep = await create_markup('reply', [
                [['🎬 Купить канал']],
                [["👤 Личный кабинет"]]])
        markup_in = await create_markup('inline', [[['💬 Поддержка', f"{support}"]]])
        if message.from_user.id not in all_user:
            if command:
                await DBuser.add_new_user(message.from_user.id, f'@{message.from_user.username}', message.from_user.first_name)
                await DBstatistics.add_new_user()
                await message.answer_photo(
                    caption=f"""<b>🚀 Добро пожаловать!</b>

Покупайте и продавайте YouTube-каналы в одном месте.

🔥 <b>Найдите канал под свои цели</b>
💰 <b>Выставьте свой канал на продажу</b>""",
                    photo=photo, reply_markup=markup_in)
                await message.answer("Воспользуйтесь меню ниже:", reply_markup=markup_rep)

        else:
            if message.from_user.id in await DBban.return_ban():
                await message.answer(f"Вы забанены!")
            else:
                await message.answer_photo(
                    caption=f"""<b>🚀 Добро пожаловать!</b>

Покупайте и продавайте YouTube-каналы в одном месте.

🔥 <b>Найдите канал под свои цели</b>
💰 <b>Выставьте свой канал на продажу</b>""",
                    photo=photo, reply_markup=markup_in)
                await message.answer("Воспользуйтесь меню ниже:", reply_markup=markup_rep)

@rt.callback_query(F.data == 'back')
async def profile2(call: CallbackQuery, state: FSMContext):
    ban = await DBban.return_ban()
    if call.from_user.id in ban:
        await call.message.answer(f"Вы заблокированы!")
    else:
        await bot.delete_message(chat_id=call.from_user.id, message_id=call.message.message_id)
        support = await DBsupport.return_support()
        sales = await DBsales.return_sales()
        if sales == 1:
            markup_rep = await create_markup('reply', [
                [['🎬 Купить канал'], ['➕ Продать канал']],
                [["👤 Личный кабинет"]]])
        else:
            markup_rep = await create_markup('reply', [
                [['🎬 Купить канал']],
                [["👤 Личный кабинет"]]])
        markup_in = await create_markup('inline', [[['💬 Поддержка', f"{support}"]]])
        await state.clear()
        photo = FSInputFile(f"photo/start.png")
        await call.message.answer_photo(
            caption=f"""<b>🚀 Добро пожаловать!</b>

Покупайте и продавайте YouTube-каналы в одном месте.

🔥 <b>Найдите канал под свои цели</b>
💰 <b>Выставьте свой канал на продажу</b>""",
            photo=photo, reply_markup=markup_in)
        await call.message.answer("Воспользуйтесь меню ниже:", reply_markup=markup_rep)
