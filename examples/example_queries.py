"""
Example SQLAlchemy queries for FIPE webapp

This file contains ready-to-use queries for common visualizations and analytics.
All queries use SQLAlchemy ORM for type safety and ease of use.

Usage:
    from example_queries import get_price_history, compare_brands, etc.
"""

from sqlalchemy import func, desc, asc
from sqlalchemy.orm import Session, joinedload
from database_models import (
    CarPrice, ModelYear, CarModel, Brand, ReferenceMonth,
    create_database
)
from typing import List, Dict, Optional
from datetime import datetime


def get_session() -> Session:
    """Helper function to create a database session."""
    _, SessionMaker = create_database()
    return SessionMaker()


# ============================================================================
# 1. PRICE HISTORY QUERIES
# ============================================================================

def get_price_history_by_model(
    session: Session,
    brand_name: str,
    model_name: str,
    year_description: str
) -> List[Dict]:
    """
    Get price history for a specific car model over all available months.

    Use case: Line chart showing price trends over time

    Args:
        session: SQLAlchemy session
        brand_name: e.g., "Volkswagen"
        model_name: e.g., "Gol 1.0"
        year_description: e.g., "2024 Flex"

    Returns:
        List of dicts with keys: month_date, price, fipe_code
    """
    results = (
        session.query(
            ReferenceMonth.month_date,
            CarPrice.price,
            CarPrice.fipe_code
        )
        .join(CarPrice.reference_month)
        .join(CarPrice.model_year)
        .join(ModelYear.car_model)
        .join(CarModel.brand)
        .filter(
            Brand.brand_name == brand_name,
            CarModel.model_name.like(f"%{model_name}%"),
            ModelYear.year_description == year_description
        )
        .order_by(ReferenceMonth.month_date)
        .all()
    )

    return [
        {
            'month_date': r.month_date,
            'price': r.price,
            'fipe_code': r.fipe_code
        }
        for r in results
    ]


def get_price_comparison_over_time(
    session: Session,
    model_configs: List[tuple],
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
) -> Dict[str, List[Dict]]:
    """
    Compare price history of multiple car configurations.

    Use case: Multi-line chart comparing different models/years

    Args:
        session: SQLAlchemy session
        model_configs: List of (brand_name, model_name, year_description) tuples
        start_date: Optional start date filter
        end_date: Optional end date filter

    Returns:
        Dict mapping model identifier to list of {month_date, price}

    Example:
        configs = [
            ("Volkswagen", "Gol 1.0", "2024 Flex"),
            ("Fiat", "Uno", "2024 Flex")
        ]
        comparison = get_price_comparison_over_time(session, configs)
    """
    result = {}

    for brand_name, model_name, year_desc in model_configs:
        query = (
            session.query(
                ReferenceMonth.month_date,
                CarPrice.price
            )
            .join(CarPrice.reference_month)
            .join(CarPrice.model_year)
            .join(ModelYear.car_model)
            .join(CarModel.brand)
            .filter(
                Brand.brand_name == brand_name,
                CarModel.model_name.like(f"%{model_name}%"),
                ModelYear.year_description == year_desc
            )
        )

        if start_date:
            query = query.filter(ReferenceMonth.month_date >= start_date)
        if end_date:
            query = query.filter(ReferenceMonth.month_date <= end_date)

        query = query.order_by(ReferenceMonth.month_date)

        key = f"{brand_name} {model_name} {year_desc}"
        result[key] = [
            {'month_date': r.month_date, 'price': r.price}
            for r in query.all()
        ]

    return result


# ============================================================================
# 2. BRAND/MODEL ANALYTICS
# ============================================================================

def get_most_expensive_by_brand(
    session: Session,
    month_date: datetime,
    limit: int = 10
) -> List[Dict]:
    """
    Get most expensive cars for each brand in a specific month.

    Use case: Bar chart of premium models by brand

    Args:
        session: SQLAlchemy session
        month_date: Month to analyze
        limit: Number of brands to return

    Returns:
        List of dicts with: brand_name, model_name, year_description, price
    """
    # Subquery to get max price per brand
    subquery = (
        session.query(
            Brand.id.label('brand_id'),
            func.max(CarPrice.price).label('max_price')
        )
        .join(Brand.models)
        .join(CarModel.years)
        .join(ModelYear.prices)
        .join(CarPrice.reference_month)
        .filter(ReferenceMonth.month_date == month_date)
        .group_by(Brand.id)
        .subquery()
    )

    # Main query to get full details
    results = (
        session.query(
            Brand.brand_name,
            CarModel.model_name,
            ModelYear.year_description,
            CarPrice.price
        )
        .join(CarModel.brand)
        .join(ModelYear.car_model)
        .join(CarPrice.model_year)
        .join(CarPrice.reference_month)
        .join(
            subquery,
            (Brand.id == subquery.c.brand_id) &
            (CarPrice.price == subquery.c.max_price)
        )
        .filter(ReferenceMonth.month_date == month_date)
        .order_by(desc(CarPrice.price))
        .limit(limit)
        .all()
    )

    return [
        {
            'brand_name': r.brand_name,
            'model_name': r.model_name,
            'year_description': r.year_description,
            'price': r.price
        }
        for r in results
    ]


