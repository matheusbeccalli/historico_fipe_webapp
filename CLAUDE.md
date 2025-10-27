1# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Flask web application that displays historical car price data from the Brazilian FIPE (Fundação Instituto de Pesquisas Econômicas) table. The application provides interactive visualizations of vehicle price trends over time using cascading dropdowns and Plotly charts.

**Key Features:**
- Multi-vehicle comparison (up to 5 vehicles)
- Economic indicators integration (IPCA, CDI)
- Market-wide depreciation analysis
- Dark/light mode theme support
- Intelligent bidirectional filtering (select model or year first)
- Security hardening with CSP, API key authentication, and rate limiting

## Development Tools & Agents

This project is equipped with specialized AI agents and the Serena MCP (Model Context Protocol) to enhance code navigation, analysis, and modification. **Always use these tools** - they are optimized for this codebase and will significantly improve your efficiency.

### Serena MCP - Semantic Code Navigation

**Serena provides symbol-based code navigation** instead of line-based file reading. This is the **preferred way** to explore and modify code in this project.

**Key capabilities:**
- **Symbol overview**: Get high-level view of classes/functions in a file without reading entire file
- **Targeted symbol reading**: Read only specific functions/classes with `find_symbol`
- **Reference tracking**: Find all places where a symbol is used with `find_referencing_symbols`
- **Pattern search**: Search for code patterns with `search_for_pattern`
- **Symbol-based editing**: Edit entire functions/classes with `replace_symbol_body`
- **Insertion helpers**: Add code before/after symbols with `insert_before_symbol` and `insert_after_symbol`
- **Memory system**: Project knowledge stored in memory files for context

**When to use Serena MCP:**
- ✅ **ALWAYS** use `get_symbols_overview` before reading full files
- ✅ Exploring unfamiliar parts of the codebase
- ✅ Finding where a function/class is used
- ✅ Searching for patterns across multiple files
- ✅ Editing entire functions or classes
- ✅ Understanding code structure without loading entire files

**Example workflow:**
```python
# 1. Get overview of file first
get_symbols_overview("app.py")

# 2. Read specific symbol with body
find_symbol(name_path="get_brands", relative_path="app.py", include_body=True)

# 3. Find where it's referenced
find_referencing_symbols(name_path="get_brands", relative_path="app.py")

# 4. Edit the symbol
replace_symbol_body(
    name_path="get_brands",
    relative_path="app.py",
    body="new function implementation"
)
```

**Serena Memory Files:**
Serena maintains project knowledge in memory files:
- `project_overview.md` - Project purpose, tech stack, architecture
- `codebase_structure.md` - File organization and responsibilities
- `code_style_conventions.md` - Coding standards and patterns
- `architecture_patterns.md` - Database patterns, API design, security
- `suggested_commands.md` - Development commands for Windows
- `task_completion_checklist.md` - Quality checks and workflow

**Read these memories when:**
- Starting work on the project for the first time
- Implementing new features
- Unsure about coding conventions
- Need to understand architectural patterns

### Specialized AI Agents

This project includes **5 specialized agents** in `.claude/agents/` that should be used proactively:

#### 1. 🔍 code-reviewer
**When to use:** After writing or modifying code (new features, bug fixes, refactoring)

**Capabilities:**
- Security vulnerability detection (SQL injection, XSS, authentication bypasses)
- Performance analysis (N+1 queries, inefficiencies)
- Code quality review (maintainability, best practices)
- Project-specific pattern validation (checks against CLAUDE.md)
- Prioritized feedback (Critical → High → Medium → Low)

**Use proactively after:**
- Adding new API endpoints
- Modifying database queries
- Implementing new features
- Refactoring existing code

**Example:**
```
User: "I've added a new /api/vehicle-details endpoint"
Assistant: "Let me use the code-reviewer agent to ensure it follows best practices and security standards."
```

