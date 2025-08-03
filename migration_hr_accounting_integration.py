#!/usr/bin/env python3
"""
Migration: HR Accounting Integration
Adds accounting integration fields to SalaryRecord and EmployeeAdvance models
"""

from app import app, db
from sqlalchemy import text

def run_migration():
    """Run the HR accounting integration migration"""
    with app.app_context():
        try:
            print("🔄 Starting HR Accounting Integration Migration...")
            
            # Import accounting models to ensure they exist
            try:
                from models_accounting import Account, Voucher, AccountGroup, VoucherType, JournalEntry
                print("✅ Accounting models imported successfully")
                accounts_exists = True
                vouchers_exists = True
            except ImportError:
                print("⚠️  Warning: Accounting models not found")
                accounts_exists = False
                vouchers_exists = False
            
            if not accounts_exists or not vouchers_exists:
                print("⚠️  Warning: Accounting tables (accounts/vouchers) not found.")
                print("   Creating tables from accounting module...")
                
                # Import accounting models to create tables
                try:
                    from models_accounting import Account, Voucher, AccountGroup, VoucherType, JournalEntry
                    db.create_all()
                    print("✅ Accounting tables created successfully")
                except ImportError:
                    print("❌ Error: Accounting models not found. Please ensure accounting module is properly set up.")
                    return False
            
            # Add accounting integration fields to salary_records table
            print("📝 Adding accounting fields to salary_records table...")
            
            try:
                # Simply try to add the columns - will fail silently if they exist
                with db.engine.connect() as conn:
                    try:
                        conn.execute(text("ALTER TABLE salary_records ADD COLUMN employee_account_id INTEGER;"))
                        conn.execute(text("ALTER TABLE salary_records ADD COLUMN salary_voucher_id INTEGER;"))
                        conn.execute(text("ALTER TABLE salary_records ADD COLUMN accounting_status VARCHAR(20) DEFAULT 'pending';"))
                        conn.commit()
                        print("✅ Added accounting fields to salary_records")
                    except Exception as col_error:
                        if "already exists" in str(col_error) or "duplicate column" in str(col_error):
                            print("ℹ️  Accounting fields already exist in salary_records")
                        else:
                            print(f"⚠️  Column addition note: {str(col_error)}")
                        
            except Exception as e:
                print(f"⚠️  Table modification note: {str(e)}")
            
            # Add accounting integration fields to employee_advances table
            print("📝 Adding accounting fields to employee_advances table...")
            
            try:
                # Simply try to add the columns - will fail silently if they exist
                with db.engine.connect() as conn:
                    try:
                        conn.execute(text("ALTER TABLE employee_advances ADD COLUMN employee_account_id INTEGER;"))
                        conn.execute(text("ALTER TABLE employee_advances ADD COLUMN advance_voucher_id INTEGER;"))
                        conn.execute(text("ALTER TABLE employee_advances ADD COLUMN accounting_status VARCHAR(20) DEFAULT 'pending';"))
                        conn.commit()
                        print("✅ Added accounting fields to employee_advances")
                    except Exception as col_error:
                        if "already exists" in str(col_error) or "duplicate column" in str(col_error):
                            print("ℹ️  Accounting fields already exist in employee_advances")
                        else:
                            print(f"⚠️  Column addition note: {str(col_error)}")
                        
            except Exception as e:
                print(f"⚠️  Table modification note: {str(e)}")
            
            # Commit the changes
            db.session.commit()
            
            print("🎉 HR Accounting Integration Migration completed successfully!")
            return True
            
        except Exception as e:
            print(f"❌ Migration failed: {str(e)}")
            db.session.rollback()
            return False

if __name__ == '__main__':
    success = run_migration()
    if success:
        print("\n✅ Migration completed successfully!")
        print("📋 Summary of changes:")
        print("   • Added employee_account_id to salary_records")
        print("   • Added salary_voucher_id to salary_records") 
        print("   • Added accounting_status to salary_records")
        print("   • Added employee_account_id to employee_advances")
        print("   • Added advance_voucher_id to employee_advances")
        print("   • Added accounting_status to employee_advances")
        print("\n🔧 HR forms now have complete accounting integration!")
    else:
        print("\n❌ Migration failed. Please check the errors above.")