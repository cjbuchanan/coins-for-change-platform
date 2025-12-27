# Coding Standards and Best Practices

This document defines the coding standards, patterns, and best practices for the Coins for Change platform.

## Code Style and Formatting

### Python Code Style

- Follow PEP 8 style guidelines
- Use Black for code formatting with line length of 88 characters
- Use isort for import sorting with Black-compatible settings
- Use type hints for all function parameters and return values
- Maximum function length: 50 lines (prefer smaller, focused functions)
- Maximum class length: 200 lines

### Naming Conventions

- **Variables and functions**: snake_case (e.g., `user_id`, `get_campaign_by_id`)
- **Classes**: PascalCase (e.g., `CampaignService`, `UserRepository`)
- **Constants**: UPPER_SNAKE_CASE (e.g., `MAX_COIN_ALLOCATION`, `DEFAULT_PAGE_SIZE`)
- **Database tables**: snake_case (e.g., `campaign_members`, `coin_allocations`)
- **API endpoints**: kebab-case for multi-word resources (e.g., `/campaign-members`)

### File and Directory Structure

```
src/
├── shared/                 # Shared utilities and common code
│   ├── database/          # Database connection and utilities
│   ├── auth/              # Authentication utilities
│   ├── logging/           # Logging configuration
│   └── validation/        # Common validation utilities
├── services/
│   ├── auth/              # Authentication service
│   ├── campaigns/         # Campaign management service
│   ├── ideas/             # Idea management service
│   ├── coins/             # Coin economy service
│   ├── search/            # Search and duplicate detection
│   ├── notifications/     # Notification service
│   └── analytics/         # Analytics and reporting
└── tests/
    ├── unit/              # Unit tests
    ├── integration/       # Integration tests
    └── e2e/               # End-to-end tests
```

## Database Patterns

### Model Definitions

```python
# Always include audit fields
class BaseModel(Base):
    __abstract__ = True
    
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow, 
        onupdate=datetime.utcnow
    )
    created_by: Mapped[Optional[UUID]] = mapped_column(ForeignKey("users.id"))
    updated_by: Mapped[Optional[UUID]] = mapped_column(ForeignKey("users.id"))

# Use proper type hints and constraints
class Campaign(BaseModel):
    __tablename__ = "campaigns"
    
    campaign_id: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text)
    status: Mapped[CampaignStatus] = mapped_column(default=CampaignStatus.DRAFT)
```

### Repository Pattern

```python
class BaseRepository:
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_by_id(self, id: UUID) -> Optional[T]:
        """Get entity by ID with proper error handling"""
        
    async def create(self, entity: T) -> T:
        """Create entity with audit trail"""
        
    async def update(self, entity: T) -> T:
        """Update entity with optimistic locking"""
        
    async def delete(self, id: UUID) -> bool:
        """Soft delete with audit trail"""

# Always use transactions for multi-step operations
async def allocate_coins(
    self, 
    user_id: UUID, 
    idea_id: UUID, 
    amount: int
) -> CoinAllocation:
    async with self.session.begin():
        # Check balance
        # Create allocation
        # Update balance
        # Log transaction
```

## API Design Patterns

### Endpoint Structure

```python
# Use consistent URL patterns
@router.get("/campaigns/{campaign_id}/ideas")
@router.post("/campaigns/{campaign_id}/ideas")
@router.get("/campaigns/{campaign_id}/ideas/{idea_id}")
@router.put("/campaigns/{campaign_id}/ideas/{idea_id}")
@router.delete("/campaigns/{campaign_id}/ideas/{idea_id}")

# Always use Pydantic models for request/response
class IdeaCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=1, max_length=5000)
    tag_ids: List[UUID] = Field(default_factory=list)

class IdeaResponse(BaseModel):
    id: UUID
    title: str
    description: str
    status: IdeaStatus
    coin_count: int
    created_at: datetime
    submitter: UserSummary
    tags: List[TagSummary]
```

### Error Handling

