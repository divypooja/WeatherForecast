from app import app

# Import GRN models for database creation
try:
    import models_grn
except ImportError:
    pass

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
