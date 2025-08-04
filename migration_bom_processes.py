#!/usr/bin/env python3
"""
BOM Process Management Migration Script
Creates the bom_processes table for step-by-step manufacturing workflow management
"""

import os
import sys
from datetime import datetime

# Add the current directory to the path so we can import our models
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import BOMProcess

def create_bom_processes_table():
    """Create the bom_processes table"""
    try:
        with app.app_context():
            # Create the table
            db.create_all()
            print("✅ BOM Processes table created successfully!")
            
            # Verify table creation
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            
            if 'bom_processes' in tables:
                print("✅ Table 'bom_processes' confirmed in database")
                
                # Get column info
                columns = inspector.get_columns('bom_processes')
                print(f"✅ Table has {len(columns)} columns:")
                for col in columns:
                    print(f"   - {col['name']}: {col['type']}")
            else:
                print("❌ Table 'bom_processes' not found in database")
                return False
                
        return True
        
    except Exception as e:
        print(f"❌ Error creating BOM processes table: {str(e)}")
        return False

def add_sample_process_data():
    """Add sample process data for demonstration"""
    try:
        with app.app_context():
            from models import BOM
            
            # Find any existing BOM to add sample processes
            sample_bom = BOM.query.first()
            if not sample_bom:
                print("⚠️ No BOM found to add sample processes")
                return True
            
            # Sample manufacturing processes
            sample_processes = [
                {
                    'step_number': 1,
                    'process_name': 'Material Cutting',
                    'process_code': 'CUT',
                    'operation_description': 'Cut raw materials to required dimensions using CNC cutting machine',
                    'setup_time_minutes': 15.0,
                    'run_time_minutes': 2.5,
                    'labor_rate_per_hour': 500.0,
                    'cost_per_unit': 25.0,
                    'quality_check_required': True,
                    'estimated_scrap_percent': 2.0,
                    'is_outsourced': False
                },
                {
                    'step_number': 2,
                    'process_name': 'Welding Assembly',
                    'process_code': 'WELD',
                    'operation_description': 'Weld cut pieces according to assembly drawing specifications',
                    'setup_time_minutes': 20.0,
                    'run_time_minutes': 8.0,
                    'labor_rate_per_hour': 600.0,
                    'cost_per_unit': 80.0,
                    'quality_check_required': True,
                    'estimated_scrap_percent': 1.5,
                    'is_outsourced': False
                },
                {
                    'step_number': 3,
                    'process_name': 'Zinc Plating',
                    'process_code': 'ZINC',
                    'operation_description': 'Apply protective zinc coating for corrosion resistance',
                    'setup_time_minutes': 30.0,
                    'run_time_minutes': 45.0,
                    'labor_rate_per_hour': 400.0,
                    'cost_per_unit': 120.0,
                    'quality_check_required': True,
                    'estimated_scrap_percent': 0.5,
                    'is_outsourced': True
                },
                {
                    'step_number': 4,
                    'process_name': 'Final Assembly',
                    'process_code': 'ASSY',
                    'operation_description': 'Final assembly and packaging for shipment',
                    'setup_time_minutes': 10.0,
                    'run_time_minutes': 5.0,
                    'labor_rate_per_hour': 450.0,
                    'cost_per_unit': 35.0,
                    'quality_check_required': True,
                    'estimated_scrap_percent': 0.2,
                    'is_outsourced': False
                }
            ]
            
            processes_added = 0
            for process_data in sample_processes:
                # Check if process already exists
                existing = BOMProcess.query.filter_by(
                    bom_id=sample_bom.id,
                    step_number=process_data['step_number']
                ).first()
                
                if not existing:
                    process = BOMProcess(
                        bom_id=sample_bom.id,
                        **process_data
                    )
                    db.session.add(process)
                    processes_added += 1
            
            if processes_added > 0:
                db.session.commit()
                print(f"✅ Added {processes_added} sample manufacturing processes to BOM {sample_bom.bom_code}")
            else:
                print("ℹ️ Sample processes already exist")
                
        return True
        
    except Exception as e:
        print(f"❌ Error adding sample process data: {str(e)}")
        return False

def main():
    """Main migration function"""
    print("=" * 60)
    print("BOM PROCESS MANAGEMENT MIGRATION")
    print("=" * 60)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Step 1: Create BOM processes table
    print("Step 1: Creating BOM processes table...")
    if not create_bom_processes_table():
        print("❌ Migration failed at table creation step")
        return False
    
    print()
    
    # Step 2: Add sample process data
    print("Step 2: Adding sample process data...")
    if not add_sample_process_data():
        print("❌ Migration failed at sample data step")
        return False
    
    print()
    print("=" * 60)
    print("✅ BOM PROCESS MANAGEMENT MIGRATION COMPLETED SUCCESSFULLY!")
    print("=" * 60)
    print("📋 Summary:")
    print("   • BOM processes table created with comprehensive process tracking")
    print("   • Sample manufacturing workflow processes added for demonstration")
    print("   • Process routing includes step numbers, timing, costs, and outsourcing")
    print("   • Quality checkpoints and scrap tracking integrated per process")
    print("   • System now supports step-by-step manufacturing workflow management")
    print()
    print("🔧 BOM Module Enhancement:")
    print("   • Enhanced BOM model with process management properties")
    print("   • Manufacturing complexity assessment based on process count")
    print("   • Detailed process cost and time calculations")
    print("   • In-house vs outsourced process categorization")
    print()
    
    return True

if __name__ == "__main__":
    if main():
        sys.exit(0)
    else:
        sys.exit(1)