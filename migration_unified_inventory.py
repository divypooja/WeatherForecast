#!/usr/bin/env python3
"""
Migration to implement unified inventory architecture
Based on user requirements for clean parent-child structure
"""

import sys
from app import app, db
from models import Item
from models_batch import InventoryBatch, BatchMovement
from sqlalchemy import text

def add_inventory_master_fields():
    """Add missing fields to items table for unified inventory master"""
    print("Adding unified inventory master fields...")
    
    with app.app_context():
        try:
            # Add batch tracking fields
            db.session.execute(text("""
                ALTER TABLE items 
                ADD COLUMN IF NOT EXISTS is_batch_tracked BOOLEAN DEFAULT true,
                ADD COLUMN IF NOT EXISTS min_stock FLOAT DEFAULT 0.0,
                ADD COLUMN IF NOT EXISTS unit_weight FLOAT DEFAULT 0.0,
                ADD COLUMN IF NOT EXISTS default_location VARCHAR(100) DEFAULT 'Raw Store',
                ADD COLUMN IF NOT EXISTS batch_prefix VARCHAR(10) DEFAULT 'BAT'
            """))
            
            db.session.commit()
            print("✓ Added unified inventory master fields")
            
        except Exception as e:
            print(f"Error adding inventory master fields: {e}")
            db.session.rollback()

def enhance_batch_table():
    """Enhance batch table structure per requirements"""
    print("Enhancing batch table structure...")
    
    with app.app_context():
        try:
            # Add location and status fields
            db.session.execute(text("""
                ALTER TABLE inventory_batches 
                ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'Available',
                ADD COLUMN IF NOT EXISTS initial_qty FLOAT DEFAULT 0.0,
                ADD COLUMN IF NOT EXISTS date_received DATE DEFAULT CURRENT_DATE
            """))
            
            # Update location to be more specific
            db.session.execute(text("""
                UPDATE inventory_batches 
                SET location = CASE 
                    WHEN qty_raw > 0 THEN 'Raw Store'
                    WHEN qty_wip > 0 THEN 'WIP Store'
                    WHEN qty_finished > 0 THEN 'Finished Store'
                    WHEN qty_scrap > 0 THEN 'Scrap Store'
                    ELSE 'Raw Store'
                END
                WHERE location = 'Default' OR location IS NULL
            """))
            
            db.session.commit()
            print("✓ Enhanced batch table structure")
            
        except Exception as e:
            print(f"Error enhancing batch table: {e}")
            db.session.rollback()

def enhance_movement_log():
    """Enhance movement log with proper transaction structure"""
    print("Enhancing movement transaction log...")
    
    with app.app_context():
        try:
            # Add transaction fields
            db.session.execute(text("""
                ALTER TABLE batch_movements 
                ADD COLUMN IF NOT EXISTS txn_id VARCHAR(50),
                ADD COLUMN IF NOT EXISTS ref_doc VARCHAR(100),
                ADD COLUMN IF NOT EXISTS from_location VARCHAR(100),
                ADD COLUMN IF NOT EXISTS to_location VARCHAR(100)
            """))
            
            # Generate transaction IDs for existing records
            db.session.execute(text("""
                UPDATE batch_movements 
                SET txn_id = 'TXN-' || LPAD(id::text, 6, '0')
                WHERE txn_id IS NULL
            """))
            
            db.session.commit()
            print("✓ Enhanced movement transaction log")
            
        except Exception as e:
            print(f"Error enhancing movement log: {e}")
            db.session.rollback()

