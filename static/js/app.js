/**
 * Factory Management System JavaScript
 * Provides enhanced user interactions and dynamic functionality
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    initializeTooltips();
    
    // Initialize popovers
    initializePopovers();
    
    // Setup form enhancements
    setupFormEnhancements();
    
    // Setup table enhancements
    setupTableEnhancements();
    
    // Setup dashboard functionality
    setupDashboard();
    
    // Setup confirmation dialogs
    setupConfirmationDialogs();
    
    // Setup search functionality
    setupSearchEnhancements();
    
    // Setup auto-refresh for dashboards
    setupAutoRefresh();
});

/**
 * Initialize Bootstrap tooltips
 */
function initializeTooltips() {
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

/**
 * Initialize Bootstrap popovers
 */
function initializePopovers() {
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
}

/**
 * Setup form enhancements
 */
function setupFormEnhancements() {
    // Auto-focus first input in forms
    const firstInput = document.querySelector('form input:not([type="hidden"]):not([readonly])');
    if (firstInput) {
        firstInput.focus();
    }
    
    // Form validation feedback
    const forms = document.querySelectorAll('form');
    forms.forEach(function(form) {
        form.addEventListener('submit', function(event) {
            const submitBtn = form.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.classList.add('loading');
                submitBtn.disabled = true;
            }
        });
    });
    
    // Number input formatting
    const numberInputs = document.querySelectorAll('input[type="number"]');
    numberInputs.forEach(function(input) {
        input.addEventListener('blur', function() {
            if (this.value && !isNaN(this.value)) {
                this.value = parseFloat(this.value).toFixed(2);
            }
        });
    });
    
    // Date input default to today for new records
    const dateInputs = document.querySelectorAll('input[type="date"]');
    dateInputs.forEach(function(input) {
        if (!input.value && input.name.includes('date') && !input.name.includes('expected')) {
            input.value = new Date().toISOString().split('T')[0];
        }
    });
}

/**
 * Setup table enhancements
 */
function setupTableEnhancements() {
    // Sortable table headers
    const sortableHeaders = document.querySelectorAll('th[data-sort]');
    sortableHeaders.forEach(function(header) {
        header.style.cursor = 'pointer';
        header.addEventListener('click', function() {
            sortTable(this);
        });
    });
    
    // Row highlighting on hover
    const tableRows = document.querySelectorAll('tbody tr');
    tableRows.forEach(function(row) {
        row.addEventListener('mouseenter', function() {
            this.style.backgroundColor = 'var(--bs-gray-100)';
        });
        
        row.addEventListener('mouseleave', function() {
            this.style.backgroundColor = '';
        });
    });
    
    // Checkbox selection for batch operations
    const selectAllCheckbox = document.querySelector('#selectAll');
    if (selectAllCheckbox) {
        selectAllCheckbox.addEventListener('change', function() {
            const checkboxes = document.querySelectorAll('tbody input[type="checkbox"]');
            checkboxes.forEach(function(checkbox) {
                checkbox.checked = selectAllCheckbox.checked;
            });
            updateBatchActions();
        });
    }
    
    const rowCheckboxes = document.querySelectorAll('tbody input[type="checkbox"]');
    rowCheckboxes.forEach(function(checkbox) {
        checkbox.addEventListener('change', updateBatchActions);
    });
}

/**
 * Setup dashboard functionality
 */
function setupDashboard() {
    // Animate counter numbers
    const counters = document.querySelectorAll('.dashboard-counter');
    counters.forEach(function(counter) {
        animateCounter(counter);
    });
    
    // Dashboard card click handlers
    const dashboardCards = document.querySelectorAll('.dashboard-card');
    dashboardCards.forEach(function(card) {
        const link = card.querySelector('a');
        if (link) {
            card.style.cursor = 'pointer';
            card.addEventListener('click', function(e) {
                if (e.target.tagName !== 'A') {
                    link.click();
                }
            });
        }
    });
    
    // Refresh dashboard data
    const refreshButton = document.querySelector('#refreshDashboard');
    if (refreshButton) {
        refreshButton.addEventListener('click', function() {
            location.reload();
        });
    }
}

/**
 * Setup confirmation dialogs
 */
function setupConfirmationDialogs() {
    // Delete confirmations
    const deleteButtons = document.querySelectorAll('[data-confirm-delete]');
    deleteButtons.forEach(function(button) {
        button.addEventListener('click', function(e) {
            const message = this.getAttribute('data-confirm-delete') || 'Are you sure you want to delete this item?';
            if (!confirm(message)) {
                e.preventDefault();
                return false;
            }
        });
    });
    
    // Status change confirmations
    const statusButtons = document.querySelectorAll('[data-confirm-status]');
    statusButtons.forEach(function(button) {
        button.addEventListener('click', function(e) {
            const message = this.getAttribute('data-confirm-status') || 'Are you sure you want to change the status?';
            if (!confirm(message)) {
                e.preventDefault();
                return false;
            }
        });
    });
}

/**
 * Setup search enhancements
 */
function setupSearchEnhancements() {
    // Real-time search (debounced)
    const searchInputs = document.querySelectorAll('input[name="search"]');
    searchInputs.forEach(function(input) {
        let searchTimeout;
        input.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(function() {
                if (input.form) {
                    input.form.submit();
                }
            }, 500);
        });
    });
    
    // Clear search button
    const clearSearchButtons = document.querySelectorAll('.clear-search');
    clearSearchButtons.forEach(function(button) {
        button.addEventListener('click', function() {
            const searchInput = document.querySelector('input[name="search"]');
            if (searchInput) {
                searchInput.value = '';
                searchInput.form.submit();
            }
        });
    });
}

