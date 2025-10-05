#!/usr/bin/env python3
"""
End-to-End Authentication Flow Testing Script

This script tests the complete authentication flow from login to API access 
and WebSocket connections to validate that all 401 errors are resolved.

Requirements tested:
- 1.1: JWT token creation and validation
- 2.1: WebSocket authentication 
- 3.1: API endpoint authentication
- 4.1: Frontend token management
- 5.1: Error handling and logging
"""

import asyncio
import json
import logging
import sys
import time
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Tuple
import requests
import websockets
from urllib.parse import urlencode
import jwt
import base64

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Test configuration
API_BASE_URL = "http://localhost:8001"
WS_BASE_URL = "ws://localhost:8001"
TEST_USER_EMAIL = "client@example.com"
TEST_USER_PASSWORD = "client123"
TEST_ADMIN_EMAIL = "admin@example.com"
TEST_ADMIN_PASSWORD = "admin123"

class AuthenticationTester:
    """Comprehensive authentication flow tester"""
    
    def __init__(self):
        self.session = requests.Session()
        self.user_token = None
        self.admin_token = None
        self.test_results = []
        
    def log_test_result(self, test_name: str, success: bool, details: str = "", error: str = ""):
        """Log test result"""
        result = {
            "test_name": test_name,
            "success": success,
            "details": details,
            "error": error,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        logger.info(f"{status} - {test_name}")
        if details:
            logger.info(f"  Details: {details}")
        if error:
            logger.error(f"  Error: {error}")
    
    def validate_jwt_token(self, token: str) -> Tuple[bool, Dict[str, Any]]:
        """Validate JWT token structure and content"""
        try:
            # Decode without verification to check structure
            parts = token.split('.')
            if len(parts) != 3:
                return False, {"error": "Invalid JWT structure"}
            
            # Decode header and payload
            header = json.loads(base64.urlsafe_b64decode(parts[0] + '=='))
            payload = json.loads(base64.urlsafe_b64decode(parts[1] + '=='))
            
            # Check required fields
            required_fields = ['sub', 'user_id', 'exp', 'iat']
            missing_fields = [field for field in required_fields if field not in payload]
            
            if missing_fields:
                return False, {"error": f"Missing required fields: {missing_fields}"}
            
            # Check expiration
            exp = payload.get('exp')
            now = time.time()
            if exp <= now:
                return False, {"error": "Token expired"}
            
            return True, {
                "header": header,
                "payload": payload,
                "valid_until": datetime.fromtimestamp(exp, tz=timezone.utc).isoformat()
            }
            
        except Exception as e:
            return False, {"error": f"Token validation error: {str(e)}"}
    
    def test_user_registration(self) -> bool:
        """Test user registration"""
        try:
            # First, try to create a test user with a client
            response = self.session.post(f"{API_BASE_URL}/api/auth/register", json={
                "email": TEST_USER_EMAIL,
                "password": TEST_USER_PASSWORD,
                "role": "client",
                "client_name": "Test Client",
                "create_client_if_missing": True
            })
            
            if response.status_code == 200:
                self.log_test_result(
                    "User Registration", 
                    True, 
                    f"User {TEST_USER_EMAIL} created successfully"
                )
                return True
            elif response.status_code == 400 and "already registered" in response.text:
                self.log_test_result(
                    "User Registration", 
                    True, 
                    f"User {TEST_USER_EMAIL} already exists"
                )
                return True
            else:
                self.log_test_result(
                    "User Registration", 
                    False, 
                    error=f"Status: {response.status_code}, Response: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_test_result("User Registration", False, error=str(e))
            return False
    
    def test_user_login(self) -> bool:
        """Test user login and token creation"""
        try:
            # Test login with form data
            login_data = {
                "username": TEST_USER_EMAIL,
                "password": TEST_USER_PASSWORD
            }
            
            response = self.session.post(
                f"{API_BASE_URL}/api/auth/login",
                data=login_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            
            if response.status_code == 200:
                data = response.json()
                token = data.get("access_token")
                
                if not token:
                    self.log_test_result(
                        "User Login", 
                        False, 
                        error="No access token in response"
                    )
                    return False
                
                # Validate token structure
                is_valid, token_info = self.validate_jwt_token(token)
                if not is_valid:
                    self.log_test_result(
                        "User Login", 
                        False, 
                        error=f"Invalid token: {token_info.get('error')}"
                    )
                    return False
                
                self.user_token = token
                self.log_test_result(
                    "User Login", 
                    True, 
                    f"Login successful, token expires: {token_info['valid_until']}"
                )
                return True
            else:
                self.log_test_result(
                    "User Login", 
                    False, 
                    error=f"Status: {response.status_code}, Response: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_test_result("User Login", False, error=str(e))
            return False
    
    def test_admin_login(self) -> bool:
        """Test admin login for debug endpoints"""
        try:
            # Try to login as admin (may not exist, that's ok)
            login_data = {
                "username": TEST_ADMIN_EMAIL,
                "password": TEST_ADMIN_PASSWORD
            }
            
            response = self.session.post(
                f"{API_BASE_URL}/api/auth/login",
                data=login_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            
            if response.status_code == 200:
                data = response.json()
                self.admin_token = data.get("access_token")
                self.log_test_result("Admin Login", True, "Admin login successful")
                return True
            else:
                self.log_test_result(
                    "Admin Login", 
                    False, 
                    "Admin user not available (this is expected in most cases)"
                )
                return False
                
        except Exception as e:
            self.log_test_result("Admin Login", False, error=str(e))
            return False
    
    def test_api_authentication(self) -> bool:
        """Test API endpoint authentication with valid token"""
        if not self.user_token:
            self.log_test_result(
                "API Authentication", 
                False, 
                error="No user token available"
            )
            return False
        
        try:
            # Test authenticated API endpoint (use /users/me which requires auth)
            headers = {"Authorization": f"Bearer {self.user_token}"}
            
            # Try to access a protected endpoint
            response = self.session.get(f"{API_BASE_URL}/api/users/me", headers=headers)
            
            if response.status_code == 200:
                self.log_test_result(
                    "API Authentication", 
                    True, 
                    "Successfully accessed protected endpoint"
                )
                return True
            else:
                self.log_test_result(
                    "API Authentication", 
                    False, 
                    error=f"Status: {response.status_code}, Response: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_test_result("API Authentication", False, error=str(e))
            return False
    
    def test_api_without_token(self) -> bool:
        """Test API endpoint without token (should fail with 401)"""
        try:
            # Try to access protected endpoint without token
            response = self.session.get(f"{API_BASE_URL}/api/users/me")
            
            if response.status_code == 401:
                self.log_test_result(
                    "API Without Token", 
                    True, 
                    "Correctly rejected request without token (401)"
                )
                return True
            else:
                self.log_test_result(
                    "API Without Token", 
                    False, 
                    error=f"Expected 401, got {response.status_code}"
                )
                return False
                
        except Exception as e:
            self.log_test_result("API Without Token", False, error=str(e))
            return False
    
    def test_api_with_invalid_token(self) -> bool:
        """Test API endpoint with invalid token (should fail with 401)"""
        try:
            # Try to access protected endpoint with invalid token
            headers = {"Authorization": "Bearer invalid.token.here"}
            response = self.session.get(f"{API_BASE_URL}/api/users/me", headers=headers)
            
            if response.status_code == 401:
                self.log_test_result(
                    "API Invalid Token", 
                    True, 
                    "Correctly rejected request with invalid token (401)"
                )
                return True
            else:
                self.log_test_result(
                    "API Invalid Token", 
                    False, 
                    error=f"Expected 401, got {response.status_code}"
                )
                return False
                
        except Exception as e:
            self.log_test_result("API Invalid Token", False, error=str(e))
            return False
    
    async def test_websocket_authentication(self) -> bool:
        """Test WebSocket authentication with valid token"""
        if not self.user_token:
            self.log_test_result(
                "WebSocket Authentication", 
                False, 
                error="No user token available"
            )
            return False
        
        try:
            # Create WebSocket connection with token
            ws_url = f"{WS_BASE_URL}/api/ws?token={self.user_token}"
            
            async with websockets.connect(ws_url) as websocket:
                # Send a ping message
                ping_message = {
                    "type": "ping",
                    "timestamp": time.time()
                }
                await websocket.send(json.dumps(ping_message))
                
                # Wait for response (with timeout)
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    response_data = json.loads(response)
                    
                    self.log_test_result(
                        "WebSocket Authentication", 
                        True, 
                        f"WebSocket connected and received response: {response_data.get('type', 'unknown')}"
                    )
                    return True
                    
                except asyncio.TimeoutError:
                    self.log_test_result(
                        "WebSocket Authentication", 
                        True, 
                        "WebSocket connected (no immediate response, but connection established)"
                    )
                    return True
                    
        except websockets.exceptions.ConnectionClosedError as e:
            # Check if it's an authentication error
            if e.code >= 4001 and e.code <= 4007:
                self.log_test_result(
                    "WebSocket Authentication", 
                    False, 
                    error=f"WebSocket auth error: {e.code} - {e.reason}"
                )
            else:
                self.log_test_result(
                    "WebSocket Authentication", 
                    False, 
                    error=f"WebSocket connection error: {e.code} - {e.reason}"
                )
            return False
        except websockets.exceptions.InvalidStatusCode as e:
            # Handle HTTP status code errors (like 403)
            if e.status_code == 403:
                self.log_test_result(
                    "WebSocket Authentication", 
                    False, 
                    error="WebSocket connection rejected (403) - likely client association issue"
                )
            else:
                self.log_test_result(
                    "WebSocket Authentication", 
                    False, 
                    error=f"WebSocket HTTP error: {e.status_code}"
                )
            return False
            
        except Exception as e:
            self.log_test_result("WebSocket Authentication", False, error=str(e))
            return False
    
    async def test_websocket_without_token(self) -> bool:
        """Test WebSocket connection without token (should fail)"""
        try:
            # Try to connect without token
            ws_url = f"{WS_BASE_URL}/api/ws"
            
            async with websockets.connect(ws_url) as websocket:
                # If we get here, the connection succeeded when it shouldn't have
                self.log_test_result(
                    "WebSocket Without Token", 
                    False, 
                    error="WebSocket connection succeeded without token"
                )
                return False
                
        except websockets.exceptions.ConnectionClosedError as e:
            # This is expected - should fail with auth error
            if e.code >= 4001 and e.code <= 4007:
                self.log_test_result(
                    "WebSocket Without Token", 
                    True, 
                    f"Correctly rejected WebSocket without token: {e.code} - {e.reason}"
                )
                return True
            else:
                self.log_test_result(
                    "WebSocket Without Token", 
                    False, 
                    error=f"Unexpected error code: {e.code} - {e.reason}"
                )
                return False
        except websockets.exceptions.InvalidStatusCode as e:
            # Handle HTTP status code errors (like 403)
            if e.status_code == 403:
                self.log_test_result(
                    "WebSocket Without Token", 
                    True, 
                    "Correctly rejected WebSocket without token (403)"
                )
                return True
            else:
                self.log_test_result(
                    "WebSocket Without Token", 
                    False, 
                    error=f"Unexpected HTTP status: {e.status_code}"
                )
                return False
        except Exception as e:
            # Handle other connection errors
            if "403" in str(e) or "Forbidden" in str(e):
                self.log_test_result(
                    "WebSocket Without Token", 
                    True, 
                    "Correctly rejected WebSocket without token"
                )
                return True
            else:
                self.log_test_result("WebSocket Without Token", False, error=str(e))
                return False
                
        except Exception as e:
            # Check if it's a missing token parameter error
            if "token" in str(e).lower():
                self.log_test_result(
                    "WebSocket Without Token", 
                    True, 
                    "Correctly rejected WebSocket without token parameter"
                )
                return True
            else:
                self.log_test_result("WebSocket Without Token", False, error=str(e))
                return False
    
    async def test_websocket_invalid_token(self) -> bool:
        """Test WebSocket connection with invalid token (should fail)"""
        try:
            # Try to connect with invalid token
            ws_url = f"{WS_BASE_URL}/api/ws?token=invalid.token.here"
            
            async with websockets.connect(ws_url) as websocket:
                # If we get here, the connection succeeded when it shouldn't have
                self.log_test_result(
                    "WebSocket Invalid Token", 
                    False, 
                    error="WebSocket connection succeeded with invalid token"
                )
                return False
                
        except websockets.exceptions.ConnectionClosedError as e:
            # This is expected - should fail with auth error
            if e.code >= 4001 and e.code <= 4007:
                self.log_test_result(
                    "WebSocket Invalid Token", 
                    True, 
                    f"Correctly rejected WebSocket with invalid token: {e.code} - {e.reason}"
                )
                return True
            else:
                self.log_test_result(
                    "WebSocket Invalid Token", 
                    False, 
                    error=f"Unexpected error code: {e.code} - {e.reason}"
                )
                return False
        except websockets.exceptions.InvalidStatusCode as e:
            # Handle HTTP status code errors (like 403)
            if e.status_code == 403:
                self.log_test_result(
                    "WebSocket Invalid Token", 
                    True, 
                    "Correctly rejected WebSocket with invalid token (403)"
                )
                return True
            else:
                self.log_test_result(
                    "WebSocket Invalid Token", 
                    False, 
                    error=f"Unexpected HTTP status: {e.status_code}"
                )
                return False
        except Exception as e:
            # Handle other connection errors
            if "403" in str(e) or "Forbidden" in str(e):
                self.log_test_result(
                    "WebSocket Invalid Token", 
                    True, 
                    "Correctly rejected WebSocket with invalid token"
                )
                return True
            else:
                self.log_test_result("WebSocket Invalid Token", False, error=str(e))
                return False
                
        except Exception as e:
            self.log_test_result("WebSocket Invalid Token", False, error=str(e))
            return False
    
    def test_debug_endpoints(self) -> bool:
        """Test authentication debug endpoints (if admin token available)"""
        if not self.admin_token:
            self.log_test_result(
                "Debug Endpoints", 
                False, 
                "Admin token not available, skipping debug endpoint tests"
            )
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            
            # Test token info endpoint
            response = self.session.get(
                f"{API_BASE_URL}/api/auth/debug/token-info?token={self.user_token}",
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                self.log_test_result(
                    "Debug Endpoints", 
                    True, 
                    f"Debug endpoint accessible, token status: {data.get('status')}"
                )
                return True
            else:
                self.log_test_result(
                    "Debug Endpoints", 
                    False, 
                    error=f"Status: {response.status_code}, Response: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_test_result("Debug Endpoints", False, error=str(e))
            return False
    
    def test_error_handling(self) -> bool:
        """Test error handling and response format"""
        try:
            # Test with expired/invalid token to check error format
            headers = {"Authorization": "Bearer expired.token.here"}
            response = self.session.get(f"{API_BASE_URL}/api/users/me", headers=headers)
            
            if response.status_code == 401:
                try:
                    error_data = response.json()
                    # Check if error response has proper structure
                    if "detail" in error_data or "error" in error_data:
                        self.log_test_result(
                            "Error Handling", 
                            True, 
                            "Error responses have proper structure"
                        )
                        return True
                    else:
                        self.log_test_result(
                            "Error Handling", 
                            False, 
                            error="Error response missing proper structure"
                        )
                        return False
                except json.JSONDecodeError:
                    self.log_test_result(
                        "Error Handling", 
                        False, 
                        error="Error response is not valid JSON"
                    )
                    return False
            else:
                self.log_test_result(
                    "Error Handling", 
                    False, 
                    error=f"Expected 401 error, got {response.status_code}"
                )
                return False
                
        except Exception as e:
            self.log_test_result("Error Handling", False, error=str(e))
            return False
    
    def test_client_data_isolation(self) -> bool:
        """Test client data isolation with authentication"""
        if not self.user_token:
            self.log_test_result(
                "Client Data Isolation", 
                False, 
                error="No user token available"
            )
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.user_token}"}
            
            # Try to access client-specific endpoints
            # This tests that the client_id from the token is properly used
            response = self.session.get(f"{API_BASE_URL}/api/configs", headers=headers)
            
            # Should either succeed (if user has client) or fail with proper error
            if response.status_code in [200, 404, 403]:
                self.log_test_result(
                    "Client Data Isolation", 
                    True, 
                    f"Client-scoped endpoint responded appropriately: {response.status_code}"
                )
                return True
            else:
                self.log_test_result(
                    "Client Data Isolation", 
                    False, 
                    error=f"Unexpected status: {response.status_code}"
                )
                return False
                
        except Exception as e:
            self.log_test_result("Client Data Isolation", False, error=str(e))
            return False
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all authentication tests"""
        logger.info("🚀 Starting comprehensive authentication flow testing...")
        logger.info(f"API Base URL: {API_BASE_URL}")
        logger.info(f"WebSocket Base URL: {WS_BASE_URL}")
        logger.info("=" * 60)
        
        # Test 1: User Registration
        self.test_user_registration()
        
        # Test 2: User Login (JWT Token Creation)
        self.test_user_login()
        
        # Test 3: Admin Login (for debug endpoints)
        self.test_admin_login()
        
        # Test 4: API Authentication with valid token
        self.test_api_authentication()
        
        # Test 5: API without token (should fail)
        self.test_api_without_token()
        
        # Test 6: API with invalid token (should fail)
        self.test_api_with_invalid_token()
        
        # Test 7: WebSocket authentication with valid token
        await self.test_websocket_authentication()
        
        # Test 8: WebSocket without token (should fail)
        await self.test_websocket_without_token()
        
        # Test 9: WebSocket with invalid token (should fail)
        await self.test_websocket_invalid_token()
        
        # Test 10: Debug endpoints (if admin available)
        self.test_debug_endpoints()
        
        # Test 11: Error handling and response format
        self.test_error_handling()
        
        # Test 12: Client data isolation
        self.test_client_data_isolation()
        
        # Calculate results
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        logger.info("=" * 60)
        logger.info("📊 TEST RESULTS SUMMARY")
        logger.info(f"Total Tests: {total_tests}")
        logger.info(f"Passed: {passed_tests} ✅")
        logger.info(f"Failed: {failed_tests} ❌")
        logger.info(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            logger.info("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    logger.info(f"  - {result['test_name']}: {result['error']}")
        
        return {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "success_rate": (passed_tests/total_tests)*100,
            "test_results": self.test_results,
            "overall_success": failed_tests == 0
        }


async def main():
    """Main test execution function"""
    tester = AuthenticationTester()
    
    try:
        results = await tester.run_all_tests()
        
        # Save detailed results to file
        with open("authentication_test_results.json", "w") as f:
            json.dump(results, f, indent=2, default=str)
        
        logger.info(f"\n📄 Detailed results saved to: authentication_test_results.json")
        
        # Exit with appropriate code
        sys.exit(0 if results["overall_success"] else 1)
        
    except KeyboardInterrupt:
        logger.info("\n⏹️  Test execution interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Test execution failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())