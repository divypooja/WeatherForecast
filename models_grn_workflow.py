from app import db
from datetime import datetime, date
from decimal import Decimal
from sqlalchemy import func

class GRNWorkflowStatus(db.Model):
    """Track GRN workflow status through the 3-step process"""
    __tablename__ = 'grn_workflow_status'
    
    id = db.Column(db.Integer, primary_key=True)
    grn_id = db.Column(db.Integer, db.ForeignKey('grn.id'), nullable=False)
    
    # Workflow stages
    material_received = db.Column(db.Boolean, default=False)
    grn_voucher_created = db.Column(db.Boolean, default=False)
    invoice_received = db.Column(db.Boolean, default=False)
    invoice_voucher_created = db.Column(db.Boolean, default=False)
    payment_made = db.Column(db.Boolean, default=False)
    payment_voucher_created = db.Column(db.Boolean, default=False)
    
    # Timestamps
    material_received_date = db.Column(db.DateTime)
    invoice_received_date = db.Column(db.DateTime)
    payment_made_date = db.Column(db.DateTime)
    
    # References
    grn_clearing_voucher_id = db.Column(db.Integer, db.ForeignKey('vouchers.id'))
    invoice_voucher_id = db.Column(db.Integer, db.ForeignKey('vouchers.id'))
    payment_voucher_id = db.Column(db.Integer, db.ForeignKey('vouchers.id'))
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    grn = db.relationship('GRN', backref='workflow_status')
    grn_clearing_voucher = db.relationship('Voucher', foreign_keys=[grn_clearing_voucher_id])
    invoice_voucher = db.relationship('Voucher', foreign_keys=[invoice_voucher_id])
    payment_voucher = db.relationship('Voucher', foreign_keys=[payment_voucher_id])

class VendorInvoice(db.Model):
    """Vendor invoices linked to GRNs"""
    __tablename__ = 'vendor_invoices'
    
    id = db.Column(db.Integer, primary_key=True)
    invoice_number = db.Column(db.String(100), nullable=False)
    invoice_date = db.Column(db.Date, nullable=False)
    
    # Vendor details
    vendor_id = db.Column(db.Integer, db.ForeignKey('suppliers.id'), nullable=False)
    
    # Invoice amounts
    base_amount = db.Column(db.Numeric(15, 2), nullable=False, default=Decimal('0.00'))
    gst_amount = db.Column(db.Numeric(15, 2), nullable=False, default=Decimal('0.00'))
    freight_amount = db.Column(db.Numeric(15, 2), nullable=False, default=Decimal('0.00'))
    other_charges = db.Column(db.Numeric(15, 2), nullable=False, default=Decimal('0.00'))
    total_amount = db.Column(db.Numeric(15, 2), nullable=False, default=Decimal('0.00'))
    
    # Payment status
    paid_amount = db.Column(db.Numeric(15, 2), nullable=False, default=Decimal('0.00'))
    outstanding_amount = db.Column(db.Numeric(15, 2), nullable=False, default=Decimal('0.00'))
    
    # Status
    status = db.Column(db.String(20), default='pending')  # pending, processed, paid
    
    # Document reference
    invoice_document_path = db.Column(db.String(500))
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    vendor = db.relationship('Supplier', backref='vendor_invoices')
    
    def update_outstanding(self):
        """Update outstanding amount (safe Decimal arithmetic)"""
        total = Decimal(str(self.total_amount or 0))
        paid = Decimal(str(self.paid_amount or 0))
        self.outstanding_amount = total - paid
        
        if self.outstanding_amount <= 0:
            self.status = 'paid'
        elif self.paid_amount > 0:
            self.status = 'partial'
        else:
            self.status = 'pending'

class VendorInvoiceGRNLink(db.Model):
    """Link vendor invoices to specific GRNs"""
    __tablename__ = 'vendor_invoice_grn_links'
    
    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey('vendor_invoices.id'), nullable=False)
    grn_id = db.Column(db.Integer, db.ForeignKey('grn.id'), nullable=False)
    
    # Amount allocation
    allocated_amount = db.Column(db.Numeric(15, 2), nullable=False, default=Decimal('0.00'))
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    invoice = db.relationship('VendorInvoice', backref='grn_links')
    grn = db.relationship('GRN', backref='invoice_links')

