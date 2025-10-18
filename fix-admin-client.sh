#!/bin/bash

# Fix admin user client assignment
# Run this on the server to fix the authentication issue

echo "🔧 Fixing admin user client assignment..."

cd /home/deploy/apps/reddit-bot

# Create default client and assign admin to it
docker-compose exec -T backend python << 'EOF'
from app.db.session import SessionLocal
from app.models.client import Client
from app.models.user import User

db = SessionLocal()

try:
    # Get or create default client
    client = db.query(Client).first()
    if not client:
        print("Creating default client...")
        client = Client(name="Default Client", slug="default-client")
        db.add(client)
        db.commit()
        db.refresh(client)
        print(f"✅ Created client: {client.name} (ID: {client.id})")
    else:
        print(f"✅ Found existing client: {client.name} (ID: {client.id})")
    
    # Update admin user to use this client
    admin = db.query(User).filter(User.email == "admin@example.com").first()
    if admin:
        if admin.client_id != client.id:
            admin.client_id = client.id
            db.commit()
            print(f"✅ Updated admin user to use client ID: {client.id}")
        else:
            print(f"✅ Admin already assigned to client ID: {client.id}")
    else:
        print("❌ Admin user not found!")
        
except Exception as e:
    print(f"❌ Error: {e}")
    db.rollback()
finally:
    db.close()

print("\n✅ Done! Please logout and login again to get a new token.")
EOF

echo ""
echo "🔄 Next steps:"
echo "1. Go to http://143.198.246.19:3000"
echo "2. Logout (if logged in)"
echo "3. Login again with admin@example.com / admin123"
echo "4. You should now be able to access all pages"
