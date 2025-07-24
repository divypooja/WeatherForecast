from flask import Blueprint, render_template, request, redirect, url_for, flash, make_response, jsonify
from flask_login import login_required, current_user
from models import Item, PurchaseOrder, SalesOrder, FactoryExpense, Supplier, Employee
from app import db
from datetime import datetime, date
from sqlalchemy import func, desc
import xml.etree.ElementTree as ET
from xml.dom import minidom
import io

tally_bp = Blueprint('tally', __name__)

@tally_bp.route('/dashboard')
@login_required
def dashboard():
    """Tally Integration Dashboard"""
    # Get statistics for Tally sync
    stats = {
        'total_ledgers': Supplier.query.count(),
        'total_items': Item.query.count(),
        'pending_vouchers': (PurchaseOrder.query.filter_by(tally_synced=False).count() + 
                           SalesOrder.query.filter_by(tally_synced=False).count() +
                           FactoryExpense.query.filter_by(tally_synced=False).count()),
        'synced_vouchers': (PurchaseOrder.query.filter_by(tally_synced=True).count() + 
                          SalesOrder.query.filter_by(tally_synced=True).count() +
                          FactoryExpense.query.filter_by(tally_synced=True).count())
    }
    
    # Recent sync activities
    recent_purchases = PurchaseOrder.query.order_by(desc(PurchaseOrder.created_at)).limit(5).all()
    recent_sales = SalesOrder.query.order_by(desc(SalesOrder.created_at)).limit(5).all()
    recent_expenses = FactoryExpense.query.order_by(desc(FactoryExpense.created_at)).limit(5).all()
    
    return render_template('tally/dashboard.html', 
                         stats=stats,
                         recent_purchases=recent_purchases,
                         recent_sales=recent_sales,
                         recent_expenses=recent_expenses)

@tally_bp.route('/export/ledgers')
@login_required
def export_ledgers():
    """Export Chart of Accounts (Ledgers) to Tally XML"""
    suppliers = Supplier.query.filter_by(is_active=True).all()
    
    # Create XML structure for Tally
    envelope = ET.Element('ENVELOPE')
    header = ET.SubElement(envelope, 'HEADER')
    ET.SubElement(header, 'TALLYREQUEST').text = 'Import Data'
    
    body = ET.SubElement(envelope, 'BODY')
    import_data = ET.SubElement(body, 'IMPORTDATA')
    request_desc = ET.SubElement(import_data, 'REQUESTDESC')
    ET.SubElement(request_desc, 'REPORTNAME').text = 'All Masters'
    
    request_data = ET.SubElement(import_data, 'REQUESTDATA')
    
    # Add Ledger Masters
    for supplier in suppliers:
        ledger = ET.SubElement(request_data, 'TALLYMESSAGE')
        ledger_master = ET.SubElement(ledger, 'LEDGER', NAME=supplier.name, ACTION="Create")
        
        ET.SubElement(ledger_master, 'NAME').text = supplier.name
        ET.SubElement(ledger_master, 'PARENT').text = 'Sundry Creditors' if supplier.partner_type in ['supplier', 'both'] else 'Sundry Debtors'
        ET.SubElement(ledger_master, 'ISBILLWISEON').text = 'Yes'
        ET.SubElement(ledger_master, 'ISCOSTCENTRESON').text = 'No'
        
        # Address details
        if supplier.address:
            address_list = ET.SubElement(ledger_master, 'ADDRESS.LIST')
            ET.SubElement(address_list, 'ADDRESS').text = supplier.address
            if supplier.city:
                ET.SubElement(address_list, 'ADDRESS').text = supplier.city
            if supplier.state:
                ET.SubElement(address_list, 'ADDRESS').text = supplier.state
        
        # GST details
        if supplier.gst_number:
            gst_details = ET.SubElement(ledger_master, 'GSTREGISTRATIONTYPE').text = 'Regular'
            ET.SubElement(ledger_master, 'GSTIN').text = supplier.gst_number
            ET.SubElement(ledger_master, 'GSTREGISTRATIONTYPE').text = 'Regular'
        
        # Contact details
        if supplier.mobile_number:
            ET.SubElement(ledger_master, 'LEDGERPHONE').text = supplier.mobile_number
        if supplier.email:
            ET.SubElement(ledger_master, 'EMAIL').text = supplier.email
    
    # Convert to pretty XML string
    rough_string = ET.tostring(envelope, 'unicode')
    reparsed = minidom.parseString(rough_string)
    pretty_xml = reparsed.toprettyxml(indent="  ")
    
    # Create response
    response = make_response(pretty_xml)
    response.headers['Content-Type'] = 'application/xml'
    response.headers['Content-Disposition'] = f'attachment; filename=ledgers_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xml'
    
    return response

