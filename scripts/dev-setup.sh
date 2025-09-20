#!/bin/bash

# Development setup script for Coins for Change Platform

set -e

echo "🚀 Setting up Coins for Change Platform development environment..."

# Check if Poetry is installed
if ! command -v poetry &> /dev/null; then
    echo "❌ Poetry is not installed. Please install Poetry first:"
    echo "   curl -sSL https://install.python-poetry.org | python3 -"
    exit 1
fi

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

echo "✅ Prerequisites check passed"

# Install Python dependencies
echo "📦 Installing Python dependencies..."
poetry install

# Install pre-commit hooks
echo "🔧 Setting up pre-commit hooks..."
poetry run pre-commit install

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please review and update the .env file with your configuration"
fi

# Start Docker services
echo "🐳 Starting Docker services..."
docker-compose up -d

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 15

# Check service health
echo "🏥 Checking service health..."

# Check PostgreSQL
if pg_isready -h localhost -p 5432 -U cfc_user > /dev/null 2>&1; then
    echo "✅ PostgreSQL is ready"
else
    echo "⚠️  PostgreSQL is not ready yet, may need more time"
fi

# Check Redis
if redis-cli -h localhost -p 6379 ping > /dev/null 2>&1; then
    echo "✅ Redis is ready"
else
    echo "⚠️  Redis is not ready yet, may need more time"
fi

# Check OpenSearch
if curl -s http://localhost:9200/_cluster/health > /dev/null 2>&1; then
    echo "✅ OpenSearch is ready"
else
    echo "⚠️  OpenSearch is not ready yet, may need more time"
fi

echo ""
echo "🎉 Development environment setup complete!"
echo ""
echo "📋 Next steps:"
echo "   1. Review and update the .env file if needed"
echo "   2. Run 'make dev' to start the application services"
echo "   3. Run 'make test' to run the test suite"
echo ""
echo "🌐 Available services:"
echo "   - PostgreSQL: localhost:5432"
echo "   - Redis: localhost:6379"
echo "   - OpenSearch: localhost:9200"
echo "   - OpenSearch Dashboards: localhost:5601"
echo "   - Jaeger UI: localhost:16686"
echo "   - Prometheus: localhost:9090"
echo "   - Grafana: localhost:3000 (admin/admin)"
echo ""
echo "📚 API Documentation will be available at:"
echo "   - Auth Service: http://localhost:8001/docs"
echo "   - Campaign Service: http://localhost:8002/docs"
echo "   - Ideas Service: http://localhost:8003/docs"
echo "   - Coins Service: http://localhost:8004/docs"
echo "   - Search Service: http://localhost:8005/docs"
echo "   - Notifications Service: http://localhost:8006/docs"
echo "   - Analytics Service: http://localhost:8007/docs"