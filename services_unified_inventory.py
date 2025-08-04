"""
Unified Inventory Service
Implements the clean parent-child architecture per user requirements
"""

from datetime import datetime, date
from app import db
from models import Item
from models_batch import InventoryBatch, BatchMovement
from sqlalchemy import text, func

class UnifiedInventoryService:
    """Service for managing unified inventory with batch tracking"""
    
    @staticmethod
    def get_inventory_dashboard_stats():
        """Optimized dashboard statistics with fallback handling"""
        try:
            # Try using the multi-state view if it exists
            stats_query = db.session.execute(text("""
                SELECT 
                    COUNT(*) as total_items,
                    COUNT(CASE WHEN stock_status = 'Low Stock' THEN 1 END) as low_stock_items,
                    COUNT(CASE WHEN stock_status = 'Out of Stock' THEN 1 END) as out_of_stock_items,
                    SUM(CASE WHEN finished_qty > 0 THEN finished_qty * COALESCE(i.unit_price, 0) ELSE 0 END) as stock_value
                FROM inventory_multi_state ims
                LEFT JOIN items i ON ims.item_id = i.id
            """)).fetchone()
            
            return {
                'total_items': stats_query.total_items or 0,
                'low_stock_items': stats_query.low_stock_items or 0,
                'out_of_stock_items': stats_query.out_of_stock_items or 0,
                'total_stock_value': stats_query.stock_value or 0.0
            }
        except Exception:
            # Fallback to direct item queries if view doesn't exist
            from sqlalchemy import func
            
            # Use raw SQL to avoid SQLAlchemy case syntax issues
            stats = db.session.execute(text("""
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN COALESCE(current_stock, 0) <= COALESCE(minimum_stock, 0) THEN 1 ELSE 0 END) as low_stock,
                    SUM(CASE WHEN COALESCE(current_stock, 0) = 0 THEN 1 ELSE 0 END) as out_of_stock,
                    SUM(COALESCE(current_stock, 0) * COALESCE(unit_price, 0)) as stock_value
                FROM items
            """)).fetchone()
            
            return {
                'total_items': stats.total or 0,
                'low_stock_items': stats.low_stock or 0,
                'out_of_stock_items': stats.out_of_stock or 0,
                'total_stock_value': stats.stock_value or 0.0
            }
    
    @staticmethod
    def get_multi_state_inventory():
        """Optimized multi-state inventory with fallback"""
        try:
            # Try using the multi-state view
            result = db.session.execute(text("""
                SELECT 
                    item_code,
                    item_name,
                    item_type,
                    uom,
                    raw_qty,
                    wip_qty,
                    finished_qty,
                    scrap_qty,
                    total_qty,
                    available_qty,
                    stock_status
                FROM inventory_multi_state
                ORDER BY item_code
            """)).fetchall()
            
            return [{
                'item_code': row.item_code,
                'item_name': row.item_name,
                'item_type': row.item_type,
                'uom': row.uom,
                'raw': row.raw_qty,
                'wip': row.wip_qty,
                'finished': row.finished_qty,
                'scrap': row.scrap_qty,
                'total': row.total_qty,
                'available': row.available_qty,
                'status': row.stock_status
            } for row in result]
            
        except Exception:
            # Fallback to direct Item queries
            items = Item.query.order_by(Item.code).all()
            
            return [{
                'item_code': item.code,
                'item_name': item.name,
                'item_type': item.item_type or 'material',
                'uom': item.unit_of_measure,
                'raw': item.current_stock or 0,
                'wip': 0,
                'finished': 0,
                'scrap': 0,
                'total': item.current_stock or 0,
                'available': item.current_stock or 0,
                'status': 'In Stock' if (item.current_stock or 0) > 0 else 'Out of Stock'
            } for item in items]
    
    @staticmethod
    def get_batch_tracking_view():
        """Get batch tracking view per user requirements"""
        
        result = db.session.execute(text("""
            SELECT 
                batch_code,
                item_code,
                item_name,
                total_qty,
                current_state,
                location,
                status,
                date_created,
                source_type
            FROM batch_summary
            ORDER BY date_created DESC
        """)).fetchall()
        
        return [{
            'batch_id': row.batch_code,
            'item': f"{row.item_code} - {row.item_name}",
            'qty': row.total_qty,
            'state': row.current_state,
            'location': row.location,
            'source': row.source_type or 'N/A',
            'last_used': row.date_created.strftime('%Y-%m-%d') if row.date_created else 'N/A'
        } for row in result]
    
    @staticmethod
    def get_all_items_with_states():
        """Get all inventory items with their multi-state data for export"""
        
        items = Item.query.all()
        items_data = []
        
        for item in items:
            items_data.append({
                'code': item.code,
                'name': item.name,
                'description': item.description,
                'item_type': item.item_type,
                'unit_of_measure': item.unit_of_measure,
                'qty_raw': item.qty_raw or 0,
                'qty_wip': item.qty_wip or 0,
                'qty_finished': item.qty_finished or 0,
                'qty_scrap': item.qty_scrap or 0,
                'minimum_stock': item.minimum_stock,
                'unit_price': item.unit_price,
                'unit_weight': item.unit_weight,
                'hsn_code': item.hsn_code,
                'gst_rate': item.gst_rate,
                'created_at': item.created_at
            })
        
        return items_data
    
    @staticmethod
    def create_batch(item_id, quantity, source_type='purchase', source_ref_id=None, 
                    supplier_batch_no=None, purchase_rate=0.0, location='Raw Store'):
        """Create new batch with proper naming convention"""
        
        item = Item.query.get(item_id)
        if not item:
            return None
        
        # Generate batch code based on location/type
        batch_count = InventoryBatch.query.filter_by(item_id=item_id).count() + 1
        
        if location == 'Raw Store' or source_type == 'purchase':
            batch_code = f"MS-{batch_count:03d}"
            initial_state = 'raw'
        elif location == 'Finished Store' or source_type == 'production':
            batch_code = f"FG-{batch_count:03d}"
            initial_state = 'finished'
        else:
            batch_code = f"BAT-{batch_count:03d}"
            initial_state = 'raw'
        
        # Create batch
        batch = InventoryBatch(
            item_id=item_id,
            batch_code=batch_code,
            uom=item.unit,
            location=location,
            initial_qty=quantity,
            supplier_batch_no=supplier_batch_no,
            purchase_rate=purchase_rate,
            source_type=source_type,
            source_ref_id=source_ref_id,
            status='Available',
            date_received=date.today()
        )
        
        # Set quantity in appropriate state
        if initial_state == 'raw':
            batch.qty_raw = quantity
        elif initial_state == 'finished':
            batch.qty_finished = quantity
        
        db.session.add(batch)
        
        # Log the creation movement
        movement = BatchMovement(
            batch_id=batch.id,
            item_id=item_id,
            quantity=quantity,
            from_state=None,
            to_state=initial_state,
            movement_type='receipt',
            ref_type=source_type,
            ref_id=source_ref_id,
            notes=f"Batch created from {source_type}",
            txn_id=f"TXN-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        )
        db.session.add(movement)
        
        return batch
    
    @staticmethod
    def move_batch_quantity(batch_id, quantity, from_state, to_state, 
                          ref_type=None, ref_id=None, notes=None):
        """Move quantity between states with proper logging"""
        
        batch = InventoryBatch.query.get(batch_id)
        if not batch:
            return False, "Batch not found"
        
        # Validate and perform move
        if batch.move_quantity(quantity, from_state, to_state, ref_type, ref_id, notes):
            
            # Update location based on new state
            if to_state == 'raw':
                batch.location = 'Raw Store'
            elif to_state == 'wip':
                batch.location = 'WIP Store'
            elif to_state == 'finished':
                batch.location = 'Finished Store'
            elif to_state == 'scrap':
                batch.location = 'Scrap Store'
            
            db.session.commit()
            return True, "Movement completed successfully"
        else:
            return False, "Insufficient quantity in source state"
    
    @staticmethod
    def get_available_batches_for_issue(item_id, required_qty, from_state='raw'):
        """Get available batches for material issue (FIFO logic)"""
        
        batches = db.session.query(InventoryBatch).filter(
            InventoryBatch.item_id == item_id,
            InventoryBatch.status == 'Available'
        ).order_by(InventoryBatch.date_received).all()
        
        available_batches = []
        total_available = 0
        
        for batch in batches:
            state_qty = getattr(batch, f'qty_{from_state}', 0) or 0
            if state_qty > 0:
                available_batches.append({
                    'batch_id': batch.id,
                    'batch_code': batch.batch_code,
                    'available_qty': state_qty,
                    'age_days': batch.age_days,
                    'location': batch.location
                })
                total_available += state_qty
                
                if total_available >= required_qty:
                    break
        
        return available_batches, total_available >= required_qty
    
    @staticmethod
    def reserve_quantity_for_sales(item_id, quantity):
        """Reserve finished goods quantity for sales orders"""
        # This will be implemented when sales module is enhanced
        pass
    
    @staticmethod
    def get_movement_history(batch_id=None, item_id=None, limit=100):
        """Get movement transaction history"""
        
        query = db.session.query(BatchMovement)
        
        if batch_id:
            query = query.filter(BatchMovement.batch_id == batch_id)
        if item_id:
            query = query.filter(BatchMovement.item_id == item_id)
        
        movements = query.order_by(BatchMovement.created_at.desc()).limit(limit).all()
        
        return [{
            'txn_id': m.txn_id,
            'batch_code': m.batch.batch_code if m.batch else 'N/A',
            'item_name': m.item.name if m.item else 'N/A',
            'quantity': m.quantity,
            'from_state': m.from_state or 'External',
            'to_state': m.to_state or 'Consumed',
            'movement_type': m.movement_type,
            'ref_doc': m.ref_doc or f"{m.ref_type or 'N/A'}-{m.ref_id or ''}",
            'date': m.created_at.strftime('%Y-%m-%d %H:%M') if m.created_at else 'N/A',
            'notes': m.notes or ''
        } for m in movements]