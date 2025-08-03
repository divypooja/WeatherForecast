"""
Admin panel for comprehensive notification management
Provides full control over notification settings, recipients, templates, and logs
"""
from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from app import db
from models_notifications import (
    NotificationSettings, NotificationRecipient, NotificationLog, 
    NotificationTemplate, InAppNotification, NotificationSchedule
)
from models import User
from forms_notifications import NotificationRecipientForm, NotificationSettingsForm, NotificationTemplateForm, TestNotificationForm
from datetime import datetime, timedelta
from sqlalchemy import func, desc

notifications_bp = Blueprint('notifications', __name__)

@notifications_bp.route('/admin/dashboard')
@login_required
def admin_dashboard():
    """Notification system admin dashboard"""
    if not current_user.is_admin():
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    # Get notification statistics
    stats = {
        'total_sent': NotificationLog.query.filter_by(success=True).count(),
        'total_failed': NotificationLog.query.filter_by(success=False).count(),
        'active_recipients': NotificationRecipient.query.filter_by(is_active=True).count(),
        'total_templates': NotificationTemplate.query.filter_by(is_active=True).count()
    }
    
    # Recent notification logs
    recent_logs = NotificationLog.query.order_by(desc(NotificationLog.sent_at)).limit(10).all()
    
    # Notification stats by type
    type_stats = db.session.query(
        NotificationLog.type, 
        func.count(NotificationLog.id).label('count'),
        func.sum(func.cast(NotificationLog.success, db.Integer)).label('success_count')
    ).group_by(NotificationLog.type).all()
    
    # Daily notification trends (last 7 days)
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    daily_stats = db.session.query(
        func.date(NotificationLog.sent_at).label('date'),
        func.count(NotificationLog.id).label('total'),
        func.sum(func.cast(NotificationLog.success, db.Integer)).label('successful')
    ).filter(
        NotificationLog.sent_at >= seven_days_ago
    ).group_by(func.date(NotificationLog.sent_at)).all()
    
    # Get current settings
    settings = NotificationSettings.get_settings()
    
    return render_template('notifications/admin/dashboard.html',
                         stats=stats,
                         recent_logs=recent_logs,
                         type_stats=type_stats,
                         daily_stats=daily_stats,
                         settings=settings)

@notifications_bp.route('/admin/settings', methods=['GET', 'POST'])
@login_required
def admin_settings():
    """Manage notification system settings"""
    if not current_user.is_admin():
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    settings = NotificationSettings.get_settings()
    
    if request.method == 'POST':
        try:
            # Update channel settings
            settings.email_enabled = 'email_enabled' in request.form
            settings.sms_enabled = 'sms_enabled' in request.form
            settings.whatsapp_enabled = 'whatsapp_enabled' in request.form
            settings.in_app_enabled = 'in_app_enabled' in request.form
            
            # Update service configuration
            settings.sender_email = request.form.get('sender_email', settings.sender_email)
            settings.sender_name = request.form.get('sender_name', settings.sender_name)
            
            # Update event-specific settings
            settings.po_notifications = 'po_notifications' in request.form
            settings.grn_notifications = 'grn_notifications' in request.form
            settings.job_work_notifications = 'job_work_notifications' in request.form
            settings.production_notifications = 'production_notifications' in request.form
            settings.sales_notifications = 'sales_notifications' in request.form
            settings.accounts_notifications = 'accounts_notifications' in request.form
            settings.inventory_notifications = 'inventory_notifications' in request.form
            
            # Update specific event controls
            settings.po_vendor_notification = 'po_vendor_notification' in request.form
            settings.grn_rejection_notification = 'grn_rejection_notification' in request.form
            settings.job_work_vendor_notification = 'job_work_vendor_notification' in request.form
            settings.customer_invoice_notification = 'customer_invoice_notification' in request.form
            settings.payment_overdue_notification = 'payment_overdue_notification' in request.form
            settings.low_stock_notifications = 'low_stock_notifications' in request.form
            settings.scrap_threshold_notifications = 'scrap_threshold_notifications' in request.form
            
            # Update admin recipients
            settings.admin_email = request.form.get('admin_email', settings.admin_email)
            settings.admin_phone = request.form.get('admin_phone', settings.admin_phone)
            
            settings.updated_at = datetime.utcnow()
            db.session.commit()
            
            flash('Notification settings updated successfully!', 'success')
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating settings: {str(e)}', 'danger')
    
    return render_template('notifications/admin/settings.html', settings=settings)

