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

@production_bp.route('/api/bom-tree')
@login_required
def api_bom_tree():
    """API endpoint for BOM tree data"""
    try:
        # Get all root BOMs (BOMs that are not components of other BOMs)
        boms = BOM.query.filter_by(is_active=True).all()
        
        def build_bom_tree_node(bom):
            """Build a tree node for a BOM"""
            node = {
                'bom_code': bom.bom_code,
                'item_name': bom.item.name if bom.item else 'Unknown Item',
                'quantity': bom.quantity,
                'uom': bom.item.unit_of_measure.symbol if bom.item and bom.item.unit_of_measure else 'PCS',
                'children': []
            }
            
            # Add child BOMs from BOM items
            for bom_item in bom.items:
                if bom_item.item:
                    # Check if this item has its own BOM
                    child_bom = BOM.query.filter_by(item_id=bom_item.item.id, is_active=True).first()
                    if child_bom:
                        child_node = build_bom_tree_node(child_bom)
                        node['children'].append(child_node)
                    else:
                        # Add as leaf node
                        leaf_node = {
                            'bom_code': bom_item.item.code,
                            'item_name': bom_item.item.name,
                            'quantity': bom_item.quantity,
                            'uom': bom_item.item.unit_of_measure.symbol if bom_item.item.unit_of_measure else 'PCS',
                            'children': []
                        }
                        node['children'].append(leaf_node)
            
            return node
        
        # Build tree structure
        tree_data = []
        for bom in boms:
            tree_node = build_bom_tree_node(bom)
            tree_data.append(tree_node)
        
        return jsonify({
            'success': True,
            'tree': tree_data
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@production_bp.route('/api/bom/<bom_code>/details')
@login_required
def api_bom_details(bom_code):
    """API endpoint for BOM details"""
    try:
        bom = BOM.query.filter_by(bom_code=bom_code).first()
        if not bom:
            return jsonify({
                'success': False,
                'message': 'BOM not found'
            }), 404
        
        # Build BOM details
        bom_data = {
            'bom_code': bom.bom_code,
            'item_name': bom.item.name if bom.item else 'Unknown Item',
            'quantity': bom.quantity,
            'uom': bom.item.unit_of_measure.symbol if bom.item and bom.item.unit_of_measure else 'PCS',
            'is_active': bom.is_active,
            'material_cost': float(bom.material_cost) if bom.material_cost else 0.0,
            'labor_cost': float(bom.labor_cost) if bom.labor_cost else 0.0,
            'overhead_cost': float(bom.overhead_cost) if bom.overhead_cost else 0.0,
            'total_cost': float(bom.total_cost) if bom.total_cost else 0.0,
            'items': []
        }
        
        # Add BOM items
        for bom_item in bom.items:
            if bom_item.item:
                item_data = {
                    'item_code': bom_item.item.code,
                    'item_name': bom_item.item.name,
                    'quantity': bom_item.quantity,
                    'uom': bom_item.item.unit_of_measure.symbol if bom_item.item.unit_of_measure else 'PCS',
                    'cost_per_unit': float(bom_item.cost_per_unit) if bom_item.cost_per_unit else 0.0,
                    'total_cost': float(bom_item.total_cost) if bom_item.total_cost else 0.0
                }
                bom_data['items'].append(item_data)
        
        return jsonify({
            'success': True,
            'bom': bom_data
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500