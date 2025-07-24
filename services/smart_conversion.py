"""
Smart Conversion Service
Integrates UOM, BOM, and Inventory systems for intelligent unit conversions
"""

from models import Item, db
from models_uom import UOMConversion, ItemUOMConversion
import logging

logger = logging.getLogger(__name__)

class SmartConversionService:
    """
    Handles smart conversions between UOM, BOM, and Inventory systems
    """
    
    @staticmethod
    def convert_quantity(item, quantity, from_unit, to_unit):
        """
        Smart quantity conversion using multiple conversion methods
        Priority: Item-specific > UOM System > Default
        """
        if from_unit == to_unit:
            return quantity
            
        # Method 1: Item-specific conversions (highest priority)
        if hasattr(item, 'unit_weight') and item.unit_weight:
            if from_unit == 'kg' and to_unit in ['pcs', 'pieces']:
                return quantity / item.unit_weight if item.unit_weight > 0 else 0
            elif from_unit in ['pcs', 'pieces'] and to_unit == 'kg':
                return quantity * item.unit_weight
        
        # Method 2: Item-specific UOM conversions
        item_conversion = ItemUOMConversion.query.filter_by(
            item_id=item.id,
            from_unit=from_unit,
            to_unit=to_unit
        ).first()
        
        if item_conversion:
            return quantity * item_conversion.conversion_factor
            
        # Method 3: Standard UOM conversions
        uom_conversion = UOMConversion.query.filter_by(
            from_unit=from_unit,
            to_unit=to_unit
        ).first()
        
        if uom_conversion:
            return quantity * uom_conversion.factor
            
        # Method 4: Try reverse conversion
        reverse_conversion = UOMConversion.query.filter_by(
            from_unit=to_unit,
            to_unit=from_unit
        ).first()
        
        if reverse_conversion and reverse_conversion.factor > 0:
            return quantity / reverse_conversion.factor
            
        # Method 5: Trading-specific conversions
        if hasattr(item, 'business_type') and item.business_type == 'trading':
            if hasattr(item, 'purchase_unit') and hasattr(item, 'sale_unit'):
                if from_unit == item.purchase_unit and to_unit == item.sale_unit:
                    return item.get_available_for_sale() if quantity == item.current_stock else quantity
                    
        logger.warning(f"No conversion found from {from_unit} to {to_unit} for item {item.name}")
        return quantity  # No conversion available
    
    @staticmethod
    def check_material_availability(item, required_qty, required_unit=None):
        """
        Check material availability with smart unit conversion
        """
        if required_unit is None:
            required_unit = item.unit_of_measure
        
        # Convert required quantity to inventory unit
        required_in_inventory_unit = SmartConversionService.convert_quantity(
            item, required_qty, required_unit, item.unit_of_measure
        )
        
        available_stock = item.current_stock or 0
        is_available = available_stock >= required_in_inventory_unit
        shortage = max(0, required_in_inventory_unit - available_stock)
        
        # Convert shortage back to required unit for user-friendly display
        shortage_in_required_unit = SmartConversionService.convert_quantity(
            item, shortage, item.unit_of_measure, required_unit
        ) if shortage > 0 else 0
        
        return {
            'available': is_available,
            'available_stock': available_stock,
            'available_unit': item.unit_of_measure,
            'required_qty': required_qty,
            'required_unit': required_unit,
            'required_in_inventory_unit': required_in_inventory_unit,
            'shortage': shortage,
            'shortage_in_required_unit': shortage_in_required_unit,
            'conversion_info': f"{required_qty} {required_unit} = {required_in_inventory_unit:.3f} {item.unit_of_measure}"
        }
    
    @staticmethod
    def calculate_bom_requirements(bom, production_quantity):
        """
        Calculate BOM material requirements with smart conversions
        """
        requirements = []
        
        for bom_item in bom.bom_items:
            material = bom_item.material
            if not material:
                continue
                
            # Calculate required quantity in BOM unit
            required_qty_bom = bom_item.quantity * production_quantity
            bom_unit = bom_item.bom_unit.symbol if bom_item.bom_unit else material.unit_of_measure
            
            # Check availability with smart conversion
            availability = SmartConversionService.check_material_availability(
                material, required_qty_bom, bom_unit
            )
            
            requirements.append({
                'material': material,
                'bom_unit': bom_unit,
                'required_qty_bom_unit': required_qty_bom,
                'required_qty_inventory_unit': availability['required_in_inventory_unit'],
                'available_stock': availability['available_stock'],
                'inventory_unit': material.unit_of_measure,
                'is_sufficient': availability['available'],
                'shortage': availability['shortage'],
                'shortage_in_bom_unit': availability['shortage_in_required_unit'],
                'unit_cost': bom_item.unit_cost or 0,
                'total_cost': required_qty_bom * (bom_item.unit_cost or 0),
                'conversion_info': availability['conversion_info'],
                'notes': bom_item.notes or ''
            })
        
        return requirements
    
    @staticmethod
    def update_inventory_after_production(bom, production_quantity, actual_produced):
        """
        Update inventory after production with smart conversions
        """
        updates = []
        
        # Deduct raw materials based on actual production
        for bom_item in bom.bom_items:
            material = bom_item.material
            if not material:
                continue
                
            # Calculate actual consumption
            consumption_ratio = actual_produced / production_quantity if production_quantity > 0 else 0
            consumed_qty_bom = bom_item.quantity * production_quantity * consumption_ratio
            bom_unit = bom_item.bom_unit.symbol if bom_item.bom_unit else material.unit_of_measure
            
            # Convert to inventory unit
            consumed_qty_inventory = SmartConversionService.convert_quantity(
                material, consumed_qty_bom, bom_unit, material.unit_of_measure
            )
            
            # Update stock
            old_stock = material.current_stock or 0
            new_stock = max(0, old_stock - consumed_qty_inventory)
            material.current_stock = new_stock
            
            updates.append({
                'material': material.name,
                'old_stock': old_stock,
                'consumed': consumed_qty_inventory,
                'new_stock': new_stock,
                'unit': material.unit_of_measure,
                'conversion_info': f"{consumed_qty_bom} {bom_unit} = {consumed_qty_inventory:.3f} {material.unit_of_measure}"
            })
        
        # Add finished goods to inventory
        finished_item = bom.item
        if finished_item:
            production_unit = bom.production_unit.symbol if bom.production_unit else finished_item.unit_of_measure
            
            # Convert produced quantity to inventory unit
            produced_qty_inventory = SmartConversionService.convert_quantity(
                finished_item, actual_produced, production_unit, finished_item.unit_of_measure
            )
            
            old_stock = finished_item.current_stock or 0
            new_stock = old_stock + produced_qty_inventory
            finished_item.current_stock = new_stock
            
            updates.append({
                'material': f"{finished_item.name} (Finished Goods)",
                'old_stock': old_stock,
                'consumed': -produced_qty_inventory,  # Negative indicates addition
                'new_stock': new_stock,
                'unit': finished_item.unit_of_measure,
                'conversion_info': f"{actual_produced} {production_unit} = {produced_qty_inventory:.3f} {finished_item.unit_of_measure}"
            })
        
        try:
            db.session.commit()
            return {'success': True, 'updates': updates}
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating inventory after production: {e}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def get_conversion_suggestions(item):
        """
        Get smart conversion suggestions for an item
        """
        suggestions = []
        
        # Item-specific conversions
        if hasattr(item, 'unit_weight') and item.unit_weight:
            suggestions.append({
                'type': 'item_specific',
                'from_unit': 'kg',
                'to_unit': 'pcs',
                'factor': 1/item.unit_weight,
                'description': f"1 kg = {1/item.unit_weight:.2f} pieces (based on unit weight)"
            })
            
        # Available UOM conversions
        uom_conversions = UOMConversion.query.filter(
            db.or_(
                UOMConversion.from_unit == item.unit_of_measure,
                UOMConversion.to_unit == item.unit_of_measure
            )
        ).all()
        
        for conv in uom_conversions:
            suggestions.append({
                'type': 'uom_standard',
                'from_unit': conv.from_unit,
                'to_unit': conv.to_unit,
                'factor': conv.factor,
                'description': f"1 {conv.from_unit} = {conv.factor} {conv.to_unit}"
            })
        
        # Item-specific UOM conversions
        item_conversions = ItemUOMConversion.query.filter_by(item_id=item.id).all()
        for conv in item_conversions:
            suggestions.append({
                'type': 'item_uom',
                'from_unit': conv.from_unit,
                'to_unit': conv.to_unit,
                'factor': conv.conversion_factor,
                'description': f"1 {conv.from_unit} = {conv.conversion_factor} {conv.to_unit} (item-specific)"
            })
        
        return suggestions