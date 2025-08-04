#!/usr/bin/env python3
"""
Comprehensive migration to add voucher_id columns to all business tables
This fixes the same issue we found in factory_expenses across all forms
"""

from app import app, db
from sqlalchemy import text

def add_voucher_id_to_all_tables():
    """Add voucher_id column to all business tables that need accounting integration"""
    with app.app_context():
        print("🔧 Adding voucher_id columns to all business tables...")
        
        # Define all tables that need voucher_id for accounting integration
        tables_to_fix = [
            'purchase_orders',
            'sales_orders', 
            'grn',
            'production_entries',
            'job_work',
            'job_work_entries',
            'salary_records',
            'invoices',
            'payments',
            'inventory_transactions'
        ]
        
        fixed_tables = []
        errors = []
        
        for table_name in tables_to_fix:
            try:
                # Check if column already exists
                result = db.session.execute(text(f"PRAGMA table_info({table_name})"))
                columns = [row[1] for row in result.fetchall()]
                
                if 'voucher_id' not in columns:
                    print(f"  📋 Adding voucher_id to {table_name}...")
                    db.session.execute(text(f"ALTER TABLE {table_name} ADD COLUMN voucher_id INTEGER"))
                    fixed_tables.append(table_name)
                    print(f"    ✅ Added voucher_id to {table_name}")
                else:
                    print(f"    ✅ {table_name} already has voucher_id column")
                    
            except Exception as e:
                error_msg = f"❌ Error adding voucher_id to {table_name}: {str(e)}"
                errors.append(error_msg)
                print(f"    {error_msg}")
                # Continue with other tables even if one fails
                continue
        
        # Commit all changes
        try:
            db.session.commit()
            print(f"\n🎉 Migration completed successfully!")
            print(f"   Fixed tables: {len(fixed_tables)}")
            print(f"   Tables with errors: {len(errors)}")
            
            if fixed_tables:
                print(f"   Successfully added voucher_id to: {', '.join(fixed_tables)}")
            
            if errors:
                print(f"   Errors encountered:")
                for error in errors:
                    print(f"     {error}")
                    
        except Exception as e:
            print(f"❌ Error committing changes: {str(e)}")
            db.session.rollback()

if __name__ == '__main__':
    add_voucher_id_to_all_tables()