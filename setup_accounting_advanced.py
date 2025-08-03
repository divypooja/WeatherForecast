#!/usr/bin/env python3
"""
Advanced Accounting Setup Script
Creates advanced accounting configuration, cost centers, and default settings
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from models_accounting import Account, AccountGroup
from models_accounting_settings import AdvancedAccountingSettings, CostCenter, PaymentMethod, LedgerMapping
from services.accounting_automation import AccountingAutomation

def setup_advanced_accounting():
    """Setup advanced accounting features"""
    app = create_app()
    
    with app.app_context():
        try:
            print("Setting up advanced accounting configuration...")
            
            # Create accounting settings
            print("1. Creating default accounting settings...")
            settings = AdvancedAccountingSettings.get_settings()
            if not settings.gst_number:
                settings.gst_number = "SAMPLE123456789"
                settings.place_of_business = "Mumbai, Maharashtra"
                settings.default_gst_rate = 18.0
                settings.inventory_valuation_method = "moving_average"
                db.session.commit()
                print("   ✓ Default settings configured")
            
            # Create cost centers
            print("2. Setting up cost centers...")
            default_cost_centers = [
                {
                    'name': 'Production Department',
                    'code': 'PROD',
                    'description': 'Manufacturing and production activities',
                    'monthly_budget': 500000.00,
                    'yearly_budget': 6000000.00
                },
                {
                    'name': 'Quality Control',
                    'code': 'QC',
                    'description': 'Quality assurance and testing',
                    'monthly_budget': 100000.00,
                    'yearly_budget': 1200000.00
                },
                {
                    'name': 'Maintenance',
                    'code': 'MAINT',
                    'description': 'Equipment and facility maintenance',
                    'monthly_budget': 150000.00,
                    'yearly_budget': 1800000.00
                },
                {
                    'name': 'Administration',
                    'code': 'ADMIN',
                    'description': 'Administrative and overhead expenses',
                    'monthly_budget': 200000.00,
                    'yearly_budget': 2400000.00
                },
                {
                    'name': 'Research & Development',
                    'code': 'RND',
                    'description': 'Product development and innovation',
                    'monthly_budget': 300000.00,
                    'yearly_budget': 3600000.00
                }
            ]
            
            for center_data in default_cost_centers:
                existing = CostCenter.query.filter_by(code=center_data['code']).first()
                if not existing:
                    center = CostCenter(**center_data)
                    db.session.add(center)
                    print(f"   ✓ Created cost center: {center_data['name']}")
            
            # Create payment methods
            print("3. Setting up payment methods...")
            
            # First, ensure we have default accounts
            cash_account = Account.query.filter_by(name='Cash in Hand').first()
            bank_account = Account.query.filter_by(name='Bank Account').first()
            
            if cash_account and bank_account:
                default_payment_methods = [
                    {
                        'name': 'Cash Payment',
                        'code': 'CASH',
                        'method_type': 'cash',
                        'account_id': cash_account.id,
                        'auto_reconcile': True
                    },
                    {
                        'name': 'Bank Transfer',
                        'code': 'BANK',
                        'method_type': 'bank',
                        'account_id': bank_account.id,
                        'requires_reference': True
                    },
                    {
                        'name': 'UPI Payment',
                        'code': 'UPI',
                        'method_type': 'upi',
                        'account_id': bank_account.id,
                        'requires_reference': True,
                        'processing_fee_rate': 0.5
                    },
                    {
                        'name': 'Cheque Payment',
                        'code': 'CHQ',
                        'method_type': 'cheque',
                        'account_id': bank_account.id,
                        'requires_reference': True
                    }
                ]
                
                for method_data in default_payment_methods:
                    existing = PaymentMethod.query.filter_by(code=method_data['code']).first()
                    if not existing:
                        method = PaymentMethod(**method_data)
                        db.session.add(method)
                        print(f"   ✓ Created payment method: {method_data['name']}")
            
            # Create default ledger mappings
            print("4. Setting up default ledger mappings...")
            
            # Map suppliers to default accounts
            suppliers_group = AccountGroup.query.filter_by(name='Sundry Creditors').first()
            customers_group = AccountGroup.query.filter_by(name='Sundry Debtors').first()
            
            if suppliers_group and customers_group:
                supplier_account = Account.query.filter_by(account_group_id=suppliers_group.id).first()
                customer_account = Account.query.filter_by(account_group_id=customers_group.id).first()
                
                if supplier_account and customer_account:
                    default_mappings = [
                        {
                            'entity_type': 'supplier',
                            'entity_name': 'Default Supplier Mapping',
                            'payable_account_id': supplier_account.id,
                            'expense_account_id': Account.query.filter_by(name='Purchase Account').first().id if Account.query.filter_by(name='Purchase Account').first() else None
                        },
                        {
                            'entity_type': 'customer',
                            'entity_name': 'Default Customer Mapping',
                            'receivable_account_id': customer_account.id,
                            'income_account_id': Account.query.filter_by(name='Sales Account').first().id if Account.query.filter_by(name='Sales Account').first() else None
                        }
                    ]
                    
                    for mapping_data in default_mappings:
                        if mapping_data.get('expense_account_id') or mapping_data.get('income_account_id'):
                            existing = LedgerMapping.query.filter_by(
                                entity_type=mapping_data['entity_type'],
                                entity_name=mapping_data['entity_name']
                            ).first()
                            if not existing:
                                mapping = LedgerMapping(**mapping_data)
                                db.session.add(mapping)
                                print(f"   ✓ Created ledger mapping: {mapping_data['entity_name']}")
            
            db.session.commit()
            print("\n✅ Advanced accounting setup completed successfully!")
            
            # Print summary
            print("\n📊 Setup Summary:")
            print(f"   • Accounting Settings: Configured")
            print(f"   • Cost Centers: {CostCenter.query.count()}")
            print(f"   • Payment Methods: {PaymentMethod.query.count()}")
            print(f"   • Ledger Mappings: {LedgerMapping.query.count()}")
            
            return True
            
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ Error during setup: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == '__main__':
    if setup_advanced_accounting():
        print("\n🎉 Advanced accounting features are now ready to use!")
        print("\nNext steps:")
        print("1. Visit /accounting/settings to configure specific settings")
        print("2. Set up inventory valuation methods")
        print("3. Configure automatic voucher posting rules")
        print("4. Create department-specific cost centers")
    else:
        print("\n⚠️  Setup failed. Please check the errors above.")
        sys.exit(1)