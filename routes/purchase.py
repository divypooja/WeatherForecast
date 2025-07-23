from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from forms import PurchaseOrderForm, SupplierForm
from models import PurchaseOrder, PurchaseOrderItem, Supplier, Item, DeliverySchedule, CompanySettings
from app import db
from sqlalchemy import func
from datetime import datetime
from utils import generate_po_number

purchase_bp = Blueprint('purchase', __name__)

@purchase_bp.route('/dashboard')
@login_required
def dashboard():
    # Purchase statistics
    stats = {
        'total_pos': PurchaseOrder.query.count(),
        'open_pos': PurchaseOrder.query.filter_by(status='open').count(),
        'partial_pos': PurchaseOrder.query.filter_by(status='partial').count(),
        'closed_pos': PurchaseOrder.query.filter_by(status='closed').count(),
        'total_suppliers': Supplier.query.count()
    }
    
    # Recent purchase orders
    recent_pos = PurchaseOrder.query.order_by(PurchaseOrder.created_at.desc()).limit(10).all()
    
    # Top suppliers by order count
    top_suppliers = db.session.query(
        Supplier.name, 
        func.count(PurchaseOrder.id).label('order_count')
    ).join(PurchaseOrder).group_by(Supplier.id).order_by(func.count(PurchaseOrder.id).desc()).limit(5).all()
    
    return render_template('purchase/dashboard.html', 
                         stats=stats, 
                         recent_pos=recent_pos,
                         top_suppliers=top_suppliers)

@purchase_bp.route('/list')
@login_required
def list_purchase_orders():
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', '', type=str)
    
    query = PurchaseOrder.query
    if status_filter:
        query = query.filter_by(status=status_filter)
    
    pos = query.order_by(PurchaseOrder.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False)
    
    return render_template('purchase/list.html', pos=pos, status_filter=status_filter)

@purchase_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_purchase_order():
    form = PurchaseOrderForm()
    form.supplier_id.choices = [(s.id, s.name) for s in Supplier.query.all()]
    
    # Auto-generate PO number if not provided
    if not form.po_number.data:
        form.po_number.data = generate_po_number()
    
    if form.validate_on_submit():
        # Check if PO number already exists
        existing_po = PurchaseOrder.query.filter_by(po_number=form.po_number.data).first()
        if existing_po:
            flash('PO number already exists', 'danger')
            return render_template('purchase/form.html', form=form, title='Add Purchase Order')
        
        po = PurchaseOrder(
            po_number=form.po_number.data,
            supplier_id=form.supplier_id.data,
            order_date=form.order_date.data,
            expected_date=form.expected_delivery.data,
            payment_terms=form.payment_terms.data,
            freight_terms=form.freight_terms.data,
            delivery_notes=form.delivery_notes.data,
            validity_months=form.validity_months.data,
            prepared_by=form.prepared_by.data,
            verified_by=form.verified_by.data,
            approved_by=form.approved_by.data,
            notes=form.notes.data,
            created_by=current_user.id
        )
        db.session.add(po)
        db.session.commit()
        flash('Purchase Order created successfully', 'success')
        return redirect(url_for('purchase.edit_purchase_order', id=po.id))
    
    return render_template('purchase/form.html', form=form, title='Add Purchase Order')

@purchase_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_purchase_order(id):
    po = PurchaseOrder.query.get_or_404(id)
    form = PurchaseOrderForm(obj=po)
    form.supplier_id.choices = [(s.id, s.name) for s in Supplier.query.all()]
    
    if form.validate_on_submit():
        # Check if PO number already exists (excluding current PO)
        existing_po = PurchaseOrder.query.filter(
            PurchaseOrder.po_number == form.po_number.data, 
            PurchaseOrder.id != id
        ).first()
        if existing_po:
            flash('PO number already exists', 'danger')
            return render_template('purchase/form.html', form=form, title='Edit Purchase Order', po=po)
        
        po.po_number = form.po_number.data
        po.supplier_id = form.supplier_id.data
        po.order_date = form.order_date.data
        po.expected_date = form.expected_delivery.data
        po.payment_terms = form.payment_terms.data
        po.freight_terms = form.freight_terms.data
        po.delivery_notes = form.delivery_notes.data
        po.validity_months = form.validity_months.data
        po.prepared_by = form.prepared_by.data
        po.verified_by = form.verified_by.data
        po.approved_by = form.approved_by.data
        po.notes = form.notes.data
        
        db.session.commit()
        flash('Purchase Order updated successfully', 'success')
        return redirect(url_for('purchase.list_purchase_orders'))
    
    # Get PO items for display
    po_items = PurchaseOrderItem.query.filter_by(purchase_order_id=id).all()
    items = Item.query.all()
    
    return render_template('purchase/form.html', 
                         form=form, 
                         title='Edit Purchase Order', 
                         po=po, 
                         po_items=po_items, 
                         items=items)

