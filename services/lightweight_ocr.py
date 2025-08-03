"""
Lightweight OCR Service - Memory-optimized version for small Replit environment
"""
import os
import cv2
import logging
import pytesseract
import numpy as np
from pdf2image import convert_from_path
from typing import Dict, Tuple
import re
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class LightweightOCRResult:
    success: bool
    text: str
    confidence: float
    extracted_fields: Dict
    error_message: str = None

class LightweightOCR:
    """Memory-optimized OCR processor for Replit environment"""
    
    def __init__(self):
        self.field_patterns = {
            'invoice_number': [
                r'invoice\s*(?:no|number|#)?[:\s]*([A-Z0-9/-]+)',
                r'inv\s*(?:no|#|number)?[:\s]*([A-Z0-9/-]+)',
                r'bill\s*(?:no|number|#)?[:\s]*([A-Z0-9/-]+)',
            ],
            'date': [
                r'invoice\s*date[:\s]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
                r'date[:\s]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
                r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            ],
            'amount': [
                r'(?:total|grand\s*total|net\s*amount)[:\s]*₹?\s*([0-9,]+\.?\d*)',
                r'₹\s*([0-9,]+\.?\d*)',
                r'rs\.?\s*([0-9,]+\.?\d*)',
            ],
            'vendor_name': [
                r'vendor[:\s]*([A-Za-z\s&.,()]+?)(?:\n|address|gstin|phone)',
                r'supplier[:\s]*([A-Za-z\s&.,()]+?)(?:\n|address|gstin|phone)',
                r'from[:\s]*([A-Za-z\s&.,()]+?)(?:\n|address|gstin|phone)',
            ],
            'customer_name': [
                r'to[:\s]*([A-Za-z\s&.,()]+?)(?:\n|address|gstin|phone)',
                r'customer[:\s]*([A-Za-z\s&.,()]+?)(?:\n|address|gstin|phone)',
                r'bill\s*to[:\s]*([A-Za-z\s&.,()]+?)(?:\n|address|gstin|phone)',
            ],
            'gstin': [
                r'gstin[:\s]*([0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1})',
                r'([0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1})',
            ]
        }
    
    def process_file(self, file_path: str) -> LightweightOCRResult:
        """Process file with lightweight OCR"""
        try:
            # Convert PDF to image if needed
            processed_path = self._prepare_file(file_path)
            
            # Simple preprocessing
            processed_path = self._lightweight_preprocess(processed_path)
            
            # Extract text with Tesseract
            text, confidence = self._extract_text(processed_path)
            
            if not text.strip():
                return LightweightOCRResult(
                    success=False,
                    text="",
                    confidence=0.0,
                    extracted_fields={},
                    error_message="No text extracted"
                )
            
            # Extract fields
            extracted_fields = self._extract_fields(text)
            
            logger.info(f"Lightweight OCR: {confidence:.1f}% confidence, {len(extracted_fields)} fields")
            
            return LightweightOCRResult(
                success=True,
                text=text,
                confidence=confidence,
                extracted_fields=extracted_fields
            )
            
        except Exception as e:
            logger.error(f"Lightweight OCR failed: {e}")
            return LightweightOCRResult(
                success=False,
                text="",
                confidence=0.0,
                extracted_fields={},
                error_message=str(e)
            )
    
    def _prepare_file(self, file_path: str) -> str:
        """Convert PDF to image if needed"""
        if file_path.lower().endswith('.pdf'):
            try:
                # Convert only first page with low DPI for memory efficiency
                images = convert_from_path(file_path, first_page=1, last_page=1, dpi=200)
                if images:
                    img_path = file_path.replace('.pdf', '_converted.png')
                    images[0].save(img_path, 'PNG')
                    return img_path
            except Exception as e:
                logger.error(f"PDF conversion failed: {e}")
                raise
        return file_path
    
    def _lightweight_preprocess(self, image_path: str) -> str:
        """Simple, memory-efficient preprocessing"""
        try:
            # Load image
            img = cv2.imread(image_path)
            if img is None:
                return image_path
            
            # Convert to grayscale
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Resize if too large (aggressive memory optimization)
            height, width = gray.shape
            max_dimension = 1000
            if max(width, height) > max_dimension:
                scale = max_dimension / max(width, height)
                new_width = int(width * scale)
                new_height = int(height * scale)
                gray = cv2.resize(gray, (new_width, new_height), interpolation=cv2.INTER_AREA)
            
            # Simple binarization
            _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            # Save processed image
            output_path = image_path.replace('.', '_processed.')
            cv2.imwrite(output_path, binary)
            
            # Clean up memory
            del img, gray, binary
            
            return output_path
            
        except Exception as e:
            logger.warning(f"Preprocessing failed: {e}")
            return image_path
    
    def _extract_text(self, image_path: str) -> Tuple[str, float]:
        """Extract text using simple Tesseract configuration"""
        try:
            # Use simple, fast configuration
            config = '--oem 3 --psm 6'
            
            # Get text
            text = pytesseract.image_to_string(image_path, config=config)
            
            # Get confidence
            try:
                data = pytesseract.image_to_data(image_path, output_type=pytesseract.Output.DICT, config=config)
                confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
                avg_confidence = sum(confidences) / len(confidences) if confidences else 0
            except:
                avg_confidence = 75.0  # Default confidence
            
            return text, avg_confidence
            
        except Exception as e:
            logger.error(f"Text extraction failed: {e}")
            return "", 0.0
    
    def _extract_fields(self, text: str) -> Dict:
        """Extract structured fields from text"""
        extracted = {}
        text_lower = text.lower()
        
        for field_name, patterns in self.field_patterns.items():
            for pattern in patterns:
                match = re.search(pattern, text_lower, re.IGNORECASE | re.MULTILINE)
                if match:
                    value = match.group(1).strip()
                    if value:
                        extracted[field_name] = value
                        break
        
        return extracted

# Global lightweight OCR instance
lightweight_ocr = LightweightOCR()