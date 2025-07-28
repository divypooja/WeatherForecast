from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from app import db
from models import JobWork, Item, User, PurchaseOrder, PurchaseOrderItem, JobWorkProcess
from models_grn import GRN, GRNLineItem
from forms_grn import GRNForm, GRNLineItemForm, QuickReceiveForm, QuickReceivePOForm, GRNSearchForm, MultiProcessQuickReceiveForm
from datetime import datetime, date
from utils import generate_next_number
from sqlalchemy import func, and_, or_


def update_po_status_based_on_grn(purchase_order_id):
    """Automatically update Purchase Order status based on GRN activities"""
    try:
        po = PurchaseOrder.query.get(purchase_order_id)
        if not po:
            return
            
        # Get all GRNs for this PO
        po_grns = GRN.query.filter_by(purchase_order_id=purchase_order_id).all()
        
        if not po_grns:
            # No GRNs yet, keep as 'sent'
            if po.status not in ['cancelled']:
                po.status = 'sent'
            return
            
        # Calculate total ordered vs received quantities
        total_ordered = {}
        total_received = {}
        
        # Sum ordered quantities by item
        for po_item in po.items:
            item_id = po_item.item_id
            total_ordered[item_id] = total_ordered.get(item_id, 0) + po_item.qty
            
        # Sum received quantities by item from all GRNs
        for grn in po_grns:
            for line_item in grn.line_items:
                item_id = line_item.item_id
                total_received[item_id] = total_received.get(item_id, 0) + line_item.quantity_received
        
        # Update quantity_received in PO items for dashboard display
        for po_item in po.items:
            item_id = po_item.item_id
            received_qty = total_received.get(item_id, 0)
            po_item.quantity_received = received_qty
                
        # Determine new status
        all_items_fully_received = True
        any_items_partially_received = False
        
        for item_id, ordered_qty in total_ordered.items():
            received_qty = total_received.get(item_id, 0)
            
            if received_qty < ordered_qty:
                all_items_fully_received = False
                
            if received_qty > 0:
                any_items_partially_received = True
                
        # Update PO status
        if all_items_fully_received:
            po.status = 'closed'
        elif any_items_partially_received:
            po.status = 'partial'
        else:
            po.status = 'sent'
            
        db.session.commit()
        
    except Exception as e:
        print(f"Error updating PO status: {str(e)}")
        db.session.rollback()

grn_bp = Blueprint('grn', __name__)

@grn_bp.route('/dashboard')
@login_required
def dashboard():
    """GRN Dashboard showing statistics and pending actions"""
    
    # Get filter parameters
    search = request.args.get('search', '').strip()
    status_filter = request.args.get('status', '').strip()
    date_from = request.args.get('date_from', '').strip()
    date_to = request.args.get('date_to', '').strip()
    
    # Build base query
    grn_query = GRN.query
    
    # Apply filters
    if search:
        grn_query = grn_query.outerjoin(JobWork).outerjoin(PurchaseOrder).filter(
            or_(
                GRN.grn_number.ilike(f'%{search}%'),
                JobWork.job_number.ilike(f'%{search}%'),
                PurchaseOrder.po_number.ilike(f'%{search}%')
            )
        )
    
    if status_filter:
        grn_query = grn_query.filter(GRN.status == status_filter)
    
    if date_from:
        try:
            from_date = datetime.strptime(date_from, '%Y-%m-%d').date()
            grn_query = grn_query.filter(GRN.received_date >= from_date)
        except ValueError:
            pass
    
    if date_to:
        try:
            to_date = datetime.strptime(date_to, '%Y-%m-%d').date()
            grn_query = grn_query.filter(GRN.received_date <= to_date)
        except ValueError:
            pass
    
    # Get filtered GRNs
    grns = grn_query.order_by(GRN.received_date.desc()).limit(50).all()
    
    # Calculate statistics
    stats = {
        'total_grns': GRN.query.count(),
        'pending_inspection': GRN.query.filter(GRN.inspection_status == 'pending').count(),
        'completed_today': GRN.query.filter(
            GRN.received_date == date.today(),
            GRN.status == 'completed'
        ).count(),
        'pending_grns': GRN.query.filter(GRN.status.in_(['draft', 'received'])).count()
    }
    
    # Get job works pending GRN creation - including unified jobs with outsourced processes
    pending_job_works = JobWork.query.filter(
        JobWork.status.in_(['sent', 'partial_received']),
        or_(
            JobWork.work_type.in_(['outsourced', 'multi_process']),
            # Include unified jobs that have outsourced processes
            and_(
                JobWork.work_type == 'unified',
                JobWork.id.in_(
                    db.session.query(JobWorkProcess.job_work_id).filter(
                        JobWorkProcess.work_type == 'outsourced'
                    ).distinct()
                )
            )
        )
    ).order_by(JobWork.sent_date.desc()).limit(20).all()
    
    # Get purchase orders pending GRN creation
    pending_purchase_orders = PurchaseOrder.query.filter(
        PurchaseOrder.status.in_(['sent', 'partial'])
    ).order_by(PurchaseOrder.order_date.desc()).limit(20).all()
    
    # Update PO quantities to ensure they're current
    for po in pending_purchase_orders:
        update_po_status_based_on_grn(po.id)
    
    # Commit any changes and refresh data
    db.session.commit()
    
    # Filter POs that actually have pending quantities
    pending_purchase_orders = [po for po in pending_purchase_orders 
                             if any(item.pending_quantity > 0 for item in po.items)]
    
    # Calculate monthly trends
    current_month = date.today().replace(day=1)
    monthly_grns = GRN.query.filter(GRN.received_date >= current_month).count()
    
    return render_template('grn/dashboard.html',
                         title='GRN Dashboard',
                         grns=grns,
                         stats=stats,
                         pending_job_works=pending_job_works,
                         pending_purchase_orders=pending_purchase_orders,
                         monthly_grns=monthly_grns)


