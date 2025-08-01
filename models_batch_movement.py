"""
Batch Movement Ledger Models - Fixed Version
Tracks every batch movement across all modules for complete traceability
"""

from app import db
from datetime import datetime
from sqlalchemy import func

class BatchMovementLedger(db.Model):
    """
    Central ledger tracking every batch movement across all modules
    Every action that affects batch quantity/state creates a movement record
    """
    __tablename__ = 'batch_movement_ledger'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Reference Information
    ref_type = db.Column(db.String(50), nullable=False)  # GRN, JobWork, Production, Dispatch, Scrap, etc.
    ref_id = db.Column(db.Integer, nullable=False)  # ID of the reference document
    ref_number = db.Column(db.String(100))  # Human-readable reference number
    
    # Batch Information - Fixed foreign key reference
    batch_id = db.Column(db.Integer, db.ForeignKey('item_batches.id'), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('items.id'), nullable=False)
    
    # Movement Details
    from_state = db.Column(db.String(50))  # None, Raw, WIP_Cutting, etc.
    to_state = db.Column(db.String(50), nullable=False)  # Raw, WIP_Cutting, Finished, Scrap, etc.
    quantity = db.Column(db.Float, nullable=False)
    unit_of_measure = db.Column(db.String(20), nullable=False)
    
    # Additional Context
    process_name = db.Column(db.String(100))  # For WIP states: cutting, bending, etc.
    vendor_id = db.Column(db.Integer, db.ForeignKey('suppliers.id'))  # For job work movements
    storage_location = db.Column(db.String(200))
    cost_per_unit = db.Column(db.Float)
    total_cost = db.Column(db.Float)
    
    # Quality and Notes
    quality_status = db.Column(db.String(50), default='good')
    notes = db.Column(db.Text)
    
    # Timestamps
    movement_date = db.Column(db.Date, nullable=False, default=datetime.utcnow().date)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # Relationships
    batch = db.relationship('ItemBatch', backref='movement_history')
    item = db.relationship('Item', backref='batch_movements')
    vendor = db.relationship('Supplier', backref='batch_movements')
    created_by_user = db.relationship('User', backref='batch_movements_created')
    
    def __repr__(self):
        return f'<BatchMovement {self.ref_type}-{self.ref_id}: {self.quantity} {self.item.name if self.item else ""}>'
    
    @property
    def movement_description(self):
        """Human-readable description of the movement"""
        from_desc = self.from_state.replace('_', ' ').title() if self.from_state else 'External'
        to_desc = self.to_state.replace('_', ' ').title()
        return f"{from_desc} → {to_desc}"
    
    @classmethod
    def create_movement(cls, ref_type, ref_id, batch_id, item_id, from_state, to_state, 
                       quantity, unit_of_measure, **kwargs):
        """Helper method to create batch movement records"""
        movement = cls(
            ref_type=ref_type,
            ref_id=ref_id,
            batch_id=batch_id,
            item_id=item_id,
            from_state=from_state,
            to_state=to_state,
            quantity=quantity,
            unit_of_measure=unit_of_measure,
            **kwargs
        )
        db.session.add(movement)
        return movement
    
    @classmethod
    def get_batch_history(cls, batch_id):
        """Get complete movement history for a batch"""
        return cls.query.filter_by(batch_id=batch_id).order_by(cls.created_at).all()
    
    @classmethod
    def get_item_movements(cls, item_id, start_date=None, end_date=None):
        """Get movements for an item within date range"""
        query = cls.query.filter_by(item_id=item_id)
        if start_date:
            query = query.filter(cls.movement_date >= start_date)
        if end_date:
            query = query.filter(cls.movement_date <= end_date)
        return query.order_by(cls.created_at.desc()).all()
    
    @classmethod
    def get_vendor_movements(cls, vendor_id, start_date=None, end_date=None):
        """Get movements related to a specific vendor"""
        query = cls.query.filter_by(vendor_id=vendor_id)
        if start_date:
            query = query.filter(cls.movement_date >= start_date)
        if end_date:
            query = query.filter(cls.movement_date <= end_date)
        return query.order_by(cls.created_at.desc()).all()

