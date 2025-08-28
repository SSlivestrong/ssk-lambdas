from helpers.es_util import ESConnector
from ascendops_commonlib.app_utils.kafka_util import KafkaWriter
from regression_test_suite.services.audit_log_consumer_app.async_consumer import AIOConsumer, VersionedMessage
from regression_test_suite.helpers import app_logger, service_helpers, rts_enums, rts_config
import datetime
import asyncio
import orjson
import uuid
import json
import re

class RTSAuditLogConsumer():
    def __init__(self, rts_record_logger: app_logger.CustomLogger):
        self.es_conn = ESConnector.instance(startup=True)
        self.rts_record_logger = rts_record_logger
        KafkaWriter.on_app_start()
        self.consumer = AIOConsumer(unique_client_id=str(uuid.uuid4()), 
                        unique_group_id="rts-audit-log-group", 
                        log=app_logger.get_app_logger(),
                        **KafkaWriter.KAFKA_PARAMS)
    
    def extract_rts_case_code(self, header_value: str, pattern: str = r"Record-([A-Z_]+(-[A-Z_]+)?)$"):
        match = re.match(pattern, header_value)
        if match:
            return match.group(1)
        return None

    async def consume(self, msgs):   
        for msg in msgs:
            if isinstance(msg, VersionedMessage):
                try:
                    consolidated_json = orjson.loads(msg.value_decompressed)
                    if not 'is_testcase' in consolidated_json: # check if the request is from v3 api
                        continue
                    if consolidated_json['is_testcase']:
                        service_data = {}
                        for service in consolidated_json['services']:
                            if not (service['service_name'] == 'SAGEMAKER' or service['service_name'] == 'SAGEMAKER-2'):
                                service_data[service['service_name']] = service
                            else:
                                service_data[f"{service['service_name']}_{service['content']['request']['model_uid']}"] = service
                        assert len(consolidated_json['services']) == len(service_data)
                        self.es_conn.upsert_document(index_name=rts_config.ES_TESTCASES_DB_NAME, 
                                            doc_id=consolidated_json['go_transaction_id'],
                                            doc_content={
                                'services': json.dumps(service_data),
                                'ao_response': json.dumps(consolidated_json['response_payload']),
                            }
                        )
                        self.rts_record_logger.log_message(message=f'>>>> RTS >>>>: Testcase services written to DB ',
                                                        transaction_id=consolidated_json['go_transaction_id'],
                                                        level="WARNING")
                except Exception as xcp:
                    xcp_detail, tb_detail = service_helpers.extract_exception_traceback(xcp)
                    self.rts_record_logger.log_json(
                        event_type = rts_enums.RtsEnum.RTS_AUDITLOG_CONSUMER.value,
                        content = {
                            "transaction_id": consolidated_json['go_transaction_id'],
                            "message": "Audit-Log Consumer App Service Logging Error",
                            "exception": xcp_detail,
                            "traceback": tb_detail
                        },
                        level="ERROR"
                    )
            else:
                try:
                    inquiry_request = json.loads(msg.value)
                    if inquiry_request['service_name'] == 'INQUIRY_REQUEST':
                        if not 'request_headers' in inquiry_request['content']: # check if the request is from v3 api
                            continue
                        
                        header_key = None
                        # handle HTTP/1.1 specification (RFC 7230)
                        if 'Test-Engine' in inquiry_request['content']['request_headers']:
                            header_key = 'Test-Engine'
                        elif 'test-engine' in inquiry_request['content']['request_headers']:
                            header_key = 'test-engine'
                        if header_key is None:
                            continue
                        
                        case_code = self.extract_rts_case_code(inquiry_request['content']['request_headers'][header_key])
                        if case_code is None:
                            continue
                        
                        self.es_conn.upsert_document(index_name=rts_config.ES_TESTCASES_DB_NAME, 
                                                doc_id=inquiry_request['go_transaction_id'],
                                                doc_content={
                                'testcase_id': inquiry_request['go_transaction_id'],
                                'ao_request': json.dumps(inquiry_request['content']['request_payload']),
                                'solution_id': inquiry_request['content']['request_payload']['solution_id'],
                                'case_code': case_code,
                                'trade_date': str(datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"))
                            }
                        )
                        self.rts_record_logger.log_message(message=f'>>>> RTS >>>>: Testcase request written to DB ',
                                                            transaction_id=inquiry_request['go_transaction_id'],
                                                            level="WARNING")    
                except Exception as xcp:
                    xcp_detail, tb_detail = service_helpers.extract_exception_traceback(xcp)
                    self.rts_record_logger.log_json(
                        event_type = rts_enums.RtsEnum.RTS_AUDITLOG_CONSUMER.value,
                        content = {
                            "transaction_id": inquiry_request['go_transaction_id'],
                            "message": "Audit-Log Consumer App Request Logging Error",
                            "exception": xcp_detail,
                            "traceback": tb_detail
                        },
                        level="ERROR"
                    )
    
    async def start_consuming(self):
        await self.consumer.consume_batch(topic=rts_config.AUDIT_LOG_TOPIC, handler=self.consume)

async def init_consumer_app():
    rts_record_logger = app_logger.CustomLogger('rts_record_consumer_app')
    rts_consumer = RTSAuditLogConsumer(rts_record_logger)
    await rts_consumer.start_consuming()
    
if __name__ == "__main__":
    asyncio.run(init_consumer_app())