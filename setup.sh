#!/bin/bash

set -e

echo "=========================================="
echo "Sentiment Analysis API - Setup Script"
echo "=========================================="
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "Creating .env file from .env.example..."
    cp .env.example .env
    echo "✓ .env file created"
    echo ""
    echo "⚠️  Please update the SECRET_KEY in .env file!"
    echo "   You can generate one with: openssl rand -hex 32"
    echo ""
else
    echo "✓ .env file already exists"
fi

# Generate SSL certificates
echo "Generating SSL certificates..."
mkdir -p nginx/ssl
if [ ! -f nginx/ssl/cert.pem ]; then
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout nginx/ssl/key.pem \
        -out nginx/ssl/cert.pem \
        -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost" \
        2>/dev/null
    echo "✓ SSL certificates generated"
else
    echo "✓ SSL certificates already exist"
fi

# Create necessary directories
echo ""
echo "Creating necessary directories..."
mkdir -p models
mkdir -p logs
mkdir -p backend/app/core
mkdir -p backend/app/db
mkdir -p backend/app/schemas
mkdir -p backend/app/dependencies
mkdir -p backend/app/services
mkdir -p backend/app/middleware
mkdir -p backend/app/routers
mkdir -p alembic/versions
echo "✓ Directories created"

# Create __init__.py files
touch backend/__init__.py
touch backend/app/__init__.py
touch backend/app/core/__init__.py
touch backend/app/db/__init__.py
touch backend/app/schemas/__init__.py
touch backend/app/dependencies/__init__.py
touch backend/app/services/__init__.py
touch backend/app/middleware/__init__.py
touch backend/app/routers/__init__.py

# Build and start services
echo ""
echo "Building Docker containers..."
docker-compose build

echo ""
echo "Starting services..."
docker-compose up -d

# Wait for services to be ready
echo ""
echo "Waiting for services to be ready..."
sleep 10

# Initialize database
echo ""
echo "Initializing database..."
docker-compose exec -T api python init_db.py

# Create initial migration
echo ""
echo "Creating initial database migration..."
docker-compose exec -T api alembic revision --autogenerate -m "Initial migration"

# Apply migrations
echo ""
echo "Applying database migrations..."
docker-compose exec -T api alembic upgrade head

# Train ML model
echo ""
echo "Training ML model..."
docker-compose exec -T api python train_model.py

echo ""
echo "=========================================="
echo "Setup completed successfully!"
echo "=========================================="
echo ""
echo "Services are running:"
echo "  API (HTTP):   http://localhost"
echo "  API (HTTPS):  https://localhost"
echo "  Swagger UI:   https://localhost/docs"
echo "  ReDoc:        https://localhost/redoc"
echo ""
echo "Database:"
echo "  PostgreSQL:   localhost:5432"
echo "  Redis:        localhost:6379"
echo ""
echo "Useful commands:"
echo "  make logs      - View API logs"
echo "  make down      - Stop all services"
echo "  make up        - Start all services"
echo "  make test      - Run API tests"
echo ""