from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from app import db
from models import MaterialInspection, PurchaseOrder, JobWork, Item, User, PurchaseOrderItem, DailyJobWorkEntry
from models_uom import ItemUOMConversion, UnitOfMeasure
from forms import MaterialInspectionForm
from datetime import datetime
from utils import generate_next_number

material_inspection = Blueprint('material_inspection', __name__)

@material_inspection.route('/dashboard')
@login_required
def dashboard():
    """Material Inspection Dashboard"""
    # Get all POs that need inspection - exclude cancelled POs and completed inspections
    # Include POs with partial status if inspection is not completed (for partial deliveries that need inspection)
    all_pos_with_items = PurchaseOrder.query.filter(
        PurchaseOrder.status != 'cancelled',
        PurchaseOrder.inspection_required == True,
        PurchaseOrder.inspection_status.in_(['pending', 'in_progress', 'failed'])
    ).all()
    
    # Filter to only show POs that have items and could need inspection
    pending_po_inspections = [po for po in all_pos_with_items if po.items]
    
    # For job works, only show outsourced ones for traditional inspection
    # In-house job works use daily entries for inspection
    pending_job_inspections = JobWork.query.filter_by(
        inspection_status='pending',
        work_type='outsourced'  # Only outsourced job works need traditional inspection
    ).all()
    
    # Get in-house job works with daily entries that need inspection
    pending_daily_entries = DailyJobWorkEntry.query.join(JobWork).filter(
        JobWork.work_type == 'in_house',
        DailyJobWorkEntry.inspection_status == 'pending'
    ).order_by(DailyJobWorkEntry.work_date.desc()).limit(10).all()
    
    # Get recent inspections
    recent_inspections = MaterialInspection.query.order_by(
        MaterialInspection.inspection_date.desc()
    ).limit(10).all()
    
    # Calculate statistics
    total_pending = len(pending_po_inspections) + len(pending_job_inspections) + len(pending_daily_entries)
    
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
                         pending_daily_entries=pending_daily_entries,
                         recent_inspections=recent_inspections,
                         stats=stats)

@material_inspection.route('/inspect/daily-entry/<int:entry_id>')
@login_required
def inspect_daily_entry(entry_id):
    """Inspect a Daily Job Work Entry for in-house work"""
    daily_entry = DailyJobWorkEntry.query.get_or_404(entry_id)
    
    # Verify this is from an in-house job work
    if daily_entry.job_work.work_type != 'in_house':
        flash('This daily entry is not from an in-house job work.', 'error')
        return redirect(url_for('material_inspection.dashboard'))
    
    # Check if already inspected
    if daily_entry.inspection_status == 'passed':
        flash('This daily entry has already been inspected and passed.', 'info')
        return redirect(url_for('material_inspection.dashboard'))
    
    return render_template('material_inspection/daily_entry_inspection.html',
                         title=f'Inspect Daily Entry - {daily_entry.job_work.job_number}',
                         daily_entry=daily_entry)

@material_inspection.route('/approve-daily-entry/<int:entry_id>', methods=['POST'])
@login_required
def approve_daily_entry(entry_id):
    """Approve a Daily Job Work Entry inspection"""
    daily_entry = DailyJobWorkEntry.query.get_or_404(entry_id)
    
    # Get inspection notes and material classification from form
    inspection_notes = request.form.get('inspection_notes', '')
    material_classification = request.form.get('material_classification', 'production_use')
    
    # Update inspection status
    daily_entry.inspection_status = 'passed'
    daily_entry.inspection_notes = inspection_notes
    daily_entry.material_classification = material_classification
    daily_entry.inspected_by = current_user.id
    daily_entry.inspected_at = datetime.utcnow()
    
    db.session.commit()
    
    flash(f'Daily entry for {daily_entry.worker_name} on {daily_entry.work_date.strftime("%d/%m/%Y")} has been approved with classification: {material_classification.replace("_", " ").title()}!', 'success')
    return redirect(url_for('material_inspection.dashboard'))

