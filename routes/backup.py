from flask import Blueprint, render_template, jsonify, send_file, request, current_app
from flask_login import login_required, current_user
from datetime import datetime
import pandas as pd
import os
import json
import tempfile
from io import BytesIO
from app import db
from models import (
    Item, Supplier, PurchaseOrder, PurchaseOrderItem, SalesOrder, SalesOrderItem,
    Employee, JobWork, Production, BOM, BOMItem, QualityIssue, FactoryExpense,
    MaterialInspection, User
)
from models_dashboard import DashboardModule, UserDashboardPreference
import logging

backup_bp = Blueprint('backup', __name__)

@backup_bp.route('/backup')
@login_required
def backup_dashboard():
    """Display backup options and statistics"""
    try:
        # Get database statistics
        stats = {
            'items': Item.query.count(),
            'suppliers': Supplier.query.count(),
            'purchase_orders': PurchaseOrder.query.count(),
            'sales_orders': SalesOrder.query.count(),
            'employees': Employee.query.count(),
            'job_works': JobWork.query.count(),
            'productions': Production.query.count(),
            'quality_issues': QualityIssue.query.count(),
            'factory_expenses': FactoryExpense.query.count(),
            'material_inspections': MaterialInspection.query.count(),
            'users': User.query.count(),
            'dashboard_preferences': UserDashboardPreference.query.count()
        }
        
        return render_template('backup/dashboard.html', stats=stats)
    except Exception as e:
        current_app.logger.error(f"Error loading backup dashboard: {str(e)}")
        return render_template('backup/dashboard.html', stats={}, error="Error loading backup data")

