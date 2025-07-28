"""
Complete rewrite of Inventory Management System
Pure multi-state inventory with zero legacy dependencies
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models import Item, ItemType, db
from forms import ItemForm
from utils_export import export_inventory_items
from utils import generate_item_code
from sqlalchemy import func
from datetime import datetime

inventory_bp = Blueprint('inventory', __name__, url_prefix='/inventory')

@inventory_bp.route('/')
@login_required
def dashboard():
    """Pure multi-state inventory dashboard"""
    # Multi-state statistics
    stats = {
        'total_items': Item.query.count(),
        'items_with_raw_material': Item.query.filter(Item.qty_raw > 0).count(),
        'items_in_wip': Item.query.filter(
            (Item.qty_wip_cutting > 0) | 
            (Item.qty_wip_bending > 0) | 
            (Item.qty_wip_welding > 0) |
            (Item.qty_wip_zinc > 0) | 
            (Item.qty_wip_painting > 0) | 
            (Item.qty_wip_assembly > 0) |
            (Item.qty_wip_machining > 0) | 
            (Item.qty_wip_polishing > 0)
        ).count(),
        'items_with_finished_goods': Item.query.filter(Item.qty_finished > 0).count(),
        'items_with_scrap': Item.query.filter(Item.qty_scrap > 0).count(),
        'low_stock_items': Item.query.filter(
            func.coalesce(Item.qty_raw, 0) + func.coalesce(Item.qty_finished, 0) <= func.coalesce(Item.minimum_stock, 0)
        ).count()
    }
    
    # Calculate total values using multi-state fields only
    all_items = Item.query.all()
    total_raw_value = sum((item.qty_raw or 0) * (item.unit_price or 0) for item in all_items)
    total_finished_value = sum((item.qty_finished or 0) * (item.unit_price or 0) for item in all_items)
    total_wip_value = sum((item.total_wip or 0) * (item.unit_price or 0) for item in all_items)
    
    stats.update({
        'total_raw_value': total_raw_value,
        'total_finished_value': total_finished_value,
        'total_wip_value': total_wip_value,
        'total_inventory_value': total_raw_value + total_finished_value + total_wip_value
    })
    
    # Recent items and alerts
    recent_items = Item.query.order_by(Item.created_at.desc()).limit(5).all()
    low_stock_items = Item.query.filter(
        func.coalesce(Item.qty_raw, 0) + func.coalesce(Item.qty_finished, 0) <= func.coalesce(Item.minimum_stock, 0)
    ).limit(10).all()
    
    # Multi-state summary
    multi_state_summary = {
        'total_raw': sum(item.qty_raw or 0 for item in all_items),
        'total_wip': sum(item.total_wip or 0 for item in all_items),
        'total_finished': sum(item.qty_finished or 0 for item in all_items),
        'total_scrap': sum(item.qty_scrap or 0 for item in all_items)
    }
    
    return render_template('inventory/dashboard_new.html', 
                         stats=stats, 
                         recent_items=recent_items,
                         low_stock_items=low_stock_items,
                         multi_state_summary=multi_state_summary)

@inventory_bp.route('/multi-state')
@login_required
def multi_state_view():
    """Pure multi-state inventory view"""
    items = Item.query.all()
    
    # Calculate totals using multi-state properties only
    total_raw = sum(item.qty_raw or 0 for item in items)
    total_wip = sum(item.total_wip or 0 for item in items)
    total_finished = sum(item.qty_finished or 0 for item in items)
    total_scrap = sum(item.qty_scrap or 0 for item in items)
    
    # Process-specific WIP totals
    process_wip_totals = {
        'cutting': sum(item.qty_wip_cutting or 0 for item in items),
        'bending': sum(item.qty_wip_bending or 0 for item in items),
        'welding': sum(item.qty_wip_welding or 0 for item in items),
        'zinc': sum(item.qty_wip_zinc or 0 for item in items),
        'painting': sum(item.qty_wip_painting or 0 for item in items),
        'assembly': sum(item.qty_wip_assembly or 0 for item in items),
        'machining': sum(item.qty_wip_machining or 0 for item in items),
        'polishing': sum(item.qty_wip_polishing or 0 for item in items)
    }
    
    return render_template('inventory/multi_state_view.html',
                         title='Multi-State Inventory Tracking',
                         items=items,
                         total_raw=total_raw,
                         total_wip=total_wip,
                         total_finished=total_finished,
                         total_scrap=total_scrap,
                         process_wip_totals=process_wip_totals)

@inventory_bp.route('/wip-breakdown')
@login_required
def wip_breakdown():
    """Process-specific WIP breakdown view"""
    items = Item.query.filter(
        (Item.qty_wip_cutting > 0) | 
        (Item.qty_wip_bending > 0) | 
        (Item.qty_wip_welding > 0) |
        (Item.qty_wip_zinc > 0) | 
        (Item.qty_wip_painting > 0) | 
        (Item.qty_wip_assembly > 0) |
        (Item.qty_wip_machining > 0) | 
        (Item.qty_wip_polishing > 0)
    ).all()
    
    # Calculate process totals
    process_totals = {
        'cutting': sum(item.qty_wip_cutting or 0 for item in items),
        'bending': sum(item.qty_wip_bending or 0 for item in items),
        'welding': sum(item.qty_wip_welding or 0 for item in items),
        'zinc': sum(item.qty_wip_zinc or 0 for item in items),
        'painting': sum(item.qty_wip_painting or 0 for item in items),
        'assembly': sum(item.qty_wip_assembly or 0 for item in items),
        'machining': sum(item.qty_wip_machining or 0 for item in items),
        'polishing': sum(item.qty_wip_polishing or 0 for item in items)
    }
    
    total_wip_items = len(items)
    
    return render_template('inventory/wip_breakdown.html',
                         items=items,
                         process_totals=process_totals,
                         total_wip_items=total_wip_items)

@inventory_bp.route('/list')
@login_required
def list_items():
    """List all inventory items with multi-state filtering"""
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
    
    # Multi-state stock filtering
    if stock_status_filter:
        if stock_status_filter == 'low_stock':
            query = query.filter(
                func.coalesce(Item.qty_raw, 0) + func.coalesce(Item.qty_finished, 0) <= func.coalesce(Item.minimum_stock, 0)
            )
        elif stock_status_filter == 'in_stock':
            query = query.filter(
                func.coalesce(Item.qty_raw, 0) + func.coalesce(Item.qty_finished, 0) > func.coalesce(Item.minimum_stock, 0)
            )
        elif stock_status_filter == 'out_of_stock':
            query = query.filter(
                func.coalesce(Item.qty_raw, 0) + func.coalesce(Item.qty_finished, 0) == 0
            )
        elif stock_status_filter == 'has_wip':
            query = query.filter(
                (Item.qty_wip_cutting > 0) | 
                (Item.qty_wip_bending > 0) | 
                (Item.qty_wip_welding > 0) |
                (Item.qty_wip_zinc > 0) | 
                (Item.qty_wip_painting > 0) | 
                (Item.qty_wip_assembly > 0) |
                (Item.qty_wip_machining > 0) | 
                (Item.qty_wip_polishing > 0)
            )
        elif stock_status_filter == 'has_scrap':
            query = query.filter(Item.qty_scrap > 0)
    
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
    
    # Paginate results
    items = query.order_by(Item.name).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('inventory/list.html', 
                         items=items,
                         search=search,
                         item_type_filter=item_type_filter,
                         stock_status_filter=stock_status_filter,
                         min_price=min_price,
                         max_price=max_price)

@inventory_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_item():
    """Add new inventory item with pure multi-state initialization"""
    form = ItemForm()
    
    # Auto-generate item code
    if not form.code.data:
        form.code.data = generate_item_code()
    
    if form.validate_on_submit():
        # Check for duplicate code
        existing_item = Item.query.filter_by(code=form.code.data).first()
        if existing_item:
            flash('Item code already exists', 'danger')
            return render_template('inventory/form_new.html', form=form, title='Add Item')
        
        # Get item type
        item_type_obj = ItemType.query.get(int(form.item_type.data))
        
        # Create new item with pure multi-state initialization
        item = Item(
            code=form.code.data,
            name=form.name.data,
            description=form.description.data,
            unit_of_measure=form.unit_of_measure.data,
            hsn_code=form.hsn_code.data,
            gst_rate=form.gst_rate.data,
            minimum_stock=form.minimum_stock.data,
            unit_price=form.unit_price.data,
            unit_weight=form.unit_weight.data,
            item_type_id=int(form.item_type.data),
            item_type=item_type_obj.name.lower() if item_type_obj else 'material',
            # Pure multi-state initialization - NO legacy current_stock
            qty_raw=form.current_stock.data or 0.0,  # Initial stock goes to raw material
            qty_wip_cutting=0.0,
            qty_wip_bending=0.0,
            qty_wip_welding=0.0,
            qty_wip_zinc=0.0,
            qty_wip_painting=0.0,
            qty_wip_assembly=0.0,
            qty_wip_machining=0.0,
            qty_wip_polishing=0.0,
            qty_finished=0.0,
            qty_scrap=0.0,
            current_stock=0.0  # Set legacy field to 0 - not used anymore
        )
        
        db.session.add(item)
        db.session.commit()
        flash('Item added successfully to Raw Material inventory', 'success')
        return redirect(url_for('inventory.multi_state_view'))
    
    return render_template('inventory/form_new.html', form=form, title='Add Item')

@inventory_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_item(id):
    """Edit inventory item with multi-state preservation"""
    item = Item.query.get_or_404(id)
    form = ItemForm(obj=item)
    
    # Pre-fill form with available stock (raw + finished)
    if not form.current_stock.data:
        form.current_stock.data = item.available_stock
    
    if form.validate_on_submit():
        # Check for duplicate code (excluding current item)
        existing_item = Item.query.filter(Item.code == form.code.data, Item.id != id).first()
        if existing_item:
            flash('Item code already exists', 'danger')
            return render_template('inventory/form_new.html', form=form, title='Edit Item', item=item)
        
        # Get item type
        item_type_obj = ItemType.query.get(int(form.item_type.data))
        
        # Update item properties (preserve multi-state quantities)
        item.code = form.code.data
        item.name = form.name.data
        item.description = form.description.data
        item.unit_of_measure = form.unit_of_measure.data
        item.hsn_code = form.hsn_code.data
        item.gst_rate = form.gst_rate.data
        item.minimum_stock = form.minimum_stock.data
        item.unit_price = form.unit_price.data
        item.unit_weight = form.unit_weight.data
        item.item_type_id = int(form.item_type.data)
        item.item_type = item_type_obj.name.lower() if item_type_obj else 'material'
        
        # Handle stock adjustment only for raw materials
        new_total_available = form.current_stock.data or 0.0
        current_available = item.available_stock
        
        if new_total_available != current_available:
            difference = new_total_available - current_available
            # Adjust raw material stock only
            item.qty_raw = max(0, (item.qty_raw or 0) + difference)
        
        db.session.commit()
        flash('Item updated successfully', 'success')
        return redirect(url_for('inventory.multi_state_view'))
    
    return render_template('inventory/form_new.html', form=form, title='Edit Item', item=item)

@inventory_bp.route('/api/item-stock/<int:item_id>')
@login_required
def api_item_stock(item_id):
    """API endpoint for real-time multi-state stock information"""
    item = Item.query.get_or_404(item_id)
    
    return jsonify({
        'id': item.id,
        'name': item.name,
        'code': item.code,
        'unit_of_measure': item.unit_of_measure,
        'qty_raw': item.qty_raw or 0,
        'total_wip': item.total_wip or 0,
        'qty_finished': item.qty_finished or 0,
        'qty_scrap': item.qty_scrap or 0,
        'total_stock': item.total_stock or 0,
        'available_stock': item.available_stock or 0,
        'minimum_stock': item.minimum_stock or 0,
        'unit_price': item.unit_price or 0,
        'wip_breakdown': item.wip_breakdown,
        'stock_status': 'adequate' if (item.available_stock or 0) > (item.minimum_stock or 0) else 'low' if (item.available_stock or 0) > 0 else 'out_of_stock'
    })

@inventory_bp.route('/api/bulk-stock-check', methods=['POST'])
@login_required
def api_bulk_stock_check():
    """Bulk stock availability check for job work creation"""
    data = request.get_json()
    items_to_check = data.get('items', [])
    
    results = []
    for item_data in items_to_check:
        item_id = item_data.get('item_id')
        requested_qty = item_data.get('quantity', 0)
        
        item = Item.query.get(item_id)
        if item:
            available = item.available_stock or 0
            status = 'sufficient' if available >= requested_qty else 'insufficient'
            shortage = max(0, requested_qty - available) if status == 'insufficient' else 0
            
            results.append({
                'item_id': item_id,
                'item_name': item.name,
                'requested_qty': requested_qty,
                'available_qty': available,
                'status': status,
                'shortage': shortage,
                'unit': item.unit_of_measure
            })
        else:
            results.append({
                'item_id': item_id,
                'status': 'not_found',
                'error': 'Item not found'
            })
    
    return jsonify({'results': results})