#!/usr/bin/env python3
"""
Analyze unused fields in database models by checking actual usage patterns
"""

import re
import os
from collections import defaultdict

def analyze_field_usage():
    """Analyze which model fields are actually used in the codebase"""
    
    print("=== ANALYZING FIELD USAGE IN MODELS ===\n")
    
    # Read models.py
    with open('models.py', 'r') as f:
        models_content = f.read()
    
    # Extract field definitions from models
    field_pattern = r'(\w+)\s*=\s*db\.Column\('
    model_pattern = r'class (\w+)\(db\.Model\):'
    
    models = {}
    current_model = None
    
    for line in models_content.split('\n'):
        # Check for model class definition
        model_match = re.search(model_pattern, line)
        if model_match:
            current_model = model_match.group(1)
            models[current_model] = {'fields': [], 'line': line}
            continue
        
        # Check for field definition
        if current_model:
            field_match = re.search(field_pattern, line.strip())
            if field_match:
                field_name = field_match.group(1)
                models[current_model]['fields'].append(field_name)
    
    # Check usage in route files
    route_files = []
    
    # Get route files from routes directory
    if os.path.exists('routes'):
        route_files.extend([os.path.join('routes', f) for f in os.listdir('routes') if f.endswith('.py')])
    
    # Get route files from root directory
    route_files.extend([f for f in os.listdir('.') if f.startswith('routes') and f.endswith('.py')])
    
    # Also check forms and services
    route_files.extend([f for f in os.listdir('.') if f.startswith(('forms', 'services')) and f.endswith('.py')])
    
    field_usage = defaultdict(set)
    
    print("Checking usage in route/form/service files...")
    for route_file in route_files:
        try:
            with open(route_file, 'r') as f:
                content = f.read()
                
            # Find field usage patterns like model.field_name
            for model_name, model_data in models.items():
                for field_name in model_data['fields']:
                    patterns = [
                        f'{model_name}.{field_name}',
                        f"'{field_name}'",
                        f'"{field_name}"',
                        f'.{field_name}',
                        f'filter_by({field_name}=',
                        f'order_by({field_name}',
                        f'order_by({model_name}.{field_name}'
                    ]
                    
                    for pattern in patterns:
                        if pattern in content:
                            field_usage[f'{model_name}.{field_name}'].add(route_file)
                            break
        except Exception as e:
            print(f"Error reading {route_file}: {e}")
    
    # Check template usage
    template_usage = defaultdict(set)
    if os.path.exists('templates'):
        print("Checking usage in templates...")
        for root, dirs, files in os.walk('templates'):
            for file in files:
                if file.endswith('.html'):
                    template_path = os.path.join(root, file)
                    try:
                        with open(template_path, 'r') as f:
                            content = f.read()
                        
                        for model_name, model_data in models.items():
                            for field_name in model_data['fields']:
                                patterns = [
                                    f'.{field_name}',
                                    f'["{field_name}"]',
                                    f"['{field_name}']"
                                ]
                                
                                for pattern in patterns:
                                    if pattern in content:
                                        template_usage[f'{model_name}.{field_name}'].add(template_path)
                                        break
                    except Exception as e:
                        continue
    
    # Generate report
    print("\n=== FIELD USAGE ANALYSIS ===\n")
    
    total_fields = 0
    used_fields = 0
    unused_fields = []
    
    for model_name, model_data in models.items():
        print(f"Model: {model_name}")
        print("-" * (len(model_name) + 7))
        
        model_unused = []
        for field_name in model_data['fields']:
            total_fields += 1
            field_key = f'{model_name}.{field_name}'
            
            route_files_using = field_usage.get(field_key, set())
            template_files_using = template_usage.get(field_key, set())
            
            if route_files_using or template_files_using:
                used_fields += 1
                print(f"  ✓ {field_name}")
                if route_files_using:
                    print(f"    Routes: {', '.join(route_files_using)}")
                if template_files_using:
                    print(f"    Templates: {', '.join(os.path.basename(f) for f in template_files_using)}")
            else:
                model_unused.append(field_name)
                unused_fields.append(field_key)
        
        if model_unused:
            print(f"  ⚠️  Potentially unused fields: {', '.join(model_unused)}")
        
        print()
    
    print(f"\n=== SUMMARY ===")
    print(f"Total fields analyzed: {total_fields}")
    print(f"Fields in use: {used_fields}")
    print(f"Potentially unused fields: {len(unused_fields)}")
    
    if unused_fields:
        print(f"\nPotentially unused fields ({len(unused_fields)}):")
        for field in unused_fields:
            print(f"  - {field}")
    
    return unused_fields

if __name__ == "__main__":
    analyze_field_usage()