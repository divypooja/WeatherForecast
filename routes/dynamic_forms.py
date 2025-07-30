"""
Dynamic Form Management Routes
Routes for managing custom fields and form templates
"""

from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from sqlalchemy.exc import IntegrityError
import json

from app import db
from models_dynamic_forms import FormTemplate, CustomField, CustomFieldValue, DynamicFormManager
from forms_dynamic import CustomFieldForm, FormTemplateForm, FieldSectionForm, DynamicFormBuilder

dynamic_forms_bp = Blueprint('dynamic_forms', __name__, url_prefix='/admin/forms')

@dynamic_forms_bp.route('/dashboard')
@login_required
def dashboard():
    """Dynamic forms management dashboard"""
    # Get statistics
    total_templates = FormTemplate.query.filter_by(is_active=True).count()
    total_fields = CustomField.query.filter_by(is_active=True).count()
    total_values = CustomFieldValue.query.count()
    
    # Get recent templates
    recent_templates = FormTemplate.query.filter_by(is_active=True).order_by(FormTemplate.updated_at.desc()).limit(5).all()
    
    # Get templates by module
    templates_by_module = {}
    templates = FormTemplate.query.filter_by(is_active=True).all()
    for template in templates:
        if template.module not in templates_by_module:
            templates_by_module[template.module] = []
        templates_by_module[template.module].append(template)
    
    return render_template('admin/dynamic_forms/dashboard.html',
                         total_templates=total_templates,
                         total_fields=total_fields,
                         total_values=total_values,
                         recent_templates=recent_templates,
                         templates_by_module=templates_by_module)

# Form Template Management
@dynamic_forms_bp.route('/templates')
@login_required
def list_templates():
    """List all form templates"""
    templates = FormTemplate.query.order_by(FormTemplate.module, FormTemplate.name).all()
    return render_template('admin/dynamic_forms/templates_list.html', templates=templates)

@dynamic_forms_bp.route('/templates/add', methods=['GET', 'POST'])
@login_required
def add_template():
    """Add new form template"""
    form = FormTemplateForm()
    
    if form.validate_on_submit():
        template = FormTemplate(
            name=form.name.data,
            code=form.code.data,
            description=form.description.data,
            module=form.module.data,
            is_active=form.is_active.data
        )
        
        try:
            db.session.add(template)
            db.session.commit()
            flash(f'Form template "{template.name}" created successfully', 'success')
            return redirect(url_for('dynamic_forms.edit_template', id=template.id))
        except IntegrityError:
            db.session.rollback()
            flash('Template code already exists. Please use a unique code.', 'error')
    
    return render_template('admin/dynamic_forms/template_form.html', form=form, title='Add Form Template')

