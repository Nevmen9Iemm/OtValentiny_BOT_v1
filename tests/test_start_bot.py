import pytest
from aiogram import Bot
from app import bot, dp, on_startup, on_shutdown

@pytest.mark.asyncio
async def test_on_startup():
    # Викликаємо on_startup і перевіряємо, чи створюється база даних
    await on_startup(bot)
    # Наприклад, можна перевірити існування таблиць у базі
    from database.engine import session_maker
    async with session_maker() as session:
        result = await session.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = result.fetchall()
        assert len(tables) > 0  # Переконатися, що є хоча б одна таблиця

@pytest.mark.asyncio
async def test_on_shutdown():
    # Викликаємо on_shutdown (перевіряємо, чи логіка коректна)
    await on_shutdown(bot)
    # В даному випадку перевіримо, чи виконується виключення бота (просто логування)