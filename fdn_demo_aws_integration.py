#!/usr/bin/env python3
"""
Demo script showing AWS Secrets Manager integration
This demonstrates how the credentials would be tested from AWS
"""

import json
import base64
import requests
import uuid
from datetime import datetime

def simulate_aws_secret_retrieval():
    """
    Simulate retrieving our credentials from AWS Secrets Manager
    This shows the format that would be returned from AWS
    """
    # This is the format we would store in AWS Secrets Manager
    aws_secret_data = {
        "AOVERIZON": "{\"basic_token\": \"YXNjZW5kLW9wcy1yZWFsLXRpbWUtc3VwcG9ydEB2ZXJpem9uLWZkbi5jb206bW1UPzVDRklITEptTlohbl4sQyFZcFAyQF9KKn12amk=\"}",
        "AOTMOBILE": "{\"basic_token\": \"YXNjZW5kLW9wcy1yZWFsLXRpbWUtc3VwcG9ydEB0bW9iaWxlLWZkbi5jb206Wj85I1kzNVh2I0lLLjY4Tng4IURTPVtCUnk3e2VTVlo=\"}",
        "AOUSCELLULAR": "{\"basic_token\": \"YXNjZW5kLW9wcy1yZWFsLXRpbWUtc3VwcG9ydEB1c2NlbGx1bGFyLWZkbi5jb206OW9+W1t7WGFGaywpfkEkQENnb2tVemFZakI+Jlc/MHQ=\"}",
        "AOATT": "{\"basic_token\": \"YXNjZW5kLW9wcy1yZWFsLXRpbWUtc3VwcG9ydEBhdHQtZmRuLmNvbTpuRU9QR2FyfWk2Q1RfK0FIUGI7X2YhUUY9VDUoZmttIQ==\"}",
        "AOBUREAUCOMPLIANCE": "{\"basic_token\": \"YXNjZW5kLW9wcy1yZWFsLXRpbWUtc3VwcG9ydEBidXJlYXVjb21wbGlhbmNlZW5naW5lY29zdHVtZXIuY29tOjRBKmU2TzUzTlpVMjE5KGtGNjk/aj1ZNTJPOE1FR0Ew\"}"
    }
    
    return aws_secret_data

def decode_basic_token(basic_token):
    """
    Decode a basic token to extract username and password
    """
    try:
        decoded = base64.b64decode(basic_token).decode('utf-8')
        username, password = decoded.split(':', 1)
        domain = username.split('@')[1] if '@' in username else None
        return username, password, domain
    except Exception as e:
        print(f"❌ Error decoding token: {e}")
        return None, None, None

def test_credential_from_aws(basic_token, domain=None):
    """
    Test a credential retrieved from AWS against the API
    """
    username, password, extracted_domain = decode_basic_token(basic_token)
    
    if not username or not password:
        return {
            'success': False,
            'error': 'Failed to decode basic token'
        }
    
    test_domain = domain or extracted_domain
    
    if not test_domain:
        return {
            'success': False,
            'error': 'No domain available for testing'
        }
    
    url = "https://da-saas-npsvhreanrlz.mn-na-test.preprod-ascend-na.io/v1/tokens/create"
    correlation_id = str(uuid.uuid4())
    
    headers = {
        'Content-Type': 'application/json',
        'X-User-Domain': test_domain,
        'X-Correlation-Id': correlation_id,
        'Authorization': f'Basic {basic_token}'
    }
    
    try:
        response = requests.post(url, headers=headers, timeout=30)
        
        result = {
            'success': response.status_code == 200,
            'status_code': response.status_code,
            'correlation_id': correlation_id,
            'timestamp': datetime.now().isoformat(),
            'username': username,
            'domain': test_domain,
            'response_time_ms': response.elapsed.total_seconds() * 1000
        }
        
        try:
            result['response_body'] = response.json()
        except:
            result['response_body'] = response.text
            
        return result
        
    except requests.exceptions.RequestException as e:
        return {
            'success': False,
            'error': str(e),
            'correlation_id': correlation_id,
            'timestamp': datetime.now().isoformat(),
            'username': username,
            'domain': test_domain
        }

