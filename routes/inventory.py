from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from forms import ItemForm
from models import Item, ItemType, ItemBatch
from models_batch_movement import BatchMovementLedger, BatchConsumptionReport
from services_batch_management import BatchManager, BatchValidator
from app import db
from sqlalchemy import func, desc, or_, and_
from utils import generate_item_code
from utils_export import export_inventory_items
from utils_batch_tracking import BatchTracker
from datetime import datetime, timedelta

inventory_bp = Blueprint('inventory', __name__)

@inventory_bp.route('/dashboard')
@login_required
def dashboard():
    # Inventory statistics
    stats = {
        'total_items': Item.query.count(),
        'low_stock_items': Item.query.filter(
            func.coalesce(Item.current_stock, 0) <= func.coalesce(Item.minimum_stock, 0)
        ).count(),
        'total_stock_value': db.session.query(func.sum(
            func.coalesce(Item.current_stock, 0) * func.coalesce(Item.unit_price, 0)
        )).scalar() or 0,
        'out_of_stock': Item.query.filter(func.coalesce(Item.current_stock, 0) == 0).count()
    }
    
    # Recent items and low stock alerts
    recent_items = Item.query.order_by(Item.created_at.desc()).limit(5).all()
    low_stock_items = Item.query.filter(
        func.coalesce(Item.current_stock, 0) <= func.coalesce(Item.minimum_stock, 0)
    ).limit(10).all()
    
    # UOM summary
    uom_stats = db.session.query(Item.unit_of_measure, func.count(Item.id)).group_by(Item.unit_of_measure).all()
    
    return render_template('inventory/dashboard.html', 
                         stats=stats, 
                         recent_items=recent_items,
                         low_stock_items=low_stock_items,
                         uom_stats=uom_stats)

