from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from forms import ItemForm
from models import Item, ItemType
from app import db
from sqlalchemy import func
from utils import generate_item_code
from utils_export import export_inventory_items

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
@inventory_bp.route('/api/items')
@login_required
def api_get_items():
    """API endpoint to get all items for dropdown population"""
    try:
        items = Item.query.filter_by(is_active=True).order_by(Item.name).all()
        items_data = []
        
        for item in items:
            items_data.append({
                'id': item.id,
                'code': item.code,
                'name': item.name,
                'unit_of_measure': item.unit_of_measure
            })
        
        return jsonify({
            'success': True,
            'items': items_data
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error fetching items: {str(e)}'
        }), 500

@inventory_bp.route('/inventory/api/item-stock/<int:item_id>')
@inventory_bp.route('/api/item-stock/<int:item_id>')
@login_required
def get_item_stock(item_id):
    """API endpoint to get item stock information with multi-state inventory and BOM data"""
    try:
        from models import BOM, BOMItem
        
        item = Item.query.get_or_404(item_id)
        
        # Initialize multi-state fields if not set
        if item.qty_raw is None:
            item.qty_raw = item.current_stock or 0.0
            item.qty_wip = 0.0
            item.qty_finished = 0.0
            item.qty_scrap = 0.0
            db.session.commit()
        
        # Check for BOM data
        active_bom = BOM.query.filter_by(product_id=item_id, is_active=True).first()
        bom_data = None
        
        if active_bom:
            bom_items = BOMItem.query.filter_by(bom_id=active_bom.id).all()
            total_material_cost = sum(
                (bom_item.quantity_required * (bom_item.unit_cost or 0)) 
                for bom_item in bom_items
            )
            
            bom_data = {
                'has_bom': True,
                'bom_id': active_bom.id,
                'output_quantity': active_bom.output_quantity or 1.0,
                'total_material_cost': float(total_material_cost),
                'total_cost_per_unit': float(active_bom.total_cost_per_unit or 0),
                'material_count': len(bom_items),
                'materials': [{
                    'item_code': bom_item.item.code,
                    'item_name': bom_item.item.name,
                    'quantity_required': float(bom_item.quantity_required),
                    'unit_cost': float(bom_item.unit_cost or 0),
                    'unit': bom_item.unit or bom_item.item.unit_of_measure
                } for bom_item in bom_items]
            }
        else:
            bom_data = {'has_bom': False}
        
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
            'low_stock': (item.available_stock or 0) <= (item.minimum_stock or 0),
            'bom': bom_data
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
