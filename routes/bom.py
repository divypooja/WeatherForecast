from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models import Item, Supplier, db
from models_bom import BillOfMaterials, BOMComponent, BOMProcess, BOMVersion, BOMCostHistory
from models_uom import UnitOfMeasure
from models_department import Department
from forms_bom import BOMForm, BOMComponentForm, BOMProcessForm, BOMSearchForm, BOMCostAnalysisForm
from sqlalchemy import or_, and_
from datetime import datetime
import json

bom_bp = Blueprint('bom', __name__)

@bom_bp.route('/dashboard')
@login_required
def dashboard():
    """BOM Dashboard with overview and metrics"""
    # Get summary statistics
    total_boms = BillOfMaterials.query.count()
    active_boms = BillOfMaterials.query.filter_by(status='active').count()
    draft_boms = BillOfMaterials.query.filter_by(status='draft').count()
    
    # Recent BOMs
    recent_boms = BillOfMaterials.query.order_by(BillOfMaterials.updated_at.desc()).limit(10).all()
    
    # BOMs with material shortages
    shortage_boms = []
    for bom in BillOfMaterials.query.filter_by(status='active').limit(20).all():
        shortages = bom.check_material_availability()
        if shortages:
            shortage_boms.append({
                'bom': bom,
                'shortages': shortages,
                'shortage_count': len(shortages)
            })
    
    # Cost analysis - highest cost BOMs
    high_cost_boms = BillOfMaterials.query.filter(
        BillOfMaterials.estimated_cost > 0
    ).order_by(BillOfMaterials.estimated_cost.desc()).limit(10).all()
    
    stats = {
        'total_boms': total_boms,
        'active_boms': active_boms,
        'draft_boms': draft_boms,
        'shortage_boms_count': len(shortage_boms)
    }
    
    return render_template('bom/dashboard.html',
                         stats=stats,
                         recent_boms=recent_boms,
                         shortage_boms=shortage_boms,
                         high_cost_boms=high_cost_boms)

