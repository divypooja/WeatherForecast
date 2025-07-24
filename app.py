import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix

# Configure logging
logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    
    # Configuration
    app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///factory.db")
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_recycle": 300,
        "pool_pre_ping": True,
    }
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    
    # Middleware
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
    
    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    
    # Import models
    from models import User, Item, Supplier, PurchaseOrder, SalesOrder, Employee, JobWork, Production, BOM, NotificationSettings, NotificationLog, NotificationRecipient, CompanySettings, QualityIssue, QualityControlLog, FactoryExpense, Document
    from models_uom import UnitOfMeasure, UOMConversion, ItemUOMConversion, UOMConversionLog
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Register blueprints
    from routes.main import main_bp
    from routes.auth import auth_bp
    from routes.inventory import inventory_bp
    from routes.purchase import purchase_bp
    from routes.sales import sales_bp
    from routes.jobwork import jobwork_bp
    from routes.production import production_bp
    from routes.hr import hr_bp
    from routes.reports import reports_bp
    from routes.settings import settings_bp
    from routes.admin import admin_bp
    from routes.quality import quality_bp
    from routes.material_inspection import material_inspection
    from routes.expenses import expenses_bp
    from routes.documents import documents_bp
    from routes.uom import uom_bp
    from routes.tally import tally_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(inventory_bp, url_prefix='/inventory')
    app.register_blueprint(purchase_bp, url_prefix='/purchase')
    app.register_blueprint(sales_bp, url_prefix='/sales')
    app.register_blueprint(jobwork_bp, url_prefix='/jobwork')
    app.register_blueprint(production_bp, url_prefix='/production')
    app.register_blueprint(hr_bp, url_prefix='/hr')
    app.register_blueprint(reports_bp, url_prefix='/reports')
    app.register_blueprint(settings_bp, url_prefix='/settings')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(quality_bp, url_prefix='/quality')
    app.register_blueprint(material_inspection, url_prefix='/inspection')
    app.register_blueprint(expenses_bp, url_prefix='/expenses')
    app.register_blueprint(documents_bp, url_prefix='/documents')
    app.register_blueprint(uom_bp, url_prefix='/uom')
    app.register_blueprint(tally_bp, url_prefix='/tally')
    from routes.backup import backup_bp
    app.register_blueprint(backup_bp, url_prefix='/backup')
    
    # Register placeholder routes for new dashboard modules
    from routes.module_placeholders import register_placeholder_routes
    register_placeholder_routes(app)
    
    # Template context processors
    @app.context_processor
    def utility_processor():
        from utils_documents import get_file_icon, format_file_size
        return dict(get_file_icon=get_file_icon, format_file_size=format_file_size)
    
    # Create database tables
    with app.app_context():
        # Import all models to ensure tables are created
        import models  # Main models (already imported)
        import models_dashboard  # Dashboard preference models
        
        db.create_all()
        
        # Initialize default dashboard modules
        from models_dashboard import init_default_modules
        init_default_modules()
    
    # Register CLI commands
    from cli import init_db_command, create_admin_command
    app.cli.add_command(init_db_command)
    app.cli.add_command(create_admin_command)
    
    # Start notification scheduler in production
    if not app.debug:
        from services.scheduler import notification_scheduler
        notification_scheduler.start()
    
    return app

app = create_app()
