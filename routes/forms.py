from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file, jsonify
from flask_login import login_required, current_user
from app import db
from models import PurchaseOrder, SalesOrder, JobWork, Production, FactoryExpense, Supplier
from utils_export import generate_pdf_document, generate_excel_document, generate_challan_pdf, generate_invoice_pdf
from services.notification_service import send_email, send_whatsapp, send_sms
import os
import tempfile
from datetime import datetime

forms_bp = Blueprint('forms', __name__, url_prefix='/forms')

@forms_bp.route('/thank-you/<form_type>/<int:entity_id>')
@login_required
def thank_you(form_type, entity_id):
    """Display thank you page after form submission"""
    
    # Get entity details based on form type
    entity = None
    entity_number = None
    entity_details = None
    entity_email = None
    entity_phone = None
    back_url = None
    create_new_url = None
    form_type_display = None
    
    # Determine document availability
    pdf_available = True
    excel_available = True
    challan_available = False
    invoice_available = False
    
    if form_type == 'purchase_order':
        entity = PurchaseOrder.query.get_or_404(entity_id)
        entity_number = entity.po_number
        form_type_display = 'Purchase Order'
        if entity.supplier:
            entity_email = entity.supplier.email
            entity_phone = entity.supplier.phone
        entity_details = f"""
        <div class="row">
            <div class="col-md-6">
                <strong>Supplier:</strong> {entity.supplier.name if entity.supplier else 'N/A'}<br>
                <strong>Order Date:</strong> {entity.order_date.strftime('%d/%m/%Y') if entity.order_date else 'N/A'}<br>
                <strong>Total Amount:</strong> ₹{entity.total_amount or 0:.2f}
            </div>
            <div class="col-md-6">
                <strong>Status:</strong> <span class="badge bg-info">{entity.status.title()}</span><br>
                <strong>Expected Delivery:</strong> {entity.expected_delivery_date.strftime('%d/%m/%Y') if entity.expected_delivery_date else 'N/A'}
            </div>
        </div>
        """
        back_url = url_for('purchase.list_purchase_orders')
        create_new_url = url_for('purchase.create_purchase_order')
        challan_available = True
        
    elif form_type == 'sales_order':
        entity = SalesOrder.query.get_or_404(entity_id)
        entity_number = entity.so_number
        form_type_display = 'Sales Order'
        if entity.customer:
            entity_email = entity.customer.email
            entity_phone = entity.customer.phone
        entity_details = f"""
        <div class="row">
            <div class="col-md-6">
                <strong>Customer:</strong> {entity.customer.name if entity.customer else 'N/A'}<br>
                <strong>Order Date:</strong> {entity.order_date.strftime('%d/%m/%Y') if entity.order_date else 'N/A'}<br>
                <strong>Total Amount:</strong> ₹{entity.total_amount or 0:.2f}
            </div>
            <div class="col-md-6">
                <strong>Status:</strong> <span class="badge bg-success">{entity.status.title()}</span><br>
                <strong>Delivery Date:</strong> {entity.delivery_date.strftime('%d/%m/%Y') if entity.delivery_date else 'N/A'}
            </div>
        </div>
        """
        back_url = url_for('sales.list_sales_orders')
        create_new_url = url_for('sales.create_sales_order')
        invoice_available = True
        
    elif form_type == 'job_work':
        entity = JobWork.query.get_or_404(entity_id)
        entity_number = entity.jobwork_number
        form_type_display = 'Job Work'
        if entity.vendor:
            entity_email = entity.vendor.email
            entity_phone = entity.vendor.phone
        entity_details = f"""
        <div class="row">
            <div class="col-md-6">
                <strong>Type:</strong> <span class="badge bg-primary">{entity.job_type.title()}</span><br>
                <strong>Item:</strong> {entity.item.name if entity.item else 'N/A'}<br>
                <strong>Quantity:</strong> {entity.quantity or 0}
            </div>
            <div class="col-md-6">
                <strong>Status:</strong> <span class="badge bg-warning">{entity.status.title()}</span><br>
                <strong>Due Date:</strong> {entity.due_date.strftime('%d/%m/%Y') if entity.due_date else 'N/A'}
            </div>
        </div>
        """
        back_url = url_for('jobwork.list_job_works')
        create_new_url = url_for('jobwork.create_job_work')
        challan_available = True
        
    elif form_type == 'production':
        entity = Production.query.get_or_404(entity_id)
        entity_number = entity.production_number
        form_type_display = 'Production Order'
        entity_details = f"""
        <div class="row">
            <div class="col-md-6">
                <strong>Item:</strong> {entity.item.name if entity.item else 'N/A'}<br>
                <strong>Quantity to Produce:</strong> {entity.quantity_to_produce or 0}<br>
                <strong>Production Date:</strong> {entity.production_date.strftime('%d/%m/%Y') if entity.production_date else 'N/A'}
            </div>
            <div class="col-md-6">
                <strong>Status:</strong> <span class="badge bg-info">{entity.status.title()}</span><br>
                <strong>Department:</strong> {entity.department.name if entity.department else 'N/A'}
            </div>
        </div>
        """
        back_url = url_for('production.list_production')
        create_new_url = url_for('production.create_production')
        
    elif form_type == 'expense':
        entity = FactoryExpense.query.get_or_404(entity_id)
        entity_number = entity.expense_number
        form_type_display = 'Factory Expense'
        if entity.vendor:
            entity_email = entity.vendor.email
            entity_phone = entity.vendor.phone
        entity_details = f"""
        <div class="row">
            <div class="col-md-6">
                <strong>Category:</strong> {entity.expense_category.replace('_', ' ').title()}<br>
                <strong>Amount:</strong> ₹{entity.amount or 0:.2f}<br>
                <strong>Date:</strong> {entity.expense_date.strftime('%d/%m/%Y') if entity.expense_date else 'N/A'}
            </div>
            <div class="col-md-6">
                <strong>Status:</strong> <span class="badge bg-secondary">{entity.status.title()}</span><br>
                <strong>Payment Method:</strong> {entity.payment_method.title() if entity.payment_method else 'N/A'}
            </div>
        </div>
        """
        back_url = url_for('expenses.list_expenses')
        create_new_url = url_for('expenses.create_expense')
    
    return render_template('forms/thank_you.html',
                         form_type=form_type,
                         form_type_display=form_type_display,
                         entity_id=entity_id,
                         entity_number=entity_number,
                         entity_details=entity_details,
                         entity_email=entity_email,
                         entity_phone=entity_phone,
                         back_url=back_url,
                         create_new_url=create_new_url,
                         pdf_available=pdf_available,
                         excel_available=excel_available,
                         challan_available=challan_available,
                         invoice_available=invoice_available,
                         company_name="AK Innovations")

