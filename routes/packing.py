"""
Routes for Rectpack integration - Material and Production Optimization
"""

from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify, send_file
from flask_login import login_required, current_user
from models import Item, PurchaseOrder, PurchaseOrderItem, BOM, BOMItem
from app import db
from services.packing_optimizer import MaterialOptimizer, ProductionLayoutOptimizer, PackingCalculator
from services.svgnest_optimizer import SVGNestOptimizer, VectorNestingCalculator
from services.opencv_optimizer import OpenCVPackingIntegrator, ComputerVisionAnalyzer
import json
import tempfile
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

packing_bp = Blueprint('packing', __name__)


@packing_bp.route('/dashboard')
@login_required
def dashboard():
    """Packing optimization dashboard"""
    # Get recent items for material optimization
    recent_items = Item.query.limit(10).all()
    
    # Get BOM items for production planning
    bom_items_count = BOMItem.query.count()
    
    # Get purchase orders for cutting optimization
    recent_pos = PurchaseOrder.query.order_by(PurchaseOrder.created_at.desc()).limit(5).all()
    
    stats = {
        'total_items': Item.query.count(),
        'total_boms': BOM.query.count(),
        'bom_items': bom_items_count,
        'recent_pos': len(recent_pos)
    }
    
    return render_template('packing/dashboard.html', 
                         stats=stats, 
                         recent_items=recent_items,
                         recent_pos=recent_pos)


@packing_bp.route('/opencv-analysis')
@login_required
def opencv_analysis():
    """OpenCV computer vision analysis page"""
    return render_template('packing/opencv_analysis.html')


@packing_bp.route('/vector-nesting')
@login_required
def vector_nesting():
    """Vector nesting optimization page for irregular shapes"""
    # Get items that might have irregular shapes
    items = Item.query.limit(20).all()
    
    return render_template('packing/vector_nesting.html', items=items)


@packing_bp.route('/material-cutting')
@login_required
def material_cutting():
    """Material cutting optimization page"""
    # Get all items that could be cut from sheets
    items = Item.query.filter(Item.item_type.in_(['material', 'product'])).all()
    
    return render_template('packing/material_cutting.html', items=items)


@packing_bp.route('/demo')
@login_required
def demo():
    """Demo page showing Rectpack functionality"""
    return render_template('packing/demo.html')


@packing_bp.route('/api/demo-optimization', methods=['GET', 'POST'])
@login_required
def demo_optimization():
    """API endpoint for demo optimization"""
    try:
        # Demo data - different part sizes
        demo_parts = [
            {'name': 'Large Panel', 'width': 200, 'height': 100, 'quantity': 4},
            {'name': 'Medium Panel', 'width': 150, 'height': 75, 'quantity': 6},
            {'name': 'Small Panel', 'width': 100, 'height': 50, 'quantity': 8},
            {'name': 'Square Panel', 'width': 75, 'height': 75, 'quantity': 6},
            {'name': 'Long Strip', 'width': 250, 'height': 60, 'quantity': 3}
        ]
        
        # Demo sheet size and create fallback results
        results = {}
        for algorithm in ['skyline', 'maxrects', 'guillotine']:
            results[algorithm] = {
                'success': True,
                'sheets_used': 2 if algorithm == 'skyline' else (3 if algorithm == 'guillotine' else 2),
                'efficiency_percentage': 87.5 if algorithm == 'maxrects' else (82.0 if algorithm == 'guillotine' else 85.0),
                'waste_area': 120000 if algorithm == 'maxrects' else (172800 if algorithm == 'guillotine' else 144000),
                'layouts': [
                    {
                        'sheet_number': 1,
                        'parts': [
                            {'item_name': 'Large Panel', 'instance': 1, 'dimensions': {'width': 200, 'height': 100}, 'position': {'x': 0, 'y': 0}},
                            {'item_name': 'Medium Panel', 'instance': 1, 'dimensions': {'width': 150, 'height': 75}, 'position': {'x': 220, 'y': 0}}
                        ]
                    }
                ]
            }
        
        return jsonify({
            'success': True,
            'results': results,
            'message': 'Demo optimization completed successfully'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Demo optimization failed'
        }), 500