@grn_bp.route('/create/job_work/<int:job_work_id>')
@login_required
def create_grn(job_work_id):
    """Create a new GRN for a job work"""
    job_work = JobWork.query.get_or_404(job_work_id)
    
    # Check if user can create GRN for this job work
    if job_work.status not in ['sent', 'partial_received']:
        flash('Cannot create GRN for this job work. Invalid status.', 'error')
        return redirect(url_for('jobwork.detail', id=job_work_id))
    
    form = GRNForm()
    if not form.grn_number.data:
        form.grn_number.data = GRN.generate_grn_number()
    form.job_work_id.data = job_work_id
    
    if form.validate_on_submit():
        try:
            # Create GRN
            grn = GRN(
                grn_number=form.grn_number.data,
                job_work_id=job_work_id,
                received_date=form.received_date.data,
                received_by=current_user.id,
                delivery_note=form.delivery_note.data,
                transporter_name=form.transporter_name.data,
                vehicle_number=form.vehicle_number.data,
                inspection_required=form.inspection_required.data,
                status='received',  # Automatically set to received
                remarks=form.remarks.data
            )
            
            db.session.add(grn)
            db.session.commit()
            
            flash(f'GRN {grn.grn_number} created successfully!', 'success')
            return redirect(url_for('grn.add_line_items', grn_id=grn.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating GRN: {str(e)}', 'error')
    
    return render_template('grn/create.html',
                         title='Create GRN',
                         form=form,
                         job_work=job_work)


@grn_bp.route('/create/purchase_order/<int:purchase_order_id>')
@login_required
def create_grn_for_po(purchase_order_id):
    """Create a new GRN for a purchase order"""
    purchase_order = PurchaseOrder.query.get_or_404(purchase_order_id)
    
    # Check if user can create GRN for this PO
    if purchase_order.status not in ['sent', 'partial']:
        flash('Cannot create GRN for this purchase order. Invalid status.', 'error')
        return redirect(url_for('purchase.detail', id=purchase_order_id))
    
    form = GRNForm()
    if not form.grn_number.data:
        form.grn_number.data = GRN.generate_grn_number()
    form.purchase_order_id.data = purchase_order_id
    
    if form.validate_on_submit():
        try:
            # Create GRN for PO
            grn = GRN(
                grn_number=form.grn_number.data,
                purchase_order_id=purchase_order_id,
                received_date=form.received_date.data,
                received_by=current_user.id,
                delivery_note=form.delivery_note.data,
                transporter_name=form.transporter_name.data,
                vehicle_number=form.vehicle_number.data,
                inspection_required=form.inspection_required.data,
                status='received',  # Automatically set to received
                remarks=form.remarks.data
            )
            
            db.session.add(grn)
            db.session.commit()
            
            # Update PO status automatically based on GRN creation
            update_po_status_based_on_grn(purchase_order_id)
            
            flash(f'GRN {grn.grn_number} created successfully for PO {purchase_order.po_number}!', 'success')
            return redirect(url_for('grn.add_line_items', grn_id=grn.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating GRN: {str(e)}', 'error')
    
    return render_template('grn/create.html',
                         title='Create GRN for Purchase Order',
                         form=form,
                         purchase_order=purchase_order)


@grn_bp.route('/quick_receive/<int:job_work_id>', methods=['GET', 'POST'])
@login_required
def quick_receive(job_work_id):
    """Quick receive form for simple material receipt"""
    job_work = JobWork.query.get_or_404(job_work_id)
    
    # Redirect multi-process jobs to specialized form
    if job_work.work_type in ['multi_process', 'unified']:
        return redirect(url_for('grn.quick_receive_multi_process', job_work_id=job_work_id))
    
    form = QuickReceiveForm()
    form.job_work_id.data = job_work_id
    
    if form.validate_on_submit():
        try:
            # Create GRN automatically
            grn = GRN(
                grn_number=GRN.generate_grn_number(),
                job_work_id=job_work_id,
                received_date=form.received_date.data,
                received_by=current_user.id,
                delivery_note=form.delivery_note.data,
                inspection_required=True,
                status='received',
                remarks=form.remarks.data
            )
            db.session.add(grn)
            db.session.flush()  # To get the GRN ID
            
            # Auto-calculate passed quantity
            quantity_passed = form.quantity_received.data - (form.quantity_rejected.data or 0)
            
            # Create line item
            line_item = GRNLineItem(
                grn_id=grn.id,
                item_id=job_work.item_id,
                quantity_received=form.quantity_received.data,
                quantity_passed=quantity_passed,
                quantity_rejected=form.quantity_rejected.data or 0,
                unit_of_measure=job_work.item.unit_of_measure,
                inspection_status=form.inspection_status.data,
                rejection_reason=form.rejection_reason.data,
                remarks=form.remarks.data
            )
            db.session.add(line_item)
            
            # Update job work quantities
            job_work.quantity_received = (job_work.quantity_received or 0) + form.quantity_received.data
            
            # Update job work status and add notes
            if job_work.quantity_received >= job_work.quantity_sent:
                job_work.status = 'completed'
                # Add completion note
                completion_note = f"[{datetime.utcnow().strftime('%Y-%m-%d %H:%M')}] Completed via GRN {grn.grn_number} - All {job_work.quantity_sent} {job_work.item.unit_of_measure} received"
            else:
                job_work.status = 'partial_received'
                # Add partial receipt note
                completion_note = f"[{datetime.utcnow().strftime('%Y-%m-%d %H:%M')}] Partial receipt via GRN {grn.grn_number} - {form.quantity_received.data} {job_work.item.unit_of_measure} received, {job_work.pending_quantity} {job_work.item.unit_of_measure} pending"
            
            # Add note to job work
            if job_work.notes:
                job_work.notes += f"\n{completion_note}"
            else:
                job_work.notes = completion_note
            
            # Update inventory if adding to stock
            if form.add_to_inventory.data and quantity_passed > 0:
                # Move from WIP to Finished (multi-state system)
                job_work.item.qty_finished = (job_work.item.qty_finished or 0) + quantity_passed
                # Add rejected quantity to scrap if any
                if form.quantity_rejected.data and form.quantity_rejected.data > 0:
                    job_work.item.qty_scrap = (job_work.item.qty_scrap or 0) + form.quantity_rejected.data
                grn.add_to_inventory = True  # Set the flag to True when inventory is updated
            else:
                grn.add_to_inventory = False  # Set the flag to False when inventory is not updated
            
            # Mark GRN as completed if no further inspection needed
            if form.inspection_status.data in ['passed', 'rejected']:
                grn.status = 'completed'
                grn.inspection_status = 'completed'
                grn.inspected_by = current_user.id
                grn.inspected_at = datetime.utcnow()
            
            db.session.commit()
            
            flash(f'Materials received successfully! GRN {grn.grn_number} created.', 'success')
            return redirect(url_for('jobwork.detail', id=job_work_id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error receiving materials: {str(e)}', 'error')
    
    return render_template('grn/quick_receive.html',
                         title='Quick Receive Materials',
                         form=form,
                         job_work=job_work)


@grn_bp.route('/quick_receive_multi_process/<int:job_work_id>', methods=['GET', 'POST'])
@login_required
def quick_receive_multi_process(job_work_id):
    """Specialized quick receive form for multi-process job works"""
    job_work = JobWork.query.get_or_404(job_work_id)
    
    # Ensure this is a multi-process or unified job work
    if job_work.work_type not in ['multi_process', 'unified']:
        flash('This function is only for multi-process job works.', 'error')
        return redirect(url_for('grn.quick_receive', job_work_id=job_work_id))
    
    # Get all processes for this job work
    processes = JobWorkProcess.query.filter_by(job_work_id=job_work_id).all()
    if not processes:
        flash('No processes found for this multi-process job work.', 'error')
        return redirect(url_for('multi_process_jobwork.detail', id=job_work_id))
    
    form = MultiProcessQuickReceiveForm()
    form.job_work_id.data = job_work_id
    
    # Get sequential process information for better understanding
    processes_ordered = sorted(processes, key=lambda x: x.sequence_number)
    
    # Populate process choices with sequential flow information
    form.process_selection.choices = []
    for p in processes_ordered:
        # Determine input source for this process
        if p.sequence_number == 1:
            input_source = job_work.item.name  # First process uses raw material
        else:
            # Find previous process
            prev_process = next((pr for pr in processes if pr.sequence_number == p.sequence_number - 1), None)
            if prev_process and prev_process.output_item_id:
                input_source = prev_process.output_item.name
            else:
                input_source = job_work.item.name
        
        # Create descriptive choice text showing sequential flow
        if p.output_item_id:
            flow_info = f" | {input_source} → {p.output_item.name} ({p.output_quantity} {p.output_item.unit_of_measure})"
        else:
            flow_info = f" | {input_source} → Same as input"
        
        form.process_selection.choices.append((p.id, f"Seq {p.sequence_number}: {p.process_name} - {p.work_type} ({p.status}){flow_info}"))
    
    if form.validate_on_submit():
        try:
            # Get selected process
            selected_process = JobWorkProcess.query.get(form.process_selection.data)
            if not selected_process:
                flash('Selected process not found.', 'error')
                return redirect(request.url)
            
            # Create GRN automatically
            grn = GRN(
                grn_number=GRN.generate_grn_number(),
                job_work_id=job_work_id,
                received_date=form.received_date.data,
                received_by=current_user.id,
                delivery_note=form.delivery_note.data,
                inspection_required=True,
                status='received',
                remarks=f"Multi-process receipt from {selected_process.process_name} process. {form.remarks.data or ''}"
            )
            db.session.add(grn)
            db.session.flush()  # To get the GRN ID
            
            # Auto-calculate passed quantity
            quantity_passed = form.quantity_received.data - (form.quantity_rejected.data or 0)
            
            # Determine which item is being received (output item or original item)
            receiving_item_id = selected_process.output_item_id if selected_process.output_item_id else job_work.item_id
            receiving_item = Item.query.get(receiving_item_id)
            
            # Create line item with process information
            line_item = GRNLineItem(
                grn_id=grn.id,
                item_id=receiving_item_id,
                quantity_received=form.quantity_received.data,
                quantity_passed=quantity_passed,
                quantity_rejected=form.quantity_rejected.data or 0,
                unit_of_measure=receiving_item.unit_of_measure,
                inspection_status=form.inspection_status.data,
                rejection_reason=form.rejection_reason.data,
                process_name=selected_process.process_name,
                process_stage=form.process_stage.data or selected_process.process_name
            )
            db.session.add(line_item)
            
            # Update inventory if requested and materials passed inspection
            if form.add_to_inventory.data and quantity_passed > 0:
                # Add to the output item's finished inventory (multi-state system)
                receiving_item.qty_finished = (receiving_item.qty_finished or 0) + quantity_passed
                # Add rejected quantity to scrap if any
                if form.quantity_rejected.data and form.quantity_rejected.data > 0:
                    receiving_item.qty_scrap = (receiving_item.qty_scrap or 0) + form.quantity_rejected.data
                grn.add_to_inventory = True
            else:
                grn.add_to_inventory = False
            
            # Process individual process scrap tracking
            process_scrap_updates = {}
            scrap_update_notes = []
            for key, value in request.form.items():
                if key.startswith('scrap_process_') and value:
                    try:
                        sequence_number = int(key.replace('scrap_process_', ''))
                        scrap_quantity = float(value)
                        if scrap_quantity > 0:
                            process_scrap_updates[sequence_number] = scrap_quantity
                    except (ValueError, TypeError):
                        continue
            
            # Update individual process scrap quantities
            for seq_num, scrap_qty in process_scrap_updates.items():
                process = JobWorkProcess.query.filter_by(
                    job_work_id=job_work_id,
                    sequence_number=seq_num
                ).first()
                if process:
                    old_scrap = process.quantity_scrap or 0
                    process.quantity_scrap = scrap_qty
                    scrap_update_notes.append(
                        f"Process {seq_num} ({process.process_name}): {old_scrap} → {scrap_qty} {receiving_item.unit_of_measure} scrap"
                    )
            
            # Update process completion status
            if form.inspection_status.data == 'passed':
                selected_process.quantity_output = (selected_process.quantity_output or 0) + quantity_passed
                # Add rejected quantity to current process scrap only if no individual scrap tracking was done
                if selected_process.sequence_number not in process_scrap_updates:
                    selected_process.quantity_scrap = (selected_process.quantity_scrap or 0) + (form.quantity_rejected.data or 0)
                if selected_process.quantity_output >= selected_process.quantity_input:
                    selected_process.status = 'completed'
                    selected_process.actual_completion = datetime.utcnow()
            
            # Mark GRN as completed if no further inspection needed
            if form.inspection_status.data in ['passed', 'rejected']:
                grn.status = 'completed'
                grn.inspection_status = 'completed'
                grn.inspected_by = current_user.id
                grn.inspected_at = datetime.utcnow()
            
            # Update job work status and quantity_received based on completion
            # For multi-process jobs, we need to check if all expected outputs have been received
            total_expected_output = sum(p.output_quantity or 0 for p in processes if p.output_item_id)
            total_received_output = sum(gli.quantity_passed for grn_item in GRN.query.filter_by(job_work_id=job_work_id).all() 
                                      for gli in grn_item.line_items if gli.item_id != job_work.item_id)  # Exclude input material
            
            if total_received_output >= total_expected_output and total_expected_output > 0:
                # All expected output received - mark job as completed
                job_work.status = 'completed'
                job_work.quantity_received = job_work.quantity_sent  # Mark input as fully processed
                
                # Remove input material from WIP since it's been transformed
                # Use the Item model's receive_from_wip method to properly clear WIP from the correct process
                if processes:
                    # For multi-process jobs, clear from first process
                    first_process = min(processes, key=lambda p: p.sequence_number)
                    process_name = first_process.process_name.lower()
                    job_work.item.receive_from_wip(0, 0, process=process_name)  # Just clear WIP, no finished/scrap added here
                    # Manually adjust to only clear the WIP amount without adding to finished (since output products were already added)
                    if process_name == 'cutting':
                        job_work.item.qty_wip_cutting = max(0, (job_work.item.qty_wip_cutting or 0) - job_work.quantity_sent)
                    elif process_name == 'bending':
                        job_work.item.qty_wip_bending = max(0, (job_work.item.qty_wip_bending or 0) - job_work.quantity_sent)
                    elif process_name == 'welding':
                        job_work.item.qty_wip_welding = max(0, (job_work.item.qty_wip_welding or 0) - job_work.quantity_sent)
                    elif process_name == 'zinc':
                        job_work.item.qty_wip_zinc = max(0, (job_work.item.qty_wip_zinc or 0) - job_work.quantity_sent)
                    elif process_name == 'painting':
                        job_work.item.qty_wip_painting = max(0, (job_work.item.qty_wip_painting or 0) - job_work.quantity_sent)
                    elif process_name == 'assembly':
                        job_work.item.qty_wip_assembly = max(0, (job_work.item.qty_wip_assembly or 0) - job_work.quantity_sent)
                    elif process_name == 'machining':
                        job_work.item.qty_wip_machining = max(0, (job_work.item.qty_wip_machining or 0) - job_work.quantity_sent)
                    elif process_name == 'polishing':
                        job_work.item.qty_wip_polishing = max(0, (job_work.item.qty_wip_polishing or 0) - job_work.quantity_sent)
                
                completion_note = f"[{datetime.utcnow().strftime('%Y-%m-%d %H:%M')}] Completed via GRN {grn.grn_number} - All expected output materials received"
            else:
                # Partial completion
                job_work.status = 'partial_received'
                completion_note = f"[{datetime.utcnow().strftime('%Y-%m-%d %H:%M')}] Partial receipt via GRN {grn.grn_number} - {quantity_passed} {receiving_item.unit_of_measure} received"
            
            # Add completion note to job work
            if job_work.notes:
                job_work.notes += f"\n{completion_note}"
            else:
                job_work.notes = completion_note
            
            db.session.commit()
            
            # Create success message with scrap tracking info
            success_message = f'Materials received from {selected_process.process_name} process! GRN {grn.grn_number} created.'
            if scrap_update_notes:
                success_message += f' Individual process scrap updated: {"; ".join(scrap_update_notes)}.'
            
            flash(success_message, 'success')
            return redirect(url_for('multi_process_jobwork.detail', id=job_work_id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error receiving materials: {str(e)}', 'error')
    
    return render_template('grn/quick_receive_multi_process.html',
                         title='Receive Multi-Process Materials',
                         form=form,
                         job_work=job_work,
                         processes=processes)


@grn_bp.route('/quick_receive_po/<int:purchase_order_id>/<int:item_id>', methods=['GET', 'POST'])
@login_required
def quick_receive_po(purchase_order_id, item_id):
    """Quick receive form for purchase order items"""
    purchase_order = PurchaseOrder.query.get_or_404(purchase_order_id)
    item = Item.query.get_or_404(item_id)
    
    # Get the specific PO item
    po_item = None
    for pi in purchase_order.items:
        if pi.item_id == item_id:
            po_item = pi
            break
    
    if not po_item:
        flash('Item not found in this purchase order.', 'error')
        return redirect(url_for('purchase.edit_purchase_order', id=purchase_order_id))
    
    form = QuickReceivePOForm()
    form.purchase_order_id.data = purchase_order_id
    form.item_id.data = item_id
    
    if form.validate_on_submit():
        try:
            # Create GRN automatically
            grn = GRN(
                grn_number=GRN.generate_grn_number(),
                purchase_order_id=purchase_order_id,
                received_date=form.received_date.data,
                received_by=current_user.id,
                delivery_note=form.delivery_note.data,
                inspection_required=True,
                status='received',
                remarks=form.remarks.data
            )
            db.session.add(grn)
            db.session.flush()  # To get the GRN ID
            
            # Auto-calculate passed quantity
            quantity_passed = form.quantity_received.data - (form.quantity_rejected.data or 0)
            
            # Create line item
            line_item = GRNLineItem(
                grn_id=grn.id,
                item_id=item_id,
                quantity_received=form.quantity_received.data,
                quantity_passed=quantity_passed,
                quantity_rejected=form.quantity_rejected.data or 0,
                unit_of_measure=po_item.uom or item.unit_of_measure,
                inspection_status=form.inspection_status.data,
                rejection_reason=form.rejection_reason.data,
                material_classification='raw_material',
                remarks=form.remarks.data
            )
            db.session.add(line_item)
            
            # Update inventory if adding to stock
            if form.add_to_inventory.data and quantity_passed > 0:
                # Add to multi-state inventory (raw materials from PO)
                item.qty_raw = (item.qty_raw or 0) + quantity_passed
                # Add rejected quantity to scrap if any
                if form.quantity_rejected.data and form.quantity_rejected.data > 0:
                    item.qty_scrap = (item.qty_scrap or 0) + form.quantity_rejected.data
                grn.add_to_inventory = True  # Set the flag to True when inventory is updated
            else:
                grn.add_to_inventory = False  # Set the flag to False when inventory is not updated
            
            # Mark GRN as completed if no further inspection needed
            if form.inspection_status.data in ['passed', 'rejected']:
                grn.status = 'completed'
                grn.inspection_status = 'completed'
                grn.inspected_by = current_user.id
                grn.inspected_at = datetime.utcnow()
            
            db.session.commit()
            
            # Update PO status automatically based on GRN receipt
            update_po_status_based_on_grn(purchase_order_id)
            
            flash(f'Materials received successfully! GRN {grn.grn_number} created for PO {purchase_order.po_number}.', 'success')
            return redirect(url_for('purchase.edit_purchase_order', id=purchase_order_id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error receiving materials: {str(e)}', 'error')
    
    return render_template('grn/quick_receive_po.html',
                         title='Quick Receive Materials',
                         form=form,
                         purchase_order=purchase_order,
                         item=item,
                         po_item=po_item)


@grn_bp.route('/list')
@login_required
def list_grns():
    """List all GRNs with filtering"""
    form = GRNSearchForm()
    
    # Build query
    query = GRN.query.join(JobWork)
    
    # Apply filters
    if request.args.get('search'):
        search_term = request.args.get('search')
        query = query.filter(
            or_(
                GRN.grn_number.ilike(f'%{search_term}%'),
                JobWork.job_number.ilike(f'%{search_term}%'),
                JobWork.customer_name.ilike(f'%{search_term}%')
            )
        )
    
    if request.args.get('status'):
        query = query.filter(GRN.status == request.args.get('status'))
    
    if request.args.get('inspection_status'):
        query = query.filter(GRN.inspection_status == request.args.get('inspection_status'))
    
    # Pagination
    page = request.args.get('page', 1, type=int)
    grns = query.order_by(GRN.received_date.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('grn/list.html',
                         title='All GRNs',
                         grns=grns,
                         form=form)


@grn_bp.route('/detail/<int:grn_id>')
@login_required
def detail(grn_id):
    """View GRN details"""
    grn = GRN.query.get_or_404(grn_id)
    
    return render_template('grn/detail.html',
                         title=f'GRN {grn.grn_number}',
                         grn=grn)


@grn_bp.route('/add_line_items/<int:grn_id>', methods=['GET', 'POST'])
@login_required
def add_line_items(grn_id):
    """Add line items to a GRN"""
    grn = GRN.query.get_or_404(grn_id)
    
    if grn.status == 'completed':
        flash('Cannot modify completed GRN', 'error')
        return redirect(url_for('grn.detail', grn_id=grn_id))
    
    form = GRNLineItemForm()
    form.grn_id.data = grn_id
    form.item_id.data = grn.job_work.item_id
    
    # Pre-fill form with job work item details
    if not form.unit_of_measure.data:
        form.unit_of_measure.data = grn.job_work.item.unit_of_measure
    
    if form.validate_on_submit():
        try:
            line_item = GRNLineItem(
                grn_id=grn_id,
                item_id=form.item_id.data,
                quantity_received=form.quantity_received.data,
                quantity_passed=form.quantity_passed.data,
                quantity_rejected=form.quantity_rejected.data,
                unit_of_measure=form.unit_of_measure.data,
                unit_weight=form.unit_weight.data,
                inspection_status=form.inspection_status.data,
                rejection_reason=form.rejection_reason.data,
                quality_grade=form.quality_grade.data,
                process_name=form.process_name.data,
                process_stage=form.process_stage.data,

                batch_number=form.batch_number.data,
                serial_numbers=form.serial_numbers.data,
                remarks=form.remarks.data
            )
            
            db.session.add(line_item)
            db.session.commit()
            
            flash('Line item added successfully!', 'success')
            return redirect(url_for('grn.detail', grn_id=grn_id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding line item: {str(e)}', 'error')
    
    return render_template('grn/add_line_items.html',
                         title='Add Line Items',
                         form=form,
                         grn=grn)


# API Endpoints for AJAX functionality

@grn_bp.route('/api/job_work/<int:job_work_id>/pending_quantity')
@login_required
def api_pending_quantity(job_work_id):
    """API to get pending quantity for a job work"""
    job_work = JobWork.query.get_or_404(job_work_id)
    
    return jsonify({
        'success': True,
        'quantity_sent': job_work.quantity_sent,
        'quantity_received': job_work.quantity_received or 0,
        'pending_quantity': job_work.pending_quantity,
        'completion_percentage': job_work.completion_percentage,
        'unit_of_measure': job_work.item.unit_of_measure
    })


@grn_bp.route('/api/grn/<int:grn_id>/summary')
@login_required
def api_grn_summary(grn_id):
    """API to get GRN summary data"""
    grn = GRN.query.get_or_404(grn_id)
    
    return jsonify({
        'success': True,
        'grn_number': grn.grn_number,
        'total_received': grn.total_quantity_received,
        'total_passed': grn.total_quantity_passed,
        'total_rejected': grn.total_quantity_rejected,
        'acceptance_rate': grn.acceptance_rate,
        'is_fully_inspected': grn.is_fully_inspected,
        'status': grn.status,
        'inspection_status': grn.inspection_status
    })