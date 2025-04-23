# FastAPI Layered Architecture Application

A FastAPI application skeleton with a layered architecture, PostgreSQL database integration, and Docker support.

## Features

- Layered architecture (controllers, services, repositories)
- PostgreSQL database with async ORM (SQLAlchemy 2.0)
- Environment configuration
- Docker and docker-compose setup
- Utilities for common tasks
- API documentation with Swagger UI

## Setup

### Using Docker

```bash
docker-compose up -d
```

### Manual Setup

1. Create a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Set up environment variables (see .env.example)

4. Run the application:

```bash
uvicorn app.main:app --reload
```

## Project Structure

```
app/
├── api/               # API routes and controllers
│   ├── dependencies/  # Route dependencies
│   └── routes/        # API endpoints
├── core/              # Core application components
│   ├── config.py      # Application configuration
│   └── exceptions.py  # Custom exceptions
├── db/                # Database components
│   ├── models/        # SQLAlchemy models
│   ├── repositories/  # Data access layer
│   └── session.py     # Database session
├── services/          # Business logic layer
├── schemas/           # Pydantic models for request/response
└── utils/             # Utility functions
main.py                # Application entry point
```

## API Documentation

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
