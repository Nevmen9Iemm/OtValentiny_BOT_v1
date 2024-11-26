import os
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from database.models import Base
from database.orm_query import orm_add_banner_description, orm_create_categories

from common.texts_for_db import categories, description_for_info_pages

# Ініціалізація двигуна для бази даних із використанням змінної оточення DB_LITE
engine = create_async_engine(os.getenv('DB_LITE'), echo=True)

# Налаштування фабрики для створення сесій
session_maker = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


async def create_tables():
    """
    Створює таблиці в базі даних, якщо вони ще не створені.
    Ініціалізує початкові дані, якщо необхідно.
    """
    async with engine.begin() as conn:
        print("Створюємо таблиці в базі даних...")
        await conn.run_sync(Base.metadata.create_all)

    # Додавання початкових даних у базу
    async with session_maker() as session:
        await orm_create_categories(session, categories)
        await orm_add_banner_description(session, description_for_info_pages)
        print("Початкові дані успішно додано!")


async def drop_db():
    """
    Видаляє всі таблиці в базі даних.
    """
    async with engine.begin() as conn:
        print("Видаляємо таблиці з бази даних...")
        await conn.run_sync(Base.metadata.drop_all)
        print("Всі таблиці успішно видалено.")