#### 2. 📊 data-analyst-sql
**When to use:** For data analysis, SQL queries, insights, or query optimization

**Capabilities:**
- Writing efficient SQLAlchemy ORM queries
- Analyzing price trends and patterns
- Query optimization and performance tuning
- Statistical analysis and insights
- Database exploration and relationship analysis

**Use for:**
- Analyzing FIPE price trends
- Optimizing slow queries
- Exploring data patterns
- Generating reports or insights
- Understanding data relationships

**Example:**
```
User: "Which brands have the most stable prices?"
Assistant: "I'll use the data-analyst-sql agent to analyze price volatility across brands."
```

#### 3. 🐛 debug-specialist
**When to use:** For errors, exceptions, test failures, or unexpected behavior

**Capabilities:**
- Systematic root cause analysis
- Stack trace interpretation
- Strategic debug logging insertion
- Minimal fix implementation
- Verification and prevention recommendations

**Use when encountering:**
- 500 errors or API failures
- Unexpected behavior (wrong data, incorrect charts)
- Application crashes or exceptions
- Database connection issues
- Test failures

**Example:**
```
User: "Getting a 500 error on /api/compare-vehicles"
Assistant: "Let me use the debug-specialist agent to investigate this error."
```

#### 4. 🎯 feature-implementation-planner
**When to use:** Planning implementation of features from "Melhorias Futuras" in README.md

**Capabilities:**
- Deep feature analysis and requirements breakdown
- Phased implementation strategy (Database → Backend → Frontend → Testing)
- Architecture-aware planning (respects existing patterns)
- Risk assessment and dependency mapping
- Code-level guidance with exact file locations

**Use for:**
- Planning new features from the roadmap
- Breaking down complex features into steps
- Understanding dependencies between features
- Creating implementation checklists

**Example:**
```
User: "Let's implement the vehicle comparison feature"
Assistant: "I'll use the feature-implementation-planner agent to create a detailed plan."
```

#### 5. 🧪 e2e-testing-specialist
**When to use:** For end-to-end testing, UI validation, and browser automation

**Capabilities:**
- Browser automation using Puppeteer MCP
- User interface functionality testing
- API integration validation
- Visual regression testing (screenshots)
- Performance metrics collection
- Console error detection
- Multi-viewport testing (desktop, mobile)

**Use for:**
- Testing complete user flows (brand → model → year → chart)
- Validating dropdown cascading and bidirectional filtering
- Checking multi-vehicle comparison feature
- Testing theme toggle (light/dark mode)
- Verifying economic indicators integration
- Post-deployment smoke testing
- Regression testing after bug fixes

**Example:**
```
User: "Test that the vehicle selection workflow works correctly"
Assistant: "I'll use the e2e-testing-specialist agent to automate and validate the complete flow."
```


### Best Practices for Tool Usage

**Priority order for code exploration:**
1. **First**: Use Serena's `get_symbols_overview` to understand file structure
2. **Second**: Use Serena's `find_symbol` to read specific functions/classes
3. **Last resort**: Read entire files only when necessary

**When implementing features:**
1. Use `feature-implementation-planner` agent to create detailed plan
2. Use Serena MCP for symbol-based code navigation and editing
3. Use `code-reviewer` agent after completing implementation
4. Use `e2e-testing-specialist` agent to validate functionality
5. Use `debug-specialist` agent if encountering issues

**When analyzing data or queries:**
1. Use `data-analyst-sql` agent for insights and optimization
2. Use Serena's `find_symbol` to understand existing query patterns
3. Use `code-reviewer` agent to validate query security and performance

**When testing:**
1. Use `e2e-testing-specialist` agent for user flow validation
2. Test after implementing new features or fixing bugs
3. Run smoke tests before deployment
4. Use screenshots and console logs for debugging

