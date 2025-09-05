"""
FDN Authentication Client using httpx with Redis caching and AWS Secrets Manager integration.

Features:
- Token generation and authentication with FDN services
- Redis-based token caching with configurable TTL
- AWS Secrets Manager integration for secure credential storage
- Automatic token refresh

Requires Python 3.11 or higher
"""
from __future__ import annotations

import sys
import os
import json
import base64
import uuid
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional, TypedDict, NotRequired, Any, Literal, Dict, List, Union
from collections.abc import Mapping

import httpx
from pydantic import BaseModel, Field

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import Redis and AWS utilities from the common library
try:
    from ascendops_commonlib.aws_utils.secrets_manager_util import SecretsManagerUtil
    from ascendops_commonlib.datastores.redis_util import RedisCache
except ImportError as e:
    logger.warning(f"Failed to import common library utilities: {e}")
    SecretsManagerUtil = None
    RedisCache = None

class FDNCredential(BaseModel):
    """FDN credential model with AWS Secrets Manager integration"""
    client_id: str
    client_secret: str
    domain: str
    username: Optional[str] = None
    
    @property
    def basic_token(self) -> str:
        """Generate basic auth token from client_id and client_secret"""
        credentials = f"{self.client_id}:{self.client_secret}"
        return base64.b64encode(credentials.encode()).decode()
    
    @classmethod
    async def from_aws_secret(cls, secret_name: str, region_name: Optional[str] = None) -> 'FDNCredential':
        """Load credentials from AWS Secrets Manager"""
        if not SecretsManagerUtil:
            raise RuntimeError("AWS Secrets Manager utilities not available")

        secrets_util = SecretsManagerUtil(region_name=region_name or "us-east-1")
        secret = secrets_util.get_secret(secret_name)
        if not secret:
            raise ValueError(f"Secret {secret_name} not found")
            
        if isinstance(secret, str):
            secret_data = json.loads(secret)
        else:
            secret_data = secret
            
        return cls(
            client_id=secret_data['client_id'],
            client_secret=secret_data['client_secret'],
            domain=secret_data.get('domain', ''),
            username=secret_data.get('username')
        )

class TokenResponse(BaseModel):
    """Token response model with expiration tracking"""
    access_token: str = Field(..., alias="access_token")
    token_type: str = Field(..., alias="token_type")
    expires_in: int = Field(..., alias="expires_in")
    scope: str = Field(default="")
    expires_at: Optional[datetime] = None
    
    def __init__(self, **data):
        super().__init__(**data)
        if not self.expires_at and 'expires_in' in data:
            self.expires_at = datetime.utcnow() + timedelta(seconds=data['expires_in'])
    
    def is_expired(self) -> bool:
        """Check if the token is expired or about to expire soon"""
        if not self.expires_at:
            return True
        return datetime.utcnow() >= (self.expires_at - timedelta(seconds=60))

