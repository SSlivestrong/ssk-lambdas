
""" This module contains the code to consume messages from Kafka """

import traceback
from aiokafka import AIOKafkaConsumer
from aiokafka.helpers import create_ssl_context
from aiokafka import AIOKafkaConsumer
from billing_consumer_new.helpers import app_config
from billing_consumer_new.helpers import app_logger
from billing_consumer_new.helpers.app_logger import custom_logger
import traceback
from ascendops_commonlib.app_utils.kafka_util import KafkaWriter
from ascendops_commonlib.ops_utils import ops_util
from billing_consumer_new.helpers import app_config
from billing_consumer_new.billing_service.billing_handler import billing_handler


class AIOConsumer:
    def __init__(self, unique_client_id, unique_group_id, **kwargs):
        """
        Each Consumer MUST have a unique ID.
        Multiple Consumers to consume the same topic MUST belong to the same group
        """
        self.consumed_msg_count = 0
        self.client_id = unique_client_id
        self.group_id = unique_group_id
        protocol = kwargs.pop("security_protocol", "SSL")
        offset_reset = kwargs.pop("auto_offset_reset", "earliest")
        if protocol == "SSL":
            private_key_pwd = kwargs.pop("private_key_pwd")
            cafile_path = kwargs.pop("cafile_path")
            certfile_path = kwargs.pop("certfile_path")
            keyfile_path = kwargs.pop("keyfile_path")
            context = create_ssl_context(
                cafile=cafile_path,
                certfile=certfile_path,
                keyfile=keyfile_path,
                password=private_key_pwd
            )
            # context.check_hostname = False
            self.consumer = AIOKafkaConsumer(
                bootstrap_servers=app_config.MSK_BOOTSTRAP_SERVERS,
                client_id=unique_client_id,
                group_id=unique_group_id,
                auto_offset_reset=offset_reset,
                enable_auto_commit=False,
                max_poll_records=app_config.NUMBER_OF_MSG_HANDLERS,
                security_protocol=protocol,
                ssl_context=context
            )
        else:
            self.consumer = AIOKafkaConsumer(
                bootstrap_servers=app_config.MSK_BOOTSTRAP_SERVERS,
                client_id=unique_client_id,
                group_id=unique_group_id,
                auto_offset_reset=offset_reset,
                enable_auto_commit=False,
                max_poll_records=app_config.NUMBER_OF_MSG_HANDLERS
              )

    async def consume_batch(self, topic, handler):
        """
        Start consuming kafka message
        Args:
            topic: the topic to consume messages.
            handler: Function to process a message. It must be synchronous; i.e.,
            blocking execution.
        """
        # Need to check if, what partition configuration here
        self.consumer.subscribe([topic])
        custom_logger.logger.info("[S] %s/%s starts consuming from topic: %s", self.group_id, self.client_id, topic)
        # self.logger.info("[S] bootstrap_connected %s", self.consumer.bootstrap_connected())
        partitions = self.consumer.partitions_for_topic(topic)
        custom_logger.logger.info("[S] partitions_for_topic %s", partitions)

        await self.consumer.start()

        while True:
            # Now, this consumer picks up message at the right position
            result = await self.consumer.getmany(timeout_ms=10 * 1000)
            for tp, messages in result.items():
                # message is an instance of ConsumerRecord(topic='test', partition=0, offset=50,
                # timestamp=1619202704246, timestamp_type=0, serialized_header_size=-1,
                # headers=[], checksum=None, serialized_key_size=13, serialized_value_size=44,
                # key=b'tB_1619202704',
                # value=b'{"msg": {"id": 46}, "body": "tB_1619202704"}')
                try:
                    if messages:
                        await handler(messages)
                        await self.consumer.commit({tp: messages[-1].offset + 1})
                        custom_logger.logger.info("[S] %s/%s consumed (partition %s offset %s) messages length: %s", self.group_id,
                                      self.client_id, tp, messages[-1].offset, len(messages))
                except Exception as xcp:
                    custom_logger.logger.error("[S] %s", xcp)
                    custom_logger.logger.error("[S] %s", traceback.format_exc())
 

class BillingConsumer:
    def __init__(self, crypto_util, mysql_instance, name="billing_consumer"):
        self.msk_topic = app_config.BILLING_TOPIC
        self.kafka_params = KafkaWriter.KAFKA_PARAMS
        consumer_client_id = name + "-consumer-" + ops_util.get_epoch_seconds_string()
        self.msk_consumer = AIOConsumer(consumer_client_id, app_config.KAFKA_GROUP_ID,
                                        **self.kafka_params.copy())
        self.mysql = mysql_instance
        self.crypto_util = crypto_util
        self.messages = []

    async def run(self):
        custom_logger.logger.info("Billing Consumer is running")
        await self.msk_consumer.consume_batch(self.msk_topic, self.batch_handler)
        custom_logger.logger.info("Billing Consumer exists")

    async def batch_handler(self, messages):
        await billing_handler(messages, self.crypto_util, self.mysql)