**General workflow:**
1. **Plan** → Use feature-implementation-planner for new features
2. **Navigate** → Use Serena MCP for code exploration
3. **Implement** → Use Serena's symbol editing for changes
4. **Review** → Use code-reviewer agent for quality assurance
5. **Test** → Use e2e-testing-specialist for validation
6. **Debug** → Use debug-specialist agent if issues arise
7. **Analyze** → Use data-analyst-sql for insights and optimization

## Key Commands

### Development
```bash
# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Run the application (development mode with auto-reload)
python app.py

# Install dependencies
pip install -r requirements.txt
```

### Quick Setup
```bash
# Windows:
setup.bat

# Linux/Mac:
chmod +x setup.sh && ./setup.sh
```

### Environment Configuration
```bash
# Copy .env.example to .env and update values
cp .env.example .env

# Generate a secure secret key for production
python generate_secret_key.py

# Generate a secure API key
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

## Architecture Overview

### Data Flow Architecture

The application follows a **read-only database pattern** where the Flask webapp queries a pre-populated SQLite database (created by a separate scraper tool):

```
User Browser → Flask Routes → SQLAlchemy ORM → SQLite Database
                    ↓
             JSON API Responses
                    ↓
          JavaScript (app.js) → Plotly Charts
```

### Database Schema

The database uses a **5-table normalized schema** with the following relationships:

```
Brands (1:N) → CarModels (1:N) → ModelYears (1:N) → CarPrices
                                                       ↓ (N:1)
                                                ReferenceMonths
```

**Critical to understand**: To get full vehicle information with price history, you must join across **all 5 tables**:
- `CarPrice` → `ModelYear` → `CarModel` → `Brand`
- `CarPrice` → `ReferenceMonth`

This join pattern is used throughout the application (see app.py:244-256).

### Configuration System

The application uses **environment-based configuration** with `.env` files:
- All sensitive configuration is stored in `.env` (never committed to git)
- `config.py` loads environment variables using `python-dotenv`
- `DevelopmentConfig` (default) - SQLite database
- `ProductionConfig` - PostgreSQL database
- Controlled via `FLASK_ENV` environment variable

**Important environment variables**:
- `DATABASE_URL` - Database connection string
- `SECRET_KEY` - Flask session secret (use `generate_secret_key.py` to create)
- `API_KEY` - Application's own API key (injected into frontend for API calls)
- `API_KEYS_ALLOWED` - Comma-separated list of valid API keys (must include API_KEY)
- `DEFAULT_BRAND` - Default brand to show on page load
- `DEFAULT_MODEL` - Default model to show on page load
- `SQLALCHEMY_ECHO` - Set to "True" to see SQL queries in logs

### API Design Pattern

All API endpoints follow a consistent pattern:
1. Create database session via `get_db()` helper (app.py:30)
2. Perform query using SQLAlchemy ORM
3. Close session in `finally` block
4. Return JSON response

**Never** manually construct SQL strings - always use SQLAlchemy ORM for type safety.

### Frontend-Backend Communication

The frontend uses a **bidirectional filtering pattern** with cascading dropdowns:
1. Load brands → User selects brand
2. Fetch models AND years for selected brand via `/api/vehicle-options/<brand_id>`
3. User can select model first (filters years) OR year first (filters models)
4. POST to `/api/compare-vehicles` with all selections to render multi-vehicle comparison chart

This pattern is implemented in `static/js/app.js` and ensures the UI remains responsive with minimal data transfer. The `/api/vehicle-options` endpoint returns a `model_year_lookup` object that enables efficient bidirectional filtering on the client side.

## File Structure and Responsibilities

```
historico_fipe_webapp/
├── app.py                      # Main Flask application
├── config.py                   # Environment-based configuration
├── webapp_database_models.py   # SQLAlchemy ORM models
├── generate_secret_key.py      # Secure key generator
├── .env                        # Environment variables (not in git)
├── .env.example                # Environment template
│
├── templates/                  # HTML templates
│   └── index.html             # Single-page application
│
├── static/                     # Frontend assets
│   ├── js/app.js              # JavaScript for API calls and charts
│   └── css/style.css          # Custom styles
│
└── docs/                       # Documentation
    ├── README.md              # Documentation index
    ├── database_schema.md     # Database structure reference
    └── ENV_SETUP.md           # Environment configuration guide
