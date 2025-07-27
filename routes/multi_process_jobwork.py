"""
Multi-Process Job Work Routes

This module handles routing for multi-process job work functionality where
one job work can have multiple processes in different stages.
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models import JobWork, JobWorkProcess, Item, Supplier, db
from forms_jobwork_process import MultiProcessJobWorkForm, JobWorkProcessForm, ProcessProgressForm
from datetime import datetime, date
import json

multi_process_jobwork_bp = Blueprint('multi_process_jobwork', __name__, url_prefix='/jobwork/multi-process')

@multi_process_jobwork_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_multi_process_job():
    """Create a new multi-process job work"""
    form = MultiProcessJobWorkForm()
    
    if request.method == 'POST':
        if form.validate_on_submit():
            try:
                # Create the main job work
                item = Item.query.get(form.item_id.data)
                if not item:
                    flash('Selected item not found', 'danger')
                    return render_template('multi_process_jobwork/form.html', form=form, title='Add Multi-Process Job Work')
                
                # Initialize multi-state inventory if not set
                if item.qty_raw is None or item.qty_raw == 0.0:
                    item.qty_raw = item.current_stock or 0.0
                    item.qty_wip = 0.0
                    item.qty_finished = 0.0
                    item.qty_scrap = 0.0
                    db.session.commit()
                
                # Check if enough raw materials available
                if item.qty_raw < form.total_quantity.data:
                    flash(f'Insufficient raw materials. Available: {item.qty_raw}, Required: {form.total_quantity.data}', 'danger')
                    return render_template('multi_process_jobwork/form.html', form=form, title='Add Multi-Process Job Work')
                
                # Create main job work record
                job = JobWork(
                    job_number=form.job_number.data,
                    customer_name="Multi-Process Job",  # Will be handled by individual processes
                    item_id=form.item_id.data,
                    process="Multi-Process",  # Indicates this is a multi-process job
                    work_type="multi_process",  # New work type for multi-process jobs
                    quantity_sent=form.total_quantity.data,
                    rate_per_unit=0.0,  # Total cost will be sum of all processes
                    sent_date=form.sent_date.data,
                    expected_return=form.expected_return.data,
                    notes=form.notes.data,
                    created_by=current_user.id
                )
                
                db.session.add(job)
                db.session.flush()  # Get the job ID
                
                # Parse processes from form data
                processes_data = request.form.getlist('processes')
                if not processes_data:
                    flash('At least one process must be defined', 'danger')
                    return render_template('multi_process_jobwork/form.html', form=form, title='Add Multi-Process Job Work')
                
                # Create individual processes
                for i, process_json in enumerate(processes_data):
                    try:
                        process_data = json.loads(process_json)
                        
                        process = JobWorkProcess(
                            job_work_id=job.id,
                            process_name=process_data['process_name'],
                            sequence_number=process_data.get('sequence_number', i + 1),
                            quantity_input=process_data['quantity_input'],
                            work_type=process_data['work_type'],
                            customer_name=process_data.get('customer_name', ''),
                            department=process_data.get('department', ''),
                            rate_per_unit=process_data.get('rate_per_unit', 0.0),
                            start_date=datetime.strptime(process_data['start_date'], '%Y-%m-%d').date() if process_data.get('start_date') else None,
                            expected_completion=datetime.strptime(process_data['expected_completion'], '%Y-%m-%d').date() if process_data.get('expected_completion') else None,
                            notes=process_data.get('notes', '')
                        )
                        
                        db.session.add(process)
                    except (json.JSONDecodeError, KeyError, ValueError) as e:
                        flash(f'Error processing process {i+1}: {str(e)}', 'danger')
                        return render_template('multi_process_jobwork/form.html', form=form, title='Add Multi-Process Job Work')
                
                # Move materials from Raw to WIP
                if item.move_to_wip(form.total_quantity.data):
                    db.session.commit()
                    flash(f'Multi-process job work {job.job_number} created successfully! {form.total_quantity.data} units moved to WIP state.', 'success')
                    return redirect(url_for('multi_process_jobwork.detail', id=job.id))
                else:
                    flash('Failed to move materials to WIP state', 'danger')
                    
            except Exception as e:
                db.session.rollback()
                flash(f'Error creating job work: {str(e)}', 'danger')
        else:
            flash('Please correct the errors below', 'danger')
    
    return render_template('multi_process_jobwork/form.html', form=form, title='Add Multi-Process Job Work')


@multi_process_jobwork_bp.route('/detail/<int:id>')
@login_required
def detail(id):
    """View multi-process job work details with all processes"""
    job = JobWork.query.get_or_404(id)
    
    # Get all processes for this job work ordered by sequence
    processes = JobWorkProcess.query.filter_by(job_work_id=id).order_by(JobWorkProcess.sequence_number).all()
    
    # Calculate overall progress
    total_processes = len(processes)
    completed_processes = len([p for p in processes if p.status == 'completed'])
    overall_progress = (completed_processes / total_processes * 100) if total_processes > 0 else 0
    
    return render_template('multi_process_jobwork/detail.html', 
                         job=job, 
                         processes=processes,
                         overall_progress=overall_progress)


@multi_process_jobwork_bp.route('/process/<int:process_id>/update', methods=['GET', 'POST'])
@login_required
def update_process(process_id):
    """Update progress on individual process"""
    process = JobWorkProcess.query.get_or_404(process_id)
    form = ProcessProgressForm(obj=process)
    
    if request.method == 'POST':
        if form.validate_on_submit():
            try:
                # Update process progress
                process.quantity_output = form.quantity_output.data
                process.quantity_scrap = form.quantity_scrap.data
                process.status = form.status.data
                process.actual_completion = form.actual_completion.data
                process.notes = form.notes.data
                process.updated_at = datetime.utcnow()
                
                # If process is completed, prepare materials for next process
                if form.status.data == 'completed':
                    # Check if this is the final process
                    final_process = not JobWorkProcess.query.filter(
                        JobWorkProcess.job_work_id == process.job_work_id,
                        JobWorkProcess.sequence_number > process.sequence_number
                    ).first()
                    
                    if final_process:
                        # Final process - move finished goods to Finished state
                        job = process.job_work
                        if job.item.receive_from_wip(form.quantity_output.data, form.quantity_scrap.data):
                            flash(f'Process {process.process_name} completed! {form.quantity_output.data} units moved to Finished goods, {form.quantity_scrap.data} to Scrap.', 'success')
                        else:
                            flash('Process completed but failed to update inventory states', 'warning')
                    else:
                        flash(f'Process {process.process_name} completed! Materials ready for next process.', 'success')
                
                db.session.commit()
                return redirect(url_for('multi_process_jobwork.detail', id=process.job_work_id))
                
            except Exception as e:
                db.session.rollback()
                flash(f'Error updating process: {str(e)}', 'danger')
        else:
            flash('Please correct the errors below', 'danger')
    
    return render_template('multi_process_jobwork/process_update.html', 
                         form=form, 
                         process=process,
                         title=f'Update {process.process_name} Process')


@multi_process_jobwork_bp.route('/list')
@login_required
def list_multi_process_jobs():
    """List all multi-process job works"""
    jobs = JobWork.query.filter_by(work_type='multi_process').order_by(JobWork.created_at.desc()).all()
    
    # Add process summary for each job
    job_summaries = []
    for job in jobs:
        processes = JobWorkProcess.query.filter_by(job_work_id=job.id).all()
        total_cost = sum(p.process_cost for p in processes)
        completed_count = len([p for p in processes if p.status == 'completed'])
        
        job_summaries.append({
            'job': job,
            'total_processes': len(processes),
            'completed_processes': completed_count,
            'total_cost': total_cost,
            'progress_percentage': (completed_count / len(processes) * 100) if processes else 0
        })
    
    return render_template('multi_process_jobwork/list.html', 
                         job_summaries=job_summaries,
                         title='Multi-Process Job Works')


@multi_process_jobwork_bp.route('/api/process-template')
@login_required
def process_template():
    """API endpoint to get process form template for dynamic addition"""
    form = JobWorkProcessForm()
    return render_template('multi_process_jobwork/process_template.html', form=form)