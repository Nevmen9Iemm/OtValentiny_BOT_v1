import os
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from database.get_menu_content import get_menu_content
from database.models import Base
from database.orm_query import orm_add_banner_description, orm_create_categories

from common.texts_for_db import categories, description_for_info_pages

# from .env file:
# DB_LITE=sqlite+aiosqlite:///my_base.db
# DB_URL=postgresql+asyncpg://login:password@localhost:5432/db_name

engine = create_async_engine(os.getenv('DB_LITE'), echo=True)

# engine = create_async_engine(os.getenv('DB_URL'), echo=True)

session_maker = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


async def create_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with session_maker() as session:
        await orm_create_categories(session, categories)
        await orm_add_banner_description(session, description_for_info_pages)


# async def create_tables():
#     """
#     Створює таблиці в базі даних, якщо вони ще не створені.
#     Ініціалізує початкові дані, якщо необхідно.
#     """
#     async with engine.begin() as conn:
#         print("Створюємо таблиці в базі даних...")
#         await conn.run_sync(Base.metadata.create_all)
#
#     # Додавання початкових даних у базу
#     async with session_maker() as session:
#         await orm_create_categories(session, categories)
#         await orm_add_banner_description(session, description_for_info_pages)
#         print("Початкові дані успішно додано!")


async def drop_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
