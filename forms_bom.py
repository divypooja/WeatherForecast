from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, TextAreaField, SelectField, FieldList, FormField, IntegerField, BooleanField
from wtforms.validators import DataRequired, NumberRange, Length, Optional
from models import Item, Supplier
from models_uom import UnitOfMeasure
from models_department import Department

class BOMComponentForm(FlaskForm):
    """Form for individual BOM components"""
    material_id = SelectField('Material', coerce=int, validators=[DataRequired()])
    qty_required = FloatField('Quantity Required', validators=[DataRequired(), NumberRange(min=0.001)])
    uom_id = SelectField('UOM', coerce=int, validators=[DataRequired()])
    scrap_percent = FloatField('Scrap %', validators=[Optional(), NumberRange(min=0, max=50)], default=0)
    process_step = IntegerField('Process Step', validators=[Optional(), NumberRange(min=1)], default=1)
    process_name = StringField('Process Name', validators=[Optional(), Length(max=100)])
    rate_per_unit = FloatField('Rate per Unit', validators=[Optional(), NumberRange(min=0)], default=0)
    default_supplier_id = SelectField('Default Supplier', coerce=int, validators=[Optional()])
    is_critical = BooleanField('Critical Component')
    remarks = TextAreaField('Remarks', validators=[Optional(), Length(max=500)])
    
    def __init__(self, *args, **kwargs):
        super(BOMComponentForm, self).__init__(*args, **kwargs)
        # Populate choices
        self.material_id.choices = [(0, 'Select Material')] + \
                                  [(item.id, f"{item.name} ({item.item_code})") 
                                   for item in Item.query.order_by(Item.name).all()]  # type: ignore
        self.uom_id.choices = [(0, 'Select UOM')] + \
                             [(uom.id, f"{uom.name} ({uom.symbol})") 
                              for uom in UnitOfMeasure.query.order_by(UnitOfMeasure.name).all()]  # type: ignore
        self.default_supplier_id.choices = [(0, 'Select Supplier')] + \
                                          [(supplier.id, supplier.name) 
                                           for supplier in Supplier.query.order_by(Supplier.name).all()]  # type: ignore

class BOMProcessForm(FlaskForm):
    """Form for individual BOM processes"""
    step_number = IntegerField('Step Number', validators=[DataRequired(), NumberRange(min=1)])
    process_name = StringField('Process Name', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Description', validators=[Optional(), Length(max=500)])
    department_id = SelectField('Department', coerce=int, validators=[Optional()])
    estimated_time_minutes = IntegerField('Estimated Time (minutes)', validators=[Optional(), NumberRange(min=0)], default=0)
    cost_per_unit = FloatField('Cost per Unit', validators=[Optional(), NumberRange(min=0)], default=0)
    default_supplier_id = SelectField('Default Supplier', coerce=int, validators=[Optional()])
    is_outsourced = BooleanField('Outsourced Process')
    is_critical_path = BooleanField('Critical Path')
    
    def __init__(self, *args, **kwargs):
        super(BOMProcessForm, self).__init__(*args, **kwargs)
        # Populate choices
        self.department_id.choices = [(0, 'Select Department')] + \
                                    [(dept.id, dept.name) 
                                     for dept in Department.query.order_by(Department.name).all()]  # type: ignore
        self.default_supplier_id.choices = [(0, 'Select Supplier')] + \
                                          [(supplier.id, supplier.name) 
                                           for supplier in Supplier.query.order_by(Supplier.name).all()]  # type: ignore

class BOMForm(FlaskForm):
    """Main BOM creation/edit form"""
    bom_code = StringField('BOM Code', validators=[DataRequired(), Length(max=50)])
    product_id = SelectField('Product', coerce=int, validators=[DataRequired()])
    output_quantity = FloatField('Output Quantity', validators=[DataRequired(), NumberRange(min=0.001)], default=1.0)
    output_uom_id = SelectField('Output UOM', coerce=int, validators=[DataRequired()])
    version = StringField('Version', validators=[DataRequired(), Length(max=20)], default='1.0')
    status = SelectField('Status', choices=[
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('obsolete', 'Obsolete')
    ], default='draft')
    description = TextAreaField('Description', validators=[Optional(), Length(max=1000)])
    remarks = TextAreaField('Remarks', validators=[Optional(), Length(max=1000)])
    estimated_scrap_percent = FloatField('Estimated Overall Scrap %', 
                                       validators=[Optional(), NumberRange(min=0, max=50)], default=0)
    
    def __init__(self, *args, **kwargs):
        super(BOMForm, self).__init__(*args, **kwargs)
        # Populate product choices
        self.product_id.choices = [(0, 'Select Product')] + \
                                 [(item.id, f"{item.name} ({item.item_code})") 
                                  for item in Item.query.order_by(Item.name).all()]  # type: ignore
        # Populate UOM choices
        self.output_uom_id.choices = [(0, 'Select UOM')] + \
                                    [(uom.id, f"{uom.name} ({uom.symbol})") 
                                     for uom in UnitOfMeasure.query.order_by(UnitOfMeasure.name).all()]  # type: ignore

class BOMSearchForm(FlaskForm):
    """Form for searching and filtering BOMs"""
    search_term = StringField('Search BOM Code or Product Name', validators=[Optional(), Length(max=100)])
    product_id = SelectField('Filter by Product', coerce=int, validators=[Optional()])
    status = SelectField('Filter by Status', choices=[
        ('', 'All Statuses'),
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('obsolete', 'Obsolete')
    ], default='')
    
    def __init__(self, *args, **kwargs):
        super(BOMSearchForm, self).__init__(*args, **kwargs)
        # Populate product choices
        self.product_id.choices = [(0, 'All Products')] + \
                                 [(item.id, f"{item.name} ({item.item_code})") 
                                  for item in Item.query.order_by(Item.name).all()]  # type: ignore

class BOMCostAnalysisForm(FlaskForm):
    """Form for BOM cost analysis and scenarios"""
    material_cost_adjustment = FloatField('Material Cost Adjustment %', 
                                        validators=[Optional(), NumberRange(min=-50, max=100)], default=0)
    process_cost_adjustment = FloatField('Process Cost Adjustment %', 
                                       validators=[Optional(), NumberRange(min=-50, max=100)], default=0)
    production_quantity = IntegerField('Production Quantity for Analysis', 
                                     validators=[Optional(), NumberRange(min=1)], default=100)
    include_scrap_cost = BooleanField('Include Scrap Cost in Analysis', default=True)

class BOMValidationForm(FlaskForm):
    """Form for BOM validation and approval"""
    validation_notes = TextAreaField('Validation Notes', validators=[Optional(), Length(max=1000)])
    approval_status = SelectField('Approval Status', choices=[
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('needs_revision', 'Needs Revision')
    ], default='pending')