from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from app import db
from models import MaterialInspection, PurchaseOrder, JobWork, Item, User, PurchaseOrderItem
from forms import MaterialInspectionForm
from datetime import datetime
from utils import generate_next_number

material_inspection = Blueprint('material_inspection', __name__)

@material_inspection.route('/dashboard')
@login_required
def dashboard():
    """Material Inspection Dashboard"""
    # Get all POs that could need inspection - exclude only cancelled and closed without inspection needs  
    all_pos_with_items = PurchaseOrder.query.filter(
        ~PurchaseOrder.status.in_(['cancelled']),
        ~PurchaseOrder.inspection_status.in_(['completed'])
    ).all()
    
    # Filter to only show POs that have items and could need inspection
    pending_po_inspections = [po for po in all_pos_with_items if po.items]
    
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
    
    # Check if po_id or job_id is provided for pre-population
    po_id = request.args.get('po_id', type=int)
    job_id = request.args.get('job_id', type=int)
    
    # Pre-populate form if po_id or job_id provided
    if request.method == 'GET':
        if po_id:
            form.purchase_order_id.data = po_id
            form.job_work_id.data = 0  # Clear job work selection
        elif job_id:
            form.job_work_id.data = job_id
            form.purchase_order_id.data = 0  # Clear purchase order selection
    
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
            damaged_quantity=0.0,  # Not used anymore, only rejected_quantity matters
            rejected_quantity=form.rejected_quantity.data,
            acceptance_rate=acceptance_rate,
            damage_types='',  # Not used anymore
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
            
            # Automatically update PO status based on completion
            if po.status in ['draft', 'open']:
                # Check if all materials are inspected and received
                total_ordered = sum(item.qty for item in po.items)
                total_received = sum(inspection.passed_quantity for inspection in po.material_inspections) + form.passed_quantity.data
                
                if total_received >= total_ordered:
                    po.status = 'closed'  # All materials received
                elif total_received > 0:
                    po.status = 'partial'  # Some materials received
                # else status remains 'open' if nothing received yet
            
            # Update inventory only with passed quantity for the specific item
            item = Item.query.get(form.item_id.data)
            if item.current_stock is None:
                item.current_stock = 0.0
            item.current_stock += form.passed_quantity.data
                
        elif form.job_work_id.data:
            job_work = JobWork.query.get(form.job_work_id.data)
            job_work.inspection_status = 'completed'
            job_work.inspected_at = datetime.utcnow()
            
            # Update inventory only with passed quantity
            item = Item.query.get(job_work.item_id)
            if item.current_stock is None:
                item.current_stock = 0.0
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

@material_inspection.route('/api/po_items/<int:po_id>')
@login_required
def get_po_items(po_id):
    """Get items from a Purchase Order for inspection"""
    try:
        po = PurchaseOrder.query.get_or_404(po_id)
        items = []
        
        for po_item in po.items:
            items.append({
                'item_id': po_item.item.id,
                'item_code': po_item.item.code,
                'item_name': po_item.item.name,
                'quantity': float(po_item.quantity_ordered),
                'unit': po_item.item.unit_of_measure
            })
        
        return jsonify({
            'success': True,
            'items': items,
            'po_number': po.po_number
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@material_inspection.route('/api/job_items/<int:job_id>')
@login_required
def get_job_items(job_id):
    """Get items from a Job Work for inspection"""
    try:
        job = JobWork.query.get_or_404(job_id)
        items = []
        
        # JobWork has a single item, not multiple items like PurchaseOrder
        if job.item:
            items.append({
                'item_id': job.item.id,
                'item_code': job.item.code,
                'item_name': job.item.name,
                'quantity': float(job.quantity_sent),
                'unit': job.item.unit_of_measure
            })
        
        return jsonify({
            'success': True,
            'items': items,
            'job_number': job.job_number
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })