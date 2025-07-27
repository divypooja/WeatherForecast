from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, DateField, SelectField, TextAreaField, IntegerField, BooleanField
from wtforms.validators import DataRequired, NumberRange, Optional, Length
from wtforms.widgets import HiddenInput
from datetime import date


class GRNForm(FlaskForm):
    """Form for creating and editing GRN (Goods Receipt Note)"""
    
    # Basic GRN Information
    grn_number = StringField('GRN Number', validators=[DataRequired(), Length(max=50)])
    job_work_id = IntegerField('Job Work ID', validators=[Optional()], widget=HiddenInput())
    purchase_order_id = IntegerField('Purchase Order ID', validators=[Optional()], widget=HiddenInput())
    received_date = DateField('Received Date', validators=[DataRequired()], default=date.today)
    
    # Delivery Information
    delivery_note = StringField('Delivery Note Number', validators=[Optional(), Length(max=100)])
    transporter_name = StringField('Transporter Name', validators=[Optional(), Length(max=100)])
    vehicle_number = StringField('Vehicle Number', validators=[Optional(), Length(max=20)])
    
    # Quality Control
    inspection_required = BooleanField('Inspection Required', default=True)
    
    # Status - will be set automatically by system
    
    # Notes
    remarks = TextAreaField('Remarks', validators=[Optional()])


class GRNLineItemForm(FlaskForm):
    """Form for GRN line items"""
    
    # Hidden fields for identification
    grn_id = IntegerField('GRN ID', widget=HiddenInput())
    item_id = IntegerField('Item ID', validators=[DataRequired()], widget=HiddenInput())
    
    # Quantity fields
    quantity_received = FloatField('Quantity Received', 
                                 validators=[DataRequired(), NumberRange(min=0.01, message="Quantity must be greater than 0")])
    quantity_passed = FloatField('Quantity Passed', 
                               validators=[Optional(), NumberRange(min=0, message="Quantity cannot be negative")],
                               default=0.0)
    quantity_rejected = FloatField('Quantity Rejected', 
                                 validators=[Optional(), NumberRange(min=0, message="Quantity cannot be negative")],
                                 default=0.0)
    
    # Unit information
    unit_of_measure = StringField('Unit', validators=[Optional(), Length(max=20)])
    unit_weight = FloatField('Unit Weight (kg)', validators=[Optional(), NumberRange(min=0)])
    
    # Quality control
    inspection_status = SelectField('Inspection Status', choices=[
        ('pending', 'Pending'),
        ('passed', 'Passed'),
        ('rejected', 'Rejected'),
        ('partial', 'Partial')
    ], default='pending')
    
    rejection_reason = StringField('Rejection Reason', validators=[Optional(), Length(max=500)])
    quality_grade = SelectField('Quality Grade', choices=[
        ('', 'Not Graded'),
        ('A', 'Grade A'),
        ('B', 'Grade B'),
        ('C', 'Grade C'),
        ('Pass', 'Pass'),
        ('Fail', 'Fail')
    ])
    
    # Process information (for multi-process job works)
    process_name = StringField('Process Name', validators=[Optional(), Length(max=100)])
    process_stage = StringField('Process Stage', validators=[Optional(), Length(max=50)])
    

    
    # Tracking information
    batch_number = StringField('Batch Number', validators=[Optional(), Length(max=50)])
    serial_numbers = TextAreaField('Serial Numbers', validators=[Optional()],
                                 render_kw={'placeholder': 'Enter serial numbers separated by commas'})
    
    # Notes
    remarks = TextAreaField('Line Item Remarks', validators=[Optional()])


class QuickReceiveForm(FlaskForm):
    """Quick form for receiving materials from job work"""
    
    job_work_id = IntegerField('Job Work ID', validators=[DataRequired()], widget=HiddenInput())
    received_date = DateField('Received Date', validators=[DataRequired()], default=date.today)
    
    # Quick quantity fields
    quantity_received = FloatField('Quantity Received', 
                                 validators=[DataRequired(), NumberRange(min=0.01, message="Quantity must be greater than 0")])
    quantity_passed = FloatField('Quantity Passed (Auto-calculated)', 
                               validators=[Optional()], 
                               render_kw={'readonly': True})
    quantity_rejected = FloatField('Quantity Rejected', 
                                 validators=[Optional(), NumberRange(min=0)],
                                 default=0.0)
    
    # Quick inspection
    inspection_status = SelectField('Overall Status', choices=[
        ('passed', 'All Passed'),
        ('rejected', 'All Rejected'),
        ('partial', 'Partial (some rejected)')
    ], default='passed')
    
    rejection_reason = TextAreaField('Rejection Reason (if any)', validators=[Optional()])
    
    # Delivery info
    delivery_note = StringField('Delivery Note', validators=[Optional(), Length(max=100)])
    
    # Add to inventory option
    add_to_inventory = BooleanField('Add Passed Quantity to Inventory', default=True)
    
    remarks = TextAreaField('Remarks', validators=[Optional()])


