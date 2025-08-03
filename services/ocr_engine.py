"""
OCR Engine - Multi-engine OCR processing with fallback support
Using only open-source tools: Tesseract, OpenCV, scikit-image
"""
import cv2
import numpy as np
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
from pdf2image import convert_from_path
import re
import json
import os
import time
import logging
import subprocess
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from skimage import restoration, filters, morphology, segmentation
from skimage.filters import threshold_otsu

logger = logging.getLogger(__name__)

@dataclass
class OCRResult:
    """OCR processing result"""
    success: bool
    text: str
    confidence: float
    processing_time: float
    engine_used: str
    error_message: str = ""
    extracted_fields: Optional[Dict] = None
    line_items: Optional[List[Dict]] = None

class ImagePreprocessor:
    """Advanced image preprocessing using OpenCV and scikit-image"""
    
    @staticmethod
    def preprocess_image(image_path: str, output_path: str = None) -> str:
        """
        Comprehensive image preprocessing pipeline
        Returns path to processed image
        """
        try:
            # Load image
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError(f"Could not load image: {image_path}")
            
            # Convert to RGB for PIL processing
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(image_rgb)
            
            # Step 1: Enhance contrast and brightness
            pil_image = ImagePreprocessor._enhance_contrast(pil_image)
            
            # Convert back to OpenCV format
            opencv_image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
            
            # Step 2: Noise reduction
            opencv_image = ImagePreprocessor._reduce_noise(opencv_image)
            
            # Step 3: Deskew correction
            opencv_image = ImagePreprocessor._correct_skew(opencv_image)
            
            # Step 4: Binarization
            opencv_image = ImagePreprocessor._binarize(opencv_image)
            
            # Step 5: Morphological operations
            opencv_image = ImagePreprocessor._morphological_cleanup(opencv_image)
            
            # Save processed image
            if output_path is None:
                base, ext = os.path.splitext(image_path)
                output_path = f"{base}_processed{ext}"
            
            cv2.imwrite(output_path, opencv_image)
            return output_path
            
        except Exception as e:
            logger.error(f"Image preprocessing failed: {e}")
            return image_path  # Return original if preprocessing fails
    
    @staticmethod
    def _enhance_contrast(image: Image.Image) -> Image.Image:
        """Enhance contrast and brightness"""
        # Adjust contrast
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(1.2)
        
        # Adjust brightness
        enhancer = ImageEnhance.Brightness(image)
        image = enhancer.enhance(1.1)
        
        # Adjust sharpness
        enhancer = ImageEnhance.Sharpness(image)
        image = enhancer.enhance(1.3)
        
        return image
    
    @staticmethod
    def _reduce_noise(image: np.ndarray) -> np.ndarray:
        """Reduce noise using various filters"""
        # Gaussian blur to reduce noise
        denoised = cv2.GaussianBlur(image, (3, 3), 0)
        
        # Non-local means denoising
        if len(image.shape) == 3:
            denoised = cv2.fastNlMeansDenoisingColored(denoised, None, 10, 10, 7, 21)
        else:
            denoised = cv2.fastNlMeansDenoising(denoised, None, 10, 7, 21)
        
        return denoised
    
    @staticmethod
    def _correct_skew(image: np.ndarray) -> np.ndarray:
        """Detect and correct skew using Hough transform"""
        try:
            # Convert to grayscale if needed
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image.copy()
            
            # Edge detection
            edges = cv2.Canny(gray, 100, 200, apertureSize=3)
            
            # Hough line detection
            lines = cv2.HoughLines(edges, 1, np.pi/180, threshold=200)
            
            if lines is not None:
                # Calculate average angle
                angles = []
                for line in lines:
                    rho, theta = line[0]
                    angle = theta * 180 / np.pi - 90
                    if abs(angle) < 45:  # Only consider reasonable skew angles
                        angles.append(angle)
                
                if angles:
                    avg_angle = np.median(angles)
                    
                    # Rotate image to correct skew
                    if abs(avg_angle) > 0.5:  # Only rotate if skew is significant
                        (h, w) = image.shape[:2]
                        center = (w // 2, h // 2)
                        rotation_matrix = cv2.getRotationMatrix2D(center, float(avg_angle), 1.0)
                        image = cv2.warpAffine(image, rotation_matrix, (w, h), 
                                             flags=cv2.INTER_CUBIC, 
                                             borderMode=cv2.BORDER_REPLICATE)
            
            return image
            
        except Exception as e:
            logger.warning(f"Skew correction failed: {e}")
            return image
    
    @staticmethod
    def _binarize(image: np.ndarray) -> np.ndarray:
        """Convert to binary image using adaptive thresholding"""
        # Convert to grayscale if needed
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()
        
        # Try different binarization methods and pick the best
        
        # Method 1: Adaptive threshold
        binary1 = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                       cv2.THRESH_BINARY, 11, 2)
        
        # Method 2: Otsu's thresholding
        _, binary2 = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Method 3: Combined approach
        blur = cv2.GaussianBlur(gray, (5, 5), 0)
        _, binary3 = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Choose the binary image with the most reasonable text-to-background ratio
        ratios = []
        for binary in [binary1, binary2, binary3]:
            white_pixels = np.sum(binary == 255)
            total_pixels = binary.size
            ratio = white_pixels / total_pixels
            ratios.append(abs(ratio - 0.8))  # Prefer ~80% white (background)
        
        best_binary = [binary1, binary2, binary3][ratios.index(min(ratios))]
        return best_binary
    
    @staticmethod
    def _morphological_cleanup(image: np.ndarray) -> np.ndarray:
        """Clean up binary image using morphological operations"""
        # Remove small noise
        kernel = np.ones((2, 2), np.uint8)
        cleaned = cv2.morphologyEx(image, cv2.MORPH_CLOSE, kernel)
        
        # Remove very small components
        kernel = np.ones((1, 1), np.uint8)
        cleaned = cv2.morphologyEx(cleaned, cv2.MORPH_OPEN, kernel)
        
        return cleaned

