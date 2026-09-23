# Импортируйте AsyncSessionLocal и модель Story из вашего файла с моделями
from utils.db.api.db import AsyncSessionLocal, Story
from sqlalchemy import select


class DBstory:
    @staticmethod
    async def add_new_story(user_id, url, name, selling_price, total_amount, channel_id):
        async with AsyncSessionLocal() as session:
            try:
                story = Story(
                    user_id=user_id, url=url, name=name,
                    selling_price=selling_price, total_amount=total_amount,
                    channel_id=channel_id
                )
                session.add(story)
                await session.commit()
            except Exception as e:
                await session.rollback()
                print(f"Ошибка при добавлении истории для user_id {user_id}: {e}")
                raise e

    @staticmethod
    async def return_story_by_id(ids):
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(Story).filter_by(id=ids))
            story = result.scalar_one_or_none()
            if not story:
                return None

            return {
                "user_id": story.user_id,
                "url": story.url,
                "name": story.name,
                "selling_price": story.selling_price,
                "total_amount": story.total_amount,
                "channel_id": story.channel_id
            }

    @staticmethod
    async def return_story_by_user_id(ids):
        async with AsyncSessionLocal() as session:
            # Внимание: убран несуществующий в модели фильтр по status=1
            query = select(Story).filter_by(user_id=ids).order_by(Story.id.asc())
            result = await session.execute(query)
            return result.scalars().all()