@material_inspection.route('/reject-daily-entry/<int:entry_id>', methods=['POST'])
@login_required
def reject_daily_entry(entry_id):
    """Reject a Daily Job Work Entry inspection"""
    daily_entry = DailyJobWorkEntry.query.get_or_404(entry_id)
    
    # Get inspection notes and material classification from form
    inspection_notes = request.form.get('inspection_notes', '')
    material_classification = request.form.get('material_classification', 'production_use')
    
    # Update inspection status
    daily_entry.inspection_status = 'failed'
    daily_entry.inspection_notes = inspection_notes
    daily_entry.material_classification = material_classification
    daily_entry.inspected_by = current_user.id
    daily_entry.inspected_at = datetime.utcnow()
    
    db.session.commit()
    
    flash(f'Daily entry for {daily_entry.worker_name} has been rejected. Classification: {material_classification.replace("_", " ").title()}. Inspection notes: {inspection_notes}', 'warning')
    return redirect(url_for('material_inspection.dashboard'))

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
    
    # Enhance PO items with correct purchase unit information from UOM conversions
    for po_item in po.items:
        # Get UOM conversion for this item
        uom_conversion = ItemUOMConversion.query.filter_by(item_id=po_item.item.id).first()
        if uom_conversion:
            # Get purchase unit symbol
            purchase_unit = UnitOfMeasure.query.get(uom_conversion.purchase_unit_id)
            if purchase_unit:
                po_item.purchase_unit = purchase_unit.symbol
            else:
                po_item.purchase_unit = po_item.item.unit_of_measure
        else:
            po_item.purchase_unit = po_item.item.unit_of_measure
    
    return render_template('material_inspection/po_inspection.html',
                         title=f'Inspect Purchase Order {po.po_number}',
                         po=po)