class TesseractEngine:
    """Tesseract OCR engine wrapper"""
    
    def __init__(self):
        self.config_options = {
            'high_accuracy': '--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz.,/:-@# ',
            'table_detection': '--oem 3 --psm 6',
            'single_line': '--oem 3 --psm 8',
            'single_word': '--oem 3 --psm 8',
            'numbers_only': '--oem 3 --psm 8 -c tessedit_char_whitelist=0123456789.,',
            'digits_and_text': '--oem 3 --psm 6'
        }
    
    def extract_text(self, image_path: str, config: str = 'high_accuracy') -> Tuple[str, float]:
        """
        Extract text using Tesseract
        Returns (text, confidence)
        """
        try:
            # Get configuration
            tesseract_config = self.config_options.get(config, self.config_options['high_accuracy'])
            
            # Extract text
            text = pytesseract.image_to_string(image_path, config=tesseract_config)
            
            # Get confidence data
            try:
                data = pytesseract.image_to_data(image_path, config=tesseract_config, output_type=pytesseract.Output.DICT)
                confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
                avg_confidence = sum(confidences) / len(confidences) if confidences else 0
            except:
                avg_confidence = 50.0  # Default confidence if calculation fails
            
            return text.strip(), avg_confidence
            
        except Exception as e:
            logger.error(f"Tesseract extraction failed: {e}")
            return "", 0.0
    
    def extract_with_coordinates(self, image_path: str) -> Dict:
        """Extract text with bounding box coordinates"""
        try:
            data = pytesseract.image_to_data(image_path, output_type=pytesseract.Output.DICT)
            
            results = []
            n_boxes = len(data['text'])
            
            for i in range(n_boxes):
                text = data['text'][i].strip()
                conf = int(data['conf'][i])
                
                if text and conf > 30:  # Only include text with reasonable confidence
                    results.append({
                        'text': text,
                        'confidence': conf,
                        'x': data['left'][i],
                        'y': data['top'][i],
                        'width': data['width'][i],
                        'height': data['height'][i],
                        'level': data['level'][i]
                    })
            
            return {
                'success': True,
                'text_blocks': results,
                'full_text': ' '.join([r['text'] for r in results])
            }
            
        except Exception as e:
            logger.error(f"Tesseract coordinate extraction failed: {e}")
            return {'success': False, 'error': str(e)}

