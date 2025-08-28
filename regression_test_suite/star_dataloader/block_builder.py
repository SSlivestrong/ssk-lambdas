from .consumer_pii import *

#################################HELPER FUNCTIONS################################################

def length_check(pii_dict: dict, keys: list) -> bool:
    for key in keys:
        if len(pii_dict[key]) == 0:
            return False
    return True

#################################################################################################

'''
Naming convention: {block}_builder
'''

def required_builder(pii_dict: dict, consumer: Consumer, **args) -> str:
    if length_check(pii_dict, ["last_name", "first_name", "ssn"]):
        required_block = f'{args["client_metadata"]} {pii_dict["last_name"]}, {pii_dict["first_name"]} {pii_dict["middle_name"]} {pii_dict["gen"]} {pii_dict["ssn"]}'
        consumer.primary_applicant.name = Name(last_name=pii_dict["last_name"],
                                                first_name=pii_dict["first_name"],
                                                middle_name=pii_dict["middle_name"],
                                                generation_code=pii_dict["gen"])
        consumer.primary_applicant.ssn = pii_dict["ssn"]
    else:
        raise Exception("Failed to create required block")
    return required_block

def current_address_builder_1(pii_dict: dict, consumer: Consumer, **args) -> str:
    if length_check(pii_dict, ["address", "city", "state", "zip_code"]):
        apt_code = f'{pii_dict["unit"]} {pii_dict["unit_number"]}'
        current_address_block = f'CA-{pii_dict["address"]} {apt_code}/{pii_dict["city"]} {pii_dict["state"]} {pii_dict["zip_code"]}'
        consumer.primary_applicant.current_address = Address(line1=f'{pii_dict["address"]} {apt_code}',
                                                            city=pii_dict["city"],
                                                            state=pii_dict["state"],
                                                            zip_code=pii_dict["zip_code"])
    else:
        # print(f'WARN: Failed to create CA address block')
        # CA block cannot be empty in the inquiry, using a placeholder here
        current_address_block = "CA-475 Anton Blvd/Costa Mesa CA 92626"
    return current_address_block

def current_address_builder_2(pii_dict: dict, consumer: Consumer, **args) -> str:
    if length_check(pii_dict, ['street_number', 'street_name', 'street_suffix', 'city', 'state', 'zip_code']):
        apt_code = f'{pii_dict["unit"]} {pii_dict["unit_number"]}'
        current_address_block = f'CA-{pii_dict["street_number"]} {pii_dict["street_name"]} {pii_dict["street_suffix"]} {apt_code}/{pii_dict["city"]} {pii_dict["state"]} {pii_dict["zip_code"]}'
        consumer.primary_applicant.current_address = Address(line1=f'{pii_dict["street_number"]} {pii_dict["street_name"]} {pii_dict["street_suffix"]} {apt_code}',
                                                            city=pii_dict["city"],
                                                            state=pii_dict["state"],
                                                            zip_code=pii_dict["zip_code"])
    else:
        # print(f'WARN: Failed to create CA address block')
        # CA block cannot be empty in the inquiry, using a placeholder here
        current_address_block = "CA-475 Anton Blvd/Costa Mesa CA 92626"
    return current_address_block

def current_address_builder_5(pii_dict: dict, consumer: Consumer, **args) -> str:
    if length_check(pii_dict, ['street_number', 'city', 'state', 'zip_code']):
        apt_code = f'{pii_dict["unit"]} {pii_dict["unit_number"]}'
        current_address_block = f'CA-{pii_dict["street_number"]} {pii_dict["street_name"]} {pii_dict["street_suffix"]} {apt_code}/{pii_dict["city"]} {pii_dict["state"]} {pii_dict["zip_code"]}'
        consumer.primary_applicant.current_address = Address(line1=f'{pii_dict["street_number"]} {pii_dict["street_name"]} {pii_dict["street_suffix"]} {apt_code}',
                                                            city=pii_dict["city"],
                                                            state=pii_dict["state"],
                                                            zip_code=pii_dict["zip_code"])
    else:
        # print(f'WARN: Failed to create CA address block')
        # CA block cannot be empty in the inquiry, using a placeholder here
        current_address_block = "CA-475 Anton Blvd/Costa Mesa CA 92626"
    return current_address_block

def current_address_builder_3(pii_dict: dict, consumer: Consumer, **args) -> str:
    if length_check(pii_dict, ['house_number', 'street_name', 'street_suffix', 'city', 'state', 'zip_code']):
        apt_code = f'{pii_dict["unit"]} {pii_dict["unit_number"]}'
        current_address_block = f'CA-{pii_dict["house_number"]} {pii_dict["street_name"]} {pii_dict["street_suffix"]} {apt_code}/{pii_dict["city"]} {pii_dict["state"]} {pii_dict["zip_code"]}'
        consumer.primary_applicant.current_address = Address(line1=f'{pii_dict["house_number"]} {pii_dict["street_name"]} {pii_dict["street_suffix"]} {apt_code}',
                                                            city=pii_dict["city"],
                                                            state=pii_dict["state"],
                                                            zip_code=pii_dict["zip_code"])
    else:
        # print(f'WARN: Failed to create CA address block')
        # CA block cannot be empty in the inquiry, using a placeholder here
        current_address_block = "CA-475 Anton Blvd/Costa Mesa CA 92626"
    return current_address_block

