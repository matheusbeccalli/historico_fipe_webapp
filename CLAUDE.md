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

The application uses environment-aware configuration in `config.py`:
- `DevelopmentConfig` (default) - SQLite database
- `ProductionConfig` - PostgreSQL database
- Controlled via `FLASK_ENV` environment variable

**Important**: The database path in `config.py:27` is hardcoded and must be updated when working in different environments.

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

### Core Application Files

- **app.py** (413 lines) - Main Flask application with all routes and API endpoints
- **config.py** (74 lines) - Environment-based configuration system
- **webapp_database_models.py** (457 lines) - SQLAlchemy ORM models with relationships

### Frontend Files

- **templates/index.html** - Single-page application template
- **static/js/app.js** - Handles all API calls, dropdown cascading, and chart rendering
- **static/css/style.css** - Custom styles

### Utility Files

- **example_queries.py** (586 lines) - Contains complex SQLAlchemy query examples for analytics features (not currently used in webapp but useful for reference)

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

The application loads with a default car (configured in config.py:36-37). The `/api/default-car` endpoint (app.py:308) uses fuzzy matching with `ILIKE` to find models containing the configured model name.

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

### Extending the Chart

The chart data format is defined in `/api/chart-data` (app.py:197-305). Each data point must include:
- `date` (ISO format string)
- `price` (float)
- `label` (Portuguese formatted date)

### Changing the Database

To switch from SQLite to PostgreSQL:
1. Set `DATABASE_URL` environment variable to PostgreSQL connection string
2. Install `psycopg2-binary` (uncomment line 14 in requirements.txt)
3. Set `FLASK_ENV=production`

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
