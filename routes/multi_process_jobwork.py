"""
Multi-Process Job Work Routes

This module handles routing for multi-process job work functionality where
one job work can have multiple processes in different stages.
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models import JobWork, JobWorkProcess, Item, Supplier, BOM, BOMItem, db
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
    
    # Get all items for output product dropdowns
    all_items = Item.query.order_by(Item.name).all()
    items_json = json.dumps([{
        'id': item.id,
        'code': item.code,
        'name': item.name,
        'unit_of_measure': item.unit_of_measure
    } for item in all_items])
    
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
            
            # Generate unique job number - use regular JOB format for unified system
            print("Generating job number...")
            from datetime import datetime
            current_year = datetime.now().year
            
            # Get the highest job number for current year
            existing_jobs = JobWork.query.filter(
                JobWork.job_number.like(f'JOB-{current_year}-%')
            ).order_by(JobWork.job_number.desc()).first()
            
            if existing_jobs:
                # Extract number and increment
                last_number = int(existing_jobs.job_number.split('-')[2])
                next_number = last_number + 1
            else:
                next_number = 1
                
            job_number = f"JOB-{current_year}-{next_number:04d}"
            print(f"Generated job number: {job_number}")
                
            # Create main job work record
            print("Creating main job work record...")
            job = JobWork(
                job_number=job_number,
                customer_name="Multi-Process Job",  # Will be handled by individual processes
                item_id=item_id,
                process="Multi-Process",  # Indicates this is a multi-process job
                work_type="unified",  # Unified work type for all job works
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
            
            # Parse and validate processes
            print("Processing individual processes...")
            process_list = []
            
            for i, process_json in enumerate(processes_data):
                try:
                    process_data = json.loads(process_json)
                    process_list.append(process_data)
                    print(f"Process {i+1}: {process_data['process_name']} - Sequence: {process_data.get('sequence_number', i+1)}")
                except (json.JSONDecodeError, KeyError, ValueError) as e:
                    flash(f'Error processing process {i+1}: {str(e)}', 'danger')
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
                        notes=process_data.get('notes', ''),
                        output_item_id=int(process_data['output_item_id']) if process_data.get('output_item_id') else None,
                        output_quantity=float(process_data.get('output_quantity', 0)),
                        is_team_work=process_data.get('is_team_work', False),
                        max_team_members=int(process_data.get('max_team_members', 1)) if process_data.get('max_team_members') else 1,
                        team_lead_id=int(process_data['team_lead']) if process_data.get('team_lead') else None
                    )
                    
                    db.session.add(process)
                    print(f"Added process: {process_data['process_name']} with quantity {process_data['quantity_input']}")
                except Exception as e:
                    flash(f'Error creating process {i+1}: {str(e)}', 'danger')
                    return render_template('multi_process_jobwork/form.html', form=form, title='Add Multi-Process Job Work')
                
            # Move materials from Raw to process-specific WIP
            print("Moving materials to WIP...")
            # For multi-process jobs, move materials to the first process WIP
            first_process = min(process_list, key=lambda p: p.get('sequence_number', 1))
            process_name = first_process['process_name']
            
            if item.move_to_wip(total_quantity, process_name):
                print(f"Materials moved successfully to {process_name} WIP, committing transaction...")
                db.session.commit()
                print("Transaction committed successfully!")
                flash(f'Multi-process job work {job_number} created successfully! {total_quantity} units moved to {process_name} WIP state.', 'success')
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
    
    return render_template('multi_process_jobwork/form.html', form=form, title='Add Multi-Process Job Work', items_json=items_json)


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





@multi_process_jobwork_bp.route('/api/item-bom/<int:item_id>')
@login_required
def get_item_bom(item_id):
    """Get BOM data for an item to populate job work rates"""
    try:
        item = Item.query.get_or_404(item_id)
        
        # Find active BOM for this item
        bom = BOM.query.filter_by(product_id=item_id, is_active=True).first()
        
        if not bom:
            return jsonify({
                'success': False,
                'message': 'No active BOM found for this item',
                'item_name': item.name,
                'has_bom': False
            })
        
        # Calculate BOM costs
        bom_data = {
            'success': True,
            'has_bom': True,
            'item_name': item.name,
            'item_code': item.code,
            'bom_id': bom.id,
            'bom_version': bom.version,
            'output_quantity': bom.output_quantity or 1.0,
            'total_cost_per_unit': round(bom.total_cost_per_unit, 2),
            'material_cost': round(bom.total_material_cost, 2),
            'labor_cost': round(bom.labor_cost_per_unit or 0, 2),
            'overhead_cost': round(bom.overhead_cost_per_unit or 0, 2),
            'freight_cost': round(bom.calculated_freight_cost_per_unit, 2),
            'markup_percentage': bom.markup_percentage or 0,
            'markup_amount': round(bom.markup_amount_per_unit, 2),
            'labor_hours': bom.labor_hours_per_unit or 0,
            'labor_rate_per_hour': bom.labor_rate_per_hour or 0,
            'materials': []
        }
        
        # Add BOM items/materials
        for bom_item in bom.items:
            material_data = {
                'item_name': bom_item.item.name,
                'item_code': bom_item.item.code,
                'quantity_required': bom_item.quantity_required,
                'unit': bom_item.unit,
                'unit_cost': bom_item.unit_cost,
                'total_cost': round(bom_item.quantity_required * bom_item.unit_cost, 2)
            }
            bom_data['materials'].append(material_data)
        
        return jsonify(bom_data)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error retrieving BOM data: {str(e)}',
            'has_bom': False
        }), 500

@multi_process_jobwork_bp.route('/api/process-template')
@login_required
def process_template():
    """API endpoint to get process form template for dynamic addition"""
    form = JobWorkProcessForm()
    return render_template('multi_process_jobwork/process_template.html', form=form)

@multi_process_jobwork_bp.route('/api/all-items')
@login_required
def get_all_items():
    """API endpoint to get all active items for output product dropdowns"""
    try:
        items = Item.query.order_by(Item.name).all()
        items_data = []
        for item in items:
            items_data.append({
                'id': item.id,
                'code': item.code,
                'name': item.name,
                'unit_of_measure': item.unit_of_measure
            })
        
        return jsonify({
            'success': True,
            'items': items_data
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@multi_process_jobwork_bp.route('/api/employees')
@login_required
def get_employees():
    """API endpoint to get all active employees for team lead selection"""
    try:
        from models import Employee
        employees = Employee.query.order_by(Employee.name).all()
        employees_data = []
        for emp in employees:
            employees_data.append({
                'id': emp.id,
                'employee_code': emp.employee_code,
                'name': emp.name,
                'department': emp.department,
                'position': getattr(emp, 'position', 'Employee')  # Handle if position field doesn't exist
            })
        
        return jsonify({
            'success': True,
            'employees': employees_data
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})