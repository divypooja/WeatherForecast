from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db

# Import UOM models
from models_uom import UnitOfMeasure, UOMConversion, ItemUOMConversion, UOMConversionLog

# Import permission models
from models_permissions import Permission, UserPermission

class CompanySettings(db.Model):
    __tablename__ = 'company_settings'
    
    id = db.Column(db.Integer, primary_key=True)
    company_name = db.Column(db.String(200), nullable=False, default='Your Company Name')
    address_line1 = db.Column(db.String(200), default='Your Company Address Line 1')
    address_line2 = db.Column(db.String(200), default='Your Company Address Line 2')
    city = db.Column(db.String(100), default='City')
    state = db.Column(db.String(100), default='State')
    pin_code = db.Column(db.String(10), default='PIN Code')
    phone = db.Column(db.String(20), default='+91-XXX-XXXXXXX')
    email = db.Column(db.String(120))
    gst_number = db.Column(db.String(50), default='XXAABCRXXXXMXZC')
    arn_number = db.Column(db.String(50), default='AAXXXXXXXGX')
    website = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    @classmethod
    def get_settings(cls):
        """Get company settings, create default if none exist"""
        settings = cls.query.first()
        if not settings:
            settings = cls()
            db.session.add(settings)
            db.session.commit()
        return settings

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='staff')  # admin, staff
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def is_admin(self):
        return self.role == 'admin'
    
    def has_permission(self, permission_code):
        """Check if user has a specific permission"""
        # Admins have all permissions
        if self.is_admin():
            return True
        
        # Check user-specific permissions
        from models_permissions import Permission, UserPermission
        permission = Permission.query.filter_by(code=permission_code).first()
        if not permission:
            return False
        
        user_permission = UserPermission.query.filter_by(
            user_id=self.id,
            permission_id=permission.id,
            granted=True
        ).first()
        
        return user_permission is not None
    
    def get_permissions(self):
        """Get all permissions for this user"""
        if self.is_admin():
            from models_permissions import Permission
            return Permission.query.all()
        
        from models_permissions import Permission, UserPermission
        return db.session.query(Permission).join(UserPermission).filter(
            UserPermission.user_id == self.id,
            UserPermission.granted == True
        ).all()
    
    def grant_permission(self, permission_code, granted_by_user_id):
        """Grant a permission to this user"""
        from models_permissions import Permission, UserPermission
        permission = Permission.query.filter_by(code=permission_code).first()
        if not permission:
            return False
        
        # Check if permission already exists
        existing = UserPermission.query.filter_by(
            user_id=self.id,
            permission_id=permission.id
        ).first()
        
        if existing:
            existing.granted = True
            existing.granted_by = granted_by_user_id
            existing.granted_at = datetime.utcnow()
        else:
            user_permission = UserPermission(
                user_id=self.id,
                permission_id=permission.id,
                granted=True,
                granted_by=granted_by_user_id
            )
            db.session.add(user_permission)
        
        return True
    
    def revoke_permission(self, permission_code):
        """Revoke a permission from this user"""
        from models_permissions import Permission, UserPermission
        permission = Permission.query.filter_by(code=permission_code).first()
        if not permission:
            return False
        
        user_permission = UserPermission.query.filter_by(
            user_id=self.id,
            permission_id=permission.id
        ).first()
        
        if user_permission:
            user_permission.granted = False
        
        return True

class Supplier(db.Model):
    __tablename__ = 'suppliers'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Basic Information
    name = db.Column(db.String(200), nullable=False)  # Full legal name
    contact_person = db.Column(db.String(100))  # Person to contact
    phone = db.Column(db.String(20))  # Mobile number
    email = db.Column(db.String(120))  # Email for orders/inquiries
    
    # Compliance Information
    gst_number = db.Column(db.String(50))  # GSTIN (mandatory for GST)
    pan_number = db.Column(db.String(20))  # PAN (optional, for compliance)
    
    # Address Information
    address = db.Column(db.Text)  # Full postal address
    city = db.Column(db.String(100))
    state = db.Column(db.String(100))
    pin_code = db.Column(db.String(10))
    
    # Banking Information (optional, for payments)
    account_number = db.Column(db.String(50))
    bank_name = db.Column(db.String(200))
    ifsc_code = db.Column(db.String(20))
    
    # Partner Type - can be 'supplier', 'customer', or 'both'
    partner_type = db.Column(db.String(20), default='supplier')  # supplier, customer, both
    
    # Additional Information
    remarks = db.Column(db.Text)  # Any notes
    is_active = db.Column(db.Boolean, default=True)  # Partner status
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    purchase_orders = db.relationship('PurchaseOrder', backref='supplier', lazy=True)
    sales_orders = db.relationship('SalesOrder', backref='customer', foreign_keys='SalesOrder.customer_id', lazy=True)
    
    @property
    def is_supplier(self):
        return self.partner_type in ['supplier', 'both']
    
    @property
    def is_customer(self):
        return self.partner_type in ['customer', 'both']

