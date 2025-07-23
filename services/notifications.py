import os
import logging
from typing import Optional, List, Dict, Any
from enum import Enum
from datetime import datetime
from twilio.rest import Client
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content
from app import db

logger = logging.getLogger(__name__)

class NotificationType(Enum):
    EMAIL = "email"
    SMS = "sms"
    WHATSAPP = "whatsapp"

class NotificationService:
    def __init__(self):
        self.sendgrid_client = None
        self.twilio_client = None
        self._initialize_clients()
    
    def _initialize_clients(self):
        """Initialize API clients if credentials are available"""
        try:
            sendgrid_key = os.environ.get('SENDGRID_API_KEY')
            if sendgrid_key:
                self.sendgrid_client = SendGridAPIClient(sendgrid_key)
                
            twilio_sid = os.environ.get('TWILIO_ACCOUNT_SID')
            twilio_token = os.environ.get('TWILIO_AUTH_TOKEN')
            if twilio_sid and twilio_token:
                self.twilio_client = Client(twilio_sid, twilio_token)
        except Exception as e:
            logger.error(f"Error initializing notification clients: {e}")
    
    def send_email(self, to_email: str, subject: str, content: str, html_content: str = None) -> bool:
        """Send email notification"""
        if not self.sendgrid_client:
            logger.warning("SendGrid client not initialized - check SENDGRID_API_KEY")
            return False
        
        try:
            from_email = Email("noreply@akfactory.com", "AK Innovations Factory")
            to_email_obj = To(to_email)
            
            message = Mail(
                from_email=from_email,
                to_emails=to_email_obj,
                subject=subject,
                plain_text_content=content,
                html_content=html_content or content
            )
            
            response = self.sendgrid_client.send(message)
            success = response.status_code in [200, 201, 202]
            
            self._log_notification(NotificationType.EMAIL, to_email, subject, success, response.status_code)
            return success
            
        except Exception as e:
            logger.error(f"Email sending failed: {e}")
            self._log_notification(NotificationType.EMAIL, to_email, subject, False, str(e))
            return False
    
    def send_email_with_attachment(self, to_email: str, subject: str, content: str, attachment: dict, html_content: str = None) -> bool:
        """Send email notification with attachment"""
        if not self.sendgrid_client:
            logger.warning("SendGrid client not initialized - check SENDGRID_API_KEY")
            return False
        
        try:
            from sendgrid.helpers.mail import Mail, Email, To, Content, Attachment
            import base64
            
            from_email = Email("noreply@akfactory.com", "AK Innovations Factory")
            to_email_obj = To(to_email)
            
            message = Mail(
                from_email=from_email,
                to_emails=to_email_obj,
                subject=subject,
                plain_text_content=content,
                html_content=html_content or content
            )
            
            # Add attachment
            attached_file = Attachment()
            attached_file.content = attachment['content']
            attached_file.type = attachment['type']
            attached_file.filename = attachment['filename']
            attached_file.disposition = attachment['disposition']
            message.attachment = attached_file
            
            response = self.sendgrid_client.send(message)
            success = response.status_code in [200, 201, 202]
            
            self._log_notification(NotificationType.EMAIL, to_email, f"{subject} (with attachment)", success, response.status_code)
            return success
            
        except Exception as e:
            logger.error(f"Email with attachment sending failed: {e}")
            self._log_notification(NotificationType.EMAIL, to_email, f"{subject} (with attachment)", False, str(e))
            return False
    
    def send_sms(self, to_phone: str, message: str) -> bool:
        """Send SMS notification"""
        if not self.twilio_client:
            logger.warning("Twilio client not initialized - check credentials")
            return False
        
        try:
            from_phone = os.environ.get('TWILIO_PHONE_NUMBER')
            if not from_phone:
                logger.error("TWILIO_PHONE_NUMBER not configured")
                return False
            
            message_obj = self.twilio_client.messages.create(
                body=message,
                from_=from_phone,
                to=to_phone
            )
            
            success = message_obj.status in ['queued', 'sent', 'delivered']
            self._log_notification(NotificationType.SMS, to_phone, message[:50] + "...", success, message_obj.sid)
            return success
            
        except Exception as e:
            logger.error(f"SMS sending failed: {e}")
            self._log_notification(NotificationType.SMS, to_phone, message[:50] + "...", False, str(e))
            return False
    
    def send_whatsapp(self, to_phone: str, message: str) -> bool:
        """Send WhatsApp notification via Twilio"""
        if not self.twilio_client:
            logger.warning("Twilio client not initialized - check credentials")
            return False
        
        try:
            from_phone = os.environ.get('TWILIO_PHONE_NUMBER')
            if not from_phone:
                logger.error("TWILIO_PHONE_NUMBER not configured")
                return False
            
            # WhatsApp requires 'whatsapp:' prefix
            whatsapp_from = f"whatsapp:{from_phone}"
            whatsapp_to = f"whatsapp:{to_phone}"
            
            message_obj = self.twilio_client.messages.create(
                body=message,
                from_=whatsapp_from,
                to=whatsapp_to
            )
            
            success = message_obj.status in ['queued', 'sent', 'delivered']
            self._log_notification(NotificationType.WHATSAPP, to_phone, message[:50] + "...", success, message_obj.sid)
            return success
            
        except Exception as e:
            logger.error(f"WhatsApp sending failed: {e}")
            self._log_notification(NotificationType.WHATSAPP, to_phone, message[:50] + "...", False, str(e))
            return False
    
    def send_notification(self, notification_type: NotificationType, recipient: str, 
                         subject: str, message: str, html_content: str = None) -> bool:
        """Send notification based on type"""
        if notification_type == NotificationType.EMAIL:
            return self.send_email(recipient, subject, message, html_content)
        elif notification_type == NotificationType.SMS:
            return self.send_sms(recipient, message)
        elif notification_type == NotificationType.WHATSAPP:
            return self.send_whatsapp(recipient, message)
        else:
            logger.error(f"Unknown notification type: {notification_type}")
            return False
    
    def send_multi_channel_notification(self, recipients: Dict[str, List[str]], 
                                      subject: str, message: str, html_content: str = None) -> Dict[str, bool]:
        """Send notification to multiple channels"""
        results = {}
        
        for channel, recipient_list in recipients.items():
            channel_results = []
            notification_type = NotificationType(channel)
            
            for recipient in recipient_list:
                success = self.send_notification(notification_type, recipient, subject, message, html_content)
                channel_results.append(success)
            
            results[channel] = all(channel_results)
        
        return results
    
    def _log_notification(self, notification_type: NotificationType, recipient: str, 
                         subject: str, success: bool, response: str):
        """Log notification attempt to database"""
        try:
            from models import NotificationLog
            log_entry = NotificationLog(
                type=notification_type.value,
                recipient=recipient,
                subject=subject,
                success=success,
                response=str(response),
                sent_at=datetime.utcnow()
            )
            db.session.add(log_entry)
            db.session.commit()
        except Exception as e:
            logger.error(f"Failed to log notification: {e}")
    
    def get_notification_settings(self):
        """Get current notification settings"""
        try:
            from models import NotificationSettings
            return NotificationSettings.query.first()
        except Exception as e:
            logger.error(f"Failed to get notification settings: {e}")
            return None
    
    def update_notification_settings(self, settings_data: Dict[str, Any]) -> bool:
        """Update notification settings"""
        try:
            from models import NotificationSettings
            settings = NotificationSettings.query.first()
            if not settings:
                settings = NotificationSettings()
            
            for key, value in settings_data.items():
                if hasattr(settings, key):
                    setattr(settings, key, value)
            
            db.session.merge(settings)
            db.session.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to update notification settings: {e}")
            return False

