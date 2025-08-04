#!/usr/bin/env python3
"""
Fix inventory_multi_state view to only count approved batches
This ensures that Raw state shows only approved quantities, not pending/quarantine
"""

from app import app, db
from sqlalchemy import text

def fix_inventory_view():
    """Update the view to only count approved batches"""
    
    with app.app_context():
        try:
            # Drop existing view
            db.session.execute(text("DROP VIEW IF EXISTS inventory_multi_state"))
            
            # Create updated view that only counts approved quantities
            db.session.execute(text("""
                CREATE VIEW inventory_multi_state AS
                SELECT 
                    i.id as item_id,
                    i.code as item_code,
                    i.name as item_name,
                    i.item_type as item_type,
                    i.unit_of_measure as uom,
                    COALESCE(i.min_stock, 0) as min_stock,
                    -- Only count approved batches for actual inventory
                    COALESCE(SUM(CASE WHEN ib.batch_status = 'approved' AND ib.qty_raw > 0 THEN ib.qty_raw ELSE 0 END), 0) as raw_qty,
                    COALESCE(SUM(CASE WHEN ib.batch_status = 'approved' AND ib.qty_wip > 0 THEN ib.qty_wip ELSE 0 END), 0) as wip_qty,
                    COALESCE(SUM(CASE WHEN ib.batch_status = 'approved' AND ib.qty_finished > 0 THEN ib.qty_finished ELSE 0 END), 0) as finished_qty,
                    COALESCE(SUM(CASE WHEN ib.batch_status = 'approved' AND ib.qty_scrap > 0 THEN ib.qty_scrap ELSE 0 END), 0) as scrap_qty,
                    -- Total includes all approved states
                    COALESCE(SUM(CASE WHEN ib.batch_status = 'approved' THEN (ib.qty_raw + ib.qty_wip + ib.qty_finished + ib.qty_scrap) ELSE 0 END), 0) as total_qty,
                    -- Available = approved raw + approved finished
                    COALESCE(SUM(CASE WHEN ib.batch_status = 'approved' THEN (ib.qty_raw + ib.qty_finished) ELSE 0 END), 0) as available_qty,
                    CASE 
                        WHEN COALESCE(SUM(CASE WHEN ib.batch_status = 'approved' THEN (ib.qty_raw + ib.qty_finished) ELSE 0 END), 0) = 0 THEN 'Out of Stock'
                        WHEN COALESCE(SUM(CASE WHEN ib.batch_status = 'approved' THEN (ib.qty_raw + ib.qty_finished) ELSE 0 END), 0) <= COALESCE(i.min_stock, 0) THEN 'Low Stock'
                        ELSE 'In Stock'
                    END as stock_status
                FROM items i
                LEFT JOIN item_batches ib ON i.id = ib.item_id
                GROUP BY i.id, i.code, i.name, i.item_type, i.unit_of_measure, i.min_stock
            """))
            
            db.session.commit()
            print("✓ Updated inventory_multi_state view to only count approved batches")
            
            # Test the fix
            result = db.session.execute(text("""
                SELECT item_code, item_name, raw_qty, total_qty, available_qty
                FROM inventory_multi_state 
                WHERE item_name = 'Ms sheet'
            """)).fetchone()
            
            if result:
                print(f"\nUpdated values for Ms sheet:")
                print(f"  Raw: {result.raw_qty}")
                print(f"  Total: {result.total_qty}")
                print(f"  Available: {result.available_qty}")
            
        except Exception as e:
            print(f"Error updating view: {e}")
            db.session.rollback()

if __name__ == "__main__":
    fix_inventory_view()