# Customer model removed - now using unified Supplier table for all business partners

class Item(db.Model):
    __tablename__ = 'items'
    
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    unit_of_measure = db.Column(db.String(20), nullable=False)  # kg, pcs, meter, etc.
    hsn_code = db.Column(db.String(20))  # HSN Code for GST
    gst_rate = db.Column(db.Float, default=0.0)  # GST rate (can be 0%, 5%, 12%, 18%, 28% etc.)
    current_stock = db.Column(db.Float, default=0.0)
    minimum_stock = db.Column(db.Float, default=0.0)
    unit_price = db.Column(db.Float, default=0.0)
    item_type = db.Column(db.String(20), default='material')  # material, product, consumable
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    purchase_order_items = db.relationship('PurchaseOrderItem', backref='item', lazy=True)
    sales_order_items = db.relationship('SalesOrderItem', backref='item', lazy=True)
    bom_items = db.relationship('BOMItem', backref='item', lazy=True)

class PurchaseOrder(db.Model):
    __tablename__ = 'purchase_orders'
    
    id = db.Column(db.Integer, primary_key=True)
    po_number = db.Column(db.String(50), unique=True, nullable=False)
    supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.id'), nullable=False)
    order_date = db.Column(db.Date, nullable=False, default=datetime.utcnow().date())
    expected_date = db.Column(db.Date)
    payment_terms = db.Column(db.String(50), default='30 Days')  # Payment terms like "30 Days"
    freight_terms = db.Column(db.String(100))  # Freight terms
    delivery_notes = db.Column(db.Text)  # Special delivery instructions
    validity_months = db.Column(db.Integer, default=6)  # PO validity in months
    status = db.Column(db.String(20), default='open')  # draft, open, partial, closed, cancelled
    subtotal = db.Column(db.Float, default=0.0)
    gst_amount = db.Column(db.Float, default=0.0)
    total_amount = db.Column(db.Float, default=0.0)
    notes = db.Column(db.Text)
    prepared_by = db.Column(db.String(100))  # Name of person who prepared
    verified_by = db.Column(db.String(100))  # Name of person who verified
    approved_by = db.Column(db.String(100))  # Name of person who approved
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Tally integration
    tally_synced = db.Column(db.Boolean, default=False)
    
    # Inspection workflow fields
    inspection_required = db.Column(db.Boolean, default=True)
    inspection_status = db.Column(db.String(20), default='pending')  # pending, in_progress, completed, failed
    inspected_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    inspected_at = db.Column(db.DateTime)
    
    # Relationships
    items = db.relationship('PurchaseOrderItem', backref='purchase_order', lazy=True, cascade='all, delete-orphan')
    delivery_schedules = db.relationship('DeliverySchedule', backref='purchase_order', lazy=True, cascade='all, delete-orphan')
    creator = db.relationship('User', foreign_keys=[created_by], backref='created_purchase_orders')
    inspector = db.relationship('User', foreign_keys=[inspected_by], backref='inspected_purchase_orders')
    material_inspections = db.relationship('MaterialInspection', backref='purchase_order', lazy=True, cascade='all, delete-orphan')

