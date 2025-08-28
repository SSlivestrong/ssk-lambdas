from threading import Lock
from concurrent.futures import ThreadPoolExecutor
from helpers.ao_request_handler import AscendOpsRequestHandler
from services.regression_test.response_validators import *
from star_dataloader import StarTestData, TestInquiryString, Consumer, Secondary, \
    validate_and_extract_function_map, block_builder_function_map
from helpers import app_logger, service_helpers, rts_enums, rts_config
from services.regression_test.rts_es_filter import RtsEsFilter
from collections import defaultdict
from copy import deepcopy
from io import BytesIO
from queue import Queue
import random
import asyncio
import boto3
import json
import uuid


class RtsJobManager:
    _job_tracker = None
    _glock = None
    _executor = None
    es_filter = RtsEsFilter()
    
    def __init__(self, job_req, logger: app_logger.CustomLogger):
        if RtsJobManager._job_tracker is None:
            RtsJobManager._job_tracker = defaultdict(dict)
            RtsJobManager._job_id_queue = Queue(maxsize=int(rts_config.JOB_QUEUE_SIZE))
            RtsJobManager._glock = Lock()
            RtsJobManager._executor = ThreadPoolExecutor(max_workers=8)
        self.logger = logger
        self.es_conn = RtsJobManager.es_filter.es_conn
        self.job_id = str(uuid.uuid4())
        RtsJobManager._executor.submit(self.run_job, job_req)

    def run_job(self, job_req):
        with RtsJobManager._glock:
            RtsJobManager._job_tracker[self.job_id]["status"] = "job started"
            if len(RtsJobManager._job_tracker) > RtsJobManager._job_id_queue.maxsize:
                oldest_job_id = RtsJobManager._job_id_queue.get()
                if RtsJobManager._job_tracker[oldest_job_id]["status"] in ("job started", 
                                                                           "created testcases", 
                                                                           "fetched testcases"):
                    RtsJobManager._job_id_queue.put(oldest_job_id) # re-insert into queue for tracking
                    self.logger.logger.error(">>>> RTS >>>>: Job Terminated due to Queue Overload")
                    del RtsJobManager._job_tracker[self.job_id]
                    return
                del RtsJobManager._job_tracker[oldest_job_id]
            RtsJobManager._job_id_queue.put(self.job_id)

        if "get" in job_req:
            try:
                get_results = RtsJobManager.es_filter.get_testcases(job_req["get"], write_to_s3=True)
                with RtsJobManager._glock:
                    RtsJobManager._job_tracker[self.job_id]["status"] = "job done"
                    if "testcases" in get_results:
                        RtsJobManager._job_tracker[self.job_id]["results"] = [get_results]
                    else:
                        RtsJobManager._job_tracker[self.job_id].update(get_results)
            except Exception as xcp:
                xcp_detail, tb_detail = service_helpers.extract_exception_traceback(xcp)
                self.logger.log_json(
                    event_type = rts_enums.RtsEnum.RTS_JOB_MANAGER.value,
                    content = {
                        "job_id": self.job_id,
                        "message": "RTS Job Get Testcases Error",
                        "exception": xcp_detail,
                        "traceback": tb_detail
                    },
                    level="ERROR"
                )
                with RtsJobManager._glock:
                    RtsJobManager._job_tracker[self.job_id]["status"] = "failed to get testcases"
                return
        
        if "run" in job_req:
            try:
                job_req["execute"] = RtsJobManager.es_filter.get_execution_request(job_req["run"])
                with RtsJobManager._glock:
                    RtsJobManager._job_tracker[self.job_id]["status"] = "fetched testcases"            
            except Exception as xcp:
                xcp_detail, tb_detail = service_helpers.extract_exception_traceback(xcp)
                self.logger.log_json(
                    event_type = rts_enums.RtsEnum.RTS_JOB_MANAGER.value,
                    content = {
                        "job_id": self.job_id,
                        "message": "RTS Job Fetch Testcases Error",
                        "exception": xcp_detail,
                        "traceback": tb_detail
                    },
                    level="ERROR"
                )
                with RtsJobManager._glock:
                    RtsJobManager._job_tracker[self.job_id]["status"] = "failed to fetch testcases"
                return
        
        if "create" in job_req:
            try:
                job_req["execute"] = self.handle_create_request(job_req["create"])
                with RtsJobManager._glock:
                    RtsJobManager._job_tracker[self.job_id]["status"] = "created testcases"            
            except Exception as xcp:
                xcp_detail, tb_detail = service_helpers.extract_exception_traceback(xcp)
                self.logger.log_json(
                    event_type = rts_enums.RtsEnum.RTS_JOB_MANAGER.value,
                    content = {
                        "job_id": self.job_id,
                        "message": "RTS Job Create Testcases Error",
                        "exception": xcp_detail,
                        "traceback": tb_detail
                    },
                    level="ERROR"
                )
                with RtsJobManager._glock:
                    RtsJobManager._job_tracker[self.job_id]["status"] = "failed to create testcases"
                return
        
        if "execute" in job_req:
            try:
                run_results = self.handle_execute_request(job_req)
                history_req = dict()
                if "create" in job_req and job_req['create']['verified_create_request']:
                    history_req["tested_by"] = job_req["create"]["tested_by"]
                    history_req["solution_id"] = job_req['create']['ao_payload_info']['solution_id']
                    history_req["request"] = job_req['create']
                    history_req["response"] = run_results
                    self.es_filter.update_rts_history(history_req, req_type="create")
                elif "run" in job_req:
                    history_req["tested_by"] = job_req["run"]["tested_by"]
                    for result in run_results:
                        if len(result["testcases"]) > 0:
                            history_req["solution_id"] = result["solution_id"]
                            history_req["request"] = deepcopy(job_req["run"])
                            history_req["request"]["tests"].clear()
                            for test in job_req["run"]["tests"]:
                                if test["filters"]["solution_id"] == result["solution_id"]:
                                    history_req["request"]["tests"].append(test)
                                    break
                            history_req["response"] = [result]
                            self.es_filter.update_rts_history(history_req, req_type="run")
                with RtsJobManager._glock:
                    RtsJobManager._job_tracker[self.job_id]["status"] = "job done"
                    RtsJobManager._job_tracker[self.job_id]["results"] = run_results
            except Exception as xcp:
                xcp_detail, tb_detail = service_helpers.extract_exception_traceback(xcp)
                self.logger.log_json(
                    event_type = rts_enums.RtsEnum.RTS_JOB_MANAGER.value,
                    content = {
                        "job_id": self.job_id,
                        "message": "RTS Job Run Testcases Error",
                        "exception": xcp_detail,
                        "traceback": tb_detail
                    },
                    level="ERROR"
                )
                with RtsJobManager._glock:
                    RtsJobManager._job_tracker[self.job_id]["status"] = "failed to run testcases"
                return      
    
    @staticmethod
    def get_test_results(job_id):
        result_response = None
        if RtsJobManager._glock is None:
            result_response = {"status": "no jobs have been initiated"}
        else:
            with RtsJobManager._glock:
                if job_id in RtsJobManager._job_tracker:
                    result_response  = RtsJobManager._job_tracker[job_id]
                else:
                    result_response = {"status": "job not found / invalid job id / job queue overload"}
        return result_response
    
    @staticmethod
    def get_postprocessed_test_results(job_id, testcase_id):
        results = deepcopy(RtsJobManager.get_test_results(job_id))
        if "results" not in results:
            return results, False
        for result in results["results"]:
            total_count = 0
            for testcase in result["testcases"]:
                total_count += 1
                if "result" in testcase:
                    if testcase_id == testcase["testcase_id"]:
                        return testcase["result"]["html_diff"], True
                    if testcase_id == None:
                        del testcase["result"]["html_diff"]
                    if testcase["result"]["pass"]:
                        if "passed" not in result:
                            result["passed"] = 1
                        else:
                            result["passed"] += 1
                    else:
                        if "passed" not in result:
                            result["passed"] = 0
            result["total"] = total_count
        if testcase_id:
            return "Run testcase_id not found for this job", True
        return results, False
    
    @staticmethod
    def delete_testcases(delete_req: dict):
        return RtsJobManager.es_filter.delete_testcases(delete_req)
    
    @staticmethod
    def populate_casecode(pop_req: dict):
        if pop_req["custom_pii"] is not None:
            action_list = []
            pii_dump_info = json.dumps(pop_req["custom_pii"])
            for _ in range(int(pop_req["volume"])):
                action_list.append({
                    '_op_type': 'create',
                    '_index': rts_config.ES_CONSUMERS_DB_NAME,
                    'pii_info': pii_dump_info, 
                    'case_code': pop_req["new_case_code"],
                    'star_info': "custom pii data"
                    })
        else:
            query = {
                    "query": {
                        "bool": {
                            "should": [{ "term": { "case_code": pop_req["existing_case_code"] } }],
                            "minimum_should_match": 1
                        }
                    }
                }
            consumer_piis = RtsJobManager.es_filter.es_conn.get_document_by_query(index_name=rts_config.ES_CONSUMERS_DB_NAME, query=query)
            volume = pop_req["volume"]
            num_cases = int(volume*len(consumer_piis) if volume <= 1 \
                            else min(volume, len(consumer_piis)))
            indices = random.sample(range(len(consumer_piis)), num_cases)
            action_list = []
            for idx in indices:
                action_list.append({
                    '_op_type': 'create',
                    '_index': rts_config.ES_CONSUMERS_DB_NAME,
                    'pii_info': consumer_piis[idx]['_source']['pii_info'], 
                    'case_code': pop_req["new_case_code"],
                    'star_info': f"populated from {pop_req['existing_case_code']}"
                    })
                
        if len(action_list) > 0:
            RtsJobManager.es_filter.es_conn.bulk_import2(actions=action_list)
        
        return {"success": True, "num_consumers_onboarded": len(action_list)}
    
    def handle_create_request(self, create_req):
        execute_req = []

        if "solution_id" in create_req["ao_payload_info"]:
            _solution_id = create_req["ao_payload_info"]["solution_id"]
        elif create_req["inquiry_string_info"] is not None:
            _solution_id = create_req["inquiry_string_info"]["solution_id"]
        else:
            raise KeyError("solution_id not found in inquiry")
        
        if create_req["is_prod_mockup"]:
            query = {
                "query": {
                            "bool": {
                                "must": [
                                    {"exists": {"field": "status"}},
                                    {"exists": {"field": "solution_id"}},
                                    {"term": {"status": "prod"}},
                                    {"term": {"solution_id": _solution_id}}
                                ]
                            }
                        }
                    }
            solution_doc = self.es_conn.get_document_by_query(create_req["solution_index"], query)[0]["_source"]
        else:
            solution_doc = self.es_conn.get_document(index_name=create_req["solution_index"], doc_id=_solution_id)["_source"]

        # override solution_id for consistency
        create_req["ao_payload_info"]["solution_id"] = _solution_id
        if create_req["inquiry_string_info"] is not None:
            create_req["inquiry_string_info"]["solution_id"] = _solution_id
        solution_doc["solution_id"] = _solution_id
        
        if create_req["new_consumers"]:
            excel_bucket = boto3.resource('s3', region_name=rts_config.DEFAULT_REGION).Bucket(rts_config.EXCEL_BUCKET_NAME)
            excel_file = BytesIO()
            excel_bucket.download_fileobj(f'star_excel_uploads/{create_req["new_consumers"]["excel_file_name"]}', excel_file)
            excel_file.seek(0)
            if excel_file.getbuffer().nbytes > 0:
                self.logger.logger.warning(f'downloaded excel file from s3')
                block_builder_mapping = create_req["new_consumers"]["block_builder"]
                validate_and_extract_mapping = create_req["new_consumers"]["validate_and_extract"]
                test_data = StarTestData(
                    excel_io=excel_file,
                    header_config=create_req["new_consumers"]["header_config"],
                    sheet_name=create_req["new_consumers"]["sheet_name"] if len(create_req["new_consumers"]["sheet_name"]) > 0 else None,
                    block_builder={key: block_builder_function_map[block_builder_mapping[key]] \
                        for key in block_builder_mapping},
                    validate_and_extract={key: validate_and_extract_function_map[validate_and_extract_mapping[key]] \
                        for key in validate_and_extract_mapping}
                )
                inquiry_list = []
                if create_req["inquiry_string_info"] is not None:
                    ii = create_req["inquiry_string_info"]
                    client_metadata = f"{ii['device_indicator']}{ii['preamble_code']} {ii['operator_initials']}{ii['inquiry_type']} {ii['subcode_and_password']}"
                    pipeline_blueprint = [ii['purpose_type'], *ii['verify_keywords'], f"GO-{ii['solution_id']}", *ii['products']]
                else:
                    client_metadata, pipeline_blueprint = "", []

                for idx in range(len(test_data)):
                    inquiry_list.append(test_data.get_case_payload(idx, deepcopy(create_req["ao_payload_info"]),
                                                                    client_metadata, pipeline_blueprint))
                    if len(inquiry_list) == create_req["new_consumers"]["max_pick"]:
                        break
                execute_req.append({"inquiry_payloads": inquiry_list, 
                                    "batch_size": create_req["run_batch_size"], 
                                    "baseline_responses": None,
                                    "solution_id": _solution_id,
                                    "case_code": create_req["new_consumers"]["case_code"],
                                    "modes": [{"Test-Engine": f'Record-{create_req["new_consumers"]["case_code"]}'} if create_req["verified_create_request"] else {}
                                        for _ in range(len(inquiry_list))]
                                    })
                if create_req["new_consumers"]["save_consumer_pii"]:
                    assert len(create_req["new_consumers"]["case_code"]) > 0, "case_code needs to be defined for saving pii"
                    action_list = []
                    for inquiry in inquiry_list:
                        action_list.append({
                            '_op_type': 'create',
                            '_index': rts_config.ES_CONSUMERS_DB_NAME,
                            'pii_info': json.dumps(inquiry["consumer_pii"]), 
                            'case_code': create_req["new_consumers"]["case_code"],
                            'star_info': create_req["new_consumers"]["excel_file_name"]
                            })
                    self.es_conn.bulk_import2(actions=action_list)
                    self.logger.write_log_item(message=f'>>>> RTS >>>>: {len(action_list)} new {create_req["new_consumers"]["case_code"]} consumers onboarded to DB ', level="WARNING")
            else:
                raise Exception("Unable to download STAR excel file")
            
        if create_req["existing_consumers"]:
            case_code_list = set()
            for case in create_req["existing_consumers"]:
                case_code_list.update(set(case["test_case_code"].split('-')))
            query = {
                "query": {
                    "bool": {
                        "should": [{ "term": { "case_code": case_code } } for case_code in case_code_list],
                        "minimum_should_match": 1
                    }
                }
            }
            consumer_piis = self.es_conn.get_document_by_query(index_name=rts_config.ES_CONSUMERS_DB_NAME, query=query)
            consumer_piis_cdict = defaultdict(list)
            for pii in consumer_piis:
                consumer_piis_cdict[pii['_source']['case_code']].append(Consumer(**json.loads(pii['_source']['pii_info'])))
            payload_pii_dict = {}
            for case in create_req["existing_consumers"]:
                case_code = case["test_case_code"]
                volume = case["volume"]
                if '-' in case_code:
                    cc1, cc2 = case_code.split('-') # primary-secondary
                    num_cases = int(volume*len(consumer_piis_cdict[cc1])*len(consumer_piis_cdict[cc2]) if volume <= 1 \
                        else min(volume, len(consumer_piis_cdict[cc1])*len(consumer_piis_cdict[cc2])))
                    random.shuffle(consumer_piis_cdict[cc1])
                    random.shuffle(consumer_piis_cdict[cc2])
                    for idx in range(len(consumer_piis_cdict[cc1])):
                        for jdx in range(len(consumer_piis_cdict[cc2])):
                            if not case_code in payload_pii_dict:
                                payload_pii_dict[case_code] = []
                            pii1 = deepcopy(consumer_piis_cdict[cc1][idx])
                            pii2 = deepcopy(consumer_piis_cdict[cc2][jdx])
                            pii1.secondary_applicant = Secondary(**json.loads(pii2.primary_applicant.json()))
                            payload_pii_dict[case_code].append(pii1)
                            if len(payload_pii_dict[case_code]) == num_cases:
                                break
                        if len(payload_pii_dict[case_code]) == num_cases:
                            break
                else:
                    num_cases = int(volume*len(consumer_piis_cdict[case_code]) if volume <= 1 \
                        else min(volume, len(consumer_piis_cdict[case_code])))
                    indices = random.sample(range(len(consumer_piis_cdict[case_code])), num_cases)
                    payload_pii_dict[case_code] = [consumer_piis_cdict[case_code][idx] for idx in indices]            
            
            for case_code in payload_pii_dict:
                inquiry_list = []
                for pii in payload_pii_dict[case_code]:
                    inquiry_payload = deepcopy(create_req["ao_payload_info"])
                    if create_req["inquiry_string_info"] is not None:
                        inquiry_payload["inquiry"] = TestInquiryString(solution_doc, create_req["inquiry_string_info"], 
                                            pii).assemble_inquiry_str_by_test_case("valid_inquiry")
                    inquiry_payload["consumer_pii"] = json.loads(pii.model_dump_json())
                    inquiry_list.append(inquiry_payload)
                execute_req.append({"inquiry_payloads": inquiry_list, 
                                    "batch_size": create_req["run_batch_size"], 
                                    "baseline_responses": None,
                                    "solution_id": _solution_id,
                                    "case_code": case_code,
                                    "modes": [{"Test-Engine": f'Record-{case_code}'} if create_req["verified_create_request"] else {}
                                                for _ in range(len(inquiry_list))]
                                    })
        
        if create_req["solution_edgecases"]:
            assert create_req["inquiry_string_info"] is not None, KeyError("inquiry_string_info is required for edgecases")
            query = {
                "query": {
                    "term": { "case_code": "HIT" }
                }
            }
            consumer_piis = self.es_conn.get_document_by_query(index_name=rts_config.ES_CONSUMERS_DB_NAME, 
                                                               query=query, max_size=5)
            inquiry_list = []
            for edgecase in create_req["solution_edgecases"]:
                for pii in consumer_piis:
                    pii = Consumer(**json.loads(pii['_source']['pii_info']))
                    inquiry_payload = deepcopy(create_req["ao_payload_info"])
                    inquiry_payload["inquiry"], inquiry_payload["consumer_pii"] = TestInquiryString(solution_doc, create_req["inquiry_string_info"], 
                                            pii).assemble_inquiry_str_by_test_case(edgecase), json.loads(pii.model_dump_json())
                    inquiry_list.append(inquiry_payload)
            execute_req.append({"inquiry_payloads": inquiry_list, 
                                "batch_size": create_req["run_batch_size"], 
                                "baseline_responses": None,
                                "solution_id": _solution_id,
                                "case_code": "EDGECASE",
                                "modes": [{"Test-Engine": "Record-EDGECASE"} if create_req["verified_create_request"] else {}
                                                            for _ in range(len(inquiry_list))]
                                })            
        
        return execute_req

    def handle_execute_request(self, job_req):
        execute_req = job_req["execute"]  
        ao_request = AscendOpsRequestHandler(ascendops_api=f'{job_req["ascendops_url"]}{job_req["ascendops_endpoint"]}', logger=self.logger)
        run_results = []  
        loop = asyncio.new_event_loop()
        for req in execute_req:       
            inquiry_responses, response_latencies = loop.run_until_complete(ao_request.getResponsesBatched(req["inquiry_payloads"], \
                batch_size=req["batch_size"], modes=req["modes"]))
            baseline_responses = req["baseline_responses"]
            if baseline_responses is not None:
                pass_track = []
                for idx in range(len(baseline_responses)):
                    curr_resp, base_resp = inquiry_responses[idx], baseline_responses[idx]['inquiry_response']
                    is_match, html_diff = match_ao_response(req["inquiry_payloads"][idx], curr_resp, base_resp)
                    pass_track.append({"pass": is_match, "html_diff": html_diff})
                latency_stats = ao_request.get_latency_stats(response_latencies, pass_track)
                run_results.append({
                    "solution_id": req["solution_id"],
                    "case_code": req["case_code"],
                    "batch_size": req["batch_size"],
                    "testcases": [{"testcase_id": base_resp["go_transaction_id"], "result": result, "latency": latency}\
                        for base_resp, result, latency in zip(baseline_responses, pass_track, response_latencies)],
                    "latency_stats": latency_stats
                })
            else:
                latency_stats = ao_request.get_latency_stats(response_latencies)
                create_result = []
                for idx, resp in enumerate(inquiry_responses):
                    create_result.append(
                        {"testcase_id": resp["payload"]["go_transaction_id"], "latency": response_latencies[idx]})
                run_results.append({
                    "solution_id": req["solution_id"],
                    "case_code": req["case_code"],
                    "batch_size": req["batch_size"],
                    "sample_ao_request": req["inquiry_payloads"][random.randint(0, len(inquiry_responses)-1)],
                    "testcases": create_result,
                    "latency_stats": latency_stats
                })
        return run_results
