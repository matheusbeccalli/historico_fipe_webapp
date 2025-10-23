"""
Configuration file for FIPE Price Tracker webapp

This file handles database configuration and can switch between
SQLite (for development) and PostgreSQL (for production).
"""

import os
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
    
    # Secret key for Flask sessions (change this in production!)
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

    # Session configuration
    SESSION_COOKIE_HTTPONLY = True  # Prevent JavaScript access to session cookie
    SESSION_COOKIE_SAMESITE = 'Lax'  # CSRF protection
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
