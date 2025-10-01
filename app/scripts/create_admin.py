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
            return

        # Create admin user with bcrypt hash
        admin = User(
            email=admin_email,
            hashed_password=get_password_hash(admin_password),
            role="admin",
            is_active=True
        )
        db.add(admin)
        db.commit()
        print("Created admin user: admin@example.com")
    finally:
        db.close()

if __name__ == "__main__":
    create_initial_admin()