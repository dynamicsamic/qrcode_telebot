import asyncio
from concurrent.futures import ProcessPoolExecutor


async def run_in_executor(f, *args):
    loop = asyncio.get_running_loop()
    executor = ProcessPoolExecutor(2)
    awaitable = loop.run_in_executor(executor, f, *args)
    return await awaitable