from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, make_response
from flask_login import login_required, current_user
from forms import SalesOrderForm, SupplierForm
from models import SalesOrder, SalesOrderItem, Supplier, Item, BOMItem, CompanySettings
from app import db
from sqlalchemy import func
from datetime import datetime
from utils import generate_so_number
from utils_documents import get_documents_for_transaction

sales_bp = Blueprint('sales', __name__)

def deduct_inventory_for_sales_order(sales_order):
    """
    Deduct inventory when sales order is confirmed.
    Returns dict with 'success' and 'message' keys.
    """
    try:
        insufficient_items = []
        
        # Check all items first before deducting anything
        for so_item in sales_order.items:
            item = so_item.item
            if item.current_stock < so_item.quantity_ordered:
                insufficient_items.append({
                    'item_name': item.name,
                    'required': so_item.quantity_ordered,
                    'available': item.current_stock
                })
        
        # If any items have insufficient stock, return error
        if insufficient_items:
            message = "Insufficient stock for the following items: "
            for insufficient in insufficient_items:
                message += f"{insufficient['item_name']} (Required: {insufficient['required']}, Available: {insufficient['available']}), "
            return {'success': False, 'message': message.rstrip(', ')}
        
        # All items have sufficient stock, proceed with deduction
        for so_item in sales_order.items:
            item = so_item.item
            item.current_stock -= so_item.quantity_ordered
            
        return {'success': True, 'message': f'Inventory deducted for Sales Order {sales_order.so_number}'}
        
    except Exception as e:
        return {'success': False, 'message': f'Error deducting inventory: {str(e)}'}