class QuickReceivePOForm(FlaskForm):
    """Quick form for receiving materials from purchase order"""
    
    purchase_order_id = IntegerField('Purchase Order ID', validators=[DataRequired()], widget=HiddenInput())
    item_id = IntegerField('Item ID', validators=[DataRequired()], widget=HiddenInput())
    received_date = DateField('Received Date', validators=[DataRequired()], default=date.today)
    
    # Quick quantity fields
    quantity_received = FloatField('Quantity Received', 
                                 validators=[DataRequired(), NumberRange(min=0.01, message="Quantity must be greater than 0")])
    quantity_passed = FloatField('Quantity Passed (Auto-calculated)', 
                               validators=[Optional()], 
                               render_kw={'readonly': True})
    quantity_rejected = FloatField('Quantity Rejected', 
                                 validators=[Optional(), NumberRange(min=0)],
                                 default=0.0)
    
    # Quick inspection
    inspection_status = SelectField('Overall Status', choices=[
        ('passed', 'All Passed'),
        ('rejected', 'All Rejected'),
        ('partial', 'Partial (some rejected)')
    ], default='passed')
    
    rejection_reason = TextAreaField('Rejection Reason (if any)', validators=[Optional()])
    
    # Delivery info
    delivery_note = StringField('Delivery Note', validators=[Optional(), Length(max=100)])
    
    # Add to inventory option
    add_to_inventory = BooleanField('Add Passed Quantity to Inventory', default=True)
    
    remarks = TextAreaField('Remarks', validators=[Optional()])


class GRNSearchForm(FlaskForm):
    """Form for searching and filtering GRNs"""
    
    search = StringField('Search GRN/Job Number', validators=[Optional()])
    
    status = SelectField('Status', choices=[
        ('', 'All Status'),
        ('draft', 'Draft'),
        ('received', 'Received'),
        ('inspected', 'Inspected'),
        ('completed', 'Completed')
    ])
    
    inspection_status = SelectField('Inspection Status', choices=[
        ('', 'All Inspection Status'),
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('failed', 'Failed')
    ])
    
    date_from = DateField('From Date', validators=[Optional()])
    date_to = DateField('To Date', validators=[Optional()])
    
    customer = StringField('Customer/Supplier', validators=[Optional()])


class MultiProcessQuickReceiveForm(FlaskForm):
    """Specialized quick receive form for multi-process job works"""
    
    job_work_id = IntegerField('Job Work ID', validators=[DataRequired()], widget=HiddenInput())
    process_id = IntegerField('Process ID', validators=[Optional()], widget=HiddenInput())
    received_date = DateField('Received Date', validators=[DataRequired()], default=date.today)
    
    # Process selection
    process_selection = SelectField('Select Process', choices=[], coerce=int, validators=[DataRequired()])
    
    # Quick quantity fields
    quantity_received = FloatField('Quantity Received from Process', 
                                 validators=[DataRequired(), NumberRange(min=0.01, message="Quantity must be greater than 0")])
    quantity_passed = FloatField('Quantity Passed (Auto-calculated)', 
                               validators=[Optional()], 
                               render_kw={'readonly': True})
    quantity_rejected = FloatField('Quantity Rejected', 
                                 validators=[Optional(), NumberRange(min=0)],
                                 default=0.0)
    
    # Process stage info
    process_stage = StringField('Process Stage Completed', validators=[Optional(), Length(max=100)])
    
    # Quick inspection
    inspection_status = SelectField('Overall Status', choices=[
        ('passed', 'All Passed'),
        ('rejected', 'All Rejected'),
        ('partial', 'Partial (some rejected)')
    ], default='passed')
    
    rejection_reason = TextAreaField('Rejection Reason (if any)', validators=[Optional()])
    
    # Delivery info
    delivery_note = StringField('Delivery Note from Process', validators=[Optional(), Length(max=100)])
    
    # Add to inventory option
    add_to_inventory = BooleanField('Add Passed Quantity to Inventory', default=True)
    
    remarks = TextAreaField('Process Completion Notes', validators=[Optional()])