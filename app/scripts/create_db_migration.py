#!/usr/bin/env python3
"""
Add scheduling columns to client_configs table
"""

from app.db.session import SessionLocal, engine
from sqlalchemy import text

def add_scheduling_columns():
    """Add scheduling columns to existing client_configs table"""
    
    db = SessionLocal()
    
    try:
        print("Adding scheduling columns to client_configs table...")
        
        # Add new columns with default values
        columns_to_add = [
            "ALTER TABLE client_configs ADD COLUMN IF NOT EXISTS scan_interval_minutes INTEGER DEFAULT 5",
            "ALTER TABLE client_configs ADD COLUMN IF NOT EXISTS scan_start_hour INTEGER DEFAULT 0", 
            "ALTER TABLE client_configs ADD COLUMN IF NOT EXISTS scan_end_hour INTEGER DEFAULT 23",
            "ALTER TABLE client_configs ADD COLUMN IF NOT EXISTS scan_days VARCHAR(20) DEFAULT '1,2,3,4,5,6,7'"
        ]
        
        for sql in columns_to_add:
            try:
                db.execute(text(sql))
                print(f"✅ Executed: {sql}")
            except Exception as e:
                print(f"⚠️  Column might already exist: {e}")
        
        db.commit()
        print("✅ All scheduling columns added successfully!")
        
    except Exception as e:
        print(f"❌ Error adding columns: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    add_scheduling_columns()