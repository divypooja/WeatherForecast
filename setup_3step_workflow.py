#!/usr/bin/env python3
"""
Setup script for 3-Step GRN Workflow with Clearing Accounts
This implements the proper SO/PO to accounts connection process.

Flow:
1. GRN → Dr. Inventory, Cr. GRN Clearing A/c (2150)
2. Invoice → Dr. GRN Clearing + GST Input Tax (1180), Cr. Vendor
3. Payment → Dr. Vendor, Cr. Bank/Cash
"""

from app import app, db
from models_accounting import Account, AccountGroup, VoucherType
from services.grn_workflow_automation import GRNWorkflowService

def setup_clearing_accounts():
    """Setup required clearing accounts for proper 3-step workflow"""
    try:
        with app.app_context():
            print("Setting up 3-Step GRN Workflow clearing accounts...")
            
            # Setup clearing accounts using the service
            success = GRNWorkflowService.setup_clearing_accounts()
            
            if success:
                print("✅ GRN Clearing Account (2150) created/verified")
                print("✅ GST Input Tax Account (1180) created/verified")
            else:
                print("❌ Failed to setup clearing accounts")
                return False
            
            # Setup required voucher types
            voucher_types = [
                {'name': 'GRN Material Receipt', 'code': 'GRNMR', 'description': 'Material received against GRN'},
                {'name': 'Vendor Invoice', 'code': 'VINV', 'description': 'Vendor invoice for clearing GRN'},
                {'name': 'Payment Voucher', 'code': 'PAY', 'description': 'Payment to vendor'},
                {'name': 'Sales Delivery', 'code': 'COGS', 'description': 'Cost of goods sold on delivery'},
                {'name': 'Customer Receipt', 'code': 'REC', 'description': 'Receipt from customer'}
            ]
            
            for vt_data in voucher_types:
                voucher_type = VoucherType.query.filter_by(code=vt_data['code']).first()
                if not voucher_type:
                    voucher_type = VoucherType(
                        name=vt_data['name'],
                        code=vt_data['code'],
                        description=vt_data['description']
                    )
                    db.session.add(voucher_type)
                    print(f"✅ Created voucher type: {vt_data['name']}")
                else:
                    print(f"✅ Voucher type exists: {vt_data['name']}")
            
            db.session.commit()
            print("\n🎉 3-Step GRN Workflow setup completed successfully!")
            print("\n📊 Workflow Summary:")
            print("Step 1: GRN Creation → Dr. Inventory, Cr. GRN Clearing A/c (2150)")
            print("Step 2: Vendor Invoice → Dr. GRN Clearing + GST Input Tax (1180), Cr. Vendor")
            print("Step 3: Payment → Dr. Vendor, Cr. Bank/Cash")
            print("\n🔄 Sales Flow:")
            print("Delivery → Dr. COGS, Cr. Finished Goods")
            print("Invoice → Dr. Customer, Cr. Sales + GST Output")
            print("Receipt → Dr. Bank, Cr. Customer")
            
            return True
            
    except Exception as e:
        print(f"❌ Error setting up 3-step workflow: {e}")
        db.session.rollback()
        return False

def verify_workflow_setup():
    """Verify that all required accounts and voucher types exist"""
    try:
        with app.app_context():
            print("\n🔍 Verifying 3-Step Workflow setup...")
            
            # Check required accounts
            required_accounts = [
                ('2150', 'GRN Clearing Account'),
                ('1180', 'GST Input Tax'),
                ('RM_INV', 'Raw Material Inventory'),
                ('FG_INV', 'Finished Goods Inventory'),
                ('SALES', 'Sales Account'),
                ('COGS', 'Cost of Goods Sold')
            ]
            
            for code, name in required_accounts:
                account = Account.query.filter_by(code=code).first()
                if account:
                    print(f"✅ {name} ({code}): {account.name}")
                else:
                    print(f"❌ Missing: {name} ({code})")
            
            # Check voucher types
            required_voucher_types = [
                ('GRNMR', 'GRN Material Receipt'),
                ('VINV', 'Vendor Invoice'),
                ('PAY', 'Payment Voucher'),
                ('COGS', 'Sales Delivery'),
                ('REC', 'Customer Receipt')
            ]
            
            print("\n📄 Voucher Types:")
            for code, name in required_voucher_types:
                vt = VoucherType.query.filter_by(code=code).first()
                if vt:
                    print(f"✅ {name} ({code}): {vt.name}")
                else:
                    print(f"❌ Missing: {name} ({code})")
            
            print("\n✅ Verification completed!")
            
    except Exception as e:
        print(f"❌ Error during verification: {e}")

if __name__ == "__main__":
    print("🚀 Setting up 3-Step GRN Workflow for Factory Management System")
    print("=" * 60)
    
    if setup_clearing_accounts():
        verify_workflow_setup()
    else:
        print("❌ Setup failed!")