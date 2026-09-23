# Импортируйте AsyncSessionLocal и модель Ban из вашего файла с моделями
from utils.db.api.db import AsyncSessionLocal, Ban
from sqlalchemy import select


class DBban:
    @staticmethod
    async def add_ban(user_id):
        async with AsyncSessionLocal() as session:
            try:
                ban = Ban(id=user_id)
                session.add(ban)
                await session.commit()
            except Exception as e:
                await session.rollback()
                print(f"Ошибка при добавлении бана для user_id {user_id}: {e}")
                raise e

    @staticmethod
    async def return_ban():
        async with AsyncSessionLocal() as session:
            # Используем await session.execute(select(...)) вместо session.query
            result = await session.execute(select(Ban))
            bans = result.scalars().all()

            # Быстрое создание списка через list comprehension
            return [ban.id for ban in bans]
