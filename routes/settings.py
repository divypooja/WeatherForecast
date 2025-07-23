from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from forms import CompanySettingsForm, NotificationSettingsForm
from models import CompanySettings, NotificationSettings
from app import db
from services.notifications import notification_service

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

@settings_bp.route('/notifications', methods=['GET', 'POST'])
@login_required
def notification_settings():
    """Notification settings page"""
    # Get or create notification settings
    settings = NotificationSettings.query.first()
    if not settings:
        settings = NotificationSettings()
        db.session.add(settings)
        db.session.commit()
    
    form = NotificationSettingsForm(obj=settings)
    
    if form.validate_on_submit():
        # Update settings from form
        form.populate_obj(settings)
        db.session.commit()
        flash('Notification settings updated successfully!', 'success')
        return redirect(url_for('settings.notification_settings'))
    
    return render_template('settings/notifications.html', form=form, settings=settings)

@settings_bp.route('/test_notification', methods=['POST'])
@login_required
def test_notification():
    """Test notification endpoints"""
    data = request.get_json()
    notification_type = data.get('type')
    recipient = data.get('recipient')
    
    if notification_type == 'email':
        success = notification_service.send_email(
            recipient, 
            "Test Email from AK Factory", 
            "This is a test email to verify your email notification settings."
        )
    elif notification_type == 'sms':
        success = notification_service.send_sms(
            recipient, 
            "Test SMS from AK Factory: Your SMS notifications are working correctly!"
        )
    elif notification_type == 'whatsapp':
        success = notification_service.send_whatsapp(
            recipient, 
            "Test WhatsApp from AK Factory: Your WhatsApp notifications are working correctly!"
        )
    else:
        return jsonify({'success': False, 'message': 'Invalid notification type'})
    
    return jsonify({
        'success': success,
        'message': f'Test {notification_type} sent successfully!' if success else f'Failed to send test {notification_type}'
    })

@settings_bp.route('/users')
@login_required
def user_management():
    """User management page (admin only)"""
    if not current_user.is_admin():
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    return render_template('settings/users.html')