class FieldExtractor:
    """Extract structured fields from OCR text using regex patterns"""
    
    def __init__(self):
        self.field_patterns = {
            # Invoice patterns
            'invoice_number': [
                r'invoice\s*(?:no|number)?[:\s]*([A-Z0-9/-]+)',
                r'inv\s*(?:no|#)?[:\s]*([A-Z0-9/-]+)',
                r'bill\s*(?:no|number)?[:\s]*([A-Z0-9/-]+)'
            ],
            'date': [
                r'date[:\s]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
                r'dated[:\s]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
                r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})'
            ],
            'amount': [
                r'total[:\s]*₹?\s*([0-9,]+\.?\d*)',
                r'amount[:\s]*₹?\s*([0-9,]+\.?\d*)',
                r'₹\s*([0-9,]+\.?\d*)'
            ],
            'gstin': [
                r'gstin[:\s]*([0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1})',
                r'gst\s*no[:\s]*([0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1})'
            ],
            # Purchase Order patterns
            'po_number': [
                r'po\s*(?:no|number)?[:\s]*([A-Z0-9/-]+)',
                r'purchase\s*order[:\s]*([A-Z0-9/-]+)',
                r'order\s*(?:no|number)?[:\s]*([A-Z0-9/-]+)'
            ],
            # Vendor/Customer patterns
            'vendor_name': [
                r'vendor[:\s]*([A-Za-z\s&.]+?)(?:\n|address|gstin)',
                r'supplier[:\s]*([A-Za-z\s&.]+?)(?:\n|address|gstin)',
                r'from[:\s]*([A-Za-z\s&.]+?)(?:\n|address|gstin)'
            ],
            'customer_name': [
                r'to[:\s]*([A-Za-z\s&.]+?)(?:\n|address|gstin)',
                r'customer[:\s]*([A-Za-z\s&.]+?)(?:\n|address|gstin)',
                r'bill\s*to[:\s]*([A-Za-z\s&.]+?)(?:\n|address|gstin)'
            ],
            # Quantity patterns
            'quantity': [
                r'qty[:\s]*(\d+(?:\.\d+)?)',
                r'quantity[:\s]*(\d+(?:\.\d+)?)',
                r'(\d+(?:\.\d+)?)\s*(?:pcs|nos|kg|mt)'
            ]
        }
    
    def extract_fields(self, text: str, document_type: str = 'general') -> Dict:
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
                        break  # Use first successful match
        
        # Post-process extracted values
        extracted = self._clean_extracted_fields(extracted)
        
        return extracted
    
    def extract_table_data(self, text: str) -> List[Dict]:
        """Extract table/line item data from text"""
        lines = text.split('\n')
        table_data = []
        
        # Look for lines that might be table rows
        # This is a simplified approach - in practice, you'd want more sophisticated table detection
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Try to identify table rows by structure
            parts = re.split(r'\s{2,}', line)  # Split on multiple spaces
            
            if len(parts) >= 3:  # Assume table has at least 3 columns
                # Try to extract: Item, Quantity, Rate, Amount
                row_data = {}
                
                # Look for quantity (numbers)
                for i, part in enumerate(parts):
                    if re.match(r'^\d+(?:\.\d+)?$', part.strip()):
                        if 'quantity' not in row_data:
                            row_data['quantity'] = float(part.strip())
                        elif 'rate' not in row_data:
                            row_data['rate'] = float(part.strip())
                        elif 'amount' not in row_data:
                            row_data['amount'] = float(part.strip())
                
                # First non-numeric part is likely the item name
                for part in parts:
                    if not re.match(r'^\d+(?:\.\d+)?$', part.strip()) and part.strip():
                        row_data['item_name'] = part.strip()
                        break
                
                if 'item_name' in row_data and 'quantity' in row_data:
                    table_data.append(row_data)
        
        return table_data
    
    def _clean_extracted_fields(self, fields: Dict) -> Dict:
        """Clean and normalize extracted field values"""
        cleaned = {}
        
        for key, value in fields.items():
            if isinstance(value, str):
                value = value.strip()
                
                # Clean amount values
                if key == 'amount':
                    value = re.sub(r'[^\d.]', '', value)
                    try:
                        value = float(value)
                    except:
                        pass
                
                # Clean quantity values
                elif key == 'quantity':
                    value = re.sub(r'[^\d.]', '', value)
                    try:
                        value = float(value)
                    except:
                        pass
                
                # Clean GSTIN
                elif key == 'gstin':
                    value = value.upper().replace(' ', '')
                
                # Clean invoice/PO numbers
                elif key in ['invoice_number', 'po_number']:
                    value = value.upper().strip()
                
            cleaned[key] = value
        
        return cleaned

