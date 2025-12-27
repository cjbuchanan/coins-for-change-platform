"""
Health check endpoints for database and system monitoring.
"""
import logging
from datetime import datetime, timezone
from typing import Dict, Any

from fastapi import APIRouter, HTTPException, status

from .database.connection import get_database_health
from .external.opensearch import get_opensearch_health
from .external.redis import get_redis_health
from .external.circuit_breaker import get_circuit_breaker_metrics

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """
    Basic health check endpoint for Kubernetes liveness probe.
    
    Returns:
        dict: Basic health status
    """
    return {
        "status": "healthy",
        "service": "coins-for-change",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/ready")
async def readiness_check() -> Dict[str, Any]:
    """
    Readiness check endpoint for Kubernetes readiness probe.
    Tests all external dependencies including database, Redis, and OpenSearch.
    
    Returns:
        dict: Detailed readiness status with all service health checks
        
    Raises:
        HTTPException: 503 if service is not ready
    """
    checks = {}
    overall_status = "ready"
    
    # Database health check
    try:
        db_health = await get_database_health()
        checks["database"] = db_health
        
        if db_health["status"] != "healthy":
            overall_status = "not_ready"
            
    except Exception as e:
        checks["database"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        overall_status = "not_ready"
        logger.error(f"Database health check failed: {e}")
    
    # Redis health check
    try:
        redis_health = await get_redis_health()
        checks["redis"] = redis_health
        
        if redis_health["status"] != "healthy":
            overall_status = "not_ready"
            
    except Exception as e:
        checks["redis"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        overall_status = "not_ready"
        logger.error(f"Redis health check failed: {e}")
    
    # OpenSearch health check
    try:
        opensearch_health = await get_opensearch_health()
        checks["opensearch"] = opensearch_health
        
        if opensearch_health["status"] != "healthy":
            overall_status = "not_ready"
            
    except Exception as e:
        checks["opensearch"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        overall_status = "not_ready"
        logger.error(f"OpenSearch health check failed: {e}")
    
    # Overall readiness assessment
    if overall_status != "ready":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "status": overall_status,
                "checks": checks,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )
    
    return {
        "status": overall_status,
        "checks": checks,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/startup")
async def startup_check() -> Dict[str, Any]:
    """
    Startup check endpoint for Kubernetes startup probe.
    
    Returns:
        dict: Startup status
    """
    # For now, just return healthy since we don't have complex initialization
    # In the future, this could check if migrations are complete, etc.
    return {
        "status": "started",
        "service": "coins-for-change",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/health/detailed")
async def detailed_health_check() -> Dict[str, Any]:
    """
    Detailed health check endpoint with circuit breaker metrics and service monitoring.
    
    Returns:
        dict: Comprehensive health status including all services and circuit breaker metrics
    """
    health_data = {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "services": {},
        "circuit_breakers": {},
        "summary": {
            "total_services": 0,
            "healthy_services": 0,
            "unhealthy_services": 0,
            "degraded_services": 0
        }
    }
    
    services_to_check = [
        ("database", get_database_health),
        ("redis", get_redis_health),
        ("opensearch", get_opensearch_health)
    ]
    
    # Check all services
    for service_name, health_func in services_to_check:
        try:
            service_health = await health_func()
            health_data["services"][service_name] = service_health
            
            # Update summary
            health_data["summary"]["total_services"] += 1
            if service_health["status"] == "healthy":
                health_data["summary"]["healthy_services"] += 1
            elif service_health["status"] == "degraded":
                health_data["summary"]["degraded_services"] += 1
            else:
                health_data["summary"]["unhealthy_services"] += 1
                health_data["status"] = "unhealthy"
                
        except Exception as e:
            health_data["services"][service_name] = {
                "status": "unhealthy",
                "error": str(e)
            }
            health_data["summary"]["total_services"] += 1
            health_data["summary"]["unhealthy_services"] += 1
            health_data["status"] = "unhealthy"
            logger.error(f"{service_name} health check failed: {e}")
    
    # Get circuit breaker metrics
    try:
        health_data["circuit_breakers"] = get_circuit_breaker_metrics()
    except Exception as e:
        logger.error(f"Failed to get circuit breaker metrics: {e}")
        health_data["circuit_breakers"] = {"error": str(e)}
    
    # Set overall status based on service health
    if health_data["summary"]["unhealthy_services"] > 0:
        health_data["status"] = "unhealthy"
    elif health_data["summary"]["degraded_services"] > 0:
        health_data["status"] = "degraded"
    
    return health_data


@router.get("/health/circuit-breakers")
async def circuit_breaker_status() -> Dict[str, Any]:
    """
    Get circuit breaker status and metrics.
    
    Returns:
        dict: Circuit breaker metrics and status
    """
    try:
        metrics = get_circuit_breaker_metrics()
        return {
            "status": "success",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "circuit_breakers": metrics,
            "summary": {
                "total_breakers": len(metrics),
                "open_breakers": sum(1 for cb in metrics.values() if cb["state"] == "open"),
                "half_open_breakers": sum(1 for cb in metrics.values() if cb["state"] == "half_open"),
                "closed_breakers": sum(1 for cb in metrics.values() if cb["state"] == "closed")
            }
        }
    except Exception as e:
        logger.error(f"Failed to get circuit breaker status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Failed to retrieve circuit breaker status", "details": str(e)}
        )