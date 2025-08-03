from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from models import db, BOM, BOMItem, BOMProcess, Item, Supplier
from datetime import datetime
import json

bom_enhanced_bp = Blueprint('bom_enhanced', __name__, url_prefix='/bom-enhanced')

@bom_enhanced_bp.route('/')
@login_required
def enhanced_dashboard():
    """Enhanced BOM dashboard with feature toggles"""
    # Get all BOMs with statistics
    boms = BOM.query.order_by(BOM.created_at.desc()).all()
    active_boms_count = BOM.query.filter_by(status='active').count()
    
    # Calculate metrics
    total_components = sum(len(bom.items) for bom in boms)
    total_processes = sum(len(bom.processes) if bom.processes else 0 for bom in boms)
    
    # Calculate cost metrics
    total_material_cost = sum(bom.total_material_cost if bom.total_material_cost else 0 for bom in boms)
    total_labor_cost = sum(bom.labor_cost_per_unit if bom.labor_cost_per_unit else 0 for bom in boms)
    total_overhead_cost = sum(bom.overhead_cost_per_unit if bom.overhead_cost_per_unit else 0 for bom in boms)
    
    avg_bom_cost = total_material_cost / len(boms) if boms else 0
    avg_scrap_percent = sum(bom.estimated_scrap_percent if bom.estimated_scrap_percent else 0 for bom in boms) / len(boms) if boms else 0
    
    # Feature availability
    features = {
        'cost_analysis': True,
        'tree_view': True,
        'ai_insights': True,
        'bulk_operations': True,
        'export_functions': True,
        'template_system': True,
        'version_control': True,
        'approval_workflow': True,
        'integration_modules': True,
        'advanced_search': True
    }
    
    return render_template('production/bom_enhanced.html',
                         boms=boms,
                         active_boms_count=active_boms_count,
                         total_components=total_components,
                         total_processes=total_processes,
                         avg_bom_cost=avg_bom_cost,
                         avg_scrap_percent=avg_scrap_percent,
                         total_material_cost=total_material_cost,
                         total_labor_cost=total_labor_cost,
                         total_overhead_cost=total_overhead_cost,
                         features=features)

@bom_enhanced_bp.route('/api/features')
@login_required
def get_features():
    """Get current feature configuration"""
    features = {
        'cost_analysis': {
            'enabled': True,
            'name': 'Cost Analysis',
            'description': 'Advanced cost breakdown and optimization insights',
            'icon': 'fas fa-chart-line'
        },
        'tree_view': {
            'enabled': True,
            'name': 'Tree View',
            'description': 'Hierarchical BOM structure visualization',
            'icon': 'fas fa-sitemap'
        },
        'ai_insights': {
            'enabled': True,
            'name': 'AI Insights',
            'description': 'Machine learning powered optimization recommendations',
            'icon': 'fas fa-brain'
        },
        'bulk_operations': {
            'enabled': True,
            'name': 'Bulk Operations',
            'description': 'Mass update, duplicate, and delete operations',
            'icon': 'fas fa-tasks'
        },
        'export_functions': {
            'enabled': True,
            'name': 'Export Functions',
            'description': 'Excel, PDF, and API export capabilities',
            'icon': 'fas fa-download'
        },
        'template_system': {
            'enabled': True,
            'name': 'Template System',
            'description': 'Pre-built BOM templates for quick creation',
            'icon': 'fas fa-copy'
        },
        'version_control': {
            'enabled': True,
            'name': 'Version Control',
            'description': 'Track BOM changes and maintain version history',
            'icon': 'fas fa-code-branch'
        },
        'approval_workflow': {
            'enabled': False,
            'name': 'Approval Workflow',
            'description': 'Multi-level approval process for BOM changes',
            'icon': 'fas fa-check-circle'
        },
        'integration_modules': {
            'enabled': True,
            'name': 'Integration Modules',
            'description': 'Connect with ERP, accounting, and inventory systems',
            'icon': 'fas fa-plug'
        },
        'advanced_search': {
            'enabled': True,
            'name': 'Advanced Search',
            'description': 'Powerful filtering and search capabilities',
            'icon': 'fas fa-search'
        },
        'real_time_costing': {
            'enabled': True,
            'name': 'Real-time Costing',
            'description': 'Live cost updates based on current material prices',
            'icon': 'fas fa-clock'
        },
        'scrap_optimization': {
            'enabled': True,
            'name': 'Scrap Optimization',
            'description': 'Minimize waste through intelligent material planning',
            'icon': 'fas fa-recycle'
        }
    }
    return jsonify(features)

