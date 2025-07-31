#!/usr/bin/env python3
"""
Fix existing job work records to set production_quantity for BOM-based jobs
"""

from app import app, db
from models import JobWork, JobWorkProcess

def fix_job_work_production_quantities():
    """Update existing job work records with production_quantity"""
    with app.app_context():
        try:
            # Find JOB-2025-0002 which was created with BOM but missing production_quantity
            job = JobWork.query.filter_by(job_number='JOB-2025-0002').first()
            
            if job:
                print(f"Found job: {job.job_number}")
                print(f"Current bom_id: {job.bom_id}")
                print(f"Current production_quantity: {job.production_quantity}")
                
                # Check if it has processes with output quantities
                if job.processes:
                    total_output = sum(p.output_quantity for p in job.processes if p.output_quantity)
                    if total_output > 0:
                        job.production_quantity = total_output
                        print(f"Setting production_quantity to: {total_output}")
                        
                        db.session.commit()
                        print("✅ Job work updated successfully!")
                        
                        # Test the pending_quantity calculation
                        print(f"New pending_quantity: {job.pending_quantity}")
                        print(f"Pending receipt display: {job.pending_receipt_display}")
                    else:
                        print("No output quantities found in processes")
                else:
                    print("No processes found for this job")
            else:
                print("Job JOB-2025-0002 not found")
                
        except Exception as e:
            print(f"Error: {str(e)}")
            db.session.rollback()

if __name__ == '__main__':
    fix_job_work_production_quantities()