#!/usr/bin/env python3
"""
Fix voucher_id columns for the actual tables that exist in the database
Based on the real table names discovered
"""

from app import app, db
from sqlalchemy import text

def add_voucher_id_to_remaining_tables():
    """Add voucher_id column to remaining business tables that need accounting integration"""
    with app.app_context():
        print("🔧 Adding voucher_id columns to remaining business tables...")
        
        # Define tables that exist and need voucher_id for accounting integration
        tables_to_fix = [
            'job_works',                    # Main job work table
            'job_work_processes',           # Individual job work process steps
            'job_work_team_assignments',    # Team assignments for job work
            'productions',                  # Production entries
            'production_batches',           # Production batch tracking
            'employee_advances',            # Employee advance payments
            'daily_job_work_entries',       # Daily job work entries
            'batch_movement_ledger',        # Inventory transactions/movements
            'inventory_batches',            # Inventory batch records
            'inventory_valuations',         # Inventory valuation records
            'payment_vouchers',             # Payment vouchers (might already have it)
            'vendor_invoices',              # Vendor invoices
            'material_inspections',         # Material inspection records
        ]
        
        fixed_tables = []
        already_has_voucher_id = []
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
                    already_has_voucher_id.append(table_name)
                    print(f"    ✅ {table_name} already has voucher_id column")
                    
            except Exception as e:
                if "no such table" in str(e).lower():
                    print(f"    ⚠️  Table {table_name} doesn't exist (might be optional feature)")
                else:
                    error_msg = f"❌ Error adding voucher_id to {table_name}: {str(e)}"
                    errors.append(error_msg)
                    print(f"    {error_msg}")
                continue
        
        # Commit all changes
        try:
            db.session.commit()
            print(f"\n🎉 Migration completed successfully!")
            print(f"   Fixed tables: {len(fixed_tables)}")
            print(f"   Already had voucher_id: {len(already_has_voucher_id)}")
            print(f"   Tables with errors: {len(errors)}")
            
            if fixed_tables:
                print(f"   Successfully added voucher_id to: {', '.join(fixed_tables)}")
            
            if already_has_voucher_id:
                print(f"   Already had voucher_id: {', '.join(already_has_voucher_id)}")
                
            if errors:
                print(f"   Errors encountered:")
                for error in errors:
                    print(f"     {error}")
                    
        except Exception as e:
            print(f"❌ Error committing changes: {str(e)}")
            db.session.rollback()

if __name__ == '__main__':
    add_voucher_id_to_remaining_tables()