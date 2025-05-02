from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
import logging

logger = logging.getLogger(__name__)

# Создаем базовый класс для моделей
Base = declarative_base()

# Импортируем модели после создания Base
from .models import User, Task, Category, Priority, UserCategory

# Синхронный движок для создания таблиц
SQLALCHEMY_DATABASE_URL = "sqlite:///./todo.db"
sync_engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}
)

# Асинхронный движок для работы с базой данных
ASYNC_SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///./todo.db"
engine = create_async_engine(
    ASYNC_SQLALCHEMY_DATABASE_URL,
    echo=True,
    connect_args={"check_same_thread": False}
)

# Создаем асинхронную сессию
SessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

# Создаем все таблицы синхронно
def init_db():
    try:
        Base.metadata.create_all(bind=sync_engine)
        logger.info("Таблицы базы данных успешно созданы")
    except Exception as e:
        logger.error(f"Ошибка при создании таблиц: {e}")
        raise

# Инициализируем базу данных
init_db()

logger.info("Асинхронная база данных успешно инициализирована")

async def get_db():
    async with SessionLocal() as session:
        try:
            yield session
        finally:
            await session.close() 