@tally_bp.route('/export/items')
@login_required
def export_items():
    """Export Stock Items to Tally XML"""
    items = Item.query.filter_by(is_active=True).all()
    
    # Create XML structure
    envelope = ET.Element('ENVELOPE')
    header = ET.SubElement(envelope, 'HEADER')
    ET.SubElement(header, 'TALLYREQUEST').text = 'Import Data'
    
    body = ET.SubElement(envelope, 'BODY')
    import_data = ET.SubElement(body, 'IMPORTDATA')
    request_desc = ET.SubElement(import_data, 'REQUESTDESC')
    ET.SubElement(request_desc, 'REPORTNAME').text = 'All Masters'
    
    request_data = ET.SubElement(import_data, 'REQUESTDATA')
    
    # Add Stock Item Masters
    for item in items:
        stock_item = ET.SubElement(request_data, 'TALLYMESSAGE')
        item_master = ET.SubElement(stock_item, 'STOCKITEM', NAME=item.name, ACTION="Create")
        
        ET.SubElement(item_master, 'NAME').text = item.name
        ET.SubElement(item_master, 'ALIAS').text = item.code
        ET.SubElement(item_master, 'PARENT').text = item.item_type.title() if item.item_type else 'Primary'
        ET.SubElement(item_master, 'CATEGORY').text = item.item_type.title() if item.item_type else 'Primary'
        ET.SubElement(item_master, 'BASEUNITS').text = item.unit_of_measure or 'Nos'
        ET.SubElement(item_master, 'ADDITIONALUNITS').text = item.unit_of_measure or 'Nos'
        
        # Opening balance
        if item.current_stock:
            opening_balance = ET.SubElement(item_master, 'OPENINGBALANCE')
            ET.SubElement(opening_balance, 'UNITS').text = str(item.current_stock)
            ET.SubElement(opening_balance, 'RATE').text = str(item.unit_price or 0)
        
        # GST details
        if item.gst_rate:
            ET.SubElement(item_master, 'GSTAPPLICABLE').text = 'Yes'
            ET.SubElement(item_master, 'GSTTYPEOFSUPPLY').text = 'Goods'
            if item.hsn_code:
                ET.SubElement(item_master, 'HSNCODE').text = item.hsn_code
    
    # Convert to pretty XML
    rough_string = ET.tostring(envelope, 'unicode')
    reparsed = minidom.parseString(rough_string)
    pretty_xml = reparsed.toprettyxml(indent="  ")
    
    response = make_response(pretty_xml)
    response.headers['Content-Type'] = 'application/xml'
    response.headers['Content-Disposition'] = f'attachment; filename=stock_items_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xml'
    
    return response