def restore_inventory_for_sales_order(sales_order):
    """
    Restore inventory when sales order is cancelled or status changed from confirmed.
    """
    try:
        for so_item in sales_order.items:
            item = so_item.item
            item.current_stock += so_item.quantity_ordered
            
        flash(f'Inventory restored for Sales Order {sales_order.so_number}', 'info')
        
    except Exception as e:
        flash(f'Error restoring inventory: {str(e)}', 'danger')

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
    customer_filter = request.args.get('customer', '', type=str)
    from_date = request.args.get('from_date', '', type=str)
    to_date = request.args.get('to_date', '', type=str)
    search_term = request.args.get('search', '', type=str)
    
    query = SalesOrder.query
    
    # Apply filters
    if status_filter:
        query = query.filter_by(status=status_filter)
        
    if customer_filter:
        query = query.filter_by(customer_id=customer_filter)
        
    if from_date:
        try:
            from datetime import datetime
            from_date_obj = datetime.strptime(from_date, '%Y-%m-%d').date()
            query = query.filter(SalesOrder.order_date >= from_date_obj)
        except ValueError:
            flash('Invalid from date format', 'error')
            
    if to_date:
        try:
            from datetime import datetime
            to_date_obj = datetime.strptime(to_date, '%Y-%m-%d').date()
            query = query.filter(SalesOrder.order_date <= to_date_obj)
        except ValueError:
            flash('Invalid to date format', 'error')
            
    if search_term:
        query = query.filter(SalesOrder.so_number.ilike(f'%{search_term}%'))
    
    # Order by date descending and paginate
    sos = query.order_by(SalesOrder.order_date.desc()).paginate(
        page=page, per_page=20, error_out=False)
    
    # Get all customers for filter dropdown
    customers = Supplier.query.filter(Supplier.partner_type.in_(['customer', 'both'])).order_by(Supplier.name).all()
    
    return render_template('sales/list.html', 
                         sos=sos, 
                         status_filter=status_filter,
                         customer_filter=customer_filter,
                         from_date=from_date,
                         to_date=to_date,
                         search_term=search_term,
                         customers=customers)

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
            items = Item.query.all()
            return render_template('sales/form.html', form=form, title='Add Sales Order', items=items)
        
        so = SalesOrder(
            so_number=form.so_number.data,
            customer_id=form.customer_id.data,
            order_date=form.order_date.data,
            delivery_date=form.delivery_date.data,
            payment_terms=form.payment_terms.data,
            freight_terms=form.freight_terms.data,
            validity_months=form.validity_months.data,
            prepared_by=form.prepared_by.data,
            verified_by=form.verified_by.data,
            approved_by=form.approved_by.data,
            delivery_notes=form.delivery_notes.data,
            notes=form.notes.data,
            status='draft',  # New sales orders always start as draft
            created_by=current_user.id
        )
        db.session.add(so)
        db.session.flush()  # Get the SO ID
        
        # Create accounting entries for SO booking
        from services.accounting_automation import AccountingAutomation
        accounting_result = AccountingAutomation.create_sales_order_voucher(so)
        
        db.session.commit()
        
        if accounting_result:
            flash('Sales Order created successfully with accounting entries', 'success')
        else:
            flash('Sales Order created successfully but accounting integration failed', 'warning')
        
        return redirect(url_for('sales.submission_success', so_id=so.id))
    
    # Get items with BOM rates for the items section
    items = db.session.query(Item).outerjoin(
        BOMItem, Item.id == BOMItem.item_id
    ).add_columns(
        BOMItem.unit_cost.label('bom_rate')
    ).all()
    
    # Convert to list of Item objects with bom_rate attribute
    enhanced_items = []
    for item, bom_rate in items:
        item.bom_rate = bom_rate if bom_rate is not None else item.unit_price
        enhanced_items.append(item)
    
    return render_template('sales/form.html', form=form, title='Add Sales Order', items=enhanced_items)

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
            so_items = SalesOrderItem.query.filter_by(sales_order_id=id).all()
            # Get items with BOM rates
            items = db.session.query(Item).outerjoin(
                BOMItem, Item.id == BOMItem.item_id
            ).add_columns(
                BOMItem.unit_cost.label('bom_rate')
            ).all()
            
            # Convert to list of Item objects with bom_rate attribute
            enhanced_items = []
            for item, bom_rate in items:
                item.bom_rate = bom_rate if bom_rate is not None else item.unit_price
                enhanced_items.append(item)
            
            return render_template('sales/form.html', form=form, title='Edit Sales Order', so=so, so_items=so_items, items=enhanced_items)
        
        so.so_number = form.so_number.data
        so.customer_id = form.customer_id.data
        so.order_date = form.order_date.data
        so.delivery_date = form.delivery_date.data
        so.payment_terms = form.payment_terms.data
        so.freight_terms = form.freight_terms.data
        so.validity_months = form.validity_months.data
        so.prepared_by = form.prepared_by.data
        so.verified_by = form.verified_by.data
        so.approved_by = form.approved_by.data
        so.delivery_notes = form.delivery_notes.data
        so.notes = form.notes.data
        
        # Check if status changed to 'confirmed' to trigger inventory deduction
        old_status = so.status
        so.status = form.status.data
        
        # Import accounting automation
        from services.accounting_automation import AccountingAutomation
        
        # If status changed from any status to 'confirmed', deduct inventory
        if old_status != 'confirmed' and so.status == 'confirmed':
            inventory_deduction_result = deduct_inventory_for_sales_order(so)
            if not inventory_deduction_result['success']:
                flash(f'Cannot confirm sales order: {inventory_deduction_result["message"]}', 'danger')
                so_items = SalesOrderItem.query.filter_by(sales_order_id=id).all()
                # Get items with BOM rates
                items = db.session.query(Item).outerjoin(
                    BOMItem, Item.id == BOMItem.item_id
                ).add_columns(
                    BOMItem.unit_cost.label('bom_rate')
                ).all()
                
                # Convert to list of Item objects with bom_rate attribute
                enhanced_items = []
                for item, bom_rate in items:
                    item.bom_rate = bom_rate if bom_rate is not None else item.unit_price
                    enhanced_items.append(item)
                
                return render_template('sales/form.html', form=form, title='Edit Sales Order', so=so, so_items=so_items, items=enhanced_items)
        
        # If status changed from 'confirmed' to another status, restore inventory
        elif old_status == 'confirmed' and so.status != 'confirmed':
            restore_inventory_for_sales_order(so)
        
        # Handle accounting status transitions
        if old_status != so.status:
            if so.status == 'delivered':
                # Create sales voucher for revenue recognition
                AccountingAutomation.create_sales_delivery_voucher(so)
            elif so.status == 'cancelled':
                # Close sales order voucher
                AccountingAutomation.close_sales_order_voucher(so)
        
        db.session.commit()
        flash('Sales Order updated successfully', 'success')
        return redirect(url_for('sales.list_sales_orders'))
    
    # Get SO items for display
    so_items = SalesOrderItem.query.filter_by(sales_order_id=id).all()
    
    # Get items with BOM rates for display
    items = db.session.query(Item).outerjoin(
        BOMItem, Item.id == BOMItem.item_id
    ).add_columns(
        BOMItem.unit_cost.label('bom_rate')
    ).all()
    
    # Convert to list of Item objects with bom_rate attribute
    enhanced_items = []
    for item, bom_rate in items:
        item.bom_rate = bom_rate if bom_rate is not None else item.unit_price
        enhanced_items.append(item)
    
    return render_template('sales/form.html', 
                         form=form, 
                         title='Edit Sales Order', 
                         so=so, 
                         so_items=so_items, 
                         items=enhanced_items)

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

