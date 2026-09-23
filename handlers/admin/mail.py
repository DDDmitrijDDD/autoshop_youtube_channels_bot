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


@rt.message(Command('mail'), StateFilter(default_state))
@rt.message(F.text == 'Рассылка', AdminIs(), StateFilter(default_state))
async def mail_message(message: Message, state: FSMContext):
    """при кнопке Рассылка"""
    markup = await create_markup('inline', [[['Написать всем', 'all']], [['Написать одному', 'one']],
                                            [['Отмена', 'cancel']]])
    await message.answer(f"Выберите действие", reply_markup=markup)

    await state.set_state(AdminState.all_mail)
    await del_mes(message.from_user.id, message.message_id)


@rt.callback_query(AdminState.all_mail, AdminIs(), F.data == 'one')
async def markup_all_mail_skip(call: CallbackQuery, state: FSMContext):
    markup = await create_markup('inline', [[['Отмена', 'cancel']]])
    await call.message.answer('Введите id или name юзера', reply_markup=markup)
    await state.set_state(AdminState.one_mail)


@rt.callback_query(AdminIs(), F.data == 'one2')
async def markup_all_mail_skip(call: CallbackQuery, state: FSMContext):
    await state.update_data(type='one2')
    markup = await create_markup('inline', [[['Отмена', 'cancel']], [['Пропустить', 'skip']]])
    await call.message.answer('Напиши кнопки по шаблону:\n'
                         '`[еее::https://t.me/DiceOfFire] [ууу::https://t.me/DiceOfFire_bot]\n'
                         '[яяя::https://google.com]`', reply_markup=markup)
    await state.set_state(AdminState.all_mail)


@rt.message(AdminState.one_mail, AdminIs())
async def markup_all_mail_skip(message: Message, state: FSMContext):
    await state.update_data(type='one')
    await state.update_data(us=f"{message.text}")
    markup = await create_markup('inline', [[['Отмена', 'cancel']], [['Пропустить', 'skip']]])
    await message.answer('Напиши кнопки по шаблону:\n'
                         '`[еее::https://t.me/DiceOfFire] [ууу::https://t.me/DiceOfFire_bot]\n'
                         '[яяя::https://google.com]`', reply_markup=markup)
    await state.set_state(AdminState.all_mail)


@rt.callback_query(AdminState.all_mail, AdminIs(), F.data == 'all')
async def markup_all_mail_skip(call: CallbackQuery, state: FSMContext):
    await state.update_data(type='all')
    markup = await create_markup('inline', [[['Отмена', 'cancel']], [['Пропустить', 'skip']]])
    await call.message.answer('Напиши кнопки по шаблону:\n'
                         '`[еее::https://t.me/DiceOfFire] [ууу::https://t.me/DiceOfFire_bot]\n'
                         '[яяя::https://google.com]`', reply_markup=markup)
    await state.set_state(AdminState.all_mail)


@rt.callback_query(AdminState.all_mail, AdminIs(), F.data == 'skip')
async def markup_all_mail_skip(call: CallbackQuery, state: FSMContext):
    """скип кнопок в рассыкле"""
    await call.message.answer(f"Напиши сообщение для рассылки",
                                 reply_markup=await create_markup('inline',
                                                                  [[['Отмена', 'cancel']]]))
    await state.set_state(AdminState.send_mail)


@rt.message(AdminState.all_mail, AdminIs())
async def markup_all_message(message: Message, state: FSMContext):
    """кнопки при рассылке у всех"""
    try:
        l1st = []
        for i in message.text.split('\n'):
            _ = []
            for j in i.split(' '):
                x, z = j.split('::')
                _.append([x[1:], z[:-1]])
            l1st.append(_)
        await state.update_data(l1st=l1st)
        await del_mes(message.from_user.id, message.message_id)
        await message.answer(f"Напиши сообщение для рассылки",
                                  reply_markup=await create_markup('reply',
                                                                   [[['Отмена']]]))
        await state.set_state(AdminState.send_mail)
    except Exception:
        await del_mes(message.from_user.id, message.message_id)


@rt.message(AdminState.send_mail, AdminIs())
async def send_mail(message: Message, state: FSMContext):
    """проверка рассылки"""
    await del_mes(message.from_user.id, message.message_id)

    await state.update_data(text=message.html_text)
    data = await state.get_data()
    if 'l1st' in data.keys():
        await message.answer(data['text'], reply_markup=await create_markup('inline', data['l1st']),
                             parse_mode='html')
    else:
        await message.answer(data['text'], parse_mode='html')
    markup = await create_markup('inline', [[['Да', 'send']], [['Отмена', 'cancel']]])
    await message.answer(f"Такая должна быть рассылка?", reply_markup=markup)
    await state.set_state(AdminState.finish_mail)


@rt.callback_query(F.data == 'send', AdminState.finish_mail, AdminIs())
async def finish_mail(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    if data['type'] == 'all':
        try:
            for user in await DBuser.all_user_id():
                if 'l1st' in data.keys():
                    await bot.send_message(user, data['text'], reply_markup=await create_markup('inline',
                                                                                                data['l1st']),
                                           parse_mode='html')
                else:
                    await bot.send_message(user, data['text'], parse_mode='html')
            await call.message.answer(f"Сообщение отправлено")
        except: ...
    else:
        try:
            if 'l1st' in data.keys():
                await bot.send_message(data["us"], data['text'], reply_markup=await create_markup('inline',
                                                                                          data['l1st']),
                                       parse_mode='html')
                await call.message.answer(f"Сообщение отправлено")
            else:
                await bot.send_message(data["us"], data['text'], parse_mode='html')
                await call.message.answer(f"Сообщение отправлено")
        except Exception:
            try:
                us = data["us"]
                if us.isdigit():
                    if 'l1st' in data.keys():
                        await bot.send_message(us, data['text'], reply_markup=await create_markup('inline',
                                                                                                             data['l1st']),
                                           parse_mode='html')
                        await call.message.answer(f"Сообщение отправлено")
                    else:
                        await bot.send_message(us, data['text'], parse_mode='html')
                        await call.message.answer(f"Сообщение отправлено")
                else:
                    if us[0] != "@":
                        us = us.replace(us, f"@{us}")
                    ids = await DBuser.return_info_user_name(us)
                    if 'l1st' in data.keys():
                        await bot.send_message(ids[1], data['text'], reply_markup=await create_markup('inline',
                                                                                                             data['l1st']),
                                           parse_mode='html')
                        await call.message.answer(f"Сообщение отправлено")
                    else:
                        await bot.send_message(ids[1], data['text'], parse_mode='html')
                        await call.message.answer(f"Сообщение отправлено")
            except Exception:
                await call.message.answer(f"Пользователь не найден")
    await state.clear()
