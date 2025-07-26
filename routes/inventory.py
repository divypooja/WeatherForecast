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
    
    # Get items separated by material classification
    raw_materials = Item.query.filter(
        Item.material_classification == 'raw_material'
    ).order_by(Item.name).all()
    
    production_use_items = Item.query.filter(
        Item.material_classification == 'production_use'
    ).order_by(Item.name).all()
    
    finished_goods = Item.query.filter(
        Item.material_classification == 'finished_goods'
    ).order_by(Item.name).all()
    
    # Get counts for tabs
    raw_material_count = len(raw_materials)
    production_use_count = len(production_use_items)
    finished_goods_count = len(finished_goods)
    total_items = Item.query.count()
    
    return render_template('inventory/list.html', 
                         items=items, 
                         raw_materials=raw_materials,
                         production_use_items=production_use_items,
                         finished_goods=finished_goods,
                         raw_material_count=raw_material_count,
                         production_use_count=production_use_count,
                         finished_goods_count=finished_goods_count,
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
            material_classification=form.material_classification.data,
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
        item.material_classification = form.material_classification.data
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
    """API endpoint to get item stock information"""
    try:
        item = Item.query.get_or_404(item_id)
        return jsonify({
            'success': True,
            'item_id': item.id,
            'item_name': item.name,
            'item_code': item.code,
            'current_stock': item.current_stock or 0,
            'minimum_stock': item.minimum_stock or 0,
            'unit_of_measure': item.unit_of_measure or 'units',
            'unit_price': float(item.unit_price or 0),
            'unit_weight': float(item.unit_weight or 0),
            'low_stock': (item.current_stock or 0) <= (item.minimum_stock or 0)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
