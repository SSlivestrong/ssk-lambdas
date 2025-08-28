"""
Use this code to upload PEM files which are used to connect to
AWS MSK cluster.
"""
import json
import os
import logging
from urllib.parse import urlparse
import boto3
from boto3.session import Session
import common.app_config as app_config

log = logging.getLogger(app_config.APP_NAME)

HEALTH_CHECK_FILE = os.path.join(app_config.APP_DIR, "health_check")

# ssl_cafile, ssl_certfile, ssl_keyfile used to construct KafkaProducer, KafkaConsumer
CERT_DIR = os.path.join(app_config.APP_DIR, "certs")

CACERT_LOCAL_PATH = os.path.join(CERT_DIR, app_config.CACERT_FILE_NAME)
PUBLIC_CERT_LOCAL_PATH = os.path.join(CERT_DIR, app_config.PUBLIC_CERT_FILE_NAME)
PRIVATE_KEY_LOCAL_PATH = os.path.join(CERT_DIR, app_config.PRIVATE_KEY_FILE_NAME)


def download_pem_files():
    """Retrieve PEM files from s3 bucket
    """
    # s3_resource = get_s3_assumed_role_resource(INTERNAL_CLIENT_ALIAS)
    s3_resource = boto3.resource('s3', region_name=app_config.DEFAULT_REGION)
    the_bucket = s3_resource.Bucket(app_config.MSK_CERT_BUCKET_NAME)

    log.info("MSK_CERT_BUCKET_NAME: %s", app_config.MSK_CERT_BUCKET_NAME)
    log.info("CACERT Local:%s|S3:%s", CACERT_LOCAL_PATH, app_config.CACERT_S3_PATH)
    log.info("PUBCERT Local:%s|S3:%s", PUBLIC_CERT_LOCAL_PATH, app_config.PUBLIC_CERT_S3_PATH)
    log.info("PRICERT Local:%s|S3:%s", PRIVATE_KEY_LOCAL_PATH, app_config.PRIVATE_KEY_S3_PATH)

    if not os.path.isfile(CACERT_LOCAL_PATH):
        with open(CACERT_LOCAL_PATH, "wb") as cacert_file:
            the_bucket.download_fileobj(app_config.CACERT_S3_PATH, cacert_file)

    if not os.path.isfile(PUBLIC_CERT_LOCAL_PATH):
        with open(PUBLIC_CERT_LOCAL_PATH, "wb") as public_cert_file:
            the_bucket.download_fileobj(app_config.PUBLIC_CERT_S3_PATH, public_cert_file)

    if not os.path.isfile(PRIVATE_KEY_LOCAL_PATH):
        with open(PRIVATE_KEY_LOCAL_PATH, "wb") as private_key_file:
            the_bucket.download_fileobj(app_config.PRIVATE_KEY_S3_PATH, private_key_file)


def upload_using_sse_kms(pem_abs_path, ssekms_key_id):
    """To upload a PEM file from laptop to MSK_CERT_BUCKET_NAME.
    This is for testing. Get this from AWS
    SSEKMS_KEY_ID = "arn:aws:kms:us-east-1:994075455914:key/69b04300-b00d-4ed0-8368-27a9bad09a0d"
    """
    session = boto3.Session(profile_name="mdlc-dev")
    s3_client = session.client('s3')
    response = s3_client.upload_file(pem_abs_path,
                                     app_config.MSK_CERT_BUCKET_NAME, 'certs/dev_go_acm_cacert.pem',
                                     ExtraArgs={"ServerSideEncryption": "aws:kms", "SSEKMSKeyId": ssekms_key_id})
    print("Uploading S3 object with SSE-KMS", response)


def get_credentials(client_alias):
    """returns credentials
    :param str client_alias: client alias
    :param str receipient: recipient message
    :return: se client
    """
    # session = boto3.Session(profile_name="mdlcdev")
    # sts_client = session.client('sts', region_name=DEFAULT_REGION,
    #                           endpoint_url=f"https://sts.{DEFAULT_REGION}.amazonaws.com")
    # role_arn = "arn:aws:iam::994075455914:role/att-ascend-go-developer-role"
    if app_config.IAM_PROFILE:
        sts_client = boto3.Session(profile_name=app_config.IAM_PROFILE) \
            .client('sts', region_name=app_config.DEFAULT_REGION, endpoint_url=f"https://sts.{app_config.DEFAULT_REGION}.amazonaws.com")
    else:
        sts_client = boto3.client('sts', region_name=app_config.DEFAULT_REGION,
                                  endpoint_url=f"https://sts.{app_config.DEFAULT_REGION}.amazonaws.com")

    role_arn = f"arn:aws:iam::{app_config.AWS_ACCOUNT}:role/{app_config.EXEC_STAGE}-{client_alias}-sagemaker"
    log.info("s3_util get_credentials role_arn to assume %s", role_arn)
    assumed_role_obj = sts_client.assume_role(
        RoleArn=role_arn,
        RoleSessionName="AssumeS3Session1"
    )

    role_credentials = assumed_role_obj["Credentials"]
    return role_credentials


