from app import app

# Import and register Tally integration blueprint
from routes.tally import tally_bp
app.register_blueprint(tally_bp)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
