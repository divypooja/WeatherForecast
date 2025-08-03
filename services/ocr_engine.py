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
            opencv_image = image.copy()  # Initialize opencv_image
            
            # Step 1: Resize for optimal OCR (if too small)
            height, width = opencv_image.shape[:2]
            if height < 600 or width < 600:
                scale_factor = max(600/height, 600/width, 1.5)
                new_width = int(width * scale_factor)
                new_height = int(height * scale_factor)
                opencv_image = cv2.resize(opencv_image, (new_width, new_height), interpolation=cv2.INTER_CUBIC)
                logger.info(f"Resized image from {width}x{height} to {new_width}x{new_height}")
            
            # Step 2: Enhance contrast and brightness
            pil_image = Image.fromarray(cv2.cvtColor(opencv_image, cv2.COLOR_BGR2RGB))
            pil_image = ImagePreprocessor._enhance_contrast(pil_image)
            
            # Convert back to OpenCV format
            opencv_image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
            
            # Step 3: Advanced noise reduction
            opencv_image = ImagePreprocessor._reduce_noise(opencv_image)
            
            # Step 4: Deskew correction
            opencv_image = ImagePreprocessor._correct_skew(opencv_image)
            
            # Step 5: Advanced binarization with multiple methods
            opencv_image = ImagePreprocessor._advanced_binarize(opencv_image)
            
            # Step 6: Morphological operations
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
        """Enhanced contrast and brightness adjustment"""
        # Convert to numpy for histogram analysis
        img_array = np.array(image)
        
        # Calculate optimal enhancement factors based on histogram
        hist = np.histogram(img_array.flatten(), bins=256, range=(0, 256))[0]
        total_pixels = img_array.size
        
        # Calculate cumulative distribution
        cumsum = np.cumsum(hist)
        normalized_cumsum = cumsum / total_pixels
        
        # Find 5th and 95th percentiles for contrast stretching
        p5 = np.where(normalized_cumsum >= 0.05)[0]
        p95 = np.where(normalized_cumsum >= 0.95)[0]
        
        if len(p5) > 0 and len(p95) > 0:
            low_val = p5[0]
            high_val = p95[0]
            
            # Determine enhancement factors based on dynamic range
            if high_val - low_val < 100:  # Low contrast
                contrast_factor = 1.5
                brightness_factor = 1.2
            else:  # Good contrast
                contrast_factor = 1.2
                brightness_factor = 1.1
        else:
            contrast_factor = 1.3
            brightness_factor = 1.1
        
        # Apply enhancements
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(contrast_factor)
        
        enhancer = ImageEnhance.Brightness(image)
        image = enhancer.enhance(brightness_factor)
        
        # Always apply sharpening for text
        enhancer = ImageEnhance.Sharpness(image)
        image = enhancer.enhance(1.4)
        
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
    
    @staticmethod
    def _advanced_binarize(image: np.ndarray) -> np.ndarray:
        """Advanced binarization with multiple techniques"""
        # Convert to grayscale if needed
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()
        
        # Method 1: Adaptive threshold (Gaussian)
        binary1 = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                       cv2.THRESH_BINARY, 11, 2)
        
        # Method 2: Adaptive threshold (Mean)
        binary2 = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, 
                                       cv2.THRESH_BINARY, 15, 3)
        
        # Method 3: Otsu's thresholding
        _, binary3 = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Method 4: Triangle thresholding
        _, binary4 = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_TRIANGLE)
        
        # Method 5: Combined approach with blur
        blur = cv2.GaussianBlur(gray, (3, 3), 0)
        _, binary5 = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Evaluate each method and choose the best
        methods = [binary1, binary2, binary3, binary4, binary5]
        scores = []
        
        for binary in methods:
            # Calculate text-to-background ratio
            white_pixels = np.sum(binary == 255)
            total_pixels = binary.size
            ratio = white_pixels / total_pixels
            
            # Calculate edge density (more edges typically means better text separation)
            edges = cv2.Canny(binary, 50, 150)
            edge_density = np.sum(edges > 0) / total_pixels
            
            # Score combines good background ratio (70-90%) and high edge density
            ratio_score = 1 - abs(ratio - 0.8)  # Prefer ~80% background
            edge_score = min(edge_density * 10, 1.0)  # Normalize edge density
            combined_score = (ratio_score * 0.6) + (edge_score * 0.4)
            scores.append(combined_score)
        
        # Select the best method
        best_idx = scores.index(max(scores))
        best_binary = methods[best_idx]
        
        logger.info(f"Selected binarization method {best_idx + 1} with score {max(scores):.3f}")
        return best_binary

