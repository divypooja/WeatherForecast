#!/usr/bin/env python3
"""
Create sample batch tracking data for demonstration
"""

import sys
import os
sys.path.append('.')

from datetime import datetime, date, timedelta
from app import app, db
from models import Item, ItemBatch, Supplier
from models_grn import GRN, GRNLineItem
import random

def create_sample_batch_data():
    """Create realistic sample batch tracking data"""
    
    with app.app_context():
        print("Creating sample batch tracking data...")
        
        # First ensure we have some items with batch tracking enabled
        items_data = [
            {"name": "Steel Rod 12mm", "code": "STL-ROD-12", "category": "Raw Material", "unit": "KG", "batch_required": True},
            {"name": "Steel Plate 5mm", "code": "STL-PLT-5", "category": "Raw Material", "unit": "SQM", "batch_required": True},
            {"name": "Aluminum Sheet", "code": "ALU-SHT-3", "category": "Raw Material", "unit": "KG", "batch_required": True},
            {"name": "Welding Wire", "code": "WLD-WIR-1", "category": "Consumable", "unit": "KG", "batch_required": True},
            {"name": "Paint Primer", "code": "PNT-PRM-1", "category": "Consumable", "unit": "LTR", "batch_required": True},
            {"name": "Zinc Coating", "code": "ZNC-COT-1", "category": "Consumable", "unit": "KG", "batch_required": True},
        ]
        
        # Create items if they don't exist
        items = []
        for item_data in items_data:
            item = Item.query.filter_by(code=item_data["code"]).first()
            if not item:
                item = Item(
                    name=item_data["name"],
                    code=item_data["code"],
                    category=item_data["category"],
                    unit_of_measure=item_data["unit"],
                    batch_required=item_data["batch_required"],
                    default_batch_prefix=item_data["code"][:3],
                    batch_numbering_auto=True,
                    shelf_life_days=365 if item_data["category"] == "Consumable" else None
                )
                db.session.add(item)
                items.append(item)
            else:
                # Update existing item to enable batch tracking
                item.batch_required = True
                item.default_batch_prefix = item_data["code"][:3]
                item.batch_numbering_auto = True
                if item_data["category"] == "Consumable":
                    item.shelf_life_days = 365
                items.append(item)
        
        db.session.commit()
        print(f"Created/updated {len(items)} items with batch tracking")
        
        # Create supplier if needed
        supplier = Supplier.query.filter_by(name="Test Steel Suppliers").first()
        if not supplier:
            supplier = Supplier(
                name="Test Steel Suppliers",
                contact_person="John Smith",
                phone="123-456-7890",
                email="john@teststeelsuppliers.com",
                address="123 Steel Street, Industrial Area",
                partner_type="supplier"
            )
            db.session.add(supplier)
            db.session.commit()
        
        # Create sample batches for each item
        batch_count = 0
        for item in items:
            # Create 3-5 batches per item with different states
            num_batches = random.randint(3, 5)
            
            for i in range(num_batches):
                batch_number = f"{item.default_batch_prefix}-{datetime.now().strftime('%Y%m')}-{batch_count+1:03d}"
                
                # Create batch with realistic manufacturing date
                mfg_date = date.today() - timedelta(days=random.randint(10, 90))
                
                # Calculate expiry date for consumables
                expiry_date = None
                if item.shelf_life_days:
                    expiry_date = mfg_date + timedelta(days=item.shelf_life_days)
                
                batch = ItemBatch(
                    item_id=item.id,
                    batch_number=batch_number,
                    supplier_batch_number=f"SUP-{batch_number}",
                    manufacturing_date=mfg_date,
                    expiry_date=expiry_date,
                    storage_location=random.choice(["A-01", "A-02", "B-01", "B-02", "C-01"]),
                    quality_status=random.choice(["approved", "approved", "approved", "pending", "rejected"]),
                    received_date=mfg_date + timedelta(days=random.randint(1, 5))
                )
                
                # Set realistic quantities in different states
                base_qty = random.uniform(100, 1000)
                
                # Raw material state
                if random.random() > 0.3:  # 70% chance of having raw material
                    batch.qty_raw = round(base_qty * random.uniform(0.2, 0.8), 2)
                
                # WIP states (simulate manufacturing progress)
                if random.random() > 0.6:  # 40% chance of having WIP
                    batch.qty_wip_cutting = round(base_qty * random.uniform(0.1, 0.3), 2)
                
                if random.random() > 0.7:  # 30% chance
                    batch.qty_wip_bending = round(base_qty * random.uniform(0.05, 0.2), 2)
                
                if random.random() > 0.8:  # 20% chance
                    batch.qty_wip_welding = round(base_qty * random.uniform(0.05, 0.15), 2)
                
                if random.random() > 0.85:  # 15% chance
                    batch.qty_wip_zinc = round(base_qty * random.uniform(0.02, 0.1), 2)
                
                if random.random() > 0.9:  # 10% chance
                    batch.qty_wip_painting = round(base_qty * random.uniform(0.02, 0.08), 2)
                
                # Finished goods
                if random.random() > 0.4:  # 60% chance of having finished goods
                    batch.qty_finished = round(base_qty * random.uniform(0.1, 0.5), 2)
                
                # Small chance of scrap
                if random.random() > 0.8:  # 20% chance
                    batch.qty_scrap = round(base_qty * random.uniform(0.01, 0.05), 2)
                
                db.session.add(batch)
                batch_count += 1
        
        db.session.commit()
        print(f"Created {batch_count} sample batches")
        
        # Create some GRNs to link batches to purchase orders
        print("Creating sample GRNs...")
        
        for i in range(3):
            grn = GRN(
                grn_number=f"GRN-{datetime.now().strftime('%Y%m')}-{i+1:03d}",
                supplier_id=supplier.id,
                received_date=date.today() - timedelta(days=random.randint(5, 30)),
                status="completed",
                vehicle_number=f"TN{random.randint(10,99)}AB{random.randint(1000,9999)}",
                driver_name="Driver Name",
                driver_phone="9876543210"
            )
            db.session.add(grn)
            db.session.flush()  # Get the GRN ID
            
            # Add line items
            selected_items = random.sample(items, 2)  # Select 2 random items
            for item in selected_items:
                line_item = GRNLineItem(
                    grn_id=grn.id,
                    item_id=item.id,
                    ordered_quantity=random.uniform(500, 1500),
                    received_quantity=random.uniform(450, 1400),
                    unit_rate=random.uniform(50, 200),
                    amount=0  # Will be calculated
                )
                line_item.amount = line_item.received_quantity * line_item.unit_rate
                db.session.add(line_item)
        
        db.session.commit()
        print("Sample GRNs created")
        
        print("\n✓ Sample batch tracking data created successfully!")
        print(f"✓ Created {len(items)} items with batch tracking enabled")
        print(f"✓ Created {batch_count} batches across all items")
        print(f"✓ Created 3 sample GRNs with line items")
        print("\nYou can now test the batch tracking functionality:")
        print("1. Visit Inventory → Batch-Wise view")
        print("2. Check Batch Tracking dashboard")
        print("3. Explore Quality Control and Process View sections")

if __name__ == "__main__":
    create_sample_batch_data()