def get_cheapest_cars_in_month(
    session: Session,
    month_date: datetime,
    limit: int = 20
) -> List[Dict]:
    """
    Get cheapest cars available in a specific month.

    Use case: Budget car recommendations, entry-level market analysis

    Returns:
        List of dicts with full car details and price
    """
    results = (
        session.query(
            Brand.brand_name,
            CarModel.model_name,
            ModelYear.year_description,
            CarPrice.price,
            CarPrice.fipe_code
        )
        .join(CarModel.brand)
        .join(ModelYear.car_model)
        .join(CarPrice.model_year)
        .join(CarPrice.reference_month)
        .filter(ReferenceMonth.month_date == month_date)
        .order_by(asc(CarPrice.price))
        .limit(limit)
        .all()
    )

    return [
        {
            'brand_name': r.brand_name,
            'model_name': r.model_name,
            'year_description': r.year_description,
            'price': r.price,
            'fipe_code': r.fipe_code
        }
        for r in results
    ]


def get_brand_statistics(
    session: Session,
    month_date: datetime,
    brand_name: str
) -> Dict:
    """
    Get comprehensive statistics for a brand in a specific month.

    Use case: Brand profile page, market analysis

    Returns:
        Dict with: total_models, avg_price, min_price, max_price, price_range
    """
    stats = (
        session.query(
            func.count(CarPrice.id).label('total_models'),
            func.avg(CarPrice.price).label('avg_price'),
            func.min(CarPrice.price).label('min_price'),
            func.max(CarPrice.price).label('max_price')
        )
        .join(CarPrice.model_year)
        .join(ModelYear.car_model)
        .join(CarModel.brand)
        .join(CarPrice.reference_month)
        .filter(
            Brand.brand_name == brand_name,
            ReferenceMonth.month_date == month_date
        )
        .first()
    )

    return {
        'brand_name': brand_name,
        'month_date': month_date,
        'total_models': stats.total_models,
        'avg_price': float(stats.avg_price) if stats.avg_price else 0,
        'min_price': float(stats.min_price) if stats.min_price else 0,
        'max_price': float(stats.max_price) if stats.max_price else 0,
        'price_range': float(stats.max_price - stats.min_price) if stats.max_price else 0
    }


# ============================================================================
# 3. MARKET ANALYTICS
# ============================================================================

