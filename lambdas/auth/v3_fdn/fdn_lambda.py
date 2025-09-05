#!/usr/bin/env python3
"""
FDN Authentication Lambda Function

This Lambda function provides basic authentication for FDN services.
It uses the common authentication library for token management with Redis caching.

Environment Variables:
- FDN_SECRET_NAME: AWS Secrets Manager secret containing FDN credentials
- AWS_REGION: AWS region for Secrets Manager (default: us-east-1)
- REDIS_ENABLED: Enable Redis caching (default: true)
- CACHE_TTL_SECONDS: Cache TTL in seconds (default: 300)

Example Event:
{
    "action": "get_token",
    "domain_key": "AOVERIZON",
    "correlation_id": "optional-correlation-id"
}

Returns:
{
    "success": true,
    "access_token": "bearer_token_here",
    "expires_in": 3600,
    "token_type": "Bearer"
}
"""
import json
import os
import logging
import asyncio
from typing import Dict, Any, Optional

# Import from common library
from ascendops_commonlib.auth_services.fdn.fdn_client import FDNClient
from ascendops_commonlib.auth_services.fdn.fdn_token_service import fdn_lambda_client, FDNTokenService

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

class FDNLambdaHandler:
    """FDN Lambda function handler using common authentication library."""

    def __init__(self):
        """Initialize FDN Lambda handler."""
        self.secret_name = os.getenv("FDN_SECRET_NAME", "fdn/credentials")
        self.aws_region = os.getenv("AWS_REGION", "us-east-1")
        self.redis_enabled = os.getenv("REDIS_ENABLED", "true").lower() == "true"
        self.cache_ttl = int(os.getenv("CACHE_TTL_SECONDS", "300"))

        # Initialize FDN client with Lambda optimizations
        self.fdn_client = FDNClient()
        self.is_initialized = False

        logger.info(f"Initialized FDN Lambda handler with secret: {self.secret_name}")

    async def _ensure_initialized(self):
        """Ensure HTTP clients are initialized for Lambda."""
        if not self.is_initialized:
            # Initialize module-level HTTP clients for Lambda
            # fdn_lambda_client is already imported at module level

            # Warm up the client if needed
            logger.info("FDN Lambda handler initialized")
            self.is_initialized = True

    async def get_token(self, domain_key: str, correlation_id: Optional[str] = None) -> Dict[str, Any]:
        """Get FDN access token for specific domain.

        Args:
            domain_key: Domain key (e.g., "AOVERIZON", "AOTMOBILE")
            correlation_id: Optional correlation ID for tracing

        Returns:
            Token response dictionary
        """
        try:
            await self._ensure_initialized()

            logger.info(f"Getting FDN token for domain_key: {domain_key}, correlation_id: {correlation_id}")

            # Get token using the common library
            token_data = await self.fdn_client.get_token_data_from_secret(
                secret_name=self.secret_name,
                domain_key=domain_key,
                region=self.aws_region,
                is_lambda=True
            )

            logger.info(f"Successfully obtained FDN token for {domain_key}")

            return {
                "success": True,
                "access_token": token_data["access_token"],
                "expires_in": token_data.get("expires_in", 3600),
                "token_type": token_data.get("token_type", "Bearer"),
                "domain_key": domain_key,
                "correlation_id": correlation_id
            }

        except Exception as e:
            logger.error(f"Failed to get FDN token for {domain_key}: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "domain_key": domain_key,
                "correlation_id": correlation_id
            }

    async def get_token_tuple(self, domain_key: str, correlation_id: Optional[str] = None) -> Dict[str, Any]:
        """Get FDN token in tuple format (compatible with Crosscore).

        Args:
            domain_key: Domain key (e.g., "AOVERIZON", "AOTMOBILE")
            correlation_id: Optional correlation ID

        Returns:
            Tuple format response
        """
        try:
            await self._ensure_initialized()

            logger.info(f"Getting FDN token tuple for domain_key: {domain_key}")

            # Get token tuple using the common library
            token, error = await self.fdn_client.get_token_tuple_from_secret(
                secret_name=self.secret_name,
                domain_key=domain_key,
                region=self.aws_region,
                is_lambda=True
            )

            if error:
                logger.error(f"Failed to get FDN token tuple for {domain_key}: {error}")
                return {
                    "success": False,
                    "error": error,
                    "domain_key": domain_key,
                    "correlation_id": correlation_id
                }

            logger.info(f"Successfully obtained FDN token tuple for {domain_key}")

            return {
                "success": True,
                "access_token": token,
                "domain_key": domain_key,
                "correlation_id": correlation_id
            }

        except Exception as e:
            logger.error(f"Failed to get FDN token tuple for {domain_key}: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "domain_key": domain_key,
                "correlation_id": correlation_id
            }

    async def validate_token(self, token: str, domain_key: str, correlation_id: Optional[str] = None) -> Dict[str, Any]:
        """Validate FDN token expiry.

        Args:
            token: Token to validate
            domain_key: Domain key for context
            correlation_id: Optional correlation ID

        Returns:
            Validation result
        """
        try:
            await self._ensure_initialized()

            logger.info(f"Validating FDN token for domain_key: {domain_key}")

            # Use FDN client validation methods
            # This uses the token validation logic from our common library

            # For Lambda flow, check if token needs refresh
            async with FDNTokenService(is_lambda=True) as service:
                # Get current token data to validate
                current_token = await self.fdn_client.get_token_data_from_secret(
                    secret_name=self.secret_name,
                    domain_key=domain_key,
                    region=self.aws_region,
                    is_lambda=True
                )

                # Compare with provided token
                is_valid = current_token.get("access_token") == token

                return {
                    "success": True,
                    "valid": is_valid,
                    "domain_key": domain_key,
                    "correlation_id": correlation_id
                }

        except Exception as e:
            logger.error(f"Failed to validate FDN token: {str(e)}", exc_info=True)
            return {
                "success": False,
                "valid": False,
                "error": str(e),
                "domain_key": domain_key,
                "correlation_id": correlation_id
            }

