from helpers.es_util import ESConnector
from regression_test_suite.helpers.singleton_wrapper import singleton
from helpers import rts_config
from collections import defaultdict
import datetime
import random
import boto3
import json

@singleton
class RtsEsFilter():
    def __init__(self) -> None:
        self.es_conn = ESConnector.instance(startup=True)

    def prepare_query(self, filters: dict):
        must_terms = []
        for key, value in filters.items():
            if len(value) > 0:
                if key == "trade_date":
                    split = value.split(",")
                    assert len(split) <= 2, "Invalid trade_date format. Should be '>start_date,<end_date'"
                    range = {}
                    for bound in split:
                        if bound[0] == ">":
                            range["gt"] = bound[1:].strip()
                        elif bound[0] == "<":
                            range["lt"] = bound[1:].strip()
                        else:
                            raise ValueError("Invalid trade_date format. Should be '>start_date,<end_date'")
                    must_terms.append({ "range": { key: range } })
                else:
                    must_terms.append({ "term": { key: value } })

        query = {
            "query": {
                    "bool": {
                        "must": must_terms
                    }
                }
            }
        
        return query
        
    def get_execution_request(self, run_req):
        execute_req = []
        for test in run_req["tests"]:
            query = self.prepare_query(test["filters"])
            testcases = self.es_conn.get_document_by_query(index_name=rts_config.ES_TESTCASES_DB_NAME, 
                                                           exclude_fields=["services"], query=query)
            volume = test["volume"]
            num_cases = int(volume*len(testcases) if volume <= 1 else min(volume, len(testcases)))
            indices = random.sample(range(len(testcases)), num_cases)
            
            inquiry_payloads = []
            baseline_responses = []
            modes = []
            for idx in indices:
                inquiry_payloads.append(json.loads(testcases[idx]['_source']['ao_request']))
                try:
                    baseline_responses.append(json.loads(testcases[idx]['_source']['ao_response']))
                except KeyError:
                    # few edgecases may not have auditlog message for ao_response
                    baseline_responses.append({
                        "go_transaction_id": testcases[idx]['_source']["testcase_id"],
                        "inquiry_response": None
                    })
                modes.append({'Test-Engine': f'Replay-{testcases[idx]["_source"]["testcase_id"]}'})
            execute_req.append({
                "solution_id": test["filters"]["solution_id"],
                "case_code": test["filters"]["case_code"],
                "inquiry_payloads": inquiry_payloads,
                "batch_size": test["batch_size"],
                "baseline_responses": baseline_responses,
                "modes": modes
            })
            
        return execute_req
    
    def get_testcases(self, get_req, write_to_s3=False):
        query = self.prepare_query(get_req)
        testcases = self.es_conn.get_all_documents_by_scroll(index_name=rts_config.ES_TESTCASES_DB_NAME, query=query)
        resp = {
            "testcases": []
        }
        for testcase in testcases:
            try:
                testcase['_source']['services'] = json.loads(testcase['_source']['services'])
                testcase['_source']['ao_request'] = json.loads(testcase['_source']['ao_request'])
                testcase['_source']['ao_response'] = json.loads(testcase['_source']['ao_response'])
            except:
                pass
            resp["testcases"].append(testcase['_source'])
        
        if write_to_s3:
            resp = json.dumps(resp, indent=4)
            output_bucket = boto3.resource('s3', region_name=rts_config.DEFAULT_REGION).Bucket(rts_config.EXCEL_BUCKET_NAME)
            testcases_file = f'get_testcases_output/{get_req["solution_id"]}_{get_req["case_code"]}.json'
            output_bucket.put_object(Key=testcases_file, 
                                     Body=resp)
            return { "file_name": f"{testcases_file}", 
                     "download_from": "s3://expn-ascend-ops-rts-testdata-bucket3" }
        return resp
    
    def get_testcases_info(self, solution_id):
        query = self.prepare_query({"solution_id": solution_id})
        testcases = self.es_conn.get_document_by_query(index_name=rts_config.ES_TESTCASES_DB_NAME, 
                                                            query=query, include_fields=["case_code", "testcase_id", "trade_date", "status"])
        resp = {
            "testcases_info": defaultdict(list)
        }
        for testcase in testcases:
            resp["testcases_info"][testcase["_source"]["case_code"]].append({
                "testcase_id": testcase["_source"]["testcase_id"],
                "trade_date": testcase["_source"]["trade_date"],
                "status": testcase["_source"]["status"]
            })
        return resp
        
    def delete_testcases(self, delete_req):
        query = self.prepare_query(delete_req["filters"])
        testcases = self.es_conn.get_document_by_query(index_name=rts_config.ES_TESTCASES_DB_NAME, 
                                                            query=query, include_fields=["testcase_id"])
        if len(testcases) > 0:
            history_req = {
                "tested_by": delete_req["tested_by"],
                "response": [testcase["_source"]["testcase_id"] for testcase in testcases],
                "solution_id": delete_req["filters"]["solution_id"]
            }
            self.update_rts_history(history_req, req_type="delete")
        result = self.es_conn.delete_documents_by_query(index_name=rts_config.ES_TESTCASES_DB_NAME, query=query)
        return {"deleted": result["deleted"], "failures": result["failures"]}
    
    def count_filtered_testcases(self, count_req):
        query = self.prepare_query(count_req)
        num_docs = self.es_conn.count_documents(index_name=rts_config.ES_TESTCASES_DB_NAME, query=query)
        return num_docs["count"]
    
    def update_rts_history(self, history_req, req_type):
        assert req_type in ["create", "run", "delete"], f"Invalid history update request type: {req_type}. Should be one of ['create', 'run', 'delete']"
        trade_date = str(datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"))
        query = self.prepare_query({"solution_id": history_req["solution_id"]})
        history = self.es_conn.get_document_by_query(index_name=rts_config.ES_HISTORY_DB_NAME, 
                                                            query=query, include_fields=["metadata"])
        if len(history) > 0:
            current_metadata = history[0].get('_source', {}).get('metadata', [])
        else:
            current_metadata = []
        if req_type == "create" or req_type == "run":
            action_list = []
            for result in history_req["response"]:
                for testcase in result["testcases"]:
                   action_list.append( {
                        "_op_type": "update",
                        "_index": rts_config.ES_TESTCASES_DB_NAME,
                        "_id": testcase["testcase_id"],
                        "doc_as_upsert" : True,
                        "doc": {"status": "NA" if "result" not in testcase else ("Pass" if testcase["result"]["pass"] else "Fail")}
                    } )
            self.es_conn.bulk_import2(actions=action_list)
            current_metadata.insert(0, {
                "tested_by": history_req["tested_by"],
                "trade_date": trade_date,
                "summary": f"{req_type.upper()} {len(action_list)} testcases."
            })
            update_req = {
                req_type: { 
                    "tested_by": history_req["tested_by"],
                    "request": json.dumps(history_req["request"]),
                    "response": json.dumps(history_req["response"]),
                    "trade_date": trade_date
                },
                "metadata": current_metadata
            }
        elif req_type == "delete":
            current_metadata.insert(0, {
                "tested_by": history_req["tested_by"],
                "trade_date": trade_date,
                "summary": f"DELETE {len(history_req['response'])} testcases."
            })
            update_req = {
                "metadata": current_metadata
            }
        update_req["solution_id"] = history_req["solution_id"]
        self.es_conn.upsert_document(index_name=rts_config.ES_HISTORY_DB_NAME, doc_id=history_req["solution_id"],
                                    doc_content=update_req)

    def get_rts_history(self, solution_id):
        query = self.prepare_query({"solution_id": solution_id})
        history = self.es_conn.get_document_by_query(index_name=rts_config.ES_HISTORY_DB_NAME, query=query)
        resp = {
            "history": []
        }
        for hist in history:
            try:
                hist["_source"]["create"]["request"] = json.loads(hist["_source"]["create"]["request"])
                hist["_source"]["create"]["response"] = json.loads(hist["_source"]["create"]["response"])
            except:
                pass
            try:
                hist["_source"]["run"]["request"] = json.loads(hist["_source"]["run"]["request"])
                hist["_source"]["run"]["response"] = json.loads(hist["_source"]["run"]["response"])
            except:
                pass
            resp["history"].append(hist["_source"])
        return resp
    
    def delete_consumers(self, case_code):
        query = self.prepare_query({"case_code": case_code})
        result = self.es_conn.delete_documents_by_query(index_name=rts_config.ES_CONSUMERS_DB_NAME, query=query)
        return {"deleted": result["deleted"], "failures": result["failures"]}