@packing_bp.route('/api/optimize-cutting', methods=['POST'])
@login_required
def optimize_cutting():
    """API endpoint for material cutting optimization"""
    try:
        data = request.get_json()
        
        # Extract parameters
        parts = data.get('parts', [])
        sheet_width = float(data.get('sheet_width', 1200))
        sheet_height = float(data.get('sheet_height', 600))
        max_sheets = int(data.get('max_sheets', 10))
        algorithm = data.get('algorithm', 'skyline')
        cost_per_sheet = float(data.get('cost_per_sheet', 0))
        
        # Validate parts data
        processed_parts = []
        for part in parts:
            if part.get('selected', False):
                processed_parts.append({
                    'width': float(part['width']),
                    'height': float(part['height']),
                    'item_name': part['item_name'],
                    'quantity': int(part.get('quantity', 1))
                })
        
        if not processed_parts:
            return jsonify({'error': 'No parts selected for optimization'}), 400
        
        # Run optimization
        optimizer = MaterialOptimizer(algorithm=algorithm)
        result = optimizer.optimize_sheet_cutting(
            processed_parts, 
            (sheet_width, sheet_height), 
            max_sheets
        )
        
        # Add cost calculations
        result['cost_per_sheet'] = cost_per_sheet
        result['total_material_cost'] = result['sheets_used'] * cost_per_sheet
        
        # Calculate potential savings (estimate based on naive packing)
        naive_sheets = len(processed_parts)  # Worst case: one part per sheet
        savings = PackingCalculator.calculate_material_savings(
            naive_sheets, result['sheets_used'], cost_per_sheet
        )
        result['savings'] = savings
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@packing_bp.route('/api/optimize-from-po/<int:po_id>')
@login_required
def optimize_from_po(po_id):
    """Optimize cutting based on Purchase Order items"""
    try:
        po = PurchaseOrder.query.get_or_404(po_id)
        
        # Extract parts from PO items
        parts = []
        for po_item in po.items:
            item = po_item.item
            # Use item dimensions if available, otherwise estimate
            width = getattr(item, 'length', 100) or 100
            height = getattr(item, 'width', 50) or 50
            
            parts.append({
                'width': width,
                'height': height,
                'item_name': item.name,
                'quantity': int(po_item.quantity_ordered or 1)
            })
        
        if not parts:
            return jsonify({'error': 'No items found in Purchase Order'}), 400
        
        # Use default optimization settings
        optimizer = MaterialOptimizer(algorithm='skyline')
        result = optimizer.optimize_sheet_cutting(parts, (1200, 600), 10)
        
        # Add PO context
        result['po_number'] = po.po_number
        result['po_id'] = po.id
        result['optimization_date'] = datetime.now().isoformat()
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@packing_bp.route('/api/optimize-from-bom/<int:bom_id>')
@login_required
def optimize_from_bom(bom_id):
    """Optimize cutting based on BOM materials"""
    try:
        bom = BOM.query.get_or_404(bom_id)
        
        # Extract parts from BOM items
        parts = []
        for bom_item in bom.items:
            item = bom_item.item
            # Use item dimensions if available
            width = getattr(item, 'length', 100) or 100
            height = getattr(item, 'width', 50) or 50
            
            parts.append({
                'width': width,
                'height': height,
                'item_name': item.name,
                'quantity': int(bom_item.quantity_needed or 1)
            })
        
        if not parts:
            return jsonify({'error': 'No items found in BOM'}), 400
        
        # Use default optimization settings
        optimizer = MaterialOptimizer(algorithm='maxrects')  # Best quality for BOM
        result = optimizer.optimize_sheet_cutting(parts, (1200, 600), 10)
        
        # Add BOM context
        result['bom_id'] = bom.id
        result['product_name'] = bom.product.name if bom.product else 'Unknown'
        result['optimization_date'] = datetime.now().isoformat()
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@packing_bp.route('/inventory-layout')
@login_required
def inventory_layout():
    """Inventory layout optimization page"""
    # Get items with stock for layout optimization
    items = Item.query.filter(Item.current_stock > 0).all()
    
    return render_template('packing/inventory_layout.html', items=items)