@inventory_bp.route('/batch-tracking')
@login_required
def batch_tracking_dashboard():
    """Parent-Child batch tracking dashboard as per documentation"""
    from models_grn import GRN
    from models import PurchaseOrder, JobWork
    
    # Batch statistics
    stats = {
        'total_batches': ItemBatch.query.count(),
        'active_batches': ItemBatch.query.filter(
            or_(
                ItemBatch.qty_raw > 0,
                ItemBatch.qty_wip > 0,
                ItemBatch.qty_finished > 0
            )
        ).count(),
        'expired_batches': ItemBatch.query.filter(
            ItemBatch.expiry_date <= datetime.now().date()
        ).count() if ItemBatch.query.filter(ItemBatch.expiry_date.isnot(None)).count() > 0 else 0,
        'batches_expiring_soon': ItemBatch.query.filter(
            ItemBatch.expiry_date <= (datetime.now().date() + timedelta(days=7)),
            ItemBatch.expiry_date > datetime.now().date()
        ).count() if ItemBatch.query.filter(ItemBatch.expiry_date.isnot(None)).count() > 0 else 0
    }
    
    # Parent-Child Structure: Get Parent orders with their associated GRNs
    parent_child_data = []
    
    # 1. Purchase Orders as Parents
    purchase_orders = PurchaseOrder.query.filter(
        PurchaseOrder.grn_receipts_po.any()
    ).order_by(PurchaseOrder.created_at.desc()).all()
    
    for po in purchase_orders:
        # Calculate totals for this PO
        total_qty = sum(item.qty for item in po.items)
        grn_count = len(po.grn_receipts_po)
        
        # Determine status based on GRN completion
        if all(grn.status == 'completed' for grn in po.grn_receipts_po):
            po_status = 'Completed'
        elif any(grn.status in ['received', 'inspected'] for grn in po.grn_receipts_po):
            po_status = 'Partial'
        else:
            po_status = 'Pending'
        
        # Build child GRNs with batch details
        child_grns = []
        for grn in po.grn_receipts_po:
            for line_item in grn.line_items:
                # Get batch info for this GRN line item
                batches = ItemBatch.query.filter_by(grn_id=grn.id, item_id=line_item.item_id).all()
                
                child_grns.append({
                    'grn_number': grn.grn_number,
                    'grn_date': grn.received_date,
                    'batch_numbers': [batch.batch_number for batch in batches] if batches else ['Manual Entry'],
                    'item_name': line_item.item.name,
                    'received_qty': line_item.quantity_received,
                    'scrap_qty': line_item.quantity_rejected or 0,
                    'status': grn.status.title(),
                    'grn_id': grn.id
                })
        
        parent_child_data.append({
            'type': 'Purchase Order',
            'parent_doc': po.po_number,
            'date': po.created_at.date(),
            'vendor_customer': po.supplier.name if po.supplier else 'N/A',
            'status': po_status,
            'total_qty': total_qty,
            'grn_count': grn_count,
            'child_grns': child_grns,
            'parent_id': po.id
        })
    
    # 2. Job Works as Parents  
    job_works = JobWork.query.filter(
        JobWork.grn_receipts.any()
    ).order_by(JobWork.created_at.desc()).all()
    
    for jw in job_works:
        # Calculate totals for this Job Work
        total_qty = jw.quantity_ordered if hasattr(jw, 'quantity_ordered') else (jw.quantity or 0)
        grn_count = len(jw.grn_receipts)
        
        # Determine status based on GRN completion
        if all(grn.status == 'completed' for grn in jw.grn_receipts):
            jw_status = 'Completed'
        elif any(grn.status in ['received', 'inspected'] for grn in jw.grn_receipts):
            jw_status = 'Partial'
        else:
            jw_status = 'Pending'
        
        # Build child GRNs with batch details
        child_grns = []
        for grn in jw.grn_receipts:
            for line_item in grn.line_items:
                # Get batch info for this GRN line item
                batches = ItemBatch.query.filter_by(grn_id=grn.id, item_id=line_item.item_id).all()
                
                child_grns.append({
                    'grn_number': grn.grn_number,
                    'grn_date': grn.received_date,
                    'batch_numbers': [batch.batch_number for batch in batches] if batches else ['Manual Entry'],
                    'item_name': line_item.item.name,
                    'received_qty': line_item.quantity_received,
                    'scrap_qty': line_item.quantity_rejected or 0,
                    'status': grn.status.title(),
                    'grn_id': grn.id
                })
        
        parent_child_data.append({
            'type': 'Job Work',
            'parent_doc': jw.job_number,
            'date': jw.created_at.date(),
            'vendor_customer': jw.vendor.name if jw.vendor else 'In-House',
            'status': jw_status,
            'total_qty': total_qty,
            'grn_count': grn_count,
            'child_grns': child_grns,
            'parent_id': jw.id
        })
    
    # Get recent batch movements for the side panel
    recent_movements = BatchMovementLedger.query.order_by(
        BatchMovementLedger.created_at.desc()
    ).limit(10).all()
    
    return render_template('inventory/batch_tracking_dashboard.html',
                         title='Batch Tracking Dashboard',
                         stats=stats,
                         parent_child_data=parent_child_data,
                         recent_movements=recent_movements)

@inventory_bp.route('/batch/<int:batch_id>/traceability')
@login_required
def batch_traceability(batch_id):
    """View complete traceability for a specific batch"""
    traceability_data = BatchManager.get_batch_traceability(batch_id)
    
    if 'error' in traceability_data:
        flash(f'Error getting batch traceability: {traceability_data["error"]}', 'error')
        return redirect(url_for('inventory.batch_tracking_dashboard'))
    
    return render_template('inventory/batch_traceability.html',
                         title=f'Batch Traceability - {traceability_data["batch"]["batch_number"]}',
                         traceability=traceability_data)

@inventory_bp.route('/multi-state')
@login_required
def multi_state_view():
    """View multi-state inventory breakdown"""
    # Get all items and ensure multi-state fields are initialized
    items = Item.query.all()
    
    # Initialize multi-state inventory for items that haven't been set up
    for item in items:
        if item.qty_raw is None:
            item.qty_raw = item.current_stock or 0.0
            item.qty_wip = 0.0
            item.qty_finished = 0.0
            item.qty_scrap = 0.0
    
    db.session.commit()
    
    # Calculate totals
    total_raw = sum(item.qty_raw or 0 for item in items)
    total_wip = sum(item.total_wip or 0 for item in items)
    total_finished = sum(item.qty_finished or 0 for item in items)
    total_scrap = sum(item.qty_scrap or 0 for item in items)
    
    return render_template('inventory/multi_state_view.html',
                         title='Multi-State Inventory Tracking',
                         items=items,
                         total_raw=total_raw,
                         total_wip=total_wip,
                         total_finished=total_finished,
                         total_scrap=total_scrap)

