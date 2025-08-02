#!/usr/bin/env python3

"""
Test Script: Demonstrate PO/SO Accounting Integration
Creates sample data and demonstrates the complete accounting integration flow
"""

from app import app, db
from models import User, Supplier, Item, PurchaseOrder, SalesOrder
from services.accounting_automation import AccountingAutomation
from models_accounting import Account, AccountGroup, VoucherType, Voucher, JournalEntry
from datetime import datetime, date

def create_test_data():
    """Create test data for accounting integration demonstration"""
    with app.app_context():
        try:
            print("Creating test data for accounting integration...")
            
            # Create test user if not exists
            user = User.query.filter_by(username='admin').first()
            if not user:
                user = User(username='admin', email='admin@test.com', role='admin')
                db.session.add(user)
                db.session.flush()
            
            # Create test supplier
            supplier = Supplier.query.filter_by(name='Test Supplier').first()
            if not supplier:
                supplier = Supplier(
                    name='Test Supplier',
                    partner_type='supplier',
                    is_active=True,
                    email='supplier@test.com',
                    phone='9876543210'
                )
                db.session.add(supplier)
                db.session.flush()
            
            # Create test customer  
            customer = Supplier.query.filter_by(name='Test Customer').first()
            if not customer:
                customer = Supplier(
                    name='Test Customer',
                    partner_type='customer',
                    is_active=True,
                    email='customer@test.com',
                    phone='9876543211'
                )
                db.session.add(customer)
                db.session.flush()
            
            # Create test item
            item = Item.query.filter_by(code='TEST001').first()
            if not item:
                item = Item(
                    code='TEST001',
                    name='Test Product',
                    description='Test product for accounting integration',
                    unit_of_measure='Pcs',
                    unit_price=100.0,
                    hsn_code='1234',
                    gst_rate=18.0
                )
                db.session.add(item)
                db.session.flush()
            
            db.session.commit()
            print("✓ Test data created successfully")
            
            return user, supplier, customer, item
            
        except Exception as e:
            db.session.rollback()
            print(f"✗ Error creating test data: {e}")
            return None, None, None, None

def demonstrate_po_accounting_flow():
    """Demonstrate complete PO accounting integration flow"""
    with app.app_context():
        print("\n=== Purchase Order Accounting Integration Demo ===")
        
        user, supplier, customer, item = create_test_data()
        if not all([user, supplier, customer, item]):
            print("Failed to create test data")
            return
        
        try:
            # 1. Create Purchase Order
            print("\n1. Creating Purchase Order...")
            po = PurchaseOrder(
                po_number=f"PO-TEST-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                supplier_id=supplier.id,
                order_date=date.today(),
                payment_terms='30 Days',
                status='sent',
                total_amount=11800.0,  # 10000 + 1800 GST
                created_by=user.id
            )
            db.session.add(po)
            db.session.flush()
            print(f"✓ Created PO: {po.po_number}")
            
            # 2. Create accounting entries for PO commitment
            print("\n2. Creating PO commitment voucher...")
            commitment_voucher = AccountingAutomation.create_purchase_order_voucher(po)
            if commitment_voucher:
                print(f"✓ Created commitment voucher: {commitment_voucher.voucher_number}")
                print(f"  - Accounting Status: {po.accounting_status}")
                print(f"  - Supplier Account ID: {po.supplier_account_id}")
            else:
                print("✗ Failed to create commitment voucher")
                return
            
            # 3. Record advance payment (50% of total)
            print("\n3. Recording advance payment...")
            # First, we need a bank account
            bank_account = Account.query.filter_by(code='BANK').first()
            if not bank_account:
                # Create a basic bank account for demo
                asset_group = AccountGroup.query.filter_by(name='Current Assets').first()
                if asset_group:
                    bank_account = Account(
                        name='Test Bank Account',
                        code='BANK',
                        account_group_id=asset_group.id,
                        account_type='bank'
                    )
                    db.session.add(bank_account)
                    db.session.flush()
            
            if bank_account:
                advance_amount = 5900.0  # 50% of total
                advance_voucher = AccountingAutomation.create_advance_payment_voucher(
                    po, advance_amount, bank_account.id
                )
                if advance_voucher:
                    print(f"✓ Created advance payment voucher: {advance_voucher.voucher_number}")
                    print(f"  - Advance Amount: ₹{po.advance_amount_paid:,.2f}")
                    print(f"  - Accounting Status: {po.accounting_status}")
                else:
                    print("✗ Failed to create advance payment voucher")
            
            # 4. Close PO (simulating completion)
            print("\n4. Closing Purchase Order...")
            close_voucher = AccountingAutomation.close_purchase_order_voucher(po)
            if close_voucher:
                print(f"✓ Created PO closure voucher: {close_voucher.voucher_number}")
                print(f"  - Accounting Status: {po.accounting_status}")
            else:
                print("✗ Failed to close PO")
            
            db.session.commit()
            
            print(f"\n=== PO Accounting Summary ===")
            print(f"PO Number: {po.po_number}")
            print(f"Total Amount: ₹{po.total_amount:,.2f}")
            print(f"Advance Paid: ₹{po.advance_amount_paid:,.2f}")
            print(f"Final Status: {po.accounting_status}")
            print(f"Commitment Voucher: {po.purchase_commitment_voucher_id}")
            print(f"Advance Voucher: {po.advance_payment_voucher_id}")
            
        except Exception as e:
            db.session.rollback()
            print(f"✗ Error in PO accounting demo: {e}")