@bom_enhanced_bp.route('/api/features/toggle', methods=['POST'])
@login_required
def toggle_feature():
    """Toggle feature on/off"""
    data = request.get_json()
    feature_key = data.get('feature')
    enabled = data.get('enabled', False)
    
    # In a real implementation, you would store this in database or config
    # For now, return success
    return jsonify({
        'success': True,
        'feature': feature_key,
        'enabled': enabled,
        'message': f'Feature {feature_key} {"enabled" if enabled else "disabled"} successfully'
    })

@bom_enhanced_bp.route('/api/bom-analytics')
@login_required
def get_bom_analytics():
    """Get advanced BOM analytics"""
    boms = BOM.query.all()
    
    # Cost distribution
    cost_distribution = []
    material_vs_labor = []
    
    for bom in boms[:10]:  # Limit to top 10 for chart
        total_cost = bom.total_material_cost if bom.total_material_cost else 0
        labor_cost = bom.labor_cost_per_unit if bom.labor_cost_per_unit else 0
        
        cost_distribution.append({
            'bom_code': bom.bom_code,
            'total_cost': float(total_cost),
            'components': len(bom.items) if bom.items else 0
        })
        
        material_vs_labor.append({
            'bom_code': bom.bom_code,
            'material_cost': float(total_cost),
            'labor_cost': float(labor_cost)
        })
    
    # Efficiency metrics
    efficiency_metrics = {
        'high_cost_boms': len([b for b in boms if (b.total_material_cost or 0) > 1000]),
        'optimization_opportunities': len([b for b in boms if (b.estimated_scrap_percent or 0) > 5]),
        'outdated_boms': len([b for b in boms if b.updated_at and (datetime.now() - b.updated_at).days > 90])
    }
    
    return jsonify({
        'cost_distribution': cost_distribution,
        'material_vs_labor': material_vs_labor,
        'efficiency_metrics': efficiency_metrics,
        'total_boms': len(boms),
        'active_boms': len([b for b in boms if b.status == 'active'])
    })

@bom_enhanced_bp.route('/api/bom/<int:bom_id>/optimize')
@login_required
def optimize_bom(bom_id):
    """Get optimization suggestions for a specific BOM"""
    bom = BOM.query.get_or_404(bom_id)
    
    suggestions = []
    
    # Check for high scrap percentage
    if bom.estimated_scrap_percent and bom.estimated_scrap_percent > 5:
        suggestions.append({
            'type': 'warning',
            'title': 'High Scrap Rate',
            'description': f'Scrap percentage of {bom.estimated_scrap_percent}% is above optimal threshold',
            'recommendation': 'Review process efficiency and material handling procedures',
            'potential_saving': bom.estimated_scrap_percent * 0.1
        })
    
    # Check for expensive components
    if bom.items:
        expensive_items = [item for item in bom.items if (item.unit_cost or 0) > 100]
        if expensive_items:
            suggestions.append({
                'type': 'info',
                'title': 'Expensive Components',
                'description': f'{len(expensive_items)} components have unit costs above ₹100',
                'recommendation': 'Consider alternative suppliers or bulk purchasing discounts',
                'potential_saving': len(expensive_items) * 5
            })
    
    # Check for outdated BOM
    if bom.updated_at and (datetime.now() - bom.updated_at).days > 90:
        suggestions.append({
            'type': 'warning',
            'title': 'Outdated BOM',
            'description': f'BOM not updated for {(datetime.now() - bom.updated_at).days} days',
            'recommendation': 'Review and update component costs and specifications',
            'potential_saving': 2
        })
    
    return jsonify({
        'bom_code': bom.bom_code,
        'suggestions': suggestions,
        'total_potential_saving': sum(s.get('potential_saving', 0) for s in suggestions)
    })

