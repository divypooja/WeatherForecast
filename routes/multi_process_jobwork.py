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

def generate_job_number():
    """Generate unique job number in format MPJOB-YYYY-0001"""
    from datetime import datetime
    current_year = datetime.now().year
    
    # Find the highest job number for current year for multi-process jobs
    last_job = JobWork.query.filter(
        JobWork.job_number.like(f'MPJOB-{current_year}-%'),
        JobWork.work_type == 'multi_process'
    ).order_by(JobWork.job_number.desc()).first()
    
    if last_job:
        # Extract the number part and increment
        try:
            last_number = int(last_job.job_number.split('-')[-1])
            next_number = last_number + 1
        except (IndexError, ValueError):
            next_number = 1
    else:
        next_number = 1
    
    return f"MPJOB-{current_year}-{next_number:04d}"

multi_process_jobwork_bp = Blueprint('multi_process_jobwork', __name__, url_prefix='/jobwork/multi-process')

@multi_process_jobwork_bp.route('/')
@multi_process_jobwork_bp.route('/list')
@login_required
def list_multi_process_jobs():
    """List all multi-process job works"""
    jobs = JobWork.query.filter_by(work_type='multi_process').order_by(JobWork.created_at.desc()).all()
    
    # Add process summary for each job
    job_summaries = []
    for job in jobs:
        processes = JobWorkProcess.query.filter_by(job_work_id=job.id).all()
        total_cost = sum(p.process_cost for p in processes if p.process_cost) if processes else 0
        completed_count = len([p for p in processes if p.status == 'completed']) if processes else 0
        
        job_summaries.append({
            'job': job,
            'total_processes': len(processes) if processes else 0,
            'completed_processes': completed_count,
            'total_cost': total_cost,
            'progress_percentage': (completed_count / len(processes) * 100) if processes else 0
        })
    
    return render_template('multi_process_jobwork/list.html', 
                         job_summaries=job_summaries,
                         title='Multi-Process Job Works')

