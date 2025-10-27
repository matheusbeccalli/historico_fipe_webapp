# Project Overview

## Purpose
Flask web application for visualizing historical car price data from the Brazilian FIPE (Fundação Instituto de Pesquisas Econômicas) table. Provides interactive visualizations of vehicle price trends over time using cascading dropdowns and Plotly charts.

## Key Features
- Cascading dropdown vehicle selection (Brand → Model → Year)
- Intelligent filtering - shows only vehicles in latest FIPE table
- Bidirectional filtering - select model or year first
- Interactive Plotly charts showing price evolution
- Comparison of up to 5 vehicles on same graph
- Period selection (start/end month)
- Automatic statistics (current price, min, max, variation)
- Economic indicators (IPCA and CDI) for context
- Absolute or indexed (Base 100) price visualization
- Dark/light theme toggle with persistence
- API key authentication for endpoint protection
- Modern UI with Bootstrap 5

## Tech Stack

### Backend
- **Flask 3.0** - Web framework
- **SQLAlchemy 2.0** - ORM for database access
- **Python 3.8+**
- **python-dotenv 1.0.0** - Environment variable management
- **Flask-Limiter 3.5.0** - Rate limiting
- **Flask-WTF 1.2.1** - CSRF protection
- **requests 2.31.0** - HTTP requests

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

## Database Schema
5-table normalized schema with relationships:
```
Brands (1:N) → CarModels (1:N) → ModelYears (1:N) → CarPrices
                                                       ↓ (N:1)
                                                ReferenceMonths
```

Full vehicle information requires joining all 5 tables.