class PurchaseOrderItem(db.Model):
    __tablename__ = 'purchase_order_items'
    
    id = db.Column(db.Integer, primary_key=True)
    purchase_order_id = db.Column(db.Integer, db.ForeignKey('purchase_orders.id'), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('items.id'), nullable=False)
    sr_no = db.Column(db.Integer)  # Serial Number (No.)
    rm_code = db.Column(db.String(50))  # RM Code (Raw Material Code)
    item_description = db.Column(db.Text)  # Item + Description
    drawing_spec_no = db.Column(db.String(100))  # Drawing / Spec Sheet No.
    hsn_code = db.Column(db.String(20))  # HSN Code
    gst_rate = db.Column(db.Float, default=18.0)  # GST Rate %
    uom = db.Column(db.String(20))  # UOM (Unit of Measure)
    qty = db.Column(db.Float, nullable=False)  # Qty (Quantity)
    rate = db.Column(db.Float, nullable=False)  # Rate (per unit)
    amount = db.Column(db.Float, nullable=False)  # Amount (qty × rate)
    # Legacy fields for compatibility
    quantity_ordered = db.Column(db.Float, nullable=False)
    quantity_received = db.Column(db.Float, default=0.0)
    unit_price = db.Column(db.Float, nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class SalesOrder(db.Model):
    __tablename__ = 'sales_orders'
    
    id = db.Column(db.Integer, primary_key=True)
    so_number = db.Column(db.String(50), unique=True, nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('suppliers.id'), nullable=False)
    order_date = db.Column(db.Date, nullable=False, default=datetime.utcnow().date())
    delivery_date = db.Column(db.Date)
    payment_terms = db.Column(db.String(100))
    freight_terms = db.Column(db.String(100))
    validity_months = db.Column(db.Integer)
    prepared_by = db.Column(db.String(100))
    verified_by = db.Column(db.String(100))
    approved_by = db.Column(db.String(100))
    delivery_notes = db.Column(db.Text)
    status = db.Column(db.String(20), default='draft')  # draft, confirmed, delivered, cancelled
    total_amount = db.Column(db.Float, default=0.0)
    notes = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Tally integration
    tally_synced = db.Column(db.Boolean, default=False)
    
    # Relationships
    items = db.relationship('SalesOrderItem', backref='sales_order', lazy=True, cascade='all, delete-orphan')
    creator = db.relationship('User', backref='created_sales_orders')

class SalesOrderItem(db.Model):
    __tablename__ = 'sales_order_items'
    
    id = db.Column(db.Integer, primary_key=True)
    sales_order_id = db.Column(db.Integer, db.ForeignKey('sales_orders.id'), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('items.id'), nullable=False)
    quantity_ordered = db.Column(db.Float, nullable=False)
    quantity_delivered = db.Column(db.Float, default=0.0)
    unit_price = db.Column(db.Float, nullable=False)
    total_price = db.Column(db.Float, nullable=False)

class Employee(db.Model):
    __tablename__ = 'employees'
    
    id = db.Column(db.Integer, primary_key=True)
    employee_code = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    designation = db.Column(db.String(100))
    department = db.Column(db.String(100))
    salary_type = db.Column(db.String(20), nullable=False)  # daily, monthly, piece_rate
    rate = db.Column(db.Float, nullable=False)  # daily rate, monthly salary, or per piece rate
    phone = db.Column(db.String(20))
    address = db.Column(db.Text)
    joining_date = db.Column(db.Date, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    salary_records = db.relationship('SalaryRecord', backref='employee', lazy=True, cascade='all, delete-orphan')
    advances = db.relationship('EmployeeAdvance', backref='employee', lazy=True, cascade='all, delete-orphan')
    
    @staticmethod
    def generate_employee_code():
        """Generate unique employee code"""
        last_employee = Employee.query.order_by(Employee.id.desc()).first()
        if last_employee:
            # Extract number from code like "EMP-0001"
            try:
                last_num = int(last_employee.employee_code.split('-')[-1])
                next_num = last_num + 1
            except (ValueError, IndexError):
                next_num = 1
        else:
            next_num = 1
        return f"EMP-{next_num:04d}"

class JobWork(db.Model):
    __tablename__ = 'job_works'
    
    id = db.Column(db.Integer, primary_key=True)
    job_number = db.Column(db.String(50), unique=True, nullable=False)
    customer_name = db.Column(db.String(100), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('items.id'), nullable=False)
    quantity_sent = db.Column(db.Float, nullable=False)
    quantity_received = db.Column(db.Float, default=0.0)
    rate_per_unit = db.Column(db.Float, nullable=False)
    sent_date = db.Column(db.Date, nullable=False, default=datetime.utcnow().date())
    received_date = db.Column(db.Date)
    expected_return = db.Column(db.Date)
    status = db.Column(db.String(20), default='sent')  # sent, partial_received, completed
    notes = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Inspection workflow fields
    inspection_required = db.Column(db.Boolean, default=True)
    inspection_status = db.Column(db.String(20), default='pending')  # pending, in_progress, completed, failed
    inspected_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    inspected_at = db.Column(db.DateTime)
    
    # Relationships
    item = db.relationship('Item', backref='job_works')
    creator = db.relationship('User', foreign_keys=[created_by], backref='created_job_works')
    inspector = db.relationship('User', foreign_keys=[inspected_by], backref='inspected_job_works')

class Production(db.Model):
    __tablename__ = 'productions'
    
    id = db.Column(db.Integer, primary_key=True)
    production_number = db.Column(db.String(50), unique=True, nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('items.id'), nullable=False)
    quantity_planned = db.Column(db.Float, nullable=False)
    quantity_produced = db.Column(db.Float, default=0.0)
    quantity_good = db.Column(db.Float, default=0.0)  # Good quality items
    quantity_damaged = db.Column(db.Float, default=0.0)  # Damaged/defective items
    production_date = db.Column(db.Date, nullable=False, default=datetime.utcnow().date())
    status = db.Column(db.String(20), default='planned')  # planned, in_progress, completed
    notes = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    produced_item = db.relationship('Item', backref='productions')
    creator = db.relationship('User', backref='created_productions')
    quality_issues = db.relationship('QualityIssue', backref='production', lazy=True, cascade='all, delete-orphan')

class BOM(db.Model):
    __tablename__ = 'boms'
    
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('items.id'), nullable=False)
    version = db.Column(db.String(20), default='1.0')
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    product = db.relationship('Item', backref='boms')
    items = db.relationship('BOMItem', backref='bom', lazy=True, cascade='all, delete-orphan')

class BOMItem(db.Model):
    __tablename__ = 'bom_items'
    
    id = db.Column(db.Integer, primary_key=True)
    bom_id = db.Column(db.Integer, db.ForeignKey('boms.id'), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('items.id'), nullable=False)
    quantity_required = db.Column(db.Float, nullable=False)
    unit_cost = db.Column(db.Float, default=0.0)

class QualityIssue(db.Model):
    __tablename__ = 'quality_issues'
    
    id = db.Column(db.Integer, primary_key=True)
    issue_number = db.Column(db.String(50), unique=True, nullable=False)
    production_id = db.Column(db.Integer, db.ForeignKey('productions.id'), nullable=True)
    item_id = db.Column(db.Integer, db.ForeignKey('items.id'), nullable=False)
    issue_type = db.Column(db.String(50), nullable=False)  # damage, malfunction, defect, contamination
    severity = db.Column(db.String(20), nullable=False)  # low, medium, high, critical
    quantity_affected = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text, nullable=False)
    root_cause = db.Column(db.Text)
    corrective_action = db.Column(db.Text)
    preventive_action = db.Column(db.Text)
    status = db.Column(db.String(20), default='open')  # open, investigating, resolved, closed
    detected_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    assigned_to = db.Column(db.Integer, db.ForeignKey('users.id'))
    detected_date = db.Column(db.DateTime, default=datetime.utcnow)
    resolved_date = db.Column(db.DateTime)
    cost_impact = db.Column(db.Float, default=0.0)  # Financial impact
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    item = db.relationship('Item', backref='quality_issues')
    detector = db.relationship('User', foreign_keys=[detected_by], backref='detected_issues')
    assignee = db.relationship('User', foreign_keys=[assigned_to], backref='assigned_issues')

