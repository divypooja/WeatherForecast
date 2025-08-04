#!/usr/bin/env python3

"""
Migration Script: Add Accounting Integration Fields to PO and SO
Adds accounting-related fields to purchase_orders and sales_orders tables
"""

from app import app, db
from sqlalchemy import text

def run_migration():
    """Run the accounting integration migration"""
    with app.app_context():
        try:
            print("Starting accounting integration migration...")
            
            # Add accounting fields to purchase_orders table
            print("Adding accounting fields to purchase_orders...")
            
            purchase_order_fields = [
                "ALTER TABLE purchase_orders ADD COLUMN supplier_account_id INTEGER REFERENCES accounts(id);",
                "ALTER TABLE purchase_orders ADD COLUMN purchase_commitment_voucher_id INTEGER REFERENCES vouchers(id);",
                "ALTER TABLE purchase_orders ADD COLUMN advance_payment_voucher_id INTEGER REFERENCES vouchers(id);",
                "ALTER TABLE purchase_orders ADD COLUMN advance_amount_paid FLOAT DEFAULT 0.0;",
                "ALTER TABLE purchase_orders ADD COLUMN accounting_status VARCHAR(20) DEFAULT 'pending';"
            ]
            
            for sql in purchase_order_fields:
                try:
                    db.session.execute(text(sql))
                    print(f"✓ Executed: {sql}")
                except Exception as e:
                    if "duplicate column name" in str(e).lower() or "already exists" in str(e).lower():
                        print(f"⚠ Column already exists: {sql}")
                    else:
                        print(f"✗ Error executing: {sql} - {e}")
            
            # Add accounting fields to sales_orders table
            print("Adding accounting fields to sales_orders...")
            
            sales_order_fields = [
                "ALTER TABLE sales_orders ADD COLUMN customer_account_id INTEGER REFERENCES accounts(id);",
                "ALTER TABLE sales_orders ADD COLUMN sales_booking_voucher_id INTEGER REFERENCES vouchers(id);",
                "ALTER TABLE sales_orders ADD COLUMN advance_receipt_voucher_id INTEGER REFERENCES vouchers(id);",
                "ALTER TABLE sales_orders ADD COLUMN sales_voucher_id INTEGER REFERENCES vouchers(id);",
                "ALTER TABLE sales_orders ADD COLUMN advance_amount_received FLOAT DEFAULT 0.0;",
                "ALTER TABLE sales_orders ADD COLUMN accounting_status VARCHAR(20) DEFAULT 'pending';",
                "ALTER TABLE sales_orders ADD COLUMN subtotal FLOAT DEFAULT 0.0;",
                "ALTER TABLE sales_orders ADD COLUMN gst_amount FLOAT DEFAULT 0.0;"
            ]
            
            for sql in sales_order_fields:
                try:
                    db.session.execute(text(sql))
                    print(f"✓ Executed: {sql}")
                except Exception as e:
                    if "duplicate column name" in str(e).lower() or "already exists" in str(e).lower():
                        print(f"⚠ Column already exists: {sql}")
                    else:
                        print(f"✗ Error executing: {sql} - {e}")
            
            # Add GST and accounting fields to sales_order_items table
            print("Adding GST fields to sales_order_items...")
            
            sales_order_item_fields = [
                "ALTER TABLE sales_order_items ADD COLUMN hsn_code VARCHAR(20);",
                "ALTER TABLE sales_order_items ADD COLUMN gst_rate FLOAT DEFAULT 18.0;",
                "ALTER TABLE sales_order_items ADD COLUMN gst_amount FLOAT DEFAULT 0.0;",
                "ALTER TABLE sales_order_items ADD COLUMN taxable_amount FLOAT DEFAULT 0.0;"
            ]
            
            for sql in sales_order_item_fields:
                try:
                    db.session.execute(text(sql))
                    print(f"✓ Executed: {sql}")
                except Exception as e:
                    if "duplicate column name" in str(e).lower() or "already exists" in str(e).lower():
                        print(f"⚠ Column already exists: {sql}")
                    else:
                        print(f"✗ Error executing: {sql} - {e}")
            
            # Commit all changes
            db.session.commit()
            print("✓ Migration completed successfully!")
            
        except Exception as e:
            db.session.rollback()
            print(f"✗ Migration failed: {e}")
            raise

if __name__ == '__main__':
    run_migration()