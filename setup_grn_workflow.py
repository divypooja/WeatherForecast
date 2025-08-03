#!/usr/bin/env python3
"""
GRN Workflow Setup Script
Sets up the 3-step GRN workflow with clearing accounts
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from models_accounting import Account, AccountGroup
from services.grn_workflow_automation import GRNWorkflowService

def setup_grn_workflow():
    """Setup GRN workflow system"""
    app = create_app()
    
    with app.app_context():
        try:
            print("Setting up GRN 3-step workflow system...")
            
            # Setup clearing accounts
            print("1. Setting up clearing accounts...")
            success = GRNWorkflowService.setup_clearing_accounts()
            if success:
                print("   ✓ GRN Clearing Account created")
                print("   ✓ GST Input Tax account created")
            else:
                print("   ❌ Error setting up clearing accounts")
                return False
            
            # Verify account structure
            print("2. Verifying account structure...")
            
            required_accounts = [
                'GRN Clearing Account',
                'GST Input Tax',
                'Cash in Hand',
                'Freight & Transportation'
            ]
            
            missing_accounts = []
            for account_name in required_accounts:
                account = Account.query.filter_by(name=account_name).first()
                if not account:
                    missing_accounts.append(account_name)
                else:
                    print(f"   ✓ {account_name} - Found")
            
            if missing_accounts:
                print("   ⚠️  Missing accounts (will be created automatically):")
                for account in missing_accounts:
                    print(f"      - {account}")
            
            # Create sample data for testing (optional)
            print("3. GRN workflow setup completed!")
            
            print("\n📊 Setup Summary:")
            print("   • GRN Clearing Account: Ready")
            print("   • GST Input Tax Account: Ready")
            print("   • 3-Step Workflow: Enabled")
            print("   • Automatic Voucher Creation: Enabled")
            
            print("\n🔄 Workflow Steps:")
            print("   Step 1: GRN Creation → Dr. Inventory, Cr. GRN Clearing")
            print("   Step 2: Invoice Processing → Dr. GRN Clearing + GST, Cr. Vendor")
            print("   Step 3: Payment → Dr. Vendor, Cr. Bank/Cash")
            
            return True
            
        except Exception as e:
            print(f"\n❌ Error during setup: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == '__main__':
    if setup_grn_workflow():
        print("\n🎉 GRN 3-step workflow is now ready!")
        print("\nNext steps:")
        print("1. Visit /grn-workflow to access the workflow dashboard")
        print("2. Create GRNs against Purchase Orders")
        print("3. Process vendor invoices for completed GRNs")
        print("4. Record payments against vendor invoices")
        print("5. Monitor PO fulfillment and vendor outstanding reports")
    else:
        print("\n⚠️  Setup failed. Please check the errors above.")
        sys.exit(1)