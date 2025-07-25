from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, TextAreaField, FloatField, IntegerField, DateField, BooleanField, SelectMultipleField, ValidationError, DateTimeField
from wtforms.validators import DataRequired, Length, Email, NumberRange, Optional
from wtforms.widgets import CheckboxInput, ListWidget
from models import User, Item, Supplier, QualityIssue, Production, PurchaseOrder, JobWork, ItemType
from models_uom import UnitOfMeasure
from datetime import datetime

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=25)])
    password = PasswordField('Password', validators=[DataRequired()])

class ItemForm(FlaskForm):
    code = StringField('Item Code', validators=[DataRequired(), Length(max=50)])
    name = StringField('Item Name', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Description')
    unit_of_measure = SelectField('Unit of Measure', 
                                choices=[],  # Will be populated dynamically
                                validators=[DataRequired()])
    hsn_code = StringField('HSN Code', validators=[Length(max=20)])
    gst_rate = FloatField('GST Rate (%)', validators=[NumberRange(min=0, max=100)], default=18.0)
    current_stock = FloatField('Current Stock', validators=[NumberRange(min=0)], default=0.0)
    minimum_stock = FloatField('Minimum Stock', validators=[NumberRange(min=0)], default=0.0)
    unit_price = FloatField('Unit Price', validators=[NumberRange(min=0)], default=0.0)
    unit_weight = FloatField('Unit Weight (kg)', validators=[NumberRange(min=0)], default=0.0)
    item_type = SelectField('Item Type', 
                          choices=[],  # Will be populated dynamically
                          validators=[DataRequired()])
    
    def __init__(self, *args, **kwargs):
        super(ItemForm, self).__init__(*args, **kwargs)
        # Populate UOM choices from database
        try:
            units = UnitOfMeasure.query.order_by(UnitOfMeasure.category, UnitOfMeasure.name).all()
            self.unit_of_measure.choices = [(unit.symbol.lower(), f"{unit.name} ({unit.symbol}) - {unit.category}") for unit in units]
            # Add fallback options if no units in database
            if not self.unit_of_measure.choices:
                self.unit_of_measure.choices = [
                    ('pcs', 'Pieces (Pcs) - Count'), 
                    ('kg', 'Kilogram (Kg) - Weight'), 
                    ('m', 'Meter (M) - Length'),
                    ('l', 'Liter (L) - Volume')
                ]
        except Exception:
            # Fallback choices if database error
            self.unit_of_measure.choices = [
                ('pcs', 'Pieces (Pcs) - Count'), 
                ('kg', 'Kilogram (Kg) - Weight'), 
                ('m', 'Meter (M) - Length'),
                ('l', 'Liter (L) - Volume')
            ]
        
        # Populate Item Type choices from database
        try:
            from app import app
            with app.app_context():
                ItemType.get_default_types()  # Ensure default types exist
                self.item_type.choices = ItemType.get_choices()
        except Exception:
            # Fallback choices if database error
            self.item_type.choices = [
                ('1', 'Material'), 
                ('2', 'Product'), 
                ('3', 'Consumable')
            ]

class SupplierForm(FlaskForm):
    # Basic Information
    name = StringField('Business Partner Name', validators=[DataRequired(), Length(max=200)], 
                      render_kw={"placeholder": "A.K. Metals"})
    contact_person = StringField('Contact Person', validators=[Length(max=100)], 
                                render_kw={"placeholder": "Mr. Rahul Kumar"})
    phone = StringField('Mobile Number', validators=[Length(max=20)], 
                       render_kw={"placeholder": "9876543210"})
    email = StringField('Email', validators=[Optional(), Email(), Length(max=120)], 
                       render_kw={"placeholder": "info@akmetals.com"})
    
    # Partner Type
    partner_type = SelectField('Partner Type', 
                              choices=[('supplier', 'Supplier'), ('customer', 'Customer'), ('both', 'Both Supplier & Customer')],
                              validators=[DataRequired()], default='supplier')
    
    # Compliance Information
    gst_number = StringField('GST Number', validators=[Length(max=50)], 
                            render_kw={"placeholder": "29ABCDE1234F1Z9"})
    pan_number = StringField('PAN Number', validators=[Optional(), Length(max=20)], 
                            render_kw={"placeholder": "ABCDE1234F"})
    
    # Address Information
    address = TextAreaField('Address', render_kw={"placeholder": "123, Industrial Area, Delhi"})
    city = StringField('City', validators=[Length(max=100)], 
                      render_kw={"placeholder": "Delhi"})
    state = StringField('State', validators=[Length(max=100)], 
                       render_kw={"placeholder": "Delhi"})
    pin_code = StringField('Pin Code', validators=[Length(max=10)], 
                          render_kw={"placeholder": "110001"})
    
    # Banking Information (Optional)
    account_number = StringField('Account Number', validators=[Optional(), Length(max=50)], 
                                render_kw={"placeholder": "123456789012"})
    bank_name = StringField('Bank Name', validators=[Optional(), Length(max=200)], 
                           render_kw={"placeholder": "State Bank of India"})
    ifsc_code = StringField('IFSC Code', validators=[Optional(), Length(max=20)], 
                           render_kw={"placeholder": "SBIN0001234"})
    
    # Additional Information
    remarks = TextAreaField('Remarks', render_kw={"placeholder": "Preferred for steel items"})
    is_active = BooleanField('Active', default=True)

# Create alias for backward compatibility
BusinessPartnerForm = SupplierForm

class PurchaseOrderForm(FlaskForm):
    po_number = StringField('PO Number', validators=[DataRequired(), Length(max=50)])
    supplier_id = SelectField('Supplier', validators=[DataRequired()], coerce=int)
    po_date = DateField('PO Date', validators=[DataRequired()])
    delivery_date = DateField('Expected Delivery Date')
    payment_terms = StringField('Payment Terms', validators=[Length(max=100)])
    freight_terms = StringField('Freight Terms', validators=[Length(max=100)])
    validity_months = IntegerField('Validity (Months)', validators=[Optional(), NumberRange(min=1, max=12)])
    prepared_by = StringField('Prepared By', validators=[Length(max=100)])
    verified_by = StringField('Verified By', validators=[Length(max=100)])
    approved_by = StringField('Approved By', validators=[Length(max=100)])
    delivery_notes = TextAreaField('Delivery Notes')
    status = SelectField('Status', choices=[('draft', 'Draft'), ('open', 'Open'), ('partial', 'Partially Received'), ('closed', 'Closed'), ('cancelled', 'Cancelled')], default='open')
    notes = TextAreaField('Notes')
    
    def __init__(self, *args, **kwargs):
        super(PurchaseOrderForm, self).__init__(*args, **kwargs)
        self.supplier_id.choices = [(0, 'Select Supplier')] + [(s.id, s.name) for s in Supplier.query.all()]

class PurchaseOrderItemForm(FlaskForm):
    item_id = SelectField('Item', validators=[DataRequired()], coerce=int)
    quantity_ordered = FloatField('Quantity', validators=[DataRequired(), NumberRange(min=0)])
    unit_price = FloatField('Unit Price', validators=[DataRequired(), NumberRange(min=0)])
    
    def __init__(self, *args, **kwargs):
        super(PurchaseOrderItemForm, self).__init__(*args, **kwargs)
        self.item_id.choices = [(0, 'Select Item')] + [(i.id, f"{i.code} - {i.name}") for i in Item.query.all()]

class SalesOrderForm(FlaskForm):
    so_number = StringField('SO Number', validators=[DataRequired(), Length(max=50)])
    customer_id = SelectField('Customer', validators=[DataRequired()], coerce=int)
    order_date = DateField('Order Date', validators=[DataRequired()])
    delivery_date = DateField('Expected Delivery Date')
    payment_terms = StringField('Payment Terms', validators=[Length(max=100)])
    freight_terms = StringField('Freight Terms', validators=[Length(max=100)])
    validity_months = IntegerField('Validity (Months)', validators=[Optional(), NumberRange(min=1, max=12)])
    prepared_by = StringField('Prepared By', validators=[Length(max=100)])
    verified_by = StringField('Verified By', validators=[Length(max=100)])
    approved_by = StringField('Approved By', validators=[Length(max=100)])
    delivery_notes = TextAreaField('Delivery Notes')
    status = SelectField('Status', choices=[('draft', 'Draft'), ('confirmed', 'Confirmed'), ('delivered', 'Delivered'), ('cancelled', 'Cancelled')], default='draft')
    notes = TextAreaField('Notes')
    
    def __init__(self, *args, **kwargs):
        super(SalesOrderForm, self).__init__(*args, **kwargs)
        # Get suppliers who are customers (partner_type is 'customer' or 'both')
        customers = Supplier.query.filter(Supplier.partner_type.in_(['customer', 'both'])).all()
        self.customer_id.choices = [(0, 'Select Customer')] + [(c.id, c.name) for c in customers]

class SalesOrderItemForm(FlaskForm):
    item_id = SelectField('Item', validators=[DataRequired()], coerce=int)
    quantity_ordered = FloatField('Quantity', validators=[DataRequired(), NumberRange(min=0)])
    unit_price = FloatField('Unit Price', validators=[DataRequired(), NumberRange(min=0)])
    
    def __init__(self, *args, **kwargs):
        super(SalesOrderItemForm, self).__init__(*args, **kwargs)
        self.item_id.choices = [(0, 'Select Item')] + [(i.id, f"{i.code} - {i.name}") for i in Item.query.all()]

class EmployeeForm(FlaskForm):
    employee_code = StringField('Employee Code', validators=[DataRequired(), Length(max=50)])
    name = StringField('Name', validators=[DataRequired(), Length(max=100)])
    designation = StringField('Designation', validators=[Length(max=100)])
    department = StringField('Department', validators=[Length(max=100)])
    salary_type = SelectField('Salary Type', 
                            choices=[('daily', 'Daily'), ('monthly', 'Monthly'), ('piece_rate', 'Piece Rate')],
                            validators=[DataRequired()])
    rate = FloatField('Rate', validators=[DataRequired(), NumberRange(min=0)])
    phone = StringField('Phone', validators=[Length(max=20)])
    address = TextAreaField('Address')
    hire_date = DateField('Hire Date', validators=[DataRequired()])
    salary = FloatField('Salary', validators=[NumberRange(min=0)])
    is_active = BooleanField('Active', default=True)

class JobWorkForm(FlaskForm):
    job_number = StringField('Job Number', validators=[DataRequired(), Length(max=50)])
    customer_name = SelectField('Customer Name', validators=[DataRequired()], coerce=str)
    item_id = SelectField('Item', validators=[DataRequired()], coerce=int)
    quantity_sent = FloatField('Quantity Sent', validators=[DataRequired(), NumberRange(min=0)])
    rate_per_unit = FloatField('Rate per Unit', validators=[DataRequired(), NumberRange(min=0)])
    sent_date = DateField('Sent Date', validators=[DataRequired()])
    expected_return = DateField('Expected Return Date')
    notes = TextAreaField('Notes')
    
    def __init__(self, *args, **kwargs):
        super(JobWorkForm, self).__init__(*args, **kwargs)
        self.item_id.choices = [(0, 'Select Item')] + [(i.id, f"{i.code} - {i.name}") for i in Item.query.all()]
        self.customer_name.choices = [('', 'Select Customer')] + [(s.name, s.name) for s in Supplier.query.order_by(Supplier.name).all()]

class JobWorkQuantityUpdateForm(FlaskForm):
    quantity_received = FloatField('Quantity Received', validators=[DataRequired(), NumberRange(min=0)])
    received_date = DateField('Received Date', validators=[DataRequired()])
    notes = TextAreaField('Notes')

class ProductionForm(FlaskForm):
    production_number = StringField('Production Number', validators=[DataRequired(), Length(max=50)])
    item_id = SelectField('Item to Produce', validators=[DataRequired()], coerce=int)
    quantity_planned = FloatField('Planned Quantity', validators=[DataRequired(), NumberRange(min=0)])
    quantity_produced = FloatField('Produced Quantity', validators=[NumberRange(min=0)], default=0.0)
    quantity_good = FloatField('Good Quality Quantity', validators=[NumberRange(min=0)], default=0.0)
    quantity_damaged = FloatField('Damaged/Defective Quantity', validators=[NumberRange(min=0)], default=0.0)
    production_date = DateField('Production Date', validators=[DataRequired()])
    status = SelectField('Status', choices=[('planned', 'Planned'), ('in_progress', 'In Progress'), ('completed', 'Completed')], default='planned')
    notes = TextAreaField('Notes')
    
    def __init__(self, *args, **kwargs):
        super(ProductionForm, self).__init__(*args, **kwargs)
        self.item_id.choices = [(0, 'Select Item')] + [(i.id, f"{i.code} - {i.name}") for i in Item.query.all()]

class QualityIssueForm(FlaskForm):
    issue_number = StringField('Issue Number', validators=[DataRequired(), Length(max=50)])
    production_id = SelectField('Production Order', validators=[Optional()], coerce=int)
    item_id = SelectField('Item', validators=[DataRequired()], coerce=int)
    issue_type = SelectField('Issue Type', 
                           choices=[('damage', 'Damage'), ('malfunction', 'Malfunction'), 
                                  ('defect', 'Defect'), ('contamination', 'Contamination'),
                                  ('dimension_error', 'Dimension Error'), ('material_defect', 'Material Defect')],
                           validators=[DataRequired()])
    severity = SelectField('Severity', 
                         choices=[('low', 'Low'), ('medium', 'Medium'), ('high', 'High'), ('critical', 'Critical')],
                         validators=[DataRequired()])
    quantity_affected = FloatField('Quantity Affected', validators=[DataRequired(), NumberRange(min=0)])
    description = TextAreaField('Description', validators=[DataRequired()])
    root_cause = TextAreaField('Root Cause Analysis')
    corrective_action = TextAreaField('Corrective Action')
    preventive_action = TextAreaField('Preventive Action')
    status = SelectField('Status', 
                       choices=[('open', 'Open'), ('investigating', 'Investigating'), 
                              ('resolved', 'Resolved'), ('closed', 'Closed')], 
                       default='open')
    assigned_to = SelectField('Assigned To', validators=[Optional()], coerce=int)
    cost_impact = FloatField('Cost Impact', validators=[NumberRange(min=0)], default=0.0)
    
    def __init__(self, *args, **kwargs):
        super(QualityIssueForm, self).__init__(*args, **kwargs)
        self.item_id.choices = [(0, 'Select Item')] + [(i.id, f"{i.code} - {i.name}") for i in Item.query.all()]
        self.production_id.choices = [(0, 'Not linked to production')] + [(p.id, f"{p.production_number}") for p in Production.query.all()]
        self.assigned_to.choices = [(0, 'Unassigned')] + [(u.id, u.username) for u in User.query.all()]

class QualityControlLogForm(FlaskForm):
    production_id = SelectField('Production Order', validators=[DataRequired()], coerce=int)
    batch_number = StringField('Batch Number', validators=[Length(max=50)])
    total_inspected = FloatField('Total Inspected', validators=[DataRequired(), NumberRange(min=0)])
    passed_quantity = FloatField('Passed Quantity', validators=[DataRequired(), NumberRange(min=0)])
    failed_quantity = FloatField('Failed Quantity', validators=[DataRequired(), NumberRange(min=0)])
    inspection_notes = TextAreaField('Inspection Notes')
    
    def __init__(self, *args, **kwargs):
        super(QualityControlLogForm, self).__init__(*args, **kwargs)
        self.production_id.choices = [(0, 'Select Production Order')] + [(p.id, f"{p.production_number} - {p.produced_item.name}") for p in Production.query.all()]

# ... rest of existing forms remain the same

class MultiCheckboxField(SelectMultipleField):
    widget = ListWidget(prefix_label=False)
    option_widget = CheckboxInput()

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
            ('quality_issue', 'Quality Issues'),
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
    production_notifications = BooleanField('Production Notifications', default=True)
    
    # Admin recipients
    admin_email = StringField('Admin Email', validators=[Optional(), Email(), Length(max=120)])
    admin_phone = StringField('Admin Phone', validators=[Optional(), Length(max=20)])
    
    submit = SubmitField('Save Settings')

class NotificationTestForm(FlaskForm):
    recipient_type = SelectField('Recipient Type', 
                               choices=[('sms', 'SMS'), ('email', 'Email'), ('whatsapp', 'WhatsApp')],
                               validators=[DataRequired()])
    recipient = StringField('Recipient', validators=[DataRequired()])
    message = TextAreaField('Test Message', validators=[DataRequired()])

class BOMForm(FlaskForm):
    product_id = SelectField('Product', validators=[DataRequired()], coerce=int)
    version = StringField('Version', validators=[DataRequired(), Length(max=20)], default='1.0')
    is_active = BooleanField('Active', default=True)
    
    # Labor and Overhead fields
    labor_cost_per_unit = FloatField('Labor Cost per Unit', validators=[NumberRange(min=0)], default=0.0)
    labor_hours_per_unit = FloatField('Labor Hours per Unit', validators=[NumberRange(min=0)], default=0.0)
    labor_rate_per_hour = FloatField('Labor Rate per Hour', validators=[NumberRange(min=0)], default=0.0)
    overhead_cost_per_unit = FloatField('Fixed Overhead per Unit', validators=[NumberRange(min=0)], default=0.0)
    overhead_percentage = FloatField('Overhead % (of material cost)', validators=[NumberRange(min=0, max=100)], default=0.0)
    freight_cost_per_unit = FloatField('Freight/Transportation Cost per Unit (Optional)', validators=[NumberRange(min=0)], default=0.0)
    
    def __init__(self, *args, **kwargs):
        super(BOMForm, self).__init__(*args, **kwargs)
        self.product_id.choices = [(0, 'Select Product')] + [(i.id, f"{i.code} - {i.name}") for i in Item.query.filter_by(item_type='product').all()]

class BOMItemForm(FlaskForm):
    item_id = SelectField('Material/Component', validators=[DataRequired()], coerce=int)
    quantity_required = FloatField('Quantity Required', validators=[DataRequired(), NumberRange(min=0)])
    unit_cost = FloatField('Unit Cost', validators=[NumberRange(min=0)], default=0.0)
    
    def __init__(self, *args, **kwargs):
        super(BOMItemForm, self).__init__(*args, **kwargs)
        self.item_id.choices = [(0, 'Select Item')] + [(i.id, f"{i.code} - {i.name}") for i in Item.query.filter(Item.item_type.in_(['material', 'consumable'])).all()]

class CompanySettingsForm(FlaskForm):
    company_name = StringField('Company Name', validators=[DataRequired(), Length(max=200)])
    address_line1 = StringField('Address Line 1', validators=[DataRequired(), Length(max=200)])
    address_line2 = StringField('Address Line 2', validators=[Optional(), Length(max=200)])
    city = StringField('City', validators=[DataRequired(), Length(max=100)])
    state = StringField('State', validators=[DataRequired(), Length(max=100)])
    pin_code = StringField('PIN Code', validators=[DataRequired(), Length(max=10)])
    phone = StringField('Phone', validators=[DataRequired(), Length(max=20)])
    email = StringField('Email', validators=[Optional(), Email(), Length(max=120)])
    gst_number = StringField('GST Number', validators=[DataRequired(), Length(max=50)])
    arn_number = StringField('ARN Number', validators=[Optional(), Length(max=50)])
    website = StringField('Website', validators=[Optional(), Length(max=200)])

class MaterialInspectionForm(FlaskForm):
    purchase_order_id = SelectField('Purchase Order', coerce=int, validators=[Optional()])
    job_work_id = SelectField('Job Work', coerce=int, validators=[Optional()])
    item_id = SelectField('Item', coerce=int, validators=[DataRequired()])
    received_quantity = FloatField('Received Quantity', validators=[DataRequired(), NumberRange(min=0.01)])
    inspected_quantity = FloatField('Inspected Quantity', validators=[DataRequired(), NumberRange(min=0.01)])
    passed_quantity = FloatField('Passed/Good Quantity', validators=[DataRequired(), NumberRange(min=0)])
    rejected_quantity = FloatField('Rejected Quantity', validators=[Optional(), NumberRange(min=0)])
    rejection_reasons = TextAreaField('Rejection Reasons', validators=[Optional()],
                                    render_kw={"placeholder": "e.g., Scratches, Dents, Corrosion, Quality issues, etc."})
    inspection_notes = TextAreaField('Inspection Notes', validators=[Optional()],
                                   render_kw={"placeholder": "Additional inspection observations"})
    
    def __init__(self, *args, **kwargs):
        super(MaterialInspectionForm, self).__init__(*args, **kwargs)
        self.purchase_order_id.choices = [(0, 'Select Purchase Order')] + [(po.id, f"{po.po_number} - {po.supplier.name}") for po in PurchaseOrder.query.filter_by(inspection_status='pending').all()]
        self.job_work_id.choices = [(0, 'Select Job Work')] + [(jw.id, f"{jw.job_number} - {jw.customer_name}") for jw in JobWork.query.filter_by(inspection_status='pending').all()]
        self.item_id.choices = [(0, 'Select Item')] + [(i.id, f"{i.code} - {i.name}") for i in Item.query.all()]

class FactoryExpenseForm(FlaskForm):
    # Basic Details
    expense_date = DateField('Expense Date', validators=[DataRequired()], default=datetime.today)
    category = SelectField('Category', validators=[DataRequired()], 
                          choices=[
                              ('utilities', 'Utilities & Infrastructure'),
                              ('maintenance', 'Maintenance & Repairs'),
                              ('salary', 'Salaries & Benefits'),
                              ('materials', 'Raw Materials & Supplies'),
                              ('overhead', 'Factory Overhead'),
                              ('transport', 'Transportation & Logistics'),
                              ('others', 'Other Expenses')
                          ])
    subcategory = StringField('Subcategory', validators=[Optional(), Length(max=100)], 
                             render_kw={"placeholder": "e.g., Electricity, Water, Equipment Repair"})
    description = TextAreaField('Description', validators=[DataRequired(), Length(max=500)], 
                               render_kw={"placeholder": "Detailed description of the expense"})
    
    # Financial Details
    amount = FloatField('Amount (₹)', validators=[DataRequired(), NumberRange(min=0.01)], 
                       render_kw={"placeholder": "0.00"})
    tax_amount = FloatField('Tax Amount (₹)', validators=[Optional(), NumberRange(min=0)], default=0.0,
                           render_kw={"placeholder": "0.00"})
    payment_method = SelectField('Payment Method', validators=[Optional()],
                                choices=[
                                    ('', 'Select Payment Method'),
                                    ('cash', 'Cash'),
                                    ('bank_transfer', 'Bank Transfer'),
                                    ('cheque', 'Cheque'),
                                    ('upi', 'UPI'),
                                    ('card', 'Card Payment')
                                ])
    paid_by = StringField('Paid By', validators=[Optional(), Length(max=100)], 
                         render_kw={"placeholder": "Person/Entity who made the payment"})
    
    # Vendor Details (Optional)
    vendor_name = StringField('Vendor/Supplier Name', validators=[Optional(), Length(max=200)], 
                             render_kw={"placeholder": "Vendor or supplier name"})
    vendor_contact = StringField('Vendor Contact', validators=[Optional(), Length(max=100)], 
                                render_kw={"placeholder": "Phone/Email of vendor"})
    invoice_number = StringField('Invoice Number', validators=[Optional(), Length(max=100)], 
                                render_kw={"placeholder": "Invoice/Bill number"})
    invoice_date = DateField('Invoice Date', validators=[Optional()])
    
    # Recurring Support
    is_recurring = BooleanField('Recurring Expense', default=False)
    recurring_frequency = SelectField('Frequency', validators=[Optional()],
                                     choices=[
                                         ('', 'Select Frequency'),
                                         ('monthly', 'Monthly'),
                                         ('quarterly', 'Quarterly'),
                                         ('yearly', 'Yearly')
                                     ])
    
    # Additional Information
    notes = TextAreaField('Notes', validators=[Optional()], 
                         render_kw={"placeholder": "Additional notes or comments"})
    
    submit = SubmitField('Save Expense')

class SalaryRecordForm(FlaskForm):
    salary_number = StringField('Salary Number', validators=[DataRequired()], render_kw={'readonly': True})
    employee_id = SelectField('Employee', coerce=int, validators=[DataRequired()])
    pay_period_start = DateField('Pay Period Start', validators=[DataRequired()])
    pay_period_end = DateField('Pay Period End', validators=[DataRequired()])
    basic_amount = FloatField('Basic Amount', validators=[DataRequired(), NumberRange(min=0.01)])
    overtime_hours = FloatField('Overtime Hours', validators=[Optional(), NumberRange(min=0)], default=0)
    overtime_rate = FloatField('Overtime Rate per Hour', validators=[Optional(), NumberRange(min=0)], default=0)
    bonus_amount = FloatField('Bonus Amount', validators=[Optional(), NumberRange(min=0)], default=0)
    deduction_amount = FloatField('Other Deductions', validators=[Optional(), NumberRange(min=0)], default=0)
    advance_deduction = FloatField('Advance Deduction', validators=[Optional(), NumberRange(min=0)], default=0)
    payment_method = SelectField('Payment Method', 
                                choices=[('cash', 'Cash'), ('bank_transfer', 'Bank Transfer'), ('cheque', 'Cheque')])
    notes = TextAreaField('Notes', render_kw={'rows': 3})
    submit = SubmitField('Save Salary Record')
    
    def __init__(self, *args, **kwargs):
        super(SalaryRecordForm, self).__init__(*args, **kwargs)
        from models import Employee
        self.employee_id.choices = [(0, 'Select Employee')] + [
            (e.id, f"{e.name} ({e.employee_code})") 
            for e in Employee.query.filter_by(is_active=True).order_by(Employee.name).all()
        ]

class EmployeeAdvanceForm(FlaskForm):
    advance_number = StringField('Advance Number', validators=[DataRequired()], render_kw={'readonly': True})
    employee_id = SelectField('Employee', coerce=int, validators=[DataRequired()])
    amount = FloatField('Advance Amount', validators=[DataRequired(), NumberRange(min=0.01)])
    reason = StringField('Reason for Advance', validators=[DataRequired(), Length(max=200)])
    advance_date = DateField('Advance Date', validators=[DataRequired()], default=datetime.utcnow().date())
    repayment_months = IntegerField('Repayment Months', validators=[DataRequired(), NumberRange(min=1, max=24)], default=1)
    payment_method = SelectField('Payment Method', 
                                choices=[('cash', 'Cash'), ('bank_transfer', 'Bank Transfer'), ('cheque', 'Cheque')])
    notes = TextAreaField('Notes', render_kw={'rows': 3})
    submit = SubmitField('Save Advance Request')
    
    def __init__(self, *args, **kwargs):
        super(EmployeeAdvanceForm, self).__init__(*args, **kwargs)
        from models import Employee
        self.employee_id.choices = [(0, 'Select Employee')] + [
            (e.id, f"{e.name} ({e.employee_code})") 
            for e in Employee.query.filter_by(is_active=True).order_by(Employee.name).all()
        ]