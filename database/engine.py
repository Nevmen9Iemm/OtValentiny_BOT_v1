from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from database.models import Base

# Створюємо асинхронний двигун для підключення до SQLite
DATABASE_URL = "sqlite+aiosqlite:///my_base.db"

engine = create_async_engine(DATABASE_URL, echo=True)

# Налаштовуємо сесії для роботи з базою даних
async_session = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def get_session() -> AsyncSession:
    """
    Генерує нову сесію для бази даних.
    Використовується як залежність у функціях або сервісах.
    """
    async with async_session() as session:
        yield session

async def create_tables():
    """
    Створює таблиці в базі даних, якщо вони ще не створені.
    Використовує метадані з Base.
    """
    async with engine.begin() as conn:
        print("Створюємо таблиці у базі даних...")
        await conn.run_sync(Base.metadata.create_all)
        print("Таблиці успішно створені!")