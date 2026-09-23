import os

import aiofiles
from aiogram import F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state, State, StatesGroup
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, Document, FSInputFile
from aiogram.utils.keyboard import InlineKeyboardBuilder
import math

from data.config import admins_id
from data.loader import rt, bot
from handlers.user.start import UserState
from utils.db.api.ban import DBban
from utils.db.api.channels import DBchannels
from utils.db.api.commission import DBcommission
from utils.system.inline_btns import create_markup
from utils.db.api.users import DBuser
from utils.db.api.story import DBstory  # Убедитесь, что импортируете асинхронный DBstory


# Состояния FSM для изоляции логики просмотра истории
class StoryStates(StatesGroup):
    viewing_page = State()

class AnnouncementStates(StatesGroup):
    viewing_page = State()
    edit_info = State()  # Новое состояние для редактирования



# ==================== ЛИЧНЫЙ КАБИНЕТ ====================

@rt.message(F.text == "👤 Личный кабинет")
async def lk(message: Message):
    ban = await DBban.return_ban()
    if message.from_user.id in ban:
        await message.answer(f"Вы заблокированы!")
    else:
        info = await DBuser.return_all_info(message.from_user.id)
        markup = await create_markup('inline', [[['📝 Мои объявления', f"my_announcements"],
                                                 ["💸 Проданные каналы", "story"]], [["💰 Вывод", "withdrawal"]]])
        await message.answer(f"""👤 Профиль <b>{message.from_user.first_name}</b>

💰 Баланс: {info["balance"]} $
💳 Всего продаж: {info["sale"]}
💸 Общая сумма продаж: {info["all_sale"]} $
--------------------------------------------------
📄 Активных объявлений: {info["announcements"]}
✏️ Объявлений на проверке: {info["examination"]}
🛒 Всего покупок: {info["purchases"]}
""", reply_markup=markup)


# ==================== ФУНКЦИЯ ГЕНЕРАЦИИ СТРАНИЦЫ ИСТОРИИ ====================