```python
# Use consistent error response format
class APIError(Exception):
    def __init__(self, code: str, message: str, details: Dict = None):
        self.code = code
        self.message = message
        self.details = details or {}

# Standard error codes
class ErrorCodes:
    AUTHENTICATION_FAILED = "AUTH_001"
    INSUFFICIENT_PERMISSIONS = "AUTH_002"
    CAMPAIGN_NOT_FOUND = "CAMPAIGN_001"
    INSUFFICIENT_COINS = "COIN_001"
    
# Always log errors with context
@app.exception_handler(APIError)
async def api_error_handler(request: Request, exc: APIError):
    logger.error(
        "API Error",
        extra={
            "error_code": exc.code,
            "message": exc.message,
            "path": request.url.path,
            "method": request.method,
            "user_id": getattr(request.state, "user_id", None)
        }
    )
```

## Testing Standards

### Unit Test Structure

```python
# Use descriptive test names
def test_allocate_coins_success_updates_balance_and_creates_allocation():
    """Test that successful coin allocation updates user balance and creates allocation record"""
    
# Use AAA pattern (Arrange, Act, Assert)
async def test_create_campaign_with_valid_data():
    # Arrange
    user = await create_test_user()
    campaign_data = CampaignCreateRequest(
        title="Test Campaign",
        description="Test Description"
    )
    
    # Act
    campaign = await campaign_service.create_campaign(user.id, campaign_data)
    
    # Assert
    assert campaign.title == "Test Campaign"
    assert campaign.created_by == user.id
    assert campaign.status == CampaignStatus.DRAFT

# Test edge cases and error conditions
async def test_allocate_coins_insufficient_balance_raises_error():
    # Test insufficient balance scenario
    
async def test_allocate_coins_to_accepted_idea_raises_error():
    # Test allocation to accepted idea
```

### Integration Test Patterns

```python
# Use test fixtures for common setup
@pytest.fixture
async def test_campaign():
    campaign = await create_test_campaign()
    yield campaign
    await cleanup_test_campaign(campaign.id)

# Test complete workflows
async def test_complete_idea_submission_workflow():
    # Create campaign
    # Invite members
    # Submit idea
    # Allocate coins
    # Accept idea
    # Verify coin expiration
```

## Kubernetes-Native Development

### Health Check Implementation

```python
# health.py - Kubernetes-compatible health checks
from fastapi import APIRouter, HTTPException, status
from sqlalchemy import text
import asyncio

router = APIRouter()

@router.get("/health")
async def health_check():
    """Kubernetes liveness probe - basic service health"""
    return {"status": "healthy", "service": "coins-for-change"}

@router.get("/ready")
async def readiness_check():
    """Kubernetes readiness probe - service ready to handle requests"""
    checks = {}
    
    # Database connectivity check
    try:
        async with get_db_session() as session:
            await session.execute(text("SELECT 1"))
        checks["database"] = "ready"
    except Exception as e:
        checks["database"] = f"not_ready: {str(e)}"
    
    # Cache connectivity check
    try:
        redis_client = get_redis_client()
        await redis_client.ping()
        checks["cache"] = "ready"
    except Exception as e:
        checks["cache"] = f"not_ready: {str(e)}"
    
    # Overall readiness
    all_ready = all("ready" in status for status in checks.values())
    
    if not all_ready:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"status": "not_ready", "checks": checks}
        )
    
    return {"status": "ready", "checks": checks}

@router.get("/startup")
async def startup_check():
    """Kubernetes startup probe - service initialization complete"""
    # Check if service has completed initialization
    if not app_initialized:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"status": "starting", "message": "Service still initializing"}
        )
    
    return {"status": "started", "service": "coins-for-change"}
```

### Configuration Management

