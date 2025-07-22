# Local Development Setup Guide

## Quick Start (Recommended)

### Option 1: Automatic Setup Script
```bash
# Download all files to your local machine
# Open terminal in the project directory
python run_local.py
```

### Option 2: Manual Setup

#### Step 1: Install Python Dependencies
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -e .
```

#### Step 2: Configure Environment
```bash
# Copy environment template
cp .env.example .env

# Edit .env file with your preferences:
DATABASE_URL=sqlite:///factory.db
SESSION_SECRET=your-secret-key-here
FLASK_ENV=development
FLASK_DEBUG=1
```

#### Step 3: Initialize Database
```bash
# Create database tables and admin user
python cli.py create-admin
```

#### Step 4: Run Application
```bash
# Start the server
python main.py

# Or with Gunicorn (production-like)
gunicorn --bind 127.0.0.1:5000 --reload main:app
```

#### Step 5: Access Application
Open your browser to: `http://localhost:5000`

## Database Options

### SQLite (Easiest for Development)
```env
DATABASE_URL=sqlite:///factory.db
```
- No additional setup required
- Database file created automatically
- Perfect for development and testing

### PostgreSQL (Production-ready)
```env
DATABASE_URL=postgresql://username:password@localhost:5432/factory_db
```
- Install PostgreSQL separately
- Create database: `createdb factory_db`
- Better for production use

## VS Code Integration

If using VS Code:
1. Open project folder in VS Code
2. Install Python extension
3. Press F5 to debug
4. Use Ctrl+Shift+P → "Tasks: Run Task" for quick actions

## Troubleshooting

### Common Issues:

**Port 5000 already in use:**
```bash
# Kill process using port 5000
# Windows:
netstat -ano | findstr :5000
taskkill /PID <PID> /F

# Mac/Linux:
lsof -ti:5000 | xargs kill -9
```

**Database connection error:**
- Check DATABASE_URL in .env file
- For SQLite: ensure directory is writable
- For PostgreSQL: ensure service is running

**Missing dependencies:**
```bash
pip install --upgrade pip
pip install -e .
```

**Permission denied (Unix/Mac):**
```bash
chmod +x run_local.py
python run_local.py
```

## File Structure Overview
```
factory-management-system/
├── main.py              # Entry point
├── app.py               # Flask app factory
├── models.py            # Database models
├── forms.py             # Form definitions
├── cli.py               # CLI commands
├── run_local.py         # Local development runner
├── .env.example         # Environment template
├── routes/              # Application routes
├── templates/           # HTML templates
├── static/              # CSS, JS, images
└── .vscode/             # VS Code configuration
```

## Default Login
After running `python cli.py create-admin`, you'll be prompted to create admin credentials.

Default development credentials (if using run_local.py defaults):
- Visit: http://localhost:5000
- Follow prompts to create admin user

## Features Available
- ✅ Inventory Management
- ✅ Purchase Orders
- ✅ Sales Orders
- ✅ Job Work Tracking
- ✅ Production Management
- ✅ HR & Employee Management
- ✅ Comprehensive Reporting
- ✅ CSV Data Export
- ✅ Role-based Access Control

## Development Tips
- Use `python run_local.py` for automatic setup
- Database changes require restart
- Static files auto-reload in debug mode
- Check browser console for JavaScript errors

## Next Steps
1. Create inventory items
2. Add suppliers and customers
3. Generate purchase orders
4. Explore reporting features