from flask import Blueprint, render_template, redirect, url_for, flash, request, make_response
from flask_login import login_required, current_user
from models import Item, PurchaseOrder, SalesOrder, Employee, JobWork, Production
from app import db
from sqlalchemy import func, and_
from datetime import datetime, date, timedelta
import csv
import io

reports_bp = Blueprint('reports', __name__)

@reports_bp.route('/dashboard')
@login_required
def dashboard():
    # Report generation options and recent exports
    report_types = [
        {'name': 'Inventory Report', 'url': 'reports.inventory_report'},
        {'name': 'Purchase Orders Report', 'url': 'reports.purchase_report'},
        {'name': 'Sales Orders Report', 'url': 'reports.sales_report'},
        {'name': 'Employee Report', 'url': 'reports.employee_report'},
        {'name': 'Job Work Report', 'url': 'reports.jobwork_report'},
        {'name': 'Production Report', 'url': 'reports.production_report'}
    ]
    
    return render_template('reports/dashboard.html', report_types=report_types)

@reports_bp.route('/inventory')
@login_required
def inventory_report():
    # Get inventory data with filters
    item_type_filter = request.args.get('item_type', '', type=str)
    low_stock_only = request.args.get('low_stock', False, type=bool)
    
    query = Item.query
    
    if item_type_filter:
        query = query.filter_by(item_type=item_type_filter)
    
    if low_stock_only:
        query = query.filter(db.func.coalesce(Item.current_stock, 0) <= db.func.coalesce(Item.minimum_stock, 0))
    
    items = query.order_by(Item.name).all()
    
    # Calculate totals
    total_items = len(items)
    total_stock_value = sum((item.current_stock or 0) * (item.unit_price or 0) for item in items)
    low_stock_count = len([item for item in items if (item.current_stock or 0) <= (item.minimum_stock or 0)])
    
    # Add pagination support
    page = request.args.get('page', 1, type=int)
    items_paginated = query.paginate(page=page, per_page=50, error_out=False)
    
    # Calculate additional stats
    all_items = Item.query.all()
    total_value = sum((item.current_stock or 0) * (item.unit_price or 0) for item in all_items)
    out_of_stock_count = len([item for item in all_items if (item.current_stock or 0) == 0])
    
    return render_template('reports/inventory_report.html', 
                         items=items_paginated,
                         total_items=total_items,
                         total_value=total_value,
                         low_stock_count=low_stock_count,
                         out_of_stock_count=out_of_stock_count,
                         item_type_filter=item_type_filter,
                         low_stock_only=low_stock_only)

@reports_bp.route('/inventory/export')
@login_required
def export_inventory():
    # Get same data as inventory report
    item_type_filter = request.args.get('item_type', '', type=str)
    low_stock_only = request.args.get('low_stock', False, type=bool)
    
    query = Item.query
    
    if item_type_filter:
        query = query.filter_by(item_type=item_type_filter)
    
    if low_stock_only:
        query = query.filter(db.func.coalesce(Item.current_stock, 0) <= db.func.coalesce(Item.minimum_stock, 0))
    
    items = query.order_by(Item.name).all()
    
    # Create CSV
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow(['Item Code', 'Item Name', 'Description', 'UOM', 'Current Stock', 
                    'Minimum Stock', 'Unit Price', 'Stock Value', 'Item Type'])
    
    # Write data
    for item in items:
        stock_value = (item.current_stock or 0) * (item.unit_price or 0)
        writer.writerow([item.code, item.name, item.description or '', item.unit_of_measure,
                        item.current_stock, item.minimum_stock, item.unit_price, 
                        stock_value, item.item_type])
    
    # Create response
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = f'attachment; filename=inventory_report_{date.today()}.csv'
    
    return response

@reports_bp.route('/purchase')
@login_required
def purchase_report():
    # Date filters
    start_date = request.args.get('start_date', '', type=str)
    end_date = request.args.get('end_date', '', type=str)
    status_filter = request.args.get('status', '', type=str)
    
    query = PurchaseOrder.query
    
    if start_date:
        start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
        query = query.filter(PurchaseOrder.order_date >= start_date_obj)
    
    if end_date:
        end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
        query = query.filter(PurchaseOrder.order_date <= end_date_obj)
    
    if status_filter:
        query = query.filter_by(status=status_filter)
    
    purchase_orders = query.order_by(PurchaseOrder.order_date.desc()).all()
    
    # Calculate totals
    total_orders = len(purchase_orders)
    total_amount = sum(po.total_amount for po in purchase_orders)
    
    return render_template('reports/purchase_report.html',
                         purchase_orders=purchase_orders,
                         total_orders=total_orders,
                         total_amount=total_amount,
                         start_date=start_date,
                         end_date=end_date,
                         status_filter=status_filter)

