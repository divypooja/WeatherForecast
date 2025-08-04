# 🚀 Quick Start Guide - Factory Management System

## Super Easy Setup (Recommended)

### Windows Users:
1. **Download** all project files to a folder (e.g., `factory-management`)
2. **Double-click** `start_windows.bat`
3. **Wait** for automatic setup to complete
4. **Open browser** to `http://localhost:5000`
5. **Login** with `admin` / `admin123`

### Linux/Mac Users:
1. **Download** all project files to a folder (e.g., `factory-management`) 
2. **Open terminal** in the project folder
3. **Run** `./start_linux_mac.sh`
4. **Wait** for automatic setup to complete
5. **Open browser** to `http://localhost:5000`
6. **Login** with `admin` / `admin123`

## Manual Setup (Advanced Users)

```bash
# 1. Create virtual environment
python -m venv venv

# 2. Activate virtual environment
# Windows: venv\Scripts\activate
# Linux/Mac: source venv/bin/activate

# 3. Install dependencies
pip install -r requirements-local.txt

# 4. Set up database and admin user
python create_admin.py

# 5. Load sample data (optional)
python create_basic_sample_data.py

# 6. Start application
python run_local.py
```

## What You Get

✅ **Complete Factory Management System**
- Inventory tracking and management
- Purchase and sales order processing
- Job work management with team assignments
- Employee management and attendance tracking
- Quality control and inspection systems
- Factory expense tracking with OCR
- Comprehensive reporting and analytics
- Document management system
- Tally integration for accounting
- Email/SMS notifications (with API setup)

✅ **Professional Dashboard Interface**
- Dark theme Bootstrap UI
- Real-time statistics and charts
- Mobile-responsive design
- Advanced filtering and search
- Export capabilities (Excel, PDF)

✅ **Sample Data Included**
- Test inventory items
- Sample employees and departments
- Example purchase and sales orders
- Demo job work assignments
- Quality control templates

## Default Login
- **Username:** `admin`
- **Password:** `admin123`

**⚠️ Important:** Change the admin password after first login!

## System Requirements
- Python 3.8 or higher
- 4GB RAM minimum
- 1GB free disk space
- Modern web browser (Chrome, Firefox, Safari, Edge)

## Troubleshooting

**Application won't start?**
- Check Python installation: `python --version`
- Ensure port 5000 is available
- Try deleting `factory.db` and run setup again

**Can't login?**
- Use default credentials: `admin` / `admin123`
- Run `python create_admin.py` to reset admin user

**Missing features?**
- Ensure all files were downloaded
- Check `requirements-local.txt` installation
- Verify database setup completed successfully

## Need Help?
- Check `LOCAL_SETUP.md` for detailed instructions
- Review console output for error messages
- Ensure all project files are in the same folder