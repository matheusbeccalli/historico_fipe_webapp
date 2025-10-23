"""
FIPE Price Tracker - Main Flask Application

This webapp displays historical car price data from the FIPE database.
It uses cascading dropdowns and Plotly charts for interactive visualization.
"""

from flask import Flask, render_template, jsonify, request, session
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import json
import requests
from functools import reduce, wraps

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

# Parse allowed API keys from config and store as a set for fast lookup
VALID_API_KEYS = set()
api_keys_str = app.config.get('API_KEYS_ALLOWED', '')
if api_keys_str:
    VALID_API_KEYS = {key.strip() for key in api_keys_str.split(',') if key.strip()}


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


def get_latest_reference_month(db):
    """
    Get the most recent reference month date from the database.

    Args:
        db: Database session

    Returns:
        datetime.date: The most recent month_date, or None if no data exists
    """
    latest_month = (
        db.query(ReferenceMonth.month_date)
        .order_by(ReferenceMonth.month_date.desc())
        .first()
    )
    return latest_month[0] if latest_month else None


def require_api_key(f):
    """
    Decorator to require authentication via session (for web browsers) or API key (for external clients).

    Authentication methods (checked in order):
    1. Session-based auth (for web browsers) - checks for 'authenticated' in session
    2. API key auth (for external clients) - checks X-API-Key header

    Returns 401 Unauthorized if neither authentication method succeeds.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check for session-based authentication first (web browsers)
        if session.get('authenticated'):
            app.logger.debug(f'Session access granted: endpoint={request.path} method={request.method} ip={request.remote_addr}')
            return f(*args, **kwargs)

        # Fall back to API key authentication (external clients)
        api_key = request.headers.get('X-API-Key')

        # If no API keys are configured, allow access (for development)
        if not VALID_API_KEYS:
            app.logger.warning('No API keys configured - allowing access without authentication')
            return f(*args, **kwargs)

        # Check if API key is provided
        if not api_key:
            return jsonify({
                'error': 'Authentication required',
                'message': 'Please authenticate via session or provide an API key in the X-API-Key header'
            }), 401

        # Check if API key is valid
        if api_key not in VALID_API_KEYS:
            app.logger.warning(f'Invalid API key attempt: {api_key[:8]}... from {request.remote_addr} accessing {request.path}')
            return jsonify({
                'error': 'Invalid API key',
                'message': 'The provided API key is not valid'
            }), 401

        # API key is valid, log successful access and proceed with the request
        app.logger.info(f'API access granted: key={api_key[:8]}... endpoint={request.path} method={request.method} ip={request.remote_addr}')
        return f(*args, **kwargs)

    return decorated_function


# ============================================================================
# ROUTES - Web Pages
# ============================================================================

@app.route('/')
def index():
    """
    Main page route.

    Renders the index.html template with the default car information.
    The template will then load the actual data via JavaScript API calls.

    This route establishes an authenticated session for the web browser,
    eliminating the need to expose API keys in the HTML source code.
    """
    # Create an authenticated session for web browser access
    session['authenticated'] = True
    session.permanent = True  # Use permanent session (configurable lifetime)

    app.logger.info(f'New web session created from {request.remote_addr}')

    return render_template(
        'index.html',
        default_brand=app.config.get('DEFAULT_BRAND', 'Volkswagen'),
        default_model=app.config.get('DEFAULT_MODEL', 'Gol')
        # API key is NO LONGER passed to the template
    )


# ============================================================================
# API ROUTES - Data Endpoints
# ============================================================================

@app.route('/api/brands', methods=['GET'])
@require_api_key
def get_brands():
    """
    Get all available car brands that have models in the latest reference month.

    This ensures we only show brands that are currently available in FIPE's
    most recent data, not historical brands that may have been discontinued.

    Returns:
        JSON array of brands: [
            {"id": 1, "name": "Volkswagen"},
            {"id": 2, "name": "Fiat"},
            ...
        ]
    """
    db = get_db()
    try:
        # Get the most recent reference month
        latest_month = get_latest_reference_month(db)

        if not latest_month:
            return jsonify([])

        # Query brands that have at least one model with prices in the latest month
        # Join through: brands → car_models → model_years → car_prices → reference_months
        brands = (
            db.query(Brand)
            .join(Brand.models)
            .join(CarModel.years)
            .join(ModelYear.prices)
            .join(CarPrice.reference_month)
            .filter(ReferenceMonth.month_date == latest_month)
            .distinct()
            .order_by(Brand.brand_name)
            .all()
        )

        # Convert to list of dictionaries for JSON response
        brands_list = [
            {"id": brand.id, "name": brand.brand_name}
            for brand in brands
        ]

        return jsonify(brands_list)

    finally:
        db.close()


@app.route('/api/models/<int:brand_id>', methods=['GET'])
@require_api_key
def get_models(brand_id):
    """
    Get all models for a specific brand that are available in the latest reference month.

    This ensures we only show models that are currently available in FIPE's
    most recent data for this brand.

    Args:
        brand_id: The ID of the brand (from URL)

    Returns:
        JSON array of models for that brand
    """
    db = get_db()
    try:
        # Get the most recent reference month
        latest_month = get_latest_reference_month(db)

        if not latest_month:
            return jsonify([])

        # Query models for this brand that have prices in the latest month
        # Join through: car_models → model_years → car_prices → reference_months
        models = (
            db.query(CarModel)
            .join(CarModel.years)
            .join(ModelYear.prices)
            .join(CarPrice.reference_month)
            .filter(
                CarModel.brand_id == brand_id,
                ReferenceMonth.month_date == latest_month
            )
            .distinct()
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
@require_api_key
def get_years(model_id):
    """
    Get all year/fuel combinations for a specific model that are available
    in the latest reference month.

    This ensures we only show years that are currently available in FIPE's
    most recent data for this model.

    Args:
        model_id: The ID of the car model (from URL)

    Returns:
        JSON array of years (e.g., "2024 Gasolina", "2023 Flex")
    """
    db = get_db()
    try:
        # Get the most recent reference month
        latest_month = get_latest_reference_month(db)

        if not latest_month:
            return jsonify([])

        # Query years for this model that have prices in the latest month
        # Join through: model_years → car_prices → reference_months
        years = (
            db.query(ModelYear)
            .join(ModelYear.prices)
            .join(CarPrice.reference_month)
            .filter(
                ModelYear.car_model_id == model_id,
                ReferenceMonth.month_date == latest_month
            )
            .distinct()
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


@app.route('/api/vehicle-options/<int:brand_id>', methods=['GET'])
@require_api_key
def get_vehicle_options(brand_id):
    """
    Get all models and years for a brand with cross-filtering mappings,
    filtered to only show data available in the latest reference month.

    This endpoint supports bidirectional filtering: users can select either
    model or year first, and the other dropdown will filter accordingly.

    Args:
        brand_id: The ID of the brand (from URL)

    Returns:
        JSON object with:
        {
            "models": [{"id": 1, "name": "Gol"}, ...],
            "year_descriptions": ["2024 Flex", "2023 Diesel", ...],
            "model_to_years": {
                "1": ["2024 Flex", "2023 Flex"],
                "2": ["2024 Diesel"]
            },
            "year_to_models": {
                "2024 Flex": [1, 3, 5],
                "2023 Diesel": [2]
            },
            "model_year_lookup": {
                "1": {"2024 Flex": 10, "2023 Flex": 11},
                "2": {"2024 Diesel": 20}
            }
        }
    """
    db = get_db()
    try:
        # Get the most recent reference month
        latest_month = get_latest_reference_month(db)

        if not latest_month:
            return jsonify({
                "models": [],
                "year_descriptions": [],
                "model_to_years": {},
                "year_to_models": {},
                "model_year_lookup": {}
            })

        # Get all models for this brand that have prices in the latest month
        models = (
            db.query(CarModel)
            .join(CarModel.years)
            .join(ModelYear.prices)
            .join(CarPrice.reference_month)
            .filter(
                CarModel.brand_id == brand_id,
                ReferenceMonth.month_date == latest_month
            )
            .distinct()
            .order_by(CarModel.model_name)
            .all()
        )

        # Build models list
        models_list = [
            {"id": model.id, "name": model.model_name}
            for model in models
        ]

        # Get all ModelYear records for this brand that have prices in the latest month
        model_years = (
            db.query(ModelYear)
            .join(ModelYear.car_model)
            .join(ModelYear.prices)
            .join(CarPrice.reference_month)
            .filter(
                CarModel.brand_id == brand_id,
                ReferenceMonth.month_date == latest_month
            )
            .distinct()
            .order_by(ModelYear.year_description.desc())
            .all()
        )

        # Build unique year descriptions
        year_descriptions = sorted(
            list(set(my.year_description for my in model_years)),
            reverse=True  # Newest first
        )

        # Build model_to_years mapping: {model_id: [year_desc1, year_desc2]}
        model_to_years = {}
        for my in model_years:
            model_id_str = str(my.car_model_id)
            if model_id_str not in model_to_years:
                model_to_years[model_id_str] = []
            if my.year_description not in model_to_years[model_id_str]:
                model_to_years[model_id_str].append(my.year_description)

        # Sort year descriptions within each model (newest first)
        for model_id_str in model_to_years:
            model_to_years[model_id_str] = sorted(
                model_to_years[model_id_str],
                reverse=True
            )

        # Build year_to_models mapping: {year_desc: [model_id1, model_id2]}
        year_to_models = {}
        for my in model_years:
            if my.year_description not in year_to_models:
                year_to_models[my.year_description] = []
            if my.car_model_id not in year_to_models[my.year_description]:
                year_to_models[my.year_description].append(my.car_model_id)

        # Sort model IDs within each year description
        for year_desc in year_to_models:
            year_to_models[year_desc] = sorted(year_to_models[year_desc])

        # Build model_year_lookup: {model_id: {year_desc: year_id}}
        model_year_lookup = {}
        for my in model_years:
            model_id_str = str(my.car_model_id)
            if model_id_str not in model_year_lookup:
                model_year_lookup[model_id_str] = {}
            model_year_lookup[model_id_str][my.year_description] = my.id

        return jsonify({
            "models": models_list,
            "year_descriptions": year_descriptions,
            "model_to_years": model_to_years,
            "year_to_models": year_to_models,
            "model_year_lookup": model_year_lookup
        })

    finally:
        db.close()


@app.route('/api/months', methods=['GET'])
@require_api_key
def get_months():
    """
    Get all available reference months from the database.

    Optional query parameter:
        year_id: Filter months to only those available for this specific vehicle (ModelYear.id)

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
        year_id = request.args.get('year_id', type=int)

        if year_id:
            # Query months that have price data for this specific vehicle
            months = (
                db.query(ReferenceMonth)
                .join(CarPrice.reference_month)
                .filter(CarPrice.model_year_id == year_id)
                .order_by(ReferenceMonth.month_date)
                .distinct()
                .all()
            )
        else:
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
@require_api_key
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