```

### Core Application Files

- **app.py** (413 lines) - Main Flask application with all routes and API endpoints
- **config.py** - Environment-based configuration system using python-dotenv
- **webapp_database_models.py** (457 lines) - SQLAlchemy ORM models with relationships
- **.env** - Environment variables (not committed to git, copy from .env.example)

### Frontend Files

- **templates/index.html** - Single-page application template
- **static/js/app.js** - Handles all API calls, dropdown cascading, and chart rendering
- **static/css/style.css** - Custom styles

### Documentation

- **docs/database_schema.md** - Complete database schema documentation with ERD
- **docs/ENV_SETUP.md** - Comprehensive environment configuration guide

### Utilities

- **generate_secret_key.py** - Helper script to generate secure random keys for Flask SECRET_KEY

## Critical Implementation Details

### Date Handling

Dates are stored as `YYYY-MM-DD` in the database but must be displayed in Portuguese format to users:
- Database: `2024-01-01`
- Display: `janeiro/2024`

Use `format_month_portuguese()` helper function (webapp_database_models.py:387) for conversion.

### Price Formatting

Prices are stored as floats but must be displayed in Brazilian Real format:
- Database: `11520.00`
- Display: `R$ 11.520,00`

Use `format_price_brl()` helper function (webapp_database_models.py:341) for conversion.

### Default Car Selection

The application loads with a default car (configured via `DEFAULT_BRAND` and `DEFAULT_MODEL` environment variables in `.env`). The `/api/default-car` endpoint (app.py:308) uses fuzzy matching with `ILIKE` to find models containing the configured model name.

### Error Handling Pattern

All API routes use try-finally blocks to ensure database sessions are always closed. Return appropriate HTTP status codes:
- 400 for missing parameters
- 404 for no data found
- 500 for server errors

## Common Modifications

### Adding New API Endpoints

Follow the existing pattern in app.py:
1. Create route with `@app.route()` decorator
2. Get database session with `get_db()`
3. Build query using SQLAlchemy ORM with proper joins
4. Return `jsonify()` response
5. Always use `try-finally` to close session

### API Endpoints Reference

The application provides 11 RESTful endpoints (all require `X-API-Key` header except `/` and `/health`):

**Vehicle Data:**
1. **GET /api/brands** - List all brands available in the most recent FIPE table
2. **GET /api/vehicle-options/<brand_id>** - Get models and years for a brand with bidirectional filtering support
3. **GET /api/months** - List all available reference months
4. **GET /api/default-car** - Get default vehicle selection (returns names + IDs)

**Price & History:**
5. **POST /api/compare-vehicles** - Get price history for multiple vehicles (up to 5)
6. **POST /api/price** - Get single price point for a vehicle at a specific month

**Economic & Market Analysis:**
7. **POST /api/economic-indicators** - Get IPCA and CDI data for date ranges
8. **POST /api/depreciation-analysis** - Get market-wide depreciation statistics by brand/year

**System:**
9. **GET /health** - Health check endpoint for monitoring and load balancers
10. **GET /** - Main page (no authentication required)

**Deprecated (Removed):**
- ~~GET /api/models/<brand_id>~~ - Replaced by `/api/vehicle-options/<brand_id>`
- ~~GET /api/years/<model_id>~~ - Replaced by `/api/vehicle-options/<brand_id>`
- ~~POST /api/chart-data~~ - Replaced by `/api/compare-vehicles`

### Single Price Lookup Endpoint

The `/api/price` endpoint (app.py:308) provides direct price lookups similar to FIPE's `/ConsultarValorComTodosParametros`:

**Request:**
```json
POST /api/price
{
  "brand": "Volkswagen",
  "model": "Gol",
  "year": "2024 Flex",
  "month": "2024-01-01"
}
```

**Response:**
```json
{
  "brand": "Volkswagen",
  "model": "Gol 1.0 12V MCV",
  "year": "2024 Flex",
  "month": "janeiro/2024",
  "month_date": "2024-01-01",
  "price": 56789.00,
  "price_formatted": "R$ 56.789,00",
  "fipe_code": "026011-6"
}
```

**Key features:**
- Uses fuzzy matching with `ILIKE` for brand and model names
- Exact match required for year description and month date
- Returns formatted price in Brazilian Real format
- Includes FIPE code for reference
- Returns 404 with search details if no data found

### Extending the Chart

The chart data format is defined in `/api/compare-vehicles`. Each data point must include:
- `date` (ISO format string)
- `price` (float)
- `label` (Portuguese formatted date)

### Changing the Database

To switch from SQLite to PostgreSQL:
1. Update `DATABASE_URL` in `.env` to PostgreSQL connection string (e.g., `postgresql://user:password@localhost/fipe_db`)
2. Install `psycopg2-binary` (uncomment line in requirements.txt)
3. Set `FLASK_ENV=production` in `.env`