def main():
    """
    Demo of testing credentials as if retrieved from AWS Secrets Manager
    """
    print("AWS Secrets Manager Integration Demo")
    print("=" * 60)
    print("🔍 This demonstrates how credentials would be tested from AWS")
    print("   (Simulating secret retrieval due to expired AWS credentials)")
    
    # Simulate getting data from AWS
    print(f"\n📡 Simulating: get_secret('uat-fdn-secrets', 'us-east-1')")
    secret_data = simulate_aws_secret_retrieval()
    
    print(f"✅ Retrieved {len(secret_data)} credentials from 'AWS'")
    
    successful_tests = []
    failed_tests = []
    
    # Test each credential
    for key, value in secret_data.items():
        print(f"\n{'='*60}")
        print(f"Testing: {key}")
        print("=" * 60)
        
        try:
            # Parse the JSON value to extract basic_token
            token_data = json.loads(value)
            basic_token = token_data.get('basic_token')
            
            if not basic_token:
                print(f"❌ No basic_token found for {key}")
                failed_tests.append(key)
                continue
            
            # Decode and display info
            username, password, domain = decode_basic_token(basic_token)
            print(f"Username: {username}")
            print(f"Domain: {domain}")
            print(f"Basic Token: {basic_token[:50]}...")
            
            # Test the credential
            print(f"\n🧪 Testing credential against API...")
            result = test_credential_from_aws(basic_token, domain)
            
            if result['success']:
                print(f"✅ SUCCESS - Status: {result['status_code']}")
                print(f"   Response time: {result['response_time_ms']:.2f}ms")
                print(f"   Correlation ID: {result['correlation_id']}")
                
                if 'response_body' in result and isinstance(result['response_body'], dict):
                    token_info = result['response_body'].get('token', {})
                    if token_info:
                        print(f"   Token expires in: {token_info.get('expires_in', 'N/A')} seconds")
                        print(f"   Token type: {token_info.get('token_type', 'N/A')}")
                
                successful_tests.append(key)
            else:
                print(f"❌ FAILED - Status: {result.get('status_code', 'N/A')}")
                print(f"   Correlation ID: {result['correlation_id']}")
                if 'error' in result:
                    print(f"   Error: {result['error']}")
                elif 'response_body' in result:
                    print(f"   Response: {result['response_body']}")
                
                failed_tests.append(key)
            
        except Exception as e:
            print(f"❌ Error testing {key}: {e}")
            failed_tests.append(key)
    
    # Summary
    print(f"\n{'='*60}")
    print("📊 AWS INTEGRATION TEST SUMMARY")
    print("=" * 60)
    print(f"✅ Successful: {len(successful_tests)} - {successful_tests}")
    print(f"❌ Failed: {len(failed_tests)} - {failed_tests}")
    print(f"📈 Success Rate: {len(successful_tests)}/{len(successful_tests) + len(failed_tests)} ({len(successful_tests)/(len(successful_tests) + len(failed_tests))*100:.1f}%)")
    
    print(f"\n{'='*60}")
    print("🚀 NEXT STEPS FOR AWS INTEGRATION:")
    print("=" * 60)
    print("1. Configure AWS credentials:")
    print("   aws configure")
    print("   # or set AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY")
    print()
    print("2. Upload credentials to AWS:")
    print("   python3 upload_aws_credentials.py")
    print()
    print("3. Test from AWS:")
    print("   python3 test_aws_credentials.py")
    print()
    print("4. Use in your application:")
    print("   secret_data = get_secret('uat-fdn-secrets')")
    print("   basic_token = json.loads(secret_data['AOVERIZON'])['basic_token']")

if __name__ == "__main__":
    main()
