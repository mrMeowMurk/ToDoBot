import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.middleware import FSMContextMiddleware
from aiogram.types import Update
from config.config import BOT_TOKEN
from src.database import engine, Base, SessionLocal, get_db, sync_engine
from src.handlers import router, check_notifications

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DatabaseSessionMiddleware:
    def __init__(self, session_maker):
        self.session_maker = session_maker

    async def __call__(self, handler, event, data):
        async with self.session_maker() as session:
            data["session"] = session
            try:
                return await handler(event, data)
            finally:
                await session.close()

async def main():
    try:
        # Создаем таблицы в базе данных используя синхронный движок
        Base.metadata.create_all(bind=sync_engine)
        logger.info("Таблицы базы данных успешно созданы")
        
        # Инициализируем бота и диспетчер
        bot = Bot(token=BOT_TOKEN)
        storage = MemoryStorage()
        dp = Dispatcher()
        logger.info("Бот и диспетчер успешно инициализированы")
        
        # Добавляем middleware для базы данных
        dp.update.middleware(DatabaseSessionMiddleware(SessionLocal))
        
        # Регистрируем роутер
        dp.include_router(router)
        logger.info("Роутер успешно зарегистрирован")
        
        # Запускаем проверку уведомлений в фоновом режиме
        asyncio.create_task(check_notifications(bot, engine))
        logger.info("Фоновая задача проверки уведомлений запущена")
        
        # Запускаем бота
        logger.info("Бот запущен")
        await dp.start_polling(bot, storage=storage)
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        raise

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"Неожиданная ошибка: {e}")
