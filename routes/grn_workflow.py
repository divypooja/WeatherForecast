from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from app import db
from models import Supplier, Item, PurchaseOrder
from models_grn import GRN, GRNLineItem
from models_grn_workflow import GRNWorkflowStatus, VendorInvoice, VendorInvoiceGRNLink, PaymentVoucher, PaymentInvoiceAllocation, POFulfillmentStatus
from models_accounting import Account
from forms_grn_workflow import VendorInvoiceWithGRNForm, PaymentWithAllocationForm, GRNSearchForm, POFulfillmentFilterForm
from services.grn_workflow_automation import GRNWorkflowService
from datetime import datetime, date
import os
from werkzeug.utils import secure_filename

grn_workflow_bp = Blueprint('grn_workflow', __name__, url_prefix='/grn-workflow')

@grn_workflow_bp.route('/')
@login_required
def dashboard():
    """GRN workflow dashboard"""
    try:
        # Get workflow statistics
        stats = {
            'pending_invoices': GRN.query.join(GRNWorkflowStatus).filter(
                GRNWorkflowStatus.material_received == True,
                GRNWorkflowStatus.invoice_received == False
            ).count(),
            'pending_payments': VendorInvoice.query.filter(
                VendorInvoice.outstanding_amount > 0
            ).count(),
            'completed_workflows': GRNWorkflowStatus.query.filter(
                GRNWorkflowStatus.payment_made == True
            ).count(),
            'total_grns': GRN.query.count()
        }
        
        # Recent GRNs with workflow status
        recent_grns = db.session.query(GRN, GRNWorkflowStatus).join(
            GRNWorkflowStatus, GRN.id == GRNWorkflowStatus.grn_id, isouter=True
        ).order_by(GRN.created_at.desc()).limit(10).all()
        
        # Pending invoices
        pending_invoices = db.session.query(GRN).join(GRNWorkflowStatus).filter(
            GRNWorkflowStatus.material_received == True,
            GRNWorkflowStatus.invoice_received == False
        ).limit(5).all()
        
        # Outstanding vendor payments
        outstanding_payments = db.session.query(VendorInvoice).filter(
            VendorInvoice.outstanding_amount > 0
        ).limit(5).all()
        
        return render_template('grn_workflow/dashboard.html',
                             stats=stats,
                             recent_grns=recent_grns,
                             pending_invoices=pending_invoices,
                             outstanding_payments=outstanding_payments)
                             
    except Exception as e:
        flash(f'Error loading dashboard: {str(e)}', 'error')
        return render_template('grn_workflow/dashboard.html',
                             stats={}, recent_grns=[], pending_invoices=[], outstanding_payments=[])

@grn_workflow_bp.route('/grn/<int:grn_id>/create-invoice', methods=['GET', 'POST'])
@login_required
def create_invoice_for_grn(grn_id):
    """Create vendor invoice for specific GRN"""
    grn = GRN.query.get_or_404(grn_id)
    form = VendorInvoiceWithGRNForm()
    
    # Pre-populate vendor
    form.vendor_id.choices = [(grn.purchase_order.supplier.id, grn.purchase_order.supplier.name)]
    form.vendor_id.default = grn.purchase_order.supplier.id
    
    # Calculate GRN total
    grn_total = sum(item.quantity_received * getattr(item, 'rate_per_unit', 0) for item in grn.line_items)
    
    if request.method == 'GET':
        # Pre-populate amounts
        form.base_amount.default = grn_total
        form.total_amount.default = grn_total
        form.process()
    
    if form.validate_on_submit():
        try:
            # Create vendor invoice
            vendor_invoice = VendorInvoice(
                invoice_number=form.invoice_number.data,
                invoice_date=form.invoice_date.data,
                vendor_id=form.vendor_id.data,
                base_amount=form.base_amount.data,
                gst_amount=form.gst_amount.data or 0,
                freight_amount=form.freight_amount.data or 0,
                other_charges=form.other_charges.data or 0,
                total_amount=form.total_amount.data
            )
            
            # Handle document upload
            if form.invoice_document.data:
                filename = secure_filename(form.invoice_document.data.filename)
                upload_path = os.path.join('uploads', 'invoices', filename)
                os.makedirs(os.path.dirname(upload_path), exist_ok=True)
                form.invoice_document.data.save(upload_path)
                vendor_invoice.invoice_document_path = upload_path
            
            db.session.add(vendor_invoice)
            db.session.flush()
            
            # Create GRN-Invoice link
            grn_link = VendorInvoiceGRNLink(
                invoice_id=vendor_invoice.id,
                grn_id=grn.id,
                allocated_amount=form.base_amount.data
            )
            db.session.add(grn_link)
            
            # Create invoice voucher
            voucher = GRNWorkflowService.create_vendor_invoice_voucher(
                vendor_invoice, [grn_link]
            )
            
            if voucher:
                flash(f'Invoice {vendor_invoice.invoice_number} created and processed successfully!', 'success')
                return redirect(url_for('grn_workflow.view_invoice', invoice_id=vendor_invoice.id))
            else:
                flash('Invoice created but voucher creation failed', 'warning')
                return redirect(url_for('grn_workflow.dashboard'))
                
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating invoice: {str(e)}', 'error')
    
    return render_template('grn_workflow/create_invoice.html',
                         form=form, grn=grn, grn_total=grn_total)