class FDNCredentialManager:
    """Manages FDN credentials with Redis caching and AWS Secrets Manager integration"""
    
    def __init__(
        self, 
        base_url: str = "https://da-saas-npsvhreanrlz.mn-na-test.preprod-ascend-na.io",
        redis_cache: Optional[RedisCache] = None,
        cache_ttl: int = 300
    ) -> None:
        """Initialize the FDN credential manager
        
        Args:
            base_url: Base URL for the FDN auth service
            redis_cache: Optional RedisCache instance for token caching
            cache_ttl: Time to live for cached tokens in seconds
        """
        self.base_url = base_url.rstrip('/')
        self.credentials: Dict[str, FDNCredential] = {}
        self.client = httpx.AsyncClient(timeout=30.0)
        self.redis_cache = redis_cache
        self.cache_ttl = cache_ttl
        
        if redis_cache and not isinstance(redis_cache, RedisCache):
            raise ValueError("redis_cache must be an instance of RedisCache")
            
        logger.info(f"Initialized FDNCredentialManager with base_url={self.base_url} and {'Redis cache' if redis_cache else 'no cache'}")
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()
    
    async def add_credential_from_secret(self, name: str, secret_name: str, region_name: Optional[str] = None) -> None:
        """Add a credential from AWS Secrets Manager
        
        Args:
            name: Name to identify this credential
            secret_name: Name of the secret in AWS Secrets Manager
            region_name: AWS region name (optional)
            
        Raises:
            RuntimeError: If AWS Secrets Manager is not available
            ValueError: If the secret is invalid or missing required fields
        """
        credential = await FDNCredential.from_aws_secret(secret_name, region_name)
        self.credentials[name] = credential
        logger.info(f"Added credential '{name}' from AWS secret '{secret_name}'")
    
    def _get_cache_key(self, credential_name: str) -> str:
        """Generate a cache key for a credential"""
        return f"AUTH:FDN:TOKEN:{credential_name}"
    
    async def _get_cached_token(self, credential_name: str) -> Optional[TokenResponse]:
        """Get a cached token if available and not expired
        
        Returns:
            TokenResponse if a valid token is found in cache, None otherwise
        """
        if not self.redis_cache:
            return None
            
        try:
            cache_key = self._get_cache_key(credential_name)
            cached_data = await self.redis_cache.get(cache_key)
            if not cached_data:
                return None
                
            token_data = json.loads(cached_data)
            token = TokenResponse(**token_data)
            
            if not token.is_expired():
                logger.debug(f"Using cached token for {credential_name}")
                return token
                
            logger.debug(f"Cached token for {credential_name} is expired")
            return None
            
        except Exception as e:
            logger.warning(f"Error reading from cache: {e}", exc_info=True)
            return None
    
    async def _cache_token(self, credential_name: str, token: TokenResponse) -> None:
        """Cache a token"""
        if not self.redis_cache:
            return
            
        try:
            cache_key = self._get_cache_key(credential_name)
            token_data = token.dict()
            await self.redis_cache.set(
                cache_key,
                json.dumps(token_data),
                ex=self.cache_ttl
            )
            logger.debug(f"Cached token for {credential_name} with TTL {self.cache_ttl}s")
        except Exception as e:
            logger.warning(f"Error caching token: {e}", exc_info=True)
    
    async def get_token(self, credential_name: str) -> str:
        """Get an access token for the specified credential
        
        Args:
            credential_name: Name of the credential to get a token for
            
        Returns:
            Access token as a string
            
        Raises:
            KeyError: If the credential is not found
            httpx.HTTPStatusError: If the token request fails
        """
        if credential_name not in self.credentials:
            raise KeyError(f"Credential '{credential_name}' not found")
            
        # Try to get a cached token first
        cached_token = await self._get_cached_token(credential_name)
        if cached_token:
            return cached_token.access_token
            
        # No valid cached token, request a new one
        credential = self.credentials[credential_name]
        token = await self._fetch_token(credential)
        
        # Cache the new token
        await self._cache_token(credential_name, token)
        
        return token.access_token
    
    async def _fetch_token(self, credential: FDNCredential) -> TokenResponse:
        """Fetch a new access token from the FDN auth service"""
        url = f"{self.base_url}/oauth/token"
        auth = (credential.client_id, credential.client_secret)
        data = {
            "grant_type": "client_credentials",
            "scope": "openid"
        }
        
        try:
            logger.info(f"Requesting new token from {url}")
            response = await self.client.post(
                url,
                auth=auth,
                data=data,
                timeout=30.0
            )
            response.raise_for_status()
            
            token_data = response.json()
            token = TokenResponse(**token_data)
            logger.info(f"Successfully obtained token expiring at {token.expires_at}")
            return token
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error fetching token: {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Error fetching token: {e}", exc_info=True)
            raise
    
    def add_credential(self, name: str, client_id: str, client_secret: str, domain: str, username: Optional[str] = None) -> None:
        """Add a credential directly
        
        Args:
            name: Name to identify this credential
            client_id: OAuth client ID
            client_secret: OAuth client secret
            domain: Domain for the credential
            username: Optional username
        """
        self.credentials[name] = FDNCredential(
            client_id=client_id,
            client_secret=client_secret,
            domain=domain,
            username=username
        )
        logger.info(f"Added credential '{name}' for domain '{domain}'")
    
    def _decode_basic_token(self, basic_token: str) -> tuple[str, str, str]:
        """Decode a basic auth token into username, password, and domain
        
        Returns:
            Tuple of (username, password, domain)
        """
        try:
            decoded = base64.b64decode(basic_token).decode('utf-8')
            username, password = decoded.split(':', 1)
            domain = username.split('@')[-1] if '@' in username else ''
            return username, password, domain
        except Exception as e:
            raise ValueError(f"Invalid basic token format: {e}")
    
    async def get_authenticated_headers(self, credential_name: str, correlation_id: Optional[str] = None) -> dict[str, str]:
        """Get headers with a valid access token
        
        Args:
            credential_name: Name of the credential to use
            correlation_id: Optional correlation ID for request tracing
            
        Returns:
            Dictionary with authentication headers including:
            - Authorization: Bearer token
            - Content-Type: application/json
            - X-User-Domain: Domain from the credential
            - X-Correlation-ID: Correlation ID if provided
            
        Raises:
            KeyError: If the credential is not found
            httpx.HTTPStatusError: If token request fails
        """
        if credential_name not in self.credentials:
            raise KeyError(f"Credential '{credential_name}' not found")
            
        credential = self.credentials[credential_name]
        token = await self.get_token(credential_name)
        
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json',
            'X-User-Domain': credential.domain
        }
        
        if correlation_id:
            headers['X-Correlation-ID'] = correlation_id
            
        return headers
                    'status_code': response.status_code,
                    'correlation_id': correlation_id,
                    'response_time_ms': response_time,
                    'error': response.text,
                    'username': cred['username'],
                    'domain': cred['domain']
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'correlation_id': correlation_id,
                'username': cred['username'],
                'domain': cred['domain']
            }
    
    async def test_all_credentials(self) -> dict[str, list[dict[str, str | float]]]:
        """Test all loaded credentials"""
        results = {'success': [], 'failed': []}
        
        for name in self.credentials:
            result = await self.get_token(name)
            if result['success']:
                results['success'].append({
                    'name': name,
                    'domain': result['domain'],
                    'response_time_ms': result['response_time_ms']
                })
            else:
                results['failed'].append({
                    'name': name,
                    'domain': result['domain'],

# Example usage
async def main():
    # Initialize the client
    client = FDNCredentialManager()
    
    try:
        # Get secret name from environment or use default
        secret_name = os.getenv("FDN_CREDENTIALS_SECRET", "fdn/credentials")
        
        # Option 1: Load from AWS Secrets Manager (production)
        try:
            print(f"Loading credentials from AWS Secrets Manager: {secret_name}")
            await client.load_credentials_from_secret(secret_name)
        except Exception as e:
            print(f"Warning: Failed to load from AWS Secrets Manager: {e}")
            # Fallback to environment variable if AWS fails
            fallback_json = os.getenv("FDN_CREDENTIALS_JSON")
            if fallback_json:
                print("Falling back to credentials from environment variable")
                client._process_credentials(fallback_json)
            else:
                raise RuntimeError("No valid credentials source found")
        
        if not client.credentials:
            print("No credentials available to test")
            return
            
        # Test all credentials
        print("\nTesting all credentials...")
        results = await client.test_all_credentials()
        
        # Print results
        print(f"\n✅ Successful: {len(results['success'])}")
        for cred in results['success']:
            print(f"- {cred['name']} ({cred['domain']}): {cred['response_time_ms']:.2f}ms")
        
        if results['failed']:
            print(f"\n❌ Failed: {len(results['failed'])}")
            for cred in results['failed']:
                print(f"- {cred['name']} ({cred['domain']}): {cred['error']}")
        
        # Example: Get a token for a specific credential
        if results['success']:
            cred_name = results['success'][0]['name']
            print(f"\nGetting token for {cred_name}...")
            token_result = await client.get_token(cred_name)
            if token_result['success']:
                token_data = token_result['token']
                print(f"Access token: {token_data['access_token'][:30]}...")
                print(f"Expires in: {token_data.get('expires_in', 'N/A')}s")
                print(f"Token type: {token_data.get('token_type', 'N/A')}")
                
                # Return the token data for use in other functions
                return token_data
    
    finally:
        # Clean up
        await client.close()

if __name__ == "__main__":
    asyncio.run(main())