async def get_story_page_markup(user_id: int, page: int = 1):
    """Генерация клавиатуры 3х3 с ID каналов и кнопками переключения страниц"""
    # Получаем список всех проданных каналов пользователя
    stories = await DBstory.return_story_by_user_id(user_id)

    if not stories:
        return "📭 У вас еще нет проданных каналов.", None

    ITEMS_PER_PAGE = 9
    total_items = len(stories)
    total_pages = (total_items + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE

    if page < 1:
        page = 1
    elif page > total_pages:
        page = total_pages

    # Получаем элементы для текущей страницы
    start_idx = (page - 1) * ITEMS_PER_PAGE
    end_idx = start_idx + ITEMS_PER_PAGE
    page_stories = stories[start_idx:end_idx]

    text = f"📊 <b>Ваши проданные каналы</b>\n"
    text += f"Выберите ID канала ниже, чтобы посмотреть подробную информацию по продаже.\n\n"
    text += f"<i>Страница {page} из {total_pages}</i>"

    builder = InlineKeyboardBuilder()

    # Заполняем сетку кнопками с ID
    for story in page_stories:
        builder.button(text=f"{story.channel_id}", callback_data=f"view_deal:{story.id}")

    # Выстраиваем кнопки строго в сетку 3х3
    builder.adjust(3)

    # Добавляем кнопки переключения страниц (Вперед / Назад)
    nav_buttons = []
    if page > 1:
        nav_buttons.append(InlineKeyboardButton(text="⬅️ Назад", callback_data=f"story_page:{page - 1}"))
    if page < total_pages:
        nav_buttons.append(InlineKeyboardButton(text="Вперед ➡️", callback_data=f"story_page:{page + 1}"))

    if nav_buttons:
        builder.row(*nav_buttons)

    # Кнопка возврата в личный кабинет
    builder.row(InlineKeyboardButton(text="🔙 В личный кабинет", callback_data="back_to_lk"))

    return text, builder.as_markup()


# ==================== ХЭНДЛЕРЫ ИСТОРИИ ПРОДАЖ ====================

@rt.callback_query(F.data == "story")
async def buy_channels_page_change(call: CallbackQuery, state: FSMContext):
    ban = await DBban.return_ban()
    if call.from_user.id in ban:
        await call.message.answer(f"Вы заблокированы!")
    else:
        """Вход в меню проданных каналов (Первая страница)"""
        await state.set_state(StoryStates.viewing_page)
        await state.update_data(current_page=1)

        text, markup = await get_story_page_markup(call.from_user.id, page=1)

        if markup:
            await call.message.edit_text(text, reply_markup=markup)
        else:
            await call.answer(text, show_alert=True)
        await call.answer()


@rt.callback_query(StoryStates.viewing_page, F.data.startswith("story_page:"))
async def change_story_page(call: CallbackQuery, state: FSMContext):
    ban = await DBban.return_ban()
    if call.from_user.id in ban:
        await call.message.answer(f"Вы заблокированы!")
    else:
        """Переключение между страницами истории"""
        page = int(call.data.split(":")[1])
        await state.update_data(current_page=page)

        text, markup = await get_story_page_markup(call.from_user.id, page=page)
        await call.message.edit_text(text, reply_markup=markup)
        await call.answer()


@rt.callback_query(StoryStates.viewing_page, F.data.startswith("view_deal:"))
async def view_deal_details(call: CallbackQuery, state: FSMContext):
    ban = await DBban.return_ban()
    if call.from_user.id in ban:
        await call.message.answer(f"Вы заблокированы!")
    else:
        """Вывод полной информации по выбранной продаже"""
        deal_id = int(call.data.split(":")[1])

        # Получаем информацию о конкретной записи из бд
        story = await DBstory.return_story_by_id(deal_id)

        if not story:
            await call.answer("⚠️ Сделка не найдена.", show_alert=True)
            await call.answer()
            return

        # Формируем полный текст со всеми имеющимися данными
        text = f"📄 <b>Информация о сделке <code>#{story['channel_id']}</code></b>\n"
        text += "--------------------------------------------------\n"
        text += f"📺 <b>Название:</b> {story['name']}\n"
        text += f"🔗 <b>Ссылка на канал:</b> {story['url']}\n"
        text += "--------------------------------------------------\n"
        text += f"💰 <b>Цена продажи:</b> {story['selling_price']} $\n"
        text += f"💸 <b>Получено чистыми:</b> {story['total_amount']} $\n"

        # Кнопка возврата обратно к списку (учитывая страницу, на которой находился юзер)
        data = await state.get_data()
        back_page = data.get("current_page", 1)

        markup = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Вернуться к списку", callback_data=f"story_page:{back_page}")]
        ])

        await call.message.edit_text(text, reply_markup=markup, disable_web_page_preview=True)
        await call.answer()