@dynamic_forms_bp.route('/templates/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_template(id):
    """Edit form template and manage its fields"""
    template = FormTemplate.query.get_or_404(id)
    form = FormTemplateForm(obj=template)
    
    if form.validate_on_submit():
        template.name = form.name.data
        template.code = form.code.data
        template.description = form.description.data
        template.module = form.module.data
        template.is_active = form.is_active.data
        
        try:
            db.session.commit()
            flash(f'Template "{template.name}" updated successfully', 'success')
        except IntegrityError:
            db.session.rollback()
            flash('Template code already exists. Please use a unique code.', 'error')
    
    # Get fields grouped by section
    sections, ungrouped_fields = DynamicFormBuilder.group_fields_by_section(template.active_fields)
    
    return render_template('admin/dynamic_forms/template_edit.html', 
                         template=template, 
                         form=form, 
                         sections=sections,
                         ungrouped_fields=ungrouped_fields,
                         title=f'Edit Template: {template.name}')

@dynamic_forms_bp.route('/templates/<int:id>/delete')
@login_required
def delete_template(id):
    """Delete form template"""
    template = FormTemplate.query.get_or_404(id)
    
    # Check if template has field values
    field_ids = [f.id for f in template.fields]
    if field_ids:
        value_count = CustomFieldValue.query.filter(CustomFieldValue.custom_field_id.in_(field_ids)).count()
        if value_count > 0:
            flash(f'Cannot delete template "{template.name}" - it has {value_count} field values in use', 'error')
            return redirect(url_for('dynamic_forms.list_templates'))
    
    db.session.delete(template)
    db.session.commit()
    flash(f'Template "{template.name}" deleted successfully', 'success')
    return redirect(url_for('dynamic_forms.list_templates'))

# Custom Field Management
@dynamic_forms_bp.route('/templates/<int:template_id>/fields/add', methods=['GET', 'POST'])
@login_required
def add_field(template_id):
    """Add custom field to template"""
    template = FormTemplate.query.get_or_404(template_id)
    form = CustomFieldForm()
    
    if form.validate_on_submit():
        field = CustomField(
            form_template_id=template_id,
            field_name=form.field_name.data,
            label=form.label.data,
            field_type=form.field_type.data,
            is_required=form.is_required.data,
            default_value=form.default_value.data,
            placeholder=form.placeholder.data,
            help_text=form.help_text.data,
            field_group=form.field_group.data,
            display_order=form.display_order.data,
            column_width=int(form.column_width.data)
        )
        
        # Set field options for select fields
        if form.field_type.data == 'select':
            field.set_options_list(form.get_options_list())
        
        # Set validation rules
        field.set_validation_dict(form.get_validation_rules())
        
        db.session.add(field)
        db.session.commit()
        flash(f'Custom field "{field.label}" added successfully', 'success')
        return redirect(url_for('dynamic_forms.edit_template', id=template_id))
    
    # Set next display order
    max_order = db.session.query(db.func.max(CustomField.display_order)).filter_by(form_template_id=template_id).scalar() or 0
    form.display_order.data = max_order + 1
    
    return render_template('admin/dynamic_forms/field_form.html', 
                         form=form, 
                         template=template, 
                         title=f'Add Field to {template.name}')

@dynamic_forms_bp.route('/fields/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_field(id):
    """Edit custom field"""
    field = CustomField.query.get_or_404(id)
    form = CustomFieldForm(obj=field)
    
    # Populate form with existing data
    if field.field_options:
        form.field_options.data = '\n'.join(field.options_list)
    
    # Populate validation rules
    rules = field.validation_dict
    form.min_length.data = rules.get('min_length')
    form.max_length.data = rules.get('max_length')
    form.min_value.data = rules.get('min_value')
    form.max_value.data = rules.get('max_value')
    
    if form.validate_on_submit():
        field.field_name = form.field_name.data
        field.label = form.label.data
        field.field_type = form.field_type.data
        field.is_required = form.is_required.data
        field.default_value = form.default_value.data
        field.placeholder = form.placeholder.data
        field.help_text = form.help_text.data
        field.field_group = form.field_group.data
        field.display_order = form.display_order.data
        field.column_width = int(form.column_width.data)
        
        # Update field options
        if form.field_type.data == 'select':
            field.set_options_list(form.get_options_list())
        else:
            field.field_options = None
        
        # Update validation rules
        field.set_validation_dict(form.get_validation_rules())
        
        db.session.commit()
        flash(f'Field "{field.label}" updated successfully', 'success')
        return redirect(url_for('dynamic_forms.edit_template', id=field.form_template_id))
    
    return render_template('admin/dynamic_forms/field_form.html', 
                         form=form, 
                         field=field,
                         template=field.form_template, 
                         title=f'Edit Field: {field.label}')

@dynamic_forms_bp.route('/fields/<int:id>/delete')
@login_required
def delete_field(id):
    """Delete custom field"""
    field = CustomField.query.get_or_404(id)
    template_id = field.form_template_id
    
    # Check if field has values
    value_count = field.field_values.count()
    if value_count > 0:
        flash(f'Cannot delete field "{field.label}" - it has {value_count} values in use', 'error')
        return redirect(url_for('dynamic_forms.edit_template', id=template_id))
    
    db.session.delete(field)
    db.session.commit()
    flash(f'Field "{field.label}" deleted successfully', 'success')
    return redirect(url_for('dynamic_forms.edit_template', id=template_id))

@dynamic_forms_bp.route('/fields/<int:id>/toggle')
@login_required
def toggle_field(id):
    """Toggle field active status"""
    field = CustomField.query.get_or_404(id)
    field.is_active = not field.is_active
    db.session.commit()
    
    status = 'activated' if field.is_active else 'deactivated'
    flash(f'Field "{field.label}" {status} successfully', 'success')
    return redirect(url_for('dynamic_forms.edit_template', id=field.form_template_id))

# Field Organization
@dynamic_forms_bp.route('/templates/<int:template_id>/fields/reorder', methods=['POST'])
@login_required
def reorder_fields(template_id):
    """Reorder fields via AJAX"""
    field_ids = request.json.get('field_ids', [])
    
    for index, field_id in enumerate(field_ids):
        field = CustomField.query.get(field_id)
        if field and field.form_template_id == template_id:
            field.display_order = index + 1
    
    db.session.commit()
    return jsonify({'success': True})

@dynamic_forms_bp.route('/templates/<int:template_id>/sections/organize', methods=['GET', 'POST'])
@login_required
def organize_sections(template_id):
    """Organize fields into sections"""
    template = FormTemplate.query.get_or_404(template_id)
    
    if request.method == 'POST':
        # Update field sections based on form data
        for field_id, section_name in request.form.items():
            if field_id.startswith('field_'):
                field_id = int(field_id.replace('field_', ''))
                field = CustomField.query.get(field_id)
                if field and field.form_template_id == template_id:
                    field.field_group = section_name if section_name else None
        
        db.session.commit()
        flash('Field sections updated successfully', 'success')
        return redirect(url_for('dynamic_forms.edit_template', id=template_id))
    
    # Get existing sections
    sections = set()
    for field in template.active_fields:
        if field.field_group:
            sections.add(field.field_group)
    
    return render_template('admin/dynamic_forms/organize_sections.html', 
                         template=template, 
                         existing_sections=sorted(sections))

# API Endpoints for Dynamic Form Integration
@dynamic_forms_bp.route('/api/templates/<code>/fields')
def api_get_template_fields(code):
    """API endpoint to get custom fields for a form template"""
    fields = DynamicFormManager.get_custom_fields(code)
    
    field_data = []
    for field in fields:
        field_data.append({
            'id': field.id,
            'field_name': field.field_name,
            'label': field.label,
            'field_type': field.field_type,
            'is_required': field.is_required,
            'default_value': field.default_value,
            'placeholder': field.placeholder,
            'help_text': field.help_text,
            'field_group': field.field_group,
            'column_width': field.column_width,
            'options': field.options_list,
            'validation_rules': field.validation_dict
        })
    
    return jsonify({'fields': field_data})

@dynamic_forms_bp.route('/api/records/<record_type>/<int:record_id>/fields')
def api_get_field_values(record_type, record_id):
    """API endpoint to get custom field values for a record"""
    values = DynamicFormManager.get_field_values(record_type, record_id)
    
    value_data = {}
    for value in values:
        value_data[value.custom_field.field_name] = value.display_value
    
    return jsonify({'values': value_data})

# Initialize default templates
@dynamic_forms_bp.route('/admin/init-templates')
@login_required
def init_default_templates():
    """Initialize default form templates (admin only)"""
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('main.dashboard'))
    
    DynamicFormManager.create_default_templates()
    flash('Default form templates initialized successfully', 'success')
    return redirect(url_for('dynamic_forms.dashboard'))