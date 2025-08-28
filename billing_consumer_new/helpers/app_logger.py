
""" Custom Logging Module """

import logging
import json
import datetime

import asyncio
import logging.handlers
try:
    # Python 3.7 and newer, fast reentrant implementation
    # witohut task tracking (not needed for that when logging)
    from queue import SimpleQueue as Queue
except ImportError:
    from queue import Queue
from typing import List


class LocalQueueHandler(logging.handlers.QueueHandler):
    def emit(self, record: logging.LogRecord) -> None:
        # Removed the call to self.prepare(), handle task cancellation
        try:
            self.enqueue(record)
        except asyncio.CancelledError:
            raise
        except Exception:
            self.handleError(record)


def setup_logging_queue() -> None:
    """Move log handlers to a separate thread.

    Replace handlers on the root logger with a LocalQueueHandler,
    and start a logging.QueueListener holding the original
    handlers.

    """
    queue = Queue()
    root = logging.getLogger()

    handlers: List[logging.Handler] = []

    handler = LocalQueueHandler(queue)
    root.addHandler(handler)
    for h in root.handlers[:]:
        if h is not handler:
            root.removeHandler(h)
            handlers.append(h)

    listener = logging.handlers.QueueListener(
        queue, *handlers, respect_handler_level=True
    )
    listener.start()


""" Writing a Custom Logger """
class CustomLogger():
    """ Custom Logger class """

    def __init__(self, name: str, level = 10) -> None:
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        
        self.transaction_id = ""

    def log_json(self, content: dict, level: str = "INFO"):
        """
        Logs a dictionary as a JSON string
        Args:
            content (dict): Dictionary to log.
            level (str): Logging level. Default is set to "info.
        """
        try:
            if "exception" not in content:
                content.update({"exception": None})
            if "traceback" not in content:
                content.update({"traceback": None})

            message = {
                "timestamp": str(datetime.datetime.now()),
                "event_type": "BILLING"
            }
            message.update(content)
            self.write_log_item(json.dumps(message), level)
            
        except Exception as xcp:
            log_msg = f" ------- Failed to write log: {str(xcp)}"
            self.write_log_item(log_msg, level="ERROR")


    def log_message(self, message: str, transaction_id: str = None, level: str = "INFO"):
        """
        Logs a message string

        Args:
            message (str): message to log.
            level (str): Logging level. Default is set to "info.
        """
        log_msg = f"{transaction_id} ------- {message}"
        self.write_log_item(log_msg, level)


    def write_log_item(self, message: str, level: str = "INFO"):
        """ writes a log message """
        if level == "INFO":
            self.logger.info(message)
        elif level == "WARNING":
            self.logger.warning(message)
        elif level == "ERROR":
            self.logger.error(message)
        elif level == "DEBUG":
            self.logger.debug(message)
        else:
            self.logger.info(message)


# Logging Config
custom_logger = CustomLogger("billing_consumer")