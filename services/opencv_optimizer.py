"""
OpenCV integration for computer vision-enhanced packing optimization
Combines image processing with Rectpack and SVGNest algorithms
"""

import cv2
import numpy as np
import json
import tempfile
import os
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from PIL import Image, ImageDraw
import base64
from io import BytesIO

from services.packing_optimizer import MaterialOptimizer, PackingCalculator
from services.svgnest_optimizer import SVGNestOptimizer, VectorNestingCalculator

logger = logging.getLogger(__name__)

class OpenCVPackingIntegrator:
    """Advanced computer vision integration with packing optimization"""
    
    def __init__(self):
        self.material_optimizer = MaterialOptimizer()
        self.svgnest_optimizer = SVGNestOptimizer()
        
    def process_image_for_packing(self, image_path: str, processing_type: str = 'auto') -> Dict[str, Any]:
        """
        Process uploaded image to extract shapes for packing optimization
        
        Args:
            image_path: Path to uploaded image file
            processing_type: 'rectangular', 'irregular', or 'auto'
            
        Returns:
            Processed shapes ready for optimization
        """
        try:
            # Load and preprocess image
            image = cv2.imread(image_path)
            if image is None:
                return {'success': False, 'error': 'Could not load image'}
            
            # Image preprocessing pipeline
            processed_data = self._preprocess_image(image)
            
            # Extract shapes based on type
            if processing_type == 'auto':
                # Automatically determine shape complexity
                shapes = self._auto_detect_shapes(processed_data)
                processing_type = self._determine_optimal_algorithm(shapes)
            elif processing_type == 'rectangular':
                shapes = self._extract_rectangular_shapes(processed_data)
            else:  # irregular
                shapes = self._extract_irregular_shapes(processed_data)
            
            # Generate optimization recommendation
            recommendation = self._generate_optimization_recommendation(shapes, processing_type)
            
            return {
                'success': True,
                'processing_type': processing_type,
                'shapes_detected': len(shapes),
                'shapes': shapes,
                'recommendation': recommendation,
                'image_analysis': {
                    'original_size': image.shape[:2],
                    'detected_contours': len(shapes),
                    'complexity_score': self._calculate_complexity_score(shapes)
                }
            }
            
        except Exception as e:
            logger.error(f"Image processing error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _preprocess_image(self, image: np.ndarray) -> Dict[str, Any]:
        """Advanced image preprocessing pipeline"""
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Noise reduction
        denoised = cv2.medianBlur(gray, 5)
        
        # Edge detection with adaptive thresholding
        edges = cv2.adaptiveThreshold(denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                      cv2.THRESH_BINARY, 11, 2)
        
        # Morphological operations to clean up edges
        kernel = np.ones((3,3), np.uint8)
        cleaned = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)
        
        return {
            'original': image,
            'gray': gray,
            'denoised': denoised,
            'edges': edges,
            'cleaned': cleaned
        }
    
    def _auto_detect_shapes(self, processed_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Automatically detect and classify shapes"""
        contours, _ = cv2.findContours(processed_data['cleaned'], cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        shapes = []
        for i, contour in enumerate(contours):
            # Filter small contours
            area = cv2.contourArea(contour)
            if area < 100:  # Minimum area threshold
                continue
            
            # Analyze shape properties
            shape_data = self._analyze_shape(contour, i)
            if shape_data:
                shapes.append(shape_data)
        
        return shapes
    
    def _analyze_shape(self, contour: np.ndarray, shape_id: int) -> Optional[Dict[str, Any]]:
        """Analyze individual shape properties"""
        try:
            # Basic shape properties
            area = cv2.contourArea(contour)
            perimeter = cv2.arcLength(contour, True)
            
            # Bounding rectangle
            x, y, w, h = cv2.boundingRect(contour)
            
            # Approximate polygon
            epsilon = 0.02 * perimeter
            approx = cv2.approxPolyDP(contour, epsilon, True)
            
            # Shape classification
            shape_type = self._classify_shape(approx, area, perimeter)
            
            # Convert contour to polygon format
            polygon = self._contour_to_polygon(contour)
            
            return {
                'id': f'shape_{shape_id}',
                'type': shape_type,
                'area': float(area),
                'perimeter': float(perimeter),
                'bounding_box': {'x': int(x), 'y': int(y), 'width': int(w), 'height': int(h)},
                'vertices': len(approx),
                'polygon': polygon,
                'contour': contour.tolist(),
                'complexity_score': self._calculate_shape_complexity(approx, area, perimeter)
            }
            
        except Exception as e:
            logger.error(f"Shape analysis error: {str(e)}")
            return None
    
    def _classify_shape(self, approx: np.ndarray, area: float, perimeter: float) -> str:
        """Classify shape based on geometric properties"""
        vertices = len(approx)
        
        # Calculate circularity
        circularity = 4 * np.pi * area / (perimeter * perimeter) if perimeter > 0 else 0
        
        if vertices == 3:
            return 'triangle'
        elif vertices == 4:
            # Check if rectangle
            x, y, w, h = cv2.boundingRect(approx)
            aspect_ratio = float(w) / h
            rect_area = w * h
            extent = float(area) / rect_area
            
            if extent > 0.95 and 0.5 < aspect_ratio < 2.0:
                return 'rectangle'
            else:
                return 'quadrilateral'
        elif vertices < 8 and circularity > 0.7:
            return 'circle'
        elif vertices >= 8:
            if circularity > 0.8:
                return 'circle'
            else:
                return 'complex_polygon'
        else:
            return 'irregular'
    
    def _calculate_shape_complexity(self, approx: np.ndarray, area: float, perimeter: float) -> float:
        """Calculate complexity score for shape (0-1, higher = more complex)"""
        vertices = len(approx)
        circularity = 4 * np.pi * area / (perimeter * perimeter) if perimeter > 0 else 0
        
        # Base complexity on vertex count and circularity
        vertex_complexity = min(vertices / 20.0, 1.0)  # Normalize to 0-1
        circularity_complexity = 1.0 - circularity  # Lower circularity = higher complexity
        
        return (vertex_complexity + circularity_complexity) / 2.0
    
    def _contour_to_polygon(self, contour: np.ndarray) -> List[Dict[str, float]]:
        """Convert OpenCV contour to polygon format"""
        # Simplify contour for better performance
        epsilon = 0.01 * cv2.arcLength(contour, True)
        simplified = cv2.approxPolyDP(contour, epsilon, True)
        
        polygon = []
        for point in simplified:
            polygon.append({
                'x': float(point[0][0]),
                'y': float(point[0][1])
            })
        
        return polygon
    
    def _extract_rectangular_shapes(self, processed_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract rectangular shapes optimized for Rectpack"""
        contours, _ = cv2.findContours(processed_data['cleaned'], cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        rectangles = []
        for i, contour in enumerate(contours):
            area = cv2.contourArea(contour)
            if area < 100:
                continue
            
            # Get bounding rectangle
            x, y, w, h = cv2.boundingRect(contour)
            
            # Check if shape is roughly rectangular
            contour_area = cv2.contourArea(contour)
            rect_area = w * h
            extent = float(contour_area) / rect_area if rect_area > 0 else 0
            
            if extent > 0.7:  # At least 70% rectangular
                rectangles.append({
                    'id': f'rect_{i}',
                    'width': w,
                    'height': h,
                    'area': contour_area,
                    'position': {'x': x, 'y': y},
                    'extent': extent,
                    'algorithm': 'rectpack'
                })
        
        return rectangles
    
    def _extract_irregular_shapes(self, processed_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract irregular shapes optimized for SVGNest"""
        return self._auto_detect_shapes(processed_data)
    
    def _determine_optimal_algorithm(self, shapes: List[Dict[str, Any]]) -> str:
        """Determine optimal algorithm based on shape analysis"""
        if not shapes:
            return 'rectpack'
        
        # Calculate average complexity
        total_complexity = sum(shape.get('complexity_score', 0) for shape in shapes)
        avg_complexity = total_complexity / len(shapes)
        
        # Count shape types
        rectangular_count = sum(1 for shape in shapes if shape.get('type') in ['rectangle', 'quadrilateral'])
        irregular_count = len(shapes) - rectangular_count
        
        # Decision logic
        if avg_complexity < 0.3 and rectangular_count > irregular_count:
            return 'rectpack'
        elif avg_complexity > 0.6 or irregular_count > rectangular_count:
            return 'svgnest'
        else:
            return 'hybrid'  # Use both algorithms
    
    def _calculate_complexity_score(self, shapes: List[Dict[str, Any]]) -> float:
        """Calculate overall complexity score for all shapes"""
        if not shapes:
            return 0.0
        
        total_complexity = sum(shape.get('complexity_score', 0) for shape in shapes)
        return total_complexity / len(shapes)
    
    def _generate_optimization_recommendation(self, shapes: List[Dict[str, Any]], 
                                            processing_type: str) -> Dict[str, Any]:
        """Generate optimization recommendations based on analysis"""
        recommendation = {
            'algorithm': processing_type,
            'estimated_savings': '5-15%' if processing_type == 'rectpack' else '15-30%',
            'processing_time': 'Fast' if processing_type == 'rectpack' else 'Medium',
            'best_for': []
        }
        
        if processing_type == 'rectpack':
            recommendation['best_for'] = [
                'Sheet metal cutting',
                'Wood panel optimization',
                'Glass cutting',
                'Simple rectangular parts'
            ]
        elif processing_type == 'svgnest':
            recommendation['best_for'] = [
                'Laser cutting',
                'Complex CNC parts',
                'Irregular geometries',
                'Custom brackets and fittings'
            ]
        else:  # hybrid
            recommendation['best_for'] = [
                'Mixed part types',
                'Complex production runs',
                'Multi-material cutting',
                'Advanced optimization'
            ]
        
        return recommendation
    
    def optimize_with_opencv_analysis(self, image_path: str, bin_config: Dict[str, Any], 
                                     optimization_config: Optional[Dict] = None) -> Dict[str, Any]:
        """Complete optimization workflow with OpenCV analysis"""
        try:
            # Process image to extract shapes
            image_analysis = self.process_image_for_packing(image_path)
            
            if not image_analysis['success']:
                return image_analysis
            
            shapes = image_analysis['shapes']
            processing_type = image_analysis['processing_type']
            
            # Run appropriate optimization
            if processing_type == 'rectpack':
                result = self._optimize_with_rectpack(shapes, bin_config, optimization_config)
            elif processing_type == 'svgnest':
                result = self._optimize_with_svgnest(shapes, bin_config, optimization_config)
            else:  # hybrid
                result = self._optimize_hybrid(shapes, bin_config, optimization_config)
            
            # Combine results
            result['opencv_analysis'] = image_analysis
            result['processing_type'] = processing_type
            
            return result
            
        except Exception as e:
            logger.error(f"OpenCV optimization error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _optimize_with_rectpack(self, shapes: List[Dict[str, Any]], 
                               bin_config: Dict[str, Any], 
                               config: Optional[Dict] = None) -> Dict[str, Any]:
        """Optimize rectangular shapes with Rectpack"""
        # Convert shapes to Rectpack format
        rectangles = []
        for shape in shapes:
            if 'width' in shape and 'height' in shape:
                rectangles.append((shape['width'], shape['height']))
            elif 'bounding_box' in shape:
                bb = shape['bounding_box']
                rectangles.append((bb['width'], bb['height']))
        
        if not rectangles:
            return {'success': False, 'error': 'No rectangular shapes found'}
        
        # Use existing Rectpack optimization
        bin_width = bin_config.get('width', 1200)
        bin_height = bin_config.get('height', 800)
        algorithm = config.get('algorithm', 'skyline') if config else 'skyline'
        
        # Use existing Rectpack optimization with proper method
        from services.packing_optimizer import MaterialOptimizer
        optimizer = MaterialOptimizer(algorithm=algorithm)
        
        # Convert rectangles to parts format
        parts = []
        for rect in rectangles:
            parts.append({
                'width': rect['width'],
                'height': rect['height'],
                'item_name': rect['id'],
                'quantity': 1
            })
        
        result = optimizer.optimize_sheet_cutting(parts, (bin_width, bin_height), 5)
        result['opencv_enhanced'] = True
        
        return result
    
    def _optimize_with_svgnest(self, shapes: List[Dict[str, Any]], 
                              bin_config: Dict[str, Any], 
                              config: Optional[Dict] = None) -> Dict[str, Any]:
        """Optimize irregular shapes with SVGNest"""
        # Convert shapes to SVGNest format
        parts = []
        for i, shape in enumerate(shapes):
            if 'polygon' in shape:
                parts.append({
                    'id': shape.get('id', f'part_{i}'),
                    'name': f"Shape {i+1}",
                    'polygon': shape['polygon'],
                    'quantity': 1
                })
        
        if not parts:
            return {'success': False, 'error': 'No irregular shapes found'}
        
        # Create bin polygon
        bin_width = bin_config.get('width', 1200)
        bin_height = bin_config.get('height', 800)
        bin_polygon = [
            {'x': 0, 'y': 0},
            {'x': bin_width, 'y': 0},
            {'x': bin_width, 'y': bin_height},
            {'x': 0, 'y': bin_height}
        ]
        
        # Use existing SVGNest optimization
        options = config or {}
        result = self.svgnest_optimizer.optimize_vector_nesting(bin_polygon, parts, options)
        result['opencv_enhanced'] = True
        
        return result
    
    def _optimize_hybrid(self, shapes: List[Dict[str, Any]], 
                        bin_config: Dict[str, Any], 
                        config: Optional[Dict] = None) -> Dict[str, Any]:
        """Hybrid optimization using both algorithms"""
        # Separate rectangular and irregular shapes
        rectangular_shapes = [s for s in shapes if s.get('type') in ['rectangle', 'quadrilateral']]
        irregular_shapes = [s for s in shapes if s not in rectangular_shapes]
        
        results = {
            'success': True,
            'algorithm': 'hybrid',
            'opencv_enhanced': True,
            'rectangular_optimization': None,
            'irregular_optimization': None,
            'combined_efficiency': 0
        }
        
        # Optimize rectangular shapes with Rectpack
        if rectangular_shapes:
            rect_result = self._optimize_with_rectpack(rectangular_shapes, bin_config, config)
            results['rectangular_optimization'] = rect_result
        
        # Optimize irregular shapes with SVGNest
        if irregular_shapes:
            irreg_result = self._optimize_with_svgnest(irregular_shapes, bin_config, config)
            results['irregular_optimization'] = irreg_result
        
        # Calculate combined efficiency
        total_efficiency = 0
        count = 0
        
        if results['rectangular_optimization'] and results['rectangular_optimization'].get('success'):
            total_efficiency += results['rectangular_optimization'].get('efficiency_percentage', 0)
            count += 1
            
        if results['irregular_optimization'] and results['irregular_optimization'].get('success'):
            total_efficiency += results['irregular_optimization'].get('efficiency_percentage', 0)
            count += 1
        
        if count > 0:
            results['combined_efficiency'] = total_efficiency / count
        
        return results
    
    def create_visual_analysis(self, image_path: str, shapes: List[Dict[str, Any]]) -> str:
        """Create visual analysis overlay showing detected shapes"""
        try:
            # Load original image
            image = cv2.imread(image_path)
            overlay = image.copy()
            
            # Draw detected shapes
            for i, shape in enumerate(shapes):
                color = self._get_shape_color(shape.get('type', 'unknown'))
                
                if 'contour' in shape:
                    # Draw contour
                    contour = np.array(shape['contour'])
                    cv2.drawContours(overlay, [contour], -1, color, 2)
                    
                    # Add label
                    if 'bounding_box' in shape:
                        bb = shape['bounding_box']
                        cv2.putText(overlay, f"{shape.get('type', 'shape')} {i+1}", 
                                   (bb['x'], bb['y'] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
            
            # Save analysis image
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            analysis_path = f"/tmp/opencv_analysis_{timestamp}.jpg"
            cv2.imwrite(analysis_path, overlay)
            
            return analysis_path
            
        except Exception as e:
            logger.error(f"Visual analysis error: {str(e)}")
            return ""
    
    def _get_shape_color(self, shape_type: str) -> Tuple[int, int, int]:
        """Get color for shape type visualization"""
        colors = {
            'rectangle': (0, 255, 0),      # Green
            'circle': (255, 0, 0),         # Blue
            'triangle': (0, 255, 255),     # Yellow
            'irregular': (255, 0, 255),    # Magenta
            'complex_polygon': (128, 0, 128),  # Purple
            'quadrilateral': (0, 128, 255)     # Orange
        }
        return colors.get(shape_type, (255, 255, 255))  # White default

class ComputerVisionAnalyzer:
    """Advanced computer vision analysis for manufacturing optimization"""
    
    @staticmethod
    def analyze_material_texture(image_path: str) -> Dict[str, Any]:
        """Analyze material texture and surface properties"""
        try:
            image = cv2.imread(image_path)
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Texture analysis using Local Binary Patterns
            # This would help determine optimal cutting parameters
            
            return {
                'texture_uniformity': 0.8,  # Placeholder
                'surface_roughness': 'smooth',
                'material_type_prediction': 'metal',
                'cutting_recommendation': 'laser_suitable'
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    @staticmethod
    def detect_defects_and_holes(image_path: str) -> Dict[str, Any]:
        """Detect defects, holes, and unusable areas in material"""
        try:
            image = cv2.imread(image_path)
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Blob detection for holes and defects using HoughCircles for better compatibility
            circles = cv2.HoughCircles(gray, cv2.HOUGH_GRADIENT, 1, 20,
                                     param1=50, param2=30, minRadius=1, maxRadius=30)
            
            defects = []
            if circles is not None:
                circles = np.round(circles[0, :]).astype("int")
                for (x, y, r) in circles:
                    defects.append({
                        'position': {'x': float(x), 'y': float(y)},
                        'size': float(r * 2),  # diameter
                        'type': 'hole_or_defect'
                    })
            
            return {
                'defects_found': len(defects),
                'defects': defects,
                'usable_area_percentage': max(0, 100 - len(defects) * 2)
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    @staticmethod
    def calculate_cutting_kerf_compensation(material_type: str, thickness: float) -> Dict[str, float]:
        """Calculate kerf compensation for different cutting methods"""
        kerf_database = {
            'laser_steel': 0.1 + (thickness * 0.05),
            'laser_aluminum': 0.08 + (thickness * 0.04),
            'plasma_steel': 1.0 + (thickness * 0.1),
            'waterjet': 0.05 + (thickness * 0.02)
        }
        
        return {
            'laser_kerf': kerf_database.get('laser_steel', 0.1),
            'plasma_kerf': kerf_database.get('plasma_steel', 1.0),
            'waterjet_kerf': kerf_database.get('waterjet', 0.05),
            'recommended_spacing': kerf_database.get('laser_steel', 0.1) * 2
        }