/**
 * Setup auto-refresh for dashboards
 */
function setupAutoRefresh() {
    // Auto-refresh dashboard every 5 minutes if user is active
    if (window.location.pathname.includes('dashboard')) {
        let lastActivity = Date.now();
        let refreshInterval;
        
        // Track user activity
        document.addEventListener('mousemove', function() {
            lastActivity = Date.now();
        });
        
        document.addEventListener('keypress', function() {
            lastActivity = Date.now();
        });
        
        // Set up refresh interval
        refreshInterval = setInterval(function() {
            // Only refresh if user was active in the last 10 minutes
            if (Date.now() - lastActivity < 10 * 60 * 1000) {
                // Show refresh indicator
                showRefreshIndicator();
                
                // Refresh after 2 seconds
                setTimeout(function() {
                    location.reload();
                }, 2000);
            }
        }, 5 * 60 * 1000); // 5 minutes
    }
}

/**
 * Utility Functions
 */

/**
 * Animate counter numbers
 */
function animateCounter(element) {
    const target = parseInt(element.textContent);
    const duration = 1000;
    const startTime = Date.now();
    
    function update() {
        const elapsed = Date.now() - startTime;
        const progress = Math.min(elapsed / duration, 1);
        const current = Math.floor(progress * target);
        element.textContent = current;
        
        if (progress < 1) {
            requestAnimationFrame(update);
        }
    }
    
    update();
}

/**
 * Sort table by column
 */
function sortTable(header) {
    const table = header.closest('table');
    const tbody = table.querySelector('tbody');
    const rows = Array.from(tbody.querySelectorAll('tr'));
    const column = Array.from(header.parentNode.children).indexOf(header);
    const isAscending = !header.classList.contains('sort-asc');
    
    // Clear existing sort classes
    table.querySelectorAll('th').forEach(function(th) {
        th.classList.remove('sort-asc', 'sort-desc');
    });
    
    // Add sort class to current header
    header.classList.add(isAscending ? 'sort-asc' : 'sort-desc');
    
    // Sort rows
    rows.sort(function(a, b) {
        const aText = a.children[column].textContent.trim();
        const bText = b.children[column].textContent.trim();
        
        // Try to parse as numbers
        const aNum = parseFloat(aText);
        const bNum = parseFloat(bText);
        
        let comparison;
        if (!isNaN(aNum) && !isNaN(bNum)) {
            comparison = aNum - bNum;
        } else {
            comparison = aText.localeCompare(bText);
        }
        
        return isAscending ? comparison : -comparison;
    });
    
    // Reorder rows in DOM
    rows.forEach(function(row) {
        tbody.appendChild(row);
    });
}

/**
 * Update batch action buttons based on selection
 */
function updateBatchActions() {
    const checkedBoxes = document.querySelectorAll('tbody input[type="checkbox"]:checked');
    const batchActions = document.querySelector('.batch-actions');
    
    if (batchActions) {
        batchActions.style.display = checkedBoxes.length > 0 ? 'block' : 'none';
        
        const countElement = batchActions.querySelector('.selected-count');
        if (countElement) {
            countElement.textContent = checkedBoxes.length;
        }
    }
}

/**
 * Show refresh indicator
 */
function showRefreshIndicator() {
    // Create refresh indicator if it doesn't exist
    let indicator = document.querySelector('#refresh-indicator');
    if (!indicator) {
        indicator = document.createElement('div');
        indicator.id = 'refresh-indicator';
        indicator.className = 'alert alert-info position-fixed top-0 start-50 translate-middle-x mt-3';
        indicator.style.zIndex = '9999';
        indicator.innerHTML = '<i class="fas fa-sync-alt fa-spin"></i> Refreshing data...';
        document.body.appendChild(indicator);
    }
    
    indicator.style.display = 'block';
}

/**
 * Format currency values
 */
function formatCurrency(amount) {
    return new Intl.NumberFormat('en-IN', {
        style: 'currency',
        currency: 'INR'
    }).format(amount);
}

/**
 * Format date values
 */
function formatDate(date) {
    return new Intl.DateTimeFormat('en-IN', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    }).format(new Date(date));
}

/**
 * Show toast notification
 */
function showToast(message, type = 'info') {
    const toastContainer = document.querySelector('#toast-container') || createToastContainer();
    
    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-white bg-${type} border-0`;
    toast.setAttribute('role', 'alert');
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">${message}</div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
    `;
    
    toastContainer.appendChild(toast);
    
    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();
    
    // Remove toast after it's hidden
    toast.addEventListener('hidden.bs.toast', function() {
        toast.remove();
    });
}

/**
 * Create toast container if it doesn't exist
 */
function createToastContainer() {
    const container = document.createElement('div');
    container.id = 'toast-container';
    container.className = 'toast-container position-fixed top-0 end-0 p-3';
    document.body.appendChild(container);
    return container;
}

/**
 * Export functionality
 */
function exportTable(format = 'csv') {
    const table = document.querySelector('table');
    if (!table) return;
    
    const rows = table.querySelectorAll('tr');
    const csvContent = Array.from(rows).map(row => {
        const cells = row.querySelectorAll('th, td');
        return Array.from(cells).map(cell => {
            // Clean up cell content
            let text = cell.textContent.trim();
            // Remove action buttons text
            if (cell.querySelector('.btn')) {
                text = '';
            }
            return `"${text.replace(/"/g, '""')}"`;
        }).join(',');
    }).join('\n');
    
    // Create download link
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', `export_${new Date().toISOString().split('T')[0]}.csv`);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

// Global functions for inline event handlers
window.factoryApp = {
    exportTable,
    showToast,
    formatCurrency,
    formatDate
};
