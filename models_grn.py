from app import db
from datetime import datetime
from utils import generate_next_number


class GRN(db.Model):
    """Goods Receipt Note - Parent table for tracking material receipts from job works and purchase orders"""
    __tablename__ = 'grn'
    
    id = db.Column(db.Integer, primary_key=True)
    grn_number = db.Column(db.String(50), unique=True, nullable=False)  # GRN-YYYY-0001
    # Foreign Keys (either job_work_id OR purchase_order_id should be set)
    job_work_id = db.Column(db.Integer, db.ForeignKey('job_works.id'), nullable=True)
    purchase_order_id = db.Column(db.Integer, db.ForeignKey('purchase_orders.id'), nullable=True)
    received_date = db.Column(db.Date, nullable=False, default=datetime.utcnow().date())
    received_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Quality control fields
    inspection_required = db.Column(db.Boolean, default=True)
    inspection_status = db.Column(db.String(20), default='pending')  # pending, in_progress, completed, failed
    inspected_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    inspected_at = db.Column(db.DateTime)
    
    # Overall GRN status
    status = db.Column(db.String(20), default='draft')  # draft, received, inspected, completed
    
    # Reference information
    delivery_note = db.Column(db.String(100))  # Vendor's delivery note number
    transporter_name = db.Column(db.String(100))
    vehicle_number = db.Column(db.String(20))
    
    # Notes and remarks
    remarks = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    job_work = db.relationship('JobWork', backref='grn_receipts')
    purchase_order = db.relationship('PurchaseOrder', backref='grn_receipts')
    receiver = db.relationship('User', foreign_keys=[received_by], backref='received_grns')
    inspector = db.relationship('User', foreign_keys=[inspected_by], backref='inspected_grns')
    
    @property
    def source_document(self):
        """Get the source document (either job work or purchase order)"""
        if self.job_work_id:
            return self.job_work
        elif self.purchase_order_id:
            return self.purchase_order
        return None
    
    @property
    def source_type(self):
        """Get the type of source document"""
        if self.job_work_id:
            return 'job_work'
        elif self.purchase_order_id:
            return 'purchase_order'
        return None
    
    @staticmethod
    def generate_grn_number():
        """Generate next GRN number in format GRN-YYYY-0001"""
        return generate_next_number('GRN', 'grns', 'grn_number')
    
    @property
    def total_quantity_received(self):
        """Calculate total quantity received across all line items"""
        return sum(item.quantity_received for item in self.line_items)
    
    @property
    def total_quantity_passed(self):
        """Calculate total quantity passed inspection"""
        return sum(item.quantity_passed for item in self.line_items)
    
    @property
    def total_quantity_rejected(self):
        """Calculate total quantity rejected during inspection"""
        return sum(item.quantity_rejected for item in self.line_items)
    
    @property
    def acceptance_rate(self):
        """Calculate acceptance rate percentage"""
        total = self.total_quantity_received
        if total > 0:
            return (self.total_quantity_passed / total) * 100
        return 0
    
    @property
    def is_fully_inspected(self):
        """Check if all received items have been inspected"""
        return all(item.inspection_status == 'completed' for item in self.line_items)
    
    def __repr__(self):
        return f'<GRN {self.grn_number}>'


class GRNLineItem(db.Model):
    """GRN Line Items - Individual items received in a GRN"""
    __tablename__ = 'grn_line_items'
    
    id = db.Column(db.Integer, primary_key=True)
    grn_id = db.Column(db.Integer, db.ForeignKey('grn.id'), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('items.id'), nullable=False)
    
    # Quantity tracking
    quantity_received = db.Column(db.Float, nullable=False)
    quantity_passed = db.Column(db.Float, default=0.0)
    quantity_rejected = db.Column(db.Float, default=0.0)
    
    # Unit information
    unit_of_measure = db.Column(db.String(20))
    unit_weight = db.Column(db.Float, default=0.0)
    
    # Quality control
    inspection_status = db.Column(db.String(20), default='pending')  # pending, passed, rejected, partial
    rejection_reason = db.Column(db.String(500))
    quality_grade = db.Column(db.String(10))  # A, B, C grade or Pass/Fail
    
    # Process information (for multi-process job works)
    process_name = db.Column(db.String(100))  # Which process this item came from
    process_stage = db.Column(db.String(50))  # Stage in the process
    
    # Cost tracking
    rate_per_unit = db.Column(db.Float, default=0.0)
    total_value = db.Column(db.Float, default=0.0)
    
    # Material classification for inventory
    material_classification = db.Column(db.String(50), default='finished_goods')  # finished_goods, semi_finished, raw_material
    
    # Notes and tracking
    remarks = db.Column(db.Text)
    batch_number = db.Column(db.String(50))
    serial_numbers = db.Column(db.Text)  # JSON or comma-separated for tracking individual items
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    grn = db.relationship('GRN', backref='line_items')
    item = db.relationship('Item', backref='grn_line_items')
    
    @property
    def acceptance_rate(self):
        """Calculate acceptance rate for this line item"""
        if self.quantity_received > 0:
            return (self.quantity_passed / self.quantity_received) * 100
        return 0
    
    @property
    def pending_inspection(self):
        """Calculate quantity pending inspection"""
        return self.quantity_received - (self.quantity_passed + self.quantity_rejected)
    
    @property
    def is_fully_inspected(self):
        """Check if this line item is fully inspected"""
        return (self.quantity_passed + self.quantity_rejected) >= self.quantity_received
    
    def __repr__(self):
        return f'<GRNLineItem {self.grn.grn_number}-{self.item.code}>'