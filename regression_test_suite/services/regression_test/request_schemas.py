from pydantic import BaseModel, model_validator
from star_dataloader.consumer_pii import Consumer
from typing import List, Tuple, Any, Optional, Union
from helpers import rts_config

class InquiryStringInfo(BaseModel):
    solution_id: str = ""
    device_indicator: str = ""
    preamble_code: str = ""
    operator_initials: str = ""
    inquiry_type: str = ""
    subcode_and_password: str = ""
    purpose_type: str = ""
    verify_keywords: List[str]
    products: List[str]

class HeaderConfig(BaseModel):
    class Config:
        extra = 'allow'
    first_name: Optional[Tuple[List[str], bool]] = (["First Name", "FIRST NAME", "FIRST", "First", "CON_FST_NM"], True)
    last_name: Optional[Tuple[List[str], bool]] = (["Last Name", "LAST NAME", "LAST", "CON_LST_NM"], True)
    second_last_name: Optional[Tuple[List[str], bool]] = (["2nd Last"], False)
    ssn: Optional[Tuple[List[str], bool]] = (["SSN", "On-file SSN", "NEW SSN"], True)
    middle_name: Optional[Tuple[List[str], bool]] = (["MID INIT", "Middle", "MIDDLE", "MI", "M", "Middle Name", "MIDDLE NAME", "CON_MID_NM"], False)
    gen: Optional[Tuple[List[str], bool]] = (["Gen", "GEN", "GEN CODE", "Gen Code"], False)
    email: Optional[Tuple[List[str], bool]] = (["EMAIL"], False)
    unit: Optional[Tuple[List[str], bool]] = (["Unit", "Curr Unit", "APT"], False)
    unit_number: Optional[Tuple[List[str], bool]] = (["Unit #", "Curr Unit #", "Address2", "APT$", "Apt #", "APT #"], False)
    house_number: Optional[Tuple[List[str], bool]] = (["House #", "HOUSE #", "Curr House #"], False)
    street_number: Optional[Tuple[List[str], bool]] = (["STR #", "STREET #", "ST #"], False)
    street_name: Optional[Tuple[List[str], bool]] = (["Street Name", "STREET NAME", "Curr Street Name", "ST NAME", "STR NAME", "CURRENT STREET", "CURR STREET", "Current Street Name"], False)
    street_suffix: Optional[Tuple[List[str], bool]] = (["Str Suf", "STR SUF", "SUFFIX", "SUFF", "Curr Str Suf", "SUBB"], False)
    address: Optional[Tuple[List[str], bool]] = (["ADDRESS", "STREET ADDRESS", "Street Address", "Address", "Street Name and House Number", "INQ_STREET_ADDR", "Address1", "INQUIRY ADDRESS"], False)
    city: Optional[Tuple[List[str], bool]] = (["City", "CITY", "Curr City", "City Name", "CURR CITY", "CURRENT CITY", "INQ_CITY_NM", "Current City"], False)
    state: Optional[Tuple[List[str], bool]] = (["State", "STATE", "ST", "Curr State", "State Code", "INQ_STATE_CD"], False)
    zip_code: Optional[Tuple[List[str], bool]] = (["ZIP Code", "ZIP CODE", "ZIP", "Curr ZIP Code", "Zipcode", "INQ_ZIP9_CD"], False)
    demographics: Optional[Tuple[List[str], bool]] = (["CITY/STATE/ZIP CODE"], False)
    prev1_unit: Optional[Tuple[List[str], bool]] = (["Prev1 Unit"], False)
    prev1_unit_number: Optional[Tuple[List[str], bool]] = (["Prev1 Unit #"], False)
    prev1_house_number: Optional[Tuple[List[str], bool]] = (["Prev1 House #"], False)
    prev1_street_name: Optional[Tuple[List[str], bool]] = (["Prev1 Street Name", "PREV STREET1", "PREV STREET NAME1"], False)
    prev1_street_suffix: Optional[Tuple[List[str], bool]] = (["Prev1 Str Suf"], False)
    prev1_city: Optional[Tuple[List[str], bool]] = (["Prev1 City", "PREV CITY1"], False)
    prev1_state: Optional[Tuple[List[str], bool]] = (["Prev1 State"], False)
    prev1_zip_code: Optional[Tuple[List[str], bool]] = (["Prev1 ZIP Code"], False)
    prev2_unit: Optional[Tuple[List[str], bool]] = (["Prev2 Unit"], False)
    prev2_unit_number: Optional[Tuple[List[str], bool]] = (["Prev2 Unit #"], False)
    prev2_house_number: Optional[Tuple[List[str], bool]] = (["Prev2 House #"], False)
    prev2_street_name: Optional[Tuple[List[str], bool]] = (["Prev2 Street Name", "PREV STREET2", "PREV STREET NAME2"], False)
    prev2_street_suffix: Optional[Tuple[List[str], bool]] = (["Prev2 Str Suf"], False)
    prev2_city: Optional[Tuple[List[str], bool]] = (["Prev2 City", "PREV CITY2"], False)
    prev2_state: Optional[Tuple[List[str], bool]] = (["Prev2 State"], False)
    prev2_zip_code: Optional[Tuple[List[str], bool]] = (["Prev2 ZIP Code"], False)
    employer1: Optional[Tuple[List[str], bool]] = (["Employment1", "EMPLOYMENT1", "Employer1", "EMPLOYER1", "PREVIOUS CURRENT EMPLOYER", "EMPLOYER NAME"], False)
    dob: Optional[Tuple[List[str], bool]] = (["DOB", "YOB", "DOB/YOB", "DOB / YOB", "DOB/ YOB", "DOB or YOB", "DOB_YOB", "YEAR OF BIRTH"], False)
    phone: Optional[Tuple[List[str], bool]] = (["PHONE", "Phone", "PHONE1", "PHONE #", "PH_NB_1", "Phone Number"], False)
    driver_license_state: Optional[Tuple[List[str], bool]] = (["DL State", "DL STATE", "DL STATE CODE", "DL State Code", "DL_STATE_CD"], False)
    driver_license_number: Optional[Tuple[List[str], bool]] = (["DL Number", "DL NUMBER", "DRIVER LICENSE", "Driver License", "DRIVERS LICENSE", "DL_NB", "Drivers License"], False)
    m_dash_keyword: Optional[Tuple[List[str], bool]] = (["M-Keyword", "M-keyword"], False)

