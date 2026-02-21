import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN
from database.db import init_db
from bot.handlers import patient, admin, common
from bot.scheduler import setup_scheduler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def main():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    # Routerlarni ro'yxatdan o'tkazish
    dp.include_router(common.router)
    dp.include_router(patient.router)
    dp.include_router(admin.router)

    # Ma'lumotlar bazasini ishga tushirish
    await init_db()
    logger.info("✅ Database initialized")

    # Eslatma scheduler
    setup_scheduler(bot)
    logger.info("✅ Scheduler started")

    logger.info("🚀 MedBot ishga tushdi!")

    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
