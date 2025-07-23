from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from models import db, NotificationSettings, NotificationRecipient, NotificationLog
from forms import NotificationSettingsForm, NotificationRecipientForm
from services.notifications import notification_service, NotificationTemplates
import os

settings_bp = Blueprint('settings', __name__, url_prefix='/settings')

@settings_bp.route('/')
@login_required
def dashboard():
    """Settings dashboard"""
    if not current_user.is_admin():
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('main.dashboard'))
    
    notification_settings = NotificationSettings.query.first()
    recent_logs = NotificationLog.query.order_by(NotificationLog.sent_at.desc()).limit(10).all()
    
    stats = {
        'total_sent': NotificationLog.query.count(),
        'successful': NotificationLog.query.filter_by(success=True).count(),
        'failed': NotificationLog.query.filter_by(success=False).count(),
        'recipients': NotificationRecipient.query.filter_by(is_active=True).count()
    }
    
    return render_template('settings/dashboard.html', 
                         notification_settings=notification_settings,
                         recent_logs=recent_logs,
                         stats=stats)

@settings_bp.route('/notifications', methods=['GET', 'POST'])
@login_required
def notifications():
    """Notification settings management"""
    if not current_user.is_admin():
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('main.dashboard'))
    
    form = NotificationSettingsForm()
    settings = NotificationSettings.query.first()
    
    if request.method == 'GET' and settings:
        # Populate form with existing settings
        form.email_enabled.data = settings.email_enabled
        form.sendgrid_api_key.data = settings.sendgrid_api_key
        form.sender_email.data = settings.sender_email
        form.sender_name.data = settings.sender_name
        form.sms_enabled.data = settings.sms_enabled
        form.whatsapp_enabled.data = settings.whatsapp_enabled
        form.twilio_account_sid.data = settings.twilio_account_sid
        form.twilio_auth_token.data = settings.twilio_auth_token
        form.twilio_phone_number.data = settings.twilio_phone_number
        form.low_stock_notifications.data = settings.low_stock_notifications
        form.order_status_notifications.data = settings.order_status_notifications
        form.production_notifications.data = settings.production_notifications
        form.admin_email.data = settings.admin_email
        form.admin_phone.data = settings.admin_phone
    
    if form.validate_on_submit():
        try:
            if not settings:
                settings = NotificationSettings()
            
            # Update settings from form
            settings.email_enabled = form.email_enabled.data
            settings.sendgrid_api_key = form.sendgrid_api_key.data
            settings.sender_email = form.sender_email.data
            settings.sender_name = form.sender_name.data
            settings.sms_enabled = form.sms_enabled.data
            settings.whatsapp_enabled = form.whatsapp_enabled.data
            settings.twilio_account_sid = form.twilio_account_sid.data
            settings.twilio_auth_token = form.twilio_auth_token.data
            settings.twilio_phone_number = form.twilio_phone_number.data
            settings.low_stock_notifications = form.low_stock_notifications.data
            settings.order_status_notifications = form.order_status_notifications.data
            settings.production_notifications = form.production_notifications.data
            settings.admin_email = form.admin_email.data
            settings.admin_phone = form.admin_phone.data
            
            db.session.merge(settings)
            db.session.commit()
            
            # Update environment variables if provided
            if form.sendgrid_api_key.data:
                os.environ['SENDGRID_API_KEY'] = form.sendgrid_api_key.data
            if form.twilio_account_sid.data:
                os.environ['TWILIO_ACCOUNT_SID'] = form.twilio_account_sid.data
            if form.twilio_auth_token.data:
                os.environ['TWILIO_AUTH_TOKEN'] = form.twilio_auth_token.data
            if form.twilio_phone_number.data:
                os.environ['TWILIO_PHONE_NUMBER'] = form.twilio_phone_number.data
            
            # Reinitialize notification service with new credentials
            notification_service._initialize_clients()
            
            flash('Notification settings updated successfully!', 'success')
            return redirect(url_for('settings.notifications'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating settings: {str(e)}', 'error')
    
    return render_template('settings/notifications.html', form=form, settings=settings)

@settings_bp.route('/recipients')
@login_required
def recipients():
    """Manage notification recipients"""
    if not current_user.is_admin():
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('main.dashboard'))
    
    recipients = NotificationRecipient.query.order_by(NotificationRecipient.name).all()
    return render_template('settings/recipients.html', recipients=recipients)

@settings_bp.route('/recipients/add', methods=['GET', 'POST'])
@login_required
def add_recipient():
    """Add new notification recipient"""
    if not current_user.is_admin():
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('main.dashboard'))
    
    form = NotificationRecipientForm()
    
    if form.validate_on_submit():
        try:
            recipient = NotificationRecipient(
                name=form.name.data,
                email=form.email.data,
                phone=form.phone.data,
                notification_types=','.join(form.notification_types.data),
                event_types=','.join(form.event_types.data),
                is_active=form.is_active.data
            )
            
            db.session.add(recipient)
            db.session.commit()
            
            flash('Recipient added successfully!', 'success')
            return redirect(url_for('settings.recipients'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding recipient: {str(e)}', 'error')
    
    return render_template('settings/add_recipient.html', form=form)

@settings_bp.route('/recipients/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_recipient(id):
    """Edit notification recipient"""
    if not current_user.is_admin():
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('main.dashboard'))
    
    recipient = NotificationRecipient.query.get_or_404(id)
    form = NotificationRecipientForm(obj=recipient)
    
    if request.method == 'GET':
        # Populate multi-select fields
        if recipient.notification_types:
            form.notification_types.data = recipient.notification_types.split(',')
        if recipient.event_types:
            form.event_types.data = recipient.event_types.split(',')
    
    if form.validate_on_submit():
        try:
            recipient.name = form.name.data
            recipient.email = form.email.data
            recipient.phone = form.phone.data
            recipient.notification_types = ','.join(form.notification_types.data)
            recipient.event_types = ','.join(form.event_types.data)
            recipient.is_active = form.is_active.data
            
            db.session.commit()
            
            flash('Recipient updated successfully!', 'success')
            return redirect(url_for('settings.recipients'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating recipient: {str(e)}', 'error')
    
    return render_template('settings/edit_recipient.html', form=form, recipient=recipient)

@settings_bp.route('/recipients/<int:id>/delete', methods=['POST'])
@login_required
def delete_recipient(id):
    """Delete notification recipient"""
    if not current_user.is_admin():
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('main.dashboard'))
    
    recipient = NotificationRecipient.query.get_or_404(id)
    
    try:
        db.session.delete(recipient)
        db.session.commit()
        flash('Recipient deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting recipient: {str(e)}', 'error')
    
    return redirect(url_for('settings.recipients'))

@settings_bp.route('/test-notification', methods=['POST'])
@login_required
def test_notification():
    """Send test notification"""
    if not current_user.is_admin():
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    data = request.get_json()
    notification_type = data.get('type')
    recipient = data.get('recipient')
    
    if not notification_type or not recipient:
        return jsonify({'success': False, 'message': 'Missing required data'}), 400
    
    try:
        template = NotificationTemplates.low_stock_alert('Test Item', 5, 10)
        
        if notification_type == 'email':
            success = notification_service.send_email(
                recipient, 
                template['subject'], 
                template['message'], 
                template['html']
            )
        elif notification_type == 'sms':
            success = notification_service.send_sms(recipient, template['message'])
        elif notification_type == 'whatsapp':
            success = notification_service.send_whatsapp(recipient, template['message'])
        else:
            return jsonify({'success': False, 'message': 'Invalid notification type'}), 400
        
        if success:
            return jsonify({'success': True, 'message': f'Test {notification_type} sent successfully!'})
        else:
            return jsonify({'success': False, 'message': f'Failed to send test {notification_type}. Check your credentials.'})
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

@settings_bp.route('/logs')
@login_required
def notification_logs():
    """View notification logs"""
    if not current_user.is_admin():
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('main.dashboard'))
    
    page = request.args.get('page', 1, type=int)
    per_page = 50
    
    logs = NotificationLog.query.order_by(NotificationLog.sent_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('settings/logs.html', logs=logs)

@settings_bp.route('/clear-logs', methods=['POST'])
@login_required
def clear_logs():
    """Clear notification logs"""
    if not current_user.is_admin():
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    try:
        NotificationLog.query.delete()
        db.session.commit()
        return jsonify({'success': True, 'message': 'Logs cleared successfully!'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500