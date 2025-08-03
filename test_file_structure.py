#!/usr/bin/env python3
"""
Test script to verify the organized file upload structure
"""

import os
from utils_documents import get_document_folder, DOCUMENT_FOLDERS

def test_file_structure():
    """Test the organized file upload structure"""
    print("🧪 Testing Organized File Upload Structure")
    print("=" * 50)
    
    # Test folder mapping
    print("\n📁 Document Folder Mapping:")
    for doc_type, folder in DOCUMENT_FOLDERS.items():
        print(f"  {doc_type} → uploads/{folder}/")
    
    # Test actual directory structure
    print("\n📂 Current Directory Structure:")
    uploads_dir = 'uploads'
    if os.path.exists(uploads_dir):
        for root, dirs, files in os.walk(uploads_dir):
            level = root.replace(uploads_dir, '').count(os.sep)
            indent = ' ' * 2 * level
            print(f"{indent}{os.path.basename(root)}/")
            subindent = ' ' * 2 * (level + 1)
            for file in files:
                print(f"{subindent}{file}")
    else:
        print("  uploads/ directory not found")
    
    # Test examples of expected file structure
    print("\n📋 Examples of organized file structure:")
    examples = [
        ("Purchase Order", "PO-1001.pdf", "po", "PO-1001"),
        ("GRN Document", "delivery-challan.jpg", "grn", "GRN-3002"),
        ("Job Work", "return-slip.png", "jobwork", "JW-2001"),
        ("Invoice", "INV-8843.pdf", "invoices", "INV-8843"),
        ("Employee", "resume.pdf", "hr/employees", "EMP-001"),
        ("Salary", "payslip.pdf", "hr/salaries", "SAL-202501"),
        ("Advance", "advance-form.pdf", "hr/advances", "ADV-001")
    ]
    
    for doc_type, filename, expected_folder, ref_num in examples:
        folder = get_document_folder(expected_folder)
        print(f"  {doc_type}: {filename} → uploads/{folder}/{ref_num}_{filename}")
    
    print("\n✅ File Upload Structure Test Complete!")
    print("\n💡 Benefits of this structure:")
    print("  • Easy to locate files by document type")
    print("  • Reference numbers in filenames for traceability")
    print("  • Organized folders prevent file clutter")
    print("  • Better backup and maintenance processes")

if __name__ == '__main__':
    test_file_structure()