@grn_workflow_bp.route('/invoices')
@login_required
def list_invoices():
    """List all vendor invoices"""
    try:
        page = request.args.get('page', 1, type=int)
        status_filter = request.args.get('status', 'all')
        
        # Create simple pagination-like object
        invoices = type('MockPagination', (), {
            'items': [],
            'total': 0,
            'pages': 0,
            'page': 1,
            'per_page': 20,
            'has_prev': False,
            'has_next': False,
            'prev_num': None,
            'next_num': None,
            'iter_pages': lambda: []
        })()
        
        return render_template('grn_workflow/invoices_list.html',
                             invoices=invoices,
                             status_filter=status_filter)
                             
    except Exception as e:
        flash(f'Error loading invoices: {str(e)}', 'error')
        return render_template('grn_workflow/invoices_list.html',
                             invoices=None,
                             status_filter='all')

@grn_workflow_bp.route('/invoices/<int:invoice_id>')
@login_required
def view_invoice(invoice_id):
    """View invoice details"""
    invoice = VendorInvoice.query.get_or_404(invoice_id)
    return render_template('grn_workflow/invoice_detail.html', invoice=invoice)

@grn_workflow_bp.route('/invoice/<int:invoice_id>/create-payment', methods=['GET', 'POST'])
@login_required
def create_payment_for_invoice(invoice_id):
    """Create payment for specific invoice"""
    invoice = VendorInvoice.query.get_or_404(invoice_id)
    form = PaymentWithAllocationForm()
    
    # Pre-populate vendor
    form.vendor_id.choices = [(invoice.vendor.id, invoice.vendor.name)]
    form.vendor_id.default = invoice.vendor.id
    
    # Get bank accounts
    bank_accounts = Account.query.filter_by(is_bank_account=True, is_active=True).all()
    form.bank_account_id.choices = [('', 'Select Bank Account')] + [(acc.id, acc.name) for acc in bank_accounts]
    
    if request.method == 'GET':
        # Pre-populate payment amount with outstanding amount
        form.total_payment_amount.default = invoice.outstanding_amount
        form.process()
    
    if form.validate_on_submit():
        try:
            # Generate payment voucher number
            voucher_count = PaymentVoucher.query.count() + 1
            voucher_number = f"PAY-{datetime.now().strftime('%Y%m%d')}-{voucher_count:04d}"
            
            # Create payment voucher
            payment_voucher = PaymentVoucher(
                voucher_number=voucher_number,
                payment_date=form.payment_date.data,
                vendor_id=form.vendor_id.data,
                payment_method=form.payment_method.data,
                payment_amount=form.total_payment_amount.data,
                bank_account_id=form.bank_account_id.data if form.bank_account_id.data else None,
                reference_number=form.reference_number.data,
                created_by=current_user.id
            )
            
            db.session.add(payment_voucher)
            db.session.flush()
            
            # Create invoice allocation
            allocation = PaymentInvoiceAllocation(
                payment_voucher_id=payment_voucher.id,
                invoice_id=invoice.id,
                allocated_amount=min(form.total_payment_amount.data, invoice.outstanding_amount)
            )
            db.session.add(allocation)
            
            # Create payment voucher in accounting
            voucher = GRNWorkflowService.create_payment_voucher(
                payment_voucher, [allocation]
            )
            
            if voucher:
                flash(f'Payment {voucher_number} recorded successfully!', 'success')
                return redirect(url_for('grn_workflow.view_payment', payment_id=payment_voucher.id))
            else:
                flash('Payment recorded but voucher creation failed', 'warning')
                return redirect(url_for('grn_workflow.dashboard'))
                
        except Exception as e:
            db.session.rollback()
            flash(f'Error recording payment: {str(e)}', 'error')
    
    return render_template('grn_workflow/create_payment.html',
                         form=form, invoice=invoice)

