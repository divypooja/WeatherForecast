#!/usr/bin/env python3
"""
Fix admin login issues by creating or updating admin user with proper credentials
"""

from app import app, db
from models import User
from werkzeug.security import generate_password_hash
from sqlalchemy import text

def fix_admin_login():
    with app.app_context():
        try:
            # First, check if admin user exists
            admin = User.query.filter_by(username='admin').first()
            
            if admin:
                print("Found existing admin user - updating credentials...")
                # Update existing admin user
                admin.password_hash = generate_password_hash('admin123')
                admin.is_active = True
                admin.email = 'admin@factory.com'
                admin.role = 'admin'
                db.session.commit()
                print("✅ Updated existing admin user")
            else:
                print("No admin user found - creating new one...")
                # Create new admin user
                admin = User(
                    username='admin',
                    email='admin@factory.com',
                    password_hash=generate_password_hash('admin123'),
                    role='admin',
                    is_active=True
                )
                db.session.add(admin)
                db.session.commit()
                print("✅ Created new admin user")
            
            # Verify the admin user works
            test_admin = User.query.filter_by(username='admin').first()
            if test_admin and test_admin.check_password('admin123') and test_admin.is_active:
                print("\n🎯 Admin login ready!")
                print("   Username: admin")
                print("   Password: admin123")
                print("   Status: Active")
                print("\nYou can now log in successfully!")
                return True
            else:
                print("❌ Admin user verification failed")
                return False
                
        except Exception as e:
            print(f"Error fixing admin login: {e}")
            db.session.rollback()
            return False

if __name__ == '__main__':
    fix_admin_login()