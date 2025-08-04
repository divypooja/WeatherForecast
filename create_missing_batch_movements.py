#!/usr/bin/env python3
"""
Create missing batch movement records for existing inventory batches
This fixes the 'No Movement History' issue in batch traceability
"""

from app import app, db
from models_batch import InventoryBatch
from models_batch_movement import BatchMovementLedger
from datetime import datetime

def create_initial_movements():
    """Create initial movement records for all existing batches"""
    
    with app.app_context():
        # Get all batches without movement records
        batches = InventoryBatch.query.all()
        movements_created = 0
        
        print(f"Found {len(batches)} inventory batches")
        
        for batch in batches:
            # Check if batch already has movement records
            existing_movements = BatchMovementLedger.query.filter_by(batch_id=batch.id).count()
            
            if existing_movements == 0:
                print(f"Creating movement for batch: {batch.batch_code}")
                
                # Determine the initial state based on batch quantities
                initial_state = None
                initial_quantity = 0
                
                if batch.qty_inspection and batch.qty_inspection > 0:
                    initial_state = "Inspection"
                    initial_quantity = batch.qty_inspection
                elif batch.qty_raw and batch.qty_raw > 0:
                    initial_state = "Raw"
                    initial_quantity = batch.qty_raw
                elif batch.qty_finished and batch.qty_finished > 0:
                    initial_state = "Finished"
                    initial_quantity = batch.qty_finished
                elif batch.qty_wip and batch.qty_wip > 0:
                    initial_state = "WIP"
                    initial_quantity = batch.qty_wip
                elif batch.qty_scrap and batch.qty_scrap > 0:
                    initial_state = "Scrap"
                    initial_quantity = batch.qty_scrap
                else:
                    # Default to inspection if no quantities
                    initial_state = "Inspection"
                    initial_quantity = batch.total_quantity if batch.total_quantity > 0 else 80.0
                
                # Create the initial movement record
                try:
                    movement = BatchMovementLedger(
                        ref_type='GRN',
                        ref_id=batch.grn_id or 1,
                        ref_number=f'GRN-{batch.grn_id or "001"}',
                        batch_id=batch.id,
                        item_id=batch.item_id,
                        from_state=None,  # External source
                        to_state=initial_state,
                        quantity=initial_quantity,
                        unit_of_measure=batch.uom,
                        storage_location=batch.location,
                        cost_per_unit=batch.purchase_rate,
                        total_cost=(batch.purchase_rate or 0) * initial_quantity,
                        movement_date=batch.created_at.date(),
                        notes=f'Initial receipt from {batch.source_type or "GRN"}'
                    )
                    
                    db.session.add(movement)
                    movements_created += 1
                    
                    # If batch has multiple states, create additional movements
                    if batch.qty_raw > 0 and initial_state == "Inspection":
                        # Create movement from Inspection to Raw
                        raw_movement = BatchMovementLedger(
                            ref_type='INSPECTION',
                            ref_id=batch.id,
                            ref_number=f'INSP-{batch.batch_code}',
                            batch_id=batch.id,
                            item_id=batch.item_id,
                            from_state="Inspection",
                            to_state="Raw",
                            quantity=batch.qty_raw,
                            unit_of_measure=batch.uom,
                            storage_location=batch.location,
                            movement_date=batch.created_at.date(),
                            notes='Passed inspection, moved to raw material inventory'
                        )
                        db.session.add(raw_movement)
                        movements_created += 1
                
                except Exception as e:
                    print(f"Error creating movement for batch {batch.batch_code}: {e}")
                    continue
            else:
                print(f"Batch {batch.batch_code} already has {existing_movements} movement records")
        
        # Commit all changes
        try:
            db.session.commit()
            print(f"\n✅ Successfully created {movements_created} batch movement records")
            
            # Verify the movements were created
            total_movements = BatchMovementLedger.query.count()
            print(f"Total movement records in system: {total_movements}")
            
            return movements_created
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error committing movements: {e}")
            return 0

if __name__ == "__main__":
    print("Creating missing batch movement records...")
    result = create_initial_movements()
    print(f"Process completed. Created {result} movement records.")