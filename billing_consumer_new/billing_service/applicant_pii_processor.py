
""" This module contains the code to process the applicant pii """

import copy
from billing_consumer_new.helpers.app_logger import custom_logger as logger
from ascendops_commonlib.models.billing_message import ApplicantPII


async def process_applicant_pii(applicant_pii: ApplicantPII, transaction_id: str):
    processed_applicant_pii = {}
    try:
        processed_applicant_pii["ssn"] = await add_padding_spaces(getattr(applicant_pii, "ssn", ""), 9, transaction_id)
        processed_applicant_pii["year_of_birth"] = await add_padding_spaces(await get_yob(getattr(applicant_pii, "dob", "")), 4, transaction_id)
        processed_applicant_pii["consumer_name"] = await create_consumer_name(applicant_pii, transaction_id)
        processed_applicant_pii["current_address"] = await create_address(getattr(applicant_pii, "inquiry_address", ""), transaction_id)
        applicant_previous_addresses = getattr(applicant_pii, "previous_address", [""])
        previous_addresses = copy.deepcopy(applicant_previous_addresses)
        if not previous_addresses:
            previous_addresses = ["",""]
        elif len(previous_addresses) == 1:
            previous_addresses.append("")
        processed_applicant_pii["1st_previous_address"] = await create_address(previous_addresses[0], transaction_id)
        processed_applicant_pii["2nd_previous_address"] = await create_address(previous_addresses[1], transaction_id)
    except Exception as xcp:
        logger.log_message(
            message=f"Error in processing applicant PII: {str(xcp)}",
            transaction_id=transaction_id,
            level="ERROR"
        )
    return processed_applicant_pii


async def get_yob(dob: str):
    """ return year of birth or empty """
    if dob and len(dob)>3:
        return dob[-4:]
    else:
        return ""


async def get_generation_code(generation_code: str):
    """
    Generation Code           1
            J= Junior
            S = Senior
            2 = 2nd
            3 = 3rd, etc.

    return Generation Code if present
    """
    gen_code = ""
    if generation_code:
        gen_code = generation_code[0].upper()
    return gen_code


async def create_consumer_name(applicant_pii: ApplicantPII, transaction_id: str):
    """
    Consumer Name                129
        Last Name                 32
        Second Last Name          32
        First Name                32
        Middle Name               32
        Generation Code           1

            J= Junior
            S = Senior
            2 = 2nd
            3 = 3rd, etc.
    """
    consumer_name = ""
    try:
        applicant_name_details = getattr(applicant_pii, "name", "")
        last_name =  await add_padding_spaces(getattr(applicant_name_details, "last_name", ""), 32, transaction_id)
        second_last_name = await add_padding_spaces(getattr(applicant_name_details, "second_last_name", ""), 32, transaction_id)
        first_name = await add_padding_spaces(getattr(applicant_name_details, "first_name", ""), 32, transaction_id)
        middle_name = await add_padding_spaces(getattr(applicant_name_details, "middle_name", ""), 32, transaction_id)
        generation_code = await add_padding_spaces(await get_generation_code(getattr(applicant_name_details, "generation_code", "")), 1, transaction_id)
        
        consumer_name = last_name + second_last_name + first_name + middle_name + generation_code

    except Exception as xcp:
        logger.log_message(
            message=f"Error in creating consumer name: {str(xcp)}",
            transaction_id=transaction_id,
            level="ERROR"
        )
    return consumer_name


def get_street_number_and_name(street_address: str, transaction_id: str):
    """
        if street address is present, first will be street number and rest is street name
    """
    st_number = ""
    st_name = ""
    try:
        if street_address is not None:
            street_address = str(street_address).strip().split()
        if street_address:
            st_number = street_address.pop(0)
            if not st_number.isdigit():
                street_address.insert(0, st_number)
                st_number = ""
            st_name = " ".join(street_address)

    except Exception as xcp:
        logger.log_message(
            message=f"Error in getting the street number and name: {str(xcp)}",
            transaction_id=transaction_id,
            level="ERROR"
        )
    return st_number, st_name


async def create_address(address: str, transaction_id: str):
    """
    SAME FORMAT FOR CURRENT ADDRESS, 1ST PREVIOUS ADDRESS AND 2ND PREVIOUS ADDRESS
        field 	            length
    Address	             97
        Street Number	     10
        Street Name	         32
        Street Suffix	     4
        City Name	         32
        State Code	         2
        Unit ID	             8
        Zipcode	             9

    currently we have street_address, city, state_code and zip_code.
    from street_address we are getting street_number and street_name.
    so street_suffix and unit_id are empty
    """
    formatted_address = ""
    try:
        street_address = ""
        line1 = getattr(address, "line1", "")
        line2 = getattr(address, "line2", "")
        if line1:
            street_address+=line1
        if line2:
            street_address+=line2
        st_number,st_name = get_street_number_and_name(street_address, transaction_id)
        street_number = await add_padding_spaces(st_number, 10, transaction_id)
        street_name = await add_padding_spaces(st_name, 32, transaction_id)
        street_suffix = await add_padding_spaces(getattr(address, "street_suffix", ""), 4, transaction_id)
        city_name = await add_padding_spaces(getattr(address, "city", ""), 32, transaction_id)
        state_code = await add_padding_spaces(getattr(address, "state", ""), 2, transaction_id)
        unit_id = await add_padding_spaces(getattr(address, "unit_id", ""), 8, transaction_id)
        zip_code = await add_padding_spaces(getattr(address, "zip_code", ""), 9, transaction_id)
        formatted_address = street_number + street_name + street_suffix + city_name + state_code + unit_id + zip_code

    except Exception as xcp:
        logger.log_message(
            message=f"Error in creating the address: {str(xcp)}",
            transaction_id=transaction_id,
            level="ERROR"
        )
    return formatted_address


async def add_padding_spaces(data_string: str, required_length: int, transaction_id: str):
    try:
        if data_string is None:
            data_string = ""
        data_string = str(data_string)
        if len(data_string) <= required_length:
            data_string += " " * (required_length - len(data_string))
        else:
            data_string = data_string[:required_length]
        
    except Exception as xcp:
        logger.log_message(
            message=f"Error in adding the padding spaces: {str(xcp)}",
            transaction_id=transaction_id,
            level="ERROR"
        )
    return str(data_string) if data_string else ""        
