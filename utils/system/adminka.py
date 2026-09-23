from aiogram.filters import BaseFilter
from aiogram.types import Message
from data.config import admins_id


class AdminIs(BaseFilter):
    """проверка на админ или нет"""
    async def __call__(self, message: Message) -> bool:
        if message.from_user.id in admins_id:
            return True
        return False