@tally_bp.route('/export/vouchers')
@login_required
def export_vouchers():
    """Export Purchase/Sales/Expense Vouchers to Tally XML"""
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    voucher_type = request.args.get('type', 'all')  # all, purchase, sales, expense
    
    # Create XML structure
    envelope = ET.Element('ENVELOPE')
    header = ET.SubElement(envelope, 'HEADER')
    ET.SubElement(header, 'TALLYREQUEST').text = 'Import Data'
    
    body = ET.SubElement(envelope, 'BODY')
    import_data = ET.SubElement(body, 'IMPORTDATA')
    request_desc = ET.SubElement(import_data, 'REQUESTDESC')
    ET.SubElement(request_desc, 'REPORTNAME').text = 'Vouchers'
    
    request_data = ET.SubElement(import_data, 'REQUESTDATA')
    
    # Build date filters
    date_filter = {}
    if date_from:
        try:
            date_filter['from'] = datetime.strptime(date_from, '%Y-%m-%d').date()
        except ValueError:
            pass
    if date_to:
        try:
            date_filter['to'] = datetime.strptime(date_to, '%Y-%m-%d').date()
        except ValueError:
            pass
    
    # Export Purchase Orders as Purchase Vouchers
    if voucher_type in ['all', 'purchase']:
        po_query = PurchaseOrder.query.filter_by(status='closed')
        if 'from' in date_filter:
            po_query = po_query.filter(PurchaseOrder.po_date >= date_filter['from'])
        if 'to' in date_filter:
            po_query = po_query.filter(PurchaseOrder.po_date <= date_filter['to'])
        
        purchase_orders = po_query.all()
        
        for po in purchase_orders:
            voucher = ET.SubElement(request_data, 'TALLYMESSAGE')
            voucher_elem = ET.SubElement(voucher, 'VOUCHER', VCHTYPE="Purchase", ACTION="Create")
            
            ET.SubElement(voucher_elem, 'DATE').text = po.po_date.strftime('%Y%m%d')
            ET.SubElement(voucher_elem, 'VOUCHERTYPENAME').text = 'Purchase'
            ET.SubElement(voucher_elem, 'VOUCHERNUMBER').text = po.po_number
            ET.SubElement(voucher_elem, 'REFERENCE').text = po.po_number
            
            # Add ledger entries
            ledger_entries = ET.SubElement(voucher_elem, 'ALLLEDGERENTRIES.LIST')
            
            # Supplier ledger (Credit)
            supplier_entry = ET.SubElement(ledger_entries, 'LEDGERENTRIES.LIST')
            ET.SubElement(supplier_entry, 'LEDGERNAME').text = po.supplier.name
            ET.SubElement(supplier_entry, 'ISDEEMEDPOSITIVE').text = 'No'
            ET.SubElement(supplier_entry, 'AMOUNT').text = f'-{po.total_amount}'
            
            # Item entries (Debit)
            for po_item in po.items:
                item_entry = ET.SubElement(ledger_entries, 'LEDGERENTRIES.LIST')
                ET.SubElement(item_entry, 'LEDGERNAME').text = po_item.item.name
                ET.SubElement(item_entry, 'ISDEEMEDPOSITIVE').text = 'Yes'
                ET.SubElement(item_entry, 'AMOUNT').text = str(po_item.total_price)
                
                # Stock item details
                if po_item.item:
                    inventory_entries = ET.SubElement(item_entry, 'ALLINVENTORYENTRIES.LIST')
                    inv_entry = ET.SubElement(inventory_entries, 'INVENTORYENTRIES.LIST')
                    ET.SubElement(inv_entry, 'STOCKITEMNAME').text = po_item.item.name
                    ET.SubElement(inv_entry, 'ISDEEMEDPOSITIVE').text = 'Yes'
                    ET.SubElement(inv_entry, 'QUANTITY').text = str(po_item.quantity)
                    ET.SubElement(inv_entry, 'RATE').text = str(po_item.unit_price)
    
    # Export Sales Orders as Sales Vouchers
    if voucher_type in ['all', 'sales']:
        so_query = SalesOrder.query.filter_by(status='delivered')
        if 'from' in date_filter:
            so_query = so_query.filter(SalesOrder.order_date >= date_filter['from'])
        if 'to' in date_filter:
            so_query = so_query.filter(SalesOrder.order_date <= date_filter['to'])
        
        sales_orders = so_query.all()
        
        for so in sales_orders:
            voucher = ET.SubElement(request_data, 'TALLYMESSAGE')
            voucher_elem = ET.SubElement(voucher, 'VOUCHER', VCHTYPE="Sales", ACTION="Create")
            
            ET.SubElement(voucher_elem, 'DATE').text = so.order_date.strftime('%Y%m%d')
            ET.SubElement(voucher_elem, 'VOUCHERTYPENAME').text = 'Sales'
            ET.SubElement(voucher_elem, 'VOUCHERNUMBER').text = so.so_number
            ET.SubElement(voucher_elem, 'REFERENCE').text = so.so_number
            
            # Add ledger entries
            ledger_entries = ET.SubElement(voucher_elem, 'ALLLEDGERENTRIES.LIST')
            
            # Customer ledger (Debit)
            customer_entry = ET.SubElement(ledger_entries, 'LEDGERENTRIES.LIST')
            ET.SubElement(customer_entry, 'LEDGERNAME').text = so.customer.name
            ET.SubElement(customer_entry, 'ISDEEMEDPOSITIVE').text = 'Yes'
            ET.SubElement(customer_entry, 'AMOUNT').text = str(so.total_amount)
            
            # Item entries (Credit)
            for so_item in so.items:
                item_entry = ET.SubElement(ledger_entries, 'LEDGERENTRIES.LIST')
                ET.SubElement(item_entry, 'LEDGERNAME').text = 'Sales'
                ET.SubElement(item_entry, 'ISDEEMEDPOSITIVE').text = 'No'
                ET.SubElement(item_entry, 'AMOUNT').text = f'-{so_item.total_price}'
    
    # Export Factory Expenses as Journal/Payment Vouchers
    if voucher_type in ['all', 'expense']:
        expense_query = FactoryExpense.query.filter_by(status='paid')
        if 'from' in date_filter:
            expense_query = expense_query.filter(FactoryExpense.expense_date >= date_filter['from'])
        if 'to' in date_filter:
            expense_query = expense_query.filter(FactoryExpense.expense_date <= date_filter['to'])
        
        expenses = expense_query.all()
        
        for expense in expenses:
            voucher = ET.SubElement(request_data, 'TALLYMESSAGE')
            voucher_type_name = 'Payment' if expense.payment_method else 'Journal'
            voucher_elem = ET.SubElement(voucher, 'VOUCHER', VCHTYPE=voucher_type_name, ACTION="Create")
            
            ET.SubElement(voucher_elem, 'DATE').text = expense.expense_date.strftime('%Y%m%d')
            ET.SubElement(voucher_elem, 'VOUCHERTYPENAME').text = voucher_type_name
            ET.SubElement(voucher_elem, 'VOUCHERNUMBER').text = expense.expense_number
            ET.SubElement(voucher_elem, 'NARRATION').text = expense.description
            
            # Add ledger entries
            ledger_entries = ET.SubElement(voucher_elem, 'ALLLEDGERENTRIES.LIST')
            
            # Expense ledger (Debit)
            expense_entry = ET.SubElement(ledger_entries, 'LEDGERENTRIES.LIST')
            expense_ledger_name = f"{expense.category.replace('_', ' ').title()} Expenses"
            ET.SubElement(expense_entry, 'LEDGERNAME').text = expense_ledger_name
            ET.SubElement(expense_entry, 'ISDEEMEDPOSITIVE').text = 'Yes'
            ET.SubElement(expense_entry, 'AMOUNT').text = str(expense.total_amount)
            
            # Payment ledger (Credit)
            payment_entry = ET.SubElement(ledger_entries, 'LEDGERENTRIES.LIST')
            if expense.payment_method == 'cash':
                payment_ledger = 'Cash'
            elif expense.payment_method == 'bank_transfer':
                payment_ledger = 'Bank Account'
            else:
                payment_ledger = 'Cash'
            
            ET.SubElement(payment_entry, 'LEDGERNAME').text = payment_ledger
            ET.SubElement(payment_entry, 'ISDEEMEDPOSITIVE').text = 'No'
            ET.SubElement(payment_entry, 'AMOUNT').text = f'-{expense.total_amount}'
    
    # Convert to pretty XML
    rough_string = ET.tostring(envelope, 'unicode')
    reparsed = minidom.parseString(rough_string)
    pretty_xml = reparsed.toprettyxml(indent="  ")
    
    response = make_response(pretty_xml)
    response.headers['Content-Type'] = 'application/xml'
    response.headers['Content-Disposition'] = f'attachment; filename=vouchers_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xml'
    
    return response

