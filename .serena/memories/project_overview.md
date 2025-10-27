# Project Overview

## Purpose
Flask web application for visualizing historical car price data from the Brazilian FIPE (Fundação Instituto de Pesquisas Econômicas) table. Provides interactive visualizations of vehicle price trends over time with multi-vehicle comparison and economic indicators integration.

## Key Features

### Analysis & Visualization
- Cascading dropdown vehicle selection (Brand → Model → Year)
- **Intelligent filtering** - shows only vehicles in latest FIPE table
- **Bidirectional filtering** - select model or year first, other adjusts automatically
- Interactive Plotly charts showing price evolution
- **Multi-vehicle comparison** - up to 5 vehicles on same graph with distinct colors
- Period selection (start/end month)
- Automatic statistics per vehicle (current price, min, max, variation %)
- **Economic indicators** - IPCA and CDI integrated into charts for context
- Absolute or **indexed (Base 100)** price visualization
- **Depreciation analysis** - market-wide statistics by brand/year

### Interface & Usability
- **Dark/light theme toggle** with persistence in localStorage
- Modern UI with Bootstrap 5 and premium design
- Dynamic updates without page reloads
- Responsive design for mobile and desktop

### Security & Performance
- **API key authentication** for endpoint protection
- **Content Security Policy (CSP)** with nonce-based script execution to prevent XSS
- **Rate limiting** to prevent API abuse
- **Production logging** with automatic rotation (10MB × 10 files)
- **Health check endpoint** for monitoring and load balancers
- **Database schema validation** on startup

### Infrastructure
- SQLite 3 for development (default)
- PostgreSQL for production (optional)
- Environment-based configuration via .env files

## Tech Stack

### Backend
- **Flask 3.0** - Web framework
- **SQLAlchemy 2.0** - ORM for database access
- **Python 3.8+**
- **python-dotenv 1.0.0** - Environment variable management
- **Flask-Limiter 3.5.0** - Rate limiting
- **Flask-WTF 1.2.1** - CSRF protection
- **requests 2.31.0** - HTTP requests for external APIs

### Frontend
- **Bootstrap 5.3** - CSS framework
- **Plotly.js 2.26** - Interactive charts
- **Vanilla JavaScript** - No additional dependencies

### Database
- **SQLite 3** - Development (default)
- **PostgreSQL** - Production (optional, requires psycopg2-binary)

## Architecture Pattern
Read-only database access pattern:
- Webapp queries pre-populated SQLite database
- Database populated by separate scraper tool (not included)
- All webapp operations are SELECT queries only
- Never performs INSERT, UPDATE, or DELETE operations
- Ensures data integrity and separation of concerns

## Database Schema
5-table normalized schema with relationships:
```
Brands (1:N) → CarModels (1:N) → ModelYears (1:N) → CarPrices
                                                       ↓ (N:1)
                                                ReferenceMonths
```

Full vehicle information requires joining all 5 tables.

## API Endpoints (11 total)

**Vehicle Data:**
1. GET /api/brands - List brands in latest FIPE table
2. GET /api/vehicle-options/<brand_id> - Models and years with bidirectional filtering
3. GET /api/months - All available reference months
4. GET /api/default-car - Default vehicle (with names + IDs)

**Price & History:**
5. POST /api/compare-vehicles - Multi-vehicle comparison (up to 5)
6. POST /api/price - Single price point lookup

**Economic & Market:**
8. POST /api/economic-indicators - IPCA and CDI data
9. POST /api/depreciation-analysis - Market depreciation statistics

**System:**
10. GET /health - Health check for monitoring
11. GET / - Main page (no auth required)

**Deprecated (Removed):**
- ~~GET /api/models/<brand_id>~~ - Replaced by /api/vehicle-options
- ~~GET /api/years/<model_id>~~ - Replaced by /api/vehicle-options

All API endpoints (except / and /health) require X-API-Key header authentication.

## Recent Improvements

### Security Hardening
- Content Security Policy (CSP) with nonce-based script execution
- Referrer-Policy header to prevent information leakage
- Rate limiting on all endpoints
- Production logging with rotation
- Database schema validation on startup
- Health check endpoint for monitoring

### Feature Additions
- Multi-vehicle comparison (up to 5 vehicles)
- Economic indicators integration (IPCA and CDI)
- Market-wide depreciation analysis
- Dark/light mode theme support
- Bidirectional filtering optimization

### Code Cleanup
- Removed 189 lines of deprecated code
- Consolidated vehicle data loading into single endpoint (/api/vehicle-options)
- Removed legacy /api/models and /api/years endpoints
- Removed unused JavaScript functions (loadModels, loadYears, displayCarInfo)
