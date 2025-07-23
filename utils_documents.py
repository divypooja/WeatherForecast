import os
import uuid
from werkzeug.utils import secure_filename
from flask import current_app
from models import Document, db
from flask_login import current_user

def allowed_file(filename):
    """Check if file extension is allowed"""
    ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'jpg', 'jpeg', 'png', 'xls', 'xlsx', 'txt'}
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_uploaded_file(file, transaction_type, transaction_id, document_category, description=None):
    """
    Save an uploaded file and create database record
    
    Args:
        file: FileStorage object from form
        transaction_type: Type of transaction (purchase_order, sales_order, etc.)
        transaction_id: ID of the transaction
        document_category: Category of document
        description: Optional description
    
    Returns:
        Document object if successful, None if failed
    """
    if file and allowed_file(file.filename):
        # Generate unique filename
        file_ext = file.filename.rsplit('.', 1)[1].lower()
        unique_filename = f"{uuid.uuid4().hex}.{file_ext}"
        
        # Create upload directory structure
        upload_dir = os.path.join('uploads', transaction_type, str(transaction_id))
        os.makedirs(upload_dir, exist_ok=True)
        
        # Save file
        file_path = os.path.join(upload_dir, unique_filename)
        file.save(file_path)
        
        # Get file info
        file_size = os.path.getsize(file_path)
        
        # Create database record
        document = Document(
            filename=unique_filename,
            original_filename=secure_filename(file.filename),
            file_size=file_size,
            file_type=file_ext,
            upload_path=os.path.join(transaction_type, str(transaction_id), unique_filename),
            transaction_type=transaction_type,
            transaction_id=transaction_id,
            document_category=document_category,
            description=description,
            uploaded_by=current_user.id
        )
        
        db.session.add(document)
        db.session.commit()
        
        return document
    
    return None

def get_documents_for_transaction(transaction_type, transaction_id):
    """Get all documents for a specific transaction"""
    return Document.query.filter_by(
        transaction_type=transaction_type,
        transaction_id=transaction_id,
        is_active=True
    ).order_by(Document.uploaded_at.desc()).all()

def delete_document(document_id):
    """Soft delete a document"""
    document = Document.query.get(document_id)
    if document:
        document.is_active = False
        db.session.commit()
        return True
    return False

def get_file_icon(file_type):
    """Get appropriate icon for file type"""
    icons = {
        'pdf': 'fas fa-file-pdf text-danger',
        'doc': 'fas fa-file-word text-primary',
        'docx': 'fas fa-file-word text-primary',
        'xls': 'fas fa-file-excel text-success',
        'xlsx': 'fas fa-file-excel text-success',
        'jpg': 'fas fa-file-image text-warning',
        'jpeg': 'fas fa-file-image text-warning',
        'png': 'fas fa-file-image text-warning',
        'txt': 'fas fa-file-alt text-secondary'
    }
    return icons.get(file_type.lower(), 'fas fa-file text-muted')

def format_file_size(size_bytes):
    """Format file size in human readable format"""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB"]
    import math
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {size_names[i]}"