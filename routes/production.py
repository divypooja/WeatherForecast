from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from models import Production, Item, BOM, Supplier
from app import db
from datetime import datetime, date

production_bp = Blueprint('production', __name__)

@production_bp.route('/dashboard')
@login_required
def dashboard():
    """Simplified production dashboard without complex calculations"""
    try:
        # Basic production statistics
        total_productions = Production.query.count()
        planned_productions = Production.query.filter_by(status='planned').count()
        completed_productions = Production.query.filter_by(status='completed').count()
        
        # Dashboard stats for template
        dashboard_stats = {
            'total_orders': total_productions,
            'planned_orders': planned_productions,
            'completed_orders': completed_productions
        }
        
        # Cost monitor with safe defaults
        cost_monitor = {
            'material_cost': 0.0,
            'labor_cost': 0.0,
            'overhead_cost': 0.0,
            'total_cost': 0.0
        }
        
        # Recent productions (limited to prevent errors)
        recent_productions = Production.query.order_by(Production.created_at.desc()).limit(5).all()
        
        # Active productions (limited and safe)
        active_productions = Production.query.filter(
            Production.status.in_(['planned', 'in_progress'])
        ).limit(3).all()
        
        # BOM status (safe query)
        bom_status = BOM.query.filter_by(is_active=True).limit(5).all()
        
        return render_template('production/dashboard_clean.html', 
                             stats=dashboard_stats,
                             cost_monitor=cost_monitor,
                             recent_productions=recent_productions,
                             active_productions=active_productions,
                             bom_status=bom_status)
    except Exception as e:
        print(f"Production dashboard error: {e}")
        # Return minimal dashboard on error
        return render_template('production/dashboard_clean.html', 
                             stats={'total_orders': 0, 'planned_orders': 0, 'completed_orders': 0},
                             cost_monitor={'material_cost': 0, 'labor_cost': 0, 'overhead_cost': 0, 'total_cost': 0},
                             recent_productions=[],
                             active_productions=[],
                             bom_status=[])

@production_bp.route('/list')
@login_required  
def list_productions():
    """List all productions"""
    try:
        productions = Production.query.order_by(Production.created_at.desc()).limit(50).all()
        return render_template('production/list.html', productions=productions)
    except Exception as e:
        flash(f'Error loading productions: {e}', 'error')
        return redirect(url_for('production.dashboard'))

@production_bp.route('/add')
@login_required
def add_production():
    """Add new production page"""
    return render_template('production/add.html')

@production_bp.route('/bom')
@login_required
def list_bom():
    """List all BOMs"""
    try:
        boms = BOM.query.filter_by(is_active=True).limit(50).all()
        return render_template('production/bom_list.html', boms=boms)
    except Exception as e:
        flash(f'Error loading BOMs: {e}', 'error')
        return redirect(url_for('production.dashboard'))

@production_bp.route('/bom/add')
@login_required
def add_bom():
    """Add new BOM page"""
    return render_template('production/bom_add.html')

@production_bp.route('/bom/tree')
@login_required
def bom_tree_view():
    """BOM tree view"""
    return render_template('production/bom_tree.html')