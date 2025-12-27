# External Service Connections and Resilience

This module provides comprehensive external service connection management with
built-in resilience patterns for the Coins for Change platform.

## Features

### 🔌 Service Connections

- **OpenSearch**: Full-text search with SSL, authentication, and connection pooling
- **Redis**: Caching and session storage with async connection pooling
- **Database**: PostgreSQL with async SQLAlchemy (in `../database/`)

### 🛡️ Resilience Patterns

- **Circuit Breaker**: Prevents cascading failures by stopping requests to
  failing services
- **Retry Logic**: Exponential backoff with jitter for transient failures
- **Graceful Degradation**: Fallback responses when services are unavailable
- **Health Monitoring**: Continuous health checks with alerting

### 🔍 Service Discovery

- **Static Discovery**: Configuration-based endpoints for development
- **Kubernetes Discovery**: DNS-based service discovery for production
- **Dynamic Endpoints**: Automatic endpoint health tracking and selection

### 📊 Monitoring & Alerting

- **Health Checks**: Comprehensive service health monitoring
- **Metrics Collection**: Performance and availability metrics
- **Alert Management**: Configurable alerting with multiple handlers
- **Circuit Breaker Metrics**: Real-time circuit breaker status and statistics

## Quick Start

### Basic Usage

```python
from shared.external import (
    get_opensearch_client,
    get_redis_client,
    circuit_breaker,
    with_retry
)

# Get service clients
opensearch = get_opensearch_client()
redis = get_redis_client()

# Use with resilience patterns
@circuit_breaker("my_service", fail_max=5, reset_timeout=60)
@with_retry(max_retries=3, base_delay=1.0)
async def my_external_call():
    # Your external service call here
    pass
```

### Health Checks

```python
from shared.external import (
    get_opensearch_health,
    get_redis_health
)

# Check service health
opensearch_health = await get_opensearch_health()
redis_health = await get_redis_health()

print(f"OpenSearch: {opensearch_health['status']}")
print(f"Redis: {redis_health['status']}")
```

### Monitoring Setup

```python
from shared.external import setup_default_monitoring, get_monitoring_manager

# Set up monitoring for all services
await setup_default_monitoring()

# Get monitoring summary
manager = get_monitoring_manager()
summary = manager.get_health_summary()
print(f"Overall health: {summary['overall_health']}")
```

## Configuration

### Environment Variables

```bash
# OpenSearch
OPENSEARCH_URL=https://localhost:9200
OPENSEARCH_USERNAME=admin
OPENSEARCH_PASSWORD=admin
OPENSEARCH_TIMEOUT=30
OPENSEARCH_MAX_RETRIES=3

# Redis
REDIS_URL=redis://localhost:6379/0
REDIS_MAX_CONNECTIONS=100
REDIS_SOCKET_TIMEOUT=5

# Database (handled by database module)
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/db
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=50
```

### Circuit Breaker Configuration

```python
from shared.external import circuit_breaker

@circuit_breaker(
    name="my_service",
    fail_max=5,              # Open after 5 failures
    reset_timeout=60,        # Try reset after 60 seconds
    success_threshold=3,     # Close after 3 successes
    excluded_exceptions=[    # Don't count these as failures
        ValidationError,
        BusinessLogicError
    ]
)
async def my_function():
    pass
```

### Retry Configuration

```python
from shared.external import with_retry

@with_retry(
    max_retries=3,           # Maximum retry attempts
    base_delay=1.0,          # Base delay in seconds
    max_delay=60.0,          # Maximum delay cap
    exponential_base=2.0,    # Exponential backoff base
    jitter=True,             # Add random jitter
    retryable_exceptions=[   # Only retry these exceptions
        ConnectionError,
        TimeoutError
    ]
)
async def my_function():
    pass
```

## Architecture

### Component Overview

