
""" This module is responsible for creating and managing boto3 sessions """

import contextlib
import os
import aioboto3
import botocore
from billing_consumer_new.helpers import app_config

class Singleton:
    def __init__(self, decorated):
        self._decorated = decorated

    def instance(self):
        try:
            return self._instance
        except AttributeError:
            self._instance = self._decorated()
            return self._instance

    def __call__(self):
        raise TypeError('Singletons must be accessed through `instance()`.')

    def __instancecheck__(self, inst):
        return isinstance(inst, self._decorated)

@Singleton
class AIOBoto3Session:
    def __init__(self) -> None:
        self.session = aioboto3.Session(region_name=app_config.DEFAULT_REGION)
        self.context_stack_s3_client_closer = contextlib.AsyncExitStack()
        self.context_stack_ddb_client_closer = contextlib.AsyncExitStack()

    async def start(self) -> None:
        self.aio_s3_client= await self.context_stack_s3_client_closer.enter_async_context(self.session.client('s3',
            config=botocore.client.Config(
                max_pool_connections=10
            )))

    async def stop(self) -> None:
        if self.context_stack_s3_client_closer:
            await self.context_stack_s3_client_closer.aclose()

        if self.context_stack_ddb_client_closer:
            await self.context_stack_ddb_client_closer.aclose()

    def get_s3_client(self):
        return self.aio_s3_client