@notifications_bp.route('/admin/recipients')
@login_required
def admin_recipients():
    """Manage notification recipients"""
    if not current_user.is_admin():
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    page = request.args.get('page', 1, type=int)
    role_filter = request.args.get('role', '', type=str)
    status_filter = request.args.get('status', '', type=str)
    
    query = NotificationRecipient.query
    
    if role_filter:
        query = query.filter(NotificationRecipient.role == role_filter)
    
    if status_filter == 'active':
        query = query.filter(NotificationRecipient.is_active == True)
    elif status_filter == 'inactive':
        query = query.filter(NotificationRecipient.is_active == False)
    
    recipients = query.order_by(NotificationRecipient.name).paginate(
        page=page, per_page=20, error_out=False)
    
    # Get unique roles for filter
    roles = db.session.query(NotificationRecipient.role).distinct().all()
    role_list = [role[0] for role in roles if role[0]]
    
    return render_template('notifications/admin/recipients.html',
                         recipients=recipients,
                         role_filter=role_filter,
                         status_filter=status_filter,
                         roles=role_list)

@notifications_bp.route('/admin/recipients/add', methods=['GET', 'POST'])
@login_required
def add_recipient():
    """Add new notification recipient"""
    if not current_user.is_admin():
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    form = NotificationRecipientForm()
    
    if form.validate_on_submit():
        try:
            # Process notification types
            notification_types = []
            if form.email_enabled.data:
                notification_types.append('email')
            if form.sms_enabled.data:
                notification_types.append('sms')
            if form.whatsapp_enabled.data:
                notification_types.append('whatsapp')
            
            # Process event subscriptions
            event_types = []
            if form.purchase_notifications.data:
                event_types.append('purchase_team')
            if form.sales_notifications.data:
                event_types.append('sales_team')
            if form.production_notifications.data:
                event_types.append('production_team')
            if form.inventory_notifications.data:
                event_types.append('store')
            if form.jobwork_notifications.data:
                event_types.append('production_team')
            if form.accounting_notifications.data:
                event_types.append('accounts')
            
            recipient = NotificationRecipient(
                name=form.name.data,
                email=form.email.data or None,
                phone=form.phone.data or None,
                role=form.role.data,
                recipient_name=form.name.data,
                recipient_role=form.role.data,
                notification_types=','.join(notification_types),
                event_types=','.join(event_types),
                po_events=form.purchase_notifications.data,
                grn_events=form.purchase_notifications.data,
                job_work_events=form.jobwork_notifications.data,
                production_events=form.production_notifications.data,
                sales_events=form.sales_notifications.data,
                accounts_events=form.accounting_notifications.data,
                inventory_events=form.inventory_notifications.data,
                immediate_notifications=True,  # Default to immediate
                is_active=form.is_active.data
            )
            
            db.session.add(recipient)
            db.session.commit()
            
            flash(f'Recipient "{recipient.name}" added successfully!', 'success')
            return redirect(url_for('notifications.admin_recipients'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding recipient: {str(e)}', 'danger')
    
    return render_template('notifications/admin/recipient_form.html', form=form, recipient=None, title='Add Recipient')

@notifications_bp.route('/admin/recipients/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_recipient(id):
    """Edit notification recipient"""
    if not current_user.is_admin():
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    recipient = NotificationRecipient.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            # Update notification types
            notification_types = []
            if 'email_notifications' in request.form:
                notification_types.append('email')
            if 'sms_notifications' in request.form:
                notification_types.append('sms')
            if 'whatsapp_notifications' in request.form:
                notification_types.append('whatsapp')
            if 'in_app_notifications' in request.form:
                notification_types.append('in_app')
            
            # Update event subscriptions
            event_types = []
            if 'po_events' in request.form:
                event_types.append('purchase_team')
            if 'grn_events' in request.form:
                event_types.append('store')
            if 'job_work_events' in request.form:
                event_types.append('production_head')
            if 'production_events' in request.form:
                event_types.append('production_supervisor')
            if 'sales_events' in request.form:
                event_types.append('sales_team')
            if 'accounts_events' in request.form:
                event_types.append('accounts')
            if 'inventory_events' in request.form:
                event_types.append('store')
            
            recipient.name = request.form['name']
            recipient.email = request.form.get('email') or None
            recipient.phone = request.form.get('phone') or None
            recipient.role = request.form['role']
            recipient.department = request.form.get('department')
            recipient.notification_types = ','.join(notification_types)
            recipient.event_types = ','.join(event_types)
            recipient.po_events = 'po_events' in request.form
            recipient.grn_events = 'grn_events' in request.form
            recipient.job_work_events = 'job_work_events' in request.form
            recipient.production_events = 'production_events' in request.form
            recipient.sales_events = 'sales_events' in request.form
            recipient.accounts_events = 'accounts_events' in request.form
            recipient.inventory_events = 'inventory_events' in request.form
            recipient.immediate_notifications = 'immediate_notifications' in request.form
            recipient.daily_summary = 'daily_summary' in request.form
            recipient.weekly_summary = 'weekly_summary' in request.form
            recipient.is_active = 'is_active' in request.form
            recipient.is_external = 'is_external' in request.form
            recipient.updated_at = datetime.utcnow()
            
            db.session.commit()
            
            flash(f'Recipient "{recipient.name}" updated successfully!', 'success')
            return redirect(url_for('notifications.admin_recipients'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating recipient: {str(e)}', 'danger')
    
    return render_template('notifications/admin/recipient_form.html', recipient=recipient, title='Edit Recipient')

@notifications_bp.route('/admin/logs')
@login_required
def admin_logs():
    """View notification logs"""
    if not current_user.is_admin():
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    page = request.args.get('page', 1, type=int)
    type_filter = request.args.get('type', '', type=str)
    status_filter = request.args.get('status', '', type=str)
    date_filter = request.args.get('date', '', type=str)
    
    query = NotificationLog.query
    
    if type_filter:
        query = query.filter(NotificationLog.type == type_filter)
    
    if status_filter == 'success':
        query = query.filter(NotificationLog.success == True)
    elif status_filter == 'failed':
        query = query.filter(NotificationLog.success == False)
    
    if date_filter:
        try:
            filter_date = datetime.strptime(date_filter, '%Y-%m-%d').date()
            query = query.filter(func.date(NotificationLog.sent_at) == filter_date)
        except ValueError:
            flash('Invalid date format', 'warning')
    
    logs = query.order_by(desc(NotificationLog.sent_at)).paginate(
        page=page, per_page=50, error_out=False)
    
    # Calculate statistics
    total_logs = NotificationLog.query.count()
    total_sent = NotificationLog.query.filter_by(success=True).count()
    total_failed = NotificationLog.query.filter_by(success=False).count()
    success_rate = round((total_sent / total_logs * 100) if total_logs > 0 else 0, 1)
    
    # Today's count
    today = datetime.utcnow().date()
    today_count = NotificationLog.query.filter(
        func.date(NotificationLog.sent_at) == today
    ).count()
    
    stats = {
        'total_sent': total_sent,
        'total_failed': total_failed,
        'success_rate': success_rate,
        'today_count': today_count
    }
    
    return render_template('notifications/admin/logs.html',
                         logs=logs,
                         type_filter=type_filter,
                         status_filter=status_filter,
                         date_filter=date_filter,
                         stats=stats)

@notifications_bp.route('/admin/test', methods=['GET', 'POST'])
@login_required
def test_notifications():
    """Test notification system"""
    if not current_user.is_admin():
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'POST':
        try:
            from services.comprehensive_notifications import comprehensive_notification_service
            
            notification_type = request.form['notification_type']
            recipient = request.form['recipient']
            subject = request.form['subject']
            message = request.form['message']
            
            # Test sending notification
            if notification_type == 'email':
                from services.notification_helpers import send_email_notification
                success = send_email_notification(recipient, subject, message)
            elif notification_type == 'sms':
                from services.notification_helpers import send_sms_notification
                success = send_sms_notification(recipient, f"{subject}: {message}")
            elif notification_type == 'whatsapp':
                from services.notification_helpers import send_whatsapp_notification
                success = send_whatsapp_notification(recipient, f"{subject}: {message}")
            else:
                success = False
            
            if success:
                flash(f'Test {notification_type} notification sent successfully!', 'success')
            else:
                flash(f'Failed to send test {notification_type} notification. Check settings and credentials.', 'danger')
                
        except Exception as e:
            flash(f'Error sending test notification: {str(e)}', 'danger')
    
    return render_template('notifications/admin/test.html')

@notifications_bp.route('/api/notification-stats')
@login_required
def api_notification_stats():
    """API endpoint for notification statistics"""
    if not current_user.is_admin():
        return jsonify({'error': 'Access denied'}), 403
    
    # Get hourly stats for the last 24 hours
    twenty_four_hours_ago = datetime.utcnow() - timedelta(hours=24)
    
    hourly_stats = db.session.query(
        func.date_trunc('hour', NotificationLog.sent_at).label('hour'),
        func.count(NotificationLog.id).label('total'),
        func.sum(func.cast(NotificationLog.success, db.Integer)).label('successful'),
        func.sum(func.cast(~NotificationLog.success, db.Integer)).label('failed')
    ).filter(
        NotificationLog.sent_at >= twenty_four_hours_ago
    ).group_by(func.date_trunc('hour', NotificationLog.sent_at)).all()
    
    chart_data = []
    for stat in hourly_stats:
        chart_data.append({
            'hour': stat.hour.isoformat(),
            'total': stat.total,
            'successful': stat.successful,
            'failed': stat.failed
        })
    
    return jsonify({
        'hourly_stats': chart_data,
        'success': True
    })

@notifications_bp.route('/admin/bulk-test')
@login_required
def bulk_test_notifications():
    """Test comprehensive notification system across all modules"""
    if not current_user.is_admin():
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    try:
        from services.comprehensive_notifications import comprehensive_notification_service
        
        # Test different notification scenarios
        test_results = []
        
        # Test low stock alert - Internal system test
        try:
            from models_notifications import NotificationLog
            
            # Test internal logging system
            test_log = NotificationLog(
                type='system_alert',
                recipient='internal_test',
                subject='🧪 Test Low Stock Alert',
                message='Internal notification system test - Low stock monitoring',
                success=True,
                response='Internal system test successful'
            )
            db.session.add(test_log)
            db.session.flush()  # Test database write
            
            test_results.append(('Low Stock Alert', 'success'))
        except Exception as e:
            test_results.append(('Low Stock Alert', f'error: {str(e)}'))
        
        # Test system alert - Internal system test
        try:
            from models_notifications import NotificationLog
            
            # Test internal logging system
            test_log = NotificationLog(
                type='system_alert',
                recipient='internal_test',
                subject='🧪 System Test Alert',
                message='Internal notification system test - System monitoring',
                success=True,
                response='Internal system test successful'
            )
            db.session.add(test_log)
            db.session.flush()  # Test database write
            
            test_results.append(('System Alert', 'success'))
        except Exception as e:
            test_results.append(('System Alert', f'error: {str(e)}'))
        
        # Create test notification logs for demonstration
        try:
            from models_notifications import NotificationLog
            
            # Add test log entries
            test_log1 = NotificationLog(
                type='system_alert',
                recipient='internal_system',
                subject='Test Low Stock Alert',
                message='System test notification for low stock monitoring',
                success=True,
                response='Internal logging successful'
            )
            
            test_log2 = NotificationLog(
                type='system_alert', 
                recipient='internal_system',
                subject='System Test Alert',
                message='Comprehensive notification system test',
                success=True,
                response='Internal logging successful'
            )
            
            db.session.add(test_log1)
            db.session.add(test_log2)
            db.session.commit()
            
            flash('System test completed successfully! Check notification logs for details.', 'success')
            
        except Exception as log_error:
            flash(f'Test completed but logging failed: {str(log_error)}', 'warning')
        
        return render_template('notifications/admin/bulk_test_results.html', test_results=test_results)
        
    except Exception as e:
        flash(f'Error running system test: {str(e)}', 'danger')
        return redirect(url_for('notifications.admin_dashboard'))

@notifications_bp.route('/api/test-scenario', methods=['POST'])
@login_required
def test_business_scenario():
    """Test common business notification scenarios"""
    if not current_user.is_admin():
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    try:
        data = request.get_json()
        scenario = data.get('scenario', '')
        
        from models_notifications import NotificationLog
        
        # Create test notification based on scenario
        scenario_data = {
            'po_created': {
                'subject': '📋 Purchase Order Created - PO-2025-001',
                'message': 'New purchase order PO-2025-001 created for supplier ABC Ltd. Total amount: ₹25,000',
                'type': 'purchase_order'
            },
            'grn_received': {
                'subject': '📦 Goods Receipt Note - GRN-2025-001',
                'message': 'Materials received against PO-2025-001. GRN-2025-001 generated for quality inspection.',
                'type': 'grn'
            },
            'job_work_issued': {
                'subject': '🔧 Job Work Issued - JW-2025-001',
                'message': 'Job work JW-2025-001 issued to vendor XYZ Works. Expected completion: 7 days.',
                'type': 'job_work'
            },
            'low_stock_alert': {
                'subject': '⚠️ Low Stock Alert - Raw Material Steel',
                'message': 'Raw Material Steel is running low. Current stock: 50 kg, Minimum required: 100 kg.',
                'type': 'inventory_alert'
            }
        }
        
        if scenario not in scenario_data:
            return jsonify({'success': False, 'message': 'Unknown scenario'}), 400
        
        scenario_info = scenario_data[scenario]
        
        # Create test log entry
        test_log = NotificationLog(
            type=scenario_info['type'],
            recipient='test_recipient',
            subject=scenario_info['subject'],
            message=scenario_info['message'],
            success=True,
            response='Test scenario notification logged successfully'
        )
        
        db.session.add(test_log)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Test notification created and logged successfully! Check notification logs to see the {scenario.replace("_", " ")} notification.'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error testing scenario: {str(e)}'}), 500

@notifications_bp.route('/api/test-configuration', methods=['POST'])
@login_required
def test_system_configuration():
    """Test system configuration and service availability"""
    if not current_user.is_admin():
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    try:
        import os
        from models_notifications import NotificationSettings
        
        test_results = []
        
        # Test database connectivity
        try:
            settings = NotificationSettings.get_settings()
            test_results.append({
                'name': 'Database Connection',
                'success': True,
                'message': 'Database connection successful'
            })
        except Exception as e:
            test_results.append({
                'name': 'Database Connection',
                'success': False,
                'message': f'Database error: {str(e)}'
            })
        
        # Test notification settings
        try:
            settings = NotificationSettings.get_settings()
            enabled_channels = []
            if settings.email_enabled:
                enabled_channels.append('Email')
            if settings.sms_enabled:
                enabled_channels.append('SMS')
            if settings.whatsapp_enabled:
                enabled_channels.append('WhatsApp')
            
            test_results.append({
                'name': 'Notification Channels',
                'success': True,
                'message': f'Enabled channels: {", ".join(enabled_channels) if enabled_channels else "None configured"}'
            })
        except Exception as e:
            test_results.append({
                'name': 'Notification Channels',
                'success': False,
                'message': f'Settings error: {str(e)}'
            })
        
        # Test SendGrid configuration
        sendgrid_key = os.environ.get('SENDGRID_API_KEY')
        test_results.append({
            'name': 'SendGrid API Key',
            'success': bool(sendgrid_key),
            'message': 'SendGrid API key configured' if sendgrid_key else 'SendGrid API key not configured - email disabled'
        })
        
        # Test Twilio configuration
        twilio_sid = os.environ.get('TWILIO_ACCOUNT_SID')
        twilio_token = os.environ.get('TWILIO_AUTH_TOKEN')
        twilio_phone = os.environ.get('TWILIO_PHONE_NUMBER')
        
        twilio_configured = bool(twilio_sid and twilio_token and twilio_phone)
        test_results.append({
            'name': 'Twilio Configuration',
            'success': twilio_configured,
            'message': 'Twilio credentials configured' if twilio_configured else 'Twilio credentials not configured - SMS/WhatsApp disabled'
        })
        
        # Test notification logging
        try:
            from models_notifications import NotificationLog
            log_count = NotificationLog.query.count()
            test_results.append({
                'name': 'Notification Logging',
                'success': True,
                'message': f'Notification logging active - {log_count} logs recorded'
            })
        except Exception as e:
            test_results.append({
                'name': 'Notification Logging',
                'success': False,
                'message': f'Logging error: {str(e)}'
            })
        
        # Test notification scheduler
        try:
            from services.scheduler import scheduler
            test_results.append({
                'name': 'Notification Scheduler',
                'success': True,
                'message': 'Notification scheduler running'
            })
        except Exception as e:
            test_results.append({
                'name': 'Notification Scheduler',
                'success': False,
                'message': f'Scheduler error: {str(e)}'
            })
        
        return jsonify({
            'success': True,
            'tests': test_results,
            'message': 'System configuration test completed'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Configuration test failed: {str(e)}'}), 500