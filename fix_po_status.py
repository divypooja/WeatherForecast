#!/usr/bin/env python3
"""
Fix Purchase Order status by running the update logic for PO-2025-0003
"""

from app import app, db
from models import PurchaseOrder

def fix_po_status():
    """Fix PO status for PO-2025-0003"""
    
    with app.app_context():
        # Import the update function
        from routes.grn import update_po_status_based_on_grn
        
        # Find the PO
        po = PurchaseOrder.query.filter_by(po_number='PO-2025-0003').first()
        if not po:
            print("PO-2025-0003 not found")
            return
        
        print(f"Current PO status: {po.status}")
        
        # Run the status update function
        try:
            update_po_status_based_on_grn(po.id)
            print("Status update function executed")
            
            # Refresh and check new status
            db.session.refresh(po)
            print(f"New PO status: {po.status}")
            
            # Show detailed breakdown
            print(f"\nPO Line Items:")
            for item in po.items:
                received = getattr(item, 'quantity_received', 0) or 0
                print(f"  {item.item.name}: {received}/{item.qty} received")
                
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    fix_po_status()