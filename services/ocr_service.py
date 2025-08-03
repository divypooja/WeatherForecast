"""
OCR Service - High-level service for OCR integration with the Factory Management System
"""
import os
import logging
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from flask import current_app
from werkzeug.utils import secure_filename

from app import db
from models_ocr import OCRResult as OCRResultModel, OCRSettings, OCRHistory, OCRTemplate
from services.ocr_engine import ocr_engine, OCRResult

logger = logging.getLogger(__name__)

class OCRService:
    """Main OCR service for document processing"""
    
    def __init__(self):
        self.upload_folder = 'uploads/ocr_docs'
        self.allowed_extensions = {'pdf', 'png', 'jpg', 'jpeg', 'tiff', 'bmp'}
        self._ensure_upload_folder()
    
    def _ensure_upload_folder(self):
        """Ensure upload folder exists"""
        os.makedirs(self.upload_folder, exist_ok=True)
    
    def is_allowed_file(self, filename: str) -> bool:
        """Check if file extension is allowed"""
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in self.allowed_extensions
    
    def process_uploaded_file(self, file, module_type: str, reference_id: Optional[int] = None, 
                            reference_type: Optional[str] = None, user_id: Optional[int] = None) -> Dict:
        """
        Process uploaded file and return OCR results
        
        Args:
            file: Uploaded file object
            module_type: Type of module (po, grn, invoice, jobwork, production)
            reference_id: ID of related record
            reference_type: Type of related record
            user_id: ID of user performing the operation
        
        Returns:
            Dict with processing results
        """
        try:
            # Validate file
            if not file or not file.filename:
                return {'success': False, 'error': 'No file provided'}
            
            if not self.is_allowed_file(file.filename):
                return {'success': False, 'error': 'File type not allowed'}
            
            # Save file
            filename = secure_filename(file.filename)
            timestamp = str(int(time.time()))
            filename = f"{timestamp}_{filename}"
            file_path = os.path.join(self.upload_folder, filename)
            file.save(file_path)
            
            # Get file info
            file_size = os.path.getsize(file_path)
            file_type = filename.rsplit('.', 1)[1].lower()
            
            # Check file size limit
            settings = OCRSettings.get_settings()
            max_size = settings.max_file_size_mb * 1024 * 1024  # Convert MB to bytes
            if file_size > max_size:
                os.remove(file_path)
                return {'success': False, 'error': f'File too large. Maximum size: {settings.max_file_size_mb}MB'}
            
            # Create OCR result record
            ocr_result = OCRResultModel()
            ocr_result.file_path = file_path
            ocr_result.original_filename = file.filename
            ocr_result.file_type = file_type
            ocr_result.file_size = file_size
            ocr_result.module_type = module_type
            ocr_result.reference_id = reference_id
            ocr_result.reference_type = reference_type
            ocr_result.status = 'processing'
            ocr_result.created_by = user_id or 1  # Default user ID if not provided
            db.session.add(ocr_result)
            db.session.commit()
            
            # Process with OCR engine
            processing_result = ocr_engine.process_document(
                file_path, 
                module_type, 
                use_preprocessing=settings.image_preprocessing,
                fallback_enabled=settings.fallback_enabled
            )
            
            # Update OCR result record
            ocr_result.status = 'completed' if processing_result.success else 'failed'
            ocr_result.raw_text = processing_result.text if settings.save_raw_text else None
            ocr_result.confidence_score = processing_result.confidence
            ocr_result.primary_engine = processing_result.engine_used
            ocr_result.processing_time = processing_result.processing_time
            ocr_result.error_message = processing_result.error_message
            
            if processing_result.extracted_fields:
                ocr_result.set_extracted_fields(processing_result.extracted_fields)
            
            if processing_result.line_items:
                ocr_result.set_line_items(processing_result.line_items)
            
            db.session.commit()
            
            # Update statistics
            OCRHistory.update_stats(
                module_type=module_type,
                success=processing_result.success,
                processing_time=processing_result.processing_time,
                confidence=processing_result.confidence,
                engine=processing_result.engine_used
            )
            
            # Prepare response
            response = {
                'success': processing_result.success,
                'ocr_result_id': ocr_result.id,
                'confidence': processing_result.confidence,
                'confidence_level': ocr_result.confidence_level,
                'processing_time': processing_result.processing_time,
                'extracted_fields': processing_result.extracted_fields or {},
                'line_items': processing_result.line_items or [],
                'raw_text': processing_result.text if settings.save_raw_text else None
            }
            
            if not processing_result.success:
                response['error'] = processing_result.error_message
            
            return response
            
        except Exception as e:
            logger.error(f"OCR processing failed: {e}")
            return {'success': False, 'error': f'Processing failed: {str(e)}'}
    
    def get_ocr_result(self, ocr_result_id: int) -> Optional[OCRResultModel]:
        """Get OCR result by ID"""
        return OCRResultModel.query.get(ocr_result_id)
    
    def update_user_corrections(self, ocr_result_id: int, corrections: Dict, user_id: int) -> bool:
        """Update OCR result with user corrections"""
        try:
            ocr_result = OCRResultModel.query.get(ocr_result_id)
            if not ocr_result:
                return False
            
            ocr_result.set_user_corrections(corrections)
            ocr_result.is_user_verified = True
            ocr_result.verified_by = user_id
            ocr_result.verified_at = datetime.utcnow()
            
            db.session.commit()
            return True
            
        except Exception as e:
            logger.error(f"Failed to update user corrections: {e}")
            return False
    
    def get_module_results(self, module_type: str, limit: int = 50) -> List[OCRResultModel]:
        """Get OCR results for a specific module"""
        return OCRResultModel.query.filter_by(module_type=module_type)\
                                  .order_by(OCRResultModel.created_at.desc())\
                                  .limit(limit).all()
    
    def get_recent_results(self, limit: int = 20) -> List[OCRResultModel]:
        """Get recent OCR results across all modules"""
        return OCRResultModel.query.order_by(OCRResultModel.created_at.desc())\
                                  .limit(limit).all()
    
    def get_statistics(self, days: int = 30) -> Dict:
        """Get OCR processing statistics"""
        from datetime import datetime, timedelta
        
        start_date = (datetime.utcnow() - timedelta(days=days)).date()
        
        # Get history data
        history_data = OCRHistory.query.filter(OCRHistory.date >= start_date).all()
        
        stats = {
            'total_processed': sum(h.total_processed for h in history_data),
            'successful_extractions': sum(h.successful_extractions for h in history_data),
            'failed_extractions': sum(h.failed_extractions for h in history_data),
            'avg_processing_time': 0,
            'avg_confidence_score': 0,
            'success_rate': 0,
            'by_module': {},
            'by_date': []
        }
        
        if history_data:
            total_time = sum(h.avg_processing_time * h.total_processed for h in history_data)
            total_confidence = sum(h.avg_confidence_score * h.total_processed for h in history_data)
            
            if stats['total_processed'] > 0:
                stats['avg_processing_time'] = total_time / stats['total_processed']
                stats['avg_confidence_score'] = total_confidence / stats['total_processed']
                stats['success_rate'] = (stats['successful_extractions'] / stats['total_processed']) * 100
            
            # Group by module
            module_stats = {}
            for h in history_data:
                if h.module_type not in module_stats:
                    module_stats[h.module_type] = {
                        'total': 0, 'successful': 0, 'failed': 0
                    }
                module_stats[h.module_type]['total'] += h.total_processed
                module_stats[h.module_type]['successful'] += h.successful_extractions
                module_stats[h.module_type]['failed'] += h.failed_extractions
            
            stats['by_module'] = module_stats
            
            # Group by date
            date_stats = {}
            for h in history_data:
                date_str = h.date.strftime('%Y-%m-%d')
                if date_str not in date_stats:
                    date_stats[date_str] = {'total': 0, 'successful': 0}
                date_stats[date_str]['total'] += h.total_processed
                date_stats[date_str]['successful'] += h.successful_extractions
            
            stats['by_date'] = [{'date': k, **v} for k, v in date_stats.items()]
        
        return stats
    
    def retry_failed_ocr(self, ocr_result_id: int) -> Dict:
        """Retry OCR processing for a failed result"""
        try:
            ocr_result = OCRResultModel.query.get(ocr_result_id)
            if not ocr_result:
                return {'success': False, 'error': 'OCR result not found'}
            
            if not os.path.exists(ocr_result.file_path):
                return {'success': False, 'error': 'Original file not found'}
            
            # Retry processing
            settings = OCRSettings.get_settings()
            processing_result = ocr_engine.process_document(
                ocr_result.file_path,
                ocr_result.module_type,
                use_preprocessing=settings.image_preprocessing,
                fallback_enabled=settings.fallback_enabled
            )
            
            # Update result
            ocr_result.status = 'completed' if processing_result.success else 'failed'
            ocr_result.raw_text = processing_result.text if settings.save_raw_text else None
            ocr_result.confidence_score = processing_result.confidence
            ocr_result.primary_engine = processing_result.engine_used
            ocr_result.processing_time = processing_result.processing_time
            ocr_result.error_message = processing_result.error_message
            
            if processing_result.extracted_fields:
                ocr_result.set_extracted_fields(processing_result.extracted_fields)
            
            if processing_result.line_items:
                ocr_result.set_line_items(processing_result.line_items)
            
            db.session.commit()
            
            return {
                'success': processing_result.success,
                'confidence': processing_result.confidence,
                'extracted_fields': processing_result.extracted_fields or {},
                'line_items': processing_result.line_items or [],
                'error': processing_result.error_message if not processing_result.success else None
            }
            
        except Exception as e:
            logger.error(f"OCR retry failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def delete_ocr_result(self, ocr_result_id: int) -> bool:
        """Delete OCR result and associated files"""
        try:
            ocr_result = OCRResultModel.query.get(ocr_result_id)
            if not ocr_result:
                return False
            
            # Delete file if exists
            if os.path.exists(ocr_result.file_path):
                os.remove(ocr_result.file_path)
            
            # Delete database record
            db.session.delete(ocr_result)
            db.session.commit()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete OCR result: {e}")
            return False

class OCRFormIntegration:
    """Integration helpers for populating forms with OCR data"""
    
    @staticmethod
    def prepare_grn_data(extracted_fields: Dict, line_items: List[Dict]) -> Dict:
        """Prepare OCR data for GRN form population"""
        grn_data = {
            'vendor_info': {},
            'document_info': {},
            'line_items': []
        }
        
        # Map extracted fields to GRN fields
        field_mapping = {
            'vendor_name': 'vendor_info.name',
            'invoice_number': 'document_info.challan_number',
            'date': 'document_info.challan_date',
            'gstin': 'vendor_info.gstin'
        }
        
        for ocr_field, grn_field in field_mapping.items():
            if ocr_field in extracted_fields:
                value = extracted_fields[ocr_field]
                if '.' in grn_field:
                    section, field = grn_field.split('.')
                    if section not in grn_data:
                        grn_data[section] = {}
                    grn_data[section][field] = value
                else:
                    grn_data[grn_field] = value
        
        # Process line items
        for item in line_items:
            grn_item = {
                'item_name': item.get('item_name', ''),
                'quantity_received': item.get('quantity', 0),
                'rate': item.get('rate', 0),
                'amount': item.get('amount', 0)
            }
            grn_data['line_items'].append(grn_item)
        
        return grn_data
    
    @staticmethod
    def prepare_invoice_data(extracted_fields: Dict, line_items: List[Dict]) -> Dict:
        """Prepare OCR data for Invoice form population"""
        invoice_data = {
            'header': {},
            'party_info': {},
            'line_items': []
        }
        
        # Map extracted fields
        field_mapping = {
            'invoice_number': 'header.invoice_number',
            'date': 'header.invoice_date',
            'vendor_name': 'party_info.party_name',
            'customer_name': 'party_info.party_name',
            'gstin': 'party_info.gstin',
            'amount': 'header.total_amount'
        }
        
        for ocr_field, invoice_field in field_mapping.items():
            if ocr_field in extracted_fields:
                value = extracted_fields[ocr_field]
                if '.' in invoice_field:
                    section, field = invoice_field.split('.')
                    if section not in invoice_data:
                        invoice_data[section] = {}
                    invoice_data[section][field] = value
                else:
                    invoice_data[invoice_field] = value
        
        # Process line items
        for item in line_items:
            invoice_item = {
                'item_description': item.get('item_name', ''),
                'quantity': item.get('quantity', 0),
                'rate': item.get('rate', 0),
                'amount': item.get('amount', 0)
            }
            invoice_data['line_items'].append(invoice_item)
        
        return invoice_data
    
    @staticmethod
    def prepare_purchase_order_data(extracted_fields: Dict, line_items: List[Dict]) -> Dict:
        """Prepare OCR data for Purchase Order form population"""
        po_data = {
            'header': {},
            'supplier_info': {},
            'line_items': []
        }
        
        # Map extracted fields
        field_mapping = {
            'po_number': 'header.po_number',
            'date': 'header.po_date',
            'vendor_name': 'supplier_info.supplier_name',
            'customer_name': 'supplier_info.customer_name'
        }
        
        for ocr_field, po_field in field_mapping.items():
            if ocr_field in extracted_fields:
                value = extracted_fields[ocr_field]
                if '.' in po_field:
                    section, field = po_field.split('.')
                    if section not in po_data:
                        po_data[section] = {}
                    po_data[section][field] = value
                else:
                    po_data[po_field] = value
        
        # Process line items
        for item in line_items:
            po_item = {
                'item_name': item.get('item_name', ''),
                'quantity': item.get('quantity', 0),
                'rate': item.get('rate', 0)
            }
            po_data['line_items'].append(po_item)
        
        return po_data

# Global OCR service instance
ocr_service = OCRService()