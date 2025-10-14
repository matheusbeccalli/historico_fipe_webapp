"""
FIPE Price Tracker - Main Flask Application

This webapp displays historical car price data from the FIPE database.
It uses cascading dropdowns and Plotly charts for interactive visualization.
"""

from flask import Flask, render_template, jsonify, request
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import json

# Import our database models and config
from webapp_database_models import (
    Base, Brand, CarModel, ModelYear, CarPrice, ReferenceMonth,
    format_month_portuguese
)
from config import get_config

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(get_config())

# Create database engine and session factory
engine = create_engine(app.config['DATABASE_URL'])
SessionLocal = sessionmaker(bind=engine)


def get_db():
    """
    Create a new database session.
    
    This is a helper function that creates a session and ensures
    it's properly closed after use (using try/finally pattern).
    """
    db = SessionLocal()
    try:
        return db
    except Exception as e:
        db.close()
        raise e


# ============================================================================
# ROUTES - Web Pages
# ============================================================================

@app.route('/')
def index():
    """
    Main page route.
    
    Renders the index.html template with the default car information.
    The template will then load the actual data via JavaScript API calls.
    """
    return render_template(
        'index.html',
        default_brand=app.config.get('DEFAULT_BRAND', 'Volkswagen'),
        default_model=app.config.get('DEFAULT_MODEL', 'Gol')
    )


# ============================================================================
# API ROUTES - Data Endpoints
# ============================================================================

@app.route('/api/brands', methods=['GET'])
def get_brands():
    """
    Get all available car brands.
    
    Returns:
        JSON array of brands: [
            {"id": 1, "name": "Volkswagen"},
            {"id": 2, "name": "Fiat"},
            ...
        ]
    """
    db = get_db()
    try:
        # Query all brands, ordered alphabetically
        brands = db.query(Brand).order_by(Brand.brand_name).all()
        
        # Convert to list of dictionaries for JSON response
        brands_list = [
            {"id": brand.id, "name": brand.brand_name}
            for brand in brands
        ]
        
        return jsonify(brands_list)
    
    finally:
        db.close()


@app.route('/api/models/<int:brand_id>', methods=['GET'])
def get_models(brand_id):
    """
    Get all models for a specific brand.
    
    Args:
        brand_id: The ID of the brand (from URL)
    
    Returns:
        JSON array of models for that brand
    """
    db = get_db()
    try:
        # Query models for the specified brand, ordered alphabetically
        models = (
            db.query(CarModel)
            .filter(CarModel.brand_id == brand_id)
            .order_by(CarModel.model_name)
            .all()
        )
        
        models_list = [
            {"id": model.id, "name": model.model_name}
            for model in models
        ]
        
        return jsonify(models_list)
    
    finally:
        db.close()


@app.route('/api/years/<int:model_id>', methods=['GET'])
def get_years(model_id):
    """
    Get all year/fuel combinations for a specific model.
    
    Args:
        model_id: The ID of the car model (from URL)
    
    Returns:
        JSON array of years (e.g., "2024 Gasolina", "2023 Flex")
    """
    db = get_db()
    try:
        # Query years for the specified model, ordered by description
        years = (
            db.query(ModelYear)
            .filter(ModelYear.car_model_id == model_id)
            .order_by(ModelYear.year_description.desc())  # Newest first
            .all()
        )
        
        years_list = [
            {"id": year.id, "description": year.year_description}
            for year in years
        ]
        
        return jsonify(years_list)
    
    finally:
        db.close()


@app.route('/api/months', methods=['GET'])
def get_months():
    """
    Get all available reference months from the database.
    
    Returns:
        JSON array of months in Portuguese format:
        [
            {"date": "2024-01-01", "label": "janeiro/2024"},
            {"date": "2024-02-01", "label": "fevereiro/2024"},
            ...
        ]
    """
    db = get_db()
    try:
        # Query all reference months, ordered chronologically
        months = (
            db.query(ReferenceMonth)
            .order_by(ReferenceMonth.month_date)
            .all()
        )
        
        months_list = [
            {
                "date": month.month_date.isoformat(),
                "label": format_month_portuguese(month.month_date)
            }
            for month in months
        ]
        
        return jsonify(months_list)
    
    finally:
        db.close()


