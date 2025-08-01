#!/usr/bin/env python3
"""
Final fix for inventory views with correct field names from Item model
"""

from app import app, db
from sqlalchemy import text

def fix_inventory_views_final():
    """Recreate inventory views with exact field names from Item model"""
    print("Final fix for inventory views...")
    
    with app.app_context():
        try:
            # Drop existing views
            try:
                db.session.execute(text("DROP VIEW IF EXISTS inventory_multi_state"))
                db.session.execute(text("DROP VIEW IF EXISTS batch_summary"))
            except:
                pass
            
            # Create multi-state view with correct field names
            db.session.execute(text("""
                CREATE VIEW inventory_multi_state AS
                SELECT 
                    i.id as item_id,
                    i.code as item_code,
                    i.name as item_name,
                    i.item_type as item_type,
                    i.unit_of_measure as uom,
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
                GROUP BY i.id, i.code, i.name, i.item_type, i.unit_of_measure, i.min_stock
            """))
            
            # Create batch summary view using existing ItemBatch table structure
            db.session.execute(text("""
                CREATE VIEW batch_summary AS
                SELECT 
                    ib.id as batch_id,
                    ib.batch_number as batch_code,
                    i.code as item_code,
                    i.name as item_name,
                    ib.current_quantity as total_qty,
                    ib.location,
                    'Available' as status,
                    ib.created_at as date_created,
                    ib.source_type,
                    CASE 
                        WHEN ib.location LIKE '%Raw%' THEN 'Raw Store'
                        WHEN ib.location LIKE '%WIP%' THEN 'WIP Store'
                        WHEN ib.location LIKE '%Finished%' THEN 'Finished Store'
                        WHEN ib.location LIKE '%Scrap%' THEN 'Scrap Store'
                        ELSE 'General Store'
                    END as current_state
                FROM item_batches ib
                JOIN items i ON ib.item_id = i.id
                WHERE ib.current_quantity > 0
            """))
            
            db.session.commit()
            print("✓ Fixed inventory views with correct field names")
            
        except Exception as e:
            print(f"Error fixing views: {e}")
            db.session.rollback()

def main():
    """Run the final fix"""
    print("Starting final inventory view fix...")
    fix_inventory_views_final()
    print("\n✅ Final inventory view fix completed!")

if __name__ == '__main__':
    main()