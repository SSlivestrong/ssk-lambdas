import re

'''
Naming convention: {key}_ve
'''

def driver_license_number_ve(driver_license_number: str) -> str:
    return re.match(r'^(?=.*[0-9])[A-Z0-9]*$', driver_license_number).string

def state_ve(state: str) -> str:
    return re.match(r'^[A-Z]{2}$', state).string

def ssn_ve(ssn: str) -> str:
    if re.match(r'^\d+\.\d+$', ssn):
         return ssn[:-2]
    return re.match(r'^\d+$', ssn).string

def phone_ve(phone: str) -> str:
    if re.match(r'^\d+\.\d+$', phone):
         return phone[:-2]
    phone = re.sub('\.', '', phone)
    return re.match(r'^\d+$', phone).string

def dob_ve(dob: str) -> str:
    if re.match(r'^\d+\.\d+$', dob):
         dob = dob[:-2]
    if re.match(r'^[0-9]{4}$', dob):
        return dob
    if re.match(r'^[0-9]{8}$', dob):
        return dob[-4:]
    # from 19th century
    return re.search(r'(18\d{2}|19\d{2}|20\d{2})$', dob).group(0)

def dob_ve_2(dob: str) -> str:
    if re.match(r'^\d+\.\d+$', dob):
         dob = dob[:-2]
    return dob

def zip_ve(zip: str) -> str:
    if re.match(r'^\d+\.\d+$', zip):
         return zip[:-2]
    return re.match(r'^\d+$', zip).string

def default_float_ve(val):
    return float(val)

def default_int_ve(val):
    return int(val)

def default_str_ve(val):
    return str(val)

validate_and_extract_function_map = {
        'driver_license_number_ve': driver_license_number_ve,
        'state_ve': state_ve,
        'phone_ve': phone_ve,
        'dob_ve': dob_ve,
        'dob_ve_2': dob_ve_2,
        'ssn_ve': ssn_ve,
        'zip_ve': zip_ve,
        'default_float_ve': default_float_ve,
        'default_int_ve': default_int_ve,
        'default_str_ve': default_str_ve
    }