
""" This module contains the code to process the billing message """

import json
import base64
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from billing_consumer_new.helpers import app_config
from billing_consumer_new.helpers.app_logger import custom_logger as logger
from billing_consumer_new.helpers.crypto_util import ContentHelper
from ascendops_commonlib.models.billing_message import BillingMessage


async def process_billing_message(billing_message: BillingMessage, applicant_pii: dict, crypto_util: ContentHelper):  
    allout_billing_record = ""
    dashboard_billing_records = []
    try:
        inquiry_date_time_in_cst = convert_utc_to_cst(billing_message.transaction_id)
        i = 0
        billing_record = ["B", "1.00"]
        i += 2
        billing_record.append(billing_message.transaction_id[0:23])
        i += 1
        billing_record.append("GOINQ" + _make_padding_spaces(3))
        i += 1
        billing_record.append(_make_padding_spaces(8))
        i += 1
        billing_record.append(_make_padding_spaces(8))
        i += 1
        billing_record.append(inquiry_date_time_in_cst[0:8])
        i += 1
        billing_record.append(inquiry_date_time_in_cst[8:14] + "00")
        i += 1
        billing_record.append(app_config.OPS_SUB_SYSTEM_NAME)
        i += 1
        billing_record.append(_make_padding_spaces(70))
        product_codes_index = i
        i += 1
        billing_record.append(_make_padding_spaces(50))
        i += 1
        billing_record.append(billing_message.subcode)
        i += 1
        billing_record.append(_make_padding_spaces(4))
        i += 1
        billing_record.append(_make_padding_spaces(4))
        i += 1
        billing_record.append(billing_message.arf_version)
        i += 1
        billing_record.append(_make_padding_spaces(53))
        i += 1
        billing_record.append(applicant_pii.get("ssn"))
        i += 1
        billing_record.append(applicant_pii.get("year_of_birth"))
        i += 1
        billing_record.append(applicant_pii.get("consumer_name"))
        i += 1
        billing_record.append(applicant_pii.get("current_address"))
        i += 1
        billing_record.append(applicant_pii.get("1st_previous_address"))
        i += 1
        billing_record.append(applicant_pii.get("2nd_previous_address"))
        i += 1
        billing_record.append("0")
        continuation_index = i
        i += 1
        billing_record.append(app_config.OPS_CALLING_SUB_SYSTEM_NAME)
        i += 1
        billing_record.append(_make_padding_spaces(46))
        i += 1

        base_product_code = ""
        product_codes = []
        
        for each in billing_message.product_codes:            
            if each.index == "10":
                base_product_code = each.productCode 
                product_code_type = "base"   
            else:
                product_codes.append(each.productCode)
                product_code_type = "optional"
            dashboard_billing_records.append((billing_message.transaction_id[0:23], datetime.strptime(billing_message.transaction_id[0:14], '%m%d%Y%H%M%S'), billing_message.solution_id, billing_message.subcode, each.productCode, product_code_type, billing_message.is_silent_launch_enabled))
        
        product_codes.insert(0, base_product_code)
        
        encrypted_billing_record = await create_transaction_billing_record(billing_message, billing_record, product_codes_index, continuation_index, crypto_util, product_codes)

        if encrypted_billing_record:
            allout_billing_record = (billing_message.transaction_id[0:23], datetime.strptime(billing_message.transaction_id[0:14], '%m%d%Y%H%M%S'), 
                                            encrypted_billing_record, billing_message.is_silent_launch_enabled, billing_message.solution_id, billing_message.subcode)
        else:
            logger.log_message(
                message=f"Error in creating the billing record",
                transaction_id=billing_message.transaction_id,
                level="WARNING"
            )
                    
    except Exception as xcp:
        logger.log_message(
            message=f"Error in processing the billing message: {str(xcp)}",
            transaction_id=billing_message.transaction_id,
            level="ERROR"
        )
    return allout_billing_record, dashboard_billing_records


async def create_transaction_billing_record(billing_message: BillingMessage, billing_record: list, product_codes_index: int, continuation_index: int, crypto_util: ContentHelper, product_codes: list):
    encrypted_billing_record = ""
    try:
        billing_record_prefix = "GCRGOINQ   00                          "
        product_code_counter = 0
        record_index = 0
        record_data = {}
        # max limit is 30 products/transaction
        product_codes_count = min(len(billing_message.product_codes), 30)
        while product_code_counter < product_codes_count:
            temp_record = billing_record.copy()
            product_codes_str = "".join(product_codes[product_code_counter:product_code_counter + 10])
            padding_length = 70 - len(product_codes_str)
            temp_record[product_codes_index] = product_codes_str + " " * padding_length

            continuation_flag = "0"
            if ((product_code_counter % 10) == 0) and ((product_codes_count - product_code_counter) > 10):
                continuation_flag = "1"

            temp_record[continuation_index] = continuation_flag

            raw_billing_record = billing_record_prefix + "".join(temp_record)

            if len(raw_billing_record) != app_config.BILLING_RECORD_LENGTH:  # 39+746=785
                raise Exception("Billing record string length ({}) != expected length ({})".format(
                    len(raw_billing_record),
                    app_config.BILLING_RECORD_LENGTH))

            # index ordering is important for transaction with more than 10 products
            record_data[record_index] = raw_billing_record
            record_index += 1
            product_code_counter += 10  # iterate every 10 products 

        # Encrypting 
        cnt_java = await crypto_util.aetask(json.dumps(record_data).encode("utf-8"))
        encrypted_billing_record = "SEncr:"+base64.b64encode(bytes(cnt_java[0])).decode("utf-8")

    except Exception as xcp:
        logger.log_message(
            message=f"Error in creating the transaction billing record: {str(xcp)}",
            transaction_id=billing_message.transaction_id,
            level="ERROR"
        )
    return encrypted_billing_record


def _make_padding_spaces(count: int):
    """To fill non require fields with spaces"""
    return "".join([" " for _ in range(0, count)])


def convert_utc_to_cst(transaction_id):
    try:
        # Combine date and time
        datetime_str = transaction_id[0:14]
        utc_time = datetime.strptime(datetime_str, "%m%d%Y%H%M%S").replace(tzinfo=ZoneInfo("UTC"))
        cst_time = utc_time.astimezone(ZoneInfo("US/Central"))
        cst_datetime_str = cst_time.strftime("%m%d%Y%H%M%S")
        return cst_datetime_str
    except Exception as xcp:
        logger.log_message(
            message=f"Error in converting time from UTC to CST: {str(xcp)}",
            transaction_id=transaction_id,
            level="ERROR"
        )