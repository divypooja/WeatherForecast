#!/usr/bin/env python3
"""
Setup HR Accounts in Existing Accounting System
Run this script to initialize HR-specific accounts for integration
"""

from app import app, db
from services.hr_accounting_integration import HRAccountingIntegration

def setup_hr_accounts():
    """Setup HR accounts in the existing accounting system"""
    with app.app_context():
        print("Setting up HR accounts in existing accounting system...")
        
        success = HRAccountingIntegration.setup_hr_accounts()
        
        if success:
            print("✅ HR accounts setup completed successfully!")
            print("\nCreated accounts:")
            print("- Salaries & Wages (SAL_WAGES)")
            print("- Employee Advances (EMP_ADV)")
            print("- Factory Overhead (FACT_OH)")
            print("- Employee Benefits (EMP_BEN)")
            print("\nHR system is now integrated with accounting!")
        else:
            print("❌ Failed to setup HR accounts.")
            print("Please check the logs for more details.")

if __name__ == '__main__':
    setup_hr_accounts()