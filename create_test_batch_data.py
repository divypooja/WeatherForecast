#!/usr/bin/env python3
"""
Create test batch data for multi-batch selection testing
"""

from app import app, db
from models import Item, ItemBatch
from datetime import datetime, date, timedelta

def create_test_batches():
    """Create test batches with proper quantities for testing multi-batch functionality"""
    
    with app.app_context():
        try:
            # Find or create Ms sheet item
            item = Item.query.filter(Item.name.like('%Ms sheet%')).first()
            if not item:
                print("Ms sheet item not found. Creating one...")
                item = Item(
                    code='ITEM-0002',
                    name='Ms sheet',
                    unit_of_measure='nos',
                    category='Raw Materials',
                    batch_required=True,
                    default_batch_prefix='ITE',
                    shelf_life_days=365
                )
                db.session.add(item)
                db.session.commit()
                print(f"Created item: {item.name} (ID: {item.id})")
            else:
                print(f"Found item: {item.name} (ID: {item.id})")
            
            # Check existing batches
            existing_batches = ItemBatch.query.filter_by(item_id=item.id).all()
            print(f"Existing batches: {len(existing_batches)}")
            
            # Update existing batch with proper quantities or create new ones
            batches_to_create = [
                {
                    'batch_number': 'ITE-2508-001',
                    'qty_raw': 50.0,
                    'supplier_batch': 'SUP-001',
                    'purchase_rate': 25.50
                },
                {
                    'batch_number': 'ITE-2508-002', 
                    'qty_raw': 30.0,
                    'supplier_batch': 'SUP-002',
                    'purchase_rate': 26.00
                },
                {
                    'batch_number': 'ITE-2508-003',
                    'qty_raw': 75.0,
                    'supplier_batch': 'SUP-003', 
                    'purchase_rate': 24.75
                }
            ]
            
            for batch_info in batches_to_create:
                # Check if batch already exists
                existing_batch = ItemBatch.query.filter_by(
                    item_id=item.id,
                    batch_number=batch_info['batch_number']
                ).first()
                
                if existing_batch:
                    # Update existing batch with proper quantities
                    existing_batch.qty_raw = batch_info['qty_raw']
                    existing_batch.supplier_batch = batch_info['supplier_batch']
                    existing_batch.purchase_rate = batch_info['purchase_rate']
                    existing_batch.quality_status = 'good'
                    existing_batch.storage_location = 'Warehouse-A'
                    existing_batch.manufacture_date = date.today() - timedelta(days=10)
                    existing_batch.expiry_date = date.today() + timedelta(days=355)
                    print(f"Updated batch: {batch_info['batch_number']} with qty_raw={batch_info['qty_raw']}")
                else:
                    # Create new batch
                    new_batch = ItemBatch(
                        item_id=item.id,
                        batch_number=batch_info['batch_number'],
                        qty_raw=batch_info['qty_raw'],
                        qty_finished=0.0,
                        qty_scrap=0.0,
                        supplier_batch=batch_info['supplier_batch'],
                        purchase_rate=batch_info['purchase_rate'],
                        quality_status='good',
                        storage_location='Warehouse-A',
                        manufacture_date=date.today() - timedelta(days=10),
                        expiry_date=date.today() + timedelta(days=355),
                        created_at=datetime.utcnow()
                    )
                    db.session.add(new_batch)
                    print(f"Created batch: {batch_info['batch_number']} with qty_raw={batch_info['qty_raw']}")
            
            # Commit all changes
            db.session.commit()
            print("✓ Successfully created/updated test batch data")
            
            # Verify the data
            print("\n--- Verification ---")
            all_batches = ItemBatch.query.filter_by(item_id=item.id).all()
            for batch in all_batches:
                print(f"Batch {batch.batch_number}: raw={batch.qty_raw}, finished={batch.qty_finished}, available={batch.available_quantity}")
            
            return True
            
        except Exception as e:
            print(f"Error creating test batches: {str(e)}")
            db.session.rollback()
            return False

if __name__ == '__main__':
    success = create_test_batches()
    if success:
        print("\n🎉 Test batch data created successfully!")
        print("You can now test multi-batch selection in the Job Work form.")
    else:
        print("\n❌ Failed to create test batch data.")