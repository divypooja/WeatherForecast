"""
Forms for notification management system
"""
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, BooleanField, SelectField, EmailField
from wtforms.validators import DataRequired, Email, Optional, Length

class NotificationRecipientForm(FlaskForm):
    """Form for adding/editing notification recipients"""
    name = StringField('Name', validators=[DataRequired(), Length(min=2, max=100)])
    email = EmailField('Email Address', validators=[Optional(), Email()])
    phone = StringField('Phone Number', validators=[Optional(), Length(max=20)])
    role = StringField('Role/Position', validators=[DataRequired(), Length(max=50)])
    
    # Notification channels
    email_enabled = BooleanField('Email Notifications')
    sms_enabled = BooleanField('SMS Notifications') 
    whatsapp_enabled = BooleanField('WhatsApp Notifications')
    
    # Event subscriptions
    purchase_notifications = BooleanField('Purchase Order Events')
    sales_notifications = BooleanField('Sales Order Events')
    production_notifications = BooleanField('Production Events')
    inventory_notifications = BooleanField('Inventory Alerts')
    jobwork_notifications = BooleanField('Job Work Events')
    accounting_notifications = BooleanField('Accounting Events')
    
    # Status
    is_active = BooleanField('Active', default=True)

class NotificationSettingsForm(FlaskForm):
    """Form for notification system settings"""
    # Email settings
    email_enabled = BooleanField('Enable Email Notifications')
    sender_email = EmailField('Sender Email', validators=[Optional(), Email()])
    sender_name = StringField('Sender Name', validators=[Optional(), Length(max=100)])
    
    # SMS/WhatsApp settings  
    sms_enabled = BooleanField('Enable SMS Notifications')
    whatsapp_enabled = BooleanField('Enable WhatsApp Notifications')
    
    # Global notification preferences
    low_stock_notifications = BooleanField('Low Stock Alerts')
    order_status_notifications = BooleanField('Order Status Updates')
    production_notifications = BooleanField('Production Notifications')
    
    # System admin contacts
    admin_email = EmailField('Admin Email', validators=[Optional(), Email()])
    admin_phone = StringField('Admin Phone', validators=[Optional(), Length(max=20)])

class NotificationTemplateForm(FlaskForm):
    """Form for notification templates"""
    name = StringField('Template Name', validators=[DataRequired(), Length(max=100)])
    subject = StringField('Subject Template', validators=[DataRequired(), Length(max=200)])
    message = TextAreaField('Message Template', validators=[DataRequired()])
    event_type = SelectField('Event Type', choices=[
        ('po_created', 'Purchase Order Created'),
        ('grn_received', 'GRN Received'),
        ('low_stock', 'Low Stock Alert'),
        ('production_complete', 'Production Complete'),
        ('payment_due', 'Payment Due'),
        ('job_work_issued', 'Job Work Issued'),
        ('job_work_returned', 'Job Work Returned')
    ], validators=[DataRequired()])
    is_active = BooleanField('Active', default=True)

class TestNotificationForm(FlaskForm):
    """Form for testing notifications"""
    notification_type = SelectField('Notification Type', choices=[
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('whatsapp', 'WhatsApp')
    ], validators=[DataRequired()])
    recipient = StringField('Test Recipient', validators=[DataRequired()])
    subject = StringField('Test Subject', validators=[DataRequired()])
    message = TextAreaField('Test Message', validators=[DataRequired()])