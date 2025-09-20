# Coins for Change Platform - Development Makefile

.PHONY: help install dev test lint format clean docker-up docker-down migrate

# Default target
help:
	@echo "Available commands:"
	@echo "  install     - Install dependencies using Poetry"
	@echo "  dev         - Start development environment"
	@echo "  test        - Run tests"
	@echo "  lint        - Run linting checks"
	@echo "  format      - Format code"
	@echo "  clean       - Clean up temporary files"
	@echo "  docker-up   - Start Docker services"
	@echo "  docker-down - Stop Docker services"
	@echo "  migrate     - Run database migrations"
	@echo "  setup       - Complete development setup"

# Install dependencies
install:
	poetry install
	poetry run pre-commit install

# Start development environment
dev:
	poetry run uvicorn src.services.auth.main:app --reload --port 8001 &
	poetry run uvicorn src.services.campaigns.main:app --reload --port 8002 &
	poetry run uvicorn src.services.ideas.main:app --reload --port 8003 &
	poetry run uvicorn src.services.coins.main:app --reload --port 8004 &
	poetry run uvicorn src.services.search.main:app --reload --port 8005 &
	poetry run uvicorn src.services.notifications.main:app --reload --port 8006 &
	poetry run uvicorn src.services.analytics.main:app --reload --port 8007

# Run tests
test:
	poetry run pytest -v --cov=src --cov-report=html --cov-report=term

# Run linting
lint:
	poetry run flake8 src/ tests/
	poetry run mypy src/
	poetry run bandit -r src/

# Format code
format:
	poetry run black src/ tests/
	poetry run isort src/ tests/

# Clean up
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type f -name ".coverage" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	rm -rf htmlcov/
	rm -rf dist/
	rm -rf build/

# Docker services
docker-up:
	docker-compose up -d
	@echo "Waiting for services to be ready..."
	@sleep 10
	@echo "Services should be ready. Check with: docker-compose ps"

docker-down:
	docker-compose down

# Database migrations (placeholder - will be implemented later)
migrate:
	@echo "Database migrations will be implemented in a later task"
	# poetry run alembic upgrade head

# Complete development setup
setup: install docker-up
	@echo "Development environment setup complete!"
	@echo ""
	@echo "Services available at:"
	@echo "  - PostgreSQL: localhost:5432"
	@echo "  - Redis: localhost:6379"
	@echo "  - OpenSearch: localhost:9200"
	@echo "  - OpenSearch Dashboards: localhost:5601"
	@echo "  - Jaeger UI: localhost:16686"
	@echo "  - Prometheus: localhost:9090"
	@echo "  - Grafana: localhost:3000 (admin/admin)"
	@echo ""
	@echo "To start the services, run: make dev"

# Check service health
health:
	@echo "Checking service health..."
	@curl -s http://localhost:9200/_cluster/health | jq '.status' || echo "OpenSearch not ready"
	@redis-cli ping || echo "Redis not ready"
	@pg_isready -h localhost -p 5432 -U cfc_user || echo "PostgreSQL not ready"