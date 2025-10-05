#!/usr/bin/env python3
"""
Test all API endpoints
"""
import requests
import json

BASE_URL = "http://localhost:8001"
API_PREFIX = "/api"

# First, login to get a token
def get_auth_token():
    print("🔐 Testing Authentication...")
    try:
        response = requests.post(
            f"{BASE_URL}{API_PREFIX}/auth/login",
            data={
                "username": "admin@example.com",
                "password": "admin123"
            }
        )
        if response.status_code == 200:
            token = response.json().get("access_token")
            print(f"✓ Login successful! Token: {token[:20]}...")
            return token
        else:
            print(f"✗ Login failed: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"✗ Login error: {e}")
        return None

def test_endpoint(method, endpoint, token=None, data=None, description=""):
    """Test a single endpoint"""
    url = f"{BASE_URL}{API_PREFIX}{endpoint}"
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    try:
        if method == "GET":
            response = requests.get(url, headers=headers)
        elif method == "POST":
            response = requests.post(url, headers=headers, json=data)
        elif method == "PUT":
            response = requests.put(url, headers=headers, json=data)
        elif method == "DELETE":
            response = requests.delete(url, headers=headers)
        
        status = "✓" if response.status_code < 400 else "✗"
        print(f"{status} {method} {endpoint} - {response.status_code} - {description}")
        
        if response.status_code < 400:
            try:
                data = response.json()
                if isinstance(data, list):
                    print(f"   → Returned {len(data)} items")
                elif isinstance(data, dict):
                    print(f"   → Keys: {list(data.keys())[:5]}")
            except:
                pass
        else:
            print(f"   → Error: {response.text[:100]}")
        
        return response
    except Exception as e:
        print(f"✗ {method} {endpoint} - ERROR: {e}")
        return None

def main():
    print("=" * 60)
    print("API ENDPOINT TESTING")
    print("=" * 60)
    
    # Get auth token
    token = get_auth_token()
    if not token:
        print("\n❌ Cannot proceed without authentication token")
        return
    
    print("\n" + "=" * 60)
    print("TESTING ENDPOINTS")
    print("=" * 60)
    
    # Health check
    print("\n📊 Health & Status:")
    test_endpoint("GET", "/health", description="Health check")
    
    # Auth endpoints
    print("\n🔐 Authentication:")
    test_endpoint("GET", "/auth/me", token, description="Get current user")
    
    # Clients
    print("\n👥 Clients:")
    test_endpoint("GET", "/clients", token, description="List clients")
    
    # Configs
    print("\n⚙️  Configurations:")
    configs_response = test_endpoint("GET", "/configs", token, description="List configs")
    
    # Posts
    print("\n📝 Posts:")
    posts_response = test_endpoint("GET", "/posts", token, description="List posts")
    
    # Analytics
    print("\n📈 Analytics:")
    test_endpoint("GET", "/analytics/summary", token, description="Dashboard summary")
    test_endpoint("GET", "/analytics/trends", token, description="Trends")
    test_endpoint("GET", "/analytics/keyword-insights", token, description="Keyword insights")
    
    # Users
    print("\n👤 Users:")
    test_endpoint("GET", "/users", token, description="List users")
    
    # Operations
    print("\n🔄 Operations:")
    scan_response = test_endpoint("POST", "/ops/scan", token, description="Trigger scan")
    
    if scan_response and scan_response.status_code == 200:
        result = scan_response.json()
        print(f"\n   📊 Scan Result:")
        print(f"   Method: {result.get('method')}")
        print(f"   Status: {result.get('status')}")
        if result.get('created_posts') is not None:
            print(f"   Posts created: {result.get('created_posts')}")
            print(f"   Responses created: {result.get('created_responses')}")
        if result.get('error'):
            print(f"   Error: {result.get('error')}")
    
    print("\n" + "=" * 60)
    print("TESTING COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    main()
