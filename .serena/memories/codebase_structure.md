# Codebase Structure

## Directory Layout
```
historico_fipe_webapp/
├── app.py                      # Main Flask application (54 KB, ~1400 lines)
├── config.py                   # Environment-based configuration (~6 KB)
├── webapp_database_models.py   # SQLAlchemy ORM models (~15 KB, 457 lines)
├── generate_secret_key.py      # Secure key generator utility
├── requirements.txt            # Python dependencies
├── .env                        # Environment variables (NOT in git)
├── .env.example                # Environment template
├── .gitignore                  # Git ignore rules
├── LICENSE                     # MIT License
├── README.md                   # Main documentation (14 KB)
├── QUICKSTART.md               # Quick setup guide
├── CLAUDE.md                   # Developer/AI assistant guide (11 KB)
├── DESIGN_INSTRUCTIONS.md      # Design guidelines
├── setup.bat                   # Windows setup script
├── setup.sh                    # Linux/Mac setup script
├── data/                       # Database directory (not in git)
│   └── fipe_data.db            # SQLite database (17.5 MB)
├── logs/                       # Production logs (not in git, created at runtime)
│   └── fipe_app.log            # Rotating log file
├── venv/                       # Python virtual environment
├── __pycache__/                # Python bytecode cache
├── .git/                       # Git repository
├── .serena/                    # Serena MCP data
├── .claude/                    # Claude Code data
│   └── agents/                 # Specialized AI agents
│       ├── code-reviewer.md
│       ├── data-analyst-sql.md
│       ├── debug-specialist.md
│       └── feature-implementation-planner.md
├── .debug/                     # Debug files
├── templates/                  # HTML templates
│   └── index.html              # Single-page application
├── static/                     # Static assets
│   ├── css/
│   │   └── style.css           # Custom CSS styles
│   └── js/
│       └── app.js              # Frontend JavaScript (~2000 lines)
└── docs/                       # Documentation
    ├── database_schema.md      # Database structure reference
    └── ENV_SETUP.md            # Environment configuration guide
```

## Core Application Files

### app.py (Main Application)
**Lines**: ~1400  
**Purpose**: Main Flask application with all routes and API endpoints

**Key Sections**:
- Configuration and initialization (lines 1-150)
  - Security headers and CSP setup
  - Production logging with rotation
  - Database schema validation
- Database session management (get_db helper)
- API key authentication decorator
- Security helpers (sanitization, validation)
- Rate limiting and CSRF protection
- API endpoints (11 total):
  - Vehicle Data:
    - `/api/brands` - Get brands (filtered by latest month)
    - `/api/vehicle-options/<brand_id>` - Bidirectional filtering data
    - `/api/months` - Get reference months
    - `/api/default-car` - Default vehicle (with names + IDs)
  - Price & History:
    - `/api/compare-vehicles` - Multi-vehicle comparison (up to 5)
    - `/api/price` - Single price lookup
  - Economic & Market:
    - `/api/economic-indicators` - IPCA and CDI data
    - `/api/depreciation-analysis` - Market depreciation stats
  - System:
    - `/health` - Health check endpoint
    - `/` - Main page
- Error handlers (404, 500)
- Security headers (CSP, Referrer-Policy)

**Deprecated endpoints (removed ~100 lines)**:
- ~~`/api/models/<brand_id>`~~ - Replaced by `/api/vehicle-options`
- ~~`/api/years/<model_id>`~~ - Replaced by `/api/vehicle-options`

### webapp_database_models.py (ORM Models)
**Lines**: 457  
**Purpose**: SQLAlchemy ORM models with relationships

**Models**:
- `ReferenceMonth` - Time periods for price data
- `Brand` - Car manufacturers/brands
- `CarModel` - Car models per brand
- `ModelYear` - Model years with fuel type
- `CarPrice` - Historical price data

**Helper Functions**:
- `get_database_engine()` - Create SQLAlchemy engine
- `get_db_session()` - Create database session
- `format_price_brl()` - Format prices as Brazilian Real
- `format_month_portuguese()` - Format dates in Portuguese
- `parse_month_portuguese()` - Parse Portuguese dates

### config.py (Configuration)
**Lines**: ~200  
**Purpose**: Environment-based configuration system

**Classes**:
- `Config` - Base configuration
- `DevelopmentConfig` - SQLite database
- `ProductionConfig` - PostgreSQL database

**Function**:
- `get_config()` - Returns appropriate config based on FLASK_ENV

## Frontend Files

### templates/index.html
**Purpose**: Single-page application template  
**Features**:
- Bootstrap 5 layout
- Cascading dropdowns with bidirectional filtering
- Multi-vehicle selection with chip display
- Plotly chart container
- Statistics display area
- Dark/light theme toggle
- Tabbed navigation (Comparação/Depreciação)
- Economic indicators display
- CSP nonce-based script loading

