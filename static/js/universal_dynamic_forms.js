/**
 * Universal Dynamic Forms Integration
 * This script automatically integrates dynamic forms into all existing application forms
 */

// Configuration mapping form types to template codes
const FORM_TEMPLATE_MAPPING = {
    // Production Module
    'bom_form': 'bom_management',
    'production_form': 'production_management',
    
    // Job Work Module
    'jobwork_form': 'job_work_management',
    'multiprocess_jobwork_form': 'job_work_management',
    
    // GRN Module
    'grn_form': 'grn_management',
    'quick_receive_form': 'grn_management',
    
    // Purchase Orders
    'purchase_order_form': 'purchase_order_management',
    'po_form': 'purchase_order_management',
    
    // Sales Orders
    'sales_order_form': 'sales_order_management',
    'so_form': 'sales_order_management',
    
    // Inventory
    'inventory_form': 'inventory_management',
    'item_form': 'inventory_management',
    'add_item_form': 'inventory_management',
    
    // UOM Management
    'uom_form': 'uom_management',
    
    // Employee Management
    'employee_form': 'employee_management',
    'salary_form': 'employee_management',
    
    // Factory Expenses
    'expense_form': 'factory_expense_management',
    'factory_expense_form': 'factory_expense_management'
};

class UniversalDynamicForms {
    constructor() {
        this.initializeOnLoad();
    }
    
    initializeOnLoad() {
        document.addEventListener('DOMContentLoaded', () => {
            this.detectAndIntegrateForms();
        });
    }
    
    detectAndIntegrateForms() {
        // Look for forms that should have dynamic fields
        const forms = document.querySelectorAll('form');
        
        forms.forEach(form => {
            const templateCode = this.detectFormType(form);
            if (templateCode) {
                this.integrateDynamicFields(form, templateCode);
            }
        });
    }
    
    detectFormType(form) {
        // Check form ID
        if (form.id && FORM_TEMPLATE_MAPPING[form.id]) {
            return FORM_TEMPLATE_MAPPING[form.id];
        }
        
        // Check form classes
        for (const className of form.classList) {
            if (FORM_TEMPLATE_MAPPING[className]) {
                return FORM_TEMPLATE_MAPPING[className];
            }
        }
        
        // Check page URL patterns
        const path = window.location.pathname;
        if (path.includes('/production/') && (path.includes('bom') || path.includes('add') || path.includes('edit'))) {
            return 'bom_management';
        } else if (path.includes('/job_work/') && (path.includes('add') || path.includes('edit'))) {
            return 'job_work_management';
        } else if (path.includes('/grn/') && (path.includes('add') || path.includes('receive'))) {
            return 'grn_management';
        } else if (path.includes('/purchase/') && (path.includes('add') || path.includes('edit'))) {
            return 'purchase_order_management';
        } else if (path.includes('/sales/') && (path.includes('add') || path.includes('edit'))) {
            return 'sales_order_management';
        } else if (path.includes('/inventory/') && (path.includes('add') || path.includes('edit'))) {
            return 'inventory_management';
        } else if (path.includes('/employees/') && (path.includes('add') || path.includes('edit'))) {
            return 'employee_management';
        } else if (path.includes('/expenses/') && (path.includes('add') || path.includes('edit'))) {
            return 'factory_expense_management';
        } else if (path.includes('/uom/') && (path.includes('add') || path.includes('edit'))) {
            return 'uom_management';
        }
        
        return null;
    }
    
    integrateDynamicFields(form, templateCode) {
        // Check if dynamic fields container already exists
        if (form.querySelector('#dynamic-fields-container')) {
            return; // Already integrated
        }
        
        // Create dynamic fields container
        const container = this.createDynamicFieldsContainer(templateCode);
        
        // Find the best insertion point (before submit buttons)
        const insertionPoint = this.findInsertionPoint(form);
        
        if (insertionPoint) {
            insertionPoint.parentNode.insertBefore(container, insertionPoint);
        } else {
            // Fallback: append to form
            form.appendChild(container);
        }
        
        // Load the dynamic fields
        this.loadDynamicFields(templateCode);
    }
    
    createDynamicFieldsContainer(templateCode) {
        const container = document.createElement('div');
        container.className = 'card mt-3';
        container.innerHTML = `
            <div class="card-header bg-info text-white">
                <h6><i class="fas fa-magic"></i> Custom Fields <span class="badge bg-warning">DYNAMIC</span></h6>
                <small class="d-block mt-1">Template: ${templateCode}</small>
            </div>
            <div class="card-body" id="dynamic-fields-container">
                <div class="text-center py-3" id="dynamic-fields-loading">
                    <i class="fas fa-spinner fa-spin"></i> Loading custom fields...
                </div>
                <div id="dynamic-fields-content" style="display: none;">
                    <!-- Dynamic fields render here -->
                </div>
                <div id="no-dynamic-fields" style="display: none;" class="text-center py-3 text-muted">
                    <i class="fas fa-info-circle"></i> No custom fields configured for this form.
                    <br><small>Add custom fields in <a href="/admin/forms/dashboard" target="_blank">Dynamic Forms</a> management.</small>
                </div>
            </div>
        `;
        
        return container;
    }
    
    findInsertionPoint(form) {
        // Look for submit buttons or form actions
        const submitButtons = form.querySelectorAll('button[type="submit"], input[type="submit"]');
        if (submitButtons.length > 0) {
            // Insert before the last submit button's container
            const lastButton = submitButtons[submitButtons.length - 1];
            const buttonContainer = lastButton.closest('.card-footer, .form-group, .row, .col, .d-flex');
            return buttonContainer || lastButton;
        }
        
        // Look for card footer
        const cardFooter = form.querySelector('.card-footer');
        if (cardFooter) {
            return cardFooter;
        }
        
        // Look for button containers
        const buttonContainers = form.querySelectorAll('.btn-group, .form-actions, .form-buttons');
        if (buttonContainers.length > 0) {
            return buttonContainers[buttonContainers.length - 1];
        }
        
        return null;
    }
    