@material_inspection.route('/inspect/job/<int:job_id>')
@login_required
def inspect_job_work(job_id):
    """Start inspection for a Job Work (outsourced only)"""
    job_work = JobWork.query.get_or_404(job_id)
    
    # Check if this is an in-house job work
    if job_work.work_type == 'in_house':
        flash('In-house job works use Daily Work Entries for inspection. Please use the Daily Entry inspection workflow.', 'info')
        return redirect(url_for('material_inspection.dashboard'))
    
    # Continue with traditional inspection for outsourced job works
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
    # Check if po_id or job_id is provided for pre-population
    po_id = request.args.get('po_id', type=int)
    job_id = request.args.get('job_id', type=int)
    
    # Debug logging
    print(f"DEBUG: po_id = {po_id}, job_id = {job_id}, method = {request.method}")
    
    # Create form instance
    form = MaterialInspectionForm()
    
    # Pre-populate form if po_id or job_id provided
    if request.method == 'GET':
        if po_id:
            print(f"DEBUG: Setting PO ID to {po_id}")
            # Get the specific PO to verify its status
            target_po = PurchaseOrder.query.get(po_id)
            if target_po:
                print(f"DEBUG: Target PO found: {target_po.po_number}, status: {target_po.status}, inspection_status: {target_po.inspection_status}")
                # Add the specific PO to choices if it's not already there
                current_choices = list(form.purchase_order_id.choices)
                if po_id not in [choice[0] for choice in current_choices]:
                    current_choices.append((target_po.id, f"{target_po.po_number} - {target_po.supplier.name}"))
                    form.purchase_order_id.choices = current_choices
                    print(f"DEBUG: Added PO to choices")
            
            # Verify the PO exists in the choices
            po_choices = form.purchase_order_id.choices
            print(f"DEBUG: Available PO choices: {po_choices}")
            form.purchase_order_id.data = po_id
            form.job_work_id.data = 0  # Clear job work selection
            print(f"DEBUG: Form PO data set to: {form.purchase_order_id.data}")
        elif job_id:
            print(f"DEBUG: Setting Job ID to {job_id}")
            # Get the specific Job Work to verify its status
            target_job = JobWork.query.get(job_id)
            if target_job:
                print(f"DEBUG: Target Job found: {target_job.job_number}, inspection_status: {target_job.inspection_status}")
                # Add the specific Job Work to choices if it's not already there
                current_choices = list(form.job_work_id.choices)
                if job_id not in [choice[0] for choice in current_choices]:
                    current_choices.append((target_job.id, f"{target_job.job_number} - {target_job.customer_name}"))
                    form.job_work_id.choices = current_choices
                    print(f"DEBUG: Added Job Work to choices")
            
            form.job_work_id.data = job_id
            form.purchase_order_id.data = 0  # Clear purchase order selection
    
    if form.validate_on_submit():
        # Generate inspection number
        inspection_number = generate_next_number('INSPECT', 'material_inspections', 'inspection_number')
        
        # Calculate acceptance rate
        passed_qty = form.passed_quantity.data or 0.0
        inspected_qty = form.inspected_quantity.data or 0.0
        acceptance_rate = (passed_qty / inspected_qty * 100) if inspected_qty > 0 else 0
        
        inspection = MaterialInspection(
            inspection_number=inspection_number,
            purchase_order_id=form.purchase_order_id.data if form.purchase_order_id.data else None,
            job_work_id=form.job_work_id.data if form.job_work_id.data else None,
            item_id=form.item_id.data,
            material_classification=form.material_classification.data,
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
            if po:
                po.inspection_status = 'completed'
                po.inspected_at = datetime.utcnow()
            
                # Automatically update PO status based on completion
                if po.status in ['draft', 'open']:
                    # Check if all materials are inspected and received
                    total_ordered = sum((item.qty or 0.0) for item in po.items if item.qty)
                    passed_quantity = form.passed_quantity.data or 0.0
                    total_received = sum((inspection.passed_quantity or 0.0) for inspection in po.material_inspections if inspection.passed_quantity) + passed_quantity
                    
                    if total_received >= total_ordered:
                        po.status = 'closed'  # All materials received
                    elif total_received > 0:
                        po.status = 'partial'  # Some materials received
                    # else status remains 'open' if nothing received yet
            
                # Update inventory with passed quantity and material classification
                item = Item.query.get(form.item_id.data)
                if item:
                    if item.current_stock is None:
                        item.current_stock = 0.0
                    passed_quantity = form.passed_quantity.data or 0.0
                    item.current_stock += passed_quantity
                    # Update the item's material classification based on inspection
                    item.material_classification = form.material_classification.data
                
        elif form.job_work_id.data:
            job_work = JobWork.query.get(form.job_work_id.data)
            if job_work:
                job_work.inspection_status = 'completed'
                job_work.inspected_at = datetime.utcnow()
            
                # Update inventory with passed quantity and material classification
                item = Item.query.get(job_work.item_id)
                if item:
                    if item.current_stock is None:
                        item.current_stock = 0.0
                    passed_quantity = form.passed_quantity.data or 0.0
                    item.current_stock += passed_quantity
                    # Update the item's material classification based on inspection
                    item.material_classification = form.material_classification.data
        
        db.session.commit()
        flash(f'Material inspection {inspection_number} logged successfully!', 'success')
        return redirect(url_for('material_inspection.dashboard'))
    
    # Set appropriate title based on context
    if job_id:
        target_job = JobWork.query.get(job_id)
        if target_job:
            title = f'Log Inspection - Job Work {target_job.job_number}'
        else:
            title = 'Log Job Work Inspection'
    elif po_id:
        target_po = PurchaseOrder.query.get(po_id)
        if target_po:
            title = f'Log Inspection - Purchase Order {target_po.po_number}'
        else:
            title = 'Log Purchase Order Inspection'
    else:
        title = 'Log Material Inspection'
    
    return render_template('material_inspection/log_form.html',
                         title=title,
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
            # Use the UOM from the purchase order item directly (already converted during PO creation)
            unit_display = po_item.uom if po_item.uom else po_item.item.unit_of_measure
                
            items.append({
                'item_id': po_item.item.id,
                'item_code': po_item.item.code,
                'item_name': po_item.item.name,
                'quantity': float(po_item.qty if po_item.qty else po_item.quantity_ordered),
                'unit': unit_display
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