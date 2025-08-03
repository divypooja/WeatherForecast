from app import db
from datetime import datetime
import json

class OCRResult(db.Model):
    """Store OCR processing results and extracted data"""
    __tablename__ = 'ocr_results'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # File Information
    document_id = db.Column(db.Integer, db.ForeignKey('documents.id'), nullable=True)
    file_path = db.Column(db.String(500), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_type = db.Column(db.String(20), nullable=False)  # pdf, jpg, png
    file_size = db.Column(db.Integer)  # Size in bytes
    
    # OCR Processing Info
    module_type = db.Column(db.String(50), nullable=False)  # po, grn, invoice, jobwork, production
    reference_id = db.Column(db.Integer)  # ID of the related record (PO, GRN, etc.)
    reference_type = db.Column(db.String(50))  # purchase_order, grn, invoice, etc.
    
    # OCR Engine Details
    primary_engine = db.Column(db.String(20), default='tesseract')  # tesseract, paddleocr, easyocr
    fallback_engine = db.Column(db.String(20))  # Used if primary failed
    processing_time = db.Column(db.Float)  # Time in seconds
    
    # Raw OCR Output
    raw_text = db.Column(db.Text)  # Raw extracted text
    confidence_score = db.Column(db.Float, default=0.0)  # Overall confidence (0-100)
    
    # Structured Data (JSON)
    extracted_fields = db.Column(db.Text)  # JSON string of extracted fields
    line_items = db.Column(db.Text)  # JSON string of extracted table data
    
    # Processing Status
    status = db.Column(db.String(20), default='pending')  # pending, processing, completed, failed
    error_message = db.Column(db.Text)
    
    # User Corrections
    user_corrections = db.Column(db.Text)  # JSON of user-corrected data
    is_user_verified = db.Column(db.Boolean, default=False)
    verified_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    verified_at = db.Column(db.DateTime)
    
    # Audit Trail
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    document = db.relationship('Document', backref='ocr_results')
    creator = db.relationship('User', foreign_keys=[created_by], backref='ocr_results_created')
    verifier = db.relationship('User', foreign_keys=[verified_by], backref='ocr_results_verified')
    
    def get_extracted_fields(self):
        """Get extracted fields as Python dict"""
        if self.extracted_fields:
            try:
                return json.loads(self.extracted_fields)
            except:
                return {}
        return {}
    
    def set_extracted_fields(self, fields_dict):
        """Set extracted fields from Python dict"""
        self.extracted_fields = json.dumps(fields_dict, indent=2)
    
    def get_line_items(self):
        """Get line items as Python list"""
        if self.line_items:
            try:
                return json.loads(self.line_items)
            except:
                return []
        return []
    
    def set_line_items(self, items_list):
        """Set line items from Python list"""
        self.line_items = json.dumps(items_list, indent=2)
    
    def get_user_corrections(self):
        """Get user corrections as Python dict"""
        if self.user_corrections:
            try:
                return json.loads(self.user_corrections)
            except:
                return {}
        return {}
    
    def set_user_corrections(self, corrections_dict):
        """Set user corrections from Python dict"""
        self.user_corrections = json.dumps(corrections_dict, indent=2)
    
    @property
    def confidence_level(self):
        """Get confidence level as text"""
        if self.confidence_score >= 80:
            return 'high'
        elif self.confidence_score >= 60:
            return 'medium'
        else:
            return 'low'
    
    @property
    def confidence_class(self):
        """Get Bootstrap class for confidence display"""
        level = self.confidence_level
        if level == 'high':
            return 'text-success'
        elif level == 'medium':
            return 'text-warning'
        else:
            return 'text-danger'

class OCRTemplate(db.Model):
    """Store OCR field extraction templates for different document types"""
    __tablename__ = 'ocr_templates'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Template Info
    name = db.Column(db.String(100), nullable=False)
    module_type = db.Column(db.String(50), nullable=False)  # po, grn, invoice, jobwork
    document_type = db.Column(db.String(50), nullable=False)  # vendor_invoice, customer_po, etc.
    
    # Field Mapping Rules (JSON)
    field_patterns = db.Column(db.Text)  # JSON of regex patterns for fields
    table_patterns = db.Column(db.Text)  # JSON of patterns for table extraction
    
    # Processing Rules
    preprocessing_rules = db.Column(db.Text)  # JSON of image preprocessing settings
    confidence_threshold = db.Column(db.Float, default=70.0)
    fallback_enabled = db.Column(db.Boolean, default=True)
    
    # Status
    is_active = db.Column(db.Boolean, default=True)
    is_default = db.Column(db.Boolean, default=False)
    
    # Audit
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    creator = db.relationship('User', backref='ocr_templates_created')
    
    def get_field_patterns(self):
        """Get field patterns as Python dict"""
        if self.field_patterns:
            try:
                return json.loads(self.field_patterns)
            except:
                return {}
        return {}
    
    def set_field_patterns(self, patterns_dict):
        """Set field patterns from Python dict"""
        self.field_patterns = json.dumps(patterns_dict, indent=2)
    
    def get_table_patterns(self):
        """Get table patterns as Python dict"""
        if self.table_patterns:
            try:
                return json.loads(self.table_patterns)
            except:
                return {}
        return {}
    
    def set_table_patterns(self, patterns_dict):
        """Set table patterns from Python dict"""
        self.table_patterns = json.dumps(patterns_dict, indent=2)

class OCRSettings(db.Model):
    """Global OCR configuration settings"""
    __tablename__ = 'ocr_settings'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Engine Preferences
    default_engine = db.Column(db.String(20), default='tesseract')
    fallback_engine = db.Column(db.String(20), default='tesseract')
    fallback_enabled = db.Column(db.Boolean, default=True)
    
    # Quality Settings
    confidence_threshold = db.Column(db.Float, default=70.0)
    image_preprocessing = db.Column(db.Boolean, default=True)
    save_raw_text = db.Column(db.Boolean, default=True)
    
    # UI Settings
    show_editable_preview = db.Column(db.Boolean, default=True)
    auto_populate_forms = db.Column(db.Boolean, default=False)  # Require user confirmation
    highlight_low_confidence = db.Column(db.Boolean, default=True)
    
    # Storage Settings
    keep_processed_images = db.Column(db.Boolean, default=True)
    max_file_size_mb = db.Column(db.Integer, default=50)
    
    # Audit
    updated_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    updater = db.relationship('User', backref='ocr_settings_updates')
    
    @classmethod
    def get_settings(cls):
        """Get or create OCR settings"""
        settings = cls.query.first()
        if not settings:
            settings = cls()
            db.session.add(settings)
            db.session.commit()
        return settings

class OCRHistory(db.Model):
    """Track OCR processing history and statistics"""
    __tablename__ = 'ocr_history'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Processing Stats
    date = db.Column(db.Date, default=datetime.utcnow().date(), nullable=False)
    module_type = db.Column(db.String(50), nullable=False)
    total_processed = db.Column(db.Integer, default=0)
    successful_extractions = db.Column(db.Integer, default=0)
    failed_extractions = db.Column(db.Integer, default=0)
    
    # Performance Metrics
    avg_processing_time = db.Column(db.Float, default=0.0)
    avg_confidence_score = db.Column(db.Float, default=0.0)
    
    # Engine Usage
    tesseract_usage = db.Column(db.Integer, default=0)
    fallback_usage = db.Column(db.Integer, default=0)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    @property
    def success_rate(self):
        """Calculate success rate percentage"""
        if self.total_processed == 0:
            return 0.0
        return (self.successful_extractions / self.total_processed) * 100
    
    @classmethod
    def update_stats(cls, module_type, success, processing_time, confidence, engine):
        """Update daily statistics"""
        today = datetime.utcnow().date()
        history = cls.query.filter_by(date=today, module_type=module_type).first()
        
        if not history:
            history = cls(date=today, module_type=module_type)
            db.session.add(history)
        
        # Update counts - ensure all values are initialized
        history.total_processed = (history.total_processed or 0) + 1
        if success:
            history.successful_extractions = (history.successful_extractions or 0) + 1
        else:
            history.failed_extractions = (history.failed_extractions or 0) + 1
        
        # Update averages - handle None values
        total = history.total_processed
        processing_time = processing_time or 0.0
        confidence = confidence or 0.0
        current_avg_time = history.avg_processing_time or 0.0
        current_avg_conf = history.avg_confidence_score or 0.0
        history.avg_processing_time = ((current_avg_time * (total - 1)) + processing_time) / total
        history.avg_confidence_score = ((current_avg_conf * (total - 1)) + confidence) / total
        
        # Update engine usage
        if engine == 'tesseract':
            history.tesseract_usage = (history.tesseract_usage or 0) + 1
        else:
            history.fallback_usage = (history.fallback_usage or 0) + 1
        
        db.session.commit()