from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from forms import ProductionForm, BOMForm, BOMItemForm, BOMProcessForm
from models import Production, Item, BOM, BOMItem, BOMProcess, Supplier
from services.process_integration import ProcessIntegrationService
from app import db
from sqlalchemy import func
from utils import generate_production_number
from datetime import datetime
import json

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
    # Allow any product type for BOM creation - no restrictions
    form.product_id.choices = [(i.id, f"{i.code} - {i.name}") for i in Item.query.order_by(Item.name).all()]
    
    if form.validate_on_submit():
        # Check if BOM code already exists
        existing_bom_code = BOM.query.filter_by(bom_code=form.bom_code.data).first()
        if existing_bom_code:
            flash('BOM code already exists. Please use a unique code.', 'warning')
            return render_template('production/bom_form.html', form=form, title='Add BOM')
        
        # Check if active BOM already exists for this product
        existing_bom = BOM.query.filter_by(product_id=form.product_id.data, is_active=True).first()
        if existing_bom and form.status.data == 'active':
            flash('An active BOM already exists for this product. Please deactivate the existing BOM first.', 'warning')
            return render_template('production/bom_form.html', form=form, title='Add BOM')
        
        # Auto-generate BOM code if not provided
        bom_code = form.bom_code.data
        if not bom_code:
            # Auto-generate BOM code: BOM-YYYY-####
            year = datetime.now().year
            last_bom = BOM.query.filter(
                BOM.bom_code.like(f'BOM-{year}-%')
            ).order_by(BOM.bom_code.desc()).first()
            
            if last_bom:
                # Extract the number from the last BOM code
                try:
                    last_number = int(last_bom.bom_code.split('-')[-1])
                    new_number = last_number + 1
                except:
                    new_number = 1
            else:
                new_number = 1
            
            bom_code = f'BOM-{year}-{new_number:04d}'

        bom = BOM(
            bom_code=bom_code,
            product_id=form.product_id.data,
            output_uom_id=form.output_uom_id.data if form.output_uom_id.data != 0 else None,
            version=form.version.data or '1.0',
            status=form.status.data or 'active',
            is_active=form.is_active.data and (form.status.data == 'active' if form.status.data else True),
            output_quantity=form.output_quantity.data or 1.0,
            estimated_scrap_percent=form.estimated_scrap_percent.data or 0.0,
            scrap_quantity=form.scrap_quantity.data or 0.0,
            scrap_uom=form.scrap_uom.data or 'kg',
            scrap_value_recovery_percent=form.scrap_value_recovery_percent.data or 15.0,
            description=form.description.data,
            remarks=form.remarks.data,
            labor_cost_per_unit=form.labor_cost_per_unit.data or 0.0,
            labor_hours_per_unit=form.labor_hours_per_unit.data or 0.0,
            labor_rate_per_hour=form.labor_rate_per_hour.data or 0.0,
            overhead_cost_per_unit=form.overhead_cost_per_unit.data or 0.0,
            overhead_percentage=form.overhead_percentage.data or 0.0,
            freight_cost_per_unit=form.freight_cost_per_unit.data or 0.0,
            freight_unit_type=form.freight_unit_type.data or 'per_piece',
            markup_percentage=form.markup_percentage.data or 0.0,
            created_by=current_user.id
        )
        db.session.add(bom)
        db.session.flush()  # Get the BOM ID
        
        db.session.commit()
        flash('Advanced BOM created successfully with enhanced features', 'success')
        
        # Check which action was clicked
        action = request.form.get('action', 'save_and_continue')
        if action == 'save_and_close':
            return redirect(url_for('production.list_bom'))
        else:
            return redirect(url_for('production.edit_bom', id=bom.id))
    
    return render_template('production/bom_form.html', form=form, title='Add BOM')

