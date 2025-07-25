from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import db, OvertimeRate
from forms import OvertimeRateForm

overtime_bp = Blueprint('overtime', __name__, url_prefix='/overtime')

@overtime_bp.route('/')
@login_required
def overtime_dashboard():
    """Overtime rates dashboard"""
    if not current_user.is_admin():
        flash('Admin access required', 'danger')
        return redirect(url_for('main.dashboard'))
    
    # Get all overtime rates
    rates = OvertimeRate.query.order_by(OvertimeRate.salary_type).all()
    
    # Calculate statistics
    total_rates = len(rates)
    active_rates = len([r for r in rates if r.is_active])
    avg_rate = sum([r.rate_per_hour for r in rates if r.is_active]) / active_rates if active_rates > 0 else 0
    
    return render_template('overtime/dashboard.html',
                         rates=rates,
                         total_rates=total_rates,
                         active_rates=active_rates,
                         avg_rate=avg_rate)

@overtime_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_overtime_rate():
    """Add new overtime rate"""
    if not current_user.is_admin():
        flash('Admin access required', 'danger')
        return redirect(url_for('main.dashboard'))
    
    form = OvertimeRateForm()
    
    if form.validate_on_submit():
        try:
            # Check if rate already exists for this salary type
            existing = OvertimeRate.query.filter_by(
                salary_type=form.salary_type.data,
                is_active=True
            ).first()
            
            if existing:
                flash(f'Active overtime rate already exists for {form.salary_type.data.replace("_", " ").title()} employees', 'warning')
                return render_template('overtime/form.html', form=form, title='Add Overtime Rate')
            
            rate = OvertimeRate(
                salary_type=form.salary_type.data,
                rate_per_hour=form.rate_per_hour.data,
                is_active=form.is_active.data
            )
            
            db.session.add(rate)
            db.session.commit()
            
            flash(f'Overtime rate for {form.salary_type.data.replace("_", " ").title()} employees added successfully!', 'success')
            return redirect(url_for('overtime.overtime_dashboard'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding overtime rate: {str(e)}', 'danger')
    
    return render_template('overtime/form.html', form=form, title='Add Overtime Rate')

@overtime_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_overtime_rate(id):
    """Edit overtime rate"""
    if not current_user.is_admin():
        flash('Admin access required', 'danger')
        return redirect(url_for('main.dashboard'))
    
    rate = OvertimeRate.query.get_or_404(id)
    form = OvertimeRateForm(obj=rate)
    
    if form.validate_on_submit():
        try:
            # Check if another active rate exists for this salary type (excluding current)
            existing = OvertimeRate.query.filter(
                OvertimeRate.salary_type == form.salary_type.data,
                OvertimeRate.is_active == True,
                OvertimeRate.id != id
            ).first()
            
            if existing and form.is_active.data:
                flash(f'Another active overtime rate already exists for {form.salary_type.data.replace("_", " ").title()} employees', 'warning')
                return render_template('overtime/form.html', form=form, rate=rate, title='Edit Overtime Rate')
            
            rate.salary_type = form.salary_type.data
            rate.rate_per_hour = form.rate_per_hour.data
            rate.is_active = form.is_active.data
            
            db.session.commit()
            
            flash(f'Overtime rate updated successfully!', 'success')
            return redirect(url_for('overtime.overtime_dashboard'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating overtime rate: {str(e)}', 'danger')
    
    return render_template('overtime/form.html', form=form, rate=rate, title='Edit Overtime Rate')

@overtime_bp.route('/delete/<int:id>')
@login_required
def delete_overtime_rate(id):
    """Delete overtime rate"""
    if not current_user.is_admin():
        flash('Admin access required', 'danger')
        return redirect(url_for('main.dashboard'))
    
    rate = OvertimeRate.query.get_or_404(id)
    
    try:
        db.session.delete(rate)
        db.session.commit()
        flash('Overtime rate deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting overtime rate: {str(e)}', 'danger')
    
    return redirect(url_for('overtime.overtime_dashboard'))

@overtime_bp.route('/toggle/<int:id>')
@login_required
def toggle_overtime_rate(id):
    """Toggle overtime rate active status"""
    if not current_user.is_admin():
        flash('Admin access required', 'danger')
        return redirect(url_for('main.dashboard'))
    
    rate = OvertimeRate.query.get_or_404(id)
    
    try:
        # If activating, check for existing active rate
        if not rate.is_active:
            existing = OvertimeRate.query.filter(
                OvertimeRate.salary_type == rate.salary_type,
                OvertimeRate.is_active == True,
                OvertimeRate.id != id
            ).first()
            
            if existing:
                flash(f'Another active overtime rate already exists for {rate.salary_type.replace("_", " ").title()} employees', 'warning')
                return redirect(url_for('overtime.overtime_dashboard'))
        
        rate.is_active = not rate.is_active
        db.session.commit()
        
        status = 'activated' if rate.is_active else 'deactivated'
        flash(f'Overtime rate {status} successfully!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating overtime rate: {str(e)}', 'danger')
    
    return redirect(url_for('overtime.overtime_dashboard'))