# Database Infrastructure Setup

This document describes the database infrastructure setup for the Coins for Change
platform, including PostgreSQL async connections, Alembic migrations, connection
pooling, health checks, and transaction management.

## Overview

The database infrastructure provides:

- **Async PostgreSQL connections** with SQLAlchemy 2.0+ and asyncpg driver
- **Connection pooling** with configurable sizing and timeout settings
- **Database migrations** using Alembic with environment-specific configurations
- **Health check endpoints** for Kubernetes probes
- **Transaction management** with proper rollback and error handling
- **Connection retry logic** with exponential backoff
- **Base models** with audit fields (created_at, updated_at, created_by, updated_by)
- **Repository pattern** for consistent data access

## Architecture

```text
src/shared/database/
├── __init__.py          # Package exports
├── base.py              # Base model with audit fields
├── connection.py        # Async connection management
├── transactions.py      # Transaction utilities
└── repository.py        # Base repository pattern

alembic/
├── env.py              # Alembic environment configuration
├── script.py.mako      # Migration template
└── versions/           # Migration files

scripts/
├── seed_database.py    # Database seeding utility
└── validate_database_setup.py  # Setup validation
```

## Configuration

Database settings are managed through environment variables:

```bash
# Database connection
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/coins_for_change

# Connection pooling
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=50
DATABASE_POOL_TIMEOUT=30

# Environment
ENVIRONMENT=development
DEBUG=false
```

## Usage Examples

### Basic Database Session

```python
from src.shared.database import get_db_session

async def get_user(user_id: UUID):
    async with get_db_session() as session:
        result = await session.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()
```

### Transaction Management

```python
from src.shared.database import database_transaction

async def create_campaign_with_members(campaign_data, member_emails):
    async with database_transaction() as session:
        # Create campaign
        campaign = Campaign(**campaign_data)
        session.add(campaign)
        await session.flush()  # Get campaign ID
        
        # Create members
        for email in member_emails:
            member = CampaignMember(
                campaign_id=campaign.id,
                email=email
            )
            session.add(member)
        
        # Commit happens automatically if no exception
        return campaign
```

### Repository Pattern

```python
from src.shared.database import BaseRepository

class UserRepository(BaseRepository[User]):
    async def get_by_unique_field(
        self, 
        session: AsyncSession, 
        field_name: str, 
        field_value: Any
    ) -> Optional[User]:
        if field_name == "email":
            result = await session.execute(
                select(User).where(User.email == field_value)
            )
            return result.scalar_one_or_none()
        return None
    
    async def get_by_email(
        self, 
        session: AsyncSession, 
        email: str
    ) -> Optional[User]:
        return await self.get_by_unique_field(session, "email", email)

# Usage
user_repo = UserRepository(User)
async with get_db_session() as session:
    user = await user_repo.get_by_email(session, "user@example.com")
```

### Health Checks

```python
from src.shared.database import get_database_health

# Get detailed health information
health_status = await get_database_health()
print(health_status)
# {
#   "status": "healthy",
#   "connection_pool": {"size": 20, "checked_in": 15, ...},
#   "query_performance": {"simple_query_ms": 5.2, ...}
# }
```

## Database Models

All models should inherit from `BaseModel` to get audit fields:

```python
from src.shared.database import BaseModel
from sqlalchemy.orm import Mapped, mapped_column

class User(BaseModel):
    __tablename__ = "users"
    
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(default=True)
    
    # Audit fields (id, created_at, updated_at, created_by, updated_by) 
    # are automatically inherited from BaseModel
```

## Migrations

### Create Migration

```bash
# Auto-generate migration from model changes
alembic revision --autogenerate -m "Add user table"

# Create empty migration
alembic revision -m "Custom migration"
```

### Run Migrations

```bash
# Upgrade to latest
alembic upgrade head

# Upgrade to specific revision
alembic upgrade abc123

# Downgrade one revision
alembic downgrade -1

# Show current revision
alembic current

# Show migration history
alembic history
```

