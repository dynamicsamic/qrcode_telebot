import asyncio
from concurrent.futures import ProcessPoolExecutor
from typing import Any, Awaitable, Callable


async def run_in_executor(f: Callable, *args: Any) -> Awaitable:
    loop = asyncio.get_running_loop()
    executor = ProcessPoolExecutor(2)
    awaitable = loop.run_in_executor(executor, f, *args)
    return await awaitable
