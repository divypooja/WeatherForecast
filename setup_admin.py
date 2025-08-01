#!/usr/bin/env python3
"""
Setup admin user for the Factory Management System
"""
import os
import sys

# Set up environment
os.environ['FLASK_ENV'] = 'development'

# Import Flask and database
from main import app
from models import db, User
from werkzeug.security import generate_password_hash

def create_admin_user():
    """Create admin user with default credentials"""
    with app.app_context():
        try:
            # Ensure all tables exist
            db.create_all()
            print("✅ Database tables created/verified")
            
            # Check if admin user already exists
            existing_admin = User.query.filter_by(username='admin').first()
            if existing_admin:
                print("⚠️  Admin user already exists!")
                print("   Username: admin")
                print("   Email: admin@factory.com")
                print("   You can use existing credentials or reset password manually")
                return
            
            # Create new admin user
            admin_user = User(
                username='admin',
                email='admin@factory.com',
                password_hash=generate_password_hash('admin123'),
                role='admin',
                is_active=True
            )
            
            db.session.add(admin_user)
            db.session.commit()
            
            print("🎉 Admin user created successfully!")
            print("")
            print("📋 Admin Credentials:")
            print("   Username: admin")
            print("   Password: admin123")
            print("   Email: admin@factory.com")
            print("   Role: admin")
            print("")
            print("🔐 Please change the default password after first login")
            print("🌐 You can now access the Factory Management System")
            
        except Exception as e:
            print(f"❌ Error creating admin user: {str(e)}")
            sys.exit(1)

if __name__ == '__main__':
    create_admin_user()