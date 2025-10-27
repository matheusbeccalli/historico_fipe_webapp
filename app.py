"""
FIPE Price Tracker - Main Flask Application

This webapp displays historical car price data from the FIPE database.
It uses cascading dropdowns and Plotly charts for interactive visualization.
"""

from flask import Flask, render_template, jsonify, request, session, g
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf.csrf import CSRFProtect, validate_csrf
from wtforms import ValidationError
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError, DatabaseError
from sqlalchemy.pool import QueuePool
from datetime import datetime, timedelta
import hashlib
import hmac
import json
import logging
from logging.handlers import RotatingFileHandler
import os
import requests
import secrets
from functools import reduce, wraps, lru_cache
from pathlib import Path

# Import our database models and config
from webapp_database_models import (
    Base, Brand, CarModel, ModelYear, CarPrice, ReferenceMonth,
    format_month_portuguese
)
from config import get_config

# Initialize Flask app
app = Flask(__name__)
config_obj = get_config()
app.config.from_object(config_obj)

# Validate configuration
from config import Config
Config.validate_secret_key()  # Check SECRET_KEY strength

# Validate production-specific configuration if in production mode
if hasattr(config_obj, 'validate'):
    config_obj.validate()

# SECURITY: Prevent DEBUG mode in production
is_production = os.getenv('FLASK_ENV') == 'production'
if is_production and app.config.get('DEBUG'):
    raise RuntimeError(
        "FATAL: DEBUG mode is enabled in production! "
        "Set FLASK_ENV=production and DEBUG=False in your configuration."
    )

# Configure production logging with rotation
if is_production:
    # Create logs directory if it doesn't exist
    logs_dir = Path(__file__).parent / 'logs'
    logs_dir.mkdir(exist_ok=True)

    # Configure rotating file handler
    # Rotates when file reaches 10MB, keeps 10 backup files (100MB total)
    file_handler = RotatingFileHandler(
        logs_dir / 'fipe_app.log',
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=10
    )

    # Set log format with timestamp, level, and message
    file_handler.setFormatter(logging.Formatter(
        '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
    ))

    # Set logging level (INFO captures most important events without spam)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)

    app.logger.info('Production logging configured: rotating file handler (10MB, 10 backups)')
else:
    # Development: Use console logging only
    app.logger.setLevel(logging.DEBUG)
    app.logger.info('Development logging: console only')

# Create database engine and session factory with connection pooling
# Configure pool settings based on database type (PostgreSQL vs SQLite)
is_postgres = app.config['DATABASE_URL'].startswith('postgresql')

if is_postgres:
    # PostgreSQL: Configure larger pool for production
    engine = create_engine(
        app.config['DATABASE_URL'],
        echo=app.config.get('SQLALCHEMY_ECHO', False),
        poolclass=QueuePool,
        pool_size=20,              # Number of connections to maintain
        max_overflow=40,           # Additional connections beyond pool_size
        pool_timeout=30,           # Seconds to wait for connection
        pool_recycle=1800,         # Recycle connections after 30 minutes
        pool_pre_ping=True         # Test connections before using
    )
    app.logger.info(f"PostgreSQL connection pool: size=20, max_overflow=40")
else:
    # SQLite: Smaller pool (SQLite doesn't benefit from large pools)
    engine = create_engine(
        app.config['DATABASE_URL'],
        echo=app.config.get('SQLALCHEMY_ECHO', False),
        poolclass=QueuePool,
        pool_size=5,               # Smaller pool for SQLite
        max_overflow=10,           # Limited overflow
        pool_timeout=30,
        pool_recycle=3600,         # Recycle after 1 hour
        pool_pre_ping=True
    )
    app.logger.info(f"SQLite connection pool: size=5, max_overflow=10")

SessionLocal = sessionmaker(bind=engine)

# Validate database schema on startup
def validate_database_schema():
    """
    Validate that all required tables exist in the database.

    This ensures the application fails fast at startup if the database
    is not properly initialized, rather than failing during runtime.
    """
    required_tables = ['brands', 'car_models', 'model_years', 'car_prices', 'reference_months']

    try:
        # Get list of existing tables from database
        from sqlalchemy import inspect
        inspector = inspect(engine)
        existing_tables = set(inspector.get_table_names())

        # Check if all required tables exist
        missing_tables = [table for table in required_tables if table not in existing_tables]

        if missing_tables:
            app.logger.critical(
                f"Database schema validation failed! Missing tables: {', '.join(missing_tables)}. "
                f"Please ensure the database is properly initialized."
            )
            raise RuntimeError(
                f"Database schema validation failed! Missing tables: {', '.join(missing_tables)}. "
                f"The database must be initialized before starting the application."
            )

        app.logger.info(f"Database schema validated: all {len(required_tables)} required tables exist")

    except Exception as e:
        if isinstance(e, RuntimeError):
            raise  # Re-raise schema validation errors
        app.logger.error(f"Error validating database schema: {str(e)}")
        raise RuntimeError(f"Failed to validate database schema: {str(e)}")

# Run schema validation at startup
validate_database_schema()

