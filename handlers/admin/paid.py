import os
import shutil

from aiogram.filters import Command, StateFilter, state
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state
from aiogram.types import Message, CallbackQuery
from data.loader import rt, bot
from aiogram import F

from handlers.admin.start import AdminState
from utils.db.api.channels import DBchannels
from utils.db.api.statistics import DBstatistics
from utils.db.api.users import DBuser
from utils.system.inline_btns import create_markup



@rt.callback_query(F.data.startswith("publish_"))
async def admin_payout_handler(call: CallbackQuery, state: FSMContext):
    params = call.data.split("_")
    try:
        channel_id = int(params[1])
        channel = await DBchannels.return_all_info_by_channel_id(channel_id)
        if channel["status"] == 1:
            await call.message.answer("Канал уже выставлен на продажу")
            await bot.delete_message(chat_id=call.from_user.id, message_id=call.message.message_id)
        else:
            user_id = channel["user_id"]
            # 1. Определяем старый путь к файлу
            old_file_path = os.path.join("examination", f"{user_id}.txt")
            new_file_path = None

            # 2. Проверяем, существует ли исходный файл перед перемещением
            if os.path.exists(old_file_path):
                # Создаем целевую папку 'channel', если её нет
                target_folder = "channel"
                os.makedirs(target_folder, exist_ok=True)

                # Формируем новое имя файла: юзерид_каналид.txt
                new_file_name = f"{user_id}_{channel_id}.txt"
                new_file_path = os.path.join(target_folder, new_file_name)

                try:
                    # Перемещаем файл в новую папку с новым именем
                    shutil.move(old_file_path, new_file_path)
                except Exception as e:
                    print(f"Ошибка при перемещении файла: {e}")
                    new_file_path = None  # Если не переместился, запишем исходный статус или обработаем ошибку

            # 3. Обновляем статус в БД и передаем туда новый путь к файлу
            # (Если файл не существовал, в базу запишется None или старое значение, в зависимости от логики)
            await DBchannels.update_status(channel_id, file_path=new_file_name)
            await DBuser.update_user_examination_minus(user_id)
            await DBuser.update_user_announcements_plus(user_id)
            await DBstatistics.listing_plus()
            await call.message.answer(f"Канал выставлен на продажу")
            await bot.send_message(chat_id=channel["user_id"], text=f"Ваш канал выставлен на продажу под номером <code>#{channel_id}</code>")
            await bot.delete_message(chat_id=call.from_user.id, message_id=call.message.message_id)
            await state.clear()
    except:
        await call.message.answer(f"Канал уже был отклонен")
        await bot.delete_message(chat_id=call.from_user.id, message_id=call.message.message_id)
        await state.clear()


@rt.callback_query(F.data.startswith("reject_"))
async def admin_payout_handler(call: CallbackQuery, state: FSMContext):
    params = call.data.split("_")
    try:
        markup = await create_markup('inline', [[["Оставить комментарий", "comment"]],
                                                [['❌ Отмена', f"cancel"]]])
        channel_id = int(params[1])
        channel = await DBchannels.return_all_info_by_channel_id(channel_id)
        await state.update_data(user_id=channel["user_id"])
        if channel["status"] == 1:
            await call.message.answer("Канал уже выставлен на продажу")
            await bot.delete_message(chat_id=call.from_user.id, message_id=call.message.message_id)
        else:
            # --- УДАЛЕНИЕ ФАЙЛА ИЗ ПАПКИ examination ---
            owner_id = channel["user_id"]
            file_path = os.path.join("examination", f"{owner_id}.txt")

            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except Exception as e:
                    print(f"Ошибка при удалении файла {file_path}: {e}")
            # -------------------------------------------
            await DBchannels.delete_channel(channel_id)
            await DBuser.update_user_examination_minus(channel["user_id"])
            await call.message.answer(f"Канал отклонен, хотите оставить комментарий пользователю?", reply_markup=markup)
            await bot.send_message(chat_id=channel["user_id"],
                                   text=f"Ваш канал отклонили в публикации")
            await bot.delete_message(chat_id=call.from_user.id, message_id=call.message.message_id)
    except:
        await call.message.answer(f"Канал уже был отклонен")
        await bot.delete_message(chat_id=call.from_user.id, message_id=call.message.message_id)
        await state.clear()


