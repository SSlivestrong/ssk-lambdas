""" Util for creating a inquiry string for a test case - based off https://code.experian.local/users/c79450a/repos/asgo-platform-api-automationframework/browse """
from typing import Optional
from star_dataloader.consumer_pii import Consumer
import copy
from copy import deepcopy
import re

class TestInquiryString():
    """ class that defines a test inquiry string for executing a specific test condition
        some test scenarios are created just through pii - others are hardcoded edits to a valid
        inquiry string
    """

    def __init__(self, solution, parameters, pii_obj: Consumer):
        """ initialize test inquiry string based on parameters and pii - this data should be the happy path scenario
            parameters:
                solution - solution document
                parameters - parameters for inquiry string, all keys should be present
                    device_indicator: Optional[str]
                    preamble_code: str
                    operator_initials: str
                    inquiry_type: str
                    subcode_and_password: str
                    purpose_type: Optional[str]
                    verify_keywords: List[str]
                    products: List[str]
                pii - identifies the consumer for inquiry string
        """
        self.solution_id = solution["solution_id"]
        self.solution_uid = solution["uid"]
        self.solution = solution
        self.pii_obj = pii_obj
        self.pii = self._create_pii_substring(pii_obj)

        # required parameters, needed for all inquiry strings, should have valid value
        self.preamble_code: str = parameters["preamble_code"]
        self.operator_initials: str = parameters["operator_initials"]
        self.inquiry_type: str = parameters["inquiry_type"]
        self.subcode_and_password: str = parameters["subcode_and_password"]

        # optional, value of key may be none
        self.device_indicator: Optional[str] = parameters["device_indicator"]
        self.purpose_type: Optional[str] = parameters["purpose_type"]

        # lists, may be empty list
        self.verify_keywords: "list[str]" = parameters["verify_keywords"]
        self.products: "list[str]" = parameters["products"]
    
    def _create_pii_substring(self, pii_obj: Consumer):
        """Create pii string from pii object
        """
        p, s = pii_obj.primary_applicant, pii_obj.secondary_applicant
        pii_substring = f"{p.name.last_name}, {p.name.first_name} {'' if p.name.middle_name is None else p.name.middle_name} {'' if p.name.generation_code is None else p.name.generation_code} {p.ssn};"
        if s is not None:
            pii_substring += f"{s.name.last_name}, {s.name.first_name} {'' if s.name.middle_name is None else s.name.middle_name} {'' if s.name.generation_code is None else s.name.generation_code} {s.ssn};"
        if p.current_address is not None:
            pii_substring += f"CA-{p.current_address.line1}/{p.current_address.city} {p.current_address.state} {p.current_address.zip_code};"
        else:
            pii_substring += "CA-475 Anton Blvd/Costa Mesa CA 92626;"
        if s is not None:
            if s.current_address is not None:
                pii_substring += f"SCA-{s.current_address.line1}/{s.current_address.city} {s.current_address.state} {s.current_address.zip_code};"
            else:
                pii_substring += "SCA-475 Anton Blvd/Costa Mesa CA 92626;"
        if p.previous_address is not None:
            for pa in p.previous_address:
                pii_substring += f"PA-{pa.line1}/{pa.city} {pa.state} {pa.zip_code};"
        if p.phone is not None:
            for ph in p.phone:
                pii_substring += f"PH-{ph.number};"
        if p.employment is not None:
            # ignoring employer address here
            pii_substring += f"E-{p.employment.employer_name};"
        if p.dob is not None:
            pii_substring += f"Y-{p.dob};"
        if s is not None:
            pii_substring += f"JOINT;"
        return pii_substring

    def _assemble_inquiry_str(self, solution_id: str, pii: str, preamble_code: str, operator_initials: str,
                                inquiry_type: str, purpose_type: str, subcode_and_password: str, device_indicator: str,
                                verify_keywords: "list[str]", products: "list[str]"):

        """ Internal method to creates inquiry string with given parameters
        """
        device_indicator_str = device_indicator if device_indicator else ""
        purpose_type_str  = f"{purpose_type};" if purpose_type else ""

        # transform list parameters into string version required by OPS Inquiry
        # join products together with ";" delimiter
        verify_keywords_str = ";".join(verify_keywords) + ";" if len(verify_keywords) > 0 else ""
        products_str = ";".join(products) + ";" if len(products) > 0 else ""

        # turn solution id into GO keyword
        solution_id_keyword = f"GO-{solution_id};" if solution_id else ""

        # combine all components into inquiry string
        prefix = f"{device_indicator_str}{preamble_code} {operator_initials}{inquiry_type} {subcode_and_password}"
        suffix = f"{purpose_type_str}{verify_keywords_str}{solution_id_keyword}{products_str}"
        return f"{prefix} {pii};{suffix}"


    def _assemble_valid_inquiry_str(self):
        """ assemble inquiry string with all information given at construction """
        return self._assemble_inquiry_str(
            self.solution_id,
            self.pii,
            self.preamble_code,
            self.operator_initials,
            self.inquiry_type,
            self.purpose_type,
            self.subcode_and_password,
            self.device_indicator,
            self.verify_keywords,
            self.products
        )
    
    def _assemble_ssn_mismatch_str(self):
        """ assemble SSN mismatch by setting it to an invalid SSN """
        _pii_obj = deepcopy(self.pii_obj)
        _pii_obj.primary_applicant.ssn = "2223337777"
        return self._assemble_inquiry_str(
            self.solution_id,
            self._create_pii_substring(_pii_obj),
            self.preamble_code,
            self.operator_initials,
            self.inquiry_type,
            self.purpose_type,
            self.subcode_and_password,
            self.device_indicator,
            self.verify_keywords,
            self.products
        )
    
    def _assemble_ssn_missing_str(self):
        """ assemble SSN missing """
        _pii_obj = deepcopy(self.pii_obj)
        _pii_obj.primary_applicant.ssn = ""
        return self._assemble_inquiry_str(
            self.solution_id,
            self._create_pii_substring(_pii_obj),
            self.preamble_code,
            self.operator_initials,
            self.inquiry_type,
            self.purpose_type,
            self.subcode_and_password,
            self.device_indicator,
            self.verify_keywords,
            self.products
        )
    
    def _assemble_address_missing_str(self):
        """ assemble no CA- block """
        _pii_obj = deepcopy(self.pii_obj)
        _pii_obj.primary_applicant.current_address = None # override current address
        _pii_str = self._create_pii_substring(_pii_obj) 
        _pii_str = re.sub(r"CA-475 Anton Blvd/Costa Mesa CA 92626", "", _pii_str, count=1) # replace default CA
        return self._assemble_inquiry_str(
            self.solution_id,
            _pii_str,
            self.preamble_code,
            self.operator_initials,
            self.inquiry_type,
            self.purpose_type,
            self.subcode_and_password,
            self.device_indicator,
            self.verify_keywords,
            self.products
        )

    def _assemble_go_keyword_missing_inquiry_str(self):
        """ assemble inquiry string with all information given at construction but removing GO keyword """
        return self._assemble_inquiry_str(
            None,
            self.pii,
            self.preamble_code,
            self.operator_initials,
            self.inquiry_type,
            self.purpose_type,
            self.subcode_and_password,
            self.device_indicator,
            self.verify_keywords,
            self.products
        )


    def _assemble_go_keyword_invalid_inquiry_str(self):
        """ assemble inquiry string with all information given at construction but replacing GO keyword """
        return self._assemble_inquiry_str(
            "INVALIDSOLUTIONUID",
            self.pii,
            self.preamble_code,
            self.operator_initials,
            self.inquiry_type,
            self.purpose_type,
            self.subcode_and_password,
            self.device_indicator,
            self.verify_keywords,
            self.products
        )


    def _assemble_missing_purpose_type_inquiry_str(self):
        """ assemble inquiry string with all information given at construction but with missing purpose type """
        return self._assemble_inquiry_str(
            self.solution_id,
            self.pii,
            self.preamble_code,
            self.operator_initials,
            self.inquiry_type,
            None,
            self.subcode_and_password,
            self.device_indicator,
            self.verify_keywords,
            self.products
        )


    def _assemble_invalid_purpose_type_inquiry_str(self):
        """ creates inquiry string with all information given at construction replacing 
            purpose type with an invalid purpose type
        """

        # TODO: there may be a purpose type that is invalid in all cases that could be used
        # here instead
        # replace with specific purpose type
        invalid_purpose_type = "T-16"

        # if hardcoded purpose type matches expected purpose type, try another
        if self.purpose_type == invalid_purpose_type:
            invalid_purpose_type = "T-08"

        return self._assemble_inquiry_str(
            self.solution_id,
            self.pii,
            self.preamble_code,
            self.operator_initials,
            self.inquiry_type,
            invalid_purpose_type,
            self.subcode_and_password,
            self.device_indicator,
            self.verify_keywords,
            self.products
        )


    def _assemble_missing_verify_keyword_inquiry_str(self):
        """ creates inquiry string with all information given at construction removing verify keyword """

        # look for verify keyword in both keywords and product
        # it should not be in products but that is not enforced
        keywords = copy.deepcopy(self.verify_keywords)
        products = copy.deepcopy(self.products)

        # verify keyword starts with verify
        verify_keyword_prefix = "VERIFY-"

        # if any item starts with verify keyword, filter out
        keywords = [keyword for keyword in keywords if not keyword.startswith(verify_keyword_prefix)]
        products = [product for product in products if not product.startswith(verify_keyword_prefix)]

        return self._assemble_inquiry_str(
            self.solution_id,
            self.pii,
            self.preamble_code,
            self.operator_initials,
            self.inquiry_type,
            self.purpose_type,
            self.subcode_and_password,
            self.device_indicator,
            keywords,
            products
        )


    def _assemble_with_rm_keyword_inquiry_str(self):
        """ creates inquiry string with all information given at construction but add additional keywords based on
            optional models in solution document
        """
        models = self.solution.get("models", [])
        keywords = copy.deepcopy(self.verify_keywords)

        # adds additional RM keyword based on optional models specified in solution doc
        for model in models:
            model_response = model["model_response"]
            model_type_indicator = model["model_type_indicator"]
            if model_response == 'optional':
                rm_keyword = f"RM-{model_type_indicator}"
                if not rm_keyword in keywords:
                    keywords.append(rm_keyword)

        return self._assemble_inquiry_str(
            self.solution_id,
            self.pii,
            self.preamble_code,
            self.operator_initials,
            self.inquiry_type,
            self.purpose_type,
            self.subcode_and_password,
            self.device_indicator,
            keywords,
            self.products
        )


    def assemble_inquiry_str_by_test_case(self, test_case_alias: str):
        """
        Creates inquiry string using data given in construction
        If condition is not defined by pii, modifies based on test case to meet condition
        Params:
        - test case alias - test case alias of case to execute

        Returns:
            inquiry string matching test case
        """

        # the following test cases rely on missing/ bad data in the inquiry string rather than
        # the specific pii
        modification_methods = {
            "missing_go_keyword": self._assemble_go_keyword_missing_inquiry_str,
            "invalid_go_keyword": self._assemble_go_keyword_invalid_inquiry_str,
            "missing_t_keyword": self._assemble_missing_purpose_type_inquiry_str,
            "missing_verify_rm_keyword": self._assemble_missing_verify_keyword_inquiry_str,
            "invalid_purpose_type": self._assemble_invalid_purpose_type_inquiry_str,
            "with_rm_keyword": self._assemble_with_rm_keyword_inquiry_str,
            "ssn_mismatch": self._assemble_ssn_mismatch_str,
            "ssn_missing": self._assemble_ssn_missing_str,
            "address_missing": self._assemble_address_missing_str
        }

        # remove ;;;; values from inquiry string
        inquiry_string = ""
        if test_case_alias in modification_methods.keys():
            inquiry_string = modification_methods[test_case_alias]()
        else:
            inquiry_string = self._assemble_valid_inquiry_str()
        
        inq_list = inquiry_string.split(";")
        final_inquiry_string = ""
        for inq_param in inq_list:
            if len(inq_param) > 0:
                final_inquiry_string = final_inquiry_string + inq_param + ";"
        # if no modification required for given test case,
        return final_inquiry_string
