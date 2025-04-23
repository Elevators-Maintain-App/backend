#!/bin/bash

echo "Initializing FastAPI Layered Application"

# Check if .env file exists
if [ ! -f ".env" ]; then
  echo "Creating .env file from .env.example"
  cp .env.example .env
  echo "Please update the .env file with your configuration"
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
  echo "Creating virtual environment"
  python -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment"
source venv/bin/activate

# Install dependencies
echo "Installing dependencies"
pip install -r requirements.txt

# Initialize the database
echo "Initializing database"
alembic upgrade head

# Done
echo "Initialization complete!"
echo "To start the application, run: uvicorn app.main:app --reload"
echo "Or with Docker: docker-compose up -d" 