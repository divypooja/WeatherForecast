#!/usr/bin/env python3
"""
Script to initialize default notification settings
"""
from app import create_app, db
from models_notifications import NotificationSettings

def initialize_default_settings():
    """Create default notification settings if none exist"""
    try:
        app = create_app()
        with app.app_context():
            # Check if settings already exist
            existing_settings = NotificationSettings.query.first()
            
            if existing_settings:
                print("Notification settings already exist:")
                print(f"Email enabled: {existing_settings.email_enabled}")
                print(f"SMS enabled: {existing_settings.sms_enabled}")
                print(f"WhatsApp enabled: {existing_settings.whatsapp_enabled}")
                return True
            
            # Create default settings
            default_settings = NotificationSettings(
                email_enabled=True,
                sms_enabled=True,
                whatsapp_enabled=True,
                in_app_enabled=True,
                sender_email='noreply@akfactory.com',
                sender_name='AK Innovations Factory',
                po_notifications=True,
                grn_notifications=True,
                job_work_notifications=True,
                production_notifications=True,
                sales_notifications=True,
                accounts_notifications=True,
                inventory_notifications=True,
                po_vendor_notification=True,
                grn_rejection_notification=True,
                job_work_vendor_notification=True,
                customer_invoice_notification=True,
                payment_overdue_notification=True,
                low_stock_notifications=True,
                scrap_threshold_notifications=True,
                default_language='EN',
                time_format='24H',
                notification_summary='immediate'
            )
            
            db.session.add(default_settings)
            db.session.commit()
            
            print("Default notification settings created successfully!")
            print(f"Email enabled: {default_settings.email_enabled}")
            print(f"SMS enabled: {default_settings.sms_enabled}")
            print(f"WhatsApp enabled: {default_settings.whatsapp_enabled}")
            print(f"Sender email: {default_settings.sender_email}")
            
            return True
            
    except Exception as e:
        print(f"Error creating default settings: {e}")
        return False

if __name__ == "__main__":
    print("Initializing default notification settings...")
    if initialize_default_settings():
        print("Initialization completed successfully!")
    else:
        print("Initialization failed!")