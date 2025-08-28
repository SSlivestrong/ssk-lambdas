import pandas as pd
import json
from .consumer_pii import Consumer, Primary, Name


class StarTestData():
    def __init__(self, excel_io,
                 header_config: dict,
                 block_builder: dict,                 
                 sheet_name: str=None,
                 validate_and_extract: dict={}) -> None:
        '''
        Star test case class.
        
        Args:
            excel_io : path to the data spreadsheet / io object
            sheet_name (str): Sheet name
            validate_and_extract (dict): Function map for validation and extraction
            block_builder (dict): Function map for building inquiry
        '''
        
        self.header_config = header_config
        if sheet_name:
            self.star_df = pd.read_excel(excel_io, sheet_name, keep_default_na=False)
        else:
            self.star_df = pd.read_excel(excel_io, keep_default_na=False)
        
        self.header_cache = {}
        self.rev_header_cache = {}
        for key in self.header_config:
            index, required = self.header_config[key]
            found = False
            for sub_key in index:
                if sub_key in self.star_df:
                    self.header_cache[key] = sub_key
                    self.rev_header_cache[sub_key] = key
                    found = True
                    print(f'INFO: Found key: {key} with sub-key: {sub_key}')
                    break # expecting a single match
            if not found and required:
                raise Exception(f'Missing required header: {key}')

        self.validate_and_extract = validate_and_extract
        self.block_builder = block_builder
    
    def __len__(self):
        return self.star_df.shape[0]

    def _prepare_inquiry(self, pii_dict: dict,
                               client_metadata: str,
                               pipeline_blueprint: list) -> str:
        consumer = Consumer(primary_applicant=Primary(name=Name(first_name='', last_name='')))

        # required block
        required_block = self.block_builder['required'](pii_dict, consumer, client_metadata=client_metadata)
        
        # address blocks
        current_address_block = self.block_builder['current_address'](pii_dict, consumer)
        prev1_address_block = self.block_builder['prev1_address'](pii_dict, consumer, suffix=1)
        prev2_address_block = self.block_builder['prev2_address'](pii_dict, consumer, suffix=2)

        # phone block
        phone_block = self.block_builder['phone'](pii_dict, consumer)

        # driver license block
        driver_license_block = self.block_builder['driver_license'](pii_dict, consumer)

        # employer block
        employer_block = self.block_builder['employment'](pii_dict, consumer)

        # year of birth block
        yob_block = self.block_builder['yob'](pii_dict, consumer)
        
        # m-dash block
        m_dash_block = self.block_builder['m_dash'](pii_dict, consumer)
        
        return ';'.join([required_block, 
                         current_address_block, 
                         prev1_address_block, 
                         prev2_address_block, 
                         phone_block, 
                         driver_license_block,
                         employer_block,
                         yob_block, 
                         m_dash_block,
                         *pipeline_blueprint]), json.loads(consumer.model_dump_json())

    def get_case_payload(self, idx: int,
                 payload_template: dict,
                 client_metadata: str=None,
                 pipeline_blueprint: list=None) -> dict:
        '''
        Fetches a record from the dataset and builds the inquiry for a 
        specified payload.

        Args:
            idx (int): Record index in the dataset
            payload_template (dict): Test json payload
            client_metadata (str): DeviceIndicatorPreamble OperatorInitialsInquiryType SubcodePassword
            pipeline_blueprint (list): List string blocks specific to Ascend Ops
        
        Returns:
            Inquiry payload json (dict)
        '''

        # load data from excel file
        pii_dict = {}
        for key in self.header_config:
            try:
                ext_str = str(self.star_df.loc[idx, self.header_cache[key]])
                if key in self.validate_and_extract:
                    ext_str = self.validate_and_extract[key](ext_str)
                pii_dict[key] = '' if ext_str == 'nan' else ext_str      
            except:
                pii_dict[key] = ''  
            if pii_dict[key] == '' and self.header_config[key][1]:
                raise Exception(f'Missing required info: {key}')            

        # setup inquiry
        inquiry_str, payload_template["consumer_pii"] = \
            self._prepare_inquiry(pii_dict, client_metadata, pipeline_blueprint)
        if len(client_metadata) > 0 and len(pipeline_blueprint) > 0 :
            payload_template["inquiry"] = inquiry_str
        
        # setup model_specific_custom_data
        if "model_specific_custom_data" in payload_template:
            for model_input in payload_template["model_specific_custom_data"]:
                for attr in model_input["attributes"]:
                    if attr["attribute"] in self.rev_header_cache:
                        attr["value"] = pii_dict[self.rev_header_cache[attr["attribute"]]]

        return payload_template