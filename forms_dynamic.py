"""
Dynamic Form Management Forms
Forms for managing custom fields and form templates
"""

from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, BooleanField, IntegerField, FloatField, FieldList, FormField, HiddenField
from wtforms.validators import DataRequired, Length, Optional, NumberRange, ValidationError
from wtforms.widgets import TextArea
import json

class CustomFieldForm(FlaskForm):
    """Form for creating/editing custom fields"""
    
    # Field Definition
    field_name = StringField('Field Name', 
                           validators=[DataRequired(), Length(max=100)],
                           render_kw={"placeholder": "e.g., supplier_certification_required"})
    label = StringField('Display Label', 
                       validators=[DataRequired(), Length(max=200)],
                       render_kw={"placeholder": "e.g., Supplier Certification Required"})
    
    field_type = SelectField('Field Type', 
                            validators=[DataRequired()],
                            choices=[
                                ('text', 'Text Input'),
                                ('textarea', 'Text Area'),
                                ('number', 'Number'),
                                ('decimal', 'Decimal Number'),
                                ('currency', 'Currency'),
                                ('select', 'Dropdown Select'),
                                ('checkbox', 'Checkbox'),
                                ('date', 'Date Picker'),
                                ('datetime', 'Date & Time'),
                                ('email', 'Email'),
                                ('url', 'URL'),
                                ('json', 'JSON Data')
                            ])
    
    # Field Configuration
    is_required = BooleanField('Required Field')
    default_value = StringField('Default Value', 
                               validators=[Optional()],
                               render_kw={"placeholder": "Optional default value"})
    placeholder = StringField('Placeholder Text', 
                             validators=[Optional(), Length(max=200)],
                             render_kw={"placeholder": "Placeholder text for user guidance"})
    help_text = TextAreaField('Help Text', 
                             validators=[Optional()],
                             render_kw={"rows": 2, "placeholder": "Additional help or instructions"})
    
    # Select Options (for dropdown fields)
    field_options = TextAreaField('Dropdown Options', 
                                 validators=[Optional()],
                                 render_kw={"rows": 4, "placeholder": "Enter options one per line:\nOption 1\nOption 2\nOption 3"})
    
    # Display Configuration
    field_group = StringField('Section/Group', 
                             validators=[Optional(), Length(max=100)],
                             render_kw={"placeholder": "e.g., Quality Control, Supplier Info"})
    display_order = IntegerField('Display Order', 
                                validators=[Optional(), NumberRange(min=0)],
                                default=0)
    column_width = SelectField('Column Width', 
                              validators=[Optional()],
                              choices=[
                                  ('12', 'Full Width (12/12)'),
                                  ('6', 'Half Width (6/12)'),
                                  ('4', 'Third Width (4/12)'),
                                  ('3', 'Quarter Width (3/12)'),
                                  ('8', 'Two Thirds (8/12)'),
                                  ('9', 'Three Quarters (9/12)')
                              ],
                              default='12')
    
    # Validation Rules
    min_length = IntegerField('Minimum Length', validators=[Optional(), NumberRange(min=0)])
    max_length = IntegerField('Maximum Length', validators=[Optional(), NumberRange(min=1)])
    min_value = FloatField('Minimum Value', validators=[Optional()])
    max_value = FloatField('Maximum Value', validators=[Optional()])
    
    def validate_field_options(self, field):
        """Validate field options for select fields"""
        if self.field_type.data == 'select' and not field.data:
            raise ValidationError('Dropdown options are required for select fields')
    
    def get_options_list(self):
        """Convert field_options text to list"""
        if self.field_options.data:
            return [opt.strip() for opt in self.field_options.data.split('\n') if opt.strip()]
        return []
    
    def get_validation_rules(self):
        """Build validation rules dictionary"""
        rules = {}
        if self.min_length.data is not None:
            rules['min_length'] = self.min_length.data
        if self.max_length.data is not None:
            rules['max_length'] = self.max_length.data
        if self.min_value.data is not None:
            rules['min_value'] = self.min_value.data
        if self.max_value.data is not None:
            rules['max_value'] = self.max_value.data
        return rules

class FormTemplateForm(FlaskForm):
    """Form for creating/editing form templates"""
    
    name = StringField('Template Name', 
                      validators=[DataRequired(), Length(max=100)],
                      render_kw={"placeholder": "e.g., Advanced BOM Management"})
    code = StringField('Template Code', 
                      validators=[DataRequired(), Length(max=50)],
                      render_kw={"placeholder": "e.g., advanced_bom"})
    description = TextAreaField('Description', 
                               validators=[Optional()],
                               render_kw={"rows": 3, "placeholder": "Brief description of this form template"})
    module = SelectField('Module', 
                        validators=[DataRequired()],
                        choices=[
                            ('production', 'Production'),
                            ('inventory', 'Inventory'),
                            ('purchase', 'Purchase Orders'),
                            ('sales', 'Sales Orders'),
                            ('job_work', 'Job Work'),
                            ('grn', 'GRN'),
                            ('quality', 'Quality Control'),
                            ('hr', 'Human Resources'),
                            ('finance', 'Finance')
                        ])
    is_active = BooleanField('Active Template', default=True)

