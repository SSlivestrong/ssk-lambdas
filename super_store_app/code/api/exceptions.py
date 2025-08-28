class Error(Exception):
    '''Base class for other exceptions'''

class OauthTokenError(Error):
    '''Raise when having communication issue with oauth'''

class CryptoServerError(Error):
    '''Raise when having communication issue with crypto server'''

class S3Error(Error):
    '''Raise when having communication issue with S3'''