class QualityControlLog(db.Model):
    __tablename__ = 'quality_control_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    production_id = db.Column(db.Integer, db.ForeignKey('productions.id'), nullable=False)
    inspection_date = db.Column(db.DateTime, default=datetime.utcnow)
    inspector_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    batch_number = db.Column(db.String(50))
    total_inspected = db.Column(db.Float, nullable=False)
    passed_quantity = db.Column(db.Float, nullable=False)
    failed_quantity = db.Column(db.Float, nullable=False)
    rejection_rate = db.Column(db.Float, nullable=False)  # Percentage
    inspection_notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    production_ref = db.relationship('Production', backref='quality_logs')
    inspector = db.relationship('User', backref='quality_inspections')

class NotificationSettings(db.Model):
    __tablename__ = 'notification_settings'
    
    id = db.Column(db.Integer, primary_key=True)
    # Email settings
    email_enabled = db.Column(db.Boolean, default=True)
    sendgrid_api_key = db.Column(db.String(255))
    sender_email = db.Column(db.String(120), default='noreply@akfactory.com')
    sender_name = db.Column(db.String(100), default='AK Innovations Factory')
    
    # SMS/WhatsApp settings
    sms_enabled = db.Column(db.Boolean, default=True)
    whatsapp_enabled = db.Column(db.Boolean, default=True)
    twilio_account_sid = db.Column(db.String(255))
    twilio_auth_token = db.Column(db.String(255))
    twilio_phone_number = db.Column(db.String(20))
    
    # Notification preferences
    low_stock_notifications = db.Column(db.Boolean, default=True)
    order_status_notifications = db.Column(db.Boolean, default=True)
    production_notifications = db.Column(db.Boolean, default=True)
    
    # Recipients
    admin_email = db.Column(db.String(120))
    admin_phone = db.Column(db.String(20))
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class NotificationLog(db.Model):
    __tablename__ = 'notification_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(20), nullable=False)  # email, sms, whatsapp
    recipient = db.Column(db.String(255), nullable=False)
    subject = db.Column(db.String(255))
    message = db.Column(db.Text)
    success = db.Column(db.Boolean, nullable=False)
    response = db.Column(db.Text)
    sent_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Optional: Link to specific events
    event_type = db.Column(db.String(50))  # low_stock, order_update, production_complete
    event_id = db.Column(db.Integer)  # ID of the related record

