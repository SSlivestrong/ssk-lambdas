import time
import asyncio
from contextlib import contextmanager
import functools
import logging

tlogger = logging.getLogger('timeit')

def decorate_sync_async(decorating_context, func):
    if asyncio.iscoroutinefunction(func):
        async def decorated(*args, **kwargs):
            with decorating_context():
                return (await func(*args, **kwargs))
    else:
        def decorated(*args, **kwargs):
            with decorating_context():
                return func(*args, **kwargs)

    return functools.wraps(func)(decorated)

@contextmanager
def wrapping_logic(func_name):
    start_ts = time.time()
    yield
    dur = time.time() - start_ts
    tlogger.debug('{} took {:.2} seconds'.format(func_name, dur))


def duration(func):
    timing_context = lambda: wrapping_logic(func.__name__)
    return decorate_sync_async( timing_context, func )
