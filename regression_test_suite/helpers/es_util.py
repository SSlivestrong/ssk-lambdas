"""ElasticSearch wrapper."""

import typing
from elasticsearch.exceptions import NotFoundError, RequestError
from elasticsearch import Elasticsearch, RequestsHttpConnection, helpers
from botocore.credentials import RefreshableCredentials
from requests_aws4auth import AWS4Auth
import boto3
import time

from ascendops_commonlib.ops_utils import ops_config
from ascendops_commonlib.ops_utils.log_util import CustomLogging

AWS_SERVICE = ops_config.AWS_SERVICE_ES
SSL_PROTOCOL = True
VERIFY_CERT = True

# By default, ES allows urllib3 to open up to 10 connections to each node.
# Change this value to suit runtime environement
DEFAULT_START = 0
DEFAULT_MAXSIZE = 10000
DEFAULT_SNIFF_ON_START = False
DEFAULT_SNIFF_ON_CONNECTION_FAIL = False
DEFAULT_SNIFFER_TIMEOUT = ops_config.DEFAULT_ES_SNIFFER_TIMEOUT
DEFAULT_SNIFF_TIMEOUT = 30
DEFAULT_RETRY_DELAY = 0.05

DEFAULT_ES_HOST = ops_config.DEFAULT_ES_HOST
DEFAULT_ES_PORT = ops_config.DEFAULT_ES_PORT
DEFAULT_ES_ROLE = ops_config.DEFAULT_ES_ROLE
DEFAULT_REGION = ops_config.DEFAULT_REGION


