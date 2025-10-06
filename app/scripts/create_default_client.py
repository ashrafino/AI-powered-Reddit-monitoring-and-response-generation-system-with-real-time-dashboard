#!/usr/bin/env python3
"""
Create a default client for the system.
This fixes the 500 error when admins try to create configs.
"""

from app.db.session import SessionLocal
from app.models.client import Client
from app.models.user import User

def create_default_client():
    """Create a default client if none exists"""
    db = SessionLocal()
    
    try:
        # Check if any clients exist
        existing_clients = db.query(Client).count()
        
        if existing_clients == 0:
            print("No clients found. Creating default client...")
            
            # Create default client
            default_client = Client(
                name="Default Client",
                slug="default-client"
            )
            db.add(default_client)
            db.commit()
            db.refresh(default_client)
            
            print(f"✅ Created default client: ID={default_client.id}, Name='{default_client.name}'")
            
            # Optionally update admin user to use this client
            admin_user = db.query(User).filter(User.email == "admin@example.com").first()
            if admin_user and admin_user.client_id is None:
                admin_user.client_id = default_client.id
                db.commit()
                print(f"✅ Updated admin user to use default client")
            
            return default_client.id
        else:
            print(f"✅ Found {existing_clients} existing clients")
            # Return the first client ID
            first_client = db.query(Client).first()
            return first_client.id
            
    except Exception as e:
        print(f"❌ Error creating default client: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    client_id = create_default_client()
    print(f"Default client ID: {client_id}")