# Parse allowed API keys from config and store as a set for fast lookup
VALID_API_KEYS = set()
api_keys_str = app.config.get('API_KEYS_ALLOWED', '')
if api_keys_str:
    keys = [key.strip() for key in api_keys_str.split(',') if key.strip()]

    # Validate all API keys meet minimum security requirements
    for key in keys:
        if len(key) < 16:
            # Very weak key - log critical warning
            app.logger.critical(
                f'SECURITY: API key is dangerously short ({len(key)} chars). '
                f'Keys should be at least 32 characters. '
                f'Generate with: python -c "import secrets; print(secrets.token_urlsafe(32))"'
            )
        elif len(key) < 32:
            # Weak key - log warning
            app.logger.warning(
                f'API key is weak ({len(key)} chars). '
                f'Recommended: 32+ characters. '
                f'Generate with: python -c "import secrets; print(secrets.token_urlsafe(32))"'
            )

    VALID_API_KEYS = set(keys)

# Custom rate limit key function
# SECURITY: Rate limit by API key when available (more secure than IP-only)
def get_rate_limit_key():
    """
    Get rate limit key for the current request.

    Uses API key hash if available (prevents bypassing limits via IP rotation),
    otherwise falls back to IP address.

    Returns:
        str: Rate limit key in format 'apikey:hash' or 'ip:address'
    """
    api_key = request.headers.get('X-API-Key')
    if api_key and len(api_key) >= 16:
        # Rate limit by API key hash (prevents key exposure in rate limit storage)
        return f"apikey:{hash_api_key(api_key)}"
    # Fall back to IP-based rate limiting
    return f"ip:{get_remote_address()}"

# Initialize rate limiter
# Uses in-memory storage (no Redis required) - suitable for single-process deployments
# For multi-process production with gunicorn, consider using Redis: storage_uri="redis://localhost:6379"
limiter = Limiter(
    app=app,
    key_func=get_rate_limit_key,  # Track by API key or IP address
    default_limits=["200 per day", "50 per hour"],  # Global fallback limits
    storage_uri="memory://",  # In-memory storage (no external database needed)
    strategy="fixed-window"  # Simple time window strategy
)

# Initialize CSRF protection
# Session-based requests (web browsers) require CSRF tokens
# API key authenticated requests (external clients) are exempt
csrf = CSRFProtect(app)


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


def hash_api_key(api_key):
    """
    Create a consistent hash for API key logging.

    Instead of logging the first 8 characters of the API key (which could aid
    brute force attacks), we hash the key and log the first 16 characters of
    the hash. This provides a unique identifier for logging without exposing
    any part of the actual key.

    Args:
        api_key: The API key string to hash

    Returns:
        str: First 16 characters of the SHA-256 hash
    """
    return hashlib.sha256(api_key.encode()).hexdigest()[:16]


def sanitize_like_pattern(text):
    """
    Escape SQL LIKE wildcards to prevent pattern injection.

    SQL LIKE operator treats % (matches any characters) and _ (matches single
    character) as wildcards. User input containing these characters could be
    used to enumerate database contents. This function escapes them to treat
    them as literal characters.

    Args:
        text: The user input string to sanitize

    Returns:
        str: Sanitized string with LIKE wildcards escaped
    """
    if not text:
        return text
    # Escape backslash first (escape character itself)
    text = text.replace('\\', '\\\\')
    # Escape SQL LIKE wildcards
    text = text.replace('%', '\\%')
    text = text.replace('_', '\\_')
    return text


# ============================================================================
# INPUT VALIDATION HELPERS
# ============================================================================

def validate_positive_integer(value, field_name="value"):
    """
    Validate that a value is a positive integer.

    Args:
        value: The value to validate
        field_name: Name of the field for error messages

    Returns:
        tuple: (validated_value, error_message)
               If valid: (int, None)
               If invalid: (None, str)
    """
    if value is None:
        return None, f"{field_name} is required"

    # Try to convert to integer
    if not isinstance(value, int):
        try:
            value = int(value)
        except (ValueError, TypeError):
            return None, f"{field_name} must be an integer"

    # Check if positive
    if value <= 0:
        return None, f"{field_name} must be a positive integer"

    return value, None


def validate_integer_array(arr, field_name="array", min_length=1, max_length=None):
    """
    Validate that an array contains only positive integers.

    Args:
        arr: The array to validate
        field_name: Name of the field for error messages
        min_length: Minimum array length (default: 1)
        max_length: Maximum array length (default: None)

    Returns:
        tuple: (validated_array, error_message)
               If valid: ([int, ...], None)
               If invalid: (None, str)
    """
    # Check if it's a list
    if not isinstance(arr, list):
        app.logger.warning(
            f'Invalid array type for {field_name}: {type(arr).__name__} from {request.remote_addr}'
        )
        return None, f"{field_name} must be an array"

    # Check length constraints
    if len(arr) < min_length:
        return None, f"{field_name} must contain at least {min_length} item(s)"

    if max_length and len(arr) > max_length:
        # Log suspicious oversized array attempts
        app.logger.warning(
            f'Array size limit exceeded for {field_name}: '
            f'{len(arr)} > {max_length} from {request.remote_addr}'
        )
        return None, f"{field_name} cannot contain more than {max_length} item(s)"

    # Validate each element
    validated_ids = []
    for i, item in enumerate(arr):
        validated_id, error = validate_positive_integer(item, f"{field_name}[{i}]")
        if error:
            return None, error
        validated_ids.append(validated_id)

    return validated_ids, None