# Global notification service instance
notification_service = NotificationService()

# Notification templates for different events
class NotificationTemplates:
    @staticmethod
    def low_stock_alert(item_name: str, current_stock: int, minimum_stock: int) -> Dict[str, str]:
        return {
            'subject': f'🚨 Low Stock Alert: {item_name}',
            'message': f'Low stock alert for {item_name}. Current stock: {current_stock}, Minimum required: {minimum_stock}. Please reorder immediately.',
            'html': f'''
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <h2 style="color: #dc3545;">🚨 Low Stock Alert</h2>
                <div style="background: #f8f9fa; padding: 20px; border-radius: 5px; margin: 20px 0;">
                    <h3>{item_name}</h3>
                    <p><strong>Current Stock:</strong> {current_stock}</p>
                    <p><strong>Minimum Required:</strong> {minimum_stock}</p>
                    <p style="color: #dc3545;"><strong>Action Required:</strong> Please reorder immediately</p>
                </div>
                <p>Best regards,<br>AK Innovations Factory Management System</p>
            </div>
            '''
        }
    
    @staticmethod
    def order_status_update(order_type: str, order_id: str, status: str) -> Dict[str, str]:
        return {
            'subject': f'📋 {order_type} Order #{order_id} - Status Update',
            'message': f'Your {order_type} order #{order_id} status has been updated to: {status}',
            'html': f'''
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <h2 style="color: #28a745;">📋 Order Status Update</h2>
                <div style="background: #f8f9fa; padding: 20px; border-radius: 5px; margin: 20px 0;">
                    <h3>{order_type} Order #{order_id}</h3>
                    <p><strong>New Status:</strong> <span style="color: #28a745;">{status}</span></p>
                </div>
                <p>Best regards,<br>AK Innovations Factory Management System</p>
            </div>
            '''
        }
    
    @staticmethod
    def production_complete(production_id: str, item_name: str, quantity: int) -> Dict[str, str]:
        return {
            'subject': f'✅ Production Complete: {item_name}',
            'message': f'Production #{production_id} completed successfully. {quantity} units of {item_name} have been produced.',
            'html': f'''
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <h2 style="color: #28a745;">✅ Production Complete</h2>
                <div style="background: #f8f9fa; padding: 20px; border-radius: 5px; margin: 20px 0;">
                    <h3>Production #{production_id}</h3>
                    <p><strong>Item:</strong> {item_name}</p>
                    <p><strong>Quantity Produced:</strong> {quantity} units</p>
                </div>
                <p>Best regards,<br>AK Innovations Factory Management System</p>
            </div>
            '''
        }