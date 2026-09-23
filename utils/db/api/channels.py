# Импортируйте AsyncSessionLocal и модель Channels из вашего файла с моделями
from utils.db.api.db import AsyncSessionLocal, Channels
from sqlalchemy import select


class DBchannels:
    @staticmethod
    async def add_new_channel(user_id, url, name, subscribers, views, topic, country,
                              monetization, income, price, description,
                              data, total):
        async with AsyncSessionLocal() as session:
            try:
                canal = Channels(
                    user_id=user_id, url=url, name=name,
                    subscribers=subscribers, views=views,
                    topic=topic, country=country, monetization=monetization,
                    income=income, price=price, description=description,
                    data=data, total_amount=total
                )
                session.add(canal)
                await session.commit()
                # Асинхронно обновляем объект, чтобы получить сгенерированный базой данных id
                await session.refresh(canal)
                return canal.id
            except Exception as e:
                await session.rollback()
                print(f"Ошибка при добавлении канала: {e}")
                raise e

    @staticmethod
    async def add_new_channel_admin(user_id, url, name, subscribers, views, topic, country,
                              monetization, income, price, description,
                              data):
        async with AsyncSessionLocal() as session:
            try:
                canal = Channels(
                    user_id=user_id, url=url, name=name,
                    subscribers=subscribers, views=views,
                    topic=topic, country=country, monetization=monetization,
                    income=income, price=price, description=description,
                    data="", total_amount=-1, status=1
                )
                session.add(canal)
                await session.commit()
                # Асинхронно обновляем объект, чтобы получить сгенерированный базой данных id
                await session.refresh(canal)
                new_data_name = f"{user_id}_{canal.id}.txt"
                canal.data = new_data_name
                await session.commit()
                return canal.id
            except Exception as e:
                await session.rollback()
                print(f"Ошибка при добавлении канала: {e}")
                raise e

    @staticmethod
    async def update_status(channel_id, file_path):
        async with AsyncSessionLocal() as session:
            try:
                result = await session.execute(select(Channels).filter_by(id=channel_id))
                channel = result.scalar_one_or_none()
                if channel:
                    channel.status = 1
                    channel.data = file_path
                    await session.commit()
            except Exception as e:
                await session.rollback()
                print(f"Ошибка при обновлении статуса канала {channel_id}: {e}")

    @staticmethod
    async def update_channel_info(channel_id, url, name, subscribers, views, topic, country,
                              monetization, income, price, description,
                              data, total):
        async with AsyncSessionLocal() as session:
            try:
                result = await session.execute(select(Channels).filter_by(id=channel_id))
                channel = result.scalar_one_or_none()
                if channel:
                    channel.url = url
                    channel.name = name
                    channel.subscribers = subscribers
                    channel.views = views
                    channel.topic = topic

                    channel.country = country
                    channel.monetization = monetization
                    channel.income = income
                    channel.price = price
                    channel.description = description
                    channel.total = total

                    channel.status = 0
                    channel.data = data
                    await session.commit()
            except Exception as e:
                await session.rollback()
                print(f"Ошибка при обновлении статуса канала {channel_id}: {e}")

    @staticmethod
    async def update_channel_info_admin(channel_id, url, name, subscribers, views, topic, country,
                                  monetization, income, price, description,
                                  data):
        async with AsyncSessionLocal() as session:
            try:
                result = await session.execute(select(Channels).filter_by(id=channel_id))
                channel = result.scalar_one_or_none()
                if channel:
                    channel.url = url
                    channel.name = name
                    channel.subscribers = subscribers
                    channel.views = views
                    channel.topic = topic

                    channel.country = country
                    channel.monetization = monetization
                    channel.income = income
                    channel.price = price
                    channel.description = description
                    channel.total = -1

                    channel.status = 1
                    channel.data = data
                    await session.commit()
            except Exception as e:
                await session.rollback()
                print(f"Ошибка при обновлении статуса канала {channel_id}: {e}")

    @staticmethod
    async def delete_channel(channel_id):
        async with AsyncSessionLocal() as session:
            try:
                result = await session.execute(select(Channels).filter_by(id=channel_id))
                channel = result.scalar_one_or_none()
                if channel:
                    await session.delete(channel)
                    await session.commit()
            except Exception as e:
                await session.rollback()
                print(f"Ошибка при удалении канала {channel_id}: {e}")

    @staticmethod
    async def return_all_info_by_channel_id(channel_id):
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(Channels).filter_by(id=channel_id))
            channel = result.scalar_one_or_none()
            if not channel:
                return None

            return {
                "user_id": channel.user_id,
                "url": channel.url,
                "name": channel.name,
                "subscribers": channel.subscribers,
                "views": channel.views,
                "topic": channel.topic,
                "country": channel.country,
                "monetization": channel.monetization,
                "income": channel.income,
                "price": channel.price,
                "description": channel.description,
                "data": channel.data,
                "status": channel.status,
                "total_amount": channel.total_amount
            }

    @staticmethod
    async def get_active_channels():
        async with AsyncSessionLocal() as session:
            # Для сортировки .order_by() передаем Channels.id.asc() прямо в select()
            query = select(Channels).filter_by(status=1).order_by(Channels.id.asc())
            result = await session.execute(query)
            return result.scalars().all()

    @staticmethod
    async def get_channels_by_user(user_id):
        async with AsyncSessionLocal() as session:
            # Для сортировки .order_by() передаем Channels.id.asc() прямо в select()
            query = select(Channels).filter_by(user_id=user_id).order_by(Channels.id.asc())
            result = await session.execute(query)
            return result.scalars().all()
