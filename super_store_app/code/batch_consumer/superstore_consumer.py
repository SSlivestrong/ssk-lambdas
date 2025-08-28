from common.kafka_util import get_kafka_params
from api.superstore_utils import SuperStore
from common.aio_utils.time_decorators import duration
from common.aio_utils.boto3_sessions import AIOBoto3Session
from common.aio_utils.async_consumer import AIOConsumer

import common.app_util as app_util
import api.app_global as app_global
import botocore


class SuperStoreConsumer:

    def __init__(self, name="superstore-app"):
        self.msk_topic = app_global.SNAPSHOT_TOPIC
        self.kafka_params = {"security_protocol": app_global.SECURITY_PROTOCOL}
        if app_global.SECURITY_PROTOCOL == "SSL":
            self.kafka_params.update(get_kafka_params())

        consumer_client_id = name + "-consumer-" + \
            app_util.get_epoch_millis_string()
        app_global.log.info("Consumer client ID: %s", consumer_client_id)
        self.msk_consumer = AIOConsumer(
            consumer_client_id,
            app_global.KAFKA_GROUP_ID,
            app_global.log,
            **self.kafka_params.copy()
        )
        self.superstore = SuperStore(
            app_global.log, AIOBoto3Session.instance().get_s3_client()
        )
        self.messages = []

    async def run(self):
        """Process a message from topic."""
        app_global.log.debug("SuperStore app is running")
        await self.msk_consumer.consume_batch(self.msk_topic,
                                              self.batch_handler)
        app_global.log.debug("SuperStore app  exits")

    @duration
    async def batch_handler(self, messages):
        try:
            await self.save_batch(messages)
        except KeyError as keyerr:
            app_global.log.error("KeyError: %s", keyerr)
        except (
                botocore.exceptions.EndpointConnectionError,
                botocore.exceptions.ClientError,
        ) as awserr:
            app_global.log.error("S3Error: %s", awserr)
            raise Exception(awserr)
        except Exception as xcpn:
            # app_global.log.error(traceback.format_exc())
            app_global.log.error("Exception: %s", xcpn)

    @duration
    async def save_batch(self, messages):
        await self.superstore.create_emr_input(messages)
        # app_global.log.info("Files are generated and uploaded")
