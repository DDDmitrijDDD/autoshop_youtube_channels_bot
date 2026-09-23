from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state
from aiogram.types import Message, CallbackQuery
from data.loader import rt, bot
from aiogram import F
from handlers.admin.start import AdminState, del_mes
from utils.db.api.commission import DBcommission
from utils.db.api.statistics import DBstatistics
from utils.system.inline_btns import create_markup
from utils.system.adminka import AdminIs


@rt.message(F.text == 'Статистика', AdminIs(), StateFilter(default_state))
async def mail_message(message: Message, state: FSMContext):
    stat = await DBstatistics.return_all_info()
    await message.answer(f"""Статистика:

Всего пользователей: {stat["users"]}
Активных объявлений: {stat["all_listings"]}
Всего продаж: {stat["all_sale"]} $
Продаж за день: {stat["sale_day"]} $
Продаж за неделю: {stat["sale_week"]} $
Продаж за месяц: {stat["sale_month"]} $

Всего получено с комиссии: {float(stat["all_sale"]) * 0.1} $""")