def get_s3_assumed_role_client(client_alias):
    """to get the s3 client for an assumed role
    
    Params:
     - client_alias: alias of the client that is used to identify resources
     - region: AWS region
    
    Returns:
     - s3_client
    """
    role_credentials = get_credentials(client_alias)
    boto3_session = Session(
        aws_access_key_id=role_credentials['AccessKeyId'],
        aws_secret_access_key=role_credentials['SecretAccessKey'],
        aws_session_token=role_credentials['SessionToken'],
    )
    s3_client = boto3_session.client('s3', app_config.DEFAULT_REGION)
    return s3_client


def get_s3_assumed_role_resource(client_alias):
    """to get the s3 client for an assumed role
    Params:
     - client_alias: alias of the client that is used to identify resources
     - region: AWS region
    Returns:
     - s3_resource
    """
    role_credentials = get_credentials(client_alias)
    s3_resource = boto3.resource(
        service_name="s3",
        aws_access_key_id=role_credentials['AccessKeyId'],
        aws_secret_access_key=role_credentials['SecretAccessKey'],
        aws_session_token=role_credentials['SessionToken'],
    )
    return s3_resource


def get_all_s3_files(bucket_name, file_path):
    """to get all the files for the given s3 bucket and path.
    
    Params:
     - bucket_name: s3 bucket name.
     - file_path: s3 object key or path of the folder.
    
    Returns:
     - list of contents in the response.
    """
    s3_client = boto3.client("s3")
    paginator = s3_client.get_paginator('list_objects_v2')
    pages = paginator.paginate(Bucket=bucket_name, Prefix=file_path)
    response = list()
    try:
        for page in pages:
            response.extend(page["Contents"])
    except Exception as ex:
        log.error("Method::get_all_s3_files :: Couldn't read files from location:: s3://%s/%s. Exception::%s.",
                  bucket_name, file_path, ex)
    return response

def get_s3_client_bucket_name(client_alias):
    """ construct s3 client bucket name from client alias """
    s3_bucket = f"{app_config.EXEC_STAGE}-{client_alias}-{app_config.DEFAULT_REGION}-{app_config.AWS_ACCOUNT}"
    return s3_bucket

def get_s3_client_sse(client_alias):
    """ construct s3 client sse name from client alias """
    return f"arn:aws:kms:{app_config.DEFAULT_REGION}:{app_config.AWS_ACCOUNT}:alias/{app_config.EXEC_STAGE}-{client_alias}-cmk"

def copy_all_files_between_prefixes(s3_client, client_sse, s3_bucket, source_s3_prefix, dest_s3_prefix):
    """  Copy files from source s3 prefix to another destination s3 prefix within the same bucket
        Params:
            s3_client: boto3 client for s3
            client_sse: sse for s3 bucket 
            s3_bucket: s3 bucket 
            source_s3_prefix: source prefix to pull files from
            dest_s3_prefix: destination prefix to copy files to
    """
    # get files from source prefix 
    files = get_all_s3_files(s3_bucket, source_s3_prefix)
    for file in files:
        # get file name from file key
        file_name = file["Key"].split("/")[-1]

        # create destination key
        dest_key = dest_s3_prefix + "/" + file_name

        copy_file(s3_client, client_sse, s3_bucket, file["Key"], dest_key)


def copy_file(s3_client, client_sse, s3_bucket, source_s3_key, dest_s3_key):
    """  Copy file from source s3 key to destination s3 key within the same bucket
        Params:
            s3_client: boto3 client for s3
            client_sse: sse for s3 bucket 
            s3_bucket: s3 bucket 
            source_s3_key: source key of file
            dest_s3_key: destination key of file
    """
    copy_source = {
        'Bucket': s3_bucket,
        'Key': source_s3_key
    }
    s3_client.copy(CopySource=copy_source, Bucket=s3_bucket, Key=dest_s3_key,
            ExtraArgs={"ServerSideEncryption": "aws:kms", "SSEKMSKeyId": client_sse})
    
def read_s3_file(s3_client, s3_file_location):
    s3_obj_target = urlparse(s3_file_location)
    s3_bucket_name_target = s3_obj_target[1]
    s3_file_path_t = s3_obj_target[2]
    s3_file_target = s3_file_path_t[1:len(s3_file_path_t)]
    object = s3_client.Object(s3_bucket_name_target, s3_file_target)
    file_content = object.get()['Body'].read().decode('utf-8')
    data = json.loads(file_content)
    return data