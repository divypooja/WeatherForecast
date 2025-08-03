from app import app, db

# Import all models to ensure they're registered
import models
import models_grn
import models_accounting
import models_accounting_settings
import models_grn_workflow

# Register accounting settings blueprint
from routes.accounting_settings import accounting_settings_bp
from routes.accounting_advanced_reports import accounting_reports_bp
from routes.grn_workflow import grn_workflow_bp

app.register_blueprint(accounting_settings_bp)
app.register_blueprint(accounting_reports_bp)
app.register_blueprint(grn_workflow_bp)

# Ensure all tables are created
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
