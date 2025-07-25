from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from forms import ProductionForm, BOMForm, BOMItemForm
from models import Production, Item, BOM, BOMItem
from app import db
from sqlalchemy import func
from utils import generate_production_number

production_bp = Blueprint('production', __name__)

@production_bp.route('/dashboard')
@login_required
def dashboard():
    # Production statistics
    stats = {
        'total_productions': Production.query.count(),
        'planned_productions': Production.query.filter_by(status='planned').count(),
        'in_progress_productions': Production.query.filter_by(status='in_progress').count(),
        'completed_productions': Production.query.filter_by(status='completed').count(),
        'total_boms': BOM.query.filter_by(is_active=True).count()
    }
    
    # Recent productions
    recent_productions = Production.query.order_by(Production.created_at.desc()).limit(10).all()
    
    # Today's production summary
    from datetime import date
    today_productions = Production.query.filter_by(production_date=date.today()).all()
    
    # Products with BOM
    products_with_bom = db.session.query(Item).join(BOM).filter(BOM.is_active == True).all()
    
    return render_template('production/dashboard.html', 
                         stats=stats, 
                         recent_productions=recent_productions,
                         today_productions=today_productions,
                         products_with_bom=products_with_bom)

@production_bp.route('/list')
@login_required
def list_productions():
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', '', type=str)
    
    query = Production.query
    if status_filter:
        query = query.filter_by(status=status_filter)
    
    productions = query.order_by(Production.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False)
    
    return render_template('production/list.html', productions=productions, status_filter=status_filter)

@production_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_production():
    form = ProductionForm()
    # Only show items that have BOM or are products
    form.item_id.choices = [(i.id, f"{i.code} - {i.name}") for i in Item.query.filter(Item.item_type == 'product').all()]
    
    # Auto-generate production number if not provided
    if not form.production_number.data:
        form.production_number.data = generate_production_number()
    
    if form.validate_on_submit():
        # Check if production number already exists
        existing_production = Production.query.filter_by(production_number=form.production_number.data).first()
        if existing_production:
            flash('Production number already exists', 'danger')
            return render_template('production/form.html', form=form, title='Add Production')
        
        # Get the BOM for the selected item
        selected_item = Item.query.get(form.item_id.data)
        active_bom = BOM.query.filter_by(product_id=form.item_id.data, is_active=True).first()
        
        material_shortages = []
        bom_items = []
        
        if active_bom:
            bom_items = BOMItem.query.filter_by(bom_id=active_bom.id).all()
            
            # Check material availability for each BOM item
            for bom_item in bom_items:
                required_qty = bom_item.quantity_required * form.quantity_planned.data
                available_qty = bom_item.item.current_stock or 0
                
                if available_qty < required_qty:
                    shortage_qty = required_qty - available_qty
                    material_shortages.append({
                        'item_code': bom_item.item.code,
                        'item_name': bom_item.item.name,
                        'required_qty': required_qty,
                        'available_qty': available_qty,
                        'shortage_qty': shortage_qty,
                        'unit': bom_item.item.unit_of_measure
                    })
        
        # If there are material shortages, show them and prevent production creation
        if material_shortages:
            shortage_message = "Cannot create production order. Material shortages detected:<br>"
            for shortage in material_shortages:
                shortage_message += f"• {shortage['item_code']} - {shortage['item_name']}: "
                shortage_message += f"Need {shortage['required_qty']:.2f} {shortage['unit']}, "
                shortage_message += f"Available {shortage['available_qty']:.2f} {shortage['unit']}, "
                shortage_message += f"<strong>Short by {shortage['shortage_qty']:.2f} {shortage['unit']}</strong><br>"
            
            flash(shortage_message, 'danger')
            return render_template('production/form.html', 
                                 form=form, 
                                 title='Add Production',
                                 material_shortages=material_shortages,
                                 bom_items=bom_items,
                                 selected_item=selected_item)
        
        production = Production(
            production_number=form.production_number.data,
            item_id=form.item_id.data,
            quantity_planned=form.quantity_planned.data,
            quantity_produced=form.quantity_produced.data or 0.0,
            quantity_good=form.quantity_good.data or 0.0,
            quantity_damaged=form.quantity_damaged.data or 0.0,
            production_date=form.production_date.data,
            status=form.status.data,
            notes=form.notes.data,
            created_by=current_user.id
        )
        db.session.add(production)
        db.session.commit()
        flash('Production order created successfully! All required materials are available.', 'success')
        return redirect(url_for('production.list_productions'))
    
    # Get BOM items for display if an item is selected
    bom_items = []
    selected_item = None
    if form.item_id.data:
        selected_item = Item.query.get(form.item_id.data)
        active_bom = BOM.query.filter_by(product_id=form.item_id.data, is_active=True).first()
        if active_bom:
            bom_items = BOMItem.query.filter_by(bom_id=active_bom.id).all()
    
    return render_template('production/form.html', 
                         form=form, 
                         title='Add Production',
                         bom_items=bom_items,
                         selected_item=selected_item)

