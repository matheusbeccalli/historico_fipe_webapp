# 🔄 Project Resume Guide

This file contains all essential information to resume development of this project after a break.

## 📊 Current Project State

**Project:** historico_fipe_webapp - FIPE Historical Price Tracker
**Latest Commit:** efb1d1f - Expand future improvements section
**Branch:** main
**Status:** ✅ Complete and functional (awaiting database population)

## ⚠️ CRITICAL: Database Required

This webapp **requires a pre-populated database** with historical FIPE data. The database and data are **NOT included** in this repository.

### Database Schema Required

The database must have exactly **5 tables** matching `webapp_database_models.py`:

1. **brands** - Brand information
   - `id` (Integer, Primary Key)
   - `brand_name` (String, Unique)

2. **car_models** - Car models
   - `id` (Integer, Primary Key)
   - `model_name` (String)
   - `brand_id` (Foreign Key → brands.id)

3. **model_years** - Year/fuel variants
   - `id` (Integer, Primary Key)
   - `year_description` (String) - e.g., "2024 Flex"
   - `car_model_id` (Foreign Key → car_models.id)
   - `fipe_code` (String, Unique)

4. **reference_months** - Available months
   - `id` (Integer, Primary Key)
   - `month_date` (Date, Unique) - Format: YYYY-MM-DD

5. **car_prices** - Historical prices
   - `id` (Integer, Primary Key)
   - `price` (Float)
   - `model_year_id` (Foreign Key → model_years.id)
   - `reference_month_id` (Foreign Key → reference_months.id)
   - `fipe_code` (String)

**Documentation:** See `docs/database_schema.md` for complete ERD and details.

## 🚀 Quick Start Guide

### Step 1: Ensure Database is Ready

```bash
# Verify you have a populated fipe_data.db file
# Database should contain:
# - Vehicle brands, models, years
# - Historical FIPE prices
# - Reference months
```

### Step 2: Configure Environment

```bash
# Copy template
cp .env.example .env

# Edit .env with your configuration:
# 1. Set DATABASE_URL to your populated database path
# 2. Generate and set API keys
# 3. Configure default vehicle (optional)
```

### Step 3: Generate API Keys

```bash
# Generate API_KEY
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Generate SECRET_KEY
python generate_secret_key.py
```

### Step 4: Update .env File

```bash
# Required configuration:
DATABASE_URL=sqlite:///C:/path/to/your/fipe_data.db
API_KEY=your-generated-key-here
API_KEYS_ALLOWED=your-generated-key-here
SECRET_KEY=your-generated-secret-key

# Optional defaults:
DEFAULT_BRAND=Volkswagen
DEFAULT_MODEL=Gol
```

### Step 5: Run Application

```bash
# Activate virtual environment
# Windows:
venv\Scripts\activate

# Linux/Mac:
source venv/bin/activate

# Run the app
python app.py

# Access at: http://127.0.0.1:5000
```

## 📁 Critical Files (DO NOT DELETE)

### Backend Files
- `app.py` (813 lines) - Main Flask application with all routes
- `config.py` - Environment-based configuration system
- `webapp_database_models.py` (457 lines) - SQLAlchemy ORM models
- `generate_secret_key.py` - Secure key generator
- `requirements.txt` - Python dependencies

### Frontend Files
- `templates/index.html` - Main HTML template
- `static/js/app.js` (1136 lines) - Frontend JavaScript with API calls
- `static/css/style.css` - Custom styling

### Configuration Files
- `.env` (NOT in git) - Your actual configuration
- `.env.example` - Configuration template
- `.gitignore` - Git exclusions

### Documentation
- `README.md` - Main project documentation
- `CLAUDE.md` (350+ lines) - Technical documentation for developers/AI
- `QUICKSTART.md` - 5-minute setup guide
- `docs/database_schema.md` - Database structure reference
- `docs/ENV_SETUP.md` - Environment configuration guide
- `LICENSE` - MIT License

## ✅ What's Already Implemented

### Core Features
- ✅ Multi-vehicle comparison (up to 5 vehicles simultaneously)
- ✅ Interactive Plotly charts with zoom, pan, export
- ✅ Base 100 indexed view for relative comparison
- ✅ Economic indicators integration (IPCA and CDI from Banco Central)
- ✅ Date range selection with dynamic month filtering
- ✅ Vehicle statistics cards (current, min, max, variation)
- ✅ Cascading dropdowns (Brand → Model → Year)

### API & Security
- ✅ 9 RESTful API endpoints (see below)
- ✅ API key authentication system
- ✅ Two-variable key design (API_KEY + API_KEYS_ALLOWED)
- ✅ Comprehensive logging (successful access + failed attempts)
- ✅ Development mode fallback (works without keys configured)

### UI/UX
- ✅ Responsive design with Bootstrap 5
- ✅ Modern glassmorphism effects
- ✅ Smooth animations and transitions
- ✅ Mobile-friendly interface
- ✅ Vehicle color coding for comparison
- ✅ Dynamic chart updates without page reload

## 🔌 API Endpoints

All endpoints require `X-API-Key` header (except index page):

1. `GET /` - Main web interface (no auth required)
2. `GET /api/brands` - List all brands
3. `GET /api/models/<brand_id>` - List models for a brand
4. `GET /api/years/<model_id>` - List years for a model
5. `GET /api/months` - List available reference months
6. `POST /api/chart-data` - Get price history for single vehicle
7. `POST /api/compare-vehicles` - Get data for multiple vehicles
8. `POST /api/price` - Get single price point (FIPE lookup style)
9. `POST /api/economic-indicators` - Get IPCA/CDI for date range
10. `GET /api/default-car` - Get default vehicle selection

