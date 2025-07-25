from flask import Blueprint, jsonify
from models import Supplier

api_bp = Blueprint('api', __name__)

@api_bp.route('/transporter/<int:transporter_id>')
def get_transporter_details(transporter_id):
    """Get transporter details including freight rate"""
    transporter = Supplier.query.get(transporter_id)
    
    if not transporter or transporter.partner_type not in ['transporter', 'both']:
        return jsonify({'success': False, 'error': 'Transporter not found'}), 404
    
    return jsonify({
        'success': True,
        'id': transporter.id,
        'name': transporter.name,
        'freight_rate_per_unit': transporter.freight_rate_per_unit or 0.0,
        'freight_unit_type': transporter.freight_unit_type or 'per_km'
    })