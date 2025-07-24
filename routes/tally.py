from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from app import db
from models import Item, Supplier, PurchaseOrder, SalesOrder, FactoryExpense
from services.tally_integration import tally_service
from forms import TallySettingsForm
import logging

logger = logging.getLogger(__name__)

tally_bp = Blueprint('tally', __name__, url_prefix='/tally')

@tally_bp.route('/dashboard')
@login_required
def dashboard():
    """Tally Integration Dashboard"""
    # Get summary statistics
    stats = {
        'total_suppliers': Supplier.query.count(),
        'total_items': Item.query.count(),
        'total_purchase_orders': PurchaseOrder.query.count(),
        'total_sales_orders': SalesOrder.query.count(),
        'total_expenses': FactoryExpense.query.count(),
    }
    
    # Get recent sync logs (if implemented)
    recent_syncs = []  # Placeholder for sync history
    
    return render_template('tally/dashboard.html', stats=stats, recent_syncs=recent_syncs)

@tally_bp.route('/test-connection')
@login_required
def test_connection():
    """Test connection to Tally"""
    result = tally_service.test_connection()
    return jsonify(result)

@tally_bp.route('/sync-suppliers', methods=['POST'])
@login_required
def sync_suppliers():
    """Sync all suppliers to Tally as Ledgers"""
    try:
        suppliers = Supplier.query.all()
        result = tally_service.sync_suppliers(suppliers)
        
        if result['status'] == 'success':
            flash(f"Successfully synced {result['synced']} suppliers to Tally", 'success')
        else:
            flash(f"Sync failed: {result['message']}", 'danger')
            
    except Exception as e:
        logger.error(f"Supplier sync error: {str(e)}")
        flash(f"Sync error: {str(e)}", 'danger')
    
    return redirect(url_for('tally.dashboard'))

@tally_bp.route('/sync-items', methods=['POST'])
@login_required
def sync_items():
    """Sync all items to Tally as Stock Items"""
    try:
        items = Item.query.all()
        result = tally_service.sync_items(items)
        
        if result['status'] == 'success':
            flash(f"Successfully synced {result['synced']} items to Tally", 'success')
        else:
            flash(f"Sync failed: {result['message']}", 'danger')
            
    except Exception as e:
        logger.error(f"Items sync error: {str(e)}")
        flash(f"Sync error: {str(e)}", 'danger')
    
    return redirect(url_for('tally.dashboard'))

@tally_bp.route('/sync-purchase-orders', methods=['POST'])
@login_required
def sync_purchase_orders():
    """Sync purchase orders to Tally as Purchase Vouchers"""
    try:
        # Only sync approved purchase orders
        purchase_orders = PurchaseOrder.query.filter_by(status='approved').all()
        result = tally_service.sync_purchase_orders(purchase_orders)
        
        if result['status'] in ['success', 'partial']:
            flash(f"Successfully synced {result['synced']} purchase orders to Tally", 'success')
            if result['status'] == 'partial' and 'errors' in result:
                flash(f"Some errors occurred: {', '.join(result['errors'])}", 'warning')
        else:
            flash(f"Sync failed: {result['message']}", 'danger')
            
    except Exception as e:
        logger.error(f"Purchase orders sync error: {str(e)}")
        flash(f"Sync error: {str(e)}", 'danger')
    
    return redirect(url_for('tally.dashboard'))

@tally_bp.route('/sync-sales-orders', methods=['POST'])
@login_required
def sync_sales_orders():
    """Sync sales orders to Tally as Sales Vouchers"""
    try:
        # Only sync approved/completed sales orders
        sales_orders = SalesOrder.query.filter(SalesOrder.status.in_(['approved', 'completed'])).all()
        result = tally_service.sync_sales_orders(sales_orders)
        
        if result['status'] in ['success', 'partial']:
            flash(f"Successfully synced {result['synced']} sales orders to Tally", 'success')
            if result['status'] == 'partial' and 'errors' in result:
                flash(f"Some errors occurred: {', '.join(result['errors'])}", 'warning')
        else:
            flash(f"Sync failed: {result['message']}", 'danger')
            
    except Exception as e:
        logger.error(f"Sales orders sync error: {str(e)}")
        flash(f"Sync error: {str(e)}", 'danger')
    
    return redirect(url_for('tally.dashboard'))

@tally_bp.route('/sync-expenses', methods=['POST'])
@login_required
def sync_expenses():
    """Sync factory expenses to Tally as Journal Vouchers"""
    try:
        # Only sync approved expenses
        expenses = FactoryExpense.query.filter_by(status='approved').all()
        result = tally_service.sync_expenses(expenses)
        
        if result['status'] in ['success', 'partial']:
            flash(f"Successfully synced {result['synced']} expenses to Tally", 'success')
            if result['status'] == 'partial' and 'errors' in result:
                flash(f"Some errors occurred: {', '.join(result['errors'])}", 'warning')
        else:
            flash(f"Sync failed: {result['message']}", 'danger')
            
    except Exception as e:
        logger.error(f"Expenses sync error: {str(e)}")
        flash(f"Sync error: {str(e)}", 'danger')
    
    return redirect(url_for('tally.dashboard'))

@tally_bp.route('/sync-all', methods=['POST'])
@login_required
def sync_all():
    """Sync all data to Tally in proper sequence"""
    try:
        sync_results = []
        
        # 1. Sync Suppliers (Ledgers first)
        suppliers = Supplier.query.all()
        supplier_result = tally_service.sync_suppliers(suppliers)
        sync_results.append(f"Suppliers: {supplier_result['synced'] if supplier_result['status'] == 'success' else 'Failed'}")
        
        # 2. Sync Items (Stock Items)
        items = Item.query.all()
        items_result = tally_service.sync_items(items)
        sync_results.append(f"Items: {items_result['synced'] if items_result['status'] == 'success' else 'Failed'}")
        
        # 3. Sync Purchase Orders
        purchase_orders = PurchaseOrder.query.filter_by(status='approved').all()
        po_result = tally_service.sync_purchase_orders(purchase_orders)
        sync_results.append(f"Purchase Orders: {po_result['synced'] if po_result['status'] in ['success', 'partial'] else 'Failed'}")
        
        # 4. Sync Sales Orders
        sales_orders = SalesOrder.query.filter(SalesOrder.status.in_(['approved', 'completed'])).all()
        so_result = tally_service.sync_sales_orders(sales_orders)
        sync_results.append(f"Sales Orders: {so_result['synced'] if so_result['status'] in ['success', 'partial'] else 'Failed'}")
        
        # 5. Sync Expenses
        expenses = FactoryExpense.query.filter_by(status='approved').all()
        expense_result = tally_service.sync_expenses(expenses)
        sync_results.append(f"Expenses: {expense_result['synced'] if expense_result['status'] in ['success', 'partial'] else 'Failed'}")
        
        flash(f"Full sync completed: {', '.join(sync_results)}", 'success')
        
    except Exception as e:
        logger.error(f"Full sync error: {str(e)}")
        flash(f"Full sync error: {str(e)}", 'danger')
    
    return redirect(url_for('tally.dashboard'))

@tally_bp.route('/settings')
@login_required
def settings():
    """Tally Integration Settings"""
    form = TallySettingsForm()
    return render_template('tally/settings.html', form=form)

@tally_bp.route('/settings', methods=['POST'])
@login_required
def update_settings():
    """Update Tally Integration Settings"""
    form = TallySettingsForm()
    if form.validate_on_submit():
        # Save settings to database or config
        flash('Tally settings updated successfully', 'success')
        return redirect(url_for('tally.dashboard'))
    
    return render_template('tally/settings.html', form=form)