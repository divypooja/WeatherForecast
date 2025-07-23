from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from forms import JobWorkForm
from models import JobWork, Supplier
from app import db
from sqlalchemy import func
from utils import generate_job_number

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
        
        job = JobWork(
            job_number=form.job_number.data,
            customer_name=form.customer_name.data,
            item_id=form.item_id.data,
            quantity_sent=form.quantity_sent.data,
            rate_per_unit=form.rate_per_unit.data,
            sent_date=form.sent_date.data,
            expected_return=form.expected_return.data,
            notes=form.notes.data,
            created_by=current_user.id
        )
        db.session.add(job)
        db.session.commit()
        flash('Job Work created successfully', 'success')
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
        
        job.job_number = form.job_number.data
        job.customer_name = form.customer_name.data
        job.item_id = form.item_id.data
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
