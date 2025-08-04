#!/usr/bin/env python3
"""
Check all major forms for potential database schema issues
Similar to the factory_expenses voucher_id issue
"""

from app import app, db
from sqlalchemy import text, inspect
import traceback

def check_table_columns(table_name, expected_columns):
    """Check if a table has all expected columns"""
    try:
        result = db.session.execute(text(f"PRAGMA table_info({table_name})"))
        existing_columns = [row[1] for row in result.fetchall()]
        
        missing_columns = [col for col in expected_columns if col not in existing_columns]
        
        return {
            'table': table_name,
            'existing_columns': existing_columns,
            'missing_columns': missing_columns,
            'has_issues': len(missing_columns) > 0
        }
    except Exception as e:
        return {
            'table': table_name,
            'error': str(e),
            'has_issues': True
        }

def check_all_critical_tables():
    """Check all critical business tables for schema issues"""
    with app.app_context():
        print("🔍 Checking all critical business tables for schema issues...")
        
        # Define critical tables and their expected columns based on accounting integration
        critical_tables = {
            'purchase_orders': ['voucher_id'],
            'sales_orders': ['voucher_id'],
            'grn': ['voucher_id'],
            'production_entries': ['voucher_id'],
            'job_work': ['voucher_id'],
            'job_work_entries': ['voucher_id'],
            'salary_records': ['voucher_id'],
            'factory_expenses': ['voucher_id'],  # We already fixed this
            'invoices': ['voucher_id'],
            'payments': ['voucher_id'],
            'inventory_transactions': ['voucher_id']
        }
        
        issues_found = []
        tables_checked = 0
        
        for table_name, expected_cols in critical_tables.items():
            print(f"📋 Checking table: {table_name}")
            result = check_table_columns(table_name, expected_cols)
            
            if result.get('has_issues'):
                if 'error' in result:
                    print(f"  ❌ Error checking {table_name}: {result['error']}")
                    if "no such table" not in result['error'].lower():
                        issues_found.append(result)
                else:
                    print(f"  ❌ Missing columns in {table_name}: {result['missing_columns']}")
                    issues_found.append(result)
            else:
                print(f"  ✅ {table_name} - All required columns present")
            
            tables_checked += 1
        
        print(f"\n📊 Summary:")
        print(f"Tables checked: {tables_checked}")
        print(f"Tables with issues: {len(issues_found)}")
        
        if issues_found:
            print(f"\n🔧 Tables requiring fixes:")
            for issue in issues_found:
                if 'missing_columns' in issue:
                    print(f"  - {issue['table']}: Missing {issue['missing_columns']}")
                elif 'error' in issue:
                    print(f"  - {issue['table']}: {issue['error']}")
        else:
            print(f"\n✅ All critical tables have proper schema!")
        
        return issues_found

if __name__ == '__main__':
    check_all_critical_tables()