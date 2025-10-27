# Architecture and Implementation Patterns

## Overall Architecture

### Read-Only Database Pattern
The webapp follows a strict read-only pattern:
- Database pre-populated by separate scraper tool (not in this repo)
- Webapp performs SELECT queries only
- No INSERT, UPDATE, or DELETE operations
- Ensures data integrity and separation of concerns

### Request Flow
```
User Browser
    ↓
Flask Routes (app.py)
    ↓
SQLAlchemy ORM
    ↓
SQLite Database (fipe_data.db)
    ↓
JSON API Response
    ↓
JavaScript (app.js)
    ↓
Plotly Charts / UI Updates
```

## Database Schema Pattern

### 5-Table Normalized Schema
```
Brands (1:N) → CarModels (1:N) → ModelYears (1:N) → CarPrices
                                                       ↓ (N:1)
                                                ReferenceMonths
```

### Critical Join Pattern
To get complete vehicle information with price history, you MUST join all 5 tables:

```python
query = (
    db.query(ReferenceMonth.month_date, CarPrice.price)
    .join(CarPrice.reference_month)        # CarPrices → ReferenceMonths
    .join(CarPrice.model_year)             # CarPrices → ModelYears
    .join(ModelYear.car_model)             # ModelYears → CarModels
    .join(CarModel.brand)                  # CarModels → Brands
    .filter(Brand.id == brand_id)
    .filter(CarModel.id == model_id)
    .filter(ModelYear.id == year_id)
    .order_by(ReferenceMonth.month_date)
)
```

This pattern appears in app.py and is fundamental to the application.

### Latest Month Filtering
Many queries filter by the latest reference month to show only current vehicles:

```python
latest_month = get_latest_reference_month(db)

brands = (
    db.query(Brand)
    .join(Brand.models)
    .join(CarModel.years)
    .join(ModelYear.prices)
    .join(CarPrice.reference_month)
    .filter(ReferenceMonth.month_date == latest_month)
    .distinct()
    .all()
)
```

This ensures dropdowns only show vehicles available in FIPE's most recent data.

## Configuration Pattern

### Environment-Based Configuration
Configuration uses python-dotenv with .env files:

**config.py structure**:
- `Config` - Base class with common settings
- `DevelopmentConfig` - SQLite database
- `ProductionConfig` - PostgreSQL database
- `get_config()` - Returns appropriate config based on FLASK_ENV

**Key environment variables**:
- `DATABASE_URL` - Database connection string
- `SECRET_KEY` - Flask session secret
- `API_KEY` - Application's API key (injected into frontend)
- `API_KEYS_ALLOWED` - Comma-separated list of valid keys
- `DEFAULT_BRAND` / `DEFAULT_MODEL` - Default selections
- `SQLALCHEMY_ECHO` - SQL query logging

### Configuration Loading
```python
from config import get_config
config_obj = get_config()
app.config.from_object(config_obj)
```

## API Design Pattern

### Consistent Endpoint Structure
Every API endpoint follows this exact pattern:

```python
@app.route('/api/endpoint', methods=['GET'])
@require_api_key
@limiter.limit("60 per minute")
def endpoint_name():
    """
    Docstring describing endpoint.
    
    Returns:
        JSON response structure
    """
    db = get_db()
    try:
        # Perform query
        results = db.query(...).filter(...).all()
        
        # Transform to JSON-serializable format
        data = [item.to_dict() for item in results]
        
        return jsonify(data)
    
    finally:
        db.close()
```

**Critical elements**:
1. Route decorator with path and HTTP methods
2. `@require_api_key` for authentication
3. `@limiter.limit()` for rate limiting
4. `get_db()` for session creation
5. `try-finally` block ensuring session cleanup
6. SQLAlchemy ORM queries (never raw SQL)
7. `jsonify()` for JSON response
8. Session closure in `finally` block

### API Endpoints (10 total)

**Vehicle Data:**
1. `GET /api/brands` - List all brands available in most recent FIPE table
2. `GET /api/vehicle-options/<brand_id>` - Get models and years with bidirectional filtering support
3. `GET /api/months` - List all available reference months
4. `GET /api/default-car` - Get default vehicle selection (returns names + IDs)

**Price & History:**
5. `POST /api/compare-vehicles` - Get price history for multiple vehicles (up to 5)
6. `POST /api/price` - Get single price point for vehicle at specific month

**Economic & Market Analysis:**
7. `POST /api/economic-indicators` - Get IPCA and CDI data for date ranges
8. `POST /api/depreciation-analysis` - Get market-wide depreciation statistics by brand/year