@inventory_bp.route('/batch-wise')
@login_required
def batch_wise_view():
    """View inventory organized by batches with complete traceability"""
    
    # Get filter parameters
    item_filter = request.args.get('item_id', type=int)
    state_filter = request.args.get('state', '')
    location_filter = request.args.get('location', '')
    
    # Build base query
    query = ItemBatch.query.join(Item)
    
    # Apply filters
    if item_filter:
        query = query.filter(ItemBatch.item_id == item_filter)
    
    if state_filter:
        if state_filter == 'raw':
            query = query.filter(ItemBatch.qty_raw > 0)
        elif state_filter == 'finished':
            query = query.filter(ItemBatch.qty_finished > 0)
        elif state_filter == 'scrap':
            query = query.filter(ItemBatch.qty_scrap > 0)
        elif state_filter in ['cutting', 'bending', 'welding', 'zinc', 'painting', 'assembly', 'machining', 'polishing']:
            query = query.filter(getattr(ItemBatch, f'qty_wip_{state_filter}') > 0)
    
    if location_filter:
        query = query.filter(ItemBatch.storage_location.ilike(f'%{location_filter}%'))
    
    # Pagination
    page = request.args.get('page', 1, type=int)
    batches = query.order_by(desc(ItemBatch.created_at)).paginate(
        page=page, per_page=20, error_out=False
    )
    
    # Get process-wise summary
    process_summary = BatchTracker.get_process_wise_inventory_summary()
    
    # Get filter options
    items = Item.query.filter(Item.batches.any()).order_by(Item.name).all()
    storage_locations = db.session.query(ItemBatch.storage_location).distinct().all()
    locations = [loc[0] for loc in storage_locations if loc[0]]
    
    # Calculate batch statistics
    batch_stats = {
        'total_batches': ItemBatch.query.count(),
        'active_batches': ItemBatch.query.filter(ItemBatch.total_quantity > 0).count(),
        'expired_batches': ItemBatch.query.filter(
            ItemBatch.expiry_date < datetime.now().date()
        ).count() if hasattr(ItemBatch, 'expiry_date') else 0,
        'quality_issues': ItemBatch.query.filter(ItemBatch.quality_status == 'defective').count()
    }
    
    return render_template('inventory/batch_wise_view.html',
                         title='Batch-Wise Inventory Tracking',
                         batches=batches,
                         process_summary=process_summary,
                         batch_stats=batch_stats,
                         items=items,
                         locations=locations,
                         current_filters={
                             'item_id': item_filter,
                             'state': state_filter,
                             'location': location_filter
                         })

@inventory_bp.route('/process-breakdown')
@login_required
def process_breakdown():
    """Show inventory breakdown by manufacturing processes"""
    
    # Get process-wise inventory summary
    process_summary = BatchTracker.get_process_wise_inventory_summary()
    
    # Calculate totals across all processes
    process_totals = {
        'raw': 0,
        'cutting': 0,
        'bending': 0,
        'welding': 0,
        'zinc': 0,
        'painting': 0,
        'assembly': 0,
        'machining': 0,
        'polishing': 0,
        'finished': 0,
        'scrap': 0
    }
    
    for item_id, item_data in process_summary.items():
        for process, qty in item_data['states'].items():
            if process in process_totals:
                process_totals[process] += qty
    
    # Get top items by process volume
    top_items_by_process = {}
    for process in process_totals.keys():
        if process_totals[process] > 0:
            # Get items with highest quantity in this process
            items_in_process = []
            for item_id, item_data in process_summary.items():
                qty = item_data['states'].get(process, 0)
                if qty > 0:
                    items_in_process.append({
                        'item_name': item_data['item_name'],
                        'item_code': item_data['item_code'],
                        'quantity': qty,
                        'unit_of_measure': item_data['unit_of_measure']
                    })
            
            # Sort by quantity and take top 5
            items_in_process.sort(key=lambda x: x['quantity'], reverse=True)
            top_items_by_process[process] = items_in_process[:5]
    
    return render_template('inventory/process_breakdown.html',
                         title='Process-Wise Inventory Breakdown',
                         process_summary=process_summary,
                         process_totals=process_totals,
                         top_items_by_process=top_items_by_process)