def current_address_builder_4(pii_dict: dict, consumer: Consumer, **args) -> str:
    if length_check(pii_dict, ['house_number', 'city', 'state', 'zip_code']):
        apt_code = f'{pii_dict["unit"]} {pii_dict["unit_number"]}'
        current_address_block = f'CA-{pii_dict["house_number"]} {pii_dict["street_name"]} {pii_dict["street_suffix"]} {apt_code}/{pii_dict["city"]} {pii_dict["state"]} {pii_dict["zip_code"]}'
        consumer.primary_applicant.current_address = Address(line1=f'{pii_dict["house_number"]} {pii_dict["street_name"]} {pii_dict["street_suffix"]} {apt_code}',
                                                            city=pii_dict["city"],
                                                            state=pii_dict["state"],
                                                            zip_code=pii_dict["zip_code"])
    else:
        # print(f'WARN: Failed to create CA address block')
        # CA block cannot be empty in the inquiry, using a placeholder here
        current_address_block = "CA-475 Anton Blvd/Costa Mesa CA 92626"
    return current_address_block

def prev_address_builder(pii_dict: dict, consumer: Consumer, **args) -> str:
    if length_check(pii_dict, [f'prev{args["suffix"]}_house_number', 
                               f'prev{args["suffix"]}_street_name',
                               f'prev{args["suffix"]}_street_suffix', 
                               f'prev{args["suffix"]}_city',
                               f'prev{args["suffix"]}_state',
                               f'prev{args["suffix"]}_zip_code']):
        prev_house_number, prev_street_name, prev_street_suffix, \
            prev_city, prev_state, prev_zip_code = pii_dict[f'prev{args["suffix"]}_house_number'],  pii_dict[f'prev{args["suffix"]}_street_name'],\
             pii_dict[f'prev{args["suffix"]}_street_suffix'],  pii_dict[f'prev{args["suffix"]}_city'],  pii_dict[f'prev{args["suffix"]}_state'],\
              pii_dict[f'prev{args["suffix"]}_zip_code']
        prev_address_block = f'PA-{prev_house_number} {prev_street_name} {prev_street_suffix}/{prev_city} {prev_state} {prev_zip_code}'
        consumer.primary_applicant.previous_address = [] if consumer.primary_applicant.previous_address is None else consumer.primary_applicant.previous_address
        consumer.primary_applicant.previous_address.append(Address(line1=f'{prev_house_number} {prev_street_name} {prev_street_suffix}',
                                                            city=prev_city,
                                                            state=prev_state,
                                                            zip_code=prev_zip_code))
    else:
        # print(f'WARN: Failed to create PA address block')
        prev_address_block = ""
    return prev_address_block

def phone_builder(pii_dict: dict, consumer: Consumer, **args) -> str:
    if length_check(pii_dict, ["phone"]):
        phone_block = f'PH-{pii_dict["phone"]}'
        consumer.primary_applicant.phone = [Phone(number=pii_dict["phone"])]
    else:
        # print(f'WARN: Failed to create phone block')
        phone_block = ""
    return phone_block

def driver_license_builder(pii_dict: dict, consumer: Consumer, **args) -> str:
    if length_check(pii_dict, ["driver_license_number", "driver_license_state"]):
        driver_license_block = f'DL-{pii_dict["driver_license_state"]} {pii_dict["driver_license_number"]}'
        consumer.primary_applicant.driverslicense = License(number=pii_dict["driver_license_number"],
                                                            state=pii_dict["driver_license_state"])
    else:
        # print(f'WARN: Failed to create DL block')
        driver_license_block = ""
    return driver_license_block

def employment_builder(pii_dict: dict, consumer: Consumer, **args) -> str:
    if length_check(pii_dict, ["employer1"]):
        employment_block = f'E-{pii_dict["employer1"]}'
        consumer.primary_applicant.employment = Employment(employer_name=pii_dict["employer1"].split("/")[0])
    else:
        # print(f'WARN: Failed to create employment block')
        employment_block = ""
    return employment_block

def yob_builder(pii_dict: dict, consumer: Consumer, **args) -> str:
    if length_check(pii_dict, ["dob"]):
        yob_block = f'Y-{pii_dict["dob"]}'
        consumer.primary_applicant.dob = pii_dict["dob"]
    else:
        # print(f'WARN: Failed to create year of birth block')
        yob_block = ""
    return yob_block

def m_dash_builder(pii_dict: dict, consumer: Consumer, **args) -> str:
    if length_check(pii_dict, ["m_dash_keyword"]):
        m_dash_block = f'M-{pii_dict["m_dash_keyword"]}'
    else:
        # print(f'WARN: Failed to create m_dash block')
        m_dash_block = ""
    return m_dash_block

block_builder_function_map = {
        'required_builder': required_builder,
        'current_address_builder_1': current_address_builder_1,
        'current_address_builder_2': current_address_builder_2,
        'current_address_builder_3': current_address_builder_3,
        'current_address_builder_4': current_address_builder_4,
        'current_address_builder_5': current_address_builder_5,
        'prev_address_builder': prev_address_builder,
        'phone_builder': phone_builder,
        'driver_license_builder': driver_license_builder,
        'employment_builder': employment_builder,
        'yob_builder': yob_builder,
        'm_dash_builder': m_dash_builder
    }