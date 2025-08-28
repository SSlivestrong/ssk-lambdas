import json
import os
import sys
sys.path.insert(0, "./")

os.environ["DEFAULT_REGION"] = "us-east-1"
os.environ["AWS_ACCOUNT"] = "262403030294"
os.environ["AWS_PROFILE"] = "ascend-go-prod"
os.environ["IAM_PROFILE"] = "ascend-go-prod"
os.environ["DEFAULT_ES_HOST"] = "vpc-uat-ascend-go-wdae7basbpxdvkgtpnicgu53jm.us-east-1.es.amazonaws.com"
os.environ["DEFAULT_ES_PORT"] = "443"
os.environ["DEFAULT_ES_ROLE"] = "arn:aws:iam::262403030294:role/uat-es-role"
from regression_test_suite.helpers.es_util import ESConnector
es_conn = ESConnector.instance(startup=True)

# index_name = 'expn-ascend-ops-rts-consumers'
# index_name = 'expn-ascend-ops-rts-testcases'
index_name = 'expn-ascend-ops-rts-history'
index_setting_file = f'regression_test_suite/es_schemas/{index_name}.json'
# mode = 'CREATE'
# mode = 'DELETE'
mode = 'CHECK'

if mode == 'CREATE':
    with open(index_setting_file) as file:
        index_setting = json.load(file)
    print(es_conn.create_index(index_name, index_setting))
elif mode == 'DELETE':
    print(es_conn.delete_index([index_name]))
elif mode == "CHECK":
    items = es_conn.get_document_by_query(index_name=index_name, query={'query':{'match_all':{}}})
    # items = es_conn.get_document_by_query(index_name=index_name, query={'query':{'match':{'case_code':'LOCKED'}}})
    # print(len(items))
    for item in items:
        print(item)
        

    # print(es_conn.get_document(index_name=index_name, doc_id="09112024001559FYDSUDAEP"))
    # query = {
    #         "query": {
    #             "bool": {
    #                 "must": { "term": { "solution_id": "AOEXETERCM" } }
    #             }
    #         }
    #     }
    # items = es_conn.get_document_by_query(index_name=index_name, query=query)

    
    # Update ES mapping and add new field value
    # mapping = {
    #     "properties": {
    #         "status": {
    #             "type": "keyword"
    #             }
    #         }
    #     }
    # resp = es_conn.esearch.indices.put_mapping(index=index_name, body=mapping)
    # action_list = [ {
    #     "_op_type": "update",
    #     "_index": index_name,
    #     "_id": item["_source"]["testcase_id"],
    #     "doc": {"status": "NA"}
    #     } for item in items ]
    # helpers.bulk(es_conn.esearch, actions=action_list)
    
pass
