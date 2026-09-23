from aiogram import F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, Document, FSInputFile
from data.config import admins_id
from data.loader import rt, bot
from utils.db.api.ban import DBban
from utils.db.api.sales import DBsales
from utils.db.api.users import DBuser
from utils.system.inline_btns import create_markup
from utils.db.api.channels import DBchannels
from utils.db.api.commission import DBcommission
from handlers.user.start import UserState
import os


@rt.message(F.text == "➕ Продать канал")
async def sell(message: Message, state: FSMContext):
    ban = await DBban.return_ban()
    if message.from_user.id in ban:
        await message.answer(f"Вы заблокированы!")
    else:
        sales = await DBsales.return_sales()
        if sales == 1:
            user_id = message.from_user.id
            # Формируем путь к возможному файлу пользователя на проверке
            check_file_path = os.path.join("examination", f"{user_id}.txt")
            commission = await DBuser.return_commission(message.from_user.id)
            # 1. Проверяем, существует ли уже файл этого пользователя на модерации
            if os.path.exists(check_file_path):
                await message.answer(
                    "⚠️ Вы не можете выставить еще один канал, пока ваш предыдущий канал находится на проверке у администратора.",
                    parse_mode="Markdown"
                )
                return  # Прерываем выполнение функции, состояние не меняется

            # 2. Если файла нет, выполняем стандартную логику
            markup = await create_markup('inline', [[['❌ Отмена', "back"]]])
            await message.answer(f"""<b>Введите необходимую информацию через <code>;</code></b>
    
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
https://www.youtube.com;Dark;10000;44300;готовка еды;Китай;нет;0;100

<b>Внимание!</b> Комиссия составляет {commission}%""", reply_markup=markup)

            await state.set_state(UserState.info_channel)
        else:
            await message.answer(f"<b>На данный момент выставить канал на продажу нельзя</b>")

@rt.message(UserState.info_channel)
async def sell(message: Message, state: FSMContext):
    markup = await create_markup('inline', [[['❌ Отмена', f"back"]]])
    text = message.text
    try:
        split = text.split(";")
        if len(split) > 10 or len(split) < 9 or split[2].isdigit() == False or split[3].isdigit() == False or split[7].isdigit() == False or split[8].isdigit() == False or (split[6] != "да" and split[6] != "нет"):
            await message.answer(f"Проверьте валидность введенных данных и введите еще раз", reply_markup=markup)
            await state.set_state(UserState.info_channel)
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
            await state.set_state(UserState.data_channel)
    except:
        await message.answer(f"Проверьте валидность введенных данных и введите еще раз", reply_markup=markup)
        await state.set_state(UserState.info_channel)


@rt.message(UserState.data_channel, F.document)
async def sell(message: Message, state: FSMContext):
    markup = await create_markup('inline', [[['❌ Отмена', f"back"]]])
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
    markup = await create_markup('inline', [[["✅ Выставить на продажу", "go_sell"]],
                                            [['❌ Отмена', f"back_document"]]])
    await message.answer(f"""Проверьте данные:
    
🔗 <b>Ссылка на YouTube-канал:</b> {data["url"]}
📺 <b>Название канала:</b> {data["name"]}
👥 <b>Количество подписчиков:</b> {data["subscribers"]}
👁 <b>Количество просмотров:</b> {data["views"]}
🏷 <b>Тематика:</b> {data["topic"]}
🌍 <b>Страна/язык аудитории:</b> {data["country"]}
💸 <b>Монетизация:</b> {data["monetization"]}
🪙 <b>Доход/показатели монетизации:</b> {data["income"]} $
💰 <b>Желаемая цена продажи:</b> {data["price"]} $ ({data["price"]} - {commission}% = {float(data["price"]) - (float(data["price"]) * (float(commission / 100)))} $ Итоговый рассчет)
📝 <b>Дополнительное описание:</b> {data["description"]}

<b>Данные которые получит покупатель:</b>
{file_text}""", reply_markup=markup)


@rt.callback_query(F.data == "back_document")
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
        await callback.message.edit_text("❌ Выставление канала на продажу отменено.")

        # 5. Отвечаем на callback, чтобы убрать часики/загрузку с инлайн-кнопки
        await callback.answer()


@rt.message(UserState.data_channel)
async def sell_file_invalid(message: Message):
    markup = await create_markup('inline', [[['❌ Отмена', f"back"]]])
    await message.answer("Ожидается файл .txt", reply_markup=markup)


@rt.callback_query(F.data == "go_sell")
async def admin_payout_handler(call: CallbackQuery, state: FSMContext):
    ban = await DBban.return_ban()
    if call.from_user.id in ban:
        await call.message.answer(f"Вы заблокированы!")
    else:
        data = await state.get_data()
        commission = await DBuser.return_commission(call.from_user.id)
        total = float(data["price"]) - (float(data["price"]) * (float(commission / 100)))
        channel_id = await DBchannels.add_new_channel(call.from_user.id, data["url"], data["name"],
                                         data["subscribers"], data["views"],
                                         data["topic"], data["country"],
                                         data["monetization"], data["income"],
                                         data["price"], data["description"], f"{call.from_user.id}.txt", total)

        await call.message.answer("""Ваше объявление отправлено на проверку администратору.
    
Вы получите уведомление о статусе объявления. 
Если объявление будет опубликовано, оно появится в вашем профиле.""")
        await DBuser.update_user_examination_plus(call.from_user.id)
        markup = await create_markup('inline', [[["✅ Выставить на продажу", f"publish_{channel_id}"]],
                                                [['❌ Отклонить', f"reject_{channel_id}"]]])
        file_path = os.path.join("examination", f"{call.from_user.id}.txt")
        document = FSInputFile(file_path, filename="data.txt")
        for i in admins_id:
            await bot.send_document(chat_id=i, caption=f"""Новая заявка #{channel_id} на продажу
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