@purchase_bp.route('/suppliers')
@login_required
def list_suppliers():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '', type=str)
    
    query = Supplier.query
    if search:
        query = query.filter(Supplier.name.contains(search))
    
    suppliers = query.order_by(Supplier.name).paginate(
        page=page, per_page=20, error_out=False)
    
    return render_template('purchase/suppliers.html', suppliers=suppliers, search=search)

@purchase_bp.route('/suppliers/add', methods=['GET', 'POST'])
@login_required
def add_supplier():
    form = SupplierForm()
    if form.validate_on_submit():
        supplier = Supplier(
            name=form.name.data,
            contact_person=form.contact_person.data,
            phone=form.phone.data,
            email=form.email.data,
            address=form.address.data,
            gst_number=form.gst_number.data
        )
        db.session.add(supplier)
        db.session.commit()
        flash('Supplier added successfully', 'success')
        return redirect(url_for('purchase.list_suppliers'))
    
    return render_template('purchase/supplier_form.html', form=form, title='Add Supplier')

@purchase_bp.route('/suppliers/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_supplier(id):
    supplier = Supplier.query.get_or_404(id)
    form = SupplierForm(obj=supplier)
    
    if form.validate_on_submit():
        supplier.name = form.name.data
        supplier.contact_person = form.contact_person.data
        supplier.phone = form.phone.data
        supplier.email = form.email.data
        supplier.address = form.address.data
        supplier.gst_number = form.gst_number.data
        
        db.session.commit()
        flash('Supplier updated successfully', 'success')
        return redirect(url_for('purchase.list_suppliers'))
    
    return render_template('purchase/supplier_form.html', form=form, title='Edit Supplier', supplier=supplier)

@purchase_bp.route('/suppliers/delete/<int:id>', methods=['POST', 'GET'])
@login_required
def delete_supplier(id):
    supplier = Supplier.query.get_or_404(id)
    
    # Check if supplier has any purchase orders
    if supplier.purchase_orders:
        flash('Cannot delete supplier with existing purchase orders', 'danger')
        return redirect(url_for('purchase.list_suppliers'))
    
    db.session.delete(supplier)
    db.session.commit()
    flash('Supplier deleted successfully', 'success')
    return redirect(url_for('purchase.list_suppliers'))

@purchase_bp.route('/print/<int:id>')
@login_required  
def print_purchase_order(id):
    po = PurchaseOrder.query.get_or_404(id)
    
    # Convert total amount to words (simple function)
    def number_to_words(num):
        ones = ["", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten",
                "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen", "seventeen", 
                "eighteen", "nineteen"]
        tens = ["", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety"]
        
        if num == 0:
            return "zero"
        
        if num < 20:
            return ones[num]
        elif num < 100:
            return tens[num // 10] + (" " + ones[num % 10] if num % 10 != 0 else "")
        elif num < 1000:
            return ones[num // 100] + " hundred" + (" " + number_to_words(num % 100) if num % 100 != 0 else "")
        elif num < 100000:
            return number_to_words(num // 1000) + " thousand" + (" " + number_to_words(num % 1000) if num % 1000 != 0 else "")
        elif num < 10000000:
            return number_to_words(num // 100000) + " lakh" + (" " + number_to_words(num % 100000) if num % 100000 != 0 else "")
        else:
            return number_to_words(num // 10000000) + " crore" + (" " + number_to_words(num % 10000000) if num % 10000000 != 0 else "")
    
    amount_words = number_to_words(int(po.total_amount))
    company = CompanySettings.get_settings()
    
    return render_template('purchase/po_print_enhanced.html', po=po, amount_words=amount_words, company=company)

@purchase_bp.route('/delete/<int:id>', methods=['POST', 'GET'])
@login_required
def delete_purchase_order(id):
    po = PurchaseOrder.query.get_or_404(id)
    
    # Check if user has permission (only admin or creator can delete)
    if not current_user.is_admin() and po.created_by != current_user.id:
        flash('You do not have permission to delete this purchase order', 'danger')
        return redirect(url_for('purchase.list_purchase_orders'))
    
    # Delete related items first
    PurchaseOrderItem.query.filter_by(purchase_order_id=id).delete()
    DeliverySchedule.query.filter_by(purchase_order_id=id).delete()
    
    db.session.delete(po)
    db.session.commit()
    flash('Purchase Order deleted successfully', 'success')
    return redirect(url_for('purchase.list_purchase_orders'))