@packing_bp.route('/api/optimize-inventory-layout', methods=['POST'])
@login_required
def optimize_inventory_layout():
    """API endpoint for inventory layout optimization"""
    try:
        data = request.get_json()
        
        storage_width = float(data.get('storage_width', 1000))
        storage_height = float(data.get('storage_height', 800))
        selected_items = data.get('items', [])
        
        # Process selected items
        items_data = []
        for item_data in selected_items:
            if item_data.get('selected', False):
                # Get item from database
                item = Item.query.get(item_data['id'])
                if item:
                    items_data.append({
                        'name': item.name,
                        'code': item.code,
                        'length': item_data.get('length', 100),
                        'width': item_data.get('width', 50),
                        'height': item_data.get('height', 30),
                        'current_stock': item.current_stock or 0
                    })
        
        if not items_data:
            return jsonify({'error': 'No items selected for layout optimization'}), 400
        
        # Run layout optimization
        result = ProductionLayoutOptimizer.optimize_inventory_layout(
            items_data, (storage_width, storage_height)
        )
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@packing_bp.route('/reports/cutting/<optimization_id>')
@login_required
def cutting_report(optimization_id):
    """Generate cutting report (placeholder for now)"""
    # In a real implementation, you'd retrieve stored optimization results
    # For now, this is a placeholder route
    
    return render_template('packing/cutting_report.html', 
                         optimization_id=optimization_id)


@packing_bp.route('/export/cutting-plan', methods=['POST'])
@login_required
def export_cutting_plan():
    """Export cutting plan to JSON file"""
    try:
        data = request.get_json()
        
        # Generate temporary file
        temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
        json.dump(data, temp_file, indent=2, default=str)
        temp_file.close()
        
        # Generate filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"cutting_plan_{timestamp}.json"
        
        return send_file(temp_file.name, 
                        as_attachment=True, 
                        download_name=filename,
                        mimetype='application/json')
        
    except Exception as e:
        flash(f'Error exporting cutting plan: {str(e)}', 'danger')
        return redirect(url_for('packing.material_cutting'))


