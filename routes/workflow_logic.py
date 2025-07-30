"""
Workflow Logic Routes
Handles conditional logic and field connections for dynamic forms
"""

from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from models_dynamic_forms import FormTemplate, CustomField
from models_workflow_logic import FieldCondition, WorkflowRule, ConditionalFieldGroup, FormWorkflowState, process_workflow_logic
from forms_workflow_logic import FieldConditionForm, WorkflowRuleForm, ConditionalFieldGroupForm
from app import db
import json

workflow_logic_bp = Blueprint('workflow_logic', __name__)

@workflow_logic_bp.route('/dashboard/<int:template_id>')
@login_required
def dashboard(template_id):
    """Workflow logic dashboard for a specific form template"""
    template = FormTemplate.query.get_or_404(template_id)
    
    # Get statistics
    conditions_count = FieldCondition.query.filter_by(form_template_id=template_id, is_active=True).count()
    rules_count = WorkflowRule.query.filter_by(form_template_id=template_id, is_active=True).count()
    groups_count = ConditionalFieldGroup.query.filter_by(form_template_id=template_id, is_active=True).count()
    
    # Get recent conditions
    recent_conditions = FieldCondition.query.filter_by(
        form_template_id=template_id,
        is_active=True
    ).order_by(FieldCondition.created_at.desc()).limit(5).all()
    
    return render_template('admin/workflow_logic/dashboard.html',
                           template=template,
                           conditions_count=conditions_count,
                           rules_count=rules_count,
                           groups_count=groups_count,
                           recent_conditions=recent_conditions)

@workflow_logic_bp.route('/conditions/<int:template_id>')
@login_required
def list_conditions(template_id):
    """List all field conditions for a template"""
    template = FormTemplate.query.get_or_404(template_id)
    conditions = FieldCondition.query.filter_by(
        form_template_id=template_id
    ).order_by(FieldCondition.condition_order).all()
    
    return render_template('admin/workflow_logic/conditions_list.html',
                           template=template,
                           conditions=conditions)

@workflow_logic_bp.route('/conditions/add/<int:template_id>', methods=['GET', 'POST'])
@login_required
def add_condition(template_id):
    """Add new field condition"""
    template = FormTemplate.query.get_or_404(template_id)
    form = FieldConditionForm()
    
    # Populate field choices
    fields = template.active_fields
    field_choices = [(f.id, f.label) for f in fields]
    form.source_field_id.choices = field_choices
    form.target_field_id.choices = field_choices
    
    if form.validate_on_submit():
        condition = FieldCondition()
        condition.form_template_id = template_id
        condition.source_field_id = form.source_field_id.data
        condition.target_field_id = form.target_field_id.data
        condition.condition_type = form.condition_type.data
        condition.operator = form.operator.data
        condition.condition_value = form.condition_value.data
        condition.action = form.action.data
        condition.action_value = form.action_value.data
        condition.condition_order = form.condition_order.data
        condition.is_active = form.is_active.data
        
        db.session.add(condition)
        db.session.commit()
        
        flash(f'Field condition created successfully!', 'success')
        return redirect(url_for('workflow_logic.list_conditions', template_id=template_id))
    
    return render_template('admin/workflow_logic/condition_form.html',
                           form=form,
                           template=template,
                           title='Add Field Condition')

@workflow_logic_bp.route('/conditions/edit/<int:condition_id>', methods=['GET', 'POST'])
@login_required
def edit_condition(condition_id):
    """Edit field condition"""
    condition = FieldCondition.query.get_or_404(condition_id)
    template = condition.form_template
    form = FieldConditionForm(obj=condition)
    
    # Populate field choices
    fields = template.active_fields
    field_choices = [(f.id, f.label) for f in fields]
    form.source_field_id.choices = field_choices
    form.target_field_id.choices = field_choices
    
    if form.validate_on_submit():
        form.populate_obj(condition)
        db.session.commit()
        
        flash(f'Field condition updated successfully!', 'success')
        return redirect(url_for('workflow_logic.list_conditions', template_id=template.id))
    
    return render_template('admin/workflow_logic/condition_form.html',
                           form=form,
                           template=template,
                           title='Edit Field Condition')

