import contextlib
import os
import aioboto3
import botocore

DEFAULT_REGION = os.getenv("DEFAULT_REGION", "us-east-1")
DB_URL = f"https://dynamodb.{DEFAULT_REGION}.amazonaws.com"

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
        self.session = aioboto3.Session()
        self.context_stack_s3_client_closer = contextlib.AsyncExitStack()
        self.context_stack_ddb_client_closer = contextlib.AsyncExitStack()

    async def start(self) -> None:
        self.aio_s3_client= await self.context_stack_s3_client_closer.enter_async_context(self.session.client('s3',
            config=botocore.client.Config(
                max_pool_connections=10
            )))
        self.aio_ddb_client= await self.context_stack_ddb_client_closer.enter_async_context(self.session.resource('dynamodb',
            endpoint_url=DB_URL,
            config=botocore.client.Config(
                max_pool_connections=10,
                retries={"max_attempts": 3},
                read_timeout=60
            )))

    async def stop(self) -> None:
        if self.context_stack_s3_client_closer:
            await self.context_stack_s3_client_closer.aclose()

        if self.context_stack_ddb_client_closer:
            await self.context_stack_ddb_client_closer.aclose()

    def get_s3_client(self):
        return self.aio_s3_client

    def get_ddb_client(self):
        return self.aio_ddb_client
