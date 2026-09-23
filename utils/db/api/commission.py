# Импортируйте AsyncSessionLocal и модель Commission из вашего файла с моделями
from utils.db.api.db import AsyncSessionLocal, Commission
from sqlalchemy import select

class DBcommission:
    @staticmethod
    async def update_commission(new_com):
        async with AsyncSessionLocal() as session:
            try:
                # Асинхронно получаем первую запись (с id=1, созданную при seed)
                result = await session.execute(select(Commission).filter_by(id=1))
                com = result.scalar_one_or_none()
                if com:
                    com.commission = new_com
                    await session.commit()
            except Exception as e:
                await session.rollback()
                print(f"Ошибка при обновлении комиссии: {e}")
                raise e

    @staticmethod
    async def return_commission():
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(Commission).filter_by(id=1))
            com = result.scalar_one_or_none()
            # Если запись вдруг не найдена, возвращаем дефолтное значение 10
            return com.commission if com else 10
