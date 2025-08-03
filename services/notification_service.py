"""
Notification service for sending emails, WhatsApp messages, and SMS
"""
import os
from typing import List, Tuple, Optional

# Email service using SendGrid
try:
    from sendgrid import SendGridAPIClient
    from sendgrid.helpers.mail import Mail, Attachment, FileContent, FileName, FileType, Disposition
    import base64
    SENDGRID_AVAILABLE = True
except ImportError:
    SENDGRID_AVAILABLE = False

# SMS and WhatsApp service using Twilio
try:
    from twilio.rest import Client
    TWILIO_AVAILABLE = True
except ImportError:
    TWILIO_AVAILABLE = False

def send_email(to_email: str, subject: str, content: str, attachments: Optional[List[Tuple[str, str]]] = None) -> bool:
    """
    Send email with optional attachments
    
    Args:
        to_email: Recipient email address
        subject: Email subject
        content: Email content
        attachments: List of tuples (file_path, filename)
    
    Returns:
        bool: True if sent successfully, False otherwise
    """
    
    if not SENDGRID_AVAILABLE:
        print("SendGrid not available. Email not sent.")
        return False
    
    try:
        # Get SendGrid API key from environment
        api_key = os.environ.get('SENDGRID_API_KEY')
        if not api_key:
            print("SENDGRID_API_KEY not found in environment variables")
            return False
        
        # Create email
        from_email = os.environ.get('FROM_EMAIL', 'noreply@akinnovations.com')
        message = Mail(
            from_email=from_email,
            to_emails=to_email,
            subject=subject,
            html_content=content.replace('\n', '<br>')
        )
        
        # Add attachments if provided
        if attachments:
            for file_path, filename in attachments:
                try:
                    with open(file_path, 'rb') as f:
                        data = f.read()
                        encoded = base64.b64encode(data).decode()
                        
                        attachment = Attachment()
                        attachment.file_content = FileContent(encoded)
                        attachment.file_name = FileName(filename)
                        attachment.file_type = FileType('application/pdf')  # Default to PDF
                        attachment.disposition = Disposition('attachment')
                        
                        message.add_attachment(attachment)
                except Exception as e:
                    print(f"Error attaching file {file_path}: {e}")
        
        # Send email
        sg = SendGridAPIClient(api_key=api_key)
        response = sg.send(message)
        
        print(f"Email sent successfully. Status code: {response.status_code}")
        return True
        
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

def send_whatsapp(phone_number: str, message: str) -> bool:
    """
    Send WhatsApp message using Twilio
    
    Args:
        phone_number: Recipient phone number (with country code)
        message: Message content
    
    Returns:
        bool: True if sent successfully, False otherwise
    """
    
    if not TWILIO_AVAILABLE:
        print("Twilio not available. WhatsApp message not sent.")
        return False
    
    try:
        # Get Twilio credentials from environment
        account_sid = os.environ.get('TWILIO_ACCOUNT_SID')
        auth_token = os.environ.get('TWILIO_AUTH_TOKEN')
        whatsapp_number = os.environ.get('TWILIO_WHATSAPP_NUMBER')
        
        if not all([account_sid, auth_token, whatsapp_number]):
            print("Twilio credentials not found in environment variables")
            return False
        
        # Create Twilio client
        client = Client(account_sid, auth_token)
        
        # Ensure phone number has country code
        if not phone_number.startswith('+'):
            phone_number = '+91' + phone_number  # Default to India
        
        # Send WhatsApp message
        message = client.messages.create(
            body=message,
            from_=f'whatsapp:{whatsapp_number}',
            to=f'whatsapp:{phone_number}'
        )
        
        print(f"WhatsApp message sent successfully. SID: {message.sid}")
        return True
        
    except Exception as e:
        print(f"Error sending WhatsApp message: {e}")
        return False

def send_sms(phone_number: str, message: str) -> bool:
    """
    Send SMS using Twilio
    
    Args:
        phone_number: Recipient phone number (with country code)
        message: Message content
    
    Returns:
        bool: True if sent successfully, False otherwise
    """
    
    if not TWILIO_AVAILABLE:
        print("Twilio not available. SMS not sent.")
        return False
    
    try:
        # Get Twilio credentials from environment
        account_sid = os.environ.get('TWILIO_ACCOUNT_SID')
        auth_token = os.environ.get('TWILIO_AUTH_TOKEN')
        twilio_number = os.environ.get('TWILIO_PHONE_NUMBER')
        
        if not all([account_sid, auth_token, twilio_number]):
            print("Twilio credentials not found in environment variables")
            return False
        
        # Create Twilio client
        client = Client(account_sid, auth_token)
        
        # Ensure phone number has country code
        if not phone_number.startswith('+'):
            phone_number = '+91' + phone_number  # Default to India
        
        # Send SMS
        message = client.messages.create(
            body=message,
            from_=twilio_number,
            to=phone_number
        )
        
        print(f"SMS sent successfully. SID: {message.sid}")
        return True
        
    except Exception as e:
        print(f"Error sending SMS: {e}")
        return False

def send_notification(method: str, recipient: str, subject: str, content: str, attachments: Optional[List[Tuple[str, str]]] = None) -> bool:
    """
    Send notification using specified method
    
    Args:
        method: 'email', 'whatsapp', or 'sms'
        recipient: Recipient contact (email or phone)
        subject: Subject/title
        content: Message content
        attachments: List of attachments (for email only)
    
    Returns:
        bool: True if sent successfully, False otherwise
    """
    
    if method == 'email':
        return send_email(recipient, subject, content, attachments)
    elif method == 'whatsapp':
        return send_whatsapp(recipient, f"{subject}\n\n{content}")
    elif method == 'sms':
        # SMS content should be shorter
        sms_content = f"{subject}: {content[:100]}"  # Truncate for SMS
        return send_sms(recipient, sms_content)
    else:
        print(f"Unknown notification method: {method}")
        return False

# Test functions for development
def test_email():
    """Test email functionality"""
    return send_email(
        to_email="test@example.com",
        subject="Test Email",
        content="This is a test email from the Factory Management System."
    )

def test_whatsapp():
    """Test WhatsApp functionality"""
    return send_whatsapp(
        phone_number="+1234567890",
        message="Test WhatsApp message from Factory Management System."
    )

def test_sms():
    """Test SMS functionality"""
    return send_sms(
        phone_number="+1234567890",
        message="Test SMS from Factory Management System."
    )

if __name__ == "__main__":
    print("Testing notification services...")
    print(f"SendGrid available: {SENDGRID_AVAILABLE}")
    print(f"Twilio available: {TWILIO_AVAILABLE}")