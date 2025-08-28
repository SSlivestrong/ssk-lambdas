import os

# kafka server
MSK_BOOTSTRAP_SERVERS = os.getenv("MSK_BOOTSTRAP_SERVERS", "localhost:9092")

# number of Kafka consumers
KAFKA_NO_CONSUMER_PER_INSTANCE = os.getenv("KAFKA_NO_CONSUMER_PER_INSTANCE", "1")

# ascend ops server
AO_SERVICE_URL = os.getenv("AO_SERVICE_URL", "localhost:5000")

# default aws region
DEFAULT_REGION = os.getenv("DEFAULT_REGION", "us-east-1")

# s3 bucket name for excel files
EXCEL_BUCKET_NAME = os.getenv("EXCEL_BUCKET_NAME", "")

# es testcases db name
ES_TESTCASES_DB_NAME = os.getenv("ES_TESTCASES_DB_NAME", "")

# es consumers db name
ES_CONSUMERS_DB_NAME = os.getenv("ES_CONSUMERS_DB_NAME", "")

# es history db name
ES_HISTORY_DB_NAME = os.getenv("ES_HISTORY_DB_NAME", "")

# regression data service replay cache size
REPLAY_CACHE_SIZE = os.getenv("REPLAY_CACHE_SIZE", "100")

# regression test service job queue size
JOB_QUEUE_SIZE = os.getenv("JOB_QUEUE_SIZE", "300")

# audit log topic
AUDIT_LOG_TOPIC = os.getenv("AUDIT_LOG_TOPIC", "audit_log")