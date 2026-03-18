# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Flask web application that displays historical car price data from the Brazilian FIPE (Fundação Instituto de Pesquisas Econômicas) table. The application provides interactive visualizations of vehicle price trends over time using cascading dropdowns and Plotly charts.

**Key Features:**
- Multi-vehicle comparison (up to 5 vehicles)
- Economic indicators integration (IPCA, CDI)
- Market-wide depreciation analysis
- Dark/light mode theme support
- Intelligent bidirectional filtering (select model or year first)
- Public API with documentation page at `/api/docs`
- Security hardening with CSP, CSRF protection, and rate limiting

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
- `suggested_commands.md` - Development commands
- `task_completion_checklist.md` - Quality checks and workflow

**Read these memories when:**
- Starting work on the project for the first time
- Implementing new features
- Unsure about coding conventions
- Need to understand architectural patterns

### Specialized AI Agents

This project includes **4 specialized agents** in `.claude/agents/` that should be used proactively:

**Note:** For code review, use the `superpowers:requesting-code-review` skill available through the superpowers plugin system.

#### 1. data-analyst-sql
**When to use:** For data analysis, SQL queries, insights, or query optimization

#### 2. debug-specialist
**When to use:** For errors, exceptions, test failures, or unexpected behavior

#### 3. feature-implementation-planner
**When to use:** Planning implementation of features from the project roadmap

**Roadmap Location:**
- **Active development**: Linear project "FIPE Webapp"
- **Feature ideas**: "Melhorias Futuras" section in README.md

#### 4. e2e-testing-specialist
**When to use:** For end-to-end testing, UI validation, and browser automation

### Best Practices for Tool Usage

**Priority order for code exploration:**
1. **First**: Use Serena's `get_symbols_overview` to understand file structure
2. **Second**: Use Serena's `find_symbol` to read specific functions/classes
3. **Last resort**: Read entire files only when necessary

**General workflow:**
1. **Plan** - Use feature-implementation-planner for new features
2. **Navigate** - Use Serena MCP for code exploration
3. **Implement** - Use Serena's symbol editing for changes
4. **Test** - Use e2e-testing-specialist for validation
5. **Debug** - Use debug-specialist agent if issues arise
6. **Review** - Use superpowers:requesting-code-review skill after major changes

## Key Commands

### Development
```bash
# Activate virtual environment
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Run the application (development mode with auto-reload)
python app.py

# Install dependencies
pip install -r requirements.txt
```

### Environment Configuration
```bash
# Copy .env.example to .env and update values
cp .env.example .env

# Generate a secure secret key for production
python generate_secret_key.py
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

This join pattern is used throughout the application (search for `join(CarPrice.reference_month)` in app.py).

### Configuration System

The application uses **environment-based configuration** with `.env` files:
- All sensitive configuration is stored in `.env` (never committed to git)
- `config.py` loads environment variables using `python-dotenv`
- `DevelopmentConfig` (default) - SQLite database in `data/fipe_data.db`
- `ProductionConfig` - PostgreSQL database
- Controlled via `FLASK_ENV` environment variable

**Important environment variables**:
- `DATABASE_URL` - Database connection string
- `SECRET_KEY` - Flask session secret (use `generate_secret_key.py` to create)
- `DEFAULT_BRAND` - Default brand to show on page load
- `DEFAULT_MODEL` - Default model to show on page load
- `GA_MEASUREMENT_ID` - Google Analytics 4 measurement ID (optional)
- `SQLALCHEMY_ECHO` - Set to "True" to see SQL queries in logs

### API Design Pattern

All API endpoints follow a consistent pattern:
1. Create database session via `get_db()` helper
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

This pattern is implemented in `static/js/app.js`. The `/api/vehicle-options` endpoint returns a `model_year_lookup` object that enables efficient bidirectional filtering on the client side.

## File Structure and Responsibilities

```
historico_fipe_webapp/
├── app.py                      # Main Flask application (~1800 lines)
├── config.py                   # Environment-based configuration
├── webapp_database_models.py   # SQLAlchemy ORM models
├── generate_secret_key.py      # Secure key generator
├── .env                        # Environment variables (not in git)
├── .env.example                # Environment template
│
├── templates/
│   ├── index.html             # Main single-page application
│   └── api_docs.html          # API documentation page
│
├── static/
│   ├── js/app.js              # JavaScript for API calls and charts
│   └── css/style.css          # Custom styles
│
└── docs/
    └── database_schema.md     # Database structure reference
