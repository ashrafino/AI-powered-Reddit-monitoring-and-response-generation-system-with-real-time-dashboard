# EMERGENCY FIX - Run This Now

## Problem
Your admin user doesn't have a `client_id`, causing 401 errors everywhere.

## Solution
Run these commands on the server **RIGHT NOW**:

```bash
# SSH into server
ssh root@164.90.222.87

# Go to project
cd /home/deploy/apps/reddit-bot

# Run this Python script to fix everything
docker-compose exec backend python << 'EOF'
from app.db.session import SessionLocal
from app.models.client import Client
from app.models.user import User

db = SessionLocal()

print("=" * 50)
print("EMERGENCY FIX - Admin Client Assignment")
print("=" * 50)

try:
    # Step 1: Get or create default client
    client = db.query(Client).first()
    if not client:
        print("\n1. Creating default client...")
        client = Client(name="Default Client", slug="default-client")
        db.add(client)
        db.commit()
        db.refresh(client)
        print(f"   ✅ Created: {client.name} (ID: {client.id})")
    else:
        print(f"\n1. ✅ Found client: {client.name} (ID: {client.id})")
    
    # Step 2: Update admin user
    admin = db.query(User).filter(User.email == "admin@example.com").first()
    if admin:
        print(f"\n2. Admin user found: {admin.email}")
        print(f"   Current client_id: {admin.client_id}")
        print(f"   Role: {admin.role}")
        
        if admin.client_id != client.id:
            admin.client_id = client.id
            db.commit()
            print(f"   ✅ FIXED! Admin now assigned to client ID: {client.id}")
        else:
            print(f"   ✅ Admin already has correct client ID")
    else:
        print("\n2. ❌ ERROR: Admin user not found!")
        print("   Creating admin user...")
        from app.core.security import get_password_hash
        admin = User(
            email="admin@example.com",
            hashed_password=get_password_hash("admin123"),
            role="admin",
            is_active=True,
            client_id=client.id
        )
        db.add(admin)
        db.commit()
        print(f"   ✅ Created admin with client ID: {client.id}")
    
    # Step 3: Verify
    print("\n3. Verification:")
    admin = db.query(User).filter(User.email == "admin@example.com").first()
    print(f"   Email: {admin.email}")
    print(f"   Role: {admin.role}")
    print(f"   Client ID: {admin.client_id}")
    print(f"   Active: {admin.is_active}")
    
    print("\n" + "=" * 50)
    print("✅ FIX COMPLETE!")
    print("=" * 50)
    print("\nNEXT STEPS:")
    print("1. Go to: http://143.198.246.19:3000")
    print("2. LOGOUT (click Logout button)")
    print("3. LOGIN again:")
    print("   Email: admin@example.com")
    print("   Password: admin123")
    print("4. You should now see all pages working!")
    print("\n")
        
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
    db.rollback()
finally:
    db.close()
EOF
```

## After Running the Script

1. **LOGOUT** from the web app
2. **LOGIN** again with:
   - Email: `admin@example.com`
   - Password: `admin123`
3. Try accessing:
   - Dashboard
   - Configs
   - Clients

Everything should work now!

## If It Still Doesn't Work

Clear your browser cache and cookies:
- Chrome: Ctrl+Shift+Delete
- Firefox: Ctrl+Shift+Delete
- Safari: Cmd+Option+E

Then login again.