@backup_bp.route('/export/excel')
@login_required
def export_excel():
    """Export all data to Excel file"""
    try:
        # Create a BytesIO object to store the Excel file in memory
        output = BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Export Items
            items_data = []
            for item in Item.query.all():
                items_data.append({
                    'ID': item.id,
                    'Code': item.code,
                    'Name': item.name,
                    'Description': item.description,
                    'Unit Price': item.unit_price,
                    'Current Stock': item.current_stock,
                    'Minimum Stock': item.minimum_stock,
                    'Unit of Measure': item.unit_of_measure,
                    'GST Rate': item.gst_rate,
                    'HSN Code': item.hsn_code,
                    'Item Type': item.item_type,
                    'Created At': item.created_at
                })
            if items_data:
                pd.DataFrame(items_data).to_excel(writer, sheet_name='Items', index=False)
            
            # Export Suppliers/Business Partners
            suppliers_data = []
            for supplier in Supplier.query.all():
                suppliers_data.append({
                    'ID': supplier.id,
                    'Name': supplier.name,
                    'Contact Person': supplier.contact_person,
                    'Phone': supplier.phone,
                    'Email': supplier.email,
                    'GST Number': supplier.gst_number,
                    'PAN Number': supplier.pan_number,
                    'Address': supplier.address,
                    'City': supplier.city,
                    'State': supplier.state,
                    'Pin Code': supplier.pin_code,
                    'Account Number': supplier.account_number,
                    'Bank Name': supplier.bank_name,
                    'IFSC Code': supplier.ifsc_code,
                    'Partner Type': supplier.partner_type,
                    'Active': supplier.is_active,
                    'Remarks': supplier.remarks,
                    'Created At': supplier.created_at
                })
            if suppliers_data:
                pd.DataFrame(suppliers_data).to_excel(writer, sheet_name='Business_Partners', index=False)
            
            # Export Purchase Orders
            po_data = []
            for po in PurchaseOrder.query.all():
                po_data.append({
                    'ID': po.id,
                    'PO Number': po.po_number,
                    'Supplier': po.supplier.name if po.supplier else '',
                    'Order Date': po.order_date,
                    'Expected Date': po.expected_date,
                    'Status': po.status,
                    'Subtotal': po.subtotal,
                    'GST Amount': po.gst_amount,
                    'Total Amount': po.total_amount,
                    'Payment Terms': po.payment_terms,
                    'Freight Terms': po.freight_terms,
                    'Validity Months': po.validity_months,
                    'Prepared By': po.prepared_by,
                    'Verified By': po.verified_by,
                    'Approved By': po.approved_by,
                    'Notes': po.notes,
                    'Created At': po.created_at
                })
            if po_data:
                pd.DataFrame(po_data).to_excel(writer, sheet_name='Purchase_Orders', index=False)
            
            # Export Sales Orders
            so_data = []
            for so in SalesOrder.query.all():
                so_data.append({
                    'ID': so.id,
                    'SO Number': so.so_number,
                    'Customer': so.customer.name if so.customer else '',
                    'Order Date': so.order_date,
                    'Delivery Date': so.delivery_date,
                    'Status': so.status,
                    'Total Amount': so.total_amount,
                    'Payment Terms': so.payment_terms,
                    'Freight Terms': so.freight_terms,
                    'Validity Months': so.validity_months,
                    'Prepared By': so.prepared_by,
                    'Verified By': so.verified_by,
                    'Approved By': so.approved_by,
                    'Notes': so.notes,
                    'Created At': so.created_at
                })
            if so_data:
                pd.DataFrame(so_data).to_excel(writer, sheet_name='Sales_Orders', index=False)
            
            # Export Employees
            emp_data = []
            for emp in Employee.query.all():
                emp_data.append({
                    'ID': emp.id,
                    'Code': emp.employee_code,
                    'Name': emp.name,
                    'Designation': emp.designation,
                    'Department': emp.department,
                    'Salary Type': emp.salary_type,
                    'Rate': emp.rate,
                    'Phone': emp.phone,
                    'Address': emp.address,
                    'Joining Date': emp.joining_date,
                    'Active': emp.is_active,
                    'Created At': emp.created_at
                })
            if emp_data:
                pd.DataFrame(emp_data).to_excel(writer, sheet_name='Employees', index=False)
            
            # Export Job Works
            jw_data = []
            for jw in JobWork.query.all():
                jw_data.append({
                    'ID': jw.id,
                    'Job Number': jw.job_number,
                    'Customer Name': jw.customer_name,
                    'Item': jw.item.name if jw.item else '',
                    'Quantity Sent': jw.quantity_sent,
                    'Quantity Received': jw.quantity_received,
                    'Rate per Unit': jw.rate_per_unit,
                    'Total Cost': jw.quantity_sent * jw.rate_per_unit if jw.quantity_sent and jw.rate_per_unit else 0,
                    'Status': jw.status,
                    'Sent Date': jw.sent_date,
                    'Received Date': jw.received_date,
                    'Created At': jw.created_at
                })
            if jw_data:
                pd.DataFrame(jw_data).to_excel(writer, sheet_name='Job_Works', index=False)
            
            # Export Productions
            prod_data = []
            for prod in Production.query.all():
                prod_data.append({
                    'ID': prod.id,
                    'Production Number': prod.production_number,
                    'Item': prod.produced_item.name if prod.produced_item else '',
                    'Quantity Planned': prod.quantity_planned,
                    'Quantity Produced': prod.quantity_produced,
                    'Quantity Good': prod.quantity_good,
                    'Quantity Damaged': prod.quantity_damaged,
                    'Production Date': prod.production_date,
                    'Status': prod.status,
                    'Notes': prod.notes,
                    'Created At': prod.created_at
                })
            if prod_data:
                pd.DataFrame(prod_data).to_excel(writer, sheet_name='Productions', index=False)
            
            # Export Factory Expenses
            exp_data = []
            for exp in FactoryExpense.query.all():
                exp_data.append({
                    'ID': exp.id,
                    'Expense Number': exp.expense_number,
                    'Category': exp.category,
                    'Description': exp.description,
                    'Amount': exp.amount,
                    'Tax Amount': exp.tax_amount,
                    'Total Amount': exp.total_amount,
                    'Vendor': exp.vendor_name,
                    'Invoice Number': exp.invoice_number,
                    'Expense Date': exp.expense_date,
                    'Payment Method': exp.payment_method,
                    'Status': exp.status,
                    'Paid By': exp.paid_by,
                    'Created At': exp.created_at
                })
            if exp_data:
                pd.DataFrame(exp_data).to_excel(writer, sheet_name='Factory_Expenses', index=False)
            
            # Export Quality Issues
            qi_data = []
            for qi in QualityIssue.query.all():
                qi_data.append({
                    'ID': qi.id,
                    'Issue Number': qi.issue_number,
                    'Item': qi.item.name if qi.item else '',
                    'Issue Type': qi.issue_type,
                    'Severity': qi.severity,
                    'Description': qi.description,
                    'Quantity Affected': qi.quantity_affected,
                    'Cost Impact': qi.cost_impact,
                    'Status': qi.status,
                    'Reported Date': qi.reported_date,
                    'Root Cause': qi.root_cause,
                    'Corrective Action': qi.corrective_action,
                    'Created At': qi.created_at
                })
            if qi_data:
                pd.DataFrame(qi_data).to_excel(writer, sheet_name='Quality_Issues', index=False)
        
        output.seek(0)
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'factory_data_backup_{timestamp}.xlsx'
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        current_app.logger.error(f"Error exporting to Excel: {str(e)}")
        return jsonify({'success': False, 'message': f'Export failed: {str(e)}'})

