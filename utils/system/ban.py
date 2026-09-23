from aiogram.filters import BaseFilter
from aiogram.types import Message

from utils.db.api.db import DBuser


class BanIs(BaseFilter):
    """проверка на админ или нет"""
    async def __call__(self, message: Message) -> bool:
        print(await DBuser.return_ban())
        if message.from_user.id in DBuser.return_ban():
            return True
        return False
