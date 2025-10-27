# Code Style and Conventions

## Python Code Style

### General Guidelines
- **Python Version**: 3.8+
- **Code formatting**: Follow PEP 8 conventions
- **Line length**: Reasonable (no strict limit observed)
- **Indentation**: 4 spaces

### Naming Conventions
- **Functions**: `snake_case` (e.g., `get_db()`, `format_price_brl()`)
- **Classes**: `PascalCase` (e.g., `Brand`, `CarModel`, `DevelopmentConfig`)
- **Variables**: `snake_case` (e.g., `latest_month`, `brands_list`)
- **Constants**: `UPPER_CASE` (e.g., `VALID_API_KEYS`)
- **Private/internal**: Leading underscore not consistently used

### Docstrings
- Used extensively for classes and functions
- **Format**: Triple-quoted strings with description
- **Example**:
```python
def get_brands():
    """
    Get all available car brands that have models in the latest reference month.

    Returns:
        JSON array of brands: [
            {"id": 1, "name": "Volkswagen"},
            ...
        ]
    """
```

### Type Hints
- **Not used** in this project
- All functions lack type annotations
- SQLAlchemy Column types provide schema-level typing

### Comments
- Inline comments used to explain business logic
- Section dividers used in app.py for organizing routes
- Portuguese comments acceptable for domain-specific context

### Imports
- Standard library imports first
- Third-party imports second
- Local imports last
- Grouped with blank lines between groups
- Example:
```python
from datetime import datetime
from functools import wraps

from flask import Flask, jsonify
from sqlalchemy import create_engine

from config import get_config
```

## SQLAlchemy Patterns

### Model Definitions
```python
class Brand(Base):
    """
    Docstring describing the model.
    
    Attributes:
        id: Primary key
        brand_name: Description
    """
    __tablename__ = 'brands'
    
    id = Column(Integer, primary_key=True)
    brand_name = Column(String(100), nullable=False)
    
    # Relationships
    models = relationship("CarModel", back_populates="brand")
    
    def __repr__(self):
        return f"<Brand(brand_name='{self.brand_name}')>"
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization."""
        return {
            'id': self.id,
            'brand_name': self.brand_name
        }
```

### Query Patterns
- Always use SQLAlchemy ORM, never raw SQL strings
- Use `try-finally` blocks for session management
- Close sessions in `finally` block
```python
db = get_db()
try:
    results = db.query(Brand).filter(...).all()
    return jsonify(results)
finally:
    db.close()
```

### Complex Joins
- Chain joins explicitly
- Use relationship names when available
- Add comments for complex join chains
```python
brands = (
    db.query(Brand)
    .join(Brand.models)
    .join(CarModel.years)
    .join(ModelYear.prices)
    .filter(...)
    .all()
)
```

## Flask API Patterns

### Route Decorators
```python
@app.route('/api/endpoint', methods=['GET'])
@require_api_key
@limiter.limit("60 per minute")
def endpoint_name():
    pass
```

### Error Handling
- Return appropriate HTTP status codes:
  - 200: Success
  - 400: Bad request (missing parameters)
  - 404: Not found
  - 413: Payload too large
  - 429: Rate limit exceeded
  - 500: Server error
- Use `jsonify()` for JSON responses
- Include descriptive error messages

### Response Format
```python
return jsonify({
    'key': 'value',
    'data': []
})
```

## JavaScript Style (Frontend)

### Naming
- Functions: `camelCase` (e.g., `updateChart()`, `loadBrands()`)
- Variables: `camelCase`
- Constants: `UPPER_CASE` (e.g., `API_KEY`)

### Async Patterns
- Use `async/await` for API calls
- Handle errors with try-catch blocks

### DOM Manipulation
- Use `querySelector` and `getElementById`
- Vanilla JavaScript, no jQuery

## Configuration Management

### Environment Variables
- All configuration via `.env` file
- Never commit `.env` to git
- Use `.env.example` as template
- Access via `os.getenv()` in Python

### Sensitive Data
- API keys stored in environment variables
- Database passwords in `DATABASE_URL`
- Use secure random key generators

## Brazilian Localization

### Date Formatting
- Database: `YYYY-MM-DD` (ISO format)
- Display: `mês/ano` in Portuguese (e.g., "janeiro/2024")
- Use `format_month_portuguese()` helper

### Price Formatting
- Database: Float (e.g., 11520.00)
- Display: Brazilian Real format (e.g., "R$ 11.520,00")
- Use `format_price_brl()` helper

### Language
- Comments: English or Portuguese acceptable
- UI: Portuguese
- Docstrings: English
- Variable names: English
