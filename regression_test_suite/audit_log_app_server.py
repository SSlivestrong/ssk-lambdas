# partly borrowed from https://code.experian.local/projects/ASGO/repos/asgo-platform-api
import asyncio
import time
import os
import multiprocessing
from multiprocessing import Process
from concurrent.futures import ThreadPoolExecutor
from aiohttp import web
from ascendops_commonlib.app_utils.kafka_util import KafkaWriter
from regression_test_suite.helpers import app_logger, rts_config
from regression_test_suite.services.audit_log_consumer_app import RTSAuditLogConsumer 


rts_record_logger = app_logger.CustomLogger('rts_record_consumer_app')
routes = web.RouteTableDef()

@routes.get("/")
async def root(request: web.Request):
    """ root path for system health check """
    print("Request: ROOT |", request)
    return web.json_response({"success": True, "message": "health check success. '/'"})

@routes.get("/ping")
async def ping(request: web.Request):
    """ /ping path for system health check """
    print("Request: PING |", request)
    return web.json_response({"success": True, "message": "health check success. '/ping'"})

async def startup_tasks(app: web.Application) -> None:
    loop = asyncio.get_running_loop()
    for _ in range(int(rts_config.KAFKA_NO_CONSUMER_PER_INSTANCE)):
        consumer = RTSAuditLogConsumer(rts_record_logger)
        loop.create_task(consumer.start_consuming())
        time.sleep(1)

async def start_async_app():
    """ start async app """
    app = web.Application()
    app.add_routes(routes)
    app.on_startup.append(startup_tasks)
    app["executor"] = ThreadPoolExecutor(max_workers=2)
    await web._run_app(app, host="localhost", port=3000, backlog=32, reuse_port=False)

def init_app():
    """ init app """
    asyncio.run(start_async_app())

def run():
    """ startup """
    # pre-download certs to avoid race conditions
    KafkaWriter.get_kafka_params() 
    num_processes = int(os.getenv('AUDIT_LOG_NUM_PROCESSES', 
                                  multiprocessing.cpu_count()))
    processes = []
    for _ in range(num_processes):
        p = Process(target=init_app)
        p.start()
        processes.append(p)
    for p in processes:
        p.join()
    run() # endless recursion


if __name__ == "__main__":
    run()