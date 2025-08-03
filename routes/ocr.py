"""
OCR Routes - Web interface for OCR document processing
"""
import json
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from app import db
from models_ocr import OCRResult, OCRSettings, OCRHistory
from services.ocr_service import ocr_service, OCRFormIntegration
from utils import admin_required

bp = Blueprint('ocr', __name__, url_prefix='/ocr')

@bp.route('/dashboard')
@login_required
def dashboard():
    """OCR processing dashboard"""
    # Get recent results
    recent_results = ocr_service.get_recent_results(limit=10)
    
    # Get statistics
    stats = ocr_service.get_statistics(days=30)
    
    # Get settings
    settings = OCRSettings.get_settings()
    
    return render_template('ocr/dashboard.html',
                         recent_results=recent_results,
                         stats=stats,
                         settings=settings)

@bp.route('/upload', methods=['GET', 'POST'])
@login_required
def upload_document():
    """Upload and process document with OCR"""
    if request.method == 'GET':
        module_type = request.args.get('module_type', 'general')
        reference_id = request.args.get('reference_id')
        reference_type = request.args.get('reference_type')
        
        return render_template('ocr/upload.html',
                             module_type=module_type,
                             reference_id=reference_id,
                             reference_type=reference_type)
    
    # Handle file upload
    if 'file' not in request.files:
        flash('No file selected', 'error')
        return redirect(request.url)
    
    file = request.files['file']
    if file.filename == '':
        flash('No file selected', 'error')
        return redirect(request.url)
    
    module_type = request.form.get('module_type', 'general')
    reference_id = request.form.get('reference_id')
    reference_type = request.form.get('reference_type')
    
    # Convert reference_id to int if provided
    if reference_id:
        try:
            reference_id = int(reference_id)
        except:
            reference_id = None
    
    # Process file with OCR
    result = ocr_service.process_uploaded_file(
        file=file,
        module_type=module_type,
        reference_id=reference_id,
        reference_type=reference_type,
        user_id=current_user.id
    )
    
    if result['success']:
        flash('Document processed successfully!', 'success')
        return redirect(url_for('ocr.preview_result', ocr_result_id=result['ocr_result_id']))
    else:
        flash(f'Processing failed: {result["error"]}', 'error')
        return redirect(request.url)

@bp.route('/preview/<int:ocr_result_id>')
@login_required
def preview_result(ocr_result_id):
    """Preview OCR results with editable fields"""
    ocr_result = ocr_service.get_ocr_result(ocr_result_id)
    
    if not ocr_result:
        flash('OCR result not found', 'error')
        return redirect(url_for('ocr.dashboard'))
    
    # Get extracted data
    extracted_fields = ocr_result.get_extracted_fields()
    line_items = ocr_result.get_line_items()
    user_corrections = ocr_result.get_user_corrections()
    
    # Prepare form data based on module type
    form_data = {}
    if ocr_result.module_type == 'grn':
        form_data = OCRFormIntegration.prepare_grn_data(extracted_fields, line_items)
    elif ocr_result.module_type == 'invoice':
        form_data = OCRFormIntegration.prepare_invoice_data(extracted_fields, line_items)
    elif ocr_result.module_type == 'po':
        form_data = OCRFormIntegration.prepare_purchase_order_data(extracted_fields, line_items)
    
    return render_template('ocr/preview.html',
                         ocr_result=ocr_result,
                         extracted_fields=extracted_fields,
                         line_items=line_items,
                         user_corrections=user_corrections,
                         form_data=form_data)

@bp.route('/api/update_corrections', methods=['POST'])
@login_required
def update_corrections():
    """Update user corrections for OCR result"""
    data = request.get_json()
    
    ocr_result_id = data.get('ocr_result_id')
    corrections = data.get('corrections', {})
    
    if not ocr_result_id:
        return jsonify({'success': False, 'error': 'OCR result ID required'})
    
    success = ocr_service.update_user_corrections(
        ocr_result_id=ocr_result_id,
        corrections=corrections,
        user_id=current_user.id
    )
    
    if success:
        return jsonify({'success': True, 'message': 'Corrections saved successfully'})
    else:
        return jsonify({'success': False, 'error': 'Failed to save corrections'})

