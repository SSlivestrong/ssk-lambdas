
import asyncio

from functools import wraps, partial
from concurrent.futures import ThreadPoolExecutor

executor_pool = ThreadPoolExecutor(max_workers=2)

def cpu_task(func):
    @wraps(func)
    async def run(*args, **kwargs):
        pfunc = partial(func, *args, **kwargs)
        event_loop = asyncio.get_running_loop()
        return await event_loop.run_in_executor(executor_pool, pfunc)
    return run