**System:**
9. `GET /health` - Health check for monitoring and load balancers
10. `GET /` - Main page (no authentication required)

**Deprecated (Removed):**
- ~~GET /api/models/<brand_id>~~ - Replaced by /api/vehicle-options/<brand_id>
- ~~GET /api/years/<model_id>~~ - Replaced by /api/vehicle-options/<brand_id>
- ~~POST /api/chart-data~~ - Replaced by /api/compare-vehicles

### API Authentication Pattern

**Two-variable system**:
- `API_KEY` - Application's own key (injected into frontend as `window.API_KEY`)
- `API_KEYS_ALLOWED` - Comma-separated list of all valid keys (must include API_KEY)

**Implementation**:
```python
@require_api_key
def endpoint():
    # API key validated before reaching here
    pass
```

**Frontend usage**:
```javascript
const response = await fetch('/api/endpoint', {
    headers: {
        'X-API-Key': window.API_KEY  // Automatically included
    }
});
```

## Frontend-Backend Communication Pattern

### Bidirectional Filtering Pattern
The UI uses an optimized bidirectional filtering pattern:

**Flow**:
1. Page loads → Fetch brands → Populate brand dropdown
2. User selects brand → Fetch `/api/vehicle-options/<brand_id>` → Returns models, years, and `model_year_lookup` mapping
3. User can select model first (filters years) OR year first (filters models)
4. User adds vehicle to comparison list
5. User clicks "Atualizar Gráfico" → POST to `/api/compare-vehicles` with all selected vehicles → Render multi-vehicle chart

**Key optimization**: `/api/vehicle-options` returns all data in one call:
```json
{
  "models": [...],
  "years": [...],
  "model_year_lookup": {
    "model_id": [year_id1, year_id2],
    "year_id": [model_id1, model_id2]
  }
}
```

**Implementation in app.js**:
```javascript
async function loadVehicleOptions(brandId) {
    const response = await fetch(`/api/vehicle-options/${brandId}`, {
        headers: { 'X-API-Key': window.API_KEY }
    });
    const data = await response.json();
    
    // Store for bidirectional filtering
    vehicleOptions = data;
    
    // Populate both dropdowns
    populateDropdown('model-select', data.models);
    populateDropdown('year-select', data.years);
}

function filterYearsByModel(modelId) {
    const validYears = vehicleOptions.model_year_lookup[modelId] || [];
    // Filter year dropdown to show only valid years for this model
}

function filterModelsByYear(yearId) {
    const validModels = vehicleOptions.model_year_lookup[yearId] || [];
    // Filter model dropdown to show only valid models for this year
}
```

### Error Handling Pattern

**Backend**:
```python
if not required_param:
    return jsonify({'error': 'Description'}), 400

results = db.query(...).all()
if not results:
    return jsonify({'error': 'No data found'}), 404
```

**Frontend**:
```javascript
try {
    const response = await fetch(...);
    if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
    }
    const data = await response.json();
    // Use data
} catch (error) {
    console.error('Error:', error);
    alert('User-friendly error message');
}
```

## Data Formatting Patterns

### Date Handling
Dates have two representations:

**Database storage**: `YYYY-MM-DD` (ISO format)
```python
month_date = "2024-01-01"
```

**User display**: Portuguese format `mês/ano`
```python
display = format_month_portuguese(month_date)  # "janeiro/2024"
```

**Helper function** (webapp_database_models.py):
```python
def format_month_portuguese(date_str):
    """Convert YYYY-MM-DD to 'mês/ano' in Portuguese."""
    pass
```

### Price Formatting
Prices have two representations:

**Database storage**: Float
```python
price = 11520.00
```

**User display**: Brazilian Real format
```python
display = format_price_brl(price)  # "R$ 11.520,00"
```

**Helper function** (webapp_database_models.py):
```python
def format_price_brl(price):
    """Format price as Brazilian Real."""
    pass
```

## Security Patterns

### Content Security Policy (CSP)
**Nonce-based script execution** prevents XSS attacks (app.py):

```python
@app.after_request
def set_security_headers(response):
    nonce = secrets.token_urlsafe(16)
    g.csp_nonce = nonce
    
    csp_directives = [
        "default-src 'self'",
        f"script-src 'self' 'nonce-{nonce}' https://cdn.plot.ly https://cdn.jsdelivr.net",
        f"style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com",
        "font-src 'self' https://fonts.gstatic.com https://cdn.jsdelivr.net",
        "img-src 'self' data:",
        "connect-src 'self' https://cdn.plot.ly https://cdn.jsdelivr.net https://api.bcb.gov.br"
    ]
    
    response.headers['Content-Security-Policy'] = "; ".join(csp_directives)
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    return response
```

