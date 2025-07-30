#!/usr/bin/env python3
"""
Create sample dynamic form fields for Job Work form to demonstrate the system
"""

from app import app, db
from models_dynamic_forms import FormTemplate, CustomField, DynamicFormManager

def create_sample_job_work_fields():
    """Create sample custom fields for Job Work form"""
    
    with app.app_context():
        print("🎯 Creating sample dynamic fields for Job Work form...")
        
        # Initialize templates first
        DynamicFormManager.create_default_templates()
        
        # Get Job Work template
        job_template = FormTemplate.query.filter_by(code='job_work_management').first()
        
        if not job_template:
            print("❌ Job Work template not found")
            return
        
        # Create sample custom fields
        fields_to_create = [
            {
                'field_name': 'priority_level',
                'label': 'Priority Level',
                'field_type': 'select',
                'options': '["Low","Medium","High","Urgent"]',
                'is_required': True,
                'field_group': 'Planning',
                'help_text': 'Set the priority level for this job work'
            },
            {
                'field_name': 'special_instructions',
                'label': 'Special Instructions',
                'field_type': 'textarea',
                'placeholder': 'Enter any special handling instructions',
                'field_group': 'Operations',
                'help_text': 'Additional instructions for the manufacturing team'
            },
            {
                'field_name': 'quality_requirement',
                'label': 'Quality Requirement',
                'field_type': 'select',
                'options': '["Standard","High Precision","Critical Inspection","Testing Required"]',
                'field_group': 'Quality Control',
                'help_text': 'Specify quality control requirements'
            },
            {
                'field_name': 'estimated_hours',
                'label': 'Estimated Hours',
                'field_type': 'number',
                'placeholder': 'Enter estimated work hours',
                'field_group': 'Planning',
                'help_text': 'Estimated time to complete this job work'
            },
            {
                'field_name': 'inspector_name',
                'label': 'Quality Inspector',
                'field_type': 'text',
                'placeholder': 'Enter inspector name',
                'field_group': 'Quality Control',
                'help_text': 'Assigned quality control inspector'
            }
        ]
        
        # Create the fields
        created_count = 0
        for field_data in fields_to_create:
            # Check if field already exists
            existing_field = CustomField.query.filter_by(
                form_template_id=job_template.id,
                field_name=field_data['field_name']
            ).first()
            
            if not existing_field:
                field = CustomField(
                    form_template_id=job_template.id,
                    field_name=field_data['field_name'],
                    label=field_data['label'],
                    field_type=field_data['field_type'],
                    field_options=field_data.get('options'),
                    placeholder=field_data.get('placeholder'),
                    is_required=field_data.get('is_required', False),
                    field_group=field_data.get('field_group'),
                    help_text=field_data.get('help_text'),
                    display_order=created_count + 1
                )
                db.session.add(field)
                created_count += 1
                print(f"   ✓ Created field: {field_data['label']}")
        
        db.session.commit()
        
        print(f"\n✅ Created {created_count} custom fields for Job Work form")
        print("\n🎯 Now visit the Job Work form and you'll see:")
        print("   • Custom Fields section with blue header")
        print("   • Priority Level dropdown")
        print("   • Special Instructions textarea")
        print("   • Quality Requirement selection")
        print("   • Estimated Hours input")
        print("   • Quality Inspector field")
        print("\n🔗 These fields are automatically loaded via API and integrated into your working form!")

if __name__ == "__main__":
    create_sample_job_work_fields()