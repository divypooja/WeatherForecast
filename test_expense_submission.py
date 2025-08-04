#!/usr/bin/env python3
"""
Test expense form submission to identify issues
"""

from app import app, db
from models import FactoryExpense, User
from services.hr_accounting_integration import HRAccountingIntegration
from datetime import datetime, date

def test_expense_submission():
    """Test expense submission end-to-end"""
    with app.app_context():
        print("🧪 Testing Expense Submission...")
        
        # Create a test user if needed
        test_user = User.query.filter_by(email='admin@test.com').first()
        if not test_user:
            test_user = User.query.first()
        
        if not test_user:
            print("❌ No users found in database")
            return
        
        print(f"👤 Using test user: {test_user.username}")
        
        # Create a test expense
        test_expense = FactoryExpense(
            expense_number='TEST-001',
            expense_date=date.today(),
            category='Maintenance & Repairs',
            subcategory='Equipment Repair',
            department_code='ACCOUNTS',
            description='Test expense submission',
            amount=100.0,
            tax_amount=0.0,
            total_amount=100.0,
            payment_method='Cash',
            paid_by='Test User',
            vendor_name='Test Vendor',
            status='pending',
            requested_by_id=test_user.id,
            created_at=datetime.utcnow()
        )
        
        try:
            db.session.add(test_expense)
            db.session.commit()
            print(f"✅ Test expense created: {test_expense.expense_number}")
            
            # Test accounting integration
            print("💰 Testing accounting integration...")
            result = HRAccountingIntegration.create_factory_expense_entry(test_expense)
            
            if result:
                print(f"✅ Accounting entry created successfully!")
                return True
            else:
                print("❌ Accounting entry creation failed")
                return False
                
        except Exception as e:
            print(f"❌ Error during test: {str(e)}")
            db.session.rollback()
            return False

if __name__ == '__main__':
    test_expense_submission()