from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db

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

class Supplier(db.Model):
    __tablename__ = 'suppliers'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    contact_person = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    email = db.Column(db.String(120))
    address = db.Column(db.Text)
    gst_number = db.Column(db.String(50))  # GST registration number
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    purchase_orders = db.relationship('PurchaseOrder', backref='supplier', lazy=True)

class Customer(db.Model):
    __tablename__ = 'customers'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    contact_person = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    email = db.Column(db.String(120))
    address = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    sales_orders = db.relationship('SalesOrder', backref='customer', lazy=True)

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
    status = db.Column(db.String(20), default='open')  # open, partial, closed, cancelled
    subtotal = db.Column(db.Float, default=0.0)
    gst_amount = db.Column(db.Float, default=0.0)
    total_amount = db.Column(db.Float, default=0.0)
    notes = db.Column(db.Text)
    prepared_by = db.Column(db.String(100))  # Name of person who prepared
    verified_by = db.Column(db.String(100))  # Name of person who verified
    approved_by = db.Column(db.String(100))  # Name of person who approved
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    items = db.relationship('PurchaseOrderItem', backref='purchase_order', lazy=True, cascade='all, delete-orphan')
    delivery_schedules = db.relationship('DeliverySchedule', backref='purchase_order', lazy=True, cascade='all, delete-orphan')
    creator = db.relationship('User', backref='created_purchase_orders')

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
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    order_date = db.Column(db.Date, nullable=False, default=datetime.utcnow().date())
    delivery_date = db.Column(db.Date)
    status = db.Column(db.String(20), default='pending')  # pending, partial, completed, cancelled
    total_amount = db.Column(db.Float, default=0.0)
    notes = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
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

class JobWork(db.Model):
    __tablename__ = 'job_works'
    
    id = db.Column(db.Integer, primary_key=True)
    job_number = db.Column(db.String(50), unique=True, nullable=False)
    customer_name = db.Column(db.String(100), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('items.id'), nullable=False)
    quantity_sent = db.Column(db.Float, nullable=False)
    rate_per_unit = db.Column(db.Float, nullable=False)
    sent_date = db.Column(db.Date, nullable=False, default=datetime.utcnow().date())
    expected_return = db.Column(db.Date)
    status = db.Column(db.String(20), default='sent')  # sent, partial_received, completed
    notes = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    item = db.relationship('Item', backref='job_works')
    creator = db.relationship('User', backref='created_job_works')

class Production(db.Model):
    __tablename__ = 'productions'
    
    id = db.Column(db.Integer, primary_key=True)
    production_number = db.Column(db.String(50), unique=True, nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('items.id'), nullable=False)
    quantity_planned = db.Column(db.Float, nullable=False)
    quantity_produced = db.Column(db.Float, default=0.0)
    production_date = db.Column(db.Date, nullable=False, default=datetime.utcnow().date())
    status = db.Column(db.String(20), default='planned')  # planned, in_progress, completed
    notes = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    produced_item = db.relationship('Item', backref='productions')
    creator = db.relationship('User', backref='created_productions')

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
