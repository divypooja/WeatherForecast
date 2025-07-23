from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from app import db
from models import MaterialInspection, PurchaseOrder, JobWork, Item, User
from forms import MaterialInspectionForm
from datetime import datetime
from utils import generate_next_number

material_inspection = Blueprint('material_inspection', __name__)

@material_inspection.route('/dashboard')
@login_required
def dashboard():
    """Material Inspection Dashboard"""
    # Get pending inspections
    pending_po_inspections = PurchaseOrder.query.filter_by(
        inspection_status='pending'
    ).all()
    
    pending_job_inspections = JobWork.query.filter_by(
        inspection_status='pending'
    ).all()
    
    # Get recent inspections
    recent_inspections = MaterialInspection.query.order_by(
        MaterialInspection.inspection_date.desc()
    ).limit(10).all()
    
    # Calculate statistics
    total_pending = len(pending_po_inspections) + len(pending_job_inspections)
    
    # Get inspections this month
    this_month = datetime.now().replace(day=1)
    this_month_inspections = MaterialInspection.query.filter(
        MaterialInspection.inspection_date >= this_month
    ).all()
    
    # Calculate damage rate
    total_inspected = sum(i.inspected_quantity for i in this_month_inspections)
    total_damaged = sum(i.damaged_quantity for i in this_month_inspections)
    damage_rate = (total_damaged / total_inspected * 100) if total_inspected > 0 else 0
    
    stats = {
        'pending_inspections': total_pending,
        'this_month_inspections': len(this_month_inspections),
        'damage_rate': round(damage_rate, 1),
        'acceptance_rate': round(100 - damage_rate, 1)
    }
    
    return render_template('material_inspection/dashboard.html',
                         title='Material Inspection Dashboard',
                         pending_po_inspections=pending_po_inspections,
                         pending_job_inspections=pending_job_inspections,
                         recent_inspections=recent_inspections,
                         stats=stats)

@material_inspection.route('/inspect/po/<int:po_id>')
@login_required
def inspect_purchase_order(po_id):
    """Start inspection for a Purchase Order"""
    po = PurchaseOrder.query.get_or_404(po_id)
    
    # Check if inspection is required
    if not po.inspection_required:
        flash('This Purchase Order does not require inspection.', 'info')
        return redirect(url_for('material_inspection.dashboard'))
    
    # Check if already inspected
    if po.inspection_status == 'completed':
        flash('This Purchase Order has already been inspected.', 'info')
        return redirect(url_for('material_inspection.dashboard'))
    
    # Update inspection status to in progress
    po.inspection_status = 'in_progress'
    po.inspected_by = current_user.id
    db.session.commit()
    
    return render_template('material_inspection/po_inspection.html',
                         title=f'Inspect Purchase Order {po.po_number}',
                         po=po)

@material_inspection.route('/inspect/job/<int:job_id>')
@login_required
def inspect_job_work(job_id):
    """Start inspection for a Job Work"""
    job_work = JobWork.query.get_or_404(job_id)
    
    # Check if inspection is required
    if not job_work.inspection_required:
        flash('This Job Work does not require inspection.', 'info')
        return redirect(url_for('material_inspection.dashboard'))
    
    # Check if already inspected
    if job_work.inspection_status == 'completed':
        flash('This Job Work has already been inspected.', 'info')
        return redirect(url_for('material_inspection.dashboard'))
    
    # Update inspection status to in progress
    job_work.inspection_status = 'in_progress'
    job_work.inspected_by = current_user.id
    db.session.commit()
    
    return render_template('material_inspection/job_inspection.html',
                         title=f'Inspect Job Work {job_work.job_number}',
                         job_work=job_work)

@material_inspection.route('/log', methods=['GET', 'POST'])
@login_required
def log_inspection():
    """Log material inspection results"""
    form = MaterialInspectionForm()
    
    if form.validate_on_submit():
        # Generate inspection number
        inspection_number = generate_next_number('INSPECT', 'material_inspections', 'inspection_number')
        
        # Calculate acceptance rate
        acceptance_rate = (form.passed_quantity.data / form.inspected_quantity.data * 100) if form.inspected_quantity.data > 0 else 0
        
        inspection = MaterialInspection(
            inspection_number=inspection_number,
            purchase_order_id=form.purchase_order_id.data if form.purchase_order_id.data else None,
            job_work_id=form.job_work_id.data if form.job_work_id.data else None,
            item_id=form.item_id.data,
            received_quantity=form.received_quantity.data,
            inspected_quantity=form.inspected_quantity.data,
            passed_quantity=form.passed_quantity.data,
            damaged_quantity=form.damaged_quantity.data,
            rejected_quantity=form.rejected_quantity.data,
            acceptance_rate=acceptance_rate,
            damage_types=form.damage_types.data,
            rejection_reasons=form.rejection_reasons.data,
            inspection_notes=form.inspection_notes.data,
            inspector_id=current_user.id
        )
        
        db.session.add(inspection)
        
        # Update related PO or Job Work
        if form.purchase_order_id.data:
            po = PurchaseOrder.query.get(form.purchase_order_id.data)
            po.inspection_status = 'completed'
            po.inspected_at = datetime.utcnow()
            
            # Update inventory only with passed quantity for the specific item
            item = Item.query.get(form.item_id.data)
            item.current_stock += form.passed_quantity.data
                
        elif form.job_work_id.data:
            job_work = JobWork.query.get(form.job_work_id.data)
            job_work.inspection_status = 'completed'
            job_work.inspected_at = datetime.utcnow()
            
            # Update inventory only with passed quantity
            item = Item.query.get(job_work.item_id)
            item.current_stock += form.passed_quantity.data
        
        db.session.commit()
        flash(f'Material inspection {inspection_number} logged successfully!', 'success')
        return redirect(url_for('material_inspection.dashboard'))
    
    return render_template('material_inspection/log_form.html',
                         title='Log Material Inspection',
                         form=form)

@material_inspection.route('/list')
@login_required
def list_inspections():
    """List all material inspections"""
    inspections = MaterialInspection.query.order_by(
        MaterialInspection.inspection_date.desc()
    ).all()
    
    return render_template('material_inspection/list.html',
                         title='Material Inspections',
                         inspections=inspections)

@material_inspection.route('/view/<int:inspection_id>')
@login_required
def view_inspection(inspection_id):
    """View inspection details"""
    inspection = MaterialInspection.query.get_or_404(inspection_id)
    
    return render_template('material_inspection/detail.html',
                         title=f'Inspection {inspection.inspection_number}',
                         inspection=inspection)