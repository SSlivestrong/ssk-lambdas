"""Utility functions"""
import time
from datetime import datetime
import string
import secrets
from time import gmtime, strftime
import dateutil


def get_epoch_millis():
    """Returns epoch time in milliseconds in UTC"""
    return round(time.time()*1000)


def get_epoch_millis_string():
    """Returns epoch time in milliseconds in UTC"""
    return str(round(time.time()*1000))


def get_epoch_seconds():
    """Returns epoch time in seconds"""
    return round(time.time())


def get_epoch_seconds_string():
    """Returns epoch time in seconds"""
    return str(round(time.time()))


def convert_iso_to_epoch_millis(iso_date):
    """ converts iso_date to epoch time in milliseconds in UTC """
    return round(dateutil.parser.isoparse(iso_date).timestamp() * 1000)

def convert_epoch_millis_to_utc_datetime(epoch_millis):
    """ converts epoch millis to datetime """
    return datetime.utcfromtimestamp(epoch_millis/1000)

def convert_epoch_millis_to_utc_date(epoch_millis):
    """ converts epoch millis to datetime """
    if epoch_millis:
        return datetime.utcfromtimestamp(epoch_millis/1000).strftime("%Y-%m-%d")
    else:
        return get_yyyy_mm_dd()

def convert_datetime_to_epoch_millis(datetime_obj):
    return round(datetime_obj.timestamp()*1000)

def check_if_max_time_passed(epoch_millis, max_seconds_passed):
    """ Returns true if more time than max_seconds_passed has elapsed since epoch millis, false otherwise """
    # get current datetime from current to epoch to make sure timezone is consistent 
    current_datetime = convert_epoch_millis_to_utc_datetime(get_epoch_millis())
    epoch_datetime = convert_epoch_millis_to_utc_datetime(epoch_millis)
    return (current_datetime - epoch_datetime).total_seconds() > max_seconds_passed

def generate_go_txn_id():
    """generate a 23-char unique string for each request hitting Ascend-Go
    credit report endpoint. This must be used to store in AuditLog
    and Billing system. 
    July 2022 - Use this string as M-text to support TCP requests, MUST upper it.
    Why? DCR echos back all upper case!!! See how wonderful it it? 
    RMDLC-4020 :- go_txn_id :- mmddYYYYHHMMSS********P   * are replaced with random aplhabet.
    ending with P indiate primary.In Joint for secondary we use S for billing.
    """
    # datetime.now().strftime("%Y%m%d%H%M%S-%f")
    # suffix = ''.join(random.choice(string.ascii_uppercase) for _ in range(9))
    # return datetime.now().strftime("%m%d%Y%H%M%S") + suffix
    suffix = ''.join(secrets.choice(string.ascii_letters) for _ in range(8))    
    return datetime.now().strftime("%m%d%Y%H%M%S") + suffix.upper() + "P"   


def get_strfgmtime_shortyear():
    """Returns GM time as String in YYMMDDHHMMSS format"""
    return strftime("%y%m%d%H%M%S", gmtime())


def get_strfgmtime_fullyear():
    """Returns GM time as String in YYYYMMDDHHMMSS format"""
    return strftime("%Y%m%d%H%M%S", gmtime())


def divide_chunks(full_list, chunk_size):
    """Returns a two dimensional list for a list with each chunk of max size 'n'"""
    for i in range(0, len(full_list), chunk_size):
        yield full_list[i:i + chunk_size]


def get_yyyy_mm_dd():
    """Returns current date in yyyy-mm-dd format"""
    return datetime.now().strftime("%Y-%m-%d")


def get_yy_mm_dd():
    """Returns current date in yy-mm-dd format"""
    return datetime.now().strftime("%y-%m-%d")


def get_yyyymmdd():
    """Returns current date in yyyymmdd format"""
    return datetime.now().strftime("%Y%m%d")


def get_yymmdd():
    """Returns current date in yymmdd format"""
    return datetime.now().strftime("%y%m%d")


def get_today_millis():
    """Returns today with millis in HHMMSSsss format"""
    return datetime.now().strftime()