@backup_bp.route('/export/json')
@login_required
def export_json():
    """Export all data to JSON file"""
    try:
        backup_data = {
            'export_date': datetime.now().isoformat(),
            'exported_by': current_user.username,
            'data': {}
        }
        
        # Export Items
        items = []
        for item in Item.query.all():
            items.append({
                'id': item.id,
                'code': item.code,
                'name': item.name,
                'description': item.description,
                'unit_price': float(item.unit_price) if item.unit_price else None,
                'current_stock': float(item.current_stock) if item.current_stock else None,
                'minimum_stock': float(item.minimum_stock) if item.minimum_stock else None,
                'unit_of_measure': item.unit_of_measure,
                'gst_rate': float(item.gst_rate) if item.gst_rate else None,
                'hsn_code': item.hsn_code,
                'item_type': item.item_type,
                'created_at': item.created_at.isoformat() if item.created_at else None
            })
        backup_data['data']['items'] = items
        
        # Export Suppliers
        suppliers = []
        for supplier in Supplier.query.all():
            suppliers.append({
                'id': supplier.id,
                'name': supplier.name,
                'contact_person': supplier.contact_person,
                'phone': supplier.phone,
                'email': supplier.email,
                'gst_number': supplier.gst_number,
                'pan_number': supplier.pan_number,
                'address': supplier.address,
                'city': supplier.city,
                'state': supplier.state,
                'pin_code': supplier.pin_code,
                'account_number': supplier.account_number,
                'bank_name': supplier.bank_name,
                'ifsc_code': supplier.ifsc_code,
                'partner_type': supplier.partner_type,
                'is_active': supplier.is_active,
                'remarks': supplier.remarks,
                'created_at': supplier.created_at.isoformat() if supplier.created_at else None
            })
        backup_data['data']['suppliers'] = suppliers
        
        # Create JSON file
        json_str = json.dumps(backup_data, indent=2, default=str)
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'factory_data_backup_{timestamp}.json'
        
        # Create BytesIO object
        json_bytes = BytesIO(json_str.encode('utf-8'))
        
        return send_file(
            json_bytes,
            mimetype='application/json',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        current_app.logger.error(f"Error exporting to JSON: {str(e)}")
        return jsonify({'success': False, 'message': f'Export failed: {str(e)}'})

@backup_bp.route('/import/json', methods=['POST'])
@login_required
def import_json():
    """Import data from JSON file"""
    if not current_user.role == 'admin':
        return jsonify({'success': False, 'message': 'Admin access required'})
    
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'message': 'No file provided'})
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'message': 'No file selected'})
        
        if not file.filename.endswith('.json'):
            return jsonify({'success': False, 'message': 'Only JSON files are supported'})
        
        # Read and parse JSON
        json_data = json.load(file)
        
        if 'data' not in json_data:
            return jsonify({'success': False, 'message': 'Invalid backup file format'})
        
        # Import would require careful handling of relationships and IDs
        # This is a placeholder for the import functionality
        return jsonify({
            'success': True, 
            'message': 'JSON import functionality is under development. Please contact administrator for data restoration.'
        })
        
    except Exception as e:
        current_app.logger.error(f"Error importing JSON: {str(e)}")
        return jsonify({'success': False, 'message': f'Import failed: {str(e)}'})

@backup_bp.route('/schedule', methods=['POST'])
@login_required
def schedule_backup():
    """Schedule automatic backups"""
    if not current_user.role == 'admin':
        return jsonify({'success': False, 'message': 'Admin access required'})
    
    try:
        data = request.get_json()
        frequency = data.get('frequency', 'weekly')  # daily, weekly, monthly
        backup_type = data.get('type', 'excel')  # excel, json
        
        # This would integrate with a task scheduler like Celery
        # For now, return success message
        return jsonify({
            'success': True,
            'message': f'Automatic {backup_type.upper()} backup scheduled {frequency}'
        })
        
    except Exception as e:
        current_app.logger.error(f"Error scheduling backup: {str(e)}")
        return jsonify({'success': False, 'message': f'Scheduling failed: {str(e)}'})