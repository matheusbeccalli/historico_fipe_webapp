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
├── fipe_data.db                # SQLite database (17.5 MB)
├── venv/                       # Python virtual environment
├── __pycache__/                # Python bytecode cache
├── .git/                       # Git repository
├── .serena/                    # Serena MCP data
├── .claude/                    # Claude Code data
├── .debug/                     # Debug files
├── templates/                  # HTML templates
│   └── index.html              # Single-page application
├── static/                     # Static assets
│   ├── css/
│   │   └── style.css           # Custom CSS styles
│   └── js/
│       └── app.js              # Frontend JavaScript
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
- Database session management (get_db helper)
- API key authentication decorator
- Security helpers (sanitization, validation)
- Rate limiting and CSRF protection
- API endpoints:
  - `/api/brands` - Get brands
  - `/api/models/<brand_id>` - Get models
  - `/api/years/<model_id>` - Get years
  - `/api/vehicle-options/<brand_id>` - Bidirectional filtering
  - `/api/months` - Get reference months
  - `/api/chart-data` - Price history for charts
  - `/api/compare-vehicles` - Multi-vehicle comparison
  - `/api/price` - Single price lookup
  - `/api/economic-indicators` - IPCA and CDI data
  - `/api/default-car` - Default vehicle selection
- Error handlers (404, 500)
- Security headers

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
- Cascading dropdowns for vehicle selection
- Plotly chart container
- Statistics display area
- Dark/light theme toggle
- Tabbed navigation for statistics
- Economic indicators display

### static/js/app.js
**Purpose**: Frontend JavaScript application  
**Features**:
- API communication (fetch with API key headers)
- Dropdown cascade logic
- Bidirectional filtering
- Chart rendering with Plotly
- Vehicle comparison logic
- Theme switching (dark/light mode)
- localStorage for preferences
- Error handling and user feedback

### static/css/style.css
**Purpose**: Custom CSS styles  
**Features**:
- Dark mode styles
- Theme transition animations
- Custom Bootstrap overrides
- Chart container styling
- Premium UI enhancements

## Documentation Files

### README.md
**Size**: 14 KB  
**Purpose**: Main project documentation  
**Sections**:
- Overview and warnings about database requirement
- Recent features
- Functionality list
- Installation and setup
- Configuration guide
- Usage instructions
- API endpoints reference
- Troubleshooting
- Technologies used
- Future improvements roadmap

### CLAUDE.md
**Size**: 11 KB  
**Purpose**: Technical guide for developers and AI assistants  
**Sections**:
- Project overview
- Key commands
- Architecture overview
- File structure and responsibilities
- Critical implementation details
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

### fipe_data.db
**Size**: 17.5 MB  
**Type**: SQLite 3 database  
**Purpose**: Historical FIPE price data  
**Note**: Not committed to git, must be created separately

## Important Patterns

### API Endpoint Structure
All API endpoints follow this pattern:
1. Route decorator with path and methods
2. `@require_api_key` decorator
3. `@limiter.limit()` decorator
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
