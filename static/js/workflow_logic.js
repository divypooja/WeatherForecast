/**
 * Workflow Logic JavaScript Library
 * Handles conditional field logic and dynamic form behavior
 */

class WorkflowLogicEngine {
    constructor(templateId, conditions = []) {
        this.templateId = templateId;
        this.conditions = conditions;
        this.fieldValues = {};
        this.formState = {
            visible_fields: [],
            required_fields: [],
            field_values: {},
            field_actions: {}
        };
        
        this.init();
    }
    
    init() {
        this.bindEvents();
        this.loadInitialState();
    }
    
    // Bind events to form fields
    bindEvents() {
        $(document).on('change keyup blur', '.dynamic-field', (e) => {
            this.handleFieldChange(e.target);
        });
    }
    
    // Load initial form state
    loadInitialState() {
        $('.dynamic-field').each((index, field) => {
            this.updateFieldValue(field);
        });
        this.processWorkflowLogic();
    }
    
    // Handle field value changes
    handleFieldChange(field) {
        this.updateFieldValue(field);
        this.processWorkflowLogic();
    }
    
    // Update field value in memory
    updateFieldValue(field) {
        const $field = $(field);
        const fieldId = $field.data('field-id');
        let value = $field.val();
        
        if ($field.attr('type') === 'checkbox') {
            value = $field.is(':checked') ? '1' : '0';
        }
        
        this.fieldValues[fieldId] = value;
    }
    
