from aiogram.types import (KeyboardButton,
                           ReplyKeyboardMarkup,
                           ReplyKeyboardRemove,
                           InlineKeyboardButton,
                           InlineKeyboardMarkup)
import validators


async def create_markup(tip, keyboard):
    """
    создание кнопок
    :param tip: "inline" or "reply"
    :param keyboard: [ [ ["lol", "kek"] ] , [ ["as", "among"] , ["ooo", "aaa"] ] ]
    :return: готовый markup
    """
    if tip == 'inline':
        markup = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=lvl2[0], url=lvl2[1])
                                                        if ":tg:" in lvl2 or validators.url(lvl2[1])
                                                        else InlineKeyboardButton(text=lvl2[0], callback_data=lvl2[1])
                                                        for lvl2 in lvl1] for lvl1 in keyboard])

    else:
        markup = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text=lvl2[0]) for lvl2 in lvl1] for lvl1 in keyboard],
                                     resize_keyboard=True)
    return markup


async def remove_markup():
    """удаение reply-markup"""
    markup = ReplyKeyboardRemove()
    return markup