@production_bp.route('/bom/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_bom(id):
    bom = BOM.query.get_or_404(id)
    
    # Initialize form and populate choices first
    form = BOMForm()
    # Allow any product type for BOM creation - no restrictions  
    form.product_id.choices = [(i.id, f"{i.code} - {i.name}") for i in Item.query.order_by(Item.name).all()]
    
    # For GET request, populate form with existing BOM data
    if request.method == 'GET':
        form.bom_code.data = bom.bom_code
        form.product_id.data = bom.product_id
        form.output_uom_id.data = bom.output_uom_id
        form.version.data = bom.version
        form.status.data = bom.status
        form.is_active.data = bom.is_active
        form.output_quantity.data = bom.output_quantity
        form.estimated_scrap_percent.data = bom.estimated_scrap_percent
        form.scrap_quantity.data = bom.scrap_quantity
        form.scrap_uom.data = bom.scrap_uom
        form.scrap_value_recovery_percent.data = bom.scrap_value_recovery_percent
        form.description.data = bom.description
        form.remarks.data = bom.remarks
        form.labor_cost_per_unit.data = bom.labor_cost_per_unit
        form.labor_hours_per_unit.data = bom.labor_hours_per_unit
        form.labor_rate_per_hour.data = bom.labor_rate_per_hour
        form.overhead_cost_per_unit.data = bom.overhead_cost_per_unit
        form.overhead_percentage.data = bom.overhead_percentage
        form.freight_cost_per_unit.data = bom.freight_cost_per_unit
        form.freight_unit_type.data = bom.freight_unit_type
        form.markup_percentage.data = bom.markup_percentage
    
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
        
        bom.bom_code = form.bom_code.data
        bom.product_id = form.product_id.data
        bom.output_uom_id = form.output_uom_id.data if form.output_uom_id.data != 0 else None
        bom.version = form.version.data
        bom.status = form.status.data
        bom.is_active = form.is_active.data and form.status.data == 'active'
        bom.output_quantity = form.output_quantity.data or 1.0
        bom.estimated_scrap_percent = form.estimated_scrap_percent.data or 0.0
        bom.scrap_quantity = form.scrap_quantity.data or 0.0
        bom.scrap_uom = form.scrap_uom.data or 'kg'
        bom.scrap_value_recovery_percent = form.scrap_value_recovery_percent.data or 15.0
        bom.description = form.description.data
        bom.remarks = form.remarks.data
        bom.labor_cost_per_unit = form.labor_cost_per_unit.data or 0.0
        bom.labor_hours_per_unit = form.labor_hours_per_unit.data or 0.0
        bom.labor_rate_per_hour = form.labor_rate_per_hour.data or 0.0
        bom.overhead_cost_per_unit = form.overhead_cost_per_unit.data or 0.0
        bom.overhead_percentage = form.overhead_percentage.data or 0.0
        bom.freight_cost_per_unit = form.freight_cost_per_unit.data or 0.0
        bom.freight_unit_type = form.freight_unit_type.data or 'per_piece'
        bom.markup_percentage = form.markup_percentage.data or 0.0
        bom.updated_at = datetime.utcnow()
        
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
    unit = request.form.get('unit', default='pcs')
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
        unit=unit,
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
    flash('Item removed from BOM successfully', 'success')
    
    return redirect(url_for('production.edit_bom', id=bom_id))

@production_bp.route('/bom/delete/<int:id>')
@login_required
def delete_bom(id):
    bom = BOM.query.get_or_404(id)
    
    # Check if BOM has items or processes
    if bom.items or bom.processes:
        flash('Cannot delete BOM with existing items or processes. Please remove all components first.', 'error')
        return redirect(url_for('production.list_bom'))
    
    try:
        db.session.delete(bom)
        db.session.commit()
        flash('Advanced BOM deleted successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting BOM: {str(e)}', 'error')
    
    return redirect(url_for('production.list_bom'))

# Enhanced BOM Item Routes
@production_bp.route('/bom/<int:bom_id>/add_item', methods=['GET', 'POST'])
@login_required
def add_bom_item_enhanced(bom_id):
    """Add advanced BOM item with enhanced features"""
    bom = BOM.query.get_or_404(bom_id)
    form = BOMItemForm()
    
    if form.validate_on_submit():
        # Handle both new and legacy field structures
        material_id = form.material_id.data or form.item_id.data
        qty_required = form.qty_required.data or form.quantity_required.data
        
        if not material_id or not qty_required:
            flash('Material and quantity are required', 'error')
            return render_template('production/bom_item_form.html', form=form, bom=bom, title='Add BOM Item')
        
        # Check for duplicate items
        existing_item = BOMItem.query.filter_by(bom_id=bom_id, material_id=material_id).first()
        if existing_item:
            flash('This material is already in the BOM', 'warning')
            return render_template('production/bom_item_form.html', form=form, bom=bom, title='Add BOM Item')
        
        # Handle UOM - use default if none selected
        uom_id = form.uom_id.data if form.uom_id.data != 0 else None
        if not uom_id:
            # Try to get a default UOM (first available)
            try:
                from models_uom import UnitOfMeasure
                default_uom = UnitOfMeasure.query.first()
                uom_id = default_uom.id if default_uom else 1  # Fallback to ID 1
            except:
                uom_id = 1  # Fallback to default UOM ID
        
        # Create enhanced BOM item
        bom_item = BOMItem(
            bom_id=bom_id,
            material_id=material_id,
            qty_required=qty_required,
            uom_id=uom_id,
            unit_cost=form.unit_cost.data or 0.0,
            scrap_percent=form.scrap_percent.data or 0.0,
            process_step=form.process_step.data or 1,
            process_name=form.process_name.data,
            is_critical=form.is_critical.data,
            substitute_materials=form.substitute_materials.data,
            default_supplier_id=form.default_supplier_id.data if form.default_supplier_id.data != 0 else None,
            remarks=form.remarks.data,
            # Legacy compatibility
            item_id=material_id,
            quantity_required=qty_required,
            unit=form.unit.data or 'pcs'
        )
        
        db.session.add(bom_item)
        db.session.commit()
        flash('Enhanced BOM item added successfully with advanced features', 'success')
        return redirect(url_for('production.edit_bom', id=bom_id))
    
    return render_template('production/bom_item_form.html', form=form, bom=bom, title='Add Enhanced BOM Item')

# BOM Process Routes
@production_bp.route('/bom/<int:bom_id>/add_process', methods=['GET', 'POST'])
@login_required
def add_bom_process(bom_id):
    """Add process routing to BOM"""
    bom = BOM.query.get_or_404(bom_id)
    form = BOMProcessForm()
    
    if form.validate_on_submit():
        # Check for duplicate step numbers
        existing_step = BOMProcess.query.filter_by(bom_id=bom_id, step_number=form.step_number.data).first()
        if existing_step:
            flash('A process with this step number already exists', 'warning')
            return render_template('production/bom_process_form.html', form=form, bom=bom, title='Add Process')
        
        bom_process = BOMProcess(
            bom_id=bom_id,
            step_number=form.step_number.data,
            process_name=form.process_name.data,
            process_code=form.process_code.data,
            operation_description=form.operation_description.data,
            setup_time_minutes=form.setup_time_minutes.data or 0.0,
            run_time_minutes=form.run_time_minutes.data or 0.0,
            labor_rate_per_hour=form.labor_rate_per_hour.data or 0.0,
            machine_id=form.machine_id.data if form.machine_id.data != 0 else None,
            department_id=form.department_id.data if form.department_id.data != 0 else None,
            is_outsourced=form.is_outsourced.data,
            vendor_id=form.vendor_id.data if form.vendor_id.data != 0 else None,
            cost_per_unit=form.cost_per_unit.data or 0.0,
            quality_check_required=form.quality_check_required.data,
            estimated_scrap_percent=form.estimated_scrap_percent.data or 0.0,
            parallel_processes=form.parallel_processes.data,
            predecessor_processes=form.predecessor_processes.data,
            notes=form.notes.data
        )
        
        db.session.add(bom_process)
        db.session.commit()
        flash('Process routing added successfully', 'success')
        return redirect(url_for('production.edit_bom', id=bom_id))
    
    return render_template('production/bom_process_form.html', form=form, bom=bom, title='Add Process Routing')

@production_bp.route('/bom/process/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_bom_process(id):
    """Edit BOM process"""
    process = BOMProcess.query.get_or_404(id)
    form = BOMProcessForm()
    
    if request.method == 'GET':
        # Populate form with existing data
        form.step_number.data = process.step_number
        form.process_name.data = process.process_name
        form.process_code.data = process.process_code
        form.operation_description.data = process.operation_description
        form.setup_time_minutes.data = process.setup_time_minutes
        form.run_time_minutes.data = process.run_time_minutes
        form.labor_rate_per_hour.data = process.labor_rate_per_hour
        form.machine_id.data = process.machine_id
        form.department_id.data = process.department_id
        form.is_outsourced.data = process.is_outsourced
        form.vendor_id.data = process.vendor_id
        form.cost_per_unit.data = process.cost_per_unit
        form.quality_check_required.data = process.quality_check_required
        form.estimated_scrap_percent.data = process.estimated_scrap_percent
        form.parallel_processes.data = process.parallel_processes
        form.predecessor_processes.data = process.predecessor_processes
        form.notes.data = process.notes
    
    if form.validate_on_submit():
        # Check for duplicate step numbers (excluding current process)
        existing_step = BOMProcess.query.filter(
            BOMProcess.bom_id == process.bom_id, 
            BOMProcess.step_number == form.step_number.data,
            BOMProcess.id != id
        ).first()
        if existing_step:
            flash('A process with this step number already exists', 'warning')
            return render_template('production/bom_process_form.html', form=form, bom=process.bom, title='Edit Process')
        
        # Update process
        process.step_number = form.step_number.data
        process.process_name = form.process_name.data
        process.process_code = form.process_code.data
        process.operation_description = form.operation_description.data
        process.setup_time_minutes = form.setup_time_minutes.data or 0.0
        process.run_time_minutes = form.run_time_minutes.data or 0.0
        process.labor_rate_per_hour = form.labor_rate_per_hour.data or 0.0
        process.machine_id = form.machine_id.data if form.machine_id.data != 0 else None
        process.department_id = form.department_id.data if form.department_id.data != 0 else None
        process.is_outsourced = form.is_outsourced.data
        process.vendor_id = form.vendor_id.data if form.vendor_id.data != 0 else None
        process.cost_per_unit = form.cost_per_unit.data or 0.0
        process.quality_check_required = form.quality_check_required.data
        process.estimated_scrap_percent = form.estimated_scrap_percent.data or 0.0
        process.parallel_processes = form.parallel_processes.data
        process.predecessor_processes = form.predecessor_processes.data
        process.notes = form.notes.data
        
        db.session.commit()
        flash('Process routing updated successfully', 'success')
        return redirect(url_for('production.edit_bom', id=process.bom_id))
    
    return render_template('production/bom_process_form.html', form=form, bom=process.bom, title='Edit Process Routing')

@production_bp.route('/bom/process/delete/<int:id>')
@login_required
def delete_bom_process(id):
    """Delete BOM process"""
    process = BOMProcess.query.get_or_404(id)
    bom_id = process.bom_id
    
    try:
        db.session.delete(process)
        db.session.commit()
        flash('Process routing deleted successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting process: {str(e)}', 'error')
    
    return redirect(url_for('production.edit_bom', id=bom_id))

# Enhanced BOM Analysis Routes
@production_bp.route('/bom/<int:id>/analysis')
@login_required
def bom_analysis(id):
    """Show detailed BOM analysis including material availability and cost breakdown"""
    bom = BOM.query.get_or_404(id)
    
    # Get material availability analysis
    shortages = bom.get_material_availability()
    
    # Calculate production capacity based on current inventory
    max_production_qty = float('inf')
    for bom_item in bom.items:
        material = bom_item.material or bom_item.item
        if material:
            available_qty = material.total_stock if hasattr(material, 'total_stock') else (material.current_stock or 0)
            effective_qty_needed = bom_item.effective_quantity
            if effective_qty_needed > 0:
                possible_production = available_qty / effective_qty_needed
                max_production_qty = min(max_production_qty, possible_production)
    
    if max_production_qty == float('inf'):
        max_production_qty = 0
    
    # Get process information
    processes = BOMProcess.query.filter_by(bom_id=bom.id).order_by(BOMProcess.step_number).all()
    
    # Calculate total process costs
    total_process_cost = sum(p.labor_cost_per_unit for p in processes)
    
    return render_template('production/bom_analysis.html', 
                         bom=bom, 
                         shortages=shortages,
                         max_production_qty=int(max_production_qty),
                         processes=processes,
                         total_process_cost=total_process_cost)

@production_bp.route('/api/bom/<int:id>/production_check/<int:qty>')
@login_required
def check_bom_production_capacity(id, qty):
    """API endpoint to check if BOM can produce specified quantity"""
    bom = BOM.query.get_or_404(id)
    can_produce, shortages = bom.can_produce_quantity(qty)
    
    return jsonify({
        'can_produce': can_produce,
        'shortages': [
            {
                'material_name': s['material'].name,
                'material_code': s['material'].code,
                'required': s['required'],
                'available': s['available'],
                'shortage': s['shortage']
            }
            for s in shortages
        ]
    })

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

# Process Integration Routes
@production_bp.route('/bom/<int:id>/sync_from_processes', methods=['POST'])
@login_required
def sync_bom_from_processes(id):
    """Intelligent synchronization: Update BOM labor costs and scrap from process workflows"""
    try:
        success = ProcessIntegrationService.sync_bom_from_processes(id)
        if success:
            bom = BOM.query.get(id)
            flash(f'Successfully synchronized BOM from process workflow. Labor Cost: ₹{bom.calculated_labor_cost_per_unit:.2f}, Scrap Rate: {bom.calculated_scrap_percent:.2f}%', 'success')
        else:
            flash('No processes found or synchronization not needed', 'info')
    except Exception as e:
        flash(f'Error during synchronization: {str(e)}', 'error')
    
    return redirect(url_for('production.edit_bom', id=id))

@production_bp.route('/api/bom/<int:id>/process_summary')
@login_required
def get_process_summary(id):
    """API endpoint for process-driven BOM calculations"""
    bom = BOM.query.get_or_404(id)
    summary = ProcessIntegrationService.get_process_summary(bom)
    return jsonify(summary)

@production_bp.route('/bom/<int:id>/process_report')
@login_required
def process_integration_report(id):
    """Generate detailed process workflow integration report"""
    bom = BOM.query.get_or_404(id)
    report = ProcessIntegrationService.generate_process_workflow_report(bom)
    
    return render_template('production/process_report.html', 
                         bom=bom, 
                         report=report,
                         title=f'Process Integration Report - {bom.bom_code}')
