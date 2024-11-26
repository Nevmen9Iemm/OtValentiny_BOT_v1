import asyncio
import os

from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.client.bot import Bot, DefaultBotProperties

from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv())

from middlewares.db import DataBaseSession

from database.engine import create_db, create_tables, drop_db, session_maker, create_tables

from handlers.user_private import user_private_router
from handlers.user_group import user_group_router
from handlers.admin_private import admin_router

bot = Bot(
    token=os.getenv('TOKEN'),
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)

bot.my_admins_list = []

dp = Dispatcher()

dp.include_router(user_private_router)
dp.include_router(user_group_router)
dp.include_router(admin_router)


async def on_startup(bot):
    """
    Дії, які виконуються при запуску бота.
    """
    # Створення бази даних
    await create_db()

    # Видалення таблиць у базі даних
    # await drop_db()

    # Створення таблиць у базі даних
    print("Перевіряємо таблиці в базі даних...")
    await create_tables()
    print("Таблиці успішно створені!")


async def on_shutdown(bot):
    """
    Дії, які виконуються при вимкненні бота.
    """
    print('БОТ ЛІГ')


async def main():
    """
    Основна функція для запуску бота.
    """
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    # Додавання middleware для роботи з базою даних
    dp.update.middleware(DataBaseSession(session_pool=session_maker))

    # Налаштування webhook або polling
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


# Запуск бота
if __name__ == "__main__":
    asyncio.run(main())