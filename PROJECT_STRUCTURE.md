# Campus Carbon Footprint Analyzer - Project Structure

## 📁 Clean Project Structure

```
36Hrs_Hackathon-main/
├── 📄 Core Application Files
│   ├── app.py                          # Main Flask application (27KB)
│   ├── .env                            # Environment variables (DB credentials)
│   ├── .gitignore                      # Git ignore rules
│   ├── pyproject.toml                  # Python project configuration
│   └── README.md                       # Project documentation
│
├── 🛠️ Utility Scripts
│   ├── add_emission_factor.py          # Adds human_daily emission factor to DB
│   ├── test_human_calculations.py      # Comprehensive calculation tests
│   └── verify_data.py                  # Quick verification script
│
├── 🗄️ database/
│   ├── schema.sql                      # Main database schema
│   ├── human_population_schema.sql     # Human emissions table schema
│   └── init_db.py                      # Database initialization script
│
├── 📊 Documents/
│   ├── activity_data_sample.csv        # Sample data for testing
│   ├── Hackathon Idea Submission.pdf   # Project submission
│   ├── Hackathon Idea Submission.pptx  # Presentation
│   └── Project Specification...pdf     # Original requirements
│
├── 🎨 static/
│   ├── css/
│   │   └── style.css                   # Application styles (13KB)
│   └── js/
│       ├── dashboard.js                # Dashboard logic (22KB)
│       └── data_input.js               # Data input form logic (7KB)
│
└── 🌐 templates/
    ├── base.html                       # Base template
    ├── login.html                      # Login page
    ├── dashboard.html                  # Dashboard view
    └── data_input.html                 # Data entry form
```

## ✅ Files Removed (Cleanup Completed)

**Test & Debug Files:**
- ❌ `check_routes.py` - Debug script
- ❌ `diagnose_issue.py` - Debug script
- ❌ `test_console.html` - Test HTML
- ❌ `test_human_api.py` - API test
- ❌ `test_human_display.html` - Display test
- ❌ `workflow.txt` - Development notes

**System Files:**
- ❌ `__pycache__/` - Python cache directory
- ❌ `attached_assets/` - Duplicate project specs

**Total Removed:** 8 files/folders

## 🎯 Essential Files for Hackathon

### Must Have:
1. ✅ `app.py` - Main application
2. ✅ `.env` - Database configuration
3. ✅ `database/` folder - All SQL schemas
4. ✅ `static/` folder - CSS and JavaScript
5. ✅ `templates/` folder - HTML pages
6. ✅ `README.md` - Documentation

### Nice to Have:
1. ✅ `verify_data.py` - Quick health check
2. ✅ `test_human_calculations.py` - Verification tests
3. ✅ `Documents/` - Project specs and samples

### Can Remove (if needed):
- `add_emission_factor.py` (one-time setup, already run)
- `pyproject.toml` (Python packaging, not required for demo)

## 📊 Project Statistics

- **Total Lines of Code:** ~2,500 lines
- **Backend (Python):** ~700 lines (app.py)
- **Frontend (HTML/JS/CSS):** ~1,800 lines
- **Database Schemas:** ~50 lines
- **Documentation:** ~6,000 characters

## 🚀 How to Run

```bash
# 1. Install dependencies
pip install flask mysql-connector-python python-dotenv pyjwt

# 2. Initialize database
python database/init_db.py

# 3. Verify setup
python verify_data.py

# 4. Run application
python app.py
```

## 📝 File Descriptions

### Core Application
- **app.py**: Flask web server with all routes, API endpoints, and business logic
- **.env**: Database credentials (keep secure!)

### Database
- **schema.sql**: Core tables (users, activity_data, emission_factors)
- **human_population_schema.sql**: Human emissions feature table
- **init_db.py**: Automated database setup

### Frontend
- **dashboard.js**: Charts, KPI updates, data visualization
- **data_input.js**: Form handling, CSV upload, validation
- **style.css**: Complete UI styling, responsive design

### Templates
- **base.html**: Common layout, navigation, header/footer
- **dashboard.html**: Main dashboard with charts and KPIs
- **data_input.html**: Data entry forms (activity + human population)
- **login.html**: Authentication page

## 🎨 Key Features

1. **Dashboard** - Real-time emissions visualization
2. **Data Input** - Manual and CSV bulk upload
3. **Human CO₂ Tracking** - Core hackathon feature
4. **Authentication** - Secure login system
5. **API Endpoints** - RESTful API for data access

## 🔒 Security Notes

- `.env` file contains database credentials
- Add to `.gitignore` before committing
- Default login: `admin` / `admin123` (change in production!)

---

**Project Status:** ✅ Production Ready  
**Last Cleaned:** November 14, 2025  
**Total Size:** ~75 KB (without documents)
