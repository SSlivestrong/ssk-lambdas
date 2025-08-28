from aiohttp import ClientSession, ClientTimeout
from helpers.app_logger import CustomLogger
from ascendops_commonlib.ops_utils import ops_util
import numpy as np
import asyncio
import ssl
import os

class AscendOpsRequestHandler():
    def __init__(self, ascendops_api: str, logger: CustomLogger, request_timeout: int = 10) -> None:
        self.ascendops_api = ascendops_api
        self.logger = logger
        self.TIME_OUT = ClientTimeout(total=request_timeout)
        self.ssl_context = ssl.create_default_context(cafile=os.path.join(os.getenv("APP_DIR", "./"), "certs/cacerts.pem"))
    
    def get_latency_stats(self, response_latencies, pass_track=None):
        if len(response_latencies) > 0:
            try:
                response_latencies = np.asarray(response_latencies)
                pass_track = np.asarray([elm["pass"] for elm in pass_track]) if pass_track \
                    else np.full((response_latencies.shape[0],), True)
                response_latencies = response_latencies[pass_track]
                if len(response_latencies) > 0:
                    return {"mean": np.mean(response_latencies), "standard_deviation": np.std(response_latencies)}
            except:
                self.logger.logger.warning(f'>>>> RTS >>>>: {self.__class__.__name__} Error Calculating Latency Statistics')
        return None

    async def getResponse(self, inquiry_payload: str, session: ClientSession, mode: dict) -> dict:
        try:
            headers = {
                'Content-Type': 'application/json',
                'User-Agent': 'Regression Test Service',
                **mode
            }
            service_call_start_time = ops_util.get_epoch_millis()
            async with session.post(self.ascendops_api, json=inquiry_payload, headers=headers, ssl=self.ssl_context ,\
                timeout=self.TIME_OUT) as response:
                response_json = await response.json()
                service_call_end_time = ops_util.get_epoch_millis()
                return response_json, service_call_end_time - service_call_start_time
        except asyncio.exceptions.TimeoutError:
            self.logger.logger.warning(f'>>>> RTS >>>>: {self.__class__.__name__} Request Timeout')
            return {}, self.TIME_OUT.total

    async def getResponses(self, inquiry_payloads: list, session: ClientSession, modes: list) -> dict:
        tasks = []
        for inquiry_payload, mode in zip(inquiry_payloads, modes):
            tasks.append(self.getResponse(inquiry_payload, session, mode))
        results = await asyncio.gather(*tasks)
        return results
    
    async def getResponsesBatched(self, inquiry_payloads: list, batch_size: int, modes: list) -> dict:
        ascendops_responses = []
        response_latencies = []
        g_idx = 0
        async with ClientSession() as session:            
            for i in range(0, len(inquiry_payloads), batch_size):
                inquiry_batch = inquiry_payloads[i:i+batch_size]
                mode_batch = modes[i:i+batch_size]
                results = await self.getResponses(inquiry_batch, session, mode_batch)
                for result, response_latency in results:
                    ascendops_responses.append(result)
                    response_latencies.append(response_latency)
                    g_idx += 1
                if i%(batch_size*10)==0:
                    self.logger.logger.warning(f'>>>> RTS >>>>: {self.__class__.__name__} Progress: {round(i*100/len(inquiry_payloads))}%')
        return ascendops_responses, response_latencies