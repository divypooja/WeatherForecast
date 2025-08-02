#!/usr/bin/env python3
"""
Setup accounting system with default accounts and data
"""
import os
from main import app

def setup_accounting_system():
    """Initialize the complete accounting system"""
    with app.app_context():
        from services.accounting_automation import AccountingAutomation
        from models_accounting import AccountGroup, Account, VoucherType, TaxMaster
        from models import CompanySettings
        from app import db
        
        print("🔄 Setting up Accounting System...")
        
        # Step 1: Setup default chart of accounts
        print("📊 Creating Chart of Accounts...")
        success = AccountingAutomation.setup_default_accounts()
        if success:
            print("✅ Chart of Accounts created successfully!")
        else:
            print("❌ Error creating Chart of Accounts")
            return False
        
        # Step 2: Setup GST tax rates
        print("💰 Setting up GST Tax Rates...")
        try:
            common_gst_rates = [
                {'hsn_sac_code': '7326', 'description': 'Iron and Steel Products', 'igst_rate': 18.0, 'cgst_rate': 9.0, 'sgst_rate': 9.0, 'tax_category': 'goods'},
                {'hsn_sac_code': '8481', 'description': 'Taps, Cocks, Valves', 'igst_rate': 18.0, 'cgst_rate': 9.0, 'sgst_rate': 9.0, 'tax_category': 'goods'},
                {'hsn_sac_code': '9995', 'description': 'Job Work Services', 'igst_rate': 18.0, 'cgst_rate': 9.0, 'sgst_rate': 9.0, 'tax_category': 'services'},
                {'hsn_sac_code': '7208', 'description': 'Flat-rolled products of iron', 'igst_rate': 18.0, 'cgst_rate': 9.0, 'sgst_rate': 9.0, 'tax_category': 'goods'},
                {'hsn_sac_code': '7219', 'description': 'Flat-rolled products of stainless steel', 'igst_rate': 18.0, 'cgst_rate': 9.0, 'sgst_rate': 9.0, 'tax_category': 'goods'},
                {'hsn_sac_code': '0000', 'description': 'Exempted Items', 'igst_rate': 0.0, 'cgst_rate': 0.0, 'sgst_rate': 0.0, 'tax_category': 'goods'},
            ]
            
            for tax_data in common_gst_rates:
                existing_tax = TaxMaster.query.filter_by(hsn_sac_code=tax_data['hsn_sac_code']).first()
                if not existing_tax:
                    tax_master = TaxMaster(**tax_data)
                    db.session.add(tax_master)
            
            db.session.commit()
            print("✅ GST Tax Rates setup completed!")
            
        except Exception as e:
            print(f"❌ Error setting up tax rates: {str(e)}")
            db.session.rollback()
        
        # Step 3: Verify company settings for GST compliance
        print("🏢 Checking Company Settings...")
        try:
            company = CompanySettings.query.first()
            if not company:
                company = CompanySettings(
                    company_name="AK Innovations",
                    address_line1="Your Factory Address",
                    city="Your City",
                    state="Your State",
                    gst_number="XXAABCRXXXXMXZC"
                )
                db.session.add(company)
                db.session.commit()
                print("✅ Company settings created!")
            else:
                print("✅ Company settings already exist!")
                
        except Exception as e:
            print(f"❌ Error with company settings: {str(e)}")
            db.session.rollback()
        
        # Step 4: Display summary
        print("\n📋 Accounting System Setup Summary:")
        print(f"   Account Groups: {AccountGroup.query.count()}")
        print(f"   Accounts: {Account.query.count()}")
        print(f"   Voucher Types: {VoucherType.query.count()}")
        print(f"   Tax Rates: {TaxMaster.query.count()}")
        
        print("\n🎉 Accounting System Setup Complete!")
        print("\n📚 Available Modules:")
        print("   • Chart of Accounts Management")
        print("   • Voucher & Journal Entry System")
        print("   • Automatic Transaction Recording")
        print("   • GST-Compliant Invoicing")
        print("   • Financial Reports (Trial Balance, P&L, Balance Sheet)")
        print("   • Bank & Cash Management")
        print("   • Integration with Purchase, Sales, Job Work, and Expenses")
        
        print("\n🔗 Access the Accounting Dashboard at: /accounting/dashboard")
        
        return True

if __name__ == '__main__':
    setup_accounting_system()