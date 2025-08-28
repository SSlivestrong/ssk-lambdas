
""" Main module for the billing consumer application """

import time
import logging
import asyncio
import os, sys
import multiprocessing
from aiohttp import web
from multiprocessing import Process
from helpers import app_config
from helpers import app_logger
from helpers import async_cputhread
from helpers.sql_util import aio_mysql
from helpers.boto3_sessions import AIOBoto3Session
from start_up.billing_consumer import BillingConsumer
from ascendops_commonlib.app_utils.kafka_util import KafkaWriter
from billing_consumer_new.helpers.crypto_util import ContentHelper

routes = web.RouteTableDef()

# Adding a health check with /ping
@routes.get("/ping")
async def ping(request):
    return web.Response(text="BillingConsumer Service available", status=200)


def initialize_logger():
    logging.getLogger("billing_consumer").setLevel(app_config.LOG_LEVEL)
    # log_Format = "%(asctime)s - %(name)s - %(process)d - %(levelname)s - %(message)s"
    # logging.basicConfig(stream=sys.stdout, format=log_Format, level=logging.ERROR)    
    logging.basicConfig(stream=sys.stdout, level=logging.ERROR)
    app_logger.setup_logging_queue()


async def startup_tasks(app: web.Application) -> None:
    
    consumers = []
    num_consumers = min(app_config.KAFKA_NO_CONSUMER_PER_INSTANCE, app_config.KAFKA_NO_CONSUMER_PER_INSTANCE_MAX)
    loop = asyncio.get_running_loop()
    await AIOBoto3Session.instance().start()
    mysql = aio_mysql()
    await mysql.connect(size=num_consumers)
    crypto_util = ContentHelper(app_config.CRYPTO_LJAR, app_config.CRYPTO_ENV, 
                                app_config.CRYPTO_ENV_PREFIX, app_config.CRYPTO_AWS_PROFILE, 
                                instances = app_config.CRYPTO_INSTANCES)
    for _ in range(3):
        time.sleep(1)
        consumer = BillingConsumer(crypto_util=crypto_util, mysql_instance=mysql, name=f"billing_consumer-{os.getpid()}-{_}")
        consumers.append(consumer)
        loop.create_task(consumer.run())


async def shutdown_tasks(app: web.Application) -> None:
    await AIOBoto3Session.instance().stop()


async def main():
    app = web.Application()
    app.on_startup.append(startup_tasks)
    app.on_shutdown.append(shutdown_tasks)
    app["executor"] = async_cputhread.executor_pool
    port = int(os.getenv('BILLING_CONSUMER_PORT', 6500))
    await web._run_app(app, port=port, backlog=32, reuse_port=True)


def start():
    initialize_logger()
    asyncio.run(main())


def run():
    KafkaWriter.on_app_start()
    cpu_count = multiprocessing.cpu_count()
    num_processes = int(os.getenv('BILLING_CONSUMER_NUM_PROCESSES', cpu_count))
    processes = []
    for _ in range(num_processes):
        p = Process(target=start)
        p.start()
        processes.append(p)   
    for p in processes:
        p.join()
    run()


if __name__ == '__main__':
    run()
