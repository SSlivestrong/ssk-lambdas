from helpers import service_helpers, rts_enums, app_logger, rts_config
from services.regression_test.rts_job_manager import RtsJobManager


async def handle_run_regression_test(run_req: dict, logger: app_logger.CustomLogger):
    job = RtsJobManager(job_req = {
        "run": run_req,
        "ascendops_url": run_req["ascendops_url"] if run_req["ascendops_url"] else rts_config.AO_SERVICE_URL,
        "ascendops_endpoint": run_req["ascendops_endpoint"]
    }, logger=logger)
    return {'job_id': job.job_id}

async def handle_create_regression_testcases(create_req: dict, logger: app_logger.CustomLogger):   
    job = RtsJobManager(job_req = {
        "create": create_req,
        "ascendops_url": create_req["ascendops_url"] if create_req["ascendops_url"] else rts_config.AO_SERVICE_URL,
        "ascendops_endpoint": create_req["ascendops_endpoint"]
    }, logger=logger)
    return {'job_id': job.job_id}

async def handle_get_regression_testcases(get_req: dict, logger: app_logger.CustomLogger): 
    try:
        if RtsJobManager.es_filter.count_filtered_testcases(get_req) > 10:
            job = RtsJobManager(job_req = {
                "get": get_req
            }, logger=logger)
            resp = {'job_id': job.job_id}
        else:
            resp = RtsJobManager.es_filter.get_testcases(get_req)
    except Exception as xcp:
        xcp_detail, tb_detail = service_helpers.extract_exception_traceback(xcp)
        logger.log_json(
            event_type = rts_enums.RtsEnum.RTS_API.value,
            content = {
                "message": "Get Testcases Failed",
                "exception": xcp_detail,
                "traceback": tb_detail
            },
            level="ERROR"
        )
        resp = {
            "error": "Error in fetching testcases"
        }
    return resp

async def handle_populate_casecode(pop_req: dict, logger: app_logger.CustomLogger):   
    try:
        resp = RtsJobManager.populate_casecode(pop_req)
        if resp["success"]:
            logger.write_log_item(message=f'>>>> RTS >>>>: {resp["num_consumers_onboarded"]} new {pop_req["new_case_code"]} consumers onboarded to DB ', level="WARNING")
    except Exception as xcp:
        xcp_detail, tb_detail = service_helpers.extract_exception_traceback(xcp)
        logger.log_json(
            event_type = rts_enums.RtsEnum.RTS_API.value,
            content = {
                "message": "Populate Casecode Failed",
                "exception": xcp_detail,
                "traceback": tb_detail
            },
            level="ERROR"
        )
        resp = {
            "error": "Error in populating new casecode"
        }
    return resp

async def handle_get_regression_test_results(result_request: dict, logger: app_logger.CustomLogger):
    try:
        resp, is_html = RtsJobManager.get_postprocessed_test_results(**result_request)
    except Exception as xcp:
        xcp_detail, tb_detail = service_helpers.extract_exception_traceback(xcp)
        logger.log_json(
            event_type = rts_enums.RtsEnum.RTS_API.value,
            content = {
                "message": "Results Fetch for Testcases Failed",
                "exception": xcp_detail,
                "traceback": tb_detail
            },
            level="ERROR"
        )
        resp, is_html = {
            "error": "Error in fetching test results"
        }, False
    return resp, is_html

async def handle_delete_regression_testcases(delete_req: dict, logger: app_logger.CustomLogger):   
    try:
        resp = RtsJobManager.delete_testcases(delete_req)
    except Exception as xcp:
        xcp_detail, tb_detail = service_helpers.extract_exception_traceback(xcp)
        logger.log_json(
            event_type = rts_enums.RtsEnum.RTS_API.value,
            content = {
                "message": "Delete Testcases Failed",
                "exception": xcp_detail,
                "traceback": tb_detail
            },
            level="ERROR"
        )
        resp = {
            "error": "Error in deleting testcases"
        }
    return resp

async def handle_delete_consumers(case_code: str, logger: app_logger.CustomLogger):   
    try:
        resp = RtsJobManager.es_filter.delete_consumers(case_code)
    except Exception as xcp:
        xcp_detail, tb_detail = service_helpers.extract_exception_traceback(xcp)
        logger.log_json(
            event_type = rts_enums.RtsEnum.RTS_API.value,
            content = {
                "message": "Delete Consumers Failed",
                "exception": xcp_detail,
                "traceback": tb_detail
            },
            level="ERROR"
        )
        resp = {
            "error": "Error in deleting consumers"
        }
    return resp

async def handle_get_testcases_info(solution_id: str, logger: app_logger.CustomLogger):
    try:
        resp = RtsJobManager.es_filter.get_testcases_info(solution_id)
    except Exception as xcp:
        xcp_detail, tb_detail = service_helpers.extract_exception_traceback(xcp)
        logger.log_json(
            event_type = rts_enums.RtsEnum.RTS_API.value,
            content = {
                "message": "Get Testcases Info Failed",
                "exception": xcp_detail,
                "traceback": tb_detail
            },
            level="ERROR"
        )
        resp = {
            "error": "Error in fetching testcases"
        }
    return resp

async def handle_get_rts_history(solution_id: str, logger: app_logger.CustomLogger):
    try:
        resp = RtsJobManager.es_filter.get_rts_history(solution_id)
    except Exception as xcp:
        xcp_detail, tb_detail = service_helpers.extract_exception_traceback(xcp)
        logger.log_json(
            event_type = rts_enums.RtsEnum.RTS_API.value,
            content = {
                "message": "History Get Failed",
                "exception": xcp_detail,
                "traceback": tb_detail
            },
            level="ERROR"
        )
        resp = {
            "error": "Error in fetching history"
        }
    return resp