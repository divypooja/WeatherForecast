from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app import db
from models import Item
from models_uom import UnitOfMeasure, UOMConversion, ItemUOMConversion, UOMConversionLog
from forms_uom import UnitOfMeasureForm, UOMConversionForm, ItemUOMConversionForm, UOMCalculatorForm
from decimal import Decimal

uom_bp = Blueprint('uom', __name__)

@uom_bp.route('/dashboard')
@login_required
def dashboard():
    """UOM management dashboard"""
    # Statistics
    total_units = UnitOfMeasure.query.count()
    total_conversions = UOMConversion.query.filter_by(is_active=True).count()
    items_with_conversions = ItemUOMConversion.query.count()
    conversion_logs_count = UOMConversionLog.query.count()
    
    # Recent items with conversions
    recent_item_conversions = ItemUOMConversion.query.join(Item).order_by(ItemUOMConversion.updated_at.desc()).limit(5).all()
    
    # Items needing setup (without proper UOM configurations)
    items_needing_setup = []
    all_items = Item.query.limit(20).all()
    
    for item in all_items:
        needs_setup = False
        
        # Check if item has unit_weight but no proper conversions
        if hasattr(item, 'unit_weight') and item.unit_weight:
            # Item has weight info, check if it has proper conversions
            item_conversions = ItemUOMConversion.query.filter_by(item_id=item.id).count()
            if item_conversions == 0:
                needs_setup = True
        
        # Check if item needs cross-unit support
        elif not ItemUOMConversion.query.filter_by(item_id=item.id).first():
            # No conversions at all
            needs_setup = True
            
        if needs_setup:
            items_needing_setup.append(item)
    
    # Unit categories
    unit_categories = db.session.query(UnitOfMeasure.category, db.func.count(UnitOfMeasure.id)).group_by(UnitOfMeasure.category).all()
    
    return render_template('uom/dashboard.html',
                         total_units=total_units,
                         total_conversions=total_conversions,
                         items_with_conversions=items_with_conversions,
                         conversion_logs_count=conversion_logs_count,
                         recent_item_conversions=recent_item_conversions,
                         items_needing_setup=items_needing_setup,
                         unit_categories=unit_categories)

@uom_bp.route('/units')
@login_required
def units_list():
    """List all units of measure"""
    units = UnitOfMeasure.query.order_by(UnitOfMeasure.category, UnitOfMeasure.name).all()
    return render_template('uom/units_list.html', units=units)