def demonstrate_so_accounting_flow():
    """Demonstrate complete SO accounting integration flow"""
    with app.app_context():
        print("\n=== Sales Order Accounting Integration Demo ===")
        
        user, supplier, customer, item = create_test_data()
        if not all([user, supplier, customer, item]):
            print("Failed to create test data")
            return
        
        try:
            # 1. Create Sales Order
            print("\n1. Creating Sales Order...")
            so = SalesOrder(
                so_number=f"SO-TEST-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                customer_id=customer.id,
                order_date=date.today(),
                payment_terms='30 Days',
                status='draft',
                total_amount=11800.0,  # 10000 + 1800 GST
                subtotal=10000.0,
                gst_amount=1800.0,
                created_by=user.id
            )
            db.session.add(so)
            db.session.flush()
            print(f"✓ Created SO: {so.so_number}")
            
            # 2. Create accounting entries for SO booking
            print("\n2. Creating SO booking voucher...")
            booking_voucher = AccountingAutomation.create_sales_order_voucher(so)
            if booking_voucher:
                print(f"✓ Created booking voucher: {booking_voucher.voucher_number}")
                print(f"  - Accounting Status: {so.accounting_status}")
                print(f"  - Customer Account ID: {so.customer_account_id}")
            else:
                print("✗ Failed to create booking voucher")
                return
            
            # 3. Record advance receipt (30% of total)
            print("\n3. Recording advance receipt...")
            bank_account = Account.query.filter_by(code='BANK').first()
            
            if bank_account:
                advance_amount = 3540.0  # 30% of total
                advance_voucher = AccountingAutomation.create_advance_receipt_voucher(
                    so, advance_amount, bank_account.id
                )
                if advance_voucher:
                    print(f"✓ Created advance receipt voucher: {advance_voucher.voucher_number}")
                    print(f"  - Advance Amount: ₹{so.advance_amount_received:,.2f}")
                    print(f"  - Accounting Status: {so.accounting_status}")
                else:
                    print("✗ Failed to create advance receipt voucher")
            
            # 4. Mark as delivered (revenue recognition)
            print("\n4. Marking Sales Order as delivered...")
            delivery_voucher = AccountingAutomation.create_sales_delivery_voucher(so)
            if delivery_voucher:
                print(f"✓ Created delivery voucher: {delivery_voucher.voucher_number}")
                print(f"  - Accounting Status: {so.accounting_status}")
            else:
                print("✗ Failed to create delivery voucher")
            
            # 5. Close SO
            print("\n5. Closing Sales Order...")
            so.accounting_status = 'closed'
            
            db.session.commit()
            
            print(f"\n=== SO Accounting Summary ===")
            print(f"SO Number: {so.so_number}")
            print(f"Total Amount: ₹{so.total_amount:,.2f}")
            print(f"Advance Received: ₹{so.advance_amount_received:,.2f}")
            print(f"Final Status: {so.accounting_status}")
            print(f"Booking Voucher: {so.sales_booking_voucher_id}")
            print(f"Advance Voucher: {so.advance_receipt_voucher_id}")
            print(f"Sales Voucher: {so.sales_voucher_id}")
            
        except Exception as e:
            db.session.rollback()
            print(f"✗ Error in SO accounting demo: {e}")

def show_voucher_details():
    """Show created voucher details"""
    with app.app_context():
        print("\n=== Generated Vouchers Summary ===")
        
        vouchers = Voucher.query.order_by(Voucher.created_at.desc()).limit(10).all()
        
        if not vouchers:
            print("No vouchers found")
            return
        
        for voucher in vouchers:
            print(f"\nVoucher: {voucher.voucher_number}")
            print(f"  Type: {voucher.voucher_type.name if voucher.voucher_type else 'N/A'}")
            print(f"  Date: {voucher.transaction_date}")
            print(f"  Amount: ₹{voucher.total_amount:,.2f}")
            print(f"  Narration: {voucher.narration}")
            
            # Show journal entries
            entries = JournalEntry.query.filter_by(voucher_id=voucher.id).all()
            for entry in entries:
                account_name = entry.account.name if entry.account else 'Unknown'
                print(f"    {entry.entry_type.title()}: {account_name} - ₹{entry.amount:,.2f}")

if __name__ == '__main__':
    print("Starting PO/SO Accounting Integration Demonstration")
    print("=" * 60)
    
    # Demonstrate PO flow
    demonstrate_po_accounting_flow()
    
    # Demonstrate SO flow  
    demonstrate_so_accounting_flow()
    
    # Show voucher details
    show_voucher_details()
    
    print("\n" + "=" * 60)
    print("Accounting Integration Demonstration Complete!")