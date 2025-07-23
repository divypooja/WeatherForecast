from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from forms import SalesOrderForm, SupplierForm
from models import SalesOrder, SalesOrderItem, Supplier, Item
from app import db
from sqlalchemy import func
from utils import generate_so_number

sales_bp = Blueprint('sales', __name__)

@sales_bp.route('/dashboard')
@login_required
def dashboard():
    # Sales statistics
    stats = {
        'total_sos': SalesOrder.query.count(),
        'pending_sos': SalesOrder.query.filter_by(status='pending').count(),
        'partial_sos': SalesOrder.query.filter_by(status='partial').count(),
        'completed_sos': SalesOrder.query.filter_by(status='completed').count(),
        'total_customers': Supplier.query.filter(Supplier.partner_type.in_(['customer', 'both'])).count()
    }
    
    # Recent sales orders
    recent_sos = SalesOrder.query.order_by(SalesOrder.created_at.desc()).limit(10).all()
    
    # Top customers by order count
    top_customers = db.session.query(
        Supplier.name, 
        func.count(SalesOrder.id).label('order_count')
    ).join(SalesOrder).filter(Supplier.partner_type.in_(['customer', 'both'])).group_by(Supplier.id).order_by(func.count(SalesOrder.id).desc()).limit(5).all()
    
    return render_template('sales/dashboard.html', 
                         stats=stats, 
                         recent_sos=recent_sos,
                         top_customers=top_customers)

@sales_bp.route('/list')
@login_required
def list_sales_orders():
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', '', type=str)
    
    query = SalesOrder.query
    if status_filter:
        query = query.filter_by(status=status_filter)
    
    sos = query.order_by(SalesOrder.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False)
    
    return render_template('sales/list.html', sos=sos, status_filter=status_filter)

@sales_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_sales_order():
    form = SalesOrderForm()
    form.customer_id.choices = [(c.id, c.name) for c in Supplier.query.filter(Supplier.partner_type.in_(['customer', 'both']), Supplier.is_active == True).all()]
    
    # Auto-generate SO number if not provided
    if not form.so_number.data:
        form.so_number.data = generate_so_number()
    
    if form.validate_on_submit():
        # Check if SO number already exists
        existing_so = SalesOrder.query.filter_by(so_number=form.so_number.data).first()
        if existing_so:
            flash('SO number already exists', 'danger')
            return render_template('sales/form.html', form=form, title='Add Sales Order')
        
        so = SalesOrder(
            so_number=form.so_number.data,
            customer_id=form.customer_id.data,
            order_date=form.order_date.data,
            delivery_date=form.delivery_date.data,
            notes=form.notes.data,
            created_by=current_user.id
        )
        db.session.add(so)
        db.session.commit()
        flash('Sales Order created successfully', 'success')
        return redirect(url_for('sales.edit_sales_order', id=so.id))
    
    return render_template('sales/form.html', form=form, title='Add Sales Order')

@sales_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_sales_order(id):
    so = SalesOrder.query.get_or_404(id)
    form = SalesOrderForm(obj=so)
    form.customer_id.choices = [(c.id, c.name) for c in Supplier.query.filter(Supplier.partner_type.in_(['customer', 'both']), Supplier.is_active == True).all()]
    
    if form.validate_on_submit():
        # Check if SO number already exists (excluding current SO)
        existing_so = SalesOrder.query.filter(
            SalesOrder.so_number == form.so_number.data, 
            SalesOrder.id != id
        ).first()
        if existing_so:
            flash('SO number already exists', 'danger')
            return render_template('sales/form.html', form=form, title='Edit Sales Order', so=so)
        
        so.so_number = form.so_number.data
        so.customer_id = form.customer_id.data
        so.order_date = form.order_date.data
        so.delivery_date = form.delivery_date.data
        so.notes = form.notes.data
        
        db.session.commit()
        flash('Sales Order updated successfully', 'success')
        return redirect(url_for('sales.list_sales_orders'))
    
    # Get SO items for display
    so_items = SalesOrderItem.query.filter_by(sales_order_id=id).all()
    items = Item.query.all()
    
    return render_template('sales/form.html', 
                         form=form, 
                         title='Edit Sales Order', 
                         so=so, 
                         so_items=so_items, 
                         items=items)

@sales_bp.route('/customers')
@login_required
def list_customers():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '', type=str)
    
    query = Supplier.query.filter(Supplier.partner_type.in_(['customer', 'both']))
    if search:
        query = query.filter(Supplier.name.contains(search))
    
    customers = query.order_by(Supplier.name).paginate(
        page=page, per_page=20, error_out=False)
    
    return render_template('sales/customers.html', customers=customers, search=search)

@sales_bp.route('/customers/add', methods=['GET', 'POST'])
@login_required
def add_customer():
    # Redirect to unified business partner form with customer type
    return redirect(url_for('purchase.add_supplier', partner_type='customer'))

@sales_bp.route('/customers/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_customer(id):
    # Redirect to unified business partner edit form
    return redirect(url_for('purchase.edit_supplier', id=id))

@sales_bp.route('/customers/delete/<int:id>', methods=['POST', 'GET'])
@login_required
def delete_customer(id):
    # Redirect to unified business partner delete
    return redirect(url_for('purchase.delete_supplier', id=id))

@sales_bp.route('/delete/<int:id>', methods=['POST', 'GET'])
@login_required
def delete_sales_order(id):
    so = SalesOrder.query.get_or_404(id)
    
    # Check if user has permission (only admin or creator can delete)
    if not current_user.is_admin() and so.created_by != current_user.id:
        flash('You do not have permission to delete this sales order', 'danger')
        return redirect(url_for('sales.list_sales_orders'))
    
    # Delete related items first
    SalesOrderItem.query.filter_by(sales_order_id=id).delete()
    
    db.session.delete(so)
    db.session.commit()
    flash('Sales Order deleted successfully', 'success')
    return redirect(url_for('sales.list_sales_orders'))
