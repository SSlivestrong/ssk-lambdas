import traceback
from aiokafka import AIOKafkaConsumer, TopicPartition, OffsetAndMetadata
from aiokafka.helpers import create_ssl_context
import common.kafka_util as constants

class AIOConsumer():

    def __init__(self, unique_client_id, unique_group_id, log, **kwargs):
        """Each Consumer MUST have a unique ID.
        Multiple Consumers to consume the same topic MUST belong to the same group
        """
        self.consumed_msg_count = 0
        self.client_id = unique_client_id
        self.group_id = unique_group_id
        self.log = log
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
                bootstrap_servers=constants.MSK_BOOTSTRAP_SERVERS,
                client_id=unique_client_id,
                group_id=unique_group_id,
                auto_offset_reset=offset_reset,
                enable_auto_commit=False,
                max_poll_records=constants.NUMBER_OF_MSG_HANDLERS,
                security_protocol=protocol,
                ssl_context=context,
                max_poll_interval_ms=constants.MAX_POLL_INTERVAL_MS,
                session_timeout_ms=constants.SESSION_TIMEOUT_MS,
                heartbeat_interval_ms=constants.HEARTBEAT_INTERVAL_MS
            )
        else:
            self.consumer = AIOKafkaConsumer(
                bootstrap_servers=constants.MSK_BOOTSTRAP_SERVERS,
                client_id=unique_client_id,
                group_id=unique_group_id,
                auto_offset_reset=offset_reset,
                enable_auto_commit=False,
                max_poll_records=constants.NUMBER_OF_MSG_HANDLERS
              )

    async def consume_msg(self, topic, handler):
        """Start consuming kafka message
        Args:
            topic: the topic to consume messages.
            handler: Function to process a message. It must be synchronous; i.e.,
            blocking execution.
        """
        # Need to check if, what partition configuration here
        self.consumer.subscribe([topic])
        self.log.info("[S] %s/%s starts consuming from topic: %s", self.group_id, self.client_id, topic)
        partitions = self.consumer.partitions_for_topic(topic)
        self.log.info("[S] partitions_for_topic %s", partitions)

        await self.consumer.start()

        # Now, this consumer picks up message at the right position
        async for message in self.consumer:
            # message is an instance of ConsumerRecord(topic='test', partition=0, offset=50,
            # timestamp=1619202704246, timestamp_type=0, serialized_header_size=-1,
            # headers=[], checksum=None, serialized_key_size=13, serialized_value_size=44,
            # key=b'tB_1619202704',
            # value=b'{"msg": {"id": 46}, "body": "tB_1619202704"}')
            try:
                await handler(message)
                await self.consumer.commit()# does not work with zookeeper
                self.log.info("[S] Commit partition/offset %s/%s", message.partition, message.offset)
                self.consumed_msg_count += 1
            except Exception as err:
                self.log.error("[S] %s", err)
                self.log.error("[S] %s", traceback.format_exc())
        self.log.error("[S] consume_msg from topic %s terminated", topic)

    async def consume_batch(self, topic, handler):
        """Start consuming kafka message
        Args:
            topic: the topic to consume messages.
            handler: Function to process a message. It must be synchronous; i.e.,
            blocking execution.
        """
        # Need to check if, what partition configuration here
        self.consumer.subscribe([topic])
        self.log.info("[S] %s/%s starts consuming from topic: %s", self.group_id, self.client_id, topic)
        # self.log.info("[S] bootstrap_connected %s", self.consumer.bootstrap_connected())
        partitions = self.consumer.partitions_for_topic(topic)
        self.log.info("[S] partitions_for_topic %s", partitions)

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
                        self.log.info("[S] %s/%s consumed (partition %s offset %s) messages length: %s", self.group_id,
                                      self.client_id, tp, messages[-1].offset, len(messages))
                except Exception as err:
                    self.log.error("[S] %s", err)
                    self.log.error("[S] %s", traceback.format_exc())
