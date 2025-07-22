from flask import Blueprint, render_template
from flask_login import login_required, current_user
from models import Item, PurchaseOrder, SalesOrder, Employee, JobWork, Production
from sqlalchemy import func

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
@login_required
def dashboard():
    # Get dashboard statistics
    stats = {
        'total_items': Item.query.count(),
        'low_stock_items': Item.query.filter(Item.current_stock <= Item.minimum_stock).count(),
        'open_purchase_orders': PurchaseOrder.query.filter_by(status='open').count(),
        'pending_sales_orders': SalesOrder.query.filter_by(status='pending').count(),
        'active_employees': Employee.query.filter_by(is_active=True).count(),
        'open_job_works': JobWork.query.filter_by(status='sent').count(),
        'planned_productions': Production.query.filter_by(status='planned').count()
    }
    
    # Recent activities
    recent_pos = PurchaseOrder.query.order_by(PurchaseOrder.created_at.desc()).limit(5).all()
    recent_sos = SalesOrder.query.order_by(SalesOrder.created_at.desc()).limit(5).all()
    low_stock_items = Item.query.filter(Item.current_stock <= Item.minimum_stock).limit(10).all()
    
    return render_template('dashboard.html', 
                         stats=stats, 
                         recent_pos=recent_pos, 
                         recent_sos=recent_sos,
                         low_stock_items=low_stock_items)