@forms_bp.route('/download-document/<form_type>/<int:entity_id>/<doc_type>')
@login_required
def download_document(form_type, entity_id, doc_type):
    """Generate and download document"""
    
    try:
        # Get entity based on form type
        entity = None
        if form_type == 'purchase_order':
            entity = PurchaseOrder.query.get_or_404(entity_id)
        elif form_type == 'sales_order':
            entity = SalesOrder.query.get_or_404(entity_id)
        elif form_type == 'job_work':
            entity = JobWork.query.get_or_404(entity_id)
        elif form_type == 'production':
            entity = Production.query.get_or_404(entity_id)
        elif form_type == 'expense':
            entity = FactoryExpense.query.get_or_404(entity_id)
        
        if not entity:
            flash('Entity not found', 'error')
            return redirect(url_for('main.dashboard'))
        
        # Generate document based on type
        temp_file = None
        filename = f"{form_type}_{entity_id}_{doc_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        if doc_type == 'pdf':
            temp_file = generate_pdf_document(form_type, entity)
            filename += '.pdf'
        elif doc_type == 'excel':
            temp_file = generate_excel_document(form_type, entity)
            filename += '.xlsx'
        elif doc_type == 'challan':
            temp_file = generate_challan_pdf(form_type, entity)
            filename += '.pdf'
        elif doc_type == 'invoice':
            temp_file = generate_invoice_pdf(form_type, entity)
            filename += '.pdf'
        
        if temp_file and os.path.exists(temp_file):
            return send_file(temp_file, as_attachment=True, download_name=filename)
        else:
            flash('Error generating document', 'error')
            return redirect(url_for('forms.thank_you', form_type=form_type, entity_id=entity_id))
            
    except Exception as e:
        flash(f'Error downloading document: {str(e)}', 'error')
        return redirect(url_for('forms.thank_you', form_type=form_type, entity_id=entity_id))

@forms_bp.route('/send-document', methods=['POST'])
@login_required
def send_document():
    """Send document via email, WhatsApp, or SMS"""
    
    try:
        form_type = request.form.get('form_type')
        entity_id = int(request.form.get('entity_id'))
        method = request.form.get('method')
        
        # Get entity
        entity = None
        if form_type == 'purchase_order':
            entity = PurchaseOrder.query.get_or_404(entity_id)
        elif form_type == 'sales_order':
            entity = SalesOrder.query.get_or_404(entity_id)
        elif form_type == 'job_work':
            entity = JobWork.query.get_or_404(entity_id)
        elif form_type == 'production':
            entity = Production.query.get_or_404(entity_id)
        elif form_type == 'expense':
            entity = FactoryExpense.query.get_or_404(entity_id)
        
        success = False
        message = ""
        
        if method == 'email':
            email_to = request.form.get('email_to')
            subject = request.form.get('subject')
            email_message = request.form.get('message')
            documents = request.form.getlist('documents')
            
            # Generate attachments
            attachments = []
            for doc_type in documents:
                if doc_type == 'pdf':
                    temp_file = generate_pdf_document(form_type, entity)
                    if temp_file:
                        attachments.append((temp_file, f"{form_type}_{entity_id}.pdf"))
                elif doc_type == 'excel':
                    temp_file = generate_excel_document(form_type, entity)
                    if temp_file:
                        attachments.append((temp_file, f"{form_type}_{entity_id}.xlsx"))
            
            success = send_email(email_to, subject, email_message, attachments)
            message = "Email sent successfully" if success else "Failed to send email"
            
        elif method == 'whatsapp':
            phone_number = request.form.get('phone_number')
            whatsapp_message = request.form.get('message')
            
            # Generate document link (you may want to implement a secure link system)
            document_link = url_for('forms.download_document', 
                                  form_type=form_type, 
                                  entity_id=entity_id, 
                                  doc_type='pdf', 
                                  _external=True)
            
            full_message = f"{whatsapp_message}\n\nDocument: {document_link}"
            success = send_whatsapp(phone_number, full_message)
            message = "WhatsApp message sent successfully" if success else "Failed to send WhatsApp message"
            
        elif method == 'sms':
            phone_number = request.form.get('phone_number')
            sms_message = request.form.get('message')
            
            success = send_sms(phone_number, sms_message)
            message = "SMS sent successfully" if success else "Failed to send SMS"
        
        return jsonify({'success': success, 'message': message})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})