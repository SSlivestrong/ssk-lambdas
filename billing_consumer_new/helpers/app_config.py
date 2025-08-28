
""" Configuration file for the billing consumer """

import os

# AWS Config
SECURITY_PROTOCOL =  os.getenv("SECURITY_PROTOCOL", "local")
DEFAULT_REGION = os.getenv("DEFAULT_REGION", "us-east-1")
DYNAMODB_URL = f"https://dynamodb.{DEFAULT_REGION}.amazonaws.com"
 
# Kafka Config
KAFKA_GROUP_ID = "lift-premium-group"
KAFKA_NO_CONSUMER_PER_INSTANCE_MAX = 8
KAFKA_NO_CONSUMER_PER_INSTANCE = int(os.getenv("KAFKA_NO_CONSUMER_PER_INSTANCE", 4))
NUMBER_OF_MSG_HANDLERS = int(os.getenv("NUMBER_OF_MSG_HANDLERS", "50"))
MSK_BOOTSTRAP_SERVERS = os.getenv("MSK_BOOTSTRAP_SERVERS", "localhost:9092")

# Billing Config
BILLING_TOPIC = os.getenv("BILLING_TOPIC", "refactored_billing")
BILLING_RECORD_LENGTH = 785
ALLOUT_BILLING_TABLE_NAME = os.getenv("ALLOUT_BILLING_TABLE_NAME", "uat_bc_billing")
PRODUCT_CODES_BILLING_TABLE_NAME = os.getenv("PRODUCT_CODES_BILLING_TABLE_NAME", "uat_bc_product_codes_info")
ALLOUT_BILLING_TABLE_COLUMNS = ["transaction_id", "inquiry_timestamp", "billing_record", "silent_launch", "solution_id", "subcode"]
PRODUCT_CODES_BILLING_TABLE_COLUMNS = ["transaction_id", "inquiry_timestamp", "solution_id", "subcode", "product_code", "product_code_type", "silent_launch"]


LOG_LEVEL = int(os.getenv("LOG_LEVEL", "10"))

# Crypto Config
CRYPTO_ENV = os.getenv("CRYPTO_ENV")
CRYPTO_ENV_PREFIX = os.getenv("CRYPTO_ENV_PREFIX")
CRYPTO_AWS_PROFILE = os.getenv("CRYPTO_AWS_PROFILE")
CRYPTO_INSTANCES = int(os.getenv("CRYPTO_INSTANCES"))
CRYPTO_LJAR = os.getenv("CRYPTO_LJAR")

# General Config
OPS_SUB_SYSTEM_NAME = "GOCR"
OPS_CALLING_SUB_SYSTEM_NAME = "GOXX"

ANALYTICS_RDS_DATABASE_SCHEMA = os.getenv("ANALYTICS_RDS_DATABASE_SCHEMA", "uat_analytics")
ANALYTICS_RDS_KEY_NAME = os.getenv("ANALYTICS_RDS_KEY_NAME", "uat-analytics-ops-rw")