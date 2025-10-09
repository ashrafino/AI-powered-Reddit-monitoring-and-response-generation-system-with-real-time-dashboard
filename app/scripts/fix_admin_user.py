#!/usr/bin/env python3
"""
Fix admin user authentication issues.
This script ensures the admin user has consistent client_id settings.
"""

from app.db.session import SessionLocal
from app.models.user import User
from app.models.client import Client
from app.core.security import create_access_token

def fix_admin_user():
    """Fix admin user client_id issues"""
    db = SessionLocal()
    
    try:
        # Find admin user
        admin_user = db.query(User).filter(User.email == "admin@example.com").first()
        
        if not admin_user:
            print("❌ Admin user not found")
            return
        
        print(f"📋 Current admin user:")
        print(f"   ID: {admin_user.id}")
        print(f"   Email: {admin_user.email}")
        print(f"   Role: {admin_user.role}")
        print(f"   Client ID: {admin_user.client_id}")
        
        # Check if there are any clients
        clients = db.query(Client).all()
        print(f"📋 Available clients: {len(clients)}")
        for client in clients:
            print(f"   - {client.name} (ID: {client.id})")
        
        # Option 1: Set admin client_id to null (recommended for admins)
        if admin_user.client_id is not None:
            print(f"🔧 Setting admin client_id to null (admin should have no specific client)")
            admin_user.client_id = None
            db.commit()
            print("✅ Admin client_id set to null")
        
        # Generate a new token to test
        new_token = create_access_token(
            user_email=admin_user.email,
            user_id=admin_user.id,
            client_id=admin_user.client_id  # This will be null
        )
        
        print(f"🔑 New token generated (first 50 chars): {new_token[:50]}...")
        
        # Decode token to verify (using jose which is already installed)
        from jose import jwt
        payload = jwt.get_unverified_claims(new_token)
        print(f"📋 Token payload:")
        print(f"   sub: {payload.get('sub')}")
        print(f"   user_id: {payload.get('user_id')}")
        print(f"   client_id: {payload.get('client_id')}")
        
        return new_token
        
    except Exception as e:
        print(f"❌ Error fixing admin user: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    token = fix_admin_user()
    print(f"\n✅ Admin user fixed!")
    print(f"💡 You may need to login again to get a new token.")