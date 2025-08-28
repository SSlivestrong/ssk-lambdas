import asyncio
import jpype
import jpype.imports
from jpype.types import *

from concurrent.futures import ThreadPoolExecutor
import contextlib
import time
import queue

class Singleton (type):
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]

class ContentHelper(metaclass=Singleton):
    def __init__(self, ljar, environment, prefix, awsProfile, instances):
        jpype.startJVM("-Xms64m", "-Xmx64m", classpath=[ljar])
        self.krypt = jpype.JClass("com.experian.ops.crypto.Crypto")
        self.krypt.extractNaeConfigFiles(environment, prefix, False)
        k = self.krypt.initAndGet(environment, prefix, awsProfile)

        self.executor = ThreadPoolExecutor(max_workers=instances)

        self.cifaceq = queue.Queue()
        for _ in range(0, instances):
            self.cifaceq.put([self.krypt.getCipher(k, True), self.krypt.getCipher(k, False)])

    def close(self):
        jpype.shutdownJVM()

    @contextlib.contextmanager
    def ciface(self, idx):
       obj = self.cifaceq.get()
       try:
           yield obj[idx]
       finally:
           self.cifaceq.put(obj)

    def decrypt(self, encrypted):
       with self.ciface(1) as obj:
          st = time.time()
          ret = self.krypt.decrypt(obj, encrypted)
          return (ret, time.time() - st)

    def encrypt(self, inp):
       with self.ciface(0) as obj:
          st = time.time()
          ret = self.krypt.encrypt(obj, inp)
          return (ret, time.time() - st)

    def etask(self, inp):
       return self.executor.submit(self.encrypt, inp)

    def dtask(self, encrypted):
       return self.executor.submit(self.decrypt, encrypted)

    async def aetask(self, inp):
       return await asyncio.wrap_future(self.executor.submit(self.encrypt, inp))

    async def adtask(self, encrypted):
       return await asyncio.wrap_future(self.executor.submit(self.decrypt, encrypted))