async def get_announcements_page_markup(user_id: int, page: int = 1):
    """Генерация клавиатуры 3х3 с ID объявлений и кнопками переключения страниц"""
    # Получаем список всех активных объявлений пользователя
    channels = await DBchannels.get_channels_by_user(user_id)

    if not channels:
        return "📭 У вас еще нет активных объявлений.", None

    ITEMS_PER_PAGE = 9
    total_items = len(channels)
    total_pages = (total_items + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE

    if page < 1:
        page = 1
    elif page > total_pages:
        page = total_pages

    # Получаем элементы для текущей страницы
    start_idx = (page - 1) * ITEMS_PER_PAGE
    end_idx = start_idx + ITEMS_PER_PAGE
    page_channels = channels[start_idx:end_idx]

    text = f"📊 <b>Ваши активные объявления</b>\n"
    text += f"Выберите ID канала ниже, чтобы посмотреть подробную информацию.\n\n"
    text += f"<i>Страница {page} из {total_pages}</i>"

    builder = InlineKeyboardBuilder()

    # Заполняем сетку кнопками с ID
    for ch in page_channels:
        # Если статус == 0, добавляем "(проверка)" к названию кнопки
        status_text = " (проверка)" if getattr(ch, 'status', None) == 0 else ""
        builder.button(text=f"{ch.id}{status_text}", callback_data=f"view_ann:{ch.id}")

    # Выстраиваем кнопки строго в сетку 3х3
    builder.adjust(3)

    # Добавляем кнопки переключения страниц (Вперед / Назад)
    nav_buttons = []
    if page > 1:
        nav_buttons.append(InlineKeyboardButton(text="⬅️ Назад", callback_data=f"ann_page:{page - 1}"))
    if page < total_pages:
        nav_buttons.append(InlineKeyboardButton(text="Вперед ➡️", callback_data=f"ann_page:{page + 1}"))

    if nav_buttons:
        builder.row(*nav_buttons)

    # Кнопка возврата в личный кабинет
    builder.row(InlineKeyboardButton(text="🔙 В личный кабинет", callback_data="back_to_lk"))

    return text, builder.as_markup()


@rt.callback_query(F.data == "back_to_lk")
async def back_to_profile(call: CallbackQuery, state: FSMContext):
    ban = await DBban.return_ban()
    if call.from_user.id in ban:
        await call.message.answer(f"Вы заблокированы!")
    else:
        """Возврат в корень личного кабинета"""
        await state.clear()  # Сбрасываем FSM состояние пагинации

        info = await DBuser.return_all_info(call.from_user.id)
        markup = await create_markup('inline', [[['📝 Мои объявления', f"my_announcements"],
                                                 ["💸 Проданные каналы", "story"]], [["💰 Вывод", "withdrawal"]]])

        await call.message.edit_text(f"""👤 Профиль <b>{call.from_user.first_name}</b>

💰 Баланс: {info["balance"]} $
💳 Всего продаж: {info["sale"]}
💸 Общая сумма продаж: {info["all_sale"]} $
--------------------------------------------------
📄 Активных объявлений: {info["announcements"]}
✏️ Объявлений на проверке: {info["examination"]}
🛒 Всего покупок: {info["purchases"]}
""", reply_markup=markup)
        await call.answer()


@rt.callback_query(F.data == "my_announcements")
async def show_my_announcements_page(call: CallbackQuery, state: FSMContext):
    ban = await DBban.return_ban()
    if call.from_user.id in ban:
        await call.message.answer(f"Вы заблокированы!")
    else:
        """Вход в меню активных объявлений (Первая страница)"""
        await state.set_state(AnnouncementStates.viewing_page)
        await state.update_data(current_page=1)

        text, markup = await get_announcements_page_markup(call.from_user.id, page=1)

        if markup:
            await call.message.edit_text(text, reply_markup=markup)
        else:
            await call.answer(text, show_alert=True)
        await call.answer()


@rt.callback_query(AnnouncementStates.viewing_page, F.data.startswith("ann_page:"))
async def change_announcements_page(call: CallbackQuery, state: FSMContext):
    ban = await DBban.return_ban()
    if call.from_user.id in ban:
        await call.message.answer(f"Вы заблокированы!")
    else:
        """Переключение между страницами активных объявлений"""
        page = int(call.data.split(":")[1])
        await state.update_data(current_page=page)

        text, markup = await get_announcements_page_markup(call.from_user.id, page=page)
        await call.message.edit_text(text, reply_markup=markup)
        await call.answer()


@rt.callback_query(AnnouncementStates.viewing_page, F.data.startswith("view_ann:"))
async def view_announcement_details(call: CallbackQuery, state: FSMContext):
    ban = await DBban.return_ban()
    if call.from_user.id in ban:
        await call.message.answer(f"Вы заблокированы!")
    else:
        """Отображение подробной информации об объявлении из таблицы Channels"""
        ann_id = int(call.data.split(":")[1])

        # Запрашиваем список каналов пользователя через правильный класс DBchannels
        channels = await DBchannels.get_channels_by_user(call.from_user.id)
        channel = next((ch for ch in channels if ch.id == ann_id), None)

        if not channel:
            await call.answer("❌ Объявление не найдено.", show_alert=True)
            return

        # --- Чтение файла из папки (data) ---
        file_content = "Файл пуст или отсутствует"

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
        text += f"💳 <b>Итоговая сумма:</b> {channel.total_amount} $\n"

        # Создаем клавиатуру возврата
        builder = InlineKeyboardBuilder()
        builder.row(InlineKeyboardButton(
            text="✏️ Изменить информацию",
            callback_data=f"edit_ann:{channel.id}"
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


@rt.callback_query(AnnouncementStates.viewing_page, F.data.startswith("edit_ann:"))
async def process_edit_announcement(call: CallbackQuery, state: FSMContext):
    ban = await DBban.return_ban()
    if call.from_user.id in ban:
        await call.message.answer(f"Вы заблокированы!")
    else:
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
        await state.set_state(AnnouncementStates.edit_info)

        commission = await DBuser.return_commission(user_id)

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
https://www.youtube.com;Dark;10000;44300;готовка еды;Китай;нет;0;100

<b>Внимание!</b> Комиссия составляет {commission}%""", reply_markup=markup)
        await call.answer()


@rt.message(AnnouncementStates.edit_info)
async def save_edited_announcement_info(message: Message, state: FSMContext):
    markup = await create_markup('inline', [[['❌ Отмена', f"back"]]])
    text = message.text
    try:
        split = text.split(";")
        if len(split) > 10 or len(split) < 9 or split[2].isdigit() == False or split[3].isdigit() == False or split[7].isdigit() == False or split[8].isdigit() == False or (split[6] != "да" and split[6] != "нет"):
            await message.answer(f"Проверьте валидность введенных данных и введите еще раз", reply_markup=markup)
            await state.set_state(AnnouncementStates.edit_info)
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
            await state.set_state(UserState.data_channel_update)
    except:
        await message.answer(f"Проверьте валидность введенных данных и введите еще раз", reply_markup=markup)
        await state.set_state(AnnouncementStates.edit_info)


@rt.message(UserState.data_channel_update, F.document)
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
    commission = await DBuser.return_commission(message.from_user.id)
    markup = await create_markup('inline', [[["✅ Изменить канал", "go_sell_update"]],
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
💰 Желаемая цена продажи: {data["price"]} $ ({data["price"]} - {commission}% = {float(data["price"]) - (float(data["price"]) * (float(commission / 100)))} $ Итоговый рассчет)
📝 Дополнительное описание: {data["description"]}

Данные которые получит покупатель:
{file_text}""", reply_markup=markup)


@rt.callback_query(F.data == "back_document_update")
async def cancel_and_delete_file(callback: CallbackQuery, state: FSMContext):
    ban = await DBban.return_ban()
    if callback.from_user.id in ban:
        await callback.message.answer(f"Вы заблокированы!")
    else:
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

@rt.message(UserState.data_channel_update)
async def sell_file_invalid(message: Message):
    markup = await create_markup('inline', [[['❌ Отмена', f"back"]]])
    await message.answer("Ожидается файл .txt", reply_markup=markup)


@rt.callback_query(F.data == "go_sell_update")
async def admin_payout_handler(call: CallbackQuery, state: FSMContext):
    ban = await DBban.return_ban()
    if call.from_user.id in ban:
        await call.message.answer(f"Вы заблокированы!")
    else:
        data = await state.get_data()
        commission = await DBuser.return_commission(call.from_user.id)
        total = float(data["price"]) - (float(data["price"]) * (float(commission / 100)))
        channel_id = await DBchannels.update_channel_info(data["editing_ann_id"], data["url"], data["name"],
                                                      data["subscribers"], data["views"],
                                                      data["topic"], data["country"],
                                                      data["monetization"], data["income"],
                                                      data["price"], data["description"], f"{call.from_user.id}.txt", total)

        old_channel_file = os.path.join("channel", f"{call.from_user.id}_{data["editing_ann_id"]}.txt")

        try:
            if os.path.exists(old_channel_file):
                os.remove(old_channel_file)
        except Exception as e:
            print(f"Ошибка при удалении старого файла {old_channel_file}: {e}")

        await call.message.answer("""Ваше объявление отправлено на проверку администратору.

Вы получите уведомление о статусе объявления. 
Если объявление будет опубликовано, оно появится в вашем профиле.""")
        await DBuser.update_user_examination_plus(call.from_user.id)
        await DBuser.update_user_announcements_minus(call.from_user.id)
        markup = await create_markup('inline', [[["✅ Выставить на продажу", f"publish_{data["editing_ann_id"]}"]],
                                                [['❌ Отклонить', f"reject_{data["editing_ann_id"]}"]]])
        file_path = os.path.join("examination", f"{call.from_user.id}.txt")
        document = FSInputFile(file_path, filename="data.txt")
        for i in admins_id:
            await bot.send_document(chat_id=i, caption=f"""Новая заявка #{data["editing_ann_id"]} на <b>обновление канала</b>
Пользователь @{call.from_user.username}
id: {call.from_user.id}

Проверьте данные:

Ссылка на YouTube-канал: {data["url"]}
Название канала: {data["name"]}
Количество подписчиков: {data["subscribers"]}
Количество просмотров: {data["views"]}
Тематика: {data["topic"]}
Страна/язык аудитории: {data["country"]}
Монетизация: {data["monetization"]}
Желаемая цена продажи: {data["price"]} $ ({data["price"]} - {commission}% = {total} $ Итоговый рассчет)
Желаемая цена продажи: {data["price"]} $
Дополнительное описание: {data["description"]}""", reply_markup=markup, document=document)
        await state.clear()


@rt.callback_query(F.data == "withdrawal")
async def admin_payout_handler(call: CallbackQuery, state: FSMContext):
    ban = await DBban.return_ban()
    if call.from_user.id in ban:
        await call.message.answer(f"Вы заблокированы!")
    else:
        status = await DBuser.return_user_status(call.from_user.id)
        balance = await DBuser.return_user_balance(call.from_user.id)
        if round(balance) != 0:
            if status == 0:
                markup = await create_markup('inline', [[['❌ Отмена', "back"]]])
                await call.message.answer(f"<b>Введите ваш кошелек и сеть для вывода</b>\n Пример: USDT erc20 0x5346b564102d261fe6a37d388ea93ceeece1547b \n\n <b>Выводятся все средства с баланса!</b>", reply_markup=markup)
                await state.set_state(UserState.wallet)
            else:
                await call.message.answer(f"<b>Ваши средства сейчас находятся в выводе. Пожалуйста ожидайте уведомления!</b>")
        else:
            await call.message.answer(f"<b>Ваш баланс равен 0!</b>")
            await state.clear()


@rt.message(UserState.wallet)
async def admin_payout_handler(message: Message, state: FSMContext):
    user = await DBuser.return_all_info(message.from_user.id)
    markup = await create_markup('inline', [[["✅ Выплачено", f"paid_{message.from_user.id}"], ['❌ Отмена', f"cancell_{message.from_user.id}"]]])
    for i in admins_id:
        await bot.send_message(chat_id=i, text=f"""Новая заявка на вывод средств

Пользователь: {message.from_user.id}
Сумма: {user["balance"]}
Кошелек: {message.text}""", reply_markup=markup)
    await message.answer(f"<b>Средства находятся в статусе вывода. Ожидайте уведомление</b>")
    await DBuser.update_user_status_one(message.from_user.id)
    await state.clear()