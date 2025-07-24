"""
Smart Weight Display Service
Handles intelligent weight display based on quantity ranges
"""

class SmartWeightDisplay:
    """
    Provides intelligent weight display formatting based on quantity ranges
    """
    
    @staticmethod
    def format_weight_display(weight_kg, include_alternatives=True):
        """
        Format weight display based on intelligent ranges:
        - Above 1000kg: Show in tons
        - Below 1kg: Show in grams  
        - Between 1kg-1000kg: Show in kg
        """
        if weight_kg is None or weight_kg == 0:
            return "0 kg"
            
        # Primary display based on range
        if weight_kg >= 1000:
            # Large quantities - show in tons
            tons = weight_kg / 1000
            primary = f"{tons:.3f} ton{'s' if tons != 1 else ''}"
            secondary = f"({weight_kg:.1f} kg)" if include_alternatives else ""
            
        elif weight_kg < 1:
            # Small quantities - show in grams
            grams = weight_kg * 1000
            primary = f"{grams:.1f} g"
            secondary = f"({weight_kg:.3f} kg)" if include_alternatives else ""
            
        else:
            # Medium range - show in kg
            primary = f"{weight_kg:.2f} kg"
            secondary = ""
            
            # Add alternative displays for context
            if include_alternatives:
                if weight_kg >= 500:  # Close to ton range
                    tons = weight_kg / 1000
                    secondary = f"(≈{tons:.3f} tons)"
                elif weight_kg <= 5:  # Close to gram range
                    grams = weight_kg * 1000
                    secondary = f"({grams:.0f} g)"
        
        return f"{primary} {secondary}".strip()
    
    @staticmethod
    def get_optimal_unit(weight_kg):
        """
        Get the optimal unit for a given weight
        """
        if weight_kg is None or weight_kg == 0:
            return 'kg'
        elif weight_kg >= 1000:
            return 'ton'
        elif weight_kg < 1:
            return 'g'
        else:
            return 'kg'
    
    @staticmethod
    def convert_to_optimal_unit(weight_kg):
        """
        Convert weight to its optimal unit and return value with unit
        """
        if weight_kg is None or weight_kg == 0:
            return {'value': 0, 'unit': 'kg'}
            
        if weight_kg >= 1000:
            return {'value': weight_kg / 1000, 'unit': 'ton'}
        elif weight_kg < 1:
            return {'value': weight_kg * 1000, 'unit': 'g'}
        else:
            return {'value': weight_kg, 'unit': 'kg'}
    
    @staticmethod
    def format_inventory_weight(item, include_pieces=True):
        """
        Format inventory weight display for items with intelligent unit selection
        """
        if not hasattr(item, 'current_stock') or not item.current_stock:
            return "No stock"
            
        # Calculate total weight
        total_weight_kg = 0
        if hasattr(item, 'total_weight_kg'):
            total_weight_kg = item.total_weight_kg
        elif hasattr(item, 'unit_weight') and item.unit_weight:
            if item.unit_of_measure == 'kg':
                total_weight_kg = item.current_stock
            elif item.unit_of_measure == 'pcs' and item.unit_weight:
                total_weight_kg = item.current_stock * item.unit_weight
        
        # Format primary weight display
        weight_display = SmartWeightDisplay.format_weight_display(total_weight_kg)
        
        # Add piece information if applicable
        if include_pieces and hasattr(item, 'unit_weight') and item.unit_weight and item.unit_of_measure == 'kg':
            pieces = int(item.current_stock / item.unit_weight) if item.unit_weight > 0 else 0
            piece_info = f" | ≈{pieces} pieces"
            weight_display += piece_info
            
        return weight_display
    
    @staticmethod
    def suggest_conversion_units(current_unit, quantity=None):
        """
        Suggest conversion units based on current unit and quantity
        """
        suggestions = []
        
        if current_unit == 'kg':
            suggestions.append('g')
            suggestions.append('ton')
            suggestions.append('pcs')  # If item has unit weight
            
        elif current_unit == 'g':
            suggestions.append('kg')
            if quantity and quantity >= 1000000:  # 1000kg worth
                suggestions.append('ton')
                
        elif current_unit == 'ton':
            suggestions.append('kg')
            suggestions.append('g')
            
        elif current_unit == 'pcs':
            suggestions.append('kg')  # If item has unit weight
            suggestions.append('g')
            suggestions.append('ton')
            
        return suggestions