@app.route('/api/compare-vehicles', methods=['POST'])
@require_api_key
def compare_vehicles():
    """
    Get price history data for multiple vehicles for comparison.

    Expects JSON POST body:
    {
        "vehicle_ids": [123, 456, 789],  # Array of ModelYear IDs
        "start_date": "2023-01-01",
        "end_date": "2024-12-01"
    }

    Returns:
        JSON object with data for each vehicle:
        {
            "vehicles": [
                {
                    "id": 123,
                    "brand": "Volkswagen",
                    "model": "Gol 1.0",
                    "year": "2024 Flex",
                    "data": [
                        {"date": "2023-01-01", "price": 45000.00, "label": "janeiro/2023"},
                        ...
                    ]
                },
                ...
            ]
        }
    """
    db = get_db()
    try:
        # Get parameters from POST request body
        data = request.get_json()
        vehicle_ids = data.get('vehicle_ids', [])
        start_date = data.get('start_date')
        end_date = data.get('end_date')

        # Validate required parameters
        if not vehicle_ids or len(vehicle_ids) == 0:
            return jsonify({"error": "vehicle_ids array is required and cannot be empty"}), 400

        # Limit to 5 vehicles for performance
        if len(vehicle_ids) > 5:
            return jsonify({"error": "Maximum 5 vehicles can be compared at once"}), 400

        # Convert date strings to datetime objects
        if start_date:
            start_date = datetime.fromisoformat(start_date)
        if end_date:
            end_date = datetime.fromisoformat(end_date)

        vehicles_data = []

        # Query each vehicle's data
        for year_id in vehicle_ids:
            # Build the query for this vehicle
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

            # Order by date
            query = query.order_by(ReferenceMonth.month_date)

            # Execute query
            results = query.all()

            # If no data for this vehicle, skip it
            if not results:
                continue

            # Extract vehicle information from first result
            vehicle_info = {
                "id": year_id,
                "brand": results[0].brand_name,
                "model": results[0].model_name,
                "year": results[0].year_description,
                "data": [
                    {
                        "date": result.month_date.isoformat(),
                        "price": float(result.price),
                        "label": format_month_portuguese(result.month_date)
                    }
                    for result in results
                ]
            }

            vehicles_data.append(vehicle_info)

        # Check if we have data for at least one vehicle
        if not vehicles_data:
            return jsonify({
                "error": "No data found for any of the selected vehicles"
            }), 404

        return jsonify({"vehicles": vehicles_data})

    except Exception as e:
        # Log the error and return a user-friendly message
        app.logger.error(f"Error in compare_vehicles: {str(e)}")
        return jsonify({"error": "An error occurred while fetching comparison data"}), 500

    finally:
        db.close()


