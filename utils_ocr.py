"""
OCR Utilities - Helper functions for OCR operations
"""
import os
import mimetypes
from werkzeug.utils import secure_filename
from flask import current_app

def allowed_file(filename, allowed_extensions=None):
    """Check if file extension is allowed for OCR processing"""
    if allowed_extensions is None:
        allowed_extensions = {'pdf', 'png', 'jpg', 'jpeg', 'tiff', 'bmp'}
    
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions

def get_file_type_icon(file_type):
    """Get Font Awesome icon class for file type"""
    icons = {
        'pdf': 'fas fa-file-pdf text-danger',
        'jpg': 'fas fa-file-image text-success',
        'jpeg': 'fas fa-file-image text-success', 
        'png': 'fas fa-file-image text-success',
        'tiff': 'fas fa-file-image text-info',
        'bmp': 'fas fa-file-image text-info'
    }
    return icons.get(file_type.lower(), 'fas fa-file text-muted')

def format_confidence_score(confidence):
    """Format confidence score with appropriate styling"""
    if confidence >= 80:
        return f'<span class="badge bg-success">{confidence:.1f}%</span>'
    elif confidence >= 60:
        return f'<span class="badge bg-warning">{confidence:.1f}%</span>'
    else:
        return f'<span class="badge bg-danger">{confidence:.1f}%</span>'

def format_file_size(size_bytes):
    """Format file size in human readable format"""
    if size_bytes == 0:
        return "0B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f}{size_names[i]}"

def get_processing_status_badge(status):
    """Get Bootstrap badge class for processing status"""
    badges = {
        'pending': 'bg-secondary',
        'processing': 'bg-warning',
        'completed': 'bg-success', 
        'failed': 'bg-danger'
    }
    return badges.get(status, 'bg-secondary')

def clean_extracted_text(text):
    """Clean and normalize extracted OCR text"""
    if not text:
        return ""
    
    # Remove excessive whitespace
    import re
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    
    # Remove special characters that might cause issues
    text = re.sub(r'[^\w\s.,;:!?()-]', '', text)
    
    return text

def extract_invoice_number(text):
    """Extract invoice number from text using common patterns"""
    import re
    
    patterns = [
        r'invoice\s*(?:no|number|#)?[:\s]*([A-Z0-9\-/]+)',
        r'inv\s*(?:no|#)?[:\s]*([A-Z0-9\-/]+)',
        r'bill\s*(?:no|number|#)?[:\s]*([A-Z0-9\-/]+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text.lower())
        if match:
            return match.group(1).upper()
    
    return None

def extract_date(text):
    """Extract date from text using common formats"""
    import re
    from datetime import datetime
    
    # Common date patterns
    patterns = [
        r'(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})',
        r'(\d{1,2}\s+\w+\s+\d{2,4})',
        r'(\w+\s+\d{1,2},?\s+\d{2,4})'
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, text)
        for match in matches:
            try:
                # Try different date formats
                for fmt in ['%d/%m/%Y', '%m/%d/%Y', '%d-%m-%Y', '%m-%d-%Y', 
                           '%d %B %Y', '%B %d, %Y']:
                    try:
                        parsed_date = datetime.strptime(match, fmt)
                        return parsed_date.strftime('%Y-%m-%d')
                    except ValueError:
                        continue
            except:
                continue
    
    return None

def extract_amount(text):
    """Extract monetary amount from text"""
    import re
    
    # Look for currency symbols and numbers
    patterns = [
        r'₹\s*([0-9,]+\.?\d*)',
        r'rs\.?\s*([0-9,]+\.?\d*)',
        r'total[:\s]*₹?\s*([0-9,]+\.?\d*)',
        r'amount[:\s]*₹?\s*([0-9,]+\.?\d*)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text.lower())
        if match:
            amount_str = match.group(1).replace(',', '')
            try:
                return float(amount_str)
            except ValueError:
                continue
    
    return None

def validate_gstin(gstin):
    """Validate GSTIN format"""
    import re
    
    if not gstin:
        return False
    
    # GSTIN format: 2 digits + 5 letters + 4 digits + 1 letter + 1 alphanumeric + Z + 1 alphanumeric
    pattern = r'^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$'
    return bool(re.match(pattern, gstin.upper()))

def get_ocr_confidence_level(score):
    """Get confidence level description"""
    if score >= 80:
        return "High"
    elif score >= 60:
        return "Medium"
    else:
        return "Low"

def safe_filename(filename):
    """Generate safe filename for OCR uploads"""
    import time
    
    # Secure the filename
    filename = secure_filename(filename)
    
    # Add timestamp to prevent conflicts
    name, ext = os.path.splitext(filename)
    timestamp = str(int(time.time()))
    
    return f"{name}_{timestamp}{ext}"

def get_module_display_name(module_type):
    """Get display name for module type"""
    names = {
        'grn': 'GRN / Delivery Challan',
        'invoice': 'Invoice / Bill',
        'po': 'Purchase Order',
        'jobwork': 'Job Work Document',
        'production': 'Production Sheet',
        'general': 'General Document'
    }
    return names.get(module_type, module_type.title())

def estimate_processing_time(file_size_mb):
    """Estimate OCR processing time based on file size"""
    # Base time per MB (rough estimate)
    base_time_per_mb = 2.0  # seconds
    
    # Minimum processing time
    min_time = 1.0
    
    estimated = max(min_time, file_size_mb * base_time_per_mb)
    
    if estimated < 60:
        return f"{estimated:.0f} seconds"
    else:
        minutes = estimated / 60
        return f"{minutes:.1f} minutes"