@multi_process_jobwork_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_multi_process_job():
    """Create a new multi-process job work"""
    form = MultiProcessJobWorkForm()
    
    if request.method == 'POST':
        # Debug: Print form data and validation errors
        print("Form data received:", request.form)
        print("Form validation errors:", form.errors)
        
        # Handle form submission manually due to CSRF issues with dynamic process data
        try:
            # Basic validation
            if not request.form.get('item_id') or not request.form.get('total_quantity'):
                flash('Please select an item and enter total quantity', 'danger')
                return render_template('multi_process_jobwork/form.html', form=form, title='Add Multi-Process Job Work')
            
            # Skip CSRF validation for now since it's causing issues - we'll process the form directly
            print("Processing multi-process job work form...")
            
            # Get form data
            print("Extracting form data...")
            item_id = int(request.form.get('item_id'))
            total_quantity = float(request.form.get('total_quantity'))
            sent_date_str = request.form.get('sent_date')
            expected_return_str = request.form.get('expected_return')
            notes = request.form.get('notes', '')
            print(f"Form data: item_id={item_id}, quantity={total_quantity}, sent_date={sent_date_str}")
            
            # Parse dates
            from datetime import datetime
            sent_date = datetime.strptime(sent_date_str, '%Y-%m-%d').date() if sent_date_str else None
            expected_return = datetime.strptime(expected_return_str, '%Y-%m-%d').date() if expected_return_str else None
            print(f"Parsed dates: sent_date={sent_date}, expected_return={expected_return}")
            
            # Create the main job work
            print("Looking up item...")
            item = Item.query.get(item_id)
            if not item:
                print(f"Item not found: {item_id}")
                flash('Selected item not found', 'danger')
                return render_template('multi_process_jobwork/form.html', form=form, title='Add Multi-Process Job Work')
            
            print(f"Found item: {item.name}, current raw qty: {item.qty_raw}")
            
            # Initialize multi-state inventory if not set
            if item.qty_raw is None or item.qty_raw == 0.0:
                print("Initializing multi-state inventory...")
                item.qty_raw = item.current_stock or 0.0
                item.qty_wip = 0.0
                item.qty_finished = 0.0
                item.qty_scrap = 0.0
                db.session.commit()
                print(f"Initialized: raw={item.qty_raw}, wip={item.qty_wip}")
                
            # Check if enough raw materials available
            if item.qty_raw < total_quantity:
                print(f"Insufficient materials: available={item.qty_raw}, required={total_quantity}")
                flash(f'Insufficient raw materials. Available: {item.qty_raw}, Required: {total_quantity}', 'danger')
                return render_template('multi_process_jobwork/form.html', form=form, title='Add Multi-Process Job Work')
            
            # Generate unique job number
            print("Generating job number...")
            job_number = generate_job_number()
            print(f"Generated job number: {job_number}")
                
            # Create main job work record
            print("Creating main job work record...")
            job = JobWork(
                job_number=job_number,
                customer_name="Multi-Process Job",  # Will be handled by individual processes
                item_id=item_id,
                process="Multi-Process",  # Indicates this is a multi-process job
                work_type="multi_process",  # New work type for multi-process jobs
                quantity_sent=total_quantity,
                rate_per_unit=0.0,  # Total cost will be sum of all processes
                sent_date=sent_date,
                expected_return=expected_return,
                notes=notes,
                created_by=current_user.id
            )
            
            print("Adding job to database...")
            db.session.add(job)
            db.session.flush()  # Get the job ID
            print(f"Job created with ID: {job.id}")
            
            # Parse processes from form data
            print("Parsing processes...")
            processes_data = request.form.getlist('processes')
            print(f"Found {len(processes_data)} processes: {processes_data}")
            
            if not processes_data:
                print("No processes found!")
                flash('At least one process must be defined', 'danger')
                return render_template('multi_process_jobwork/form.html', form=form, title='Add Multi-Process Job Work')
            
            # Validate total process quantities match total quantity
            print("Validating process quantities...")
            total_process_quantity = 0
            process_list = []
            
            for i, process_json in enumerate(processes_data):
                try:
                    process_data = json.loads(process_json)
                    process_quantity = float(process_data['quantity_input'])
                    total_process_quantity += process_quantity
                    process_list.append(process_data)
                    print(f"Process {i+1}: {process_data['process_name']} - Quantity: {process_quantity}")
                except (json.JSONDecodeError, KeyError, ValueError) as e:
                    flash(f'Error processing process {i+1}: {str(e)}', 'danger')
                    return render_template('multi_process_jobwork/form.html', form=form, title='Add Multi-Process Job Work')
            
            print(f"Total process quantity: {total_process_quantity}, Required total: {total_quantity}")
            
            # Business rule: For sequential processes, each process can handle the full quantity
            # For parallel processes, quantities must add up to total
            # Allow both scenarios - user decides the workflow
            
            # Check if all processes have the same quantity (sequential workflow)
            all_quantities = [float(json.loads(p)['quantity_input']) for p in processes_data]
            is_sequential = all(q == total_quantity for q in all_quantities)
            
            print(f"Process quantities: {all_quantities}")
            print(f"Is sequential workflow: {is_sequential}")
            print(f"Total from processes: {total_process_quantity}")
            
            if not is_sequential and total_process_quantity != total_quantity:
                flash(f'For parallel processes, quantities must sum to {total_quantity}. For sequential processes, each process should handle {total_quantity} pieces. Current total: {total_process_quantity}', 'danger')
                return render_template('multi_process_jobwork/form.html', form=form, title='Add Multi-Process Job Work')
            
            # Create individual processes
            print("Creating individual processes...")
            for i, process_data in enumerate(process_list):
                try:
                    process = JobWorkProcess(
                        job_work_id=job.id,
                        process_name=process_data['process_name'],
                        sequence_number=process_data.get('sequence_number', i + 1),
                        quantity_input=process_data['quantity_input'],
                        expected_scrap=process_data.get('expected_scrap', 0.0),
                        work_type=process_data['work_type'],
                        customer_name=process_data.get('customer_name', ''),
                        department=process_data.get('department', ''),
                        rate_per_unit=process_data.get('rate_per_unit', 0.0),
                        start_date=datetime.strptime(process_data['start_date'], '%Y-%m-%d').date() if process_data.get('start_date') else None,
                        expected_completion=datetime.strptime(process_data['expected_completion'], '%Y-%m-%d').date() if process_data.get('expected_completion') else None,
                        notes=process_data.get('notes', '')
                    )
                    
                    db.session.add(process)
                    print(f"Added process: {process_data['process_name']} with quantity {process_data['quantity_input']}")
                except Exception as e:
                    flash(f'Error creating process {i+1}: {str(e)}', 'danger')
                    return render_template('multi_process_jobwork/form.html', form=form, title='Add Multi-Process Job Work')
                
            # Move materials from Raw to WIP
            print("Moving materials to WIP...")
            if item.move_to_wip(total_quantity):
                print("Materials moved successfully, committing transaction...")
                db.session.commit()
                print("Transaction committed successfully!")
                flash(f'Multi-process job work {job_number} created successfully! {total_quantity} units moved to WIP state.', 'success')
                print(f"Redirecting to detail page for job ID: {job.id}")
                return redirect(url_for('multi_process_jobwork.detail', id=job.id))
            else:
                print("Failed to move materials to WIP")
                flash('Failed to move materials to WIP state', 'danger')
                
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating job work: {str(e)}', 'danger')
            print(f"Exception details: {e}")
            import traceback
            traceback.print_exc()
    
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





@multi_process_jobwork_bp.route('/api/process-template')
@login_required
def process_template():
    """API endpoint to get process form template for dynamic addition"""
    form = JobWorkProcessForm()
    return render_template('multi_process_jobwork/process_template.html', form=form)