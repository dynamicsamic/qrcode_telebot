import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from cv2 import QRCodeDetector

from db import Base, engine
from handlers import router
from settings import settings

dp = Dispatcher(storage=MemoryStorage())

async def main():
    async with engine.begin() as con:
        await con.run_sync(Base.metadata.create_all)

    qreader = QRCodeDetector()
    bot = Bot(settings.BOT_TOKEN)
    dp.include_router(router)
    await dp.start_polling(bot, qreader=qreader)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