@app.route('/api/price', methods=['POST'])
@require_api_key
def get_price():
    """
    Get price information for a specific car at a specific month.

    Similar to FIPE's /ConsultarValorComTodosParametros endpoint.
    This returns a single price data point instead of full history.

    Expects JSON POST body:
    {
        "brand": "Volkswagen",
        "model": "Gol",
        "year": "2024 Flex",
        "month": "2024-01-01"
    }

    Returns:
        JSON object with price information:
        {
            "brand": "Volkswagen",
            "model": "Gol 1.0 12V MCV",
            "year": "2024 Flex",
            "month": "janeiro/2024",
            "month_date": "2024-01-01",
            "price": 56789.00,
            "price_formatted": "R$ 56.789,00",
            "fipe_code": "026011-6"
        }
    """
    db = get_db()
    try:
        # Get parameters from POST request body
        data = request.get_json()
        brand_name = data.get('brand')
        model_name = data.get('model')
        year_desc = data.get('year')
        month_date = data.get('month')

        # Validate required parameters
        if not all([brand_name, model_name, year_desc, month_date]):
            return jsonify({
                "error": "Missing required parameters. Need: brand, model, year, month"
            }), 400

        # Convert month string to datetime object
        try:
            month_date = datetime.fromisoformat(month_date)
        except (ValueError, TypeError):
            return jsonify({"error": "Invalid month date format. Use YYYY-MM-DD"}), 400

        # Build query joining all tables
        result = (
            db.query(
                Brand.brand_name,
                CarModel.model_name,
                ModelYear.year_description,
                CarPrice.price,
                CarPrice.fipe_code,
                ReferenceMonth.month_date
            )
            .join(CarModel.brand)
            .join(ModelYear.car_model)
            .join(CarPrice.model_year)
            .join(CarPrice.reference_month)
            .filter(
                Brand.brand_name.ilike(func.concat('%', brand_name, '%')),
                CarModel.model_name.ilike(func.concat('%', model_name, '%')),
                ModelYear.year_description == year_desc,
                ReferenceMonth.month_date == month_date
            )
            .first()
        )

        # Check if we found data
        if not result:
            return jsonify({
                "error": "No price data found for the specified car and month",
                "searched_for": {
                    "brand": brand_name,
                    "model": model_name,
                    "year": year_desc,
                    "month": month_date.isoformat()
                }
            }), 404

        # Import formatting function
        from webapp_database_models import format_price_brl

        # Format response
        return jsonify({
            "brand": result.brand_name,
            "model": result.model_name,
            "year": result.year_description,
            "month": format_month_portuguese(result.month_date),
            "month_date": result.month_date.isoformat(),
            "price": float(result.price),
            "price_formatted": format_price_brl(result.price),
            "fipe_code": result.fipe_code
        })

    except Exception as e:
        # Log the error and return a user-friendly message
        app.logger.error(f"Error in get_price: {str(e)}")
        return jsonify({"error": "An error occurred while fetching price data"}), 500

    finally:
        db.close()


