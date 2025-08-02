"""
Batch Tracking Models for Factory Management System
Implements comprehensive batch-wise inventory and job work tracking
"""

from datetime import datetime, date
from flask_sqlalchemy import SQLAlchemy
from app import db

class InventoryBatch(db.Model):
    """
    Track inventory in batches with state management
    Supports Raw, WIP, Finished, and Scrap states per batch
    """
    __tablename__ = 'inventory_batches'
    
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('items.id'), nullable=False)
    batch_code = db.Column(db.String(50), nullable=False, index=True)
    
    # Quantities by state
    qty_raw = db.Column(db.Float, default=0.0)
    qty_wip = db.Column(db.Float, default=0.0)
    qty_finished = db.Column(db.Float, default=0.0)
    qty_scrap = db.Column(db.Float, default=0.0)
    
    # Batch metadata
    uom = db.Column(db.String(20), nullable=False)
    location = db.Column(db.String(100), default='Default')
    mfg_date = db.Column(db.Date)
    expiry_date = db.Column(db.Date)
    supplier_batch_no = db.Column(db.String(50))  # Vendor's batch number
    purchase_rate = db.Column(db.Float, default=0.0)
    
    # References
    grn_id = db.Column(db.Integer, db.ForeignKey('grn.id'))  # Source GRN
    source_type = db.Column(db.String(20), default='purchase')  # purchase, production, return
    source_ref_id = db.Column(db.Integer)  # Reference to source document
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    item = db.relationship('Item', backref='inventory_batches')
    movements = db.relationship('BatchMovement', backref='batch', lazy=True, cascade='all, delete-orphan')
    
    @property
    def total_quantity(self):
        """Total quantity across all states"""
        return (self.qty_raw or 0) + (self.qty_wip or 0) + (self.qty_finished or 0) + (self.qty_scrap or 0)
    
    @property
    def available_quantity(self):
        """Available quantity (Raw + Finished)"""
        return (self.qty_raw or 0) + (self.qty_finished or 0)
    
    @property
    def is_expired(self):
        """Check if batch is expired"""
        if not self.expiry_date:
            return False
        return self.expiry_date < date.today()
    
    @property
    def age_days(self):
        """Age of batch in days"""
        if not self.mfg_date:
            return 0
        return (date.today() - self.mfg_date).days
    
    def move_quantity(self, quantity, from_state, to_state, ref_type=None, ref_id=None, notes=None):
        """
        Move quantity between states within this batch
        Returns True if successful, False if insufficient quantity
        """
        if quantity <= 0:
            return False
            
        # Check available quantity in from_state
        from_qty = getattr(self, f'qty_{from_state}', 0) or 0
        if from_qty < quantity:
            return False
        
        # Perform the move
        setattr(self, f'qty_{from_state}', from_qty - quantity)
        to_qty = getattr(self, f'qty_{to_state}', 0) or 0
        setattr(self, f'qty_{to_state}', to_qty + quantity)
        
        # Log the movement
        movement = BatchMovement(
            batch_id=self.id,
            item_id=self.item_id,
            quantity=quantity,
            from_state=from_state,
            to_state=to_state,
            movement_type='internal_transfer',
            ref_type=ref_type,
            ref_id=ref_id,
            notes=notes
        )
        db.session.add(movement)
        
        self.updated_at = datetime.utcnow()
        return True
    
    def __repr__(self):
        return f'<InventoryBatch {self.batch_code}: {self.item.name if self.item else "Unknown"}>'

class BatchMovement(db.Model):
    """
    Track all batch quantity movements for audit trail
    """
    __tablename__ = 'batch_movements'
    
    id = db.Column(db.Integer, primary_key=True)
    batch_id = db.Column(db.Integer, db.ForeignKey('inventory_batches.id'), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('items.id'), nullable=False)
    
    # Movement details
    quantity = db.Column(db.Float, nullable=False)
    from_state = db.Column(db.String(20))  # raw, wip, finished, scrap, or None for new batch
    to_state = db.Column(db.String(20))    # raw, wip, finished, scrap, or None for consumed
    movement_type = db.Column(db.String(30), nullable=False)  # receipt, issue, return, transfer, scrap, internal_transfer
    
    # Reference to source document
    ref_type = db.Column(db.String(20))  # grn, jobwork, production, adjustment
    ref_id = db.Column(db.Integer)       # ID of reference document
    notes = db.Column(db.Text)
    
    # Metadata
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    item = db.relationship('Item')
    user = db.relationship('User')
    
    def __repr__(self):
        return f'<BatchMovement {self.quantity} {self.from_state}->{self.to_state}>'

