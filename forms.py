from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, FloatField, DateField, TextAreaField, IntegerField
from wtforms.validators import DataRequired, Email, Length, NumberRange, Optional
from wtforms.widgets import PasswordInput

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=80)])
    password = PasswordField('Password', validators=[DataRequired()])

class ItemForm(FlaskForm):
    code = StringField('Item Code', validators=[DataRequired(), Length(max=50)])
    name = StringField('Item Name', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Description')
    unit_of_measure = SelectField('Unit of Measure', 
                                choices=[('kg', 'Kilogram'), ('pcs', 'Pieces'), ('meter', 'Meter'), 
                                       ('liter', 'Liter'), ('box', 'Box'), ('set', 'Set')],
                                validators=[DataRequired()])
    minimum_stock = FloatField('Minimum Stock', validators=[NumberRange(min=0)], default=0)
    unit_price = FloatField('Unit Price', validators=[NumberRange(min=0)], default=0)
    item_type = SelectField('Item Type', 
                          choices=[('material', 'Raw Material'), ('product', 'Finished Product'), 
                                 ('consumable', 'Consumable')],
                          validators=[DataRequired()])

class SupplierForm(FlaskForm):
    name = StringField('Supplier Name', validators=[DataRequired(), Length(max=100)])
    contact_person = StringField('Contact Person', validators=[Length(max=100)])
    phone = StringField('Phone', validators=[Length(max=20)])
    email = StringField('Email', validators=[Optional(), Email()])
    address = TextAreaField('Address')

class CustomerForm(FlaskForm):
    name = StringField('Customer Name', validators=[DataRequired(), Length(max=100)])
    contact_person = StringField('Contact Person', validators=[Length(max=100)])
    phone = StringField('Phone', validators=[Length(max=20)])
    email = StringField('Email', validators=[Optional(), Email()])
    address = TextAreaField('Address')

class PurchaseOrderForm(FlaskForm):
    po_number = StringField('PO Number', validators=[DataRequired(), Length(max=50)])
    supplier_id = SelectField('Supplier', coerce=int, validators=[DataRequired()])
    order_date = DateField('Order Date', validators=[DataRequired()])
    expected_date = DateField('Expected Delivery Date')
    notes = TextAreaField('Notes')

class SalesOrderForm(FlaskForm):
    so_number = StringField('SO Number', validators=[DataRequired(), Length(max=50)])
    customer_id = SelectField('Customer', coerce=int, validators=[DataRequired()])
    order_date = DateField('Order Date', validators=[DataRequired()])
    delivery_date = DateField('Delivery Date')
    notes = TextAreaField('Notes')

class EmployeeForm(FlaskForm):
    employee_code = StringField('Employee Code', validators=[DataRequired(), Length(max=50)])
    name = StringField('Employee Name', validators=[DataRequired(), Length(max=100)])
    designation = StringField('Designation', validators=[Length(max=100)])
    department = StringField('Department', validators=[Length(max=100)])
    salary_type = SelectField('Salary Type', 
                            choices=[('daily', 'Daily Rate'), ('monthly', 'Monthly Salary'), 
                                   ('piece_rate', 'Piece Rate')],
                            validators=[DataRequired()])
    rate = FloatField('Rate/Salary', validators=[DataRequired(), NumberRange(min=0)])
    phone = StringField('Phone', validators=[Length(max=20)])
    address = TextAreaField('Address')
    joining_date = DateField('Joining Date', validators=[DataRequired()])

class JobWorkForm(FlaskForm):
    job_number = StringField('Job Number', validators=[DataRequired(), Length(max=50)])
    supplier_id = SelectField('Job Work Vendor', coerce=int, validators=[DataRequired()])
    job_date = DateField('Job Date', validators=[DataRequired()])
    expected_return_date = DateField('Expected Return Date')
    notes = TextAreaField('Notes')

class ProductionForm(FlaskForm):
    production_number = StringField('Production Number', validators=[DataRequired(), Length(max=50)])
    item_id = SelectField('Product to Produce', coerce=int, validators=[DataRequired()])
    quantity_planned = FloatField('Planned Quantity', validators=[DataRequired(), NumberRange(min=0)])
    production_date = DateField('Production Date', validators=[DataRequired()])
    notes = TextAreaField('Notes')