class TesseractEngine:
    """Tesseract OCR engine wrapper"""
    
    def __init__(self):
        self.config_options = {
            'ultra_high_accuracy': '--oem 1 --psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz.,/:-@#%()[]{}+=₹ ',
            'high_accuracy': '--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz.,/:-@#%()[]{}+=₹ ',
            'document_layout': '--oem 3 --psm 4',
            'sparse_text': '--oem 3 --psm 6',
            'single_block': '--oem 3 --psm 7',
            'single_line': '--oem 3 --psm 8',
            'single_word': '--oem 3 --psm 8',
            'numbers_only': '--oem 3 --psm 8 -c tessedit_char_whitelist=0123456789.,₹',
            'digits_and_text': '--oem 3 --psm 6'
        }
    
    def extract_text(self, image_path: str, config: str = 'high_accuracy') -> Tuple[str, float]:
        """
        Extract text using Tesseract with multiple attempts for best accuracy
        Returns (text, confidence)
        """
        try:
            # Try multiple configurations and select the best result
            configs_to_try = [
                ('ultra_high_accuracy', config),
                ('high_accuracy', config),
                ('document_layout', 'document_layout'),
                ('sparse_text', 'sparse_text')
            ]
            
            best_text = ""
            best_confidence = 0.0
            best_config = config
            
            for config_name, fallback_config in configs_to_try:
                try:
                    tesseract_config = self.config_options.get(config_name, self.config_options[fallback_config])
                    
                    # Extract text
                    text = pytesseract.image_to_string(image_path, config=tesseract_config)
                    
                    # Get confidence data with weighted calculation
                    try:
                        data = pytesseract.image_to_data(image_path, config=tesseract_config, output_type=pytesseract.Output.DICT)
                        
                        # Calculate weighted confidence (longer words get more weight)
                        total_weight = 0
                        weighted_conf = 0
                        
                        for i, conf in enumerate(data['conf']):
                            word = data['text'][i].strip()
                            if word and int(conf) > 0:
                                word_weight = len(word)
                                weighted_conf += int(conf) * word_weight
                                total_weight += word_weight
                        
                        avg_confidence = weighted_conf / total_weight if total_weight > 0 else 0
                        
                    except:
                        # Fallback confidence calculation
                        confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
                        avg_confidence = sum(confidences) / len(confidences) if confidences else 0
                    
                    # Select result with best combination of confidence and text length
                    score = avg_confidence * (1 + len(text.strip()) / 1000)  # Slight bias for longer text
                    best_score = best_confidence * (1 + len(best_text.strip()) / 1000)
                    
                    if score > best_score and len(text.strip()) > 5:
                        best_text = text.strip()
                        best_confidence = avg_confidence
                        best_config = config_name
                        logger.info(f"Better result with {config_name}: {avg_confidence:.1f}% confidence")
                
                except Exception as config_error:
                    logger.warning(f"Config {config_name} failed: {config_error}")
                    continue
            
            # If no good result found, try the original config
            if not best_text:
                tesseract_config = self.config_options.get(config, self.config_options['high_accuracy'])
                best_text = pytesseract.image_to_string(image_path, config=tesseract_config)
                data = pytesseract.image_to_data(image_path, config=tesseract_config, output_type=pytesseract.Output.DICT)
                confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
                best_confidence = sum(confidences) / len(confidences) if confidences else 50.0
            
            logger.info(f"Final OCR result using {best_config}: {best_confidence:.1f}% confidence, {len(best_text)} chars")
            return best_text, best_confidence
            
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
            # Invoice patterns - enhanced with more variations
            'invoice_number': [
                r'invoice\s*(?:no|number|#)?[:\s]*([A-Z0-9/-]+)',
                r'inv\s*(?:no|#|number)?[:\s]*([A-Z0-9/-]+)',
                r'bill\s*(?:no|number|#)?[:\s]*([A-Z0-9/-]+)',
                r'receipt\s*(?:no|number|#)?[:\s]*([A-Z0-9/-]+)',
                r'voucher\s*(?:no|number|#)?[:\s]*([A-Z0-9/-]+)'
            ],
            'date': [
                r'invoice\s*date[:\s]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
                r'bill\s*date[:\s]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
                r'date[:\s]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
                r'dated[:\s]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
                r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
                r'(\d{2}[/-]\d{2}[/-]\d{4})',
                r'(\d{4}[/-]\d{2}[/-]\d{2})',
                r'(\d{1,2}\s+[a-zA-Z]{3,9}\s+\d{2,4})'  # "15 March 2025"
            ],
            'amount': [
                r'(?:total|grand\s*total|net\s*amount)[:\s]*₹?\s*([0-9,]+\.?\d*)',
                r'(?:amount|total\s*amount)[:\s]*₹?\s*([0-9,]+\.?\d*)',
                r'₹\s*([0-9,]+\.?\d*)',
                r'rs\.?\s*([0-9,]+\.?\d*)',
                r'inr\s*([0-9,]+\.?\d*)',
                r'([0-9,]+\.?\d*)\s*/-',
                r'([0-9,]+\.?\d*)\s*only'
            ],
            'gstin': [
                r'gstin[:\s]*([0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1})',
                r'gst\s*(?:no|number|registration)[:\s]*([0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1})',
                r'tin[:\s]*([0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1})',
                r'([0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1})'  # Direct GSTIN pattern
            ],
            # Purchase Order patterns
            'po_number': [
                r'po\s*(?:no|number|#)?[:\s]*([A-Z0-9/-]+)',
                r'purchase\s*order\s*(?:no|number|#)?[:\s]*([A-Z0-9/-]+)',
                r'order\s*(?:no|number|#)?[:\s]*([A-Z0-9/-]+)',
                r'ref\s*(?:no|number)?[:\s]*([A-Z0-9/-]+)'
            ],
            # Vendor/Customer patterns - improved to capture more variations
            'vendor_name': [
                r'vendor[:\s]*([A-Za-z\s&.,()]+?)(?:\n|address|gstin|phone)',
                r'supplier[:\s]*([A-Za-z\s&.,()]+?)(?:\n|address|gstin|phone)',
                r'from[:\s]*([A-Za-z\s&.,()]+?)(?:\n|address|gstin|phone)',
                r'billed\s*by[:\s]*([A-Za-z\s&.,()]+?)(?:\n|address|gstin|phone)'
            ],
            'customer_name': [
                r'to[:\s]*([A-Za-z\s&.,()]+?)(?:\n|address|gstin|phone)',
                r'customer[:\s]*([A-Za-z\s&.,()]+?)(?:\n|address|gstin|phone)',
                r'bill\s*to[:\s]*([A-Za-z\s&.,()]+?)(?:\n|address|gstin|phone)',
                r'ship\s*to[:\s]*([A-Za-z\s&.,()]+?)(?:\n|address|gstin|phone)'
            ],
            # Quantity patterns
            'quantity': [
                r'qty[:\s]*(\d+(?:\.\d+)?)',
                r'quantity[:\s]*(\d+(?:\.\d+)?)',
                r'(\d+(?:\.\d+)?)\s*(?:pcs|nos|kg|mt|units|pieces)',
                r'(\d+(?:\.\d+)?)\s*(?:pc|no|piece)'
            ],
            # Additional patterns for better extraction
            'tax_amount': [
                r'(?:tax|gst|vat)[:\s]*₹?\s*([0-9,]+\.?\d*)',
                r'(?:cgst|sgst|igst)[:\s]*₹?\s*([0-9,]+\.?\d*)'
            ],
            'discount': [
                r'discount[:\s]*₹?\s*([0-9,]+\.?\d*)',
                r'less[:\s]*₹?\s*([0-9,]+\.?\d*)'
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
            
            # Step 3: Extract text using Tesseract with enhanced configuration
            text, confidence = self.tesseract.extract_text(processed_file_path, config='high_accuracy')
            
            processing_time = time.time() - start_time
            
            # If confidence is low, try alternative processing
            if confidence < 60.0 and use_preprocessing:
                logger.info(f"Low confidence ({confidence:.1f}%), trying alternative processing")
                # Try without preprocessing
                alt_text, alt_confidence = self.tesseract.extract_text(file_path, config='high_accuracy')
                if alt_confidence > confidence:
                    text, confidence = alt_text, alt_confidence
                    logger.info(f"Alternative processing improved confidence to {confidence:.1f}%")
            
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
            
            # Debug logging
            logger.info(f"OCR Text Length: {len(text)} chars")
            logger.info(f"OCR Text Sample: {text[:200]}...")
            logger.info(f"Extracted {len(extracted_fields)} fields: {list(extracted_fields.keys())}")
            for field, value in extracted_fields.items():
                logger.info(f"  {field}: {value}")
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