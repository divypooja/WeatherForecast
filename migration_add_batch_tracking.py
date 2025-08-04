#!/usr/bin/env python3
"""
Migration script to add batch tracking columns to existing items table
and update all modules with comprehensive batch tracking
"""

from app import create_app, db
from models import Item, ItemBatch
from sqlalchemy import text
import os

def add_batch_tracking_columns():
    """Add batch tracking columns to items table"""
    app = create_app()
    
    with app.app_context():
        try:
            # Check if columns already exist
            result = db.session.execute(text("PRAGMA table_info(items)"))
            columns = [row[1] for row in result.fetchall()]
            
            if 'batch_required' not in columns:
                print("Adding batch_required column...")
                db.session.execute(text("ALTER TABLE items ADD COLUMN batch_required BOOLEAN DEFAULT 1"))
            
            if 'default_batch_prefix' not in columns:
                print("Adding default_batch_prefix column...")
                db.session.execute(text("ALTER TABLE items ADD COLUMN default_batch_prefix VARCHAR(10)"))
            
            if 'shelf_life_days' not in columns:
                print("Adding shelf_life_days column...")
                db.session.execute(text("ALTER TABLE items ADD COLUMN shelf_life_days INTEGER"))
            
            if 'batch_numbering_auto' not in columns:
                print("Adding batch_numbering_auto column...")
                db.session.execute(text("ALTER TABLE items ADD COLUMN batch_numbering_auto BOOLEAN DEFAULT 1"))
            
            # Commit the changes
            db.session.commit()
            print("Successfully added batch tracking columns to items table")
            
            # Initialize batch settings for existing items
            items = Item.query.all()
            for item in items:
                if item.batch_required is None:
                    item.batch_required = True
                if item.batch_numbering_auto is None:
                    item.batch_numbering_auto = True
                if not item.default_batch_prefix:
                    item.default_batch_prefix = item.code[:3].upper() if item.code else 'ITM'
            
            db.session.commit()
            print(f"Updated batch settings for {len(items)} existing items")
            
        except Exception as e:
            print(f"Error during migration: {str(e)}")
            db.session.rollback()
            raise

if __name__ == '__main__':
    add_batch_tracking_columns()