    // Process workflow logic
    async processWorkflowLogic() {
        try {
            const response = await fetch(`/admin/workflow/api/test_logic/${this.templateId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    field_values: this.fieldValues
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.applyFormState(data.form_state);
            } else {
                console.error('Workflow logic error:', data.error);
            }
        } catch (error) {
            console.error('Failed to process workflow logic:', error);
        }
    }
    
    // Apply form state changes
    applyFormState(formState) {
        this.formState = formState;
        
        // Apply visibility changes
        this.applyVisibilityChanges();
        
        // Apply required field changes
        this.applyRequiredChanges();
        
        // Apply value changes
        this.applyValueChanges();
        
        // Trigger custom event
        $(document).trigger('workflowStateChanged', [formState]);
    }
    
    // Apply field visibility changes
    applyVisibilityChanges() {
        $('.dynamic-field').each((index, field) => {
            const $field = $(field);
            const fieldId = $field.data('field-id');
            const $container = $field.closest('.field-container, .form-group, .mb-3, .col-md-6');
            
            if (this.formState.visible_fields.includes(String(fieldId))) {
                $container.show();
                $container.removeClass('d-none');
            } else if (this.formState.visible_fields.length > 0) {
                // Only hide if there are explicit visibility rules
                $container.hide();
                $container.addClass('d-none');
            }
        });
    }
    
    // Apply required field changes
    applyRequiredChanges() {
        $('.dynamic-field').each((index, field) => {
            const $field = $(field);
            const fieldId = $field.data('field-id');
            const $label = $field.closest('.field-container, .form-group, .mb-3, .col-md-6').find('label');
            
            if (this.formState.required_fields.includes(String(fieldId))) {
                $field.prop('required', true);
                if (!$label.find('.required-indicator').length) {
                    $label.append(' <span class="required-indicator text-danger">*</span>');
                }
                $field.addClass('required-field');
            } else {
                $field.prop('required', false);
                $label.find('.required-indicator').remove();
                $field.removeClass('required-field');
            }
        });
    }
    
    // Apply automatic value changes
    applyValueChanges() {
        for (const [fieldId, value] of Object.entries(this.formState.field_values)) {
            const $field = $(`.dynamic-field[data-field-id="${fieldId}"]`);
            
            if ($field.length && $field.val() !== String(value)) {
                if ($field.attr('type') === 'checkbox') {
                    $field.prop('checked', value === '1' || value === true);
                } else {
                    $field.val(value);
                }
                
                // Add visual indicator for auto-set values
                this.showAutoValueIndicator($field);
            }
        }
    }
    
    // Show indicator for automatically set values
    showAutoValueIndicator($field) {
        const $container = $field.closest('.field-container, .form-group, .mb-3, .col-md-6');
        let $indicator = $container.find('.auto-value-indicator');
        
        if (!$indicator.length) {
            $indicator = $('<small class="auto-value-indicator text-info"><i class="fas fa-magic"></i> Auto-set</small>');
            $container.append($indicator);
        }
        
        $indicator.show().fadeOut(3000);
    }
    
    // Get current form state
    getFormState() {
        return this.formState;
    }
    
    // Get field values
    getFieldValues() {
        return this.fieldValues;
    }
    
    // Add new condition
    addCondition(condition) {
        this.conditions.push(condition);
        this.processWorkflowLogic();
    }
    
    // Remove condition
    removeCondition(conditionId) {
        this.conditions = this.conditions.filter(c => c.id !== conditionId);
        this.processWorkflowLogic();
    }
    
    // Update condition
    updateCondition(conditionId, updatedCondition) {
        const index = this.conditions.findIndex(c => c.id === conditionId);
        if (index !== -1) {
            this.conditions[index] = updatedCondition;
            this.processWorkflowLogic();
        }
    }
}

// Utility functions for workflow logic
const WorkflowUtils = {
    // Initialize workflow logic on a form
    initializeForm: function(templateId, formSelector = 'form') {
        const $form = $(formSelector);
        
        // Add dynamic-field class to form fields
        $form.find('input, select, textarea').each(function() {
            const $field = $(this);
            const fieldId = $field.attr('name')?.replace('field_', '') || $field.data('field-id');
            
            if (fieldId) {
                $field.addClass('dynamic-field');
                $field.attr('data-field-id', fieldId);
            }
        });
        
        // Create workflow engine instance
        const engine = new WorkflowLogicEngine(templateId);
        $form.data('workflowEngine', engine);
        
        return engine;
    },
    
    // Create field condition preview
    createConditionPreview: function(condition) {
        let preview = `<strong>${condition.condition_type.toUpperCase()}</strong> `;
        preview += `"${condition.source_field_name}" ${condition.operator.replace('_', ' ')}`;
        
        if (condition.condition_value && !['empty', 'not_empty'].includes(condition.operator)) {
            preview += ` "${condition.condition_value}"`;
        }
        
        preview += `<br><strong>THEN</strong> ${condition.action.replace('_', ' ')} `;
        preview += `"${condition.target_field_name}"`;
        
        if (condition.action_value && condition.action === 'set_value') {
            preview += ` to "${condition.action_value}"`;
        }
        
        return preview;
    },
    
    // Validate condition
    validateCondition: function(condition) {
        const errors = [];
        
        if (!condition.source_field_id) {
            errors.push('Source field is required');
        }
        
        if (!condition.target_field_id) {
            errors.push('Target field is required');
        }
        
        if (condition.source_field_id === condition.target_field_id) {
            errors.push('Source and target fields cannot be the same');
        }
        
        if (!condition.operator) {
            errors.push('Condition operator is required');
        }
        
        if (!condition.action) {
            errors.push('Action is required');
        }
        
        if (condition.action === 'set_value' && !condition.action_value) {
            errors.push('Action value is required for "Set Value" action');
        }
        
        return errors;
    },
    
    // Export workflow configuration
    exportWorkflow: function(templateId) {
        return fetch(`/admin/workflow/export/${templateId}`)
            .then(response => response.json())
            .then(data => {
                const blob = new Blob([JSON.stringify(data, null, 2)], {
                    type: 'application/json'
                });
                
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `workflow_${templateId}_${new Date().toISOString().split('T')[0]}.json`;
                a.click();
                
                URL.revokeObjectURL(url);
            });
    }
};

// jQuery plugin for workflow logic
$.fn.workflowLogic = function(templateId, options = {}) {
    return this.each(function() {
        const $form = $(this);
        
        if (!$form.data('workflowEngine')) {
            const engine = WorkflowUtils.initializeForm(templateId, this);
            
            // Apply custom options
            if (options.autoTest !== false) {
                engine.processWorkflowLogic();
            }
        }
    });
};

// Global initialization
$(document).ready(function() {
    // Auto-initialize forms with workflow-enabled class
    $('.workflow-enabled').each(function() {
        const templateId = $(this).data('template-id');
        if (templateId) {
            $(this).workflowLogic(templateId);
        }
    });
});