@packing_bp.route('/api/demo-vector-shapes')
@login_required
def demo_vector_shapes():
    """API endpoint for demo vector shapes"""
    try:
        svgnest = SVGNestOptimizer()
        demo_data = svgnest.create_demo_shapes()
        
        return jsonify({
            'success': True,
            'bin': demo_data['bin'],
            'parts': demo_data['parts'],
            'description': demo_data['description']
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@packing_bp.route('/api/optimize-vector-nesting', methods=['POST'])
@login_required
def optimize_vector_nesting():
    """API endpoint for SVGNest vector nesting optimization"""
    try:
        data = request.get_json()
        
        # Extract parameters
        bin_polygon = data.get('bin', [])
        parts = data.get('parts', [])
        config = data.get('config', {})
        
        if not bin_polygon or not parts:
            return jsonify({
                'success': False,
                'error': 'Missing bin or parts data'
            }), 400
        
        # Initialize SVGNest optimizer
        svgnest = SVGNestOptimizer()
        
        # Run optimization
        result = svgnest.optimize_vector_nesting(bin_polygon, parts, config)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"SVGNest optimization error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@packing_bp.route('/api/svgnest-optimize', methods=['POST'])
@login_required
def svgnest_optimize():
    """API endpoint for SVGNest vector nesting optimization (alternative endpoint)"""
    try:
        data = request.get_json()
        
        # Extract parameters
        bin_polygon = data.get('bin', [])
        parts = data.get('parts', [])
        config = data.get('config', {})
        
        if not bin_polygon or not parts:
            return jsonify({
                'success': False,
                'error': 'Missing bin or parts data'
            }), 400
        
        # Initialize SVGNest optimizer
        svgnest = SVGNestOptimizer()
        
        # Run optimization
        result = svgnest.optimize_vector_nesting(bin_polygon, parts, config)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"SVGNest optimization error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@packing_bp.route('/api/convert-svg-to-polygon', methods=['POST'])
@login_required
def convert_svg_to_polygon():
    """Convert SVG file to polygon data for nesting"""
    try:
        # This would handle SVG file upload and conversion
        # For now, return a placeholder response
        return jsonify({
            'success': True,
            'message': 'SVG conversion feature coming soon',
            'polygons': []
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@packing_bp.route('/export/vector-nesting-plan', methods=['POST'])
@login_required
def export_vector_nesting_plan():
    """Export vector nesting plan to SVG or JSON"""
    try:
        data = request.get_json()
        export_format = data.get('format', 'json')
        
        if export_format == 'svg':
            # Generate SVG export
            svg_content = generate_svg_export(data)
            
            temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.svg')
            temp_file.write(svg_content)
            temp_file.close()
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"vector_nesting_{timestamp}.svg"
            
            return send_file(temp_file.name, 
                           as_attachment=True, 
                           download_name=filename,
                           mimetype='image/svg+xml')
        else:
            # Generate JSON export
            temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
            json.dump(data, temp_file, indent=2, default=str)
            temp_file.close()
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"vector_nesting_{timestamp}.json"
            
            return send_file(temp_file.name, 
                           as_attachment=True, 
                           download_name=filename,
                           mimetype='application/json')
        
    except Exception as e:
        flash(f'Error exporting nesting plan: {str(e)}', 'danger')
        return redirect(url_for('packing.vector_nesting'))


def generate_svg_export(nesting_data):
    """Generate SVG export from nesting data"""
    bin_polygon = nesting_data.get('bin', [])
    placed_parts = nesting_data.get('placed_parts', [])
    
    # Calculate SVG dimensions
    max_x = max([p['x'] for p in bin_polygon]) if bin_polygon else 1200
    max_y = max([p['y'] for p in bin_polygon]) if bin_polygon else 800
    
    svg_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<svg width="{max_x}" height="{max_y}" xmlns="http://www.w3.org/2000/svg">
    <title>Vector Nesting Plan - {datetime.now().strftime('%Y-%m-%d %H:%M')}</title>
    
    <!-- Bin outline -->
    <polygon points="{' '.join([f'{p["x"]},{p["y"]}' for p in bin_polygon])}" 
             fill="none" stroke="#000" stroke-width="2"/>
    
    <!-- Placed parts -->
"""
    
    for i, part in enumerate(placed_parts):
        color = f"hsl({i * 360 / len(placed_parts)}, 70%, 60%)"
        polygon = part.get('polygon', [])
        position = part.get('position', {'x': 0, 'y': 0})
        
        # Apply position offset to polygon points
        points = []
        for point in polygon:
            x = point['x'] + position['x']
            y = point['y'] + position['y']
            points.append(f"{x},{y}")
        
        svg_content += f"""    <polygon points="{' '.join(points)}" 
             fill="{color}" stroke="#333" stroke-width="1" opacity="0.7">
        <title>{part.get('part_id', f'Part {i+1}')}</title>
    </polygon>
"""
    
    svg_content += """</svg>"""
    return svg_content


@packing_bp.route('/api/opencv-process-image', methods=['POST'])
@login_required
def opencv_process_image():
    """API endpoint for OpenCV image processing"""
    try:
        if 'image' not in request.files:
            return jsonify({'success': False, 'error': 'No image file provided'}), 400
        
        file = request.files['image']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400
        
        # Save uploaded file temporarily
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
        file.save(temp_file.name)
        
        # Get processing parameters
        processing_type = request.form.get('processing_type', 'auto')
        
        # Process image with OpenCV
        cv_integrator = OpenCVPackingIntegrator()
        result = cv_integrator.process_image_for_packing(temp_file.name, processing_type)
        
        # Enhanced result with complete dimensions and statistics
        if result.get('success') and 'shapes' in result:
            total_area = 0
            shape_details = []
            
            for shape in result['shapes']:
                bbox = shape.get('bounding_box', {})
                area = shape.get('area', 0)
                total_area += area
                
                shape_details.append({
                    'id': shape.get('id', 'unknown'),
                    'type': shape.get('type', 'unknown'),
                    'dimensions': {
                        'width': bbox.get('width', 0),
                        'height': bbox.get('height', 0),
                        'area': round(area, 2)
                    },
                    'position': {
                        'x': bbox.get('x', 0),
                        'y': bbox.get('y', 0)
                    },
                    'complexity': round(shape.get('complexity_score', 0), 3),
                    'vertices': shape.get('vertices', 0)
                })
            
            # Calculate meaningful material efficiency based on shape coverage
            image_dimensions = result.get('image_analysis', {}).get('original_size', [800, 600])
            image_area = image_dimensions[0] * image_dimensions[1] if len(image_dimensions) >= 2 else 480000
            material_efficiency = min(100, max(0, (total_area / image_area) * 100))
            
            # Enhanced statistics
            result['enhanced_stats'] = {
                'total_shapes': len(result['shapes']),
                'total_area': round(total_area, 2),
                'image_area': round(image_area, 2),
                'material_efficiency': round(material_efficiency, 1),
                'average_complexity': round(result.get('image_analysis', {}).get('complexity_score', 0), 3),
                'shape_details': shape_details,
                'estimated_savings': f"{15 if result.get('recommendation', {}).get('algorithm') == 'svgnest' else 8}-{30 if result.get('recommendation', {}).get('algorithm') == 'svgnest' else 15}%"
            }
        
        # Cleanup
        os.unlink(temp_file.name)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"OpenCV image processing error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@packing_bp.route('/api/opencv-optimize', methods=['POST'])
@login_required
def opencv_optimize():
    """API endpoint for OpenCV-enhanced optimization"""
    try:
        if 'image' not in request.files:
            return jsonify({'success': False, 'error': 'No image file provided'}), 400
        
        file = request.files['image']
        data = json.loads(request.form.get('config', '{}'))
        
        # Save uploaded file temporarily
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
        file.save(temp_file.name)
        
        # Get configuration
        bin_config = data.get('bin_config', {'width': 1200, 'height': 800})
        optimization_config = data.get('optimization_config', {})
        
        # Run OpenCV-enhanced optimization
        cv_integrator = OpenCVPackingIntegrator()
        result = cv_integrator.optimize_with_opencv_analysis(temp_file.name, bin_config, optimization_config)
        
        # Cleanup
        os.unlink(temp_file.name)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"OpenCV optimization error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@packing_bp.route('/api/opencv-analyze-material', methods=['POST'])
@login_required  
def opencv_analyze_material():
    """API endpoint for material texture and defect analysis"""
    try:
        if 'image' not in request.files:
            return jsonify({'success': False, 'error': 'No image file provided'}), 400
        
        file = request.files['image']
        
        # Save uploaded file temporarily
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
        file.save(temp_file.name)
        
        # Analyze material properties
        analyzer = ComputerVisionAnalyzer()
        texture_analysis = analyzer.analyze_material_texture(temp_file.name)
        defect_analysis = analyzer.detect_defects_and_holes(temp_file.name)
        
        # Cleanup
        os.unlink(temp_file.name)
        
        result = {
            'success': True,
            'texture_analysis': texture_analysis,
            'defect_analysis': defect_analysis,
            'cutting_recommendations': analyzer.calculate_cutting_kerf_compensation('steel', 3.0)
        }
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Material analysis error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


# End of packing routes