@app.route('/api/default-car', methods=['GET'])
@require_api_key
def get_default_car():
    """
    Get the default car to display when the page loads.

    This finds a car based on the DEFAULT_BRAND and DEFAULT_MODEL
    settings in config.py, filtered to only show vehicles available
    in the latest reference month.

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
        # Get the most recent reference month
        latest_month = get_latest_reference_month(db)

        if not latest_month:
            return jsonify({"error": "No reference months found in database"}), 404

        default_brand = app.config.get('DEFAULT_BRAND', 'Volkswagen')
        default_model = app.config.get('DEFAULT_MODEL', 'Gol')

        # Find the brand that has data in the latest month
        brand = (
            db.query(Brand)
            .join(Brand.models)
            .join(CarModel.years)
            .join(ModelYear.prices)
            .join(CarPrice.reference_month)
            .filter(
                Brand.brand_name == default_brand,
                ReferenceMonth.month_date == latest_month
            )
            .distinct()
            .first()
        )

        if not brand:
            # If default brand not found, get the first brand with data in latest month
            brand = (
                db.query(Brand)
                .join(Brand.models)
                .join(CarModel.years)
                .join(ModelYear.prices)
                .join(CarPrice.reference_month)
                .filter(ReferenceMonth.month_date == latest_month)
                .distinct()
                .order_by(Brand.brand_name)
                .first()
            )
            if not brand:
                return jsonify({"error": "No brands found in latest reference month"}), 404

        # Find a model containing the default model name with data in latest month
        model = (
            db.query(CarModel)
            .join(CarModel.years)
            .join(ModelYear.prices)
            .join(CarPrice.reference_month)
            .filter(
                CarModel.brand_id == brand.id,
                CarModel.model_name.ilike(func.concat('%', default_model, '%')),
                ReferenceMonth.month_date == latest_month
            )
            .distinct()
            .first()
        )

        if not model:
            # If default model not found, get the first model for this brand with data
            model = (
                db.query(CarModel)
                .join(CarModel.years)
                .join(ModelYear.prices)
                .join(CarPrice.reference_month)
                .filter(
                    CarModel.brand_id == brand.id,
                    ReferenceMonth.month_date == latest_month
                )
                .distinct()
                .order_by(CarModel.model_name)
                .first()
            )

        if not model:
            return jsonify({"error": "No models found for default brand in latest month"}), 404

        # Find the most recent year for this model with data in latest month
        year = (
            db.query(ModelYear)
            .join(ModelYear.prices)
            .join(CarPrice.reference_month)
            .filter(
                ModelYear.car_model_id == model.id,
                ReferenceMonth.month_date == latest_month
            )
            .distinct()
            .order_by(ModelYear.year_description.desc())
            .first()
        )

        if not year:
            return jsonify({"error": "No years found for default model in latest month"}), 404

        return jsonify({
            "brand_id": brand.id,
            "model_id": model.id,
            "year_id": year.id
        })

    finally:
        db.close()


@app.route('/api/economic-indicators', methods=['POST'])
@require_api_key
def get_economic_indicators():
    """
    Get economic indicators (IPCA and CDI) from Banco Central do Brasil API
    for a given date range.

    Expects JSON POST body:
    {
        "start_date": "2023-01-01",
        "end_date": "2024-12-01"
    }

    Returns:
        JSON object with accumulated IPCA and CDI for the period:
        {
            "ipca": 5.45,  // Accumulated IPCA % in period
            "cdi": 12.30   // Accumulated CDI % in period
        }
    """
    try:
        # Get parameters from POST request body
        data = request.get_json()
        start_date = data.get('start_date')
        end_date = data.get('end_date')

        # Validate required parameters
        if not start_date or not end_date:
            return jsonify({"error": "start_date and end_date are required"}), 400

        # Convert date strings to datetime objects
        try:
            start_dt = datetime.fromisoformat(start_date)
            end_dt = datetime.fromisoformat(end_date)
        except (ValueError, TypeError):
            return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400

        # Format dates for BCB API (dd/MM/yyyy)
        start_date_bcb = start_dt.strftime('%d/%m/%Y')
        end_date_bcb = end_dt.strftime('%d/%m/%Y')

        # Banco Central API URLs
        # Series 433: IPCA (monthly variation %)
        # Series 4391: CDI (monthly accumulated %)
        ipca_url = f'https://api.bcb.gov.br/dados/serie/bcdata.sgs.433/dados?formato=json&dataInicial={start_date_bcb}&dataFinal={end_date_bcb}'
        cdi_url = f'https://api.bcb.gov.br/dados/serie/bcdata.sgs.4391/dados?formato=json&dataInicial={start_date_bcb}&dataFinal={end_date_bcb}'

        # Fetch IPCA data
        try:
            ipca_response = requests.get(ipca_url, timeout=10)
            ipca_response.raise_for_status()
            ipca_data = ipca_response.json()
        except Exception as e:
            app.logger.error(f"Error fetching IPCA data: {str(e)}")
            ipca_data = []

        # Fetch CDI data
        try:
            cdi_response = requests.get(cdi_url, timeout=10)
            cdi_response.raise_for_status()
            cdi_data = cdi_response.json()
        except Exception as e:
            app.logger.error(f"Error fetching CDI data: {str(e)}")
            cdi_data = []

        # Calculate accumulated values
        # For IPCA and CDI, we need to compound the monthly rates
        # Formula: (1 + r1/100) * (1 + r2/100) * ... - 1
        def calculate_accumulated(data_list):
            if not data_list:
                return None
            try:
                # Compound the rates
                accumulated = reduce(
                    lambda acc, item: acc * (1 + float(item['valor']) / 100),
                    data_list,
                    1.0
                )
                # Convert back to percentage and subtract 1
                return (accumulated - 1) * 100
            except (ValueError, KeyError):
                return None

        ipca_accumulated = calculate_accumulated(ipca_data)
        cdi_accumulated = calculate_accumulated(cdi_data)

        return jsonify({
            "ipca": round(ipca_accumulated, 2) if ipca_accumulated is not None else None,
            "cdi": round(cdi_accumulated, 2) if cdi_accumulated is not None else None
        })

    except Exception as e:
        # Log the error and return a user-friendly message
        app.logger.error(f"Error in get_economic_indicators: {str(e)}")
        return jsonify({"error": "An error occurred while fetching economic indicators"}), 500


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
