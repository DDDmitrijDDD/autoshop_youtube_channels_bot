# Импортируйте AsyncSessionLocal и модель Statistics из вашего файла с моделями
from utils.db.api.db import AsyncSessionLocal, Statistics
from sqlalchemy import select


class DBstatistics:
    @staticmethod
    async def add_new_user():
        async with AsyncSessionLocal() as session:
            try:
                result = await session.execute(select(Statistics).filter_by(id=1))
                stat = result.scalar_one_or_none()
                if stat:
                    stat.users += 1
                    await session.commit()
            except Exception as e:
                await session.rollback()
                print(f"Ошибка при добавлении пользователя в статистику: {e}")

    @staticmethod
    async def update_sum(amount):
        async with AsyncSessionLocal() as session:
            try:
                result = await session.execute(select(Statistics).filter_by(id=1))
                stat = result.scalar_one_or_none()
                if stat:
                    stat.all_sale += amount
                    stat.sale_day += amount
                    stat.sale_month += amount
                    stat.sale_week += amount
                    await session.commit()
            except Exception as e:
                await session.rollback()
                print(f"Ошибка при обновлении сумм продаж в статистике: {e}")

    @staticmethod
    async def listing_plus():
        async with AsyncSessionLocal() as session:
            try:
                result = await session.execute(select(Statistics).filter_by(id=1))
                stat = result.scalar_one_or_none()
                if stat:
                    stat.all_listings += 1
                    await session.commit()  # Добавлено сохранение в БД
            except Exception as e:
                await session.rollback()
                print(f"Ошибка при увеличении счетчика листингов: {e}")

    @staticmethod
    async def listing_minus():
        async with AsyncSessionLocal() as session:
            try:
                result = await session.execute(select(Statistics).filter_by(id=1))
                stat = result.scalar_one_or_none()
                if stat:
                    stat.all_listings -= 1
                    await session.commit()  # Добавлено сохранение в БД
            except Exception as e:
                await session.rollback()
                print(f"Ошибка при уменьшении счетчика листингов: {e}")

    @staticmethod
    async def return_all_info():
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(Statistics).filter_by(id=1))
            stat = result.scalar_one_or_none()
            if not stat:
                return None

            return {
                "users": stat.users,
                "all_sale": stat.all_sale,
                "all_listings": stat.all_listings,
                "sale_day": stat.sale_day,  # Исправлено: возвращается корректное поле sale_day вместо all_sale
                "sale_week": stat.sale_week,
                "sale_month": stat.sale_month
            }