# API Endpoints for Batch Integration

@inventory_bp.route('/api/item/<int:item_id>/batch-summary')
@login_required
def api_item_batch_summary(item_id):
    """Get batch summary for a specific item"""
    try:
        item = Item.query.get_or_404(item_id)
        batches = ItemBatch.query.filter_by(item_id=item_id).all()
        
        summary = {
            'item_id': item_id,
            'item_name': item.name,
            'item_code': item.code,
            'total_batches': len(batches),
            'states': {
                'raw': sum(b.qty_raw or 0 for b in batches),
                'cutting': sum(b.qty_wip_cutting or 0 for b in batches),
                'bending': sum(b.qty_wip_bending or 0 for b in batches),
                'welding': sum(b.qty_wip_welding or 0 for b in batches),
                'zinc': sum(b.qty_wip_zinc or 0 for b in batches),
                'painting': sum(b.qty_wip_painting or 0 for b in batches),
                'assembly': sum(b.qty_wip_assembly or 0 for b in batches),
                'machining': sum(b.qty_wip_machining or 0 for b in batches),
                'polishing': sum(b.qty_wip_polishing or 0 for b in batches),
                'finished': sum(b.qty_finished or 0 for b in batches),
                'scrap': sum(b.qty_scrap or 0 for b in batches)
            },
            'batches': []
        }
        
        for batch in batches:
            batch_info = {
                'id': batch.id,
                'batch_number': batch.batch_number,
                'total_quantity': batch.total_quantity,
                'available_quantity': batch.available_quantity,
                'quality_status': batch.quality_status,
                'storage_location': batch.storage_location,
                'wip_breakdown': batch.wip_breakdown
            }
            summary['batches'].append(batch_info)
        
        summary['total_quantity'] = sum(summary['states'].values())
        summary['available_quantity'] = summary['states']['raw'] + summary['states']['finished']
        
        return jsonify(summary)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@inventory_bp.route('/unified')
@login_required
def unified_view():
    """Unified inventory view combining standard and multi-state information"""
    # Get filter parameters
    search = request.args.get('search', '').strip()
    item_type_filter = request.args.get('item_type', '')
    stock_status = request.args.get('stock_status', '')
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)
    
    # Base query
    query = Item.query
    
    # Apply filters
    if search:
        query = query.filter(
            (Item.name.ilike(f'%{search}%')) | 
            (Item.code.ilike(f'%{search}%'))
        )
    
    if item_type_filter:
        query = query.join(ItemType).filter(ItemType.name == item_type_filter)
    
    if min_price is not None:
        query = query.filter(Item.unit_price >= min_price)
    
    if max_price is not None:
        query = query.filter(Item.unit_price <= max_price)
    
    # Get all items
    items = query.order_by(Item.name).all()
    
    # Initialize multi-state inventory for items that haven't been set up
    for item in items:
        if item.qty_raw is None:
            item.qty_raw = item.current_stock or 0.0
            item.qty_wip = 0.0
            item.qty_finished = 0.0
            item.qty_scrap = 0.0
    
    db.session.commit()
    
    # Apply stock status filter after multi-state initialization
    if stock_status:
        if stock_status == 'low':
            items = [item for item in items if (item.available_stock or 0) <= (item.minimum_stock or 0) and (item.minimum_stock or 0) > 0]
        elif stock_status == 'out':
            items = [item for item in items if (item.available_stock or 0) == 0]
        elif stock_status == 'available':
            items = [item for item in items if (item.available_stock or 0) > 0]
    
    # Get item types for filter dropdown
    item_types = ItemType.query.filter_by(is_active=True).order_by(ItemType.name).all()
    
    return render_template('inventory/unified_view.html',
                         title='Unified Inventory View',
                         items=items,
                         item_types=item_types)