    loadDynamicFields(templateCode) {
        const loading = document.getElementById('dynamic-fields-loading');
        const content = document.getElementById('dynamic-fields-content');
        const noFields = document.getElementById('no-dynamic-fields');
        
        if (!loading || !content || !noFields) return;
        
        // Load custom fields from Dynamic Forms API
        fetch(`/admin/forms/api/templates/${templateCode}/fields`)
            .then(response => response.json())
            .then(data => {
                loading.style.display = 'none';
                
                if (data.fields && data.fields.length > 0) {
                    content.style.display = 'block';
                    this.renderDynamicFields(data.fields, content);
                } else {
                    noFields.style.display = 'block';
                }
            })
            .catch(error => {
                console.log(`No dynamic fields configured for ${templateCode} template`);
                loading.style.display = 'none';
                noFields.style.display = 'block';
            });
    }
    
    renderDynamicFields(fields, container) {
        let html = '';
        
        // Group fields by field_group
        const groupedFields = {};
        fields.forEach(field => {
            const group = field.field_group || 'General';
            if (!groupedFields[group]) {
                groupedFields[group] = [];
            }
            groupedFields[group].push(field);
        });
        
        // Render each group
        Object.keys(groupedFields).forEach(groupName => {
            html += `<div class="row mb-3">`;
            html += `<div class="col-12"><h6 class="text-primary border-bottom pb-1">${groupName}</h6></div>`;
            
            groupedFields[groupName].forEach(field => {
                html += `<div class="col-md-${field.column_width || 6} mb-3">`;
                html += this.renderDynamicField(field);
                html += `</div>`;
            });
            
            html += `</div>`;
        });
        
        container.innerHTML = html;
        this.applyWorkflowLogic();
    }
    
    renderDynamicField(field) {
        let html = `<label class="form-label">${field.label}`;
        if (field.is_required) html += ' <span class="text-danger">*</span>';
        html += `</label>`;
        
        const fieldName = `dynamic_${field.field_name}`;
        
        switch (field.field_type) {
            case 'text':
                html += `<input type="text" class="form-control" name="${fieldName}" 
                         placeholder="${field.placeholder || ''}" 
                         ${field.is_required ? 'required' : ''}>`;
                break;
            case 'textarea':
                html += `<textarea class="form-control" name="${fieldName}" rows="3" 
                         placeholder="${field.placeholder || ''}" 
                         ${field.is_required ? 'required' : ''}></textarea>`;
                break;
            case 'number':
            case 'decimal':
                html += `<input type="number" class="form-control" name="${fieldName}" 
                         step="${field.field_type === 'decimal' ? '0.01' : '1'}"
                         placeholder="${field.placeholder || ''}" 
                         ${field.is_required ? 'required' : ''}>`;
                break;
            case 'currency':
                html += `<div class="input-group">
                         <span class="input-group-text">₹</span>
                         <input type="number" class="form-control" name="${fieldName}" 
                                step="0.01" placeholder="${field.placeholder || '0.00'}" 
                                ${field.is_required ? 'required' : ''}>
                         </div>`;
                break;
            case 'select':
                html += `<select class="form-select" name="${fieldName}" 
                         ${field.is_required ? 'required' : ''}>`;
                html += `<option value="">Choose...</option>`;
                if (field.options) {
                    field.options.forEach(option => {
                        html += `<option value="${option}">${option}</option>`;
                    });
                }
                html += `</select>`;
                break;
            case 'checkbox':
                html += `<div class="form-check">
                         <input type="checkbox" class="form-check-input" name="${fieldName}" 
                                id="${fieldName}">
                         <label class="form-check-label" for="${fieldName}">
                             ${field.help_text || 'Enable this option'}
                         </label>
                         </div>`;
                break;
            case 'date':
                html += `<input type="date" class="form-control" name="${fieldName}" 
                         ${field.is_required ? 'required' : ''}>`;
                break;
            case 'datetime':
                html += `<input type="datetime-local" class="form-control" name="${fieldName}" 
                         ${field.is_required ? 'required' : ''}>`;
                break;
            case 'email':
                html += `<input type="email" class="form-control" name="${fieldName}" 
                         placeholder="${field.placeholder || 'email@example.com'}" 
                         ${field.is_required ? 'required' : ''}>`;
                break;
            case 'url':
                html += `<input type="url" class="form-control" name="${fieldName}" 
                         placeholder="${field.placeholder || 'https://example.com'}" 
                         ${field.is_required ? 'required' : ''}>`;
                break;
            default:
                html += `<input type="text" class="form-control" name="${fieldName}" 
                         placeholder="${field.placeholder || ''}" 
                         ${field.is_required ? 'required' : ''}>`;
        }
        
        if (field.help_text) {
            html += `<small class="form-text text-muted">${field.help_text}</small>`;
        }
        
        return html;
    }
    
    applyWorkflowLogic() {
        console.log('🔗 Universal Dynamic Forms: Workflow logic system ready');
        
        // Load workflow logic for this template if available
        if (typeof loadWorkflowLogic === 'function') {
            loadWorkflowLogic();
        }
    }
    
    // Utility method to manually integrate a specific form
    static integrateForm(formElement, templateCode) {
        const instance = new UniversalDynamicForms();
        instance.integrateDynamicFields(formElement, templateCode);
    }
}

// Initialize the universal dynamic forms system
const universalDynamicForms = new UniversalDynamicForms();

// Export for manual usage
window.UniversalDynamicForms = UniversalDynamicForms;