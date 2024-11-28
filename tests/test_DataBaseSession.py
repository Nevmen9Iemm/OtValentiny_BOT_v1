from middlewares.db import DataBaseSession
from unittest.mock import AsyncMock
import pytest

@pytest.mark.asyncio
async def test_database_session():
    # Мокаємо пул сесій
    session_mock = AsyncMock()

    # Ініціалізуємо проміжне ПЗ
    middleware = DataBaseSession(session_pool=session_mock)

    # Перевіряємо виклик сесії в рамках обробника
    handler_mock = AsyncMock()
    event_mock = {}
    data_mock = {}

    await middleware(handler_mock, event_mock, data_mock)

    # Переконаємося, що сесія була додана в data
    session_mock.assert_called_once()
    assert "db_session" in data_mock