"""
Utility functions for generating documents (PDF, Excel, etc.)
"""
import os
import tempfile
from datetime import datetime
from io import BytesIO
import pandas as pd

# Import PDF generation libraries
try:
    from weasyprint import HTML, CSS
    WEASYPRINT_AVAILABLE = True
except ImportError:
    WEASYPRINT_AVAILABLE = False

def generate_pdf_document(form_type, entity):
    """Generate PDF document for the given entity"""
    
    if not WEASYPRINT_AVAILABLE:
        return None
    
    try:
        # Generate HTML content based on form type
        html_content = generate_html_content(form_type, entity)
        
        # Create temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
        temp_file.close()
        
        # Generate PDF
        HTML(string=html_content).write_pdf(temp_file.name)
        
        return temp_file.name
        
    except Exception as e:
        print(f"Error generating PDF: {e}")
        return None

def generate_excel_document(form_type, entity):
    """Generate Excel document for the given entity"""
    
    try:
        # Create temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx')
        temp_file.close()
        
        # Generate Excel content based on form type
        if form_type == 'purchase_order':
            generate_purchase_order_excel(entity, temp_file.name)
        elif form_type == 'sales_order':
            generate_sales_order_excel(entity, temp_file.name)
        elif form_type == 'job_work':
            generate_job_work_excel(entity, temp_file.name)
        elif form_type == 'production':
            generate_production_excel(entity, temp_file.name)
        elif form_type == 'expense':
            generate_expense_excel(entity, temp_file.name)
        
        return temp_file.name
        
    except Exception as e:
        print(f"Error generating Excel: {e}")
        return None

def generate_challan_pdf(form_type, entity):
    """Generate delivery challan PDF"""
    
    if not WEASYPRINT_AVAILABLE:
        return None
    
    try:
        html_content = generate_challan_html(form_type, entity)
        
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
        temp_file.close()
        
        HTML(string=html_content).write_pdf(temp_file.name)
        
        return temp_file.name
        
    except Exception as e:
        print(f"Error generating challan PDF: {e}")
        return None

def generate_invoice_pdf(form_type, entity):
    """Generate invoice PDF"""
    
    if not WEASYPRINT_AVAILABLE:
        return None
    
    try:
        html_content = generate_invoice_html(form_type, entity)
        
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
        temp_file.close()
        
        HTML(string=html_content).write_pdf(temp_file.name)
        
        return temp_file.name
        
    except Exception as e:
        print(f"Error generating invoice PDF: {e}")
        return None

def generate_html_content(form_type, entity):
    """Generate HTML content for PDF generation"""
    
    css_styles = """
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        .header { text-align: center; margin-bottom: 30px; }
        .company-name { font-size: 24px; font-weight: bold; color: #2c3e50; }
        .document-title { font-size: 18px; margin: 20px 0; }
        .info-section { margin: 20px 0; }
        .info-table { width: 100%; border-collapse: collapse; }
        .info-table td { padding: 8px; border-bottom: 1px solid #ddd; }
        .label { font-weight: bold; width: 30%; }
        .items-table { width: 100%; border-collapse: collapse; margin: 20px 0; }
        .items-table th, .items-table td { border: 1px solid #ddd; padding: 10px; text-align: left; }
        .items-table th { background-color: #f8f9fa; font-weight: bold; }
        .total-section { margin-top: 20px; text-align: right; }
        .total-amount { font-size: 18px; font-weight: bold; color: #27ae60; }
        .footer { margin-top: 40px; text-align: center; font-size: 12px; color: #7f8c8d; }
    </style>
    """
    
    # Company header
    header = """
    <div class="header">
        <div class="company-name">AK Innovations</div>
        <div>Factory Management System</div>
        <div>Phone: +91-XXXXXXXXXX | Email: contact@akinnovations.com</div>
    </div>
    """
    
    content = ""
    
    if form_type == 'purchase_order':
        content = generate_purchase_order_html(entity)
    elif form_type == 'sales_order':
        content = generate_sales_order_html(entity)
    elif form_type == 'job_work':
        content = generate_job_work_html(entity)
    elif form_type == 'production':
        content = generate_production_html(entity)
    elif form_type == 'expense':
        content = generate_expense_html(entity)
    
    footer = f"""
    <div class="footer">
        Generated on: {datetime.now().strftime('%d/%m/%Y %I:%M %p')}<br>
        This is a computer-generated document.
    </div>
    """
    
    return f"<html><head>{css_styles}</head><body>{header}{content}{footer}</body></html>"

