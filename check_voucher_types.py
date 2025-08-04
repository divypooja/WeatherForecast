#!/usr/bin/env python3
"""
Check available voucher types in the accounting system
"""

from app import app, db
from models_accounting import VoucherType

def check_voucher_types():
    """Check what voucher types are available"""
    with app.app_context():
        print("🔍 Checking available voucher types...")
        
        voucher_types = VoucherType.query.all()
        if voucher_types:
            print(f"Found {len(voucher_types)} voucher types:")
            for vt in voucher_types:
                print(f"  - Code: {vt.code}, Name: {vt.name}")
        else:
            print("❌ No voucher types found in database")
            
            # Create basic voucher types
            print("Creating basic voucher types...")
            basic_types = [
                {'code': 'JNL', 'name': 'Journal Entry', 'description': 'General journal entries'},
                {'code': 'PAY', 'name': 'Payment', 'description': 'Payment vouchers'},
                {'code': 'REC', 'name': 'Receipt', 'description': 'Receipt vouchers'},
                {'code': 'CON', 'name': 'Contra', 'description': 'Contra vouchers'},
                {'code': 'PUR', 'name': 'Purchase', 'description': 'Purchase vouchers'},
                {'code': 'SAL', 'name': 'Sales', 'description': 'Sales vouchers'}
            ]
            
            for vt_data in basic_types:
                vt = VoucherType(
                    code=vt_data['code'],
                    name=vt_data['name'],
                    description=vt_data['description']
                )
                db.session.add(vt)
            
            try:
                db.session.commit()
                print("✅ Created basic voucher types")
            except Exception as e:
                print(f"❌ Error creating voucher types: {str(e)}")
                db.session.rollback()

if __name__ == '__main__':
    check_voucher_types()