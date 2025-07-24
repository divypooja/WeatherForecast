from flask import Blueprint, flash, redirect, url_for
from flask_login import login_required
from datetime import datetime
from services.excel_export import ExcelExportService

exports_bp = Blueprint('exports', __name__)

@exports_bp.route('/inventory/excel')
@login_required
def export_inventory_excel():
    """Export Inventory to Excel"""
    try:
        wb = ExcelExportService.export_inventory()
        filename = f"inventory_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        return ExcelExportService.create_response(wb, filename)
    except Exception as e:
        flash(f'Error exporting Inventory: {str(e)}', 'danger')
        return redirect(url_for('inventory.list_items'))

@exports_bp.route('/suppliers/excel')
@login_required
def export_suppliers_excel():
    """Export Suppliers to Excel"""
    try:
        wb = ExcelExportService.export_suppliers()
        filename = f"suppliers_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        return ExcelExportService.create_response(wb, filename)
    except Exception as e:
        flash(f'Error exporting Suppliers: {str(e)}', 'danger')
        return redirect(url_for('purchase.list_suppliers'))

@exports_bp.route('/factory-expenses/excel')
@login_required
def export_factory_expenses_excel():
    """Export Factory Expenses to Excel"""
    try:
        wb = ExcelExportService.export_factory_expenses()
        filename = f"factory_expenses_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        return ExcelExportService.create_response(wb, filename)
    except Exception as e:
        flash(f'Error exporting Factory Expenses: {str(e)}', 'danger')
        return redirect(url_for('factory_expenses.list_expenses'))