def generate_purchase_order_html(entity):
    """Generate Purchase Order HTML content"""
    
    items_html = ""
    if hasattr(entity, 'items') and entity.items:
        items_html = """
        <table class="items-table">
            <thead>
                <tr>
                    <th>Item</th>
                    <th>Quantity</th>
                    <th>Unit Price</th>
                    <th>Total</th>
                </tr>
            </thead>
            <tbody>
        """
        for item in entity.items:
            items_html += f"""
                <tr>
                    <td>{item.item.name if item.item else 'N/A'}</td>
                    <td>{item.quantity or 0}</td>
                    <td>₹{item.unit_price or 0:.2f}</td>
                    <td>₹{(item.quantity or 0) * (item.unit_price or 0):.2f}</td>
                </tr>
            """
        items_html += """
            </tbody>
        </table>
        """
    
    return f"""
    <div class="document-title">PURCHASE ORDER</div>
    
    <div class="info-section">
        <table class="info-table">
            <tr><td class="label">PO Number:</td><td>{entity.po_number or 'N/A'}</td></tr>
            <tr><td class="label">Order Date:</td><td>{entity.order_date.strftime('%d/%m/%Y') if entity.order_date else 'N/A'}</td></tr>
            <tr><td class="label">Supplier:</td><td>{entity.supplier.name if entity.supplier else 'N/A'}</td></tr>
            <tr><td class="label">Expected Delivery:</td><td>{entity.expected_delivery_date.strftime('%d/%m/%Y') if entity.expected_delivery_date else 'N/A'}</td></tr>
            <tr><td class="label">Status:</td><td>{entity.status.title() if entity.status else 'N/A'}</td></tr>
        </table>
    </div>
    
    {items_html}
    
    <div class="total-section">
        <div class="total-amount">Total Amount: ₹{entity.total_amount or 0:.2f}</div>
    </div>
    """

def generate_sales_order_html(entity):
    """Generate Sales Order HTML content"""
    
    items_html = ""
    if hasattr(entity, 'items') and entity.items:
        items_html = """
        <table class="items-table">
            <thead>
                <tr>
                    <th>Item</th>
                    <th>Quantity</th>
                    <th>Unit Price</th>
                    <th>Total</th>
                </tr>
            </thead>
            <tbody>
        """
        for item in entity.items:
            items_html += f"""
                <tr>
                    <td>{item.item.name if item.item else 'N/A'}</td>
                    <td>{item.quantity or 0}</td>
                    <td>₹{item.unit_price or 0:.2f}</td>
                    <td>₹{(item.quantity or 0) * (item.unit_price or 0):.2f}</td>
                </tr>
            """
        items_html += """
            </tbody>
        </table>
        """
    
    return f"""
    <div class="document-title">SALES ORDER</div>
    
    <div class="info-section">
        <table class="info-table">
            <tr><td class="label">SO Number:</td><td>{entity.so_number or 'N/A'}</td></tr>
            <tr><td class="label">Order Date:</td><td>{entity.order_date.strftime('%d/%m/%Y') if entity.order_date else 'N/A'}</td></tr>
            <tr><td class="label">Customer:</td><td>{entity.customer.name if entity.customer else 'N/A'}</td></tr>
            <tr><td class="label">Delivery Date:</td><td>{entity.delivery_date.strftime('%d/%m/%Y') if entity.delivery_date else 'N/A'}</td></tr>
            <tr><td class="label">Status:</td><td>{entity.status.title() if entity.status else 'N/A'}</td></tr>
        </table>
    </div>
    
    {items_html}
    
    <div class="total-section">
        <div class="total-amount">Total Amount: ₹{entity.total_amount or 0:.2f}</div>
    </div>
    """

def generate_job_work_html(entity):
    """Generate Job Work HTML content"""
    
    return f"""
    <div class="document-title">JOB WORK ORDER</div>
    
    <div class="info-section">
        <table class="info-table">
            <tr><td class="label">Job Work Number:</td><td>{entity.jobwork_number or 'N/A'}</td></tr>
            <tr><td class="label">Type:</td><td>{entity.job_type.title() if entity.job_type else 'N/A'}</td></tr>
            <tr><td class="label">Item:</td><td>{entity.item.name if entity.item else 'N/A'}</td></tr>
            <tr><td class="label">Quantity:</td><td>{entity.quantity or 0}</td></tr>
            <tr><td class="label">Vendor:</td><td>{entity.vendor.name if entity.vendor else 'Internal'}</td></tr>
            <tr><td class="label">Due Date:</td><td>{entity.due_date.strftime('%d/%m/%Y') if entity.due_date else 'N/A'}</td></tr>
            <tr><td class="label">Status:</td><td>{entity.status.title() if entity.status else 'N/A'}</td></tr>
        </table>
    </div>
    
    <div class="info-section">
        <h4>Description:</h4>
        <p>{entity.description or 'No description provided'}</p>
    </div>
    """

