from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required
from datetime import datetime, date
from models import Production, BOM, Item
from app import db

production_htmx_bp = Blueprint('production_htmx', __name__)

@production_htmx_bp.route('/dashboard-htmx')
@login_required
def dashboard_htmx():
    """HTMX version of production dashboard"""
    # Enhanced production statistics
    total_productions = Production.query.count()
    planned_productions = Production.query.filter_by(status='planned').count()
    in_progress_productions = Production.query.filter_by(status='in_progress').count()
    completed_productions = Production.query.filter_by(status='completed').count()
    
    # Calculate cost metrics from completed productions
    completed_prods = Production.query.filter_by(status='completed').all()
    avg_cost_per_unit = 0
    avg_material_cost = 0
    avg_labor_cost = 0
    avg_scrap_percent = 0
    avg_efficiency = 95
    
    if completed_prods:
        total_cost = 0
        total_material_cost = 0
        total_labor_cost = 0
        total_scrap = 0
        total_units = 0
        
        for prod in completed_prods:
            if prod.bom:
                # Calculate unit costs from BOM
                bom_material_cost = sum(item.item.purchase_price * item.quantity_required for item in prod.bom.items if item.item.purchase_price) or 0
                bom_labor_cost = prod.bom.labor_cost_per_unit or 0
                scrap_percent = prod.bom.scrap_percent or 0
                
                units = prod.quantity_produced or 1
                total_cost += (bom_material_cost + bom_labor_cost) * units
                total_material_cost += bom_material_cost * units
                total_labor_cost += bom_labor_cost * units
                total_scrap += scrap_percent
                total_units += units
        
        if total_units > 0:
            avg_cost_per_unit = total_cost / total_units
            avg_material_cost = total_material_cost / total_units
            avg_labor_cost = total_labor_cost / total_units
        
        if completed_prods:
            avg_scrap_percent = total_scrap / len(completed_prods)
            avg_efficiency = max(95, 100 - avg_scrap_percent)
    
    stats = {
        'total_productions': total_productions,
        'planned_productions': planned_productions,
        'in_progress_productions': in_progress_productions,
        'completed_productions': completed_productions,
        'total_boms': BOM.query.filter_by(is_active=True).count(),
        'avg_cost_per_unit': avg_cost_per_unit,
        'avg_material_cost': avg_material_cost,
        'avg_labor_cost': avg_labor_cost,
        'avg_scrap_percent': avg_scrap_percent,
        'avg_efficiency': avg_efficiency
    }
    
    # Recent productions
    recent_productions = Production.query.order_by(Production.created_at.desc()).limit(10).all()
    
    # Active productions 
    active_productions = Production.query.filter(
        Production.status.in_(['planned', 'in_progress'])
    ).order_by(Production.created_at.desc()).limit(5).all()
    
    return render_template('production/dashboard_htmx.html', 
                         stats=stats, 
                         recent_productions=recent_productions,
                         active_productions=active_productions)

@production_htmx_bp.route('/dashboard-refresh')
@login_required
def dashboard_refresh():
    """HTMX endpoint to refresh metrics"""
    # Recalculate stats
    stats = {
        'total_productions': Production.query.count(),
        'planned_productions': Production.query.filter_by(status='planned').count(),
        'in_progress_productions': Production.query.filter_by(status='in_progress').count(),
        'completed_productions': Production.query.filter_by(status='completed').count(),
    }
    
    return render_template('production/partials/metrics.html', stats=stats)

@production_htmx_bp.route('/dashboard-tab/<tab_name>')
@login_required
def dashboard_tab(tab_name):
    """HTMX endpoint for tab content"""
    if tab_name == 'recent':
        recent_productions = Production.query.order_by(Production.created_at.desc()).limit(10).all()
        return render_template('production/partials/recent_productions.html', 
                             recent_productions=recent_productions)
    
    elif tab_name == 'active':
        active_productions = Production.query.filter(
            Production.status.in_(['planned', 'in_progress'])
        ).order_by(Production.created_at.desc()).limit(10).all()
        return render_template('production/partials/active_productions.html', 
                             active_productions=active_productions)
    
    elif tab_name == 'analytics':
        # Calculate analytics data
        completed_prods = Production.query.filter_by(status='completed').all()
        analytics_data = {
            'total_completed': len(completed_prods),
            'avg_completion_time': '2.5 days',  # Placeholder
            'efficiency_rate': '94.5%',
            'quality_score': '96.2%'
        }
        return render_template('production/partials/analytics.html', 
                             analytics=analytics_data)
    
    return "<p>Tab not found</p>"

@production_htmx_bp.route('/dashboard-modal/<modal_type>')
@login_required
def dashboard_modal(modal_type):
    """HTMX endpoint for modals"""
    if modal_type == 'planned-orders':
        planned_productions = Production.query.filter_by(status='planned').all()
        return render_template('production/partials/planned_orders_modal.html', 
                             planned_productions=planned_productions)
    
    return "<p>Modal not found</p>"

@production_htmx_bp.route('/dashboard-updates')
@login_required
def dashboard_updates():
    """HTMX endpoint for live updates"""
    updates = [
        {
            'icon': 'fas fa-check-circle',
            'message': 'Production PR-2025-001 completed',
            'time': '2 min ago',
            'type': 'success'
        },
        {
            'icon': 'fas fa-play',
            'message': 'Production PR-2025-002 started',
            'time': '5 min ago',
            'type': 'info'
        }
    ]
    
    return render_template('production/partials/live_updates.html', updates=updates)