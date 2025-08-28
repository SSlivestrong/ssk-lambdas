import os
import asyncio
from fastapi import FastAPI, Request, Query
from fastapi.responses import HTMLResponse
from contextlib import asynccontextmanager
from helpers.app_logger import CustomLogger
from ascendops_commonlib.aws_utils.boto_session import BotoSession
from services.regression_test import (
    handle_create_regression_testcases,
    handle_run_regression_test,
    handle_get_regression_testcases,
    handle_delete_regression_testcases,
    handle_get_regression_test_results,
    handle_populate_casecode,
    handle_get_testcases_info,
    handle_get_rts_history,
    handle_delete_consumers
)
from services.regression_test.request_schemas import (
    CreateTestcasesModel,
    RunTestcasesModel,
    FilterTestcasesModel,
    DeleteTestcasesModel,
    PopulateCasecodeModel
)
import uvicorn


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting up...")
    await startup_tasks()
    yield
    print("Shutting down...")
    await shutdown_tasks()

app = FastAPI(
    title="AO Regression Test APIs",
    description="This is the Swagger for Ascend Ops - Regression Test Service (RTS) APIs",
    version="0.1",
    contact={
        "name": "Ascend Ops Team",
        "email": "Ascend-Ops-Realtime-Support@experian.com",
    },
    lifespan=lifespan
)

regression_test_api_logger = CustomLogger("regression_test_api")

@app.get("/")
async def root(request: Request):
    """ root path for system health check """
    print("Request: ROOT |", request)
    return {"success": True, "message": "health check success. '/'"}

@app.get("/ping")
async def ping(request: Request):
    """ /ping path for system health check """
    print("Request: PING |", request)
    return {"success": True, "message": "health check success. '/ping'"}

@app.post("/api/v3/regression-test/run-testcases")
async def run_regression_test(request: RunTestcasesModel):
    """ handles regression test requests for pre-recorded transactions """
    resp = await handle_run_regression_test(request.model_dump(), regression_test_api_logger)
    return resp

@app.post("/api/v3/regression-test/create-testcases")
async def create_regression_testcases(request: CreateTestcasesModel):
    """ handles creation of new testcases for new consumers and solution docs """
    resp = await handle_create_regression_testcases(request.model_dump(), regression_test_api_logger)
    return resp

@app.post("/api/v3/regression-test/get-testcases")
async def get_regression_testcases(request: FilterTestcasesModel):
    """ handles get request to retrieve recorded testcases """
    resp = await handle_get_regression_testcases(request.model_dump(), regression_test_api_logger)
    return resp

@app.post("/api/v3/regression-test/populate-casecode")
async def populate_test_casecode(request: PopulateCasecodeModel):
    """ handles populate casecode request for creating chained testcases """
    resp = await handle_populate_casecode(request.model_dump(), regression_test_api_logger)
    return resp

@app.delete("/api/v3/regression-test/delete-testcases")
async def delete_regression_testcases(request: DeleteTestcasesModel):
    """ handles delete request to delete recorded testcases """
    resp = await handle_delete_regression_testcases(request.model_dump(), regression_test_api_logger)
    return resp

@app.delete("/api/v3/regression-test/delete-consumers/{case_code}")
async def delete_regression_consumers(case_code: str):
    """ handles delete request to delete recorded testcases """
    resp = await handle_delete_consumers(case_code, regression_test_api_logger)
    return resp

@app.get("/api/v3/regression-test/get-results/{job_id}")
async def get_regression_test_results(job_id: str, testcase_id: str = Query(None)):
    """ returns the test result """
    request = {
        "job_id": job_id,
        "testcase_id": testcase_id
    }
    resp, is_html = await handle_get_regression_test_results(request, regression_test_api_logger)
    if is_html:
        return HTMLResponse(content=resp, media_type="text/html")
    return resp

@app.get("/api/v3/regression-test/get-history/{solution_id}")
async def get_regression_test_history(solution_id: str):
    """ handles get request to retrieve history of rts requests for a solution"""
    resp = await handle_get_rts_history(solution_id, regression_test_api_logger)
    return resp

@app.get("/api/v3/regression-test/get-testcases-info/{solution_id}")
async def get_regression_testcases_info(solution_id: str):
    """ handles get request to retrieve recorded testcases info for a solution """
    resp = await handle_get_testcases_info(solution_id, regression_test_api_logger)
    return resp

async def startup_tasks():
    """  startup tasks defined here """
    if os.getenv("IAM_PROFILE"):
        BotoSession.init(
            profile=os.getenv("IAM_PROFILE"),
            region_name=os.getenv("DEFAULT_REGION", "us-east-1")
        )
    else:
        BotoSession.init(
            region_name=os.getenv("DEFAULT_REGION", "us-east-1")
        )

async def shutdown_tasks():
    """ app shutdown tasks func """
    pass

async def run_app():
    """ run app """
    config = uvicorn.Config(app, host="127.0.0.1", port=9000)
    server = uvicorn.Server(config)
    await server.serve()

if __name__ == "__main__":
    asyncio.run(run_app())