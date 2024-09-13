import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from db import Base, engine
from handlers import router
from settings import settings

dp = Dispatcher(storage=MemoryStorage())
dp.include_router(router)
bot = Bot(settings.BOT_TOKEN)


async def main():
    async with engine.begin() as con:
        await con.run_sync(Base.metadata.create_all)

    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