def generate_production_html(entity):
    """Generate Production Order HTML content"""
    
    return f"""
    <div class="document-title">PRODUCTION ORDER</div>
    
    <div class="info-section">
        <table class="info-table">
            <tr><td class="label">Production Number:</td><td>{entity.production_number or 'N/A'}</td></tr>
            <tr><td class="label">Item:</td><td>{entity.item.name if entity.item else 'N/A'}</td></tr>
            <tr><td class="label">Quantity to Produce:</td><td>{getattr(entity, 'quantity_to_produce', 0) or getattr(entity, 'quantity', 0)}</td></tr>
            <tr><td class="label">Production Date:</td><td>{entity.production_date.strftime('%d/%m/%Y') if entity.production_date else 'N/A'}</td></tr>
            <tr><td class="label">Department:</td><td>{entity.department.name if hasattr(entity, 'department') and entity.department else 'N/A'}</td></tr>
            <tr><td class="label">Status:</td><td>{entity.status.title() if entity.status else 'N/A'}</td></tr>
        </table>
    </div>
    
    <div class="info-section">
        <h4>Notes:</h4>
        <p>{getattr(entity, 'notes', 'No notes provided') or 'No notes provided'}</p>
    </div>
    """

def generate_expense_html(entity):
    """Generate Factory Expense HTML content"""
    
    return f"""
    <div class="document-title">FACTORY EXPENSE VOUCHER</div>
    
    <div class="info-section">
        <table class="info-table">
            <tr><td class="label">Expense Number:</td><td>{entity.expense_number or 'N/A'}</td></tr>
            <tr><td class="label">Category:</td><td>{entity.expense_category.replace('_', ' ').title() if entity.expense_category else 'N/A'}</td></tr>
            <tr><td class="label">Amount:</td><td>₹{entity.amount or 0:.2f}</td></tr>
            <tr><td class="label">Date:</td><td>{entity.expense_date.strftime('%d/%m/%Y') if entity.expense_date else 'N/A'}</td></tr>
            <tr><td class="label">Vendor:</td><td>{entity.vendor.name if entity.vendor else 'N/A'}</td></tr>
            <tr><td class="label">Payment Method:</td><td>{entity.payment_method.title() if entity.payment_method else 'N/A'}</td></tr>
            <tr><td class="label">Status:</td><td>{entity.status.title() if entity.status else 'N/A'}</td></tr>
        </table>
    </div>
    
    <div class="info-section">
        <h4>Description:</h4>
        <p>{entity.description or 'No description provided'}</p>
    </div>
    
    <div class="info-section">
        <h4>Notes:</h4>
        <p>{entity.notes or 'No notes provided'}</p>
    </div>
    """

def generate_challan_html(form_type, entity):
    """Generate Delivery Challan HTML content"""
    
    return f"""
    <div class="document-title">DELIVERY CHALLAN</div>
    
    <div class="info-section">
        <table class="info-table">
            <tr><td class="label">Challan Number:</td><td>CH-{entity.id}-{datetime.now().strftime('%Y%m%d')}</td></tr>
            <tr><td class="label">Date:</td><td>{datetime.now().strftime('%d/%m/%Y')}</td></tr>
            <tr><td class="label">Reference:</td><td>{getattr(entity, f'{form_type.split("_")[0]}_number', f'{form_type}_{entity.id}')}</td></tr>
        </table>
    </div>
    
    <div class="info-section">
        <p><strong>Note:</strong> This is a delivery challan for the above referenced document.</p>
        <p>Please acknowledge receipt by signing and returning a copy.</p>
    </div>
    """

def generate_invoice_html(form_type, entity):
    """Generate Invoice HTML content"""
    
    return f"""
    <div class="document-title">INVOICE</div>
    
    <div class="info-section">
        <table class="info-table">
            <tr><td class="label">Invoice Number:</td><td>INV-{entity.id}-{datetime.now().strftime('%Y%m%d')}</td></tr>
            <tr><td class="label">Date:</td><td>{datetime.now().strftime('%d/%m/%Y')}</td></tr>
            <tr><td class="label">Reference:</td><td>{getattr(entity, f'{form_type.split("_")[0]}_number', f'{form_type}_{entity.id}')}</td></tr>
        </table>
    </div>
    
    <div class="total-section">
        <div class="total-amount">Invoice Amount: ₹{getattr(entity, 'total_amount', 0) or getattr(entity, 'amount', 0) or 0:.2f}</div>
    </div>
    """

