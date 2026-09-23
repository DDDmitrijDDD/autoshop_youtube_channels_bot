# Импортируйте AsyncSessionLocal и модель Ban из вашего файла с моделями
from utils.db.api.db import AsyncSessionLocal, Sales
from sqlalchemy import select


class DBsales:
    @staticmethod
    async def sales_on():
        async with AsyncSessionLocal() as session:
            try:
                # Асинхронно получаем первую запись (с id=1, созданную при seed)
                result = await session.execute(select(Sales).filter_by(id=1))
                sales = result.scalar_one_or_none()
                if sales:
                    sales.sales = 1
                    await session.commit()
            except Exception as e:
                await session.rollback()
                print(f"Ошибка при обновлении комиссии: {e}")
                raise e

    @staticmethod
    async def sales_off():
        async with AsyncSessionLocal() as session:
            try:
                # Асинхронно получаем первую запись (с id=1, созданную при seed)
                result = await session.execute(select(Sales).filter_by(id=1))
                sales = result.scalar_one_or_none()
                if sales:
                    sales.sales = 0
                    await session.commit()
            except Exception as e:
                await session.rollback()
                print(f"Ошибка при обновлении комиссии: {e}")
                raise e

    @staticmethod
    async def return_sales():
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(Sales))
            sales = result.scalar_one_or_none()
            return int(sales.sales)
