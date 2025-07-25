from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from forms import EmployeeForm, SalaryRecordForm, EmployeeAdvanceForm
from models import Employee, SalaryRecord, EmployeeAdvance, OvertimeRate
from app import db
from sqlalchemy import func, desc
from utils import generate_employee_code
from utils_documents import save_uploaded_documents, get_documents_for_transaction
from datetime import datetime, date
from calendar import monthrange
import os

hr_bp = Blueprint('hr', __name__)

@hr_bp.route('/dashboard')
@login_required
def dashboard():
    # HR statistics
    stats = {
        'total_employees': Employee.query.count(),
        'active_employees': Employee.query.filter_by(is_active=True).count(),
        'daily_rate_employees': Employee.query.filter_by(salary_type='daily', is_active=True).count(),
        'monthly_salary_employees': Employee.query.filter_by(salary_type='monthly', is_active=True).count(),
        'piece_rate_employees': Employee.query.filter_by(salary_type='piece_rate', is_active=True).count(),
        'pending_salaries': SalaryRecord.query.filter_by(status='pending').count(),
        'pending_advances': EmployeeAdvance.query.filter_by(status='pending').count(),
        'total_monthly_advances': db.session.query(func.sum(EmployeeAdvance.remaining_amount)).filter_by(status='active').scalar() or 0
    }
    
    # Recent employees
    recent_employees = Employee.query.filter_by(is_active=True).order_by(Employee.joining_date.desc()).limit(10).all()
    
    # Department summary
    dept_stats = db.session.query(
        Employee.department, 
        func.count(Employee.id).label('emp_count')
    ).filter_by(is_active=True).group_by(Employee.department).all()
    
    # Salary type distribution
    salary_type_stats = db.session.query(
        Employee.salary_type, 
        func.count(Employee.id).label('emp_count')
    ).filter_by(is_active=True).group_by(Employee.salary_type).all()
    
    return render_template('hr/dashboard.html', 
                         stats=stats, 
                         recent_employees=recent_employees,
                         dept_stats=dept_stats,
                         salary_type_stats=salary_type_stats)

@hr_bp.route('/employees')
@login_required
def list_employees():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '', type=str)
    department_filter = request.args.get('department', '', type=str)
    status_filter = request.args.get('status', 'active', type=str)
    
    query = Employee.query
    
    if search:
        query = query.filter(Employee.name.contains(search) | Employee.employee_code.contains(search))
    
    if department_filter:
        query = query.filter_by(department=department_filter)
    
    if status_filter == 'active':
        query = query.filter_by(is_active=True)
    elif status_filter == 'inactive':
        query = query.filter_by(is_active=False)
    
    employees = query.order_by(Employee.name).paginate(
        page=page, per_page=20, error_out=False)
    
    # Get departments for filter dropdown
    departments = db.session.query(Employee.department).distinct().filter(Employee.department.isnot(None)).all()
    departments = [dept[0] for dept in departments if dept[0]]
    
    return render_template('hr/employees.html', 
                         employees=employees, 
                         search=search,
                         department_filter=department_filter,
                         status_filter=status_filter,
                         departments=departments)

@hr_bp.route('/employees/add', methods=['GET', 'POST'])
@login_required
def add_employee():
    form = EmployeeForm()
    
    # Auto-generate employee code for GET request
    if request.method == 'GET':
        form.employee_code.data = generate_employee_code()
    
    if form.validate_on_submit():
        # Check if employee code already exists
        existing_employee = Employee.query.filter_by(employee_code=form.employee_code.data).first()
        if existing_employee:
            flash('Employee code already exists', 'danger')
            return render_template('hr/employee_form.html', form=form, title='Add Employee', get_documents_for_transaction=get_documents_for_transaction)
        
        employee = Employee(
            employee_code=form.employee_code.data,
            name=form.name.data,
            designation=form.designation.data,
            department=form.department.data,
            salary_type=form.salary_type.data,
            rate=form.rate.data,
            phone=form.phone.data,
            address=form.address.data,
            joining_date=form.joining_date.data
        )
        db.session.add(employee)
        db.session.commit()
        
        # Handle document uploads
        documents_uploaded = 0
        if form.documents.data:
            files = request.files.getlist('documents')
            documents_uploaded = save_uploaded_documents(files, 'employee', employee.id)
        
        success_message = f'Employee added successfully'
        if documents_uploaded > 0:
            success_message += f' with {documents_uploaded} document(s) uploaded'
        flash(success_message, 'success')
        return redirect(url_for('hr.list_employees'))
    
    return render_template('hr/employee_form.html', form=form, title='Add Employee', get_documents_for_transaction=get_documents_for_transaction)

