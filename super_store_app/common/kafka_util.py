"""
All AWS MSK - Kafka related stuffs
"""
import json
import os

import boto3

from common.s3_util import CACERT_LOCAL_PATH, PUBLIC_CERT_LOCAL_PATH, \
    PRIVATE_KEY_LOCAL_PATH, download_pem_files

# bootstrap_servers: use one of these
# "b-1.msk-cluster.dgoa46.c10.kafka.us-east-1.amazonaws.com:9094",
# "b-2.msk-cluster.dgoa46.c10.kafka.us-east-1.amazonaws.com:9094"
# As of June 22, 2021
# b-1.msk-cluster.88xc7u.c5.kafka.us-east-1.amazonaws.com
# b-2.msk-cluster.88xc7u.c5.kafka.us-east-1.amazonaws.com

NUMBER_OF_MSG_HANDLERS = int(os.getenv("NUMBER_OF_MSG_HANDLERS", "50"))
MSK_BOOTSTRAP_SERVERS = os.getenv("MSK_BOOTSTRAP_SERVERS", "10.10.138.134:9092")
MSK_BATCH_TOPIC = os.getenv("MSK_BATCH_TOPIC", "test")
MSK_ERROR_TOPIC = os.getenv("MSK_ERROR_TOPIC", "error")
COMSUMER_POLL_TIMEOUT = int(os.getenv("COMSUMER_POLL_TIMEOUT", "10"))
MAX_POLL_INTERVAL_MS = int(os.getenv("MAX_POLL_INTERVAL_MS", "300000"))
SESSION_TIMEOUT_MS = int(os.getenv("SESSION_TIMEOUT_MS", "10000"))
HEARTBEAT_INTERVAL_MS = int(os.getenv("HEARTBEAT_INTERVAL_MS", "3000"))

DEFAULT_REGION = os.getenv("DEFAULT_REGION", "us-east-1")
# DEFAULT_ROLE = os.getenv("DEFAULT_ROLE", "arn:aws:iam::994075455914:role/dev-batch-execution-task-execution-role")       
MSK_SECRET_NAME = os.getenv("MSK_SECRET_NAME", "batch_transformation_msk")

def retrieve_password():
    """Retrieve from secret manage    
    arn:aws:secretsmanager:us-east-1:994075455914:secret:batch_transformation_msk-T5NLZD 
    
    {'ARN': 'arn:aws:secretsmanager:us-east-1:994075455914:secret:batch_transformation_msk-T5NLZD', 
    'Name': 'batch_transformation_msk', 'VersionId': '8ca01d2d-5a6c-4878-a41e-12979a896b25', 
    'SecretString': '{"msk_private_key_pwd":"Test123"}', 
    'VersionStages': ['AWSCURRENT'], 
    'CreatedDate': datetime.datetime(2021, 5, 3, 17, 15, 13, 751000, tzinfo=tzlocal()), 
    'ResponseMetadata': {'RequestId': 'db73682a-9022-41e8-9615-139f2608dad9', 
    'HTTPStatusCode': 200, 
    'HTTPHeaders': {'x-amzn-requestid': 'db73682a-9022-41e8-9615-139f2608dad9', 
    'content-type': 'application/x-amz-json-1.1', 
    'content-length': '296', 'date': 'Mon, 03 May 2021 19:33:22 GMT'}, 'RetryAttempts': 0}}      
    """
    password = None
    secret_name = MSK_SECRET_NAME
    session = boto3.Session(region_name=DEFAULT_REGION)
    credentials = session.get_credentials()
    secret_client = session.client(
        service_name='secretsmanager',
        aws_access_key_id=credentials.access_key,
        aws_secret_access_key=credentials.secret_key,
        aws_session_token=credentials.token,
        region_name=DEFAULT_REGION
    )
    secret_res = secret_client.get_secret_value(SecretId=secret_name)
    secret_json = json.loads(secret_res["SecretString"])
    password = secret_json["msk_private_key_pwd"]
    return password


def get_kafka_params():
    """To retrieve PEM files from S3, and password from Secret Manger.
    An application MUST be aware to avoid calling this multiple times.
    """
    password = retrieve_password()
    download_pem_files()
    return  {
        "private_key_pwd": password,
        "cafile_path": CACERT_LOCAL_PATH,        
        "certfile_path": PUBLIC_CERT_LOCAL_PATH,
        "keyfile_path": PRIVATE_KEY_LOCAL_PATH
    }
