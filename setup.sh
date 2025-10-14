#!/bin/bash
# FIPE Price Tracker - Linux/Mac Setup Script
# This script automates the initial setup process

echo "================================"
echo "FIPE Price Tracker - Setup"
echo "================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed"
    echo "Please install Python 3.8 or higher"
    exit 1
fi

echo "Python found!"
python3 --version
echo ""

# Create virtual environment
echo "Creating virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "Virtual environment created successfully!"
else
    echo "Virtual environment already exists."
fi
echo ""

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt
echo ""

echo "================================"
echo "Setup completed successfully!"
echo "================================"
echo ""
echo "To start the application, run:"
echo "  1. source venv/bin/activate"
echo "  2. python app.py"
echo ""
echo "The application will be available at: http://127.0.0.1:5000"
echo ""
