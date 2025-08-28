import logging
import os
import sys


SECURITY_PROTOCOL = os.getenv("SECURITY_PROTOCOL", "local")
DEFAULT_REGION = os.getenv("DEFAULT_REGION", "us-east-1")


SNAPSHOT_TOPIC = os.getenv("SUPER_STORE_TOPIC", "reporting")
KAFKA_GROUP_ID = os.getenv("KAFKA_GROUP_ID", "snapshot")
KAFKA_NO_CONSUMER_PER_INSTANCE_MAX = 8
KAFKA_NO_CONSUMER_PER_INSTANCE = int(os.getenv("KAFKA_NO_CONSUMER_PER_INSTANCE", "1"))


SNAPSHOT_ENCRYPTION_KEY = os.getenv(
    "SNAPSHOT_ENCRYPTION_KEY",
    "arn:aws:kms:us-east-1:262403030294:key/b6dc6ebe-b405-40c5-a28d-ed8a19a2c40e",
)
SUPER_STORE_S3_PATH = os.getenv(
    "SUPER_STORE_S3_PATH",
    "uat-ascend-ops-platform-us-east-1-262403030294/super_store_interim_data/",
)
SUPER_STORE_CONFIG_PATH = os.getenv(
    "SNAPSHOT_CONFIG_PATH",
    "uat-iad-us-east-1-262403030294/super_store_app/examples/configs/",
)
SUPER_STORE_PGP_SECRET_VAULT = os.getenv(
    "SUPER_STORE_PGP_SECRET_VAULT", "uat-reporting-secrets"
)
SUPER_STORE_PGP_SECRET = os.getenv("SUPER_STORE_PGP_SECRET", "reporting-private-key")

FEATURE_INDEX_NAME = os.getenv("FEATURE_INDEX_NAME", "feature")
DATASET_INDEX_NAME = os.getenv("DATASET_INDEX_NAME", "dataset")

APP_TEMP_DIR = os.getenv("APP_TEMP_DIR", "/tmp/")
FILE_NAME = "superstore_dataset-year-month-date-timestamp.json"
RECORD_COUNT = int(os.getenv("RECORD_COUNT", "200"))
log = logging.getLogger("superstore")
LOG_LEVEL = int(os.getenv("LOG_LEVEL", "20"))
log.setLevel(LOG_LEVEL)

for handler in log.handlers:
    log.removeHandler(handler)

stdout_handler = logging.StreamHandler(sys.stdout)
stdout_handler.setLevel(LOG_LEVEL)
# formatter = logging.Formatter("%(asctime)s - %(levelname)s %(message)s")
formatter = logging.Formatter("%(message)s")
stdout_handler.setFormatter(formatter)
log.addHandler(stdout_handler)
