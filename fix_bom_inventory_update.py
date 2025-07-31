#!/usr/bin/env python3
"""
Fix BOM-based GRN inventory updates that went to wrong items
"""

from app import app, db
from models import JobWork, Item
from models_grn import GRN, GRNLineItem

def fix_bom_inventory_updates():
    """Fix inventory updates for BOM-based GRNs"""
    with app.app_context():
        try:
            # Find BOM-based job work with incorrect inventory updates
            job = JobWork.query.filter_by(job_number='JOB-2025-0002').first()
            
            if not job:
                print("Job JOB-2025-0002 not found")
                return
                
            print(f"Found job: {job.job_number}")
            print(f"BOM ID: {job.bom_id}, Production Quantity: {job.production_quantity}")
            
            # Find the GRNs for this job
            grns = GRN.query.filter_by(job_work_id=job.id).all()
            print(f"Found {len(grns)} GRNs for this job")
            
            if not grns:
                print("No GRNs found for this job")
                return
                
            # Find the final output item (Mounted Plate)
            final_output_item = None
            if job.processes:
                sorted_processes = sorted(job.processes, key=lambda x: x.sequence_number or 0)
                if sorted_processes and sorted_processes[-1].output_item:
                    final_output_item = sorted_processes[-1].output_item
                    print(f"Final output item: {final_output_item.name} ({final_output_item.code})")
            
            if not final_output_item:
                print("No final output item found")
                return
                
            # Calculate total quantities that were incorrectly added to input material
            total_incorrectly_added = 0
            for grn in grns:
                for line_item in grn.line_items:
                    if line_item.quantity_passed > 0:
                        total_incorrectly_added += line_item.quantity_passed
                        
            print(f"Total quantity incorrectly added to input material: {total_incorrectly_added}")
            
            if total_incorrectly_added > 0:
                # Get current inventory states
                print(f"Current Ms Sheet (input) finished qty: {job.item.qty_finished}")
                print(f"Current Mounted Plate (output) finished qty: {final_output_item.qty_finished}")
                
                # Move the incorrectly added quantity from input to output
                if job.item.qty_finished >= total_incorrectly_added:
                    job.item.qty_finished -= total_incorrectly_added
                    final_output_item.qty_finished = (final_output_item.qty_finished or 0) + total_incorrectly_added
                    
                    db.session.commit()
                    
                    print("✅ Inventory fixed successfully!")
                    print(f"New Ms Sheet (input) finished qty: {job.item.qty_finished}")
                    print(f"New Mounted Plate (output) finished qty: {final_output_item.qty_finished}")
                else:
                    print(f"Error: Input material only has {job.item.qty_finished} finished qty, cannot move {total_incorrectly_added}")
            else:
                print("No inventory corrections needed")
                
        except Exception as e:
            print(f"Error: {str(e)}")
            db.session.rollback()

if __name__ == '__main__':
    fix_bom_inventory_updates()