## Database Query Patterns

### Basic Pattern for Price History

```python
query = (
    db.query(ReferenceMonth.month_date, CarPrice.price)
    .join(CarPrice.reference_month)
    .join(CarPrice.model_year)
    .join(ModelYear.car_model)
    .join(CarModel.brand)
    .filter(ModelYear.id == year_id)
    .order_by(ReferenceMonth.month_date)
)
```

This pattern is fundamental to the application - see app.py:244-266 for the canonical implementation.

### Filtering by Date Range

```python
if start_date:
    query = query.filter(ReferenceMonth.month_date >= start_date)
if end_date:
    query = query.filter(ReferenceMonth.month_date <= end_date)
```

## Important Constraints

### Read-Only Database Access

The webapp should **NEVER** perform INSERT, UPDATE, or DELETE operations. The database is populated by a separate scraper tool. All webapp operations should be SELECT queries only.

### Data Availability

Not all vehicle/month combinations exist in the database. Always check if query results are empty before processing (see app.py:272-275).

### Session Management

Always close database sessions in `finally` blocks. Unclosed sessions will cause connection pool exhaustion. The `get_db()` helper (app.py:30-42) demonstrates the correct pattern.

## API Authentication

### API Key System

The application uses a **two-variable API key system** for authentication:

1. **`API_KEY`** - The application's own key, injected into the frontend JavaScript (`window.API_KEY`) for automatic authentication of browser requests
2. **`API_KEYS_ALLOWED`** - Comma-separated list of ALL valid API keys that can access the API (must include `API_KEY` plus any external client keys)

**How it works:**
- All API endpoints (except the index page `/`) require authentication via the `@require_api_key` decorator
- API key must be provided in the `X-API-Key` HTTP header
- Frontend automatically includes the key from `window.API_KEY` in all fetch requests
- If no keys are configured, the app allows access in development mode with a warning

**Configuration example (.env):**
```bash
# Generate with: python -c "import secrets; print(secrets.token_urlsafe(32))"
API_KEY=your-app-key-abc123xyz

# Include API_KEY plus any external client keys
API_KEYS_ALLOWED=your-app-key-abc123xyz,partner-key-1,partner-key-2
```

**Logging:**
- Successful API access: Logs key prefix (first 8 chars), endpoint, method, and IP address
- Invalid attempts: Logs key prefix, IP address, and attempted endpoint
- All logs use Flask's standard logger (app.logger)

**Adding API key authentication to new endpoints:**
```python
@app.route('/api/new-endpoint', methods=['GET'])
@require_api_key  # Add this decorator
def new_endpoint():
    # Your endpoint code
    pass
```

