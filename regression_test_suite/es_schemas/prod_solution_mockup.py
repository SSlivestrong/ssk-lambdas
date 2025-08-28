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

print(es_conn.delete_documents_by_query("test_eng_solution", query={
        "query": {
            "match_all": {}
        }
    }
))

with open("regression_test_suite/es_schemas/prod_solutions.json") as f:
    prod_solutions = json.load(f)

num_sols = 0
for solution in prod_solutions["payload"]["solutions"]:
    if "status" in solution:
        if solution["status"] == "prod":
            print(es_conn.upsert_document("test_eng_solution", solution["uid"], solution))
            num_sols += 1

print(f'Total solutions inserted: {num_sols}')