from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from forms import JobWorkForm, JobWorkQuantityUpdateForm
from models import JobWork, Supplier, Item, BOM, BOMItem, CompanySettings
from app import db
from sqlalchemy import func
from utils import generate_job_number  
from services.notification_helpers import send_email_notification, send_whatsapp_notification, send_email_with_attachment
from utils_documents import get_documents_for_transaction

jobwork_bp = Blueprint('jobwork', __name__)

@jobwork_bp.route('/dashboard')
@login_required
def dashboard():
    # Job work statistics
    stats = {
        'total_jobs': JobWork.query.count(),
        'sent_jobs': JobWork.query.filter_by(status='sent').count(),
        'partial_received': JobWork.query.filter_by(status='partial_received').count(),
        'completed_jobs': JobWork.query.filter_by(status='completed').count()
    }
    
    # Recent job works
    recent_jobs = JobWork.query.order_by(JobWork.created_at.desc()).limit(10).all()
    
    # Pending returns (jobs sent but not completed)
    pending_jobs = JobWork.query.filter(JobWork.status.in_(['sent', 'partial_received'])).all()
    
    # Top job work customers
    top_customers = db.session.query(
        JobWork.customer_name, 
        func.count(JobWork.id).label('job_count')
    ).group_by(JobWork.customer_name).order_by(func.count(JobWork.id).desc()).limit(5).all()
    
    return render_template('jobwork/dashboard.html', 
                         stats=stats, 
                         recent_jobs=recent_jobs,
                         pending_jobs=pending_jobs,
                         top_customers=top_customers)

@jobwork_bp.route('/list')
@login_required
def list_job_works():
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', '', type=str)
    
    query = JobWork.query
    if status_filter:
        query = query.filter_by(status=status_filter)
    
    jobs = query.order_by(JobWork.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False)
    
    return render_template('jobwork/list.html', jobs=jobs, status_filter=status_filter)

@jobwork_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_job_work():
    form = JobWorkForm()
    
    # Auto-generate job number if not provided
    if not form.job_number.data:
        form.job_number.data = generate_job_number()
    
    if form.validate_on_submit():
        # Check if job number already exists
        existing_job = JobWork.query.filter_by(job_number=form.job_number.data).first()
        if existing_job:
            flash('Job number already exists', 'danger')
            return render_template('jobwork/form.html', form=form, title='Add Job Work')
        
        # Check if there's sufficient inventory
        item = Item.query.get(form.item_id.data)
        if not item:
            flash('Selected item not found', 'danger')
            return render_template('jobwork/form.html', form=form, title='Add Job Work')
            
        if (item.current_stock or 0) < form.quantity_sent.data:
            flash(f'Insufficient inventory. Available stock: {item.current_stock or 0} {item.unit_of_measure}', 'danger')
            return render_template('jobwork/form.html', form=form, title='Add Job Work')

        job = JobWork(
            job_number=form.job_number.data,
            customer_name=form.customer_name.data,
            item_id=form.item_id.data,
            process=form.process.data,
            quantity_sent=form.quantity_sent.data,
            rate_per_unit=form.rate_per_unit.data,
            sent_date=form.sent_date.data,
            expected_return=form.expected_return.data,
            notes=form.notes.data,
            created_by=current_user.id
        )
        
        # Deduct from inventory when sending to vendor
        item.current_stock = (item.current_stock or 0) - form.quantity_sent.data
        
        db.session.add(job)
        db.session.commit()
        flash(f'Job Work created successfully. {form.quantity_sent.data} {item.unit_of_measure} deducted from inventory.', 'success')
        return redirect(url_for('jobwork.list_job_works'))
    
    return render_template('jobwork/form.html', form=form, title='Add Job Work')

@jobwork_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_job_work(id):
    job = JobWork.query.get_or_404(id)
    form = JobWorkForm(obj=job)
    
    if form.validate_on_submit():
        # Check if job number already exists (excluding current job)
        existing_job = JobWork.query.filter(
            JobWork.job_number == form.job_number.data, 
            JobWork.id != id
        ).first()
        if existing_job:
            flash('Job number already exists', 'danger')
            return render_template('jobwork/form.html', form=form, title='Edit Job Work', job=job)
        
        # Handle inventory adjustments if quantity_sent is changed
        old_quantity_sent = job.quantity_sent
        new_quantity_sent = form.quantity_sent.data
        
        if old_quantity_sent != new_quantity_sent:
            item = job.item
            quantity_difference = new_quantity_sent - old_quantity_sent
            
            # Check if there's sufficient inventory for increase
            if quantity_difference > 0 and (item.current_stock or 0) < quantity_difference:
                flash(f'Insufficient inventory for increase. Available stock: {item.current_stock or 0} {item.unit_of_measure}', 'danger')
                return render_template('jobwork/form.html', form=form, title='Edit Job Work', job=job)
            
            # Adjust inventory: subtract additional sent quantity or add back if reduced
            item.current_stock = (item.current_stock or 0) - quantity_difference
        
        job.job_number = form.job_number.data
        job.customer_name = form.customer_name.data
        job.item_id = form.item_id.data
        job.process = form.process.data
        job.quantity_sent = form.quantity_sent.data
        job.rate_per_unit = form.rate_per_unit.data
        job.sent_date = form.sent_date.data
        job.expected_return = form.expected_return.data
        job.notes = form.notes.data
        
        db.session.commit()
        flash('Job Work updated successfully', 'success')
        return redirect(url_for('jobwork.list_job_works'))
    
    return render_template('jobwork/form.html', form=form, title='Edit Job Work', job=job)

