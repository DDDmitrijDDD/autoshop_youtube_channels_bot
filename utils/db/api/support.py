# Импортируйте AsyncSessionLocal и модель Support из вашего файла с моделями
from utils.db.api.db import AsyncSessionLocal, Support
from sqlalchemy import select

class DBsupport:
    @staticmethod
    async def update_support(new_support):
        async with AsyncSessionLocal() as session:
            try:
                # Асинхронно получаем запись техподдержки с id=1
                result = await session.execute(select(Support).filter_by(id=1))
                support = result.scalar_one_or_none()
                if support:
                    support.url = new_support
                    await session.commit()
                    print(f"Ссылка на техподдержку успешно обновлена: {new_support}")
            except Exception as e:
                await session.rollback()
                print(f"Ошибка при обновлении ссылки техподдержки: {e}")
                raise e

    @staticmethod
    async def return_support():
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(Support).filter_by(id=1))
            support = result.scalar_one_or_none()
            return support.url
