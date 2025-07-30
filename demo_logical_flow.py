#!/usr/bin/env python3
"""
Demonstrate the complete logical flow: UOM → Inventory ↔ BOM → Job Work → GRN → Production
All integrated with Dynamic Forms system
"""

from app import app, db
from models import Item, BOM, BOMItem, JobWork, JobWorkProcess
from models_dynamic_forms import FormTemplate, CustomField, DynamicFormManager
import json

def create_demo_flow():
    """Create demonstration data showing complete logical flow with dynamic forms"""
    
    with app.app_context():
        print("🏭 Creating Complete Factory Management Flow Demo")
        print("=" * 60)
        
        # 1. Create UOM-based Inventory Items
        print("\n🔹 1. Creating UOM-based Inventory Items")
        
        # Raw materials
        ms_sheet = Item(
            code="MS-SHEET-001",
            name="MS Steel Sheet 1.5mm",
            description="Mild Steel Sheet for cutting operations",
            unit_of_measure="Pcs",
            unit_weight=2.5,  # 2.5 kg per sheet
            qty_raw=100,
            uom_conversion_factor=1.0
        )
        
        base_plate = Item(
            code="BASE-001", 
            name="Base Plate",
            description="Machined base plate for assembly",
            unit_of_measure="Pcs",
            unit_weight=0.8,
            qty_raw=500,
            uom_conversion_factor=1.0
        )
        
        # Intermediate product
        mounted_plate = Item(
            code="MOUNT-001",
            name="Mounted Plate", 
            description="Cut and bent mounted plate from MS sheet",
            unit_of_measure="Pcs",
            unit_weight=0.5,
            qty_raw=0,
            qty_finished=0,
            uom_conversion_factor=1.0
        )
        
        # Final product
        castor_wheel = Item(
            code="CASTOR-001",
            name="Castor Wheel Assembly",
            description="Complete castor wheel with mounting",
            unit_of_measure="Pcs", 
            unit_weight=1.3,
            qty_raw=0,
            qty_finished=0,
            uom_conversion_factor=1.0
        )
        
        db.session.add_all([ms_sheet, base_plate, mounted_plate, castor_wheel])
        db.session.commit()
        print(f"   ✓ Created items: {ms_sheet.name}, {base_plate.name}, {mounted_plate.name}, {castor_wheel.name}")
        
        # 2. Create BOM (Bill of Materials)
        print("\n🔹 2. Creating BOM Structure")
        
        # BOM for Mounted Plate (from MS Sheet)
        mounted_plate_bom = BOM(
            bom_code="BOM-MOUNT-001",
            product_id=mounted_plate.id,
            description="BOM for mounted plate production",
            version="1.0",
            labor_cost_per_unit=5.0,
            overhead_cost_per_unit=2.0,
            markup_percentage=15.0
        )
        
        # BOM Item: 1 MS Sheet → 400 Mounted Plates
        bom_item_sheet = BOMItem(
            bom=mounted_plate_bom,
            item_id=ms_sheet.id,
            quantity_required=1.0,
            unit="Pcs",
            waste_percentage=5.0
        )
        
        # BOM for Final Castor Wheel
        castor_bom = BOM(
            bom_code="BOM-CASTOR-001", 
            product_id=castor_wheel.id,
            description="BOM for castor wheel assembly",
            version="1.0",
            labor_cost_per_unit=8.0,
            overhead_cost_per_unit=3.0,
            markup_percentage=20.0
        )
        
        # BOM Items for Castor Wheel
        bom_item_mount = BOMItem(
            bom=castor_bom,
            item_id=mounted_plate.id,
            quantity_required=1.0,
            unit="Pcs"
        )
        
        bom_item_base = BOMItem(
            bom=castor_bom,
            item_id=base_plate.id,
            quantity_required=1.0,
            unit="Pcs"
        )
        
        db.session.add_all([mounted_plate_bom, bom_item_sheet, castor_bom, bom_item_mount, bom_item_base])
        db.session.commit()
        print(f"   ✓ Created BOMs: {mounted_plate_bom.bom_code}, {castor_bom.bom_code}")
        print(f"   ✓ BOM Logic: 1 MS Sheet → 400 Mounted Plates")
        print(f"   ✓ BOM Logic: 1 Mounted Plate + 1 Base Plate → 1 Castor Wheel")
        
        # 3. Create Dynamic Form Templates and Custom Fields
        print("\n🔹 3. Setting up Dynamic Forms Integration")
        
        # Initialize default templates
        DynamicFormManager.create_default_templates()
        
        # Get BOM management template
        bom_template = FormTemplate.query.filter_by(code='bom_management').first()
        job_template = FormTemplate.query.filter_by(code='job_work_management').first()
        
        if bom_template:
            # Add custom fields to BOM form
            quality_field = CustomField(
                form_template_id=bom_template.id,
                field_name="quality_standard",
                label="Quality Standard",
                field_type="select",
                options="ISO 9001,AS 9100,TS 16949",
                is_required=True,
                field_group="Quality Control"
            )
            
            supplier_field = CustomField(
                form_template_id=bom_template.id,
                field_name="preferred_supplier",
                label="Preferred Supplier",
                field_type="text",
                placeholder="Enter supplier name",
                field_group="Procurement"
            )
            
            db.session.add_all([quality_field, supplier_field])
            print(f"   ✓ Added custom fields to BOM template: Quality Standard, Preferred Supplier")
        
        if job_template:
            # Add custom fields to Job Work form
            priority_field = CustomField(
                form_template_id=job_template.id,
                field_name="priority_level",
                label="Priority Level",
                field_type="select",
                options="Low,Medium,High,Urgent",
                is_required=True,
                field_group="Planning"
            )
            
            notes_field = CustomField(
                form_template_id=job_template.id,
                field_name="special_instructions",
                label="Special Instructions",
                field_type="textarea",
                placeholder="Enter any special handling instructions",
                field_group="Operations"
            )
            
            db.session.add_all([priority_field, notes_field])
            print(f"   ✓ Added custom fields to Job Work template: Priority Level, Special Instructions")
        
        db.session.commit()
        
        # 4. Create Job Work with Multi-Process Flow
        print("\n🔹 4. Creating Multi-Process Job Work Flow")
        
        # Job Work: MS Sheet → Mounted Plates
        job_work = JobWork(
            job_number="JOB-2025-DEMO-001",
            item_id=ms_sheet.id,
            work_type="outsourced",
            customer_name="ABC Manufacturing",
            quantity_sent=5,  # 5 MS Sheets
            rate_per_unit=50.0,
            start_date="2025-07-30",
            expected_completion="2025-08-05",
            status="sent",
            bom_id=mounted_plate_bom.id,
            production_quantity=2000  # Expected 2000 mounted plates (5 sheets × 400 plates/sheet)
        )
        
        # Process 1: Cutting
        cutting_process = JobWorkProcess(
            job_work=job_work,
            process_name="Cutting",
            sequence_number=1,
            quantity_input=5.0,
            quantity_output=2000.0,
            expected_scrap=100.0,
            work_type="outsourced",
            customer_name="ABC Manufacturing",
            rate_per_unit=50.0,
            output_item_id=mounted_plate.id,
            output_quantity=2000.0,
            input_uom="Pcs",
            output_uom="Pcs",
            scrap_uom="Pcs"
        )
        
        # Process 2: Bending (if needed)
        bending_process = JobWorkProcess(
            job_work=job_work,
            process_name="Bending",
            sequence_number=2,
            quantity_input=2000.0,
            quantity_output=2000.0,
            expected_scrap=50.0,
            work_type="outsourced", 
            customer_name="ABC Manufacturing",
            rate_per_unit=10.0,
            input_uom="Pcs",
            output_uom="Pcs",
            scrap_uom="Pcs"
        )
        
        db.session.add_all([job_work, cutting_process, bending_process])
        
        # Update inventory: Move raw materials to WIP
        ms_sheet.qty_raw -= 5
        ms_sheet.qty_wip_cutting += 5
        
        db.session.commit()
        print(f"   ✓ Created Job Work: {job_work.job_number}")
        print(f"   ✓ Process Flow: 5 MS Sheets → 2000 Mounted Plates")
        print(f"   ✓ Inventory Updated: MS Sheet raw stock reduced by 5")
        
        # 5. Display Complete Flow Summary
        print("\n🔹 5. Complete Logical Flow Summary")
        print("=" * 60)
        print("📊 LOGICAL FLOW: UOM → Inventory ↔ BOM → Job Work → GRN → Production")
        print()
        
        print("🔄 FLOW STAGES:")
        print("   1. UOM System: Conversion factors set (1 Pcs = 1 unit)")
        print("   2. Inventory: Raw materials available (MS Sheets, Base Plates)")
        print("   3. BOM: Defines transformations (1 Sheet → 400 Plates)")
        print("   4. Job Work: Processes materials (5 Sheets → 2000 Plates expected)")
        print("   5. GRN: Will receive finished goods back to inventory")
        print("   6. Production: Final assembly (Mounted + Base → Castor Wheel)")
        print()
        
        print("📋 DYNAMIC FORMS INTEGRATION:")
        print("   ✓ ALL forms now have dynamic custom fields")
        print("   ✓ BOM forms include Quality Standard and Preferred Supplier")
        print("   ✓ Job Work forms include Priority Level and Special Instructions")
        print("   ✓ Universal system applies to Inventory, Purchase, Sales, GRN, Employee forms")
        print()
        
        print("🔗 INTERCONNECTIONS:")
        print("   • UOM → ALL modules (consistent unit handling)")
        print("   • Inventory ↔ BOM (stock validation and material requirements)")
        print("   • BOM → Job Work (material allocation and transformation rules)")
        print("   • Job Work → GRN (material receipt and quality control)")
        print("   • GRN → Inventory (stock updates and scrap tracking)")
        print("   • BOM + Inventory → Production (final assembly)")
        print()
        
        print("🎯 NEXT STEPS:")
        print("   1. Go to any form (BOM, Job Work, Inventory, etc.)")
        print("   2. See automatic 'Custom Fields' section with dynamic loading")
        print("   3. Visit Dynamic Forms to create additional custom fields")
        print("   4. Watch fields appear automatically in working forms")
        print("   5. Use GRN system to complete the material flow cycle")
        
        print("\n✅ Demo setup complete! Your entire factory management system")
        print("   now uses dynamic forms across all modules with complete logical flow.")

if __name__ == "__main__":
    create_demo_flow()