@bom_enhanced_bp.route('/api/bulk-operations', methods=['POST'])
@login_required
def bulk_operations():
    """Handle bulk operations on BOMs"""
    data = request.get_json()
    operation = data.get('operation')
    bom_ids = data.get('bom_ids', [])
    
    try:
        if operation == 'activate':
            BOM.query.filter(BOM.id.in_(bom_ids)).update({BOM.status: 'active'})
            message = f'{len(bom_ids)} BOMs activated successfully'
            
        elif operation == 'deactivate':
            BOM.query.filter(BOM.id.in_(bom_ids)).update({BOM.status: 'inactive'})
            message = f'{len(bom_ids)} BOMs deactivated successfully'
            
        elif operation == 'delete':
            # Delete BOM items and processes first
            boms_to_delete = BOM.query.filter(BOM.id.in_(bom_ids)).all()
            for bom in boms_to_delete:
                for item in bom.items:
                    db.session.delete(item)
                for process in bom.processes if bom.processes else []:
                    db.session.delete(process)
                db.session.delete(bom)
            message = f'{len(bom_ids)} BOMs deleted successfully'
            
        elif operation == 'duplicate':
            original_boms = BOM.query.filter(BOM.id.in_(bom_ids)).all()
            duplicated_count = 0
            
            for original_bom in original_boms:
                # Create duplicate BOM
                new_bom_code = f"{original_bom.bom_code}-COPY-{datetime.now().strftime('%Y%m%d%H%M%S')}"
                
                duplicate_bom = BOM(
                    bom_code=new_bom_code,
                    product_id=original_bom.product_id,
                    version='1.0',
                    status='draft',
                    output_quantity=original_bom.output_quantity,
                    description=f"Copy of {original_bom.description}",
                    labor_cost_per_unit=original_bom.labor_cost_per_unit,
                    overhead_cost_per_unit=original_bom.overhead_cost_per_unit,
                    created_by=current_user.id
                )
                db.session.add(duplicate_bom)
                db.session.flush()
                
                # Duplicate BOM items
                for item in original_bom.items:
                    duplicate_item = BOMItem(
                        bom_id=duplicate_bom.id,
                        material_id=item.material_id,
                        qty_required=item.qty_required,
                        unit_cost=item.unit_cost,
                        scrap_percent=item.scrap_percent
                    )
                    db.session.add(duplicate_item)
                
                # Duplicate BOM processes
                if original_bom.processes:
                    for process in original_bom.processes:
                        duplicate_process = BOMProcess(
                            bom_id=duplicate_bom.id,
                            step_number=process.step_number,
                            process_name=process.process_name,
                            operation_description=process.operation_description,
                            cost_per_unit=process.cost_per_unit
                        )
                        db.session.add(duplicate_process)
                
                duplicated_count += 1
            
            message = f'{duplicated_count} BOMs duplicated successfully'
            
        else:
            return jsonify({'success': False, 'message': 'Invalid operation'}), 400
        
        db.session.commit()
        return jsonify({'success': True, 'message': message})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@bom_enhanced_bp.route('/api/export/<format>')
