# Fixed Flask app initialization for proper session management
from app import create_app, db

# Create the Flask app instance
app = create_app()

# Import all models to ensure they're registered with the app context
with app.app_context():
    import models
    import models_grn
    import models_accounting
    import models_accounting_settings
    import models_grn_workflow
    import models_notifications

    # Register additional blueprints if they exist
    try:
        from routes.accounting_settings import accounting_settings_bp
        from routes.accounting_advanced_reports import accounting_reports_bp
        from routes.grn_workflow import grn_workflow_bp
        
        app.register_blueprint(accounting_settings_bp, url_prefix='/accounting-settings')
        app.register_blueprint(accounting_reports_bp, url_prefix='/accounting-reports')
        app.register_blueprint(grn_workflow_bp, url_prefix='/grn-workflow')
    except ImportError:
        pass  # Skip if blueprints don't exist

    # Ensure all tables are created
    db.create_all()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
