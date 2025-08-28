import unittest
from unittest.mock import Mock
from ascendops_commonlib.models.billing_message import ApplicantPII
from billing_consumer_new.helpers.app_logger import custom_logger as logger
from billing_consumer_new.billing_service.applicant_pii_processor import process_applicant_pii
# from ascendops_realtime.background_tasks.billing.create_billing_record import add_pii


class TestCreateBillingRecord(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.logger = logger
        self.applicant_type = "primary"
        self.transaction_id = "04032024034048LXBINNHWP"
    
    async def test_add_pii_1(self):
        """
            SSN : None
            DOB : None
            Name:
                Middle_Name : None
                Generation_Code : None
                Prefix : None
            Current Address:
                line2 : None
                Country : None
            previous_address: None
        """
        mock_applicant_pii = ApplicantPII(
            name = {
                "last_name": "ANASTASIO",
                "first_name": "JESSE"
            },
            inquiry_address = {
                "line1": "2752 SOLOMONS ISLAND RD",
                "city": "EDGEWATER",
                "state": "MD",
                "zip_code": "210371211"
            }
        )

        mock_inquiry_context = Mock()
        mock_inquiry_context.applicant_pii = mock_applicant_pii
        mock_inquiry_context.logger = self.logger
        mock_inquiry_context.applicant_type = self.applicant_type
        mock_inquiry_context.transaction_id = self.transaction_id
        
        applicant_billing_record = await process_applicant_pii(mock_applicant_pii, self.transaction_id)
        
        for key, value in applicant_billing_record.items():
            if key == "ssn":
                self.assertEqual(len(value), 9)
            elif key == "year_of_birth":
                self.assertEqual(len(value), 4)
            elif key == "consumer_name":
                self.assertEqual(len(value), 129)
            elif key == "current_address":
                self.assertEqual(len(value), 97)
            elif key == "1st_previous_address":
                self.assertEqual(len(value), 97)
            elif key == "2nd_previous_address":
                self.assertEqual(len(value), 97)
        
        expected_applicant_billing_record = {
            "ssn": "         ",
            "year_of_birth": "    ",
            "consumer_name": "ANASTASIO                                                       JESSE                                                            ",
            "current_address": "2752      SOLOMONS ISLAND RD                  EDGEWATER                       MD        210371211",
            "1st_previous_address": " " * 97,
            "2nd_previous_address": " " * 97
        }

        # Verify applicant_billing_record with expected_applicant_billing_record
        self.assertEqual(applicant_billing_record, expected_applicant_billing_record)


    async def test_add_pii_2(self):
        """
            SSN : ""
            DOB : ""
            Name:
                Middle_Name : ""
                Generation_Code : ""
                Prefix : ""
            Current Address:
                line2 : ""
                Country : ""
            previous_address: []
        """
        mock_applicant_pii = ApplicantPII(
            name = {
                "last_name": "ANASTASIO",
                "first_name": "JESSE",
                "middle_name": "",
                "generation_code": "",
                "prefix": ""
            },
            ssn = "",
            dob = "",
            inquiry_address = {
                "line1": "2752 SOLOMONS ISLAND RD",
                "line2": "",
                "city": "EDGEWATER",
                "state": "MD",
                "zip_code": "210371211",
                "country": ""
            },
            previous_address = []
        )

        mock_inquiry_context = Mock()
        mock_inquiry_context.applicant_pii = mock_applicant_pii
        mock_inquiry_context.logger = self.logger
        mock_inquiry_context.applicant_type = self.applicant_type
        mock_inquiry_context.transaction_id = self.transaction_id
        
        applicant_billing_record = await process_applicant_pii(mock_applicant_pii, self.transaction_id)

        for key, value in applicant_billing_record.items():
            if key == "ssn":
                self.assertEqual(len(value), 9)
            elif key == "year_of_birth":
                self.assertEqual(len(value), 4)
            elif key == "consumer_name":
                self.assertEqual(len(value), 129)
            elif key == "current_address":
                self.assertEqual(len(value), 97)
            elif key == "1st_previous_address":
                self.assertEqual(len(value), 97)
            elif key == "2nd_previous_address":
                self.assertEqual(len(value), 97)
           
        expected_applicant_billing_record = {
            "ssn": "         ",
            "year_of_birth": "    ",
            "consumer_name": "ANASTASIO                                                       JESSE                                                            ",
            "current_address": "2752      SOLOMONS ISLAND RD                  EDGEWATER                       MD        210371211",
            "1st_previous_address": " " * 97,
            "2nd_previous_address": " " * 97
        }

        # Verify applicant_billing_record with expected_applicant_billing_record
        self.assertEqual(applicant_billing_record, expected_applicant_billing_record)

    
    async def test_add_pii_3(self):
        """
            SSN : Not Empty/None
            DOB : Not Empty/None
            Name:
                Middle_Name : Not Empty/None
                Generation_Code : Not Empty/None
                Prefix : Not Empty/None
            Current Address:
                line2 : Not Empty/None
                Country : Not Empty/None
            previous_address: Contains 1 previous_address
        """
        mock_applicant_pii = ApplicantPII(
            name = {
                "last_name": "SHINDELAR",
                "first_name": "VINCENT",
                "middle_name": "E",
                "generation_code": "JR",
                "prefix": "Mr"
            },
            ssn = "666641376",
            dob = "02111933",
            inquiry_address = {
                "line1": "2541 STONE RIDGE DR",
                "line2": "Apt 1122",
                "city": "POPLAR BLUFF",
                "state": "MO",
                "zip_code": "639012169",
                "country": "USA"
            },
            previous_address = [
                {
                    "line1": "1234 Anystreet Rd",
                    "line2": "Apt 1122",
                    "city": "Anytown",
                    "state": "AZ",
                    "zip_code": "12344",
                    "country": "USA"
                }
            ]
        )

        mock_inquiry_context = Mock()
        mock_inquiry_context.applicant_pii = mock_applicant_pii
        mock_inquiry_context.logger = self.logger
        mock_inquiry_context.applicant_type = "secondary"
        mock_inquiry_context.transaction_id = self.transaction_id
        
        applicant_billing_record = await process_applicant_pii(mock_applicant_pii, self.transaction_id)

        for key, value in applicant_billing_record.items():
            if key == "ssn":
                self.assertEqual(len(value), 9)
            elif key == "year_of_birth":
                self.assertEqual(len(value), 4)
            elif key == "consumer_name":
                self.assertEqual(len(value), 129)
            elif key == "current_address":
                self.assertEqual(len(value), 97)
            elif key == "1st_previous_address":
                self.assertEqual(len(value), 97)
            elif key == "2nd_previous_address":
                self.assertEqual(len(value), 97)
           
        expected_applicant_billing_record = {
            "ssn": "666641376",
            "year_of_birth": "1933",
            "consumer_name": "SHINDELAR                                                       VINCENT                         E                               J",
            "current_address": "2541      STONE RIDGE DRApt 1122              POPLAR BLUFF                    MO        639012169",
            "1st_previous_address": "1234      Anystreet RdApt 1122                Anytown                         AZ        12344    ",
            "2nd_previous_address": " " * 97
        }

        # Verify applicant_billing_record with expected_applicant_billing_record
        self.assertEqual(applicant_billing_record, expected_applicant_billing_record)


    async def test_add_pii_4(self):
        """
            SSN : Not Empty/None
            DOB : None
            Name:
                Middle_Name : Not Empty/None
                Generation_Code :None
                Prefix : None
            Current Address:
                line2 : None
                Country : Empty
            previous_address: Contains 2 previous_address
        """
        mock_applicant_pii = ApplicantPII(
            name = {
                "last_name": "BARNETT",
                "first_name": "IRENE",
                "middle_name": "F",
                "generation_code": "",
            },
            ssn = "666444255",
            inquiry_address = {
                "line1": "2752 SOLOMONS ISLAND RD",
                "city": "EDGEWATER",
                "state": "MD",
                "zip_code": "210371211",
                "country": ""
            },
            previous_address = [
                {
                    "line1": "999 Oak Street",
                    "line2": "",
                    "city": "Orange",
                    "state": "CA",
                    "zip_code": "92544"
                },
                {
                    "line1": "1001 Oak Street",
                    "line2": "Apt 1122",
                    "city": "Orange",
                    "state": "CA",
                    "zip_code": "92544",
                    "country": "USA"
                }
            ]
        )

        mock_inquiry_context = Mock()
        mock_inquiry_context.applicant_pii = mock_applicant_pii
        mock_inquiry_context.logger = self.logger
        mock_inquiry_context.applicant_type = "secondary"
        mock_inquiry_context.transaction_id = self.transaction_id
        
        applicant_billing_record = await process_applicant_pii(mock_applicant_pii, self.transaction_id)

        for key, value in applicant_billing_record.items():
            if key == "ssn":
                self.assertEqual(len(value), 9)
            elif key == "year_of_birth":
                self.assertEqual(len(value), 4)
            elif key == "consumer_name":
                self.assertEqual(len(value), 129)
            elif key == "current_address":
                self.assertEqual(len(value), 97)
            elif key == "1st_previous_address":
                self.assertEqual(len(value), 97)
            elif key == "2nd_previous_address":
                self.assertEqual(len(value), 97)
        
        expected_applicant_billing_record = {
            "ssn": "666444255",
            "year_of_birth": "    ",
            "consumer_name": "BARNETT                                                         IRENE                           F                                ",
            "current_address": "2752      SOLOMONS ISLAND RD                  EDGEWATER                       MD        210371211",
            "1st_previous_address": "999       Oak Street                          Orange                          CA        92544    ",
            "2nd_previous_address": "1001      Oak StreetApt 1122                  Orange                          CA        92544    "
        }

        # Verify applicant_billing_record with expected_applicant_billing_record
        self.assertEqual(applicant_billing_record, expected_applicant_billing_record)