**Important**: When adding external resources, update the appropriate CSP directive or they will be blocked.

### Referrer-Policy Header
Prevents information leakage in HTTP headers:
```python
response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
```

### Production Logging
Log rotation prevents disk exhaustion (app.py):
```python
if is_production:
    logs_dir = Path(__file__).parent / 'logs'
    logs_dir.mkdir(exist_ok=True)
    
    file_handler = RotatingFileHandler(
        logs_dir / 'fipe_app.log',
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=10
    )
```

### Database Schema Validation
Ensures database integrity on startup (app.py):
```python
def validate_database_schema():
    """Validate that all required tables exist in the database."""
    required_tables = ['brands', 'car_models', 'model_years', 'car_prices', 'reference_months']
    
    from sqlalchemy import inspect
    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())
    
    missing_tables = [table for table in required_tables if table not in existing_tables]
    
    if missing_tables:
        app.logger.critical(f"Database schema validation failed! Missing tables: {', '.join(missing_tables)}")
        raise RuntimeError(f"Database schema validation failed!")
    
    app.logger.info(f"Database schema validated: all {len(required_tables)} required tables exist")
```

### Rate Limiting
Prevents API abuse using Flask-Limiter:
```python
limiter = Limiter(
    app=app,
    key_func=lambda: request.headers.get('X-API-Key', 'anonymous')
)

# Default: 200 per day, 50 per hour
# Specific endpoints:
@limiter.limit("60 per hour")  # /api/economic-indicators
@limiter.limit("60 per minute")  # /health
```

### Input Validation
```python
def validate_positive_integer(value, param_name):
    """Validate integer parameters are positive."""
    if not isinstance(value, int) or value <= 0:
        raise ValueError(f"{param_name} must be positive integer")
```

### SQL Injection Protection
```python
def sanitize_like_pattern(pattern):
    """Escape special characters in LIKE patterns."""
    return pattern.replace('%', '\\%').replace('_', '\\_')
```

**Never construct raw SQL**:
```python
# WRONG - vulnerable to injection
query = f"SELECT * FROM brands WHERE name = '{user_input}'"

# CORRECT - use SQLAlchemy ORM
results = db.query(Brand).filter(Brand.brand_name == user_input).all()
```

## Session Management Pattern

### Database Session Lifecycle
```python
def get_db():
    """
    Create a new database session.
    
    Usage:
        db = get_db()
        try:
            results = db.query(...).all()
        finally:
            db.close()
    """
    return SessionLocal()
```

**Critical rules**:
- ALWAYS use try-finally
- ALWAYS close in finally block
- NEVER reuse sessions across requests
- Each request gets new session via `get_db()`

## Chart Data Pattern

### Multi-Vehicle Comparison
For vehicle comparison, structure is:

```python
{
    'vehicles': [
        {
            'name': 'Volkswagen Gol 2024 Flex',
            'dates': [...],
            'prices': [...],
            'labels': [...],
            'stats': {
                'current': 56789.00,
                'min': 54000.00,
                'max': 58000.00,
                'variation_percent': 5.2
            }
        },
        # ... up to 5 vehicles
    ]
}
```

## Default Car Selection Pattern

### Fuzzy Matching for Defaults
When loading default car, use ILIKE for fuzzy matching:

```python
default_brand = os.getenv('DEFAULT_BRAND', 'Volkswagen')
default_model = os.getenv('DEFAULT_MODEL', 'Gol')

# Find brand
brand = db.query(Brand).filter(
    Brand.brand_name.ilike(f'%{default_brand}%')
).first()

# Find model (matches any model containing "Gol")
model = db.query(CarModel).filter(
    CarModel.brand_id == brand.id,
    CarModel.model_name.ilike(f'%{default_model}%')
).first()
```

This allows flexible configuration like:
- `DEFAULT_MODEL=Gol` matches "Gol 1.0", "Gol GTI", etc.

## Theme Switching Pattern

### Dark/Light Mode
Theme preference stored in localStorage:

```javascript
// Get system preference
const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;

// Load saved preference or use system
const savedTheme = localStorage.getItem('theme') || (prefersDark ? 'dark' : 'light');

// Apply theme
document.documentElement.setAttribute('data-theme', savedTheme);

// Save preference
function toggleTheme() {
    const current = document.documentElement.getAttribute('data-theme');
    const next = current === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', next);
    localStorage.setItem('theme', next);
}
```

Charts automatically adapt via CSS variables.