@tally_bp.route('/sync/mark_synced', methods=['POST'])
@login_required
def mark_synced():
    """Mark records as synced with Tally"""
    record_type = request.json.get('type')  # purchase, sales, expense
    record_ids = request.json.get('ids', [])
    
    try:
        if record_type == 'purchase':
            PurchaseOrder.query.filter(PurchaseOrder.id.in_(record_ids)).update(
                {PurchaseOrder.tally_synced: True}, synchronize_session=False
            )
        elif record_type == 'sales':
            SalesOrder.query.filter(SalesOrder.id.in_(record_ids)).update(
                {SalesOrder.tally_synced: True}, synchronize_session=False
            )
        elif record_type == 'expense':
            FactoryExpense.query.filter(FactoryExpense.id.in_(record_ids)).update(
                {FactoryExpense.tally_synced: True}, synchronize_session=False
            )
        
        db.session.commit()
        return jsonify({'success': True, 'message': f'{len(record_ids)} records marked as synced'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@tally_bp.route('/reports/sync_status')
@login_required
def sync_status_report():
    """Generate sync status report"""
    # Get sync statistics
    purchase_stats = {
        'total': PurchaseOrder.query.count(),
        'synced': PurchaseOrder.query.filter_by(tally_synced=True).count(),
        'pending': PurchaseOrder.query.filter_by(tally_synced=False).count()
    }
    
    sales_stats = {
        'total': SalesOrder.query.count(),
        'synced': SalesOrder.query.filter_by(tally_synced=True).count(),
        'pending': SalesOrder.query.filter_by(tally_synced=False).count()
    }
    
    expense_stats = {
        'total': FactoryExpense.query.count(),
        'synced': FactoryExpense.query.filter_by(tally_synced=True).count(),
        'pending': FactoryExpense.query.filter_by(tally_synced=False).count()
    }
    
    # Get pending records
    pending_purchases = PurchaseOrder.query.filter_by(tally_synced=False).limit(20).all()
    pending_sales = SalesOrder.query.filter_by(tally_synced=False).limit(20).all()
    pending_expenses = FactoryExpense.query.filter_by(tally_synced=False).limit(20).all()
    
    return render_template('tally/sync_status.html',
                         purchase_stats=purchase_stats,
                         sales_stats=sales_stats,
                         expense_stats=expense_stats,
                         pending_purchases=pending_purchases,
                         pending_sales=pending_sales,
                         pending_expenses=pending_expenses)

@tally_bp.route('/settings')
@login_required
def settings():
    """Tally integration settings"""
    return render_template('tally/settings.html')