### static/js/app.js
**Lines**: ~2000 (after cleanup, removed ~68 deprecated lines)  
**Purpose**: Frontend JavaScript application  
**Features**:
- API communication (fetch with X-API-Key headers)
- Bidirectional filtering logic
- Multi-vehicle comparison (up to 5 vehicles)
- Vehicle chip display with remove buttons (CSP-compliant)
- Chart rendering with Plotly
- Theme switching (dark/light mode)
- localStorage for preferences
- Error handling and user feedback
- Economic indicators integration

**Deprecated functions (removed)**:
- ~~`loadModels()`~~ - Replaced by `loadVehicleOptions()`
- ~~`loadYears()`~~ - Replaced by `loadVehicleOptions()`
- ~~`displayCarInfo()`~~ - Not used anymore

### static/css/style.css
**Purpose**: Custom CSS styles  
**Features**:
- Dark mode styles with CSS variables
- Theme transition animations
- Custom Bootstrap overrides
- Chart container styling
- Premium UI enhancements
- Vehicle chip styling

## Documentation Files

### README.md
**Size**: 14 KB  
**Purpose**: Main project documentation (in Portuguese)  
**Sections**:
- Overview and warnings about database requirement
- Recent features (security, multi-vehicle, depreciation)
- Functionality list (organized by category)
- Installation and setup
- Configuration guide
- Usage instructions
- API endpoints reference (11 endpoints)
- Security section (CSP, rate limiting, logging, etc.)
- Troubleshooting
- Technologies used
- Future improvements roadmap

### CLAUDE.md
**Size**: 11 KB  
**Purpose**: Technical guide for developers and AI assistants  
**Sections**:
- Project overview with key features
- Development tools & agents (Serena MCP, specialized agents)
- Key commands
- Architecture overview
- File structure and responsibilities
- Critical implementation details
- API endpoints reference (11 endpoints with deprecation notes)
- Security features section (CSP, Referrer-Policy, logging, etc.)
- Common modifications
- Database query patterns
- API authentication system

### docs/database_schema.md
**Purpose**: Complete database schema documentation  
**Contents**:
- Table definitions
- Column descriptions
- Relationships
- Example data
- ERD diagram

### docs/ENV_SETUP.md
**Purpose**: Environment configuration guide  
**Contents**:
- Detailed variable explanations
- Configuration examples
- Security best practices
- Troubleshooting

## Configuration Files

### .env (Not in git)
**Purpose**: Environment variables for local instance  
**Contents**:
- FLASK_ENV
- DATABASE_URL
- SECRET_KEY
- API_KEY
- API_KEYS_ALLOWED
- DEFAULT_BRAND
- DEFAULT_MODEL
- SQLALCHEMY_ECHO

### .env.example
**Purpose**: Template for .env file  
**Contents**: Same as .env but with example/placeholder values

### requirements.txt
**Purpose**: Python dependencies  
**Packages**:
- Flask==3.0.0
- SQLAlchemy==2.0.36
- python-dotenv==1.0.0
- requests==2.31.0
- Flask-Limiter==3.5.0
- Flask-WTF==1.2.1
- psycopg2-binary (commented out, for PostgreSQL)

## Utility Scripts

### generate_secret_key.py
**Purpose**: Generate secure random keys for Flask SECRET_KEY  
**Usage**: `python generate_secret_key.py`

### setup.bat (Windows)
**Purpose**: Automated setup for Windows  
**Actions**:
- Creates virtual environment
- Activates venv
- Installs dependencies
- Provides next steps

### setup.sh (Linux/Mac)
**Purpose**: Automated setup for Linux/Mac  
**Actions**: Same as setup.bat but for Unix systems

## Database File

### data/fipe_data.db
**Size**: 17.5 MB  
**Type**: SQLite 3 database  
**Purpose**: Historical FIPE price data  
**Note**: Not committed to git, must be created separately
**Location**: Moved to `data/` directory (previously in root)

## Logs Directory

### logs/fipe_app.log
**Purpose**: Production application logs  
**Features**:
- Rotating file handler (10MB per file, 10 backups)
- Only created in production mode
- Contains API access logs, errors, and warnings
**Note**: Not committed to git, created at runtime

## Important Patterns

### API Endpoint Structure
All API endpoints follow this pattern:
1. Route decorator with path and methods
2. `@require_api_key` decorator (except `/` and `/health`)
3. `@limiter.limit()` decorator for rate limiting
4. Get database session via `get_db()`
5. Try-finally block for session management
6. Query using SQLAlchemy ORM
7. Return JSON via `jsonify()`
8. Close session in finally block

### Frontend API Calls
All frontend API calls:
1. Use `fetch()` with async/await
2. Include `X-API-Key` header from `window.API_KEY`
3. Handle errors with try-catch
4. Update UI based on response
5. Show user feedback on errors

### Security Implementation
1. CSP with nonce-based script execution
2. Referrer-Policy header
3. Rate limiting on all endpoints
4. API key authentication
5. Production logging with rotation
6. Database schema validation on startup
7. Input sanitization for SQL LIKE patterns

### Code Cleanup (Recent)
Removed 189 lines of deprecated code:
- Backend: 2 endpoints (~100 lines)
- Frontend: 3 functions (~68 lines)
- Consolidated vehicle data loading into single endpoint
