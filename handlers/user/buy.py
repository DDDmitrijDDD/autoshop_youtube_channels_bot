from pprint import pprint

from aiogram import F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, Document, FSInputFile
from data.config import admins_id
from data.loader import rt, bot
from utils.db.api.ban import DBban
from utils.db.api.statistics import DBstatistics
from utils.db.api.story import DBstory
from utils.db.api.users import DBuser
from utils.system.inline_btns import create_markup
from utils.db.api.channels import DBchannels
from handlers.user.start import UserState
import os
from aiogram.utils.keyboard import InlineKeyboardBuilder
from data.crypto_api import check_check, create_check, delete_check


# Вспомогательная функция для генерации постраничной клавиатуры 3х3
async def get_channels_keyboard(channels, page: int = 1):
    builder = InlineKeyboardBuilder()

    # Лимит каналов на одной странице
    limit = 9
    start_index = (page - 1) * limit
    end_index = start_index + limit

    # Берем каналы только для текущей страницы
    page_channels = channels[start_index:end_index]

    # Добавляем кнопки каналов
    for channel in page_channels:
        # Текст кнопки: "ID - Цена$" (например: "1 - 100$")
        button_text = f"{channel.id} — {channel.price}$"
        # callback_data содержит id канала для последующего открытия карточки
        builder.button(text=button_text, callback_data=f"buy_channel_{channel.id}")

    # Настраиваем сетку для каналов: по 3 кнопки в ряд
    builder.adjust(3)

    # Формируем навигационную строку (последний ряд со стрелками)
    nav_buttons = []

    # Если мы не на первой странице, добавляем стрелку "Назад"
    if page > 1:
        nav_buttons.append(builder.button(text="⬅️ Назад", callback_data=f"buy_page_{page - 1}").button)

    # Если есть каналы дальше текущей страницы, добавляем стрелку "Вперед"
    if len(channels) > end_index:
        nav_buttons.append(builder.button(text="Вперед ➡️", callback_data=f"buy_page_{page + 1}").button)

    # Если навигационные кнопки появились, принудительно размещаем их в самом низу
    if nav_buttons:
        builder.adjust(*([3] * ((len(page_channels) + 2) // 3)), len(nav_buttons))

    return builder.as_markup()


# 1. Хэндлер на нажатие кнопки "🎬 Купить канал"
@rt.message(F.text == "🎬 Купить канал")
async def buy_channels_start(message: Message, state: FSMContext):
    ban = await DBban.return_ban()
    if message.from_user.id in ban:
        await message.answer(f"Вы заблокированы!")
    else:
        # Получаем все каналы со статусом 1 из БД
        all_channels = await DBchannels.get_active_channels()

        # Исключаем каналы, которые принадлежат текущему пользователю
        # (Предполагается, что в объекте channel ID создателя лежит в поле user_id или owner_id)
        channels = [ch for ch in all_channels if ch.user_id != message.from_user.id]

        if not channels:
            await message.answer("😔 К сожалению, в данный момент нет доступных каналов для продажи.")
            return

        # Генерируем клавиатуру для первой страницы
        reply_markup = await get_channels_keyboard(channels, page=1)

        await message.answer(
            "🎬 **Выбери интересующий канал из списка ниже:**\n"
            "_(Кнопки подписаны в формате: ID — Цена)_",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )


# 2. Callback-хэндлер для переключения страниц пагинации
@rt.callback_query(F.data.startswith("buy_page_"))
async def buy_channels_page_change(call: CallbackQuery):
    ban = await DBban.return_ban()
    if call.from_user.id in ban:
        await call.message.answer(f"Вы заблокированы!")
    else:
        # Достаем номер страницы из callback_data
        page = int(call.data.split("_")[2])

        # Снова запрашиваем актуальный список каналов
        all_channels = await DBchannels.get_active_channels()

        # Точно так же исключаем каналы текущего пользователя
        channels = [ch for ch in all_channels if ch.user_id != call.from_user.id]

        if not channels:
            await call.message.edit_text("😔 К сожалению, все доступные каналы были распроданы.")
            await call.answer()
            return

        # Генерируем клавиатуру для новой страницы
        reply_markup = await get_channels_keyboard(channels, page=page)

        # Редактируем текущее сообщение, меняя только страницу клавиатуры
        await call.message.edit_text(
            f"🎬 **Выбери интересующий канал из списка ниже (Страница {page}):**\n"
            "_(Кнопки подписаны в формате: ID — Цена)_",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        await call.answer()



@rt.callback_query(F.data.startswith("buy_channel_"))
async def buy_channels_page_change(call: CallbackQuery, state: FSMContext):
    ban = await DBban.return_ban()
    if call.from_user.id in ban:
        await call.message.answer(f"Вы заблокированы!")
    else:
        markup = await create_markup('inline', [[["✅ Купить", "buy"]], [['❌ Отмена', f"back"]]])
        ids = int(call.data.split("_")[2])
        channel = await DBchannels.return_all_info_by_channel_id(ids)
        await state.update_data(ids=ids, txt=channel["data"], price=channel["price"])
        if channel["description"] == "-":
            description = ""
        else:
            description = f"📝 <b>Дополнительное описание:</b> {channel["description"]}"
        if channel["income"] == 0:
            income = ""
        else:
            income = f"🪙 <b>Показатели монетизации:</b> {channel["income"]} $"
        await call.message.answer(f"""<b>Канал</b> <code>#{ids}</code>
--------------------------------------------------
🔗 <b>Ссылка:</b> {channel["url"]}
📺 <b>Название канала:</b> {channel["name"]}
👥 <b>Количество подписчиков:</b> {channel["subscribers"]}
👁 <b>Количество просмотров:</b> {channel["views"]}
🏷 <b>Тематика:</b> {channel["topic"]}
🌍 <b>Язык аудитории:</b> {channel["country"]}
💸 <b>Монетизация:</b> {channel["monetization"]}
{income}
--------------------------------------------------
💰 <b>Цена продажи:</b> {channel["price"]} $
{description}""", reply_markup=markup)


@rt.callback_query(F.data == "buy")
async def buy_channels_page_change(call: CallbackQuery, state: FSMContext):
    ban = await DBban.return_ban()
    if call.from_user.id in ban:
        await call.message.answer(f"Вы заблокированы!")
    else:
        await bot.delete_message(chat_id=call.from_user.id, message_id=call.message.message_id)
        data = await state.get_data()
        url = await create_check(data["price"])
        uuid = url["result"]["uuid"]
        await state.update_data(uuid=uuid, url=url["result"]["link"], aa=url)
        markup = await create_markup('inline', [[["Оплатите счет", f"{url["result"]["link"]}"]],
                                                [["✅ Оплатил", "access_buy"],['❌ Отмена', f"cancel_buy"]]])
        await call.message.answer(f"<b>Оплатите заказ и подтвердите покупку</b>", reply_markup=markup)



@rt.callback_query(F.data == "cancel_buy")
async def buy_channels_page_change(call: CallbackQuery, state: FSMContext):
    ban = await DBban.return_ban()
    if call.from_user.id in ban:
        await call.message.answer(f"Вы заблокированы!")
    else:
        await bot.delete_message(chat_id=call.from_user.id, message_id=call.message.message_id)
        data = await state.get_data()
        a = await delete_check(data["uuid"])
        await state.clear()


import os
from aiogram.types import FSInputFile


@rt.callback_query(F.data == "access_buy")
async def buy_channels_page_change(call: CallbackQuery, state: FSMContext):
    ban = await DBban.return_ban()
    if call.from_user.id in ban:
        await call.message.answer(f"Вы заблокированы!")
    else:
        await bot.delete_message(chat_id=call.from_user.id, message_id=call.message.message_id)
        data = await state.get_data()
        check = await check_check(data["uuid"])
        status = check["result"][0]["status"]
        markup = await create_markup('inline', [[["Оплатите счет", f"{data["url"]}"]],
                                                [["✅ Оплатил", "access_buy"], ['❌ Отмена', f"cancel_buy"]]])
        if status == "created" or status == "partial":
            await call.message.answer(f"<b>Вы не оплатили счет!</b>", reply_markup=markup)
        else:

            # Извлекаем путь/название файла и ID канала из состояния
            file_name_or_path = data.get("txt")
            channel_id = data.get("ids")

            if not channel_id:
                await call.answer("⚠️ Ошибка: Данные о канале не найдены в состоянии.", show_alert=True)
                return

            # Корректируем путь к файлу (если в txt хранится только имя файла)
            if file_name_or_path and not file_name_or_path.startswith("channel"):
                file_path = os.path.join("channel", file_name_or_path)
            else:
                file_path = file_name_or_path

            # 1. Проверяем, существует ли файл физически на сервере
            if file_path and os.path.exists(file_path):
                # Готовим файл к отправке
                document = FSInputFile(file_path, filename=f"credentials_channel_{channel_id}.txt")
                channel = await DBchannels.return_all_info_by_channel_id(channel_id)
                if channel["description"] == "-":
                    description = ""
                else:
                    description = f"📝 <b>Дополнительное описание:</b> {channel["description"]}"
                if channel["income"] == 0:
                    income = ""
                else:
                    income = f"🪙 <b>Показатели монетизации:</b> {channel["income"]} $"
                # Отправляем сообщение об успешной покупке и сам файл
                await call.message.answer(f"""✅ <b>Канал <code>#{channel_id}</code> был успешно куплен!</b>
--------------------------------------------------
🔗 <b>Ссылка:</b> {channel["url"]}
📺 <b>Название канала:</b> {channel["name"]}
👥 <b>Количество подписчиков:</b> {channel["subscribers"]}
👁 <b>Количество просмотров:</b> {channel["views"]}
🏷 <b>Тематика:</b> {channel["topic"]}
🌍 <b>Язык аудитории:</b> {channel["country"]}
💸 <b>Монетизация:</b> {channel["monetization"]}
{income}
--------------------------------------------------
💰 <b>Цена продажи:</b> {channel["price"]} $
{description}""")
                await call.message.answer_document(
                    document=document,
                    caption="📂 Вот ваши данные для доступа к купленному аккаунту. Сохраните их!"
                )
                # 2. УДАЛЕНИЕ ФАЙЛА С ДИСКА (так как данные переданы покупателю)
                try:
                    os.remove(file_path)
                except Exception as e:
                    print(f"Ошибка при удалении файла {file_path} после покупки: {e}")

                # 3. УДАЛЕНИЕ ЗАПИСИ ИЗ БАЗЫ ДАННЫХ
                try:
                    if channel["total_amount"] != -1:
                        await bot.send_message(chat_id=channel["user_id"], text=f"""Аккаунт <code>{channel_id}</code> купили!
        
Ваш баланс пополнен на {channel["total_amount"]} $""")
                        for i in admins_id:
                            await bot.send_message(chat_id=i, text=f"""Пользователь продал аккаунт <code>{channel_id}</code>!
    
Сумма платежа {channel["price"]} $""")
                        await DBuser.update_purchases(call.from_user.id)
                        await DBstory.add_new_story(channel["user_id"], channel["url"], channel["name"], channel["price"], channel["total_amount"], channel_id)
                        await DBuser.update_user_announcements_minus(channel["user_id"])
                        await DBuser.update_user_sum(channel["user_id"], float(channel["total_amount"]))
                        await DBstatistics.listing_minus()
                        await DBstatistics.update_sum(float(channel["price"]))
                        await DBchannels.delete_channel(int(channel_id))
                    else:
                        await bot.send_message(chat_id=channel["user_id"], text=f"""Аккаунт <code>{channel_id}</code> купили!
        
Вы получили {channel["price"]} $""")
                        await DBstatistics.update_sum(float(channel["price"]))
                        await DBchannels.delete_channel(int(channel_id))
                except Exception as e:
                    print(f"Ошибка при удалении канала #{channel_id} из БД: {e}")

            else:
                # Если файла почему-то не оказалось на месте
                await call.message.answer(
                    f"✅ Канал <code>#{channel_id}</code> куплен, но произошла ошибка при отправке файла с данными. "
                    f"Пожалуйста, немедленно свяжитесь с администрацией."
                )
                print(f"Критическая ошибка: Файл {file_path} отсутствует на сервере при покупке!")

            # Отвечаем на callback-запрос, чтобы убрать анимацию загрузки на кнопке
            await call.answer()

            # Полностью очищаем состояние покупателя
            await state.clear()
