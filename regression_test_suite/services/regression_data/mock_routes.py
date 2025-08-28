from aiohttp import web
from regression_test_suite.services.regression_data.replay_cache import ReplayCache
from regression_test_suite.helpers import app_logger, rts_config, service_helpers, rts_enums
from regression_test_suite.services.regression_data.request_validators import *
import json


rts_replay_logger = app_logger.CustomLogger('rts_replay_service')
replay_cache = ReplayCache(db_table_name=rts_config.ES_TESTCASES_DB_NAME, logger=rts_replay_logger)

mock_routes = web.RouteTableDef()

@mock_routes.post("/ccr_base")
async def ccr_base_route(request: web.Request):
    """ handle async post """
    current_request = await request.json()
    headers = request.headers
    testcase_id = headers.get('testcase_id')
    try:
        service_key = 'CCR' if headers['applicant_type'] == 'primary' else 'CCR-2'
        ccr_record = json.loads(replay_cache.get_record(testcase_id)['services'])[service_key]
        baseline_request = ccr_record['content']['request']['payload']
        if ccr_base_validate(current_request, baseline_request):
            replay_response = ccr_record['content']['response']
            replay_status = ccr_record['result']['rc']
        else:
            replay_response = {'rts_status': 'CCR Request Validation Failed'}
            replay_status = 400
    except Exception as xcp:
        handle_error(xcp, testcase_id)
        replay_response = {'rts_status': 'Mock CCR Request Failed'}
        replay_status = 500
    return web.json_response(replay_response, status=replay_status)

@mock_routes.post("/proctor_base")
@mock_routes.post("/proctor_cm")
async def procter_base_route(request: web.Request):
    """ handle async post """
    current_request = await request.json()
    headers = request.headers
    testcase_id = headers.get('testcase_id')
    try:
        service_key = 'PROCTOR' if headers['applicant_type'] == 'primary' else 'PROCTOR-2'
        proctor_record = json.loads(replay_cache.get_record(testcase_id)['services'])[service_key]
        baseline_request = proctor_record['content']['request']['payload']
        if proctor_base_validate(current_request, baseline_request):
            replay_response = proctor_record['content']['response']
            replay_status = proctor_record['result']['rc']
        else:
            replay_response = {'rts_status': 'Proctor Request Validation Failed'}
            replay_status = 400
    except Exception as xcp:
        handle_error(xcp, testcase_id)
        replay_response = {'rts_status': 'Mock PROCTOR Request Failed'}
        replay_status = 500
    return web.json_response(replay_response, status=replay_status)

@mock_routes.post("/pinning_base")
async def pinning_base_route(request: web.Request):
    """ handle async post """
    current_request = await request.json()
    headers = request.headers
    testcase_id = headers.get('testcase_id')
    try:
        service_key = 'PINNING' if headers['applicant_type'] == 'primary' else 'PINNING-2'
        pinning_record = json.loads(replay_cache.get_record(testcase_id)['services'])[service_key]
        baseline_request = pinning_record['content']['request']['payload']
        if pinning_base_validate(current_request, baseline_request):
            replay_response = pinning_record['content']['response']
            replay_status = pinning_record['result']['rc']
        else:
            replay_response = {'rts_status': 'Pinning Request Validation Failed'}
            replay_status = 400
    except Exception as xcp:
        handle_error(xcp, testcase_id)
        replay_response = {'rts_status': 'Mock PINNING Request Failed'}
        replay_status = 500
    return web.json_response(replay_response, status=replay_status)

@mock_routes.post("/clarity_base")
@mock_routes.post("/clarity_cm")
async def clarity_base_route(request: web.Request):
    """ handle async post """
    current_request = await request.json()
    headers = request.headers
    testcase_id = headers.get('testcase_id')
    try:
        service_key = 'CLARITY' if headers['applicant_type'] == 'primary' else 'CLARITY-2'
        clarity_record = json.loads(replay_cache.get_record(testcase_id)['services'])[service_key]
        baseline_request = clarity_record['content']['request']['payload']
        if clarity_base_validate(current_request, baseline_request):
            replay_response = clarity_record['content']['response']
            replay_status = clarity_record['result']['rc']
        else:
            replay_response = {'rts_status': 'Clarity Request Validation Failed'}
            replay_status = 400
    except Exception as xcp:
        handle_error(xcp, testcase_id)
        replay_response = {'rts_status': 'Mock CLARITY Request Failed'}
        replay_status = 500
    return web.json_response(replay_response, status=replay_status)

@mock_routes.post("/atb_base")
async def atb_base_route(request: web.Request):
    """ handle async post """
    current_request = await request.json()
    headers = request.headers
    service_key = headers.get('bureau')
    testcase_id = headers.get('testcase_id')
    try:
        service_key = service_key if headers['applicant_type'] == 'primary' else f'{service_key}-2'
        atb_record = json.loads(replay_cache.get_record(testcase_id)['services'])[service_key]
        baseline_request = atb_record['content']['request']['payload']
        if atb_base_validate(current_request, baseline_request, ignore_values=[testcase_id]):
            replay_response = atb_record['content']['response']
            replay_status = atb_record['result']['rc']
        else:
            replay_response = {'rts_status': 'ATB Request Validation Failed'}
            replay_status = 400
    except Exception as xcp:
        handle_error(xcp, testcase_id)
        replay_response = {'rts_status': 'Mock ATB Request Failed'}
        replay_status = 500
    return web.json_response(replay_response, status=replay_status)

@mock_routes.post("/crosscore_token_base")
async def crosscore_token_base_route(request: web.Request):
    """ handle async post """
    return

@mock_routes.post("/crosscore_base")
async def crosscore_base_route(request: web.Request):
    """ handle async post """
    return

@mock_routes.post("/criteria_base")
async def criteria_base_route(request: web.Request):
    """ handle async post """
    return

@mock_routes.post("/decision_base")
async def decision_base_route(request: web.Request):
    """ handle async post """
    return

@mock_routes.post("/sagemaker")
async def sagemaker_route(request: web.Request):
    """ handle async post """
    current_request = await request.json()
    headers = request.headers
    testcase_id = headers.get('testcase_id')
    try:
        model_uid = headers.get('model_uid')    
        service_key = 'SAGEMAKER' if headers['applicant_type'] == 'primary' else 'SAGEMAKER-2'
        sagemaker_record = json.loads(replay_cache.get_record(testcase_id)['services'])[f'{service_key}_{model_uid}']
        baseline_request = sagemaker_record['content']['request']['payload']
        if sagemaker_validate(current_request, baseline_request):
            replay_response = sagemaker_record['content']['response']
            replay_status = sagemaker_record['result']['rc']
        else:
            replay_response = {'rts_status': 'Sagemaker Request Validation Failed'}
            replay_status = 400
    except Exception as xcp:
        handle_error(xcp, testcase_id)
        replay_response = {'rts_status': 'Mock SAGEMAKER Request Failed'}
        replay_status = 500
    return web.json_response(replay_response, status=replay_status)

def handle_error(xcp: Exception, testcase_id):
    xcp_detail, tb_detail = service_helpers.extract_exception_traceback(xcp)
    rts_replay_logger.log_json(
        event_type = rts_enums.RtsEnum.RTS_MOCK_SERVICE.value,
        content = {
            "testcase_id": testcase_id,
            "message": "Mock Service Replay Testcase Error",
            "exception": xcp_detail,
            "traceback": tb_detail
        },
        level="ERROR"
    )