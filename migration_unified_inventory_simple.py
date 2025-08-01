#!/usr/bin/env python3
"""
Simplified migration for unified inventory architecture
Compatible with SQLite and existing structure
"""

import sys
from app import app, db
from models import Item
from sqlalchemy import text

def add_inventory_master_fields():
    """Add missing fields to items table using simpler approach"""
    print("Adding unified inventory master fields...")
    
    with app.app_context():
        try:
            # Add batch tracking fields one by one (SQLite compatible)
            columns_to_add = [
                ("is_batch_tracked", "BOOLEAN DEFAULT 1"),
                ("min_stock", "FLOAT DEFAULT 0.0"),
                ("unit_weight", "FLOAT DEFAULT 0.0"),
                ("default_location", "VARCHAR(100) DEFAULT 'Raw Store'"),
                ("batch_prefix", "VARCHAR(10) DEFAULT 'BAT'")
            ]
            
            for column_name, column_def in columns_to_add:
                try:
                    db.session.execute(text(f"ALTER TABLE items ADD COLUMN {column_name} {column_def}"))
                    print(f"✓ Added column: {column_name}")
                except Exception as e:
                    if "duplicate column name" in str(e).lower():
                        print(f"• Column {column_name} already exists")
                    else:
                        print(f"! Error adding {column_name}: {e}")
            
            db.session.commit()
            print("✓ Inventory master fields updated")
            
        except Exception as e:
            print(f"Error in inventory master update: {e}")
            db.session.rollback()

def update_existing_items():
    """Update existing items with new field values"""
    print("Updating existing items...")
    
    with app.app_context():
        try:
            # Update items to have batch tracking enabled
            items = Item.query.all()
            for item in items:
                if not hasattr(item, 'is_batch_tracked'):
                    continue
                    
                item.is_batch_tracked = True
                item.min_stock = item.min_stock if hasattr(item, 'min_stock') and item.min_stock else 10.0
                item.default_location = 'Raw Store'
                
                # Set batch prefix based on item type
                if item.type == 'Raw Material':
                    item.batch_prefix = 'MS'  # Material Store
                elif item.type == 'Finished Good':
                    item.batch_prefix = 'FG'  # Finished Goods
                else:
                    item.batch_prefix = 'BAT'
            
            db.session.commit()
            print(f"✓ Updated {len(items)} items")
            
        except Exception as e:
            print(f"Error updating items: {e}")
            db.session.rollback()

def create_simple_views():
    """Create simple views for inventory summary"""
    print("Creating inventory summary views...")
    
    with app.app_context():
        try:
            # Drop existing views if they exist
            try:
                db.session.execute(text("DROP VIEW IF EXISTS inventory_multi_state"))
                db.session.execute(text("DROP VIEW IF EXISTS batch_summary"))
            except:
                pass
            
            # Create simplified multi-state view
            db.session.execute(text("""
                CREATE VIEW inventory_multi_state AS
                SELECT 
                    i.id as item_id,
                    i.code as item_code,
                    i.name as item_name,
                    i.type as item_type,
                    i.unit as uom,
                    COALESCE(i.min_stock, 0) as min_stock,
                    COALESCE(SUM(CASE WHEN ib.qty_raw > 0 THEN ib.qty_raw ELSE 0 END), 0) as raw_qty,
                    COALESCE(SUM(CASE WHEN ib.qty_wip > 0 THEN ib.qty_wip ELSE 0 END), 0) as wip_qty,
                    COALESCE(SUM(CASE WHEN ib.qty_finished > 0 THEN ib.qty_finished ELSE 0 END), 0) as finished_qty,
                    COALESCE(SUM(CASE WHEN ib.qty_scrap > 0 THEN ib.qty_scrap ELSE 0 END), 0) as scrap_qty,
                    COALESCE(SUM(ib.qty_raw + ib.qty_wip + ib.qty_finished + ib.qty_scrap), 0) as total_qty,
                    COALESCE(SUM(ib.qty_raw + ib.qty_finished), 0) as available_qty,
                    CASE 
                        WHEN COALESCE(SUM(ib.qty_raw + ib.qty_finished), 0) = 0 THEN 'Out of Stock'
                        WHEN COALESCE(SUM(ib.qty_raw + ib.qty_finished), 0) <= COALESCE(i.min_stock, 0) THEN 'Low Stock'
                        ELSE 'In Stock'
                    END as stock_status
                FROM items i
                LEFT JOIN item_batches ib ON i.id = ib.item_id
                WHERE i.is_active = 1
                GROUP BY i.id, i.code, i.name, i.type, i.unit, i.min_stock
            """))
            
            db.session.commit()
            print("✓ Created inventory summary views")
            
        except Exception as e:
            print(f"Error creating views: {e}")
            db.session.rollback()

def main():
    """Run simplified migration"""
    print("Starting simplified unified inventory migration...")
    
    add_inventory_master_fields()
    update_existing_items() 
    create_simple_views()
    
    print("\n✅ Simplified unified inventory migration completed!")
    print("\nNew features added:")
    print("• Added batch tracking flags to items table")
    print("• Set minimum stock levels for all items")
    print("• Created inventory summary views")
    print("• Ready for unified dashboard implementation")

if __name__ == '__main__':
    main()