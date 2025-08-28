import base64
import gzip
import json
from datetime import datetime
from functools import lru_cache

import api.app_global as app_global
import boto3
import gnupg
import orjson


class SuperStore:
    def __init__(self, log, s3_connector):
        """initialize"""
        self.log = log
        self.s3_connector = s3_connector

    @lru_cache(maxsize=1)
    def load_config(self, conf_file: str) -> dict:
        """Config file is just a json file with one key config which is an array of allowed solutions.
        For example:
        {
            "config": ["AOEXETERCM", "AOEXETER", "AOOHM" ]
        }
        """
        j = self.s3_connector.get_object(app_global.SUPER_STORE_CONFIG_PATH, conf_file)
        try:
            json.loads(j["Body"].read().decode("utf-8"))
        except Exception as e:
            log_msg = {
                "msg_type": "config_file_error",
                "error": str(e),
            }
            app_global.log.error(json.dumps(log_msg))
            raise
        return j

    def get_pgp_key_from_secret_manager(self, secret_name):
        client = boto3.client("secretsmanager")
        response = {}
        try:
            response = client.get_secret_value(SecretId=secret_name)
            secret_dict = json.loads(response["SecretString"])
            secret_string = secret_dict[app_global.SUPER_STORE_PGP_SECRET]

        except Exception as ex:
            app_global.log.error(response)
            raise Exception(f"Cannot fetch  secret: {str(ex)}")

        return secret_string

    def encrypt_string_with_pgp(self, entire_string, pgp_key):
        gpg = gnupg.GPG()
        decoded_pgp_key = base64.b64decode(pgp_key).decode("utf-8")
        import_result = gpg.import_keys(decoded_pgp_key)

        if not import_result:
            raise Exception(f"Failed to import PGP key")

        encrypted_data = gpg.encrypt(
            entire_string, import_result.fingerprints[0], always_trust=True
        )

        if not encrypted_data.ok:
            raise Exception(f"Encryption failed: {encrypted_data.status}")

        return str(encrypted_data)

    def validate_message(self, msg):
        """validates wether its ECS and its consolidated kafka msg if so returns consolidated message or {}"""
        list_of_tuples = msg.headers
        if len(list_of_tuples) > 0:
            value = msg.value
            value_decompressed = gzip.decompress(value)
            consolidated_message = orjson.loads(value_decompressed)
            flow_tags = consolidated_message.get("flow_tags", {})
            solution_id = str(flow_tags.get("solution_id", ""))
            log_msg = {"solution_id": str(solution_id)}
            app_global.log.info(log_msg)
            if solution_id in self.load_config("superstore_config.json")["config"]:
                return consolidated_message
        return {}

    async def create_emr_input(self, messages):
        """takes batch of kafka messages and writes them to S3"""
        if messages:
            for message in messages:
                msg_key = message.key
                log_msg = {"msg_key": str(msg_key), "msg_type": "processing_check"}
                app_global.log.info(json.dumps(log_msg))
                try:
                    msg_value = orjson.loads(gzip.decompress(message.value))
                    # here we filter objects that we need.
                    # objects = Audit(msg_value).load_data()
                    if msg_value:
                        await self.write_to_s3(msg_value)
                    else:
                        log_msg = {
                            "timestamp": message.timestamp,
                            "msg_key": f"{msg_key}",
                            "msg_type": "no_data",
                        }
                        app_global.log.info(json.dumps(log_msg))
                except Exception as e:
                    log_msg = {
                        "timestamp": message.timestamp,
                        "msg_key": f"{msg_key}",
                        "msg_type": "error pushing to s3",
                        "error": str(e),
                    }
                    app_global.log.info(json.dumps(log_msg))
                    raise

    async def write_to_s3(self, msg):
        """Write record to S3"""
        try:
            transaction_id = msg["INQUIRY"]["INQREQ"]["transaction_id"]
        except KeyError as e:
            log_msg = {
                "msg_type": "transaction_id_not_found",
                "data": str(msg),
                "error": str(e),
            }
            app_global.log.error(json.dumps(log_msg))
            raise

        log_msg = {"msg_type": "processing", "transid": f"{transaction_id}"}
        app_global.log.error(json.dumps(log_msg))

        try:
            solution_id = msg["INQUIRY"]["INQREQ"]["solution_id"]
        except KeyError as e:
            log_msg = {
                "msg_type": "solution_id_not_found",
                "data": str(msg),
                "error": str(e),
            }
            app_global.log.error(json.dumps(log_msg))
            raise

        try:
            s3path = app_global.SUPER_STORE_S3_PATH.split("/", 1)
            s3bucket = s3path[0]
            log_msg = {
                "msg_type": "superstore_record",
                "s3bucket": s3bucket,
            }

            app_global.log.info(json.dumps(log_msg))
            
            CURRENT_MONTH = transaction_id[0:2]
            CURRENT_DAY = transaction_id[2:4]
            CURRENT_YEAR = transaction_id[4:8]
            YYMMDD = CURRENT_YEAR + CURRENT_MONTH + CURRENT_DAY

            DIR_PREFIX_FORMAT = f"{CURRENT_YEAR}/{CURRENT_MONTH}/{YYMMDD}"

            s3_file_name = (
                f"/{solution_id}/{DIR_PREFIX_FORMAT}/"
                f"raw_data/{transaction_id}.json.gz"
            )

            key = f"{s3path[1].strip()}{s3_file_name}"
            entire_string = ""
            json_line = json.dumps(msg)
            entire_string += json_line
            entire_string += "\n"
            pgp_key = self.get_pgp_key_from_secret_manager(
                app_global.SUPER_STORE_PGP_SECRET_VAULT
            )

            encrypted_string = self.encrypt_string_with_pgp(entire_string, pgp_key)
            compressed_value = gzip.compress(bytes(encrypted_string, "utf-8"))

            await self.s3_connector.put_object(
                Bucket=s3bucket,
                Key=key,
                Body=compressed_value,
                ServerSideEncryption="aws:kms",
                SSEKMSKeyId=app_global.SNAPSHOT_ENCRYPTION_KEY,
            )
            log_msg = {
                "transid": f"{transaction_id}",
                "s3_file_name": s3_file_name,
                "s3_path": s3path[1],
                "msg_type": "uploaded_superstore_batch_object",
            }
            app_global.log.info(json.dumps(log_msg))

        except Exception as xcp:
            log_msg = {
                "transid": f"{transaction_id}",
                "msg_type": "superstore_write_to_s3_error",
                "error": str(xcp),
            }
            app_global.log.error(json.dumps(log_msg))
            raise