@reports_bp.route('/sales')
@login_required
def sales_report():
    # Date filters
    start_date = request.args.get('start_date', '', type=str)
    end_date = request.args.get('end_date', '', type=str)
    status_filter = request.args.get('status', '', type=str)
    
    query = SalesOrder.query
    
    if start_date:
        start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
        query = query.filter(SalesOrder.order_date >= start_date_obj)
    
    if end_date:
        end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
        query = query.filter(SalesOrder.order_date <= end_date_obj)
    
    if status_filter:
        query = query.filter_by(status=status_filter)
    
    sales_orders = query.order_by(SalesOrder.order_date.desc()).all()
    
    # Calculate totals
    total_orders = len(sales_orders)
    total_amount = sum(so.total_amount for so in sales_orders)
    
    return render_template('reports/sales_report.html',
                         sales_orders=sales_orders,
                         total_orders=total_orders,
                         total_amount=total_amount,
                         start_date=start_date,
                         end_date=end_date,
                         status_filter=status_filter)

@reports_bp.route('/employee')
@login_required
def employee_report():
    # Employee filters
    department_filter = request.args.get('department', '', type=str)
    salary_type_filter = request.args.get('salary_type', '', type=str)
    status_filter = request.args.get('status', 'active', type=str)
    
    query = Employee.query
    
    if department_filter:
        query = query.filter_by(department=department_filter)
    
    if salary_type_filter:
        query = query.filter_by(salary_type=salary_type_filter)
    
    if status_filter == 'active':
        query = query.filter_by(is_active=True)
    elif status_filter == 'inactive':
        query = query.filter_by(is_active=False)
    
    employees = query.order_by(Employee.name).all()
    
    # Get departments and salary types for filters
    departments = db.session.query(Employee.department).distinct().filter(Employee.department.isnot(None)).all()
    departments = [dept[0] for dept in departments if dept[0]]
    
    salary_types = ['daily', 'monthly', 'piece_rate']
    
    return render_template('reports/employee_report.html',
                         employees=employees,
                         departments=departments,
                         salary_types=salary_types,
                         department_filter=department_filter,
                         salary_type_filter=salary_type_filter,
                         status_filter=status_filter)

@reports_bp.route('/jobwork')
@login_required
def jobwork_report():
    # Date and status filters
    start_date = request.args.get('start_date', '', type=str)
    end_date = request.args.get('end_date', '', type=str)
    status_filter = request.args.get('status', '', type=str)
    
    query = JobWork.query
    
    if start_date:
        start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
        query = query.filter(JobWork.sent_date >= start_date_obj)
    
    if end_date:
        end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
        query = query.filter(JobWork.sent_date <= end_date_obj)
    
    if status_filter:
        query = query.filter_by(status=status_filter)
    
    job_works = query.order_by(JobWork.sent_date.desc()).all()
    
    return render_template('reports/jobwork_report.html',
                         job_works=job_works,
                         start_date=start_date,
                         end_date=end_date,
                         status_filter=status_filter)

@reports_bp.route('/production')
@login_required
def production_report():
    # Date and status filters
    start_date = request.args.get('start_date', '', type=str)
    end_date = request.args.get('end_date', '', type=str)
    status_filter = request.args.get('status', '', type=str)
    
    query = Production.query
    
    if start_date:
        start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
        query = query.filter(Production.production_date >= start_date_obj)
    
    if end_date:
        end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
        query = query.filter(Production.production_date <= end_date_obj)
    
    if status_filter:
        query = query.filter_by(status=status_filter)
    
    productions = query.order_by(Production.production_date.desc()).all()
    
    return render_template('reports/production_report.html',
                         productions=productions,
                         start_date=start_date,
                         end_date=end_date,
                         status_filter=status_filter)
