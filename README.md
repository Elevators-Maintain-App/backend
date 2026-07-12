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

### Running tests safely

Do not run pytest inside the normal `api` service. It loads `.env`, which may contain a production `DATABASE_URL`.

Use the isolated test compose instead:

```bash
docker compose -f docker-compose.test.yml up -d --build
docker compose -f docker-compose.test.yml exec -T api-test python scripts/bootstrap_test_database.py
docker compose -f docker-compose.test.yml exec -T api-test alembic stamp 7b8d4f2c1a90
docker compose -f docker-compose.test.yml exec -T api-test alembic current
docker compose -f docker-compose.test.yml exec -T api-test python -m pytest tests/test_database_safety.py -v --no-cov
docker compose -f docker-compose.test.yml down
```

See `docs/testing-database-isolation.md` for the full policy and commands. The historical Alembic chain is not yet bootstrappeable from an empty database, so tests temporarily use `create_all + stamp` only in `db-test`.

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

5. **(Optional)** Run migrations
   crear migracion:
   `docker exec -it fastapi_app alembic revision --autogenerate -m "agregar campo de logo"`

Run migracion:
`docker exec -it fastapi_app alembic upgrade head`

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
