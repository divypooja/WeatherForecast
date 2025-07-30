"""
Forms for Workflow Logic Management
Handles conditional logic and field connections for dynamic forms
"""

from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, TextAreaField, IntegerField, BooleanField, HiddenField
from wtforms.validators import DataRequired, Length, Optional
from wtforms.widgets import TextArea

class FieldConditionForm(FlaskForm):
    """Form for creating and editing field conditions"""
    
    # Source and target fields (populated dynamically)
    source_field_id = SelectField('Source Field', 
                                  coerce=int, 
                                  validators=[DataRequired()],
                                  description='Field that triggers the condition')
    
    target_field_id = SelectField('Target Field', 
                                  coerce=int, 
                                  validators=[DataRequired()],
                                  description='Field that is affected by the condition')
    
    # Condition configuration
    condition_type = SelectField('Condition Type',
                                choices=[
                                    ('if', 'If'),
                                    ('elif', 'Else If'),
                                    ('else', 'Else')
                                ],
                                default='if',
                                validators=[DataRequired()])
    
    operator = SelectField('Operator',
                          choices=[
                              ('equals', 'Equals'),
                              ('not_equals', 'Not Equals'),
                              ('greater_than', 'Greater Than'),
                              ('less_than', 'Less Than'),
                              ('contains', 'Contains'),
                              ('starts_with', 'Starts With'),
                              ('ends_with', 'Ends With'),
                              ('empty', 'Is Empty'),
                              ('not_empty', 'Is Not Empty')
                          ],
                          validators=[DataRequired()])
    
    condition_value = StringField('Condition Value',
                                  validators=[Optional(), Length(max=200)],
                                  description='Value to compare against (leave empty for "empty" operators)')
    
    # Action configuration
    action = SelectField('Action',
                        choices=[
                            ('show', 'Show Field'),
                            ('hide', 'Hide Field'),
                            ('require', 'Make Required'),
                            ('optional', 'Make Optional'),
                            ('set_value', 'Set Value'),
                            ('clear_value', 'Clear Value')
                        ],
                        validators=[DataRequired()])
    
    action_value = StringField('Action Value',
                               validators=[Optional(), Length(max=200)],
                               description='Value to set (only for "Set Value" action)')
    
    condition_order = IntegerField('Order',
                                   default=0,
                                   validators=[Optional()],
                                   description='Order of execution (lower numbers first)')
    
    is_active = BooleanField('Active', default=True)

class WorkflowRuleForm(FlaskForm):
    """Form for creating complex workflow rules"""
    
    name = StringField('Rule Name',
                       validators=[DataRequired(), Length(min=3, max=100)],
                       description='Descriptive name for this workflow rule')
    
    description = TextAreaField('Description',
                                validators=[Optional(), Length(max=500)],
                                widget=TextArea(),
                                description='Detailed description of what this rule does')
    
    # Rule configuration will be handled by JavaScript
    rule_config = HiddenField('Rule Configuration')
    
    priority = IntegerField('Priority',
                            default=0,
                            validators=[Optional()],
                            description='Higher numbers have higher priority')
    
    is_active = BooleanField('Active', default=True)

class ConditionalFieldGroupForm(FlaskForm):
    """Form for creating field groups"""
    
    name = StringField('Group Name',
                       validators=[DataRequired(), Length(min=3, max=100)],
                       description='Name for this field group')
    
    description = TextAreaField('Description',
                                validators=[Optional(), Length(max=500)],
                                widget=TextArea(),
                                description='Description of this field group')
    
    group_behavior = SelectField('Group Behavior',
                                choices=[
                                    ('show_all', 'Show All Fields'),
                                    ('hide_all', 'Hide All Fields'),
                                    ('require_all', 'Require All Fields'),
                                    ('optional_all', 'Make All Optional')
                                ],
                                default='show_all',
                                validators=[DataRequired()])
    
    # Field selection will be handled by JavaScript
    field_ids = HiddenField('Field IDs')
    
    is_active = BooleanField('Active', default=True)

class WorkflowTestForm(FlaskForm):
    """Form for testing workflow logic"""
    
    test_data = HiddenField('Test Data')  # JSON string with field values to test
    
    def __init__(self, form_template=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Dynamically add fields based on form template
        if form_template:
            for field in form_template.active_fields:
                field_name = f'test_{field.id}'
                
                if field.field_type == 'text':
                    setattr(self, field_name, StringField(field.label, validators=[Optional()]))
                elif field.field_type == 'number':
                    setattr(self, field_name, IntegerField(field.label, validators=[Optional()]))
                elif field.field_type == 'select':
                    # Parse options from JSON
                    try:
                        import json
                        options = json.loads(field.field_options or '[]')
                        choices = [(opt, opt) for opt in options]
                    except:
                        choices = []
                    setattr(self, field_name, SelectField(field.label, choices=choices, validators=[Optional()]))
                elif field.field_type == 'checkbox':
                    setattr(self, field_name, BooleanField(field.label))
                else:
                    setattr(self, field_name, StringField(field.label, validators=[Optional()]))