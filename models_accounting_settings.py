from app import db
from datetime import datetime
from sqlalchemy import text

class AdvancedAccountingSettings(db.Model):
    """Advanced accounting configuration settings"""
    __tablename__ = 'advanced_accounting_settings'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Auto voucher settings
    auto_jv_posting = db.Column(db.Boolean, default=True)
    auto_grn_voucher = db.Column(db.Boolean, default=True)
    auto_sales_voucher = db.Column(db.Boolean, default=True)
    auto_production_voucher = db.Column(db.Boolean, default=True)
    auto_expense_voucher = db.Column(db.Boolean, default=True)
    auto_salary_voucher = db.Column(db.Boolean, default=True)
    
    # Rounding rules
    amount_rounding_places = db.Column(db.Integer, default=2)
    rounding_method = db.Column(db.String(20), default='normal')  # normal, up, down
    
    # Inventory valuation
    inventory_valuation_method = db.Column(db.String(20), default='moving_average')  # fifo, lifo, moving_average, standard_cost
    
    # Default accounts
    default_cash_account_id = db.Column(db.Integer, db.ForeignKey('accounts.id'))
    default_bank_account_id = db.Column(db.Integer, db.ForeignKey('accounts.id'))
    default_purchase_account_id = db.Column(db.Integer, db.ForeignKey('accounts.id'))
    default_sales_account_id = db.Column(db.Integer, db.ForeignKey('accounts.id'))
    default_inventory_account_id = db.Column(db.Integer, db.ForeignKey('accounts.id'))
    default_cogs_account_id = db.Column(db.Integer, db.ForeignKey('accounts.id'))
    
    # GST settings
    gst_number = db.Column(db.String(50))
    place_of_business = db.Column(db.String(100))
    default_gst_rate = db.Column(db.Numeric(5, 2), default=18.0)
    
    # Payment modes
    enable_upi_payments = db.Column(db.Boolean, default=True)
    enable_credit_payments = db.Column(db.Boolean, default=True)
    default_credit_days = db.Column(db.Integer, default=30)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    default_cash_account = db.relationship('Account', foreign_keys=[default_cash_account_id])
    default_bank_account = db.relationship('Account', foreign_keys=[default_bank_account_id])
    default_purchase_account = db.relationship('Account', foreign_keys=[default_purchase_account_id])
    default_sales_account = db.relationship('Account', foreign_keys=[default_sales_account_id])
    default_inventory_account = db.relationship('Account', foreign_keys=[default_inventory_account_id])
    default_cogs_account = db.relationship('Account', foreign_keys=[default_cogs_account_id])
    
    @classmethod
    def get_settings(cls):
        """Get or create advanced accounting settings"""
        settings = cls.query.first()
        if not settings:
            settings = cls()
            db.session.add(settings)
            db.session.commit()
        return settings

class CostCenter(db.Model):
    """Cost centers for department-wise expense tracking"""
    __tablename__ = 'cost_centers'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(20), nullable=False, unique=True)
    description = db.Column(db.Text)
    
    # Hierarchy
    parent_center_id = db.Column(db.Integer, db.ForeignKey('cost_centers.id'))
    
    # Budgeting
    monthly_budget = db.Column(db.Numeric(15, 2), default=0.0)
    yearly_budget = db.Column(db.Numeric(15, 2), default=0.0)
    
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    parent_center = db.relationship('CostCenter', remote_side=[id], backref='sub_centers')
    
    def __repr__(self):
        return f'<CostCenter {self.name}>'

class LedgerMapping(db.Model):
    """Automatic ledger mapping for different categories"""
    __tablename__ = 'ledger_mappings'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Mapping rules
    entity_type = db.Column(db.String(50), nullable=False)  # supplier, customer, item_category, department
    entity_id = db.Column(db.Integer)  # Reference to the entity
    entity_name = db.Column(db.String(200))  # For generic mappings
    
    # Account mappings
    receivable_account_id = db.Column(db.Integer, db.ForeignKey('accounts.id'))
    payable_account_id = db.Column(db.Integer, db.ForeignKey('accounts.id'))
    expense_account_id = db.Column(db.Integer, db.ForeignKey('accounts.id'))
    income_account_id = db.Column(db.Integer, db.ForeignKey('accounts.id'))
    
    # Cost center
    cost_center_id = db.Column(db.Integer, db.ForeignKey('cost_centers.id'))
    
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    receivable_account = db.relationship('Account', foreign_keys=[receivable_account_id])
    payable_account = db.relationship('Account', foreign_keys=[payable_account_id])
    expense_account = db.relationship('Account', foreign_keys=[expense_account_id])
    income_account = db.relationship('Account', foreign_keys=[income_account_id])
    cost_center = db.relationship('CostCenter')

class PaymentMethod(db.Model):
    """Payment methods configuration"""
    __tablename__ = 'payment_methods'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(20), nullable=False, unique=True)
    method_type = db.Column(db.String(20), nullable=False)  # cash, bank, upi, credit_card, cheque
    
    # Account mapping
    account_id = db.Column(db.Integer, db.ForeignKey('accounts.id'), nullable=False)
    
    # Configuration
    requires_reference = db.Column(db.Boolean, default=False)  # For cheque numbers, UPI IDs
    auto_reconcile = db.Column(db.Boolean, default=False)
    processing_fee_rate = db.Column(db.Numeric(5, 2), default=0.0)
    
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    account = db.relationship('Account')
    
    def __repr__(self):
        return f'<PaymentMethod {self.name}>'

class InventoryValuation(db.Model):
    """Inventory valuation tracking for different methods"""
    __tablename__ = 'inventory_valuations'
    
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('items.id'), nullable=False)
    batch_id = db.Column(db.Integer, db.ForeignKey('item_batches.id'))
    
    # Valuation data
    valuation_date = db.Column(db.Date, nullable=False)
    quantity = db.Column(db.Numeric(15, 3), nullable=False)
    
    # Different valuation methods
    fifo_rate = db.Column(db.Numeric(15, 2))
    lifo_rate = db.Column(db.Numeric(15, 2))
    moving_avg_rate = db.Column(db.Numeric(15, 2))
    standard_cost_rate = db.Column(db.Numeric(15, 2))
    
    # Current method value
    current_rate = db.Column(db.Numeric(15, 2), nullable=False)
    total_value = db.Column(db.Numeric(15, 2), nullable=False)
    
    # Transaction reference
    transaction_type = db.Column(db.String(50))  # grn, production, sales, adjustment
    transaction_id = db.Column(db.Integer)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    item = db.relationship('Item')
    batch = db.relationship('ItemBatch')
    
    @classmethod
    def calculate_moving_average(cls, item_id, new_quantity, new_rate):
        """Calculate moving average rate for an item"""
        latest = cls.query.filter_by(item_id=item_id).order_by(cls.created_at.desc()).first()
        
        if not latest or latest.quantity == 0:
            return new_rate
        
        current_value = latest.quantity * latest.moving_avg_rate
        new_value = new_quantity * new_rate
        total_quantity = latest.quantity + new_quantity
        
        if total_quantity == 0:
            return new_rate
        
        return (current_value + new_value) / total_quantity
    
    def __repr__(self):
        return f'<InventoryValuation {self.item.name if self.item else "N/A"} - {self.quantity}>'