@production_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_production(id):
    production = Production.query.get_or_404(id)
    form = ProductionForm(obj=production)
    form.item_id.choices = [(i.id, f"{i.code} - {i.name}") for i in Item.query.filter(Item.item_type == 'product').all()]
    
    if form.validate_on_submit():
        # Check if production number already exists (excluding current production)
        existing_production = Production.query.filter(
            Production.production_number == form.production_number.data, 
            Production.id != id
        ).first()
        if existing_production:
            flash('Production number already exists', 'danger')
            return render_template('production/form.html', form=form, title='Edit Production', production=production)
        
        production.production_number = form.production_number.data
        production.item_id = form.item_id.data
        production.quantity_planned = form.quantity_planned.data
        production.production_date = form.production_date.data
        production.notes = form.notes.data
        
        db.session.commit()
        flash('Production order updated successfully', 'success')
        return redirect(url_for('production.list_productions'))
    
    # Get BOM for the product if available
    bom = BOM.query.filter_by(product_id=production.item_id, is_active=True).first()
    bom_items = []
    if bom:
        bom_items = BOMItem.query.filter_by(bom_id=bom.id).all()
    
    return render_template('production/form.html', 
                         form=form, 
                         title='Edit Production', 
                         production=production,
                         bom_items=bom_items)

@production_bp.route('/update_status/<int:id>/<status>')
@login_required
def update_status(id, status):
    production = Production.query.get_or_404(id)
    if status in ['planned', 'in_progress', 'completed']:
        production.status = status
        db.session.commit()
        flash(f'Production status updated to {status}', 'success')
    else:
        flash('Invalid status', 'danger')
    
    return redirect(url_for('production.list_productions'))

@production_bp.route('/bom')
@login_required
def list_bom():
    page = request.args.get('page', 1, type=int)
    boms = BOM.query.filter_by(is_active=True).paginate(
        page=page, per_page=20, error_out=False)
    
    return render_template('production/bom_list.html', boms=boms)

@production_bp.route('/bom/add', methods=['GET', 'POST'])
@login_required
def add_bom():
    form = BOMForm()
    # Only show products (finished goods)
    form.product_id.choices = [(i.id, f"{i.code} - {i.name}") for i in Item.query.filter(Item.item_type == 'product').all()]
    
    if form.validate_on_submit():
        # Check if BOM already exists for this product
        existing_bom = BOM.query.filter_by(product_id=form.product_id.data, is_active=True).first()
        if existing_bom:
            flash('An active BOM already exists for this product. Please deactivate the existing BOM first.', 'warning')
            return render_template('production/bom_form.html', form=form, title='Add BOM')
        
        bom = BOM(
            product_id=form.product_id.data,
            version=form.version.data,
            is_active=True,
            labor_cost_per_unit=form.labor_cost_per_unit.data or 0.0,
            labor_hours_per_unit=form.labor_hours_per_unit.data or 0.0,
            labor_rate_per_hour=form.labor_rate_per_hour.data or 0.0,
            overhead_cost_per_unit=form.overhead_cost_per_unit.data or 0.0,
            overhead_percentage=form.overhead_percentage.data or 0.0,
            freight_cost_per_unit=form.freight_cost_per_unit.data or 0.0
        )
        db.session.add(bom)
        db.session.commit()
        flash('BOM created successfully', 'success')
        return redirect(url_for('production.edit_bom', id=bom.id))
    
    return render_template('production/bom_form.html', form=form, title='Add BOM')

