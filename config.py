"""
Configuration file for FIPE Price Tracker webapp

This file handles database configuration and can switch between
SQLite (for development) and PostgreSQL (for production).
"""

import os
from pathlib import Path
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
    

class DevelopmentConfig(Config):
    """Development configuration - more verbose for debugging"""
    DEBUG = True


class ProductionConfig(Config):
    """Production configuration - optimized for performance"""
    DEBUG = False

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
