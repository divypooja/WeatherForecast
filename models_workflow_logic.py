"""
Workflow Logic Models for Dynamic Forms System
Implements conditional logic and field connections for custom workflows
"""

from app import db
from datetime import datetime
import json

class FieldCondition(db.Model):
    """
    Model for storing conditional logic between form fields
    Supports if/else/elif conditions for dynamic workflow creation
    """
    __tablename__ = 'field_conditions'
    
    id = db.Column(db.Integer, primary_key=True)
    form_template_id = db.Column(db.Integer, db.ForeignKey('form_templates.id'), nullable=False)
    
    # Source field that triggers the condition
    source_field_id = db.Column(db.Integer, db.ForeignKey('custom_fields.id'), nullable=False)
    
    # Target field that is affected by the condition
    target_field_id = db.Column(db.Integer, db.ForeignKey('custom_fields.id'), nullable=False)
    
    # Condition type: if, elif, else
    condition_type = db.Column(db.String(10), nullable=False, default='if')
    
    # Operator: equals, not_equals, greater_than, less_than, contains, empty, not_empty
    operator = db.Column(db.String(20), nullable=False)
    
    # Value to compare against (JSON for complex values)
    condition_value = db.Column(db.Text)
    
    # Action to take: show, hide, require, optional, set_value, clear_value
    action = db.Column(db.String(20), nullable=False)
    
    # Action value (for set_value actions)
    action_value = db.Column(db.Text)
    
    # Order for multiple conditions on same source field
    condition_order = db.Column(db.Integer, default=0)
    
    # Active status
    is_active = db.Column(db.Boolean, default=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    form_template = db.relationship('FormTemplate', backref='field_conditions')
    source_field = db.relationship('CustomField', foreign_keys=[source_field_id], backref='source_conditions')
    target_field = db.relationship('CustomField', foreign_keys=[target_field_id], backref='target_conditions')
    
    def __repr__(self):
        return f'<FieldCondition {self.condition_type}: {self.source_field.name} -> {self.target_field.name}>'
    
    def to_dict(self):
        """Convert condition to dictionary for JavaScript"""
        return {
            'id': self.id,
            'source_field_id': self.source_field_id,
            'target_field_id': self.target_field_id,
            'condition_type': self.condition_type,
            'operator': self.operator,
            'condition_value': self.condition_value,
            'action': self.action,
            'action_value': self.action_value,
            'condition_order': self.condition_order,
            'is_active': self.is_active
        }

class WorkflowRule(db.Model):
    """
    Model for complex workflow rules that can chain multiple conditions
    Supports advanced if/elif/else logic flows
    """
    __tablename__ = 'workflow_rules'
    
    id = db.Column(db.Integer, primary_key=True)
    form_template_id = db.Column(db.Integer, db.ForeignKey('form_templates.id'), nullable=False)
    
    # Rule name and description
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    
    # Rule configuration as JSON
    # Structure: {"conditions": [...], "actions": [...], "logic": "AND/OR"}
    rule_config = db.Column(db.Text)
    
    # Rule priority (higher number = higher priority)
    priority = db.Column(db.Integer, default=0)
    
    # Active status
    is_active = db.Column(db.Boolean, default=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    form_template = db.relationship('FormTemplate', backref='workflow_rules')
    
    def __repr__(self):
        return f'<WorkflowRule {self.name}>'
    
    def get_rule_config(self):
        """Get rule configuration as Python object"""
        if self.rule_config:
            return json.loads(self.rule_config)
        return {}
    
    def set_rule_config(self, config):
        """Set rule configuration from Python object"""
        self.rule_config = json.dumps(config)

class FormWorkflowState(db.Model):
    """
    Model for tracking form workflow states and field values
    Stores current state of dynamic forms with conditional logic
    """
    __tablename__ = 'form_workflow_states'
    
    id = db.Column(db.Integer, primary_key=True)
    form_template_id = db.Column(db.Integer, db.ForeignKey('form_templates.id'), nullable=False)
    
    # Reference to the actual form record (e.g., purchase_order_id, job_work_id)
    record_type = db.Column(db.String(50), nullable=False)  # 'purchase_order', 'job_work', etc.
    record_id = db.Column(db.Integer, nullable=False)
    
    # Current workflow state as JSON
    # Structure: {"field_values": {...}, "visible_fields": [...], "required_fields": [...]}
    workflow_state = db.Column(db.Text)
    
    # Current step/stage in workflow
    current_step = db.Column(db.String(50))
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    form_template = db.relationship('FormTemplate', backref='workflow_states')
    
    def __repr__(self):
        return f'<FormWorkflowState {self.record_type}:{self.record_id}>'
    
    def get_workflow_state(self):
        """Get workflow state as Python object"""
        if self.workflow_state:
            return json.loads(self.workflow_state)
        return {}
    
    def set_workflow_state(self, state):
        """Set workflow state from Python object"""
        self.workflow_state = json.dumps(state)

class ConditionalFieldGroup(db.Model):
    """
    Model for grouping fields that work together in conditional logic
    Allows creating field sets that show/hide together
    """
    __tablename__ = 'conditional_field_groups'
    
    id = db.Column(db.Integer, primary_key=True)
    form_template_id = db.Column(db.Integer, db.ForeignKey('form_templates.id'), nullable=False)
    
    # Group name and description
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    
    # Group behavior: show_all, hide_all, require_all, optional_all
    group_behavior = db.Column(db.String(20), default='show_all')
    
    # Fields in this group (JSON array of field IDs)
    field_ids = db.Column(db.Text)
    
    # Active status
    is_active = db.Column(db.Boolean, default=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    form_template = db.relationship('FormTemplate', backref='field_groups')
    
    def __repr__(self):
        return f'<ConditionalFieldGroup {self.name}>'
    
    def get_field_ids(self):
        """Get field IDs as Python list"""
        if self.field_ids:
            return json.loads(self.field_ids)
        return []
    
    def set_field_ids(self, field_ids):
        """Set field IDs from Python list"""
        self.field_ids = json.dumps(field_ids)

# Helper Functions for Workflow Logic

def evaluate_condition(source_value, operator, condition_value):
    """
    Evaluate a single condition
    
    Args:
        source_value: Current value of source field
        operator: Comparison operator
        condition_value: Value to compare against
    
    Returns:
        bool: True if condition is met
    """
    if operator == 'equals':
        return str(source_value) == str(condition_value)
    elif operator == 'not_equals':
        return str(source_value) != str(condition_value)
    elif operator == 'greater_than':
        try:
            return float(source_value) > float(condition_value)
        except (ValueError, TypeError):
            return False
    elif operator == 'less_than':
        try:
            return float(source_value) < float(condition_value)
        except (ValueError, TypeError):
            return False
    elif operator == 'contains':
        return str(condition_value).lower() in str(source_value).lower()
    elif operator == 'empty':
        return not source_value or source_value == ''
    elif operator == 'not_empty':
        return source_value and source_value != ''
    elif operator == 'starts_with':
        return str(source_value).lower().startswith(str(condition_value).lower())
    elif operator == 'ends_with':
        return str(source_value).lower().endswith(str(condition_value).lower())
    
    return False

def process_workflow_logic(form_template_id, field_values):
    """
    Process all workflow logic for a form template
    
    Args:
        form_template_id: ID of the form template
        field_values: Dict of current field values
    
    Returns:
        dict: Updated form state with visibility, requirements, and values
    """
    # Get all conditions for this form template
    conditions = FieldCondition.query.filter_by(
        form_template_id=form_template_id,
        is_active=True
    ).order_by(FieldCondition.condition_order).all()
    
    # Initialize form state
    form_state = {
        'visible_fields': [],
        'required_fields': [],
        'field_values': field_values.copy(),
        'field_actions': {}
    }
    
    # Process each condition
    for condition in conditions:
        source_field_id = str(condition.source_field_id)
        target_field_id = str(condition.target_field_id)
        
        # Get source field value
        source_value = field_values.get(source_field_id, '')
        
        # Evaluate condition
        condition_met = evaluate_condition(source_value, condition.operator, condition.condition_value)
        
        # Apply action if condition is met
        if condition_met:
            if condition.action == 'show':
                if target_field_id not in form_state['visible_fields']:
                    form_state['visible_fields'].append(target_field_id)
            elif condition.action == 'hide':
                if target_field_id in form_state['visible_fields']:
                    form_state['visible_fields'].remove(target_field_id)
            elif condition.action == 'require':
                if target_field_id not in form_state['required_fields']:
                    form_state['required_fields'].append(target_field_id)
            elif condition.action == 'optional':
                if target_field_id in form_state['required_fields']:
                    form_state['required_fields'].remove(target_field_id)
            elif condition.action == 'set_value':
                form_state['field_values'][target_field_id] = condition.action_value
            elif condition.action == 'clear_value':
                form_state['field_values'][target_field_id] = ''
    
    return form_state