class NotificationRecipient(db.Model):
    __tablename__ = 'notification_recipients'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120))
    phone = db.Column(db.String(20))
    notification_types = db.Column(db.String(100))  # comma-separated: email,sms,whatsapp
    event_types = db.Column(db.String(200))  # comma-separated: low_stock,order_update,production
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class DeliverySchedule(db.Model):
    __tablename__ = 'delivery_schedules'
    
    id = db.Column(db.Integer, primary_key=True)
    purchase_order_id = db.Column(db.Integer, db.ForeignKey('purchase_orders.id'), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('items.id'), nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    delivery_date = db.Column(db.Date, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    item = db.relationship('Item', backref='delivery_schedules')

class MaterialInspection(db.Model):
    __tablename__ = 'material_inspections'
    
    id = db.Column(db.Integer, primary_key=True)
    inspection_number = db.Column(db.String(50), unique=True, nullable=False)
    purchase_order_id = db.Column(db.Integer, db.ForeignKey('purchase_orders.id'), nullable=True)
    job_work_id = db.Column(db.Integer, db.ForeignKey('job_works.id'), nullable=True)
    item_id = db.Column(db.Integer, db.ForeignKey('items.id'), nullable=False)
    received_quantity = db.Column(db.Float, nullable=False)
    inspected_quantity = db.Column(db.Float, nullable=False)
    passed_quantity = db.Column(db.Float, nullable=False)
    damaged_quantity = db.Column(db.Float, nullable=False)
    rejected_quantity = db.Column(db.Float, nullable=False)
    acceptance_rate = db.Column(db.Float, nullable=False)  # Percentage of accepted quantity
    damage_types = db.Column(db.Text)  # JSON or comma-separated damage types
    rejection_reasons = db.Column(db.Text)  # Reasons for rejection
    inspection_notes = db.Column(db.Text)
    inspector_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    inspection_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='completed')  # pending, in_progress, completed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    item = db.relationship('Item', backref='material_inspections')
    inspector = db.relationship('User', backref='material_inspections')
    job_work = db.relationship('JobWork', backref='material_inspections')

class FactoryExpense(db.Model):
    __tablename__ = 'factory_expenses'
    
    id = db.Column(db.Integer, primary_key=True)
    expense_number = db.Column(db.String(50), unique=True, nullable=False)  # EXP-YYYY-0001
    
    # Basic Details
    expense_date = db.Column(db.Date, nullable=False)
    category = db.Column(db.String(50), nullable=False)  # utilities, maintenance, salary, materials, overhead, transport, others
    subcategory = db.Column(db.String(100))  # electricity, water, repair, cleaning, etc.
    description = db.Column(db.String(500), nullable=False)
    
    # Financial Details
    amount = db.Column(db.Numeric(15, 2), nullable=False)
    tax_amount = db.Column(db.Numeric(15, 2), default=0.0)
    total_amount = db.Column(db.Numeric(15, 2), nullable=False)
    payment_method = db.Column(db.String(50))  # cash, bank_transfer, cheque, upi, card
    paid_by = db.Column(db.String(100))  # person/entity who made the payment
    
    # Vendor/Supplier Details (optional)
    vendor_name = db.Column(db.String(200))
    vendor_contact = db.Column(db.String(100))
    invoice_number = db.Column(db.String(100))
    invoice_date = db.Column(db.Date)
    
    # Approval and Processing
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected, paid
    requested_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    approved_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    approval_date = db.Column(db.DateTime)
    payment_date = db.Column(db.Date)
    
    # Documentation
    receipt_path = db.Column(db.String(500))  # Path to uploaded receipt/invoice
    notes = db.Column(db.Text)
    
    # Recurring Expense Support
    is_recurring = db.Column(db.Boolean, default=False)
    recurring_frequency = db.Column(db.String(20))  # monthly, quarterly, yearly
    parent_expense_id = db.Column(db.Integer, db.ForeignKey('factory_expenses.id'))
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Tally integration
    tally_synced = db.Column(db.Boolean, default=False)
    
    # Relationships
    requested_by = db.relationship('User', foreign_keys=[requested_by_id], backref='requested_expenses')
    approved_by = db.relationship('User', foreign_keys=[approved_by_id], backref='approved_expenses')
    child_expenses = db.relationship('FactoryExpense', backref=db.backref('parent_expense', remote_side=[id]))
    
    @classmethod
    def generate_expense_number(cls):
        """Generate next expense number in format EXP-YYYY-0001"""
        from datetime import datetime
        current_year = datetime.now().year
        
        # Find the latest expense number for current year
        latest_expense = cls.query.filter(
            cls.expense_number.like(f'EXP-{current_year}-%')
        ).order_by(cls.expense_number.desc()).first()
        
        if latest_expense:
            # Extract the sequence number and increment
            last_sequence = int(latest_expense.expense_number.split('-')[-1])
            next_sequence = last_sequence + 1
        else:
            next_sequence = 1
        
        return f'EXP-{current_year}-{next_sequence:04d}'
    
    @property
    def category_display(self):
        """Return user-friendly category name"""
        categories = {
            'utilities': 'Utilities & Infrastructure',
            'maintenance': 'Maintenance & Repairs',
            'salary': 'Salaries & Benefits',
            'materials': 'Raw Materials & Supplies',
            'overhead': 'Factory Overhead',
            'transport': 'Transportation & Logistics',
            'others': 'Other Expenses'
        }
        return categories.get(self.category, self.category.title())
    
    @property
    def status_badge_class(self):
        """Return Bootstrap badge class for status"""
        status_classes = {
            'pending': 'bg-warning',
            'approved': 'bg-success',
            'rejected': 'bg-danger',
            'paid': 'bg-primary'
        }
        return status_classes.get(self.status, 'bg-secondary')

class SalaryRecord(db.Model):
    __tablename__ = 'salary_records'
    
    id = db.Column(db.Integer, primary_key=True)
    salary_number = db.Column(db.String(50), unique=True, nullable=False)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    pay_period_start = db.Column(db.Date, nullable=False)
    pay_period_end = db.Column(db.Date, nullable=False)
    basic_amount = db.Column(db.Float, nullable=False)
    overtime_hours = db.Column(db.Float, default=0.0)
    overtime_rate = db.Column(db.Float, default=0.0)
    overtime_amount = db.Column(db.Float, default=0.0)
    bonus_amount = db.Column(db.Float, default=0.0)
    deduction_amount = db.Column(db.Float, default=0.0)
    advance_deduction = db.Column(db.Float, default=0.0)  # Auto-deducted from advances
    gross_amount = db.Column(db.Float, nullable=False)
    net_amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, approved, paid
    payment_date = db.Column(db.Date)
    payment_method = db.Column(db.String(50))  # cash, bank_transfer, cheque
    notes = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    approved_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    approved_at = db.Column(db.DateTime)
    
    # Relationships
    creator = db.relationship('User', foreign_keys=[created_by], backref='created_salary_records')
    approver = db.relationship('User', foreign_keys=[approved_by], backref='approved_salary_records')
    
    @staticmethod
    def generate_salary_number():
        """Generate unique salary record number"""
        from datetime import datetime
        year = datetime.now().year
        last_record = SalaryRecord.query.filter(
            SalaryRecord.salary_number.like(f'SAL-{year}-%')
        ).order_by(SalaryRecord.id.desc()).first()
        
        if last_record:
            try:
                last_num = int(last_record.salary_number.split('-')[-1])
                next_num = last_num + 1
            except (ValueError, IndexError):
                next_num = 1
        else:
            next_num = 1
        
        return f"SAL-{year}-{next_num:04d}"

class EmployeeAdvance(db.Model):
    __tablename__ = 'employee_advances'
    
    id = db.Column(db.Integer, primary_key=True)
    advance_number = db.Column(db.String(50), unique=True, nullable=False)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    remaining_amount = db.Column(db.Float, nullable=False)  # Amount yet to be deducted
    reason = db.Column(db.String(200), nullable=False)
    advance_date = db.Column(db.Date, nullable=False, default=datetime.utcnow().date())
    repayment_months = db.Column(db.Integer, default=1)  # Number of months to deduct
    monthly_deduction = db.Column(db.Float, nullable=False)  # Amount to deduct per month
    status = db.Column(db.String(20), default='pending')  # pending, approved, active, completed, cancelled
    payment_method = db.Column(db.String(50))  # cash, bank_transfer, cheque
    notes = db.Column(db.Text)
    requested_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    approved_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    approved_at = db.Column(db.DateTime)
    
    # Relationships
    requester = db.relationship('User', foreign_keys=[requested_by], backref='requested_advances')
    approver = db.relationship('User', foreign_keys=[approved_by], backref='approved_advances')
    
    @staticmethod
    def generate_advance_number():
        """Generate unique advance number"""
        from datetime import datetime
        year = datetime.now().year
        last_advance = EmployeeAdvance.query.filter(
            EmployeeAdvance.advance_number.like(f'ADV-{year}-%')
        ).order_by(EmployeeAdvance.id.desc()).first()
        
        if last_advance:
            try:
                last_num = int(last_advance.advance_number.split('-')[-1])
                next_num = last_num + 1
            except (ValueError, IndexError):
                next_num = 1
        else:
            next_num = 1
        
        return f"ADV-{year}-{next_num:04d}"
    
    def __repr__(self):
        return f'<EmployeeAdvance {self.advance_number}>'

class Document(db.Model):
    __tablename__ = 'documents'
    
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_size = db.Column(db.Integer, nullable=False)
    file_type = db.Column(db.String(50), nullable=False)
    upload_path = db.Column(db.String(500), nullable=False)
    
    # Transaction association
    transaction_type = db.Column(db.String(50), nullable=False)  # 'purchase_order', 'sales_order', 'job_work', etc.
    transaction_id = db.Column(db.Integer, nullable=False)
    
    # Document metadata
    document_category = db.Column(db.String(100), nullable=False)  # 'invoice', 'receipt', 'contract', 'specification', etc.
    description = db.Column(db.Text)
    
    # Audit fields
    uploaded_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    uploader = db.relationship('User', backref='uploaded_documents')
    
    def __repr__(self):
        return f'<Document {self.original_filename}>'
    
    @property
    def file_size_mb(self):
        return round(self.file_size / (1024 * 1024), 2)
    
    def get_file_path(self):
        import os
        return os.path.join('uploads', self.upload_path)
