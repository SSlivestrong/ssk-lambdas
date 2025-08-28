"""pydantic consumer object model"""
from typing import List, Optional
from pydantic import BaseModel


class Name(BaseModel):
    """ Consumer Name object """
    last_name: str
    first_name: str
    middle_name: str | None = None
    generation_code: str | None = None
    prefix: str | None = None


class License(BaseModel):
    """ License object """
    number: str | None = None
    state: str | None = None


class SecondaryId(BaseModel):
    """ Secondary ID object """
    type: str
    value: str
    region: str | None = None
    country: str | None = None
    expiration: str | None = None


class Phone(BaseModel):
    """ Phone object """
    number: str
    type: str | None = None


class Address(BaseModel):
    """ Address object """
    line1: str
    line2: str | None = None
    city: str | None = None
    state: str | None = None
    zip_code: str | None = None
    country: str | None = None


class Employment(BaseModel):
    """ Employment object """
    employer_name: str
    employer_address: Address | None = None


class Primary(BaseModel):
    """ Primary Applicant object """
    name: Name
    dob: str | None = None
    ssn: str | None = None
    ein: str | None = None
    tin: str | None = None
    driverslicense: License | None = None
    secondary_id: SecondaryId | None = None
    phone: List[Phone] | None = None
    email_id: str | None = None
    employment: Employment | None = None
    current_address: Address | None = None
    previous_address: List[Address] | None = None
    inquiry_address: Address | None = None
    epin: str | None = None


class Secondary(BaseModel):
    """ Secondary Applicant object """
    name: Name
    dob: str | None = None
    ssn: str | None = None
    ein: str | None = None
    tin: str | None = None
    driverslicense: License | None = None
    secondary_id: SecondaryId | None = None
    phone: List[Phone] | None = None
    email_id: str | None = None
    employment: Employment | None = None
    current_address: Optional[Address] = None
    previous_address: List[Address] | None = None
    inquiry_address: Address | None = None
    epin: str | None = None


class Consumer(BaseModel):
    """ Consumer object """
    primary_applicant: Primary | None
    secondary_applicant: Optional[Secondary] | None = None