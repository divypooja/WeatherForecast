# Windows Setup Guide - Factory Management System

## Quick Fix for Your Current Issue

You're getting errors because:
1. You're in the wrong folder (WeatherForecast instead of factory management system)
2. Dependencies aren't installed yet
3. Missing the project files

## Step-by-Step Solution:

### 1. Download Project Files
Make sure you have ALL these files in one folder:
```
factory-management-system/
├── main.py
├── app.py
├── models.py
├── forms.py
├── cli.py
├── config.py
├── pyproject.toml
├── .env.example
├── setup_windows.bat  (NEW - I just created this)
├── routes/ (folder)
├── templates/ (folder)
├── static/ (folder)
└── other files...
```

### 2. Open Command Prompt in Correct Folder
- Navigate to the folder containing `main.py` and all the factory management files
- **NOT** the WeatherForecast folder

### 3. Run the Windows Setup Script
```cmd
setup_windows.bat
```

This will automatically:
- Create virtual environment
- Install all dependencies one by one
- Create .env file with SQLite database
- Initialize database tables
- Prompt you to create admin user
- Start the application

### 4. Alternative Manual Method (if script fails):

```cmd
REM Create and activate virtual environment
python -m venv venv
venv\Scripts\activate.bat

REM Install dependencies individually
pip install Flask>=3.1.1
pip install Flask-SQLAlchemy>=3.1.1
pip install Flask-Login>=0.6.3
pip install Flask-WTF>=1.2.2
pip install SQLAlchemy>=2.0.41
pip install WTForms>=3.2.1
pip install email-validator>=2.2.0
pip install Werkzeug>=3.1.3
pip install Click>=8.2.1
pip install gunicorn>=23.0.0

REM Create environment file
echo DATABASE_URL=sqlite:///factory.db > .env
echo SESSION_SECRET=dev-secret-key >> .env
echo FLASK_ENV=development >> .env
echo FLASK_DEBUG=1 >> .env

REM Initialize database
python -c "from app import app, db; app.app_context().push(); db.create_all()"

REM Create admin user
python cli.py create-admin

REM Start application
python main.py
```

## Common Windows Issues:

### "source command not found"
- Windows uses `venv\Scripts\activate.bat` instead of `source venv/bin/activate`

### "pip install -e" requires argument
- Use `pip install -e .` (note the dot at the end)
- Or use `pip install Flask Flask-SQLAlchemy Flask-Login Flask-WTF ...`

### "Module not found" errors
- Make sure virtual environment is activated: `venv\Scripts\activate.bat`
- Install dependencies before running any Python scripts

### Python not found
- Install Python from https://python.org
- **Important**: Check "Add Python to PATH" during installation
- Restart Command Prompt after installation

## Verify Setup:
1. Virtual environment activated: `(venv)` should appear in prompt
2. Dependencies installed: `pip list` should show Flask, SQLAlchemy, etc.
3. Database created: `factory.db` file should exist
4. Admin user created: Follow prompts from `python cli.py create-admin`
5. Application running: `python main.py` should start server
6. Browser access: Open http://localhost:5000

## Next Steps After Setup:
1. Login with your admin credentials
2. Navigate through the dashboard
3. Add inventory items, suppliers, customers
4. Create purchase orders and sales orders
5. Explore production and reporting features

The application includes:
- ✅ Complete inventory management
- ✅ Purchase and sales order tracking  
- ✅ Job work management
- ✅ Production planning with BOM
- ✅ HR and employee management
- ✅ Comprehensive reporting with CSV export
- ✅ Professional Bootstrap UI