```python
# config.py - Kubernetes-friendly configuration
from pydantic import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    # Service configuration
    service_name: str = "coins-for-change"
    service_version: str = "1.0.0"
    
    # Database configuration
    database_url: str
    database_pool_size: int = 20
    database_max_overflow: int = 50
    
    # Cache configuration
    redis_url: str = "redis://localhost:6379"
    redis_max_connections: int = 100
    
    # Kubernetes-specific settings
    pod_name: Optional[str] = os.getenv("HOSTNAME")
    pod_namespace: Optional[str] = os.getenv("POD_NAMESPACE")
    pod_ip: Optional[str] = os.getenv("POD_IP")
    
    # Observability
    otel_service_name: str = "coins-for-change"
    otel_exporter_jaeger_endpoint: Optional[str] = None
    prometheus_metrics_port: int = 9090
    
    class Config:
        env_file = ".env"
        case_sensitive = False
```

### Resource Management

```python
# Implement graceful shutdown for Kubernetes
import signal
import asyncio
from contextlib import asynccontextmanager

class GracefulShutdown:
    def __init__(self):
        self.shutdown = False
        self.tasks = set()
    
    def signal_handler(self, signum, frame):
        print(f"Received signal {signum}, initiating graceful shutdown...")
        self.shutdown = True
    
    async def cleanup(self):
        """Cleanup resources before shutdown"""
        # Cancel running tasks
        for task in self.tasks:
            task.cancel()
        
        # Wait for tasks to complete
        if self.tasks:
            await asyncio.gather(*self.tasks, return_exceptions=True)
        
        # Close database connections
        await database.disconnect()
        
        # Close Redis connections
        await redis_client.close()

# Register signal handlers
shutdown_handler = GracefulShutdown()
signal.signal(signal.SIGTERM, shutdown_handler.signal_handler)
signal.signal(signal.SIGINT, shutdown_handler.signal_handler)
```

### Logging for Kubernetes

```python
# logging_config.py - Structured logging for Kubernetes
import logging
import json
import os
from datetime import datetime

class KubernetesFormatter(logging.Formatter):
    def format(self, record):
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "service": os.getenv("SERVICE_NAME", "coins-for-change"),
            "pod_name": os.getenv("HOSTNAME"),
            "pod_namespace": os.getenv("POD_NAMESPACE"),
            "correlation_id": getattr(record, "correlation_id", None),
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_entry)

# Configure logging for Kubernetes
def setup_kubernetes_logging():
    handler = logging.StreamHandler()
    handler.setFormatter(KubernetesFormatter())
    
    logger = logging.getLogger()
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    
    return logger
```

### Metrics for Kubernetes

```python
# metrics.py - Prometheus metrics for Kubernetes monitoring
from prometheus_client import Counter, Histogram, Gauge, start_http_server
import time

# Business metrics
coin_allocations_total = Counter(
    'coin_allocations_total',
    'Total number of coin allocations',
    ['campaign_id', 'user_type']
)

idea_submissions_total = Counter(
    'idea_submissions_total',
    'Total number of idea submissions',
    ['campaign_id', 'status']
)

# Technical metrics
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status_code']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint']
)

database_connections_active = Gauge(
    'database_connections_active',
    'Number of active database connections'
)

# Middleware for automatic metrics collection
async def metrics_middleware(request, call_next):
    start_time = time.time()
    
    response = await call_next(request)
    
    # Record metrics
    duration = time.time() - start_time
    http_requests_total.labels(
        method=request.method,
        endpoint=request.url.path,
        status_code=response.status_code
    ).inc()
    
    http_request_duration_seconds.labels(
        method=request.method,
        endpoint=request.url.path
    ).observe(duration)
    
    return response

# Start Prometheus metrics server
def start_metrics_server(port: int = 9090):
    start_http_server(port)
```

## Security Guidelines

### Authentication and Authorization

```python
# Always validate permissions at multiple levels
async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    # Validate JWT token
    # Check user status
    # Return user with permissions

# Use dependency injection for authorization
async def require_campaign_manager(
    campaign_id: UUID,
    current_user: User = Depends(get_current_user)
) -> CampaignMember:
    # Check if user is campaign manager
    # Return campaign membership or raise error

# Implement resource-level authorization
async def can_modify_idea(user: User, idea: Idea) -> bool:
    # Check if user is idea submitter or campaign manager
```

