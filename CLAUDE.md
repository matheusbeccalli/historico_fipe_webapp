1# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Flask web application that displays historical car price data from the Brazilian FIPE (Fundação Instituto de Pesquisas Econômicas) table. The application provides interactive visualizations of vehicle price trends over time using cascading dropdowns and Plotly charts.

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

The frontend uses a **cascading dropdown pattern**:
1. Load brands → User selects brand
2. Fetch models for selected brand → User selects model
3. Fetch years for selected model → User selects year
4. POST to `/api/chart-data` with all selections to render chart

This pattern is implemented in `static/js/app.js` and ensures the UI remains responsive with minimal data transfer.

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

The application provides 7 RESTful endpoints:

1. **GET /api/brands** - List all brands
2. **GET /api/models/<brand_id>** - List models for a brand
3. **GET /api/years/<model_id>** - List years for a model
4. **GET /api/months** - List all available reference months
5. **POST /api/chart-data** - Get price history (multiple months) for a vehicle
6. **POST /api/price** - Get single price point for a vehicle at a specific month (NEW)
7. **GET /api/default-car** - Get default vehicle selection

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

The chart data format is defined in `/api/chart-data` (app.py:197-305). Each data point must include:
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