class ValidateAndExtract(BaseModel):
    class Config:
        extra = 'allow'
    driver_license_number: Optional[str] = "driver_license_number_ve"
    state: Optional[str] = "state_ve"
    driver_license_state: Optional[str] = "state_ve"
    phone: Optional[str] = "phone_ve"
    dob: Optional[str] = "dob_ve"
    ssn: Optional[str] = "ssn_ve"
    zip_code: Optional[str] = "zip_ve"

class BlockBuilder(BaseModel):
    required: Optional[str] = "required_builder"
    current_address: Optional[str] = "current_address_builder_3"
    prev1_address: Optional[str] = "prev_address_builder"
    prev2_address: Optional[str] = "prev_address_builder"
    phone: Optional[str] = "phone_builder"
    driver_license: Optional[str] = "driver_license_builder"
    employment: Optional[str] = "employment_builder"
    yob: Optional[str] = "yob_builder"
    m_dash: Optional[str] = "m_dash_builder"

class NewConsumers(BaseModel):
    excel_file_name: str = ""
    case_code: str = ""
    save_consumer_pii: bool = False
    sheet_name: str = ""
    max_pick: int = 50
    header_config: HeaderConfig
    validate_and_extract: ValidateAndExtract
    block_builder: BlockBuilder

class ExistingConsumers(BaseModel):
    test_case_code: str = ""
    volume: float = 5

class CreateTestcasesModel(BaseModel):
    ascendops_url: str = rts_config.AO_SERVICE_URL
    ascendops_endpoint: str = "/api/v3/ops-inquiry"
    solution_index: str = "solution"
    is_prod_mockup: bool = False
    tested_by: str = "Bureau Composer Team"
    inquiry_string_info: InquiryStringInfo = None
    ao_payload_info: Any
    verified_create_request: bool = False
    run_batch_size: int = 1
    solution_edgecases: Optional[List[str]] = None
    new_consumers: Optional[NewConsumers] = None
    existing_consumers: Optional[List[ExistingConsumers]] = None

    @model_validator(mode='after')
    def check_at_least_one(cls, values):
        if not (values.solution_edgecases or values.new_consumers or values.existing_consumers):
            raise ValueError('At least one of "solution_edgecases", "new_consumers", or "existing_consumers" must be specified.')
        return values

class FilterTestcasesModel(BaseModel):
    solution_id: str
    case_code: str = ""
    trade_date: str = ""
    testcase_id: str = ""

    @model_validator(mode='after')
    def check_at_least_one(cls, values):
        if not (values.solution_id):
            raise ValueError('"solution_id" must be specified.')
        return values

class Test(BaseModel):
    filters: FilterTestcasesModel
    volume: float = 1.0
    batch_size: int = 1

class RunTestcasesModel(BaseModel):
    ascendops_url: str = rts_config.AO_SERVICE_URL
    ascendops_endpoint: str = "/api/v3/ops-inquiry"
    solution_index: str = "solution"
    tested_by: str = "Bureau Composer Team"
    tests: List[Test]

class DeleteTestcasesModel(BaseModel):
    filters: FilterTestcasesModel
    tested_by: str = "Bureau Composer Team"

class PopulateCasecodeModel(BaseModel):
    custom_pii: Optional[Consumer] = None
    new_case_code: str = ""
    existing_case_code: str = ""
    volume: float = 5

    @model_validator(mode='after')
    def check_at_least_one(cls, values):
        if not (values.custom_pii or values.existing_case_code):
            raise ValueError('At least one of "custom_pii" or "existing_case_code" must be specified.')
        return values
