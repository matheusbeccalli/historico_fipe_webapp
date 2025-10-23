"""
Configuration file for FIPE Price Tracker webapp

This file handles database configuration and can switch between
SQLite (for development) and PostgreSQL (for production).
"""

import os
import secrets
import warnings
from pathlib import Path
from datetime import timedelta
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """
    Base configuration class.

    You can override these settings using environment variables.
    This makes it easy to deploy to different environments.
    """

    # Secret key for Flask sessions
    # Generate a random secret key for development if none is provided
    # In production, you MUST set SECRET_KEY in your .env file
    _dev_secret_key = secrets.token_hex(32)
    SECRET_KEY = os.getenv('SECRET_KEY') or _dev_secret_key

    # Session configuration
    SESSION_COOKIE_HTTPONLY = True  # Prevent JavaScript access to session cookie
    SESSION_COOKIE_SAMESITE = 'Strict'  # Maximum CSRF protection
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)  # Session expires after 7 days

    # Request size limits (prevent memory exhaustion attacks)
    MAX_CONTENT_LENGTH = 1 * 1024 * 1024  # 1MB max request body size

    # Database configuration
    # By default, uses SQLite for development
    # Set DATABASE_URL environment variable to use PostgreSQL
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///fipe_data.db')
    
    # SQLAlchemy settings
    SQLALCHEMY_TRACK_MODIFICATIONS = False  # Reduces overhead
    SQLALCHEMY_ECHO = os.getenv('SQLALCHEMY_ECHO', 'False').lower() == 'true'  # Set to True to see SQL queries
    
    # Default car to show when page loads
    # You can change these to any car in your database
    DEFAULT_BRAND = os.getenv('DEFAULT_BRAND', 'Volkswagen')
    DEFAULT_MODEL = os.getenv('DEFAULT_MODEL', 'Gol')  # Will search for models containing "Gol"

    # API Key Authentication
    # API_KEY: The application's own API key (used by frontend to make API calls)
    API_KEY = os.getenv('API_KEY', '')

    # API_KEYS_ALLOWED: Comma-separated list of valid API keys that can access the API
    # Should include API_KEY plus any external client keys
    # Example: API_KEYS_ALLOWED=app-key-123,external-key-456,partner-key-789
    API_KEYS_ALLOWED = os.getenv('API_KEYS_ALLOWED', '')

    # CSRF Protection
    WTF_CSRF_ENABLED = True  # Enable CSRF protection for forms
    WTF_CSRF_TIME_LIMIT = None  # CSRF tokens don't expire (valid for session lifetime)
    WTF_CSRF_SSL_STRICT = False  # Allow development without HTTPS (set True in production if needed)

    @staticmethod
    def validate_secret_key():
        """
        Validate that SECRET_KEY is properly configured.

        Checks that the secret key exists and meets minimum security requirements.
        Issues warnings for development or raises errors for production.
        """
        secret = os.getenv('SECRET_KEY', '')
        is_production = os.getenv('FLASK_ENV') == 'production'

        if not secret:
            # No SECRET_KEY set - using random key
            if is_production:
                raise ValueError(
                    "SECRET_KEY must be set in production! "
                    "Generate one with: python generate_secret_key.py"
                )
            else:
                warnings.warn(
                    "\n"
                    "No SECRET_KEY set in .env file. Using randomly generated key.\n"
                    "Sessions will not persist across server restarts.\n"
                    "For persistent sessions, run: python generate_secret_key.py",
                    UserWarning,
                    stacklevel=2
                )
        elif len(secret) < 32:
            # SECRET_KEY is too short
            if is_production:
                raise ValueError(
                    f"SECRET_KEY is too short ({len(secret)} chars). "
                    "Must be at least 32 characters for production!"
                )
            else:
                warnings.warn(
                    f"SECRET_KEY is weak ({len(secret)} chars). "
                    "Should be at least 32 characters.",
                    UserWarning,
                    stacklevel=2
                )


class DevelopmentConfig(Config):
    """Development configuration - more verbose for debugging"""
    DEBUG = True


class ProductionConfig(Config):
    """Production configuration - optimized for performance"""
    DEBUG = False
    SESSION_COOKIE_SECURE = True  # Only send session cookie over HTTPS in production

    # In production, you MUST set these environment variables in .env:
    # - SECRET_KEY: A strong random secret key
    # - DATABASE_URL: PostgreSQL connection string
    #   Example: postgresql://user:password@localhost/fipe_db
    # - FORCE_HTTPS: Set to 'true' to confirm app is behind HTTPS

    @staticmethod
    def validate():
        """
        Validate that production requirements are met.

        This checks that the application is properly configured for
        production deployment, particularly HTTPS enforcement.
        """
        import warnings

        # Check if HTTPS is confirmed
        force_https = os.getenv('FORCE_HTTPS', '').lower()
        if force_https != 'true':
            warnings.warn(
                "\n\n"
                "=" * 70 + "\n"
                "SECURITY WARNING: Production mode without FORCE_HTTPS=true\n"
                "=" * 70 + "\n"
                "Session cookies will be vulnerable to interception!\n\n"
                "You MUST deploy this application behind HTTPS (nginx/Apache).\n"
                "Once confirmed, set FORCE_HTTPS=true in your .env file.\n"
                "=" * 70,
                SecurityWarning,
                stacklevel=2
            )


# Dictionary to easily switch between configs
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}


def get_config():
    """
    Get the appropriate configuration based on environment.
    
    Returns:
        Config class based on FLASK_ENV environment variable
    """
    env = os.getenv('FLASK_ENV', 'development')
    return config.get(env, config['default'])