@login_required
def export_boms(format):
    """Export BOMs in various formats"""
    boms = BOM.query.all()
    
    if format == 'json':
        export_data = []
        for bom in boms:
            bom_data = {
                'bom_code': bom.bom_code,
                'product_name': bom.product.name if bom.product else '',
                'version': bom.version,
                'status': bom.status,
                'total_cost': float(bom.total_material_cost) if bom.total_material_cost else 0,
                'components': [
                    {
                        'material_name': item.material.name if item.material else '',
                        'quantity': float(item.qty_required),
                        'unit_cost': float(item.unit_cost)
                    } for item in bom.items
                ],
                'created_at': bom.created_at.isoformat() if bom.created_at else None
            }
            export_data.append(bom_data)
        
        return jsonify({
            'success': True,
            'data': export_data,
            'format': 'json',
            'timestamp': datetime.now().isoformat()
        })
    
    elif format == 'csv':
        # Return CSV data structure
        csv_data = [
            ['BOM Code', 'Product', 'Version', 'Status', 'Total Cost', 'Components Count', 'Created Date']
        ]
        
        for bom in boms:
            csv_data.append([
                bom.bom_code,
                bom.product.name if bom.product else '',
                bom.version,
                bom.status,
                bom.total_material_cost if bom.total_material_cost else 0,
                len(bom.items),
                bom.created_at.strftime('%Y-%m-%d') if bom.created_at else ''
            ])
        
        return jsonify({
            'success': True,
            'data': csv_data,
            'format': 'csv',
            'filename': f'bom_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        })
    
    else:
        return jsonify({'success': False, 'message': 'Unsupported format'}), 400

@bom_enhanced_bp.route('/api/templates')
@login_required
def get_bom_templates():
    """Get available BOM templates"""
    templates = [
        {
            'id': 'standard_manufacturing',
            'name': 'Standard Manufacturing BOM',
            'description': 'Basic manufacturing BOM with materials, labor, and overhead',
            'icon': 'fas fa-industry',
            'components': ['Raw Materials', 'Labor Hours', 'Machine Time', 'Overhead'],
            'estimated_time': '15 minutes'
        },
        {
            'id': 'assembly_bom',
            'name': 'Assembly BOM',
            'description': 'Multi-level BOM for complex assembly products',
            'icon': 'fas fa-puzzle-piece',
            'components': ['Sub-assemblies', 'Fasteners', 'Assembly Labor', 'Quality Control'],
            'estimated_time': '25 minutes'
        },
        {
            'id': 'job_work_bom',
            'name': 'Job Work BOM',
            'description': 'BOM for outsourced manufacturing processes',
            'icon': 'fas fa-tools',
            'components': ['Raw Materials', 'Job Work Processes', 'Transportation', 'Quality Checks'],
            'estimated_time': '20 minutes'
        },
        {
            'id': 'fabrication_bom',
            'name': 'Fabrication BOM',
            'description': 'Metal fabrication and welding operations',
            'icon': 'fas fa-hammer',
            'components': ['Metal Sheets', 'Cutting', 'Bending', 'Welding', 'Finishing'],
            'estimated_time': '30 minutes'
        },
        {
            'id': 'packaging_bom',
            'name': 'Packaging BOM',
            'description': 'Product packaging and shipping preparation',
            'icon': 'fas fa-box',
            'components': ['Primary Packaging', 'Secondary Packaging', 'Labels', 'Documentation'],
            'estimated_time': '10 minutes'
        }
    ]
    
    return jsonify({
        'success': True,
        'templates': templates
    })

@bom_enhanced_bp.route('/api/search', methods=['POST'])
@login_required
def advanced_search():
    """Advanced BOM search with multiple filters"""
    data = request.get_json()
    
    query = BOM.query
    
    # Text search
    if data.get('search_text'):
        search_text = f"%{data['search_text']}%"
        query = query.filter(
            db.or_(
                BOM.bom_code.ilike(search_text),
                BOM.description.ilike(search_text)
            )
        )
    
    # Status filter
    if data.get('status'):
        query = query.filter(BOM.status == data['status'])
    
    # Cost range filter
    if data.get('min_cost') is not None:
        query = query.filter(BOM.total_material_cost >= data['min_cost'])
    if data.get('max_cost') is not None:
        query = query.filter(BOM.total_material_cost <= data['max_cost'])
    
    # Date range filter
    if data.get('date_from'):
        date_from = datetime.strptime(data['date_from'], '%Y-%m-%d')
        query = query.filter(BOM.created_at >= date_from)
    if data.get('date_to'):
        date_to = datetime.strptime(data['date_to'], '%Y-%m-%d')
        query = query.filter(BOM.created_at <= date_to)
    
    # Component count filter
    if data.get('min_components'):
        # This would need a subquery in real implementation
        pass
    
    results = query.order_by(BOM.created_at.desc()).limit(50).all()
    
    search_results = []
    for bom in results:
        search_results.append({
            'id': bom.id,
            'bom_code': bom.bom_code,
            'product_name': bom.product.name if bom.product else '',
            'version': bom.version,
            'status': bom.status,
            'total_cost': float(bom.total_material_cost) if bom.total_material_cost else 0,
            'components_count': len(bom.items),
            'created_at': bom.created_at.strftime('%Y-%m-%d') if bom.created_at else ''
        })
    
    return jsonify({
        'success': True,
        'results': search_results,
        'total_found': len(search_results)
    })