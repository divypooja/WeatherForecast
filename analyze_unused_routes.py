#!/usr/bin/env python3
"""
Analyze unused routes and templates that can be safely removed
"""

import os
import re

def analyze_unused_routes():
    """Find routes that are not registered in app.py"""
    
    print("=== ROUTE CLEANUP ANALYSIS ===\n")
    
    # Get all route files
    route_files = []
    if os.path.exists('routes'):
        route_files = [f for f in os.listdir('routes') if f.endswith('.py') and not f.startswith('__')]
    
    # Also check root directory
    root_route_files = [f for f in os.listdir('.') if f.startswith('routes') and f.endswith('.py')]
    
    print(f"Route files found: {len(route_files) + len(root_route_files)}")
    
    # Read app.py to find registered blueprints
    registered_blueprints = []
    try:
        with open('app.py', 'r') as f:
            app_content = f.read()
            # Find all register_blueprint calls
            blueprint_matches = re.findall(r'register_blueprint\((\w+)', app_content)
            registered_blueprints = list(set(blueprint_matches))
    except Exception as e:
        print(f"Error reading app.py: {e}")
        return
    
    print(f"\nRegistered blueprints ({len(registered_blueprints)}):")
    for bp in sorted(registered_blueprints):
        print(f"  ✓ {bp}")
    
    # Analyze each route file
    unused_routes = []
    used_routes = []
    
    all_routes = route_files + root_route_files
    
    for route_file in all_routes:
        try:
            if route_file.startswith('routes') and not route_file.startswith('routes/'):
                file_path = route_file  # Root directory file
            else:
                file_path = f'routes/{route_file}'
                
            with open(file_path, 'r') as f:
                content = f.read()
                
            # Extract blueprint name from file
            bp_matches = re.findall(r'(\w+_bp)\s*=\s*Blueprint', content)
            if bp_matches:
                blueprint_name = bp_matches[0]
                if blueprint_name in registered_blueprints:
                    used_routes.append((route_file, blueprint_name))
                else:
                    unused_routes.append((route_file, blueprint_name))
            else:
                # Check if it's a special case
                if 'material_inspection' in route_file:
                    # This might be imported directly
                    if 'material_inspection' in app_content:
                        used_routes.append((route_file, 'material_inspection'))
                    else:
                        unused_routes.append((route_file, 'unknown'))
                else:
                    unused_routes.append((route_file, 'no_blueprint'))
                    
        except Exception as e:
            print(f"Error analyzing {route_file}: {e}")
    
    print(f"\n=== USED ROUTES ({len(used_routes)}) ===")
    for route_file, bp_name in sorted(used_routes):
        print(f"  ✓ {route_file} ({bp_name})")
    
    print(f"\n=== UNUSED ROUTES ({len(unused_routes)}) ===")
    for route_file, bp_name in sorted(unused_routes):
        print(f"  ⚠️  {route_file} ({bp_name})")
    
    # Find associated templates
    print(f"\n=== CHECKING ASSOCIATED TEMPLATES ===")
    template_dirs = []
    if os.path.exists('templates'):
        for root, dirs, files in os.walk('templates'):
            for d in dirs:
                template_dirs.append(os.path.join(root, d))
    
    for route_file, bp_name in unused_routes:
        route_name = route_file.replace('.py', '').replace('routes/', '')
        
        # Look for template directories matching route name
        matching_template_dirs = []
        for template_dir in template_dirs:
            dir_name = os.path.basename(template_dir)
            if route_name in dir_name or dir_name in route_name:
                matching_template_dirs.append(template_dir)
        
        if matching_template_dirs:
            print(f"  📁 {route_file} -> Templates: {', '.join(matching_template_dirs)}")
    
    return unused_routes

if __name__ == "__main__":
    unused_routes = analyze_unused_routes()
    
    if unused_routes:
        print(f"\n=== RECOMMENDATIONS ===")
        print("The following files can potentially be removed:")
        for route_file, bp_name in unused_routes:
            print(f"  - routes/{route_file}")
        print("\nRemember to also check for associated templates and test thoroughly!")