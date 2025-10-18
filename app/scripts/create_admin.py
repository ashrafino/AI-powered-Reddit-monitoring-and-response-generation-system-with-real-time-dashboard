import os
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.user import User
from app.core.security import get_password_hash
from app.scripts.db import create_tables

def create_initial_admin():
    # Create database tables first
    create_tables()
    
    db = SessionLocal()
    try:
        # Get admin credentials from environment
        admin_email = os.getenv("ADMIN_EMAIL", "admin@example.com")
        admin_password = os.getenv("ADMIN_PASSWORD", "admin123")

        # Check if admin already exists
        admin = db.query(User).filter(User.email == admin_email).first()
        if admin:
            print(f"Admin user already exists: {admin_email}")
            
            # Make sure admin has a client_id if one exists
            from app.models.client import Client
            if not admin.client_id:
                first_client = db.query(Client).first()
                if first_client:
                    admin.client_id = first_client.id
                    db.commit()
                    print(f"✅ Assigned admin to client ID: {first_client.id}")
            return

        # Get first client if exists (for admin assignment)
        from app.models.client import Client
        first_client = db.query(Client).first()
        client_id = first_client.id if first_client else None

        # Create admin user with bcrypt hash
        admin = User(
            email=admin_email,
            hashed_password=get_password_hash(admin_password),
            role="admin",
            is_active=True,
            client_id=client_id  # Assign to first client if exists
        )
        db.add(admin)
        db.commit()
        
        if client_id:
            print(f"✅ Created admin user: {admin_email} (assigned to client ID: {client_id})")
        else:
            print(f"✅ Created admin user: {admin_email} (no client assigned yet)")
    finally:
        db.close()

if __name__ == "__main__":
    create_initial_admin()