# Excel generation functions
def generate_purchase_order_excel(entity, filename):
    """Generate Purchase Order Excel"""
    
    with pd.ExcelWriter(filename, engine='openpyxl') as writer:
        # Basic info
        info_data = {
            'Field': ['PO Number', 'Order Date', 'Supplier', 'Expected Delivery', 'Status', 'Total Amount'],
            'Value': [
                entity.po_number or 'N/A',
                entity.order_date.strftime('%d/%m/%Y') if entity.order_date else 'N/A',
                entity.supplier.name if entity.supplier else 'N/A',
                entity.expected_delivery_date.strftime('%d/%m/%Y') if entity.expected_delivery_date else 'N/A',
                entity.status.title() if entity.status else 'N/A',
                f"₹{entity.total_amount or 0:.2f}"
            ]
        }
        
        df_info = pd.DataFrame(info_data)
        df_info.to_excel(writer, sheet_name='Purchase Order', index=False)

def generate_sales_order_excel(entity, filename):
    """Generate Sales Order Excel"""
    
    with pd.ExcelWriter(filename, engine='openpyxl') as writer:
        info_data = {
            'Field': ['SO Number', 'Order Date', 'Customer', 'Delivery Date', 'Status', 'Total Amount'],
            'Value': [
                entity.so_number or 'N/A',
                entity.order_date.strftime('%d/%m/%Y') if entity.order_date else 'N/A',
                entity.customer.name if entity.customer else 'N/A',
                entity.delivery_date.strftime('%d/%m/%Y') if entity.delivery_date else 'N/A',
                entity.status.title() if entity.status else 'N/A',
                f"₹{entity.total_amount or 0:.2f}"
            ]
        }
        
        df_info = pd.DataFrame(info_data)
        df_info.to_excel(writer, sheet_name='Sales Order', index=False)

def generate_job_work_excel(entity, filename):
    """Generate Job Work Excel"""
    
    with pd.ExcelWriter(filename, engine='openpyxl') as writer:
        info_data = {
            'Field': ['Job Work Number', 'Type', 'Item', 'Quantity', 'Vendor', 'Due Date', 'Status'],
            'Value': [
                entity.jobwork_number or 'N/A',
                entity.job_type.title() if entity.job_type else 'N/A',
                entity.item.name if entity.item else 'N/A',
                entity.quantity or 0,
                entity.vendor.name if entity.vendor else 'Internal',
                entity.due_date.strftime('%d/%m/%Y') if entity.due_date else 'N/A',
                entity.status.title() if entity.status else 'N/A'
            ]
        }
        
        df_info = pd.DataFrame(info_data)
        df_info.to_excel(writer, sheet_name='Job Work', index=False)

def generate_production_excel(entity, filename):
    """Generate Production Excel"""
    
    with pd.ExcelWriter(filename, engine='openpyxl') as writer:
        info_data = {
            'Field': ['Production Number', 'Item', 'Quantity', 'Production Date', 'Status'],
            'Value': [
                entity.production_number or 'N/A',
                entity.item.name if entity.item else 'N/A',
                getattr(entity, 'quantity_to_produce', 0) or getattr(entity, 'quantity', 0),
                entity.production_date.strftime('%d/%m/%Y') if entity.production_date else 'N/A',
                entity.status.title() if entity.status else 'N/A'
            ]
        }
        
        df_info = pd.DataFrame(info_data)
        df_info.to_excel(writer, sheet_name='Production', index=False)

def generate_expense_excel(entity, filename):
    """Generate Expense Excel"""
    
    with pd.ExcelWriter(filename, engine='openpyxl') as writer:
        info_data = {
            'Field': ['Expense Number', 'Category', 'Amount', 'Date', 'Vendor', 'Payment Method', 'Status'],
            'Value': [
                entity.expense_number or 'N/A',
                entity.expense_category.replace('_', ' ').title() if entity.expense_category else 'N/A',
                f"₹{entity.amount or 0:.2f}",
                entity.expense_date.strftime('%d/%m/%Y') if entity.expense_date else 'N/A',
                entity.vendor.name if entity.vendor else 'N/A',
                entity.payment_method.title() if entity.payment_method else 'N/A',
                entity.status.title() if entity.status else 'N/A'
            ]
        }
        
        df_info = pd.DataFrame(info_data)
        df_info.to_excel(writer, sheet_name='Expense', index=False)

# Legacy functions for backward compatibility
def export_inventory_items():
    """Legacy function for inventory export"""
    return "Inventory export functionality moved to new forms system"

def export_factory_expenses():
    """Legacy function for expense export"""
    return "Expense export functionality moved to new forms system"

def export_purchase_orders():
    """Legacy function for purchase order export"""
    return "Purchase order export functionality moved to new forms system"

def export_sales_orders():
    """Legacy function for sales order export"""
    return "Sales order export functionality moved to new forms system"

def export_job_works():
    """Legacy function for job work export"""
    return "Job work export functionality moved to new forms system"

def export_production_orders():
    """Legacy function for production export"""
    return "Production export functionality moved to new forms system"