# Global handler instance for Lambda reuse
fdn_handler = None

def get_handler():
    """Get or create FDN handler instance."""
    global fdn_handler
    if fdn_handler is None:
        fdn_handler = FDNLambdaHandler()
    return fdn_handler

async def handle_event(event: Dict[str, Any], context) -> Dict[str, Any]:
    """Handle Lambda event asynchronously.

    Args:
        event: Lambda event dictionary
        context: Lambda context object

    Returns:
        Response dictionary
    """
    handler = get_handler()

    try:
        action = event.get("action", "get_token")
        domain_key = event.get("domain_key", "AOVERIZON")  # Default domain
        correlation_id = event.get("correlation_id")

        logger.info(f"Processing FDN Lambda request: action={action}, domain_key={domain_key}, correlation_id={correlation_id}")

        if action == "get_token":
            return await handler.get_token(domain_key, correlation_id)
        elif action == "get_token_tuple":
            return await handler.get_token_tuple(domain_key, correlation_id)
        elif action == "validate_token":
            token = event.get("token")
            if not token:
                return {
                    "success": False,
                    "error": "Token required for validation",
                    "domain_key": domain_key,
                    "correlation_id": correlation_id
                }
            return await handler.validate_token(token, domain_key, correlation_id)
        else:
            return {
                "success": False,
                "error": f"Unsupported action: {action}",
                "domain_key": domain_key,
                "correlation_id": correlation_id
            }

    except Exception as e:
        logger.error(f"FDN Lambda error: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "domain_key": event.get("domain_key"),
            "correlation_id": event.get("correlation_id")
        }

def lambda_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """AWS Lambda handler entry point.

    Args:
        event: Lambda event
        context: Lambda context

    Returns:
        Response dictionary
    """
    # Run async handler
    return asyncio.run(handle_event(event, context))

# For local testing
if __name__ == "__main__":
    async def test():
        # Test event
        test_event = {
            "action": "get_token",
            "domain_key": "AOVERIZON",
            "correlation_id": "test-123"
        }

        # Mock context
        class MockContext:
            pass

        context = MockContext()

        # Run test
        result = await handle_event(test_event, context)
        print("Test Result:")
        print(json.dumps(result, indent=2, default=str))

    asyncio.run(test())