def validate_date_range(start_date_str, end_date_str, allow_none=True):
    """
    Validate date strings and ensure reasonable range.

    Args:
        start_date_str: Start date string in ISO format (YYYY-MM-DD)
        end_date_str: End date string in ISO format (YYYY-MM-DD)
        allow_none: Whether to allow None values (default: True)

    Returns:
        tuple: (start_date, end_date, error_message)
               If valid: (datetime, datetime, None)
               If invalid: (None, None, str)
    """
    start_date = None
    end_date = None

    # Parse start date
    if start_date_str:
        try:
            start_date = datetime.fromisoformat(start_date_str)
        except (ValueError, TypeError):
            return None, None, "start_date must be in ISO format (YYYY-MM-DD)"
    elif not allow_none:
        return None, None, "start_date is required"

    # Parse end date
    if end_date_str:
        try:
            end_date = datetime.fromisoformat(end_date_str)
        except (ValueError, TypeError):
            return None, None, "end_date must be in ISO format (YYYY-MM-DD)"
    elif not allow_none:
        return None, None, "end_date is required"

    # Validate date ranges
    if start_date or end_date:
        min_allowed = datetime(2000, 1, 1)
        max_allowed = datetime.now() + timedelta(days=365)

        if start_date and start_date < min_allowed:
            return None, None, "start_date cannot be before 2000-01-01"

        if end_date and end_date > max_allowed:
            return None, None, "end_date cannot be more than 1 year in the future"

        # Check start is before end
        if start_date and end_date and start_date > end_date:
            return None, None, "start_date must be before or equal to end_date"

    return start_date, end_date, None