**Testing API:**
```bash
curl -H "X-API-Key: your-key" http://127.0.0.1:5000/api/brands
```

## 🔧 Key Technical Details

### Database Pattern
- **Read-only access** - Webapp NEVER writes to database
- Database populated by separate scraper (not included)
- Uses SQLAlchemy ORM (no raw SQL queries)
- All queries use try-finally pattern for session cleanup

### API Authentication
- **API_KEY**: App's own key (injected into frontend via `window.API_KEY`)
- **API_KEYS_ALLOWED**: Comma-separated list of valid keys (must include API_KEY)
- Frontend automatically includes key in all fetch requests
- Backend validates via `@require_api_key` decorator

### Frontend Architecture
- Vanilla JavaScript (no frameworks)
- State management via global variables
- Fetch API for all HTTP requests
- Plotly.js for interactive charts
- Bootstrap 5 for styling

### Configuration System
- Environment variables via `.env` file
- `python-dotenv` for loading
- Supports SQLite (dev) and PostgreSQL (prod)
- `FLASK_ENV` switches between DevelopmentConfig and ProductionConfig

## 📦 Dependencies

```txt
Flask>=3.0.0
SQLAlchemy>=2.0.0
python-dotenv>=1.0.0
requests>=2.31.0
```

Optional (for PostgreSQL):
```txt
psycopg2-binary>=2.9.0
```

## 🎯 Next Steps (When Resuming)

### Immediate Actions
1. ✅ Ensure database is populated with FIPE data
2. ✅ Configure `.env` with database path and API keys
3. ✅ Test application runs without errors
4. ✅ Verify data loads correctly in browser

### Testing Checklist
- [ ] Brands dropdown populates
- [ ] Models load when brand selected
- [ ] Years load when model selected
- [ ] Chart renders with data
- [ ] Multiple vehicle comparison works
- [ ] Economic indicators display
- [ ] Base 100 view toggles correctly
- [ ] Statistics cards show correct values

### Future Development
See `README.md` section "🔜 Melhorias Futuras" for comprehensive roadmap with 44+ feature suggestions organized by category.

**Priority features to implement:**
1. Inflation-adjusted prices (real vs nominal)
2. Depreciation rate calculation
3. Export to Excel/CSV
4. Similar vehicle suggestions
5. Dark mode

## 🐛 Common Issues & Solutions

### Issue: "Unable to open database file"
**Solution:**
- Verify database path in `.env` is correct
- Ensure database file exists and is populated
- Check file permissions (read access required)
- See `docs/database_schema.md` for required structure

### Issue: "API key required"
**Solution:**
- Configure `API_KEY` and `API_KEYS_ALLOWED` in `.env`
- Ensure `API_KEY` is included in `API_KEYS_ALLOWED`
- For testing, leave empty to allow access in dev mode

### Issue: "No data found for vehicle"
**Solution:**
- Database may not have data for selected vehicle/period
- Try different vehicle or date range
- Verify database is fully populated

### Issue: Charts not loading
**Solution:**
- Check browser console (F12) for JavaScript errors
- Verify API endpoints are responding (test with curl)
- Ensure Plotly.js CDN is accessible

## 📚 Documentation References

| Document | Purpose | Lines |
|----------|---------|-------|
| `CLAUDE.md` | Technical guide for developers/AI | 350+ |
| `README.md` | Main project documentation | 300+ |
| `QUICKSTART.md` | 5-minute setup guide | 180+ |
| `docs/database_schema.md` | Database structure | Full ERD |
| `docs/ENV_SETUP.md` | Environment config guide | Detailed |

## 🤖 For AI Assistants (Claude, etc.)

**When resuming this project:**
1. Read `CLAUDE.md` first - contains complete technical context
2. Database is read-only - webapp never modifies data
3. API uses two-variable key system (see "API Authentication" above)
4. All database queries must join across 5 tables for full vehicle info
5. Frontend JavaScript handles all chart rendering and state

**Key Implementation Patterns:**
```python
# Database session pattern
db = get_db()
try:
    # Query logic here
    return jsonify(results)
finally:
    db.close()

# API endpoint pattern
@app.route('/api/endpoint')
@require_api_key  # Add this decorator
def endpoint():
    pass
```

## 🔐 Security Notes

- `.env` file is in `.gitignore` (never commit secrets)
- API keys use secure random generation
- Session secrets use cryptographic randomness
- All API endpoints protected except index route
- Logging includes IP addresses for audit trail

## 📊 Project Statistics

- **Total Lines of Code:** ~2,500+
- **API Endpoints:** 10
- **Database Tables:** 5
- **Dependencies:** 4 core + 1 optional
- **Documentation Files:** 6
- **Commits:** 8 (latest session)

## 🎓 Learning Resources

- [Flask Documentation](https://flask.palletsprojects.com/)
- [SQLAlchemy ORM Documentation](https://docs.sqlalchemy.org/)
- [Plotly JavaScript](https://plotly.com/javascript/)
- [Bootstrap 5](https://getbootstrap.com/docs/5.3/)

---

## ✨ Final Checklist Before Running

- [ ] Database file exists and is populated
- [ ] `.env` file configured with all required variables
- [ ] Virtual environment activated
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] Port 5000 is available
- [ ] Database path is absolute and correct

**Ready to go?** Run `python app.py` and access http://127.0.0.1:5000

---

**Last Updated:** 2025-10-16
**Project Version:** v1.0 - Feature Complete (pending database)
**License:** MIT
**Author:** Matheus Beccalli
