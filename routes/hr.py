from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from forms import EmployeeForm
from models import Employee
from app import db
from sqlalchemy import func

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
        'piece_rate_employees': Employee.query.filter_by(salary_type='piece_rate', is_active=True).count()
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
    if form.validate_on_submit():
        # Check if employee code already exists
        existing_employee = Employee.query.filter_by(employee_code=form.employee_code.data).first()
        if existing_employee:
            flash('Employee code already exists', 'danger')
            return render_template('hr/employee_form.html', form=form, title='Add Employee')
        
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
        flash('Employee added successfully', 'success')
        return redirect(url_for('hr.list_employees'))
    
    return render_template('hr/employee_form.html', form=form, title='Add Employee')

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
            return render_template('hr/employee_form.html', form=form, title='Edit Employee', employee=employee)
        
        employee.employee_code = form.employee_code.data
        employee.name = form.name.data
        employee.designation = form.designation.data
        employee.department = form.department.data
        employee.salary_type = form.salary_type.data
        employee.rate = form.rate.data
        employee.phone = form.phone.data
        employee.address = form.address.data
        employee.joining_date = form.joining_date.data
        
        db.session.commit()
        flash('Employee updated successfully', 'success')
        return redirect(url_for('hr.list_employees'))
    
    return render_template('hr/employee_form.html', form=form, title='Edit Employee', employee=employee)

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
