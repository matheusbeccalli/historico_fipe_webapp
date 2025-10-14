# Examples

This folder contains example code and reference implementations for the FIPE Price Tracker webapp.

## Files

### [example_queries.py](example_queries.py)
A comprehensive collection of SQLAlchemy query examples demonstrating how to:
- Retrieve price history for specific vehicles
- Compare prices across multiple models
- Calculate brand statistics (avg, min, max prices)
- Generate market analytics
- Search and filter vehicles
- Create price distribution histograms
- Analyze fuel type pricing

**Categories of examples**:
1. **Price History Queries** - Track vehicle prices over time
2. **Brand/Model Analytics** - Statistics and comparisons by brand
3. **Market Analytics** - Market-wide insights and trends
4. **Search and Filter** - Query patterns for building search features

**Usage**:
```python
from examples.example_queries import get_price_history_by_model
from webapp_database_models import get_db_session

session = get_db_session()
try:
    history = get_price_history_by_model(
        session,
        brand_name="Volkswagen",
        model_name="Gol",
        year_description="2024 Flex"
    )
    for record in history:
        print(f"{record['month_date']}: R$ {record['price']:,.2f}")
finally:
    session.close()
```

**Note**: These queries are not currently used in the main webapp but are provided as:
- Learning resources for SQLAlchemy ORM patterns
- Reference implementations for future features
- Templates for custom analytics

## Adding Your Own Examples

When adding new example files:
1. Include detailed docstrings explaining the purpose
2. Provide usage examples in comments or docstrings
3. Follow the existing code style and patterns
4. Keep examples independent and self-contained
5. Update this README with a description of the new file

## Related Documentation

- [Database Schema](../docs/database_schema.md) - Understanding the data model
- [CLAUDE.md](../CLAUDE.md) - Database query patterns used in the webapp
- [webapp_database_models.py](../webapp_database_models.py) - ORM model definitions
