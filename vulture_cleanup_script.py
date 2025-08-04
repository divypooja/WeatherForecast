#!/usr/bin/env python3
"""
Vulture-based cleanup script for Factory Management System
"""

import os
import subprocess
import re

def run_vulture_analysis():
    """Run vulture analysis and categorize findings"""
    
    print("=== VULTURE DEAD CODE ANALYSIS ===\n")
    
    # Run vulture with different confidence levels
    confidence_levels = [90, 80, 70, 60]
    results = {}
    
    for confidence in confidence_levels:
        print(f"Running vulture with {confidence}% confidence...")
        try:
            result = subprocess.run([
                'vulture', '.', 
                f'--min-confidence={confidence}',
                '--exclude=migrations,__pycache__,.cache,.git,static,uploads,instance'
            ], capture_output=True, text=True)
            
            if result.stdout:
                results[confidence] = result.stdout.split('\n')
            else:
                results[confidence] = []
                
        except Exception as e:
            print(f"Error running vulture with confidence {confidence}: {e}")
            results[confidence] = []
    
    return results

def categorize_findings(results):
    """Categorize vulture findings by type and safety"""
    
    categories = {
        'safe_to_remove': [],
        'imports_unused': [],
        'functions_unused': [],
        'variables_unused': [],
        'classes_unused': [],
        'attributes_unused': [],
        'requires_verification': []
    }
    
    # Process highest confidence findings first
    for confidence in [90, 80, 70, 60]:
        if confidence not in results:
            continue
            
        print(f"\n=== CONFIDENCE {confidence}% FINDINGS ===")
        
        for line in results[confidence]:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
                
            print(f"  {line}")
            
            # Categorize by type
            if 'unused import' in line:
                categories['imports_unused'].append((line, confidence))
            elif 'unused function' in line:
                categories['functions_unused'].append((line, confidence))
            elif 'unused variable' in line:
                categories['variables_unused'].append((line, confidence))
            elif 'unused class' in line:
                categories['classes_unused'].append((line, confidence))
            elif 'unused attribute' in line:
                categories['attributes_unused'].append((line, confidence))
            else:
                categories['requires_verification'].append((line, confidence))
    
    return categories

def generate_cleanup_recommendations(categories):
    """Generate actionable cleanup recommendations"""
    
    print(f"\n=== CLEANUP RECOMMENDATIONS ===\n")
    
    # Safe to remove (high confidence imports and variables)
    safe_items = []
    safe_items.extend([(item, conf) for item, conf in categories['imports_unused'] if conf >= 80])
    safe_items.extend([(item, conf) for item, conf in categories['variables_unused'] if conf >= 80])
    
    if safe_items:
        print("🟢 SAFE TO REMOVE (High Confidence):")
        for item, conf in safe_items:
            print(f"  {conf}% - {item}")
    
    # Requires verification (functions, classes)
    verify_items = []
    verify_items.extend(categories['functions_unused'])
    verify_items.extend(categories['classes_unused'])
    verify_items.extend(categories['attributes_unused'])
    
    if verify_items:
        print(f"\n🟡 REQUIRES VERIFICATION:")
        for item, conf in verify_items:
            print(f"  {conf}% - {item}")
    
    # Manual review needed
    if categories['requires_verification']:
        print(f"\n🔴 MANUAL REVIEW NEEDED:")
        for item, conf in categories['requires_verification']:
            print(f"  {conf}% - {item}")
    
    return {
        'safe_to_remove': safe_items,
        'needs_verification': verify_items,
        'manual_review': categories['requires_verification']
    }

def main():
    """Main cleanup analysis function"""
    
    print("Factory Management System - Dead Code Analysis")
    print("=" * 50)
    
    # Check if vulture is available
    try:
        subprocess.run(['vulture', '--version'], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Vulture not found. Please install: pip install vulture")
        return
    
    # Run analysis
    results = run_vulture_analysis()
    
    # Categorize findings
    categories = categorize_findings(results)
    
    # Generate recommendations
    recommendations = generate_cleanup_recommendations(categories)
    
    print(f"\n=== SUMMARY ===")
    print(f"Safe to remove: {len(recommendations['safe_to_remove'])} items")
    print(f"Needs verification: {len(recommendations['needs_verification'])} items")
    print(f"Manual review: {len(recommendations['manual_review'])} items")
    
    return recommendations

if __name__ == "__main__":
    main()