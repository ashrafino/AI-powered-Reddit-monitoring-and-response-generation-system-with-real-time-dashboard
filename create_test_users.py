#!/usr/bin/env python3
"""
Script to create test users for authentication testing
"""

import requests
import json

API_BASE_URL = "http://localhost:8001"

def create_admin_user():
    """Create an admin user"""
    try:
        response = requests.post(f"{API_BASE_URL}/api/auth/register", json={
            "email": "admin@example.com",
            "password": "admin123",
            "role": "admin"
        })
        
        if response.status_code == 200:
            print("✅ Admin user created successfully")
            return True
        elif response.status_code == 400 and "already registered" in response.text:
            print("✅ Admin user already exists")
            return True
        else:
            print(f"❌ Failed to create admin user: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error creating admin user: {e}")
        return False

def create_client_user():
    """Create a user with a client"""
    try:
        response = requests.post(f"{API_BASE_URL}/api/auth/register", json={
            "email": "client@example.com",
            "password": "client123",
            "role": "client",
            "client_name": "Test Client Company",
            "create_client_if_missing": True
        })
        
        if response.status_code == 200:
            print("✅ Client user created successfully")
            data = response.json()
            print(f"   User ID: {data.get('id')}")
            print(f"   Client ID: {data.get('client_id')}")
            return True
        elif response.status_code == 400 and "already registered" in response.text:
            print("✅ Client user already exists")
            return True
        else:
            print(f"❌ Failed to create client user: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error creating client user: {e}")
        return False

def update_existing_user_with_client():
    """Update the existing test user to have a client"""
    try:
        # First create a client
        client_response = requests.post(f"{API_BASE_URL}/api/auth/register", json={
            "email": "temp@example.com",
            "password": "temp123",
            "role": "client",
            "client_name": "Test Client for Existing User",
            "create_client_if_missing": True
        })
        
        if client_response.status_code == 200:
            client_data = client_response.json()
            client_id = client_data.get('client_id')
            print(f"✅ Created client with ID: {client_id}")
            
            # Note: We would need to update the existing user's client_id in the database
            # For now, we'll just create a new user with a client
            return True
        else:
            print(f"❌ Failed to create client: {client_response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error updating user with client: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Creating test users...")
    
    # Create admin user
    create_admin_user()
    
    # Create client user
    create_client_user()
    
    print("\n✅ Test user creation complete!")