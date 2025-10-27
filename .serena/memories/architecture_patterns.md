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

This pattern appears in app.py around lines 244-266 and is fundamental to the application.

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

### Cascading Dropdown Pattern
The UI uses a progressive disclosure pattern:

**Flow**:
1. Page loads → Fetch brands → Populate brand dropdown
2. User selects brand → Fetch models for brand → Populate model dropdown
3. User selects model → Fetch years for model → Populate year dropdown
4. User selects year + date range → POST to `/api/chart-data` → Render chart

**Bidirectional filtering** (newer feature):
- Can select model OR year first
- The other dropdown adjusts automatically
- `/api/vehicle-options/<brand_id>` returns mappings for both directions

**Implementation in app.js**:
```javascript
async function loadBrands() {
    const response = await fetch('/api/brands', {
        headers: { 'X-API-Key': window.API_KEY }
    });
    const brands = await response.json();
    populateDropdown('brand-select', brands);
}

async function onBrandChange() {
    const brandId = document.getElementById('brand-select').value;
    const models = await loadModels(brandId);
    populateDropdown('model-select', models);
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

**Helper function** (webapp_database_models.py:387):
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

**Helper function** (webapp_database_models.py:341):
```python
def format_price_brl(price):
    """Format price as Brazilian Real."""
    pass
```

## Security Patterns

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

### CSRF Protection
```python
csrf = CSRFProtect(app)
# Automatically protects POST requests
```

### Rate Limiting
```python
limiter = Limiter(
    app=app,
    key_func=lambda: request.headers.get('X-API-Key', 'anonymous')
)

@limiter.limit("60 per minute")
def endpoint():
    pass
```

### Security Headers
```python
@app.after_request
def set_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    return response
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

### Chart Data Structure
Data sent to Plotly must have this format:

```python
chart_data = {
    'dates': ['2024-01-01', '2024-02-01', ...],
    'prices': [11520.00, 11800.00, ...],
    'labels': ['janeiro/2024', 'fevereiro/2024', ...]
}
```

**Implementation**:
```python
dates = []
prices = []
labels = []

for month_date, price in query.all():
    dates.append(month_date.isoformat())
    prices.append(price)
    labels.append(format_month_portuguese(month_date))

return jsonify({
    'dates': dates,
    'prices': prices,
    'labels': labels
})
```

### Multi-Vehicle Comparison
For vehicle comparison, structure is:

```python
{
    'vehicles': [
        {
            'name': 'Volkswagen Gol 2024 Flex',
            'dates': [...],
            'prices': [...],
            'labels': [...]
        },
        {
            'name': 'Fiat Uno 2024 Flex',
            'dates': [...],
            'prices': [...],
            'labels': [...]
        }
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
