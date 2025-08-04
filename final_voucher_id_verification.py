#!/usr/bin/env python3
"""
Final verification that all critical business tables now have voucher_id columns
"""

from app import app, db
from sqlalchemy import text

def verify_all_voucher_id_columns():
    """Verify all critical business tables have voucher_id columns"""
    with app.app_context():
        print("🔍 Final verification of voucher_id columns across all business tables...")
        
        # All critical business tables that should have voucher_id
        critical_tables = [
            # Core business documents
            'purchase_orders',
            'sales_orders', 
            'grn',
            'invoices',
            'factory_expenses',
            'salary_records',
            
            # Job work and production
            'job_works',
            'job_work_processes',
            'productions',
            'production_batches',
            
            # Employee and HR
            'employee_advances',
            'daily_job_work_entries',
            
            # Inventory and batches
            'batch_movement_ledger',
            'inventory_batches',
            'inventory_valuations',
            
            # Vendor and payments
            'payment_vouchers',
            'vendor_invoices',
            'material_inspections'
        ]
        
        missing_voucher_id = []
        has_voucher_id = []
        table_not_exists = []
        
        for table_name in critical_tables:
            try:
                result = db.session.execute(text(f"PRAGMA table_info({table_name})"))
                columns = [row[1] for row in result.fetchall()]
                
                if 'voucher_id' in columns:
                    has_voucher_id.append(table_name)
                    print(f"  ✅ {table_name} has voucher_id")
                else:
                    missing_voucher_id.append(table_name)
                    print(f"  ❌ {table_name} missing voucher_id")
                    
            except Exception as e:
                if "no such table" in str(e).lower():
                    table_not_exists.append(table_name)
                    print(f"  ⚠️  {table_name} doesn't exist")
                else:
                    print(f"  ❌ Error checking {table_name}: {str(e)}")
        
        print(f"\n📊 Final Summary:")
        print(f"   Tables with voucher_id: {len(has_voucher_id)}")
        print(f"   Tables missing voucher_id: {len(missing_voucher_id)}")
        print(f"   Tables that don't exist: {len(table_not_exists)}")
        
        if missing_voucher_id:
            print(f"\n❌ Still missing voucher_id:")
            for table in missing_voucher_id:
                print(f"     - {table}")
        
        if table_not_exists:
            print(f"\n⚠️  Tables that don't exist (might be optional features):")
            for table in table_not_exists:
                print(f"     - {table}")
        
        if not missing_voucher_id:
            print(f"\n🎉 SUCCESS: All existing critical business tables have voucher_id columns!")
            print(f"   Your ERP system is now fully ready for accounting integration!")
        
        return len(missing_voucher_id) == 0

if __name__ == '__main__':
    verify_all_voucher_id_columns()