@inventory_bp.route('/list')
@login_required
def list_items():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '', type=str)
    item_type_filter = request.args.get('item_type', '', type=str)
    stock_status_filter = request.args.get('stock_status', '', type=str)
    min_price = request.args.get('min_price', '', type=str)
    max_price = request.args.get('max_price', '', type=str)
    
    query = Item.query
    
    # Apply filters
    if search:
        query = query.filter(Item.name.contains(search) | Item.code.contains(search))
    
    if item_type_filter:
        query = query.filter_by(item_type=item_type_filter)
    
    if stock_status_filter:
        if stock_status_filter == 'low_stock':
            query = query.filter(func.coalesce(Item.current_stock, 0) <= func.coalesce(Item.minimum_stock, 0))
        elif stock_status_filter == 'in_stock':
            query = query.filter(func.coalesce(Item.current_stock, 0) > func.coalesce(Item.minimum_stock, 0))
        elif stock_status_filter == 'out_of_stock':
            query = query.filter(func.coalesce(Item.current_stock, 0) == 0)
    
    if min_price:
        try:
            min_price_val = float(min_price)
            query = query.filter(func.coalesce(Item.unit_price, 0) >= min_price_val)
        except ValueError:
            flash('Invalid minimum price', 'error')
    
    if max_price:
        try:
            max_price_val = float(max_price)
            query = query.filter(func.coalesce(Item.unit_price, 0) <= max_price_val)
        except ValueError:
            flash('Invalid maximum price', 'error')
    
    items = query.order_by(Item.name).paginate(
        page=page, per_page=20, error_out=False)
    
    # Get all items for the list
    material_items = query.order_by(Item.name).all()
    
    # Get total count
    total_items = Item.query.count()
    
    return render_template('inventory/list.html', 
                         items=items, 
                         material_items=material_items,
                         total_items=total_items,
                         search=search,
                         item_type_filter=item_type_filter,
                         stock_status_filter=stock_status_filter,
                         min_price=min_price,
                         max_price=max_price)

@inventory_bp.route('/export')
@login_required
def export_items():
    """Export inventory items to Excel"""
    # Get same filter parameters as list_items
    search = request.args.get('search', '')
    item_type_filter = request.args.get('item_type', '')
    stock_status_filter = request.args.get('stock_status', '')
    min_price = request.args.get('min_price', '')
    max_price = request.args.get('max_price', '')
    
    query = Item.query
    
    # Apply filters
    if search:
        query = query.filter(Item.name.ilike(f'%{search}%') | Item.code.ilike(f'%{search}%'))
    
    if item_type_filter:
        query = query.filter_by(item_type=item_type_filter)
    
    if stock_status_filter == 'low_stock':
        query = query.filter(func.coalesce(Item.current_stock, 0) <= func.coalesce(Item.minimum_stock, 0))
    elif stock_status_filter == 'out_of_stock':
        query = query.filter(func.coalesce(Item.current_stock, 0) == 0)
    elif stock_status_filter == 'in_stock':
        query = query.filter(func.coalesce(Item.current_stock, 0) > 0)
    
    if min_price:
        try:
            min_price_val = float(min_price)
            query = query.filter(Item.unit_price >= min_price_val)
        except ValueError:
            pass
    
    if max_price:
        try:
            max_price_val = float(max_price)
            query = query.filter(Item.unit_price <= max_price_val)
        except ValueError:
            pass
    
    items = query.order_by(Item.name).all()
    
    return export_inventory_items(items)