### Input Validation

```python
# Always validate and sanitize input
class IdeaCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=255, regex=r'^[^<>]*$')
    description: str = Field(..., min_length=1, max_length=5000)
    
    @validator('title')
    def validate_title(cls, v):
        # Additional validation logic
        return v.strip()

# Use parameterized queries (SQLAlchemy handles this)
# Never concatenate user input into SQL strings
```

## Performance Guidelines

### Database Optimization

```python
# Use appropriate indexes
class Campaign(BaseModel):
    campaign_id: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    status: Mapped[CampaignStatus] = mapped_column(index=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, index=True)

# Use eager loading for related data
campaigns = await session.execute(
    select(Campaign)
    .options(selectinload(Campaign.members))
    .where(Campaign.status == CampaignStatus.ACTIVE)
)

# Implement pagination for large datasets
class PaginationParams(BaseModel):
    page: int = Field(1, ge=1)
    size: int = Field(20, ge=1, le=100)
    
async def get_campaigns_paginated(pagination: PaginationParams):
    offset = (pagination.page - 1) * pagination.size
    # Use offset and limit in query
```

### Caching Strategy

```python
# Cache frequently accessed data
@cache(expire=300)  # 5 minutes
async def get_campaign_summary(campaign_id: UUID) -> CampaignSummary:
    # Expensive calculation
    
# Invalidate cache on updates
async def update_campaign(campaign_id: UUID, updates: CampaignUpdate):
    campaign = await campaign_repo.update(campaign_id, updates)
    await cache.delete(f"campaign_summary:{campaign_id}")
    return campaign
```

## Documentation Standards

### Code Documentation

```python
class CoinService:
    """Service for managing coin economy operations.
    
    This service handles coin allocation, reallocation, and balance management
    while enforcing campaign boundaries and business rules.
    """
    
    async def allocate_coins(
        self, 
        user_id: UUID, 
        idea_id: UUID, 
        amount: int
    ) -> CoinAllocation:
        """Allocate coins from user balance to an idea.
        
        Args:
            user_id: ID of the user allocating coins
            idea_id: ID of the idea receiving coins
            amount: Number of coins to allocate (must be positive)
            
        Returns:
            CoinAllocation: The created allocation record
            
        Raises:
            InsufficientCoinsError: If user doesn't have enough coins
            IdeaNotCompetingError: If idea is not in competing status
            CampaignInactiveError: If campaign is not active
        """
```

### API Documentation

- Use FastAPI's automatic OpenAPI generation
- Provide detailed descriptions for all endpoints
- Include example requests and responses
- Document all possible error codes and their meanings

## Logging and Monitoring

### Structured Logging

```python
import structlog

logger = structlog.get_logger()

# Always include context in logs
logger.info(
    "Coin allocation created",
    user_id=user_id,
    idea_id=idea_id,
    amount=amount,
    campaign_id=campaign_id,
    allocation_id=allocation.id
)

# Log errors with full context
logger.error(
    "Failed to allocate coins",
    user_id=user_id,
    idea_id=idea_id,
    amount=amount,
    error=str(e),
    exc_info=True
)
```

### Metrics and Tracing

```python
# Add custom metrics for business events
from opentelemetry import metrics

meter = metrics.get_meter(__name__)
coin_allocations_counter = meter.create_counter(
    "coin_allocations_total",
    description="Total number of coin allocations"
)

# Add tracing to important operations
from opentelemetry import trace

tracer = trace.get_tracer(__name__)

async def allocate_coins(self, user_id: UUID, idea_id: UUID, amount: int):
    with tracer.start_as_current_span("allocate_coins") as span:
        span.set_attributes({
            "user_id": str(user_id),
            "idea_id": str(idea_id),
            "amount": amount
        })
        # Implementation
        coin_allocations_counter.add(1, {"campaign_id": campaign_id})
```
