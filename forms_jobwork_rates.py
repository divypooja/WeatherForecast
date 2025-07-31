from flask_wtf import FlaskForm
from wtforms import SelectField, FloatField, TextAreaField, BooleanField, SubmitField, StringField
from wtforms.validators import DataRequired, NumberRange, Optional, Length
from models import Item

class JobWorkRateForm(FlaskForm):
    item_id = SelectField('Item', coerce=int, validators=[DataRequired()])
    rate_per_unit = FloatField('Rate per Unit (₹)', validators=[DataRequired(), NumberRange(min=0)])
    process_type = SelectField('Process Type (Optional)', choices=[
        ('', 'All Processes'),
        ('Zinc', 'Zinc Plating'),
        ('Cutting', 'Cutting'),
        ('Bending', 'Bending'),
        ('Welding', 'Welding'),
        ('Painting', 'Painting'),
        ('Assembly', 'Assembly'),
        ('Machining', 'Machining'),
        ('Polishing', 'Polishing')
    ])
    vendor_name = StringField('Vendor Name (Optional)', validators=[Optional(), Length(max=200)], 
                             render_kw={"placeholder": "Vendor/Supplier Name"})
    notes = TextAreaField('Notes')
    is_active = BooleanField('Active', default=True)
    submit = SubmitField('Save Rate')
    
    def __init__(self, *args, **kwargs):
        super(JobWorkRateForm, self).__init__(*args, **kwargs)
        self.item_id.choices = [(0, 'Select Item')] + [(item.id, f"{item.code} - {item.name}") for item in Item.query.order_by(Item.name).all()]