@sales_bp.route('/change_status/<int:so_id>', methods=['POST'])
@login_required
def change_so_status(so_id):
    # Only admins can change status
    if current_user.role != 'admin':
        return jsonify({'success': False, 'message': 'Only admins can change sales order status'})
    
    so = SalesOrder.query.get_or_404(so_id)
    new_status = request.form.get('status')
    
    # Validate status
    valid_statuses = ['draft', 'pending', 'confirmed', 'shipped', 'delivered', 'cancelled']
    if new_status not in valid_statuses:
        return jsonify({'success': False, 'message': 'Invalid status'})
    
    old_status = so.status
    so.status = new_status
    db.session.commit()
    
    return jsonify({
        'success': True, 
        'message': f'Sales Order {so.so_number} status changed from {old_status.title()} to {new_status.title()}'
    })

@sales_bp.route('/add_item/<int:so_id>', methods=['POST'])
@login_required
def add_sales_order_item(so_id):
    """Add an item to a sales order"""
    from flask import jsonify
    
    so = SalesOrder.query.get_or_404(so_id)
    
    try:
        item_id = int(request.form.get('item_id'))
        quantity = float(request.form.get('quantity'))
        unit_price = float(request.form.get('unit_price'))
        
        item = Item.query.get_or_404(item_id)
        total_price = quantity * unit_price
        
        # Check if item already exists in this SO
        existing_item = SalesOrderItem.query.filter_by(
            sales_order_id=so_id, 
            item_id=item_id
        ).first()
        
        if existing_item:
            # Update existing item
            existing_item.quantity_ordered += quantity
            existing_item.total_price = existing_item.quantity_ordered * existing_item.unit_price
        else:
            # Create new item
            so_item = SalesOrderItem(
                sales_order_id=so_id,
                item_id=item_id,
                quantity_ordered=quantity,
                unit_price=unit_price,
                total_price=total_price
            )
            db.session.add(so_item)
        
        # Update SO total
        so.total_amount = sum(item.total_price for item in so.items)
        
        db.session.commit()
        flash('Item added to sales order', 'success')
        
        return jsonify({'success': True, 'message': 'Item added successfully'})
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})

@sales_bp.route('/remove_item/<int:item_id>', methods=['POST'])
@login_required
def remove_sales_order_item(item_id):
    """Remove an item from a sales order"""
    from flask import jsonify
    
    try:
        so_item = SalesOrderItem.query.get_or_404(item_id)
        so = so_item.sales_order
        
        db.session.delete(so_item)
        
        # Update SO total
        so.total_amount = sum(item.total_price for item in so.items)
        
        db.session.commit()
        flash('Item removed from sales order', 'success')
        
        return jsonify({'success': True, 'message': 'Item removed successfully'})
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})

def number_to_words(num):
    """Convert number to words for amounts"""
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

@sales_bp.route('/view/<int:id>')
@login_required
def view_sales_order(id):
    """View sales order details"""
    so = SalesOrder.query.get_or_404(id)
    return render_template('sales/view.html', so=so, title=f'Sales Order {so.so_number}')

@sales_bp.route('/submission-success/<int:so_id>')
@login_required
def submission_success(so_id):
    """SO submission success page with invoice generation and communication options"""
    so = SalesOrder.query.get_or_404(so_id)
    return render_template('sales/submission_success.html', so=so, title='Sales Order Submitted Successfully')

@sales_bp.route('/generate-invoice/<int:id>')
@sales_bp.route('/generate-invoice/<int:id>/<format>')
@login_required  
def generate_invoice(id, format='html'):
    """Generate GST compliant invoice for sales order"""
    so = SalesOrder.query.get_or_404(id)
    
    # Calculate GST amounts (assuming 18% GST)
    gst_rate = 18
    subtotal = so.total_amount or 0
    gst_amount = (subtotal * gst_rate) / 100
    total_with_gst = subtotal + gst_amount
    
    # Update SO with GST calculations
    so.subtotal = subtotal
    so.gst_amount = gst_amount
    so.total_amount = total_with_gst
    db.session.commit()
    
    amount_words = number_to_words(int(total_with_gst))
    company = CompanySettings.get_settings()
    
    if format == 'pdf':
        # Generate PDF
        from weasyprint import HTML
        invoice_html = render_template('sales/invoice_gst.html', so=so, 
                                     amount_words=amount_words, company=company,
                                     gst_rate=gst_rate, subtotal=subtotal, 
                                     gst_amount=gst_amount, total_with_gst=total_with_gst)
        pdf_data = HTML(string=invoice_html).write_pdf()
        
        response = make_response(pdf_data)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename=Invoice_{so.so_number}.pdf'
        return response
    
    return render_template('sales/invoice_gst.html', so=so, amount_words=amount_words, 
                         company=company, gst_rate=gst_rate, subtotal=subtotal, 
                         gst_amount=gst_amount, total_with_gst=total_with_gst)

