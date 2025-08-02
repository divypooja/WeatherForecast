"""
Automatic Journal Entry Generation Service
Integrates accounting with existing factory operations
"""
from app import db
from models_accounting import (Account, AccountGroup, Voucher, VoucherType, JournalEntry, 
                             Invoice, InvoiceItem, TaxMaster)
from models import (PurchaseOrder, SalesOrder, FactoryExpense, Production, Supplier, Item,
                   Employee, SalaryRecord, CompanySettings)
from models_grn import GRN, GRNLineItem
from datetime import datetime, date
from decimal import Decimal

class AccountingAutomation:
    """Service for automatic journal entry generation"""
    
    @staticmethod
    def setup_default_accounts():
        """Create default chart of accounts"""
        try:
            # Create default account groups if they don't exist
            default_groups = [
                {'name': 'Current Assets', 'code': 'CA', 'group_type': 'assets'},
                {'name': 'Fixed Assets', 'code': 'FA', 'group_type': 'assets'},
                {'name': 'Current Liabilities', 'code': 'CL', 'group_type': 'liabilities'},
                {'name': 'Long Term Liabilities', 'code': 'LTL', 'group_type': 'liabilities'},
                {'name': 'Capital & Reserves', 'code': 'CR', 'group_type': 'equity'},
                {'name': 'Sales & Income', 'code': 'SI', 'group_type': 'income'},
                {'name': 'Direct Expenses', 'code': 'DE', 'group_type': 'expenses'},
                {'name': 'Indirect Expenses', 'code': 'IE', 'group_type': 'expenses'},
            ]
            
            for group_data in default_groups:
                existing_group = AccountGroup.query.filter_by(code=group_data['code']).first()
                if not existing_group:
                    group = AccountGroup(**group_data)
                    db.session.add(group)
            
            db.session.flush()
            
            # Create sub-groups
            sub_groups = [
                {'name': 'Inventory', 'code': 'INV', 'group_type': 'assets', 'parent': 'Current Assets'},
                {'name': 'Sundry Debtors', 'code': 'SD', 'group_type': 'assets', 'parent': 'Current Assets'},
                {'name': 'Cash & Bank', 'code': 'CB', 'group_type': 'assets', 'parent': 'Current Assets'},
                {'name': 'Sundry Creditors', 'code': 'SC', 'group_type': 'liabilities', 'parent': 'Current Liabilities'},
                {'name': 'Duties & Taxes', 'code': 'DT', 'group_type': 'liabilities', 'parent': 'Current Liabilities'},
            ]
            
            for sub_group_data in sub_groups:
                existing_sub_group = AccountGroup.query.filter_by(code=sub_group_data['code']).first()
                if not existing_sub_group:
                    parent = AccountGroup.query.filter_by(name=sub_group_data['parent']).first()
                    if parent:
                        sub_group = AccountGroup(
                            name=sub_group_data['name'],
                            code=sub_group_data['code'],
                            group_type=sub_group_data['group_type'],
                            parent_group_id=parent.id
                        )
                        db.session.add(sub_group)
            
            db.session.flush()
            
            # Create default accounts
            default_accounts = [
                # Assets
                {'name': 'Raw Material Inventory', 'code': 'RM_INV', 'group': 'Inventory', 'type': 'current_asset'},
                {'name': 'Work in Progress', 'code': 'WIP_INV', 'group': 'Inventory', 'type': 'current_asset'},
                {'name': 'Finished Goods Inventory', 'code': 'FG_INV', 'group': 'Inventory', 'type': 'current_asset'},
                {'name': 'Scrap Inventory', 'code': 'SCRAP_INV', 'group': 'Inventory', 'type': 'current_asset'},
                {'name': 'Cash Account', 'code': 'CASH', 'group': 'Cash & Bank', 'type': 'current_asset', 'is_cash': True},
                
                # Liabilities
                {'name': 'CGST Payable', 'code': 'CGST_PAY', 'group': 'Duties & Taxes', 'type': 'current_liability'},
                {'name': 'SGST Payable', 'code': 'SGST_PAY', 'group': 'Duties & Taxes', 'type': 'current_liability'},
                {'name': 'IGST Payable', 'code': 'IGST_PAY', 'group': 'Duties & Taxes', 'type': 'current_liability'},
                
                # Income
                {'name': 'Sales Revenue', 'code': 'SALES', 'group': 'Sales & Income', 'type': 'revenue'},
                {'name': 'Job Work Income', 'code': 'JW_INCOME', 'group': 'Sales & Income', 'type': 'revenue'},
                {'name': 'Scrap Sales', 'code': 'SCRAP_SALES', 'group': 'Sales & Income', 'type': 'revenue'},
                
                # Expenses
                {'name': 'Cost of Goods Sold', 'code': 'COGS', 'group': 'Direct Expenses', 'type': 'cost_of_goods_sold'},
                {'name': 'Purchase Expenses', 'code': 'PURCHASE', 'group': 'Direct Expenses', 'type': 'expense'},
                {'name': 'Job Work Charges', 'code': 'JW_CHARGES', 'group': 'Direct Expenses', 'type': 'expense'},
                {'name': 'Wages & Salaries', 'code': 'WAGES', 'group': 'Direct Expenses', 'type': 'expense'},
                {'name': 'Factory Overhead', 'code': 'OVERHEAD', 'group': 'Indirect Expenses', 'type': 'expense'},
                {'name': 'Transportation', 'code': 'TRANSPORT', 'group': 'Indirect Expenses', 'type': 'expense'},
            ]
            
            for account_data in default_accounts:
                existing_account = Account.query.filter_by(code=account_data['code']).first()
                if not existing_account:
                    group = AccountGroup.query.filter_by(name=account_data['group']).first()
                    if group:
                        account = Account(
                            name=account_data['name'],
                            code=account_data['code'],
                            account_group_id=group.id,
                            account_type=account_data['type'],
                            is_cash_account=account_data.get('is_cash', False),
                            is_bank_account=account_data.get('is_bank', False)
                        )
                        db.session.add(account)
            
            # Create default voucher types
            default_voucher_types = [
                {'name': 'Purchase Voucher', 'code': 'PUR'},
                {'name': 'Sales Voucher', 'code': 'SAL'},
                {'name': 'Payment Voucher', 'code': 'PAY'},
                {'name': 'Receipt Voucher', 'code': 'REC'},
                {'name': 'Journal Voucher', 'code': 'JOU'},
                {'name': 'Contra Voucher', 'code': 'CON'},
            ]
            
            for vt_data in default_voucher_types:
                existing_vt = VoucherType.query.filter_by(code=vt_data['code']).first()
                if not existing_vt:
                    vt = VoucherType(**vt_data)
                    db.session.add(vt)
            
            db.session.commit()
            return True
            
        except Exception as e:
            db.session.rollback()
            print(f"Error setting up default accounts: {str(e)}")
            return False
    
    @staticmethod
    def create_purchase_voucher(purchase_order):
        """Create journal entries for purchase order"""
        try:
            # Get purchase voucher type
            voucher_type = VoucherType.query.filter_by(code='PUR').first()
            if not voucher_type:
                return False
            
            # Create voucher
            voucher = Voucher(
                voucher_number=Voucher.generate_voucher_number('PUR'),
                voucher_type_id=voucher_type.id,
                transaction_date=purchase_order.order_date or date.today(),
                reference_number=purchase_order.po_number,
                narration=f"Purchase from {purchase_order.supplier.name}",
                party_id=purchase_order.supplier_id,
                party_type='supplier',
                total_amount=purchase_order.total_amount,
                tax_amount=purchase_order.tax_amount or 0,
                is_gst_applicable=True,
                created_by=purchase_order.created_by
            )
            
            db.session.add(voucher)
            db.session.flush()
            
            # Get accounts
            inventory_account = Account.query.filter_by(code='RM_INV').first()
            gst_account = Account.query.filter_by(code='CGST_PAY').first()
            supplier_account = AccountingAutomation.get_or_create_party_account(purchase_order.supplier)
            
            if not all([inventory_account, supplier_account]):
                return False
            
            # Debit inventory (raw materials)
            inventory_entry = JournalEntry(
                voucher_id=voucher.id,
                account_id=inventory_account.id,
                entry_type='debit',
                amount=purchase_order.subtotal,
                narration=f"Purchase of raw materials - {purchase_order.po_number}",
                transaction_date=voucher.transaction_date,
                reference_type='purchase_order',
                reference_id=purchase_order.id
            )
            db.session.add(inventory_entry)
            
            # Debit GST if applicable
            if purchase_order.tax_amount and purchase_order.tax_amount > 0 and gst_account:
                gst_entry = JournalEntry(
                    voucher_id=voucher.id,
                    account_id=gst_account.id,
                    entry_type='debit',
                    amount=purchase_order.tax_amount,
                    narration=f"GST on purchases - {purchase_order.po_number}",
                    transaction_date=voucher.transaction_date,
                    reference_type='purchase_order',
                    reference_id=purchase_order.id
                )
                db.session.add(gst_entry)
            
            # Credit supplier account
            supplier_entry = JournalEntry(
                voucher_id=voucher.id,
                account_id=supplier_account.id,
                entry_type='credit',
                amount=purchase_order.total_amount,
                narration=f"Purchase from {purchase_order.supplier.name}",
                transaction_date=voucher.transaction_date,
                reference_type='purchase_order',
                reference_id=purchase_order.id
            )
            db.session.add(supplier_entry)
            
            db.session.commit()
            return voucher
            
        except Exception as e:
            db.session.rollback()
            print(f"Error creating purchase voucher: {str(e)}")
            return False
    
    @staticmethod
    def create_sales_voucher(sales_order):
        """Create journal entries for sales order"""
        try:
            # Get sales voucher type
            voucher_type = VoucherType.query.filter_by(code='SAL').first()
            if not voucher_type:
                return False
            
            # Create voucher
            voucher = Voucher(
                voucher_number=Voucher.generate_voucher_number('SAL'),
                voucher_type_id=voucher_type.id,
                transaction_date=sales_order.order_date or date.today(),
                reference_number=sales_order.so_number,
                narration=f"Sales to {sales_order.customer.name}",
                party_id=sales_order.customer_id,
                party_type='customer',
                total_amount=sales_order.total_amount,
                tax_amount=sales_order.tax_amount or 0,
                is_gst_applicable=True,
                created_by=sales_order.created_by
            )
            
            db.session.add(voucher)
            db.session.flush()
            
            # Get accounts
            sales_account = Account.query.filter_by(code='SALES').first()
            gst_account = Account.query.filter_by(code='CGST_PAY').first()
            customer_account = AccountingAutomation.get_or_create_party_account(sales_order.customer)
            
            if not all([sales_account, customer_account]):
                return False
            
            # Debit customer account
            customer_entry = JournalEntry(
                voucher_id=voucher.id,
                account_id=customer_account.id,
                entry_type='debit',
                amount=sales_order.total_amount,
                narration=f"Sales to {sales_order.customer.name}",
                transaction_date=voucher.transaction_date,
                reference_type='sales_order',
                reference_id=sales_order.id
            )
            db.session.add(customer_entry)
            
            # Credit sales account
            sales_entry = JournalEntry(
                voucher_id=voucher.id,
                account_id=sales_account.id,
                entry_type='credit',
                amount=sales_order.subtotal,
                narration=f"Sales revenue - {sales_order.so_number}",
                transaction_date=voucher.transaction_date,
                reference_type='sales_order',
                reference_id=sales_order.id
            )
            db.session.add(sales_entry)
            
            # Credit GST if applicable
            if sales_order.tax_amount and sales_order.tax_amount > 0 and gst_account:
                gst_entry = JournalEntry(
                    voucher_id=voucher.id,
                    account_id=gst_account.id,
                    entry_type='credit',
                    amount=sales_order.tax_amount,
                    narration=f"GST on sales - {sales_order.so_number}",
                    transaction_date=voucher.transaction_date,
                    reference_type='sales_order',
                    reference_id=sales_order.id
                )
                db.session.add(gst_entry)
            
            db.session.commit()
            return voucher
            
        except Exception as e:
            db.session.rollback()
            print(f"Error creating sales voucher: {str(e)}")
            return False
    
    @staticmethod
    def create_grn_voucher(grn):
        """Create journal entries for GRN (Job Work)"""
        try:
            # Get purchase voucher type
            voucher_type = VoucherType.query.filter_by(code='PUR').first()
            if not voucher_type:
                return False
            
            # Create voucher
            voucher = Voucher(
                voucher_number=Voucher.generate_voucher_number('GRN'),
                voucher_type_id=voucher_type.id,
                transaction_date=grn.receipt_date or date.today(),
                reference_number=grn.grn_number,
                narration=f"GRN from {grn.supplier.name}",
                party_id=grn.supplier_id,
                party_type='supplier',
                total_amount=grn.total_amount,
                created_by=grn.created_by
            )
            
            db.session.add(voucher)
            db.session.flush()
            
            # Get accounts
            if grn.grn_type == 'job_work':
                inventory_account = Account.query.filter_by(code='FG_INV').first()  # Finished goods
                expense_account = Account.query.filter_by(code='JW_CHARGES').first()  # Job work charges
            else:
                inventory_account = Account.query.filter_by(code='RM_INV').first()  # Raw materials
                expense_account = None
            
            supplier_account = AccountingAutomation.get_or_create_party_account(grn.supplier)
            
            if not all([inventory_account, supplier_account]):
                return False
            
            # Process each GRN line item
            for line_item in grn.line_items:
                # Debit inventory for received goods
                inventory_entry = JournalEntry(
                    voucher_id=voucher.id,
                    account_id=inventory_account.id,
                    entry_type='debit',
                    amount=line_item.total_amount,
                    narration=f"Received {line_item.item.name} - {grn.grn_number}",
                    transaction_date=voucher.transaction_date,
                    reference_type='grn',
                    reference_id=grn.id
                )
                db.session.add(inventory_entry)
                
                # If job work, also debit job work charges
                if grn.grn_type == 'job_work' and expense_account and line_item.job_work_rate:
                    jw_amount = line_item.quantity_received * (line_item.job_work_rate or 0)
                    if jw_amount > 0:
                        jw_entry = JournalEntry(
                            voucher_id=voucher.id,
                            account_id=expense_account.id,
                            entry_type='debit',
                            amount=jw_amount,
                            narration=f"Job work charges for {line_item.item.name}",
                            transaction_date=voucher.transaction_date,
                            reference_type='grn',
                            reference_id=grn.id
                        )
                        db.session.add(jw_entry)
            
            # Credit supplier account
            supplier_entry = JournalEntry(
                voucher_id=voucher.id,
                account_id=supplier_account.id,
                entry_type='credit',
                amount=grn.total_amount,
                narration=f"GRN from {grn.supplier.name}",
                transaction_date=voucher.transaction_date,
                reference_type='grn',
                reference_id=grn.id
            )
            db.session.add(supplier_entry)
            
            db.session.commit()
            return voucher
            
        except Exception as e:
            db.session.rollback()
            print(f"Error creating GRN voucher: {str(e)}")
            return False
    
    @staticmethod
    def create_expense_voucher(factory_expense):
        """Create journal entries for factory expenses"""
        try:
            # Get journal voucher type
            voucher_type = VoucherType.query.filter_by(code='JOU').first()
            if not voucher_type:
                return False
            
            # Create voucher
            voucher = Voucher(
                voucher_number=Voucher.generate_voucher_number('EXP'),
                voucher_type_id=voucher_type.id,
                transaction_date=factory_expense.expense_date or date.today(),
                reference_number=factory_expense.expense_number,
                narration=factory_expense.description,
                total_amount=factory_expense.total_amount,
                created_by=factory_expense.requested_by
            )
            
            db.session.add(voucher)
            db.session.flush()
            
            # Get appropriate expense account based on category
            expense_account_code = {
                'utilities': 'OVERHEAD',
                'maintenance': 'OVERHEAD',
                'salary': 'WAGES',
                'materials': 'PURCHASE',
                'overhead': 'OVERHEAD',
                'transport': 'TRANSPORT',
                'others': 'OVERHEAD'
            }.get(factory_expense.category, 'OVERHEAD')
            
            expense_account = Account.query.filter_by(code=expense_account_code).first()
            cash_account = Account.query.filter_by(is_cash_account=True).first()
            
            if not all([expense_account, cash_account]):
                return False
            
            # Debit expense account
            expense_entry = JournalEntry(
                voucher_id=voucher.id,
                account_id=expense_account.id,
                entry_type='debit',
                amount=factory_expense.total_amount,
                narration=factory_expense.description,
                transaction_date=voucher.transaction_date,
                reference_type='factory_expense',
                reference_id=factory_expense.id
            )
            db.session.add(expense_entry)
            
            # Credit cash/bank account based on payment mode
            if factory_expense.payment_mode == 'cash':
                credit_account = cash_account
            else:
                # For now, use cash account; in future, implement bank account selection
                credit_account = cash_account
            
            cash_entry = JournalEntry(
                voucher_id=voucher.id,
                account_id=credit_account.id,
                entry_type='credit',
                amount=factory_expense.total_amount,
                narration=f"Expense payment - {factory_expense.payment_mode}",
                transaction_date=voucher.transaction_date,
                reference_type='factory_expense',
                reference_id=factory_expense.id
            )
            db.session.add(cash_entry)
            
            db.session.commit()
            return voucher
            
        except Exception as e:
            db.session.rollback()
            print(f"Error creating expense voucher: {str(e)}")
            return False
    
    @staticmethod
    def create_salary_voucher(salary_record):
        """Create journal entries for salary payments"""
        try:
            # Get payment voucher type
            voucher_type = VoucherType.query.filter_by(code='PAY').first()
            if not voucher_type:
                return False
            
            # Create voucher
            voucher = Voucher(
                voucher_number=Voucher.generate_voucher_number('SAL'),
                voucher_type_id=voucher_type.id,
                transaction_date=salary_record.payment_date or date.today(),
                reference_number=salary_record.salary_number,
                narration=f"Salary payment to {salary_record.employee.name}",
                total_amount=salary_record.net_salary,
                created_by=1  # System user
            )
            
            db.session.add(voucher)
            db.session.flush()
            
            # Get accounts
            wages_account = Account.query.filter_by(code='WAGES').first()
            cash_account = Account.query.filter_by(is_cash_account=True).first()
            
            if not all([wages_account, cash_account]):
                return False
            
            # Debit wages account
            wages_entry = JournalEntry(
                voucher_id=voucher.id,
                account_id=wages_account.id,
                entry_type='debit',
                amount=salary_record.net_salary,
                narration=f"Salary to {salary_record.employee.name} for {salary_record.pay_period_start} to {salary_record.pay_period_end}",
                transaction_date=voucher.transaction_date,
                reference_type='salary_record',
                reference_id=salary_record.id
            )
            db.session.add(wages_entry)
            
            # Credit cash account
            cash_entry = JournalEntry(
                voucher_id=voucher.id,
                account_id=cash_account.id,
                entry_type='credit',
                amount=salary_record.net_salary,
                narration=f"Salary payment to {salary_record.employee.name}",
                transaction_date=voucher.transaction_date,
                reference_type='salary_record',
                reference_id=salary_record.id
            )
            db.session.add(cash_entry)
            
            db.session.commit()
            return voucher
            
        except Exception as e:
            db.session.rollback()
            print(f"Error creating salary voucher: {str(e)}")
            return False
    
    @staticmethod
    def get_or_create_party_account(party):
        """Get or create account for supplier/customer"""
        try:
            # Try to find existing account
            account = Account.query.filter_by(name=party.name).first()
            
            if not account:
                # Determine account group based on party type
                if party.is_supplier:
                    group = AccountGroup.query.filter_by(name='Sundry Creditors').first()
                    account_type = 'current_liability'
                    code_prefix = 'SUP'
                else:
                    group = AccountGroup.query.filter_by(name='Sundry Debtors').first()
                    account_type = 'current_asset'
                    code_prefix = 'CUS'
                
                if group:
                    account = Account(
                        name=party.name,
                        code=f"{code_prefix}_{party.id}",
                        account_group_id=group.id,
                        account_type=account_type
                    )
                    db.session.add(account)
                    db.session.flush()
            
            return account
            
        except Exception as e:
            print(f"Error creating party account: {str(e)}")
            return None
    
    @staticmethod
    def create_cogs_entry(production):
        """Create Cost of Goods Sold entry for production"""
        try:
            # Get journal voucher type
            voucher_type = VoucherType.query.filter_by(code='JOU').first()
            if not voucher_type:
                return False
            
            # Create voucher
            voucher = Voucher(
                voucher_number=Voucher.generate_voucher_number('PROD'),
                voucher_type_id=voucher_type.id,
                transaction_date=production.production_date or date.today(),
                reference_number=production.production_number,
                narration=f"Production of {production.item.name}",
                total_amount=production.total_cost or 0,
                created_by=production.created_by
            )
            
            db.session.add(voucher)
            db.session.flush()
            
            # Get accounts
            wip_account = Account.query.filter_by(code='WIP_INV').first()
            fg_account = Account.query.filter_by(code='FG_INV').first()
            rm_account = Account.query.filter_by(code='RM_INV').first()
            
            if not all([wip_account, fg_account, rm_account]):
                return False
            
            # Transfer from Raw Materials to WIP
            if production.bom and production.bom.items:
                total_material_cost = sum(
                    (bom_item.qty_required or 0) * (bom_item.unit_cost or 0) 
                    for bom_item in production.bom.items
                )
                
                if total_material_cost > 0:
                    # Debit WIP
                    wip_entry = JournalEntry(
                        voucher_id=voucher.id,
                        account_id=wip_account.id,
                        entry_type='debit',
                        amount=total_material_cost,
                        narration=f"Material consumption for {production.item.name}",
                        transaction_date=voucher.transaction_date,
                        reference_type='production',
                        reference_id=production.id
                    )
                    db.session.add(wip_entry)
                    
                    # Credit Raw Materials
                    rm_entry = JournalEntry(
                        voucher_id=voucher.id,
                        account_id=rm_account.id,
                        entry_type='credit',
                        amount=total_material_cost,
                        narration=f"Material issued for production",
                        transaction_date=voucher.transaction_date,
                        reference_type='production',
                        reference_id=production.id
                    )
                    db.session.add(rm_entry)
            
            # Transfer from WIP to Finished Goods when completed
            if production.status == 'completed' and production.total_cost:
                # Debit Finished Goods
                fg_entry = JournalEntry(
                    voucher_id=voucher.id,
                    account_id=fg_account.id,
                    entry_type='debit',
                    amount=production.total_cost,
                    narration=f"Completed production of {production.item.name}",
                    transaction_date=voucher.transaction_date,
                    reference_type='production',
                    reference_id=production.id
                )
                db.session.add(fg_entry)
                
                # Credit WIP
                wip_completion_entry = JournalEntry(
                    voucher_id=voucher.id,
                    account_id=wip_account.id,
                    entry_type='credit',
                    amount=production.total_cost,
                    narration=f"Production completion transfer",
                    transaction_date=voucher.transaction_date,
                    reference_type='production',
                    reference_id=production.id
                )
                db.session.add(wip_completion_entry)
            
            db.session.commit()
            return voucher
            
        except Exception as e:
            db.session.rollback()
            print(f"Error creating production voucher: {str(e)}")
            return False