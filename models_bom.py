from app import db
from datetime import datetime
from sqlalchemy import func

class BillOfMaterials(db.Model):
    __tablename__ = 'bill_of_materials'
    
    id = db.Column(db.Integer, primary_key=True)
    bom_code = db.Column(db.String(50), unique=True, nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('items.id'), nullable=False)
    output_quantity = db.Column(db.Float, nullable=False, default=1.0)
    output_uom_id = db.Column(db.Integer, db.ForeignKey('units_of_measure.id'), nullable=False)
    version = db.Column(db.String(20), default='1.0')
    status = db.Column(db.String(20), default='active')  # active, inactive, draft
    description = db.Column(db.Text)
    remarks = db.Column(db.Text)
    estimated_cost = db.Column(db.Float, default=0.0)
    estimated_scrap_percent = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # Relationships
    product = db.relationship('Item', foreign_keys=[product_id], backref='bill_of_materials')
    output_uom = db.relationship('UnitOfMeasure', foreign_keys=[output_uom_id])  # type: ignore
    components = db.relationship('BOMComponent', backref='bom', cascade='all, delete-orphan')
    processes = db.relationship('BOMProcess', backref='bom', cascade='all, delete-orphan')
    creator = db.relationship('User', foreign_keys=[created_by])
    
    def __repr__(self):
        return f'<BOM {self.bom_code}: {self.product.name if self.product else "N/A"}>'
    
    @property
    def total_material_cost(self):
        """Calculate total material cost for this BOM"""
        return sum(comp.total_cost for comp in self.components or [])
    
    @property
    def total_process_cost(self):
        """Calculate total process cost for this BOM"""
        return sum(proc.cost_per_unit * self.output_quantity for proc in self.processes or [])
    
    @property
    def total_bom_cost(self):
        """Calculate total BOM cost including materials and processes"""
        return self.total_material_cost + self.total_process_cost
    
    @property
    def cost_per_unit(self):
        """Calculate cost per output unit"""
        if self.output_quantity > 0:
            return self.total_bom_cost / self.output_quantity
        return 0.0
    
    def check_material_availability(self):
        """Check if all required materials are available in inventory"""
        shortages = []
        for component in self.components or []:
            available_qty = component.material.current_stock or 0
            required_qty = component.qty_required_with_scrap
            
            if available_qty < required_qty:
                shortages.append({
                    'material': component.material,
                    'required': required_qty,
                    'available': available_qty,
                    'shortage': required_qty - available_qty
                })
        return shortages
    
    def can_produce_quantity(self, production_qty=1):
        """Check how many units can be produced with current inventory"""
        min_possible = float('inf')
        
        for component in self.components or []:
            available_qty = component.material.current_stock or 0
            required_per_unit = component.qty_required_with_scrap / self.output_quantity
            possible_qty = available_qty / required_per_unit if required_per_unit > 0 else 0
            min_possible = min(min_possible, possible_qty)
        
        return max(0, int(min_possible)) if min_possible != float('inf') else 0

class BOMComponent(db.Model):
    __tablename__ = 'bom_components'
    
    id = db.Column(db.Integer, primary_key=True)
    bom_id = db.Column(db.Integer, db.ForeignKey('bill_of_materials.id'), nullable=False)
    material_id = db.Column(db.Integer, db.ForeignKey('items.id'), nullable=False)
    qty_required = db.Column(db.Float, nullable=False)
    uom_id = db.Column(db.Integer, db.ForeignKey('units_of_measure.id'), nullable=False)
    scrap_percent = db.Column(db.Float, default=0.0)
    process_step = db.Column(db.Integer, default=1)
    process_name = db.Column(db.String(100))
    rate_per_unit = db.Column(db.Float, default=0.0)
    default_supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.id'))
    is_critical = db.Column(db.Boolean, default=False)
    substitute_materials = db.Column(db.Text)  # JSON string of substitute material IDs
    remarks = db.Column(db.Text)
    
    # Relationships
    material = db.relationship('Item', foreign_keys=[material_id], backref='bom_material_components')
    uom = db.relationship('UnitOfMeasure', foreign_keys=[uom_id])  # type: ignore
    default_supplier = db.relationship('Supplier', foreign_keys=[default_supplier_id])
    
    def __repr__(self):
        return f'<BOMComponent: {self.material.name if self.material else "N/A"} - {self.qty_required}>'
    
    @property
    def qty_required_with_scrap(self):
        """Calculate quantity required including scrap allowance"""
        scrap_multiplier = 1 + (self.scrap_percent / 100)
        return self.qty_required * scrap_multiplier
    
    @property
    def total_cost(self):
        """Calculate total cost for this component"""
        return self.qty_required_with_scrap * (self.rate_per_unit or 0)
    
    @property
    def availability_status(self):
        """Check availability status of this component"""
        available_qty = self.material.current_stock or 0
        required_qty = self.qty_required_with_scrap
        
        if available_qty >= required_qty:
            return 'available'
        elif available_qty > 0:
            return 'partial'
        else:
            return 'shortage'

class BOMProcess(db.Model):
    __tablename__ = 'bom_processes'
    
    id = db.Column(db.Integer, primary_key=True)
    bom_id = db.Column(db.Integer, db.ForeignKey('bill_of_materials.id'), nullable=False)
    step_number = db.Column(db.Integer, nullable=False)
    process_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'))
    estimated_time_minutes = db.Column(db.Integer, default=0)
    cost_per_unit = db.Column(db.Float, default=0.0)
    default_supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.id'))
    quality_checkpoints = db.Column(db.Text)  # JSON string of quality checks
    is_outsourced = db.Column(db.Boolean, default=False)
    is_critical_path = db.Column(db.Boolean, default=False)
    
    # Relationships
    department = db.relationship('Department', foreign_keys=[department_id])
    default_supplier = db.relationship('Supplier', foreign_keys=[default_supplier_id])
    
    def __repr__(self):
        return f'<BOMProcess: Step {self.step_number} - {self.process_name}>'

class BOMVersion(db.Model):
    __tablename__ = 'bom_versions'
    
    id = db.Column(db.Integer, primary_key=True)
    bom_id = db.Column(db.Integer, db.ForeignKey('bill_of_materials.id'), nullable=False)
    version_number = db.Column(db.String(20), nullable=False)
    change_description = db.Column(db.Text)
    changed_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    change_date = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=False)
    approval_status = db.Column(db.String(20), default='pending')  # pending, approved, rejected
    approved_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    approval_date = db.Column(db.DateTime)
    
    # Relationships
    bom = db.relationship('BillOfMaterials', backref='versions')
    changed_by_user = db.relationship('User', foreign_keys=[changed_by])
    approved_by_user = db.relationship('User', foreign_keys=[approved_by])

class BOMCostHistory(db.Model):
    __tablename__ = 'bom_cost_history'
    
    id = db.Column(db.Integer, primary_key=True)
    bom_id = db.Column(db.Integer, db.ForeignKey('bill_of_materials.id'), nullable=False)
    calculation_date = db.Column(db.DateTime, default=datetime.utcnow)
    material_cost = db.Column(db.Float, default=0.0)
    process_cost = db.Column(db.Float, default=0.0)
    total_cost = db.Column(db.Float, default=0.0)
    cost_per_unit = db.Column(db.Float, default=0.0)
    calculated_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # Relationships
    bom = db.relationship('BillOfMaterials', backref='cost_history')
    calculated_by_user = db.relationship('User', foreign_keys=[calculated_by])