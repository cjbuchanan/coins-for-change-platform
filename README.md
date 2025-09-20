# Coins for Change Platform

A collaborative ideation and prioritization platform that enables organizations to
gather, evaluate, and prioritize ideas from stakeholders using a coin-based
allocation mechanism.

## Overview

The Coins for Change platform serves four distinct user types:

- **System Administrators**: Manage platform infrastructure and user access
- **Campaign Managers**: Configure and oversee ideation campaigns
- **Campaign Members**: Submit ideas and allocate coins to prioritize
  features
- **System Sponsors**: Track system usage and business value

## Architecture

The platform follows a microservices architecture with the following services:

- **Authentication Service** (Port 8001): User management, role-based access control
- **Campaign Service** (Port 8002): Campaign lifecycle and configuration
- **Ideas Service** (Port 8003): Idea submission and approval workflow
- **Coins Service** (Port 8004): Coin economy and allocation management
- **Search Service** (Port 8005): Full-text search and duplicate detection
- **Notifications Service** (Port 8006): Email and in-app notifications
- **Analytics Service** (Port 8007): Reporting and metrics aggregation

## Technology Stack

### Backend

- **Python 3.11+** with **FastAPI** framework
- **PostgreSQL** for structured data and transactions
- **OpenSearch** for full-text search and analytics
- **Redis** for caching and session management

### Infrastructure

- **Docker & Docker Compose** for local development
- **Kubernetes** for production deployment
- **OpenTelemetry** for observability (tracing, metrics, logging)
- **Prometheus & Grafana** for monitoring
- **Jaeger** for distributed tracing

## Quick Start

### Prerequisites

- Python 3.11+
- Poetry (for dependency management)
- Docker and Docker Compose
- Make (optional, for convenience commands)

### Development Setup

1. **Clone the repository**

   ```bash
   git clone <repository-url>
   cd coins-for-change-platform
   ```

2. **Install dependencies**

   ```bash
   make install
   # or manually:
   poetry install
   poetry run pre-commit install
   ```

3. **Start infrastructure services**

   ```bash
   make docker-up
   # or manually:
   docker-compose up -d
   ```

4. **Configure environment**

   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Start development services**

   ```bash
   make dev
   # This starts all microservices on ports 8001-8007
   ```

### Complete Setup

For a complete setup including all dependencies:

```bash
make setup
```

This will install dependencies, start Docker services, and provide you with
service URLs.

## Development

### Project Structure

```text
src/
├── services/           # Microservices
│   ├── auth/          # Authentication service
│   ├── campaigns/     # Campaign management
│   ├── ideas/         # Idea management
│   ├── coins/         # Coin economy
│   ├── search/        # Search and duplicate detection
│   ├── notifications/ # Notification service
│   └── analytics/     # Analytics and reporting
└── shared/            # Shared utilities
    ├── database/      # Database utilities
    ├── auth/          # Authentication utilities
    ├── logging/       # Logging configuration
    └── validation/    # Common validation schemas
```

### Available Commands

- `make install` - Install dependencies
- `make dev` - Start development services
- `make test` - Run tests with coverage
- `make lint` - Run linting checks
- `make format` - Format code with Black and isort
- `make docker-up` - Start Docker services
- `make docker-down` - Stop Docker services
- `make clean` - Clean temporary files
- `make health` - Check service health

### Code Quality

The project uses several tools to maintain code quality:

- **Black** for code formatting
- **isort** for import sorting
- **flake8** for linting
- **mypy** for type checking
- **bandit** for security scanning
- **pre-commit** hooks for automated checks

### Testing

Run tests with:

```bash
make test
```

This runs pytest with coverage reporting. Tests are organized into:

- Unit tests (`tests/unit/`)
- Integration tests (`tests/integration/`)
- End-to-end tests (`tests/e2e/`)

## Services

### Infrastructure Services

When you run `make docker-up`, the following services will be available:

- **PostgreSQL**: `localhost:5432`
  - Database: `coins_for_change`
  - User: `cfc_user`
  - Password: `cfc_password`

- **Redis**: `localhost:6379`

- **OpenSearch**: `localhost:9200`
  - OpenSearch Dashboards: `localhost:5601`

- **Jaeger UI**: `localhost:16686`

- **Prometheus**: `localhost:9090`

- **Grafana**: `localhost:3000`
  - Username: `admin`
  - Password: `admin`

### Application Services

When you run `make dev`, the following API services will be available:

- **Auth Service**: `http://localhost:8001/docs`
- **Campaign Service**: `http://localhost:8002/docs`
- **Ideas Service**: `http://localhost:8003/docs`
- **Coins Service**: `http://localhost:8004/docs`
- **Search Service**: `http://localhost:8005/docs`
- **Notifications Service**: `http://localhost:8006/docs`
- **Analytics Service**: `http://localhost:8007/docs`

Each service provides interactive API documentation at the `/docs` endpoint.

## Configuration

Configuration is managed through environment variables. Copy `.env.example` to
`.env` and update the values:

```bash
cp .env.example .env
```

Key configuration sections:

- **Application Settings**: Environment, debug mode, logging
- **Database Settings**: PostgreSQL connection and pooling
- **Redis Settings**: Cache configuration
- **OpenSearch Settings**: Search engine configuration
- **Security Settings**: JWT secrets and password requirements
- **Email Settings**: SMTP configuration for notifications
- **Observability**: OpenTelemetry and monitoring configuration

## Contributing

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/your-feature`
3. **Make your changes** following the coding standards
4. **Run tests**: `make test`
5. **Run linting**: `make lint`
6. **Commit your changes**: `git commit -m 'Add some feature'`
7. **Push to the branch**: `git push origin feature/your-feature`
8. **Submit a pull request**

### Coding Standards

- Follow PEP 8 style guidelines
- Use type hints for all functions
- Write docstrings for all public functions and classes
- Maintain test coverage above 80%
- Use meaningful commit messages

## Documentation

- **API Documentation**: Available at each service's `/docs` endpoint
- **Architecture Documentation**: See `docs/` directory
- **Deployment Guide**: See `docs/deployment.md`

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For questions and support:

- Create an issue in the repository
- Check the documentation in the `docs/` directory
- Review the API documentation at service endpoints