def require_api_key(f):
    """
    Decorator to require authentication via session (for web browsers) or API key (for external clients).

    Authentication methods (checked in order):
    1. Session-based auth (for web browsers) - checks for 'authenticated' in session
       - Also validates CSRF token for state-changing methods (POST, PUT, DELETE, PATCH)
    2. API key auth (for external clients) - checks X-API-Key header
       - No CSRF validation needed as API keys are not vulnerable to CSRF

    Returns 401 Unauthorized if neither authentication method succeeds.
    Returns 403 Forbidden if CSRF validation fails.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check for session-based authentication first (web browsers)
        if session.get('authenticated'):
            # Validate CSRF token for state-changing methods
            if request.method in ['POST', 'PUT', 'DELETE', 'PATCH']:
                try:
                    # Get CSRF token from header or form data
                    csrf_token = request.headers.get('X-CSRFToken') or request.form.get('csrf_token')
                    validate_csrf(csrf_token)
                except ValidationError:
                    app.logger.warning(f'CSRF validation failed from {request.remote_addr} for {request.path}')
                    return jsonify({
                        'error': 'CSRF validation failed',
                        'message': 'Invalid or missing CSRF token'
                    }), 403
            
            # Validate session hasn't expired
            created_at = session.get('created_at')
            if created_at:
                try:
                    created = datetime.fromisoformat(created_at)
                    age = datetime.now() - created
                    max_age = timedelta(days=7)  # Match PERMANENT_SESSION_LIFETIME

                    if age > max_age:
                        # Session expired - clear it
                        session.clear()
                        app.logger.warning(
                            f'Expired session rejected: age={age.days} days from {request.remote_addr}'
                        )
                        return jsonify({
                            'error': 'Session expired',
                            'message': 'Your session has expired. Please reload the page.'
                        }), 401
                except (ValueError, TypeError) as e:
                    # Invalid created_at timestamp - clear session for security
                    app.logger.warning(
                        f'Invalid session timestamp from {request.remote_addr}: {e}'
                    )
                    session.clear()
                    return jsonify({
                        'error': 'Invalid session',
                        'message': 'Your session is invalid. Please reload the page.'
                    }), 401

            app.logger.debug(f'Session access granted: endpoint={request.path} method={request.method} ip={request.remote_addr}')
            return f(*args, **kwargs)

        # Fall back to API key authentication (external clients)
        api_key = request.headers.get('X-API-Key')

        # If no API keys are configured, handle based on environment
        if not VALID_API_KEYS:
            # STRICT MODE: Never allow access without keys in production
            is_production = app.config.get('ENV') == 'production' or os.getenv('FLASK_ENV') == 'production'

            if is_production:
                app.logger.critical('SECURITY: No API keys configured in production! Denying access.')
                return jsonify({
                    'error': 'Service unavailable',
                    'message': 'Authentication system not configured'
                }), 503
            else:
                app.logger.warning(
                    'DEVELOPMENT MODE: No API keys configured - allowing access. '
                    'THIS MUST NOT HAPPEN IN PRODUCTION!'
                )
                return f(*args, **kwargs)

        # Check if API key is provided
        if not api_key:
            return jsonify({
                'error': 'Authentication required',
                'message': 'Please authenticate via session or provide an API key in the X-API-Key header'
            }), 401

        # Reject suspiciously short API keys immediately
        if len(api_key) < 16:
            app.logger.warning(
                f'Suspiciously short API key attempt ({len(api_key)} chars) '
                f'from {request.remote_addr} accessing {request.path}'
            )
            return jsonify({
                'error': 'Invalid API key',
                'message': 'The provided API key is not valid'
            }), 401

        # Check if API key is valid using constant-time comparison
        # This prevents timing attacks where attackers measure response times
        # to determine if they're getting closer to a valid key
        is_valid = any(
            hmac.compare_digest(api_key, valid_key)
            for valid_key in VALID_API_KEYS
        )

        if not is_valid:
            # SECURITY: Hash the invalid key instead of logging partial plaintext
            app.logger.warning(f'Invalid API key attempt: key_hash={hash_api_key(api_key)} from {request.remote_addr} accessing {request.path}')
            return jsonify({
                'error': 'Invalid API key',
                'message': 'The provided API key is not valid'
            }), 401

        # API key is valid, log successful access and proceed with the request
        app.logger.info(f'API access granted: key_hash={hash_api_key(api_key)} endpoint={request.path} method={request.method} ip={request.remote_addr}')
        return f(*args, **kwargs)

    return decorated_function


# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(413)
def request_entity_too_large(e):
    """
    Custom handler for request too large errors (HTTP 413).

    Triggered when a request body exceeds MAX_CONTENT_LENGTH.
    Prevents memory exhaustion attacks from large payloads.
    """
    app.logger.warning(f'Request too large: {request.remote_addr} on {request.path}')
    return jsonify({
        'error': 'Request too large',
        'message': 'Request body exceeds maximum allowed size (1MB)',
        'max_size': '1MB'
    }), 413


@app.errorhandler(429)
def ratelimit_handler(e):
    """
    Custom handler for rate limit exceeded errors (HTTP 429).

    Provides a user-friendly JSON response with information about the limit
    and when the user can retry.
    """
    app.logger.warning(f'Rate limit exceeded: {request.remote_addr} on {request.path}')
    return jsonify({
        'error': 'Rate limit exceeded',
        'message': f'Too many requests. Please slow down and try again later.',
        'limit': e.description  # e.g., "1 per 1 minute"
    }), 429


# ============================================================================
# RESPONSE SECURITY HEADERS
# ============================================================================

@app.after_request
def set_security_headers(response):
    """
    Add security headers to all responses.

    These headers protect against common web vulnerabilities:
    - X-Content-Type-Options: Prevents MIME sniffing
    - X-Frame-Options: Prevents clickjacking
    - X-XSS-Protection: Enables browser XSS filter
    - Strict-Transport-Security: Enforces HTTPS (production only)
    - Content-Security-Policy: Controls resource loading with nonce-based script execution
    """
    # Prevent MIME type sniffing
    response.headers['X-Content-Type-Options'] = 'nosniff'

    # Prevent clickjacking - don't allow embedding in iframes
    response.headers['X-Frame-Options'] = 'DENY'

    # Enable browser XSS protection
    response.headers['X-XSS-Protection'] = '1; mode=block'

    # Enforce HTTPS in production (only if not in development)
    if not app.config.get('DEBUG'):
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'

    # Generate a random nonce for this request (stored in g for template access)
    # This allows specific inline scripts while blocking all others
    nonce = getattr(g, 'csp_nonce', None)
    if not nonce:
        nonce = secrets.token_urlsafe(16)
        g.csp_nonce = nonce

    # Content Security Policy - controls what resources can be loaded
    # NOTE: Plotly requires 'unsafe-inline' for styles as it dynamically generates inline styles
    # Scripts still use nonce-based execution for security
    csp_directives = [
        "default-src 'self'",
        f"script-src 'self' 'nonce-{nonce}' https://cdn.plot.ly https://cdn.jsdelivr.net",
        f"style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com",
        "font-src 'self' https://fonts.gstatic.com https://cdn.jsdelivr.net",
        "img-src 'self' data:",
        "connect-src 'self' https://cdn.plot.ly https://cdn.jsdelivr.net https://api.bcb.gov.br"
    ]
    response.headers['Content-Security-Policy'] = '; '.join(csp_directives)

    # Control referrer information leakage
    # SECURITY: strict-origin-when-cross-origin sends full URL on same-origin,
    # but only origin on cross-origin requests (no path/query string)
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'

    return response


# ============================================================================
# ROUTES - Web Pages
# ============================================================================

@app.route('/')
@limiter.limit("20 per minute")  # Allow reasonable access but prevent session exhaustion attacks
def index():
    """
    Main page route.

    Renders the index.html template with the default car information.
    The template will then load the actual data via JavaScript API calls.

    This route establishes an authenticated session for the web browser,
    eliminating the need to expose API keys in the HTML source code.
    """
    # Generate CSP nonce for this request (needed before rendering template)
    if not hasattr(g, 'csp_nonce'):
        g.csp_nonce = secrets.token_urlsafe(16)
    
    # Regenerate session ID on authentication to prevent session fixation
    if not session.get('authenticated'):
        # Clear any existing session data (prevents session fixation attack)
        session.clear()

        # Create new authenticated session
        session['authenticated'] = True
        session['created_at'] = datetime.now().isoformat()
        session.permanent = True  # Use permanent session (configurable lifetime)
        session.modified = True  # Force session to be saved with new ID

        app.logger.info(f'New web session created from {request.remote_addr}')
    else:
        # Session already exists, just access the page
        app.logger.debug(f'Existing session access from {request.remote_addr}')

    return render_template(
        'index.html',
        default_brand=app.config.get('DEFAULT_BRAND', 'Volkswagen'),
        default_model=app.config.get('DEFAULT_MODEL', 'Gol')
        # API key is NO LONGER passed to the template
    )


@app.route('/health')
@limiter.limit("60 per minute")  # Higher limit for health checks
def health():
    """
    Health check endpoint for monitoring and load balancers.

    Returns JSON with service status and basic diagnostics.
    Does NOT require API key authentication.

    Returns:
        200: Service is healthy
        503: Service is unhealthy (database connection failed)
    """
    from sqlalchemy import text
    
    health_status = {
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'fipe-price-tracker',
        'checks': {
            'database': 'unknown',
            'session': 'unknown'
        }
    }

    # Check database connectivity
    db = None
    try:
        db = get_db()
        # Simple query to test database connectivity (SQLAlchemy 2.0 requires text())
        db.execute(text('SELECT 1')).fetchone()
        health_status['checks']['database'] = 'ok'
    except Exception as e:
        app.logger.error(f'Health check database error: {str(e)}')
        health_status['status'] = 'unhealthy'
        health_status['checks']['database'] = 'failed'
        return jsonify(health_status), 503
    finally:
        if db:
            db.close()

    # Check session system (verify SECRET_KEY is set)
    if app.config.get('SECRET_KEY'):
        health_status['checks']['session'] = 'ok'
    else:
        health_status['checks']['session'] = 'warning'

    return jsonify(health_status), 200


# ============================================================================
# API ROUTES - Data Endpoints
# ============================================================================

@app.route('/api/brands', methods=['GET'])
@require_api_key
@limiter.limit("60 per minute")  # Generous limit for simple GET request
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
@limiter.limit("60 per minute")
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
@limiter.limit("60 per minute")
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
@limiter.limit("60 per minute")
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
@limiter.limit("60 per minute")
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
@limiter.limit("20 per minute")  # Reduced limit to prevent data scraping
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
        year_id_raw = data.get('year_id')
        start_date_str = data.get('start_date')
        end_date_str = data.get('end_date')

        # Validate year_id
        year_id, error = validate_positive_integer(year_id_raw, 'year_id')
        if error:
            return jsonify({"error": error}), 400

        # Validate date range
        start_date, end_date, error = validate_date_range(start_date_str, end_date_str)
        if error:
            return jsonify({"error": error}), 400
        
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
    
    except ValueError as e:
        # Client error - invalid input that passed initial validation
        app.logger.warning(f"Invalid input in get_chart_data: {type(e).__name__}")
        return jsonify({"error": "Invalid input parameters"}), 400
    except (SQLAlchemyError, DatabaseError) as e:
        # Database error - don't expose details to client
        app.logger.error(f"Database error in get_chart_data: {type(e).__name__}", exc_info=True)
        return jsonify({"error": "Database error occurred"}), 500
    except Exception as e:
        # Unexpected error - log but don't expose details
        app.logger.error(f"Unexpected error in get_chart_data: {type(e).__name__}", exc_info=True)
        return jsonify({"error": "An unexpected error occurred"}), 500

    finally:
        db.close()


@app.route('/api/compare-vehicles', methods=['POST'])
@require_api_key
@limiter.limit("10 per minute")  # Strict limit - very expensive query comparing multiple vehicles
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
        vehicle_ids_raw = data.get('vehicle_ids', [])
        start_date_str = data.get('start_date')
        end_date_str = data.get('end_date')

        # Validate vehicle_ids array (min: 1, max: 5)
        vehicle_ids, error = validate_integer_array(vehicle_ids_raw, 'vehicle_ids', min_length=1, max_length=5)
        if error:
            return jsonify({"error": error}), 400

        # Validate date range
        start_date, end_date, error = validate_date_range(start_date_str, end_date_str)
        if error:
            return jsonify({"error": error}), 400

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

    except ValueError as e:
        # Client error - invalid input that passed initial validation
        app.logger.warning(f"Invalid input in compare_vehicles: {type(e).__name__}")
        return jsonify({"error": "Invalid input parameters"}), 400
    except (SQLAlchemyError, DatabaseError) as e:
        # Database error - don't expose details to client
        app.logger.error(f"Database error in compare_vehicles: {type(e).__name__}", exc_info=True)
        return jsonify({"error": "Database error occurred"}), 500
    except Exception as e:
        # Unexpected error - log but don't expose details
        app.logger.error(f"Unexpected error in compare_vehicles: {type(e).__name__}", exc_info=True)
        return jsonify({"error": "An unexpected error occurred"}), 500

    finally:
        db.close()


@app.route('/api/price', methods=['POST'])
@require_api_key
@limiter.limit("20 per minute")  # Reduced limit to prevent data scraping
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
                Brand.brand_name.ilike(func.concat('%', sanitize_like_pattern(brand_name), '%')),
                CarModel.model_name.ilike(func.concat('%', sanitize_like_pattern(model_name), '%')),
                ModelYear.year_description == year_desc,
                ReferenceMonth.month_date == month_date
            )
            .first()
        )

        # Check if we found data
        if not result:
            error_response = {
                "error": "No price data found for the specified car and month"
            }

            # Only include search details in development for debugging
            # In production, this would leak information about valid brands/models
            # SECURITY: Double-check environment to prevent accidental DEBUG=True in production
            is_dev = app.config.get('DEBUG') and os.getenv('FLASK_ENV') != 'production'
            if is_dev:
                error_response["searched_for"] = {
                    "brand": brand_name,
                    "model": model_name,
                    "year": year_desc,
                    "month": month_date.isoformat()
                }

            return jsonify(error_response), 404

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

    except ValueError as e:
        # Client error - invalid input that passed initial validation
        app.logger.warning(f"Invalid input in get_price: {type(e).__name__}")
        return jsonify({"error": "Invalid input parameters"}), 400
    except (SQLAlchemyError, DatabaseError) as e:
        # Database error - don't expose details to client
        app.logger.error(f"Database error in get_price: {type(e).__name__}", exc_info=True)
        return jsonify({"error": "Database error occurred"}), 500
    except Exception as e:
        # Unexpected error - log but don't expose details
        app.logger.error(f"Unexpected error in get_price: {type(e).__name__}", exc_info=True)
        return jsonify({"error": "An unexpected error occurred"}), 500

    finally:
        db.close()


@app.route('/api/default-car', methods=['GET'])
@require_api_key
@limiter.limit("60 per minute")
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
                CarModel.model_name.ilike(func.concat('%', sanitize_like_pattern(default_model), '%')),
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
            "brand_name": brand.brand_name,
            "model_id": model.id,
            "model_name": model.model_name,
            "year_id": year.id,
            "year_description": year.year_description
        })

    finally:
        db.close()


@app.route('/api/economic-indicators', methods=['POST'])
@require_api_key
@limiter.limit("60 per hour")  # Stricter hourly limit - makes external API calls
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
        start_date_str = data.get('start_date')
        end_date_str = data.get('end_date')

        # Validate date range (both dates are required for this endpoint)
        start_dt, end_dt, error = validate_date_range(start_date_str, end_date_str, allow_none=False)
        if error:
            return jsonify({"error": error}), 400

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

    except ValueError as e:
        # Client error - invalid input that passed initial validation
        app.logger.warning(f"Invalid input in get_economic_indicators: {type(e).__name__}")
        return jsonify({"error": "Invalid input parameters"}), 400
    except requests.RequestException as e:
        # External API error - don't expose details to client
        app.logger.error(f"External API error in get_economic_indicators: {type(e).__name__}", exc_info=True)
        return jsonify({"error": "External service unavailable"}), 503
    except Exception as e:
        # Unexpected error - log but don't expose details
        app.logger.error(f"Unexpected error in get_economic_indicators: {type(e).__name__}", exc_info=True)
        return jsonify({"error": "An unexpected error occurred"}), 500


@app.route('/api/depreciation-analysis', methods=['GET'])
@require_api_key
@limiter.limit("10 per minute")  # Lower limit due to expensive calculations
def get_depreciation_analysis():
    """
    Get market-wide depreciation analysis by brand, model, and year groups.

    This endpoint calculates average annual depreciation rates across the entire
    database to show which brands/models/years retain value best.

    Query Parameters:
        months (optional): Number of months to analyze (default: 12, max: 60)
        brand_id (optional): If provided, returns model-level breakdown for that brand

    Returns:
        JSON object with depreciation analysis:
        {
            "calculated_at": "2024-01-15T10:30:00",
            "analysis_period_months": 12,
            "brands": [
                {
                    "brand_id": 1,
                    "brand_name": "Toyota",
                    "avg_depreciation_rate": -3.2,  # Annual rate as percentage
                    "value_retention": 68.0,  # Percentage of original value retained
                    "sample_size": 150  # Number of vehicle models analyzed
                },
                ...
            ],
            "year_groups": [
                {
                    "year_range": "2020-2024",
                    "avg_depreciation_rate": -5.5,
                    "value_retention": 72.0,
                    "sample_size": 500
                },
                ...
            ],
            "models": [  # Only if brand_id provided
                {
                    "model_id": 10,
                    "model_name": "Corolla",
                    "avg_depreciation_rate": -2.8,
                    "value_retention": 70.0,
                    "sample_size": 5
                },
                ...
            ]
        }
    """
    db = get_db()
    try:
        # Get parameters
        months = request.args.get('months', default=12, type=int)
        brand_id_raw = request.args.get('brand_id', type=int)

        # Validate months parameter
        if months < 1 or months > 60:
            return jsonify({"error": "months must be between 1 and 60"}), 400

        # Validate brand_id if provided
        brand_id = None
        if brand_id_raw is not None:
            brand_id, error = validate_positive_integer(brand_id_raw, 'brand_id')
            if error:
                return jsonify({"error": error}), 400

        # Get latest reference month to determine analysis window
        latest_month = get_latest_reference_month(db)
        if not latest_month:
            return jsonify({"error": "No reference months found in database"}), 404

        # Calculate start date for analysis window
        start_date = latest_month - timedelta(days=months * 30)

        # Use cached calculation function
        cache_key = f"{latest_month.isoformat()}_{months}_{brand_id or 'all'}"
        result = _calculate_depreciation_analysis(cache_key, start_date, latest_month, brand_id)

        return jsonify(result)

    except ValueError as e:
        app.logger.warning(f"Invalid input in get_depreciation_analysis: {type(e).__name__}")
        return jsonify({"error": "Invalid input parameters"}), 400
    except (SQLAlchemyError, DatabaseError) as e:
        app.logger.error(f"Database error in get_depreciation_analysis: {type(e).__name__}", exc_info=True)
        return jsonify({"error": "Database error occurred"}), 500
    except Exception as e:
        app.logger.error(f"Unexpected error in get_depreciation_analysis: {type(e).__name__}", exc_info=True)
        return jsonify({"error": "An unexpected error occurred"}), 500

    finally:
        db.close()


@lru_cache(maxsize=10)
def _calculate_depreciation_analysis(cache_key, start_date, end_date, brand_id=None):
    """
    Calculate depreciation analysis with caching.

    Cache key includes the date range and brand_id to auto-refresh when:
    - New data is added to the database (latest_month changes)
    - User requests different time period
    - User requests different brand

    Args:
        cache_key: String combining latest_month, months, and brand_id
        start_date: Start of analysis period
        end_date: End of analysis period (latest month)
        brand_id: Optional brand to analyze at model level

    Returns:
        Dict with depreciation analysis results
    """
    db = get_db()
    try:
        # Calculate brand-level depreciation
        brands_analysis = _calculate_brand_depreciation(db, start_date, end_date)

        # Calculate year group depreciation
        year_groups_analysis = _calculate_year_group_depreciation(db, start_date, end_date)

        # Calculate model-level depreciation if brand_id provided
        models_analysis = None
        if brand_id:
            models_analysis = _calculate_model_depreciation(db, start_date, end_date, brand_id)

        # Build response
        result = {
            "calculated_at": datetime.now().isoformat(),
            "analysis_period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "months": round((end_date - start_date).days / 30)
            },
            "brands": brands_analysis,
            "year_groups": year_groups_analysis
        }

        if models_analysis is not None:
            result["models"] = models_analysis

        return result

    finally:
        db.close()


def _calculate_brand_depreciation(db, start_date, end_date):
    """
    Calculate average depreciation rate by brand.

    For each brand, we:
    1. Find all models with price data in the analysis period
    2. For each model, calculate depreciation from first to last price
    3. Annualize the depreciation rate
    4. Average across all models in the brand
    """
    from sqlalchemy import case, distinct

    # Subquery to get first and last price for each ModelYear
    first_price_sq = (
        db.query(
            CarPrice.model_year_id,
            func.min(ReferenceMonth.month_date).label('first_date'),
            func.max(ReferenceMonth.month_date).label('last_date')
        )
        .join(CarPrice.reference_month)
        .filter(ReferenceMonth.month_date >= start_date)
        .filter(ReferenceMonth.month_date <= end_date)
        .group_by(CarPrice.model_year_id)
        .having(func.min(ReferenceMonth.month_date) < func.max(ReferenceMonth.month_date))
        .subquery()
    )

    # Get first prices
    first_prices = (
        db.query(
            CarPrice.model_year_id,
            CarPrice.price.label('first_price')
        )
        .join(CarPrice.reference_month)
        .join(first_price_sq,
              (CarPrice.model_year_id == first_price_sq.c.model_year_id) &
              (ReferenceMonth.month_date == first_price_sq.c.first_date))
        .subquery()
    )

    # Get last prices
    last_prices = (
        db.query(
            CarPrice.model_year_id,
            CarPrice.price.label('last_price')
        )
        .join(CarPrice.reference_month)
        .join(first_price_sq,
              (CarPrice.model_year_id == first_price_sq.c.model_year_id) &
              (ReferenceMonth.month_date == first_price_sq.c.last_date))
        .subquery()
    )

    # Calculate brand-level aggregations
    query = (
        db.query(
            Brand.id.label('brand_id'),
            Brand.brand_name,
            func.count(distinct(CarModel.id)).label('sample_size'),
            func.avg(
                ((last_prices.c.last_price - first_prices.c.first_price) / first_prices.c.first_price) * 100 *
                (365.25 / (func.julianday(first_price_sq.c.last_date) - func.julianday(first_price_sq.c.first_date)))
            ).label('avg_annual_depreciation')
        )
        .join(CarModel.brand)
        .join(CarModel.years)
        .join(first_price_sq, ModelYear.id == first_price_sq.c.model_year_id)
        .join(first_prices, ModelYear.id == first_prices.c.model_year_id)
        .join(last_prices, ModelYear.id == last_prices.c.model_year_id)
        .group_by(Brand.id, Brand.brand_name)
        .having(func.count(distinct(CarModel.id)) >= 3)  # Only brands with 3+ models
        .order_by(func.avg(
            ((last_prices.c.last_price - first_prices.c.first_price) / first_prices.c.first_price) * 100 *
            (365.25 / (func.julianday(first_price_sq.c.last_date) - func.julianday(first_price_sq.c.first_date)))
        ).desc())
    )

    results = query.all()

    return [
        {
            "brand_id": row.brand_id,
            "brand_name": row.brand_name,
            "avg_depreciation_rate": round(float(row.avg_annual_depreciation or 0), 2),
            "value_retention": round(100 + float(row.avg_annual_depreciation or 0), 1),
            "sample_size": row.sample_size
        }
        for row in results
    ]


def _calculate_year_group_depreciation(db, start_date, end_date):
    """
    Calculate average depreciation rate by year groups.

    Groups vehicles by manufacture year ranges:
    - 2020-2024 (0-5 years old)
    - 2015-2019 (6-10 years old)
    - 2010-2014 (11-15 years old)
    - 2005-2009 (16-20 years old)
    - <2005 (20+ years old)
    """
    from sqlalchemy import case, distinct, cast, Integer

    # Extract year from year_description (format: "2024 Flex")
    # Most year descriptions start with 4-digit year
    current_year = datetime.now().year

    # Subquery for first and last prices (same as brand calculation)
    first_price_sq = (
        db.query(
            CarPrice.model_year_id,
            func.min(ReferenceMonth.month_date).label('first_date'),
            func.max(ReferenceMonth.month_date).label('last_date')
        )
        .join(CarPrice.reference_month)
        .filter(ReferenceMonth.month_date >= start_date)
        .filter(ReferenceMonth.month_date <= end_date)
        .group_by(CarPrice.model_year_id)
        .having(func.min(ReferenceMonth.month_date) < func.max(ReferenceMonth.month_date))
        .subquery()
    )

    first_prices = (
        db.query(
            CarPrice.model_year_id,
            CarPrice.price.label('first_price')
        )
        .join(CarPrice.reference_month)
        .join(first_price_sq,
              (CarPrice.model_year_id == first_price_sq.c.model_year_id) &
              (ReferenceMonth.month_date == first_price_sq.c.first_date))
        .subquery()
    )

    last_prices = (
        db.query(
            CarPrice.model_year_id,
            CarPrice.price.label('last_price')
        )
        .join(CarPrice.reference_month)
        .join(first_price_sq,
              (CarPrice.model_year_id == first_price_sq.c.model_year_id) &
              (ReferenceMonth.month_date == first_price_sq.c.last_date))
        .subquery()
    )

    # Create year group categories
    year_group = case(
        (cast(func.substr(ModelYear.year_description, 1, 4), Integer) >= 2020, '2020-2024'),
        (cast(func.substr(ModelYear.year_description, 1, 4), Integer) >= 2015, '2015-2019'),
        (cast(func.substr(ModelYear.year_description, 1, 4), Integer) >= 2010, '2010-2014'),
        (cast(func.substr(ModelYear.year_description, 1, 4), Integer) >= 2005, '2005-2009'),
        else_='<2005'
    )

    query = (
        db.query(
            year_group.label('year_range'),
            func.count(distinct(ModelYear.id)).label('sample_size'),
            func.avg(
                ((last_prices.c.last_price - first_prices.c.first_price) / first_prices.c.first_price) * 100 *
                (365.25 / (func.julianday(first_price_sq.c.last_date) - func.julianday(first_price_sq.c.first_date)))
            ).label('avg_annual_depreciation')
        )
        .join(first_price_sq, ModelYear.id == first_price_sq.c.model_year_id)
        .join(first_prices, ModelYear.id == first_prices.c.model_year_id)
        .join(last_prices, ModelYear.id == last_prices.c.model_year_id)
        .group_by(year_group)
        .order_by(year_group.desc())
    )

    results = query.all()

    return [
        {
            "year_range": row.year_range,
            "avg_depreciation_rate": round(float(row.avg_annual_depreciation or 0), 2),
            "value_retention": round(100 + float(row.avg_annual_depreciation or 0), 1),
            "sample_size": row.sample_size
        }
        for row in results
    ]


def _calculate_model_depreciation(db, start_date, end_date, brand_id):
    """
    Calculate average depreciation rate by model for a specific brand.

    Similar to brand calculation but at model level.
    """
    from sqlalchemy import distinct

    # Subquery for first and last prices
    first_price_sq = (
        db.query(
            CarPrice.model_year_id,
            func.min(ReferenceMonth.month_date).label('first_date'),
            func.max(ReferenceMonth.month_date).label('last_date')
        )
        .join(CarPrice.reference_month)
        .filter(ReferenceMonth.month_date >= start_date)
        .filter(ReferenceMonth.month_date <= end_date)
        .group_by(CarPrice.model_year_id)
        .having(func.min(ReferenceMonth.month_date) < func.max(ReferenceMonth.month_date))
        .subquery()
    )

    first_prices = (
        db.query(
            CarPrice.model_year_id,
            CarPrice.price.label('first_price')
        )
        .join(CarPrice.reference_month)
        .join(first_price_sq,
              (CarPrice.model_year_id == first_price_sq.c.model_year_id) &
              (ReferenceMonth.month_date == first_price_sq.c.first_date))
        .subquery()
    )

    last_prices = (
        db.query(
            CarPrice.model_year_id,
            CarPrice.price.label('last_price')
        )
        .join(CarPrice.reference_month)
        .join(first_price_sq,
              (CarPrice.model_year_id == first_price_sq.c.model_year_id) &
              (ReferenceMonth.month_date == first_price_sq.c.last_date))
        .subquery()
    )

    query = (
        db.query(
            CarModel.id.label('model_id'),
            CarModel.model_name,
            func.count(distinct(ModelYear.id)).label('sample_size'),
            func.avg(
                ((last_prices.c.last_price - first_prices.c.first_price) / first_prices.c.first_price) * 100 *
                (365.25 / (func.julianday(first_price_sq.c.last_date) - func.julianday(first_price_sq.c.first_date)))
            ).label('avg_annual_depreciation')
        )
        .join(CarModel.years)
        .join(first_price_sq, ModelYear.id == first_price_sq.c.model_year_id)
        .join(first_prices, ModelYear.id == first_prices.c.model_year_id)
        .join(last_prices, ModelYear.id == last_prices.c.model_year_id)
        .filter(CarModel.brand_id == brand_id)
        .group_by(CarModel.id, CarModel.model_name)
        .order_by(func.avg(
            ((last_prices.c.last_price - first_prices.c.first_price) / first_prices.c.first_price) * 100 *
            (365.25 / (func.julianday(first_price_sq.c.last_date) - func.julianday(first_price_sq.c.first_date)))
        ).desc())
    )

    results = query.all()

    return [
        {
            "model_id": row.model_id,
            "model_name": row.model_name,
            "avg_depreciation_rate": round(float(row.avg_annual_depreciation or 0), 2),
            "value_retention": round(100 + float(row.avg_annual_depreciation or 0), 1),
            "sample_size": row.sample_size
        }
        for row in results
    ]


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
    # Check if running in production mode
    is_production = os.getenv('FLASK_ENV') == 'production'

    if is_production:
        # CRITICAL SECURITY: Never run Flask dev server in production!
        raise RuntimeError(
            "\n\n"
            "=" * 70 + "\n"
            "CRITICAL ERROR: Cannot run Flask development server in production!\n"
            "=" * 70 + "\n\n"
            "The Flask development server is not designed for production use.\n"
            "It lacks essential security features and performance optimizations.\n\n"
            "Please use a production WSGI server like:\n"
            "  - Gunicorn: gunicorn -w 4 app:app\n"
            "  - Waitress: waitress-serve --port=8080 app:app\n\n"
            "Deploy behind a reverse proxy (nginx/Apache) with HTTPS.\n"
            "=" * 70 + "\n"
        )

    # Run the Flask development server (development only)
    app.run(
        debug=True,  # Safe in development
        host='127.0.0.1',  # Only accessible from your computer
        port=5000
    )
