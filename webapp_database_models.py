"""
Database models for FIPE webapp (read-only version)

This is a cleaned version of database_models.py optimized for webapp use.
It removes scraper-specific functionality and is designed for read-only access.

Usage in your webapp:
    from webapp_database_models import (
        get_db_session,
        ReferenceMonth, Brand, CarModel, ModelYear, CarPrice
    )

    session = get_db_session()
    # Perform queries...
    session.close()
"""

from sqlalchemy import create_engine, Column, Integer, String, Float, Date, ForeignKey, UniqueConstraint
from sqlalchemy.orm import declarative_base, relationship, sessionmaker, Session, joinedload
from datetime import datetime
from typing import Tuple
import os

Base = declarative_base()


# ============================================================================
# MODEL DEFINITIONS
# ============================================================================

class ReferenceMonth(Base):
    """
    Reference months for FIPE price data.

    Attributes:
        id: Primary key
        month_code: FIPE's internal code (e.g., "21" for Janeiro/2024)
        month_date: Date representation (first day of month)
        created_at: Record creation timestamp
        prices: Relationship to CarPrice records
    """
    __tablename__ = 'reference_months'

    id = Column(Integer, primary_key=True)
    month_code = Column(String(50), unique=True, nullable=False)
    month_date = Column(Date, nullable=False)
    created_at = Column(Date, default=datetime.now)

    # Relationships
    prices = relationship("CarPrice", back_populates="reference_month")

    def __repr__(self):
        return f"<ReferenceMonth(month_code='{self.month_code}', month_date='{self.month_date}')>"

    def to_dict(self):
        """Convert to dictionary for JSON serialization."""
        return {
            'id': self.id,
            'month_code': self.month_code,
            'month_date': self.month_date.isoformat(),
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Brand(Base):
    """
    Car brands/manufacturers.

    Attributes:
        id: Primary key
        brand_code: FIPE's internal brand code
        brand_name: Brand name (e.g., "Volkswagen", "Fiat")
        created_at: Record creation timestamp
        models: Relationship to CarModel records
    """
    __tablename__ = 'brands'

    id = Column(Integer, primary_key=True)
    brand_code = Column(String(50), unique=True, nullable=False)
    brand_name = Column(String(100), nullable=False)
    created_at = Column(Date, default=datetime.now)

    # Relationships
    models = relationship("CarModel", back_populates="brand")

    def __repr__(self):
        return f"<Brand(brand_name='{self.brand_name}')>"

    def to_dict(self):
        """Convert to dictionary for JSON serialization."""
        return {
            'id': self.id,
            'brand_code': self.brand_code,
            'brand_name': self.brand_name,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class CarModel(Base):
    """
    Car models within each brand.

    Attributes:
        id: Primary key
        brand_id: Foreign key to Brand
        model_code: FIPE's internal model code
        model_name: Model name (e.g., "Gol 1.0", "Civic EX")
        created_at: Record creation timestamp
        brand: Relationship to Brand
        years: Relationship to ModelYear records
    """
    __tablename__ = 'car_models'

    id = Column(Integer, primary_key=True)
    brand_id = Column(Integer, ForeignKey('brands.id'), nullable=False)
    model_code = Column(String(50), nullable=False)
    model_name = Column(String(200), nullable=False)
    created_at = Column(Date, default=datetime.now)

    # Constraints
    __table_args__ = (UniqueConstraint('brand_id', 'model_code', name='_brand_model_uc'),)

    # Relationships
    brand = relationship("Brand", back_populates="models")
    years = relationship("ModelYear", back_populates="car_model")

    def __repr__(self):
        return f"<CarModel(model_name='{self.model_name}')>"

    def to_dict(self, include_brand=False):
        """Convert to dictionary for JSON serialization."""
        data = {
            'id': self.id,
            'brand_id': self.brand_id,
            'model_code': self.model_code,
            'model_name': self.model_name,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
        if include_brand and self.brand:
            data['brand'] = self.brand.to_dict()
        return data


class ModelYear(Base):
    """
    Year and fuel type combinations for each car model.

    Attributes:
        id: Primary key
        car_model_id: Foreign key to CarModel
        year_code: FIPE's internal year code
        year_description: Year + fuel type (e.g., "2024 Gasolina", "2023 Flex")
        created_at: Record creation timestamp
        car_model: Relationship to CarModel
        prices: Relationship to CarPrice records
    """
    __tablename__ = 'model_years'

    id = Column(Integer, primary_key=True)
    car_model_id = Column(Integer, ForeignKey('car_models.id'), nullable=False)
    year_code = Column(String(50), nullable=False)
    year_description = Column(String(100), nullable=False)
    created_at = Column(Date, default=datetime.now)

    # Constraints
    __table_args__ = (UniqueConstraint('car_model_id', 'year_code', name='_model_year_uc'),)

    # Relationships
    car_model = relationship("CarModel", back_populates="years")
    prices = relationship("CarPrice", back_populates="model_year")

    def __repr__(self):
        return f"<ModelYear(year_description='{self.year_description}')>"

    def to_dict(self, include_model=False):
        """Convert to dictionary for JSON serialization."""
        data = {
            'id': self.id,
            'car_model_id': self.car_model_id,
            'year_code': self.year_code,
            'year_description': self.year_description,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
        if include_model and self.car_model:
            data['car_model'] = self.car_model.to_dict(include_brand=True)
        return data


class CarPrice(Base):
    """
    Actual price data linking reference months with vehicle configurations.

    This is the main table with scraped price data.

    Attributes:
        id: Primary key
        reference_month_id: Foreign key to ReferenceMonth
        model_year_id: Foreign key to ModelYear
        price: Price in BRL (Brazilian Real)
        fipe_code: FIPE code for this vehicle (e.g., "038003-2")
        vehicle_type: Vehicle category (optional)
        fuel_type: Fuel type (optional, usually in year_description)
        scraped_at: When this data was scraped
        reference_month: Relationship to ReferenceMonth
        model_year: Relationship to ModelYear
    """
    __tablename__ = 'car_prices'

    id = Column(Integer, primary_key=True)
    reference_month_id = Column(Integer, ForeignKey('reference_months.id'), nullable=False)
    model_year_id = Column(Integer, ForeignKey('model_years.id'), nullable=False)

    # Price information
    price = Column(Float, nullable=False)
    fipe_code = Column(String(50))

    # Additional information
    vehicle_type = Column(String(50))
    fuel_type = Column(String(50))

    # Metadata
    scraped_at = Column(Date, default=datetime.now)

    # Constraints
    __table_args__ = (UniqueConstraint('reference_month_id', 'model_year_id', name='_month_year_uc'),)

    # Relationships
    reference_month = relationship("ReferenceMonth", back_populates="prices")
    model_year = relationship("ModelYear", back_populates="prices")

    def __repr__(self):
        return f"<CarPrice(price={self.price}, fipe_code='{self.fipe_code}')>"

    def to_dict(self, include_details=False):
        """
        Convert to dictionary for JSON serialization.

        Args:
            include_details: If True, include full vehicle and month details
        """
        data = {
            'id': self.id,
            'reference_month_id': self.reference_month_id,
            'model_year_id': self.model_year_id,
            'price': self.price,
            'fipe_code': self.fipe_code,
            'vehicle_type': self.vehicle_type,
            'fuel_type': self.fuel_type,
            'scraped_at': self.scraped_at.isoformat() if self.scraped_at else None
        }

        if include_details:
            if self.reference_month:
                data['reference_month'] = self.reference_month.to_dict()
            if self.model_year:
                data['model_year'] = self.model_year.to_dict(include_model=True)

        return data


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def format_price_brl(price: float) -> str:
    """
    Format price in Brazilian Real format.

    Args:
        price: Price value (e.g., 11520.00)

    Returns:
        Formatted string (e.g., "R$ 11.520,00")
    """
    # Convert to Brazilian format: thousands separator = . , decimal separator = ,
    formatted = f"{price:,.2f}"
    formatted = formatted.replace(',', 'TEMP').replace('.', ',').replace('TEMP', '.')
    return f"R$ {formatted}"


def format_month_portuguese(date_obj: datetime) -> str:
    """
    Format datetime to Portuguese month string.

    Args:
        date_obj: datetime object

    Returns:
        String like "janeiro/2024" or "dezembro/2025"
    """
    months_pt = [
        'janeiro', 'fevereiro', 'março', 'abril', 'maio', 'junho',
        'julho', 'agosto', 'setembro', 'outubro', 'novembro', 'dezembro'
    ]

    month_name = months_pt[date_obj.month - 1]
    return f"{month_name}/{date_obj.year}"


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    print("FIPE Database Models for Webapp")
    print("=" * 50)

    # Create session (using the same pattern as app.py)
    database_url = os.getenv('DATABASE_URL', 'sqlite:///fipe_data.db')
    engine = create_engine(database_url, echo=False)
    SessionMaker = sessionmaker(bind=engine)
    session = SessionMaker()

    try:
        # Example 1: Count records
        print("\n1. Database Statistics:")
        print(f"   Brands: {session.query(Brand).count()}")
        print(f"   Models: {session.query(CarModel).count()}")
        print(f"   Model Years: {session.query(ModelYear).count()}")
        print(f"   Price Records: {session.query(CarPrice).count()}")

        # Example 2: Get a sample price with full details
        print("\n2. Sample Price Record (with details):")
        price = (
            session.query(CarPrice)
            .options(
                joinedload(CarPrice.reference_month),
                joinedload(CarPrice.model_year).joinedload(ModelYear.car_model).joinedload(CarModel.brand)
            )
            .first()
        )

        if price:
            print(f"   Brand: {price.model_year.car_model.brand.brand_name}")
            print(f"   Model: {price.model_year.car_model.model_name}")
            print(f"   Year: {price.model_year.year_description}")
            print(f"   Month: {format_month_portuguese(price.reference_month.month_date)}")
            print(f"   Price: {format_price_brl(price.price)}")
            print(f"   FIPE Code: {price.fipe_code}")

        # Example 3: Convert to dict for JSON API
        print("\n3. JSON Serialization Example:")
        if price:
            import json
            price_dict = price.to_dict(include_details=True)
            print(json.dumps(price_dict, indent=2, default=str))

    finally:
        session.close()

    print("\n" + "=" * 50)
    print("Ready to use in your webapp!")
    print("Import with: from webapp_database_models import Brand, CarModel, ModelYear, etc.")