@jobwork_bp.route('/update_status/<int:id>/<status>')
@login_required
def update_status(id, status):
    job = JobWork.query.get_or_404(id)
    if status in ['sent', 'partial_received', 'completed']:
        job.status = status
        db.session.commit()
        flash(f'Job Work status updated to {status}', 'success')
    else:
        flash('Invalid status', 'danger')
    
    return redirect(url_for('jobwork.list_job_works'))

@jobwork_bp.route('/update_quantity/<int:id>', methods=['GET', 'POST'])
@login_required
def update_quantity(id):
    job = JobWork.query.get_or_404(id)
    form = JobWorkQuantityUpdateForm(job=job)
    
    if form.validate_on_submit():
        # Update quantity received
        additional_received = form.quantity_received.data
        job.quantity_received += additional_received
        job.received_date = form.received_date.data
        
        # Add received quantity back to inventory
        item = job.item
        item.current_stock = (item.current_stock or 0) + additional_received
        
        # Update notes
        if form.notes.data:
            if job.notes:
                job.notes += f"\n\n[{form.received_date.data.strftime('%m/%d/%Y')}] Received: {additional_received} {item.unit_of_measure}. {form.notes.data}"
            else:
                job.notes = f"[{form.received_date.data.strftime('%m/%d/%Y')}] Received: {additional_received} {item.unit_of_measure}. {form.notes.data}"
        else:
            if job.notes:
                job.notes += f"\n\n[{form.received_date.data.strftime('%m/%d/%Y')}] Received: {additional_received} {item.unit_of_measure}"
            else:
                job.notes = f"[{form.received_date.data.strftime('%m/%d/%Y')}] Received: {additional_received} {item.unit_of_measure}"
        
        # Update status based on quantity received
        if job.quantity_received >= job.quantity_sent:
            job.status = 'completed'
            job.quantity_received = job.quantity_sent  # Ensure we don't exceed sent quantity
        elif job.quantity_received > 0:
            job.status = 'partial_received'
        
        db.session.commit()
        flash(f'Quantity updated successfully. Received: {additional_received} {job.item.unit_of_measure}', 'success')
        return redirect(url_for('jobwork.list_job_works'))
    
    return render_template('jobwork/update_quantity.html', form=form, job=job, title='Update Quantity')

@jobwork_bp.route('/send/<int:job_id>', methods=['GET', 'POST'])
@login_required
def send_job_work(job_id):
    job = JobWork.query.get_or_404(job_id)
    
    if request.method == 'POST':
        send_type = request.form.get('send_type')
        recipient = request.form.get('recipient')
        message = request.form.get('message', '')
        
        # Get company info for email
        company = CompanySettings.query.first()
        
        # Create Job Work summary for message
        job_summary = f"""
Job Work Order: {job.job_number}
Customer: {job.customer_name}
Item: {job.item.name}
Quantity Sent: {job.quantity_sent} {job.item.unit_of_measure}
Rate per Unit: ₹{job.rate_per_unit:.2f}
Total Value: ₹{job.quantity_sent * job.rate_per_unit:.2f}
Sent Date: {job.sent_date}
Expected Return: {job.expected_return or 'Not specified'}

{message}
"""
        
        success = False
        if send_type == 'email':
            subject = f"Job Work Order {job.job_number} - {company.company_name if company else 'AK Innovations'}"
            
            # Generate PDF attachment for Job Work
            from weasyprint import HTML, CSS
            from flask import render_template_string
            
            # Create a simple Job Work PDF template
            job_html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Job Work Order - {job.job_number}</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 20px; }}
                    .header {{ text-align: center; margin-bottom: 30px; }}
                    .details {{ margin-bottom: 20px; }}
                    .details th, .details td {{ padding: 8px; text-align: left; }}
                    table {{ width: 100%; border-collapse: collapse; }}
                    th, td {{ border: 1px solid #ddd; }}
                </style>
            </head>
            <body>
                <div class="header">
                    <h2>{company.company_name if company else 'AK Innovations'}</h2>
                    <h3>Job Work Order</h3>
                </div>
                <table class="details">
                    <tr><th>Job Number:</th><td>{job.job_number}</td></tr>
                    <tr><th>Customer:</th><td>{job.customer_name}</td></tr>
                    <tr><th>Item:</th><td>{job.item.name}</td></tr>
                    <tr><th>Quantity Sent:</th><td>{job.quantity_sent} {job.item.unit_of_measure}</td></tr>
                    <tr><th>Rate per Unit:</th><td>₹{job.rate_per_unit:.2f}</td></tr>
                    <tr><th>Total Value:</th><td>₹{job.quantity_sent * job.rate_per_unit:.2f}</td></tr>
                    <tr><th>Sent Date:</th><td>{job.sent_date}</td></tr>
                    <tr><th>Expected Return:</th><td>{job.expected_return or 'Not specified'}</td></tr>
                </table>
            </body>
            </html>
            """
            
            # Convert to PDF
            pdf_bytes = HTML(string=job_html, base_url=request.url_root).write_pdf()
            
            # Send email with PDF attachment
            success = send_email_with_attachment(
                recipient, 
                subject, 
                job_summary,
                pdf_bytes,
                f"JobWork_{job.job_number}.pdf"
            )
        elif send_type == 'whatsapp':
            success = send_whatsapp_notification(recipient, job_summary)
        
        if success:
            flash(f'Job Work order sent successfully via {send_type.title()}!', 'success')
        else:
            flash(f'Failed to send Job Work order via {send_type.title()}. Please check your notification settings.', 'danger')
        
        return redirect(url_for('jobwork.list_job_works'))
    
    return render_template('jobwork/send.html', job=job, title=f'Send Job Work {job.job_number}')

# BOM rate auto-filling API removed as requested - users will manually enter rates
