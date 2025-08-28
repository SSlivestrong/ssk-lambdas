# borrowed from https://code.experian.local/projects/ASGO/repos/asgo-platform-api
import gzip
import os
import traceback
from typing import List
from aiokafka import AIOKafkaConsumer, ConsumerRecord, TopicPartition, OffsetAndMetadata
from aiokafka.helpers import create_ssl_context
from regression_test_suite.helpers import rts_config

NUMBER_OF_MSG_HANDLERS = int(os.getenv("NUMBER_OF_MSG_HANDLERS", "50"))

class VersionedMessage:
    def __init__(self, version, key, value_decompressed, headers) -> None:
        self.version = version
        self.key = key
        self.value_decompressed = value_decompressed
        self.headers = headers

class AIOConsumer():

    def __init__(self, unique_client_id, unique_group_id, log, **kwargs):
        """Each Consumer MUST have a unique ID.
        Multiple Consumers to consume the same topic MUST belong to the same group
        """
        self.consumed_msg_count = 0
        self.client_id = unique_client_id
        self.group_id = unique_group_id
        self.log = log
        self.protocol = kwargs.pop("security_protocol", "SSL")
        offset_reset = kwargs.pop("auto_offset_reset", "earliest")
        if self.protocol == "SSL":
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
                bootstrap_servers=rts_config.MSK_BOOTSTRAP_SERVERS,
                client_id=unique_client_id,
                group_id=unique_group_id,
                auto_offset_reset=offset_reset,
                enable_auto_commit=False,
                max_poll_records=NUMBER_OF_MSG_HANDLERS,
                security_protocol=self.protocol,
                ssl_context=context
            )
        else:
            #for dev/local testing
            self.consumer = AIOKafkaConsumer(
                bootstrap_servers=rts_config.MSK_BOOTSTRAP_SERVERS,
                client_id=unique_client_id,
                group_id=unique_group_id,
                max_poll_records=1,
                auto_offset_reset=offset_reset,
                enable_auto_commit=True
            )

    async def consume_batch(self, topic, handler):
        """Start consuming kafka message
        Args:
            topic: the topic to consume messages.
            handler: Function to process a message. It must be synchronous; i.e.,
            blocking execution.
        """
        # Need to check if, what partition configuration here
        self.consumer.subscribe([topic])

        self.log.info(self.protocol)
        if self.protocol == "local":
            await self.consume_dev(handler)
            return

        self.log.info("[S] %s/%s starts consuming from topic: %s", self.group_id, self.client_id, topic)
        # self.log.info("[S] bootstrap_connected %s", self.consumer.bootstrap_connected())
        partitions = self.consumer.partitions_for_topic(topic)
        self.log.info("[S] partitions_for_topic %s", partitions)

        await self.consumer.start()
        poll_for_ms = int(os.getenv("KAFKA_POLL_FOR_MS", "10000"))
        while True:
            # Now, this consumer picks up message at the right position
            result = await self.consumer.getmany(timeout_ms=poll_for_ms)
            for tp, messages in result.items():
                # message is an instance of ConsumerRecord(topic='test', partition=0, offset=50,
                # timestamp=1619202704246, timestamp_type=0, serialized_header_size=-1,
                # headers=[], checksum=None, serialized_key_size=13, serialized_value_size=44,
                # key=b'tB_1619202704',
                # value=b'{"msg": {"id": 46}, "body": "tB_1619202704"}')
                try:
                    if messages:
                        await self.wrap_handler(messages, handler)
                        await self.consumer.commit({tp: messages[-1].offset + 1})
                        self.log.info("[S] %s/%s consumed (partition %s offset %s) messages length: %s", self.group_id,
                                      self.client_id, tp, messages[-1].offset, len(messages))
                except Exception as err:
                    self.log.error("[S] %s", err)
                    self.log.error("[S] %s", traceback.format_exc())
    
    async def consume_dev(self, handler):
        await self.consumer.start()
        while True:
            try:
                async for msg in self.consumer:
                    self.log.info("consumed: %s %s %s %s %s", msg.topic, msg.partition, msg.offset, 
                        msg.key, msg.timestamp)
                    await self.wrap_handler([msg], handler)
            except Exception as err:
                    self.log.error("[S] %s", err)
                    self.log.error("[S] %s", traceback.format_exc())
            finally:
                pass

    async def wrap_handler(self, msgs: List[ConsumerRecord], handler):
        versioned_msgs = []
        other_msgs = []
        for msg in msgs:
            list_of_tuples = msg.headers
            if len(list_of_tuples) > 0:
                version = list_of_tuples[0][0]
                value_decompressed = gzip.decompress(msg.value)
                versioned_msgs.append(VersionedMessage(version, msg.key, value_decompressed, list_of_tuples))
            else:
                other_msgs.append(msg)
        
        if other_msgs:
            await handler(other_msgs)

        if versioned_msgs:
            await handler(versioned_msgs)