class ESConnector:
    """To connect to a pre-configured ES:
    Design assumption:
        - Each index stores one document type.
    """


    def __init__(self):
        """
        profile (str):
           If provided, it is used for the assumed role;
           Otherwise, connect to ES using credential of whatever
           profile currently configured in the environment.
        """
        aws_auth = self._create_auth()
        self.esearch = Elasticsearch(
            hosts=[{'host': DEFAULT_ES_HOST, 'port': DEFAULT_ES_PORT}],
            http_auth=aws_auth,
            use_ssl=SSL_PROTOCOL,
            verify_certs=VERIFY_CERT,
            connection_class=RequestsHttpConnection,
            sniff_on_start=DEFAULT_SNIFF_ON_START,
            sniff_on_connection_fail=DEFAULT_SNIFF_ON_CONNECTION_FAIL,
            sniffer_timeout=DEFAULT_SNIFFER_TIMEOUT,
            sniff_timeout=DEFAULT_SNIFF_TIMEOUT
        )

    
    def _get_session_credentials(self, role_arn=DEFAULT_ES_ROLE, session_name="ES-Session", expiry_time=3600):
        """
        Get session credentials
        """
        profile = ops_config.IAM_PROFILE
        if profile:
            print("Using profile: ", profile)
            session = boto3.Session(profile_name=profile, region_name=DEFAULT_REGION)
            sts_client = session.client('sts')
        else:
            session = boto3.Session(region_name=DEFAULT_REGION)
            sts_client = session.client('sts', endpoint_url=f"https://sts.{DEFAULT_REGION}.amazonaws.com")
            
        role_credentials = sts_client.assume_role(
            RoleArn=role_arn,
            RoleSessionName=session_name,
            DurationSeconds=expiry_time,
        ).get("Credentials")
        
        session_credentials  = {
            "access_key": role_credentials.get("AccessKeyId"),
            "secret_key": role_credentials.get("SecretAccessKey"),
            "token": role_credentials.get("SessionToken"),
            "expiry_time": role_credentials.get("Expiration").isoformat(),
        }
        
        return session_credentials 
        
        
    def _create_auth(self) -> boto3.Session:
        """
        Get AWS auth.
        """
        try:
            # get refreshable credentials
            refreshable_credentials = RefreshableCredentials.create_from_metadata(
                metadata=self._get_session_credentials(),
                refresh_using=self._get_session_credentials,
                method="sts-assume-role",
            )

            # create auth with refreshable credentials
            aws_auth = AWS4Auth(
                region=DEFAULT_REGION,
                service=AWS_SERVICE,
                refreshable_credentials=refreshable_credentials
            )        
        except:
            # create auth with credentials
            credentials = self._get_session_credentials()
            aws_auth = AWS4Auth(
                credentials['access_key'],
                credentials['secret_key'],
                DEFAULT_REGION, AWS_SERVICE, session_token=credentials['token']
            )
        
        return aws_auth


    @staticmethod
    def instance(startup=False):
        """To obtain an instance"""
        CustomLogging.log_es_call_stack_trace(startup, None)
        return ESConnector()


    def handle_exception(self, xcp: Exception):
        # we are not expecting this, but if that happens then retry
        print(f'Exception: {str(xcp)}: Will retry in {DEFAULT_RETRY_DELAY} seconds')
        time.sleep(DEFAULT_RETRY_DELAY)


    def get_es_info(self):
        """For testing and debugging purpose
        Note: Version 7.11 has a {"type": "version"}
        """
        try:
            info = self.esearch.info()
        except Exception as xcp:
            self.handle_exception(xcp)
            return self.get_es_info()
        return info


    def inspect_indices(self):
        """For testing and debugging purpose
        """
        try:
            all_indices = self.esearch.indices.get_alias()
        except Exception as xcp:
            self.handle_exception(xcp)
            return self.inspect_indices()
        return all_indices


    def get_index_mapping(self, index_name):
        """For testing and debugging purpose
        Params:
            - index_name: name of the index to get mapping
        Return: ES response
        """
        try:
            res = self.esearch.indices.get_mapping(index=index_name)
        except Exception as xcp:
            self.handle_exception(xcp)
            return self.get_index_mapping(index_name)
        return res


    def index_exists(self, index_name_list):
        """To check if given indices exist. This is mainly
        to support self.create_index method.
        Note that the API returns False if one in the list
        does not exist.
        Params:
            - index_name_list: list of names
        Return: ES response
        """
        try:
            res = self.esearch.indices.exists(index_name_list)
        except Exception as xcp:
            self.handle_exception(xcp)
            return self.index_exists(index_name_list)
        return res


    def delete_index(self, index_name_list):
        """To 'delete' indices with a given list of indices as an array object
        Params:
            - index_name_list: list of names
        Return:
        If the index does not exist, ES throws NotFoundError:
            status_code: 404,
            error: 'index_not_found_exception
            info: {error dictionary will have the details}
        Catch and return a dictionary to the caller:
            {
                'target': index_name,
                'error': 'index_not_found_exception',
                status_code': 404
            }
        Note: even if one index is non existent in an array, the whole operation is rejected
        """
        try:
            try:
                res = self.esearch.indices.delete(index_name_list)
            except NotFoundError as err:
                error_info = err.info
                error_reason = str(err)
                if isinstance(error_info, dict):
                    error_reason = error_info.get("error", {}).get("reason")
                return {'reason': error_reason,
                        'error': err.error, 'status_code': err.status_code}
            return res
        except Exception as xcp:
            self.handle_exception(xcp)
            return self.delete_index(index_name_list)


    def create_index(self, index_name, body_content):
        """To create an index, with optional settings and mappings,
        only if the index does not exist.
        Params:
            - index_name: The index's name
            - body_content: dictionary
        Sample body_content with default settings value of 1
        {
            "settings": {
                "number_of_shards": 1,
                "number_of_replicas": 1
            },
            "mappings": {
            }
        }

        If the index already exists: ES throws ConflictError:
            status_code: 400,
            error: 'resource_already_exists_exception',
            info: {dictionary contains a lot more details}
        Catch and return a dictionary to caller:
            {
                'target': index_name,
                'error': 'resource_already_exists_exception',
                'status_code': 400
            }
        """
        try:
            try:
                return self.esearch.indices.create(index_name, body=body_content)
            except RequestError as err:
                return {'target': index_name, 'error': err.error, 'status_code': err.status_code}
        except Exception as xcp:
            self.handle_exception(xcp)
            return self.create_index(index_name, body_content)


    def update_index(self, index_name, body_content):
        """
        Updates the mapping of an Elasticsearch index.

        Args:
            index_name (str): The name of the index to update.
            body_content (dict): The mapping content to update the index with.

        Returns:
            dict: A dictionary containing the result of the update operation. If an error occurs,
                    the dictionary will contain the target index name, the error message, and the status code.
        """
        try:
            try:
                return self.esearch.indices.put_mapping(index=index_name, body=body_content)
            except RequestError as err:
                return {'target': index_name, 'error': err.error, 'status_code': err.status_code}
        except Exception as xcp:
            self.handle_exception(xcp)
            return self.update_index(index_name, body_content)


    def put_mapping(self, index_name, mapping_content, **kwargs):
        """To put a mapping definition to the index index_name
        Params:
            - index_name: The index's name
            - mapping_content: dictionary
        """
        try:
            res = self.esearch.indices.put_mapping(body=mapping_content, index=index_name, **kwargs)
            return res
        except Exception as xcp:
            self.handle_exception(xcp)
            return self.put_mapping(index_name, mapping_content, **kwargs)


    def get_document(self, index_name, doc_id, include_fields: typing.Optional[list]=None, exclude_fields: typing.Optional[list]=None):
        """To retrieve a document identified by doc_id.
        Params:
            - index_name: The index's name
            - doc_id: id of the document
        """
        try:
            kwargs = {}
            if include_fields:
                kwargs["_source_includes"] = include_fields
            if exclude_fields:
                kwargs["_source_excludes"] = exclude_fields
            if not include_fields and not exclude_fields:
                return self.esearch.get(index_name, doc_id)

            return self.esearch.get(index_name, doc_id, **kwargs)
        except Exception as xcp:
            self.handle_exception(xcp)
            return self.get_document(index_name, doc_id, include_fields, exclude_fields)
        

    def get_document_by_query(self, index_name, query, raw_res=False,
                              start=DEFAULT_START, max_size=DEFAULT_MAXSIZE,
                              include_fields: typing.Optional[list]=None, exclude_fields: typing.Optional[list]=None):
        """To retieve documents with a query.
        Params:
            - index_name: The index's name
            - query: dictionary query specification
            - raw_res: default False
                If true, return the entire response.
            - max_size: detault 100, number of documents to return
        """
        try:
            kwargs = {}
            if start:
                kwargs["from_"] = start
            if max_size:
                kwargs["size"] = max_size
            if include_fields:
                kwargs["_source_includes"] = include_fields
            if exclude_fields:
                kwargs["_source_excludes"] = exclude_fields
            res = self.esearch.search(index=index_name, body=query, **kwargs)
            if raw_res:
                return res
            return res['hits']['hits']
        except Exception as xcp:
            self.handle_exception(xcp)
            return self.get_document_by_query(index_name, query, raw_res, start, max_size, 
                                              include_fields, exclude_fields)


    def get_document_by_query_filter(self, index_name, query, raw_res=True, start=DEFAULT_START,
                                     max_size=DEFAULT_MAXSIZE, filter_spec: typing.Optional[list]=None,
                                     include_fields: typing.Optional[list]=None, exclude_fields: typing.Optional[list]=None):
        """To retieve documents with a query.
        Params:
            - index_name: The index's name
            - query: dictionary query specification
            - max_size: detault 100, number of documents to return
            - filter_spec: A list such as ['hits.hits._source']
                To reduce the payload ES return.
        """
        try:
            kwargs = {}
            if start:
                kwargs["from_"] = start
            if max_size:
                kwargs["size"] = max_size
            if filter_spec:
                kwargs["filter_path"] = filter_spec
            if include_fields:
                kwargs["_source_includes"] = include_fields
            if exclude_fields:
                kwargs["_source_excludes"] = exclude_fields

            res = self.esearch.search(index=index_name, body=query, **kwargs)
            if raw_res:
                return res
            return res['hits']['hits']
        except Exception as xcp:
            self.handle_exception(xcp)
            return self.get_document_by_query_filter(index_name, query, raw_res, start,
                                     max_size, filter_spec, include_fields, exclude_fields)
        

    def get_all_documents_by_scroll(self, index_name, query, scroll="5s"):
        """ To retrieve all documents in an index with a query """
        try:
            kwargs = {}
            if scroll:
                kwargs["scroll"]=scroll
            resp = self.esearch.search(index=index_name, body=query, **kwargs)
            docs = []
            while len(resp['hits']['hits']):
                # print('scroll size: ', len(resp['hits']['hits']))
                docs.extend(resp['hits']['hits'])
                old_scroll_id = resp['_scroll_id']
                resp = self.esearch.scroll(
                        scroll_id = old_scroll_id,
                        **kwargs
                    )
                
            return docs
        except Exception as xcp:
            self.handle_exception(xcp)
            return self.get_all_documents_by_scroll(index_name, query, scroll)
    
    def count_documents(self, index_name, query):
        """To count documents with a query.
        Params:
            - index_name: The index's name
            - query: dictionary query specification
        """
        try:
            return self.esearch.count(index=index_name, body=query)
        except Exception as xcp:
            self.handle_exception(xcp)
            return self.esearch.count(index=index_name, body=query)
        
    def index_document(self, index_name, doc_id, doc_content):
        """To 'insert' a document identified by doc_id.
        Params:
            - index_name: The index's name
            - doc_id: id of the document
            - doc_content: data dictionary
        If the document exists, its '_version' is increased by 1
        """
        try:
            return self.esearch.index(index_name, body=doc_content, id=doc_id)
        except Exception as xcp:
            self.handle_exception(xcp)
            return self.index_document(index_name, doc_id, doc_content)
        

    def create_document(self, index_name, doc_id, doc_content):
        """To 'create' a document with given doc_id, a unique identifier.
        Params:
            - index_name: The index's name
            - doc_id: id of the document
            - doc_content: data dictionary
        If the document already exists: ES throws ConflictError:
            status_code: 409,
            error: 'version_conflict_engine_exception',
            info: {dictionary contains a lot more details}
        """
        try:
            return self.esearch.create(index_name, doc_id, body=doc_content)
        except Exception as xcp:
            self.handle_exception(xcp)
            return self.create_document(index_name, doc_id, doc_content)
        

    def update_document(self, index_name, doc_id, doc_content):
        """Tp 'update' a document with the given body and reference ID.
        Params:
            - index_name: name of the index
            - doc_id: id of the document
            - doc_content: Must be a dictionary as below. Note the key `doc`
            {"doc":{"field_a": "value_a", "field_b": "value_b"}}
        """
        try:
            kwargs = {}
            kwargs["refresh"] = "wait_for"
            return self.esearch.update(index_name, doc_id, body=doc_content, **kwargs)
        except Exception as xcp:
            self.handle_exception(xcp)
            return self.update_document(index_name, doc_id, doc_content)


    def upsert_document(self, index_name, doc_id, doc_content):
        """To insert or update a document with the given body and reference doc ID
        Params:
            - index_name: name of the index
            - doc_id: id of the document
            - doc_content: json document for insert or update
        """
        try:
            doc = {
                "doc": doc_content,
                "doc_as_upsert": True
            }
            return self.esearch.update(index_name, doc_id, body=doc)
        except Exception as xcp:
            self.handle_exception(xcp)
            return self.upsert_document(index_name, doc_id, doc_content)
        

    def delete_document(self, index_name, doc_id):
        """To delete a document in an index with a given doc_id
        Params:
            - index_name: The index's name
            - doc_id: id of the document
        If the document is not available, ES throws NotFoundError:
            status_code: 404,
            error: ''
            info: {error dictionary will have the details}
        """
        try:
            return self.esearch.delete(index_name, doc_id)
        except Exception as xcp:
            self.handle_exception(xcp)
            return self.delete_document(index_name, doc_id)


    def delete_documents_by_query(self, index_name, query):
        """To delete documents by query on a given index
        Params:
            - index_name: name of the index
            - query: query to delete
        """
        try:
            return self.esearch.delete_by_query(index_name, body=query)
        except Exception as xcp:
            self.handle_exception(xcp)
            return self.delete_documents_by_query(index_name, query)
        

    def bulk_import(self, objects_list, index, doc_type):
        """
        To importing bulk data into index
        """
        try:
            print("index= ", index)
            return helpers.bulk(self.esearch, objects_list, index=index, doc_type=doc_type)
        except Exception as xcp:
            self.handle_exception(xcp)
            return self.bulk_import(objects_list, index, doc_type)
        
    
    def bulk_import2(self, actions):
        """To import bulk data into indices
        Params:
            - actions: as defined in https://www.elastic.co/guide/en/elasticsearch/client/python-api/current/client-helpers.html
        """
        try:
            return helpers.bulk(client=self.esearch, actions=actions)
        except Exception as xcp:
            self.handle_exception(xcp)
            return self.bulk_import2(actions)
        
