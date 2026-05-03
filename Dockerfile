FROM python:3.11-slim

WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# Instalar dependencias 
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    libffi-dev \
    libcairo2 \
    fonts-liberation \
    fonts-dejavu \
    curl \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt test-requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt -r test-requirements.txt

# Copy project
COPY . /app/

# Expose port
EXPOSE 8000

# Run the application with Uvicorn
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
