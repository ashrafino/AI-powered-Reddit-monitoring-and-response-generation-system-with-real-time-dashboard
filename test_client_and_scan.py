#!/usr/bin/env python3
"""
Test script to verify client creation and scan functionality
"""
import requests
import json
import time

API_BASE_URL = "http://localhost:8000/api"

def test_login():
    """Login as admin"""
    print("\n🔐 Testing login...")
    response = requests.post(f"{API_BASE_URL}/auth/login", data={
        "username": "admin@example.com",
        "password": "admin123"
    })
    
    if response.status_code == 200:
        token = response.json()["access_token"]
        print(f"✅ Login successful")
        return token
    else:
        print(f"❌ Login failed: {response.status_code} - {response.text}")
        return None

def test_list_clients(token):
    """List existing clients"""
    print("\n📋 Listing clients...")
    response = requests.get(
        f"{API_BASE_URL}/clients",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    if response.status_code == 200:
        clients = response.json()
        print(f"✅ Found {len(clients)} clients")
        for client in clients:
            print(f"   - {client['name']} (ID: {client['id']})")
        return clients
    else:
        print(f"❌ Failed to list clients: {response.status_code} - {response.text}")
        return []

def test_create_client(token):
    """Create a test client"""
    print("\n➕ Creating test client...")
    response = requests.post(
        f"{API_BASE_URL}/clients",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": f"Test Client {int(time.time())}"}
    )
    
    if response.status_code == 200:
        client = response.json()
        print(f"✅ Client created: {client['name']} (ID: {client['id']})")
        return client
    else:
        print(f"❌ Failed to create client: {response.status_code} - {response.text}")
        return None

def test_create_config(token, client_id):
    """Create a test configuration"""
    print(f"\n⚙️  Creating config for client {client_id}...")
    response = requests.post(
        f"{API_BASE_URL}/configs",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "client_id": client_id,
            "reddit_subreddits": ["technology", "programming"],
            "keywords": ["API", "integration"],
            "is_active": True,
            "scan_interval_minutes": 360,
            "scan_start_hour": 0,
            "scan_end_hour": 23,
            "scan_days": "1,2,3,4,5,6,7"
        }
    )
    
    if response.status_code == 200:
        config = response.json()
        print(f"✅ Config created (ID: {config['id']})")
        return config
    else:
        print(f"❌ Failed to create config: {response.status_code} - {response.text}")
        return None

def test_list_configs(token):
    """List configurations"""
    print("\n📋 Listing configs...")
    response = requests.get(
        f"{API_BASE_URL}/configs",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    if response.status_code == 200:
        configs = response.json()
        print(f"✅ Found {len(configs)} configs")
        for config in configs:
            print(f"   - Config {config['id']} for client {config['client_id']}")
        return configs
    else:
        print(f"❌ Failed to list configs: {response.status_code} - {response.text}")
        return []

def test_trigger_scan(token):
    """Trigger a manual scan"""
    print("\n🔄 Triggering scan...")
    response = requests.post(
        f"{API_BASE_URL}/ops/scan",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Scan triggered successfully")
        print(f"   Status: {result.get('status')}")
        print(f"   Method: {result.get('method')}")
        if result.get('created_posts') is not None:
            print(f"   Posts created: {result.get('created_posts')}")
            print(f"   Responses created: {result.get('created_responses')}")
        return result
    else:
        print(f"❌ Failed to trigger scan: {response.status_code} - {response.text}")
        return None

def test_list_posts(token):
    """List matched posts"""
    print("\n📋 Listing posts...")
    response = requests.get(
        f"{API_BASE_URL}/posts",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    if response.status_code == 200:
        posts = response.json()
        print(f"✅ Found {len(posts)} posts")
        for post in posts[:5]:  # Show first 5
            print(f"   - {post['title'][:60]}... (r/{post['subreddit']})")
        return posts
    else:
        print(f"❌ Failed to list posts: {response.status_code} - {response.text}")
        return []

def main():
    print("=" * 60)
    print("Testing Client Creation and Scan Functionality")
    print("=" * 60)
    
    # Login
    token = test_login()
    if not token:
        print("\n❌ Cannot proceed without authentication")
        return
    
    # List existing clients
    existing_clients = test_list_clients(token)
    
    # Create a new client
    new_client = test_create_client(token)
    if not new_client:
        print("\n❌ Cannot proceed without a client")
        return
    
    # Create a config for the new client
    config = test_create_config(token, new_client['id'])
    if not config:
        print("\n⚠️  Config creation failed, but continuing...")
    
    # List all configs
    test_list_configs(token)
    
    # Trigger a scan
    scan_result = test_trigger_scan(token)
    
    # Wait a bit for scan to complete (if sync)
    if scan_result and scan_result.get('method') == 'sync':
        print("\n⏳ Waiting for scan to complete...")
        time.sleep(2)
    
    # List posts
    test_list_posts(token)
    
    print("\n" + "=" * 60)
    print("✅ All tests completed!")
    print("=" * 60)

if __name__ == "__main__":
    main()