@workflow_logic_bp.route('/conditions/delete/<int:condition_id>', methods=['POST'])
@login_required
def delete_condition(condition_id):
    """Delete field condition"""
    condition = FieldCondition.query.get_or_404(condition_id)
    template_id = condition.form_template_id
    
    db.session.delete(condition)
    db.session.commit()
    
    flash('Field condition deleted successfully!', 'success')
    return redirect(url_for('workflow_logic.list_conditions', template_id=template_id))

@workflow_logic_bp.route('/rules/<int:template_id>')
@login_required
def list_rules(template_id):
    """List workflow rules for a template"""
    template = FormTemplate.query.get_or_404(template_id)
    rules = WorkflowRule.query.filter_by(
        form_template_id=template_id
    ).order_by(WorkflowRule.priority.desc()).all()
    
    return render_template('admin/workflow_logic/rules_list.html',
                           template=template,
                           rules=rules)

@workflow_logic_bp.route('/test/<int:template_id>')
@login_required
def test_workflow(template_id):
    """Test workflow logic with sample data"""
    template = FormTemplate.query.get_or_404(template_id)
    
    return render_template('admin/workflow_logic/test_workflow.html',
                           template=template)

@workflow_logic_bp.route('/api/test_logic/<int:template_id>', methods=['POST'])
@login_required
def api_test_logic(template_id):
    """API endpoint to test workflow logic"""
    try:
        data = request.get_json()
        field_values = data.get('field_values', {})
        
        # Process workflow logic
        form_state = process_workflow_logic(template_id, field_values)
        
        return jsonify({
            'success': True,
            'form_state': form_state
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

@workflow_logic_bp.route('/api/field_options/<int:field_id>')
@login_required
def api_field_options(field_id):
    """Get field options for select fields"""
    field = CustomField.query.get_or_404(field_id)
    
    try:
        options = json.loads(field.field_options or '[]')
    except:
        options = []
    
    return jsonify({
        'success': True,
        'options': options,
        'field_type': field.field_type
    })

@workflow_logic_bp.route('/visual_builder/<int:template_id>')
@login_required
def visual_builder(template_id):
    """Visual workflow builder interface"""
    template = FormTemplate.query.get_or_404(template_id)
    
    # Get all conditions for visualization
    conditions = FieldCondition.query.filter_by(
        form_template_id=template_id,
        is_active=True
    ).all()
    
    # Convert to JSON for JavaScript
    conditions_json = [c.to_dict() for c in conditions]
    
    return render_template('admin/workflow_logic/visual_builder.html',
                           template=template,
                           conditions=conditions_json)

@workflow_logic_bp.route('/groups/<int:template_id>')
@login_required
def list_groups(template_id):
    """List field groups for a template"""
    template = FormTemplate.query.get_or_404(template_id)
    groups = ConditionalFieldGroup.query.filter_by(
        form_template_id=template_id
    ).all()
    
    return render_template('admin/workflow_logic/groups_list.html',
                           template=template,
                           groups=groups)

@workflow_logic_bp.route('/export/<int:template_id>')
@login_required
def export_workflow(template_id):
    """Export workflow configuration as JSON"""
    template = FormTemplate.query.get_or_404(template_id)
    
    # Get all workflow components
    conditions = FieldCondition.query.filter_by(form_template_id=template_id, is_active=True).all()
    rules = WorkflowRule.query.filter_by(form_template_id=template_id, is_active=True).all()
    groups = ConditionalFieldGroup.query.filter_by(form_template_id=template_id, is_active=True).all()
    
    # Build export data
    export_data = {
        'template': {
            'name': template.name,
            'code': template.code,
            'description': template.description,
            'module': template.module
        },
        'conditions': [c.to_dict() for c in conditions],
        'rules': [{'name': r.name, 'description': r.description, 'config': r.get_rule_config()} for r in rules],
        'groups': [{'name': g.name, 'description': g.description, 'field_ids': g.get_field_ids()} for g in groups]
    }
    
    return jsonify(export_data)