@sales_bp.route('/send-invoice-email/<int:id>', methods=['POST'])
@login_required  
def send_invoice_email(id):
    """Send invoice via email"""
    so = SalesOrder.query.get_or_404(id)
    
    try:
        data = request.get_json()
        email_to = data.get('email_to')
        email_subject = data.get('email_subject')
        email_message = data.get('email_message')
        
        if not all([email_to, email_subject, email_message]):
            return jsonify({'success': False, 'message': 'Missing required fields'})
        
        # Check if SendGrid API key exists
        import os
        if not os.environ.get('SENDGRID_API_KEY'):
            return jsonify({'success': False, 'message': 'Email service not configured. Please contact administrator.'})
        
        # Generate invoice PDF
        from weasyprint import HTML
        
        # Calculate GST amounts
        gst_rate = 18
        subtotal = so.total_amount or 0
        gst_amount = (subtotal * gst_rate) / 100
        total_with_gst = subtotal + gst_amount
        
        company = CompanySettings.get_settings()
        amount_words = number_to_words(int(total_with_gst))
        
        invoice_html = render_template('sales/invoice_gst.html', so=so, 
                                     company=company, amount_words=amount_words,
                                     gst_rate=gst_rate, subtotal=subtotal, 
                                     gst_amount=gst_amount, total_with_gst=total_with_gst)
        
        pdf_data = HTML(string=invoice_html).write_pdf()
        
        # Send email using SendGrid
        from sendgrid import SendGridAPIClient
        from sendgrid.helpers.mail import Mail, Attachment, FileContent, FileName, FileType, Disposition
        import base64
        
        sg = SendGridAPIClient(api_key=os.environ.get('SENDGRID_API_KEY'))
        
        message = Mail(
            from_email='noreply@akinnovations.com',
            to_emails=email_to,
            subject=email_subject,
            html_content=email_message.replace('\n', '<br>')
        )
        
        # Add PDF attachment
        encoded_file = base64.b64encode(pdf_data).decode()
        attachment = Attachment(
            FileContent(encoded_file),
            FileName(f'Invoice_{so.so_number}.pdf'),
            FileType('application/pdf'),
            Disposition('attachment')
        )
        message.attachment = attachment
        
        response = sg.send(message)
        
        return jsonify({'success': True, 'message': 'Invoice email sent successfully'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error sending email: {str(e)}'})

@sales_bp.route('/send-invoice-whatsapp/<int:id>', methods=['POST'])
@login_required
def send_invoice_whatsapp(id):
    """Send invoice via WhatsApp"""
    so = SalesOrder.query.get_or_404(id)
    
    try:
        data = request.get_json()
        whatsapp_number = data.get('whatsapp_number')
        whatsapp_message = data.get('whatsapp_message')
        
        if not all([whatsapp_number, whatsapp_message]):
            return jsonify({'success': False, 'message': 'Missing required fields'})
        
        # Check if Twilio credentials exist
        import os
        if not all([os.environ.get('TWILIO_ACCOUNT_SID'), os.environ.get('TWILIO_AUTH_TOKEN')]):
            return jsonify({'success': False, 'message': 'WhatsApp service not configured. Please contact administrator.'})
        
        # Send WhatsApp message using Twilio
        from twilio.rest import Client
        
        client = Client(os.environ.get('TWILIO_ACCOUNT_SID'), os.environ.get('TWILIO_AUTH_TOKEN'))
        
        # Clean phone number format
        clean_number = whatsapp_number.replace(' ', '').replace('-', '')
        if not clean_number.startswith('+'):
            clean_number = '+' + clean_number
        
        message = client.messages.create(
            body=whatsapp_message,
            from_=f'whatsapp:{os.environ.get("TWILIO_PHONE_NUMBER")}',
            to=f'whatsapp:{clean_number}'
        )
        
        return jsonify({'success': True, 'message': 'Invoice WhatsApp sent successfully'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error sending WhatsApp: {str(e)}'})