@rt.callback_query(F.data == "comment")
async def admin_payout_handler(call: CallbackQuery, state: FSMContext):
    markup = await create_markup('inline', [[['❌ Отмена', f"cancel"]]])
    await call.message.answer(f"Введите комментарий", reply_markup=markup)
    await state.set_state(AdminState.comment)


@rt.message(AdminState.comment)
async def admin_payout_handler(message: Message, state: FSMContext):
    data = await state.get_data()
    await bot.send_message(chat_id=data["user_id"], text=f"""Администратор оставил комментарий по отмене вашего объявления
    
<b>{message.text}</b>""")
    await message.answer(f"Комментарий успешно отправлен")
    await state.clear()


@rt.callback_query(F.data.startswith("paid_"))
async def admin_payout_handler(call: CallbackQuery, state: FSMContext):
    params = call.data.split("_")
    try:
        user_id = int(params[1])
        user = await DBuser.return_all_info(user_id)
        if user["status"] == 0:
            await call.message.answer("Пользователю уже выплатили средства или отклонили вывод")
            await bot.delete_message(chat_id=call.from_user.id, message_id=call.message.message_id)
        else:
            await DBuser.update_user_status_null(user_id)
            await DBuser.update_user_balance(user_id)
            await call.message.answer(f"Средства отправлены пользователю")
            await bot.send_message(chat_id=user_id, text=f"<b>Ваши средства отправлены. Ожидайте поступления</b>")
            await bot.delete_message(chat_id=call.from_user.id, message_id=call.message.message_id)
            await state.clear()
    except:
        await call.message.answer(f"Пользователю уже выплатили средства или отклонили вывод")
        await bot.delete_message(chat_id=call.from_user.id, message_id=call.message.message_id)
        await state.clear()


@rt.callback_query(F.data.startswith("cancell_"))
async def admin_payout_handler(call: CallbackQuery, state: FSMContext):
    params = call.data.split("_")
    try:
        markup = await create_markup('inline', [[["Оставить комментарий", "comment2"]],
                                                [['❌ Отмена', f"cancel"]]])
        user_id = int(params[1])
        user = await DBuser.return_all_info(user_id)
        await state.update_data(user_id=user_id)
        if user["status"] == 0:
            await call.message.answer("Пользователю уже выплатили средства или отклонили вывод")
            await bot.delete_message(chat_id=call.from_user.id, message_id=call.message.message_id)
        else:
            await DBuser.update_user_status_null(user_id)
            await call.message.answer(f"Вывод отклонен, хотите оставить комментарий пользователю?", reply_markup=markup)
            await bot.send_message(chat_id=user_id,
                                   text=f"Ваш вывод отклонили")
            await bot.delete_message(chat_id=call.from_user.id, message_id=call.message.message_id)
    except:
        await call.message.answer(f"Пользователю уже выплатили средства или отклонили вывод")
        await bot.delete_message(chat_id=call.from_user.id, message_id=call.message.message_id)
        await state.clear()


@rt.callback_query(F.data == "comment2")
async def admin_payout_handler(call: CallbackQuery, state: FSMContext):
    markup = await create_markup('inline', [[['❌ Отмена', f"cancel"]]])
    await call.message.answer(f"Введите комментарий", reply_markup=markup)
    await state.set_state(AdminState.comment2)


@rt.message(AdminState.comment2)
async def admin_payout_handler(message: Message, state: FSMContext):
    data = await state.get_data()
    await bot.send_message(chat_id=data["user_id"], text=f"""Администратор оставил комментарий по отмене вашего вывода

<b>{message.text}</b>""")
    await message.answer(f"Комментарий успешно отправлен")
    await state.clear()