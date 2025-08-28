""" Enum that defines the event type for logging """
from enum import Enum


class RtsEnum(str, Enum):
    """ Defines the type of event for logging """

    # for header logging on request received
    RTS_AUDITLOG_CONSUMER = "RTS_AUDITLOG_CONSUMER"
    
    # for fetching testcase from db
    REPLAY_CACHE = "REPLAY_CACHE"
    
    # for rts job manager
    RTS_JOB_MANAGER = "RTS_JOB_MANAGER"
    
    # for mock service
    RTS_MOCK_SERVICE = "RTS_MOCK_SERVICE"
    
    # for rts apis
    RTS_API = "RTS_API"