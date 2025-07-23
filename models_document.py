# Document Management Models
from app import db
from datetime import datetime
import os

class Document(db.Model):
    __tablename__ = 'documents'
    
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_size = db.Column(db.Integer, nullable=False)
    file_type = db.Column(db.String(50), nullable=False)
    upload_path = db.Column(db.String(500), nullable=False)
    
    # Transaction association
    transaction_type = db.Column(db.String(50), nullable=False)  # 'purchase_order', 'sales_order', 'job_work', etc.
    transaction_id = db.Column(db.Integer, nullable=False)
    
    # Document metadata
    document_category = db.Column(db.String(100), nullable=False)  # 'invoice', 'receipt', 'contract', 'specification', etc.
    description = db.Column(db.Text)
    
    # Audit fields
    uploaded_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    uploader = db.relationship('User', backref='uploaded_documents')
    
    def __repr__(self):
        return f'<Document {self.original_filename}>'
    
    @property
    def file_size_mb(self):
        return round(self.file_size / (1024 * 1024), 2)
    
    def get_file_path(self):
        return os.path.join('uploads', self.upload_path)