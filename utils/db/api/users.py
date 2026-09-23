# Импортируйте AsyncSessionLocal и модель User из вашего файла с моделями
from utils.db.api.db import AsyncSessionLocal, User
from sqlalchemy import select, update


class DBuser:
    @staticmethod
    async def all_user_id():
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(User))
            users = result.scalars().all()
            # Быстрый сбор ID через list comprehension
            return [user.user_id for user in users]

    @staticmethod
    async def add_new_user(user_id, user_name, full_name):
        async with AsyncSessionLocal() as session:
            try:
                user = User(user_id=user_id, user_name=user_name, full_name=full_name)
                session.add(user)
                await session.commit()
            except Exception as e:
                await session.rollback()
                print(f"Ошибка при добавлении нового пользователя {user_id}: {e}")
                raise e

    @staticmethod
    async def return_user_by_username(name):
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(User).filter_by(user_name=name))
            user = result.scalar_one_or_none()
            if not user:
                return None
            # Исправлено: заменено несуществующее поле user.id на user.user_id
            return [user.user_id, user.user_name, user.full_name, user.user_id]

    @staticmethod
    async def return_all_info(user_id):
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(User).filter_by(user_id=user_id))
            user = result.scalar_one_or_none()
            if not user:
                return None

            return {
                "user_name": user.user_name,
                "full_name": user.full_name,
                "balance": user.balance,
                "sale": user.sale,
                "all_sale": user.all_sale,
                "announcements": user.announcements,
                "examination": user.examination,
                "purchases": user.purchases,
                "status": user.status,
                "buy": user.buy,
                "commission": user.commission
            }

    @staticmethod
    async def update_user_sum(user_id, amount):
        async with AsyncSessionLocal() as session:
            try:
                result = await session.execute(select(User).filter_by(user_id=user_id))
                user = result.scalar_one_or_none()
                if user:
                    user.balance += amount
                    user.sale += 1
                    user.all_sale += amount
                    await session.commit()
            except Exception as e:
                await session.rollback()
                print(f"Ошибка при обновлении баланса пользователя {user_id}: {e}")

    @staticmethod
    async def update_purchases(user_id):
        async with AsyncSessionLocal() as session:
            try:
                result = await session.execute(select(User).filter_by(user_id=user_id))
                user = result.scalar_one_or_none()
                if user:
                    user.purchases += 1
                    await session.commit()
            except Exception as e:
                await session.rollback()
                print(f"Ошибка при обновлении покупок пользователя {user_id}: {e}")

    @staticmethod
    async def update_user_announcements_minus(user_id):
        async with AsyncSessionLocal() as session:
            try:
                result = await session.execute(select(User).filter_by(user_id=user_id))
                user = result.scalar_one_or_none()
                if user:
                    user.announcements -= 1
                    await session.commit()
            except Exception as e:
                await session.rollback()
                print(f"Ошибка при уменьшении объявлений пользователя {user_id}: {e}")

    @staticmethod
    async def update_user_announcements_plus(user_id):
        async with AsyncSessionLocal() as session:
            try:
                result = await session.execute(select(User).filter_by(user_id=user_id))
                user = result.scalar_one_or_none()
                if user:
                    user.announcements += 1
                    await session.commit()
            except Exception as e:
                await session.rollback()
                print(f"Ошибка при увеличении объявлений пользователя {user_id}: {e}")

    @staticmethod
    async def update_user_examination_minus(user_id):
        async with AsyncSessionLocal() as session:
            try:
                result = await session.execute(select(User).filter_by(user_id=user_id))
                user = result.scalar_one_or_none()
                if user:
                    user.examination -= 1
                    await session.commit()
            except Exception as e:
                await session.rollback()
                print(f"Ошибка при уменьшении проверок пользователя {user_id}: {e}")

    @staticmethod
    async def update_user_examination_plus(user_id):
        async with AsyncSessionLocal() as session:
            try:
                result = await session.execute(select(User).filter_by(user_id=user_id))
                user = result.scalar_one_or_none()
                if user:
                    user.examination += 1
                    await session.commit()
            except Exception as e:
                await session.rollback()
                print(f"Ошибка при увеличении проверок пользователя {user_id}: {e}")

    @staticmethod
    async def update_user_status_one(user_id):
        async with AsyncSessionLocal() as session:
            try:
                result = await session.execute(select(User).filter_by(user_id=user_id))
                user = result.scalar_one_or_none()
                if user:
                    user.status = 1
                    await session.commit()
            except Exception as e:
                await session.rollback()
                print(f"Ошибка при увеличении проверок пользователя {user_id}: {e}")

    @staticmethod
    async def update_user_status_null(user_id):
        async with AsyncSessionLocal() as session:
            try:
                result = await session.execute(select(User).filter_by(user_id=user_id))
                user = result.scalar_one_or_none()
                if user:
                    user.status = 0
                    await session.commit()
            except Exception as e:
                await session.rollback()
                print(f"Ошибка при увеличении проверок пользователя {user_id}: {e}")

    @staticmethod
    async def update_user_balance(user_id):
        async with AsyncSessionLocal() as session:
            try:
                result = await session.execute(select(User).filter_by(user_id=user_id))
                user = result.scalar_one_or_none()
                if user:
                    user.balance = 0
                    await session.commit()
            except Exception as e:
                await session.rollback()
                print(f"Ошибка при увеличении проверок пользователя {user_id}: {e}")

    @staticmethod
    async def update_commission_all(new_com):
        async with AsyncSessionLocal() as session:
            try:
                query = update(User).values(commission=new_com)

                await session.execute(query)
                await session.commit()

            except Exception as e:
                await session.rollback()
                print(f"Ошибка при обновлении комиссии для всех пользователей: {e}")
                raise e

    @staticmethod
    async def update_commission_one_user(user_id, new_com):
        async with AsyncSessionLocal() as session:
            try:
                # Асинхронно получаем первую запись (с id=1, созданную при seed)
                result = await session.execute(select(User).filter_by(user_id=user_id))
                com = result.scalar_one_or_none()
                if com:
                    com.commission = new_com
                    await session.commit()
            except Exception as e:
                await session.rollback()
                print(f"Ошибка при обновлении комиссии: {e}")
                raise e

    @staticmethod
    async def return_commission(user_id):
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(User).filter_by(user_id=user_id))
            com = result.scalar_one_or_none()
            return com.commission

    @staticmethod
    async def return_user_status(user_id):
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(User).filter_by(user_id=user_id))
            user = result.scalar_one_or_none()
            return user.status

    @staticmethod
    async def return_user_balance(user_id):
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(User).filter_by(user_id=user_id))
            user = result.scalar_one_or_none()
            return user.balance