### Environment-Specific Migrations

The Alembic configuration automatically uses the database URL from your
environment settings, so you can run migrations against different environments
by setting the appropriate environment variables.

## Database Seeding

Use the seeding script for development and testing:

```bash
# Seed development data
python scripts/seed_database.py --action seed-dev

# Seed test data
python scripts/seed_database.py --action seed-test

# Create tables only
python scripts/seed_database.py --action create

# Clear database (testing only)
python scripts/seed_database.py --action clear

# Run health check
python scripts/seed_database.py --action health
```

## Health Check Endpoints

The application provides Kubernetes-compatible health check endpoints:

- `GET /health` - Basic liveness probe
- `GET /ready` - Readiness probe with database connectivity check
- `GET /startup` - Startup probe

Example readiness check response:

```json
{
  "status": "ready",
  "checks": {
    "database": {
      "status": "healthy",
      "connection_pool": {
        "size": 20,
        "checked_in": 15,
        "checked_out": 5,
        "overflow": 0,
        "invalid": 0
      },
      "query_performance": {
        "simple_query_ms": 5.2,
        "complex_query_ms": 12.8
      }
    }
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

## Connection Pooling

The database connection pool is configured with:

- **Pool Size**: Number of persistent connections (default: 20)
- **Max Overflow**: Additional connections when pool is full (default: 50)
- **Pool Timeout**: Seconds to wait for connection (default: 30)
- **Pool Recycle**: Seconds before recycling connections (default: 3600)
- **Pre-ping**: Validate connections before use (enabled)

## Error Handling

The database infrastructure provides comprehensive error handling:

- **Connection errors**: Automatic retry with exponential backoff
- **Transaction errors**: Automatic rollback with detailed logging
- **Pool exhaustion**: Proper timeout and error reporting
- **Query errors**: Structured error responses with context

## Performance Monitoring

Database performance is monitored through:

- **Connection pool metrics**: Active, idle, and overflow connections
- **Query performance**: Response times for health check queries
- **Error rates**: Failed connections and query errors
- **Health check thresholds**: Configurable performance alerts

## Testing

### Unit Tests

```bash
# Run database unit tests
python -m pytest tests/unit/test_database_connection.py -v
```

### Integration Tests

```bash
# Run database integration tests (requires running database)
python -m pytest tests/integration/test_database_integration.py -v -m integration
```

### Validation

```bash
# Validate database setup
python scripts/validate_database_setup.py
```

## Troubleshooting

### Common Issues

1. **Connection refused**: Check if PostgreSQL is running and accessible
2. **Pool timeout**: Increase `DATABASE_POOL_TIMEOUT` or `DATABASE_POOL_SIZE`
3. **Migration errors**: Ensure database schema is up to date
4. **Import errors**: Install dependencies with `poetry install`

### Debug Mode

Enable debug mode to see SQL queries and connection pool events:

```bash
DEBUG=true
```

### Connection Testing

```python
from src.shared.database.connection import DatabaseManager

db_manager = DatabaseManager()
success = await db_manager.retry_connection(max_retries=3)
if success:
    print("Database connection successful")
else:
    print("Database connection failed")
```

## Security Considerations

- **Connection strings**: Never commit database credentials to version control
- **SSL connections**: Use SSL in production environments
- **Connection limits**: Configure appropriate pool sizes to prevent resource exhaustion
- **Query logging**: Disable SQL query logging in production
- **Access control**: Use least-privilege database users

## Production Deployment

For production deployment:

1. **Environment variables**: Set all required database configuration
2. **SSL connections**: Enable SSL for database connections
3. **Connection pooling**: Tune pool sizes based on expected load
4. **Health checks**: Configure Kubernetes probes with appropriate timeouts
5. **Monitoring**: Set up alerts for database health and performance
6. **Backups**: Implement regular database backup procedures
7. **Migration strategy**: Plan for zero-downtime migrations
