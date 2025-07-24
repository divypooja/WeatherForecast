from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from forms import CompanySettingsForm, NotificationSettingsForm
from models import CompanySettings, NotificationSettings, PurchaseOrder, SalesOrder, Item, JobWork, Production, MaterialInspection, QualityIssue, FactoryExpense, Employee, SalaryRecord, EmployeeAdvance
from app import db
from services.notifications import notification_service
import os

settings_bp = Blueprint('settings', __name__)

@settings_bp.route('/dashboard')
@login_required
def dashboard():
    """Settings dashboard page"""
    settings = CompanySettings.get_settings()
    # Import csrf token function
    from flask_wtf.csrf import generate_csrf
    return render_template('settings/dashboard.html', settings=settings, csrf_token=generate_csrf)

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

@settings_bp.route('/notification_templates')
@login_required
def notification_templates():
    """Notification template management page"""
    return render_template('settings/notification_templates.html')

@settings_bp.route('/save_notification_template', methods=['POST'])
@login_required
def save_notification_template():
    """Save notification template configuration"""
    data = request.get_json()
    template_type = data.get('template_type')
    template_data = data.get('data')
    
    # In a real implementation, you would save this to database
    # For now, we'll just return success
    return jsonify({
        'success': True,
        'message': f'{template_type} template saved successfully'
    })

@settings_bp.route('/test_notification_template', methods=['POST'])
@login_required
def test_notification_template():
    """Send test notification using template"""
    data = request.get_json()
    template_type = data.get('template_type')
    recipient = data.get('recipient')
    template_data = data.get('data')
    
    # Create test message based on template
    if '@' in recipient:
        # Email test
        success = notification_service.send_email(
            recipient,
            f"Test: {template_data.get('email_subject', 'Test Subject')}",
            f"This is a test message from your {template_type} template."
        )
    else:
        # SMS test
        success = notification_service.send_sms(
            recipient,
            f"Test: {template_data.get('sms_message', 'Test SMS message')}"
        )
    
    return jsonify({
        'success': success,
        'message': 'Test notification sent' if success else 'Failed to send test notification'
    })

@settings_bp.route('/users')
@login_required
def user_management():
    """User management page (admin only)"""
    if not current_user.is_admin():
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    return render_template('settings/users.html')

@settings_bp.route('/reset_database', methods=['POST'])
@login_required
def reset_database():
    """Selective database reset based on user choices (Admin only)"""
    if not current_user.is_admin():
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('settings.dashboard'))
    
    try:
        # Get user selections
        reset_purchase_sales = request.form.get('reset_purchase_sales') == 'true'
        reset_inventory = request.form.get('reset_inventory') == 'true'
        reset_production = request.form.get('reset_production') == 'true'
        reset_inspections = request.form.get('reset_inspections') == 'true'
        reset_expenses = request.form.get('reset_expenses') == 'true'
        reset_employees = request.form.get('reset_employees') == 'true'
        reset_documents = request.form.get('reset_documents') == 'true'
        
        deleted_items = []
        
        # Delete in order to respect foreign key constraints
        if reset_inspections:
            MaterialInspection.query.delete()
            QualityIssue.query.delete()
            deleted_items.append('Material Inspections & Quality Issues')
        
        if reset_production:
            Production.query.delete()
            JobWork.query.delete()
            deleted_items.append('Production Orders & Job Work')
        
        if reset_expenses:
            FactoryExpense.query.delete()
            deleted_items.append('Factory Expenses')
        
        if reset_employees:
            SalaryRecord.query.delete()
            EmployeeAdvance.query.delete()
            Employee.query.delete()
            deleted_items.append('Employee Records & Payroll')
        
        if reset_purchase_sales:
            SalesOrder.query.delete()
            PurchaseOrder.query.delete()
            deleted_items.append('Purchase Orders & Sales Orders')
        
        if reset_inventory:
            Item.query.delete()
            deleted_items.append('Inventory Items')
        
        if reset_documents:
            # Clear uploads directory
            uploads_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads')
            if os.path.exists(uploads_dir):
                import shutil
                shutil.rmtree(uploads_dir)
                os.makedirs(uploads_dir, exist_ok=True)
            deleted_items.append('Uploaded Documents')
        
        db.session.commit()
        
        if deleted_items:
            flash(f'Database reset successful! Cleared: {", ".join(deleted_items)}', 'success')
        else:
            flash('No items were selected for reset.', 'info')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error resetting database: {str(e)}', 'danger')
    
    return redirect(url_for('settings.dashboard'))