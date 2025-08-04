#!/usr/bin/env python3
"""
Check and fix GRN inspection logic - ensure consistency between inspection status and inventory updates
"""

from app import app, db
from models_grn import GRN

def analyze_grn_inspection_consistency():
    """Analyze GRN inspection and inventory consistency"""
    
    with app.app_context():
        # Find GRNs with inconsistent inspection/inventory states
        grns = GRN.query.all()
        
        print("=== GRN Inspection & Inventory Analysis ===\n")
        
        inconsistent_grns = []
        for grn in grns:
            add_to_inv = getattr(grn, 'add_to_inventory', True)  # Default True if not set
            inspection = grn.inspection_status or 'pending'
            
            # Check for inconsistencies
            if add_to_inv and inspection == 'pending':
                inconsistent_grns.append({
                    'grn': grn,
                    'issue': 'Inventory added but inspection still pending'
                })
            
            print(f"GRN: {grn.grn_number}")
            print(f"  Status: {grn.status}")
            print(f"  Inspection: {inspection}")
            print(f"  Add to Inventory: {add_to_inv}")
            print(f"  Consistent: {'✓' if not (add_to_inv and inspection == 'pending') else '✗'}")
            print()
        
        if inconsistent_grns:
            print(f"\n=== Found {len(inconsistent_grns)} Inconsistent GRNs ===")
            for item in inconsistent_grns:
                print(f"- {item['grn'].grn_number}: {item['issue']}")
        else:
            print("\n=== All GRNs are consistent ===")
        
        return inconsistent_grns

def fix_grn_inspection_status():
    """Fix inspection status for GRNs that have inventory added"""
    
    with app.app_context():
        grns_to_fix = GRN.query.filter(
            GRN.inspection_status == 'pending'
        ).all()
        
        fixed_count = 0
        for grn in grns_to_fix:
            add_to_inv = getattr(grn, 'add_to_inventory', True)
            
            # If inventory is added and inspection is pending, auto-complete inspection
            if add_to_inv:
                print(f"Fixing {grn.grn_number}: pending → passed")
                grn.inspection_status = 'passed'
                fixed_count += 1
        
        if fixed_count > 0:
            db.session.commit()
            print(f"\n✓ Fixed {fixed_count} GRN inspection statuses")
        else:
            print("\n✓ No GRNs needed fixing")

if __name__ == "__main__":
    print("Step 1: Analyzing current state...")
    inconsistent = analyze_grn_inspection_consistency()
    
    if inconsistent:
        print("\nStep 2: Fixing inconsistencies...")
        fix_grn_inspection_status()
        
        print("\nStep 3: Re-checking after fixes...")
        analyze_grn_inspection_consistency()
    else:
        print("\nNo fixes needed - all GRNs are consistent!")