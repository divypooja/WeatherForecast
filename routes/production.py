from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from models import Production, Item, BOM, Supplier
from app import db
from datetime import datetime, date

production_bp = Blueprint('production', __name__)

def get_uom_symbol(uom_obj):
    """Safely get UOM symbol whether it's an object or string"""
    if uom_obj is None:
        return 'PCS'
    if hasattr(uom_obj, 'symbol'):
        return uom_obj.symbol
    return str(uom_obj)  # If it's already a string

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
            # Get UOM symbol safely
            uom_symbol = 'PCS'
            if bom.output_uom:
                uom_symbol = get_uom_symbol(bom.output_uom)
            elif bom.product and bom.product.unit_of_measure:
                uom_symbol = get_uom_symbol(bom.product.unit_of_measure)
            
            node = {
                'bom_code': bom.bom_code,
                'item_name': bom.product.name if bom.product else 'Unknown Item',
                'quantity': bom.output_quantity,
                'uom': uom_symbol,
                'children': []
            }
            
            # Add child BOMs from BOM items
            for bom_item in bom.items:
                if bom_item.material:
                    # Check if this material has its own BOM
                    child_bom = BOM.query.filter_by(product_id=bom_item.material.id, is_active=True).first()
                    if child_bom:
                        child_node = build_bom_tree_node(child_bom)
                        node['children'].append(child_node)
                    else:
                        # Get UOM symbol safely for leaf node
                        leaf_uom_symbol = 'PCS'
                        if bom_item.uom:
                            leaf_uom_symbol = get_uom_symbol(bom_item.uom)
                        elif bom_item.material and bom_item.material.unit_of_measure:
                            leaf_uom_symbol = get_uom_symbol(bom_item.material.unit_of_measure)
                        
                        # Add as leaf node
                        leaf_node = {
                            'bom_code': bom_item.material.code,
                            'item_name': bom_item.material.name,
                            'quantity': bom_item.qty_required,
                            'uom': leaf_uom_symbol,
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
        # Get UOM symbol safely
        bom_uom_symbol = 'PCS'
        if bom.output_uom:
            bom_uom_symbol = get_uom_symbol(bom.output_uom)
        elif bom.product and bom.product.unit_of_measure:
            bom_uom_symbol = get_uom_symbol(bom.product.unit_of_measure)
        
        bom_data = {
            'bom_code': bom.bom_code,
            'item_name': bom.product.name if bom.product else 'Unknown Item',
            'quantity': bom.output_quantity,
            'uom': bom_uom_symbol,
            'is_active': bom.is_active,
            'material_cost': 0.0,  # Calculate from BOM items
            'labor_cost': float(bom.labor_cost_per_unit) if bom.labor_cost_per_unit else 0.0,
            'overhead_cost': float(bom.overhead_cost_per_unit) if bom.overhead_cost_per_unit else 0.0,
            'total_cost': 0.0,  # Calculate total
            'items': []
        }
        
        # Add BOM items and calculate total costs
        material_cost = 0.0
        for bom_item in bom.items:
            if bom_item.material:
                cost_per_unit = float(bom_item.unit_cost) if bom_item.unit_cost else 0.0
                total_cost = cost_per_unit * bom_item.qty_required
                material_cost += total_cost
                
                # Get UOM symbol safely for BOM item
                item_uom_symbol = 'PCS'
                if bom_item.uom:
                    item_uom_symbol = get_uom_symbol(bom_item.uom)
                elif bom_item.material and bom_item.material.unit_of_measure:
                    item_uom_symbol = get_uom_symbol(bom_item.material.unit_of_measure)
                
                item_data = {
                    'item_code': bom_item.material.code,
                    'item_name': bom_item.material.name,
                    'quantity': bom_item.qty_required,
                    'uom': item_uom_symbol,
                    'cost_per_unit': cost_per_unit,
                    'total_cost': total_cost
                }
                bom_data['items'].append(item_data)
        
        # Update calculated costs
        bom_data['material_cost'] = material_cost
        bom_data['total_cost'] = material_cost + bom_data['labor_cost'] + bom_data['overhead_cost']
        
        return jsonify({
            'success': True,
            'bom': bom_data
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500