@uom_bp.route('/units/add', methods=['GET', 'POST'])
@login_required
def add_unit():
    """Add new unit of measure"""
    form = UnitOfMeasureForm()
    
    if form.validate_on_submit():
        unit = UnitOfMeasure(
            name=form.name.data,
            symbol=form.symbol.data,
            category=form.category.data,
            is_base_unit=form.is_base_unit.data,
            description=form.description.data
        )
        
        try:
            db.session.add(unit)
            db.session.commit()
            flash(f'Unit "{unit.name}" created successfully!', 'success')
            return redirect(url_for('uom.units_list'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating unit: {str(e)}', 'error')
    
    return render_template('uom/unit_form.html', form=form, title='Add Unit of Measure')

@uom_bp.route('/units/edit/<int:unit_id>', methods=['GET', 'POST'])
@login_required
def edit_unit(unit_id):
    """Edit unit of measure"""
    unit = UnitOfMeasure.query.get_or_404(unit_id)
    form = UnitOfMeasureForm(obj=unit)
    
    if form.validate_on_submit():
        form.populate_obj(unit)
        
        try:
            db.session.commit()
            flash(f'Unit "{unit.name}" updated successfully!', 'success')
            return redirect(url_for('uom.units_list'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating unit: {str(e)}', 'error')
    
    return render_template('uom/unit_form.html', form=form, title='Edit Unit of Measure', unit=unit)

@uom_bp.route('/conversions')
@login_required
def conversions_list():
    """List all UOM conversions"""
    conversions = UOMConversion.query.filter(UOMConversion.is_active == True)\
                                   .order_by(UOMConversion.created_at.desc()).all()
    
    return render_template('uom/conversions_list.html', conversions=conversions)

@uom_bp.route('/conversions/add', methods=['GET', 'POST'])
@login_required
def add_conversion():
    """Add new UOM conversion"""
    form = UOMConversionForm()
    
    if form.validate_on_submit():
        # Check if conversion already exists
        existing = UOMConversion.query.filter_by(
            from_unit_id=form.from_unit.data,
            to_unit_id=form.to_unit.data
        ).first()
        
        if existing:
            flash('Conversion between these units already exists!', 'error')
            return render_template('uom/conversion_form.html', form=form, title='Add UOM Conversion')
        
        conversion = UOMConversion(
            from_unit_id=form.from_unit.data,
            to_unit_id=form.to_unit.data,
            conversion_factor=form.conversion_factor.data,
            notes=form.notes.data
        )
        
        try:
            db.session.add(conversion)
            db.session.commit()
            flash('UOM conversion created successfully!', 'success')
            return redirect(url_for('uom.conversions_list'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating conversion: {str(e)}', 'error')
    
    return render_template('uom/conversion_form.html', form=form, title='Add UOM Conversion')

@uom_bp.route('/item-conversions')
@login_required
def item_conversions_list():
    """List all item-specific UOM conversions"""
    item_conversions = ItemUOMConversion.query.join(Item).order_by(Item.name).all()
    return render_template('uom/item_conversions_list.html', item_conversions=item_conversions)

@uom_bp.route('/simple-setup', methods=['GET', 'POST'])
@login_required
def simple_setup():
    """Simplified UOM setup interface"""
    if request.method == 'POST':
        item_id = request.form.get('item_id')
        workflow_type = request.form.get('workflow_type')
        
        if not item_id:
            flash('Please select an item', 'error')
            return redirect(url_for('uom.simple_setup'))
        
        item = Item.query.get_or_404(item_id)
        
        try:
            if workflow_type == 'same_unit':
                # Simple case - same unit for all operations
                unit_type = request.form.get('same_unit_type')
                if not unit_type:
                    flash('Please select a unit type', 'error')
                    return redirect(url_for('uom.simple_setup'))
                
                # Update item to use same unit for purchase, storage, and sale
                item.purchase_unit = unit_type
                item.sale_unit = unit_type
                item.unit_of_measure = unit_type
                
                flash(f'✅ Simple setup complete! {item.name} uses {unit_type} for all operations.', 'success')
                
            elif workflow_type == 'different_units':
                # Different units case
                purchase_unit = request.form.get('purchase_unit')
                storage_unit = request.form.get('storage_unit')
                sale_unit = request.form.get('sale_unit')
                conversion_quantity = request.form.get('conversion_quantity')
                
                if not all([purchase_unit, storage_unit, sale_unit, conversion_quantity]):
                    flash('Please fill all fields for different units setup', 'error')
                    return redirect(url_for('uom.simple_setup'))
                
                # Update item units
                item.purchase_unit = purchase_unit
                item.sale_unit = sale_unit
                item.unit_of_measure = storage_unit
                
                # Set unit weight if converting from weight to count
                if storage_unit == 'kg' and sale_unit == 'pcs':
                    try:
                        pieces_per_kg = float(conversion_quantity)
                        item.unit_weight = 1.0 / pieces_per_kg
                    except:
                        pass
                
                flash(f'✅ Unit conversion setup complete! {item.name}: 1 {storage_unit} = {conversion_quantity} {sale_unit}', 'success')
            
            db.session.commit()
            return redirect(url_for('uom.dashboard'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error setting up units: {str(e)}', 'error')
    
    # GET request - show form
    items = Item.query.order_by(Item.name).all()
    return render_template('uom/simple_conversion_form.html', items=items)

@uom_bp.route('/item-conversions/add', methods=['GET', 'POST'])
@login_required
def add_item_conversion():
    """Add new item-specific UOM conversion"""
    form = ItemUOMConversionForm()
    
    if form.validate_on_submit():
        # Check if item already has conversion
        existing = ItemUOMConversion.query.filter_by(item_id=form.item.data).first()
        if existing:
            flash('This item already has UOM conversion configured!', 'error')
            return render_template('uom/item_conversion_form.html', form=form, title='Add Item UOM Conversion')
        
        # Calculate derived values
        purchase_to_sale = None
        if form.pieces_per_kg.data and form.weight_per_piece.data:
            # Validate that pieces_per_kg and weight_per_piece are consistent
            calculated_weight = 1.0 / float(form.pieces_per_kg.data)
            if abs(calculated_weight - float(form.weight_per_piece.data)) > 0.001:
                flash('Warning: Weight per piece and pieces per Kg values are inconsistent!', 'warning')
        
        # Calculate purchase to sale conversion if not provided
        purchase_to_sale = float(form.purchase_to_inventory.data) * float(form.inventory_to_sale.data)
        
        item_conversion = ItemUOMConversion(
            item_id=form.item.data,
            purchase_unit_id=form.purchase_unit.data,
            sale_unit_id=form.sale_unit.data,
            inventory_unit_id=form.inventory_unit.data,
            purchase_to_inventory=form.purchase_to_inventory.data,
            inventory_to_sale=form.inventory_to_sale.data,
            purchase_to_sale=purchase_to_sale,
            weight_per_piece=form.weight_per_piece.data,
            pieces_per_kg=form.pieces_per_kg.data,
            notes=form.notes.data
        )
        
        try:
            db.session.add(item_conversion)
            db.session.commit()
            flash('Item UOM conversion created successfully!', 'success')
            return redirect(url_for('uom.item_conversions_list'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating item conversion: {str(e)}', 'error')
    
    return render_template('uom/item_conversion_form.html', form=form, title='Add Item UOM Conversion')

@uom_bp.route('/item-conversions/edit/<int:conversion_id>', methods=['GET', 'POST'])
@login_required
def edit_item_conversion(conversion_id):
    """Edit item-specific UOM conversion"""
    conversion = ItemUOMConversion.query.get_or_404(conversion_id)
    form = ItemUOMConversionForm(obj=conversion)
    
    if form.validate_on_submit():
        # Update all fields
        form.populate_obj(conversion)
        
        # Recalculate purchase to sale conversion
        conversion.purchase_to_sale = float(conversion.purchase_to_inventory) * float(conversion.inventory_to_sale)
        
        try:
            db.session.commit()
            flash('Item UOM conversion updated successfully!', 'success')
            return redirect(url_for('uom.item_conversions_list'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating conversion: {str(e)}', 'error')
    
    return render_template('uom/item_conversion_form.html', form=form, title='Edit Item UOM Conversion', conversion=conversion)

@uom_bp.route('/auto-setup-item/<int:item_id>', methods=['GET', 'POST'])
@login_required
def auto_setup_item(item_id):
    """Automatically setup UOM conversions for an item based on intelligent defaults"""
    item = Item.query.get_or_404(item_id)
    
    try:
        # Check if item already has conversions
        existing_conversions = ItemUOMConversion.query.filter_by(item_id=item.id).first()
        if existing_conversions:
            flash(f'Item "{item.name}" already has UOM conversions configured.', 'info')
            return redirect(url_for('uom.dashboard'))
        
        conversions_added = 0
        
        # Auto-setup based on item properties
        if hasattr(item, 'unit_weight') and item.unit_weight and item.unit_weight > 0:
            # Item has unit weight - create kg to pieces conversion
            kg_unit = UnitOfMeasure.query.filter_by(symbol='kg').first()
            pcs_unit = UnitOfMeasure.query.filter_by(symbol='pcs').first()
            
            if kg_unit and pcs_unit:
                # Create kg to pieces conversion (1 kg = X pieces where X = 1/unit_weight)
                pieces_per_kg = 1.0 / item.unit_weight
                
                conversion1 = ItemUOMConversion(
                    item_id=item.id,
                    from_unit_id=kg_unit.id,
                    to_unit_id=pcs_unit.id,
                    conversion_factor=pieces_per_kg,
                    notes=f"Auto-generated: 1 kg = {pieces_per_kg:.3f} pieces (based on unit weight {item.unit_weight} kg/piece)"
                )
                
                # Create reverse conversion (pieces to kg)
                conversion2 = ItemUOMConversion(
                    item_id=item.id,
                    from_unit_id=pcs_unit.id,
                    to_unit_id=kg_unit.id,
                    conversion_factor=item.unit_weight,
                    notes=f"Auto-generated: 1 piece = {item.unit_weight} kg"
                )
                
                db.session.add(conversion1)
                db.session.add(conversion2)
                conversions_added += 2
        
        # Add standard conversions based on item's current unit
        current_unit = UnitOfMeasure.query.filter_by(symbol=item.unit_of_measure).first()
        if current_unit:
            # Find related standard conversions
            related_conversions = UOMConversion.query.filter(
                db.or_(
                    UOMConversion.from_unit == item.unit_of_measure,
                    UOMConversion.to_unit == item.unit_of_measure
                )
            ).all()
            
            for std_conv in related_conversions:
                # Create item-specific conversion based on standard conversion
                from_unit = UnitOfMeasure.query.filter_by(symbol=std_conv.from_unit).first()
                to_unit = UnitOfMeasure.query.filter_by(symbol=std_conv.to_unit).first()
                
                if from_unit and to_unit:
                    # Check if this conversion doesn't already exist
                    existing = ItemUOMConversion.query.filter_by(
                        item_id=item.id,
                        from_unit_id=from_unit.id,
                        to_unit_id=to_unit.id
                    ).first()
                    
                    if not existing:
                        item_conversion = ItemUOMConversion(
                            item_id=item.id,
                            from_unit_id=from_unit.id,
                            to_unit_id=to_unit.id,
                            conversion_factor=std_conv.factor,
                            notes=f"Auto-generated from standard conversion: {std_conv.from_unit} to {std_conv.to_unit}"
                        )
                        db.session.add(item_conversion)
                        conversions_added += 1
        
        if conversions_added > 0:
            db.session.commit()
            
            # Log the auto-setup
            log_entry = UOMConversionLog(
                item_id=item.id,
                from_unit=item.unit_of_measure,
                to_unit="multiple",
                from_quantity=1.0,
                to_quantity=1.0,
                conversion_type="auto_setup",
                notes=f"Auto-configured {conversions_added} conversions for {item.name}",
                created_by=current_user.id if current_user.is_authenticated else None
            )
            db.session.add(log_entry)
            db.session.commit()
            
            flash(f'Successfully auto-configured {conversions_added} UOM conversions for "{item.name}"!', 'success')
        else:
            flash(f'No suitable conversions found to auto-configure for "{item.name}". Please set up manually.', 'warning')
            
    except Exception as e:
        db.session.rollback()
        flash(f'Error auto-configuring conversions for "{item.name}": {str(e)}', 'error')
    
    return redirect(url_for('uom.dashboard'))

@uom_bp.route('/auto-setup-all', methods=['GET'])
@login_required
def auto_setup_all():
    """Automatically setup UOM conversions for all items needing setup"""
    try:
        # Find all items needing setup
        items_needing_setup = []
        all_items = Item.query.all()
        
        for item in all_items:
            needs_setup = False
            
            # Check if item has unit_weight but no proper conversions
            if hasattr(item, 'unit_weight') and item.unit_weight:
                item_conversions = ItemUOMConversion.query.filter_by(item_id=item.id).count()
                if item_conversions == 0:
                    needs_setup = True
            
            # Check if item needs cross-unit support
            elif not ItemUOMConversion.query.filter_by(item_id=item.id).first():
                needs_setup = True
                
            if needs_setup:
                items_needing_setup.append(item)
        
        total_items = len(items_needing_setup)
        successful_setups = 0
        
        for item in items_needing_setup:
            try:
                conversions_added = 0
                
                # Auto-setup based on item properties and smart weight logic
                if hasattr(item, 'unit_weight') and item.unit_weight and item.unit_weight > 0:
                    # Get required units
                    kg_unit = UnitOfMeasure.query.filter_by(symbol='kg').first()
                    pcs_unit = UnitOfMeasure.query.filter_by(symbol='pcs').first()
                    g_unit = UnitOfMeasure.query.filter_by(symbol='g').first()
                    ton_unit = UnitOfMeasure.query.filter_by(symbol='ton').first()
                    
                    # Create missing units if they don't exist
                    if not g_unit:
                        g_unit = UnitOfMeasure(name='Gram', symbol='g', category='Weight', is_base_unit=False)
                        db.session.add(g_unit)
                        db.session.flush()
                        
                    if not ton_unit:
                        ton_unit = UnitOfMeasure(name='Ton', symbol='ton', category='Weight', is_base_unit=False)
                        db.session.add(ton_unit)
                        db.session.flush()
                    
                    if kg_unit and pcs_unit:
                        # Create kg to pieces conversion
                        pieces_per_kg = 1.0 / item.unit_weight
                        
                        conversion1 = ItemUOMConversion(
                            item_id=item.id,
                            from_unit_id=kg_unit.id,
                            to_unit_id=pcs_unit.id,
                            conversion_factor=pieces_per_kg,
                            notes=f"Auto-generated: 1 kg = {pieces_per_kg:.3f} pieces (based on unit weight {item.unit_weight} kg/piece)"
                        )
                        
                        # Create reverse conversion (pieces to kg)
                        conversion2 = ItemUOMConversion(
                            item_id=item.id,
                            from_unit_id=pcs_unit.id,
                            to_unit_id=kg_unit.id,
                            conversion_factor=item.unit_weight,
                            notes=f"Auto-generated: 1 piece = {item.unit_weight} kg"
                        )
                        
                        db.session.add(conversion1)
                        db.session.add(conversion2)
                        conversions_added += 2
                        
                        # Add smart weight conversions based on unit_weight
                        # If unit weight suggests small items (< 1kg), add gram conversions
                        if item.unit_weight < 1 and g_unit:
                            grams_per_piece = item.unit_weight * 1000
                            
                            conversion3 = ItemUOMConversion(
                                item_id=item.id,
                                from_unit_id=pcs_unit.id,
                                to_unit_id=g_unit.id,
                                conversion_factor=grams_per_piece,
                                notes=f"Auto-generated: 1 piece = {grams_per_piece:.1f} g (smart weight conversion)"
                            )
                            db.session.add(conversion3)
                            conversions_added += 1
                        
                        # If unit weight suggests heavy items, add ton conversions  
                        elif item.unit_weight > 100 and ton_unit:  # Items heavier than 100kg each
                            tons_per_piece = item.unit_weight / 1000
                            
                            conversion4 = ItemUOMConversion(
                                item_id=item.id,
                                from_unit_id=pcs_unit.id,
                                to_unit_id=ton_unit.id,
                                conversion_factor=tons_per_piece,
                                notes=f"Auto-generated: 1 piece = {tons_per_piece:.4f} ton (smart weight conversion)"
                            )
                            db.session.add(conversion4)
                            conversions_added += 1
                
                # Add standard conversions based on item's current unit
                current_unit = UnitOfMeasure.query.filter_by(symbol=item.unit_of_measure).first()
                if current_unit:
                    related_conversions = UOMConversion.query.filter(
                        db.or_(
                            UOMConversion.from_unit == item.unit_of_measure,
                            UOMConversion.to_unit == item.unit_of_measure
                        )
                    ).all()
                    
                    for std_conv in related_conversions:
                        from_unit = UnitOfMeasure.query.filter_by(symbol=std_conv.from_unit).first()
                        to_unit = UnitOfMeasure.query.filter_by(symbol=std_conv.to_unit).first()
                        
                        if from_unit and to_unit:
                            existing = ItemUOMConversion.query.filter_by(
                                item_id=item.id,
                                from_unit_id=from_unit.id,
                                to_unit_id=to_unit.id
                            ).first()
                            
                            if not existing:
                                item_conversion = ItemUOMConversion(
                                    item_id=item.id,
                                    from_unit_id=from_unit.id,
                                    to_unit_id=to_unit.id,
                                    conversion_factor=std_conv.factor,
                                    notes=f"Auto-generated from standard conversion"
                                )
                                db.session.add(item_conversion)
                                conversions_added += 1
                
                if conversions_added > 0:
                    successful_setups += 1
                    
                    # Log the auto-setup
                    log_entry = UOMConversionLog(
                        item_id=item.id,
                        from_unit=item.unit_of_measure,
                        to_unit="multiple",
                        from_quantity=1.0,
                        to_quantity=1.0,
                        conversion_type="bulk_auto_setup",
                        notes=f"Bulk auto-configured {conversions_added} conversions for {item.name}",
                        created_by=current_user.id if current_user.is_authenticated else None
                    )
                    db.session.add(log_entry)
                    
            except Exception as e:
                # Continue with other items if one fails
                continue
        
        db.session.commit()
        
        if successful_setups > 0:
            flash(f'Successfully auto-configured UOM conversions for {successful_setups} out of {total_items} items!', 'success')
        else:
            flash('No items could be auto-configured. Please set up manually.', 'warning')
            
    except Exception as e:
        db.session.rollback()
        flash(f'Error during bulk auto-setup: {str(e)}', 'error')
    
    return redirect(url_for('uom.dashboard'))

@uom_bp.route('/calculator', methods=['GET', 'POST'])
@login_required
def calculator():
    """UOM calculator for quick conversions"""
    form = UOMCalculatorForm()
    result = None
    
    if form.validate_on_submit():
        item = Item.query.get(form.item.data)
        item_conversion = ItemUOMConversion.query.filter_by(item_id=form.item.data).first()
        
        if not item_conversion:
            flash('No UOM conversion configured for this item!', 'error')
            return render_template('uom/calculator.html', form=form, result=result)
        
        quantity = float(form.quantity.data)
        from_unit = UnitOfMeasure.query.get(form.from_unit.data)
        to_unit = UnitOfMeasure.query.get(form.to_unit.data)
        
        try:
            # Determine conversion path
            converted_qty = None
            conversion_path = ""
            
            if from_unit.id == item_conversion.purchase_unit_id and to_unit.id == item_conversion.inventory_unit_id:
                converted_qty = item_conversion.convert_purchase_to_inventory(quantity)
                conversion_path = f"Purchase → Inventory (×{item_conversion.purchase_to_inventory})"
            elif from_unit.id == item_conversion.inventory_unit_id and to_unit.id == item_conversion.sale_unit_id:
                converted_qty = item_conversion.convert_inventory_to_sale(quantity)
                conversion_path = f"Inventory → Sale (×{item_conversion.inventory_to_sale})"
            elif from_unit.id == item_conversion.sale_unit_id and to_unit.id == item_conversion.inventory_unit_id:
                converted_qty = item_conversion.convert_sale_to_inventory(quantity)
                conversion_path = f"Sale → Inventory (÷{item_conversion.inventory_to_sale})"
            elif from_unit.id == item_conversion.purchase_unit_id and to_unit.id == item_conversion.sale_unit_id:
                converted_qty = item_conversion.convert_purchase_to_sale(quantity)
                conversion_path = f"Purchase → Sale (×{item_conversion.purchase_to_sale})"
            else:
                flash('No conversion path available between selected units for this item!', 'error')
                return render_template('uom/calculator.html', form=form, result=result)
            
            result = {
                'item': item,
                'original_qty': quantity,
                'from_unit': from_unit,
                'converted_qty': round(converted_qty, 6),
                'to_unit': to_unit,
                'conversion_path': conversion_path
            }
            
            # Log the conversion
            log_entry = UOMConversionLog(
                item_id=item.id,
                transaction_type='calculation',
                original_quantity=quantity,
                original_unit_id=from_unit.id,
                converted_quantity=converted_qty,
                converted_unit_id=to_unit.id,
                conversion_factor=converted_qty / quantity if quantity > 0 else 0,
                created_by=current_user.id
            )
            db.session.add(log_entry)
            db.session.commit()
            
        except Exception as e:
            flash(f'Error calculating conversion: {str(e)}', 'error')
    
    return render_template('uom/calculator.html', form=form, result=result)

@uom_bp.route('/api/item-uom-info/<int:item_id>')
@login_required
def get_item_uom_info(item_id):
    """API endpoint to get UOM information for an item"""
    item_conversion = ItemUOMConversion.query.filter_by(item_id=item_id).first()
    
    if not item_conversion:
        return jsonify({'has_conversion': False})
    
    return jsonify({
        'has_conversion': True,
        'purchase_unit': {
            'id': item_conversion.purchase_unit.id,
            'name': item_conversion.purchase_unit.name,
            'symbol': item_conversion.purchase_unit.symbol
        },
        'inventory_unit': {
            'id': item_conversion.inventory_unit.id,
            'name': item_conversion.inventory_unit.name,
            'symbol': item_conversion.inventory_unit.symbol
        },
        'sale_unit': {
            'id': item_conversion.sale_unit.id,
            'name': item_conversion.sale_unit.name,
            'symbol': item_conversion.sale_unit.symbol
        },
        'purchase_to_inventory': float(item_conversion.purchase_to_inventory),
        'inventory_to_sale': float(item_conversion.inventory_to_sale),
        'purchase_to_sale': float(item_conversion.purchase_to_sale or 0),
        'weight_per_piece': float(item_conversion.weight_per_piece or 0),
        'pieces_per_kg': float(item_conversion.pieces_per_kg or 0)
    })

@uom_bp.route('/api/convert-quantity', methods=['POST'])
@login_required
def convert_quantity():
    """API endpoint for quantity conversion"""
    data = request.get_json()
    item_id = data.get('item_id')
    quantity = float(data.get('quantity', 0))
    from_unit_id = data.get('from_unit_id')
    to_unit_id = data.get('to_unit_id')
    
    item_conversion = ItemUOMConversion.query.filter_by(item_id=item_id).first()
    
    if not item_conversion:
        return jsonify({'error': 'No UOM conversion configured for this item'}), 400
    
    try:
        converted_qty = None
        
        if from_unit_id == item_conversion.purchase_unit_id and to_unit_id == item_conversion.inventory_unit_id:
            converted_qty = item_conversion.convert_purchase_to_inventory(quantity)
        elif from_unit_id == item_conversion.inventory_unit_id and to_unit_id == item_conversion.sale_unit_id:
            converted_qty = item_conversion.convert_inventory_to_sale(quantity)
        elif from_unit_id == item_conversion.sale_unit_id and to_unit_id == item_conversion.inventory_unit_id:
            converted_qty = item_conversion.convert_sale_to_inventory(quantity)
        elif from_unit_id == item_conversion.purchase_unit_id and to_unit_id == item_conversion.sale_unit_id:
            converted_qty = item_conversion.convert_purchase_to_sale(quantity)
        else:
            return jsonify({'error': 'No conversion path available between these units'}), 400
        
        return jsonify({
            'converted_quantity': round(converted_qty, 6),
            'original_quantity': quantity
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500