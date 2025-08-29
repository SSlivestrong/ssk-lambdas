#!/usr/bin/env python3
"""
Test specific credentials from JSON format
Tests the provided credential tokens against the API
"""

import json
import base64
import requests
import uuid
from datetime import datetime

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

def test_credential(basic_token, domain=None):
    """
    Test a credential against the API
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
    Test the provided credentials
    """
    print("Testing Provided JSON Credentials")
    print("=" * 60)
    
    # The credentials provided by the user
    credentials_json = """{"AOVERIZON":"{\\\"basic_token\\\": \\\"YXNjZW5kLW9wcy1yZWFsLXRpbWUtc3VwcG9ydEB2ZXJpem9uLWZkbi5jb206bW1UPzVDRklITEptTlohbl4sQyFZcFAyQF9KKn12amk=\\\"}","AOTMOBILE":"{\\\"basic_token\\\": \\\"YXNjZW5kLW9wcy1yZWFsLXRpbWUtc3VwcG9ydEB0bW9iaWxlLWZkbi5jb206Wj85I1kzNVh2I0lLLjY4Tng4IURTPVtCUnk3e2VTVlo=\\\"}","AOUSCELLULAR":"{\\\"basic_token\\\": \\\"YXNjZW5kLW9wcy1yZWFsLXRpbWUtc3VwcG9ydEB1c2NlbGx1bGFyLWZkbi5jb206OW9+W1t7WGFGaywpfkEkQENnb2tVemFZakI+Jlc/MHQ=\\\"}","AOATT":"{\\\"basic_token\\\": \\\"YXNjZW5kLW9wcy1yZWFsLXRpbWUtc3VwcG9ydEBhdHQtZmRuLmNvbTpuRU9QR2FyfWk2Q1RfK0FIUGI7X2YhUUY9VDUoZmttIQ==\\\"}","AOBUREAUCOMPLIANCE":"{\\\"basic_token\\\": \\\"YXNjZW5kLW9wcy1yZWFsLXRpbWUtc3VwcG9ydEBidXJlYXVjb21wbGlhbmNlZW5naW5lY29zdHVtZXIuY29tOjRBKmU2TzUzTlpVMjE5KGtGNjk/aj1ZNTJPOE1FR0Ew\\\"}"}"""
    
    try:
        # Parse the JSON
        credentials = json.loads(credentials_json)
        print(f"✅ Parsed {len(credentials)} credentials from JSON")
        
        successful_tests = []
        failed_tests = []
        
        # Test each credential
        for key, value in credentials.items():
            print(f"\n{'='*60}")
            print(f"Testing: {key}")
            print("=" * 60)
            
            try:
                # Parse the inner JSON to get the basic_token
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
                print(f"Decoded: {username}:{password[:10]}...")
                
                # Test the credential
                print(f"\n🧪 Testing credential against API...")
                result = test_credential(basic_token, domain)
                
                if result['success']:
                    print(f"✅ SUCCESS - Status: {result['status_code']}")
                    print(f"   Response time: {result['response_time_ms']:.2f}ms")
                    print(f"   Correlation ID: {result['correlation_id']}")
                    
                    if 'response_body' in result and isinstance(result['response_body'], dict):
                        token_info = result['response_body'].get('token', {})
                        if token_info:
                            print(f"   Token expires in: {token_info.get('expires_in', 'N/A')} seconds")
                            print(f"   Token type: {token_info.get('token_type', 'N/A')}")
                            access_token = token_info.get('access_token', '')
                            print(f"   Access token: {access_token[:30]}...")
                    
                    successful_tests.append(key)
                else:
                    print(f"❌ FAILED - Status: {result.get('status_code', 'N/A')}")
                    print(f"   Correlation ID: {result['correlation_id']}")
                    if 'error' in result:
                        print(f"   Error: {result['error']}")
                    elif 'response_body' in result:
                        if isinstance(result['response_body'], dict):
                            print(f"   Error code: {result['response_body'].get('code', 'N/A')}")
                            print(f"   Description: {result['response_body'].get('description', 'N/A')}")
                        else:
                            print(f"   Response: {result['response_body']}")
                    
                    failed_tests.append(key)
                
            except Exception as e:
                print(f"❌ Error testing {key}: {e}")
                failed_tests.append(key)
        
        # Summary
        print(f"\n{'='*60}")
        print("📊 TEST SUMMARY")
        print("=" * 60)
        print(f"✅ Successful: {len(successful_tests)} - {successful_tests}")
        print(f"❌ Failed: {len(failed_tests)} - {failed_tests}")
        
        if len(successful_tests) > 0 and len(failed_tests) == 0:
            print(f"🎉 ALL CREDENTIALS WORKING! Perfect success rate!")
        elif len(successful_tests) > 0:
            print(f"📈 Success Rate: {len(successful_tests)}/{len(successful_tests) + len(failed_tests)} ({len(successful_tests)/(len(successful_tests) + len(failed_tests))*100:.1f}%)")
        else:
            print(f"😱 No credentials are working!")
        
        # Show curl examples for successful ones
        if successful_tests:
            print(f"\n{'='*60}")
            print("🚀 CURL EXAMPLES FOR WORKING CREDENTIALS:")
            print("=" * 60)
            
            for key in successful_tests:
                token_data = json.loads(credentials[key])
                basic_token = token_data['basic_token']
                _, _, domain = decode_basic_token(basic_token)
                
                print(f"\n{key} ({domain}):")
                print(f'curl -X POST "https://da-saas-npsvhreanrlz.mn-na-test.preprod-ascend-na.io/v1/tokens/create" \\')
                print(f'  -H "Content-Type: application/json" \\')
                print(f'  -H "X-User-Domain: {domain}" \\')
                print(f'  -H "X-Correlation-Id: $(uuidgen)" \\')
                print(f'  -H "Authorization: Basic {basic_token}" \\')
                print(f'  -v')
        
    except json.JSONDecodeError as e:
        print(f"❌ Error parsing JSON: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    main()

    """
    curl -X POST "https://da-saas-npsvhreanrlz.mn-na-test.preprod-ascend-na.io/v1/tokens/create" \
    -H "Content-Type: application/json" \
    -H "X-User-Domain: bureaucomplianceenginecostumer.com" \
    -H "X-Correlation-Id: $(uuidgen)" \
    -H "Authorization: Basic YXNjZW5kLW9wcy1yZWFsLXRpbWUtc3VwcG9ydEBidXJlYXVjb21wbGlhbmNlZW5naW5lY29zdHVtZXIuY29tOjRBKmU2TzUzTlpVMjE5KGtGNjk/aj1ZNTJPOE1FR0Ew" \
    -v
    * Host da-saas-npsvhreanrlz.mn-na-test.preprod-ascend-na.io:443 was resolved.
    * IPv6: (none)
    * IPv4: 10.30.233.89, 10.30.233.173
    *   Trying 10.30.233.89:443...
    * Connected to da-saas-npsvhreanrlz.mn-na-test.preprod-ascend-na.io (10.30.233.89) port 443
    * ALPN: curl offers h2,http/1.1
    * (304) (OUT), TLS handshake, Client hello (1):
    *  CAfile: /etc/ssl/cert.pem
    *  CApath: none
    * (304) (IN), TLS handshake, Server hello (2):
    * TLSv1.2 (IN), TLS handshake, Certificate (11):
    * TLSv1.2 (IN), TLS handshake, Server key exchange (12):
    * TLSv1.2 (IN), TLS handshake, Server finished (14):
    * TLSv1.2 (OUT), TLS handshake, Client key exchange (16):
    * TLSv1.2 (OUT), TLS change cipher, Change cipher spec (1):
    * TLSv1.2 (OUT), TLS handshake, Finished (20):
    * TLSv1.2 (IN), TLS change cipher, Change cipher spec (1):
    * TLSv1.2 (IN), TLS handshake, Finished (20):
    * SSL connection using TLSv1.2 / ECDHE-RSA-AES128-GCM-SHA256 / [blank] / UNDEF
    * ALPN: server accepted h2
    * Server certificate:
    *  subject: CN=*.mn-na-test.preprod-ascend-na.io
    *  start date: May 28 00:00:00 2025 GMT
    *  expire date: Jun 26 23:59:59 2026 GMT
    *  subjectAltName: host "da-saas-npsvhreanrlz.mn-na-test.preprod-ascend-na.io" matched cert's "*.mn-na-test.preprod-ascend-na.io"
    *  issuer: C=US; O=Amazon; CN=Amazon RSA 2048 M03
    *  SSL certificate verify ok.
    * using HTTP/2
    * [HTTP/2] [1] OPENED stream for https://da-saas-npsvhreanrlz.mn-na-test.preprod-ascend-na.io/v1/tokens/create
    * [HTTP/2] [1] [:method: POST]
    * [HTTP/2] [1] [:scheme: https]
    * [HTTP/2] [1] [:authority: da-saas-npsvhreanrlz.mn-na-test.preprod-ascend-na.io]
    * [HTTP/2] [1] [:path: /v1/tokens/create]
    * [HTTP/2] [1] [user-agent: curl/8.7.1]
    * [HTTP/2] [1] [accept: */*]
    * [HTTP/2] [1] [content-type: application/json]
    * [HTTP/2] [1] [x-user-domain: bureaucomplianceenginecostumer.com]
    * [HTTP/2] [1] [x-correlation-id: 4EA4B3E5-6325-4600-B9FA-F5A6A4037905]
    * [HTTP/2] [1] [authorization: Basic YXNjZW5kLW9wcy1yZWFsLXRpbWUtc3VwcG9ydEBidXJlYXVjb21wbGlhbmNlZW5naW5lY29zdHVtZXIuY29tOjRBKmU2TzUzTlpVMjE5KGtGNjk/aj1ZNTJPOE1FR0Ew]
    > POST /v1/tokens/create HTTP/2
    > Host: da-saas-npsvhreanrlz.mn-na-test.preprod-ascend-na.io
    > User-Agent: curl/8.7.1
    > Accept: */*
    > Content-Type: application/json
    > X-User-Domain: bureaucomplianceenginecostumer.com
    > X-Correlation-Id: 4EA4B3E5-6325-4600-B9FA-F5A6A4037905
    > Authorization: Basic YXNjZW5kLW9wcy1yZWFsLXRpbWUtc3VwcG9ydEBidXJlYXVjb21wbGlhbmNlZW5naW5lY29zdHVtZXIuY29tOjRBKmU2TzUzTlpVMjE5KGtGNjk/aj1ZNTJPOE1FR0Ew
    > 
    * Request completely sent off
    < HTTP/2 200 
    < date: Fri, 29 Aug 2025 01:24:13 GMT
    < content-type: application/json
    < x-content-type-options: nosniff
    < content-security-policy: frame-ancestors 'none'
    < x-correlation-id: 4EA4B3E5-6325-4600-B9FA-F5A6A4037905
    < cache-control: no-store
    < pragma: no-cache
    < x-execution-time: 654
    < 
    * Connection #0 to host da-saas-npsvhreanrlz.mn-na-test.preprod-ascend-na.io left intact
    {"status":"SUCCESS","token":{"token_type":"Bearer","access_token":"eyJraWQiOiJkYS5zYWFzLnVzLWVhc3QtMS5wcm9kLjIwMjUwODA4LjQ4IiwidHlwIjoiSldUIiwiYWxnIjoiRVMyNTYifQ.eyJleHAiOjE3NTY0NTk0NTMsImlhdCI6MTc1NjQzMDY1MywibmJmIjoxNzU2NDMwNjUwLCJqdGkiOiI3YjQ3MWI4YS04MGQwLTQ0ZDctYjhlOS01YzU0ZWJjZTA4OTUiLCJpc3MiOiJ0b2tlbi1zZXJ2aWNlIiwiYXVkIjoic2FhcyIsInN1YiI6Ijk5NjU5NWYwODJlZDhjMzdhZWJkMGM1ZmZlNWFiNDUzYjcxYWZlMDkiLCJ1c2VySWQiOiJhc2NlbmQtb3BzLXJlYWwtdGltZS1zdXBwb3J0QGJ1cmVhdWNvbXBsaWFuY2VlbmdpbmVjb3N0dW1lci5jb20iLCJ1c2VybmFtZSI6ImFzY2VuZC1vcHMtcmVhbC10aW1lLXN1cHBvcnRAYnVyZWF1Y29tcGxpYW5jZWVuZ2luZWNvc3R1bWVyLmNvbSIsImZpcnN0bmFtZSI6ImFzY2VuZC1vcHMiLCJsYXN0bmFtZSI6InJlYWwtdGltZS1zdXBwb3J0Iiwiem9uZWluZm8iOiJFdGMvVVRDIiwicm9sZXMiOlsiQ0NfQVBJX0NMSUVOVCJdLCJwZXJtaXNzaW9ucyI6WyJBY2Nlc3MtRmVlZGJhY2tBUEkiLCJBY2Nlc3MtR2V0UmVjb3JkQVBJIiwiQWNjZXNzLVB1cmdlQVBJIiwiQWNjZXNzLVN1Ym1pdEFQSSIsIlZpZXctVXNlciJdLCJlbnZpcm9ubWVudHMiOlsiMGE1N2RjMzA0MmNmNGRhMmFhY2ViYjA5YTRhZGNlM2IiXSwiYWNjZXNzUHJvZmlsZXMiOnt9LCJ0ZW5hbnRJZCI6IlRFTkFOVDEiLCJjbGllbnRJZCI6IjEzYmQxYTBkM2IwNDRhZjg5MzIwM2RlYjhjNzc5YSIsImNvbXBhbnlJZCI6IjU2MDI5MiIsImdyb3VwTmFtZSI6IkV4cGVyaWFuT05FIENyb3NzQ29yZSIsImlwUmVzdHJpY3Rpb25zIjpbIjEwLjQuNjYuMC0xMC40LjY2LjI1NSIsIjEwLjMwLjE0MC4wLTEwLjMwLjE0MS4yNTUiLCIxMC40LjEyNi4wLTEwLjQuMTI3LjI1NSIsIjEwLjQuOTYuMC0xMC40LjEwMy4yNTUiXSwicGxhdGZvcm1Qcm92aWRlciI6IkVPRUtTIiwiY2xpZW50VHlwZSI6IlNUQU5EQVJEIiwiaWRwVUlkIjoiMDB1MmdrOW8xZGMzZW1EWmYwaDgiLCJjbGllbnREb21haW4iOiJidXJlYXVjb21wbGlhbmNlZW5naW5lY29zdHVtZXIuY29tIiwiY291bnRyeUNvZGUiOiJVUyIsImFjY291bnQiOiJleHBlcmlhbi1uYWIub2t0YXByZXZpZXcuY29tL2NvbXBhbnkvNTYwMjkyIiwiaW50ZXJuYWwiOmZhbHNlfQ.b9TmhafyhcEs71eERdC-jmOKo0RkfwVZo5AWIhuMWd37csQc4g9vldlfqk4bXyqo70OjTqqG2K1YVwBIZacdOA","refresh_token_type":"Refresh","refresh_token":"cca01c58-35e2-4f2d-9cb2-9854660f8b16","expires_in":28800}}%    
    """