def update_existing_batches():
    """Update existing batches with proper structure"""
    print("Updating existing batch data...")
    
    with app.app_context():
        try:
            # Set initial quantities for existing batches
            db.session.execute(text("""
                UPDATE inventory_batches 
                SET initial_qty = qty_raw + qty_wip + qty_finished + qty_scrap
                WHERE initial_qty = 0 OR initial_qty IS NULL
            """))
            
            # Update batch codes to follow new format
            db.session.execute(text("""
                UPDATE inventory_batches 
                SET batch_code = CASE 
                    WHEN qty_raw > 0 THEN 'MS-' || LPAD(id::text, 3, '0')
                    WHEN qty_finished > 0 THEN 'FG-' || LPAD(id::text, 3, '0')
                    ELSE 'BAT-' || LPAD(id::text, 3, '0')
                END
                WHERE batch_code NOT LIKE 'MS-%' 
                AND batch_code NOT LIKE 'FG-%'
                AND batch_code NOT LIKE 'WIP-%'
            """))
            
            db.session.commit()
            print("✓ Updated existing batch data")
            
        except Exception as e:
            print(f"Error updating batch data: {e}")
            db.session.rollback()

def create_inventory_views():
    """Create database views for efficient querying"""
    print("Creating inventory summary views...")
    
    with app.app_context():
        try:
            # Create multi-state inventory view
            db.session.execute(text("""
                CREATE OR REPLACE VIEW inventory_multi_state AS
                SELECT 
                    i.id as item_id,
                    i.code as item_code,
                    i.name as item_name,
                    i.type as item_type,
                    i.unit as uom,
                    i.min_stock,
                    COALESCE(SUM(ib.qty_raw), 0) as raw_qty,
                    COALESCE(SUM(ib.qty_wip), 0) as wip_qty,
                    COALESCE(SUM(ib.qty_finished), 0) as finished_qty,
                    COALESCE(SUM(ib.qty_scrap), 0) as scrap_qty,
                    COALESCE(SUM(ib.qty_raw + ib.qty_wip + ib.qty_finished + ib.qty_scrap), 0) as total_qty,
                    COALESCE(SUM(ib.qty_raw + ib.qty_finished), 0) as available_qty,
                    CASE 
                        WHEN COALESCE(SUM(ib.qty_raw + ib.qty_finished), 0) = 0 THEN 'Out of Stock'
                        WHEN COALESCE(SUM(ib.qty_raw + ib.qty_finished), 0) <= i.min_stock THEN 'Low Stock'
                        ELSE 'In Stock'
                    END as stock_status
                FROM items i
                LEFT JOIN inventory_batches ib ON i.id = ib.item_id
                WHERE i.is_active = true
                GROUP BY i.id, i.code, i.name, i.type, i.unit, i.min_stock
            """))
            
            # Create batch summary view
            db.session.execute(text("""
                CREATE OR REPLACE VIEW batch_summary AS
                SELECT 
                    ib.id as batch_id,
                    ib.batch_code,
                    i.code as item_code,
                    i.name as item_name,
                    ib.qty_raw + ib.qty_wip + ib.qty_finished + ib.qty_scrap as total_qty,
                    ib.location,
                    ib.status,
                    ib.created_at as date_created,
                    ib.source_type,
                    CASE 
                        WHEN ib.qty_raw > 0 THEN 'Raw Store'
                        WHEN ib.qty_wip > 0 THEN 'WIP Store'
                        WHEN ib.qty_finished > 0 THEN 'Finished Store'
                        WHEN ib.qty_scrap > 0 THEN 'Scrap Store'
                        ELSE 'Empty'
                    END as current_state
                FROM inventory_batches ib
                JOIN items i ON ib.item_id = i.id
                WHERE ib.qty_raw + ib.qty_wip + ib.qty_finished + ib.qty_scrap > 0
            """))
            
            db.session.commit()
            print("✓ Created inventory summary views")
            
        except Exception as e:
            print(f"Error creating views: {e}")
            db.session.rollback()

def main():
    """Run all migration steps"""
    print("Starting unified inventory migration...")
    
    add_inventory_master_fields()
    enhance_batch_table()
    enhance_movement_log()
    update_existing_batches()
    create_inventory_views()
    
    print("\n✅ Unified inventory migration completed successfully!")
    print("\nNew features added:")
    print("• Unified inventory master with batch tracking flags")
    print("• Enhanced batch table with status and location tracking")
    print("• Improved movement transaction log")
    print("• Standardized batch code formats (MS-001, FG-001)")
    print("• Database views for efficient multi-state querying")

if __name__ == '__main__':
    main()