@production_bp.route('/bom/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_bom(id):
    bom = BOM.query.get_or_404(id)
    form = BOMForm(obj=bom)
    form.product_id.choices = [(i.id, f"{i.code} - {i.name}") for i in Item.query.filter(Item.item_type == 'product').all()]
    
    if form.validate_on_submit():
        # Check if BOM already exists for this product (excluding current BOM)
        existing_bom = BOM.query.filter(
            BOM.product_id == form.product_id.data, 
            BOM.is_active == True,
            BOM.id != id
        ).first()
        if existing_bom:
            flash('An active BOM already exists for this product. Please deactivate the existing BOM first.', 'warning')
            return render_template('production/bom_form.html', form=form, title='Edit BOM', bom=bom)
        
        bom.product_id = form.product_id.data
        bom.version = form.version.data
        bom.labor_cost_per_unit = form.labor_cost_per_unit.data or 0.0
        bom.labor_hours_per_unit = form.labor_hours_per_unit.data or 0.0
        bom.labor_rate_per_hour = form.labor_rate_per_hour.data or 0.0
        bom.overhead_cost_per_unit = form.overhead_cost_per_unit.data or 0.0
        bom.overhead_percentage = form.overhead_percentage.data or 0.0
        bom.freight_cost_per_unit = form.freight_cost_per_unit.data or 0.0
        
        db.session.commit()
        flash('BOM updated successfully', 'success')
        return redirect(url_for('production.list_bom'))
    
    # Get BOM items
    bom_items = BOMItem.query.filter_by(bom_id=bom.id).all()
    
    # Calculate total BOM cost using the enhanced BOM model properties
    material_cost = bom.total_material_cost
    total_cost_per_unit = bom.total_cost_per_unit
    
    # Get materials for adding new items
    materials = Item.query.filter(Item.item_type.in_(['material', 'consumable'])).all()
    
    return render_template('production/bom_form.html', 
                         form=form, 
                         title='Edit BOM', 
                         bom=bom,
                         bom_items=bom_items,
                         materials=materials,
                         material_cost=material_cost,
                         total_cost_per_unit=total_cost_per_unit)

@production_bp.route('/bom/<int:bom_id>/add_item', methods=['POST'])
@login_required
def add_bom_item(bom_id):
    bom = BOM.query.get_or_404(bom_id)
    
    item_id = request.form.get('item_id', type=int)
    quantity_required = request.form.get('quantity_required', type=float)
    unit_cost = request.form.get('unit_cost', type=float, default=0.0)
    
    if not item_id or not quantity_required:
        flash('Please provide item and quantity', 'danger')
        return redirect(url_for('production.edit_bom', id=bom_id))
    
    # Check if item already exists in this BOM
    existing_item = BOMItem.query.filter_by(bom_id=bom_id, item_id=item_id).first()
    if existing_item:
        flash('This item is already in the BOM', 'warning')
        return redirect(url_for('production.edit_bom', id=bom_id))
    
    # Auto-populate unit cost from inventory if not provided
    if unit_cost == 0.0:
        item = Item.query.get(item_id)
        if item and item.unit_price:
            unit_cost = item.unit_price
    
    bom_item = BOMItem(
        bom_id=bom_id,
        item_id=item_id,
        quantity_required=quantity_required,
        unit_cost=unit_cost
    )
    
    db.session.add(bom_item)
    db.session.commit()
    flash('Item added to BOM successfully', 'success')
    
    return redirect(url_for('production.edit_bom', id=bom_id))

@production_bp.route('/bom_item/delete/<int:id>')
@login_required
def delete_bom_item(id):
    bom_item = BOMItem.query.get_or_404(id)
    bom_id = bom_item.bom_id
    
    db.session.delete(bom_item)
    db.session.commit()
    flash('Item removed from BOM', 'success')
    
    return redirect(url_for('production.edit_bom', id=bom_id))

@production_bp.route('/bom/delete/<int:id>')
@login_required
def delete_bom(id):
    bom = BOM.query.get_or_404(id)
    
    # Set BOM as inactive instead of deleting
    bom.is_active = False
    db.session.commit()
    flash('BOM deactivated successfully', 'success')
    
    return redirect(url_for('production.list_bom'))

@production_bp.route('/api/item_details/<int:item_id>')
@login_required  
def get_item_details(item_id):
    """API endpoint to get item details including unit price for BOM auto-population"""
    item = Item.query.get_or_404(item_id)
    return {
        'id': item.id,
        'code': item.code,
        'name': item.name,
        'unit_price': item.unit_price or 0.0,
        'unit_of_measure': item.unit_of_measure,
        'item_type': item.item_type
    }

@production_bp.route('/check_material_availability', methods=['POST'])
@login_required
def check_material_availability():
    """API endpoint to check material availability for production planning"""
    item_id = request.json.get('item_id')
    quantity = float(request.json.get('quantity', 1))
    
    if not item_id:
        return jsonify({'error': 'Item ID required'}), 400
    
    # Get BOM for the item
    active_bom = BOM.query.filter_by(product_id=item_id, is_active=True).first()
    
    if not active_bom:
        return jsonify({
            'has_bom': False,
            'message': 'No BOM found for this item'
        })
    
    # Check material availability
    bom_items = BOMItem.query.filter_by(bom_id=active_bom.id).all()
    material_data = []
    has_shortages = False
    
    for bom_item in bom_items:
        required_qty = bom_item.quantity_required * quantity
        available_qty = bom_item.item.current_stock or 0
        is_sufficient = available_qty >= required_qty
        
        if not is_sufficient:
            has_shortages = True
        
        material_data.append({
            'item_code': bom_item.item.code,
            'item_name': bom_item.item.name,
            'quantity_required': bom_item.quantity_required,
            'total_required': required_qty,
            'available_qty': available_qty,
            'is_sufficient': is_sufficient,
            'shortage_qty': max(0, required_qty - available_qty),
            'unit': bom_item.item.unit_of_measure
        })
    
    return jsonify({
        'has_bom': True,
        'has_shortages': has_shortages,
        'materials': material_data
    })
