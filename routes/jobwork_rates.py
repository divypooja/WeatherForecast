from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from forms_jobwork_rates import JobWorkRateForm
from models import JobWorkRate, Item
from app import db
from sqlalchemy import desc

jobwork_rates_bp = Blueprint('jobwork_rates', __name__)

@jobwork_rates_bp.route('/dashboard')
@login_required
def dashboard():
    # Statistics
    stats = {
        'total_rates': JobWorkRate.query.filter_by(is_active=True).count(),
        'total_items_with_rates': db.session.query(JobWorkRate.item_id).filter_by(is_active=True).distinct().count(),
        'avg_rate': db.session.query(db.func.avg(JobWorkRate.rate_per_unit)).filter_by(is_active=True).scalar() or 0,
        'inactive_rates': JobWorkRate.query.filter_by(is_active=False).count()
    }
    
    # Recent rates
    recent_rates = JobWorkRate.query.filter_by(is_active=True).order_by(desc(JobWorkRate.created_at)).limit(5).all()
    
    # Items without rates
    items_with_rates = db.session.query(JobWorkRate.item_id).filter_by(is_active=True).distinct().all()
    items_with_rates_ids = [rate[0] for rate in items_with_rates]
    items_without_rates = Item.query.filter(~Item.id.in_(items_with_rates_ids)).filter_by(is_active=True).limit(10).all()
    
    return render_template('jobwork_rates/dashboard.html', 
                         stats=stats, 
                         recent_rates=recent_rates,
                         items_without_rates=items_without_rates)

@jobwork_rates_bp.route('/list')
@login_required
def list_rates():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '', type=str)
    process_filter = request.args.get('process_filter', '', type=str)
    
    query = JobWorkRate.query.join(Item).filter(JobWorkRate.is_active == True)
    
    # Apply filters
    if search:
        query = query.filter(Item.name.contains(search) | Item.code.contains(search))
    
    if process_filter:
        if process_filter == 'none':
            query = query.filter(JobWorkRate.process_type.is_(None) | (JobWorkRate.process_type == ''))
        else:
            query = query.filter(JobWorkRate.process_type == process_filter)
    
    rates = query.order_by(Item.name).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('jobwork_rates/list.html', rates=rates, search=search, process_filter=process_filter)

@jobwork_rates_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_rate():
    form = JobWorkRateForm()
    
    if form.validate_on_submit():
        # Check if rate already exists for this item and process
        existing_rate = JobWorkRate.query.filter_by(
            item_id=form.item_id.data,
            process_type=form.process_type.data if form.process_type.data else None,
            is_active=True
        ).first()
        
        if existing_rate:
            flash('Rate already exists for this item and process combination', 'error')
            return render_template('jobwork_rates/form.html', form=form, title='Add Job Work Rate')
        
        rate = JobWorkRate(
            item_id=form.item_id.data,
            rate_per_unit=form.rate_per_unit.data,
            process_type=form.process_type.data if form.process_type.data else None,
            notes=form.notes.data,
            is_active=form.is_active.data
        )
        
        db.session.add(rate)
        db.session.commit()
        
        flash('Job work rate added successfully!', 'success')
        return redirect(url_for('jobwork_rates.list_rates'))
    
    return render_template('jobwork_rates/form.html', form=form, title='Add Job Work Rate')

@jobwork_rates_bp.route('/edit/<int:rate_id>', methods=['GET', 'POST'])
@login_required
def edit_rate(rate_id):
    rate = JobWorkRate.query.get_or_404(rate_id)
    form = JobWorkRateForm(obj=rate)
    
    if form.validate_on_submit():
        # Check if rate already exists for this item and process (excluding current rate)
        existing_rate = JobWorkRate.query.filter(
            JobWorkRate.id != rate_id,
            JobWorkRate.item_id == form.item_id.data,
            JobWorkRate.process_type == (form.process_type.data if form.process_type.data else None),
            JobWorkRate.is_active == True
        ).first()
        
        if existing_rate:
            flash('Rate already exists for this item and process combination', 'error')
            return render_template('jobwork_rates/form.html', form=form, title='Edit Job Work Rate', rate=rate)
        
        rate.item_id = form.item_id.data
        rate.rate_per_unit = form.rate_per_unit.data
        rate.process_type = form.process_type.data if form.process_type.data else None
        rate.notes = form.notes.data
        rate.is_active = form.is_active.data
        
        db.session.commit()
        
        flash('Job work rate updated successfully!', 'success')
        return redirect(url_for('jobwork_rates.list_rates'))
    
    return render_template('jobwork_rates/form.html', form=form, title='Edit Job Work Rate', rate=rate)

@jobwork_rates_bp.route('/delete/<int:rate_id>', methods=['POST'])
@login_required
def delete_rate(rate_id):
    rate = JobWorkRate.query.get_or_404(rate_id)
    rate.is_active = False  # Soft delete
    db.session.commit()
    
    flash('Job work rate deactivated successfully!', 'success')
    return redirect(url_for('jobwork_rates.list_rates'))

@jobwork_rates_bp.route('/api/get-rate/<int:item_id>')
@login_required
def get_item_rate(item_id):
    """API endpoint to get job work rate for an item"""
    process_type = request.args.get('process_type', '')
    
    # First try to find rate for specific process
    rate = None
    if process_type:
        rate = JobWorkRate.query.filter_by(
            item_id=item_id,
            process_type=process_type,
            is_active=True
        ).first()
    
    # If no process-specific rate found, try general rate
    if not rate:
        rate = JobWorkRate.query.filter_by(
            item_id=item_id,
            process_type=None,
            is_active=True
        ).first()
        
        # Also check for empty string process_type
        if not rate:
            rate = JobWorkRate.query.filter_by(
                item_id=item_id,
                process_type='',
                is_active=True
            ).first()
    
    if rate:
        return jsonify({
            'success': True,
            'rate': rate.rate_per_unit,
            'process_type': rate.process_type,
            'notes': rate.notes
        })
    else:
        return jsonify({
            'success': False,
            'message': 'No rate found for this item'
        })