""" custom logging module """

import logging
import json
import datetime
from ascendops_commonlib.ops_utils.ops_config import IS_AWS


def get_app_logger():
    return logging.getLogger("bureaucomposertest")


class CustomLogger():
    """ Custom Logger class """

    def __init__(self, name: str, level = 20) -> None:
        self.logger = logging.getLogger(name)
        self.transaction_id = ""
        # self.write_log_item(
        #     message=f"ServingRequest: {self.transaction_id}"
        # )


    def set_transaction_id(self, transaction_id: str):
        """
        Sets the transaction ID.

        Args:
            transaction_id (str): The transaction ID to be set.
        """
        self.transaction_id = transaction_id


    def log_json(self, event_type: str, content: dict, level: str = "INFO"):
        """
        Logs a dictionary as a JSON string

        Args:
            event_type (str): Event type
            content (dict): Dictionary to log.
            level (str): Logging level. Default is set to "info.
        """
        try:
            if IS_AWS is False:
                for k,v in content.items():
                    if k in ["exception", "traceback"] and v is not None and event_type != "AUDIT_LOG":
                        print("Breakpoint here to debug")

            if "exception" not in content:
                content.update({"exception": None})
            if "traceback" not in content:
                content.update({"traceback": None})

            message = {
                # "transaction_id": self.transaction_id,
                "timestamp": str(datetime.datetime.now()),
                "event_type": event_type
            }
            message.update(content)

            self.write_log_item(json.dumps(message), level)
        except Exception as xcp:
            # log_msg = f"{self.transaction_id} ------- Failed to write log: {str(xcp)}"
            log_msg = f" ------- Failed to write log: {str(xcp)}"
            self.write_log_item(log_msg, level="ERROR")


    def log_message(self, message: str, transaction_id: str | None = None, level: str = "INFO"):
        """
        Logs a message string

        Args:
            message (str): message to log.
            level (str): Logging level. Default is set to "info.
        """

        # log_msg = f"{self.transaction_id} ------- {message}"
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
