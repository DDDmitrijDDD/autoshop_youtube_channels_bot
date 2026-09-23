import asyncio
import os

import aiofiles
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, Document, FSInputFile
from aiogram.utils.keyboard import InlineKeyboardBuilder

from data.config import admins_id
from data.loader import rt, bot
from aiogram import F
from handlers.admin.start import AdminState, del_mes
from utils.db.api.channels import DBchannels
from utils.db.api.commission import DBcommission
from utils.db.api.sales import DBsales
from utils.db.api.users import DBuser
from utils.system.inline_btns import create_markup
from utils.system.adminka import AdminIs


async def get_announcements_page_markup(user_id: int, page: int = 1):
    from data.config import admins_id

    # 1. Сбор объявлений в зависимости от того, админ пользователь или нет
    if user_id in admins_id:
        # Если это админ, запрашиваем каналы всех админов параллельно
        tasks = [DBchannels.get_channels_by_user(adm_id) for adm_id in admins_id]
        results = await asyncio.gather(*tasks)

        # Объединяем списки в один плоский список
        channels = []
        for chunk in results:
            if chunk:
                channels.extend(chunk)

        text_header = "📊 <b>Активные объявления администраторов</b>\n"
    else:
        # Для обычного пользователя оставляем старую логику
        channels = await DBchannels.get_channels_by_user(user_id)
        text_header = "📊 <b>Ваши активные объявления</b>\n"

    # 2. Проверка на пустоту
    if not channels:
        return "📭 Объявлений не найдено.", None

    # 3. Расчет пагинации
    ITEMS_PER_PAGE = 9
    total_items = len(channels)
    total_pages = (total_items + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE

    if page < 1:
        page = 1
    elif page > total_pages:
        page = total_pages

    # Срез элементов для текущей страницы
    start_idx = (page - 1) * ITEMS_PER_PAGE
    end_idx = start_idx + ITEMS_PER_PAGE
    page_channels = channels[start_idx:end_idx]

    # Формируем текст
    text = text_header
    text += f"Выберите ID канала ниже, чтобы посмотреть подробную информацию.\n\n"
    text += f"<i>Страница {page} из {total_pages}</i>"

    builder = InlineKeyboardBuilder()

    # 4. Заполняем сетку кнопками с ID
    for ch in page_channels:
        status_text = " (проверка)" if getattr(ch, 'status', None) == 0 else ""
        builder.button(text=f"{ch.id}{status_text}", callback_data=f"view_ann:{ch.id}")

    # Выстраиваем кнопки строго в сетку 3х3
    builder.adjust(3)

    # 5. Добавляем кнопки навигации
    nav_buttons = []
    if page > 1:
        nav_buttons.append(InlineKeyboardButton(text="⬅️ Назад", callback_data=f"ann_page:{page - 1}"))
    if page < total_pages:
        nav_buttons.append(InlineKeyboardButton(text="Вперед ➡️", callback_data=f"ann_page:{page + 1}"))

    if nav_buttons:
        builder.row(*nav_buttons)

    builder.row(InlineKeyboardButton(text="➕ Создать", callback_data="create"))
    builder.row(InlineKeyboardButton(text="❌ Отмена", callback_data="cancel"))

    return text, builder.as_markup()


@rt.message(F.text == 'Каналы', AdminIs(), StateFilter(default_state))
async def mail_message(message: Message, state: FSMContext):
    """Вход в меню активных объявлений по текстовой команде (Первая страница)"""
    user_id = message.from_user.id

    await state.set_state(AdminState.viewing_page)
    await state.update_data(current_page=1)

    # Получаем текст и inline-клавиатуру 3х3 для первой страницы
    text, markup = await get_announcements_page_markup(user_id, page=1)

    if markup:
        # Отправляем новое сообщение с клавиатурой пагинации
        await message.answer(text, reply_markup=markup)
    else:
        markup = await create_markup('inline', [[['➕ Создать', f"create"]]])
        # Если объявлений нет, просто пишем об этом пользователю
        await message.answer(text, reply_markup=markup)


@rt.callback_query(F.data == "create")
async def change_announcements_page(call: CallbackQuery, state: FSMContext):
    markup = await create_markup('inline', [[['❌ Отмена', "cancel"]]])
    await call.message.answer(f"""<b>Введите необходимую информацию через <code>;</code></b>

1. <b>Ссылка на YouTube-канал</b>
2. <b>Название канала</b>
3. <b>Количество подписчиков</b> (число)
4. <b>Количество просмотров</b> (число)
5. <b>Тематика</b>
6. <b>Страна/язык аудитории</b>
7. <b>Монетизация</b> — да/нет
8. <b>Доход/показатели монетизации,</b> если применимо (число в $, если нету, то <code>0</code>)
9. <b>Желаемая цена продажи</b> (число в $)
10. <b>Дополнительное описание</b> (по желанию, если нет, то оставьте пустым)

<b>Пример:</b>
https://www.youtube.com;Dark;10000;44300;готовка еды;Китай;нет;0;100""", reply_markup=markup)

    await state.set_state(AdminState.info_channel)


@rt.message(AdminState.info_channel)
async def sell(message: Message, state: FSMContext):
    markup = await create_markup('inline', [[['❌ Отмена', f"cancel"]]])
    text = message.text
    try:
        split = text.split(";")
        if len(split) > 10 or len(split) < 9 or split[2].isdigit() == False or split[3].isdigit() == False or split[7].isdigit() == False or split[8].isdigit() == False or (split[6] != "да" and split[6] != "нет"):
            await message.answer(f"Проверьте валидность введенных данных и введите еще раз", reply_markup=markup)
            await state.set_state(AdminState.info_channel)
        else:
            if split[6].lower() == "да":
                moneta = split[7]
            else:
                moneta = 0
            if len(split) == 9:
                description = "-"
            else:
                description = split[9]
            await state.update_data(url=split[0], name=split[1], subscribers=split[2], views=split[3], topic=split[4],
                                    country=split[5], monetization=split[6], income=moneta, price=split[8], description=description)
            await message.answer(f"Отправьте файл .txt в котором будут указаны все данные для доступа к аккаунту, которые получит покупатель",
                                 reply_markup=markup)
            await state.set_state(AdminState.data_channel)
    except:
        await message.answer(f"Проверьте валидность введенных данных и введите еще раз", reply_markup=markup)
        await state.set_state(AdminState.info_channel)


@rt.message(AdminState.data_channel, F.document)
async def sell(message: Message, state: FSMContext):
    markup = await create_markup('inline', [[['❌ Отмена', f"cancel"]]])
    document: Document = message.document
    if not document.file_name.endswith(".txt"):
        await message.answer("Отправьте файл именно формата .txt", reply_markup=markup)
        return

    # 2. Создаем папку 'examination', если её не существует
    folder_path = "examination"
    os.makedirs(folder_path, exist_ok=True)

    # 3. Формируем путь: берем Telegram ID пользователя
    user_id = message.from_user.id
    local_file_name = f"{user_id}.txt"
    destination_path = os.path.join(folder_path, local_file_name)

    # 4. Скачиваем файл на диск (если файл уже существовал, он перезапишется новым)
    await message.bot.download(
        file=document.file_id,
        destination=destination_path
    )

    # 5. Читаем содержимое сохраненного файла для вывода пользователю
    with open(destination_path, "r", encoding="utf-8", errors="ignore") as f:
        file_text = f.read()

    data = await state.get_data()

    # 6. Сохраняем в состояние путь к файлу
    await state.update_data(data_channel_path=destination_path)
    commission = await DBuser.return_commission(message.from_user.id)
    markup = await create_markup('inline', [[["✅ Выставить на продажу", "go_sell_admin"]],
                                            [['❌ Отмена', f"cancel_document"]]])
    await message.answer(f"""Проверьте данные:

🔗 <b>Ссылка на YouTube-канал:</b> {data["url"]}
📺 <b>Название канала:</b> {data["name"]}
👥 <b>Количество подписчиков:</b> {data["subscribers"]}
👁 <b>Количество просмотров:</b> {data["views"]}
🏷 <b>Тематика:</b> {data["topic"]}
🌍 <b>Страна/язык аудитории:</b> {data["country"]}
💸 <b>Монетизация:</b> {data["monetization"]}
🪙 <b>Доход/показатели монетизации:</b> {data["income"]} $
💰 <b>Желаемая цена продажи:</b> {data["price"]} $
📝 <b>Дополнительное описание:</b> {data["description"]}

<b>Данные которые получит покупатель:</b>
{file_text}""", reply_markup=markup)


@rt.callback_query(F.data == "cancel_document")
async def cancel_and_delete_file(callback: CallbackQuery, state: FSMContext):
    # 1. Получаем данные из состояния (там хранится наш data_channel_path)
    data = await state.get_data()
    file_path = data.get("data_channel_path")

    # 2. Проверяем, существует ли файл, и удаляем его
    if file_path and os.path.exists(file_path):
        try:
            os.remove(file_path)
        except Exception as e:
            # Логируем ошибку, если не удалось удалить файл (например, он заблокирован)
            print(f"Ошибка при удалении файла: {e}")

    # 3. Полностью очищаем состояние FSM пользователя
    await state.clear()

    # 4. Уведомляем пользователя об отмене (можно изменить текст под ваше меню)
    await callback.message.edit_text("❌ Выставление канала на продажу отменено.")

    # 5. Отвечаем на callback, чтобы убрать часики/загрузку с инлайн-кнопки
    await callback.answer()


@rt.message(AdminState.data_channel)
async def sell_file_invalid(message: Message):
    markup = await create_markup('inline', [[['❌ Отмена', f"back"]]])
    await message.answer("Ожидается файл .txt", reply_markup=markup)


@rt.callback_query(F.data == "go_sell_admin")
async def admin_payout_handler(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    channel_id = await DBchannels.add_new_channel_admin(call.from_user.id, data["url"], data["name"],
                                                  data["subscribers"], data["views"],
                                                  data["topic"], data["country"],
                                                  data["monetization"], data["income"],
                                                  data["price"], data["description"], f"{call.from_user.id}.txt")
    # === БЛОК ПЕРЕМЕЩЕНИЯ И ПЕРЕИМЕНОВАНИЯ ФАЙЛА ===
    # Путь к исходному файлу в examination (userid.txt)
    old_file_path = os.path.join("examination", f"{call.from_user.id}.txt")

    # Путь к новому файлу в channel (userid_channelid.txt)
    new_file_path = os.path.join("channel", f"{call.from_user.id}_{channel_id}.txt")

    try:
        if os.path.exists(old_file_path):
            # Перемещаем файл из examination в channel с новым именем
            shutil.move(old_file_path, new_file_path)
        else:
            print(f"Предупреждение: Файл в examination не найден ({old_file_path})")
    except Exception as e:
        print(f"Ошибка при перемещении файла: {e}")
    # ===============================================
    await call.message.answer("""Ваше канал опубликован""")
    await state.clear()


@rt.callback_query(AdminState.viewing_page, F.data.startswith("ann_page:"))
async def change_announcements_page(call: CallbackQuery, state: FSMContext):
    """Переключение между страницами активных объявлений"""
    page = int(call.data.split(":")[1])
    await state.update_data(current_page=page)

    text, markup = await get_announcements_page_markup(call.from_user.id, page=page)
    await call.message.edit_text(text, reply_markup=markup)
    await call.answer()


@rt.callback_query(AdminState.viewing_page, F.data.startswith("view_ann:"))
async def view_announcement_details(call: CallbackQuery, state: FSMContext):
    """Отображение подробной информации об объявлении из таблицы Channels"""
    ann_id = int(call.data.split(":")[1])
    current_user_id = call.from_user.id

    # 1. Получаем список каналов (всех админов или только текущего пользователя)
    if current_user_id in admins_id:
        tasks = [DBchannels.get_channels_by_user(adm_id) for adm_id in admins_id]
        results = await asyncio.gather(*tasks)
        channels = []
        for chunk in results:
            if chunk:
                channels.extend(chunk)
    else:
        channels = await DBchannels.get_channels_by_user(current_user_id)

    # Ищем канал по ID объявления
    channel = next((ch for ch in channels if ch.id == ann_id), None)

    if not channel:
        await call.answer("❌ Объявление не найдено.", show_alert=True)
        return

    # --- Чтение файла из папки (data) ---
    file_content = "Файл пуст или отсутствует"

    creator_id = getattr(channel, 'user_id', current_user_id)

    if channel.status == 0:
        # На проверке: папка examination, файл userid.txt
        file_path = os.path.join("examination", f"{call.from_user.id}.txt")
    else:
        # Активное: папка channel, файл userid_channelid.txt
        file_path = os.path.join("channel", f"{call.from_user.id}_{channel.id}.txt")

    if os.path.exists(file_path):
        try:
            async with aiofiles.open(file_path, mode='r', encoding='utf-8') as f:
                file_content = await f.read()
        except Exception as e:
            file_content = f"Ошибка чтения файла: {e}"
    else:
        file_content = f"Файл не найден ({file_path})"
    # ------------------------------------

    # Заголовок в зависимости от статуса
    status_header = f"Информация об объявлении #{channel.id} (На проверке)" if channel.status == 0 else f"Информация об объявлении #{channel.id} (Активное)"

    # Формируем динамический вывод полей
    text = f"📄 <b>{status_header}</b>\n"
    text += f"--------------------------------------------------\n"
    text += f"🔗 <b>Ссылка:</b> {channel.url}\n"
    text += f"📺 <b>Название:</b> {channel.name}\n"
    text += f"👥 <b>Количество подписчиков:</b> {channel.subscribers}\n"
    text += f"👁 <b>Количество просмотров:</b> {channel.views}\n"
    text += f"🏷 <b>Тематика:</b> {channel.topic}\n"
    text += f"🌍 <b>Язык аудитории:</b> {channel.country}\n"

    # Логика монетизации и дохода
    if channel.monetization == "да":
        text += f"💸 <b>Монетизация:</b> Да\n"
        # Выводим доход только если монетизация есть
        text += f"🪙 <b>Доход/показатели монетизации</b> {channel.income} $\n"
    else:
        text += f"💸 <b>Монетизация:</b> Нет\n"

    # Скрываем строку описания, если его нет (переменная пустая, None или пустая строка)
    if channel.description != "-":
        text += f"📝 <b>Описание:</b> {channel.description}\n"

    text += f"--------------------------------------------------\n"
    text += f"📂 <b>Данные аккаунта:</b> \n<i>{file_content}</i>\n"
    text += f"--------------------------------------------------\n"
    text += f"💰 <b>Цена продажи:</b> {channel.price} $\n"

    # Создаем клавиатуру возврата
    builder = InlineKeyboardBuilder()
    if current_user_id == creator_id:
        builder.row(InlineKeyboardButton(
            text="✏️ Изменить информацию",
            callback_data=f"edit_ann:{channel.id}"
        ))

        # Кнопка удаления доступна всегда (для своего канала или для чужого админского)
    builder.row(InlineKeyboardButton(
        text="❌ Удалить канал",
        callback_data=f"delete_ann:{channel.id}"
    ))

    user_data = await state.get_data()
    current_page = user_data.get("current_page", 1)

    builder.row(InlineKeyboardButton(
        text="⬅️ Вернуться к списку",
        callback_data=f"ann_page:{current_page}"
    ))

    # Обновляем сообщение (отключаем превью ссылок)
    await call.message.edit_text(text=text, reply_markup=builder.as_markup(), disable_web_page_preview=True)
    await call.answer()


@rt.callback_query(AdminState.viewing_page, F.data.startswith("delete_ann:"))
async def process_edit_announcement(call: CallbackQuery, state: FSMContext):
    ann_id = int(call.data.split(":")[1])
    current_user_id = call.from_user.id

    # 2. Для удаления файла нам тоже сначала нужно узнать, чей это был канал
    if current_user_id in admins_id:
        tasks = [DBchannels.get_channels_by_user(adm_id) for adm_id in admins_id]
        results = await asyncio.gather(*tasks)
        channels = []
        for chunk in results:
            if chunk:
                channels.extend(chunk)
    else:
        channels = await DBchannels.get_channels_by_user(current_user_id)

    channel = next((ch for ch in channels if ch.id == ann_id), None)

    if not channel:
        await call.answer("❌ Канал для удаления не найден.", show_alert=True)
        return

    creator_id = getattr(channel, 'user_id', current_user_id)

    # Формируем корректный путь на основе создателя канала
    if channel.status == 0:
        file_path = os.path.join("examination", f"{creator_id}.txt")
    else:
        file_path = os.path.join("channel", f"{creator_id}_{ann_id}.txt")

    # Удаляем из БД
    await DBchannels.delete_channel(ann_id)

    # Безопасное удаление файла с диска
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
    except Exception as e:
        print(f"Ошибка при удалении файла {file_path}: {e}")

    await call.message.answer(f"Канал #{ann_id} успешно удален")
    await call.answer()


@rt.callback_query(AdminState.viewing_page, F.data.startswith("edit_ann:"))
async def process_edit_announcement(call: CallbackQuery, state: FSMContext):
    """Начало процесса редактирования объявления с проверкой папки examination"""
    ann_id = int(call.data.split(":")[1])
    user_id = call.from_user.id

    # 1. Проверяем, есть ли уже файл этого пользователя на проверке (модерации)
    check_file_path = os.path.join("examination", f"{user_id}.txt")
    if os.path.exists(check_file_path):
        await call.answer(
            "⚠️ Вы не можете изменить канал, пока ваш предыдущий канал находится на проверке у администратора.",
            show_alert=True
        )
        return  # Прерываем выполнение функции, состояние не меняется

    # 2. Если файла на проверке нет, продолжаем стандартную логику редактирования
    await state.update_data(editing_ann_id=ann_id)
    await state.set_state(AdminState.edit_info)

    # Кнопка отмены вернет пользователя обратно на страницу этого же объявления
    markup = await create_markup('inline', [[['❌ Отмена', f"view_ann:{ann_id}"]]])

    await call.message.edit_text(f"""<b>Редактирование объявления #{ann_id}</b>

<b>Введите НОВУЮ информацию через <code>;</code></b>

1. Ссылка на YouTube-канал
2. Название канала
3. Количество подписчиков (число)
4. Количество просмотров (число)
5. Тематика
6. Страна/язык аудитории
7. Монетизация — да/нет
8. Доход/показатели монетизации, если применимо (число в $, если нету, то <code>0</code>)
9. Желаемая цена продажи (число в $)
10. Дополнительное описание (по желанию, если нет, то оставьте пустым)

Пример:
https://www.youtube.com;Dark;10000;44300;готовка еды;Китай;нет;0;100""", reply_markup=markup)
    await call.answer()


@rt.message(AdminState.edit_info)
async def save_edited_announcement_info(message: Message, state: FSMContext):
    markup = await create_markup('inline', [[['❌ Отмена', f"back"]]])
    text = message.text
    try:
        split = text.split(";")
        if len(split) > 10 or len(split) < 9 or split[2].isdigit() == False or split[3].isdigit() == False or split[7].isdigit() == False or split[8].isdigit() == False or (split[6] != "да" and split[6] != "нет"):
            await message.answer(f"Проверьте валидность введенных данных и введите еще раз", reply_markup=markup)
            await state.set_state(AdminState.edit_info)
        else:
            if split[6].lower() == "да":
                moneta = split[7]
            else:
                moneta = 0
            if len(split) == 9:
                description = "-"
            else:
                description = split[9]
            await state.update_data(url=split[0], name=split[1], subscribers=split[2], views=split[3], topic=split[4],
                                    country=split[5], monetization=split[6], income=moneta, price=split[8], description=description)
            await message.answer(f"Отправьте файл .txt в котором будут указаны все данные для доступа к аккаунту, которые получит покупатель",
                                 reply_markup=markup)
            await state.set_state(AdminState.data_channel_update)
    except:
        await message.answer(f"Проверьте валидность введенных данных и введите еще раз", reply_markup=markup)
        await state.set_state(AdminState.edit_info)


@rt.message(AdminState.data_channel_update, F.document)
async def sell(message: Message, state: FSMContext):
    markup = await create_markup('inline', [[['❌ Отмена', f"back"]]])
    document: Document = message.document
    if not document.file_name.endswith(".txt"):
        await message.answer("Отправьте файл именно формата .txt", reply_markup=markup)
        return

    folder_path = "examination"
    os.makedirs(folder_path, exist_ok=True)

    user_id = message.from_user.id
    local_file_name = f"{user_id}.txt"
    destination_path = os.path.join(folder_path, local_file_name)

    await message.bot.download(
        file=document.file_id,
        destination=destination_path
    )

    with open(destination_path, "r", encoding="utf-8", errors="ignore") as f:
        file_text = f.read()

    data = await state.get_data()

    # 6. Сохраняем в состояние путь к файлу
    await state.update_data(data_channel_path=destination_path)
    markup = await create_markup('inline', [[["✅ Изменить канал", "go_sell_update_admin"]],
                                            [['❌ Отмена', f"back_document_update"]]])
    await message.answer(f"""Проверьте данные:

🔗 Ссылка на YouTube-канал: {data["url"]}
📺 Название канала: {data["name"]}
👥 Количество подписчиков: {data["subscribers"]}
👁 Количество просмотров: {data["views"]}
🏷 Тематика: {data["topic"]}
🌍 Страна/язык аудитории: {data["country"]}
💸 Монетизация: {data["monetization"]}
🪙 Доход/показатели монетизации: {data["income"]} $
💰 Желаемая цена продажи: {data["price"]} $)
📝 Дополнительное описание: {data["description"]}

Данные которые получит покупатель:
{file_text}""", reply_markup=markup)


@rt.callback_query(F.data == "back_document_update")
async def cancel_and_delete_file(callback: CallbackQuery, state: FSMContext):
    # 1. Получаем данные из состояния (там хранится наш data_channel_path)
    data = await state.get_data()
    file_path = data.get("data_channel_path")

    # 2. Проверяем, существует ли файл, и удаляем его
    if file_path and os.path.exists(file_path):
        try:
            os.remove(file_path)
        except Exception as e:
            # Логируем ошибку, если не удалось удалить файл (например, он заблокирован)
            print(f"Ошибка при удалении файла: {e}")

    # 3. Полностью очищаем состояние FSM пользователя
    await state.clear()

    # 4. Уведомляем пользователя об отмене (можно изменить текст под ваше меню)
    await callback.message.edit_text("❌ Обновление канала отменено.")

    # 5. Отвечаем на callback, чтобы убрать часики/загрузку с инлайн-кнопки
    await callback.answer()


@rt.message(AdminState.data_channel_update)
async def sell_file_invalid(message: Message):
    markup = await create_markup('inline', [[['❌ Отмена', f"back"]]])
    await message.answer("Ожидается файл .txt", reply_markup=markup)

import shutil
@rt.callback_query(F.data == "go_sell_update_admin")
async def admin_payout_handler(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    channel_id = await DBchannels.update_channel_info_admin(data["editing_ann_id"], data["url"], data["name"],
                                                  data["subscribers"], data["views"],
                                                  data["topic"], data["country"],
                                                  data["monetization"], data["income"],
                                                  data["price"], data["description"], f"{call.from_user.id}_{data["editing_ann_id"]}.txt")

    # Путь к новому файлу, который сейчас лежит в examination (имя файла: userid.txt)
    new_exam_file = os.path.join("examination", f"{call.from_user.id}.txt")

    # Путь, куда его нужно переместить в папку channel (имя файла: userid_channelid.txt)
    # Обратите внимание на одинарные кавычки ['editing_ann_id'] внутри f-строки, чтобы не было синтаксической ошибки
    target_channel_file = os.path.join("channel", f"{call.from_user.id}_{data['editing_ann_id']}.txt")

    try:
        if os.path.exists(new_exam_file):
            # Перемещаем файл из examination в channel с новым именем
            shutil.move(new_exam_file, target_channel_file)
        else:
            print(f"Предупреждение: Файл в examination не найден ({new_exam_file})")
    except Exception as e:
        print(f"Ошибка при перемещении нового файла: {e}")

    await call.message.answer("""Канал выставлен на продажу""")
    await state.clear()