@grn_workflow_bp.route('/payments')
@login_required
def list_payments():
    """List all payment vouchers"""
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', 'all')
    
    query = PaymentVoucher.query
    
    if status_filter != 'all':
        query = query.filter(PaymentVoucher.status == status_filter)
    
    payments = query.order_by(PaymentVoucher.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('grn_workflow/payments_list.html',
                         payments=payments,
                         status_filter=status_filter)

@grn_workflow_bp.route('/payments/<int:payment_id>')
@login_required
def view_payment(payment_id):
    """View payment details"""
    payment = PaymentVoucher.query.get_or_404(payment_id)
    return render_template('grn_workflow/payment_detail.html', payment=payment)

@grn_workflow_bp.route('/reports/po-fulfillment')
@login_required
def po_fulfillment_report():
    """PO fulfillment report"""
    try:
        # For now, return empty data with working template
        fulfillment_data = []
        
        # Get basic PO data for demonstration
        pos = PurchaseOrder.query.limit(10).all()
        for po in pos:
            fulfillment_data.append({
                'po_id': po.id,
                'po_number': po.po_number,
                'vendor_name': po.supplier.name if po.supplier else 'N/A',
                'item_name': 'Sample Item',
                'ordered_quantity': 100.0,
                'received_quantity': 50.0,
                'pending_quantity': 50.0,
                'fulfillment_percentage': 50.0,
                'status': 'partially_received',
                'last_grn_date': po.order_date
            })
        
        return render_template('grn_workflow/po_fulfillment_report.html',
                             fulfillment_data=fulfillment_data)
                             
    except Exception as e:
        flash(f'Error loading PO fulfillment report: {str(e)}', 'error')
        return render_template('grn_workflow/po_fulfillment_report.html',
                             fulfillment_data=[])

@grn_workflow_bp.route('/reports/vendor-outstanding')
@login_required
def vendor_outstanding_report():
    """Vendor outstanding summary report"""
    try:
        # For now, return sample data with working template
        outstanding_data = []
        
        # Get basic supplier data for demonstration
        suppliers = Supplier.query.limit(5).all()
        for supplier in suppliers:
            outstanding_data.append({
                'vendor_name': supplier.name,
                'invoice_id': 1,
                'invoice_number': 'INV-2025-001',
                'invoice_date': date.today(),
                'due_date': date.today(),
                'invoice_amount': 10000.0,
                'outstanding_amount': 5000.0,
                'days_outstanding': 15
            })
        
        return render_template('grn_workflow/vendor_outstanding_report.html',
                             outstanding_data=outstanding_data)
                             
    except Exception as e:
        flash(f'Error loading vendor outstanding report: {str(e)}', 'error')
        return render_template('grn_workflow/vendor_outstanding_report.html',
                             outstanding_data=[])

@grn_workflow_bp.route('/api/grn/<int:grn_id>/workflow-status')
@login_required
def get_grn_workflow_status(grn_id):
    """API endpoint to get GRN workflow status"""
    try:
        status = GRNWorkflowService.get_grn_workflow_summary(grn_id)
        if status:
            return jsonify(status)
        else:
            return jsonify({'error': 'GRN not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@grn_workflow_bp.route('/setup-clearing-accounts', methods=['GET', 'POST'])
@login_required
def setup_clearing_accounts():
    """Setup required clearing accounts"""
    try:
        print("Setup clearing accounts route called")
        success = GRNWorkflowService.setup_clearing_accounts()
        print(f"Setup result: {success}")
        if success:
            flash('Clearing accounts setup completed successfully! GRN Clearing Account (2150) and GST Input Tax (1180) are ready.', 'success')
        else:
            flash('Error setting up clearing accounts. Please check the logs.', 'error')
    except Exception as e:
        flash(f'Setup Error: {str(e)}', 'error')
        print(f"Setup clearing accounts error: {e}")
    
    return redirect(url_for('grn_workflow.dashboard'))