@bom_bp.route('/list')
@login_required
def bom_list():
    """List all BOMs with search and filter"""
    form = BOMSearchForm()
    page = request.args.get('page', 1, type=int)
    
    # Build query
    query = BillOfMaterials.query
    
    # Apply filters
    if form.search_term.data:
        search_term = f"%{form.search_term.data}%"
        query = query.join(Item).filter(
            or_(
                BillOfMaterials.bom_code.ilike(search_term),
                Item.name.ilike(search_term)
            )
        )
    
    if form.product_id.data and form.product_id.data != 0:
        query = query.filter(BillOfMaterials.product_id == form.product_id.data)
    
    if form.status.data:
        query = query.filter(BillOfMaterials.status == form.status.data)
    
    # Paginate results
    boms = query.order_by(BillOfMaterials.updated_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('bom/list.html', boms=boms, form=form)

@bom_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_bom():
    """Create new BOM"""
    form = BOMForm()
    
    if form.validate_on_submit():
        try:
            # Create BOM
            bom = BillOfMaterials(
                bom_code=form.bom_code.data,
                product_id=form.product_id.data,
                output_quantity=form.output_quantity.data,
                output_uom_id=form.output_uom_id.data,
                version=form.version.data,
                status=form.status.data,
                description=form.description.data,
                remarks=form.remarks.data,
                estimated_scrap_percent=form.estimated_scrap_percent.data,
                created_by=current_user.id
            )
            
            db.session.add(bom)
            db.session.commit()
            
            flash(f'BOM {bom.bom_code} created successfully!', 'success')
            return redirect(url_for('bom.edit_bom', id=bom.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating BOM: {str(e)}', 'danger')
    
    return render_template('bom/create.html', form=form)

@bom_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_bom(id):
    """Edit existing BOM"""
    bom = BillOfMaterials.query.get_or_404(id)
    form = BOMForm(obj=bom)
    
    if form.validate_on_submit():
        try:
            # Update BOM
            form.populate_obj(bom)
            bom.updated_at = datetime.utcnow()
            
            db.session.commit()
            flash(f'BOM {bom.bom_code} updated successfully!', 'success')
            return redirect(url_for('bom.view_bom', id=bom.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating BOM: {str(e)}', 'danger')
    
    return render_template('bom/edit.html', form=form, bom=bom)

@bom_bp.route('/view/<int:id>')
@login_required
def view_bom(id):
    """View BOM details"""
    bom = BillOfMaterials.query.get_or_404(id)
    
    # Check material availability
    material_shortages = bom.check_material_availability()
    
    # Calculate production capacity
    max_producible = bom.can_produce_quantity()
    
    # Get cost history
    cost_history = BOMCostHistory.query.filter_by(bom_id=id).order_by(
        BOMCostHistory.calculation_date.desc()
    ).limit(10).all()
    
    return render_template('bom/view.html',
                         bom=bom,
                         material_shortages=material_shortages,
                         max_producible=max_producible,
                         cost_history=cost_history)

@bom_bp.route('/components/<int:bom_id>')
@login_required
def manage_components(bom_id):
    """Manage BOM components"""
    bom = BillOfMaterials.query.get_or_404(bom_id)
    components = BOMComponent.query.filter_by(bom_id=bom_id).order_by(
        BOMComponent.process_step, BOMComponent.id
    ).all()
    
    return render_template('bom/components.html', bom=bom, components=components)

@bom_bp.route('/add_component/<int:bom_id>', methods=['GET', 'POST'])
@login_required
def add_component(bom_id):
    """Add component to BOM"""
    bom = BillOfMaterials.query.get_or_404(bom_id)
    form = BOMComponentForm()
    
    if form.validate_on_submit():
        try:
            component = BOMComponent(
                bom_id=bom_id,
                material_id=form.material_id.data,
                qty_required=form.qty_required.data,
                uom_id=form.uom_id.data,
                scrap_percent=form.scrap_percent.data,
                process_step=form.process_step.data,
                process_name=form.process_name.data,
                rate_per_unit=form.rate_per_unit.data,
                default_supplier_id=form.default_supplier_id.data if form.default_supplier_id.data != 0 else None,
                is_critical=form.is_critical.data,
                remarks=form.remarks.data
            )
            
            db.session.add(component)
            db.session.commit()
            
            flash('Component added successfully!', 'success')
            return redirect(url_for('bom.manage_components', bom_id=bom_id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding component: {str(e)}', 'danger')
    
    return render_template('bom/add_component.html', form=form, bom=bom)

@bom_bp.route('/edit_component/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_component(id):
    """Edit BOM component"""
    component = BOMComponent.query.get_or_404(id)
    form = BOMComponentForm(obj=component)
    
    if form.validate_on_submit():
        try:
            form.populate_obj(component)
            if form.default_supplier_id.data == 0:
                component.default_supplier_id = None
                
            db.session.commit()
            flash('Component updated successfully!', 'success')
            return redirect(url_for('bom.manage_components', bom_id=component.bom_id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating component: {str(e)}', 'danger')
    
    return render_template('bom/edit_component.html', form=form, component=component)

@bom_bp.route('/delete_component/<int:id>')
@login_required
def delete_component(id):
    """Delete BOM component"""
    component = BOMComponent.query.get_or_404(id)
    bom_id = component.bom_id
    
    try:
        db.session.delete(component)
        db.session.commit()
        flash('Component deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting component: {str(e)}', 'danger')
    
    return redirect(url_for('bom.manage_components', bom_id=bom_id))

@bom_bp.route('/cost_analysis/<int:id>')
@login_required
def cost_analysis(id):
    """BOM cost analysis"""
    bom = BillOfMaterials.query.get_or_404(id)
    form = BOMCostAnalysisForm()
    
    # Calculate current costs
    material_cost = bom.total_material_cost
    process_cost = bom.total_process_cost
    total_cost = bom.total_bom_cost
    cost_per_unit = bom.cost_per_unit
    
    # Component cost breakdown
    component_costs = []
    for component in bom.components:
        component_costs.append({
            'component': component,
            'base_cost': component.qty_required * (component.rate_per_unit or 0),
            'scrap_cost': (component.qty_required_with_scrap - component.qty_required) * (component.rate_per_unit or 0),
            'total_cost': component.total_cost
        })
    
    # Process cost breakdown
    process_costs = []
    for process in bom.processes:
        process_costs.append({
            'process': process,
            'unit_cost': process.cost_per_unit,
            'total_cost': process.cost_per_unit * bom.output_quantity
        })
    
    return render_template('bom/cost_analysis.html',
                         bom=bom,
                         form=form,
                         material_cost=material_cost,
                         process_cost=process_cost,
                         total_cost=total_cost,
                         cost_per_unit=cost_per_unit,
                         component_costs=component_costs,
                         process_costs=process_costs)

@bom_bp.route('/api/calculate_cost/<int:id>')
@login_required
def api_calculate_cost(id):
    """API endpoint to recalculate BOM cost"""
    bom = BillOfMaterials.query.get_or_404(id)
    
    try:
        # Update estimated cost
        bom.estimated_cost = bom.total_bom_cost
        
        # Save cost history
        cost_history = BOMCostHistory(
            bom_id=id,
            material_cost=bom.total_material_cost,
            process_cost=bom.total_process_cost,
            total_cost=bom.total_bom_cost,
            cost_per_unit=bom.cost_per_unit,
            calculated_by=current_user.id
        )
        
        db.session.add(cost_history)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'material_cost': bom.total_material_cost,
            'process_cost': bom.total_process_cost,
            'total_cost': bom.total_bom_cost,
            'cost_per_unit': bom.cost_per_unit
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400

@bom_bp.route('/api/check_availability/<int:id>')
@login_required
def api_check_availability(id):
    """API endpoint to check material availability"""
    bom = BillOfMaterials.query.get_or_404(id)
    
    shortages = bom.check_material_availability()
    max_producible = bom.can_produce_quantity()
    
    return jsonify({
        'shortages': [{
            'material_name': shortage['material'].name,
            'material_code': shortage['material'].item_code,
            'required': shortage['required'],
            'available': shortage['available'],
            'shortage': shortage['shortage']
        } for shortage in shortages],
        'max_producible': max_producible,
        'can_produce': len(shortages) == 0
    })

@bom_bp.route('/copy/<int:id>')
@login_required
def copy_bom(id):
    """Copy existing BOM"""
    original_bom = BillOfMaterials.query.get_or_404(id)
    
    try:
        # Create new BOM
        new_bom = BillOfMaterials(
            bom_code=f"{original_bom.bom_code}_COPY",
            product_id=original_bom.product_id,
            output_quantity=original_bom.output_quantity,
            output_uom_id=original_bom.output_uom_id,
            version="1.0",
            status="draft",
            description=f"Copy of {original_bom.description}",
            remarks=original_bom.remarks,
            estimated_scrap_percent=original_bom.estimated_scrap_percent,
            created_by=current_user.id
        )
        
        db.session.add(new_bom)
        db.session.flush()  # Get the new BOM ID
        
        # Copy components
        for component in original_bom.components:
            new_component = BOMComponent(
                bom_id=new_bom.id,
                material_id=component.material_id,
                qty_required=component.qty_required,
                uom_id=component.uom_id,
                scrap_percent=component.scrap_percent,
                process_step=component.process_step,
                process_name=component.process_name,
                rate_per_unit=component.rate_per_unit,
                default_supplier_id=component.default_supplier_id,
                is_critical=component.is_critical,
                remarks=component.remarks
            )
            db.session.add(new_component)
        
        # Copy processes
        for process in original_bom.processes:
            new_process = BOMProcess(
                bom_id=new_bom.id,
                step_number=process.step_number,
                process_name=process.process_name,
                description=process.description,
                department_id=process.department_id,
                estimated_time_minutes=process.estimated_time_minutes,
                cost_per_unit=process.cost_per_unit,
                default_supplier_id=process.default_supplier_id,
                is_outsourced=process.is_outsourced,
                is_critical_path=process.is_critical_path
            )
            db.session.add(new_process)
        
        db.session.commit()
        
        flash(f'BOM copied successfully as {new_bom.bom_code}!', 'success')
        return redirect(url_for('bom.edit_bom', id=new_bom.id))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error copying BOM: {str(e)}', 'danger')
        return redirect(url_for('bom.view_bom', id=id))