**Frontend JavaScript pattern:**
```javascript
const response = await fetch('/api/endpoint', {
    headers: {
        'X-API-Key': window.API_KEY  // Automatically included
    }
});
```

## Security Features

The application implements multiple layers of security:

### Content Security Policy (CSP)

**Nonce-based script execution** prevents XSS attacks:
- All inline scripts require a unique nonce generated per request
- External scripts whitelisted from trusted CDNs (cdn.plot.ly, cdn.jsdelivr.net)
- Inline styles allowed for Plotly compatibility (lower XSS risk than scripts)

**CSP Directives** (app.py:592-641):
```python
csp_directives = [
    "default-src 'self'",
    f"script-src 'self' 'nonce-{nonce}' https://cdn.plot.ly https://cdn.jsdelivr.net",
    f"style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com",
    "font-src 'self' https://fonts.gstatic.com https://cdn.jsdelivr.net",
    "img-src 'self' data:",
    "connect-src 'self' https://cdn.plot.ly https://cdn.jsdelivr.net https://api.bcb.gov.br"
]
```

**Important**: When adding external resources, update the appropriate CSP directive or they will be blocked by the browser.

### Referrer-Policy Header

**Prevents information leakage** in HTTP headers (app.py:641):
```python
response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
```

This ensures that only the origin (not full URL) is sent in the Referer header when navigating to external sites.

### Production Logging

**Log rotation prevents disk exhaustion** (app.py:57-85):
- RotatingFileHandler with 10MB max per file
- Keeps 10 backup files (100MB total)
- Logs stored in `logs/fipe_app.log`
- Only enabled in production mode (`FLASK_ENV=production`)

### Database Schema Validation

**Ensures database integrity on startup** (app.py:120-158):
- Validates all 5 required tables exist (brands, car_models, model_years, car_prices, reference_months)
- Application refuses to start if schema is invalid
- Logs detailed validation results

### Rate Limiting

**Prevents API abuse** using Flask-Limiter with **intelligent rate limit differentiation**:

The application applies **different rate limits for browser users vs external API clients**:
- **Browser users** (using the shared `API_KEY` from `.env`) are rate-limited **by IP address**, with generous per-minute limits for interactive UI usage
- **External API clients** (using their own unique API keys) are rate-limited **by API key**, with stricter limits to prevent scraping and abuse

**Rate Limits by Endpoint:**

| Endpoint | Browser Users | External API Clients |
|----------|--------------|---------------------|
| `/api/brands` | 120/minute | 60/minute |
| `/api/vehicle-options` | 120/minute | 60/minute |
| `/api/months` | 120/minute | 60/minute |
| `/api/default-car` | 120/minute | 60/minute |
| `/api/price` | 60/minute | 20/minute |
| `/api/compare-vehicles` | 30/minute | 10/minute |
| `/api/economic-indicators` | 60/minute | 60/hour |
| `/api/depreciation-analysis` | 20/minute | 10/minute |
| `/health` | 60/minute | 60/minute |
| `/` (index page) | 20/minute | 20/minute |

**Implementation Details** (app.py:186-236):
- `get_rate_limit_key()` distinguishes browser users from API clients based on the API key
- `make_rate_limit(browser_limit, api_limit)` creates dynamic limit functions per endpoint
- Browser users identified by matching `request.headers['X-API-Key']` with `app.config['API_KEY']`
- Returns HTTP 429 Too Many Requests when limits exceeded

### Health Check Endpoint

**Enables monitoring and load balancer integration** (app.py:688-733):
```bash
GET /health
```

Returns JSON with database connectivity status:
```json
{
  "status": "healthy",
  "timestamp": "2025-10-27T10:30:00",
  "service": "fipe-price-tracker",
  "checks": {
    "database": "ok",
    "session": "unknown"
  }
}
```

Returns HTTP 503 if database connection fails.
