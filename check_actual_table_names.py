#!/usr/bin/env python3
"""
Check what tables actually exist in the database
Some might have different names than expected
"""

from app import app, db
from sqlalchemy import text

def check_actual_tables():
    """Check all tables that actually exist in the database"""
    with app.app_context():
        print("🔍 Checking all actual tables in the database...")
        
        # Get all table names
        result = db.session.execute(text("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"))
        all_tables = [row[0] for row in result.fetchall()]
        
        print(f"Found {len(all_tables)} tables in database:")
        
        # Look for tables that might need voucher_id
        business_related_tables = []
        for table in all_tables:
            # Skip system tables
            if table.startswith('sqlite_'):
                continue
            
            # Look for business-related tables
            if any(keyword in table.lower() for keyword in [
                'job', 'work', 'production', 'payment', 'transaction', 
                'inventory', 'advance', 'entry', 'record'
            ]):
                business_related_tables.append(table)
            
            print(f"  - {table}")
        
        if business_related_tables:
            print(f"\n📋 Business-related tables that might need voucher_id:")
            for table in business_related_tables:
                print(f"  - {table}")
                
                # Check if it has voucher_id column
                try:
                    col_result = db.session.execute(text(f"PRAGMA table_info({table})"))
                    columns = [row[1] for row in col_result.fetchall()]
                    has_voucher_id = 'voucher_id' in columns
                    status = "✅ Has voucher_id" if has_voucher_id else "❌ Missing voucher_id"
                    print(f"    {status}")
                except Exception as e:
                    print(f"    Error checking: {str(e)}")
        
        return all_tables, business_related_tables

if __name__ == '__main__':
    check_actual_tables()