@hr_bp.route('/employees/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_employee(id):
    employee = Employee.query.get_or_404(id)
    form = EmployeeForm(obj=employee)
    
    if form.validate_on_submit():
        # Check if employee code already exists (excluding current employee)
        existing_employee = Employee.query.filter(
            Employee.employee_code == form.employee_code.data, 
            Employee.id != id
        ).first()
        if existing_employee:
            flash('Employee code already exists', 'danger')
            return render_template('hr/employee_form.html', form=form, title='Edit Employee', employee=employee, get_documents_for_transaction=get_documents_for_transaction)
        
        employee.employee_code = form.employee_code.data
        employee.name = form.name.data
        employee.designation = form.designation.data
        employee.department = form.department.data
        employee.salary_type = form.salary_type.data
        employee.rate = form.rate.data
        employee.phone = form.phone.data
        employee.address = form.address.data
        employee.joining_date = form.joining_date.data
        
        # Handle document uploads
        documents_uploaded = 0
        if form.documents.data:
            files = request.files.getlist('documents')
            documents_uploaded = save_uploaded_documents(files, 'employee', employee.id)
        
        db.session.commit()
        success_message = f'Employee updated successfully'
        if documents_uploaded > 0:
            success_message += f' with {documents_uploaded} new document(s) uploaded'
        flash(success_message, 'success')
        return redirect(url_for('hr.list_employees'))
    
    return render_template('hr/employee_form.html', form=form, title='Edit Employee', employee=employee, get_documents_for_transaction=get_documents_for_transaction)

@hr_bp.route('/employees/toggle_status/<int:id>')
@login_required
def toggle_employee_status(id):
    if not current_user.is_admin():
        flash('Only administrators can change employee status', 'danger')
        return redirect(url_for('hr.list_employees'))
    
    employee = Employee.query.get_or_404(id)
    employee.is_active = not employee.is_active
    db.session.commit()
    
    status = 'activated' if employee.is_active else 'deactivated'
    flash(f'Employee {status} successfully', 'success')
    return redirect(url_for('hr.list_employees'))

@hr_bp.route('/employees/detail/<int:id>')
@login_required
def employee_detail(id):
    """View employee details with salary and advance history"""
    employee = Employee.query.get_or_404(id)
    
    # Get recent salary records
    recent_salaries = SalaryRecord.query.filter_by(employee_id=id).order_by(desc(SalaryRecord.created_at)).limit(5).all()
    
    # Get recent advances
    recent_advances = EmployeeAdvance.query.filter_by(employee_id=id).order_by(desc(EmployeeAdvance.created_at)).limit(5).all()
    
    # Calculate advance summary
    total_advances = db.session.query(func.sum(EmployeeAdvance.amount)).filter_by(employee_id=id).scalar() or 0
    remaining_advances = db.session.query(func.sum(EmployeeAdvance.remaining_amount)).filter_by(employee_id=id, status='active').scalar() or 0
    
    return render_template('hr/employee_detail.html', 
                         employee=employee,
                         recent_salaries=recent_salaries,
                         recent_advances=recent_advances,
                         total_advances=total_advances,
                         remaining_advances=remaining_advances)

# ============ SALARY RECORDS MANAGEMENT ============

@hr_bp.route('/salaries')
@login_required
def salary_list():
    """List all salary records"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '', type=str)
    status = request.args.get('status', '', type=str)
    month = request.args.get('month', '', type=str)
    
    query = SalaryRecord.query.join(Employee)
    
    if search:
        query = query.filter(Employee.name.contains(search) | Employee.employee_code.contains(search))
    
    if status:
        query = query.filter(SalaryRecord.status == status)
    
    if month:
        try:
            month_start = datetime.strptime(month, '%Y-%m').date()
            month_end = date(month_start.year, month_start.month, monthrange(month_start.year, month_start.month)[1])
            query = query.filter(SalaryRecord.pay_period_start >= month_start, SalaryRecord.pay_period_end <= month_end)
        except ValueError:
            pass
    
    salaries = query.order_by(desc(SalaryRecord.created_at)).paginate(
        page=page, per_page=20, error_out=False
    )
    
    # Calculate totals for current filter
    total_gross = query.with_entities(func.sum(SalaryRecord.gross_amount)).scalar() or 0
    total_net = query.with_entities(func.sum(SalaryRecord.net_amount)).scalar() or 0
    
    return render_template('hr/salary_list.html', 
                         salaries=salaries, 
                         search=search, 
                         status=status, 
                         month=month,
                         total_gross=total_gross,
                         total_net=total_net)

@hr_bp.route('/salaries/add', methods=['GET', 'POST'])
@login_required
def add_salary():
    """Add new salary record"""
    form = SalaryRecordForm()
    form.salary_number.data = SalaryRecord.generate_salary_number()
    
    if form.validate_on_submit():
        try:
            # Calculate amounts
            overtime_amount = form.overtime_hours.data * form.overtime_rate.data
            gross_amount = form.basic_amount.data + overtime_amount + form.bonus_amount.data
            net_amount = gross_amount - form.deduction_amount.data - form.advance_deduction.data
            
            salary = SalaryRecord(
                salary_number=form.salary_number.data,
                employee_id=form.employee_id.data,
                pay_period_start=form.pay_period_start.data,
                pay_period_end=form.pay_period_end.data,
                basic_amount=form.basic_amount.data,
                overtime_hours=form.overtime_hours.data or 0,
                overtime_rate=form.overtime_rate.data or 0,
                overtime_amount=overtime_amount,
                bonus_amount=form.bonus_amount.data or 0,
                deduction_amount=form.deduction_amount.data or 0,
                advance_deduction=form.advance_deduction.data or 0,
                gross_amount=gross_amount,
                net_amount=net_amount,
                payment_method=form.payment_method.data,
                notes=form.notes.data,
                created_by=current_user.id
            )
            
            db.session.add(salary)
            db.session.commit()
            
            flash(f'Salary record {salary.salary_number} created successfully!', 'success')
            return redirect(url_for('hr.salary_detail', id=salary.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating salary record: {str(e)}', 'danger')
    
    return render_template('hr/salary_form.html', form=form, title='Add Salary Record')

@hr_bp.route('/salaries/detail/<int:id>')
@login_required
def salary_detail(id):
    """View salary record details"""
    salary = SalaryRecord.query.get_or_404(id)
    return render_template('hr/salary_detail.html', salary=salary)

@hr_bp.route('/salaries/approve/<int:id>')
@login_required
def approve_salary(id):
    """Approve salary record (Admin only)"""
    if not current_user.is_admin():
        flash('Only administrators can approve salary records', 'danger')
        return redirect(url_for('hr.salary_list'))
    
    salary = SalaryRecord.query.get_or_404(id)
    
    if salary.status != 'pending':
        flash('Salary record is not pending approval', 'warning')
        return redirect(url_for('hr.salary_detail', id=id))
    
    salary.status = 'approved'
    salary.approved_by = current_user.id
    salary.approved_at = datetime.utcnow()
    
    db.session.commit()
    flash(f'Salary record {salary.salary_number} approved successfully!', 'success')
    return redirect(url_for('hr.salary_detail', id=id))

# ============ EMPLOYEE ADVANCES MANAGEMENT ============

@hr_bp.route('/advances')
@login_required
def advance_list():
    """List all employee advances"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '', type=str)
    status = request.args.get('status', '', type=str)
    
    query = EmployeeAdvance.query.join(Employee)
    
    if search:
        query = query.filter(Employee.name.contains(search) | Employee.employee_code.contains(search))
    
    if status:
        query = query.filter(EmployeeAdvance.status == status)
    
    advances = query.order_by(desc(EmployeeAdvance.created_at)).paginate(
        page=page, per_page=20, error_out=False
    )
    
    # Calculate totals
    total_amount = query.with_entities(func.sum(EmployeeAdvance.amount)).scalar() or 0
    total_remaining = query.with_entities(func.sum(EmployeeAdvance.remaining_amount)).scalar() or 0
    
    return render_template('hr/advance_list.html', 
                         advances=advances, 
                         search=search, 
                         status=status,
                         total_amount=total_amount,
                         total_remaining=total_remaining)

@hr_bp.route('/advances/add', methods=['GET', 'POST'])
@login_required
def add_advance():
    """Add new employee advance"""
    form = EmployeeAdvanceForm()
    form.advance_number.data = EmployeeAdvance.generate_advance_number()
    
    if form.validate_on_submit():
        try:
            # Calculate monthly deduction
            monthly_deduction = form.amount.data / form.repayment_months.data
            
            advance = EmployeeAdvance(
                advance_number=form.advance_number.data,
                employee_id=form.employee_id.data,
                amount=form.amount.data,
                remaining_amount=form.amount.data,  # Initially full amount
                reason=form.reason.data,
                advance_date=form.advance_date.data,
                repayment_months=form.repayment_months.data,
                monthly_deduction=monthly_deduction,
                payment_method=form.payment_method.data,
                notes=form.notes.data,
                requested_by=current_user.id
            )
            
            db.session.add(advance)
            db.session.commit()
            
            flash(f'Advance request {advance.advance_number} created successfully!', 'success')
            return redirect(url_for('hr.advance_detail', id=advance.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating advance request: {str(e)}', 'danger')
    
    return render_template('hr/advance_form.html', form=form, title='Add Employee Advance')

@hr_bp.route('/advances/detail/<int:id>')
@login_required
def advance_detail(id):
    """View advance details"""
    advance = EmployeeAdvance.query.get_or_404(id)
    return render_template('hr/advance_detail.html', advance=advance)

@hr_bp.route('/advances/approve/<int:id>')
@login_required
def approve_advance(id):
    """Approve employee advance (Admin only)"""
    if not current_user.is_admin():
        flash('Only administrators can approve advances', 'danger')
        return redirect(url_for('hr.advance_list'))

# ============ API ENDPOINTS ============

@hr_bp.route('/api/employee/<int:employee_id>/overtime-rate')
@login_required
def get_employee_overtime_rate(employee_id):
    """Get overtime rate for employee based on their salary type"""
    employee = Employee.query.get_or_404(employee_id)
    overtime_rate = OvertimeRate.get_rate_for_salary_type(employee.salary_type)
    
    return jsonify({
        'employee_id': employee_id,
        'salary_type': employee.salary_type,
        'overtime_rate': overtime_rate
    })
    
    if advance.status != 'pending':
        flash('Advance is not pending approval', 'warning')
        return redirect(url_for('hr.advance_detail', id=id))
    
    advance.status = 'approved'
    advance.approved_by = current_user.id
    advance.approved_at = datetime.utcnow()
    
    db.session.commit()
    flash(f'Advance {advance.advance_number} approved successfully!', 'success')
    return redirect(url_for('hr.advance_detail', id=id))