@bp.route('/api/populate_form', methods=['POST'])
@login_required
def populate_form():
    """Get OCR data formatted for form population"""
    data = request.get_json()
    
    ocr_result_id = data.get('ocr_result_id')
    use_corrections = data.get('use_corrections', True)
    
    ocr_result = ocr_service.get_ocr_result(ocr_result_id)
    if not ocr_result:
        return jsonify({'success': False, 'error': 'OCR result not found'})
    
    # Get data (with corrections if available)
    if use_corrections and ocr_result.is_user_verified:
        extracted_fields = ocr_result.get_user_corrections()
        line_items = extracted_fields.get('line_items', [])
    else:
        extracted_fields = ocr_result.get_extracted_fields()
        line_items = ocr_result.get_line_items()
    
    # Prepare form data
    form_data = {}
    if ocr_result.module_type == 'grn':
        form_data = OCRFormIntegration.prepare_grn_data(extracted_fields, line_items)
    elif ocr_result.module_type == 'invoice':
        form_data = OCRFormIntegration.prepare_invoice_data(extracted_fields, line_items)
    elif ocr_result.module_type == 'po':
        form_data = OCRFormIntegration.prepare_purchase_order_data(extracted_fields, line_items)
    
    return jsonify({
        'success': True,
        'form_data': form_data,
        'confidence': ocr_result.confidence_score,
        'confidence_level': ocr_result.confidence_level
    })

@bp.route('/history')
@login_required
def history():
    """View OCR processing history"""
    page = request.args.get('page', 1, type=int)
    module_type = request.args.get('module_type', '')
    
    query = OCRResult.query
    
    if module_type:
        query = query.filter_by(module_type=module_type)
    
    results = query.order_by(OCRResult.created_at.desc())\
                  .paginate(page=page, per_page=20, error_out=False)
    
    # Get available module types for filter
    module_types = db.session.query(OCRResult.module_type.distinct()).all()
    module_types = [mt[0] for mt in module_types]
    
    return render_template('ocr/history.html',
                         results=results,
                         module_types=module_types,
                         current_module_type=module_type)

@bp.route('/api/retry/<int:ocr_result_id>', methods=['POST'])
@login_required
def retry_ocr(ocr_result_id):
    """Retry OCR processing for a failed result"""
    result = ocr_service.retry_failed_ocr(ocr_result_id)
    
    if result['success']:
        flash('OCR processing completed successfully', 'success')
    else:
        flash(f'OCR retry failed: {result["error"]}', 'error')
    
    return jsonify(result)

@bp.route('/api/delete/<int:ocr_result_id>', methods=['DELETE'])
@login_required
def delete_result(ocr_result_id):
    """Delete OCR result"""
    success = ocr_service.delete_ocr_result(ocr_result_id)
    
    if success:
        return jsonify({'success': True, 'message': 'OCR result deleted successfully'})
    else:
        return jsonify({'success': False, 'error': 'Failed to delete OCR result'})

@bp.route('/settings', methods=['GET', 'POST'])
@admin_required
def settings():
    """OCR settings management"""
    settings = OCRSettings.get_settings()
    
    if request.method == 'POST':
        # Update settings
        settings.default_engine = request.form.get('default_engine', 'tesseract')
        settings.fallback_enabled = 'fallback_enabled' in request.form
        settings.confidence_threshold = float(request.form.get('confidence_threshold', 70.0))
        settings.image_preprocessing = 'image_preprocessing' in request.form
        settings.save_raw_text = 'save_raw_text' in request.form
        settings.show_editable_preview = 'show_editable_preview' in request.form
        settings.auto_populate_forms = 'auto_populate_forms' in request.form
        settings.highlight_low_confidence = 'highlight_low_confidence' in request.form
        settings.keep_processed_images = 'keep_processed_images' in request.form
        settings.max_file_size_mb = int(request.form.get('max_file_size_mb', 50))
        settings.updated_by = current_user.id
        
        db.session.commit()
        flash('OCR settings updated successfully', 'success')
        return redirect(url_for('ocr.settings'))
    
    return render_template('ocr/settings.html', settings=settings)

@bp.route('/api/statistics')
@login_required
def api_statistics():
    """Get OCR statistics as JSON"""
    days = request.args.get('days', 30, type=int)
    stats = ocr_service.get_statistics(days=days)
    return jsonify(stats)

@bp.route('/test')
@admin_required
def test_page():
    """OCR testing page for admins"""
    return render_template('ocr/test.html')

@bp.route('/api/test_engine', methods=['POST'])
@admin_required
def test_engine():
    """Test OCR engine with uploaded file"""
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file provided'})
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'error': 'No file selected'})
    
    # Process file for testing
    result = ocr_service.process_uploaded_file(
        file=file,
        module_type='test',
        user_id=current_user.id
    )
    
    return jsonify(result)

# Context processor for OCR templates
@bp.app_context_processor
def inject_ocr_helpers():
    """Inject OCR helper functions into templates"""
    def confidence_badge_class(confidence):
        if confidence >= 80:
            return 'bg-success'
        elif confidence >= 60:
            return 'bg-warning'
        else:
            return 'bg-danger'
    
    def format_processing_time(seconds):
        if seconds < 1:
            return f"{seconds*1000:.0f}ms"
        else:
            return f"{seconds:.2f}s"
    
    return dict(
        confidence_badge_class=confidence_badge_class,
        format_processing_time=format_processing_time
    )