class JobWorkBatch(db.Model):
    """
    Track batch-wise job work processing
    Links input batches to output batches through job work
    """
    __tablename__ = 'jobwork_batches'
    
    id = db.Column(db.Integer, primary_key=True)
    job_work_id = db.Column(db.Integer, db.ForeignKey('job_works.id'), nullable=False)
    
    # Input batch details
    input_batch_id = db.Column(db.Integer, db.ForeignKey('inventory_batches.id'))
    input_item_id = db.Column(db.Integer, db.ForeignKey('items.id'))
    quantity_issued = db.Column(db.Float, nullable=False)
    issue_date = db.Column(db.Date, default=date.today)
    
    # Output batch details (filled when job work is returned)
    output_batch_id = db.Column(db.Integer, db.ForeignKey('inventory_batches.id'))
    output_item_id = db.Column(db.Integer, db.ForeignKey('items.id'))
    quantity_produced = db.Column(db.Float, default=0.0)
    quantity_scrap = db.Column(db.Float, default=0.0)
    quantity_returned_unused = db.Column(db.Float, default=0.0)
    return_date = db.Column(db.Date)
    
    # Process tracking
    process_name = db.Column(db.String(50), nullable=False)
    vendor_name = db.Column(db.String(100))
    rate_per_unit = db.Column(db.Float, default=0.0)
    
    # Status
    status = db.Column(db.String(20), default='issued')  # issued, returned, completed
    notes = db.Column(db.Text)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    job_work = db.relationship('JobWork', backref='batch_records')
    input_batch = db.relationship('InventoryBatch', foreign_keys=[input_batch_id], backref='job_work_issues')
    output_batch = db.relationship('InventoryBatch', foreign_keys=[output_batch_id], backref='job_work_returns')
    input_item = db.relationship('Item', foreign_keys=[input_item_id])
    output_item = db.relationship('Item', foreign_keys=[output_item_id])
    
    @property
    def yield_percentage(self):
        """Calculate yield percentage (output/input * 100)"""
        if not self.quantity_issued or self.quantity_issued == 0:
            return 0.0
        return (self.quantity_produced / self.quantity_issued) * 100
    
    @property
    def scrap_percentage(self):
        """Calculate scrap percentage"""
        if not self.quantity_issued or self.quantity_issued == 0:
            return 0.0
        return (self.quantity_scrap / self.quantity_issued) * 100
    
    @property
    def is_completed(self):
        """Check if job work batch is completed"""
        return self.status == 'completed' and self.return_date is not None
    
    def __repr__(self):
        return f'<JobWorkBatch {self.job_work.job_number if self.job_work else "Unknown"}: {self.process_name}>'

class BatchTraceability(db.Model):
    """
    Track end-to-end traceability of batches through the production process
    """
    __tablename__ = 'batch_traceability'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Source batch
    source_batch_id = db.Column(db.Integer, db.ForeignKey('inventory_batches.id'), nullable=False)
    source_item_id = db.Column(db.Integer, db.ForeignKey('items.id'), nullable=False)
    
    # Destination batch
    dest_batch_id = db.Column(db.Integer, db.ForeignKey('inventory_batches.id'), nullable=False)
    dest_item_id = db.Column(db.Integer, db.ForeignKey('items.id'), nullable=False)
    
    # Transformation details
    transformation_type = db.Column(db.String(30), nullable=False)  # jobwork, production, assembly
    transformation_ref_id = db.Column(db.Integer)  # Reference to jobwork, production order, etc.
    quantity_consumed = db.Column(db.Float, nullable=False)
    quantity_produced = db.Column(db.Float, nullable=False)
    
    # Process metadata
    process_date = db.Column(db.Date, default=date.today)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    source_batch = db.relationship('InventoryBatch', foreign_keys=[source_batch_id], backref='transformations_out')
    dest_batch = db.relationship('InventoryBatch', foreign_keys=[dest_batch_id], backref='transformations_in')
    source_item = db.relationship('Item', foreign_keys=[source_item_id])
    dest_item = db.relationship('Item', foreign_keys=[dest_item_id])
    
    def __repr__(self):
        return f'<BatchTraceability {self.source_batch.batch_code if self.source_batch else "Unknown"} -> {self.dest_batch.batch_code if self.dest_batch else "Unknown"}>'