from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from forms import CompanySettingsForm
from models import CompanySettings
from app import db

settings_bp = Blueprint('settings', __name__)

@settings_bp.route('/dashboard')
@login_required
def dashboard():
    """Settings dashboard page"""
    settings = CompanySettings.get_settings()
    return render_template('settings/dashboard.html', settings=settings)

@settings_bp.route('/company', methods=['GET', 'POST'])
@login_required
def company_settings():
    """Company settings page for managing business information"""
    settings = CompanySettings.get_settings()
    form = CompanySettingsForm(obj=settings)
    
    if form.validate_on_submit():
        settings.company_name = form.company_name.data
        settings.address_line1 = form.address_line1.data
        settings.address_line2 = form.address_line2.data
        settings.city = form.city.data
        settings.state = form.state.data
        settings.pin_code = form.pin_code.data
        settings.phone = form.phone.data
        settings.email = form.email.data
        settings.gst_number = form.gst_number.data
        settings.arn_number = form.arn_number.data
        settings.website = form.website.data
        
        db.session.commit()
        flash('Company settings updated successfully', 'success')
        return redirect(url_for('settings.company_settings'))
    
    return render_template('settings/company.html', form=form, settings=settings)

@settings_bp.route('/notifications')
@login_required
def notification_settings():
    """Notification settings page"""
    return render_template('settings/notifications.html')

@settings_bp.route('/users')
@login_required
def user_management():
    """User management page (admin only)"""
    if not current_user.is_admin():
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    return render_template('settings/users.html')