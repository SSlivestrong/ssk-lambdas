from helpers.es_util import ESConnector
from regression_test_suite.helpers import service_helpers, rts_enums, rts_config
from regression_test_suite.helpers.singleton_wrapper import singleton
from functools import lru_cache

@singleton
class ReplayCache():
    def __init__(self, db_table_name, logger) -> None:
        self.es_conn = ESConnector.instance(startup=True)
        self.index_name = db_table_name
        self.logger = logger   
        
    @lru_cache(maxsize=int(rts_config.REPLAY_CACHE_SIZE))
    def get_record(self, testcase_id: str):
        try:
            return self.es_conn.get_document(index_name=self.index_name, doc_id=testcase_id, 
                                             include_fields=["services"])["_source"]
        except Exception as xcp:
            xcp_detail, tb_detail = service_helpers.extract_exception_traceback(xcp)
            self.logger.log_json(
                event_type = rts_enums.RtsEnum.REPLAY_CACHE.value,
                content = {
                    "testcase_id": testcase_id,
                    "message": "Failed to fetch testcase from DB",
                    "exception": xcp_detail,
                    "traceback": tb_detail
                },
                level="ERROR"
            )   
        