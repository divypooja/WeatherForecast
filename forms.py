from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, TextAreaField, FloatField, IntegerField, DateField, BooleanField, SelectMultipleField
from wtforms.validators import DataRequired, Length, Email, NumberRange, Optional, ValidationError
from wtforms.widgets import CheckboxInput, ListWidget
from models import User, Item, Supplier, Customer

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=25)])
    password = PasswordField('Password', validators=[DataRequired()])

class ItemForm(FlaskForm):
    code = StringField('Item Code', validators=[DataRequired(), Length(max=50)])
    name = StringField('Item Name', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Description')
    unit_of_measure = SelectField('Unit of Measure', 
                                choices=[('pcs', 'Pieces'), ('kg', 'Kilograms'), ('meter', 'Meters'), 
                                       ('liter', 'Liters'), ('box', 'Boxes'), ('set', 'Sets')],
                                validators=[DataRequired()])
    current_stock = FloatField('Current Stock', validators=[NumberRange(min=0)], default=0.0)
    minimum_stock = FloatField('Minimum Stock', validators=[NumberRange(min=0)], default=0.0)
    unit_price = FloatField('Unit Price', validators=[NumberRange(min=0)], default=0.0)
    item_type = SelectField('Item Type', 
                          choices=[('material', 'Material'), ('product', 'Product'), ('consumable', 'Consumable')],
                          validators=[DataRequired()])

class SupplierForm(FlaskForm):
    name = StringField('Supplier Name', validators=[DataRequired(), Length(max=100)])
    contact_person = StringField('Contact Person', validators=[Length(max=100)])
    phone = StringField('Phone', validators=[Length(max=20)])
    email = StringField('Email', validators=[Optional(), Email(), Length(max=120)])
    address = TextAreaField('Address')

class CustomerForm(FlaskForm):
    name = StringField('Customer Name', validators=[DataRequired(), Length(max=100)])
    contact_person = StringField('Contact Person', validators=[Length(max=100)])
    phone = StringField('Phone', validators=[Length(max=20)])
    email = StringField('Email', validators=[Optional(), Email(), Length(max=120)])
    address = TextAreaField('Address')

class PurchaseOrderForm(FlaskForm):
    supplier_id = SelectField('Supplier', validators=[DataRequired()], coerce=int)
    po_number = StringField('PO Number', validators=[DataRequired(), Length(max=50)])
    order_date = DateField('Order Date', validators=[DataRequired()])
    expected_delivery = DateField('Expected Delivery')
    notes = TextAreaField('Notes')
    
    def __init__(self, *args, **kwargs):
        super(PurchaseOrderForm, self).__init__(*args, **kwargs)
        self.supplier_id.choices = [(0, 'Select Supplier')] + [(s.id, s.name) for s in Supplier.query.all()]

class SalesOrderForm(FlaskForm):
    customer_id = SelectField('Customer', validators=[DataRequired()], coerce=int)
    so_number = StringField('SO Number', validators=[DataRequired(), Length(max=50)])
    order_date = DateField('Order Date', validators=[DataRequired()])
    delivery_date = DateField('Delivery Date')
    notes = TextAreaField('Notes')
    
    def __init__(self, *args, **kwargs):
        super(SalesOrderForm, self).__init__(*args, **kwargs)
        self.customer_id.choices = [(0, 'Select Customer')] + [(c.id, c.name) for c in Customer.query.all()]

class EmployeeForm(FlaskForm):
    employee_id = StringField('Employee ID', validators=[DataRequired(), Length(max=20)])
    name = StringField('Name', validators=[DataRequired(), Length(max=100)])
    department = StringField('Department', validators=[DataRequired(), Length(max=50)])
    position = StringField('Position', validators=[DataRequired(), Length(max=50)])
    phone = StringField('Phone', validators=[Length(max=20)])
    email = StringField('Email', validators=[Optional(), Email(), Length(max=120)])
    hire_date = DateField('Hire Date', validators=[DataRequired()])
    salary = FloatField('Salary', validators=[NumberRange(min=0)])
    is_active = BooleanField('Active', default=True)

class JobWorkForm(FlaskForm):
    job_number = StringField('Job Number', validators=[DataRequired(), Length(max=50)])
    customer_name = StringField('Customer Name', validators=[DataRequired(), Length(max=100)])
    item_id = SelectField('Item', validators=[DataRequired()], coerce=int)
    quantity_sent = FloatField('Quantity Sent', validators=[DataRequired(), NumberRange(min=0)])
    rate_per_unit = FloatField('Rate per Unit', validators=[DataRequired(), NumberRange(min=0)])
    sent_date = DateField('Sent Date', validators=[DataRequired()])
    expected_return = DateField('Expected Return Date')
    notes = TextAreaField('Notes')
    
    def __init__(self, *args, **kwargs):
        super(JobWorkForm, self).__init__(*args, **kwargs)
        self.item_id.choices = [(0, 'Select Item')] + [(i.id, f"{i.code} - {i.name}") for i in Item.query.all()]

class ProductionForm(FlaskForm):
    production_number = StringField('Production Number', validators=[DataRequired(), Length(max=50)])
    item_id = SelectField('Item to Produce', validators=[DataRequired()], coerce=int)
    quantity_planned = FloatField('Quantity Planned', validators=[DataRequired(), NumberRange(min=0)])
    start_date = DateField('Start Date', validators=[DataRequired()])
    target_completion = DateField('Target Completion')
    notes = TextAreaField('Notes')
    
    def __init__(self, *args, **kwargs):
        super(ProductionForm, self).__init__(*args, **kwargs)
        self.item_id.choices = [(0, 'Select Item')] + [(i.id, f"{i.code} - {i.name}") for i in Item.query.filter_by(item_type='product').all()]

class BOMForm(FlaskForm):
    product_id = SelectField('Product', validators=[DataRequired()], coerce=int)
    version = StringField('Version', validators=[DataRequired(), Length(max=20)], default='1.0')
    
    def __init__(self, *args, **kwargs):
        super(BOMForm, self).__init__(*args, **kwargs)
        self.product_id.choices = [(0, 'Select Product')] + [(i.id, f"{i.code} - {i.name}") for i in Item.query.filter_by(item_type='product').all()]

class BOMItemForm(FlaskForm):
    item_id = SelectField('Material/Component', validators=[DataRequired()], coerce=int)
    quantity_required = FloatField('Quantity Required', validators=[DataRequired(), NumberRange(min=0)])
    unit_cost = FloatField('Unit Cost', validators=[NumberRange(min=0)], default=0.0)
    
    def __init__(self, *args, **kwargs):
        super(BOMItemForm, self).__init__(*args, **kwargs)
        self.item_id.choices = [(0, 'Select Material/Component')] + [(i.id, f"{i.code} - {i.name}") for i in Item.query.filter(Item.item_type.in_(['material', 'consumable'])).all()]

# Notification Forms
class MultiCheckboxField(SelectMultipleField):
    widget = ListWidget(prefix_label=False)
    option_widget = CheckboxInput()

class NotificationSettingsForm(FlaskForm):
    # Email settings
    email_enabled = BooleanField('Enable Email Notifications', default=True)
    sendgrid_api_key = StringField('SendGrid API Key', validators=[Optional(), Length(max=255)])
    sender_email = StringField('Sender Email', validators=[Optional(), Email(), Length(max=120)], default='noreply@akfactory.com')
    sender_name = StringField('Sender Name', validators=[Optional(), Length(max=100)], default='AK Innovations Factory')
    
    # SMS/WhatsApp settings
    sms_enabled = BooleanField('Enable SMS Notifications', default=True)
    whatsapp_enabled = BooleanField('Enable WhatsApp Notifications', default=True)
    twilio_account_sid = StringField('Twilio Account SID', validators=[Optional(), Length(max=255)])
    twilio_auth_token = StringField('Twilio Auth Token', validators=[Optional(), Length(max=255)])
    twilio_phone_number = StringField('Twilio Phone Number', validators=[Optional(), Length(max=20)])
    
    # Notification preferences
    low_stock_notifications = BooleanField('Low Stock Alerts', default=True)
    order_status_notifications = BooleanField('Order Status Updates', default=True)
    production_notifications = BooleanField('Production Updates', default=True)
    
    # Admin recipients
    admin_email = StringField('Admin Email', validators=[Optional(), Email(), Length(max=120)])
    admin_phone = StringField('Admin Phone', validators=[Optional(), Length(max=20)])

class NotificationRecipientForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(max=100)])
    email = StringField('Email', validators=[Optional(), Email(), Length(max=120)])
    phone = StringField('Phone', validators=[Optional(), Length(max=20)])
    
    notification_types = MultiCheckboxField(
        'Notification Types',
        choices=[('email', 'Email'), ('sms', 'SMS'), ('whatsapp', 'WhatsApp')],
        validators=[DataRequired()]
    )
    
    event_types = MultiCheckboxField(
        'Event Types',
        choices=[
            ('low_stock', 'Low Stock Alerts'),
            ('order_update', 'Order Updates'),
            ('production_complete', 'Production Complete'),
            ('system_alert', 'System Alerts')
        ],
        validators=[DataRequired()]
    )
    
    is_active = BooleanField('Active', default=True)
    
    def validate(self, extra_validators=None):
        if not super().validate(extra_validators):
            return False
        
        # Ensure at least email or phone is provided
        if not self.email.data and not self.phone.data:
            self.email.errors.append('Either email or phone must be provided.')
            self.phone.errors.append('Either email or phone must be provided.')
            return False
        
        # Validate notification types match available contact methods
        if 'email' in self.notification_types.data and not self.email.data:
            self.notification_types.errors.append('Email is required for email notifications.')
            return False
        
        if ('sms' in self.notification_types.data or 'whatsapp' in self.notification_types.data) and not self.phone.data:
            self.notification_types.errors.append('Phone is required for SMS/WhatsApp notifications.')
            return False
        
        return True