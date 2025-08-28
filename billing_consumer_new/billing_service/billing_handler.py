
""" This module contains the billing handler from which the processing of the billing messages starts """

import json
from pydantic import ValidationError
from billing_consumer_new.helpers import app_config
from billing_consumer_new.helpers.app_logger import custom_logger as logger
from billing_consumer_new.helpers.sql_util import aio_mysql
from billing_consumer_new.helpers.crypto_util import ContentHelper
from ascendops_commonlib.models.billing_message import BillingMessage
from billing_consumer_new.billing_service import applicant_pii_processor, billing_message_processor


async def billing_handler(messages, crypto_util: ContentHelper, mysql: aio_mysql):
    allout_billing_records = []
    dashboard_billing_records = []
    transactions = []
    try:
        for each in messages:
            # Step 1: Do the schema validation
            message_key = each.key
            try:
                billing_message = json.loads(each.value.decode("utf-8"))
                billing_message: BillingMessage  = BillingMessage.model_validate(billing_message)
            except ValidationError as xcp:
                logger.log_message(
                    message=f"Schema Validation Error: {str(xcp)}",
                    transaction_id=message_key,
                    level="WARNING"
                )
                continue
            
            # Step 2: Process the consumer_pii
            applicant_pii: dict = await applicant_pii_processor.process_applicant_pii(billing_message.applicant_pii, billing_message.transaction_id)

            # Step 3: Create RDS billing records based on the billing data        
            billing_record, product_code_records = await billing_message_processor.process_billing_message(billing_message, applicant_pii, crypto_util)

            if billing_record and product_code_records:
                # Step 4: Append to the ops billing records
                allout_billing_records.append(billing_record)
                dashboard_billing_records.extend(product_code_records)
                transactions.append(billing_message.transaction_id)
            else:
                # Log the transaction ID
                logger.log_message(
                    message=f"Failure in the creation of billing records for transaction: {billing_message.transaction_id}",
                    transaction_id=message_key,
                    level="INFO"
                )
        
        if allout_billing_records and dashboard_billing_records:
            # Write all the message to RDS
            await mysql.bulk_insert_data(app_config.ALLOUT_BILLING_TABLE_NAME, app_config.ALLOUT_BILLING_TABLE_COLUMNS, allout_billing_records, 
                                         app_config.PRODUCT_CODES_BILLING_TABLE_NAME, app_config.PRODUCT_CODES_BILLING_TABLE_COLUMNS, dashboard_billing_records)
            logger.log_message(
                message=f"Transactions successfully processed: {transactions}",
                level="INFO"
            )
    except Exception as xcp:
        logger.log_message(
            message=f"Error in the main billing handler: {str(xcp)}",
            level="ERROR"
        )
    




"""
import asyncio

if __name__ == "__main__":    
    # logger = CustomLogger("billing-consumer")
    # mysql = aio_mysql(logger.logger)
    # mysql.connect(size=4)
    # crypto_util = ContentHelper(app_config.CRYPTO_LJAR, app_config.CRYPTO_ENV, 
    #                             app_config.CRYPTO_ENV_PREFIX, app_config.CRYPTO_AWS_PROFILE, 
    #                             instances = app_config.CRYPTO_INSTANCES)
    asyncio.run(billing_handler(logger=None, crypto_util=None, messages=None, mysql=None))

        messages = [
            {
                "transaction_id": "10232024095207EPUJQINUP",
                "product_codes": [
                    {
                        "productCode": "0AGSVC1",
                        "index": "999"
                    },
                    {
                        "productCode": "PPC0001",
                        "index": "10"
                    },
                    {
                        "productCode": "0040BX1",
                        "index": "999"
                    },
                    {
                        "productCode": "0040FR1",
                        "index": "999"
                    },
                    {
                        "productCode": "1234567",
                        "index": "999"
                    },
                    {
                        "productCode": "2345678",
                        "index": "999"
                    },
                    {
                        "productCode": "3456789",
                        "index": "999"
                    },
                    {
                        "productCode": "4567890",
                        "index": "999"
                    },
                    {
                        "productCode": "ABCDEFG",
                        "index": "999"
                    },
                    {
                        "productCode": "BCDEFGH",
                        "index": "999"
                    },
                    {
                        "productCode": "CDEFGHI",
                        "index": "999"
                    }
                ],
                "solution_id": "AOOMFDAT",
                "subcode": "2344867",
                "client_id": "",
                "inquiry_date": "10232024",
                "inquiry_time": "095207",
                "arf_version": "07",
                "applicant_pii": {
                    "name": {
                        "last_name": "ANASTASIO",
                        "first_name": "JESSE",
                        "middle_name": "",
                        "generation_code": None,
                        "prefix": None
                    },
                    "dob": "",
                    "ssn": "666131472",
                    "ein": None,
                    "tin": None,
                    "driverslicense": None,
                    "secondary_id": None,
                    "phone": None,
                    "email_id": None,
                    "employment": None,
                    "current_address": {
                        "line1": "2752 SOLOMONS ISLAND RD",
                        "line2": None,
                        "city": "EDGEWATER",
                        "state": "MD",
                        "zip_code": "210371211",
                        "country": ""
                    },
                    "previous_address": None,
                    "inquiry_address": {
                        "line1": "2752 SOLOMONS ISLAND RD",
                        "line2": None,
                        "city": "EDGEWATER",
                        "state": "MD",
                        "zip_code": "210371211",
                        "country": ""
                    }
                }
            }
        ]
"""