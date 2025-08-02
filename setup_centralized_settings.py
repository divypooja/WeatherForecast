#!/usr/bin/env python3
"""
Setup script for Centralized Settings System
Creates default companies, settings, and initializes the multi-company infrastructure
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from models_settings import (
    Company, SystemSettings, InventorySettings, AccountingSettings, 
    ProductionSettings, JobWorkSettings, DEFAULT_SETTINGS
)
from models import User

def create_default_company():
    """Create a default company if none exists"""
    existing_company = Company.query.first()
    if existing_company:
        print(f"Company already exists: {existing_company.name}")
        return existing_company
    
    # Create default company
    company = Company(
        name="AK Innovations",
        code="MAIN",
        address_line1="Factory Address Line 1",
        city="Your City",
        state="Your State",
        gst_number="27ABCDE1234F1Z5",
        is_default=True,
        is_active=True
    )
    
    db.session.add(company)
    db.session.commit()
    print(f"Created default company: {company.name}")
    return company

def create_system_settings(company_id=None):
    """Create default system settings"""
    print("Creating default system settings...")
    
    for category, settings in DEFAULT_SETTINGS.items():
        for key, (value, data_type, description) in settings.items():
            # Check if setting already exists
            existing = SystemSettings.query.filter_by(
                category=category,
                setting_key=key,
                company_id=company_id,
                is_global=company_id is None
            ).first()
            
            if not existing:
                setting = SystemSettings(
                    category=category,
                    setting_key=key,
                    setting_value=value,
                    data_type=data_type,
                    description=description,
                    company_id=company_id,
                    is_global=company_id is None
                )
                db.session.add(setting)
                print(f"  Created {category}.{key} = {value}")
    
    db.session.commit()

def create_detailed_settings(company_id):
    """Create detailed settings models for the company"""
    print(f"Creating detailed settings for company ID: {company_id}")
    
    # Create inventory settings
    if not InventorySettings.query.filter_by(company_id=company_id).first():
        inventory_settings = InventorySettings(
            company_id=company_id,
            shared_inventory=False,
            stock_valuation_method='FIFO',
            enable_multi_uom=True,
            enable_batch_tracking=True,
            warn_negative_stock=True,
            auto_generate_batch=True,
            minimum_stock_alert=True,
            reorder_level_alert=True,
            expiry_alert_days=30
        )
        db.session.add(inventory_settings)
        print("  Created inventory settings")
    
    # Create accounting settings
    if not AccountingSettings.query.filter_by(company_id=company_id).first():
        accounting_settings = AccountingSettings(
            company_id=company_id,
            auto_journal_entries=True,
            auto_grn_accounting=True,
            auto_sales_accounting=True,
            auto_production_accounting=True,
            default_cgst_rate=9.0,
            default_sgst_rate=9.0,
            default_igst_rate=18.0,
            gst_calculation_method='inclusive'
        )
        db.session.add(accounting_settings)
        print("  Created accounting settings")
    
    # Create production settings
    if not ProductionSettings.query.filter_by(company_id=company_id).first():
        production_settings = ProductionSettings(
            company_id=company_id,
            enable_nested_bom=True,
            auto_cost_calculation=True,
            link_output_to_batch=True,
            lock_consumption=False,
            allow_overproduction=False,
            overproduction_limit_percent=10.0,
            require_material_availability=True,
            auto_reserve_materials=True,
            mandatory_quality_check=False,
            auto_scrap_failed_items=False
        )
        db.session.add(production_settings)
        print("  Created production settings")
    
    # Create job work settings
    if not JobWorkSettings.query.filter_by(company_id=company_id).first():
        jobwork_settings = JobWorkSettings(
            company_id=company_id,
            grn_required_on_return=True,
            track_vendor_rates=True,
            enable_scrap_entry=True,
            billing_mode='manual',
            mandatory_process_selection=True,
            allow_partial_returns=True,
            auto_calculate_loss=True,
            require_approval_for_issue=False,
            require_approval_for_return=False,
            approval_limit_amount=0.0
        )
        db.session.add(jobwork_settings)
        print("  Created job work settings")
    
    db.session.commit()

def assign_admin_to_company(company_id):
    """Assign all admin users to the default company"""
    from models_settings import UserCompanyAccess
    
    admin_users = User.query.filter_by(role='admin').all()
    
    for admin in admin_users:
        # Check if assignment already exists
        existing = UserCompanyAccess.query.filter_by(
            user_id=admin.id,
            company_id=company_id
        ).first()
        
        if not existing:
            assignment = UserCompanyAccess(
                user_id=admin.id,
                company_id=company_id,
                is_active=True
            )
            db.session.add(assignment)
            print(f"  Assigned admin user '{admin.username}' to company")
    
    db.session.commit()

def main():
    """Main setup function"""
    print("=== Centralized Settings Setup ===")
    
    app = create_app()
    
    with app.app_context():
        # Create database tables
        db.create_all()
        print("Database tables created/verified")
        
        # Create default company
        company = create_default_company()
        
        # Create global system settings
        create_system_settings()
        
        # Create company-specific system settings
        create_system_settings(company.id)
        
        # Create detailed settings models
        create_detailed_settings(company.id)
        
        # Assign admin users to company
        assign_admin_to_company(company.id)
        
        print("\n=== Setup Complete ===")
        print(f"Default company: {company.name} (ID: {company.id})")
        print("System settings created")
        print("Detailed settings models created")
        print("Admin users assigned to company")
        print("\nYou can now access the centralized settings at /settings/dashboard")

if __name__ == "__main__":
    main()