class OCREngine:
    """Main OCR engine that orchestrates preprocessing and text extraction"""
    
    def __init__(self):
        self.preprocessor = ImagePreprocessor()
        self.tesseract = TesseractEngine()
        self.extractor = FieldExtractor()
        self.temp_dir = '/tmp/ocr_processing'
        os.makedirs(self.temp_dir, exist_ok=True)
    
    def process_document(self, file_path: str, module_type: str = 'general', 
                        use_preprocessing: bool = True, 
                        fallback_enabled: bool = True) -> OCRResult:
        """
        Main document processing pipeline
        """
        start_time = time.time()
        
        try:
            # Step 1: Convert PDF to images if needed
            processed_file_path = self._prepare_file(file_path)
            
            # Step 2: Preprocess image if enabled
            if use_preprocessing:
                processed_file_path = self.preprocessor.preprocess_image(processed_file_path)
            
            # Step 3: Extract text using Tesseract
            text, confidence = self.tesseract.extract_text(processed_file_path)
            
            processing_time = time.time() - start_time
            
            if not text.strip():
                return OCRResult(
                    success=False,
                    text="",
                    confidence=0.0,
                    processing_time=processing_time,
                    engine_used="tesseract",
                    error_message="No text extracted"
                )
            
            # Step 4: Extract structured fields
            extracted_fields = self.extractor.extract_fields(text, module_type)
            line_items = self.extractor.extract_table_data(text)
            
            return OCRResult(
                success=True,
                text=text,
                confidence=confidence,
                processing_time=processing_time,
                engine_used="tesseract",
                extracted_fields=extracted_fields,
                line_items=line_items
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"OCR processing failed: {e}")
            
            return OCRResult(
                success=False,
                text="",
                confidence=0.0,
                processing_time=processing_time,
                engine_used="tesseract",
                error_message=str(e)
            )
    
    def _prepare_file(self, file_path: str) -> str:
        """Prepare file for OCR (convert PDF to image if needed)"""
        file_ext = os.path.splitext(file_path)[1].lower()
        
        if file_ext == '.pdf':
            # Convert PDF to image using poppler-utils
            try:
                # First try with system PATH (should work with poppler-utils installed)
                images = convert_from_path(file_path, first_page=1, last_page=1, dpi=300)
                if images:
                    # Save first page as image
                    img_path = os.path.join(self.temp_dir, f"converted_{int(time.time())}.png")
                    images[0].save(img_path, 'PNG')
                    logger.info(f"Successfully converted PDF to image: {img_path}")
                    return img_path
                else:
                    raise ValueError("No pages found in PDF")
            except Exception as e:
                logger.error(f"PDF conversion failed: {e}")
                raise ValueError(f"Unable to process PDF file. Please try uploading the document as an image (PNG, JPG) instead. Error: {str(e)}")
        
        elif file_ext in ['.jpg', '.jpeg', '.png', '.tiff', '.bmp']:
            return file_path
        
        else:
            raise ValueError(f"Unsupported file format: {file_ext}")
    
    def cleanup_temp_files(self):
        """Clean up temporary processing files"""
        try:
            for file in os.listdir(self.temp_dir):
                file_path = os.path.join(self.temp_dir, file)
                if os.path.isfile(file_path):
                    os.remove(file_path)
        except Exception as e:
            logger.warning(f"Cleanup failed: {e}")

# Global OCR engine instance
ocr_engine = OCREngine()