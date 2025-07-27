from flask import Blueprint, request, jsonify, render_template, flash, redirect, url_for
from flask_login import login_required, current_user
from models import db, JobWork, JobWorkProcess, Item, ItemBatch
from datetime import datetime
import json

live_status_bp = Blueprint('live_status', __name__, url_prefix='/live-status')

@live_status_bp.route('/process-dashboard')
@login_required
def process_dashboard():
    """Live dashboard showing all job work processes with real-time status"""
    # Get all active job work processes
    processes = JobWorkProcess.query.join(JobWork).filter(
        JobWork.status.in_(['sent', 'partial_received'])
    ).order_by(JobWorkProcess.updated_at.desc()).all()
    
    # Calculate summary statistics
    stats = {
        'total_processes': len(processes),
        'pending': len([p for p in processes if p.status == 'pending']),
        'in_progress': len([p for p in processes if p.status == 'in_progress']),
        'completed': len([p for p in processes if p.status == 'completed']),
        'on_hold': len([p for p in processes if p.status == 'on_hold']),
        'delayed': len([p for p in processes if p.is_delayed])
    }
    
    return render_template('live_status/process_dashboard.html', 
                         processes=processes, stats=stats)

@live_status_bp.route('/wip-breakdown')
@login_required  
def wip_breakdown():
    """Show WIP breakdown by process across all items"""
    items = Item.query.all()
    
    # Calculate process totals
    process_totals = {
        'cutting': sum((item.qty_wip_cutting or 0) for item in items),
        'bending': sum((item.qty_wip_bending or 0) for item in items),
        'welding': sum((item.qty_wip_welding or 0) for item in items),
        'zinc': sum((item.qty_wip_zinc or 0) for item in items),
        'painting': sum((item.qty_wip_painting or 0) for item in items),
        'assembly': sum((item.qty_wip_assembly or 0) for item in items),
        'machining': sum((item.qty_wip_machining or 0) for item in items),
        'polishing': sum((item.qty_wip_polishing or 0) for item in items),
        'other': sum((item.qty_wip or 0) for item in items)
    }
    
    total_wip_items = len([item for item in items if item.total_wip > 0])
    
    return render_template('inventory/wip_breakdown.html',
                         items=items, 
                         process_totals=process_totals,
                         total_wip_items=total_wip_items)

@live_status_bp.route('/update-process-status', methods=['POST'])
@login_required
def update_process_status():
    """Update individual process status with tracking"""
    try:
        data = request.get_json()
        process_id = data.get('process_id')
        new_status = data.get('status')  
        reason = data.get('reason', '')
        
        if not process_id or not new_status:
            return jsonify({'success': False, 'message': 'Missing required fields'})
        
        process = JobWorkProcess.query.get(process_id)
        if not process:
            return jsonify({'success': False, 'message': 'Process not found'})
        
        # Update status with tracking
        old_status = process.status
        if process.update_status(new_status, current_user.id, reason):
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': f'Process status updated from {old_status} to {new_status}',
                'process': {
                    'id': process.id,
                    'status': process.status,
                    'status_badge_class': process.status_badge_class,
                    'time_in_status': str(process.time_in_current_status) if process.time_in_current_status else None,
                    'is_delayed': process.is_delayed
                }
            })
        else:
            return jsonify({'success': False, 'message': 'Failed to update status'})
            
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})

@live_status_bp.route('/batch-tracking')
@login_required
def batch_tracking():
    """Show batch/lot tracking across all items"""
    batches = ItemBatch.query.join(Item).order_by(ItemBatch.created_at.desc()).all()
    
    # Calculate summary statistics
    stats = {
        'total_batches': len(batches),
        'expired_batches': len([b for b in batches if b.is_expired]),
        'active_batches': len([b for b in batches if not b.is_expired and b.total_quantity > 0]),
        'total_batch_quantity': sum(b.total_quantity for b in batches)
    }
    
    return render_template('live_status/batch_tracking.html',
                         batches=batches, stats=stats)

@live_status_bp.route('/create-batch', methods=['POST'])
@login_required
def create_batch():
    """Create a new batch/lot for an item"""
    try:
        data = request.get_json()
        item_id = data.get('item_id')
        batch_number = data.get('batch_number')
        supplier_batch = data.get('supplier_batch', '')
        manufacture_date_str = data.get('manufacture_date')
        expiry_date_str = data.get('expiry_date')
        initial_quantity = float(data.get('initial_quantity', 0))
        
        if not item_id or not batch_number:
            return jsonify({'success': False, 'message': 'Missing required fields'})
        
        item = Item.query.get(item_id)
        if not item:
            return jsonify({'success': False, 'message': 'Item not found'})
        
        # Check for duplicate batch number
        existing_batch = ItemBatch.query.filter_by(
            item_id=item_id, batch_number=batch_number
        ).first()
        if existing_batch:
            return jsonify({'success': False, 'message': 'Batch number already exists for this item'})
        
        # Parse dates
        manufacture_date = None
        if manufacture_date_str:
            manufacture_date = datetime.strptime(manufacture_date_str, '%Y-%m-%d').date()
            
        expiry_date = None
        if expiry_date_str:
            expiry_date = datetime.strptime(expiry_date_str, '%Y-%m-%d').date()
        
        # Create new batch
        batch = ItemBatch(
            item_id=item_id,
            batch_number=batch_number,
            supplier_batch=supplier_batch,
            manufacture_date=manufacture_date,
            expiry_date=expiry_date,
            qty_raw=initial_quantity,
            created_by=current_user.id
        )
        
        db.session.add(batch)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Batch {batch_number} created successfully',
            'batch': {
                'id': batch.id,
                'batch_number': batch.batch_number,
                'total_quantity': batch.total_quantity,
                'is_expired': batch.is_expired
            }
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})

@live_status_bp.route('/api/process-status/<int:process_id>')
@login_required
def get_process_status(process_id):
    """Get real-time status of a specific process"""
    process = JobWorkProcess.query.get_or_404(process_id)
    
    # Parse status history
    status_history = []
    if process.status_history:
        try:
            status_history = json.loads(process.status_history)
        except (json.JSONDecodeError, TypeError):
            status_history = []
    
    return jsonify({
        'process_id': process.id,
        'process_name': process.process_name,
        'current_status': process.status,
        'status_badge_class': process.status_badge_class,
        'time_in_status': str(process.time_in_current_status) if process.time_in_current_status else None,
        'is_delayed': process.is_delayed,
        'completion_percentage': process.completion_percentage,
        'on_hold_reason': process.on_hold_reason,
        'status_history': status_history[-5:] if status_history else []  # Last 5 status changes
    })