@inventory_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_item():
    form = ItemForm()
    
    # Auto-generate item code if not provided
    if not form.code.data:
        form.code.data = generate_item_code()
    
    if form.validate_on_submit():
        # Check if item code already exists
        existing_item = Item.query.filter_by(code=form.code.data).first()
        if existing_item:
            flash('Item code already exists', 'danger')
            return render_template('inventory/form.html', form=form, title='Add Item')
        
        item_type_obj = ItemType.query.get(int(form.item_type.data))
        item = Item(
            code=form.code.data,
            name=form.name.data,
            description=form.description.data,
            unit_of_measure=form.unit_of_measure.data,
            hsn_code=form.hsn_code.data,
            gst_rate=form.gst_rate.data,
            current_stock=form.current_stock.data,
            minimum_stock=form.minimum_stock.data,
            unit_price=form.unit_price.data,
            unit_weight=form.unit_weight.data,
            item_type_id=int(form.item_type.data),
            item_type=item_type_obj.name.lower() if item_type_obj else 'material'
        )
        db.session.add(item)
        db.session.commit()
        flash('Item added successfully', 'success')
        return redirect(url_for('inventory.list_items'))
    
    return render_template('inventory/form.html', form=form, title='Add Item')

@inventory_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_item(id):
    item = Item.query.get_or_404(id)
    form = ItemForm(obj=item)
    
    if form.validate_on_submit():
        # Check if item code already exists (excluding current item)
        existing_item = Item.query.filter(Item.code == form.code.data, Item.id != id).first()
        if existing_item:
            flash('Item code already exists', 'danger')
            return render_template('inventory/form.html', form=form, title='Edit Item')
        
        item_type_obj = ItemType.query.get(int(form.item_type.data))
        item.code = form.code.data
        item.name = form.name.data
        item.description = form.description.data
        item.unit_of_measure = form.unit_of_measure.data
        item.hsn_code = form.hsn_code.data
        item.gst_rate = form.gst_rate.data
        item.current_stock = form.current_stock.data
        item.minimum_stock = form.minimum_stock.data
        item.unit_price = form.unit_price.data
        item.unit_weight = form.unit_weight.data
        item.item_type_id = int(form.item_type.data)
        item.item_type = item_type_obj.name.lower() if item_type_obj else 'material'
        
        db.session.commit()
        flash('Item updated successfully', 'success')
        return redirect(url_for('inventory.list_items'))
    
    return render_template('inventory/form.html', form=form, title='Edit Item', item=item)

@inventory_bp.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete_item(id):
    if not current_user.is_admin():
        flash('Only administrators can delete items', 'danger')
        return redirect(url_for('inventory.list_items'))
    
    item = Item.query.get_or_404(id)
    
    # Check if item is used in any orders or BOM
    if item.purchase_order_items or item.sales_order_items or item.bom_items:
        flash('Cannot delete item. It is referenced in orders or BOM.', 'danger')
        return redirect(url_for('inventory.list_items'))
    
    db.session.delete(item)
    db.session.commit()
    flash('Item deleted successfully', 'success')
    return redirect(url_for('inventory.list_items'))


# API Endpoints
@inventory_bp.route('/inventory/api/item-stock/<int:item_id>')
@inventory_bp.route('/api/item-stock/<int:item_id>')
@login_required
def get_item_stock(item_id):
    """API endpoint to get item stock information with multi-state inventory"""
    try:
        item = Item.query.get_or_404(item_id)
        
        # Initialize multi-state fields if not set
        if item.qty_raw is None:
            item.qty_raw = item.current_stock or 0.0
            item.qty_wip = 0.0
            item.qty_finished = 0.0
            item.qty_scrap = 0.0
            db.session.commit()
        
        return jsonify({
            'success': True,
            'item_id': item.id,
            'item_name': item.name,
            'item_code': item.code,
            'current_stock': item.current_stock or 0,
            'qty_raw': item.qty_raw or 0,
            'qty_wip': item.qty_wip or 0,
            'qty_finished': item.qty_finished or 0,
            'qty_scrap': item.qty_scrap or 0,
            'total_stock': item.total_stock,
            'available_stock': item.available_stock,
            'minimum_stock': item.minimum_stock or 0,
            'unit_of_measure': item.unit_of_measure or 'units',
            'unit_price': float(item.unit_price or 0),
            'unit_weight': float(item.unit_weight or 0),
            'low_stock': (item.available_stock or 0) <= (item.minimum_stock or 0)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