```

## Critical Implementation Details

### Date Handling

Dates are stored as `YYYY-MM-DD` in the database but must be displayed in Portuguese format to users:
- Database: `2024-01-01`
- Display: `janeiro/2024`

Use `format_month_portuguese()` helper function in `webapp_database_models.py` for conversion.

### Price Formatting

Prices are stored as floats but must be displayed in Brazilian Real format:
- Database: `11520.00`
- Display: `R$ 11.520,00`

Use `format_price_brl()` helper function in `webapp_database_models.py` for conversion.

### Default Car Selection

The application loads with a default car (configured via `DEFAULT_BRAND` and `DEFAULT_MODEL` environment variables in `.env`). The `/api/default-car` endpoint uses fuzzy matching with `ILIKE` to find models containing the configured model name.

### Error Handling Pattern

All API routes use try-finally blocks to ensure database sessions are always closed. Return appropriate HTTP status codes:
- 400 for missing parameters
- 404 for no data found
- 500 for server errors

## Common Modifications

### Adding New API Endpoints

Follow the existing pattern in app.py:
1. Create route with `@app.route()` decorator
2. Add `@limiter.limit()` for rate limiting
3. Get database session with `get_db()`
4. Build query using SQLAlchemy ORM with proper joins
5. Return `jsonify()` response
6. Always use `try-finally` to close session
7. For POST endpoints: add `@csrf.exempt` if the endpoint should be callable by external consumers

### API Endpoints Reference

The application provides these RESTful endpoints (all rate-limited by IP, API is public with no authentication required):

**Pages:**
- **GET /** - Main page
- **GET /api/docs** - API documentation page

**Vehicle Data:**
- **GET /api/brands** - List all brands available in the most recent FIPE table
- **GET /api/vehicle-options/<brand_id>** - Get models and years for a brand with bidirectional filtering support
- **GET /api/months** - List all available reference months
- **GET /api/default-car** - Get default vehicle selection (returns names + IDs)

**Price & History:**
- **POST /api/compare-vehicles** - Get price history for multiple vehicles (up to 5)
- **POST /api/price** - Get single price point for a vehicle at a specific month

**Economic & Market Analysis:**
- **POST /api/economic-indicators** - Get IPCA and CDI data for date ranges
- **GET /api/depreciation-analysis** - Get market-wide depreciation statistics by brand/year

**System:**
- **GET /health** - Health check endpoint for monitoring and load balancers

### Single Price Lookup Endpoint

The `/api/price` endpoint provides direct price lookups similar to FIPE's `/ConsultarValorComTodosParametros`:

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

Not all vehicle/month combinations exist in the database. Always check if query results are empty before processing.

### Session Management

Always close database sessions in `finally` blocks. Unclosed sessions will cause connection pool exhaustion. The `get_db()` helper demonstrates the correct pattern.

## Security Features

The application implements multiple layers of security:

### Content Security Policy (CSP)

**Nonce-based script execution** prevents XSS attacks:
- All inline scripts require a unique nonce generated per request
- External scripts whitelisted from trusted CDNs (cdn.plot.ly, cdn.jsdelivr.net)
- Inline styles allowed for Plotly compatibility (lower XSS risk than scripts)

**Important**: When adding external resources, update the appropriate CSP directive in `set_security_headers()` or they will be blocked by the browser.

### CSRF Protection

The application uses **Flask-WTF's global CSRF protection** (`CSRFProtect(app)`). The frontend includes a CSRF token meta tag (`{{ csrf_token() }}`) and sends it via `X-CSRFToken` header on POST requests.

**API POST routes are CSRF-exempt** via `@csrf.exempt` to allow external consumers (curl, Postman, server-to-server) to call them directly. A custom `CSRFError` handler returns JSON error responses.

### Rate Limiting

**Prevents API abuse** using Flask-Limiter with IP-based rate limiting:

| Endpoint | Rate Limit |
|----------|-----------|
| `/api/brands` | 120/minute |
| `/api/vehicle-options` | 120/minute |
| `/api/months` | 120/minute |
| `/api/default-car` | 120/minute |
| `/api/price` | 60/minute |
| `/api/compare-vehicles` | 30/minute |
| `/api/economic-indicators` | 60/minute |
| `/api/depreciation-analysis` | 20/minute |
| `/health` | 60/minute |
| `/` and `/api/docs` | 20/minute |

Returns HTTP 429 Too Many Requests when limits exceeded.

### Other Security Features

- **Referrer-Policy**: `strict-origin-when-cross-origin` prevents information leakage
- **Production Logging**: RotatingFileHandler with 10MB max per file, 10 backups
- **Database Schema Validation**: Validates all 5 required tables exist on startup
- **Health Check**: `/health` endpoint returns database connectivity status (HTTP 503 if down)
