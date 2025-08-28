import os
import asyncio
from aiohttp import web
from helpers.app_logger import CustomLogger
from services.regression_data.mock_routes import mock_routes
from ascendops_commonlib.aws_utils.boto_session import BotoSession

regression_test_api_logger = CustomLogger("regression_data_api")
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

async def startup_tasks(app: web.Application):
    """  startup tasks defined here """
    print("Initiating startup tasks...", app)
    if os.getenv("IAM_PROFILE"):
        BotoSession.init(
            profile=os.getenv("IAM_PROFILE"),
            region_name=os.getenv("DEFAULT_REGION", "us-east-1")
        )
    else:
        BotoSession.init(
            region_name=os.getenv("DEFAULT_REGION", "us-east-1")
        )

async def shutdown_tasks(app: web.Application):
    """ app shutdown tasks func """
    pass

async def start_async_app():
    """ start async app """
    app = web.Application()
    app.add_routes(routes)
    app.add_routes(mock_routes)
    app.on_startup.append(startup_tasks)
    app.on_shutdown.append(shutdown_tasks)
    return app

async def init_app():
    """ init app """
    app = await start_async_app()
    return app

async def startup():
    """ startup """
    app = await init_app()
    await web._run_app(app, host="localhost", port=7000, backlog=32, reuse_port=False)


if __name__ == "__main__":
    asyncio.run(startup())