class PaymentVoucher(db.Model):
    """Payment vouchers for vendor payments"""
    __tablename__ = 'payment_vouchers'
    
    id = db.Column(db.Integer, primary_key=True)
    voucher_number = db.Column(db.String(50), unique=True, nullable=False)
    payment_date = db.Column(db.Date, nullable=False)
    
    # Vendor details
    vendor_id = db.Column(db.Integer, db.ForeignKey('suppliers.id'), nullable=False)
    
    # Payment details
    payment_method = db.Column(db.String(50), nullable=False)  # cash, bank, upi, cheque
    payment_amount = db.Column(db.Numeric(15, 2), nullable=False)
    
    # Bank details (for non-cash payments)
    bank_account_id = db.Column(db.Integer, db.ForeignKey('accounts.id'))
    reference_number = db.Column(db.String(100))  # cheque number, UPI ref, etc.
    
    # Status
    status = db.Column(db.String(20), default='draft')  # draft, posted, cancelled
    
    # Accounting reference
    voucher_id = db.Column(db.Integer, db.ForeignKey('vouchers.id'))
    
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    vendor = db.relationship('Supplier', backref='vendor_payments')
    bank_account = db.relationship('Account')
    voucher = db.relationship('Voucher')
    created_by_user = db.relationship('User')

class PaymentInvoiceAllocation(db.Model):
    """Allocate payments to specific invoices"""
    __tablename__ = 'payment_invoice_allocations'
    
    id = db.Column(db.Integer, primary_key=True)
    payment_voucher_id = db.Column(db.Integer, db.ForeignKey('payment_vouchers.id'), nullable=False)
    invoice_id = db.Column(db.Integer, db.ForeignKey('vendor_invoices.id'), nullable=False)
    
    allocated_amount = db.Column(db.Numeric(15, 2), nullable=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    payment_voucher = db.relationship('PaymentVoucher', backref='invoice_allocations')
    invoice = db.relationship('VendorInvoice', backref='payment_allocations')

class POFulfillmentStatus(db.Model):
    """Track PO fulfillment status"""
    __tablename__ = 'po_fulfillment_status'
    
    id = db.Column(db.Integer, primary_key=True)
    po_id = db.Column(db.Integer, db.ForeignKey('purchase_orders.id'), nullable=False)
    po_item_id = db.Column(db.Integer, db.ForeignKey('purchase_order_items.id'), nullable=False)
    
    # Quantities
    ordered_quantity = db.Column(db.Numeric(15, 3), nullable=False)
    received_quantity = db.Column(db.Numeric(15, 3), nullable=False, default=Decimal('0.000'))
    pending_quantity = db.Column(db.Numeric(15, 3), nullable=False, default=Decimal('0.000'))
    
    # Values
    ordered_value = db.Column(db.Numeric(15, 2), nullable=False)
    received_value = db.Column(db.Numeric(15, 2), nullable=False, default=Decimal('0.00'))
    pending_value = db.Column(db.Numeric(15, 2), nullable=False, default=Decimal('0.00'))
    
    # Status
    fulfillment_percentage = db.Column(db.Numeric(5, 2), default=Decimal('0.00'))
    status = db.Column(db.String(20), default='pending')  # pending, partial, complete
    
    last_grn_date = db.Column(db.Date)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    po = db.relationship('PurchaseOrder', backref='fulfillment_status')
    po_item = db.relationship('PurchaseOrderItem', backref='fulfillment_status')
    
    def update_status(self):
        """Update fulfillment status based on quantities"""
        if self.ordered_quantity > 0:
            self.fulfillment_percentage = (self.received_quantity / self.ordered_quantity) * 100
            
            if self.received_quantity >= self.ordered_quantity:
                self.status = 'complete'
                self.pending_quantity = 0
                self.pending_value = 0
            elif self.received_quantity > 0:
                self.status = 'partial'
                self.pending_quantity = self.ordered_quantity - self.received_quantity
                # Calculate pending value proportionally
                if self.ordered_value > 0:
                    unit_rate = self.ordered_value / self.ordered_quantity
                    self.pending_value = self.pending_quantity * unit_rate
            else:
                self.status = 'pending'
                self.pending_quantity = self.ordered_quantity
                self.pending_value = self.ordered_value