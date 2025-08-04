"""
HR to Accounting Integration Service
Integrates HR operations with existing accounting system without modifying accounting models
"""
from app import db
from models_accounting import Account, AccountGroup, Voucher, VoucherType, JournalEntry
from models import Employee, SalaryRecord, FactoryExpense, User
from datetime import datetime, date
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

class HRAccountingIntegration:
    """Service to integrate HR operations with existing accounting system"""
    
    @staticmethod
    def setup_hr_accounts():
        """Setup HR-specific accounts in the existing accounting system"""
        try:
            # Get or create expense groups
            expense_group = AccountGroup.query.filter_by(name='Direct Expenses').first()
            if not expense_group:
                expense_group = AccountGroup.query.filter_by(group_type='expenses').first()
            
            current_asset_group = AccountGroup.query.filter_by(name='Current Assets').first()
            if not current_asset_group:
                current_asset_group = AccountGroup.query.filter_by(group_type='assets').first()
            
            if not expense_group or not current_asset_group:
                logger.error("Required account groups not found")
                return False
            
            # Create HR-specific accounts if they don't exist
            hr_accounts = [
                {
                    'name': 'Salaries & Wages',
                    'code': 'SAL_WAGES',
                    'account_group_id': expense_group.id,
                    'account_type': 'expense'
                },
                {
                    'name': 'Employee Advances',
                    'code': 'EMP_ADV',
                    'account_group_id': current_asset_group.id,
                    'account_type': 'current_asset'
                },
                {
                    'name': 'Factory Overhead',
                    'code': 'FACT_OH',
                    'account_group_id': expense_group.id,
                    'account_type': 'expense'
                },
                {
                    'name': 'Employee Benefits',
                    'code': 'EMP_BEN',
                    'account_group_id': expense_group.id,
                    'account_type': 'expense'
                }
            ]
            
            for account_data in hr_accounts:
                existing_account = Account.query.filter_by(code=account_data['code']).first()
                if not existing_account:
                    account = Account(**account_data)
                    db.session.add(account)
            
            db.session.commit()
            return True
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error setting up HR accounts: {str(e)}")
            return False
    
    @staticmethod
    def create_salary_payment_entry(salary_record):
        """Create journal entry when salary is paid"""
        try:
            # Get required voucher type
            voucher_type = VoucherType.query.filter_by(code='PAY').first()
            if not voucher_type:
                # Try to get any payment type voucher
                voucher_type = VoucherType.query.filter(
                    VoucherType.name.ilike('%payment%')
                ).first()
            
            if not voucher_type:
                logger.error("Payment voucher type not found")
                return False
            
            # Get required accounts
            salary_account = Account.query.filter_by(code='SAL_WAGES').first()
            cash_account = Account.query.filter_by(is_cash_account=True).first()
            
            if not salary_account:
                salary_account = Account.query.filter(
                    Account.name.ilike('%salary%')
                ).first()
            
            if not cash_account:
                cash_account = Account.query.filter_by(code='CASH').first()
            
            if not all([salary_account, cash_account]):
                logger.error("Required accounts not found for salary entry")
                return False
            
            # Create voucher
            voucher_number = f"SAL-{salary_record.salary_number}"
            voucher = Voucher(
                voucher_number=voucher_number,
                voucher_type_id=voucher_type.id,
                transaction_date=salary_record.payment_date or date.today(),
                reference_number=salary_record.salary_number,
                narration=f"Salary payment to {salary_record.employee.name}",
                total_amount=Decimal(str(salary_record.net_amount)),
                status='posted',
                created_by=1  # System user
            )
            
            db.session.add(voucher)
            db.session.flush()
            
            # Create journal entries
            # Debit salary expense
            salary_entry = JournalEntry(
                voucher_id=voucher.id,
                account_id=salary_account.id,
                entry_type='debit',
                amount=Decimal(str(salary_record.net_amount)),
                narration=f"Salary to {salary_record.employee.name}",
                transaction_date=voucher.transaction_date
            )
            db.session.add(salary_entry)
            
            # Credit cash
            cash_entry = JournalEntry(
                voucher_id=voucher.id,
                account_id=cash_account.id,
                entry_type='credit',
                amount=Decimal(str(salary_record.net_amount)),
                narration=f"Cash paid to {salary_record.employee.name}",
                transaction_date=voucher.transaction_date
            )
            db.session.add(cash_entry)
            
            # Link voucher to salary record
            salary_record.voucher_id = voucher.id
            
            db.session.commit()
            logger.info(f"Salary payment entry created: {voucher_number}")
            return voucher
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating salary payment entry: {str(e)}")
            return False
    
    @staticmethod
    def create_factory_expense_entry(expense):
        """Create journal entry for factory expense"""
        try:
            # Get required voucher type
            voucher_type = VoucherType.query.filter_by(code='JNL').first()
            if not voucher_type:
                voucher_type = VoucherType.query.filter(
                    VoucherType.name.ilike('%journal%')
                ).first()
            
            if not voucher_type:
                logger.error("Journal voucher type not found")
                return False
            
            # Determine expense account based on category
            expense_account = None
            if expense.category in ['salary', 'wages']:
                expense_account = Account.query.filter_by(code='SAL_WAGES').first()
            elif expense.category in ['utilities', 'maintenance', 'overhead']:
                expense_account = Account.query.filter_by(code='FACT_OH').first()
            else:
                # General factory expense
                expense_account = Account.query.filter_by(code='FACT_OH').first()
            
            # Fallback to any expense account
            if not expense_account:
                expense_group = AccountGroup.query.filter_by(group_type='expenses').first()
                if expense_group:
                    expense_account = Account.query.filter_by(account_group_id=expense_group.id).first()
            
            # Get cash/bank account
            cash_account = Account.query.filter_by(is_cash_account=True).first()
            if not cash_account:
                cash_account = Account.query.filter_by(code='CASH').first()
            
            if not all([expense_account, cash_account]):
                logger.error("Required accounts not found for expense entry")
                return False
            
            # Create voucher
            voucher_number = f"EXP-{expense.expense_number}"
            voucher = Voucher(
                voucher_number=voucher_number,
                voucher_type_id=voucher_type.id,
                transaction_date=expense.expense_date,
                reference_number=expense.expense_number,
                narration=expense.description,
                total_amount=Decimal(str(expense.total_amount)),
                status='posted',
                created_by=expense.requested_by_id
            )
            
            db.session.add(voucher)
            db.session.flush()
            
            # Create journal entries
            # Debit expense
            expense_entry = JournalEntry(
                voucher_id=voucher.id,
                account_id=expense_account.id,
                entry_type='debit',
                amount=Decimal(str(expense.total_amount)),
                narration=f"{expense.category} - {expense.description}",
                transaction_date=voucher.transaction_date
            )
            db.session.add(expense_entry)
            
            # Credit cash
            cash_entry = JournalEntry(
                voucher_id=voucher.id,
                account_id=cash_account.id,
                entry_type='credit',
                amount=Decimal(str(expense.total_amount)),
                narration=f"Payment for {expense.description}",
                transaction_date=voucher.transaction_date
            )
            db.session.add(cash_entry)
            
            # Link voucher to expense
            expense.voucher_id = voucher.id
            
            db.session.commit()
            logger.info(f"Factory expense entry created: {voucher_number}")
            return voucher
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating factory expense entry: {str(e)}")
            return False
    
    @staticmethod
    def create_employee_advance_entry(advance):
        """Create journal entry for employee advance"""
        try:
            # Get required voucher type
            voucher_type = VoucherType.query.filter_by(code='PAY').first()
            if not voucher_type:
                voucher_type = VoucherType.query.filter(
                    VoucherType.name.ilike('%payment%')
                ).first()
            
            if not voucher_type:
                logger.error("Payment voucher type not found")
                return False
            
            # Get required accounts
            advance_account = Account.query.filter_by(code='EMP_ADV').first()
            cash_account = Account.query.filter_by(is_cash_account=True).first()
            
            if not advance_account:
                # Try to find any asset account for advances
                asset_group = AccountGroup.query.filter_by(group_type='assets').first()
                if asset_group:
                    advance_account = Account.query.filter_by(account_group_id=asset_group.id).first()
            
            if not cash_account:
                cash_account = Account.query.filter_by(code='CASH').first()
            
            if not all([advance_account, cash_account]):
                logger.error("Required accounts not found for advance entry")
                return False
            
            # Create voucher
            voucher_number = f"ADV-{advance.advance_number}"
            voucher = Voucher(
                voucher_number=voucher_number,
                voucher_type_id=voucher_type.id,
                transaction_date=advance.advance_date,
                reference_number=advance.advance_number,
                narration=f"Advance to {advance.employee.name}",
                total_amount=Decimal(str(advance.amount)),
                status='posted',
                created_by=advance.requested_by_id
            )
            
            db.session.add(voucher)
            db.session.flush()
            
            # Create journal entries
            # Debit employee advance (asset)
            advance_entry = JournalEntry(
                voucher_id=voucher.id,
                account_id=advance_account.id,
                entry_type='debit',
                amount=Decimal(str(advance.amount)),
                narration=f"Advance to {advance.employee.name}",
                transaction_date=voucher.transaction_date
            )
            db.session.add(advance_entry)
            
            # Credit cash
            cash_entry = JournalEntry(
                voucher_id=voucher.id,
                account_id=cash_account.id,
                entry_type='credit',
                amount=Decimal(str(advance.amount)),
                narration=f"Cash advance to {advance.employee.name}",
                transaction_date=voucher.transaction_date
            )
            db.session.add(cash_entry)
            
            # Link voucher to advance
            advance.voucher_id = voucher.id
            
            db.session.commit()
            logger.info(f"Employee advance entry created: {voucher_number}")
            return voucher
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating employee advance entry: {str(e)}")
            return False

    @staticmethod
    def get_hr_financial_summary():
        """Get financial summary of HR-related accounts"""
        try:
            summary = {}
            
            # Get HR account balances
            hr_account_codes = ['SAL_WAGES', 'EMP_ADV', 'FACT_OH', 'EMP_BEN']
            
            for code in hr_account_codes:
                account = Account.query.filter_by(code=code).first()
                if account:
                    balance = account.calculate_balance()
                    summary[code] = {
                        'name': account.name,
                        'balance': balance,
                        'type': account.account_type
                    }
            
            return summary
            
        except Exception as e:
            logger.error(f"Error getting HR financial summary: {str(e)}")
            return {}