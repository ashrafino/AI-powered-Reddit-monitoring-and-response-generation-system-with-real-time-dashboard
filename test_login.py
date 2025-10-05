#!/usr/bin/env python3
"""
Simple script to test the login functionality
"""
import requests
import json

def test_login():
    # Test login endpoint
    login_url = "http://localhost/api/auth/login"
    
    # Login data (form-encoded for OAuth2PasswordRequestForm)
    login_data = {
        "username": "admin@example.com",
        "password": "admin123"
    }
    
    print("Testing login...")
    print(f"URL: {login_url}")
    print(f"Data: {login_data}")
    
    try:
        response = requests.post(login_url, data=login_data)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            token_data = response.json()
            print("✅ Login successful!")
            print(f"Token: {token_data.get('access_token', 'N/A')}")
            
            # Test dashboard endpoint with token
            token = token_data.get('access_token')
            if token:
                dashboard_url = "http://localhost/api/analytics/dashboard"
                headers = {"Authorization": f"Bearer {token}"}
                
                print("\nTesting dashboard endpoint...")
                dashboard_response = requests.get(dashboard_url, headers=headers)
                print(f"Dashboard Status: {dashboard_response.status_code}")
                print(f"Dashboard Response: {dashboard_response.text}")
                
        else:
            print("❌ Login failed!")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")

if __name__ == "__main__":
    test_login()