@app.route('/api/chart-data', methods=['POST'])
def get_chart_data():
    """
    Get price history data for a specific car within a date range.
    
    Expects JSON POST body:
    {
        "year_id": 123,
        "start_date": "2023-01-01",
        "end_date": "2024-12-01"
    }
    
    Returns:
        JSON object with chart data and car information:
        {
            "car_info": {
                "brand": "Volkswagen",
                "model": "Gol 1.0",
                "year": "2024 Flex"
            },
            "data": [
                {"date": "2023-01-01", "price": 45000.00, "label": "janeiro/2023"},
                {"date": "2023-02-01", "price": 46000.00, "label": "fevereiro/2023"},
                ...
            ]
        }
    """
    db = get_db()
    try:
        # Get parameters from POST request body
        data = request.get_json()
        year_id = data.get('year_id')
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        
        # Validate required parameters
        if not year_id:
            return jsonify({"error": "year_id is required"}), 400
        
        # Convert date strings to datetime objects
        if start_date:
            start_date = datetime.fromisoformat(start_date)
        if end_date:
            end_date = datetime.fromisoformat(end_date)
        
        # Build the query
        # We join multiple tables to get all the information we need
        query = (
            db.query(
                ReferenceMonth.month_date,
                CarPrice.price,
                Brand.brand_name,
                CarModel.model_name,
                ModelYear.year_description
            )
            .join(CarPrice.reference_month)
            .join(CarPrice.model_year)
            .join(ModelYear.car_model)
            .join(CarModel.brand)
            .filter(ModelYear.id == year_id)
        )
        
        # Apply date filters if provided
        if start_date:
            query = query.filter(ReferenceMonth.month_date >= start_date)
        if end_date:
            query = query.filter(ReferenceMonth.month_date <= end_date)
        
        # Order by date (oldest to newest for the chart)
        query = query.order_by(ReferenceMonth.month_date)
        
        # Execute query
        results = query.all()
        
        # Check if we have data
        if not results:
            return jsonify({
                "error": "No data found for the selected car and date range"
            }), 404
        
        # Extract car information from first result
        car_info = {
            "brand": results[0].brand_name,
            "model": results[0].model_name,
            "year": results[0].year_description
        }
        
        # Format the price data for the chart
        chart_data = [
            {
                "date": result.month_date.isoformat(),
                "price": float(result.price),  # Ensure it's a float for JSON
                "label": format_month_portuguese(result.month_date)
            }
            for result in results
        ]
        
        return jsonify({
            "car_info": car_info,
            "data": chart_data
        })
    
    except Exception as e:
        # Log the error and return a user-friendly message
        app.logger.error(f"Error in get_chart_data: {str(e)}")
        return jsonify({"error": "An error occurred while fetching data"}), 500
    
    finally:
        db.close()


@app.route('/api/default-car', methods=['GET'])
def get_default_car():
    """
    Get the default car to display when the page loads.
    
    This finds a car based on the DEFAULT_BRAND and DEFAULT_MODEL
    settings in config.py.
    
    Returns:
        JSON object with default selections:
        {
            "brand_id": 1,
            "model_id": 123,
            "year_id": 456
        }
    """
    db = get_db()
    try:
        default_brand = app.config.get('DEFAULT_BRAND', 'Volkswagen')
        default_model = app.config.get('DEFAULT_MODEL', 'Gol')
        
        # Find the brand
        brand = (
            db.query(Brand)
            .filter(Brand.brand_name == default_brand)
            .first()
        )
        
        if not brand:
            # If default brand not found, just get the first brand
            brand = db.query(Brand).order_by(Brand.brand_name).first()
            if not brand:
                return jsonify({"error": "No brands found in database"}), 404
        
        # Find a model containing the default model name
        model = (
            db.query(CarModel)
            .filter(
                CarModel.brand_id == brand.id,
                CarModel.model_name.ilike(f'%{default_model}%')
            )
            .first()
        )
        
        if not model:
            # If default model not found, get the first model for this brand
            model = (
                db.query(CarModel)
                .filter(CarModel.brand_id == brand.id)
                .order_by(CarModel.model_name)
                .first()
            )
        
        if not model:
            return jsonify({"error": "No models found for default brand"}), 404
        
        # Find the most recent year for this model
        year = (
            db.query(ModelYear)
            .filter(ModelYear.car_model_id == model.id)
            .order_by(ModelYear.year_description.desc())
            .first()
        )
        
        if not year:
            return jsonify({"error": "No years found for default model"}), 404
        
        return jsonify({
            "brand_id": brand.id,
            "model_id": model.id,
            "year_id": year.id
        })
    
    finally:
        db.close()


# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({"error": "Not found"}), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return jsonify({"error": "Internal server error"}), 500


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

if __name__ == '__main__':
    # Run the Flask development server
    # Debug mode will auto-reload when you change code
    app.run(
        debug=True,
        host='127.0.0.1',  # Only accessible from your computer
        port=5000
    )