```text
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Application   │    │   Application   │    │   Application   │
│    Service      │    │    Service      │    │    Service      │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          └──────────────────────┼──────────────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │  External Services      │
                    │  Resilience Layer       │
                    │                         │
                    │  ┌─────────────────┐    │
                    │  │ Circuit Breaker │    │
                    │  └─────────────────┘    │
                    │  ┌─────────────────┐    │
                    │  │ Retry Logic     │    │
                    │  └─────────────────┘    │
                    │  ┌─────────────────┐    │
                    │  │ Health Monitor  │    │
                    │  └─────────────────┘    │
                    └────────────┬────────────┘
                                 │
          ┌──────────────────────┼──────────────────────┐
          │                      │                      │
┌─────────▼───────┐    ┌─────────▼───────┐    ┌─────────▼───────┐
│   PostgreSQL    │    │   OpenSearch    │    │     Redis       │
│   Database      │    │   Search        │    │    Cache        │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Service Managers

Each external service has a dedicated manager class:

- **OpenSearchManager**: Handles OpenSearch connections with SSL and authentication
- **RedisManager**: Manages Redis connection pools and health checks
- **DatabaseManager**: PostgreSQL connections (in `../database/`)

### Resilience Components

- **CircuitBreaker**: State machine with open/closed/half-open states
- **RetryManager**: Configurable retry logic with exponential backoff
- **ServiceMonitor**: Continuous health monitoring with alerting
- **ServiceRegistry**: Service discovery and endpoint management

## Health Check Endpoints

The module integrates with FastAPI health check endpoints:

### `/health`

Basic liveness probe for Kubernetes

### `/ready`

Readiness probe that checks all external services

### `/health/detailed`

Comprehensive health status with metrics

### `/health/circuit-breakers`

Circuit breaker status and metrics

## Monitoring and Alerting

### Alert Severity Levels

- **INFO**: Service recovery, normal operations
- **WARNING**: Performance degradation, high error rates
- **ERROR**: Service failures, circuit breaker trips
- **CRITICAL**: Multiple service failures, system-wide issues

### Metrics Collected

- Response times
- Error rates
- Success/failure counts
- Circuit breaker states
- Connection pool status
- Service uptime

### Alert Handlers

- **LogAlertHandler**: Logs alerts with appropriate levels
- **Custom Handlers**: Implement `AlertHandler` interface for email, Slack, etc.

## Best Practices

### 1. Use Appropriate Timeouts

```python
# Short timeouts for cache operations
@with_retry(max_retries=2, base_delay=0.5, max_delay=5.0)
async def cache_operation():
    pass

# Longer timeouts for search operations
@with_retry(max_retries=3, base_delay=1.0, max_delay=30.0)
async def search_operation():
    pass
```

### 2. Configure Circuit Breakers by Service Type

```python
# Strict for critical services
@circuit_breaker("database", fail_max=3, reset_timeout=30)

# More lenient for optional services
@circuit_breaker("analytics", fail_max=10, reset_timeout=120)
```

### 3. Implement Graceful Degradation

```python
async def search_with_fallback(query: str):
    try:
        return await opensearch_search(query)
    except CircuitBreakerError:
        # Fallback to simple database search
        return await database_search(query)
```

### 4. Monitor Key Metrics

- Set up alerts for high error rates (>10%)
- Monitor response time degradation
- Track circuit breaker state changes
- Alert on consecutive failures

## Testing

### Unit Tests

```python
import pytest
from shared.external import CircuitBreaker, RetryManager

@pytest.mark.asyncio
async def test_circuit_breaker():
    cb = CircuitBreaker("test", fail_max=2)
    # Test circuit breaker behavior
```

### Integration Tests

```python
@pytest.mark.asyncio
async def test_service_health():
    health = await get_opensearch_health()
    assert health["status"] == "healthy"
```

### Load Testing

Use the monitoring metrics to validate performance under load:

- Response time percentiles
- Error rate thresholds
- Circuit breaker behavior
- Connection pool utilization

## Troubleshooting

### Common Issues

1. **Circuit Breaker Stuck Open**
   - Check service health
   - Verify reset timeout configuration
   - Review failure threshold settings

2. **High Retry Rates**
   - Investigate root cause of failures
   - Adjust retry configuration
   - Consider circuit breaker tuning

3. **Connection Pool Exhaustion**
   - Monitor pool metrics
   - Adjust pool size configuration
   - Check for connection leaks

4. **Service Discovery Issues**
   - Verify DNS resolution
   - Check Kubernetes service configuration
   - Review endpoint health checks

### Debug Logging

Enable debug logging to troubleshoot issues:

```python
import logging
logging.getLogger("shared.external").setLevel(logging.DEBUG)
```

## Performance Considerations

### Connection Pooling

- Use appropriate pool sizes for your workload
- Monitor pool utilization metrics
- Configure connection timeouts properly

### Circuit Breaker Tuning

- Set failure thresholds based on service SLAs
- Adjust reset timeouts for service recovery patterns
- Use appropriate success thresholds for stability

### Retry Strategy

- Use exponential backoff to avoid overwhelming failing services
- Add jitter to prevent thundering herd problems
- Set maximum delays to avoid excessive wait times

### Monitoring Overhead

- Adjust health check intervals based on service criticality
- Use appropriate alert thresholds to avoid noise
- Consider monitoring resource usage

## Future Enhancements

- **Advanced Service Discovery**: Consul, etcd integration
- **Load Balancing**: Weighted round-robin, least connections
- **Distributed Circuit Breakers**: Shared state across instances
- **Advanced Monitoring**: Custom metrics, dashboards
- **Security**: mTLS, certificate rotation
- **Performance**: Connection multiplexing, HTTP/2 support