def get_price_distribution(
    session: Session,
    month_date: datetime,
    bucket_size: float = 10000.0
) -> List[Dict]:
    """
    Get price distribution histogram data.

    Use case: Histogram showing market price distribution

    Args:
        session: SQLAlchemy session
        month_date: Month to analyze
        bucket_size: Price range for each bucket (default: R$ 10,000)

    Returns:
        List of dicts with: price_range, count
    """
    # Get all prices
    prices = (
        session.query(CarPrice.price)
        .join(CarPrice.reference_month)
        .filter(ReferenceMonth.month_date == month_date)
        .all()
    )

    # Create histogram buckets
    if not prices:
        return []

    price_list = [p.price for p in prices]
    min_price = min(price_list)
    max_price = max(price_list)

    buckets = {}
    for price in price_list:
        bucket = int(price // bucket_size) * bucket_size
        buckets[bucket] = buckets.get(bucket, 0) + 1

    return [
        {
            'price_range': f"R$ {bucket:,.0f} - R$ {bucket + bucket_size:,.0f}",
            'price_min': bucket,
            'price_max': bucket + bucket_size,
            'count': count
        }
        for bucket, count in sorted(buckets.items())
    ]


def get_fuel_type_comparison(
    session: Session,
    month_date: datetime
) -> List[Dict]:
    """
    Compare average prices by fuel type.

    Use case: Bar chart showing fuel type price comparison
    Note: Fuel type is extracted from year_description field

    Returns:
        List of dicts with: fuel_type, avg_price, count
    """
    results = (
        session.query(
            ModelYear.year_description,
            func.avg(CarPrice.price).label('avg_price'),
            func.count(CarPrice.id).label('count')
        )
        .join(CarPrice.model_year)
        .join(CarPrice.reference_month)
        .filter(ReferenceMonth.month_date == month_date)
        .group_by(ModelYear.year_description)
        .all()
    )

    # Extract fuel type from year_description (e.g., "2024 Gasolina" -> "Gasolina")
    fuel_stats = {}
    for r in results:
        parts = r.year_description.split()
        fuel_type = parts[-1] if len(parts) > 1 else 'Unknown'

        if fuel_type not in fuel_stats:
            fuel_stats[fuel_type] = {'total_price': 0, 'count': 0}

        fuel_stats[fuel_type]['total_price'] += r.avg_price * r.count
        fuel_stats[fuel_type]['count'] += r.count

    return [
        {
            'fuel_type': fuel_type,
            'avg_price': stats['total_price'] / stats['count'],
            'count': stats['count']
        }
        for fuel_type, stats in sorted(fuel_stats.items())
    ]


def get_market_leaders(
    session: Session,
    month_date: datetime,
    limit: int = 10
) -> List[Dict]:
    """
    Get brands with most models in the market.

    Use case: Market share analysis, brand diversity comparison

    Returns:
        List of dicts with: brand_name, model_count, avg_price
    """
    results = (
        session.query(
            Brand.brand_name,
            func.count(func.distinct(CarModel.id)).label('model_count'),
            func.avg(CarPrice.price).label('avg_price')
        )
        .join(Brand.models)
        .join(CarModel.years)
        .join(ModelYear.prices)
        .join(CarPrice.reference_month)
        .filter(ReferenceMonth.month_date == month_date)
        .group_by(Brand.id)
        .order_by(desc('model_count'))
        .limit(limit)
        .all()
    )

    return [
        {
            'brand_name': r.brand_name,
            'model_count': r.model_count,
            'avg_price': float(r.avg_price)
        }
        for r in results
    ]


# ============================================================================
# 4. SEARCH AND FILTER
# ============================================================================

def search_models(
    session: Session,
    search_term: str,
    month_date: Optional[datetime] = None,
    limit: int = 50
) -> List[Dict]:
    """
    Search for car models by name.

    Use case: Autocomplete, search functionality

    Args:
        session: SQLAlchemy session
        search_term: Search string to match model names
        month_date: Optional - include price for specific month
        limit: Maximum results to return

    Returns:
        List of dicts with car details and optional price
    """
    query = (
        session.query(
            Brand.brand_name,
            CarModel.model_name,
            ModelYear.year_description,
            CarPrice.price if month_date else None,
            CarPrice.fipe_code if month_date else None
        )
        .join(CarModel.brand)
        .join(ModelYear.car_model)
    )

    if month_date:
        query = (
            query
            .join(CarPrice.model_year)
            .join(CarPrice.reference_month)
            .filter(ReferenceMonth.month_date == month_date)
        )

    query = (
        query
        .filter(
            (CarModel.model_name.ilike(f"%{search_term}%")) |
            (Brand.brand_name.ilike(f"%{search_term}%"))
        )
        .order_by(Brand.brand_name, CarModel.model_name)
        .limit(limit)
    )

    results = query.all()

    return [
        {
            'brand_name': r.brand_name,
            'model_name': r.model_name,
            'year_description': r.year_description,
            'price': r.price if month_date else None,
            'fipe_code': r.fipe_code if month_date else None
        }
        for r in results
    ]


def get_available_brands(session: Session) -> List[str]:
    """Get list of all available brands."""
    results = session.query(Brand.brand_name).order_by(Brand.brand_name).all()
    return [r.brand_name for r in results]


def get_models_by_brand(session: Session, brand_name: str) -> List[str]:
    """Get all models for a specific brand."""
    results = (
        session.query(CarModel.model_name)
        .join(CarModel.brand)
        .filter(Brand.brand_name == brand_name)
        .order_by(CarModel.model_name)
        .all()
    )
    return [r.model_name for r in results]


def get_available_months(session: Session) -> List[datetime]:
    """Get all available reference months."""
    results = (
        session.query(ReferenceMonth.month_date)
        .order_by(ReferenceMonth.month_date)
        .all()
    )
    return [r.month_date for r in results]


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    # Create session
    session = get_session()

    try:
        # Example 1: Get price history
        print("=== Example 1: Price History ===")
        history = get_price_history_by_model(
            session,
            brand_name="Acura",
            model_name="Integra",
            year_description="1992 Gasolina"
        )
        for record in history[:5]:
            print(f"{record['month_date']}: R$ {record['price']:,.2f}")

        # Example 2: Get cheapest cars
        print("\n=== Example 2: Cheapest Cars (January 2024) ===")
        from datetime import date
        cheapest = get_cheapest_cars_in_month(
            session,
            month_date=date(2024, 1, 1),
            limit=5
        )
        for car in cheapest:
            print(f"{car['brand_name']} {car['model_name']} {car['year_description']}: R$ {car['price']:,.2f}")

        # Example 3: Brand statistics
        print("\n=== Example 3: Brand Statistics ===")
        stats = get_brand_statistics(
            session,
            month_date=date(2024, 1, 1),
            brand_name="Acura"
        )
        print(f"Total models: {stats['total_models']}")
        print(f"Average price: R$ {stats['avg_price']:,.2f}")
        print(f"Price range: R$ {stats['min_price']:,.2f} - R$ {stats['max_price']:,.2f}")

        # Example 4: Search
        print("\n=== Example 4: Search 'Gol' ===")
        results = search_models(session, "Gol", limit=5)
        for car in results:
            print(f"{car['brand_name']} {car['model_name']} {car['year_description']}")

    finally:
        session.close()
