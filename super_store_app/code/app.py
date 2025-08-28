import asyncio
import logging
import multiprocessing
import os
import sys
import time
import uuid
from multiprocessing import Process

import api.app_global as app_global
import common.app_config as app_config
from aiohttp import web
from batch_consumer.superstore_consumer import SuperStoreConsumer
from common.aio_utils import async_cputhread, async_logger, time_decorators
from common.aio_utils.boto3_sessions import AIOBoto3Session
from common.kafka_util import get_kafka_params


@time_decorators.duration
def blocking_func(seconds: int) -> str:
    time.sleep(seconds)
    return f"Waited for {seconds} second(s)"


routes = web.RouteTableDef()
stub = None


@routes.get("/ping")
@time_decorators.duration
async def ping():
    return web.Response(text="SuperStore Consumer Service available")


@routes.get("/")
async def health_check(request):
    return web.Response(text="Service is healthy", status=200)




def initialize_logger():
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    logging.getLogger("superstore_consumer").setLevel(app_config.LOG_LEVEL)
    logging.getLogger("timeit").setLevel(app_config.LOG_LEVEL)

    # log_format = "%(asctime)s - %(name)s - %(process)d - %(levelname)s - %(message)s"
    log_format = "%(message)s"
    logging.basicConfig(stream=sys.stdout, format=log_format, level=logging.ERROR)
    async_logger.setup_logging_queue()


async def startup_tasks(app: web.Application) -> None:
    # start consumers
    consumers = []
    loop = asyncio.get_running_loop()
    await AIOBoto3Session.instance().start()
    num_consumers = min(
        app_global.KAFKA_NO_CONSUMER_PER_INSTANCE,
        app_global.KAFKA_NO_CONSUMER_PER_INSTANCE_MAX,
    )
    for _consumer in range(num_consumers):
        time.sleep(1)
        consumer = SuperStoreConsumer(
            name=f"SUPERSTORE-{os.getpid()}-{_consumer}-{uuid.uuid4().hex}"
        )
        consumers.append(consumer)
        loop.create_task(consumer.run())


async def shutdown_tasks(app: web.Application) -> None:
    await AIOBoto3Session.instance().stop()


async def main():
    app = web.Application()
    app.add_routes(routes)
    app.on_startup.append(startup_tasks)
    app.on_shutdown.append(shutdown_tasks)
    app["executor"] = async_cputhread.executor_pool

    port = int(os.getenv("SUPER_STORE_CONSUMER_PORT", 7000))
    await web._run_app(app, port=port, backlog=32, reuse_port=True)


def start():
    # initialize_logger()
    asyncio.run(main())


def run():
    cpu_count = 1
    num_processes = 1
    if app_global.SECURITY_PROTOCOL == "SSL":
        get_kafka_params()
        cpu_count = multiprocessing.cpu_count()
        num_processes = int(os.getenv("ECS_SNAPSHOT_CONSUMER_NUM_PROCESSES", cpu_count))
    if num_processes > 3:
        num_processes = num_processes - 1
    processes = []
    for _ in range(num_processes):
        p = Process(target=start)
        p.start()
        processes.append(p)

    for p in processes:
        p.join()
    run()


if __name__ == "__main__":
    run()
