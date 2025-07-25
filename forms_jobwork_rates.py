from flask_wtf import FlaskForm
from wtforms import SelectField, FloatField, TextAreaField, BooleanField, SubmitField
from wtforms.validators import DataRequired, NumberRange
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
    notes = TextAreaField('Notes')
    is_active = BooleanField('Active', default=True)
    submit = SubmitField('Save Rate')
    
    def __init__(self, *args, **kwargs):
        super(JobWorkRateForm, self).__init__(*args, **kwargs)
        self.item_id.choices = [(0, 'Select Item')] + [(item.id, f"{item.code} - {item.name}") for item in Item.query.filter_by(is_active=True).order_by(Item.name).all()]