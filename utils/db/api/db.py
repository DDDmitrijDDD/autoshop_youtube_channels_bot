import pytz
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy import Column, Integer, String, ForeignKey, Float, select
from apscheduler.schedulers.asyncio import AsyncIOScheduler

Base = declarative_base()

# Используем асинхронный драйвер aiosqlite вместо sqlite
DATABASE_URL = "sqlite+aiosqlite:///utils/db/user.db"
engine = create_async_engine(DATABASE_URL, echo=False)

# Создаем фабрику асинхронных сессий
AsyncSessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


# ==================== МОДЕЛИ ТАБЛИЦ ====================

class User(Base):
    __tablename__ = "users"
    user_id = Column(Integer, primary_key=True)
    user_name = Column(String)
    full_name = Column(String)
    balance = Column(Float, default=0)
    sale = Column(Integer, default=0)
    all_sale = Column(Float, default=0)
    announcements = Column(Integer, default=0)
    examination = Column(Integer, default=0)
    purchases = Column(Integer, default=0)
    status = Column(Integer, default=0)
    buy = Column(Integer, default=0)
    commission = Column(Integer, default=10)
    ban = relationship("Ban", back_populates="user_ban", cascade="all, delete")
    story_user = relationship("Story", back_populates="user_story", cascade="all, delete")
    channel_user = relationship("Channels", back_populates="user_channel", cascade="all, delete")


class Ban(Base):
    __tablename__ = "ban"
    id = Column(Integer, ForeignKey("users.user_id"), primary_key=True)
    user_ban = relationship("User", back_populates="ban")

class Sales(Base):
    __tablename__ = "sales"
    id = Column(Integer, primary_key=True)
    sales = Column(Integer, default=0)

class Channels(Base):
    __tablename__ = "channels"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.user_id"))
    user_channel = relationship("User", back_populates="channel_user")
    url = Column(String)
    name = Column(String)
    subscribers = Column(Integer)
    views = Column(Integer)
    topic = Column(String)
    country = Column(String)
    monetization = Column(Integer)
    income = Column(Integer, default=0)
    price = Column(Integer)
    description = Column(String, default="")
    data = Column(String)
    status = Column(Integer, default=0)
    total_amount = Column(Float)


class Statistics(Base):
    __tablename__ = "statistics"
    id = Column(Integer, primary_key=True, autoincrement=True)
    users = Column(Integer, default=0)
    all_sale = Column(Float, default=0)
    all_listings = Column(Integer, default=0)
    sale_day = Column(Float, default=0)
    sale_week = Column(Float, default=0)
    sale_month = Column(Float, default=0)


class Story(Base):
    __tablename__ = "story"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.user_id"))
    user_story = relationship("User", back_populates="story_user")
    url = Column(String)
    name = Column(String)
    selling_price = Column(Float)
    total_amount = Column(Float)
    channel_id = Column(Integer)


class Commission(Base):
    __tablename__ = "commission"
    id = Column(Integer, primary_key=True, default=1)
    commission = Column(Integer, default=10)


class Support(Base):
    __tablename__ = "support"
    id = Column(Integer, primary_key=True, default=1)
    url = Column(String, default="https://t.me")


# ==================== АСИНХРОННАЯ ИНИЦИАЛИЗАЦИЯ И SEED ====================

async def init_db():
    """Асинхронное создание таблиц и заполнение начальными данными"""
    async with engine.begin() as conn:
        # Создаем таблицы асинхронно
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        # Проверяем и создаем Commission
        comm_query = await session.execute(select(Commission).filter_by(id=1))
        if not comm_query.scalar_one_or_none():
            session.add(Commission(id=1, commission=10))

        # Проверяем и создаем Support
        supp_query = await session.execute(select(Support).filter_by(id=1))
        if not supp_query.scalar_one_or_none():
            session.add(Support(id=1, url="https://t.me"))

        # Проверяем и создаем Statistics
        stats_query = await session.execute(select(Statistics).filter_by(id=1))
        if not stats_query.scalar_one_or_none():
            session.add(Statistics(id=1))

        # Проверяем и создаем Sales
        stats_query = await session.execute(select(Sales).filter_by(id=1))
        if not stats_query.scalar_one_or_none():
            session.add(Sales(id=1, sales=0))

        try:
            await session.commit()
        except Exception as e:
            await session.rollback()
            print(f"Ошибка при заполнении БД начальными данными: {e}")


# ==================== АСИНХРОННЫЙ СБРОС СТАТИСТИКИ ====================

async def reset_stat_field(field_name: str):
    """Универсальная асинхронная функция для обнуления конкретного поля статистики"""
    async with AsyncSessionLocal() as session:
        try:
            query = await session.execute(select(Statistics).filter_by(id=1))
            stats = query.scalar_one_or_none()
            if stats:
                setattr(stats, field_name, 0.0)
                await session.commit()
                print(f"Асинхронный сброс: поле '{field_name}' успешно обнулено.")
        except Exception as e:
            await session.rollback()
            print(f"Ошибка при обнулении поля {field_name}: {e}")


def start_scheduler():
    """Запуск асинхронного планировщика задач"""
    moscow_tz = pytz.timezone("Europe/Moscow")
    scheduler = AsyncIOScheduler(timezone=moscow_tz)

    # Исправлено: целевой функцией указана reset_stat_field, принимающая имя поля из args
    # 1. Каждый день в 00:00:00 по МСК
    scheduler.add_job(reset_stat_field, 'cron', args=['sale_day'], hour=0, minute=0, second=0)

    # 2. Каждый понедельник в 00:00:00 по МСК
    scheduler.add_job(reset_stat_field, 'cron', args=['sale_week'], day_of_week='mon', hour=0, minute=0, second=0)

    # 3. Каждое 1-е число месяца в 00:00:00 по МСК
    scheduler.add_job(reset_stat_field, 'cron', args=['sale_month'], day=1, hour=0, minute=0, second=0)

    scheduler.start()