class BatchConsumptionReport(db.Model):
    """
    Aggregated batch consumption data for reporting
    Automatically updated when batch movements occur
    """
    __tablename__ = 'batch_consumption_report'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Batch Information - Fixed foreign key reference
    batch_id = db.Column(db.Integer, db.ForeignKey('item_batches.id'), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('items.id'), nullable=False)
    batch_number = db.Column(db.String(100), nullable=False)
    
    # Consumption Summary
    total_received = db.Column(db.Float, default=0.0)  # From GRN
    total_issued = db.Column(db.Float, default=0.0)    # To Job Work/Production
    total_finished = db.Column(db.Float, default=0.0)  # Finished products
    total_scrap = db.Column(db.Float, default=0.0)     # Scrapped
    total_returned = db.Column(db.Float, default=0.0)  # Unused returned
    total_dispatched = db.Column(db.Float, default=0.0) # Dispatched to customers
    
    # Process-wise consumption
    qty_cutting = db.Column(db.Float, default=0.0)
    qty_bending = db.Column(db.Float, default=0.0)
    qty_welding = db.Column(db.Float, default=0.0)
    qty_zinc = db.Column(db.Float, default=0.0)
    qty_painting = db.Column(db.Float, default=0.0)
    qty_assembly = db.Column(db.Float, default=0.0)
    qty_machining = db.Column(db.Float, default=0.0)
    qty_polishing = db.Column(db.Float, default=0.0)
    
    # Efficiency Metrics
    yield_percentage = db.Column(db.Float)  # (finished / issued) * 100
    scrap_percentage = db.Column(db.Float)  # (scrap / issued) * 100
    utilization_percentage = db.Column(db.Float)  # (issued / received) * 100
    
    # Vendor and Cost Information
    vendor_id = db.Column(db.Integer, db.ForeignKey('suppliers.id'))
    unit_cost = db.Column(db.Float)
    total_cost = db.Column(db.Float)
    
    # Timestamps
    first_received = db.Column(db.Date)
    last_movement = db.Column(db.Date)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    batch = db.relationship('ItemBatch', backref='consumption_report')
    item = db.relationship('Item', backref='batch_consumption_reports')
    vendor = db.relationship('Supplier', backref='batch_consumption_reports')
    
    def __repr__(self):
        return f'<BatchConsumption {self.batch_number}: {self.yield_percentage:.1f}% yield>'
    
    @property
    def is_active(self):
        """Check if batch is still active (has remaining quantity)"""
        return (self.total_received - self.total_issued - self.total_dispatched) > 0
    
    @property
    def remaining_quantity(self):
        """Calculate remaining quantity in batch"""
        return max(0, self.total_received - self.total_issued - self.total_dispatched)
    
    def update_from_movement(self, movement):
        """Update consumption report based on batch movement"""
        if movement.ref_type == 'GRN':
            self.total_received += movement.quantity
            if not self.first_received:
                self.first_received = movement.movement_date
        
        elif movement.ref_type in ['JobWork', 'Production']:
            if movement.to_state.startswith('WIP') or movement.to_state == 'Issued':
                self.total_issued += movement.quantity
                
                # Update process-wise quantities
                if 'cutting' in movement.to_state.lower():
                    self.qty_cutting += movement.quantity
                elif 'bending' in movement.to_state.lower():
                    self.qty_bending += movement.quantity
                elif 'welding' in movement.to_state.lower():
                    self.qty_welding += movement.quantity
                elif 'zinc' in movement.to_state.lower():
                    self.qty_zinc += movement.quantity
                elif 'painting' in movement.to_state.lower():
                    self.qty_painting += movement.quantity
                elif 'assembly' in movement.to_state.lower():
                    self.qty_assembly += movement.quantity
                elif 'machining' in movement.to_state.lower():
                    self.qty_machining += movement.quantity
                elif 'polishing' in movement.to_state.lower():
                    self.qty_polishing += movement.quantity
            
            elif movement.to_state == 'Finished':
                self.total_finished += movement.quantity
            elif movement.to_state == 'Scrap':
                self.total_scrap += movement.quantity
            elif movement.to_state == 'Raw' and movement.from_state != 'None':
                self.total_returned += movement.quantity
        
        elif movement.ref_type == 'Dispatch':
            self.total_dispatched += movement.quantity
        
        # Update efficiency metrics
        self._calculate_efficiency_metrics()
        self.last_movement = movement.movement_date
        self.updated_at = datetime.utcnow()
    
    def _calculate_efficiency_metrics(self):
        """Calculate yield, scrap, and utilization percentages"""
        if self.total_issued > 0:
            self.yield_percentage = (self.total_finished / self.total_issued) * 100
            self.scrap_percentage = (self.total_scrap / self.total_issued) * 100
        
        if self.total_received > 0:
            self.utilization_percentage = (self.total_issued / self.total_received) * 100
    
    @classmethod
    def get_or_create(cls, batch_id):
        """Get existing report or create new one for batch"""
        report = cls.query.filter_by(batch_id=batch_id).first()
        if not report:
            from models import ItemBatch
            batch = ItemBatch.query.get(batch_id)
            if batch:
                report = cls(
                    batch_id=batch_id,
                    item_id=batch.item_id,
                    batch_number=batch.batch_number
                )
                db.session.add(report)
        return report