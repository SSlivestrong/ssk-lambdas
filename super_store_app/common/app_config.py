"""Module contains all constants
"""
import os

# Env Config
DEFAULT_REGION = os.getenv("DEFAULT_REGION", "us-east-1")
AWS_ACCOUNT = os.getenv("AWS_ACCOUNT", "994075455914")
EXEC_STAGE = os.getenv("EXEC_STAGE", "dev")
LOG_LEVEL = int(os.getenv("LOG_LEVEL", "20"))
IAM_PROFILE = os.getenv("IAM_PROFILE", "")
KAFKA_PRODUCER_TIMEOUT = int(os.getenv("KAFKA_PRODUCER_TIMEOUT", "10"))
APP_NAME = os.getenv("APP_NAME", "goapi")
INTERNAL_CLIENT_ALIAS = os.getenv("INTERNAL_CLIENT_ALIAS", "experian")
ASCEND_OPS_CLIENT_ALIAS = os.getenv("ASCEND_OPS_CLIENT_ALIAS","ascend-ops-platform")
APP_DIR = os.getenv("APP_DIR", "/Users/c72246a/tmp")

# Kafka Config
SECURITY_PROTOCOL = os.getenv("SECURITY_PROTOCOL", "local")
MSK_CERT_BUCKET_NAME = os.getenv("MSK_CERT_BUCKET_NAME", "dev-go-artifacts-us-east-1-994075455914")

# Certs
CACERT_S3_PATH = os.getenv("CACERT_S3_PATH", "certs/dev_go_acm_cacert.pem")
PUBLIC_CERT_S3_PATH = os.getenv("PUBLIC_CERT_S3_PATH", "certs/dev_go_public_cert.pem")
PRIVATE_KEY_S3_PATH = os.getenv("PRIVATE_KEY_S3_PATH", "certs/dev_go_private_key.pem")
CACERT_FILE_NAME = os.getenv("CACERT_FILE_NAME", "dev_go_acm_cacert.pem")
PUBLIC_CERT_FILE_NAME = os.getenv("PUBLIC_CERT_FILE_NAME", "dev_go_public_cert.pem")
PRIVATE_KEY_FILE_NAME = os.getenv("PRIVATE_KEY_FILE_NAME", "dev_go_private_key.pem")
