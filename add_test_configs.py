#!/usr/bin/env python3
"""
Add test configurations for Reddit scanning
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app.db.session import SessionLocal
from app.models.config import ClientConfig
from app.models.client import Client

def add_test_configs():
    db = SessionLocal()
    
    try:
        # Check if client exists, create if not
        client = db.query(Client).filter(Client.id == 1).first()
        if not client:
            client = Client(
                id=1,
                name="Test Client",
                email="test@example.com",
                is_active=True
            )
            db.add(client)
            db.commit()
            print(f"✓ Created test client: {client.name}")
        else:
            print(f"✓ Using existing client: {client.name}")
        
        # Test configurations with different niches
        test_configs = [
            {
                "client_id": 1,
                "reddit_subreddits": "AskReddit,explainlikeimfive,NoStupidQuestions",
                "keywords": "how to,what is,why does,explain,help,question",
                "is_active": True
            },
            {
                "client_id": 1,
                "reddit_subreddits": "learnprogramming,webdev,javascript,python",
                "keywords": "tutorial,learn,beginner,help,error,problem,how do i",
                "is_active": True
            },
            {
                "client_id": 1,
                "reddit_subreddits": "fitness,loseit,bodyweightfitness",
                "keywords": "workout,diet,weight loss,exercise,routine,beginner",
                "is_active": True
            },
            {
                "client_id": 1,
                "reddit_subreddits": "personalfinance,investing,financialindependence",
                "keywords": "budget,save money,invest,retirement,debt,advice",
                "is_active": True
            },
            {
                "client_id": 1,
                "reddit_subreddits": "technology,gadgets,android,apple",
                "keywords": "review,recommend,best,which,should i buy,comparison",
                "is_active": True
            }
        ]
        
        # Delete existing configs for client 1 to avoid duplicates
        existing = db.query(ClientConfig).filter(ClientConfig.client_id == 1).all()
        if existing:
            for cfg in existing:
                db.delete(cfg)
            db.commit()
            print(f"✓ Removed {len(existing)} existing configs")
        
        # Add new configs
        created = 0
        for config_data in test_configs:
            config = ClientConfig(**config_data)
            db.add(config)
            created += 1
        
        db.commit()
        print(f"\n✓ Successfully created {created} test configurations!")
        print("\nConfigurations added:")
        
        configs = db.query(ClientConfig).filter(ClientConfig.client_id == 1).all()
        for cfg in configs:
            print(f"\n  Config #{cfg.id}")
            print(f"  Subreddits: {cfg.reddit_subreddits}")
            print(f"  Keywords: {cfg.keywords}")
            print(f"  Active: {cfg.is_active}")
        
        print("\n✓ Ready to scan! Go to the dashboard and click 'Scan now'")
        
    except Exception as e:
        print(f"✗ Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    add_test_configs()