class FieldSectionForm(FlaskForm):
    """Form for organizing fields into sections"""
    
    section_name = StringField('Section Name', 
                              validators=[DataRequired(), Length(max=100)],
                              render_kw={"placeholder": "e.g., Quality Control, Supplier Information"})
    section_description = TextAreaField('Section Description', 
                                       validators=[Optional()],
                                       render_kw={"rows": 2, "placeholder": "Brief description of this section"})
    display_order = IntegerField('Display Order', 
                                validators=[Optional(), NumberRange(min=0)],
                                default=0)
    is_collapsible = BooleanField('Collapsible Section', default=False)
    is_expanded = BooleanField('Expanded by Default', default=True)

class DynamicFormBuilder:
    """Service class for building dynamic forms"""
    
    @staticmethod
    def render_custom_field(field, value=None, form_data=None):
        """Render a custom field as HTML"""
        field_id = f"custom_{field.field_name}"
        field_value = value or field.default_value or ""
        
        # Common attributes
        base_attrs = {
            'id': field_id,
            'name': f'custom_{field.field_name}',
            'class': 'form-control'
        }
        
        if field.placeholder:
            base_attrs['placeholder'] = field.placeholder
        if field.is_required:
            base_attrs['required'] = 'required'
        
        def build_attrs(attrs_dict, exclude_keys=None):
            """Helper to build attribute string"""
            exclude_keys = exclude_keys or []
            parts = []
            for k, v in attrs_dict.items():
                if k not in exclude_keys:
                    parts.append(f'{k}="{v}"')
            return " ".join(parts)
        
        # Build field based on type
        if field.field_type == 'text':
            attrs = base_attrs.copy()
            attrs['type'] = 'text'
            attrs['value'] = field_value
            return f'<input {build_attrs(attrs)}>'
            
        elif field.field_type == 'textarea':
            return f'<textarea {build_attrs(base_attrs, ["type"])}>{field_value}</textarea>'
            
        elif field.field_type in ['number', 'decimal', 'currency']:
            attrs = base_attrs.copy()
            attrs['type'] = 'number'
            attrs['step'] = '0.01' if field.field_type in ['decimal', 'currency'] else '1'
            attrs['value'] = field_value
            return f'<input {build_attrs(attrs)}>'
            
        elif field.field_type == 'select':
            options_html = ""
            if not field.is_required:
                options_html += '<option value="">-- Select Option --</option>'
            
            for option in field.options_list:
                selected = 'selected' if str(option) == str(field_value) else ''
                options_html += f'<option value="{option}" {selected}>{option}</option>'
            
            return f'<select {build_attrs(base_attrs, ["type", "value", "placeholder"])}>{options_html}</select>'
            
        elif field.field_type == 'checkbox':
            checked = 'checked' if field_value else ''
            return f'<div class="form-check"><input type="checkbox" class="form-check-input" id="{field_id}" name="custom_{field.field_name}" value="1" {checked}><label class="form-check-label" for="{field_id}">{field.label}</label></div>'
            
        elif field.field_type == 'date':
            attrs = base_attrs.copy()
            attrs['type'] = 'date'
            attrs['value'] = field_value
            return f'<input {build_attrs(attrs)}>'
            
        elif field.field_type == 'datetime':
            attrs = base_attrs.copy()
            attrs['type'] = 'datetime-local'
            attrs['value'] = field_value
            return f'<input {build_attrs(attrs)}>'
            
        elif field.field_type == 'email':
            attrs = base_attrs.copy()
            attrs['type'] = 'email'
            attrs['value'] = field_value
            return f'<input {build_attrs(attrs)}>'
            
        elif field.field_type == 'url':
            attrs = base_attrs.copy()
            attrs['type'] = 'url'
            attrs['value'] = field_value
            return f'<input {build_attrs(attrs)}>'
        
        return ""
    
    @staticmethod
    def group_fields_by_section(fields):
        """Group custom fields by their sections"""
        sections = {}
        ungrouped = []
        
        for field in fields:
            if field.field_group:
                if field.field_group not in sections:
                    sections[field.field_group] = []
                sections[field.field_group].append(field)
            else:
                ungrouped.append(field)
        
        # Sort fields within each section by display_order
        for section_name in sections:
            sections[section_name].sort(key=lambda f: f.display_order)
        
        ungrouped.sort(key=lambda f: f.display_order)
        
        return sections, ungrouped
    
    @staticmethod
    def validate_custom_fields(fields, form_data):
        """Validate custom field values"""
        errors = {}
        
        for field in fields:
            field_name = f'custom_{field.field_name}'
            value = form_data.get(field_name)
            
            # Required field validation
            if field.is_required and not value:
                errors[field_name] = f'{field.label} is required'
                continue
            
            if value:  # Only validate if value exists
                # Validation rules
                rules = field.validation_dict
                
                # Length validation for text fields
                if field.field_type in ['text', 'textarea'] and value:
                    if 'min_length' in rules and len(value) < rules['min_length']:
                        errors[field_name] = f'{field.label} must be at least {rules["min_length"]} characters'
                    if 'max_length' in rules and len(value) > rules['max_length']:
                        errors[field_name] = f'{field.label} must be no more than {rules["max_length"]} characters'
                
                # Numeric validation
                if field.field_type in ['number', 'decimal', 'currency']:
                    try:
                        num_value = float(value)
                        if 'min_value' in rules and num_value < rules['min_value']:
                            errors[field_name] = f'{field.label} must be at least {rules["min_value"]}'
                        if 'max_value' in rules and num_value > rules['max_value']:
                            errors[field_name] = f'{field.label} must be no more than {rules["max_value"]}'
                    except ValueError:
                        errors[field_name] = f'{field.label} must be a valid number'
        
        return errors